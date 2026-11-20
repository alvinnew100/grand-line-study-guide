# Evaluation metrics and imbalanced data

So far we have scored classifiers with accuracy and regressors with $R^2$. Those are only two of many
ways to summarise performance, and they are often the wrong ones for the job. This lesson covers the
metrics from chapter 5 of Müller & Guido: the confusion matrix, precision, recall and F-scores,
precision–recall and ROC curves, multiclass averaging, regression metrics, and how to use any of them in
model selection.

## 1. Keep the end goal in mind

When choosing a metric, keep the **end goal of the application** in mind. We are rarely interested in
accurate predictions for their own sake. They feed a larger decision process. Before picking a metric,
think about the high-level goal, often called the **business metric**: fewer traffic accidents, fewer
hospital admissions, more revenue. The consequences of choosing an algorithm are its **business impact**.
Choose the model and parameters with the most positive influence on that metric.

This is often hard, because measuring business impact may require putting the model into production. In
early development it is usually infeasible to try models on real users, so we use evaluation procedures
that are easier to compute, as stand-ins. Pick the stand-in closest to the business goal.

## 2. Kinds of errors

Binary classification has a **positive** class (the thing we are looking for) and a **negative** class.
Consider screening for cancer with an automated test:

- A **false positive** (type I error) is a healthy patient flagged as possibly ill. The result is extra
  testing, cost and worry.
- A **false negative** (type II error) is a sick patient told they are healthy. The result is a missed
  diagnosis, possibly fatal.

The two errors rarely cost the same. In the cancer example, false negatives should be avoided as far as
possible, and false positives are a comparatively minor nuisance.

## 3. Why accuracy fails on imbalanced data

Datasets where one class is far more frequent than the other are called **imbalanced**. In practice they
are the norm: click-through prediction (most impressions are not clicked), fraud, rare diseases.

Suppose 99% of the data is "no click". A classifier that always predicts "no click" is 99% accurate and
entirely useless. Accuracy cannot tell a constant "no" from a potentially good model.

```python-run
import numpy as np
from sklearn.datasets import load_digits
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split

digits = load_digits()
y = (digits.target == 9).astype(int)                 # "nine" vs "not nine": a 9:1 imbalance
X_tr, X_te, y_tr, y_te = train_test_split(digits.data, y, random_state=0)
print("share of positives:", y.mean().round(3))
models = {
    "always 'not nine'": DummyClassifier(strategy="most_frequent"),
    "depth-2 tree": DecisionTreeClassifier(max_depth=2, random_state=0),
    "logistic regression": LogisticRegression(C=0.1, max_iter=5000),
}
for name, m in models.items():
    print(f"{name:20s} accuracy = {m.fit(X_tr, y_tr).score(X_te, y_te):.3f}")
```

The do-nothing classifier scores 90%, and the shallow tree only two points more. Accuracy barely
separates a useless model from a weak one. We need metrics that show the difference.

## 4. The confusion matrix

The most complete summary of a binary classifier is the **confusion matrix**. In scikit-learn, **rows are
true classes and columns are predicted classes**:

| | predicted negative | predicted positive |
|---|---|---|
| **actually negative** | TN (true negative) | FP (false positive) |
| **actually positive** | FN (false negative) | TP (true positive) |

Every summary metric is a formula over these four counts:

$$\text{accuracy} = \frac{TP+TN}{TP+TN+FP+FN}\qquad \text{precision} = \frac{TP}{TP+FP}\qquad \text{recall} = \frac{TP}{TP+FN}$$

- **Precision** (positive predictive value): of the samples predicted positive, how many really are? Use
  it when the goal is to **limit false positives**. An example is predicting whether a new drug will work
  in clinical trials, where a false positive starts a very expensive trial.
- **Recall** (sensitivity, hit rate, true positive rate): of the actual positives, how many did we find?
  Use it when it is important to **avoid false negatives**, as in cancer screening.

