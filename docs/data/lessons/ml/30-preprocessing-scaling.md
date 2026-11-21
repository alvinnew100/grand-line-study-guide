# Unsupervised learning, preprocessing and scaling

> **Before this lesson:** you should know the estimator API (`fit`, `predict`, `transform`) and training and test sets from [The scikit-learn API and your first model](#/lesson/ml/sklearn-first-model), and the difference between supervised and unsupervised learning from [What machine learning is](#/lesson/ml/what-is-ml). The models mentioned by name (k-NN, SVMs, trees, linear models) are from module 2; you only need to know that they exist.

## In plain words

Suppose a table describes people by age in years and income in dollars. Ages differ by tens; incomes differ by tens of thousands. To a program that measures how "far apart" two people are by subtracting the numbers, income is the only thing that matters and age might as well not be there, purely because of the units chosen. **Scaling** means re-expressing every feature in comparable units so that none dominates by accident.

It is like comparing athletes from different sports. A sprint time of 10 seconds and a javelin throw of 80 metres cannot be compared directly, but "how far above the average competitor, in typical-spread units" can be, for both.

Scaling is one kind of **preprocessing**: any change made to the data before a model sees it. It is also the gentlest example of **unsupervised learning**, because it uses the features only and never looks at the labels. This lesson first introduces unsupervised learning in general, then covers scaling in detail.

Why this matters for a job: forgetting to scale is one of the most common reasons a model that should work does not, and doing the scaling in the wrong place (using the test data) quietly produces results that are too good to be true. Both points are favourite interview questions.

## 1. Two kinds of unsupervised learning

In supervised learning every training example comes with the right answer. In **unsupervised learning** the algorithm is given only the inputs and must find structure in them on its own. There are two broad kinds.

**Unsupervised transformations** produce a new description of the data that is easier for people or for other algorithms to work with than the original.

- *Dimensionality reduction* takes data with many features and summarises it with fewer, keeping the most important information. A common use is reducing to two features so that the data can be drawn on a flat chart (lesson 31).
- *Finding the components* that make up the data. An example is extracting topics from a collection of documents, where every document is treated as a blend of a few unknown themes (lesson 71).

**Clustering algorithms** divide the data into groups of similar items (lesson 32). A photo application that groups pictures by the person in them, without being told who anyone is or how many people there are, is clustering.

## 2. The challenge: did it learn anything useful?

With no labels there is no answer key. **Nobody has said what the right output is**, so it is hard to tell whether an algorithm did well. A clustering method asked to group photos of faces might group them by whether the face is turned sideways or towards the camera, when you wanted them grouped by person. Both groupings are real structure in the data. Nothing tells the algorithm which one you had in mind, and often the only way to check is to look at the results yourself.

For this reason unsupervised methods are used mostly for **exploration**, when an analyst wants to understand a dataset better, and less often as part of a fully automatic system. Their other main use is as a **preprocessing step before supervised learning**: a better description of the data can raise a model's accuracy or cut its memory use and running time. Scaling is the most basic such step.

## 3. Why scale?

Some algorithms are affected by the numeric size of the feature values and some are not.

| sensitive to scale | why | not sensitive | why |
|---|---|---|---|
| k-NN, k-means, DBSCAN | they compute distances between points | decision trees | a split asks only whether a value is above or below a threshold |
| SVMs | kernels are built from distances and dot products | random forests | made of trees |
| linear models with a penalty (ridge, lasso, logistic regression) | the penalty treats all weights alike, whatever units the features are in | gradient boosted trees | made of trees |
| neural networks | gradient descent is slow and unstable when features differ greatly in size | naive Bayes | it summarises each feature separately |
| PCA | it looks for the directions of largest variance, and variance depends on units | | |

The worked example in section 10 puts numbers on this.

## 4. Four kinds of scaling

scikit-learn's `sklearn.preprocessing` module offers several scalers. Each is a **transformer**: an object with a `fit` method that learns some numbers from the data and a `transform` method that applies them.

First, four statistical terms. The **mean** of a feature is its average. Its **standard deviation** measures how spread out the values are around the mean. The **median** is the middle value when the values are sorted. The **quartiles** are the values one quarter and three quarters of the way through the sorted list, and the distance between them is the **interquartile range** (IQR), the width of the middle half of the data. An **outlier** is a value far from all the others, caused by a measurement error or by a truly unusual case.

| scaler | what it does | formula | notes |
|---|---|---|---|
| `StandardScaler` | shifts and stretches each feature so its mean is 0 and its standard deviation is 1 | $z = (x-\mu)/\sigma$ | the usual default; values are not confined to a range; outliers pull $\mu$ and $\sigma$ |
| `RobustScaler` | the same idea using the median and the interquartile range | $(x-\text{median})/\text{IQR}$ | barely affected by outliers |
| `MinMaxScaler` | shifts and stretches each feature so its smallest value is 0 and its largest is 1 | $(x-\min)/(\max-\min)$ | a single outlier squashes all other values together |
| `Normalizer` | rescales each **row** so that its length (Euclidean norm) is 1 | $x / \lVert x\rVert$ | keeps only the direction of each sample; used when the proportions between features matter and their total size does not |

In the formulas $\mu$ (mu) is the mean and $\sigma$ (sigma) the standard deviation of the feature. Worked example for `StandardScaler`: a feature with mean 40 and standard deviation 12 maps the value 25 to $(25-40)/12 = -1.25$, meaning "1.25 standard deviations below average".

The first three work **column by column** (feature by feature). `Normalizer` works **row by row** (sample by sample) and is a different kind of operation altogether.

```python-run
import numpy as np
from sklearn.preprocessing import StandardScaler, RobustScaler, MinMaxScaler, Normalizer

X = np.array([[1.0, 100.0], [2.0, 110.0], [3.0, 120.0], [4.0, 130.0], [50.0, 140.0]])   # 50 is an outlier
for scaler in [StandardScaler(), RobustScaler(), MinMaxScaler(), Normalizer()]:
    Z = scaler.fit_transform(X)
    print(f"{type(scaler).__name__:15s} first column -> {Z[:, 0].round(2)}")
```

**Reading this code line by line**

- `X` is a table of five samples and two features. The first feature runs 1, 2, 3, 4 and then jumps to 50: an outlier.
- The loop creates each scaler in turn. `scaler.fit_transform(X)` learns the scaler's numbers from `X` and returns the rescaled table in one call.
- `type(scaler).__name__` is the scaler's class name, used as a label. `Z[:, 0]` is the first column of the result.

Look at what happens to the four ordinary values under each scaler. `MinMaxScaler` crushes them into the sliver from 0 to 0.06, because the outlier claims the whole upper range. `StandardScaler` does somewhat better (−0.58 to −0.42). `RobustScaler` keeps them well spread (−1 to 0.5) and lets the outlier sit far away at 23.5. `Normalizer` gives numbers that are not comparable with the others, because it divided each row by that row's own length.

## 5. Applying a transformation: fit on train, transform both

A scaler is used in two steps. `fit` computes the statistics it needs (for `MinMaxScaler`, each feature's minimum and maximum). `transform` applies them to whatever data you give it.

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

`scaler.fit(X_train)` is given the training features only, and no labels: this is the sense in which scaling is unsupervised. The same fitted scaler then transforms both the training set and the test set. `.min(axis=0)` and `.max(axis=0)` find the smallest and largest value in each column; `[:4]` shows the first four features.

After scaling, each training feature runs exactly from 0 to 1. The **test features do not**: their minimums are a little above 0 (0.03, 0.02...) and their maximums a little below 1 (0.96, 0.82...), and in general they can fall below 0 or above 1. This is correct and expected. `transform` always subtracts the *training* minimum and divides by the *training* range, and the test set happens to have slightly different extremes.

## 6. Scale training and test data the same way

What goes wrong if you fit a second scaler on the test set? Each set would be stretched to fill the range 0 to 1 on its own terms, so the test points would shift relative to the training points. A test sample identical to a training sample would end up with different coordinates. The model learned where its boundary lies in the training set's coordinates, and that boundary would no longer line up with the test data.

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

The value 5.0 appears in both sets. With one scaler fitted on the training data (minimum 0, maximum 10), 5.0 becomes 0.5 in both. With a separate scaler fitted on the test data (minimum 5, maximum 7), the test set's 5.0 becomes 0: the same raw value now means two different things.

> [!WARNING]
> **Never call `fit` or `fit_transform` on the test set.** For the same reason, never fit a scaler on the whole dataset before splitting it, or before cross-validation. Doing so lets information about the test data seep into training, a mistake called **data leakage**, and makes your results look better than they are. Lesson 60 shows a tool (the pipeline) that makes this mistake impossible.

**Shortcut.** `scaler.fit_transform(X_train)` fits and transforms in one call. Use it on the training set, then plain `transform` on the test set.

## 7. The effect on supervised learning

Does scaling change results? Here is a kernel SVM on the tumour data, with no scaling and with three different scalers.

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

Without scaling the SVM scores 0.944; with any of the three scalers it does better, up to 0.965 with `MinMaxScaler`. The gain here is modest because recent versions of scikit-learn pick the kernel's width automatically from the data's spread. With a fixed kernel width, as in lesson 23, the same data went from 0.63 to 0.97.

Swapping one scaler for another is a one-line change, because they all share the same methods. Which one is best depends on the data, so if it matters, try several and compare them on validation data, as you would any other setting.

## 8. Standardisation by hand

It is worth knowing exactly what `StandardScaler` computes, because interviewers ask and because you implement it in the problem *ml-standard-scaler*. For each feature $j$: compute the mean of the column, compute the standard deviation of the column, then subtract the mean from every value and divide by the standard deviation.

$$\mu_j = \frac1n\sum_i x_{ij},\qquad \sigma_j = \sqrt{\frac1n\sum_i (x_{ij}-\mu_j)^2},\qquad z_{ij} = \frac{x_{ij}-\mu_j}{\sigma_j}.$$

Here $x_{ij}$ is the value of feature $j$ for sample $i$, $n$ is the number of samples and $z_{ij}$ is the scaled value. Tiny example: the column 2, 4, 6 has mean 4. The squared distances from the mean are 4, 0, 4, with average $8/3$, so $\sigma = \sqrt{8/3} = 1.63$, and the scaled column is $-1.22, 0, 1.22$.

Three details of scikit-learn's version: it divides by $n$ (the "population" standard deviation), not by $n-1$; it stores the results in the attributes `mean_` and `scale_`; and if a feature is constant, so that its standard deviation is 0, it divides by 1 to avoid dividing by zero.

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

`rng.normal(loc=[10, 200], scale=[2, 50], size=(100, 2))` draws 100 samples of two features, the first centred on 10 with spread 2 and the second centred on 200 with spread 50. The two lines after the blank line do the standardising by hand with the *training* mean and standard deviation, applied to the test data. `np.allclose` confirms that this matches `StandardScaler` exactly. The last line makes the same point as section 5: the scaled test set's mean is close to 0 (0.0 and −0.28) but not exactly 0, because the statistics came from the training set.

## 9. Beyond linear scaling

The scalers above shift and stretch a feature without changing the shape of its distribution. Some preprocessing changes the shape:

- `np.log1p` (the logarithm of one plus the value) pulls in the long tail of features such as counts or prices, where a few values are enormous (lesson 41);
- `PowerTransformer` finds a transformation that makes a feature look more like a bell curve;
- `QuantileTransformer` replaces each value by its rank, so that the result is spread evenly or follows a bell curve;
- **missing values** must be filled in before most models will run. Filling them in is called **imputation**: `SimpleImputer` uses the column's mean, median or most frequent value, and `KNNImputer` uses the values of similar rows. Imputers too are fitted on the training data only.

> [!INTERVIEW]
> **"Normalisation vs standardisation, and when does it matter?"** Min-max normalisation maps each feature to the range 0 to 1 and is sensitive to outliers. Standardisation gives mean 0 and standard deviation 1 and is the usual default. Scaling matters for models based on distances, for kernel methods, for linear models with a penalty, for PCA and for networks trained by gradient descent. It does not matter for tree-based models. Always compute the statistics on the training portion only and apply them to validation and test data.

## 10. Worked example: why scaling changes k-NN's neighbours

A calculation by hand shows the effect better than any accuracy figure. Take three people described by age in years and income in dollars:

| person | age | income |
|---|---|---|
| A | 25 | 50,000 |
| B | 60 | 51,000 |
| C | 27 | 58,000 |

Who is A's nearest neighbour? The straight-line distance is the square root of the sum of squared differences. On the raw numbers, $d(A,B) = \sqrt{35^2 + 1000^2} \approx 1000.6$ and $d(A,C) = \sqrt{2^2 + 8000^2} \approx 8000.0$. B wins easily. A 35-year age gap counts for almost nothing, because income is recorded in units a thousand times larger. The distance is, in effect, the income difference alone.

Now standardise both features using the mean and standard deviation of a realistic population (age: mean 40, standard deviation 12; income: mean 55,000, standard deviation 15,000). For A's age: $(25-40)/12 = -1.25$.

| person | age (z) | income (z) |
|---|---|---|
| A | −1.25 | −0.33 |
| B | 1.67 | −0.27 |
| C | −1.08 | 0.20 |

$d(A,B) = \sqrt{2.92^2 + 0.07^2} \approx 2.92$ and $d(A,C) = \sqrt{0.17^2 + 0.53^2} \approx 0.56$. Now C, who is almost the same age and earns somewhat more, is the nearest neighbour. Neither answer is "true" in an absolute sense. But the scaled version treats a typical difference in age and a typical difference in income as equally important, which is almost always what you intend.

```python-run
import numpy as np
people = np.array([[25, 50000.0], [60, 51000.0], [27, 58000.0]])
mu, sigma = np.array([40.0, 55000.0]), np.array([12.0, 15000.0])
for name, data in [("raw", people), ("standardised", (people - mu) / sigma)]:
    d_ab, d_ac = np.linalg.norm(data[0] - data[1]), np.linalg.norm(data[0] - data[2])
    print(f"{name:13s} d(A,B)={d_ab:9.2f}  d(A,C)={d_ac:9.2f}  -> nearest to A is {'B' if d_ab < d_ac else 'C'}")
```

`(people - mu) / sigma` standardises the whole table in one expression (NumPy applies the two-entry arrays to every row). `np.linalg.norm` of a difference is the Euclidean distance. The output repeats the hand calculation: on raw data the nearest person to A is B, and after standardising it is C.

The same reasoning explains the other scale-sensitive models. The RBF kernel of an SVM is a function of this distance. A ridge penalty $\alpha\sum_j w_j^2$ punishes a weight of 0.001 on income far less than a weight of 1.0 on age, though the two may express effects of the same size. And PCA looks for the direction in which the data varies most, which on raw data is the income axis, for no better reason than its units.

## 11. Pitfalls and questions to ask

- **Scaling a sparse matrix.** A sparse matrix stores only its non-zero entries, to save memory. Subtracting the mean turns every zero into a non-zero and can exhaust memory. For sparse data use `StandardScaler(with_mean=False)` or `MaxAbsScaler`, which leave zeros as zeros.
- **Scaling 0/1 indicator columns.** It is rarely needed and makes the features harder to read. Scale the numeric columns only, using a `ColumnTransformer` (lesson 61).
- **Scaling the target.** For regression with models trained by gradient descent it can help to standardise `y` as well. Remember to convert the predictions back to the original units.
- **Outliers and `MinMaxScaler`.** One extreme value squeezes all the others into a sliver of the range. Clip the extreme values, use `RobustScaler`, or take a logarithm first.
- **New data outside the training range.** `MinMaxScaler` then produces values below 0 or above 1. That is harmless for most models, but one that assumes bounded inputs may behave oddly.
- **Trees do not need scaling, and it does no harm.** If the same prepared data feeds both a linear model and a tree, you can scale once for both.
- **Keep the scaler with the model.** At prediction time you need the *training* mean and standard deviation. Saving the scaler and the model together as one object (a pipeline) is the reliable way to keep them in step.

A quick test of whether scaling matters for a model: *would its predictions change if one feature were recorded in different units?* For k-NN, SVMs, penalised linear models, PCA and neural networks the answer is yes. For trees and ensembles of trees it is no.

## Summary

- Unsupervised learning has no labels. It is valuable for exploration and preprocessing, and hard to evaluate.
- `StandardScaler`, `RobustScaler` and `MinMaxScaler` rescale columns. `Normalizer` rescales rows.
- `fit` on the training set, then `transform` everything with those statistics. Test features may fall outside the training range, and that is fine.
- Scaling can turn a useless SVM, k-NN or neural network into an excellent one. Trees are indifferent to it.

## Glossary

- **Preprocessing**: any transformation applied to data before it reaches a model.
- **Scaling**: re-expressing features in comparable units.
- **Unsupervised learning**: learning from inputs alone, with no labels.
- **Transformer**: a scikit-learn object with `fit` and `transform` that changes data.
- **Mean / standard deviation**: a feature's average / its typical spread around the average.
- **Median / quartiles / interquartile range**: the middle value / the values a quarter and three quarters of the way through the sorted data / the distance between those two.
- **Outlier**: a value far from the rest of the data.
- **Standardisation**: subtracting the mean and dividing by the standard deviation (`StandardScaler`).
- **Min-max normalisation**: mapping a feature to the range 0 to 1 (`MinMaxScaler`).
- **`Normalizer`**: rescaling each sample (row) to length 1.
- **`fit` / `transform` / `fit_transform`**: learn statistics / apply them / do both on the same data.
- **Data leakage**: information from test data influencing training, which inflates results.
- **Imputation**: filling in missing values.
- **Sparse matrix**: a table stored by listing only its non-zero entries.

## Check yourself

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
