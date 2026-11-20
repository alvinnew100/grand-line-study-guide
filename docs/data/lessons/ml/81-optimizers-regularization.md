# Optimisers and regularisation

Two questions decide whether a neural network works. Can the optimiser find parameters with a low training
loss? And do those parameters generalise? This lesson covers the tools for both. For optimisation: SGD,
momentum, RMSProp, Adam and learning-rate schedules. For generalisation: weight decay, dropout, early
stopping, data augmentation and normalisation layers. Müller & Guido introduce the first of these ideas
through `MLPClassifier`'s `alpha` (L2 penalty) and its `solver` choice (`adam`, `lbfgs`, `sgd`). Here we
look at how they work.

## 1. Stochastic gradient descent

Plain mini-batch SGD updates each parameter against its gradient:

$$\theta_{t+1} = \theta_t - \eta\, g_t,\qquad g_t = \nabla_\theta L_{\text{batch}}(\theta_t).$$

It has two weaknesses:

- **Ravines.** When the loss surface is much steeper in one direction than another, SGD bounces across the
  steep direction and crawls along the shallow one. A single learning rate cannot suit both.
- **Noise.** Each mini-batch gradient is a noisy estimate of the true gradient.

## 2. Momentum

Momentum keeps a running **velocity**, an exponentially decaying sum of past gradients, and moves along
it:

$$v_{t+1} = \mu\,v_t + g_t,\qquad \theta_{t+1} = \theta_t - \eta\,v_{t+1}.$$

Think of a heavy ball rolling downhill. Components of the gradient that keep pointing the same way
accumulate, so progress along the ravine speeds up. Components that flip sign cancel, so the bouncing is
damped. The usual value is $\mu = 0.9$, which makes the effective step up to $1/(1-\mu) = 10$ times
larger in consistent directions. **Nesterov momentum** evaluates the gradient at the look-ahead position
and is often slightly better.

## 3. Adaptive learning rates: RMSProp and Adam

**RMSProp** gives every parameter its own step size. It keeps a moving average of the squared gradient
and divides by its square root:

$$s_t = \rho\,s_{t-1} + (1-\rho)\,g_t^2,\qquad \theta_{t+1} = \theta_t - \eta\,\frac{g_t}{\sqrt{s_t}+\epsilon}.$$

Parameters with consistently large gradients take smaller steps. Parameters with small or rare gradients
take larger ones.

**Adam** combines momentum with RMSProp, and adds a bias correction:

$$m_t = \beta_1 m_{t-1} + (1-\beta_1)g_t\qquad v_t = \beta_2 v_{t-1} + (1-\beta_2)g_t^2$$
$$\hat m_t = \frac{m_t}{1-\beta_1^t}\qquad \hat v_t = \frac{v_t}{1-\beta_2^t}\qquad \theta_t = \theta_{t-1} - \eta\,\frac{\hat m_t}{\sqrt{\hat v_t}+\epsilon}$$

The defaults are $\beta_1 = 0.9$, $\beta_2 = 0.999$, $\epsilon = 10^{-8}$ and $\eta = 10^{-3}$.

Why the **bias correction**? Both averages start at zero, so in the first steps they are biased towards
zero. After one step $m_1 = (1-\beta_1)g_1 = 0.1\,g_1$. Dividing by $1-\beta_1^1 = 0.1$ restores $g_1$.
The correction fades as $t$ grows. A useful consequence is that the very first Adam step moves every
parameter by about $\eta$, whatever the size of its gradient.

