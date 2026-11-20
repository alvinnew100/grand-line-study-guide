# Unsupervised learning, preprocessing and scaling

Chapter 3 of Müller & Guido turns to **unsupervised learning**: algorithms that get only input data, with
no labels, and must extract knowledge from it. This lesson introduces the two kinds of unsupervised
learning and its main difficulty. It then covers the most common unsupervised step in real pipelines:
**rescaling features**.

## 1. Two kinds of unsupervised learning

**Unsupervised transformations** create a new representation of the data that is easier for humans or
other algorithms to use than the original.

- *Dimensionality reduction* takes a high-dimensional representation and summarises its essential
  characteristics in fewer features. A common use is reducing to two dimensions for visualisation.
- *Finding the parts or components* that make up the data. An example is topic extraction from text, where
  each document is treated as a mix of unknown topics.

**Clustering algorithms** partition data into groups of similar items. An example is grouping photos on a
social site by the person who appears in them, without knowing who anyone is or how many people there are.

## 2. The challenge: did it learn anything useful?

Because there are no labels, **we don't know what the right output should be**, and so it is hard to say
whether an algorithm "did well". A clustering algorithm might group faces by whether they are in profile or
frontal, when you wanted them grouped by identity. Nothing tells the algorithm what you are looking for.
Often the only evaluation is to inspect the results by hand.

For this reason unsupervised methods are used mostly in an **exploratory** setting, when a data scientist
wants to understand the data better, and less often in a fully automatic system. Their other common use is
as a **preprocessing step for supervised learning**. A new representation can improve accuracy or cut
memory and time. Scaling is the simplest such step, and it is "unsupervised" in the sense that it never
looks at the labels.

## 3. Why scale?

Some algorithms care about the *numeric size* of features:

| sensitive to scale | not sensitive |
|---|---|
| k-NN, k-means, DBSCAN (distances) | decision trees |
| SVMs (kernels are distance/dot-product based) | random forests |
| regularised linear models (penalty treats all weights alike) | gradient boosted trees |
| neural networks (gradient descent conditioning) | naive Bayes (per-feature statistics) |
| PCA (variance is scale-dependent) | |

If one feature is an income in dollars (range in the tens of thousands) and another an age (range in the
tens), Euclidean distance is almost entirely the income difference. Scaling puts the features on an equal
footing.

## 4. Four kinds of scaling

The book compares four transformers from `sklearn.preprocessing`:

| scaler | what it does | notes |
|---|---|---|
| `StandardScaler` | each feature gets mean 0 and variance 1: $z = (x-\mu)/\sigma$ | does not bound the values; outliers still influence $\mu$ and $\sigma$ |
| `RobustScaler` | uses the median and quartiles: $(x-\text{median})/\text{IQR}$ | ignores **outliers** (measurement errors, very different points) |
| `MinMaxScaler` | shifts each feature to lie exactly in $[0,1]$: $(x-\min)/(\max-\min)$ | one outlier squashes everything else |
| `Normalizer` | scales each **row** (sample) to unit Euclidean length | projects points onto a sphere; use when only the *direction* matters |

The first three work per **column**. `Normalizer` works per **row** and is a different kind of operation.

```python-run
import numpy as np
from sklearn.preprocessing import StandardScaler, RobustScaler, MinMaxScaler, Normalizer

X = np.array([[1.0, 100.0], [2.0, 110.0], [3.0, 120.0], [4.0, 130.0], [50.0, 140.0]])   # 50 is an outlier
for scaler in [StandardScaler(), RobustScaler(), MinMaxScaler(), Normalizer()]:
    Z = scaler.fit_transform(X)
    print(f"{type(scaler).__name__:15s} first column -> {Z[:, 0].round(2)}")
```

Look at the first four values under each scaler. `MinMaxScaler` crushes them into $[0, 0.06]$ because of
the outlier. `RobustScaler` keeps them nicely spread.

## 5. Applying a transformation: fit on train, transform both

Scalers follow the estimator API. `fit` learns the statistics, and `transform` applies them.

