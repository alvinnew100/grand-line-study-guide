# Factor variables and interpreting regression

> **Before this lesson:** [Multiple regression: assessment, cross-validation and model selection](#/lesson/statistics/multiple-regression), especially the bedrooms example where a coefficient changed sign. Degrees of freedom from [t-tests, z-tests and degrees of freedom](#/lesson/statistics/t-tests) explain why categories need one column fewer than they have levels.

## In plain words

Regression works with numbers, but many important predictors are categories: property type, city zone, device, plan. **Factor variables** (categorical predictors) must be turned into numeric columns before regression can use them, and the way you do it changes how the coefficients read. Then, once a model includes several predictors, interpreting it requires care: predictors can be correlated with each other (**multicollinearity**), an important predictor may be missing (**confounding**), and the effect of one predictor may depend on another (**interaction**).

An everyday picture: a recipe's success depends on oven temperature and baking time, but also on which oven you use (a category). "Oven B adds 5 minutes compared with oven A" only makes sense once you have picked oven A as the reference. And the temperature effect may depend on the oven: a hot fan oven needs less time than a hot gas oven. That is an interaction.

Why it matters for a job: almost every business model has categorical predictors, and analysts constantly explain coefficients to stakeholders. Interviewers ask "how would you encode a categorical variable with 3 levels for linear regression, and why only 2 columns?", "what is multicollinearity and how do you detect it?", "what is a confounder?" and "what does an interaction term mean?"

## 1. Dummy variables

The standard encoding creates one 0/1 column per category, called a **dummy variable** (or indicator, or one-hot column): 1 if the record belongs to that category, 0 otherwise.

```python-run
import pandas as pd
homes = pd.DataFrame({"ptype": ["house", "condo", "townhouse", "condo", "house", "townhouse"]})
print(pd.get_dummies(homes["ptype"], dtype=int))
print(pd.get_dummies(homes["ptype"], drop_first=True, dtype=int))
```

**Reading this code line by line**

- `pd.get_dummies(column, dtype=int)` creates one 0/1 column per distinct value, in alphabetical order; `dtype=int` shows 0 and 1 rather than `False` and `True`.
- `drop_first=True` drops the first category's column (here `condo`).

The first table has three columns (condo, house, townhouse), and every row has exactly one 1. That is **one-hot encoding**. For a regression *with an intercept*, it causes a problem: the three columns always add up to 1, which is exactly the intercept's column. One column is a perfect linear combination of others, so infinitely many coefficient combinations fit equally well and least squares has no unique answer. This is called **perfect multicollinearity** (the "dummy variable trap").

The fix is **reference coding** (also called treatment coding): drop one category, the **reference level** (here condo). Then $k$ levels need $k - 1$ columns, matching the $k - 1$ degrees of freedom a categorical variable has. Each remaining coefficient is the difference between that category and the reference, holding other predictors fixed. (Machine-learning methods such as trees and regularised models often keep all $k$ columns; the trap only matters for unpenalised regression with an intercept.)

## 2. Factors in statsmodels

Statsmodels formulas create reference-coded dummies automatically when you wrap a column in `C(...)`. We simulate 600 sales across four city zones (A most expensive, D cheapest) and three property types.

```python-run
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
rng = np.random.default_rng(42)
n = 600
zone = rng.choice(["A", "B", "C", "D"], n, p=[0.2, 0.3, 0.3, 0.2])
zone_premium = pd.Series(zone).map({"A": 120_000, "B": 60_000, "C": 20_000, "D": 0}).to_numpy()
ptype = rng.choice(["condo", "house", "townhouse"], n, p=[0.3, 0.5, 0.2])
type_effect = pd.Series(ptype).map({"condo": -30_000, "house": 0, "townhouse": -15_000}).to_numpy()
sqft = rng.normal(1700, 450, n).clip(500, 4000) - 0.5 * zone_premium / 150
price = 80_000 + 150 * sqft + zone_premium + type_effect + rng.normal(0, 35_000, n)
homes = pd.DataFrame(dict(price=price, sqft=sqft, zone=zone, ptype=ptype))
m = smf.ols("price ~ sqft + C(ptype) + C(zone)", data=homes).fit()
print(m.params.round(0))
m2 = smf.ols("price ~ sqft + C(ptype, Treatment(reference='house')) + C(zone)", data=homes).fit()
print(m2.params.filter(like="ptype").round(0))
```

**Reading this code line by line**

- The simulation gives each zone a price premium relative to D and each property type an effect relative to house. Homes in pricier zones are made somewhat smaller (the `sqft` line subtracts a zone-dependent amount), which matters in section 4.
- `C(ptype)` tells statsmodels to treat `ptype` as categorical; the first level alphabetically (condo) becomes the reference. Coefficient names like `C(ptype)[T.house]` mean "house compared with the reference" (`T.` stands for treatment coding).
- `Treatment(reference='house')` chooses a different reference level.
- `.filter(like="ptype")` keeps only the coefficients whose names contain "ptype".

With condo as reference: houses are worth 30,894 more than condos and townhouses 13,612 more, holding size and zone fixed. Zones B, C and D are 52,762, 88,722 and 116,308 cheaper than zone A (the true gaps are 60,000, 100,000 and 120,000; estimates differ by noise). With house as reference, condo is $-30{,}894$ and townhouse $-17{,}282$: the same model, different baseline. The predictions are identical whichever reference you choose; only the meaning of each coefficient changes. Choose the reference that makes the story clearest, usually the most common or the "standard" category.

Other codings exist: **deviation coding** (sum contrasts) compares each level with the overall mean instead of a reference level; **polynomial coding** suits ordered factors.

### Factors with many levels

A predictor such as postcode can have thousands of levels: too many dummies, most with few records. Options:

- Group rare levels into "other".
- Group levels by a related numeric summary, for example by the median residual of a simpler model or by median price, cut into a handful of bands. (Beware leakage: compute such summaries on training data only.)
- Replace the category by a numeric attribute of it, such as the region's average income.
- Use methods built for high cardinality: target encoding with regularisation, mixed-effects (hierarchical) models, or tree-based models.

### Ordered factors

An **ordered factor** (ordinal variable), such as a building-quality grade from 1 to 5, can be entered as a single number (assuming each step has the same effect, using one degree of freedom) or as dummies (allowing each step its own effect, using four). Compare the two with cross-validation or an F-test; the numeric version is more parsimonious when it fits well.

## 3. Correlated predictors and multicollinearity

When predictors are strongly correlated with each other, the model struggles to separate their effects. Coefficients become unstable: small changes in the data swing them widely, sometimes flipping their sign, and their standard errors are large, although predictions may remain fine. This is **multicollinearity** (short of perfect multicollinearity, which makes the fit impossible).

The **variance inflation factor** (VIF) measures it for each predictor: regress that predictor on all the others, take the $R^2$ of that regression, and compute $VIF = 1/(1 - R^2)$. A VIF of 1 means no correlation with other predictors; values above about 5 to 10 signal trouble, because the variance of that coefficient is inflated by that factor.

```python-run
import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor
rng = np.random.default_rng(7)
n = 300
sqft = rng.normal(1800, 500, n)
rooms = sqft / 250 + rng.normal(0, 0.6, n)
age = rng.uniform(0, 60, n)
X = sm.add_constant(pd.DataFrame({"sqft": sqft, "rooms": rooms, "age": age}))
for i, col in enumerate(X.columns):
    if col != "const":
        print(f"VIF {col:5s}: {variance_inflation_factor(X.values, i):6.2f}")
price = 50_000 + 120 * sqft + 5_000 * rooms - 500 * age + rng.normal(0, 30_000, n)
for s in range(3):
    idx = np.random.default_rng(s).choice(n, n, replace=True)
    fit = sm.OLS(price[idx], X.iloc[idx]).fit()
    print(f"bootstrap {s}: sqft {fit.params['sqft']:7.1f}  rooms {fit.params['rooms']:9.0f}")
```

**Reading this code line by line**

- `rooms` is built mostly from `sqft`, so the two are highly correlated; `age` is independent.
- `sm.add_constant` adds an intercept column named `const` (the array interface `sm.OLS` does not add one automatically, unlike formulas).
- `variance_inflation_factor(X.values, i)` computes the VIF of column `i`; `enumerate` gives each column's position and name.
- The loop refits the model on three bootstrap resamples of the rows to show how much the coefficients move.

The VIFs are 11.94 for both sqft and rooms and 1.00 for age. Across bootstrap resamples, the rooms coefficient swings from 3,137 to 8,856. The model cannot tell whether price follows floor area or room count, because they almost always move together.

Remedies: drop one of the correlated predictors, combine them (rooms per square foot), collect data where they vary independently, or use ridge regression, which stabilises coefficients by shrinking them. If the goal is only prediction, moderate multicollinearity can be ignored.

## 4. Confounding variables

A **confounder** is a variable that influences both a predictor and the response. Leaving it out of the model makes the predictor's coefficient absorb part of the confounder's effect, a distortion called **omitted variable bias**. Including too many predictors causes multicollinearity; including too few causes confounding.

```python-run
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
rng = np.random.default_rng(42)
n = 600
zone = rng.choice(["A", "B", "C", "D"], n, p=[0.2, 0.3, 0.3, 0.2])
zone_premium = pd.Series(zone).map({"A": 120_000, "B": 60_000, "C": 20_000, "D": 0}).to_numpy()
ptype = rng.choice(["condo", "house", "townhouse"], n, p=[0.3, 0.5, 0.2])
type_effect = pd.Series(ptype).map({"condo": -30_000, "house": 0, "townhouse": -15_000}).to_numpy()
sqft = rng.normal(1700, 450, n).clip(500, 4000) - 0.5 * zone_premium / 150
price = 80_000 + 150 * sqft + zone_premium + type_effect + rng.normal(0, 35_000, n)
homes = pd.DataFrame(dict(price=price, sqft=sqft, zone=zone, ptype=ptype))
print("sqft coefficient with zone   :", round(smf.ols("price ~ sqft + C(ptype) + C(zone)", data=homes).fit().params["sqft"], 1))
print("sqft coefficient without zone:", round(smf.ols("price ~ sqft + C(ptype)", data=homes).fit().params["sqft"], 1))
print("correlation of sqft with zone premium:", round(np.corrcoef(sqft, zone_premium)[0, 1], 3))
```

**Reading this code line by line**

- Same simulated city as before. We fit the model with and without zone and compare the floor-area coefficient.

With zone included, each square foot is worth 145.2 dollars (true 150). Without zone it drops to 118.4. The reason is the correlation of $-0.329$: homes in expensive zones tend to be smaller. Without zone in the model, "bigger" partly means "in a cheaper zone", so the size effect is understated. Location confounds the size-price relationship. In product analytics, typical confounders are user tenure, platform, country and seasonality: heavy users both adopt new features and spend more, so "feature adopters spend more" is confounded by engagement.

## 5. Interactions

The models so far assume **main effects** only: each predictor adds the same amount regardless of the others. An **interaction** lets the effect of one predictor depend on another. In a formula, `a * b` includes both main effects and their interaction (`a:b`).

```python-run
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
rng = np.random.default_rng(43)
n = 800
zone = rng.choice(["prime", "suburb"], n)
sqft = rng.normal(1700, 450, n).clip(500, 4000)
per_sqft = np.where(zone == "prime", 260, 140)
price = 60_000 + per_sqft * sqft + rng.normal(0, 30_000, n)
homes = pd.DataFrame(dict(price=price, sqft=sqft, zone=zone))
main = smf.ols("price ~ sqft + C(zone)", data=homes).fit()
inter = smf.ols("price ~ sqft * C(zone)", data=homes).fit()
print(inter.params.round(1))
print(f"adj R^2 main effects {main.rsquared_adj:.4f}, with interaction {inter.rsquared_adj:.4f}")
```

**Reading this code line by line**

- In this simulated city, a square foot is worth 260 dollars in the prime zone and 140 in the suburbs: the slope depends on the zone.
- `sqft * C(zone)` expands to `sqft + C(zone) + sqft:C(zone)`.

The output says: in the reference zone (prime) each square foot adds 265.5; in the suburbs the slope is $265.5 - 122.8 = 142.7$ per square foot. The interaction coefficient, $-122.8$, is the *difference in slopes*. The suburb main effect (1,267) is now the difference between zones for a zero-square-foot home, which is not meaningful by itself; with interactions, interpret main effects carefully. Adjusted $R^2$ rises from 0.9217 to 0.9577, so the interaction is real and useful.

How to find interactions: domain knowledge first (location changes the value of size; device changes the effect of a layout change), then test candidate interactions with cross-validation or stepwise selection. Tree-based models discover interactions automatically, which is one of their strengths.

> [!INTERVIEW]
> "A feature's effect on conversion is +2% overall. Product asks whether it works on mobile." Fit `converted ~ treatment * C(platform)` (logistic regression, but the idea is the same). The interaction coefficient tests whether the treatment effect differs by platform; slicing the data and eyeballing separate results invites false segment discoveries.

## Summary

- Categorical predictors become dummy variables; with an intercept, use $k-1$ columns (reference coding) to avoid perfect multicollinearity.
- Each dummy coefficient is a difference from the reference level; changing the reference changes interpretation, not predictions.
- High-cardinality factors need grouping or special methods; ordered factors can be numeric or dummies.
- Multicollinearity (high VIF) makes coefficients unstable; confounding (omitted variables) biases them.
- Interactions let one predictor's effect depend on another; `a * b` in a formula adds both main effects and their product.

## Glossary

- **Factor variable**: a categorical predictor.
- **Dummy (indicator) variable**: a 0/1 column for one category.
- **One-hot encoding**: one dummy per category.
- **Reference (treatment) coding / reference level**: dropping one category's dummy / the category others are compared with.
- **Perfect multicollinearity (dummy variable trap)**: a predictor that is an exact linear combination of others.
- **Deviation coding**: comparing each level with the overall mean.
- **High cardinality**: a categorical variable with very many levels.
- **Ordered factor**: a categorical variable with a natural order.
- **Multicollinearity**: strong correlation among predictors.
- **Variance inflation factor (VIF)**: $1/(1 - R^2_j)$ from regressing predictor $j$ on the others.
- **Confounder / omitted variable bias**: a variable affecting both predictor and response / the distortion from leaving it out.
- **Main effect / interaction**: a predictor's own effect / an effect that depends on another predictor.

## Check yourself

```quiz
[
  {"q": "A categorical predictor has 5 levels. How many dummy columns does an OLS model with an intercept need?", "options": ["4", "5", "6", "1"], "answer": 0,
   "explain": "k − 1 columns; the dropped level is the reference captured by the intercept."},
  {"q": "In `price ~ sqft + C(ptype)` with condo as reference, the coefficient for house is 30,894. It means…", "options": ["Houses sell for about 30,894 more than condos of the same floor area", "Houses cost 30,894 on average", "Condos cost 30,894 more than houses", "Each square foot of a house is worth 30,894"], "answer": 0,
   "explain": "Dummy coefficients are differences from the reference, holding other predictors fixed."},
  {"q": "Two predictors have VIFs of 12. What is the main consequence?", "options": ["Their coefficients have inflated variance and are unstable, though predictions may be fine", "The model cannot be fit", "R² is zero", "The residuals are biased"], "answer": 0,
   "explain": "High VIF inflates coefficient variance; perfect collinearity would make the fit impossible."},
  {"q": "Dropping zone from a price model changed the sqft coefficient from 145 to 118. Zone is acting as…", "options": ["a confounder", "an interaction", "a reference level", "a dummy variable trap"], "answer": 0,
   "explain": "Zone affects price and is correlated with size, so omitting it biases the size coefficient."},
  {"q": "In `price ~ sqft * C(zone)` the coefficient `sqft:C(zone)[T.suburb]` is −122.8. It means…", "options": ["the price per square foot is 122.8 lower in the suburb than in the reference zone", "suburban homes are 122.8 cheaper", "sqft and zone are correlated", "the suburb has 122.8 fewer homes"], "answer": 0,
   "explain": "An interaction coefficient is a difference in slopes."},
  {"q": "Why does one-hot encoding with all k columns plus an intercept break OLS?", "options": ["The k columns sum to the intercept column, so coefficients are not uniquely determined", "It creates too few columns", "It makes the data non-normal", "OLS cannot use 0/1 columns"], "answer": 0,
   "explain": "This exact linear dependence is perfect multicollinearity."}
]
```

> **Source:** Bruce & Bruce, *Practical Statistics for Data Scientists* (O'Reilly, 2017), ch. 4, "Factor Variables in Regression" (dummy variables, factor variables with many levels, ordered factor variables) and "Interpreting the Regression Equation" (correlated predictors, multicollinearity, confounding variables, interactions and main effects); statsmodels documentation for formulas and `variance_inflation_factor`; the simulated data are original.
