# Nonlinear transforms, feature selection and expert knowledge

The second half of chapter 4 of Müller & Guido covers three more tools: mathematical transformations of
single features, automatic selection of the features worth keeping, and the use of domain knowledge to
build features that no algorithm would invent.

## 1. Univariate nonlinear transformations

Adding squared or cubed features helps linear regression. Other transformations are often useful too:
applying **`log`, `exp` or `sin`** to a feature. Tree-based models only care about the *order* of the
values in a feature, so a monotonic transform changes nothing for them. Linear models and neural networks
are tied closely to the **scale and distribution** of each feature. If the relation between a feature and
the target is nonlinear, a linear model struggles, especially in regression.

Most models work best when each feature (and, in regression, the target too) is roughly **Gaussian**.
`log` and `exp` are a hacky but simple and effective way to get there. A common case is **count data**:
"how often did user A log in?" Counts are never negative and often follow a skewed distribution, with many
small values and a few very large ones.

```python-run
import numpy as np
from sklearn.linear_model import Ridge
from sklearn.model_selection import train_test_split

rng = np.random.RandomState(0)
X_org = rng.normal(size=(1000, 3))
w = rng.normal(size=3)
X = rng.poisson(10 * np.exp(X_org))               # skewed, non-negative integer counts
y = X_org @ w                                     # the target depends on the *underlying* values

print("feature 0: median =", np.median(X[:, 0]), " max =", X[:, 0].max(), " share of values < 10:", (X[:, 0] < 10).mean().round(2))
X_tr, X_te, y_tr, y_te = train_test_split(X, y, random_state=0)
print(f"Ridge on raw counts:     test R2 = {Ridge().fit(X_tr, y_tr).score(X_te, y_te):.3f}")
print(f"Ridge on log(counts+1):  test R2 = {Ridge().fit(np.log(X_tr + 1), y_tr).score(np.log(X_te + 1), y_te):.3f}")
```

This mirrors the book's experiment: Ridge scores about 0.62 on the raw counts and about 0.88 after
`log(X + 1)`. The transformation makes the distribution much more symmetric and removes the very large
outliers.

Points to remember:

- Use `np.log1p(x)` (that is, $\log(1+x)$) when zeros are present, since $\log 0$ is undefined.
- Usually only some features need transforming, and sometimes each needs a different transform. Finding
  the right ones is "somewhat of an art".
- It can also help to transform the **target** `y` in regression. Predicting counts or prices is a common
  example: fit on `log(y + 1)` and convert the predictions back with `expm1`. scikit-learn's
  `TransformedTargetRegressor` does this cleanly.
- These transformations are irrelevant to tree models. They matter for linear models, and they can matter
  for SVMs, nearest neighbours and neural networks.

Binning, polynomials and interactions can all have a large effect on linear models and naive Bayes, and
sometimes on kernel methods and networks. Trees can usually discover important interactions themselves.

## 2. Automatic feature selection

With so many ways to create features, it is tempting to make the data far wider than the original. But
more features make models more complex and raise the risk of overfitting. When adding features, or with
high-dimensional data in general, it can be a good idea to **keep only the most useful features** and
discard the rest. The result is a simpler model that may generalise better, trains and predicts faster,
and is easier to understand.

There are three basic strategies. All are **supervised** (they need the target), and so all must be fitted
**on the training set only**.

| strategy | idea | scikit-learn |
|---|---|---|
| univariate statistics | test each feature individually against the target | `SelectKBest`, `SelectPercentile` |
| model-based selection | use a model's importances/coefficients | `SelectFromModel` |
| iterative selection | repeatedly build models, adding or removing features | `RFE`, `SequentialFeatureSelector` |

To see whether selection works, the book appends 50 pure-noise features to the 30 breast-cancer features
and checks whether the methods recover the originals. We do the same.

### 2.1 Univariate statistics

Compute whether there is a statistically significant relationship between **each feature and the target**,
and keep the features with the highest confidence. For classification this is the analysis of variance
(ANOVA) F-test, `f_classif`. For regression use `f_regression`. For non-negative counts `chi2` is common.
The tests are **univariate**: each feature is judged on its own. A feature that is informative only in
combination with another one is discarded. In exchange, univariate tests are very fast and need no model.