```python-run
import numpy as np
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler

X, y = load_breast_cancer(return_X_y=True)
X_train, X_test, y_train, y_test = train_test_split(X, y, random_state=1)

scaler = MinMaxScaler()
scaler.fit(X_train)                      # learns min and max of each feature on the TRAINING set (no y!)
X_train_scaled = scaler.transform(X_train)
X_test_scaled = scaler.transform(X_test)

print("train: min", X_train_scaled.min(axis=0)[:4].round(2), " max", X_train_scaled.max(axis=0)[:4].round(2))
print("test:  min", X_test_scaled.min(axis=0)[:4].round(2), " max", X_test_scaled.max(axis=0)[:4].round(2))
```

After scaling, the training features are exactly in $[0,1]$. The **test features are not**. Some fall
below 0 or above 1. This is correct and expected: `transform` always subtracts the *training* minimum and
divides by the *training* range, and the test set has slightly different extremes.

## 6. Scale training and test data the same way

The book makes a point of what goes wrong if you fit a separate scaler on the test set. Each set is
stretched to fill $[0,1]$ on its own, so the test points move relative to the training points. A test
point that is identical to a training point would get different coordinates. The arrangement of the data
has been changed arbitrarily, and the model's learned boundary no longer applies.

```python-run
import numpy as np
from sklearn.preprocessing import MinMaxScaler
train = np.array([[0.0], [5.0], [10.0]])
test = np.array([[5.0], [7.0]])                 # 5.0 also appears in the training set

right = MinMaxScaler().fit(train)
print("correct:  train 5.0 ->", right.transform([[5.0]])[0], " test 5.0 ->", right.transform(test)[0])
wrong = MinMaxScaler().fit(test)                # WRONG: separate statistics for the test set
print("wrong:    train 5.0 ->", right.transform([[5.0]])[0], " test 5.0 ->", wrong.transform(test)[0])
```

> [!WARNING]
> **Never call `fit` (or `fit_transform`) on the test set.** Never fit the scaler on the full dataset
> before splitting or before cross-validation either. That leaks information about the test fold into
> training. Module 6 (Pipelines) shows how to make this mistake impossible.

**Shortcut.** `scaler.fit_transform(X_train)` does both steps in one call and can be more efficient. Use it
on the training set, then plain `transform` on the test set.

## 7. The effect on supervised learning

