# Representing data: categorical features, binning and polynomials

Until now every dataset in this track was a numeric table: rows of decimal values, with each column a
**continuous feature**. Real data is rarely like that. It contains **categorical** (discrete) features
such as a product's brand or colour, and the way you represent your data can matter more than which model
you choose. The question of how best to represent data for a particular application is called **feature
engineering**. On applied projects it takes up a large share of a practitioner's time, and it is the subject of
chapter 4 of Müller & Guido.

## 1. Categorical variables

The book's running example is the **adult** census dataset. The task is to predict whether a worker's
income is above or below \$50k, from features such as `age` and `hours-per-week` (continuous) and
`workclass`, `education`, `gender` and `occupation` (categorical).

Suppose we use logistic regression, $\hat y = w^\top x + b > 0$. The formula multiplies each feature by a
number, so $x$ must be numeric. A value like `"Masters"` cannot go in. We need a different representation.

### One-hot encoding (dummy variables)

The most common approach is **one-hot encoding**, also called one-out-of-N encoding or dummy variables. A
categorical feature is replaced by one new 0/1 feature **per category**. Say `workclass` takes the values
`Public`, `Private`, `Freelance` and `Own company`. You get four
new columns, and exactly one of them is 1 for each person.

| workclass | is Public | is Private | is Freelance | is Own company |
|---|---|---|---|---|
| Public | 1 | 0 | 0 | 0 |
| Private | 0 | 1 | 0 | 0 |
| Freelance | 0 | 0 | 1 | 0 |

> [!NOTE]
> In statistics it is common to encode $k$ categories with $k-1$ columns, to avoid making the design
> matrix rank-deficient. The last category is then represented by all zeros. In ML we usually keep all $k$
> columns, since regularised models don't mind the redundancy. Use `drop="first"` for an unregularised
> linear model.

### With pandas

```python-run
import pandas as pd
df = pd.DataFrame({
    "age": [39, 50, 38, 53, 28],
    "workclass": ["State-gov", "Self-emp", "Private", "Private", "Private"],
    "education": ["Bachelors", "Bachelors", "HS-grad", "11th", "Masters"],
    "income": ["<=50K", "<=50K", "<=50K", ">50K", ">50K"],
})
print(df["workclass"].value_counts(), "\n")           # ALWAYS check the values first
dummies = pd.get_dummies(df, columns=["workclass", "education"], dtype=int)
print(list(dummies.columns))
print(dummies.drop(columns="income").head(3).T)   # transposed so every column is visible
```

**Check the contents of each column first** with `value_counts()`. Human-entered data often has no fixed
set of categories and contains spelling and capitalisation variants (`"Man"`, `"male"`, `"Male "`). These
must be cleaned and merged before encoding.

After encoding, separate the target from the features (`X = dummies.drop(columns="income")`). Be careful
not to leave the target, or anything derived from it, in the feature matrix.

> [!WARNING]
> **The train/test trap.** If you call `get_dummies` separately on the training and test sets, the two
> may get different columns. A category missing from the test set means a missing column. A different
> order means the same column position has different meanings. Either call `get_dummies` on the combined
> DataFrame before splitting, or (better) use scikit-learn's `OneHotEncoder`, which learns the categories
> in `fit` and applies them in `transform`.

### With scikit-learn

```python-run
import numpy as np
from sklearn.preprocessing import OneHotEncoder
train = np.array([["Private"], ["State-gov"], ["Private"], ["Self-emp"]])
test = np.array([["State-gov"], ["Never-worked"]])        # the second category was never seen in training

enc = OneHotEncoder(handle_unknown="ignore", sparse_output=False).fit(train)
print("categories_:", enc.categories_[0])
print("train:\n", enc.transform(train))
print("test (unknown category -> all zeros):\n", enc.transform(test))
```

`handle_unknown="ignore"` matters in production. New categories appear all the time, and the default is to
raise an error. You implement this behaviour in *ml-one-hot*.

### Numbers can encode categoricals

