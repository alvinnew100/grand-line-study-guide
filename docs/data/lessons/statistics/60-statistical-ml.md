# Statistical machine learning: k-NN, trees, bagging and boosting

> **Before this lesson:** [Multiple regression: assessment, cross-validation and model selection](#/lesson/statistics/multiple-regression) (cross-validation, overfitting), [The bootstrap](#/lesson/statistics/bootstrap) (resampling with replacement, the basis of bagging) and [Evaluating classifiers and handling rare classes](#/lesson/statistics/classification-evaluation). The ML track teaches these models hands-on in [Generalisation, overfitting and k-NN](#/lesson/ml/generalization-knn) and [Naive Bayes, decision trees and ensembles](#/lesson/ml/bayes-trees-ensembles); this lesson concentrates on the statistical ideas: bias and variance, why averaging helps, how importance is measured and how to keep flexible models honest.

## In plain words

Regression and logistic regression assume a specific shape (a line, a plane, an S-curve). **Statistical machine learning** methods let the data decide the shape. **k-nearest neighbours** (k-NN) predicts from the most similar past records. **Decision trees** split the data into boxes with simple yes/no questions. **Ensembles** combine many models: **bagging** and **random forests** average many trees grown on bootstrap samples; **boosting** builds trees one after another, each fixing the previous ones' mistakes. These methods often predict better than regression, at the price of interpretability and a real risk of overfitting.

An everyday picture: estimating a house's price. k-NN asks the agent "what did the five most similar houses sell for?". A tree is a flowchart: "more than 3 bedrooms? within 1 km of the station?". A random forest polls hundreds of agents with slightly different experience and averages their answers. Boosting is a team where each new member specialises in the cases the team keeps getting wrong.

Why it matters for a job: tree ensembles (random forests, gradient boosting such as XGBoost and LightGBM) win most tabular prediction tasks and power many production models. Interviewers ask about the **bias-variance trade-off**, why random forests reduce variance, why k-NN needs standardised features, how variable importance can mislead, and how boosting is regularised.

## 1. The bias-variance trade-off

The expected error of a model on new data splits into three parts:

$$\text{expected error} = \text{bias}^2 + \text{variance} + \text{irreducible noise}$$

- **Bias**: error from a model too rigid to capture the true pattern (a straight line for a curve). Simple models have high bias.
- **Variance**: error from sensitivity to the particular training sample; a model that changes a lot when trained on a different sample has high variance. Flexible models have high variance.
- **Irreducible noise**: randomness no model can predict.

Every method in this lesson has a knob that moves along this trade-off: the number of neighbours $K$, the depth of a tree, the number and size of boosting steps. Cross-validation finds the setting with the lowest out-of-sample error. Ensembles are clever because averaging reduces variance *without* adding much bias.

## 2. k-nearest neighbours

To predict a record, find the $K$ training records closest to it (by a **distance metric**, usually Euclidean: the straight-line distance $\sqrt{\sum_j (x_j - x'_j)^2}$) and take a majority vote (classification) or average (regression).

Two statistical points matter:

- **Scale matters.** Distance adds up differences across features, so a feature measured in large units (income in dollars) swamps one in small units (a ratio between 0 and 1). Standardise features (convert to z-scores) first.
- **$K$ controls bias and variance.** $K = 1$ follows the training data's every quirk (low bias, high variance); a huge $K$ averages over most of the data and predicts nearly the same everywhere (high bias, low variance).

```python-run
import numpy as np
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score
rng = np.random.default_rng(60)
n = 1000
income = rng.normal(60_000, 20_000, n)
debt_ratio = rng.uniform(0, 1, n)
y = (rng.random(n) < 1 / (1 + np.exp(-(-1 + 4 * (debt_ratio - 0.5) - (income - 60_000) / 40_000)))).astype(int)
X = np.column_stack([income, debt_ratio])
for k in [1, 5, 25, 101, 401]:
    raw = cross_val_score(KNeighborsClassifier(k), X, y, cv=5).mean()
    scaled = cross_val_score(make_pipeline(StandardScaler(), KNeighborsClassifier(k)), X, y, cv=5).mean()
    print(f"K={k:>3}: accuracy raw {raw:.3f}  standardised {scaled:.3f}")
```

**Reading this code line by line**

- Loan default depends mostly on the debt ratio (0 to 1) and somewhat on income (tens of thousands of dollars).
- `KNeighborsClassifier(k)` is k-NN with `k` neighbours. The second version puts `StandardScaler` (which converts each feature to z-scores using the training fold's mean and SD) in a pipeline before k-NN.
- `cross_val_score(..., cv=5).mean()` is the 5-fold cross-validated accuracy.

Without standardisation, distances are almost entirely income differences, the debt ratio is effectively ignored, and accuracy suffers at every $K$ (0.597 at $K = 1$). Standardised, accuracy rises to 0.726 at $K = 101$. $K = 1$ overfits (0.652); $K = 401$ over-smooths (0.701). The best $K$ is found by cross-validation, as always.

k-NN is also used as a **feature engine**: the out-of-fold k-NN prediction for each record (the "what similar records did" signal) can be added as a feature to another model.

Standardising treats each feature separately. When features are **correlated** (height and weight, income and spending), plain Euclidean distance still double-counts the information they share. The **Mahalanobis distance** fixes this by measuring distance in units of the data's own covariance: it rescales and "unskews" the space so that a step along a direction where the data naturally varies a lot counts for less than the same step along a direction where it barely varies. It uses the inverse of the features' covariance matrix, and with uncorrelated, standardised features it reduces to ordinary Euclidean distance. It is more principled but costs a matrix inversion and becomes unstable when features are nearly collinear or numerous, which is why scaling plus Euclidean distance is the common default in k-NN, and Mahalanobis distance appears more often in outlier detection.

## 3. Decision trees

A **decision tree** (also called recursive partitioning, or CART for classification and regression trees) repeatedly splits the data on the single predictor and cut-off value that best separates the outcome, then splits each resulting group again. Prediction for a new record follows the splits to a **leaf** and returns the leaf's majority class (or proportion, or mean).

"Best" split is measured by the decrease in **impurity**, how mixed the classes are in a group. For a group with class proportions $p_k$:

- **Gini impurity**: $1 - \sum_k p_k^2$. Zero for a pure group; 0.5 for a 50/50 binary group.
- **Entropy**: $-\sum_k p_k \log_2 p_k$. Zero for pure; 1 bit for 50/50. Its decrease after a split is called **information gain**.

```python-run
import numpy as np
def gini(labels):
    p = np.bincount(labels, minlength=2) / len(labels)
    return 1 - np.sum(p ** 2)
def entropy(labels):
    p = np.bincount(labels, minlength=2) / len(labels)
    p = p[p > 0]
    return -np.sum(p * np.log2(p))
parent = np.array([1] * 40 + [0] * 60)
left = np.array([1] * 30 + [0] * 10)
right = np.array([1] * 10 + [0] * 50)
w_gini = (len(left) * gini(left) + len(right) * gini(right)) / len(parent)
print(f"parent Gini {gini(parent):.4f}, after split {w_gini:.4f}, decrease {gini(parent) - w_gini:.4f}")
w_ent = (len(left) * entropy(left) + len(right) * entropy(right)) / len(parent)
print(f"parent entropy {entropy(parent):.4f}, after split {w_ent:.4f}, information gain {entropy(parent) - w_ent:.4f}")
```

**Reading this code line by line**

- `np.bincount(labels, minlength=2)` counts 0s and 1s; dividing by the length gives class proportions.
- In `entropy`, `p[p > 0]` drops zero proportions, because $0 \times \log 0$ is treated as 0.
- A parent group of 100 records (40 positive) is split into a left child (30 of 40 positive) and a right child (10 of 60 positive). Child impurities are weighted by size.

The split lowers Gini impurity from 0.48 to 0.3167 (a decrease of 0.1633) and entropy from 0.971 to 0.7145 (information gain 0.2564). A tree evaluates this for every predictor and every cut-off and picks the best.

Statistical properties of trees:

- **Interpretability**: a shallow tree is a readable set of rules ("if tenure < 6 months and tickets ≥ 2, churn risk 45%").
- **Automatic interactions and nonlinearity**: splits within splits capture both.
- **High variance**: a fully grown tree fits noise, and a slightly different sample can produce a different tree. Control it by limiting depth, requiring a minimum number of records per leaf, or **pruning** (growing a big tree, then cutting back branches that do not improve cross-validated error).

## 4. Bagging and random forests: averaging away variance

If you average $B$ independent estimates each with variance $\sigma^2$, the average has variance $\sigma^2/B$, the square-root law again. **Bagging** (bootstrap aggregating) applies this to unstable models: fit a deep tree on each of many bootstrap samples and average their predictions (or vote). The trees are not independent (they see overlapping data), so the variance does not fall all the way to $\sigma^2/B$; it falls towards $\rho\sigma^2$, where $\rho$ is the correlation between trees.

A **random forest** reduces that correlation: at every split, each tree may only choose among a random subset of the predictors (commonly $\sqrt{p}$ for classification). Trees become more different from each other, so averaging cancels more of their errors.

Each bootstrap sample leaves out about 37% of the records (the "out-of-bag" records). Predicting each record with only the trees that did not see it gives the **out-of-bag (OOB) error**, a free estimate of test error without a separate validation set.

```python-run
import numpy as np
from sklearn.datasets import make_classification
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import BaggingClassifier, RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import cross_val_score
X, y = make_classification(n_samples=1000, n_features=12, n_informative=5, n_redundant=3, flip_y=0.08, random_state=0)
models = {
    "single deep tree": DecisionTreeClassifier(random_state=0),
    "tree, max_depth=4": DecisionTreeClassifier(max_depth=4, random_state=0),
    "bagged trees (60)": BaggingClassifier(DecisionTreeClassifier(), n_estimators=60, random_state=0),
    "random forest (60)": RandomForestClassifier(n_estimators=60, random_state=0),
    "gradient boosting": GradientBoostingClassifier(random_state=0),
}
for name, m in models.items():
    s = cross_val_score(m, X, y, cv=5)
    print(f"{name:20s} CV accuracy {s.mean():.3f} (fold SD {s.std():.3f})")
rf = RandomForestClassifier(n_estimators=100, oob_score=True, random_state=0).fit(X, y)
print(f"random forest out-of-bag accuracy {rf.oob_score_:.3f}")
```

**Reading this code line by line**

- `make_classification` generates a synthetic dataset: 12 features, of which 5 carry signal and 3 are combinations of those; `flip_y=0.08` flips 8% of labels at random (irreducible noise).
- Five models are compared by 5-fold cross-validated accuracy; the fold-to-fold standard deviation hints at stability.
- `oob_score=True` asks the forest to compute out-of-bag accuracy while fitting.

A single fully grown tree scores 0.850; limiting depth to 4 helps (0.866) by cutting variance. Bagging 60 deep trees jumps to 0.906 and is also more stable across folds (SD 0.006). The random forest does slightly better still, 0.919. Gradient boosting with default settings reaches 0.903. The forest's out-of-bag accuracy, 0.925, agrees closely with the cross-validated estimate.

## 5. Variable importance, and how it can mislead

Forests report which predictors matter. Two common measures:

- **Impurity importance** (scikit-learn's `feature_importances_`): the total impurity decrease from splits on each predictor, averaged over trees. Fast, but biased towards predictors with many distinct values, which offer many possible cut-offs and can split noise.
- **Permutation importance**: shuffle one predictor's values in held-out data and measure how much accuracy drops. If shuffling does not hurt, the model was not really using it. Slower but more trustworthy.

```python-run
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.inspection import permutation_importance
rng = np.random.default_rng(61)
n = 2000
signal = rng.normal(size=n)
noise_id = rng.integers(0, 1000, n).astype(float)
noise_bin = rng.integers(0, 2, n).astype(float)
y = (signal + rng.normal(0, 1, n) > 0).astype(int)
X = np.column_stack([signal, noise_id, noise_bin])
rf = RandomForestClassifier(n_estimators=200, random_state=0).fit(X[:1500], y[:1500])
perm = permutation_importance(rf, X[1500:], y[1500:], n_repeats=10, random_state=0)
for name, imp, pimp in zip(["signal", "noisy id (1000 values)", "noisy 0/1"], rf.feature_importances_, perm.importances_mean):
    print(f"{name:24s} impurity importance {imp:.3f}  permutation importance {pimp:.3f}")
```

**Reading this code line by line**

- Only `signal` affects the outcome. `noise_id` is a meaningless code with 1,000 distinct values (like a user ID); `noise_bin` is a meaningless 0/1 flag.
- The forest is trained on 1,500 rows; `permutation_importance` shuffles each column of the 500 held-out rows 10 times and reports the average accuracy drop.

Impurity importance gives the meaningless ID 0.332, half as much as the real signal (0.664), because deep trees use its many values to split noise in the training data. Permutation importance on held-out data correctly gives it almost nothing (0.005) and the signal 0.214. Lesson: prefer permutation importance on held-out data, and remember that neither measure is causal; correlated predictors also share or steal importance from each other.

## 6. Boosting

**Boosting** builds an ensemble sequentially. Each new small tree is fit to the errors of the current ensemble (in **gradient boosting**, to the gradient of the loss, which for squared error equals the residuals), and added with a small weight called the **learning rate** (or shrinkage). Where bagging mainly reduces variance, boosting mainly reduces bias, and it can overfit if it runs too long.

Regularisation knobs: the learning rate (smaller is safer but needs more trees), the number of trees (chosen by validation or **early stopping**), tree depth (2 to 6 is typical), subsampling of rows and columns per tree (stochastic gradient boosting), and penalties on leaf values (as in XGBoost).

```python-run
import numpy as np
from sklearn.datasets import make_classification
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import train_test_split
X, y = make_classification(n_samples=2000, n_features=12, n_informative=5, flip_y=0.1, random_state=3)
Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.3, random_state=0)
for lr in [1.0, 0.1]:
    gb = GradientBoostingClassifier(learning_rate=lr, n_estimators=300, max_depth=3, random_state=0).fit(Xtr, ytr)
    test_acc = [np.mean(p == yte) for p in gb.staged_predict(Xte)]
    best = int(np.argmax(test_acc))
    print(f"learning rate {lr}: best test accuracy {test_acc[best]:.3f} at {best + 1} trees; after 300 trees {test_acc[-1]:.3f}; train {gb.score(Xtr, ytr):.3f}")
```

**Reading this code line by line**

- `train_test_split(..., test_size=0.3)` holds out 30% of rows.
- `staged_predict` yields the ensemble's predictions after 1, 2, ..., 300 trees, so we can trace test accuracy as trees are added.
- We compare a large learning rate (1.0) with a small one (0.1).

Both models fit the training data almost perfectly (training accuracy 1.000 and 0.984) while test accuracy is around 0.87 to 0.89: a gap that signals overfitting capacity. The smaller learning rate reaches a higher peak (0.893 versus 0.873). In practice you monitor validation error as trees are added and stop when it stops improving (early stopping), and tune the learning rate, depth and number of trees by cross-validation.

## 7. Choosing among them

| Method | Main strength | Main weakness | Key knobs |
|---|---|---|---|
| k-NN | simple, no training, local patterns | needs scaling; slow and weak in high dimensions | $K$, distance, scaling |
| Single tree | readable rules, interactions | high variance, unstable | depth, leaf size, pruning |
| Random forest | strong default, little tuning, OOB error | less interpretable, large | trees, features per split, leaf size |
| Gradient boosting | often the most accurate on tabular data | overfits without care, many knobs | learning rate, trees, depth, subsampling |
| Regression (for comparison) | interpretable, inference, extrapolates linearly | must specify shape | terms, interactions, regularisation |

> [!INTERVIEW]
> "Why does a random forest generalise better than a single decision tree?" A deep tree has low bias but high variance. Averaging many trees fit on bootstrap samples reduces variance, and choosing among random subsets of features at each split decorrelates the trees so the averaging cancels more error. Bias stays roughly the same. Out-of-bag error gives a built-in estimate of test performance.

## Summary

- Error splits into bias², variance and noise; flexible models trade bias for variance, and cross-validation picks the balance.
- k-NN predicts from the nearest records; standardise features and tune $K$.
- Trees split on the predictor and cut-off that most reduce impurity (Gini or entropy); they are interpretable but high-variance.
- Bagging averages trees on bootstrap samples; random forests also randomise features per split; out-of-bag error estimates test error.
- Impurity importance is biased towards many-valued predictors; permutation importance on held-out data is more reliable, and neither is causal.
- Boosting adds small trees sequentially to fix errors; regularise with a small learning rate, shallow trees, subsampling and early stopping.

## Glossary

- **Mahalanobis distance**: a distance that accounts for the scale and correlation of features through their covariance matrix; equal to Euclidean distance for standardised, uncorrelated features.
- **Statistical machine learning**: flexible, data-driven prediction methods.
- **Bias / variance / irreducible noise**: error from rigidity / from sensitivity to the sample / from randomness.
- **k-nearest neighbours (k-NN)**: predicting from the $K$ most similar training records.
- **Distance metric / Euclidean distance**: a measure of dissimilarity / straight-line distance.
- **Feature engine**: using one model's predictions as a feature for another.
- **Decision tree (recursive partitioning, CART)**: a model of nested yes/no splits.
- **Leaf**: a terminal node of a tree.
- **Impurity / Gini impurity / entropy / information gain**: class mixing / $1 - \sum p_k^2$ / $-\sum p_k \log_2 p_k$ / entropy decrease from a split.
- **Pruning**: cutting back a grown tree to reduce overfitting.
- **Bagging**: averaging models fit on bootstrap samples.
- **Random forest**: bagged trees with a random subset of features at each split.
- **Out-of-bag (OOB) error**: error on records not in a tree's bootstrap sample.
- **Impurity / permutation importance**: importance from split gains / from accuracy loss when a feature is shuffled.
- **Boosting / gradient boosting**: sequential ensembles fixing previous errors / boosting by fitting the loss gradient.
- **Learning rate (shrinkage)**: the weight on each new tree.
- **Early stopping**: halting boosting when validation error stops improving.

## Check yourself

```quiz
[
  {"q": "k-NN on income (in dollars) and debt ratio (0 to 1) without scaling will mostly…", "options": ["ignore the debt ratio, because income differences dominate the distance", "ignore income", "work perfectly", "fail to run"], "answer": 0,
   "explain": "Distance sums squared differences; dollar-scale differences swamp ratio-scale ones. Standardise first."},
  {"q": "In k-NN, increasing K generally…", "options": ["increases bias and decreases variance", "decreases bias and increases variance", "has no effect", "always improves accuracy"], "answer": 0,
   "explain": "Averaging over more neighbours smooths the prediction."},
  {"q": "A group has 40 positives and 60 negatives. Its Gini impurity is…", "options": ["0.48", "0.24", "0.5", "0.97"], "answer": 0,
   "explain": "$1 - (0.4^2 + 0.6^2) = 1 - 0.52 = 0.48$."},
  {"q": "Why do random forests pick a random subset of features at each split?", "options": ["To decorrelate the trees so averaging reduces variance more", "To reduce bias", "To speed up prediction only", "To make trees deeper"], "answer": 0,
   "explain": "Averaging correlated trees leaves variance $\\rho\\sigma^2$; lowering $\\rho$ helps."},
  {"q": "A meaningless user-ID column gets high impurity importance in a forest. The better check is…", "options": ["permutation importance on held-out data", "removing all other columns", "increasing the number of trees", "using the training accuracy"], "answer": 0,
   "explain": "Impurity importance favours many-valued features; permutation importance on held-out data reveals they do not help."},
  {"q": "Which statement about boosting is right?", "options": ["It adds trees sequentially to fix current errors and can overfit if run too long", "It averages independent trees like bagging", "It never overfits", "It needs no tuning"], "answer": 0,
   "explain": "Boosting mainly reduces bias; learning rate, depth and early stopping control overfitting."}
]
```

> **Source:** Bruce & Bruce, *Practical Statistics for Data Scientists* (O'Reilly, 2017), ch. 6, "K-Nearest Neighbors" (distance metrics, standardization, choosing K, KNN as a feature engine), "Tree Models" (recursive partitioning, measuring impurity, stopping the tree from growing), "Bagging and the Random Forest" (variable importance, hyperparameters) and "Boosting" (the boosting algorithm, regularization, hyperparameters and cross-validation); scikit-learn documentation.
