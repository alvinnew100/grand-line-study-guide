# Representing data: categorical features, binning and polynomials

> **Before this lesson:** you should know how a scaler is fitted on training data and then applied with `transform`, from [Preprocessing and scaling](#/lesson/ml/preprocessing-scaling). The models used here are linear regression and logistic regression from [Linear models](#/lesson/ml/linear-models) and decision trees from [Naive Bayes, decision trees and ensembles](#/lesson/ml/bayes-trees-ensembles); the one fact you need about each is repeated below. pandas DataFrames were introduced in [The scikit-learn API and your first model](#/lesson/ml/sklearn-first-model).

## In plain words

A model can only do arithmetic. It multiplies numbers, adds them, and compares them with thresholds. Real data, though, arrives as a mixture of numbers ("age 39") and words ("works for the government", "has a master's degree"). Someone has to decide how each fact becomes one or more columns of numbers. That decision is called **feature engineering**: choosing how to represent the raw data as features, the measured columns a model reads.

Think of a pocket calculator. If you want it to compare holiday costs in three countries, you cannot type "France" into it. You have to turn your question into numbers first, and the way you do that limits which questions the calculator can answer. Type the countries as 1, 2 and 3 and the calculator will happily conclude that Spain (3) is "three times" France (1), which is nonsense. Feature engineering is the craft of doing that translation well.

Why this matters for a job: almost every business table contains category columns such as country, device type, product id or payment method, and a better representation of the same data often helps more than switching to a fancier model. Interviewers regularly ask "how would you encode a column with 10,000 different values?" and "why do linear models need feature engineering when tree models don't?". This lesson answers both.

## 1. Two kinds of feature

So far every dataset in this track has been a table of decimal numbers. Each column was a **continuous feature**: a measurement on a scale where any value in a range is possible and in-between values make sense, such as a petal length of 1.43 cm.

Many columns are not like that. A **categorical feature** (also called a discrete feature) takes one value from a fixed list of possibilities, called **categories** or **levels**: the brand of a phone, the colour of a car, the department a person works in. There are two sub-kinds:

- **Nominal** categories have no order at all. "Red", "green" and "blue" are different, but none is bigger than another.
- **Ordinal** categories have a natural order but no meaningful spacing. "Small < medium < large" is ordered, yet nobody can say that the step from small to medium equals the step from medium to large.

The number of different categories a feature has is its **cardinality**. "Gender" in an old census form has a cardinality of 2; a postcode column can have tens of thousands.

The running example in Müller & Guido is the **adult** dataset, drawn from the 1994 United States census. Each row is a working adult, and the task is to predict whether that person's income is above or below \$50,000 a year. Some features are continuous (`age`, `hours-per-week`) and others are categorical (`workclass`, `education`, `gender`, `occupation`). Since there are two possible answers, this is a binary classification task.

### Why a model cannot read a word

Take logistic regression, the classifier from the linear-models lesson. In words, it multiplies each feature by a learned number called a **weight**, adds the results and a constant called the **intercept**, and predicts the positive class when the total is above zero:

$$\hat y = w_1 x_1 + w_2 x_2 + \dots + w_p x_p + b > 0$$

Here $x_1, \dots, x_p$ are the $p$ feature values of one person, $w_1, \dots, w_p$ the weights and $b$ the intercept. A tiny worked example with two features: suppose training has produced $w_1 = 0.02$ for age, $w_2 = 0.03$ for hours per week, and $b = -2$. For a 40-year-old who works 45 hours, the total is $0.02 \times 40 + 0.03 \times 45 - 2 = 0.8 + 1.35 - 2 = 0.15$. That is above zero, so the model predicts "over \$50k".

Now try the same with `education = "Masters"`. There is no way to compute $0.05 \times \text{"Masters"}$. The category has to be turned into numbers before the model can use it.

### The tempting shortcut, and why it fails

The quickest idea is to number the categories. Suppose `workclass` has four values and we write Public = 0, Private = 1, Freelance = 2, Own company = 3. The model then adds $w \times \text{code}$ to its total. With $w = 0.4$, Private adds 0.4, Freelance adds 0.8 and Own company adds 1.2.

Look at what that forces on the model. Own company must have exactly three times the effect of Private. Freelance must sit exactly halfway between Private and Own company. Public must be at the far end. None of this comes from the data; it comes from the alphabet, or from whoever filled in the code list. If in reality freelancers earn the least, a single weight cannot express it, because the codes have put them in the middle. Integer codes invent an order and a spacing that nominal categories do not have.

## 2. One-hot encoding

The standard fix is **one-hot encoding**, also known as one-out-of-N encoding or **dummy variables**. A categorical feature with $k$ categories is replaced by $k$ new columns, one per category. Each new column holds 1 if the row belongs to that category and 0 otherwise. Exactly one of them is "hot" (equal to 1) in every row, which is where the name comes from.

| workclass | is Public | is Private | is Freelance | is Own company |
|---|---|---|---|---|
| Public | 1 | 0 | 0 | 0 |
| Private | 0 | 1 | 0 | 0 |
| Freelance | 0 | 0 | 1 | 0 |
| Own company | 0 | 0 | 0 | 1 |

Now each category gets **its own weight**. Suppose training gives the four columns weights $0.3, 0.1, -0.5$ and $0.6$. A freelancer's row is $(0, 0, 1, 0)$, so the workclass part of the total is $0.3 \times 0 + 0.1 \times 0 + (-0.5) \times 1 + 0.6 \times 0 = -0.5$. The other three columns are zero and drop out. The model is free to give freelancers the lowest effect and the self-employed the highest, in any order the data supports.

> [!NOTE]
> In statistics it is common to use only $k-1$ columns for $k$ categories, leaving one category (the **reference level**) as the row of all zeros. The reason: the $k$ one-hot columns always add up to 1 in every row, which duplicates what the intercept $b$ already does. When one column can be computed exactly from others, the columns are called **collinear**, and an ordinary least-squares fit has infinitely many equally good answers. In machine learning we usually keep all $k$ columns, because most models are **regularised** (they pay a small penalty for large weights, see the linear-models lesson), and the penalty picks one sensible answer. If you fit an unregularised linear model, pass `drop="first"` to `OneHotEncoder`.

### With pandas

The function `pd.get_dummies` one-hot encodes the chosen columns of a DataFrame.

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

**Reading this code line by line**

- `pd.DataFrame({...})` builds a small table from a dictionary: each key becomes a column name and each list becomes that column's values. These five rows imitate the adult data.
- `df["workclass"].value_counts()` lists every distinct value in the column with how many times it occurs. The output shows Private 3, State-gov 1, Self-emp 1.
- `pd.get_dummies(df, columns=[...], dtype=int)` replaces the two named columns with one 0/1 column per category. `dtype=int` asks for 0 and 1 instead of `True` and `False`. Columns not listed (`age`, `income`) are kept as they are.
- `list(dummies.columns)` prints the new column names. Each is the old name, an underscore and the category: `workclass_Private`, `education_Masters` and so on. Three workclass values became three columns and four education values became four.
- The last line drops the target column, keeps the first three rows (`head(3)`) and transposes the table (`.T`) so that columns become rows and fit on screen. Row 0, the 39-year-old government worker with a bachelor's degree, has a 1 in `workclass_State-gov` and in `education_Bachelors` and 0 everywhere else in those groups.

**Check the contents of each column first.** Data typed by people rarely has a clean, fixed list of categories. The same answer appears as `"Man"`, `"male"` and `"Male "` (with a trailing space), and one-hot encoding would make three separate columns for them. Use `value_counts()` on every categorical column and merge the variants before encoding.

After encoding, separate the features from the target: `X = dummies.drop(columns="income")` and `y = dummies["income"]`. Be careful not to leave the target, or any column computed from it, among the features. A model that can see the answer during training will look brilliant and be useless.

> [!WARNING]
> **The train/test trap.** If you call `get_dummies` separately on the training set and the test set, they can end up with different columns. A category that happens to be missing from the test set produces a missing column. A category that only appears in the test set produces an extra one. Even with the same set of columns, a different order means that column 7 means one thing in training and another in testing, and the model will silently use the wrong weights. Either call `get_dummies` once on the combined data before splitting, or, better, use scikit-learn's `OneHotEncoder`, which learns the list of categories during `fit` on the training data and applies exactly that list during `transform`.

### With scikit-learn

`OneHotEncoder` follows the same fit-then-transform pattern as the scalers in lesson 30: `fit` learns the categories from training data, and `transform` turns any data into columns using that learned list.

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

**Reading this code line by line**

- `train` and `test` are two-dimensional arrays with one column. scikit-learn always expects a table (rows by columns), even when there is only one feature, hence the double brackets.
- `OneHotEncoder(...)` creates the encoder. `handle_unknown="ignore"` says what to do with a category that was not seen during `fit`: write a row of zeros instead of stopping with an error. `sparse_output=False` asks for an ordinary array. By default the encoder returns a **sparse matrix**, a memory-saving format that stores only the non-zero entries; that is the right choice for real data with many categories, but a normal array is easier to print.
- `.fit(train)` learns the categories. `enc.categories_[0]` shows them for the first (and only) column: `['Private' 'Self-emp' 'State-gov']`, sorted alphabetically. That sorted order is the order of the output columns.
- `enc.transform(train)` gives four rows of three numbers. Row 0 is `[1, 0, 0]` (Private), row 1 is `[0, 0, 1]` (State-gov), and so on.
- `enc.transform(test)` encodes the test rows with the categories learned from training. `State-gov` becomes `[0, 0, 1]` as before, and `Never-worked`, which training never saw, becomes `[0, 0, 0]`.

The `handle_unknown="ignore"` setting matters in production. New categories turn up all the time (a new product line, a new country), and the default behaviour is to raise an error the first time one arrives. The problem *ml-one-hot* asks you to implement exactly this behaviour with NumPy.

Two further options are useful with messy data. `min_frequency=n` groups every category seen fewer than $n$ times into a single "infrequent" column, so that rare spellings and one-off values do not each get a column of their own. `max_categories=m` keeps at most $m$ columns per feature in the same way.

### Numbers can encode categoricals

Categorical data is not always stored as text. A census form might have numbered boxes, so `workclass` could arrive as the integers 0 to 8. An integer column is not automatically continuous. Ask two questions about it: is there a real **order**, and is the **distance** between values meaningful? A five-star rating passes both tests reasonably well; a workclass code passes neither and must be treated as categorical.

`pd.get_dummies` only encodes columns that hold text or pandas' own categorical type, so integer-coded categories are left alone unless you say otherwise:

```python-run
import pandas as pd
demo = pd.DataFrame({"integer_feature": [0, 1, 2, 1], "categorical_feature": ["socks", "fox", "socks", "box"]})
print(pd.get_dummies(demo, dtype=int).to_string(), "\n")                       # the integer column is left untouched
demo["integer_feature"] = demo["integer_feature"].astype(str)
print(pd.get_dummies(demo, dtype=int).to_string())                             # now both are encoded
```

The first printout still has a single `integer_feature` column holding 0, 1, 2, 1, next to three new columns for box, fox and socks. After `.astype(str)` converts the integers to the strings `"0"`, `"1"`, `"2"`, the second printout has three `integer_feature_...` columns as well. You could also name the integer column in `columns=[...]`. `OneHotEncoder` has no such ambiguity: it treats every column you hand it as categorical, so give it only the categorical ones.

### Other encodings worth knowing

One-hot encoding is the default, not the only option. Each alternative below solves a problem that one-hot encoding has.

- **Ordinal encoding** (`OrdinalEncoder`) gives each category one integer. That is the "tempting shortcut" from section 1, and it is the right choice in two situations: when the categories really are ordered (`low < medium < high`, and you choose the order), and for tree models, which split on thresholds and can isolate any code with two splits, so an arbitrary order hurts them much less than it hurts a linear model.
- **Target encoding** (also called mean encoding, `TargetEncoder`) replaces each category with the average target value for that category. Worked example: three training rows have postcode A with labels 1, 0 and 1, so A becomes $2/3 \approx 0.67$; two rows have postcode B with labels 0 and 0, so B becomes 0. One column now carries the information, however many postcodes there are, which makes it attractive for high-cardinality features. The danger is that each row's own label is part of its category's average, so the feature partly *contains the answer*. With rare categories the effect is large: a postcode seen once gets exactly its own label. The cure is to compute the averages **out of fold**, meaning each row's value is computed from other rows only (the cross-validation lesson explains folds), and to blend rare categories towards the overall average. scikit-learn's `TargetEncoder` does both during `fit_transform`.
- **Feature hashing** (`FeatureHasher`) runs each category name through a **hash function**, a fixed formula that turns any text into a number, and uses that number modulo $m$ to pick one of $m$ columns. No list of categories needs to be stored, and new categories are handled automatically. The price is **collisions**: two unrelated categories can land in the same column and become indistinguishable.
- **Learned embeddings** are used in neural networks. Each category gets a short list of numbers (for example 16 of them) that is adjusted during training like any other weight, so similar categories end up with similar lists. Module 8 covers embeddings.

## 3. Binning, discretisation, linear models and trees

The best representation depends on the model as well as on the data. Linear models and tree models react very differently to the same features, and this section shows why with one continuous feature.

The dataset is a "wave": one input $x$ between −3 and 3, and a target that rises overall while wiggling up and down (the formula is $\sin(4x) + x$ plus random noise). A linear regression can only draw one straight line through it, so it misses the wiggles. A decision tree splits the input range into intervals and predicts one constant value in each, giving a **piecewise-constant** function: a staircase of flat steps, which can follow the wiggles.

**Binning**, also called **discretisation**, gives a linear model some of that flexibility. The steps are:

1. Split the range of the feature into intervals called **bins**. With 10 equal-width bins between −3 and 3, each bin is 0.6 wide: the first covers −3 to −2.4, the second −2.4 to −1.8, and so on.
2. For every data point, record which bin it falls into. The value 0.5 lies between 0.0 and 0.6, which is the sixth bin (index 5 when counting from 0).
3. One-hot encode the bin number, giving 10 columns of which exactly one is 1.

A linear model on these 10 columns learns one weight per bin, which means **one constant prediction per bin**: a staircase, like a tree's, but with the step positions fixed in advance.

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

**Reading this code line by line**

- `rng.uniform(-3, 3, size=(200, 1))` draws 200 random inputs between −3 and 3 as a one-column table. The next line builds the wavy target and adds noise with `rng.randn`.
- `KBinsDiscretizer(n_bins=10, strategy="uniform", encode="onehot-dense")` is the binning tool. `strategy="uniform"` asks for equal-width bins; `encode="onehot-dense"` asks for one-hot columns as an ordinary array. `.fit(X_tr)` finds the smallest and largest training values and divides the range between them.
- `kb.bin_edges_[0]` prints the 11 edges of the 10 bins. They run from −2.97 to 2.92 rather than exactly −3 to 3, because the encoder uses the extremes of the actual training data.
- `kb.transform([[0.5]])` encodes the single value 0.5: the output has a 1 in position 5, the bin from −0.02 to 0.57.
- The loop fits four models: a linear regression and a tree, each on the raw feature and on the binned version, and prints the test $R^2$ (1 is perfect, 0 is no better than predicting the average, as explained in the generalisation lesson). `min_samples_leaf=5` stops the tree from making steps that contain fewer than five training points.

The output reads 0.832 for the linear model on the raw feature, 0.927 after binning, 0.955 for the tree on the raw feature and 0.927 for the tree after binning. Three conclusions:

- **The linear model became much more flexible.** Each bin now gets its own predicted level, so the model can follow the wave approximately instead of drawing one line through it.
- **The tree became less flexible.** A tree can already put its split points wherever they help most. Binning forces it to use our ten fixed intervals and throws away the information about where inside a bin a point lies. It is no coincidence that the binned tree and the binned linear model score exactly the same: once the only information left is "which bin", the best either model can do is predict one value per bin.
- Binning is therefore worth trying when you have a good reason to use a linear model (very large or high-dimensional data, where linear models are fast and robust) and some feature has a curved, non-straight relationship with the target.

Equal-width bins can leave some bins nearly empty when the data is bunched up. The alternative `strategy="quantile"` puts the edges at **quantiles**, the values below which a given fraction of the data lies, so that every bin holds roughly the same number of points.

## 4. Interactions and polynomials

Linear models gain from two further kinds of derived feature, both built from the original columns.

An **interaction feature** is the product of two features, such as $x_1 \times x_2$. It lets a linear model express "the effect of $x_1$ depends on the value of $x_2$". A **polynomial feature** is a power of a feature, such as $x^2$ or $x^3$, which lets a linear model draw a curve instead of a straight line. A linear model fitted on polynomial features is called **polynomial regression**.

**Interactions with bins.** The binned linear model from section 3 is a staircase: flat inside every bin. To let it slope, we could add the original $x$ as an extra column, but then all bins would share one slope. To give *each bin its own slope*, add a product column for every bin: (bin indicator) × $x$. Inside bin 5 that product equals $x$, and everywhere else it is 0, so its weight acts as the slope for bin 5 alone. With 10 bins this means 20 columns: 10 levels and 10 slopes.

**Polynomial features.** `PolynomialFeatures(degree=d)` adds all powers and products of the input features up to total degree $d$. For two features $a$ and $b$ at degree 2, the products of degree 2 are $a^2$, $ab$ and $b^2$.

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

**Reading this code line by line**

- `X` is one row with two features, $a = 2$ and $b = 3$.
- `PolynomialFeatures(degree=2, include_bias=False)` creates the transformer. `include_bias=False` leaves out a column of constant 1s, which the model's intercept already provides.
- `get_feature_names_out(["a", "b"])` names the outputs: `a`, `b`, `a^2`, `a b`, `b^2`.
- `poly.transform(X)` computes them for our row: $2, 3, 4, 6, 9$, since $2^2 = 4$, $2 \times 3 = 6$ and $3^2 = 9$.
- `interaction_only=True` keeps the products of different features and drops the pure powers, leaving `a`, `b`, `a b`.
- The loop counts how many columns degree 2 produces for 5, 13 and 50 input features: 20, 104 and 1,325.

That last count grows fast. In words: the number of polynomial features is the number of ways to choose a combination of features whose powers add up to at most $d$, minus the constant term. As a formula, with $p$ input features and degree $d$,

$$\text{number of output features} = \binom{p+d}{d} - 1.$$

The symbol $\binom{n}{k}$ ("n choose k") counts the ways to choose $k$ items from $n$. Worked example: $p = 13$, $d = 2$ gives $\binom{15}{2} - 1 = \frac{15 \times 14}{2} - 1 = 105 - 1 = 104$, matching the output. With 50 features and degree 3 the count is already 23,425. Expansions like this need regularisation and plenty of data, or they overfit.

**Behaviour at the edges.** High-degree polynomials tend to swing wildly near the ends of the data range and in regions with few points, because a high power such as $x^{10}$ changes enormously for small changes in $x$ once $|x| > 1$. The book contrasts this with a kernel support vector machine (lesson 23) fitted on the original feature, which produces a similarly flexible curve without any explicit expansion.

**Who benefits?** In the book, adding degree-2 interactions and powers to the 13 features of a housing dataset lifts a `Ridge` regression (a regularised linear model) from a test $R^2$ of 0.62 to 0.75, while a random forest scores about 0.80 on the original features and slightly *worse* with the expanded ones. (That housing dataset has since been removed from scikit-learn, as the generalisation lesson explains, so the demo below uses generated data.) The rule of thumb: expanding features helps simple models; flexible models such as forests find interactions on their own and gain little.

```python-run
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

The target here is $x_0 x_1 + x_2^2$ plus a little noise: one interaction and one square, and no straight-line part at all. `make_pipeline` chains the steps so that the features are expanded and scaled before the ridge model sees them (pipelines get their own lesson, 60). `cross_val_score(..., cv=5)` scores each model five times on different held-out slices and we print the average (lesson 50 explains this).

The output is about −0.006 for ridge on the raw features, 0.997 for ridge on degree-2 features and 0.689 for the forest. Ridge on raw features is no better than predicting the average, because no straight-line combination of $x_0$, $x_1$ and $x_2$ can describe a product or a square. Once the products and squares are offered as columns, the right answer is a plain weighted sum of two of them, and the linear model finds it almost perfectly. The forest gets a decent score with no help, by approximating the curved surface with many small steps, but it cannot match a model whose features match the truth.

> [!INTERVIEW]
> **"Why one-hot encode instead of using integer codes? And when is one-hot a problem?"** Integer codes impose a false order and spacing on nominal categories: a linear model would have to treat category 3 as three times category 1. One-hot gives each category its own weight. The problems come with **high cardinality** (thousands of mostly-zero columns, many categories seen only a few times): use hashing, out-of-fold target encoding or learned embeddings instead. For tree ensembles, deep chains of splits on single one-hot columns are inefficient, so ordinal codes or native categorical support (LightGBM, CatBoost, scikit-learn's `HistGradientBoosting` models) usually work better.

## 5. Worked example: what an interaction term lets a linear model say

Suppose we predict a salary (in thousands) from years of experience $x_1$ and from whether the person has a university degree, $x_2$, which is 1 for yes and 0 for no. A plain linear model is

$$\hat y = b + w_1x_1 + w_2x_2 .$$

Fill in the two possible values of $x_2$. For people without a degree ($x_2 = 0$) the prediction is the line $b + w_1x_1$. For people with a degree ($x_2 = 1$) it is $(b + w_2) + w_1x_1$. The two lines have **different starting heights and the same slope**. The model can say "a degree adds a fixed amount". It cannot say "a degree makes each year of experience worth more".

Add the product $x_1x_2$ as a third feature:

$$\hat y = b + w_1x_1 + w_2x_2 + w_3\,x_1x_2 .$$

Without a degree, $x_2 = 0$ wipes out both new terms and the line is still $b + w_1x_1$. With a degree it becomes $(b + w_2) + (w_1 + w_3)x_1$. Now the slopes differ by $w_3$. Numbers make it concrete: with $b = 30$, $w_1 = 1$, $w_2 = 5$ and $w_3 = 1.5$, a person with 10 years and no degree is predicted $30 + 10 = 40$, and a person with 10 years and a degree $30 + 10 + 5 + 15 = 60$. At 20 years the gap widens from 20 to 35.

One extra column gave the model a new kind of statement. The model is still **linear in its parameters** (the prediction is still a weighted sum, only of a different set of columns), so the fitting procedure, the regularisation and the way you read the weights all stay the same.

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

**Reading this code line by line**

- `years` holds 500 random experience values between 0 and 20; `rng.randint(0, 2, n)` gives 500 random 0s and 1s for `degree`.
- `salary` is generated from exactly the formula above with $b = 30$, $w_1 = 1$, $w_2 = 5$, $w_3 = 1.5$, plus random noise with a spread of 2.
- `np.column_stack([years, degree])` puts the columns side by side into a feature table. The second model's table has the product `years * degree` as a third column.
- `.coef_` holds the learned weights, one per column, rounded to two decimals.

The plain model reaches $R^2 = 0.904$ with weights 1.83 and 19.95; the model with the interaction reaches 0.984 with weights 1.02, 5.08 and 1.50. The plain model's numbers are distorted because it must squeeze two different slopes into one. Its slope of 1.83 lies between the true 1.0 (no degree) and 2.5 (with a degree), and its "degree bonus" of about 20 is the true gap at the average experience of 10 years ($5 + 1.5 \times 10 = 20$). With the interaction column, the three weights recover the true values and can be read directly. A tree model would discover this structure by splitting on `degree` first and then following a different trend on each side, which is why trees rarely need the product feature.

## 6. Pitfalls

- **Fitting the encoder on all the data.** Learn the categories, bin edges or target averages from the training set only, then apply them to the test set. Otherwise information from the test set leaks into training (lesson 61 is devoted to this).
- **Unseen and rare categories.** Plan for categories that appear only after deployment (`handle_unknown`) and for categories so rare that their weight is pure noise (`min_frequency`).
- **Missing values.** A blank in a categorical column is often informative ("did not answer"). Treat it as its own category rather than dropping the row.
- **Too many columns.** One-hot encoding a high-cardinality feature, or a high-degree polynomial expansion, can produce more columns than rows. Regularise, or choose a more compact encoding.
- **Reading one-hot weights.** With all $k$ columns kept, only the *differences* between category weights are meaningful, since adding the same amount to all of them and subtracting it from the intercept gives identical predictions.

## Summary

- Models need numbers. Nominal categories should be one-hot encoded, not numbered; check `value_counts()` and clean the values first.
- Fit encoders on the training data and make sure training and test data get the same columns: `OneHotEncoder(handle_unknown="ignore")` does both.
- An integer column is not necessarily continuous; ask whether its order and spacing mean anything.
- For high-cardinality features, consider target encoding (computed out of fold), hashing or embeddings.
- Binning, interactions and polynomials make linear models far more expressive. Tree models rarely need them and binning can hurt them.
- Feature expansion grows combinatorially, so pair it with regularisation.

## Glossary

- **Feature engineering**: choosing how to represent raw data as the numeric features a model reads.
- **Continuous feature**: a measurement on a scale where in-between values make sense.
- **Categorical feature**: a feature whose value is one of a fixed list of categories.
- **Nominal / ordinal**: categories with no order / categories with an order but no meaningful spacing.
- **Cardinality**: the number of distinct categories a feature has.
- **One-hot encoding (dummy variables)**: one 0/1 column per category, with exactly one 1 per row.
- **Reference level**: the category left out when only $k-1$ dummy columns are used.
- **Collinear**: describes columns where one can be computed exactly from the others.
- **Sparse matrix**: a storage format that keeps only the non-zero entries.
- **Ordinal encoding**: one integer code per category.
- **Target (mean) encoding**: replacing a category with the average target of its rows, ideally computed out of fold.
- **Feature hashing**: mapping categories to a fixed number of columns with a hash function; collisions are possible.
- **Binning (discretisation)**: replacing a continuous value by the interval it falls into.
- **Piecewise-constant**: a function made of flat steps, one value per interval.
- **Quantile**: the value below which a given fraction of the data lies.
- **Interaction feature**: the product of two features, letting one feature's effect depend on another.
- **Polynomial feature / polynomial regression**: a power or product of features / a linear model fitted on them.

## Check yourself

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
   "explain": "With 'ignore' no column is set; the default behaviour is to raise an error."},
  {"q": "Why must target encoding be computed out of fold?", "options": ["Otherwise each row's own label is inside its category's average, leaking the answer", "Because it is too slow on the full data", "Because it only works on numeric features", "Because one-hot encoding requires it"], "answer": 0,
   "explain": "A category seen once would be encoded as exactly its own label, so the model learns to read the answer."}
]
```

> **Source:** Müller & Guido, *Introduction to Machine Learning with Python*, ch. 4 ("Categorical Variables", "One-Hot-Encoding (Dummy Variables)", "Numbers Can Encode Categoricals", "Binning, Discretization, Linear Models, and Trees", "Interactions and Polynomials"); scikit-learn User Guide, "Preprocessing data: Encoding categorical features".