There is a **trade-off**. Predicting everything as positive gives perfect recall and terrible precision.
Predicting positive only for the single most certain sample gives perfect precision and terrible recall.

The **F1 score** combines them as a harmonic mean:

$$F_1 = 2\cdot\frac{\text{precision}\cdot\text{recall}}{\text{precision}+\text{recall}}$$

It takes both into account, so it can be a better measure than accuracy on imbalanced binary data. Its
drawback is that it is harder to interpret and explain than accuracy. The general form $F_\beta$ weights
recall $\beta$ times as much as precision.

```python-run
import numpy as np
from sklearn.datasets import load_digits
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import confusion_matrix, classification_report, f1_score

digits = load_digits()
y = (digits.target == 9).astype(int)
X_tr, X_te, y_tr, y_te = train_test_split(digits.data, y, random_state=0)
dummy = DummyClassifier(strategy="most_frequent").fit(X_tr, y_tr)
logreg = LogisticRegression(C=0.1, max_iter=5000).fit(X_tr, y_tr)

for name, m in [("always 'not nine'", dummy), ("logistic regression", logreg)]:
    pred = m.predict(X_te)
    print(name, "\n", confusion_matrix(y_te, pred), " f1 =", round(f1_score(y_te, pred, zero_division=0), 3))
print(classification_report(y_te, logreg.predict(X_te), target_names=["not nine", "nine"]))
```

`classification_report` prints precision, recall and F1 **for each class treated as the positive one**,
with the **support** (number of true samples) of each. The dummy classifier has an F1 of 0 for the "nine"
class, which exposes it at once.

## 5. Taking uncertainty into account: thresholds

Most classifiers produce a score through `decision_function` or `predict_proba`. A prediction comes from
thresholding it at a fixed point: 0 for the decision function, 0.5 for probabilities. **Changing the
threshold trades precision against recall.** If recall on the positive class matters more, lower the
threshold so that more points are classified as positive.

```python-run
import numpy as np
from sklearn.datasets import load_breast_cancer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.metrics import precision_score, recall_score

X, y = load_breast_cancer(return_X_y=True)
y = 1 - y                                           # make "malignant" the positive class
X_tr, X_te, y_tr, y_te = train_test_split(X, y, stratify=y, random_state=0)
proba = make_pipeline(StandardScaler(), LogisticRegression()).fit(X_tr, y_tr).predict_proba(X_te)[:, 1]
print("threshold  precision  recall  flagged")
for t in [0.9, 0.5, 0.2, 0.05]:
    pred = (proba >= t).astype(int)
    print(f"   {t:4.2f}     {precision_score(y_te, pred):.3f}    {recall_score(y_te, pred):.3f}   {pred.sum():4d}")
```

Two cautions from the book:

- **Do not set the threshold on the test set.** As with any other parameter, doing so gives optimistic
  results. Use a validation set or cross-validation.
- A threshold of 0.5 is meaningful only if the model is **calibrated**. A fully grown decision tree is
  always 100% certain, even when it is wrong.

## 6. Precision–recall curves

Setting a requirement such as "90% recall" is called setting the **operating point**. This is often a
business decision. When developing a new model the operating point may not be known yet. It is then
useful to look at **all possible thresholds** at once, which is the **precision–recall curve**. The
closer a curve stays to the top-right corner (high precision *and* high recall), the better.

Different classifiers can be good in different parts of the curve. The book compares an SVM and a random
forest: the forest is better at the extremes (very high recall or very high precision), and the SVM is
better in the middle. Comparing only the F1 at the default threshold would hide this.

To summarise the whole curve in one number, use the area under it, the **average precision** (AP).
It lies between 0 (worst) and 1 (best). A random classifier's AP equals the fraction of positives.