`SelectKBest` keeps a fixed number $k$ of features. `SelectPercentile` keeps a fixed percentage.

```python-run
import numpy as np
from sklearn.datasets import load_breast_cancer
from sklearn.feature_selection import SelectPercentile, f_classif
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline

cancer = load_breast_cancer()
rng = np.random.RandomState(42)
noise = rng.normal(size=(len(cancer.data), 50))
X_w_noise = np.hstack([cancer.data, noise])            # first 30 real, last 50 noise
X_tr, X_te, y_tr, y_te = train_test_split(X_w_noise, cancer.target, random_state=0, test_size=0.5)

select = SelectPercentile(score_func=f_classif, percentile=50).fit(X_tr, y_tr)   # training data only
mask = select.get_support()
print("selected:", mask.sum(), "of", len(mask), "| real kept:", mask[:30].sum(), "/30 | noise kept:", mask[30:].sum(), "/50")

clf = lambda: make_pipeline(StandardScaler(), LogisticRegression(max_iter=5000))
print(f"all 80 features:      test accuracy = {clf().fit(X_tr, y_tr).score(X_te, y_te):.3f}")
print(f"selected 40 features: test accuracy = {clf().fit(select.transform(X_tr), y_tr).score(select.transform(X_te), y_te):.3f}")
```

`get_support()` returns a boolean mask of the kept features. Most of the real features are recovered and
most of the noise is removed, though not perfectly.

### 2.2 Model-based selection

Model-based selection uses a supervised model to judge the importance of each feature and keeps only the
most important ones. The model used for selection **need not be the model used for the final prediction**.
It must provide a measure of importance: tree-based models have `feature_importances_`, and linear models
have coefficients whose absolute values can be used. An L1-penalised linear model is a natural choice,
because it already sets many coefficients to zero.

Unlike univariate selection, model-based selection **considers all features at once**, so it can capture
interactions, if the model can.

```python-run
import numpy as np
from sklearn.datasets import load_breast_cancer
from sklearn.feature_selection import SelectFromModel
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

cancer = load_breast_cancer()
rng = np.random.RandomState(42)
X = np.hstack([cancer.data, rng.normal(size=(len(cancer.data), 50))])
X_tr, X_te, y_tr, y_te = train_test_split(X, cancer.target, random_state=0, test_size=0.5)

select = SelectFromModel(RandomForestClassifier(n_estimators=100, random_state=42), threshold="median").fit(X_tr, y_tr)
mask = select.get_support()
print("selected:", mask.sum(), "| real kept:", mask[:30].sum(), "/30 | noise kept:", mask[30:].sum(), "/50")
```

`threshold="median"` keeps the half of the features whose importance is above the median, so the result is
comparable with the 50% kept by `SelectPercentile` above.

### 2.3 Iterative selection

Iterative methods build a *series* of models with varying numbers of features. There are two basic
approaches: start with no features and add them one at a time, or start with all features and remove them
one at a time, until a stopping criterion is reached. Many models are built, so these methods are far more
expensive.

**Recursive feature elimination (RFE)** starts with all features, builds a model, and discards the least
important feature according to that model. It then builds a new model on the remaining features, and
repeats until the requested number is left. As with model-based selection, the model must provide
importances.

```python-run
import numpy as np
from sklearn.datasets import load_breast_cancer
from sklearn.feature_selection import RFE
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

cancer = load_breast_cancer()
rng = np.random.RandomState(42)
X = np.hstack([cancer.data, rng.normal(size=(len(cancer.data), 20))])
X_tr, X_te, y_tr, y_te = train_test_split(X, cancer.target, random_state=0, test_size=0.5)

rfe = RFE(RandomForestClassifier(n_estimators=40, random_state=42), n_features_to_select=10, step=5).fit(X_tr, y_tr)
mask = rfe.get_support()
print("selected 10 | real kept:", mask[:30].sum(), "| noise kept:", mask[30:].sum())
print("ranking_ of the first 10 features (1 = selected):", rfe.ranking_[:10])
print("test accuracy using RFE's internal model:", round(rfe.score(X_te, y_te), 3))
```

