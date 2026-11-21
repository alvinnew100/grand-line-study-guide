# Multiple regression: assessment, cross-validation and model selection

> **Before this lesson:** [Simple linear regression and prediction intervals](#/lesson/statistics/simple-regression) (least squares, $R^2$, residual standard error, reading statsmodels output). Cross-validation is introduced here from the statistical side; the [ML track's cross-validation lesson](#/lesson/ml/cross-validation) covers its scikit-learn mechanics in depth.

## In plain words

Real outcomes depend on many things at once. A house price depends on floor area, number of bedrooms and bathrooms, age, location and more. **Multiple linear regression** extends the straight line to several predictors, so that each coefficient measures the effect of one predictor *while holding the others fixed*. This lesson shows how to fit and read such a model, how to judge it (RMSE, $R^2$, adjusted $R^2$), how to check it honestly on new data with **cross-validation**, how to choose which predictors to keep (AIC, BIC and stepwise methods), and how **weighted regression** handles records of unequal reliability.

An everyday picture: comparing two flats by price alone is unfair if one is twice the size. You mentally adjust: "per square metre, and allowing for age, which is better value?" Multiple regression does that adjusting systematically for every predictor at once.

Why it matters for a job: multiple regression is the standard tool for estimating effects while controlling for other factors ("did the redesign raise revenue after accounting for seasonality and traffic mix?") and a strong baseline for prediction. Interviewers ask you to interpret a coefficient "holding other variables constant", explain why a coefficient changed sign when another variable was added, compare $R^2$ with adjusted $R^2$, and describe how you would select features without overfitting.

## 1. The model

With $p$ predictors $X_1, \dots, X_p$:

$$Y = b_0 + b_1 X_1 + b_2 X_2 + \dots + b_p X_p + e$$

Least squares still chooses the coefficients that minimise the residual sum of squares. Geometrically the "line" becomes a flat surface (a plane, or hyperplane in more dimensions). The key interpretive change: $b_j$ is the expected change in $Y$ for a one-unit increase in $X_j$ **with all other predictors held constant**.

We simulate 500 house sales so that we know the truth: price $= 50{,}000 + 150 \times \text{sqft} - 10{,}000 \times \text{bedrooms} + 8{,}000 \times \text{bathrooms} - 600 \times \text{age}$ plus noise. Bedrooms and bathrooms are correlated with floor area, and two pure-noise columns are included to see how the methods treat useless predictors.

```python-run
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
rng = np.random.default_rng(41)
n = 500
sqft = rng.normal(1800, 500, n).clip(600, 4000)
bedrooms = np.clip(np.round(sqft / 600 + rng.normal(0, 0.7, n)), 1, 7)
bathrooms = np.clip(np.round(sqft / 900 + rng.normal(0, 0.5, n) * 2) / 2, 1, 5)
age = rng.uniform(0, 80, n)
noise1, noise2 = rng.normal(size=n), rng.normal(size=n)
price = 50_000 + 150 * sqft - 10_000 * bedrooms + 8_000 * bathrooms - 600 * age + rng.normal(0, 40_000, n)
homes = pd.DataFrame(dict(price=price, sqft=sqft, bedrooms=bedrooms, bathrooms=bathrooms, age=age, noise1=noise1, noise2=noise2))
full = smf.ols("price ~ sqft + bedrooms + bathrooms + age + noise1 + noise2", data=homes).fit()
print(pd.DataFrame({"coef": full.params, "t": full.tvalues, "p": full.pvalues}).round(3))
print(f"R^2 {full.rsquared:.4f}  adjusted R^2 {full.rsquared_adj:.4f}  RSE {np.sqrt(full.scale):,.0f}")
print("bedrooms alone:", smf.ols("price ~ bedrooms", data=homes).fit().params.round(0).to_dict())
```

**Reading this code line by line**

- `.clip(600, 4000)` and `np.clip(..., 1, 7)` keep simulated values in realistic ranges; `np.round(...)` makes bedroom counts whole numbers, and dividing a rounded value by 2 gives bathrooms in half steps.
- `dict(price=price, ...)` builds a dictionary with keyword syntax; pandas turns it into columns.
- The formula `"price ~ sqft + bedrooms + ..."` lists predictors separated by `+`.
- `full.scale` is the estimated error variance, so its square root is the residual standard error.
- The last line fits price on bedrooms alone for comparison; `.to_dict()` turns the coefficients into a dictionary for compact printing.

Reading the output:

- **sqft**: 157.4 dollars per square foot (true 150), $t = 28.7$.
- **bedrooms**: $-14{,}237$ (true $-10{,}000$). Negative! Holding floor area fixed, an extra bedroom means the same space is cut into smaller rooms, which buyers value less.
- **age**: $-450$ per year (true $-600$).
- **bathrooms**: 8,912 (true 8,000) but with $p = 0.089$: the data cannot pin it down precisely because bathrooms move with floor area.
- **noise1, noise2**: tiny coefficients with p-values of 0.82 and 0.93, correctly flagged as useless.

Now look at the last line: regressing price on bedrooms *alone* gives $+37{,}249$ per bedroom. Both are "right"; they answer different questions. Alone, bedrooms act as a stand-in for size (bigger houses have more bedrooms and cost more). With size held constant, the remaining bedroom effect is negative. A coefficient's meaning always depends on which other predictors are in the model. This is the first glimpse of **confounding**, developed in [Factor variables and interpreting regression](#/lesson/statistics/factors-interpretation).

## 2. Assessing the model

- **Root mean squared error** (RMSE): $\sqrt{\frac{1}{n}\sum (Y_i - \hat{Y}_i)^2}$, the typical prediction error in the units of $Y$. The most important number when the goal is prediction.
- **Residual standard error** (RSE): the same but dividing by the degrees of freedom $n - p - 1$; almost identical to RMSE for large $n$. Here about 38,530 dollars.
- **$R^2$**: the share of variance explained, 0.7616 here.
- **Adjusted $R^2$**: $R^2$ penalised for the number of predictors:

$$R^2_\text{adj} = 1 - (1 - R^2)\frac{n - 1}{n - p - 1}$$

Plain $R^2$ never decreases when you add a predictor, even pure noise, because least squares can always use an extra column to fit the training data slightly better. Adjusted $R^2$ (0.7587 here) falls when an added predictor contributes less than chance would. It is a crude guard against overfitting; cross-validation is a better one.

## 3. Cross-validation: judging a model on data it has not seen

Every in-sample measure (RSE, $R^2$) is computed on the same data used to fit the model, so it is optimistic. The honest test is performance on new data. **Holdout** validation sets aside part of the data, fits on the rest, and measures error on the held-out part. **k-fold cross-validation** repeats this systematically:

1. Split the data into $k$ equal parts (**folds**), typically 5 or 10.
2. For each fold: fit the model on the other $k - 1$ folds, predict the held-out fold, record the error.
3. Average the $k$ errors.

Every record is used for testing exactly once, and the average is far more stable than a single split. The demo below uses scikit-learn for this, alongside a model-selection comparison.

## 4. Model selection: which predictors to keep?

Adding predictors has costs: more variance in the estimates, harder interpretation, more data to collect in production, and overfitting. The principle of **parsimony** (Occam's razor) says to prefer the simpler of two models that perform about equally well.

Criteria that trade fit against complexity:

- **AIC** (Akaike's information criterion): $AIC = 2P + n\log(RSS/n)$ for linear regression, where $P$ is the number of estimated parameters. Lower is better; each extra parameter must reduce RSS enough to pay its penalty of 2.
- **BIC** (Bayesian information criterion): replaces the penalty 2 by $\log(n)$, so it penalises complexity more heavily for $n > 7$ and tends to choose smaller models.
- **Mallows' Cp** and adjusted $R^2$ are related criteria.

Search strategies:

- **All-subsets regression**: fit every combination of predictors; feasible only for small $p$ ($2^p$ models).
- **Forward selection**: start with no predictors; repeatedly add the one that improves the criterion most; stop when nothing helps.
- **Backward elimination**: start with all predictors; repeatedly drop the least useful.
- **Stepwise regression**: alternate additions and removals.
- **Penalised regression** (ridge and lasso): instead of discrete in-or-out decisions, shrink coefficients towards zero; the lasso sets some exactly to zero. See the [ML track's linear models lesson](#/lesson/ml/linear-models).

```python-run
import numpy as np
import pandas as pd
from itertools import combinations
import statsmodels.formula.api as smf
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import cross_val_score, KFold
rng = np.random.default_rng(41)
n = 500
sqft = rng.normal(1800, 500, n).clip(600, 4000)
bedrooms = np.clip(np.round(sqft / 600 + rng.normal(0, 0.7, n)), 1, 7)
bathrooms = np.clip(np.round(sqft / 900 + rng.normal(0, 0.5, n) * 2) / 2, 1, 5)
age = rng.uniform(0, 80, n)
noise1, noise2 = rng.normal(size=n), rng.normal(size=n)
price = 50_000 + 150 * sqft - 10_000 * bedrooms + 8_000 * bathrooms - 600 * age + rng.normal(0, 40_000, n)
homes = pd.DataFrame(dict(price=price, sqft=sqft, bedrooms=bedrooms, bathrooms=bathrooms, age=age, noise1=noise1, noise2=noise2))
cands = ["sqft", "bedrooms", "bathrooms", "age", "noise1", "noise2"]
rows = []
for k in range(1, len(cands) + 1):
    for subset in combinations(cands, k):
        fit = smf.ols("price ~ " + " + ".join(subset), data=homes).fit()
        rows.append((" + ".join(subset), fit.aic, fit.bic, fit.rsquared_adj))
res = pd.DataFrame(rows, columns=["predictors", "AIC", "BIC", "adjR2"]).sort_values("AIC")
print(res.head(4).round({"AIC": 2, "BIC": 2, "adjR2": 4}).to_string(index=False))
cv = KFold(5, shuffle=True, random_state=0)
for cols in [["sqft"], ["sqft", "bedrooms", "age"], ["sqft", "bedrooms", "bathrooms", "age"], cands]:
    scores = cross_val_score(LinearRegression(), homes[cols], homes["price"], cv=cv, scoring="neg_root_mean_squared_error")
    print(f"{' + '.join(cols):45s} CV RMSE {-scores.mean():,.0f}")
```

**Reading this code line by line**

- The nested loops use `combinations(cands, k)` to generate every subset of the six candidate predictors (63 models), build a formula string with `" + ".join(subset)`, fit it, and record its AIC, BIC and adjusted $R^2$.
- `sort_values("AIC")` puts the best (lowest) AIC first; `.to_string(index=False)` prints without row numbers.
- `KFold(5, shuffle=True, random_state=0)` defines 5 folds after shuffling rows.
- `cross_val_score(model, X, y, cv=..., scoring="neg_root_mean_squared_error")` fits and scores the model on each fold. Scikit-learn always maximises scores, so errors are returned negated; we flip the sign back.

All-subsets search by AIC picks exactly the true model (sqft, bedrooms, bathrooms, age). BIC, with its heavier penalty, prefers the smaller model without bathrooms (its BIC is lower). Models that add a noise column are close behind: a reminder that with weak predictors, criteria differ only slightly and the choice is partly judgement.

Cross-validated RMSE tells the same story in prediction terms: floor area alone gives 41,388; adding bedrooms and age, 38,954; adding bathrooms, 38,843 (the best); adding the two noise columns makes it worse again, 39,141. Useless predictors hurt out-of-sample accuracy.

> [!WARNING]
> Stepwise and all-subsets methods are themselves a form of multiple testing. The p-values and confidence intervals printed for the *selected* model are too optimistic, because the selection used the same data. Report cross-validated performance, or validate on a fresh holdout set.

## 5. Weighted regression

Ordinary least squares treats every record as equally reliable. Sometimes they are not:

- Some records are averages of many observations and others of few (a store-level average from 1,000 transactions is more precise than one from 10).
- The noise grows with the size of $Y$ (expensive houses have larger price uncertainty in dollars). Unequal error variance is called **heteroskedasticity**.
- Older records may be less relevant (sales from years ago reflect an older market).

**Weighted least squares** (WLS) minimises $\sum w_i (Y_i - \hat{Y}_i)^2$. When the error variance of record $i$ is proportional to $v_i$, the efficient choice is $w_i = 1/v_i$: noisier records count less.

```python-run
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
rng = np.random.default_rng(42)
n = 400
sqft = rng.uniform(600, 4000, n)
price = 40_000 + 160 * sqft + rng.normal(0, 1, n) * 0.08 * 160 * sqft
df = pd.DataFrame({"sqft": sqft, "price": price})
ols = smf.ols("price ~ sqft", data=df).fit()
wls = smf.wls("price ~ sqft", data=df, weights=1 / sqft**2).fit()
for name, m in [("OLS", ols), ("WLS", wls)]:
    print(f"{name}: slope {m.params['sqft']:.2f}, std err {m.bse['sqft']:.2f}")
reps = []
for s in range(300):
    r = np.random.default_rng(1000 + s)
    p = 40_000 + 160 * sqft + r.normal(0, 1, n) * 0.08 * 160 * sqft
    d = pd.DataFrame({"sqft": sqft, "price": p})
    reps.append((smf.ols("price ~ sqft", data=d).fit().params["sqft"], smf.wls("price ~ sqft", data=d, weights=1 / sqft**2).fit().params["sqft"]))
reps = np.array(reps)
print(f"spread of slope over 300 repeat samples: OLS {reps[:, 0].std():.2f}, WLS {reps[:, 1].std():.2f}")
```

**Reading this code line by line**

- The noise term is proportional to floor area (8% of the expected size-driven price), so big houses have much noisier prices: heteroskedasticity by construction.
- `smf.wls(..., weights=1 / sqft**2)` fits weighted least squares; since the noise standard deviation is proportional to sqft, its variance is proportional to sqft², and the weight is the inverse.
- The loop redraws the noise 300 times (keeping the same houses) and records both slope estimates, to measure their real sampling variability.

Both methods estimate the slope near the true 160 (161.47 and 161.25), but WLS is more precise: its standard error is 1.33 against 1.69, and across 300 repeat samples its slope varies by 1.23 against OLS's 1.68. Weighting lets the reliable records speak louder. Statsmodels' WLS is also how you fit **survey-weighted** or **recency-weighted** regressions, by passing the appropriate weights.

## 6. Prediction versus explanation

Regression serves two purposes, and they pull in different directions.

- **Explanation (profiling)**: understand how $Y$ relates to each $X$. Coefficients, their signs, intervals and the causal story matter; correlated predictors and confounders must be thought through carefully.
- **Prediction**: forecast $Y$ for new records. Coefficients can be uninterpretable as long as out-of-sample error is low; cross-validation is the judge.

Much of data science is prediction, but product analytics often needs explanation: "how much does load time affect conversion, holding device and country fixed?" Know which question you are answering.

## Summary

- Multiple regression fits $Y = b_0 + \sum b_j X_j + e$ by least squares; each coefficient is an effect holding the other predictors fixed.
- A coefficient's sign and size can change when other predictors are added (bedrooms: $+37{,}249$ alone, $-14{,}237$ given floor area).
- RMSE and RSE measure typical error; $R^2$ never falls when predictors are added, adjusted $R^2$ penalises extra predictors.
- Cross-validation measures performance on held-out data and is the honest judge of predictive models.
- AIC and BIC trade fit against complexity (BIC more strictly); all-subsets, forward, backward and stepwise searches use them; post-selection p-values are optimistic.
- Weighted least squares down-weights noisier or less relevant records.

## Glossary

- **Multiple linear regression**: regression with several predictors.
- **Holding other predictors constant**: the interpretation of each coefficient in multiple regression.
- **RMSE (root mean squared error)**: square root of the average squared residual.
- **Adjusted $R^2$**: $R^2$ penalised for the number of predictors.
- **Holdout set**: data kept aside to evaluate a model.
- **k-fold cross-validation / fold**: rotating each of $k$ parts as the test set / one of those parts.
- **Parsimony (Occam's razor)**: preferring the simpler of comparable models.
- **AIC / BIC**: model criteria that penalise parameters by 2 / by $\log(n)$ each.
- **All-subsets regression**: fitting every combination of predictors.
- **Forward selection / backward elimination / stepwise regression**: adding, removing, or alternating predictors one at a time.
- **Penalised regression (ridge, lasso)**: shrinking coefficients to control complexity.
- **Weighted least squares (WLS)**: least squares with record weights.
- **Heteroskedasticity**: error variance that differs across records.

## Check yourself

```quiz
[
  {"q": "In a house-price regression with floor area included, the bedrooms coefficient is −14,000. The best interpretation is…", "options": ["Among houses of the same floor area (and other predictors), each extra bedroom is associated with about 14,000 lower price", "Bedrooms reduce house prices in general", "The model is wrong because bedrooms should be positive", "Adding a bedroom to any house loses 14,000"], "answer": 0,
   "explain": "Holding size fixed, more bedrooms means smaller rooms; the coefficient is conditional on the other predictors."},
  {"q": "You add a column of random noise to a regression. What happens to R² on the training data?", "options": ["It stays the same or increases slightly", "It always decreases", "It becomes negative", "It drops to zero"], "answer": 0,
   "explain": "Least squares can always use an extra column to fit the training data at least as well; adjusted R² may fall."},
  {"q": "Which criterion penalises extra predictors most heavily for large n?", "options": ["BIC", "AIC", "R²", "RSS"], "answer": 0,
   "explain": "BIC's penalty is log(n) per parameter versus AIC's 2."},
  {"q": "Why is cross-validated RMSE more trustworthy than in-sample RSE for choosing a predictive model?", "options": ["It measures error on data not used to fit the model", "It is always smaller", "It needs no data splitting", "It ignores outliers"], "answer": 0,
   "explain": "In-sample error rewards overfitting; held-out error does not."},
  {"q": "After stepwise selection, the selected model's p-values are…", "options": ["too optimistic, because selection used the same data", "exactly correct", "too conservative", "unrelated to selection"], "answer": 0,
   "explain": "Selection is a hidden form of multiple testing."},
  {"q": "Store-level averages are computed from very different numbers of transactions. In a regression on these averages you should…", "options": ["weight each store by its number of transactions (WLS)", "drop the small stores", "use plain OLS", "use the median instead"], "answer": 0,
   "explain": "Averages of more transactions have smaller variance and deserve more weight."}
]
```

> **Source:** Bruce & Bruce, *Practical Statistics for Data Scientists* (O'Reilly, 2017), ch. 4, "Multiple Linear Regression" (example: King County housing data, assessing the model, cross-validation, model selection and stepwise regression, weighted regression); the simulated housing data are original; statsmodels and scikit-learn documentation.