```python-run
import numpy as np

def loss(p):                      # a ravine: 100 times steeper in y than in x
    return 0.5 * (p[0] ** 2 + 100 * p[1] ** 2)
def grad(p):
    return np.array([p[0], 100 * p[1]])

def run(optimizer, steps=100):
    p = np.array([10.0, 1.0]); state = {}
    for t in range(1, steps + 1):
        p = optimizer(p, grad(p), state, t)
    return loss(p)

def sgd(p, g, s, t, lr=0.018):                       # must stay below 2/100 or it diverges
    return p - lr * g
def momentum(p, g, s, t, lr=0.018, mu=0.9):
    s["v"] = mu * s.get("v", 0) + g
    return p - lr * s["v"]
def rmsprop(p, g, s, t, lr=0.1, rho=0.9, eps=1e-8):
    s["s"] = rho * s.get("s", 0) + (1 - rho) * g * g
    return p - lr * g / (np.sqrt(s["s"]) + eps)
def adam(p, g, s, t, lr=0.3, b1=0.9, b2=0.999, eps=1e-8):
    s["m"] = b1 * s.get("m", 0) + (1 - b1) * g
    s["v"] = b2 * s.get("v", 0) + (1 - b2) * g * g
    return p - lr * (s["m"] / (1 - b1 ** t)) / (np.sqrt(s["v"] / (1 - b2 ** t)) + eps)

print("starting loss:", loss(np.array([10.0, 1.0])))
for name, opt in [("SGD", sgd), ("SGD + momentum", momentum), ("RMSProp", rmsprop), ("Adam", adam)]:
    print(f"{name:15s} loss after 100 steps: {run(opt):.3e}")
```

Plain SGD is held back by the steep direction: its learning rate must stay tiny, so the shallow direction
barely moves. Momentum and the adaptive methods get much further in the same number of steps. Problem
*ml-adam-step* asks you to implement Adam's update.

### Which optimiser?

| optimiser | use it for | notes |
|---|---|---|
| SGD + momentum | convolutional networks for vision | often generalises slightly better; needs a tuned learning rate and schedule |
| Adam | a robust default for most problems | fast convergence with little tuning |
| **AdamW** | transformers and most modern deep learning | Adam with *decoupled* weight decay (below) |
| L-BFGS | small, full-batch problems | scikit-learn's `lbfgs` solver; not for mini-batches |

This matches the book's advice for `MLPClassifier`: `adam` works well in most situations but is sensitive
to the scaling of the data, `lbfgs` is quite robust but slow on large datasets, and `sgd` with momentum
is what many deep-learning researchers use, at the cost of more parameters to set.

## 4. Learning-rate schedules

The learning rate is rarely kept constant.

- **Warm-up**: start very small and grow linearly over the first few hundred or thousand steps. Early
  gradients are unreliable, and Adam's variance estimates are not yet settled.
- **Decay**: reduce the rate as training goes on, so the parameters can settle into a minimum. Common
  choices are step decay (divide by 10 at fixed epochs), **cosine annealing** and linear decay.
- `ReduceLROnPlateau`: cut the rate when the validation loss stops improving.

```python-run
import numpy as np
def lr_at(step, base=1e-3, warmup=100, total=1000):
    if step < warmup:
        return base * (step + 1) / warmup                      # linear warm-up
    progress = (step - warmup) / (total - warmup)
    return base * 0.5 * (1 + np.cos(np.pi * progress))         # cosine decay to zero
for s in [0, 50, 99, 100, 300, 550, 800, 999]:
    print(f"step {s:4d}: learning rate = {lr_at(s):.2e}")
```

```python
optimizer = torch.optim.AdamW(model.parameters(), lr=3e-4, weight_decay=0.01)
scheduler = torch.optim.lr_scheduler.OneCycleLR(optimizer, max_lr=3e-4, total_steps=n_steps)
for xb, yb in loader:
    optimizer.zero_grad()
    loss = loss_fn(model(xb), yb)
    loss.backward()
    torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)   # guard against exploding gradients
    optimizer.step()
    scheduler.step()
```

**Gradient clipping** rescales the gradient when its norm exceeds a threshold. It is standard for
recurrent networks and transformers, where an occasional huge gradient can wreck training.

## 5. Regularisation: fighting overfitting

Large networks can memorise their training set. Regularisation is any technique that lowers the test
error, possibly at the cost of a higher training error.

### 5.1 Weight decay (L2)

Add $\frac{\lambda}{2}\lVert w\rVert^2$ to the loss, which adds $\lambda w$ to the gradient. This is the
`alpha` parameter of `MLPClassifier` and the ridge penalty of linear models. The book shows that raising
`alpha` gives smoother decision boundaries.