Categorical features are often stored as integers. In the adult data, `workclass` might be recorded as
0–8 because the census form had numbered boxes. An integer column is not automatically continuous. Ask
whether there is an *order* and a meaningful distance: a five-star rating has one, and a workclass code
does not. `pd.get_dummies` only converts string or categorical columns by default, so convert such integer
columns to strings first (`df["col"].astype(str)`), or list them in `columns=[...]`. `OneHotEncoder`
treats every column you give it as categorical.

```python-run
import pandas as pd
demo = pd.DataFrame({"integer_feature": [0, 1, 2, 1], "categorical_feature": ["socks", "fox", "socks", "box"]})
print(pd.get_dummies(demo, dtype=int).to_string(), "\n")                       # the integer column is left untouched
demo["integer_feature"] = demo["integer_feature"].astype(str)
print(pd.get_dummies(demo, dtype=int).to_string())                             # now both are encoded
```

Other encodings worth knowing for interviews:

- **Ordinal encoding** (`OrdinalEncoder`): one integer per category. This is fine for tree models, and for
  categories that really are ordered (`low < medium < high`).
- **Target (mean) encoding**: replace a category with the average target for that category. It is powerful
  for high-cardinality features such as zip codes, but it leaks the target unless computed out-of-fold.
  `TargetEncoder` does this for you.
- **Hashing** (`FeatureHasher`): map categories into a fixed number of buckets. No vocabulary to store,
  at the price of collisions.
- **Learned embeddings**: in neural networks, each category gets a trainable dense vector (module 8).

## 2. Binning, discretisation, linear models and trees

The best representation depends on the model as well as on the data. Linear models and tree models react
very differently to the same features.

On the 1-D `wave` regression data, a linear model can only fit a straight line. A decision tree builds a
far more complex piecewise-constant model. A simple trick that gives a linear model extra flexibility on a continuous input
is **binning** (discretisation): split the feature's range into bins (say 10 equal-width bins from −3 to
3), record which bin each point falls into, and one-hot encode the bin. The linear model then learns a
separate constant for each bin.

```python-run
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor
from sklearn.preprocessing import KBinsDiscretizer
from sklearn.model_selection import train_test_split

rng = np.random.RandomState(42)
X = rng.uniform(-3, 3, size=(200, 1))
y = np.sin(4 * X[:, 0]) + X[:, 0] + 0.3 * rng.randn(200)       # the book's "wave" pattern
X_tr, X_te, y_tr, y_te = train_test_split(X, y, random_state=0)

kb = KBinsDiscretizer(n_bins=10, strategy="uniform", encode="onehot-dense").fit(X_tr)
print("bin edges:", kb.bin_edges_[0].round(2))
print("x = 0.5 becomes:", kb.transform([[0.5]])[0].astype(int))
for name, model, tr, te in [
    ("linear, raw feature", LinearRegression(), X_tr, X_te),
    ("linear, 10 bins", LinearRegression(), kb.transform(X_tr), kb.transform(X_te)),
    ("tree, raw feature", DecisionTreeRegressor(min_samples_leaf=5, random_state=0), X_tr, X_te),
    ("tree, 10 bins", DecisionTreeRegressor(min_samples_leaf=5, random_state=0), kb.transform(X_tr), kb.transform(X_te)),
]:
    print(f"{name:20s} test R2 = {model.fit(tr, y_tr).score(te, y_te):.3f}")
```

The book's conclusions:

- The **linear model became much more flexible**. Each bin now gets its own predicted level.
- The **tree became less flexible**. Trees can already learn to split the data wherever is useful, so
  binning only removes information.
- Binning helps mainly when you have good reasons to use a linear model (the dataset is very large and
  high-dimensional) and some features have a nonlinear relation to the output.

## 3. Interactions and polynomials

Linear models in particular also benefit from two further kinds of derived feature: **interaction**
terms and **polynomial** terms built from the original columns.

**Interactions.** The binned linear model learns a constant per bin. We can give it back a slope by adding
the original feature. But then there is a single slope shared by every bin. To get a *separate slope in
each bin*, add **product features**: bin indicator × original feature. A product feature means "the effect
of $x$ depends on which bin we are in". More generally, an interaction $x_1x_2$ lets a linear model
express "the effect of $x_1$ depends on $x_2$".

