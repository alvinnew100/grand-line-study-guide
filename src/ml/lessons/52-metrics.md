# Evaluation metrics and imbalanced data

> **Before this lesson:** you need [Cross-validation](#/lesson/ml/cross-validation) and [Grid search and nested cross-validation](#/lesson/ml/grid-search), since metrics are what those procedures compute. Classifiers' scores from `predict_proba` and `decision_function` were introduced in [Kernel SVMs, neural networks and uncertainty](#/lesson/ml/svm-mlp-uncertainty) and are re-explained below; $R^2$ comes from [Generalisation, overfitting and k-NN](#/lesson/ml/generalization-knn).

## In plain words

A **metric** is the number you use to say how good a model is. So far we have used accuracy for classifiers and $R^2$ for regressors. Both can be badly misleading. This lesson shows the measures professionals actually use, and how to choose among them based on what a mistake costs.

An everyday picture: a smoke alarm. An alarm that never sounds is "right" on almost every day of the year, because there is almost never a fire, so its accuracy is superb and it is useless. An alarm that sounds whenever you make toast catches every fire and drives you mad. To judge an alarm you need two separate questions: when there is a fire, does it go off? And when it goes off, is there a fire? Those two questions are called recall and precision, and they are the heart of this lesson.

Why this matters for a job: fraud detection, medical screening, spam filtering, search and recommendation all involve rare events, where accuracy is close to meaningless. Interviewers ask you to compute precision and recall from a small table, to explain ROC AUC, and to say which metric fits a business problem. Choosing the wrong metric is one of the most common ways to build a model that scores well and helps nobody.

## 1. Keep the end goal in mind

A model's predictions are rarely the goal in themselves; they feed a decision. A fraud model decides which payments to block; a medical model decides who gets a follow-up scan. Before choosing a metric, name the high-level goal, often called the **business metric**: fewer fraudulent payments, fewer missed diagnoses, more revenue. The effect a model has on that goal is its **business impact**, and ideally you would choose the model with the best impact.

Measuring business impact directly usually requires putting a model in front of real users, which is impossible for every candidate during development. So we use metrics that can be computed offline as stand-ins. The skill is to pick the stand-in that best matches the real goal.

## 2. Kinds of errors

In **binary classification** (two classes) one class is called **positive**: the thing we are looking for, such as "has cancer" or "is fraud". The other is **negative**. "Positive" does not mean good; it means "the condition is present".

Take an automated cancer screening test. It can be wrong in two different ways:

- A **false positive** (also called a type I error) is a healthy patient flagged as possibly ill. The cost: extra tests, money and worry.
- A **false negative** (a type II error) is an ill patient told they are healthy. The cost: a missed diagnosis, possibly fatal.

The two errors rarely cost the same. Here false negatives must be avoided as far as possible, while false positives are a comparatively minor nuisance. In a spam filter it is the other way round: losing a real email in the spam folder (a false positive) is worse than letting one spam message through.

## 3. Why accuracy fails on imbalanced data

A dataset is **imbalanced** when one class is far more frequent than the other. In practice imbalance is the norm: most ads are not clicked, most payments are not fraud, most patients do not have a rare disease.

Suppose 99% of ad impressions are not clicked. A "model" that always predicts "no click" is 99% accurate and completely useless. Accuracy cannot tell a constant "no" apart from a genuinely good model.

The demo below makes an imbalanced task from the digits dataset (8×8 pixel images of handwritten digits): is this digit a 9 or not? About one image in ten is a 9.

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

**Reading this code line by line**

- `digits.target == 9` gives `True` for nines and `False` otherwise; `.astype(int)` turns that into 1 and 0. So the positive class is "nine".
- `y.mean()` is the share of 1s: 0.1, one in ten.
- The dictionary `models` holds three classifiers: a `DummyClassifier` that always predicts the most common class, a decision tree allowed only two levels of questions, and a logistic regression. The loop fits each one and prints its test accuracy.

The do-nothing classifier scores 0.896, the shallow tree 0.918 and logistic regression 0.984. Accuracy puts the useless model only two points behind the tree. We need measures that show the real difference.

## 4. The confusion matrix

The most complete summary of a binary classifier's predictions is the **confusion matrix**: a 2×2 table counting every combination of true class and predicted class. In scikit-learn the **rows are the true classes and the columns are the predicted classes**:

| | predicted negative | predicted positive |
|---|---|---|
| **actually negative** | TN (true negative) | FP (false positive) |
| **actually positive** | FN (false negative) | TP (true positive) |

"True" or "false" says whether the prediction was right; "positive" or "negative" says what was predicted. Every metric in this lesson is a formula built from these four counts.

**Accuracy** is the share of all predictions that are right. **Precision** asks: of everything the model flagged as positive, what share really is positive? **Recall** asks: of everything that really is positive, what share did the model flag?

$$\text{accuracy} = \frac{TP+TN}{TP+TN+FP+FN}\qquad \text{precision} = \frac{TP}{TP+FP}\qquad \text{recall} = \frac{TP}{TP+FN}$$

A worked example. A fraud model flags 100 payments; 30 of them really are fraud. There were 60 frauds in total among 1,000 payments. So TP = 30, FP = 70, FN = 30, and TN = 1000 − 30 − 70 − 30 = 870. Precision is $30/100 = 0.30$; recall is $30/60 = 0.50$; accuracy is $(30 + 870)/1000 = 0.90$. The 90% accuracy hides that most flags are wrong and half the frauds are missed.

- **Precision** is also called positive predictive value. Use it when the goal is to **limit false positives**: for example, when each positive prediction triggers something expensive, such as starting a clinical trial for a drug predicted to work.
- **Recall** is also called sensitivity, hit rate or **true positive rate**. Use it when it is important to **avoid false negatives**, as in cancer screening.

There is a **trade-off** between them. Predicting every sample as positive gives perfect recall (nothing is missed) and terrible precision. Predicting positive only for the single case the model is most sure of gives (probably) perfect precision and terrible recall.

### The F1 score

The **F1 score** combines precision and recall into one number using the **harmonic mean**, a kind of average that is pulled strongly towards the smaller of the two values:

$$F_1 = 2\cdot\frac{\text{precision}\cdot\text{recall}}{\text{precision}+\text{recall}}$$

Why not the ordinary average? Take a model with precision 1.0 and recall 0.1. The ordinary average is 0.55, which sounds respectable for a model that misses 90% of cases. The harmonic mean gives $2 \times 1.0 \times 0.1 / 1.1 = 0.18$. F1 is only high when *both* are high. For the fraud example above, $F_1 = 2 \times 0.3 \times 0.5 / 0.8 = 0.375$.

F1 takes both kinds of error into account, which makes it more informative than accuracy on imbalanced data. Its drawback is that it is harder to explain to non-specialists. The general form $F_\beta = (1+\beta^2)\,\frac{P \cdot R}{\beta^2 P + R}$, with $P$ the precision and $R$ the recall, treats recall as $\beta$ times as important as precision: $F_2$ favours recall, $F_{0.5}$ favours precision.

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

**Reading this code line by line**

- `confusion_matrix(y_te, pred)` takes the true labels first and the predictions second and returns the 2×2 table of counts.
- `f1_score(..., zero_division=0)` computes F1. The dummy model never predicts a positive, so its precision would be $0/0$; `zero_division=0` says to count that as 0 instead of printing a warning.
- `classification_report` prints precision, recall and F1 for each class, treating each in turn as the positive one.

The dummy's matrix is `[[403 0] [47 0]]`: all 403 non-nines right, all 47 nines missed, F1 = 0. One number exposes it at once. Logistic regression's matrix is `[[402 1] [6 41]]`. Working it through: precision $= 41/(41+1) = 0.976$, recall $= 41/(41+6) = 0.872$, and $F_1 = 2 \times 0.976 \times 0.872/(0.976 + 0.872) = 0.921$, matching the printout.

In the report, the "nine" row shows precision 0.98, recall 0.87 and F1 0.92; the **support** column is the number of true samples of each class (403 and 47). The "macro avg" and "weighted avg" rows are explained in section 8.

## 5. Taking uncertainty into account: thresholds

Most classifiers do not produce a yes/no answer directly. They compute a score: `predict_proba` gives an estimated probability of each class, and `decision_function` gives an unbounded score where larger means "more positive". The yes/no prediction comes from comparing that score with a **threshold**: by default 0.5 for probabilities and 0 for decision functions.

**Changing the threshold trades precision against recall.** A lower threshold flags more samples as positive: more true positives are caught (recall rises), but more false positives slip in (precision falls). If missing positives is expensive, lower the threshold.

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

**Reading this code line by line**

- In this dataset 0 means malignant, so `y = 1 - y` flips the labels to make "malignant" the positive class, the one we are hunting for.
- `predict_proba(X_te)` returns one row per tumour with two probabilities (benign, malignant); `[:, 1]` keeps the malignant column.
- For each threshold `t`, `(proba >= t)` flags every tumour whose probability reaches it, and the line prints precision, recall and how many were flagged.

At threshold 0.9, 47 tumours are flagged, all correctly (precision 1.000), but recall is 0.887: some malignant tumours are missed. Moving the threshold down to 0.05 flags 68, catches every malignant tumour (recall 1.000), and precision falls to 0.779. For screening, the low threshold is probably the right one.

Two cautions:

- **Do not choose the threshold on the test set.** The threshold is a setting like any hyperparameter, and choosing it on test data gives optimistic results. Use a validation set or cross-validation.
- A threshold of 0.5 only means "more likely than not" if the model is **calibrated**: its stated probabilities match how often it is right (of all cases given 0.8, about 80% really are positive). Many models are not. A fully grown decision tree, for instance, reports 100% certainty for every prediction, even the wrong ones.

## 6. Precision–recall curves

Choosing a requirement such as "we need 90% recall" fixes an **operating point**: a specific threshold with a specific precision and recall. That is often a business decision. While developing a model the operating point may not be known yet, so it helps to look at **all thresholds at once**. Sweeping the threshold from high to low and plotting precision against recall at each value gives the **precision–recall curve**. The closer the curve stays to the top-right corner (high precision *and* high recall), the better the model.

Different models can be better in different parts of the curve. The book compares a support vector machine and a random forest on the same data: the forest is better at the extremes (very high recall or very high precision) and the SVM in the middle. Comparing only F1 at the default threshold would hide this.

To summarise the whole curve in one number, use **average precision** (AP), which is close to the area under the curve. In words, it walks down the ranked predictions and averages the precision at each point where recall increases, weighting each by how much recall went up:

$$AP = \sum_n (R_n - R_{n-1})\,P_n$$

where $P_n$ and $R_n$ are precision and recall at the $n$-th threshold. AP lies between 0 and 1. A model that ranks at random has an AP about equal to the fraction of positives, so on data with 10% positives a "random" AP is 0.1, not 0.5.

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

**Reading this code line by line**

- `make_classification(...)` generates an artificial two-class problem: `weights=[0.9]` makes 90% of samples negative, `flip_y=0.03` flips 3% of labels at random as noise, and `class_sep` and `n_informative` control how hard it is.
- For each model, `s` holds the predicted probability of the positive class for every test sample.
- `precision_recall_curve(y_te, s)` tries every distinct score as a threshold and returns arrays of precision and recall (and the thresholds).
- `np.argmin(np.abs(recall - 0.8))` finds the position where recall is closest to 0.8, so we can read the precision at that operating point.

The forest wins clearly on every summary: AP 0.816 against 0.502, F1 at the default threshold 0.729 against 0.261, and at 80% recall the forest's flags are right 58% of the time while logistic regression's are right only 16% of the time. This generated data has curved class boundaries that a straight-line model cannot follow.

## 7. ROC curves and AUC

The **receiver operating characteristic (ROC) curve** also sweeps over all thresholds, but plots two different rates. The **true positive rate** (TPR) is recall: the share of positives that are flagged. The **false positive rate** (FPR) is the share of negatives that are wrongly flagged:

$$TPR = \text{recall} = \frac{TP}{TP+FN}\qquad\qquad FPR = \frac{FP}{FP+TN}$$

The ideal curve rises straight up the left edge and then runs along the top (high recall with almost no false positives), so a good curve hugs the **top-left** corner. A model that ranks at random produces the diagonal line from bottom-left to top-right.

The area under the ROC curve is called the **AUC** (area under the curve), computed by `roc_auc_score`. It has a very useful meaning: **AUC is the probability that a randomly chosen positive example gets a higher score than a randomly chosen negative one.**

A worked example. Two positives get scores 0.9 and 0.4; three negatives get 0.7, 0.3 and 0.2. There are $2 \times 3 = 6$ positive–negative pairs. The positive at 0.9 beats all three negatives (3 pairs). The positive at 0.4 beats 0.3 and 0.2 but not 0.7 (2 pairs). So 5 of the 6 pairs are ranked correctly and AUC $= 5/6 \approx 0.833$. Computing it from the curve gives the same answer:

```python-run
import numpy as np
from sklearn.metrics import roc_auc_score, roc_curve
y = np.array([1, 1, 0, 0, 0])
s = np.array([0.9, 0.4, 0.7, 0.3, 0.2])
fpr, tpr, th = roc_curve(y, s)
print("thresholds:", th, "\nFPR:", fpr.round(2), "\nTPR:", tpr)
print("AUC:", round(roc_auc_score(y, s), 3))
pos, neg = s[y == 1], s[y == 0]
print("share of positive-negative pairs ranked correctly:", round((pos[:, None] > neg[None, :]).mean(), 3))
```

`roc_curve` returns the false and true positive rates at each threshold. Reading the printout: at threshold 0.9 one positive is flagged (TPR 0.5, FPR 0); at 0.7 a negative is added (FPR 0.33); at 0.4 the second positive (TPR 1.0); at 0.2 everything is flagged. (The first threshold, `inf`, flags nothing and starts the curve at the origin.) The last line counts pairs directly: `pos[:, None] > neg[None, :]` compares every positive with every negative in a 2×3 table of True/False, and `.mean()` gives the share of True, 0.833.

Consequences of the pairwise meaning:

- A model that ranks at random has AUC 0.5 **whatever the class balance**. That makes AUC far more informative than accuracy on imbalanced problems.
- A perfect ranking (every positive above every negative) has AUC 1.0.
- AUC measures only **ranking** quality. It ignores where the threshold is set and whether the probabilities are calibrated.

The last point leads to a striking experiment from the book: support vector machines with three values of `gamma` on the nine-versus-rest digits task. All three have **the same accuracy, 90%**, because at the default threshold they predict "not nine" almost everywhere. Their AUCs in the book are 0.50, 0.90 and 1.00. With `gamma=0.01` every nine is ranked above every non-nine: the model is a perfect ranker, and only its threshold is badly placed. Accuracy alone would never reveal this.

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

Here the scores come from `decision_function`, since AUC and AP only need a ranking. In this run (current scikit-learn) the AUCs come out as 0.50, 1.00 and 1.00, with average precision 0.10, 0.99 and 1.00, while accuracy stays at 0.90 for all three. The `gamma=1` model gives essentially the same score to every image, so its ranking is random: AUC 0.5 and AP equal to the 10% share of nines.

> [!INTERVIEW]
> **"ROC AUC or PR AUC?"** Both summarise ranking over all thresholds. ROC uses the false positive rate, whose denominator is the number of negatives. With extreme imbalance, say a million negatives, a model can produce thousands of false positives while the FPR stays tiny, so ROC AUC still looks excellent. Precision exposes that problem directly. When positives are rare and you care about the quality of what you flag (fraud, search results, alerts), use the **precision–recall curve and average precision**. Use ROC AUC when both classes matter or to compare rankers across datasets with different class balance.

## 8. Metrics for multiclass classification

Metrics for more than two classes are built from the binary ones. Accuracy is again the fraction of correct predictions, and is again misleading when classes are imbalanced. The confusion matrix becomes a $C \times C$ table for $C$ classes and shows *which* classes get mistaken for which. For precision, recall and F1, compute a binary score for each class (that class against all the others) and then average the per-class scores. There are three ways to average:

| average | how | use when |
|---|---|---|
| `macro` | plain mean of the per-class scores | **each class** should count equally, whatever its size |
| `weighted` | mean weighted by each class's support | the default summary in the classification report |
| `micro` | add up TP, FP and FN over all classes first, then compute one score | **each sample** should count equally |

A worked example: three classes with F1 scores 0.9, 0.8 and 0.2 and supports 80, 15 and 5. The macro average is $(0.9 + 0.8 + 0.2)/3 = 0.63$; the weighted average is $(0.9 \times 80 + 0.8 \times 15 + 0.2 \times 5)/100 = 0.85$. The macro score reveals the failing small class; the weighted score hides it.

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

This time all ten digits are classes. In the 10×10 confusion matrix row $i$, column $j$ counts the images of digit $i$ predicted as digit $j$; the diagonal holds the correct predictions. The off-diagonal entries show the typical confusions: for example three 2s predicted as 3, and three 8s predicted as 1. Accuracy is 0.953, micro F1 is also 0.953, and macro F1 is 0.954.

Micro F1 equals accuracy whenever each sample has exactly one label: every wrong prediction is one false positive (for the predicted class) and one false negative (for the true class), so pooled precision and pooled recall are both "correct predictions divided by all predictions".

## 9. Regression metrics

For regression the book's view is that $R^2$, the default of `score`, is enough for most purposes and the easiest to interpret. Business decisions are sometimes made on other measures, which you should know:

| metric | formula | notes |
|---|---|---|
| MSE (mean squared error) | $\frac1n\sum(y-\hat y)^2$ | penalises large errors heavily; in squared units |
| RMSE (root mean squared error) | $\sqrt{\text{MSE}}$ | in the units of the target |
| MAE (mean absolute error) | $\frac1n\sum\lvert y-\hat y\rvert$ | less sensitive to outliers; minimised by predicting the median |
| $R^2$ | $1 - \frac{SS_{res}}{SS_{tot}}$ | 1 is perfect, 0 is "predict the mean", can be negative |
| MAPE (mean absolute percentage error) | $\frac1n\sum\lvert\frac{y-\hat y}{y}\rvert$ | relative error; breaks down when $y$ is near 0 |

Here $y$ is a true value, $\hat y$ the prediction, $SS_{res}$ the sum of squared errors and $SS_{tot}$ the sum of squared differences from the mean of $y$.

A worked example with five true values $3, 5, 2.5, 7, 4$ and predictions $2.5, 5, 3, 8, 4.5$. The errors are $0.5, 0, -0.5, -1, -0.5$. Squared: $0.25, 0, 0.25, 1, 0.25$, summing to 1.75, so MSE $= 1.75/5 = 0.35$ and RMSE $= \sqrt{0.35} = 0.592$. The absolute errors sum to 2.5, so MAE $= 0.5$. The mean of the true values is 4.3; the squared differences from it sum to 12.8, so $R^2 = 1 - 1.75/12.8 = 0.863$.

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

The first two lines of output repeat the hand calculation. The third line replaces the first prediction with 13 (an error of 10): RMSE jumps from 0.59 to 4.51, nearly eight times larger, while MAE goes from 0.5 to 2.4. Squaring makes one large error dominate. Choose RMSE when large errors are disproportionately bad, MAE when every unit of error costs the same.

## 10. Using metrics in model selection

`cross_val_score`, `cross_validate` and `GridSearchCV` all take a **`scoring`** argument naming the metric to compute: `"accuracy"`, `"roc_auc"`, `"average_precision"`, `"f1"`, `"f1_macro"`, `"recall"`, `"r2"`, `"neg_mean_squared_error"`, `"neg_mean_absolute_error"` and more. Error measures are **negated** (multiplied by −1), because model selection always picks the highest score, and for an error lower is better. The metric you optimise changes which model wins:

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

The same grid search, run twice with different `scoring`, picks `gamma=0.0001` when optimising accuracy and `gamma=0.01` when optimising AUC. The two metrics reward different things: accuracy rewards correct yes/no answers at the default threshold, AUC rewards the best ranking. Decide which matters for your application before you search.

## 11. Handling imbalanced data

Options, roughly in the order to try them:

1. **Use a suitable metric** (average precision, recall at a fixed precision, F1) and **stratified** splits.
2. **Move the decision threshold** to the operating point you need.
3. **Class weights**: `class_weight="balanced"` makes errors on the rare class count more during training, in proportion to how rare it is.
4. **Resampling**: **undersample** the majority class (drop some of its rows) or **oversample** the minority (repeat rows, or create synthetic ones with SMOTE from the `imbalanced-learn` library). Apply resampling to the *training folds only*, never to validation or test data, or the evaluation no longer reflects real data.
5. Collect more positives, or, when positives are extremely rare, treat the task as anomaly detection.

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

The data has 3% positives. Without weights the model is cautious: precision 1.00, recall 0.53, so it misses almost half the positives. With `class_weight="balanced"` recall rises to 0.62 and precision drops to 0.28. Neither is "correct"; class weighting moves the model along the same trade-off as lowering the threshold, and the business costs decide which point is right.

## Summary

- Choose metrics from the business goal and from the relative cost of false positives and false negatives.
- Accuracy is misleading on imbalanced data. Read the confusion matrix.
- Precision = TP/(TP+FP), recall = TP/(TP+FN), and F1 is their harmonic mean.
- The threshold trades precision for recall. Precision–recall and ROC curves show every threshold; average precision and AUC summarise them.
- AUC is the probability that a random positive outranks a random negative; 0.5 is chance at any class balance. With rare positives, prefer average precision.
- Macro averaging treats every class equally; micro averaging treats every sample equally.
- Pass `scoring=` to cross-validation and grid search so that you optimise what matters.

## Glossary

- **Metric**: a number summarising how well a model performs.
- **Business metric**: the real-world goal the model serves, such as revenue or missed diagnoses.
- **Positive / negative class**: the condition being looked for / its absence.
- **False positive (type I error)**: a negative case predicted as positive.
- **False negative (type II error)**: a positive case predicted as negative.
- **Imbalanced data**: one class far more frequent than another.
- **Confusion matrix**: a table counting true classes against predicted classes.
- **Precision**: of the predicted positives, the share that are truly positive.
- **Recall (sensitivity, true positive rate)**: of the true positives, the share that are predicted positive.
- **Harmonic mean / F1**: an average pulled towards the smaller value / the harmonic mean of precision and recall.
- **Support**: the number of true samples of a class.
- **Threshold**: the score above which a sample is predicted positive.
- **Calibrated**: describes probabilities that match observed frequencies.
- **Operating point**: a chosen threshold with its precision and recall.
- **Precision–recall curve / average precision**: precision against recall over all thresholds / a one-number summary of it.
- **False positive rate**: the share of negatives wrongly flagged.
- **ROC curve / AUC**: true positive rate against false positive rate over all thresholds / the area under it.
- **Macro / weighted / micro average**: equal weight per class / weight by support / pool counts over classes.
- **MSE, RMSE, MAE, MAPE**: mean squared error, its square root, mean absolute error, mean absolute percentage error.
- **Class weights / resampling**: making rare-class errors cost more / changing the class mix of the training data.

## Check yourself

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
  {"q": "Three SVMs all have 90% accuracy on a 9:1 dataset but AUCs of 0.5, 0.9 and 1.0. What does AUC = 1.0 tell you?", "options": ["The scores rank every positive above every negative; only the threshold is poorly set", "The model is overfitted and useless", "Accuracy was computed wrongly", "The data is balanced"], "answer": 0,
   "explain": "A perfect ranking with a badly placed default threshold still predicts the majority class everywhere."},
  {"q": "Macro-averaged F1 is the right choice when…", "options": ["every class should count equally, regardless of how many samples it has", "large classes should dominate", "you want a number equal to accuracy", "there is only one class"], "answer": 0,
   "explain": "Macro averaging takes an unweighted mean of per-class F1 scores."},
  {"q": "Why is the scorer called 'neg_mean_squared_error'?", "options": ["scikit-learn's model selection always maximises, so errors are negated", "MSE can be negative", "It subtracts the mean first", "It is a typo kept for compatibility"], "answer": 0,
   "explain": "Higher must mean better for every scorer, so losses are multiplied by −1."}
]
```

> **Source:** Müller & Guido, *Introduction to Machine Learning with Python*, ch. 5 ("Evaluation Metrics and Scoring": keep the end goal in mind, metrics for binary classification, kinds of errors, imbalanced datasets, confusion matrices, taking uncertainty into account, precision-recall curves and ROC curves, metrics for multiclass classification, regression metrics, using evaluation metrics in model selection); scikit-learn User Guide, "Metrics and scoring".