With plain SGD, L2 regularisation and "shrink the weights by a factor each step" are the same thing. With
Adam they are not. The $\lambda w$ term gets divided by $\sqrt{\hat v}$, so weights with large gradients
are regularised *less*. **AdamW** fixes this by applying the decay directly to the weights, outside the
adaptive update:

$$\theta_t = \theta_{t-1} - \eta\left(\frac{\hat m_t}{\sqrt{\hat v_t}+\epsilon} + \lambda\,\theta_{t-1}\right).$$

Biases and normalisation parameters are usually excluded from weight decay.

### 5.2 Dropout

During training, **randomly set each activation to zero with probability $p$**, a fresh random mask for
every sample and every step. The network cannot rely on any single unit, so it learns redundant, robust
features. It also behaves like an ensemble of many thinned sub-networks.

To keep the expected activation unchanged, the surviving activations are scaled by $1/(1-p)$ during
training. This is **inverted dropout**. At test time dropout is switched off and nothing needs rescaling.
This is why `model.eval()` matters.

```python-run
import numpy as np
rng = np.random.RandomState(0)

def dropout(h, p, training):
    if not training or p == 0:
        return h                                    # evaluation mode: identity
    mask = (rng.rand(*h.shape) >= p) / (1 - p)      # inverted dropout: rescale the survivors
    return h * mask

h = np.ones((2, 10))
out = dropout(h, p=0.5, training=True)
print("training output:\n", out)
print("mean activation in training:", dropout(np.ones((1000, 1000)), 0.5, True).mean().round(3), "(expected value preserved)")
print("evaluation output:", dropout(h, 0.5, False)[0])
```

Typical rates are 0.1 to 0.5. Dropout is used less in convolutional layers and widely in transformers.

### 5.3 Early stopping

Monitor the validation loss during training and **stop when it has not improved for a set number of
epochs** (the *patience*). Keep the weights from the best epoch. It costs nothing and limits how far the
weights can travel from their initial values, which has an effect similar to L2. scikit-learn exposes it
as `early_stopping=True` in `MLPClassifier` and as `n_iter_no_change` in gradient boosting.

```python-run
import numpy as np
from sklearn.datasets import make_moons
from sklearn.model_selection import train_test_split

X, y = make_moons(n_samples=120, noise=0.4, random_state=1)
X_tr, X_va, y_tr, y_va = train_test_split(X, y, test_size=0.5, random_state=0)
rng = np.random.RandomState(0)
W1 = rng.randn(2, 64) * 2; b1 = rng.randn(64); W2 = rng.randn(64, 2) * 0.1; b2 = np.zeros(2)

def forward(X):
    A = X @ W1 + b1; H = np.maximum(0, A); Z = H @ W2 + b2
    Z = Z - Z.max(1, keepdims=True); P = np.exp(Z); P /= P.sum(1, keepdims=True)
    return A, H, P
def nll(P, y):
    return -np.log(P[np.arange(len(y)), y] + 1e-12).mean()

lr, patience = 0.3, 200
best, best_epoch, wait = np.inf, 0, 0
for epoch in range(1, 3001):
    A, H, P = forward(X_tr)
    dZ = P.copy(); dZ[np.arange(len(y_tr)), y_tr] -= 1; dZ /= len(y_tr)
    dA = (dZ @ W2.T) * (A > 0)
    W2 -= lr * H.T @ dZ; b2 -= lr * dZ.sum(0); W1 -= lr * X_tr.T @ dA; b1 -= lr * dA.sum(0)
    val = nll(forward(X_va)[2], y_va)
    if epoch in (10, 50, 200, 500, 1000):
        print(f"epoch {epoch:4d}: train loss {nll(P, y_tr):.3f}  validation loss {val:.3f}")
    if val < best - 1e-4:
        best, best_epoch, wait = val, epoch, 0          # a real loop would also save the weights here
    else:
        wait += 1
        if wait >= patience:
            print(f"early stop at epoch {epoch}: the best validation loss {best:.3f} was at epoch {best_epoch}")
            break
```

The training loss keeps falling while the validation loss bottoms out and starts to rise. That gap is
overfitting, and early stopping halts training near the best point.

### 5.4 More data and data augmentation