```python-run
import numpy as np
from sklearn.datasets import make_classification
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import precision_recall_curve, average_precision_score, f1_score

X, y = make_classification(n_samples=2000, weights=[0.9], flip_y=0.03, class_sep=1.5, n_informative=4, random_state=0)
X_tr, X_te, y_tr, y_te = train_test_split(X, y, stratify=y, random_state=0)
for name, m in [("logistic regression", LogisticRegression(max_iter=1000)),
                ("random forest", RandomForestClassifier(n_estimators=50, random_state=0))]:
    s = m.fit(X_tr, y_tr).predict_proba(X_te)[:, 1]
    precision, recall, thresholds = precision_recall_curve(y_te, s)
    i = np.argmin(np.abs(recall - 0.8))               # the operating point with recall closest to 0.8
    print(f"{name:20s} AP={average_precision_score(y_te, s):.3f}  F1@0.5={f1_score(y_te, s >= 0.5):.3f}  "
          f"precision at recall 0.8 = {precision[i]:.3f}")
```

## 7. ROC curves and AUC

The **receiver operating characteristic (ROC) curve** also considers all thresholds, but plots the **true
positive rate** against the **false positive rate**:

$$TPR = \text{recall} = \frac{TP}{TP+FN}\qquad\qquad FPR = \frac{FP}{FP+TN}$$

The ideal curve hugs the **top-left** corner: high recall with a low false positive rate. The diagonal is
random guessing.

The area under it is the **AUC** (`roc_auc_score`). It can be read as **the probability that a randomly
chosen positive example gets a higher score than a randomly chosen negative one**. So:

- a random classifier has AUC 0.5 **whatever the class balance**, which makes AUC a far better metric
  than accuracy for imbalanced problems;
- a perfect ranking has AUC 1.0;
- AUC measures *ranking* quality only. It ignores the threshold and the calibration of the probabilities.

The book's experiment: SVMs with three values of `gamma` on the nine-vs-rest digits all get **the same
accuracy, 90%**, because they predict the majority class almost everywhere. Their AUCs are 0.5, about
0.95 and 1.0. With `gamma=0.01` every positive is ranked above every negative. The model is perfect as a
ranker, and only the **threshold** needs adjusting. Accuracy alone would never have shown this.

```python-run
from sklearn.datasets import load_digits
from sklearn.svm import SVC
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, average_precision_score

digits = load_digits()
y = (digits.target == 9).astype(int)
X_tr, X_te, y_tr, y_te = train_test_split(digits.data, y, random_state=0)
for gamma in [1, 0.05, 0.01]:
    svc = SVC(gamma=gamma).fit(X_tr, y_tr)
    scores = svc.decision_function(X_te)
    print(f"gamma={gamma:<5} accuracy={svc.score(X_te, y_te):.2f}  AUC={roc_auc_score(y_te, scores):.2f}  AP={average_precision_score(y_te, scores):.2f}")
```

> [!INTERVIEW]
> **"ROC AUC or PR AUC?"** Both summarise ranking over all thresholds. ROC uses the FPR, whose denominator
> is the number of negatives. With extreme imbalance a model can produce many false positives while the
> FPR stays tiny, so ROC AUC looks excellent. Precision exposes the problem directly. When positives are
> rare and you care about the quality of what you flag (fraud, search, alerts), use the **PR curve / average
> precision**. Use ROC AUC when both classes matter or to compare rankers across datasets with different
> class balance.

## 8. Metrics for multiclass classification

Multiclass metrics are derived from binary ones, averaged over the classes. Accuracy is again the
fraction correct, and again misleading under imbalance. The confusion matrix is $C\times C$ and shows
*which* classes get confused. For the F-score, compute a binary F1 per class (that class vs the rest) and
then average:

| average | how | use when |
|---|---|---|
| `macro` | unweighted mean of the per-class scores | you care about **each class equally**, whatever its size |
| `weighted` | mean weighted by each class's support | the default in the classification report |
| `micro` | pool all TP, FP, FN over classes, then compute | you care about **each sample equally** |

