# Nonlinear transforms, feature selection and expert knowledge

> **Before this lesson:** read [Categorical features, binning and polynomials](#/lesson/ml/feature-engineering) first: this lesson uses one-hot encoding, interaction features and `PolynomialFeatures` from there. You should also recognise ridge and lasso regression from [Linear models](#/lesson/ml/linear-models) and random forests with their `feature_importances_` from [Naive Bayes, decision trees and ensembles](#/lesson/ml/bayes-trees-ensembles). Each is re-described in a sentence when it appears.

## In plain words

The previous lesson turned raw facts into columns. This one asks three follow-up questions. First, is each numeric column in a shape the model can use, or should it be bent, for example with a logarithm? Second, now that we can create columns cheaply, which of them are worth keeping? Third, what does a person who knows the subject know that the data does not show directly?

An everyday picture: you are packing for a trip with a suitcase of limited size. Some items need reshaping to fit (rolling clothes instead of folding them is the "transform"). Some items are not worth their space at all (that is "feature selection"). And a friend who has been to the place tells you to take a raincoat, because it rains every afternoon there, something you would never guess from a weather average (that is "expert knowledge").

Why this matters for a job: real datasets contain skewed money and count columns, hundreds of candidate features of mixed quality, and timestamps that hide daily and weekly rhythms. Knowing when a log transform helps, how to drop useless columns without cheating, and how to turn a date into useful features is everyday work, and "how would you engineer features from a timestamp?" is a standard interview question.

## 1. Univariate nonlinear transformations

A **univariate transformation** changes one feature at a time by applying a mathematical function to every value in the column, for example replacing each value $x$ by $\log x$, by $e^x$ (written `exp`) or by $\sin x$. The previous lesson added squares and cubes; these are further functions of the same kind.

Whether such a transform helps depends on the model:

- **Tree models do not care.** A decision tree only asks questions of the form "is $x$ below 7.5?", so all it uses is the *order* of the values. A **monotonic** transform is one that never changes the order (if $a < b$ then $f(a) < f(b)$), and $\log$ and $\exp$ are monotonic. The tree's splits move to the transformed thresholds, and its predictions stay exactly the same.
- **Linear models, nearest neighbours, support vector machines and neural networks care a lot.** They use the actual numeric values: in sums, in distances, in dot products. A feature whose relationship with the target is curved, or whose values are spread very unevenly, makes them work badly.

### Skewed data and the Gaussian ideal

Many models work best when each feature, and in regression the target too, is roughly **Gaussian**: distributed in the bell shape of the normal distribution, symmetric around its average, with few extreme values. Real data often is not. A distribution is **skewed** when it has a long tail on one side, many small values and a handful of very large ones.

The classic case is **count data**: how many times something happened, such as how many times a user logged in this month. A count cannot be negative, most users have small counts, and a few heavy users have huge ones. A linear model fitted on such a column is dominated by the few extreme rows.

The **logarithm** fixes much of this. In words, $\log x$ tells you roughly how many times you must multiply by a fixed base to reach $x$, so it turns multiplication into addition and compresses large values much more than small ones. Because $\log 0$ is undefined (it goes to minus infinity) and counts are often zero, we use $\log(1 + x)$ instead, available in NumPy as `np.log1p(x)`:

$$x' = \log(1 + x).$$

A worked example with the natural logarithm: the counts 0, 1, 10, 100 and 1,000 become 0, 0.69, 2.40, 4.62 and 6.91. The gap between 100 and 1,000 was 900 and is now 2.3; the gap between 0 and 1 was 1 and is still 0.69. Large values are pulled in towards the rest.

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

**Reading this code line by line**

- `X_org` is 1,000 rows of three normally distributed hidden values, and `w` is three random weights.
- `rng.poisson(10 * np.exp(X_org))` turns each hidden value into a count. A **Poisson** draw produces a random whole number around a given average; here the average is $10e^{x}$, which is small for most rows and very large for a few. This builds skewed count features, the kind you get from real logs.
- `y = X_org @ w` makes the target a weighted sum of the *hidden* values (the `@` symbol is matrix multiplication, here a weighted sum per row). So the target is linear in the logarithm of the counts, not in the counts themselves.
- The `print` line summarises feature 0: the median is 10, the maximum 140, and 48% of values are below 10. Half the data is squeezed into a small range while the tail stretches far out.
- The last two lines fit a `Ridge` regression (linear regression with a small penalty on large weights) once on the raw counts and once on $\log(X + 1)$, and print the test $R^2$.

The raw counts give a test $R^2$ of about 0.62 and the log-transformed counts about 0.88, the same numbers as the book's version of this experiment. Nothing about the model changed; only the shape of its input did.

Points to remember:

- Use `np.log1p(x)`, which computes $\log(1+x)$, when zeros are present.
- Usually only some features need transforming, and different features may need different transforms. Finding the right ones is partly judgement: look at each column's distribution and at how it relates to the target.
- It can also help to transform the **target** in regression, for prices or counts especially. Fit the model on $\log(1 + y)$, then convert predictions back with the inverse function `np.expm1`, which computes $e^x - 1$. scikit-learn's `TransformedTargetRegressor` wraps both steps so they cannot be forgotten.
- These transforms are irrelevant to tree models. They matter most for linear models, and can matter for support vector machines, nearest neighbours and neural networks.

More broadly, the techniques of the last two lessons (binning, polynomials, interactions, transforms) can change a linear model or naive Bayes dramatically, sometimes help kernel methods and neural networks, and rarely help trees, which discover thresholds and interactions on their own.

## 2. Automatic feature selection

Creating features is easy, so it is tempting to make a table far wider than the original. More features make a model more complex, which raises the risk of overfitting: with enough columns, some will match the training labels by pure chance. **Feature selection** means keeping only the most useful features and discarding the rest. The reward is a simpler model that often generalises better, trains and predicts faster, and is easier to explain.

There are three basic strategies. All of them are **supervised**: they look at the target to decide which features are useful. That has a serious consequence. Because they use the labels, they must be fitted **on the training data only**, or they leak information about the test labels into the model (the warning box below demonstrates how badly).

| strategy | idea | scikit-learn |
|---|---|---|
| univariate statistics | score each feature on its own against the target | `SelectKBest`, `SelectPercentile` |
| model-based selection | fit one model and keep the features it relies on most | `SelectFromModel` |
| iterative selection | fit a series of models, adding or removing features step by step | `RFE`, `SequentialFeatureSelector` |

To check whether selection works, the experiments below take the breast-cancer data (30 real measurements of tumours) and glue 50 columns of pure random noise onto it. A good method should keep the real columns and throw away the noise.

### 2.1 Univariate statistics

**Univariate** means "one variable at a time". This strategy computes, for each feature separately, a **statistic**: a single number summarising how strongly that feature is related to the target. It then keeps the features with the best scores.

For classification the usual statistic is the **ANOVA F-statistic** (ANOVA stands for analysis of variance), computed by `f_classif`. In words, it asks: are the class averages of this feature far apart compared with how much the values scatter within each class? Far-apart averages with little scatter give a large F; overlapping classes give an F near zero. As a formula, with $k$ classes, $n$ samples, class averages $\bar x_c$, class sizes $n_c$ and overall average $\bar x$:

$$F = \frac{\sum_c n_c(\bar x_c - \bar x)^2 \,/\, (k-1)}{\sum_c \sum_{i \in c}(x_i - \bar x_c)^2 \,/\, (n-k)}$$

The top measures the spread *between* the class averages; the bottom measures the spread *within* the classes. Worked example: class 0 has feature values 1, 2, 3 (average 2) and class 1 has 5, 6, 7 (average 6), so the overall average is 4. Between: $3(2-4)^2 + 3(6-4)^2 = 24$, divided by $k - 1 = 1$ gives 24. Within: $(1 + 0 + 1) + (1 + 0 + 1) = 4$, divided by $n - k = 4$ gives 1. So $F = 24/1 = 24$, a strong feature. A feature whose class averages are equal, such as values 1, 7, 4 in class 0 and 2, 6, 4 in class 1 (both average 4), gets $F = 0$.

```python-run
import numpy as np
from sklearn.feature_selection import f_classif
x = np.array([[1.], [2.], [3.], [5.], [6.], [7.]])
y = np.array([0, 0, 0, 1, 1, 1])
F, p = f_classif(x, y)
print("separated feature: F =", F.round(2), " p-value =", p.round(4))
noise = np.array([[1.], [7.], [4.], [2.], [6.], [4.]])
F2, p2 = f_classif(noise, y)
print("useless feature:   F =", F2.round(2), " p-value =", p2.round(2))
```

`f_classif(x, y)` returns two arrays with one entry per feature: the F-statistic and the **p-value**, the probability of seeing an F at least this large if the feature had no real relationship with the target. The output confirms the hand calculation: F = 24 with a p-value of about 0.008 for the separated feature, and F = 0 with a p-value of 1 for the useless one. A small p-value means "unlikely to be chance".

For regression the corresponding function is `f_regression`, and for non-negative counts such as word counts `chi2` (the chi-squared test) is common. All of these judge each feature in isolation, which has a cost and a benefit. The cost: a feature that is only informative *in combination* with another (the interaction case from the previous lesson) looks useless on its own and gets discarded. The benefit: the tests are very fast and need no model.

`SelectKBest` keeps a fixed number $k$ of features; `SelectPercentile` keeps a fixed percentage of them.

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

**Reading this code line by line**

- `np.hstack([cancer.data, noise])` places the 50 noise columns to the right of the 30 real ones, so columns 0–29 are real and 30–79 are noise. Half the rows are held back for testing.
- `SelectPercentile(score_func=f_classif, percentile=50)` will keep the 50% of features with the highest F-scores. `.fit(X_tr, y_tr)` computes the scores from the training rows only.
- `select.get_support()` returns a **boolean mask**: an array of 80 `True`/`False` values, `True` for each kept feature. Summing a boolean array counts the `True` entries, so `mask[:30].sum()` is the number of real features kept.
- `clf` is a small function that builds a fresh scaler-plus-logistic-regression model each time it is called. The last two lines train one on all 80 columns and one on the 40 selected columns (`select.transform` keeps only those), and print test accuracy.

The output shows 40 of 80 features selected, 26 of the 30 real ones kept and 14 of the 50 noise columns kept. Selection is good but imperfect: with 285 training rows, a few noise columns look related to the labels by chance. Test accuracy rises from 0.954 with all features to 0.965 with the selected ones, because the model has fewer chance patterns to latch onto.

### 2.2 Model-based selection

**Model-based selection** fits one supervised model, reads off how much each feature matters to it, and keeps the top-ranked features. The selecting model does **not** have to be the model you use for the final prediction; its only job is to rank. It must provide a measure of importance:

- Tree-based models such as random forests have `feature_importances_`: for each feature, how much the splits on it improved the tree's predictions, averaged over the forest.
- Linear models have coefficients, and the size of a coefficient (its absolute value, on scaled features) indicates how much the feature matters. An **L1-penalised** linear model such as lasso is a natural choice, because its penalty pushes many coefficients to exactly zero, which is a selection in itself.

Unlike univariate tests, this approach considers **all features together**, so it can keep features that matter only in combination, provided the selecting model can capture such combinations.

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

`SelectFromModel(model, threshold="median")` fits the forest, then keeps every feature whose importance is above the median importance, which is half of them, so the result is comparable with the 50% kept above. The output shows 28 of the 30 real features kept and 12 noise columns, slightly better than the univariate test.

### 2.3 Iterative selection

**Iterative selection** builds a whole *series* of models, each on a different set of features. There are two directions. **Forward selection** starts with no features and adds the single most helpful one at each step. **Backward elimination** starts with all features and removes the least helpful one at each step. Either way, it stops when the requested number of features is reached. Since many models are trained, these methods are far more expensive than the other two.

**Recursive feature elimination (RFE)** is the best-known backward method. It fits a model on all features, drops the feature (or the few features) that the model ranks as least important, refits on the remainder, and repeats until the requested number is left. As with model-based selection, the model must provide importances or coefficients.

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

**Reading this code line by line**

- This time 20 noise columns are added (to keep the run short), giving 50 columns.
- `RFE(model, n_features_to_select=10, step=5)` removes 5 features per round until 10 remain. With 50 features that is 8 elimination rounds plus one final fit on the 10 survivors, so 9 forests are trained.
- `rfe.ranking_` gives each feature the round in which it was eliminated, counted backwards: 1 means "kept to the end", 2 means "removed in the last round", and so on. The first ten real features get ranks such as `[3 2 1 1 7 3 1 1 4 7]`.
- `rfe.score(X_te, y_te)` uses the forest fitted on the final 10 features to score the test set.

The output shows all 10 selected features are real and none is noise, with test accuracy around 0.94 from only a third of the real features. **Sequential feature selection** (`SequentialFeatureSelector`) is the more general cousin: it can run forward or backward and judges each candidate set by a cross-validated score rather than by importances, at an even higher cost.

### When does selection help?

When you are not sure which inputs a model should get, automatic selection is a useful aid. It is also a practical way to cut the number of features in order to **speed up prediction**, or to get a **model people can read**. On real problems, though, it rarely yields large gains in accuracy; regularisation already protects most models from moderate numbers of weak features.

> [!WARNING]
> **Feature selection is a classic source of leakage.** **Leakage** means information about the answers reaches the model in a way that will not be possible on real future data. If you pick the features most related to the target using the *whole* dataset, then cross-validate a model on those features, the selection step has already seen the labels of every validation fold. The scores come out wildly optimistic, even on pure noise, as the demo below shows. Selection must happen *inside* each training fold, which in practice means inside a `Pipeline` (module 6).

```python-run
import numpy as np
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score
from sklearn.pipeline import make_pipeline

rng = np.random.RandomState(0)
X = rng.normal(size=(60, 2000))        # 60 samples, 2000 columns of pure noise
y = rng.randint(0, 2, 60)              # random labels: nothing to learn

X_best = SelectKBest(f_classif, k=20).fit_transform(X, y)      # WRONG: selection sees every label
wrong = cross_val_score(LogisticRegression(), X_best, y, cv=5).mean()
right = cross_val_score(make_pipeline(SelectKBest(f_classif, k=20), LogisticRegression()), X, y, cv=5).mean()
print(f"select on all data, then CV:   accuracy = {wrong:.2f}")
print(f"selection inside each CV fold: accuracy = {right:.2f}")
```

**Reading this code line by line**

- `X` is 60 rows of 2,000 random numbers and `y` is 60 random 0/1 labels. There is nothing real to learn, so an honest score must be near 50%, the rate of guessing.
- The "wrong" line selects the 20 columns most related to `y` using all 60 rows, then cross-validates a logistic regression on those 20 columns. `cross_val_score(..., cv=5)` splits the rows into 5 parts, trains on 4 and tests on the fifth, five times over, and we average the five accuracies (lesson 50 covers this in detail).
- The "right" line puts the selector and the model in one pipeline, so each of the five training runs selects its own 20 columns from its own training rows only.

The wrong approach reports about 92% accuracy on random noise; the right one reports about 40%, which is chance level give or take the randomness of 60 rows. Out of 2,000 random columns, some match 60 random labels well by luck. When the selection has seen the validation rows, it picks exactly the columns that are lucky *on those rows*.

## 3. Utilising expert knowledge

Feature engineering is often where **domain knowledge** (also called expert knowledge: what people who work in the field know) enters a model. Machine learning aims to avoid hand-written rules, but that does not mean throwing away what experts know. They can often point to features far more informative than anything in the raw data.

A travel example: flight prices are high around school holidays and public holidays. Some holidays fall on fixed dates, but others follow the lunar calendar or are set each year by authorities. A model that only sees the date cannot learn these from a few years of data, but adding a column "is this date inside a holiday period?" is easy for anyone who knows the calendar.

### Case study: bike rentals

The book's case study uses data from New York's Citi Bike scheme. The task is to predict, for a given date and time, how many bikes will be rented from one station. The data is the number of rentals in each three-hour interval over one month. The first 23 days are used for training and the last 8 for testing. That is a **time-based split**: in a forecasting problem the model will always be predicting the future from the past, so the test must be later than the training data.

The first attempt uses the only feature that comes with the data: the time itself, as a **POSIX timestamp**, the number of seconds since 1 January 1970, a single growing integer. A random forest on this feature predicts a flat line and scores a negative $R^2$ (worse than predicting the average). The reason is general and important: every test timestamp is later than every training timestamp, and **trees cannot extrapolate**. A tree's prediction for any value beyond the training range is whatever its last leaf predicts, so all test points get the same answer.

Here knowledge helps. Anyone looking at bike rentals would guess that the **hour of the day** (commuting peaks) and the **day of the week** (weekends differ) drive demand. The book's sequence of experiments:

| features | model | test $R^2$ (book) |
|---|---|---|
| POSIX time | random forest | −0.04 |
| hour of day | random forest | 0.60 |
| hour + day of week | random forest | 0.84 |
| hour + day of week (as integers) | linear regression | 0.13 |
| one-hot hour + one-hot day | ridge | 0.62 |
| one-hot + **interaction** hour × day | ridge | 0.85 |

The linear model does badly on integer features because it has to treat the hour as a straight-line effect, "each extra hour adds the same amount", when rentals actually peak in the morning and evening. One-hot encoding gives each hour its own weight, as the previous lesson explained. The interaction features (one product column for each hour and day combination) let the model learn a separate value for, say, Saturday at 9am and Monday at 9am. It then matches the random forest, with an extra advantage: each coefficient can be read to see what it learned.

We reproduce the idea on generated rental data with a weekday commuting pattern and a weekend lunchtime pattern:

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

**Reading this code line by line**

- `t` counts the 248 three-hour intervals of a 31-day month. `t % 8` is the position within a day (0 to 7), times 3 gives the hour (0, 3, ..., 21); `t // 8` is the day number and `% 7` turns it into a day of the week, 0 to 6.
- `commute` sets the pattern: on weekdays (`dow < 5`) 30 extra rentals at 6, 9, 15 and 18 o'clock; at weekends 12 extra at 12 and 15 o'clock. `np.isin(hour, [...])` is `True` where the hour is in the list, and multiplying by 30 turns `True` into 30 and `False` into 0. Random Poisson noise is added on top.
- `evaluate` trains on the first 23 days and prints the test $R^2$ on the last 8. `reshape(-1, 1)` turns a plain list into a one-column table.
- The six calls repeat the book's six experiments.

The output runs: about −0.02 on the timestamp, 0.62 on the hour, 0.99 on hour plus weekday for the forest; 0.12 for ridge on integer codes, 0.74 after one-hot encoding, and 0.96 with interactions. The same story as the book: the right features turn a useless model into a good one, and the right *representation* of those features brings a linear model up to the forest's level.

### Cyclical features

A clock wraps around: 23:00 is one hour from midnight, yet as numbers 23 and 0 are as far apart as they can be. For linear models and neural networks a common fix is a **cyclical encoding**: place each hour on a circle and use the two coordinates of that point as features,

$$x_{\sin} = \sin\!\left(\frac{2\pi h}{24}\right), \qquad x_{\cos} = \cos\!\left(\frac{2\pi h}{24}\right).$$

Worked example: hour 0 becomes $(0, 1)$, hour 6 becomes $(1, 0)$, hour 12 becomes $(0, -1)$ and hour 23 becomes $(-0.259, 0.966)$. The straight-line distance between hour 23 and hour 0 is now about 0.26, while hour 12, the opposite side of the clock, is at distance 2 from hour 0. Two columns describe the whole cycle smoothly. The same trick works for day of the week (divide by 7) and month (divide by 12).

> [!INTERVIEW]
> **"How would you engineer features from a timestamp?"** Extract the cyclical parts (hour, day of week, month, is-weekend, is-holiday), elapsed times ("days since the last purchase"), and **lags** (the target's value one day or one week earlier) and **rolling aggregates** (the average over the last seven days) computed from *past* data only. For linear models, one-hot encode the cyclical parts or use sine/cosine encodings so that hour 23 is close to hour 0. Split by time, never randomly, so that the model is never trained on the future.

## 4. A checklist for feature engineering

1. Look at the distributions: skewed counts or amounts suggest `log1p`; extreme outliers suggest clipping or a robust scaler (lesson 30).
2. Encode categoricals in a way that suits the model: one-hot for linear models, ordinal codes or native categorical support for tree ensembles.
3. Add domain features: ratios (price per square metre), differences, date parts, and aggregates per user or group.
4. For linear models, consider bins, polynomials and interactions, together with regularisation.
5. Remove leaks: any feature not available at the moment of prediction, or computed from the target.
6. Put every fitted step (encoders, scalers, selectors) in a pipeline, so that it is learned from training folds only.

## Summary

- Monotonic transforms such as `log1p` make skewed features more symmetric. They are a big win for linear models and irrelevant to trees.
- Feature selection has three families: univariate tests (fast, blind to combinations), model-based selection (`SelectFromModel`) and iterative selection (RFE, sequential selection). It helps speed and readability more often than accuracy.
- Selection uses the labels, so it must be fitted on training data only, ideally inside a pipeline; otherwise even pure noise looks predictive.
- Domain knowledge often beats algorithmic cleverness: splitting a timestamp into hour and weekday turned a useless model into a good one.
- Trees cannot extrapolate beyond the range of the training data.

## Glossary

- **Univariate transformation**: applying a function such as $\log$ to every value of one feature.
- **Monotonic**: never changing the order of values; if $a < b$ then $f(a) < f(b)$.
- **Gaussian (normal) distribution**: the symmetric bell-shaped distribution.
- **Skewed**: a distribution with a long tail on one side.
- **Count data**: non-negative whole numbers recording how often something happened.
- **Feature selection**: keeping only the most useful features.
- **Statistic**: a single number summarising some property of the data.
- **ANOVA F-statistic**: between-class spread divided by within-class spread; large means the feature separates the classes.
- **p-value**: the probability of a result at least this extreme if there were no real relationship.
- **Boolean mask**: an array of True/False values marking which items to keep.
- **Model-based selection**: keeping the features a fitted model ranks as most important.
- **Recursive feature elimination (RFE)**: repeatedly fitting a model and removing its least important features.
- **Forward selection / backward elimination**: adding the best feature / removing the worst feature, one step at a time.
- **Leakage**: information about the answers reaching the model in a way that is impossible on real future data.
- **Domain (expert) knowledge**: what practitioners in the field know about how the data arises.
- **Time-based split**: training on earlier data and testing on later data.
- **Extrapolate**: predict beyond the range of values seen in training.
- **Cyclical encoding**: representing a repeating quantity such as the hour by its sine and cosine.
- **Lag / rolling aggregate**: a past value of the target / a summary such as the mean over a recent window.

## Check yourself

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
   "explain": "As an integer, hour can only have a linear effect; rentals peak at commute times, which is not linear in the hour."},
  {"q": "Class 0 has feature values 1, 2, 3 and class 1 has 5, 6, 7. What is the ANOVA F-statistic?", "options": ["24", "4", "1", "0"], "answer": 0,
   "explain": "Between-class spread 3(2−4)² + 3(6−4)² = 24 over k−1 = 1; within-class spread 4 over n−k = 4 gives 1; F = 24/1."}
]
```

> **Source:** Müller & Guido, *Introduction to Machine Learning with Python*, ch. 4 ("Univariate Nonlinear Transformations", "Automatic Feature Selection": univariate statistics, model-based feature selection, iterative feature selection; "Utilizing Expert Knowledge"); scikit-learn User Guide, "Feature selection".