More data is the most reliable regulariser. When you can't collect more, **augment** what you have with
label-preserving transformations. For images: random crops, flips, colour jitter, mixup. For text: back-
translation and token masking. For audio: time and pitch shifts. Augmentation builds the invariances you
want into the model.

### 5.5 Normalisation layers

**Batch normalisation** standardises each feature of a layer's activations using the mean and variance of
the current mini-batch, then applies a learned scale $\gamma$ and shift $\beta$:

$$\hat x = \frac{x - \mu_{\text{batch}}}{\sqrt{\sigma^2_{\text{batch}} + \epsilon}},\qquad y = \gamma\hat x + \beta.$$

It makes deep networks much easier to optimise, allows higher learning rates, and has a mild regularising
effect, because every sample is perturbed by the statistics of its batch. At test time it uses **running
averages** collected during training. That is the second reason `model.eval()` matters.

**Layer normalisation** normalises across the features of each individual sample. It does not depend on
the batch, which makes it the standard choice in transformers and recurrent networks.

```python-run
import numpy as np
rng = np.random.RandomState(0)
x = rng.randn(4, 3) * [1.0, 10.0, 100.0] + [0.0, 5.0, -50.0]     # a batch of 4 samples, 3 badly scaled features
bn = (x - x.mean(axis=0)) / np.sqrt(x.var(axis=0) + 1e-5)         # batch norm: statistics per feature, over the batch
ln = (x - x.mean(axis=1, keepdims=True)) / np.sqrt(x.var(axis=1, keepdims=True) + 1e-5)   # layer norm: per sample
print("batch norm -> per-feature mean:", bn.mean(axis=0).round(6), " std:", bn.std(axis=0).round(3))
print("layer norm -> per-sample mean: ", ln.mean(axis=1).round(6), " std:", ln.std(axis=1).round(3))
```

### 5.6 Other tools

- **Smaller models**: fewer layers or units. This is the bluntest regulariser.
- **Label smoothing**: train towards targets like 0.9/0.1 instead of 1/0. It discourages over-confident
  predictions.
- **Transfer learning**: start from pretrained weights and fine-tune. The pretrained features act as a
  strong prior, which is why fine-tuning works with little data.
- **Ensembling**: average several models, as random forests do.

## 6. Vanishing and exploding gradients

Backpropagation multiplies many Jacobians together. If the factors are mostly below 1, the gradient
shrinks towards zero in the early layers (**vanishing**), and those layers stop learning. If they are
above 1, it grows without bound (**exploding**).

