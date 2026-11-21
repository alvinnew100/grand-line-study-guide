# Optimisers (SGD, momentum, Adam, AdamW) and validation

> **Before this lesson:** you need gradient descent, the learning rate and input standardisation from [Learning as parameter estimation](#/lesson/deep-learning/learning-from-data), and `.grad`, `zero_grad` and `no_grad` from [Autograd in depth](#/lesson/deep-learning/autograd). An **exponential moving average** is explained below when it first appears.

## In plain words

An **optimiser** is the object that turns gradients into parameter updates. Plain gradient descent takes a step straight downhill of a fixed size. Smarter optimisers remember previous steps (**momentum**) or give each parameter its own step size (**adaptive** methods such as **Adam**). Choosing and configuring the optimiser often decides whether a model trains in an hour, in a day, or not at all.

The second half of the lesson answers a different question: how do you know training is *working*? A falling training loss is not enough, because a big model can memorise its training examples. You hold back some data the model never trains on, the **validation set**, and watch its loss too. When training loss keeps falling but validation loss rises, the model is **overfitting**: learning quirks of the training examples that do not generalise.

Analogy: a student preparing for an exam. Momentum is study habit, continuing in the direction that was working. Adam is a tutor who notices you are already strong in algebra but weak in geometry and adjusts time per topic. The validation set is a mock exam with fresh questions: if your homework marks rise while your mock-exam marks fall, you are memorising answers rather than learning.

Why it matters for a job: "SGD or Adam? What does AdamW change? Why is my validation loss going up?" are among the most common deep-learning interview questions, and every training job you run will involve picking an optimiser, a learning rate, a weight decay and a validation strategy.

## 1. The torch.optim interface

Every PyTorch optimiser follows the same pattern:

```python
optimizer = torch.optim.SGD(model.parameters(), lr=0.01, momentum=0.9)

for x, y in train_loader:
    optimizer.zero_grad()            # clear .grad of every parameter
    loss = loss_fn(model(x), y)
    loss.backward()                  # fill .grad
    optimizer.step()                 # update parameters using .grad and internal state
```

- The constructor receives an iterable of parameters (usually `model.parameters()`) and hyperparameters. A **hyperparameter** is a setting chosen by you rather than learned, such as the learning rate.
- `step()` reads each parameter's `.grad`, updates the parameter in place and updates the optimiser's **state** (momentum buffers, running averages). The state lives in `optimizer.state` and appears in `optimizer.state_dict()`, which you must save in checkpoints to resume training exactly.
- `param_groups` lets different parameters use different settings, for example no weight decay on biases or a smaller learning rate for pretrained layers:

```python
decay, no_decay = [], []
for name, p in model.named_parameters():
    (no_decay if p.ndim == 1 else decay).append(p)     # biases and norm scales are 1-D
optimizer = torch.optim.AdamW([
    {"params": decay, "weight_decay": 0.05},
    {"params": no_decay, "weight_decay": 0.0},
], lr=3e-4)
```

## 2. Stochastic gradient descent

Computing the gradient on the full dataset for every step is expensive with millions of examples. **Stochastic gradient descent (SGD)** estimates the gradient from a random **mini-batch** of examples (typically 32 to 1,024) and steps immediately. The estimate is noisy, but:

- each step is far cheaper, so you take many more steps per hour;
- the noise helps escape flat regions and sharp, narrow minima, which tends to improve generalisation;
- mini-batches fill a GPU's parallel units efficiently.

Larger batches give smoother gradient estimates and better hardware use, up to a point; very large batches often need a larger learning rate (a common heuristic scales it roughly in proportion to batch size) plus a warm-up period, covered in the [schedules lesson](#/lesson/deep-learning/schedules-clipping).

## 3. Momentum

Plain SGD struggles in long narrow valleys: the gradient points mostly across the valley, so steps bounce from wall to wall while creeping along the floor. **Momentum** fixes this by keeping a running **velocity**: a blend of the current gradient and previous steps. Components that keep pointing the same way (along the valley) build up; components that flip sign (across it) cancel out.

PyTorch's formulation, with momentum coefficient $\mu$ (usually 0.9) and gradient $g_t$ at step $t$:

$$b_t = \mu\, b_{t-1} + g_t, \qquad \theta_t = \theta_{t-1} - \eta\, b_t$$

$b_t$ is the momentum **buffer** (the first step sets $b_1 = g_1$), $\theta$ the parameters and $\eta$ the learning rate. **Nesterov momentum** (`nesterov=True`) uses $g_t + \mu\, b_t$ in the update instead of $b_t$, a "look ahead" correction that often reduces overshooting.

**Weight decay** in `SGD` adds $\lambda \theta$ to the gradient before everything else, which pulls weights towards zero (an L2 penalty, see [regularisation](#/lesson/deep-learning/regularisation)).

## 4. Adaptive methods: Adam

Different parameters can have gradients of very different typical sizes (recall the slope imbalance between weight and bias in the previous lessons). **Adam** (adaptive moment estimation) gives each parameter its own effective step size by tracking two **exponential moving averages**. An exponential moving average updates a running value as $a \leftarrow \beta a + (1 - \beta) x$: each new observation gets weight $1 - \beta$ and older ones fade geometrically.

$$m_t = \beta_1 m_{t-1} + (1-\beta_1) g_t \qquad v_t = \beta_2 v_{t-1} + (1-\beta_2) g_t^2$$

$$\hat m_t = \frac{m_t}{1-\beta_1^t}, \quad \hat v_t = \frac{v_t}{1-\beta_2^t}, \quad \theta_t = \theta_{t-1} - \eta \frac{\hat m_t}{\sqrt{\hat v_t} + \epsilon}$$

- $m$ is a momentum-like average of gradients (the "first moment").
- $v$ averages squared gradients (the "second moment"), measuring each parameter's typical gradient size.
- Dividing by $\sqrt{\hat v}$ normalises: parameters with consistently large gradients take smaller steps, parameters with tiny gradients take larger ones. Every parameter moves roughly $\eta$ per step at most.
- Both averages start at zero, which biases them towards zero early on; dividing by $1 - \beta^t$ is the **bias correction** that undoes this.
- PyTorch defaults: `lr=1e-3`, `betas=(0.9, 0.999)`, `eps=1e-8`.

Adam is forgiving: the default learning rate works acceptably across many problems, which is why it is the usual first choice. Its cost is memory: two extra numbers per parameter.

## 5. AdamW: weight decay done right

With plain `Adam`, the `weight_decay` argument adds $\lambda\theta$ to the gradient, exactly like SGD. But Adam then divides that term by $\sqrt{\hat v}$, so parameters with large gradients get almost no decay and parameters with small gradients get a lot. The regularisation becomes uneven and weaker than intended.

**AdamW** (Loshchilov and Hutter) **decouples** weight decay: it shrinks the parameters directly, $\theta \leftarrow \theta - \eta \lambda \theta$, and runs the Adam update on the raw gradient. Every parameter decays at the same rate. In practice AdamW generalises better and is the default optimiser for transformers and most modern models. Note that `torch.optim.AdamW` has a default `weight_decay` of 0.01, while `torch.optim.Adam` defaults to 0.

| optimiser | extra state per parameter | typical learning rate | where it shines |
|---|---|---|---|
| SGD | none | 0.01 to 0.1 | simple, cheap; strong for convnets with a schedule |
| SGD + momentum (0.9) | 1 | 0.01 to 0.1 | the classic image-classification recipe |
| Adam | 2 | 1e-4 to 1e-3 | robust default, fast progress early |
| AdamW | 2 | 1e-4 to 1e-3 (weight decay 0.01 to 0.1) | transformers, fine-tuning, most new work |

## 6. Seeing the difference

Here is a NumPy implementation of `SGD` (with momentum, Nesterov and weight decay) and `Adam`/`AdamW`, written to match PyTorch's update rules, raced on a narrow valley $f(x, y) = \frac{1}{2}(x^2 + 100 y^2)$: the $y$ direction is 100 times steeper than $x$.

```python-run
import numpy as np

class Param:
    def __init__(self, data):
        self.data, self.grad = np.asarray(data, dtype=float), None

class SGD:
    def __init__(self, params, lr, momentum=0.0, nesterov=False, weight_decay=0.0):
        self.params, self.lr, self.mu, self.nesterov, self.wd = list(params), lr, momentum, nesterov, weight_decay
        self.state = {}
    def step(self):
        for p in self.params:
            g = p.grad + self.wd * p.data                    # L2-style weight decay
            if self.mu:
                buf = self.state.get(id(p))
                buf = g.copy() if buf is None else self.mu * buf + g
                self.state[id(p)] = buf
                g = g + self.mu * buf if self.nesterov else buf
            p.data -= self.lr * g

class Adam:
    def __init__(self, params, lr=1e-3, betas=(0.9, 0.999), eps=1e-8, weight_decay=0.0, decoupled=False):
        self.params, self.lr, (self.b1, self.b2), self.eps = list(params), lr, betas, eps
        self.wd, self.decoupled, self.t = weight_decay, decoupled, 0
        self.m = {id(p): np.zeros_like(p.data) for p in self.params}
        self.v = {id(p): np.zeros_like(p.data) for p in self.params}
    def step(self):
        self.t += 1
        for p in self.params:
            g = p.grad
            if self.decoupled:
                p.data *= 1 - self.lr * self.wd              # AdamW: shrink weights directly
            elif self.wd:
                g = g + self.wd * p.data                     # Adam: decay folded into the gradient
            m = self.m[id(p)] = self.b1 * self.m[id(p)] + (1 - self.b1) * g
            v = self.v[id(p)] = self.b2 * self.v[id(p)] + (1 - self.b2) * g * g
            m_hat, v_hat = m / (1 - self.b1 ** self.t), v / (1 - self.b2 ** self.t)
            p.data -= self.lr * m_hat / (np.sqrt(v_hat) + self.eps)

def race(make_opt, steps):
    p = Param([-4.0, 1.0])
    opt = make_opt([p])
    for _ in range(steps):
        x, y = p.data
        p.grad = np.array([x, 100 * y])                       # gradient of 0.5*(x^2 + 100 y^2)
        opt.step()
    x, y = p.data
    return 0.5 * (x * x + 100 * y * y)

contestants = {
    "SGD lr=0.012":            lambda ps: SGD(ps, 0.012),
    "SGD + momentum 0.9":      lambda ps: SGD(ps, 0.012, momentum=0.9),
    "SGD + Nesterov 0.9":      lambda ps: SGD(ps, 0.012, momentum=0.9, nesterov=True),
    "Adam lr=0.1":             lambda ps: Adam(ps, 0.1),
}
print(f"{'optimiser':<22}{'after 10':>12}{'after 50':>12}{'after 100':>12}")
for name, make in contestants.items():
    print(f"{name:<22}" + "".join(f"{race(make, s):12.5f}" for s in (10, 50, 100)))
```

**Reading the result**

- The learning rate for SGD cannot exceed about $2/100$ or the steep $y$ direction diverges, so progress along the gentle $x$ direction is slow: after 100 steps the loss is still about 0.7.
- Momentum and Nesterov build speed along $x$ and reach losses hundreds to thousands of times lower in the same number of steps (momentum starts worse because the velocity first overshoots).
- Adam rescales each coordinate by its own gradient size, so both directions progress at similar rates without tuning for the steepest one.

This toy is the whole story of why plain SGD is rarely used without momentum, and why adaptive methods are popular.

## 7. Validation: is the model learning or memorising?

The training loss measures fit on examples the model has seen. What we care about is performance on **new** examples. So we split the data:

- **Training set**: used to compute gradients.
- **Validation set** (also called the development set): never used for gradients; used to choose hyperparameters, pick the best epoch, and detect overfitting.
- **Test set**: touched once at the end to report final performance. If you tune on it, it stops being an honest estimate.

A random split in PyTorch:

```python
n = len(dataset)
perm = torch.randperm(n)                    # a random ordering of 0..n-1
n_val = int(0.2 * n)
val_idx, train_idx = perm[:n_val], perm[n_val:]
train_set = torch.utils.data.Subset(dataset, train_idx.tolist())
val_set = torch.utils.data.Subset(dataset, val_idx.tolist())
# or: train_set, val_set = torch.utils.data.random_split(dataset, [0.8, 0.2])
```

And a validation pass, which must not build graphs or update weights:

```python
model.eval()
total, count = 0.0, 0
with torch.no_grad():
    for x, y in val_loader:
        total += loss_fn(model(x), y).item() * len(y)
        count += len(y)
val_loss = total / count
model.train()
```

Not every split should be random. If several samples come from the same person, patient, user or device, split **by group** so no group appears on both sides, otherwise the model scores well by recognising the person rather than learning the task. Time-ordered data should be split by time. The [CT project](#/lesson/deep-learning/ct-data-pipeline) splits by scan for exactly this reason.

### Reading the curves

Plot training and validation loss after every epoch:

- **Both falling**: keep training.
- **Both high and flat**: **underfitting**. The model is too small, the learning rate is wrong, or there is a bug. Increase capacity or fix the setup.
- **Training falling, validation rising**: **overfitting**. Stop at the best validation epoch (**early stopping**), add regularisation or data augmentation, or get more data.

The demo fits a flexible model (a degree-12 polynomial, which has far more freedom than the data's underlying sine curve needs) to 18 noisy training points with Adam, tracks 6 held-out validation points, and then draws both loss curves with **matplotlib**, Python's plotting library (the first run downloads it, which takes a few seconds).

```python-run
import numpy as np
import matplotlib.pyplot as plt

rng = np.random.default_rng(3)
n = 24
x = rng.uniform(-1, 1, n)
y = np.sin(3 * x) + rng.normal(0, 0.25, n)          # true signal plus noise
perm = rng.permutation(n)
val_idx, train_idx = perm[:6], perm[6:]

F = np.stack([x ** k for k in range(1, 13)], axis=1)  # 12 polynomial features
w, b = np.zeros(12), 0.0
m, v, lr = np.zeros(13), np.zeros(13), 0.05
mse = lambda idx: ((F[idx] @ w + b - y[idx]) ** 2).mean()

best = (np.inf, 0)
train_curve, val_curve = [], []
for t in range(1, 10001):
    err = F[train_idx] @ w + b - y[train_idx]
    g = np.append(2 * F[train_idx].T @ err / len(err), 2 * err.mean())
    m = 0.9 * m + 0.1 * g; v = 0.999 * v + 0.001 * g * g          # Adam moments
    step = lr * (m / (1 - 0.9 ** t)) / (np.sqrt(v / (1 - 0.999 ** t)) + 1e-8)
    w, b = w - step[:-1], b - step[-1]
    train_curve.append(mse(train_idx)); val_curve.append(mse(val_idx))
    best = min(best, (val_curve[-1], t))
    if t in (10, 100, 500, 1000, 2000, 5000, 10000):
        print(f"epoch {t:5d}   train {mse(train_idx):.4f}   validation {mse(val_idx):.4f}")
print(f"best validation loss {best[0]:.4f} at epoch {best[1]}  <- early stopping would keep this one")

epochs = np.arange(1, 10001)
plt.plot(epochs, train_curve, label="training loss")
plt.plot(epochs, val_curve, label="validation loss")
plt.axvline(best[1], color="gray", linestyle="--", label=f"best validation epoch ({best[1]})")
plt.xscale("log"); plt.yscale("log")
plt.xlabel("epoch (log scale)"); plt.ylabel("mean squared error (log scale)")
plt.legend()
plt.show()
```

The two lists `train_curve` and `val_curve` collect the losses after every update, `plt.plot` draws each list as a line against the epoch numbers, `plt.axvline` marks the best validation epoch with a dashed vertical line, and `plt.show()` displays the chart. Both axes use a **log scale** (equal steps mean multiplying by 10), so the first few hundred epochs, where the interesting turn happens, are not squashed into the left edge.

Training loss keeps falling all the way to epoch 10,000, but validation loss bottoms out within the first few hundred epochs and then climbs steadily as the polynomial bends to fit individual noisy points. In the chart this is the classic overfitting shape from the list above: the two curves fall together, then separate, with the gap widening to the right of the dashed line. The short spikes late in training are Adam's steps overshooting a little; they do not change the trend. Saving the parameters from the best validation epoch, early stopping, would keep the generalising model. You will implement early-stopping logic as a problem in the model-design module.

> [!INTERVIEW]
> **"Adam or SGD?"** Adam (in practice AdamW) is the robust default: it converges quickly with little tuning and is standard for transformers and fine-tuning. Well-tuned SGD with momentum and a learning-rate schedule can match or beat it on some vision tasks and uses less memory (one buffer instead of two). Then explain AdamW: plain Adam's L2 term gets divided by the adaptive denominator, so decay is uneven; AdamW applies decay directly to the weights. Bonus: exclude biases and normalisation parameters from weight decay.

## Summary

- `torch.optim` optimisers take parameters and hyperparameters; `step()` applies updates using `.grad` and internal state; save `optimizer.state_dict()` in checkpoints.
- SGD uses noisy mini-batch gradients, cheap and good for generalisation.
- Momentum accumulates a velocity buffer that speeds travel along consistent directions; Nesterov adds a look-ahead correction.
- Adam keeps per-parameter averages of gradients and squared gradients, with bias correction, giving adaptive step sizes.
- AdamW decouples weight decay from the adaptive scaling and is the modern default.
- Split data into training, validation and test sets (by group or time when needed); evaluate in `eval()` mode under `no_grad()`.
- Diverging curves (training down, validation up) signal overfitting; keep the best validation checkpoint.

## Glossary

- **Optimiser**: the object that updates parameters from gradients.
- **Hyperparameter**: a setting you choose rather than learn.
- **Mini-batch / SGD**: a random subset of examples / gradient descent on mini-batch gradients.
- **Momentum / velocity buffer**: accumulating past gradients to keep moving in consistent directions.
- **Nesterov momentum**: momentum with a look-ahead correction.
- **Exponential moving average**: a running average where older values fade geometrically.
- **Adam**: an optimiser with per-parameter steps from first and second moment averages.
- **Bias correction**: dividing the averages by $1-\beta^t$ to undo their zero start.
- **Weight decay**: shrinking weights towards zero each step.
- **AdamW / decoupled weight decay**: Adam with weight decay applied directly to the weights.
- **Parameter group**: a subset of parameters with its own optimiser settings.
- **Training / validation / test set**: data for fitting / for tuning and monitoring / for the final report.
- **Overfitting / underfitting**: memorising training data / failing to fit even the training data.
- **Early stopping**: keeping the parameters from the epoch with the best validation score.
- **Group split**: keeping all samples from one person or source on the same side of a split.

## Check yourself

```quiz
[
  {"q": "What does momentum add to plain SGD?", "options": ["A running velocity that accumulates consistent gradient directions", "A separate learning rate per parameter", "Automatic learning-rate decay", "Gradient clipping"], "answer": 0,
   "explain": "Components that keep the same sign build up; oscillating ones cancel."},
  {"q": "Why does Adam divide by the square root of a running average of squared gradients?", "options": ["To give each parameter a step size adapted to its typical gradient magnitude", "To make gradients positive", "To implement weight decay", "To reduce memory use"], "answer": 0,
   "explain": "Parameters with large gradients take smaller steps and vice versa."},
  {"q": "What is the purpose of Adam's bias correction terms 1 − β^t?", "options": ["To undo the bias towards zero of averages initialised at zero", "To add L2 regularisation", "To clip large gradients", "To warm up the learning rate"], "answer": 0,
   "explain": "Early in training m and v are underestimates; dividing by 1 − β^t rescales them."},
  {"q": "How does AdamW differ from Adam with weight_decay set?", "options": ["AdamW shrinks weights directly instead of adding the decay term to the gradient", "AdamW has no momentum", "AdamW uses a fixed learning rate", "There is no difference"], "answer": 0,
   "explain": "In Adam the L2 term is divided by the adaptive denominator, making decay uneven."},
  {"q": "Training loss keeps decreasing while validation loss started increasing 20 epochs ago. What is happening?", "options": ["Overfitting", "Underfitting", "A learning rate that is too small", "Data leakage from validation to training"], "answer": 0,
   "explain": "The model is fitting training-set specifics; use early stopping, regularisation or more data."},
  {"q": "A dataset has 10 X-ray images per patient for 1,000 patients. How should you split it?", "options": ["By patient, so each patient's images are all in one split", "Randomly by image", "By image file size", "Put all images in training"], "answer": 0,
   "explain": "Otherwise the model can score well by recognising patients rather than the condition."},
  {"q": "Which must be saved to resume training with Adam exactly where you left off?", "options": ["Both model.state_dict() and optimizer.state_dict()", "Only model.state_dict()", "Only the learning rate", "Only the last batch"], "answer": 0,
   "explain": "The optimizer state holds the moment estimates and step count."},
  {"q": "Which parameters are commonly excluded from weight decay?", "options": ["Biases and normalisation-layer scales", "All convolution weights", "The first layer only", "The output layer only"], "answer": 0,
   "explain": "Decaying these 1-D parameters rarely helps and can hurt; parameter groups make the exclusion easy."}
]
```

> **Source:** Stevens, Antiga & Viehmann, *Deep Learning with PyTorch*, ch. 5 (optimizers, the `torch.optim` interface, training, validation and overfitting, splitting a dataset); PyTorch documentation, `torch.optim.SGD`, `torch.optim.Adam`, `torch.optim.AdamW`; Loshchilov & Hutter, "Decoupled Weight Decay Regularization" (2019).
