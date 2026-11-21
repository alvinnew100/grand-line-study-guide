# Evaluating classifiers and handling rare classes

> **Before this lesson:** [Logistic regression: odds, log-odds and maximum likelihood](#/lesson/statistics/logistic-regression) (predicted probabilities) and expected value from [Exploring distributions and categorical data](#/lesson/statistics/distributions-categorical). The [ML track's metrics lesson](#/lesson/ml/metrics) walks through precision-recall and ROC curves with scikit-learn in detail; this lesson adds the statistical reading of AUC, lift, the cost-based threshold and what resampling does to probabilities.

## In plain words

A classifier outputs a score or probability; turning it into decisions requires a threshold, and judging it requires metrics that respect what errors cost. The hardest and most common case in business is the **rare class**: fraud, churn in a given week, clicks on an ad, defaults on a loan. With 2% positives, a model that always says "no" is 98% accurate and worthless. This lesson covers the confusion matrix and its metrics, ROC curves and AUC read as a probability, lift, choosing a threshold by expected value, and the main strategies for imbalanced data (undersampling, oversampling, weighting) with their side effect on predicted probabilities.

An everyday picture: an airport scanner. Set it to beep at everything and you catch every threat while queues stretch for hours; set it to beep at almost nothing and queues vanish while threats pass. The right setting depends on the costs of a missed threat and of a false alarm, not on "accuracy".

Why it matters for a job: choosing metrics and thresholds is a business decision that data scientists must frame. Interviewers ask: "Your fraud model is 98% accurate; is it good?", "What does an AUC of 0.8 mean?", "How do you pick a threshold?", and "What happens to predicted probabilities if you undersample the majority class?"

## 1. The confusion matrix and its metrics

For a chosen threshold, every prediction falls into one of four cells:

| | predicted positive | predicted negative |
|---|---|---|
| **actually positive** | true positive (TP) | false negative (FN) |
| **actually negative** | false positive (FP) | true negative (TN) |

From these:

- **Accuracy** $= (TP + TN)/\text{all}$: share of correct predictions.
- **Precision** $= TP/(TP + FP)$: of those flagged, the share that are truly positive.
- **Recall** (sensitivity, true positive rate) $= TP/(TP + FN)$: of the true positives, the share flagged.
- **Specificity** (true negative rate) $= TN/(TN + FP)$: of the true negatives, the share correctly left alone. $1 - \text{specificity}$ is the **false positive rate**.

```python-run
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix
rng = np.random.default_rng(52)
n = 20_000
X = rng.normal(size=(n, 3))
logit = -4.6 + 1.2 * X[:, 0] + 0.8 * X[:, 1]
y = (rng.random(n) < 1 / (1 + np.exp(-logit))).astype(int)
tr, te = slice(0, 15_000), slice(15_000, None)
model = LogisticRegression().fit(X[tr], y[tr])
p = model.predict_proba(X[te])[:, 1]
print(f"positive rate in test set: {y[te].mean():.4f}")
for t in [0.5, 0.1, 0.03]:
    tn, fp, fn, tp = confusion_matrix(y[te], (p >= t).astype(int)).ravel()
    acc = (tp + tn) / (tp + tn + fp + fn)
    prec = tp / (tp + fp) if tp + fp else float("nan")
    rec = tp / (tp + fn)
    spec = tn / (tn + fp)
    print(f"threshold {t:4}: TP {tp:3d} FP {fp:4d} FN {fn:3d} TN {tn:4d} | accuracy {acc:.3f} precision {prec:.3f} recall {rec:.3f} specificity {spec:.3f}")
```

**Reading this code line by line**

- We simulate 20,000 transactions with about 2.6% fraud; the third feature is pure noise.
- `slice(0, 15_000)` and `slice(15_000, None)` split rows into training and test sets.
- `confusion_matrix(y_true, y_pred).ravel()` flattens scikit-learn's 2 × 2 matrix (rows = truth, columns = prediction) into TN, FP, FN, TP in that order.
- The loop evaluates three thresholds on the predicted probability.

At the default threshold 0.5, accuracy is 0.974, but recall is only 0.038: the model catches 5 of 132 frauds. Lowering the threshold to 0.1 catches 53 (recall 0.402) at the cost of 211 false alarms (precision 0.201); at 0.03, recall reaches 0.712 but precision falls to 0.090 and accuracy to 0.803. Accuracy *falls* as the model becomes more useful. With rare classes, ignore accuracy and look at the trade-off you actually care about.

## 2. ROC curves and AUC as a probability

The **ROC curve** (receiver operating characteristic, a name from radar engineering) plots recall (true positive rate) against the false positive rate as the threshold sweeps from 1 down to 0. A useless model follows the diagonal; a perfect one hugs the top-left corner. The **AUC** (area under the ROC curve) summarises it in one number with a precise meaning:

$$AUC = P(\text{score of a random positive} > \text{score of a random negative})$$

counting ties as one half. An AUC of 0.5 is random ranking, 1.0 is perfect. This interpretation also shows that AUC measures only *ranking*: it is unchanged by any monotone transformation of the scores and by the threshold. It is equivalent to the Mann-Whitney U statistic from the t-test lesson, rescaled.

```python-run
import numpy as np
from sklearn.metrics import roc_auc_score
rng = np.random.default_rng(53)
y = np.array([0] * 900 + [1] * 100)
score = np.where(y == 1, rng.normal(1.2, 1, 1000), rng.normal(0, 1, 1000))
pos, neg = score[y == 1], score[y == 0]
pairs = (pos[:, None] > neg[None, :]).mean() + 0.5 * (pos[:, None] == neg[None, :]).mean()
print(f"AUC as P(random positive outranks random negative): {pairs:.4f}")
print(f"sklearn roc_auc_score                             : {roc_auc_score(y, score):.4f}")
order = np.argsort(-score)
top10 = order[:100]
print(f"lift in top 10%: {y[top10].mean() / y.mean():.2f}  (captures {y[top10].sum()} of {y.sum()} positives)")
```

**Reading this code line by line**

- Positives get scores centred at 1.2 and negatives at 0, so the model ranks imperfectly.
- `pos[:, None] > neg[None, :]` compares every positive with every negative at once (a 100 × 900 table of `True`/`False`) through broadcasting; its mean is the share of pairs ranked correctly.
- `np.argsort(-score)` lists records from highest to lowest score; the first 100 are the top 10%.

The pairwise share, 0.8069, equals scikit-learn's AUC exactly. **Lift** answers a marketer's question: if we act on the top 10% of scores, how much richer in positives is that group than average? Here the top decile has 4.30 times the base rate and captures 43 of the 100 positives. **Gains charts** (cumulative share of positives captured against share of population targeted) and lift charts are the standard way to present targeting models to business teams.

For very rare classes, the **precision-recall curve** and its summary, average precision, are often more informative than ROC, because the false positive rate can look tiny even when false positives vastly outnumber true positives.

## 3. Choosing a threshold by expected value

The best threshold follows from costs and benefits, not from 0.5. Suppose reviewing a flagged transaction costs 5 dollars and catching a fraud saves 200. Reviewing a transaction with fraud probability $p$ has expected value $200p - 5(1-p)$, which is positive when

$$p > \frac{\text{cost of a false positive}}{\text{cost of a false positive} + \text{benefit of a true positive}}$$

```python-run
benefit_tp = 200
cost_fp = 5
threshold = cost_fp / (cost_fp + benefit_tp)
print(f"act when P(fraud) > {threshold:.4f}")
for p in [0.01, 0.03, 0.10]:
    ev = p * benefit_tp - (1 - p) * cost_fp
    print(f"P = {p:.2f}: expected value of reviewing = {ev:+.2f}")
```

**Reading this code line by line**

- The threshold formula comes from setting the expected value to zero and solving for $p$.
- `{ev:+.2f}` prints the sign explicitly.

Reviews pay off whenever the fraud probability exceeds 0.0244: at 1% the expected value is $-2.95$ dollars, at 3% it is $+1.15$. A threshold of 0.5 would leave a great deal of money on the table. This calculation requires *calibrated* probabilities, which is one reason logistic regression remains popular, and why the next section matters. When review capacity is fixed (say, 500 reviews a day), the threshold is instead set by ranking: review the top 500 scores.

## 4. Strategies for imbalanced data

When positives are rare, models may struggle to learn their patterns, and default thresholds produce almost no positive predictions. Common strategies:

- **Undersampling** the majority class: keep all positives and a random subset of negatives, for example a 50/50 mix. Faster training; discards data.
- **Oversampling** the minority class: replicate positives (bootstrap them) or generate synthetic ones. **SMOTE** (synthetic minority oversampling technique) creates new positives by interpolating between a positive and one of its nearest positive neighbours.
- **Up-weighting** (class weights): keep all data but make each positive count more in the loss, for example `class_weight="balanced"` in scikit-learn.
- **Threshold moving**: keep the model as is and lower the threshold. Often the simplest and as effective as anything else.
- **Cost-sensitive evaluation**: judge models by expected value rather than accuracy.

What these strategies do to probabilities:

```python-run
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
rng = np.random.default_rng(54)
n = 40_000
X = rng.normal(size=(n, 2))
y = (rng.random(n) < 1 / (1 + np.exp(-(-4.0 + 1.0 * X[:, 0] + 0.7 * X[:, 1])))).astype(int)
Xtr, ytr, Xte, yte = X[:30_000], y[:30_000], X[30_000:], y[30_000:]
pos = np.where(ytr == 1)[0]
neg = rng.choice(np.where(ytr == 0)[0], size=len(pos), replace=False)
idx = np.concatenate([pos, neg])
models = {
    "original data": LogisticRegression().fit(Xtr, ytr),
    "undersampled 50/50": LogisticRegression().fit(Xtr[idx], ytr[idx]),
    "class_weight=balanced": LogisticRegression(class_weight="balanced").fit(Xtr, ytr),
}
print(f"true positive rate in test data: {yte.mean():.4f}")
for name, m in models.items():
    p = m.predict_proba(Xte)[:, 1]
    print(f"{name:22s} mean predicted P {p.mean():.4f}  AUC {roc_auc_score(yte, p):.4f}")
p_u = models["undersampled 50/50"].predict_proba(Xte)[:, 1]
beta = len(neg) / (ytr == 0).sum()
p_fixed = beta * p_u / (beta * p_u - p_u + 1)
print(f"undersampled, corrected   mean predicted P {p_fixed.mean():.4f}")
```

**Reading this code line by line**

- `np.where(ytr == 1)[0]` lists the positions of positives; `rng.choice(..., replace=False)` picks an equal number of negatives without repeats.
- Three logistic regressions are trained: on the original data, on the balanced undersample, and on the original data with balanced class weights.
- `beta` is the share of negatives kept by undersampling. The last formula converts an undersampled model's probability back to the original base rate (a standard **prior correction**).

All three models have the same AUC (0.8022): resampling and weighting did not improve the ranking at all. But the average predicted probability jumps from 0.0329 (close to the true 0.0333) to about 0.38 for the rebalanced models: their probabilities are no longer calibrated. Using them for expected-value thresholds would trigger far too many reviews. The prior correction restores a mean of 0.0338.

Lessons: resampling and weighting mostly shift the intercept (and the implied threshold) for simple models; they can help flexible models (trees, boosting) learn the rare class and help when data are huge. If you resample, either correct the probabilities or recalibrate on untouched data, and always evaluate on data with the real class mix.

> [!INTERVIEW]
> "Fraud is 0.5% of transactions. How do you build and evaluate a model?" Use a time-based train/test split; evaluate with precision-recall (average precision), recall at a fixed review budget, and expected dollars saved, not accuracy. Try class weights or undersampling for training efficiency, but keep the test set at the true base rate and recalibrate probabilities before setting a cost-based threshold.

## 5. Other classification metrics briefly

- **Log-loss**: the average negative log-likelihood; rewards calibrated probabilities and punishes confident mistakes harshly.
- **Brier score**: mean squared difference between predicted probability and outcome; a calibration-sensitive alternative.
- **F1 score**: harmonic mean of precision and recall, for when both matter and no costs are known.
- **Calibration plot**: predicted probability (binned) against observed frequency; points on the diagonal mean calibrated.

## Summary

- The confusion matrix gives accuracy, precision, recall, specificity; with rare classes accuracy is misleading.
- Moving the threshold trades precision against recall; ROC and precision-recall curves show all thresholds.
- AUC is the probability that a random positive is scored above a random negative; it measures ranking only.
- Lift and gains charts show how much better than random a targeted group is.
- Pick thresholds by expected value: act when $p > \text{cost}_{FP} / (\text{cost}_{FP} + \text{benefit}_{TP})$, using calibrated probabilities.
- Undersampling, oversampling (including SMOTE) and class weights rebalance training; they distort probabilities, which need correction or recalibration.

## Glossary

- **Confusion matrix**: counts of true/false positives/negatives.
- **Accuracy / precision / recall / specificity**: overall correctness / purity of flags / share of positives found / share of negatives left alone.
- **False positive rate**: $FP/(FP + TN)$.
- **ROC curve**: true positive rate against false positive rate over all thresholds.
- **AUC**: area under the ROC curve; probability of correct ranking of a random positive-negative pair.
- **Lift / gains chart**: concentration of positives in a top-scored group relative to the base rate / cumulative capture curve.
- **Precision-recall curve / average precision**: precision against recall / its summary.
- **Expected-value threshold**: the probability above which acting has positive expected payoff.
- **Rare class problem (imbalanced data)**: one class much rarer than the other.
- **Undersampling / oversampling**: dropping majority records / adding minority records.
- **SMOTE**: generating synthetic minority records by interpolating between neighbours.
- **Class weights (up-weighting)**: making minority errors cost more in training.
- **Prior correction**: adjusting probabilities from a resampled model back to the true base rate.
- **Log-loss / Brier score**: calibration-sensitive scores of predicted probabilities.

## Check yourself

```quiz
[
  {"q": "A fraud model with 2.6% positives has 97.4% accuracy at threshold 0.5 but catches 5 of 132 frauds. Its recall is about…", "options": ["0.04", "0.97", "0.63", "0.50"], "answer": 0,
   "explain": "Recall = TP/(TP + FN) = 5/132 ≈ 0.038."},
  {"q": "An AUC of 0.80 means…", "options": ["a randomly chosen positive gets a higher score than a randomly chosen negative 80% of the time", "80% of predictions are correct", "80% of positives are caught at threshold 0.5", "precision is 0.80"], "answer": 0,
   "explain": "AUC is a ranking probability, independent of any threshold."},
  {"q": "Catching a fraud saves \\$200 and a review costs \\$5. Above what fraud probability should you review?", "options": ["About 0.024", "0.5", "0.05", "0.20"], "answer": 0,
   "explain": "Threshold = 5 / (5 + 200) ≈ 0.0244."},
  {"q": "After undersampling negatives to a 50/50 mix, a logistic model's average predicted probability on real data is 0.38 while the true rate is 3%. What happened?", "options": ["Resampling shifted the intercept, so probabilities are no longer calibrated", "The model overfit", "AUC dropped", "The test set is wrong"], "answer": 0,
   "explain": "The model learned a 50% base rate; correct the probabilities or recalibrate."},
  {"q": "Which statement about class weighting and undersampling for logistic regression is typically true?", "options": ["They change calibration much more than ranking quality (AUC)", "They always raise AUC substantially", "They make accuracy the right metric", "They remove the need for a threshold"], "answer": 0,
   "explain": "In the demo all three models had identical AUC; only the probability level moved."},
  {"q": "The top 10% of scored customers contain 4.3 times the average rate of responders. This number is the…", "options": ["lift of the top decile", "AUC", "recall", "specificity"], "answer": 0,
   "explain": "Lift compares the response rate in a targeted group with the base rate."}
]
```

> **Source:** Bruce & Bruce, *Practical Statistics for Data Scientists* (O'Reilly, 2017), ch. 5, "Evaluating Classification Models" (confusion matrix, the rare class problem, precision, recall and specificity, ROC curve, AUC, lift) and "Strategies for Imbalanced Data" (undersample, oversample and up/down weighting, data generation, cost-based classification, exploring the predictions); scikit-learn documentation. Examples are original.