```python-run
from sklearn.datasets import load_digits
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import confusion_matrix, f1_score, accuracy_score

digits = load_digits()
X_tr, X_te, y_tr, y_te = train_test_split(digits.data, digits.target, random_state=0)
pred = LogisticRegression(max_iter=5000).fit(X_tr, y_tr).predict(X_te)
print("accuracy:", round(accuracy_score(y_te, pred), 3))
print(confusion_matrix(y_te, pred))
print("micro F1:", round(f1_score(y_te, pred, average="micro"), 3), " macro F1:", round(f1_score(y_te, pred, average="macro"), 3))
```

For single-label multiclass problems, micro-averaged F1 equals accuracy.

## 9. Regression metrics

The book's view is that the default **$R^2$** of `score` is enough for most applications, since it is the
most intuitive. Business decisions are sometimes made on other measures:

| metric | formula | notes |
|---|---|---|
| MSE | $\frac1n\sum(y-\hat y)^2$ | penalises large errors heavily; in squared units |
| RMSE | $\sqrt{\text{MSE}}$ | in the units of the target |
| MAE | $\frac1n\sum\lvert y-\hat y\rvert$ | robust to outliers; corresponds to predicting the median |
| $R^2$ | $1 - \frac{SS_{res}}{SS_{tot}}$ | 1 is perfect, 0 is "predict the mean", can be negative |
| MAPE | $\frac1n\sum\lvert\frac{y-\hat y}{y}\rvert$ | relative error; breaks down near $y=0$ |

```python-run
import numpy as np
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
y_true = np.array([3.0, 5.0, 2.5, 7.0, 4.0])
y_pred = np.array([2.5, 5.0, 3.0, 8.0, 4.5])
print("MSE :", mean_squared_error(y_true, y_pred), " RMSE:", round(float(np.sqrt(mean_squared_error(y_true, y_pred))), 3))
print("MAE :", mean_absolute_error(y_true, y_pred), " R2:", round(r2_score(y_true, y_pred), 3))
y_out = y_pred.copy(); y_out[0] = 13.0                      # one very bad prediction
print("with one outlier error -> RMSE:", round(float(np.sqrt(mean_squared_error(y_true, y_out))), 2), " MAE:", mean_absolute_error(y_true, y_out))
```

## 10. Using metrics in model selection

`cross_val_score` and `GridSearchCV` take a **`scoring`** argument: `"accuracy"`, `"roc_auc"`,
`"average_precision"`, `"f1"`, `"f1_macro"`, `"recall"`, `"r2"`, `"neg_mean_squared_error"`,
`"neg_mean_absolute_error"` and more. Errors are **negated** so that higher is always better. The metric
you optimise changes which model is chosen.

```python-run
from sklearn.datasets import load_digits
from sklearn.svm import SVC
from sklearn.model_selection import GridSearchCV, train_test_split
digits = load_digits()
y = (digits.target == 9).astype(int)
X_tr, X_te, y_tr, y_te = train_test_split(digits.data, y, random_state=0)
for scoring in ["accuracy", "roc_auc"]:
    grid = GridSearchCV(SVC(), {"gamma": [0.0001, 0.01, 0.1, 1, 10]}, scoring=scoring, cv=3).fit(X_tr, y_tr)
    print(f"scoring={scoring:9s} -> best gamma={grid.best_params_['gamma']}  CV score={grid.best_score_:.3f}")
```

## 11. Handling imbalanced data

Options, roughly in the order to try them:

1. **Use the right metric** (PR AUC, recall at a fixed precision) and **stratified** splits.
2. **Move the decision threshold** to the operating point you need.
3. **Class weights**: `class_weight="balanced"` reweights the loss so that minority errors cost more.
4. **Resampling**: undersample the majority or oversample the minority (random, or SMOTE in
   `imbalanced-learn`). Apply it to the *training folds only*, never to validation or test data.
5. Collect more positives, or treat the task as anomaly detection when positives are extremely rare.

