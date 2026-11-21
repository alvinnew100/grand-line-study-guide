# Simple linear regression and prediction intervals

> **Before this lesson:** [Correlation and exploring two or more variables](#/lesson/statistics/correlation-bivariate) (scatterplots, Pearson's $r$), [Confidence intervals done right](#/lesson/statistics/confidence-intervals) and [t-tests, z-tests and degrees of freedom](#/lesson/statistics/t-tests). Regression to the mean from [Random sampling and the many faces of bias](#/lesson/statistics/sampling-bias) explains the method's name.

## In plain words

Correlation says how strongly two variables move together. **Regression** goes further: it gives an equation that predicts one variable from the other, and says how much one changes, on average, when the other changes by one unit. **Simple linear regression** fits the best straight line through a scatterplot of one **predictor** $X$ and one **response** $Y$.

An everyday picture: a shop owner plots weekly advertising spend against weekly sales and draws a straight line through the cloud of points with a ruler. The line's steepness says roughly how many extra sales each extra dollar of advertising brings; reading the line at a planned budget gives a forecast. Regression is the precise, repeatable version of that ruler.

Why it matters for a job: regression is the workhorse of statistics and the foundation of most machine learning. Data scientists use it to quantify relationships ("each extra second of page load costs X% of conversions"), to forecast, and to control for confounding variables. Interviewers ask you to interpret coefficients, explain least squares, distinguish confidence from prediction intervals, and warn about extrapolation.

## 1. The model

Simple linear regression assumes

$$Y = b_0 + b_1 X + e$$

- $b_0$ is the **intercept**: the predicted $Y$ when $X = 0$.
- $b_1$ is the **slope** (or **coefficient** of $X$): the change in the predicted $Y$ for a one-unit increase in $X$.
- $e$ is the **error** (residual): everything about $Y$ that the line does not explain.

Synonyms are everywhere. The response is also called the dependent variable, target or outcome; the predictor is called the independent variable, feature or explanatory variable. From data we compute estimates, written with hats: $\hat{b}_0$, $\hat{b}_1$. The **fitted values** (predictions for the training data) are $\hat{Y}_i = \hat{b}_0 + \hat{b}_1 X_i$, and the **residuals** are $e_i = Y_i - \hat{Y}_i$.

## 2. Least squares

Which line is "best"? The standard answer is the line that minimises the **residual sum of squares** (RSS):

$$RSS = \sum_{i=1}^n (Y_i - \hat{b}_0 - \hat{b}_1 X_i)^2$$

This is **ordinary least squares** (OLS). Squaring makes large misses count heavily and makes the minimum easy to compute with calculus. The solution is

$$\hat{b}_1 = \frac{\sum_i (X_i - \bar{X})(Y_i - \bar{Y})}{\sum_i (X_i - \bar{X})^2}, \qquad \hat{b}_0 = \bar{Y} - \hat{b}_1 \bar{X}$$

The slope is the covariance of $X$ and $Y$ divided by the variance of $X$, which can also be written $\hat{b}_1 = r\, s_Y / s_X$: correlation rescaled into the units of the data. The intercept makes the line pass through the point of means $(\bar{X}, \bar{Y})$.

```python-run
import numpy as np
rng = np.random.default_rng(40)
spend = np.round(rng.uniform(1, 10, 40), 1)
sales = np.round(20 + 3.5 * spend + rng.normal(0, 4, 40), 1)
b1 = np.sum((spend - spend.mean()) * (sales - sales.mean())) / np.sum((spend - spend.mean()) ** 2)
b0 = sales.mean() - b1 * spend.mean()
print(f"by hand : intercept {b0:.3f}, slope {b1:.3f}")
print("polyfit :", np.round(np.polyfit(spend, sales, 1), 3))
r = np.corrcoef(spend, sales)[0, 1]
print(f"slope = r * sy / sx = {r * sales.std(ddof=1) / spend.std(ddof=1):.3f}")
```

**Reading this code line by line**

- We simulate 40 weeks: advertising `spend` (thousands of dollars, between 1 and 10) and `sales` (thousands of units), built as $20 + 3.5 \times \text{spend}$ plus noise. In real life you would not know the true line; simulation lets us check the method.
- `b1` and `b0` apply the least-squares formulas directly.
- `np.polyfit(x, y, 1)` fits a polynomial of degree 1 (a line) and returns `[slope, intercept]`, highest power first.
- The last line confirms the slope equals $r \times s_Y / s_X$.

All three agree: intercept 20.671, slope 3.198. Interpretation: each extra thousand dollars of advertising is associated with about 3.2 thousand more units sold; with zero advertising, the line predicts 20.7 thousand units. (The true slope was 3.5; the estimate differs because of noise, and section 4 quantifies by how much.)

## 3. Fitted values, residuals and goodness of fit

```python-run
import numpy as np
rng = np.random.default_rng(40)
spend = np.round(rng.uniform(1, 10, 40), 1)
sales = np.round(20 + 3.5 * spend + rng.normal(0, 4, 40), 1)
b1, b0 = np.polyfit(spend, sales, 1)
fitted = b0 + b1 * spend
resid = sales - fitted
rss = np.sum(resid ** 2)
tss = np.sum((sales - sales.mean()) ** 2)
print("first 3 fitted:", np.round(fitted[:3], 2), " residuals:", np.round(resid[:3], 2))
print(f"mean residual {abs(resid.mean()):.6f}; RSS {rss:.1f}; R^2 {1 - rss / tss:.4f}")
print(f"residual standard error {np.sqrt(rss / (len(spend) - 2)):.3f}")
for slope in [b1 - 0.5, b1, b1 + 0.5]:
    intercept = sales.mean() - slope * spend.mean()
    print(f"slope {slope:.3f}: RSS {np.sum((sales - intercept - slope * spend) ** 2):.1f}")
```

**Reading this code line by line**

- `fitted` are the line's predictions for the 40 weeks and `resid` the misses.
- `tss` is the **total sum of squares**: variation of sales around their mean, ignoring spend.
- The loop tries slopes 0.5 below and above the least-squares slope (adjusting the intercept to keep the line through the means) and prints their RSS.

The residuals average to zero (a property of least squares with an intercept). RSS is 671.5; nudging the slope either way raises it to 721.0, confirming that least squares found the minimum. Two summaries of fit:

- $R^2 = 1 - RSS/TSS = 0.7511$: the share of the variation in sales explained by spend. In simple regression it equals $r^2$.
- The **residual standard error** (RSE), $\sqrt{RSS/(n-2)} = 4.204$: the typical size of a miss, in the units of $Y$. The $n - 2$ reflects two estimated parameters (degrees of freedom again).

## 4. Inference: standard errors, t-statistics and intervals for coefficients

The estimated slope would change with a different sample, so it has a standard error. Statsmodels reports it along with a t-statistic (estimate divided by its standard error), a p-value for the null hypothesis that the true coefficient is zero, and a confidence interval.

```python-run
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
rng = np.random.default_rng(40)
spend = np.round(rng.uniform(1, 10, 40), 1)
sales = np.round(20 + 3.5 * spend + rng.normal(0, 4, 40), 1)
df = pd.DataFrame({"spend": spend, "sales": sales})
model = smf.ols("sales ~ spend", data=df).fit()
table = pd.DataFrame({"coef": model.params, "std err": model.bse, "t": model.tvalues})
print(table.round(3))
print(model.conf_int().round(3))
print(f"R^2 {model.rsquared:.4f}, p-value for slope {model.pvalues['spend']:.2e}")
```

**Reading this code line by line**

- `import statsmodels.formula.api as smf` loads statsmodels' **formula interface**, which describes models with R-style strings.
- `"sales ~ spend"` reads "model sales as a function of spend"; an intercept is included automatically.
- `.fit()` estimates the model by OLS and returns a results object with `params`, `bse` (standard errors), `tvalues`, `pvalues`, `conf_int()` and `rsquared`. (`model.summary()` prints all of it in one large table.)

The slope is 3.198 with standard error 0.299, so $t = 10.71$ and the p-value is $4.94 \times 10^{-13}$: overwhelming evidence that sales are related to spend. The 95% confidence interval for the slope, (2.593, 3.803), contains the true value 3.5. For data scientists, the p-value of a coefficient matters less than its size and interval, and much less than predictive accuracy on new data, but these numbers appear in every regression output and you must be able to read them.

## 5. Confidence intervals versus prediction intervals

When we use the line to predict at a new $X$, there are two different questions:

- **Where is the average $Y$ for this $X$?** A **confidence interval for the mean response** reflects only the uncertainty in the estimated line. It narrows as $n$ grows.
- **Where will a single new $Y$ fall?** A **prediction interval** adds the scatter of individual points around the line (the error term). It is always wider and never shrinks below the residual noise, however much data you collect.

```python-run
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
rng = np.random.default_rng(40)
spend = np.round(rng.uniform(1, 10, 40), 1)
sales = np.round(20 + 3.5 * spend + rng.normal(0, 4, 40), 1)
model = smf.ols("sales ~ spend", data=pd.DataFrame({"spend": spend, "sales": sales})).fit()
new = pd.DataFrame({"spend": [2.0, 5.5, 9.0]})
frame = model.get_prediction(new).summary_frame(alpha=0.05)
print(frame[["mean", "mean_ci_lower", "mean_ci_upper", "obs_ci_lower", "obs_ci_upper"]].round(2))
```

**Reading this code line by line**

- `new` is a DataFrame of spends we want predictions for; its column name must match the formula.
- `get_prediction(new).summary_frame(alpha=0.05)` returns the prediction (`mean`), the 95% confidence interval for the mean response (`mean_ci_*`) and the 95% prediction interval for a new observation (`obs_ci_*`).

At a spend of 5.5 the line predicts 38.26. The average sales for weeks with that spend are pinned down to (36.84, 39.68), but any single week could plausibly land anywhere in (29.63, 46.89), six times wider. Note also that the confidence interval is narrowest near the middle of the data (5.5) and wider at the edges (2.0 and 9.0), because the line is least certain far from the mean of $X$.

> [!INTERVIEW]
> "What is the difference between a confidence interval and a prediction interval in regression?" The CI describes uncertainty about the average response at a given $X$; the PI describes where an individual new observation will fall, so it adds the irreducible noise and is always wider. Forecasting next week's sales needs the PI.

Prediction intervals can also be built by the bootstrap: resample rows, refit, predict, and add a randomly drawn residual to each prediction; the percentiles of these values form the interval. This works for models without formulas.

## 6. The danger of extrapolation

A fitted line is only trustworthy within the range of the data used to fit it. Predicting outside that range is **extrapolation**, and relationships that look linear over a small range are often curved over a larger one: advertising has diminishing returns, prices cannot go below zero, growth saturates.

```python-run
import numpy as np
rng = np.random.default_rng(41)
x = rng.uniform(0, 10, 200)
y = 100 * (1 - np.exp(-x / 6)) + rng.normal(0, 3, 200)
b1, b0 = np.polyfit(x, y, 1)
for x0 in [5, 10, 20, 40]:
    truth = 100 * (1 - np.exp(-x0 / 6))
    print(f"x = {x0:>2}: line predicts {b0 + b1 * x0:6.1f}, truth {truth:5.1f}")
```

**Reading this code line by line**

- The true relationship rises and then levels off towards 100 (saturation); we only observe $x$ between 0 and 10.
- We fit a straight line and compare its predictions with the truth inside and far outside the observed range.

Inside the data the line is off by a few units (51.6 versus 56.5 at $x = 5$). At $x = 20$ it predicts 162.5 against a truth of 96.4; at $x = 40$, 310.3 against 99.9. The line has no way of knowing the curve flattens beyond the data. Regression cannot tell you what happens where you have never looked.

## 7. Correlation, regression and causation

- Regression of $Y$ on $X$ and regression of $X$ on $Y$ give different lines (each minimises errors in its own response). Correlation is symmetric; regression is not.
- The name "regression" comes from Galton's observation of regression to the mean: because $|r| < 1$, the predicted $Y$ is fewer standard deviations from its mean than $X$ is from its own. Tall parents' children are predicted to be tall, but less extreme.
- A slope describes association. It equals a causal effect only if $X$ was randomised or all confounders are accounted for. In our simulation spend causes sales by construction; in real data, shops might advertise more in weeks they already expect to be busy, which would inflate the slope. See [Correlation, causation and Simpson's paradox](#/lesson/statistics/causation-simpson).

## Summary

- Simple linear regression models $Y = b_0 + b_1 X + e$; the slope is the average change in $Y$ per unit of $X$.
- Least squares minimises the residual sum of squares; $\hat{b}_1 = \text{cov}(X, Y)/\text{var}(X) = r s_Y/s_X$, and the line passes through the means.
- $R^2$ is the share of variance explained; the residual standard error is the typical miss.
- Statsmodels reports coefficient standard errors, t-statistics, p-values and confidence intervals.
- Confidence intervals cover the mean response; prediction intervals cover a new observation and are wider.
- Do not extrapolate beyond the data, and do not read slopes as causal without a design that supports it.

## Glossary

- **Regression**: modelling a response as a function of predictors.
- **Simple linear regression**: one predictor and a straight line.
- **Response / predictor**: the variable predicted / the variable used to predict.
- **Intercept ($b_0$) / slope ($b_1$)**: the predicted value at $X = 0$ / the change per unit of $X$.
- **Coefficient**: a parameter multiplying a predictor.
- **Fitted value ($\hat{Y}$)**: the model's prediction for a data point.
- **Residual**: observed minus fitted value.
- **Residual sum of squares (RSS)**: the sum of squared residuals.
- **Ordinary least squares (OLS)**: estimating coefficients by minimising RSS.
- **Total sum of squares (TSS)**: variation of $Y$ around its mean.
- **$R^2$ (coefficient of determination)**: $1 - RSS/TSS$.
- **Residual standard error (RSE)**: $\sqrt{RSS/(n - 2)}$ in simple regression.
- **Formula interface**: describing a model with a string such as `"y ~ x"`.
- **Confidence interval for the mean response / prediction interval**: uncertainty about the average $Y$ at $X$ / about a new individual $Y$.
- **Extrapolation**: predicting outside the range of the data.

## Check yourself

```quiz
[
  {"q": "A regression of sales (thousand units) on ad spend (thousand dollars) has slope 3.2. The best interpretation is…", "options": ["Each extra thousand dollars of spend is associated with about 3,200 more units sold on average", "Sales are 3.2 times spend", "Spend causes a 3.2% rise in sales", "The correlation is 3.2"], "answer": 0,
   "explain": "The slope is the average change in Y per one-unit change in X, in the data's units; causality needs more."},
  {"q": "Least squares chooses the line that minimises…", "options": ["the sum of squared residuals", "the sum of absolute residuals", "the number of points off the line", "the largest residual"], "answer": 0,
   "explain": "That is the definition of ordinary least squares."},
  {"q": "In simple linear regression with correlation r = 0.6, R² is…", "options": ["0.36", "0.6", "0.77", "1.2"], "answer": 0,
   "explain": "With one predictor, $R^2 = r^2$."},
  {"q": "Which interval should you report to forecast next week's sales?", "options": ["The prediction interval", "The confidence interval for the mean response", "The confidence interval for the slope", "The interquartile range"], "answer": 0,
   "explain": "A single future week includes the individual noise around the line."},
  {"q": "Why is a prediction interval wider than a confidence interval for the mean response at the same X?", "options": ["It adds the scatter of individual observations around the line", "It uses a 99% level", "It ignores the uncertainty in the slope", "It is computed from fewer data"], "answer": 0,
   "explain": "PI = uncertainty in the line + irreducible noise; CI = uncertainty in the line only."},
  {"q": "A model fit on spends of 1 to 10 predicts sales at a spend of 40. The main concern is…", "options": ["extrapolation: the relationship may not stay linear outside the data", "multicollinearity", "a low R²", "too many degrees of freedom"], "answer": 0,
   "explain": "The simulation showed a straight line predicting 310 where the truth was about 100."},
  {"q": "The fitted least-squares line always passes through…", "options": ["the point $(\\bar{X}, \\bar{Y})$", "the origin", "the largest data point", "the median of X"], "answer": 0,
   "explain": "Because $\\hat{b}_0 = \\bar{Y} - \\hat{b}_1\\bar{X}$."}
]
```

> **Source:** Bruce & Bruce, *Practical Statistics for Data Scientists* (O'Reilly, 2017), ch. 4, "Simple Linear Regression" (the regression equation, fitted values and residuals, least squares, prediction versus explanation) and "Prediction Using Regression" (dangers of extrapolation, confidence and prediction intervals); statsmodels documentation for the formula API and `get_prediction`.