### When does selection help?

The book's guidance: if you are unsure what to use as input to your models, automatic feature selection
can be quite helpful. It is also good for reducing the number of features, either to **speed up
prediction** or to get **more interpretable models**. In most real-world cases, though, feature selection
is unlikely to produce large gains in accuracy. It remains a valuable tool for the feature engineer.

> [!WARNING]
> **Feature selection is a classic source of leakage.** Selecting the features most correlated with the
> target on the *full* dataset and then cross-validating a model on those features gives wildly optimistic
> scores. This happens even on pure noise. Selection must be a step *inside* the cross-validation loop,
> which means inside a `Pipeline` (module 6).

## 3. Utilising expert knowledge

Feature engineering is often where **expert knowledge** enters a model. ML aims to avoid hand-written
rules, but that does not mean prior knowledge should be thrown away. Domain experts can often point to
useful features that are far more informative than the raw data.

The book's example is travel-agent pricing. Flight prices peak around school holidays and public holidays.
Some holidays have fixed dates, but others depend on the lunar calendar or are set by authorities. A model
cannot learn those from the date alone, and it is easy to add a feature saying whether a flight falls in
a holiday period.

### Case study: Citi Bike rentals

The task: predict, for a given date and time, how many people will rent a bicycle in front of the
author's house. The data is the number of rentals in each three-hour interval over a month. The first 23
days are used for training and the last 8 for testing, a **time-based split** because this is a
forecasting problem.

The first attempt uses the only obvious feature, the POSIX timestamp, a single integer. A random forest
then predicts a flat line and gets a negative $R^2$. The reason is that the test timestamps are all later
than any training timestamp, and **trees cannot extrapolate** beyond the range of features they have seen.

This is where expert knowledge comes in. Looking at the data, two factors stand out: the **time of day**
and the **day of the week**. The book's sequence of experiments:

| features | model | test $R^2$ (book) |
|---|---|---|
| POSIX time | random forest | −0.04 |
| hour of day | random forest | 0.60 |
| hour + day of week | random forest | 0.84 |
| hour + day of week (as integers) | linear regression | 0.13 |
| one-hot hour + one-hot day | ridge | 0.62 |
| one-hot + **interaction** hour × day | ridge | 0.85 |

The linear model does badly on the integer features because it must treat hour-of-day as a continuous,
*linear* effect. One-hot encoding fixes that. Adding interaction features lets the model learn a separate
coefficient for each combination of day and time, and it then matches the random forest. It also has an
advantage: the coefficients can be read to see exactly what was learned.

We reproduce the idea on synthetic rental data:

```python-run
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.preprocessing import OneHotEncoder, PolynomialFeatures
from sklearn.pipeline import make_pipeline

rng = np.random.RandomState(0)
t = np.arange(31 * 8)                               # one month of 3-hour intervals
hour, dow = (t % 8) * 3, (t // 8) % 7
commute = np.where(dow < 5, np.isin(hour, [6, 9, 15, 18]) * 30, np.isin(hour, [12, 15]) * 12)
y = 5 + commute + rng.poisson(3, len(t))
n_train = 23 * 8                                    # first 23 days train, last 8 test

def evaluate(name, X, model):
    model.fit(X[:n_train], y[:n_train])
    print(f"{name:42s} test R2 = {model.score(X[n_train:], y[n_train:]):6.2f}")

rf = lambda: RandomForestRegressor(n_estimators=50, random_state=0)
evaluate("random forest on timestamp", t.reshape(-1, 1), rf())
evaluate("random forest on hour", hour.reshape(-1, 1), rf())
evaluate("random forest on hour + day of week", np.column_stack([hour, dow]), rf())
evaluate("ridge on hour + day (integers)", np.column_stack([hour, dow]), Ridge())
enc = OneHotEncoder(sparse_output=False)
evaluate("ridge on one-hot hour + day", np.column_stack([hour, dow]), make_pipeline(enc, Ridge()))
evaluate("ridge on one-hot + interactions", np.column_stack([hour, dow]),
         make_pipeline(enc, PolynomialFeatures(2, interaction_only=True, include_bias=False), Ridge()))
```

