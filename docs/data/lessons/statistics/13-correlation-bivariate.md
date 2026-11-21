# Correlation and exploring two or more variables

> **Before this lesson:** [Estimates of variability](#/lesson/statistics/variability) (standard deviation and deviations from the mean) and [Exploring distributions and categorical data](#/lesson/statistics/distributions-categorical) (boxplots, frequency tables, proportions).

## In plain words

So far we have looked at one variable at a time. Most interesting questions involve two or more: do users who visit more often also buy more? Does conversion differ by device? **Correlation** measures how strongly two numeric variables move together, and a handful of tables and charts let you explore relationships between any mix of numeric and categorical variables.

An everyday picture: taller people tend to weigh more. Not always (there are tall slim people and short heavy ones), but there is a clear tendency. Correlation puts a number on "tendency to move together", from $-1$ (perfectly opposite) through 0 (no straight-line relationship) to $+1$ (perfectly together).

Why it matters for a job: correlation tables are among the first things you compute on a new dataset, they guide which features to put in a model, and they are behind a famous trap: correlation is not causation. Interviewers check that you can compute and interpret a correlation, know when Pearson's version misleads, and can choose the right table or chart for each pair of variable types.

## 1. Covariance and Pearson's correlation coefficient

Start with deviations from the mean for two variables $x$ and $y$. When high values of $x$ tend to go with high values of $y$, the products $(x_i - \bar{x})(y_i - \bar{y})$ are mostly positive (both deviations positive, or both negative). When high $x$ goes with low $y$, the products are mostly negative. The **covariance** averages these products:

$$\operatorname{cov}(x, y) = \frac{1}{n-1}\sum_{i=1}^n (x_i - \bar{x})(y_i - \bar{y})$$

Covariance has awkward units (hours times points, for example) and its size depends on the scale of each variable. Dividing by both standard deviations removes the units and gives **Pearson's correlation coefficient**, usually written $r$:

$$r = \frac{\sum_{i}(x_i - \bar{x})(y_i - \bar{y})}{(n-1)\, s_x\, s_y}$$

$r$ always lies between $-1$ and $+1$. A value of $+1$ means the points lie exactly on a rising straight line; $-1$, exactly on a falling one; 0 means no *linear* (straight-line) relationship.

```python-run
import numpy as np
from scipy import stats
hours = np.array([1, 2, 2, 3, 4, 5, 6, 7, 8, 9])
score = np.array([52, 55, 61, 58, 66, 70, 71, 78, 80, 86])
dx, dy = hours - hours.mean(), score - score.mean()
r = np.sum(dx * dy) / ((len(hours) - 1) * hours.std(ddof=1) * score.std(ddof=1))
print("Pearson r by hand  :", round(r, 4))
print("np.corrcoef        :", round(np.corrcoef(hours, score)[0, 1], 4))
print("Spearman rho       :", round(stats.spearmanr(hours, score).statistic, 4))
print("Kendall tau        :", round(stats.kendalltau(hours, score).statistic, 4))
score_typo = score.copy(); score_typo[0] = 520
print("with one typo -> Pearson", round(np.corrcoef(hours, score_typo)[0, 1], 3),
      " Spearman", round(stats.spearmanr(hours, score_typo).statistic, 3))
```

**Reading this code line by line**

- `hours` and `score` are ten students' study hours and exam scores.
- `dx` and `dy` are the deviations from each mean; `np.sum(dx * dy)` adds their products, and dividing by $(n-1)s_x s_y$ is the formula above.
- `np.corrcoef(hours, score)` returns a 2 × 2 **correlation matrix** (each variable's correlation with itself, 1, on the diagonal); `[0, 1]` picks the off-diagonal entry.
- `stats.spearmanr` and `stats.kendalltau` compute two rank-based alternatives described in section 2; `.statistic` extracts the coefficient from the returned result object.
- The last two lines replace the first score, 52, with a typo, 520, and recompute.

$r = 0.9832$ both by hand and with NumPy: a very strong positive linear relationship. With one typo, Pearson's $r$ collapses to $-0.412$ and even changes sign. Spearman's coefficient falls too, to 0.432, but it is far less distorted.

> [!NOTE]
> The square of $r$, often written $R^2$, is the share of the variance in $y$ that a straight line in $x$ can explain. $r = 0.98$ gives $r^2 = 0.97$. You will meet $R^2$ again in the regression lessons.

## 2. Rank correlations: Spearman and Kendall

Pearson's $r$ uses the actual values, so it is sensitive to outliers and only captures straight-line relationships. **Rank correlations** first replace each value by its **rank** (1 for the smallest, 2 for the next, and so on) and then measure agreement between the rankings.

- **Spearman's rho** ($\rho$) is Pearson's $r$ computed on the ranks. It equals 1 whenever $y$ always increases when $x$ increases, even along a curve. Such a relationship is called **monotonic** (always moving in one direction).
- **Kendall's tau** ($\tau$) looks at every pair of records and asks whether they are ordered the same way by both variables (a **concordant** pair) or opposite ways (**discordant**). Tau is the difference between the share of concordant and discordant pairs. It is usually smaller in size than Spearman's rho and is popular with small samples.

Both are robust to outliers because an extreme value only gets the top rank, however extreme it is. Use them for ordinal data (ratings), skewed data, or when you care about "goes up together" rather than "lies on a line".

## 3. What correlation cannot see

A correlation near zero does not mean "no relationship".

```python-run
import numpy as np
x = np.linspace(-3, 3, 61)
y = x ** 2
print("r for y = x^2 on a symmetric range:", round(np.corrcoef(x, y)[0, 1], 4))
y2 = np.exp(x)
print("r for y = exp(x):", round(np.corrcoef(x, y2)[0, 1], 3))
```

**Reading this code line by line**

- `np.linspace(-3, 3, 61)` makes 61 evenly spaced numbers from $-3$ to $3$.
- `y = x ** 2` is a perfect U-shaped relationship: $y$ is completely determined by $x$.
- `np.exp(x)` is a perfect, curved, always-rising relationship.

The U-shape gets $r = 0.0$: the left half falls and the right half rises, and the two cancel exactly. The exponential gets 0.816, not 1, because it is curved. Correlation measures *linear* association only. Always plot the data: a **scatterplot**, one dot per record with $x$ on the horizontal axis and $y$ on the vertical, reveals curves, clusters and outliers that one number hides. A classic demonstration, Anscombe's quartet, shows four datasets with identical means, variances and correlation (about 0.82) whose scatterplots look completely different.

> [!WARNING]
> **Correlation is not causation.** Ice-cream sales and drowning deaths are correlated because both rise in hot weather. A third variable that drives both is called a **confounder**. The lesson [Correlation, causation and Simpson's paradox](#/lesson/statistics/causation-simpson) is devoted to this; for now, treat every correlation as a lead to investigate, not a conclusion.

## 4. Correlation matrices

With many numeric columns, a **correlation matrix** shows every pairwise correlation in one table. pandas computes it with `.corr()` (Pearson by default; pass `method="spearman"` or `"kendall"` for the others).

```python-run
import numpy as np
import pandas as pd
rng = np.random.default_rng(11)
n = 1000
visits = rng.poisson(8, n)
minutes = visits * 3 + rng.normal(0, 6, n)
orders = rng.binomial(visits, 0.08)
support = rng.poisson(1, n)
df = pd.DataFrame({"visits": visits, "minutes": minutes, "orders": orders, "tickets": support})
print(df.corr().round(2))
```

**Reading this code line by line**

- We simulate 1,000 users. `rng.poisson(8, n)` draws visit counts averaging 8 (the Poisson distribution, for counts, is covered in [Binomial, Poisson and other common distributions](#/lesson/statistics/discrete-distributions)).
- `minutes` is built from visits plus noise, so the two should be strongly related.
- `rng.binomial(visits, 0.08)` gives each visit an 8% chance of becoming an order, so orders depend on visits but with a lot of randomness.
- `tickets` (support tickets) is generated independently of everything else.

The matrix shows visits and minutes at 0.82, visits and orders at 0.26, and tickets near 0 with everything. The diagonal is always 1, and the matrix is symmetric. In real data such a table is often drawn as a heatmap with colour for strength. Two warnings: with many variables, some sizeable correlations appear by chance alone; and two features that are very highly correlated with each other (like visits and minutes) can cause trouble in regression, a problem called multicollinearity, covered in the regression lessons.

## 5. Two numeric variables with many points

With thousands of points a scatterplot becomes a solid blob. Alternatives:

- **Hexagonal binning** (hexbin): tile the plane with hexagons and colour each by the number of points inside. It is a two-dimensional histogram.
- **Contour plots**: draw lines of equal density, like a topographic map, from a two-dimensional KDE.
- Transparency (each dot faint so overlaps darken) and random sub-sampling.

These show where most of the data is, which a crowded scatterplot hides.

## 6. Two categorical variables: contingency tables

For two categorical variables, the tool is a **contingency table** (cross-tabulation): rows are the categories of one variable, columns the categories of the other, and each cell counts the records with that combination.

```python-run
import pandas as pd
import numpy as np
rng = np.random.default_rng(5)
n = 600
device = rng.choice(["android", "ios", "web"], size=n, p=[0.5, 0.3, 0.2])
p_buy = pd.Series(device).map({"android": 0.10, "ios": 0.16, "web": 0.06}).to_numpy()
bought = np.where(rng.random(n) < p_buy, "yes", "no")
tab = pd.crosstab(device, bought, rownames=["device"], colnames=["bought"], margins=True)
print(tab)
print(pd.crosstab(device, bought, rownames=["device"], colnames=["bought"], normalize="index").round(3))
```

**Reading this code line by line**

- `rng.choice([...], size=n, p=[...])` draws 600 devices with the given probabilities.
- `.map({...})` replaces each device with its purchase probability; `.to_numpy()` converts the result to a NumPy array.
- `pd.crosstab(rows, columns, margins=True)` counts each combination and adds row and column totals labelled `All`.
- `normalize="index"` divides each row by its own total, giving the purchase rate within each device.

The raw counts show 39 Android, 23 iOS and 6 web buyers. Raw counts mislead because the groups differ in size; the row percentages show the real story: 12.0% of Android users bought, 14.8% of iOS and 5.0% of web. Always decide which way to normalise: by row (rate within each device), by column (device mix among buyers) or by the grand total. Whether such differences are bigger than chance is the job of the chi-square test in [ANOVA and the chi-square test](#/lesson/statistics/anova-chi-square).

## 7. Numeric versus categorical: grouped summaries

To compare a numeric variable across categories, compute the summary per group and draw side-by-side boxplots. A **violin plot** is a variant that draws a mirrored density curve instead of a box, showing the shape of each group's distribution (for example two peaks) that a box would hide.

```python-run
import numpy as np
import pandas as pd
rng = np.random.default_rng(3)
df = pd.DataFrame({
    "plan": np.repeat(["free", "basic", "pro"], [300, 150, 50]),
    "minutes": np.concatenate([rng.lognormal(1.5, 0.6, 300), rng.lognormal(1.9, 0.5, 150), rng.lognormal(2.3, 0.4, 50)]),
})
print(df.groupby("plan")["minutes"].describe()[["count", "25%", "50%", "75%"]].round(1))
```

**Reading this code line by line**

- `np.repeat(["free", "basic", "pro"], [300, 150, 50])` repeats each label the given number of times.
- `np.concatenate` joins three arrays of simulated session lengths, one per plan.
- `df.groupby("plan")["minutes"]` splits the minutes column by plan; `.describe()` summarises each group, and the double brackets select four of its columns.

Median minutes rise from 4.5 (free) to 7.1 (basic) to 10.0 (pro), and the quartiles move up too. These are the numbers a side-by-side boxplot would draw. Note that groupby sorts groups alphabetically, which is why basic comes first.

## 8. Conditioning on a third variable

To explore three or more variables, split the data by a third, categorical variable and repeat the two-variable display in each panel. This is called **conditioning** (or faceting, or small multiples). For example, plot minutes against orders separately for each country. Conditioning is how you discover that a relationship holds in one segment and not another, or even reverses, which is Simpson's paradox, met later.

## Summary

- Covariance averages products of deviations; Pearson's $r$ rescales it to $[-1, 1]$ and measures linear association.
- Spearman's rho and Kendall's tau work on ranks: robust to outliers and sensitive to any monotonic relationship.
- $r$ near zero does not rule out a strong curved relationship; always look at a scatterplot.
- Correlation matrices summarise many pairs; watch for chance correlations and highly correlated features.
- Use hexbin or contour plots for big numeric data, contingency tables for two categorical variables, grouped boxplots or violins for numeric versus categorical, and conditioning for a third variable.
- Correlation does not establish causation.

## Glossary

- **Covariance**: the average product of two variables' deviations from their means.
- **Pearson's correlation coefficient ($r$)**: covariance divided by both standard deviations; ranges from $-1$ to $1$.
- **Correlation matrix**: a table of all pairwise correlations.
- **Linear relationship**: one where points scatter around a straight line.
- **Rank**: a value's position in sorted order.
- **Spearman's rho / Kendall's tau**: correlation of ranks / net share of concordant pairs.
- **Monotonic**: always moving in one direction, though not necessarily in a straight line.
- **Concordant / discordant pair**: two records ordered the same way / opposite ways by both variables.
- **Scatterplot**: a chart with one dot per record at its $(x, y)$ position.
- **Confounder**: a third variable that influences both variables being compared.
- **Hexagonal binning / contour plot**: two-dimensional histogram with hexagons / lines of equal density.
- **Contingency table (cross-tabulation)**: counts for each combination of two categorical variables.
- **Violin plot**: a boxplot-like chart showing each group's density shape.
- **Conditioning (faceting)**: repeating a chart for each value of a third variable.

## Check yourself

```quiz
[
  {"q": "Points lie exactly on the curve $y = x^2$ for $x$ from $-3$ to $3$. Pearson's $r$ is about…", "options": ["0", "1", "−1", "0.5"], "answer": 0,
   "explain": "The relationship is perfect but not linear; the falling and rising halves cancel."},
  {"q": "Which statistic is least affected by one wildly wrong value?", "options": ["Spearman's rho", "Pearson's r", "Covariance", "The mean of x"], "answer": 0,
   "explain": "Rank-based measures only see that the extreme value is the largest, not how large it is."},
  {"q": "Pearson's r between two metrics is 0.9. What can you conclude?", "options": ["They have a strong positive linear association, but not that one causes the other", "One metric causes the other", "Their means are equal", "90% of users are in both groups"], "answer": 0,
   "explain": "Correlation measures association; a confounder or reverse causation could explain it."},
  {"q": "Spearman's rho is 1 for which relationship?", "options": ["$y = e^x$, always increasing", "$y = x^2$ on $[-3, 3]$", "Random noise", "$y = -x$"], "answer": 0,
   "explain": "Any strictly increasing (monotonic) relationship has perfectly matching ranks."},
  {"q": "In a device × purchase crosstab, Android has 39 buyers and web has 6. What should you compute before concluding Android converts better?", "options": ["Row percentages: buyers divided by users within each device", "Column totals only", "The correlation between device names", "Nothing; counts are enough"], "answer": 0,
   "explain": "The groups differ in size; rates within each group are what compare fairly."},
  {"q": "Which display suits two numeric variables with a million points?", "options": ["A hexbin or contour plot", "A pie chart", "A contingency table", "A single correlation number only"], "answer": 0,
   "explain": "Density-style plots show where data concentrate; a raw scatterplot becomes a solid blob."}
]
```

> **Source:** Bruce & Bruce, *Practical Statistics for Data Scientists* (O'Reilly, 2017), ch. 1, "Correlation" (correlation coefficient, correlation matrix, scatterplots, other correlation estimates) and "Exploring Two or More Variables" (hexagonal binning and contours, two categorical variables, categorical and numeric data, visualizing multiple variables); examples here are original.
