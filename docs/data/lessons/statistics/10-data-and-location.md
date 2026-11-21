# Data types and estimates of location

> **Before this lesson:** [Probability, conditional probability and Bayes' rule](#/lesson/statistics/probability-bayes) introduced the expected value, which is the "population" version of the mean you meet here. You should be able to read a short Python program; pandas is explained from scratch below.

## In plain words

Before you can analyse data you have to know what kind of data it is, and the first thing almost anyone wants to know about a column of numbers is "what is a typical value?" This lesson covers both: the **types** of data you will meet, and the **estimates of location**, the single numbers (mean, median and their relatives) that summarise where the data sits.

An everyday picture: you ask what people in your office earn. Ten engineers earn around S\$7,000 a month and the founder earns S\$200,000. The average is about S\$24,500, a number that describes nobody in the room. The median, the salary of the person in the middle, is about S\$7,000 and describes most people well. Choosing the right summary is a real decision with real consequences.

Why it matters for a job: **exploratory data analysis** (EDA), the first look at a dataset before any modelling, is the opening move in every analytics task and many interview case questions. Interviewers ask "mean or median for session length?", "how would you average conversion rates across stores?" and "what does an outlier do to your metric?". Getting these right is what separates a careful analyst from someone who runs `.mean()` on everything.

## 1. Kinds of data

Raw data arrives as images, text, click logs and sensor streams: **unstructured** data with no fixed rows and columns. Most statistical methods need **structured** data: a table where each column has a definite type. The main types are:

- **Numeric** data is measured or counted.
  - **Continuous** data can take any value in a range: an order amount of S\$23.50, a session lasting 312.7 seconds. Also called interval, float or numeric data.
  - **Discrete** data takes only whole-number values, usually counts: number of items in a basket, logins per week.
- **Categorical** data takes one of a fixed set of labels: payment method, country, device type. Also called nominal data, factors or enums.
  - **Binary** data is categorical with exactly two values: clicked or not, member or not, 1 or 0. Also called dichotomous, boolean or indicator data.
  - **Ordinal** data is categorical with a meaningful order: a rating of poor < fair < good < excellent, a T-shirt size S < M < L.

Why bother classifying? Because the type decides which summaries, charts and models make sense. Averaging country codes is meaningless; sorting ratings alphabetically puts "excellent" before "fair". Telling software the type lets it choose sensible defaults, store data compactly and refuse invalid values.

## 2. Rectangular data and pandas

The standard shape for analysis is **rectangular data**: a table like a spreadsheet. Each row is a **record** (also called a case, observation, instance or sample); each column is a **feature** (also called a variable, attribute or predictor). When we want to predict one column from the others, that column is the **outcome** (also called the target, response or dependent variable).

In Python, rectangular data lives in a pandas **DataFrame**, a table with labelled columns where each column has a single type, its **dtype** (data type).

```python-run
import pandas as pd
orders = pd.DataFrame({
    "order_id":   [101, 102, 103, 104, 105, 106],
    "amount_sgd": [23.50, 8.90, 120.00, 45.25, 15.00, 61.80],
    "items":      [2, 1, 6, 3, 1, 4],
    "channel":    ["app", "web", "app", "app", "web", "app"],
    "is_member":  [True, False, True, False, False, True],
    "rating":     ["good", "poor", "excellent", "good", "fair", "good"],
})
print(orders.dtypes)
orders["channel"] = orders["channel"].astype("category")
orders["rating"] = pd.Categorical(orders["rating"],
                                  categories=["poor", "fair", "good", "excellent"], ordered=True)
print(orders["rating"].max(), "|", (orders["rating"] >= "good").sum(), "orders rated good or better")
```

**Reading this code line by line**

- `import pandas as pd` loads the pandas library under the short name `pd`.
- `pd.DataFrame({...})` builds a table from a dictionary: each key becomes a column name and each list becomes that column's values, row by row.
- `orders.dtypes` lists each column's type. Whole numbers become `int64` (64-bit integers), decimals `float64`, true/false `bool`, and text shows as `object` (or `str` in the newest pandas versions). The text columns are not yet marked as categorical.
- `.astype("category")` converts `channel` to pandas' categorical type, which stores each label once and refers to it by a small code.
- `pd.Categorical(..., categories=[...], ordered=True)` makes `rating` an **ordered** categorical, so comparisons follow the order we listed rather than the alphabet.

After conversion, `orders["rating"].max()` is `excellent`, and 4 orders are rated good or better. With plain text, `max` would compare letters and return "poor", because "p" comes last alphabetically.

Note the column `order_id`: it is stored as an integer but it is really a label. Its "mean" is meaningless. A column's storage type and its statistical type are not always the same, and part of EDA is deciding which is which.

> [!NOTE]
> Not all data is rectangular. **Time series** record one variable at successive times; **spatial** data is tied to locations; **graph** (network) data records connections between entities, such as who follows whom. Each needs its own methods, but most analyses end by flattening into a table.

## 3. The mean

The **mean** (arithmetic average) is the sum of the values divided by how many there are. For values $x_1, x_2, \dots, x_n$:

$$\bar{x} = \frac{1}{n}\sum_{i=1}^{n} x_i$$

The bar over $x$ is the standard notation for a sample mean, and $n$ is the number of records. The mean uses every value, which is its strength (it is efficient when the data are well behaved) and its weakness (one extreme value can drag it anywhere).

## 4. The median, outliers and robustness

The **median** is the middle value after sorting. With an odd number of values it is the one in the centre; with an even number it is the average of the two central values. It depends only on the order of the values, not their size, so it barely moves when one value becomes extreme.

An **outlier** is a value very far from most of the others. Outliers may be data errors (a price typed in cents instead of dollars, a test account) or genuine but unusual records (a corporate customer). Either way they deserve a look; deleting them without investigation is a mistake. An estimate that is little affected by outliers is called **robust** (or resistant).

The **trimmed mean** is a compromise between mean and median: sort the values, drop a fixed share from each end, and average what remains. A 10% trimmed mean of 100 values drops the 10 smallest and 10 largest. It keeps more information than the median but resists a few extreme values. Judges' scores in diving and gymnastics competitions use the same idea, discarding the highest and lowest score.

```python-run
import numpy as np
from scipy import stats
spend = np.array([12, 15, 18, 20, 22, 25, 27, 30, 34, 38, 41, 2400])
print("mean          :", round(spend.mean(), 2))
print("median        :", np.median(spend))
print("trimmed mean  :", round(stats.trim_mean(spend, 0.1), 2))
print("mean w/o whale:", round(spend[:-1].mean(), 2))
```

**Reading this code line by line**

- `np.array([...])` holds the monthly spend, in dollars, of 12 customers. The last customer, a "whale" (a very high spender), spent 2,400.
- `spend.mean()` and `np.median(spend)` compute the two basic summaries.
- `stats.trim_mean(spend, 0.1)` from SciPy drops 10% of the values from each end before averaging. With 12 values, 10% is 1.2, which SciPy rounds down to 1 value per end.
- `spend[:-1]` means "everything except the last element".

The mean is 223.5, almost ten times what anyone other than the whale spent. The median is 26.0 and the 10% trimmed mean 27.0, both close to the 25.64 you get by removing the whale entirely. One customer controls the mean.

Which should you report? It depends on the question.

- If you need **total revenue** (for example to forecast spend for 1,000 similar customers), the mean is right, whale included: total = mean × count. The median would badly underestimate.
- If you need a **typical customer** (for example to design a default bundle), the median or trimmed mean describes people far better.
- For heavily skewed metrics such as revenue per user, analysts often report both, and sometimes **winsorise** (cap extreme values at a high percentile, such as the 99th) to reduce noise while keeping every customer in the data.

> [!INTERVIEW]
> "Our average session length jumped 20% overnight." A good first answer: check the median too. If the median did not move, a handful of extreme sessions (bots, a tab left open for days, a logging bug) probably drove the mean. Then segment by platform and app version to find them.

## 5. Weighted mean and weighted median

Sometimes records deserve different importance. The **weighted mean** multiplies each value by a **weight** $w_i$ and divides by the total weight:

$$\bar{x}_w = \frac{\sum_{i} w_i x_i}{\sum_i w_i}$$

Two common reasons to weight:

1. **Records summarise groups of different sizes.** A store with 12,000 visits deserves more say in an average conversion rate than one with 150 visits.
2. **Some groups are under- or over-represented in a sample.** If a survey reached too few older users, weighting their answers up corrects the mix.

```python-run
import numpy as np
visits = np.array([12000, 800, 450, 3000, 150])
conv_rate = np.array([0.021, 0.050, 0.060, 0.030, 0.100])
print("simple mean of rates :", round(conv_rate.mean(), 4))
print("weighted by visits   :", round(np.average(conv_rate, weights=visits), 4))
print("pooled orders/visits :", round((conv_rate * visits).sum() / visits.sum(), 4))

def weighted_median(values, weights):
    order = np.argsort(values)
    v, w = values[order], weights[order]
    cum = np.cumsum(w)
    return v[np.searchsorted(cum, cum[-1] / 2)]
print("weighted median rate :", weighted_median(conv_rate, visits))
```

**Reading this code line by line**

- `visits` and `conv_rate` describe five stores: how many visits each had and what share of visits became orders.
- `np.average(values, weights=...)` computes the weighted mean.
- The "pooled" line rebuilds the number of orders per store (`rate × visits`), adds them up and divides by total visits. It equals the visit-weighted mean, which shows what weighting means: it is the rate you get by treating all visits as one big group.
- `weighted_median` sorts the values (`np.argsort` returns the positions that would sort the array), adds up the weights in that order with `np.cumsum` (cumulative sum), and returns the first value where the running total reaches half the total weight. `np.searchsorted` finds that position.

The simple mean of the five rates is 0.0522, but the visit-weighted mean is 0.0259, half as large. The tiny stores with high rates pull the simple average up although they contribute few orders. If the question is "what share of all our visits convert?", the answer is 2.59%. The weighted median, 0.021, says that at least half of all visits happen at stores converting at 2.1% or less.

> [!WARNING]
> "Average of averages" is one of the most common analytics bugs. Averaging per-store rates, per-day rates or per-country rates gives each group equal say no matter how big it is. Decide deliberately whether you want an unweighted mean of groups or the overall (pooled) rate, and say which in your report.

## 6. Other robust estimates of location

- The **weighted median** above combines robustness with weighting.
- The **mode** is the most frequent value. It is the natural "typical value" for categorical data (the most common payment method) and is covered in the next lessons.
- For data with a few gross errors, robust estimates are a cheap insurance policy. But robustness has a price: the median ignores how far values are from the centre, so with clean, symmetric data it is noisier than the mean. That is why the mean remains the default for well-behaved data and for anything that must add up to totals.

## 7. Sample versus population

A **population** is the whole set of things we care about (all our customers); a **sample** is the subset we actually observe. Statisticians use Greek letters for population quantities ($\mu$, mu, for the population mean) and Roman letters for sample estimates ($\bar{x}$). A number computed from a sample, such as $\bar{x}$, is an **estimate** or **statistic**; the corresponding population quantity is a **parameter**. Data scientists tend to say **metric** for any number used to track a business, such as daily active users. The rest of this track is largely about how far an estimate can be from the parameter it targets.

## 8. Summary table

| Estimate | Uses | Robust to outliers? | Use it when |
|---|---|---|---|
| Mean | every value | No | data are roughly symmetric, or you need totals |
| Median | only the order | Yes | data are skewed or contain outliers; "typical" value |
| Trimmed mean | the middle share | Mostly | you want a robust but efficient compromise |
| Weighted mean | values and weights | No | records stand for groups of different size |
| Weighted median | order and weights | Yes | weighted and skewed |
| Mode | counts | Yes | categorical data |

## Common mistakes

- Averaging identifier or code columns because they are stored as numbers.
- Sorting ordinal labels alphabetically instead of by their meaning.
- Reporting only the mean of a heavily skewed metric such as revenue, latency or session length.
- Averaging rates across groups of very different sizes without weighting.
- Deleting outliers to make a chart look nicer instead of finding out what they are.

## Summary

- Structured data is numeric (continuous or discrete) or categorical (including binary and ordinal); the type decides which summaries and models make sense.
- A DataFrame holds rectangular data: rows are records, columns are features, and one column may be the outcome. Mark categorical and ordinal columns explicitly.
- The mean uses every value and is sensitive to outliers; the median and trimmed mean are robust.
- Weighted means give larger groups more say; the pooled rate equals the size-weighted mean of group rates.
- Pick the estimate that answers the business question: totals need the mean, "typical" usually needs the median.

## Glossary

- **Exploratory data analysis (EDA)**: the first look at data, with summaries and plots, before modelling.
- **Structured / unstructured data**: data in a fixed table layout / data such as raw text or images without one.
- **Continuous / discrete data**: numeric data that can take any value in a range / only whole-number counts.
- **Categorical, binary, ordinal data**: labels from a fixed set / with two values / with a meaningful order.
- **Rectangular data / DataFrame**: a table of rows and columns / pandas' table object.
- **Record / feature / outcome**: a row / a column / the column to be predicted.
- **dtype**: the storage type of a pandas column.
- **Mean ($\bar{x}$)**: sum of values divided by their number.
- **Median**: the middle value of the sorted data.
- **Outlier**: a value far from most others.
- **Robust (resistant)**: little affected by outliers.
- **Trimmed mean**: the mean after dropping a share of the smallest and largest values.
- **Winsorise**: cap extreme values at a chosen percentile.
- **Weighted mean / weighted median**: mean / median in which each value counts according to a weight.
- **Mode**: the most frequent value.
- **Population / sample**: everything of interest / the part observed.
- **Parameter / statistic (estimate)**: a population quantity / a number computed from a sample.
- **Metric**: a number used to measure or track something in a business.

## Check yourself

```quiz
[
  {"q": "A column of customer star ratings (1 to 5) is best described as…", "options": ["ordinal categorical", "continuous", "nominal categorical with no order", "binary"], "answer": 0,
   "explain": "The values are labels with a natural order but the gaps between them are not guaranteed to be equal."},
  {"q": "Twelve customers spent 12, 15, ..., 41 and one spent 2,400. Which estimate best describes a typical customer?", "options": ["The median", "The mean", "The maximum", "The sum"], "answer": 0,
   "explain": "One whale drags the mean to 223.5 while the median stays at 26."},
  {"q": "You need to forecast total monthly revenue from 10,000 new customers like these. Which estimate do you multiply by 10,000?", "options": ["The mean", "The median", "The mode", "The trimmed mean"], "answer": 0,
   "explain": "Total = mean × count. Robust estimates throw away exactly the extreme spend that contributes to the total."},
  {"q": "Store A converts 2% of 10,000 visits and store B converts 10% of 100 visits. The overall conversion rate is closest to…", "options": ["2.1%", "6%", "10%", "12%"], "answer": 0,
   "explain": "Pooled: (200 + 10) / 10,100 is about 2.08%. The unweighted average of rates (6%) gives the tiny store equal say."},
  {"q": "What does a 10% trimmed mean of 50 values do?", "options": ["Drops the 5 smallest and 5 largest values and averages the remaining 40", "Drops the 10 largest values", "Averages only the middle 10% of values", "Multiplies the mean by 0.9"], "answer": 0,
   "explain": "10% of 50 is 5 values cut from each end."},
  {"q": "Why mark a text column as an ordered categorical in pandas?", "options": ["So that sorting and comparisons follow the meaningful order rather than the alphabet", "To make it numeric so you can average it", "Because pandas cannot store text", "To remove missing values"], "answer": 0,
   "explain": "With `ordered=True`, `'poor' < 'fair' < 'good' < 'excellent'` is respected by sort, min, max and comparisons."}
]
```

> **Source:** Bruce & Bruce, *Practical Statistics for Data Scientists* (O'Reilly, 2017), ch. 1, sections "Elements of Structured Data", "Rectangular Data" and "Estimates of Location" (mean, trimmed mean, weighted mean, median, weighted median, outliers, robust estimates); examples here are original and use pandas, NumPy and SciPy.