**Polynomials.** `PolynomialFeatures(degree=d)` adds powers $x^2, x^3, \dots$ and, for several input
features, all products up to degree $d$. A linear model on polynomial features is **polynomial
regression**, which fits a smooth curve.

```python-run
import numpy as np
from sklearn.preprocessing import PolynomialFeatures
X = np.array([[2.0, 3.0]])
poly = PolynomialFeatures(degree=2, include_bias=False).fit(X)
print("names:", list(poly.get_feature_names_out(["a", "b"])))
print("values:", poly.transform(X)[0])
print("interaction_only:", list(PolynomialFeatures(2, interaction_only=True, include_bias=False).fit(X).get_feature_names_out(["a", "b"])))
for p in [5, 13, 50]:
    n_out = PolynomialFeatures(2, include_bias=False).fit(np.zeros((1, p))).n_output_features_
    print(f"{p} features -> {n_out} features at degree 2")
```

The number of features grows quickly, as $\binom{p+d}{d}-1$. On the Boston housing data in the book,
13 features become 105 at degree 2 (104 plus the constant column).

**Behaviour at the edges.** High-degree polynomials tend to behave wildly at the boundaries of the data
and in regions with few points. For comparison, the book fits a kernel SVM on the original feature and
gets a similarly complex prediction without any explicit transformation.

**Who benefits?** On Boston housing, adding interactions and polynomials improves `Ridge` substantially
(test $R^2$ from 0.62 to 0.75 in the book). A random forest scores about 0.80 *without* the extra features,
and adding them makes it slightly worse. The lesson: expanding features helps simple models. Complex
models such as forests can find interactions themselves.

```python-run
from sklearn.datasets import load_diabetes
from sklearn.preprocessing import PolynomialFeatures, StandardScaler
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import cross_val_score
from sklearn.pipeline import make_pipeline
import numpy as np

rng = np.random.RandomState(0)
X = rng.uniform(-2, 2, size=(300, 3))
y = X[:, 0] * X[:, 1] + X[:, 2] ** 2 + 0.1 * rng.randn(300)     # the target depends on an interaction and a square
for name, model in [
    ("ridge, raw features", make_pipeline(StandardScaler(), Ridge())),
    ("ridge, degree-2 features", make_pipeline(PolynomialFeatures(2), StandardScaler(), Ridge())),
    ("random forest, raw features", RandomForestRegressor(n_estimators=50, random_state=0)),
]:
    print(f"{name:28s} CV R2 = {cross_val_score(model, X, y, cv=5).mean():.3f}")
```

> [!INTERVIEW]
> **"Why one-hot encode instead of using integer codes? And when is it a problem?"** Integer codes impose
> a false order and spacing on nominal categories. A linear model would have to treat "category 3" as three
> times "category 1". One-hot gives each category its own weight. The problems come with **high
> cardinality** (thousands of sparse columns): use hashing, target encoding or embeddings. For trees, deep
> splits on one-hot columns are inefficient, so ordinal codes or native categorical support (LightGBM,
> CatBoost, `HistGradientBoosting`) work better.

## 4. Worked example: what an interaction term lets a linear model say

Suppose we predict a salary from years of experience $x_1$ and from whether the person has a degree,
$x_2\in\{0,1\}$. A plain linear model is

$$\hat y = b + w_1x_1 + w_2x_2 .$$

For people without a degree this is the line $b + w_1x_1$. For people with a degree it is
$(b + w_2) + w_1x_1$. The two lines have **different intercepts and the same slope**. The model can say
"a degree adds a fixed amount". It cannot say "a degree makes each year of experience worth more".

Add the product $x_1x_2$:

$$\hat y = b + w_1x_1 + w_2x_2 + w_3\,x_1x_2 .$$

Without a degree the line is still $b + w_1x_1$. With a degree it becomes $(b + w_2) + (w_1 + w_3)x_1$.
Now the slopes differ by $w_3$. One extra feature gave the model a new kind of statement. The model is
still linear in its parameters, so everything about fitting and regularising it stays the same.