| remedy | how it helps |
|---|---|
| ReLU-family activations | derivative is 1 for positive inputs (sigmoid's is at most 0.25) |
| He / Xavier initialisation | keeps the variance of the signal constant through the layers |
| normalisation layers | re-centre and rescale activations at every layer |
| **residual (skip) connections** | $y = x + F(x)$ gives the gradient a direct path around each block |
| gradient clipping | caps exploding gradients |
| LSTM / GRU gating | additive memory path for recurrent networks |

```python-run
import numpy as np
rng = np.random.RandomState(0)
def gradient_norm_at_first_layer(activation_grad, depth=30, width=64, scale=1.0):
    g = np.ones(width)
    for _ in range(depth):
        W = rng.randn(width, width) * scale / np.sqrt(width)
        g = (W.T @ g) * activation_grad(rng.randn(width))
    return np.linalg.norm(g)
sig = lambda a: (1 / (1 + np.exp(-a))) * (1 - 1 / (1 + np.exp(-a)))
relu = lambda a: (a > 0).astype(float)
print(f"30 sigmoid layers: gradient norm = {gradient_norm_at_first_layer(sig):.2e}   (vanished)")
print(f"30 ReLU layers, He init: gradient norm = {gradient_norm_at_first_layer(relu, scale=np.sqrt(2)):.2e}")
print(f"30 ReLU layers, weights 3x too large: {gradient_norm_at_first_layer(relu, scale=3 * np.sqrt(2)):.2e}   (exploded)")
```

> [!INTERVIEW]
> **"Your model overfits. What do you try, in order?"** (1) Check for leakage and confirm the gap between
> training and validation is real. (2) Get more data, or augment. (3) Add weight decay, and dropout.
> (4) Stop early on the validation loss. (5) Reduce capacity, or start from a pretrained model.
> (6) Ensemble. Be ready to explain *how* each works: weight decay as a Gaussian prior, dropout as an
> implicit ensemble with inverted scaling, and the different behaviour of dropout and batch norm in
> training and evaluation mode. A common follow-up is Adam versus AdamW: in AdamW the decay is decoupled
> from the adaptive gradient scaling.

## Summary

- SGD struggles with ravines. Momentum averages gradients, and RMSProp and Adam scale the step per
  parameter. Adam = momentum + RMSProp + bias correction.
- AdamW decouples weight decay and is the default for transformers. SGD with momentum is still strong in
  vision.
- Use warm-up and decay schedules, and gradient clipping for sequence models.
- Regularise with weight decay, dropout (inverted, off at evaluation time), early stopping, augmentation
  and normalisation.
- Vanishing and exploding gradients are tamed by ReLU, good initialisation, normalisation and residual
  connections.

```quiz
[
  {"q": "What does momentum add to plain SGD?", "options": ["A velocity that accumulates past gradients, speeding up consistent directions and damping oscillations", "A per-parameter learning rate", "A penalty on large weights", "Random noise in the gradient"], "answer": 0,
   "explain": "Gradients that keep the same sign add up; those that flip sign cancel."},
  {"q": "Why does Adam apply bias correction to its moment estimates?", "options": ["They are initialised at zero, so early estimates are biased towards zero", "To add weight decay", "To make the learning rate decay", "To avoid division by zero"], "answer": 0,
   "explain": "Dividing by (1 − β^t) compensates for the zero initialisation; the effect vanishes as t grows."},
  {"q": "How does AdamW differ from Adam with an L2 penalty added to the loss?", "options": ["Weight decay is applied directly to the weights instead of passing through the adaptive gradient scaling", "It uses no momentum", "It removes bias correction", "It uses a fixed learning rate per layer"], "answer": 0,
   "explain": "In plain Adam the λw term is divided by sqrt(v), so heavily updated weights are decayed less."},
  {"q": "With inverted dropout at rate p = 0.5, a surviving activation during training is…", "options": ["multiplied by 2", "multiplied by 0.5", "left unchanged", "set to its mean"], "answer": 0,
   "explain": "Scaling by 1/(1 − p) keeps the expected activation the same, so nothing needs changing at test time."},
  {"q": "What does early stopping monitor?", "options": ["The validation loss (or metric), stopping when it no longer improves", "The training loss, stopping when it reaches zero", "The learning rate", "The number of parameters"], "answer": 0,
   "explain": "Training loss keeps falling when overfitting; validation performance shows when generalisation stops improving."},
  {"q": "At evaluation time, batch normalisation uses…", "options": ["running averages of mean and variance collected during training", "the statistics of the current test batch", "no normalisation at all", "the statistics of the first training batch only"], "answer": 0,
   "explain": "Predictions must not depend on which other samples happen to be in the batch."},
  {"q": "Which of these helps against vanishing gradients in very deep networks?", "options": ["Residual (skip) connections", "Sigmoid activations in every layer", "A larger batch size", "Removing the bias terms"], "answer": 0,
   "explain": "The identity path lets gradients flow directly to earlier layers."},
  {"q": "Why is learning-rate warm-up used?", "options": ["Early gradients and Adam's statistics are unreliable, so large initial steps can destabilise training", "It makes the final learning rate larger", "It replaces weight decay", "It is required by the chain rule"], "answer": 0,
   "explain": "Starting small and ramping up avoids divergence in the first steps, especially for transformers."}
]
```

> **Source:** Müller & Guido, *Introduction to Machine Learning with Python*, ch. 2 ("Neural Networks": tuning, `alpha` regularisation, estimating complexity, the `solver` choices); Goodfellow, Bengio & Courville, *Deep Learning*, ch. 7 (regularisation) and ch. 8 (optimisation); Kingma & Ba, "Adam: A Method for Stochastic Optimization"; Loshchilov & Hutter, "Decoupled Weight Decay Regularization"; PyTorch documentation, `torch.optim`.