On the breast-cancer data, an RBF SVM improves once the features are scaled. (With the kernel settings
used in the book's edition of scikit-learn the jump was far larger, from about 63% to 97%; see lesson 2.4.)

```python-run
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler, StandardScaler, RobustScaler
from sklearn.svm import SVC

X, y = load_breast_cancer(return_X_y=True)
X_tr, X_te, y_tr, y_te = train_test_split(X, y, random_state=0)
print(f"{'no scaling':15s} test accuracy = {SVC(C=100).fit(X_tr, y_tr).score(X_te, y_te):.3f}")
for scaler in [MinMaxScaler(), StandardScaler(), RobustScaler()]:
    s = scaler.fit(X_tr)
    acc = SVC(C=100).fit(s.transform(X_tr), y_tr).score(s.transform(X_te), y_te)
    print(f"{type(scaler).__name__:15s} test accuracy = {acc:.3f}")
```

Swapping one scaler for another is a one-line change, because they share the same interface. Which scaler
is best depends on the data, so treat it as a hyperparameter if it matters.

## 8. Standardisation by hand

It is worth knowing exactly what `StandardScaler` computes, because interviewers ask and because you
implement it in *ml-standard-scaler*:

$$\mu_j = \frac1n\sum_i x_{ij},\qquad \sigma_j = \sqrt{\frac1n\sum_i (x_{ij}-\mu_j)^2},\qquad z_{ij} = \frac{x_{ij}-\mu_j}{\sigma_j}.$$

scikit-learn uses the **population** standard deviation (divide by $n$), stores the results in `mean_` and
`scale_`, and replaces a zero standard deviation by 1 so that constant features don't cause a division by
zero.

```python-run
import numpy as np
from sklearn.preprocessing import StandardScaler
rng = np.random.RandomState(0)
X_train = rng.normal(loc=[10, 200], scale=[2, 50], size=(100, 2))
X_test = rng.normal(loc=[10, 200], scale=[2, 50], size=(20, 2))

mu, sigma = X_train.mean(axis=0), X_train.std(axis=0)       # ddof=0
manual = (X_test - mu) / sigma
sk = StandardScaler().fit(X_train)
print("mean_:", sk.mean_.round(2), " scale_:", sk.scale_.round(2))
print("manual == sklearn:", np.allclose(manual, sk.transform(X_test)))
print("test set mean after scaling (close to, but not exactly, 0):", manual.mean(axis=0).round(2))
```

## 9. Beyond linear scaling

Some preprocessing changes the *shape* of a distribution, not just its location and spread:

- `np.log1p` for heavy-tailed counts (module 4);
- `PowerTransformer` (Box-Cox / Yeo-Johnson) makes features more Gaussian;
- `QuantileTransformer` maps each feature to a uniform or normal distribution by rank;
- missing values need **imputation** before most models: `SimpleImputer` (mean, median, most frequent) or
  `KNNImputer`. Imputers are also fitted on the training data only.

> [!INTERVIEW]
> **"Normalisation vs standardisation, and when does it matter?"** Min-max normalisation maps to $[0,1]$
> and is sensitive to outliers. Standardisation gives zero mean and unit variance and is the usual default.
> It matters for distance-based models, kernel methods, regularised linear models, PCA and gradient-trained
> networks. It does not matter for tree-based models. Always compute the statistics on the training split
> only, and apply them to validation and test data.

## 10. Worked example: why scaling changes k-NN's neighbours

A calculation by hand shows the effect better than any accuracy figure. Take three people described by
age (years) and income (dollars):

| person | age | income |
|---|---|---|
| A | 25 | 50,000 |
| B | 60 | 51,000 |
| C | 27 | 58,000 |

Who is A's nearest neighbour? On the raw numbers,
$d(A,B) = \sqrt{35^2 + 1000^2} \approx 1000.6$ and $d(A,C) = \sqrt{2^2 + 8000^2} \approx 8000.0$. B wins
easily. A 35-year age gap counts for almost nothing, because income is measured in units a thousand times
larger. The distance is, in effect, the income difference.

Now standardise both features using the mean and standard deviation of a realistic population (age: mean
40, std 12; income: mean 55,000, std 15,000):

| person | age (z) | income (z) |
|---|---|---|
| A | −1.25 | −0.33 |
| B | 1.67 | −0.27 |
| C | −1.08 | 0.20 |

$d(A,B) = \sqrt{2.92^2 + 0.07^2} \approx 2.92$ and $d(A,C) = \sqrt{0.17^2 + 0.53^2} \approx 0.56$. Now C,
who is the same age and earns a little more, is the nearest neighbour. Neither answer is "true" in an
absolute sense. But the scaled version treats a typical difference in age and a typical difference in
income as equally important, which is almost always what you intend.

```python-run
import numpy as np
people = np.array([[25, 50000.0], [60, 51000.0], [27, 58000.0]])
mu, sigma = np.array([40.0, 55000.0]), np.array([12.0, 15000.0])
for name, data in [("raw", people), ("standardised", (people - mu) / sigma)]:
    d_ab, d_ac = np.linalg.norm(data[0] - data[1]), np.linalg.norm(data[0] - data[2])
    print(f"{name:13s} d(A,B)={d_ab:9.2f}  d(A,C)={d_ac:9.2f}  -> nearest to A is {'B' if d_ab < d_ac else 'C'}")
```

The same reasoning explains the other scale-sensitive models. An RBF kernel is a function of this
distance. A ridge penalty $\alpha\sum_j w_j^2$ punishes a weight of 0.001 on income far less than a
weight of 1.0 on age, though both may express an effect of the same size. And PCA finds the direction of
largest variance, which on raw data is simply the income axis.

## 11. Pitfalls and questions to ask

- **Scaling a sparse matrix.** Subtracting the mean makes every zero non-zero and can exhaust memory. For
  sparse data use `StandardScaler(with_mean=False)` or `MaxAbsScaler`, which keep zeros as zeros.
- **Scaling one-hot columns.** It is rarely needed, and it makes the features harder to read. Scale the
  numeric columns only, using a `ColumnTransformer` (module 6).
- **Scaling the target.** For regression with gradient-trained models it can help to standardise `y` too.
  Remember to transform the predictions back.
- **Outliers and `MinMaxScaler`.** One extreme value compresses all the others into a sliver of the
  range. Clip, use `RobustScaler`, or apply a log first.
- **New data outside the training range.** `MinMaxScaler` then produces values outside $[0,1]$. That is
  harmless for most models, but a model that assumes bounded inputs may behave oddly.
- **Trees do not need it, but it does no harm.** If a pipeline feeds both a linear model and a tree, you
  can scale once for both.
- **Persist the scaler with the model.** At prediction time you need the *training* mean and standard
  deviation. Saving the fitted pipeline as one object is the reliable way to keep them together.

A quick way to decide whether scaling matters for your model is to ask: *would the predictions change if
I measured one feature in different units?* For k-NN, SVMs, regularised linear models, PCA and neural
networks the answer is yes. For trees and their ensembles it is no.

## Summary

- Unsupervised learning has no labels. It is powerful for exploration and preprocessing, but hard to
  evaluate.
- `StandardScaler`, `RobustScaler` and `MinMaxScaler` rescale columns. `Normalizer` rescales rows.
- `fit` on the training set and `transform` everything with those statistics. Test features may fall
  outside the training range, and that is fine.
- Scaling can turn a useless SVM, k-NN or MLP into an excellent one. Trees don't care.

```quiz
[
  {"q": "Why is unsupervised learning harder to evaluate than supervised learning?", "options": ["There are no labels to tell us what the correct output is", "The algorithms are slower", "It needs more features", "It cannot be run on a test set"], "answer": 0,
   "explain": "Without ground truth, quality is often judged by manual inspection or by usefulness downstream."},
  {"q": "After `MinMaxScaler().fit(X_train)`, the transformed TEST data…", "options": ["may contain values below 0 or above 1", "is always exactly within [0, 1]", "has mean 0 and variance 1", "raises an error if outside the training range"], "answer": 0,
   "explain": "The training min and range are applied; test extremes can differ from training extremes."},
  {"q": "Which scaler is the best choice when a feature has extreme outliers?", "options": ["RobustScaler", "MinMaxScaler", "Normalizer", "No scaler can be used"], "answer": 0,
   "explain": "It uses the median and interquartile range, which outliers barely affect."},
  {"q": "What does `Normalizer` do?", "options": ["Rescales each sample (row) to unit norm", "Rescales each feature to unit variance", "Maps each feature to [0, 1]", "Removes outliers"], "answer": 0,
   "explain": "It works row-wise, so only the direction of each sample's feature vector remains."},
  {"q": "Which model's accuracy is unaffected by standardising the features?", "options": ["Random forest", "RBF SVM", "k-nearest neighbours", "MLP trained with Adam"], "answer": 0,
   "explain": "Tree splits depend only on the order of values within a feature."},
  {"q": "Fitting a scaler separately on the test set is wrong because…", "options": ["train and test points get transformed differently, shifting them relative to each other", "the test set is too small to compute a mean", "scalers can only be fitted once", "it makes the test accuracy too low to report"], "answer": 0,
   "explain": "The same raw value would map to different scaled values, so the learned model no longer applies consistently."},
  {"q": "StandardScaler computes the standard deviation with…", "options": ["denominator n (population, ddof=0)", "denominator n − 1", "the interquartile range", "the max minus the min"], "answer": 0,
   "explain": "scikit-learn uses numpy's default population standard deviation."}
]
```

> **Source:** Müller & Guido, *Introduction to Machine Learning with Python*, ch. 3 ("Types of Unsupervised Learning", "Challenges in Unsupervised Learning", "Preprocessing and Scaling": different kinds of preprocessing, applying data transformations, scaling training and test data the same way, the effect on supervised learning); scikit-learn User Guide, "Preprocessing data".