```python-run
import numpy as np
from sklearn.linear_model import LinearRegression
rng = np.random.RandomState(0)
n = 500
years = rng.uniform(0, 20, n)
degree = rng.randint(0, 2, n)
salary = 30 + 1.0 * years + 5 * degree + 1.5 * years * degree + rng.normal(0, 2, n)   # in thousands

plain = LinearRegression().fit(np.column_stack([years, degree]), salary)
inter = LinearRegression().fit(np.column_stack([years, degree, years * degree]), salary)
print("without interaction: R2 =", round(plain.score(np.column_stack([years, degree]), salary), 3), " coefficients:", plain.coef_.round(2))
print("with interaction:    R2 =", round(inter.score(np.column_stack([years, degree, years * degree]), salary), 3), " coefficients:", inter.coef_.round(2))
print("true values: slope 1.0, degree bonus 5, extra slope with a degree 1.5")
```

The plain model's coefficients are distorted. It has to stretch one slope and one bonus to cover an
effect it cannot represent. With the interaction, the three coefficients recover the true values and can
be read directly. A tree-based model would find this structure by splitting on `degree` first and then
fitting different trends on each side, which is why it rarely needs the product feature.

## Summary

- Models need numbers. Nominal categories → one-hot encoding. Check `value_counts()` first.
- Fit the encoding on the training data, and make sure train and test share the same columns
  (`OneHotEncoder(handle_unknown="ignore")`).
- Integers are not necessarily continuous. Decide per feature.
- Binning, interactions and polynomials make linear models far more expressive. Tree models rarely need
  them.
- Feature expansion grows combinatorially, so combine it with regularisation.

```quiz
[
  {"q": "Why can't logistic regression use the raw string values of a 'workclass' column?", "options": ["Its prediction multiplies feature values by weights, so features must be numeric", "Strings use too much memory", "Logistic regression only accepts binary features", "scikit-learn cannot read text files"], "answer": 0,
   "explain": "w·x + b requires numbers; the categories must first be encoded."},
  {"q": "What is the danger of calling pd.get_dummies separately on train and test DataFrames?", "options": ["The two results can have different columns or column meanings", "It is slower", "It changes the target", "It removes numeric columns"], "answer": 0,
   "explain": "Categories absent from one split produce missing columns, so the matrices no longer line up."},
  {"q": "A column stores workclass as integer codes 0–8. For a linear model you should…", "options": ["treat it as categorical and one-hot encode it", "use it directly as a continuous feature", "standardise it and use it", "take its logarithm"], "answer": 0,
   "explain": "The codes have no order or meaningful distances."},
  {"q": "After binning a single feature into 10 one-hot bins, a linear model can represent…", "options": ["a piecewise-constant function with one value per bin", "only a straight line", "any smooth curve exactly", "a decision tree of depth 10"], "answer": 0,
   "explain": "Each bin gets its own coefficient, i.e. its own constant prediction."},
  {"q": "How does binning typically affect a decision tree on the same feature?", "options": ["It makes the tree less flexible, since the tree could already choose its own split points", "It always improves the tree", "It has no effect at all", "It makes the tree linear"], "answer": 0,
   "explain": "Binning discards within-bin information that the tree could have used."},
  {"q": "PolynomialFeatures(degree=2, include_bias=False) applied to features (a, b) produces…", "options": ["a, b, a², ab, b²", "a², b²", "a, b, ab", "a, b, a², b², a³, b³"], "answer": 0,
   "explain": "All monomials of degree 1 and 2, including the interaction term."},
  {"q": "OneHotEncoder(handle_unknown='ignore') encodes a category not seen during fit as…", "options": ["a row of all zeros", "a new extra column", "NaN values", "an exception"], "answer": 0,
   "explain": "With 'ignore' no column is set; the default behaviour is to raise an error."}
]
```

> **Source:** Müller & Guido, *Introduction to Machine Learning with Python*, ch. 4 ("Categorical Variables", "One-Hot-Encoding (Dummy Variables)", "Numbers Can Encode Categoricals", "Binning, Discretization, Linear Models, and Trees", "Interactions and Polynomials"); scikit-learn User Guide, "Preprocessing data: Encoding categorical features".