> [!INTERVIEW]
> **"How would you engineer features from a timestamp?"** Extract cyclical parts (hour, day of week, month,
> is-weekend, is-holiday), elapsed times ("days since the last purchase"), and lags and rolling aggregates
> of the target that use only *past* data. For linear models, one-hot encode or use sine/cosine encodings
> so that hour 23 is close to hour 0. Split by time, never randomly, to avoid training on the future.

## 4. A checklist for feature engineering

1. Look at distributions: skewed counts → `log1p`; outliers → clip, or use a robust scaler.
2. Encode categoricals in a way that suits the model (one-hot for linear, ordinal or native for trees).
3. Add domain features: ratios, differences, dates, aggregates per user or group.
4. For linear models, consider bins, polynomials and interactions, with regularisation.
5. Remove leaks: any feature not available at prediction time, or derived from the target.
6. Put every fitted step in a pipeline, so it is learned from training folds only.

## Summary

- `log`/`exp` transforms make skewed features more Gaussian. They are a big win for linear models and
  irrelevant for trees.
- Feature selection: univariate tests (fast, no interactions), model-based (`SelectFromModel`) and
  iterative (RFE). It helps speed and interpretability more than accuracy.
- Selection uses the labels, so fit it on training data only.
- Domain knowledge often beats algorithmic cleverness. Decomposing a timestamp turned a useless model into
  a good one.

```quiz
[
  {"q": "Which model is unaffected by replacing a feature x with log(x + 1)?", "options": ["A decision tree", "Ridge regression", "An MLP", "A linear SVM"], "answer": 0,
   "explain": "A monotonic transform preserves the order of values, which is all that tree splits depend on."},
  {"q": "Why is log(x + 1) often applied to count features for linear models?", "options": ["It makes the skewed distribution more symmetric and reduces the influence of very large values", "It converts counts to categories", "It removes all zeros from the data", "It makes the feature binary"], "answer": 0,
   "explain": "Counts are typically heavy-tailed; the log compresses the tail and makes relations closer to linear."},
  {"q": "A limitation of univariate feature selection is that…", "options": ["it judges each feature alone, so features useful only in combination are discarded", "it requires training many models", "it cannot be used for classification", "it needs the test labels"], "answer": 0,
   "explain": "Univariate tests ignore interactions between features."},
  {"q": "What does RFE do?", "options": ["Repeatedly fits a model and removes the least important features until the target number remains", "Adds random features to test robustness", "Selects features with the highest variance", "Projects features onto principal components"], "answer": 0,
   "explain": "Recursive feature elimination is a backward, model-driven iterative method."},
  {"q": "Why did the random forest fail when given only the POSIX timestamp for bike-rental forecasting?", "options": ["Test timestamps lie outside the training range and trees cannot extrapolate", "Random forests cannot handle integers", "The timestamp was not scaled", "There were too many trees"], "answer": 0,
   "explain": "All test times are later than any training time, so every test point falls into the last leaf."},
  {"q": "Selecting the 'best' features using the whole dataset and then cross-validating a model on them…", "options": ["leaks label information and gives over-optimistic scores", "is the recommended practice", "only affects training speed", "is harmless if the model is linear"], "answer": 0,
   "explain": "The selection step has already seen the validation folds' labels; it must happen inside each CV split."},
  {"q": "In the bike example, why did one-hot encoding the hour help ridge regression?", "options": ["It lets the model learn a separate effect per hour instead of a single linear trend", "It reduced the number of features", "It made the target Gaussian", "It removed weekends from the data"], "answer": 0,
   "explain": "As an integer, hour can only have a linear effect; rentals peak at commute times, which is not linear in the hour."}
]
```

> **Source:** Müller & Guido, *Introduction to Machine Learning with Python*, ch. 4 ("Univariate Nonlinear Transformations", "Automatic Feature Selection": univariate statistics, model-based feature selection, iterative feature selection; "Utilizing Expert Knowledge"); scikit-learn User Guide, "Feature selection".
