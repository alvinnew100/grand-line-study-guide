# Rare positives: precision, recall, F1 and balanced sampling

> **Before this lesson:** read [A training application](#/lesson/deep-learning/training-application), whose first nodule classifier scored 99.7% while finding no nodules. You need cross-entropy options from [A first image classifier](#/lesson/deep-learning/image-classifier) and samplers from [Dataset, transforms and DataLoader](#/lesson/deep-learning/datasets-dataloaders). The general treatment of classification metrics is in the ML track's [Evaluation metrics and imbalanced data](#/lesson/ml/metrics); this lesson applies it to deep learning training.

## In plain words

When one class is very rare, two things go wrong at once. **Measurement** breaks: accuracy rewards ignoring the rare class. **Learning** breaks: the rare class contributes so little to the average loss that the model learns to ignore it. This lesson fixes both.

For measurement we count the two kinds of mistakes separately. A **false positive** is a false alarm (the model says "nodule" and it is not); a **false negative** is a miss (a real nodule the model ignored). **Recall** asks "of the real positives, how many did we find?"; **precision** asks "of the things we flagged, how many were real?". **F1** combines them into one number that is only high when both are.

For learning we change what the model sees: show it positives more often (**oversampling** or a **weighted sampler**), or make each positive count more in the loss (**class weights**).

Think of a smoke alarm. A very sensitive alarm (high recall) never misses a fire but goes off whenever you make toast (low precision). A lazy alarm (high precision) only rings for real fires but sleeps through a smouldering one (low recall). Both properties matter, and the right balance depends on what a miss and a false alarm each cost.

Why it matters for a job: fraud, defects, rare diseases, ad clicks, abuse detection and security alerts are all rare-positive problems. "Accuracy is 99%, is the model good?" and "how do you handle class imbalance?" are near-certain interview questions.

## 1. Four outcomes

With a **threshold** on the predicted probability (say, flag as nodule if $p \ge 0.5$), every sample lands in one cell of the **confusion matrix**:

| | predicted positive | predicted negative |
|---|---|---|
| **actually positive** | true positive (TP) | false negative (FN): a miss |
| **actually negative** | false positive (FP): a false alarm | true negative (TN) |

From the four counts:

$$\text{recall} = \frac{TP}{TP + FN} \qquad \text{precision} = \frac{TP}{TP + FP} \qquad F_1 = \frac{2 \cdot \text{precision} \cdot \text{recall}}{\text{precision} + \text{recall}}$$

- **Recall** (also called sensitivity or true positive rate): the fraction of real positives that were caught. The "always say no" model has recall 0.
- **Precision** (positive predictive value): the fraction of alarms that were real. A model that flags everything has recall 1 but precision equal to the positive rate (0.25% here).
- **Specificity** (true negative rate) $= TN / (TN + FP)$ and the **false positive rate** $= 1 - $ specificity appear in ROC curves ([end-to-end lesson](#/lesson/deep-learning/end-to-end-finetuning)).
- Accuracy $= (TP + TN)/\text{total}$ is dominated by TN when negatives are abundant.

### Why the harmonic mean?

We want a single score that is high only when both precision and recall are high. The ordinary average of 1.0 and 0.0 is 0.5, which would rate a useless "flag everything" model as mediocre rather than bad. Taking the minimum is strict but ignores improvements in the better metric. The **harmonic mean** $2pr/(p + r)$ sits between them: it is dominated by the smaller value but still rewards improving either. With precision 1.0 and recall 0.02 it gives about 0.04, not 0.51.

When one error matters more, use the **F-beta** score, $F_\beta = (1+\beta^2)\frac{p\,r}{\beta^2 p + r}$; $\beta = 2$ weighs recall more (screening, where misses are costly), $\beta = 0.5$ weighs precision more (when each alarm costs expensive human review).

```python-run
import numpy as np

def confusion(labels, probs, threshold):
    pred = probs >= threshold
    tp = int((pred & (labels == 1)).sum()); fp = int((pred & (labels == 0)).sum())
    fn = int((~pred & (labels == 1)).sum()); tn = int((~pred & (labels == 0)).sum())
    return tp, fp, fn, tn

def prf(tp, fp, fn):
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return precision, recall, f1

rng = np.random.default_rng(0)
labels = np.r_[np.zeros(9900, int), np.ones(100, int)]
probs = np.r_[rng.beta(1, 12, 9900), rng.beta(5, 3, 100)]      # a decent but imperfect classifier

print(f"{'threshold':>9} {'TP':>4} {'FP':>5} {'FN':>4} {'precision':>9} {'recall':>7} {'F1':>6} {'accuracy':>9}")
for t in [0.1, 0.3, 0.5, 0.7, 0.9]:
    tp, fp, fn, tn = confusion(labels, probs, t)
    p, r, f = prf(tp, fp, fn)
    print(f"{t:>9} {tp:>4} {fp:>5} {fn:>4} {p:>9.3f} {r:>7.3f} {f:>6.3f} {(tp + tn) / len(labels):>9.4f}")

p, r = 1.0, 0.02
print(f"\nprecision {p}, recall {r}: arithmetic mean {(p + r) / 2:.3f}, min {min(p, r):.3f}, harmonic (F1) {2 * p * r / (p + r):.3f}")
```

**Reading the table**

- Raising the threshold trades recall for precision: fewer alarms, more of them real, more misses.
- Accuracy is above 98% for every threshold from 0.3 upwards, including 0.9, where 96 of the 100 positives are missed. It hides exactly the trade-off we care about.
- F1 peaks at an intermediate threshold. Choosing the threshold is a separate decision from training the model, made on validation data according to the costs of each error.

## 2. Logging precision, recall and F1

The training application's metric function grows three lines:

```python
label = metrics[METRICS_LABEL] == 1
pred = metrics[METRICS_PRED] >= 0.5
tp = (label & pred).sum().item(); fp = (~label & pred).sum().item(); fn = (label & ~pred).sum().item()
precision = tp / max(tp + fp, 1)
recall = tp / max(tp + fn, 1)
f1 = 2 * precision * recall / max(precision + recall, 1e-12)
writer.add_scalar("pr/precision", precision, total_samples)
writer.add_scalar("pr/recall", recall, total_samples)
writer.add_scalar("pr/f1_score", f1, total_samples)
```

Note the guards against division by zero: a model that never predicts positive has no defined precision. Logged this way, the first model's failure is obvious: recall and F1 are zero.

## 3. Why the model ignores rare positives

Each training step follows the average gradient of the batch. With 400 negatives per positive, a batch of 32 contains a positive only about once every 12 batches. The gradient almost always says "lower the nodule probability", and lowering it for everything is the fastest way to reduce the average loss. The model converges to the base rate.

An **ideal** training set for learning, as opposed to the real-world mix, would present the classes in roughly equal numbers, so that every batch carries signal from both. We can create that presentation without new data.

## 4. Balancing what the model sees

### Oversampling the rare class

Keep separate lists of positive and negative indices and build each epoch so that positives appear far more often, for example alternating or at a fixed ratio. The book's `LunaDataset` gains a `ratio_int` argument: with ratio 1, every other sample is a positive (cycling through the positive list repeatedly), so batches are about half positive. A training "epoch" is then defined as a fixed number of samples (such as 200,000) rather than one pass over all negatives.

### WeightedRandomSampler

The general-purpose PyTorch tool assigns each sample a **weight** proportional to how often it should be drawn. Giving each class equal total weight ($w_i = 1/n_{\text{class}(i)}$) produces balanced batches in expectation:

```python
from torch.utils.data import WeightedRandomSampler

class_counts = torch.bincount(labels)                    # e.g. tensor([550000, 1350])
weights = 1.0 / class_counts[labels].float()              # rare-class samples get large weights
sampler = WeightedRandomSampler(weights, num_samples=200_000, replacement=True)
loader = DataLoader(train_set, batch_size=32, sampler=sampler, num_workers=8)   # no shuffle= with a sampler
```

### Weighting the loss instead

Instead of changing how often samples appear, change how much each one counts: `nn.CrossEntropyLoss(weight=torch.tensor([1.0, 400.0]))`, or for a single-logit binary model `nn.BCEWithLogitsLoss(pos_weight=torch.tensor(400.0))`. Every positive then contributes as much gradient as 400 negatives. Sampling and weighting are roughly equivalent in expectation; sampling gives every batch both classes (smoother gradients and better batch-norm statistics), while weighting keeps the natural data order and makes rare samples produce large, noisy gradient spikes.

### Focal loss

**Focal loss** multiplies each sample's cross-entropy by $(1 - p_t)^\gamma$, where $p_t$ is the probability of the true class: well-classified (easy) examples are down-weighted, so training concentrates on hard ones. It was designed for dense object detection, where easy background regions vastly outnumber objects.

The demo trains a logistic-regression classifier (one linear layer with a sigmoid, the smallest possible "network") on 20,000 negatives and 100 positives three ways.

```python-run
import numpy as np

rng = np.random.default_rng(0)
n_neg, n_pos = 20000, 100
X = np.vstack([rng.normal(0, 1, (n_neg, 2)), rng.normal(1.8, 1, (n_pos, 2))])
y = np.r_[np.zeros(n_neg), np.ones(n_pos)]
X_val = np.vstack([rng.normal(0, 1, (20000, 2)), rng.normal(1.8, 1, (100, 2))])
y_val = y.copy()

def train(pos_weight=1.0, balanced_sampler=False, steps=3000, lr=0.1, batch=256):
    w, b = np.zeros(2), 0.0
    p = np.where(y == 1, 0.5 / n_pos, 0.5 / n_neg) if balanced_sampler else np.full(len(y), 1 / len(y))
    for _ in range(steps):
        idx = rng.choice(len(y), batch, p=p)                       # WeightedRandomSampler, with replacement
        xb, yb = X[idx], y[idx]
        s = 1 / (1 + np.exp(-(xb @ w + b)))
        g = np.where(yb == 1, pos_weight, 1.0) * (s - yb) / batch   # gradient of (weighted) BCE w.r.t. logits
        w -= lr * xb.T @ g; b -= lr * g.sum()
    return 1 / (1 + np.exp(-(X_val @ w + b)))

for name, kwargs in [("plain training", {}), ("pos_weight = 200", {"pos_weight": 200}),
                     ("balanced sampler", {"balanced_sampler": True})]:
    probs = train(**kwargs)
    pred = probs >= 0.5
    tp = (pred & (y_val == 1)).sum(); fp = (pred & (y_val == 0)).sum(); fn = (~pred & (y_val == 1)).sum()
    prec = tp / (tp + fp) if tp + fp else 0.0
    print(f"{name:17s} TP {tp:3d}  FP {fp:5d}  FN {fn:3d}  precision {prec:.3f}  recall {tp / (tp + fn):.2f}"
          f"  mean prob on positives {probs[y_val == 1].mean():.2f}")
```

**Reading the result**

- Plain training finds almost no positives at threshold 0.5: high precision on a handful of flags, recall near zero. The model's probabilities for positives stay low, mirroring the 0.5% base rate.
- Loss weighting and balanced sampling both lift recall to around 90%, at the cost of thousands of false alarms: precision drops to a few percent. The two methods behave almost identically.
- Neither approach changes what the features can separate; they change *where the model's 0.5 sits*. Balanced training makes the model believe positives are common, so its probabilities are inflated relative to the real world. That is fine for ranking and for choosing a threshold on validation data, but if you need **calibrated** probabilities (for example, to display a risk score), correct them afterwards, for instance by refitting the output with temperature or Platt scaling on unbalanced validation data.

## 5. What happened in the CT project

Training with a balanced presentation transformed the classifier: recall on nodules jumped from zero to high values, while precision fell because many negatives were now flagged. F1 became meaningful. But a new symptom appeared after a few epochs: validation recall and F1 peaked and then declined while training metrics kept rising. With only about a thousand distinct positives, each shown again and again, the model began **memorising** them, the classic overfitting signature. The cure, the topic of the [next lesson](#/lesson/deep-learning/augmentation), is to make every repetition of a positive look slightly different.

## 6. Threshold-free evaluation

A single threshold summarises one operating point. To compare models independently of the threshold:

- **Precision-recall (PR) curve** and its area, **average precision (AP)**: the preferred summary when positives are rare, because it ignores the huge number of easy true negatives.
- **ROC curve** (recall versus false positive rate) and **ROC AUC**: the probability that a random positive gets a higher score than a random negative. Insensitive to class balance, which makes it look optimistic on rare-positive problems; worked through in the [end-to-end lesson](#/lesson/deep-learning/end-to-end-finetuning).
- In detection settings, **false positives per scan** (or per image) at a fixed recall is what users feel; LUNA's official score is based on recall at several false-positive-per-scan levels.

> [!INTERVIEW]
> **"How do you handle severe class imbalance in a deep learning classifier?"** Measure correctly first: confusion matrix, precision, recall, F1 or F-beta, PR-AUC; never accuracy alone. Then fix learning: balanced sampling (WeightedRandomSampler or oversampling the rare class), class-weighted loss (`weight` or `pos_weight`), or focal loss; augment the rare class to avoid memorising repeated positives; collect more positives if possible (hard-negative mining helps on the other side). Choose the operating threshold on validation data from the business cost of each error, and recalibrate probabilities if downstream consumers need true risk estimates.

## Summary

- Rare positives break both accuracy (dominated by true negatives) and learning (the average gradient ignores them).
- Recall = TP/(TP+FN), precision = TP/(TP+FP); F1 is their harmonic mean, high only when both are; F-beta shifts the emphasis.
- The decision threshold trades precision against recall; choose it on validation data according to error costs.
- Balance the presentation with oversampling or `WeightedRandomSampler`, or weight the loss (`weight`, `pos_weight`), or use focal loss; these inflate predicted probabilities, so recalibrate if needed.
- Repeating few positives leads to overfitting, which augmentation addresses.
- Use PR-AUC, ROC-AUC and false positives per case for threshold-free comparison.

## Glossary

- **Class imbalance**: one class being far rarer than another.
- **False positive / false negative**: a false alarm / a miss.
- **Confusion matrix**: the table of TP, FP, FN and TN counts.
- **Recall (sensitivity, true positive rate)**: TP / (TP + FN).
- **Precision (positive predictive value)**: TP / (TP + FP).
- **Specificity / false positive rate**: TN / (TN + FP) / FP / (FP + TN).
- **F1 score / F-beta**: harmonic mean of precision and recall / a weighted version.
- **Harmonic mean**: a mean dominated by the smaller of its inputs.
- **Decision threshold (operating point)**: the probability above which a sample is flagged.
- **Oversampling**: showing rare-class samples more often.
- **WeightedRandomSampler**: a sampler drawing indices with given per-sample weights.
- **pos_weight / class weight**: loss multipliers for the positive class / for each class.
- **Focal loss**: cross-entropy scaled down for easy examples.
- **Calibration**: agreement between predicted probabilities and observed frequencies.
- **Average precision (PR-AUC)**: the area under the precision-recall curve.

## Check yourself

```quiz
[
  {"q": "A model flags 50 candidates; 10 are real nodules, and the data contain 40 nodules in total. What are precision and recall?", "options": ["Precision 0.2, recall 0.25", "Precision 0.25, recall 0.2", "Precision 0.8, recall 0.25", "Precision 0.2, recall 0.8"], "answer": 0,
   "explain": "Precision = 10/50; recall = 10/40."},
  {"q": "Why use the harmonic mean in F1 rather than the arithmetic mean?", "options": ["It stays low unless both precision and recall are high", "It is easier to compute", "It always equals accuracy", "It ignores false positives"], "answer": 0,
   "explain": "Precision 1.0 and recall 0.02 give F1 ≈ 0.04 instead of 0.51."},
  {"q": "Raising the decision threshold usually…", "options": ["Increases precision and decreases recall", "Increases both", "Decreases both", "Has no effect on precision"], "answer": 0,
   "explain": "Fewer flags, each more likely to be right, and more misses."},
  {"q": "What does WeightedRandomSampler with weights 1/class_count achieve?", "options": ["Batches that contain each class equally often in expectation", "Removal of the rare class", "A smaller dataset", "Calibrated probabilities"], "answer": 0,
   "explain": "Each class gets equal total sampling weight."},
  {"q": "After training with a balanced sampler, the model's probabilities for real-world data are…", "options": ["Inflated towards the rare class; recalibrate if you need true risks", "Perfectly calibrated", "Always 0.5", "Unchanged from plain training"], "answer": 0,
   "explain": "The model learned that positives are common; thresholds or calibration must account for the real base rate."},
  {"q": "Which threshold-free metric is usually preferred for very rare positives?", "options": ["Average precision (PR-AUC)", "Accuracy", "Mean squared error", "Top-5 accuracy"], "answer": 0,
   "explain": "ROC AUC can look optimistic because true negatives are so plentiful."},
  {"q": "After balancing, validation F1 peaks and then falls while training F1 keeps rising. Why?", "options": ["The model memorises the few repeated positives: overfitting", "The learning rate is too small", "The sampler stopped working", "Validation data leaked into training"], "answer": 0,
   "explain": "Augmentation makes repeated positives look different each time."},
  {"q": "For a binary model with one logit, how do you make each positive count 300 times more in the loss?", "options": ["nn.BCEWithLogitsLoss(pos_weight=torch.tensor(300.0))", "nn.CrossEntropyLoss(ignore_index=300)", "Multiply the learning rate by 300", "Set label_smoothing=300"], "answer": 0,
   "explain": "pos_weight scales the positive term of the binary cross-entropy."}
]
```

> **Source:** Stevens, Antiga & Viehmann, *Deep Learning with PyTorch*, ch. 12 (false positives and false negatives, graphing the positives and negatives, recall, precision, implementing them in logMetrics, the F1 score, what an ideal dataset looks like, making the data look less like the actual and more like the ideal, contrasting balanced training with previous runs, recognising overfitting); PyTorch documentation, `WeightedRandomSampler`, `BCEWithLogitsLoss`; Lin et al., "Focal Loss for Dense Object Detection" (2017).
