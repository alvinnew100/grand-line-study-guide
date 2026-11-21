# Hyperparameter tuning at scale

> **Before this lesson:** read [Experiment tracking with MLflow](#/lesson/mlops/mlflow-tracking)
> (every trial here is a tracked run), [Reproducibility: seeds, environments and lineage](#/lesson/mlops/reproducibility)
> for seed variance, and [Distributed training and GPUs](#/lesson/mlops/distributed-gpus) for
> checkpoints and spot instances.

## In plain words

Every learning algorithm has dials that you set before it starts: how big each learning step is,
how deep a decision tree may grow, how strongly to discourage complicated solutions. These dials
are **hyperparameters**. The numbers the algorithm then works out by itself from the data are its
**parameters**. **Hyperparameter optimisation** (HPO), or tuning, is the search for the dial
settings that give the best model.

Tuning an oven for a new bread recipe is the same activity. You cannot calculate the right
temperature and time; you bake a loaf, taste it, adjust, and bake again. Each loaf costs flour
and an hour. The questions are the ones this lesson answers: which settings should you try next,
how do you avoid wasting loaves on settings that are clearly failing, and how do you judge the
result fairly?

Why this matters for a job: tuning is the most compute-hungry part of training and the easiest to
waste money on. An MLOps engineer is expected to run it in parallel, within a budget, with every
trial recorded. In interviews, "how would you tune an expensive model on a fixed budget?" and
"why does random search beat grid search?" are both standard.

## Parameters vs hyperparameters

**Parameters** are learned from data: the weights of a neural network, the split points of a
decision tree. **Hyperparameters** are chosen around the training: learning rate, tree depth,
regularisation strength (a penalty that keeps the model from fitting noise), batch size, the
shape of the network, even choices in preprocessing. One training with one setting of the dials
is called a **trial**, and the set of values each dial is allowed to take is the **search
space**. HPO looks for the configuration with the best validation score that can be found within
a budget of computing time.

## The evaluation protocol comes first

Before searching, decide how a trial is scored. Mueller and Guido (ch. 5) are emphatic on one
rule: if you pick hyperparameters by looking at the **test set**, the test score stops being an
honest estimate of how the model will do on new data, because you have chosen the settings that
happen to suit those particular rows. The standard protocol uses three parts: a training part to
fit the parameters, a **validation** part to choose hyperparameters, and a test part that is used
exactly once at the end. Cross-validation inside the training data can stand in for a fixed
validation part.

```mermaid
flowchart LR
  D[All data] --> TV[Train plus validation]
  D --> TEST[Test set: touched once at the end]
  TV --> TR[Train: fit parameters]
  TV --> VAL[Validation or CV folds: choose hyperparameters]
  VAL --> BEST[Best config]
  BEST --> REFIT[Refit on train plus validation]
  REFIT --> TEST
```

- **Grid search with cross-validation** (`GridSearchCV` in scikit-learn) scores each configuration
  by k-fold cross-validation on the training data, then retrains the winner on all of it.
- For data ordered in time, use **time-series splits**: train on the past, validate on a later
  period. Randomly mixed folds let the model see the future.
- For grouped data (several rows per user), use **GroupKFold**, which keeps all rows of one user
  on the same side.
- **Nested cross-validation** wraps the whole "tune, then train" procedure in an outer loop and
  gives an unbiased score for the procedure itself when data is scarce.

> [!WARNING]
> Every time you look at the test set and then change something, you leak a little. With thousands of
> HPO trials evaluated on the same validation set, you also overfit the *validation* set — the best
> trial's score is optimistically biased. Confirm the winner on untouched test data.

## Search strategies

### Grid search

Choose a few values for each hyperparameter and try every combination. It is easy to understand,
repeatable, and every trial is independent of the others, so they can all run at once. The
weakness is that the number of trials multiplies: four hyperparameters with five values each is
5 × 5 × 5 × 5 = 625 trainings.

### Random search

Draw each trial's settings at random from a stated range. Bergstra and Bengio showed in 2012 that
this beats a grid whenever only a few of the hyperparameters really matter, which is the usual
case. The reason is visible in a small example: a 3×3 grid over two hyperparameters tests only 3
different values of the important one, three times each, while 9 random points test 9 different
values of it.

The simulation below uses an invented scoring function in which the learning rate `lr` matters a
great deal and `depth` hardly at all, and gives both methods nine trials.

```python-run
import numpy as np
rng = np.random.default_rng(0)
# Objective: only "lr" matters much; "depth" barely matters.
def score(lr, depth):
    return 0.9 - 2.0 * (np.log10(lr) + 1.7) ** 2 - 0.0005 * (depth - 6) ** 2

grid_lr = [1e-3, 1e-2, 1e-1]; grid_depth = [3, 6, 9]
grid_best = max(score(lr, d) for lr in grid_lr for d in grid_depth)

best_random = []
for _ in range(500):                         # repeat the 9-trial random search many times
    lrs = 10 ** rng.uniform(-3, -1, 9)       # log-uniform sampling!
    ds = rng.integers(3, 10, 9)
    best_random.append(max(score(lr, d) for lr, d in zip(lrs, ds)))
print(f"grid search (9 trials)  best = {grid_best:.4f}")
print(f"random search (9 trials) mean best = {np.mean(best_random):.4f}, "
      f"beats grid in {np.mean(np.array(best_random) > grid_best) * 100:.0f}% of repeats")
```

`grid_best` is the best of the nine grid combinations. The loop then repeats a nine-trial random
search 500 times and records the best score of each repetition. The output:

```text
grid search (9 trials)  best = 0.7200
random search (9 trials) mean best = 0.8620, beats grid in 95% of repeats
```

The best learning rate in this toy function is about 0.02, and the grid's three values (0.001,
0.01, 0.1) all miss it. Nine random values nearly always land closer.

Note the line `10 ** rng.uniform(-3, -1, 9)`. It draws the *exponent* uniformly, so values
between 0.001 and 0.01 are as likely as values between 0.01 and 0.1. This is **log-uniform**
sampling, and it is the right choice for any hyperparameter whose sensible values span several
powers of ten, such as a learning rate or a regularisation strength.

### Bayesian optimisation

Random search ignores what earlier trials found. **Bayesian optimisation** uses it. After each
trial it updates a cheap statistical model, called a **surrogate**, that predicts the score of
configurations not yet tried, along with how uncertain that prediction is. A rule called the
**acquisition function** then picks the next configuration, balancing **exploitation** (try near
the best results so far) against **exploration** (try where the surrogate is unsure). Two common
surrogates are Gaussian processes and the **Tree-structured Parzen Estimator (TPE)**, the default
in the Optuna and Hyperopt libraries. Bayesian methods reach a good configuration in fewer
trials, which matters when each trial is expensive. They are harder to parallelise, because each
suggestion is better the more earlier results are already known.

### Early stopping: successive halving, Hyperband, ASHA

Most bad configurations show themselves early in training. **Successive halving** exploits that.
Start many trials but give each only a small budget, say one epoch. Keep the best third (in
general the best $1/\eta$, where $\eta$ is a chosen factor such as 3), give the survivors three
times the budget, and repeat until one remains. **Hyperband** runs several rounds of successive
halving with different starting points, hedging between "many configurations with tiny budgets"
and "few configurations with large budgets". **ASHA** (asynchronous successive halving) promotes
a trial as soon as it qualifies without waiting for its whole group to finish, which suits a
cluster where machines free up at different times.

The simulation starts 27 configurations with $\eta = 3$. Each has a hidden true quality, and
`observe` returns a noisy score that rises towards that quality as the budget grows, the way a
learning curve does.
```python-run
import numpy as np
rng = np.random.default_rng(1)
n, eta, min_budget = 27, 3, 1
quality = rng.uniform(0.6, 0.9, n)                       # true final accuracy of each config
def observe(q, budget):                                   # noisy learning curve
    return q * (1 - np.exp(-budget / 3)) + rng.normal(0, 0.01)

alive = list(range(n)); budget = min_budget; spent = 0
while len(alive) > 1:
    scores = {i: observe(quality[i], budget) for i in alive}
    spent += len(alive) * budget
    keep = max(1, len(alive) // eta)
    alive = sorted(alive, key=scores.get, reverse=True)[:keep]
    print(f"budget={budget:2d} epochs -> kept {len(alive):2d} configs")
    budget *= eta
full_cost = n * budget
print(f"picked config quality {quality[alive[0]]:.3f} (true best {quality.max():.3f}); "
      f"epochs spent {spent} vs {full_cost} for training all {n} fully")
```

The output:

```text
budget= 1 epochs -> kept  9 configs
budget= 3 epochs -> kept  3 configs
budget= 9 epochs -> kept  1 configs
picked config quality 0.885 (true best 0.894); epochs spent 81 vs 729 for training all 27 fully
```

The method spent 27×1 + 9×3 + 3×9 = 81 epochs, against 729 for training all 27 configurations to
the end, and picked a configuration within 0.01 of the true best. It did not pick *the* best:
early scores are noisy, and a slow starter can be eliminated. That is the trade this method
makes, a small risk for a ninefold saving.

### Population-based training (PBT)

Train a population in parallel; periodically, poor performers copy the weights of good performers
(exploit) and perturb their hyperparameters (explore). PBT discovers hyperparameter *schedules* and is
popular in reinforcement learning.

| Method | Sample efficiency | Parallelism | Best when |
|---|---|---|---|
| Grid | poor | perfect | ≤ 2–3 hyperparameters, need exhaustive table |
| Random | fair | perfect | cheap trials, strong baseline |
| Bayesian (TPE/GP) | good | moderate | expensive trials |
| Hyperband/ASHA | good | high | iterative training with meaningful early signal |
| PBT | good | high | long trainings, schedules matter |

## Tools

**Optuna** is the most popular Python library for HPO. You write an `objective` function that
receives a `trial`, asks it for hyperparameter values, trains, and returns the score. Optuna
decides which values to hand out (its "sampler", TPE by default), can stop hopeless trials early
(its "pruners"), and can store results in a database so that many machines work on one study.

```python
import optuna, mlflow
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.model_selection import cross_val_score

def objective(trial: optuna.Trial) -> float:
    params = {
        "learning_rate": trial.suggest_float("learning_rate", 1e-3, 0.3, log=True),
        "max_leaf_nodes": trial.suggest_int("max_leaf_nodes", 8, 128, log=True),
        "l2_regularization": trial.suggest_float("l2_regularization", 1e-8, 10.0, log=True),
        "max_iter": trial.suggest_int("max_iter", 100, 600, step=100),
    }
    with mlflow.start_run(nested=True):                      # one child run per trial
        mlflow.log_params(params)
        score = cross_val_score(HistGradientBoostingClassifier(**params, random_state=0),
                                X_train, y_train, cv=5, scoring="average_precision").mean()
        mlflow.log_metric("cv_pr_auc", score)
    return score

study = optuna.create_study(direction="maximize",
                            sampler=optuna.samplers.TPESampler(seed=0),
                            pruner=optuna.pruners.MedianPruner(n_warmup_steps=5),
                            storage="postgresql://optuna:***@db/optuna",   # shared storage -> many workers
                            study_name="churn-gbm", load_if_exists=True)
with mlflow.start_run(run_name="hpo-parent"):
    study.optimize(objective, n_trials=100, timeout=3600)
    mlflow.log_params({f"best_{k}": v for k, v in study.best_params.items()})
```

Inside `objective`, each `trial.suggest_*` call both declares a hyperparameter's range and
returns the value to use in this trial; `log=True` requests log-uniform sampling. Each trial is
recorded as a nested MLflow run and scored by 5-fold cross-validation. `create_study` sets the
direction (maximise), the sampler, the pruner and a shared database, and `optimize` runs up to
100 trials or one hour, whichever ends first.

For iterative training, report intermediate values and let the pruner stop hopeless trials:

```python
for epoch in range(epochs):
    val = train_one_epoch(...)
    trial.report(val, step=epoch)
    if trial.should_prune():
        raise optuna.TrialPruned()
```

**Ray Tune** — distributed HPO on a Ray cluster with ASHA, PBT, Bayesian search backends, per-trial
resource requests (e.g., 1 GPU each) and checkpointing. **Katib** — Kubernetes-native HPO in Kubeflow
(each trial is a pod/job). Managed: **SageMaker Automatic Model Tuning**, **Vertex AI Vizier**, **Azure
ML sweeps**; W&B Sweeps.

## Operational concerns

- **Budget first**: decide the number of trials / GPU-hours before starting; log cost per study.
- **Track every trial** as a child run with params, metrics, seed — failed and pruned ones included.
- **Fixed data and seed policy**: all trials see the same splits; otherwise you compare noise.
  For the finalists, rerun with several seeds (lesson 11).
- **Fault tolerance**: trials should checkpoint so spot preemptions do not waste them (lesson 14).
- **Parallelism vs efficiency**: 100 parallel random trials finish fast; 100 sequential Bayesian trials
  are more sample-efficient. With K parallel workers, Bayesian methods suggest K points using partial
  information — a middle ground.
- **Multi-objective**: accuracy vs latency vs model size. Optuna supports Pareto fronts
  (`directions=["maximize", "minimize"]`); in production you usually maximise quality *subject to* a
  latency budget.
- **Warm starts**: seed the search with last month's best configuration; narrow ranges over time.
- **Do not over-tune**: for scheduled retrains, re-tuning every time adds cost and variance. Tune
  occasionally; retrain with fixed hyperparameters.

```mermaid
flowchart LR
  STUDY[(Study storage DB)] <--> W1[Worker 1: trial pod]
  STUDY <--> W2[Worker 2: trial pod]
  STUDY <--> W3[Worker 3: trial pod]
  W1 --> ML[(MLflow: one child run per trial)]
  W2 --> ML
  W3 --> ML
  ML --> PICK[Select best, rerun with seeds, test once]
  PICK --> REG[(Registry)]
```

> [!INTERVIEW]
> "How would you tune hyperparameters for an expensive model with a fixed budget?" — Define the metric and
> a leak-free validation scheme; choose log-scaled search spaces; start with random search or TPE plus an
> early-stopping scheduler (ASHA/Hyperband) so bad configs die cheaply; run trials in parallel on spot
> instances with checkpointing; track everything; confirm the top few with multiple seeds; evaluate once
> on the test set. Mention that random search beats grid search in high dimensions.

## Designing a search space

The search space is the most consequential HPO decision; a perfect optimiser cannot fix ranges that
exclude the optimum or waste budget on irrelevant dimensions.

| Hyperparameter kind | Examples | How to search |
|---|---|---|
| Scale parameters spanning decades | learning rate, weight decay, regularisation | log-uniform |
| Capacity | depth, leaves, hidden units, layers | integers, often log-scaled or powers of two |
| Probabilities / fractions | dropout, subsample, colsample | uniform on a sensible interval |
| Choices | optimiser, activation, model family | categorical |
| Conditional | momentum only if optimiser = SGD | define-by-run branches |

Guidelines:

1. **Start wide, then narrow.** A first coarse sweep finds the region; a second sweep zooms in. If the
   best trials sit on the edge of a range, the range is wrong — extend it.
2. **Tune the few that matter.** For gradient-boosted trees: learning rate with number of trees (use
   early stopping to set the latter), tree complexity (leaves/depth), regularisation, subsampling. For
   neural nets: learning rate first, then batch size, weight decay, warmup.
3. **Fix what you can reason about.** Do not tune the random seed; do not tune things that barely matter.
4. **Use domain knowledge as priors.** Seed the study with known-good configurations
   (`study.enqueue_trial({...})`).

```python
def objective(trial):
    family = trial.suggest_categorical("model", ["gbm", "logreg"])
    if family == "gbm":                                   # conditional space: define-by-run
        params = {"learning_rate": trial.suggest_float("gbm_lr", 1e-3, 0.3, log=True),
                  "max_leaf_nodes": trial.suggest_int("gbm_leaves", 8, 128, log=True)}
        model = HistGradientBoostingClassifier(early_stopping=True, max_iter=2000, **params)
    else:
        model = LogisticRegression(C=trial.suggest_float("lr_C", 1e-4, 1e2, log=True), max_iter=2000)
    return cross_val_score(model, X, y, cv=cv, scoring="average_precision").mean()
```

## How many trials? Thinking in probabilities

How many random trials are enough? There is a neat piece of arithmetic. Suppose you would be
satisfied with any configuration in the best 5% of the search space. One random trial misses that
region with probability 0.95, and $n$ independent trials all miss it with probability $0.95^n$.
For a 95% chance of at least one hit you need $1 - 0.95^n \ge 0.95$, which gives about 59 trials,
whatever the number of hyperparameters.

```python-run
import math
print("trials needed for P(at least one trial in the top q of the space) >= conf")
for q in (0.10, 0.05, 0.01):
    for conf in (0.90, 0.95, 0.99):
        n = math.ceil(math.log(1 - conf) / math.log(1 - q))
        print(f"  top {q:4.0%}, confidence {conf:.0%}: {n:4d} trials")
```

The table printed by the program shows the pattern: 59 trials for the top 5% at 95% confidence,
but 299 trials for the top 1%. Around 60 trials is therefore a principled size for a first random
sweep. After that, a smarter sampler or a narrower search space uses the budget better than
hundreds more random points.

## Reading the results

The best trial's settings (`study.best_params`) are not the whole result. Also inspect:

- **Optimisation history**: is the best value still improving, or flat for the last half? Flat means you
  can stop.
- **Parameter importance** (fANOVA in Optuna): which hyperparameters explain score variance? Drop the
  rest from the next sweep.
- **Slice / parallel-coordinate plots**: is the optimum inside the range or pinned at a boundary?
- **Sensitivity around the best point**: prefer a configuration in a *flat, wide* good region over a
  marginally better one on a cliff — it will be more robust to data changes at the next retrain.
- **Top-k agreement**: if the top ten trials have similar scores and very different hyperparameters, the
  model is insensitive and further tuning is wasted effort.

```python-run
import numpy as np
rng = np.random.default_rng(3)
# Simulated study: score depends strongly on log10(lr), weakly on leaves, not at all on subsample.
n = 200
log_lr = rng.uniform(-3, -0.5, n); leaves = rng.integers(8, 129, n); sub = rng.uniform(0.5, 1.0, n)
score = 0.74 - 0.03 * (log_lr + 1.3) ** 2 - 0.000002 * (leaves - 48) ** 2 + rng.normal(0, 0.003, n)

def importance(x, y, bins=8):                     # variance explained by binning one parameter
    edges = np.quantile(x, np.linspace(0, 1, bins + 1)); idx = np.clip(np.searchsorted(edges, x, side="right") - 1, 0, bins - 1)
    means = np.array([y[idx == b].mean() for b in range(bins)]); counts = np.bincount(idx, minlength=bins)
    return float((counts * (means - y.mean()) ** 2).sum() / ((y - y.mean()) ** 2).sum())
for name, x in (("learning_rate (log)", log_lr), ("max_leaf_nodes", leaves.astype(float)), ("subsample", sub)):
    print(f"{name:20s} importance ~ {importance(x, score):.2f}")
best = np.argsort(score)[-10:]
print(f"top-10 trials: lr in [{10**log_lr[best].min():.3f}, {10**log_lr[best].max():.3f}], "
      f"leaves in [{leaves[best].min()}, {leaves[best].max()}], subsample in [{sub[best].min():.2f}, {sub[best].max():.2f}]")
```

The program invents 200 trials whose score depends strongly on the learning rate, weakly on the
number of leaves and not at all on `subsample`. `importance` sorts one hyperparameter's values
into eight bins and measures what share of the variation in score is explained by which bin a
trial fell in. The output:

```text
learning_rate (log)  importance ~ 0.92
max_leaf_nodes       importance ~ 0.05
subsample            importance ~ 0.04
top-10 trials: lr in [0.030, 0.084], leaves in [26, 67], subsample in [0.52, 0.97]
```

The learning rate explains about 92% of the variation. The ten best trials agree on a narrow
learning-rate range and are spread over nearly the whole `subsample` range, which confirms that
`subsample` does not matter here. Remove it from the next search and spend the budget where it
counts.

## HPO and continuous training

For scheduled retrains, a common policy is: **fixed hyperparameters by default; a small warm-started
re-tune when the promotion gate fails or drift is large; a full study quarterly or after feature
changes.** Record with each production model which study produced its hyperparameters, so the lineage
includes the tuning decision.

## Summary

- Tune on validation data (or CV), never on the test set; respect time and group structure.
- Random search > grid search when few hyperparameters matter; sample scale-type hyperparameters
  log-uniformly.
- Bayesian optimisation is sample-efficient; successive halving/Hyperband/ASHA save compute by stopping
  bad trials early; PBT learns schedules.
- Operationally: budget, track every trial, fix data/seed policy, checkpoint, and consider multi-objective
  trade-offs.

## Glossary

- **Hyperparameter** - a setting chosen before training, such as the learning rate.
- **Parameter** - a value the model learns from data.
- **HPO (tuning)** - the search for the best hyperparameter configuration.
- **Trial / study** - one training with one configuration / a whole search.
- **Search space** - the allowed values of each hyperparameter.
- **Validation set** - data used to choose hyperparameters, separate from the final test set.
- **Grid search** - trying every combination of listed values.
- **Random search** - drawing configurations at random from ranges.
- **Log-uniform** - sampling so that each power of ten is equally likely.
- **Bayesian optimisation** - choosing the next trial with a model of earlier results.
- **Surrogate / acquisition function** - that model / the rule that picks the next point.
- **TPE** - the Tree-structured Parzen Estimator, a common surrogate.
- **Exploration / exploitation** - trying uncertain regions / refining the best known region.
- **Successive halving** - repeatedly keeping the best fraction of trials and raising their
  budget.
- **Hyperband / ASHA** - several halving rounds with different trade-offs / its asynchronous form.
- **Pruner** - the component that stops unpromising trials early.
- **PBT** - population-based training, which adapts hyperparameters during training.
- **Pareto front** - the configurations for which no other is better on every objective.
- **Warm start** - beginning a search from previously good configurations.

```quiz
[
  {"q": "Why does random search often beat grid search with the same number of trials?",
   "options": ["It uses GPUs better", "It tests more distinct values of the few hyperparameters that matter", "It never repeats a configuration", "It uses the test set"],
   "answer": 1, "explain": "A grid wastes trials repeating the same values of important hyperparameters."},
  {"q": "How should a learning rate range of 1e-4 to 1e-1 be sampled?",
   "options": ["Uniformly", "Log-uniformly", "Only at the endpoints", "From a normal distribution centred at 0.05"],
   "answer": 1, "explain": "Parameters spanning orders of magnitude should be searched on a log scale."},
  {"q": "What does successive halving do?",
   "options": ["Halves the learning rate each epoch", "Gives many configs a small budget, keeps the best fraction, and increases their budget repeatedly", "Splits data in half", "Halves the batch size on OOM"],
   "answer": 1, "explain": "It allocates more budget only to promising configurations."},
  {"q": "For time-series data, which validation scheme is appropriate during tuning?",
   "options": ["Random k-fold", "Train on the past, validate on later periods", "Leave-one-out with shuffling", "Validate on the training set"],
   "answer": 1, "explain": "Random folds leak future information."},
  {"q": "After 2,000 trials, the best validation score is 0.912. What is the right expectation for test performance?",
   "options": ["Exactly 0.912", "Probably somewhat lower, because the maximum over many noisy trials is optimistically biased", "Higher", "Unrelated"],
   "answer": 1, "explain": "Selecting the max overfits the validation set; confirm on untouched test data."},
  {"q": "Which Optuna feature stops unpromising trials early?",
   "options": ["Samplers", "Pruners", "Storages", "Directions"],
   "answer": 1, "explain": "Pruners use reported intermediate values to stop trials."},
  {"q": "What is the role of the surrogate model in Bayesian optimisation?",
   "options": ["It replaces the final model in production", "It predicts the score of untried configurations to guide which to try next", "It labels data", "It prunes the dataset"],
   "answer": 1, "explain": "The surrogate plus an acquisition function balances exploration and exploitation."}
]
```

> **Source:** Mueller & Guido, *Introduction to Machine Learning with Python*, ch. 5 (cross-validation, grid search, the danger of using the test set for selection); Bergstra & Bengio, *Random Search for Hyper-Parameter Optimization* (JMLR 2012); Li et al., *Hyperband* (2018) and *ASHA* (2020); Optuna, Ray Tune and Katib documentation.