```python-run
from sklearn.datasets import make_classification
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import precision_score, recall_score
X, y = make_classification(n_samples=4000, weights=[0.97], class_sep=0.9, random_state=1)
X_tr, X_te, y_tr, y_te = train_test_split(X, y, stratify=y, random_state=0)
for cw in [None, "balanced"]:
    pred = LogisticRegression(class_weight=cw, max_iter=1000).fit(X_tr, y_tr).predict(X_te)
    print(f"class_weight={str(cw):9s} precision={precision_score(y_te, pred):.2f}  recall={recall_score(y_te, pred):.2f}")
```

## Summary

- Choose metrics from the business goal and the relative cost of false positives and false negatives.
- Accuracy is misleading on imbalanced data. Read the confusion matrix.
- Precision = TP/(TP+FP), recall = TP/(TP+FN), and F1 is their harmonic mean.
- Thresholds trade precision for recall. PR curves and ROC curves show every threshold. AP and AUC
  summarise them.
- AUC is the probability that a random positive outranks a random negative. 0.5 is chance at any class
  balance.
- Pass `scoring=` to cross-validation and grid search so that you optimise what matters.

```quiz
[
  {"q": "A classifier flags 100 transactions as fraud; 30 really are. There are 60 frauds in total. Precision and recall are…", "options": ["precision 0.30, recall 0.50", "precision 0.50, recall 0.30", "precision 0.30, recall 0.30", "precision 0.60, recall 0.30"], "answer": 0,
   "explain": "Precision = TP/predicted positive = 30/100; recall = TP/actual positive = 30/60."},
  {"q": "On a dataset with 99% negatives, a model that always predicts negative has…", "options": ["99% accuracy and 0 recall", "50% accuracy", "99% recall", "an AUC of 0.99"], "answer": 0,
   "explain": "It never finds a positive. Its constant scores give an AUC of 0.5."},
  {"q": "In scikit-learn's confusion_matrix, entry [1, 0] of a binary matrix is the number of…", "options": ["false negatives", "false positives", "true positives", "true negatives"], "answer": 0,
   "explain": "Rows are true classes and columns predicted classes: true 1, predicted 0."},
  {"q": "Lowering the decision threshold of a classifier generally…", "options": ["increases recall and decreases precision", "increases precision and decreases recall", "increases both", "changes neither"], "answer": 0,
   "explain": "More samples are labelled positive: more true positives are caught, but more false positives too."},
  {"q": "ROC AUC can be interpreted as…", "options": ["the probability that a random positive is scored higher than a random negative", "the accuracy at the best threshold", "the fraction of positives in the data", "the area under the precision–recall curve"], "answer": 0,
   "explain": "It measures ranking quality, independent of any threshold."},
  {"q": "Three SVMs all have 90% accuracy on a 9:1 dataset but AUCs of 0.5, 0.95 and 1.0. What does AUC = 1.0 tell you?", "options": ["The scores rank every positive above every negative; only the threshold is poorly set", "The model is overfitted and useless", "Accuracy was computed wrongly", "The data is balanced"], "answer": 0,
   "explain": "A perfect ranking with a badly placed default threshold still predicts the majority class everywhere."},
  {"q": "Macro-averaged F1 is the right choice when…", "options": ["every class should count equally, regardless of how many samples it has", "large classes should dominate", "you want a number equal to accuracy", "there is only one class"], "answer": 0,
   "explain": "Macro averaging takes an unweighted mean of per-class F1 scores."},
  {"q": "Why is the scorer called 'neg_mean_squared_error'?", "options": ["scikit-learn's model selection always maximises, so errors are negated", "MSE can be negative", "It subtracts the mean first", "It is a typo kept for compatibility"], "answer": 0,
   "explain": "Higher must mean better for every scorer, so losses are multiplied by −1."}
]
```

> **Source:** Müller & Guido, *Introduction to Machine Learning with Python*, ch. 5 ("Evaluation Metrics and Scoring": keep the end goal in mind, metrics for binary classification, kinds of errors, imbalanced datasets, confusion matrices, taking uncertainty into account, precision-recall curves and ROC curves, metrics for multiclass classification, regression metrics, using evaluation metrics in model selection); scikit-learn User Guide, "Metrics and scoring".
