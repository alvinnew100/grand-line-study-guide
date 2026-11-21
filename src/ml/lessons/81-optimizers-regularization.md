# Optimisers and regularisation

> **Before this lesson:** read [Tensors, autograd and the training loop](#/lesson/ml/training-loop) first: this lesson replaces the plain SGD step of that loop with better optimisers and adds regularisation to it. Overfitting comes from [Generalisation, overfitting and k-NN](#/lesson/ml/generalization-knn), and the L2 (ridge) penalty from [Linear models](#/lesson/ml/linear-models). Gradient descent and the learning rate come from [Calculus, gradients and gradient descent](#/lesson/ml/calculus-optimization).

## In plain words

Two questions decide whether a neural network works. First, can training find weights with a low training loss at all? That is the job of the **optimiser**, the rule that turns gradients into weight updates. Second, do those weights work on new data, or has the network memorised its training set? That is the job of **regularisation**, any technique that improves performance on unseen data, even at the cost of a slightly worse fit to the training data.

An everyday picture for each. An optimiser is like a hiker descending a foggy valley who can only feel the slope underfoot. Plain gradient descent takes a step straight downhill each time; better optimisers remember which way they have been going (momentum) and take shorter steps on steep, slippery ground (adaptive step sizes). Regularisation is like a teacher who stops a student from memorising the answer key: mixing up the questions (data augmentation), covering some of the student's notes at random (dropout), or ending revision before the student starts memorising (early stopping).

Why this matters for a job: the choice between SGD, Adam and AdamW, the learning-rate schedule, and the regularisation recipe are decisions you make in every deep-learning project, and "your model overfits, what do you try?" and "what is the difference between Adam and AdamW?" are standard interview questions. Müller & Guido introduce the first of these ideas through `MLPClassifier`'s `alpha` (an L2 penalty) and its `solver` options (`adam`, `lbfgs`, `sgd`); this lesson shows how they work.

## 1. Stochastic gradient descent

Plain mini-batch stochastic gradient descent (SGD), from the previous lesson, moves every parameter a step against its gradient. Writing all parameters together as $\theta$ (theta), the learning rate as $\eta$ (eta), and the gradient of the loss on the current mini-batch as $g_t$:

$$\theta_{t+1} = \theta_t - \eta\, g_t,\qquad g_t = \nabla_\theta L_{\text{batch}}(\theta_t).$$

The subscript $t$ counts steps, and $\nabla_\theta$ means "the gradient with respect to all parameters". SGD has two weaknesses:

- **Ravines.** When the loss surface is much steeper in one direction than another, like a long narrow valley, SGD bounces from side to side across the steep direction and crawls along the shallow one. A single learning rate cannot suit both directions.
- **Noise.** Each mini-batch gradient is a noisy estimate of the gradient over the whole dataset.

A worked example of the ravine problem. Take the loss $L = \tfrac12(x^2 + 100y^2)$: 100 times steeper in $y$ than in $x$. Its gradient is $(x, 100y)$. One SGD step multiplies $y$ by $(1 - 100\eta)$, and if $100\eta > 2$ that factor is below −1 and $y$ grows every step, so training **diverges** (runs away to infinity). The learning rate must therefore stay below $2/100 = 0.02$. But then each step multiplies $x$ by only $(1 - \eta) \geq 0.98$, so progress along the valley floor is painfully slow: with $\eta = 0.018$, after 100 steps $x$ has only shrunk from 10 to $10 \times 0.982^{100} \approx 1.63$, leaving a loss of about $\tfrac12 \times 1.63^2 \approx 1.3$. The demo below confirms this number.

## 2. Momentum

**Momentum** keeps a running **velocity** $v$, a sum of past gradients in which older gradients count less and less, and moves along it:

$$v_{t+1} = \mu\,v_t + g_t,\qquad \theta_{t+1} = \theta_t - \eta\,v_{t+1}.$$

The factor $\mu$ (mu, usually 0.9) says how much of the old velocity survives each step. Picture a heavy ball rolling downhill. Gradient components that keep pointing the same way add up, so progress along the ravine floor speeds up. Components that flip sign from step to step cancel, so the side-to-side bouncing is damped.

Worked example: if the gradient is 1 at every step, the velocity grows $1, 1.9, 2.71, 3.44, \dots$ and approaches $1/(1-\mu) = 10$. So in a consistent direction momentum takes steps up to ten times larger than plain SGD. If instead the gradient alternates $+1, -1, +1, -1$, the velocity goes $1, -0.1, 0.91, -0.18, \dots$ and never builds up: it hovers around ±0.5 instead of growing towards 10. **Nesterov momentum** computes the gradient at the position the velocity is about to carry you to, a "look-ahead" that is often slightly better.

## 3. Adaptive learning rates: RMSProp and Adam

**RMSProp** gives every parameter its own step size. It keeps an **exponential moving average** of each parameter's squared gradient (a running average in which each new value gets weight $1-\rho$ and the old average keeps weight $\rho$), and divides the step by its square root:

$$s_t = \rho\,s_{t-1} + (1-\rho)\,g_t^2,\qquad \theta_{t+1} = \theta_t - \eta\,\frac{g_t}{\sqrt{s_t}+\epsilon}.$$

Here $\rho$ (rho) is typically 0.9 and $\epsilon$ (epsilon) is a tiny number that prevents division by zero. The effect: a parameter whose gradients are consistently large takes small steps, and a parameter whose gradients are small or rare takes relatively large ones. In the ravine, the steep $y$ direction is automatically slowed and the shallow $x$ direction sped up.

**Adam** (short for adaptive moment estimation) combines momentum with RMSProp and adds a bias correction. It keeps a moving average of the gradient, $m$ (the momentum part), and of the squared gradient, $v$ (the RMSProp part):

$$m_t = \beta_1 m_{t-1} + (1-\beta_1)g_t\qquad v_t = \beta_2 v_{t-1} + (1-\beta_2)g_t^2$$
$$\hat m_t = \frac{m_t}{1-\beta_1^t}\qquad \hat v_t = \frac{v_t}{1-\beta_2^t}\qquad \theta_t = \theta_{t-1} - \eta\,\frac{\hat m_t}{\sqrt{\hat v_t}+\epsilon}$$

The usual defaults are $\beta_1 = 0.9$, $\beta_2 = 0.999$, $\epsilon = 10^{-8}$ and $\eta = 10^{-3}$.

Why the **bias correction**? Both averages start at zero, so for the first few steps they are pulled towards zero. After one step, $m_1 = (1-\beta_1)g_1 = 0.1\,g_1$, only a tenth of the true gradient. Dividing by $1-\beta_1^1 = 0.1$ restores $g_1$. As $t$ grows, $\beta^t$ approaches 0 and the correction fades away.

A worked first step: suppose a parameter's first gradient is $g_1 = 4$. Then $m_1 = 0.4$ and $v_1 = 0.001 \times 16 = 0.016$. Corrected, $\hat m_1 = 0.4/0.1 = 4$ and $\hat v_1 = 0.016/0.001 = 16$. The step is $\eta \times 4/\sqrt{16} = \eta \times 1$. Had the gradient been 0.04 instead, the step would still be $\eta$. The very first Adam step moves every parameter by about $\eta$, whatever the size of its gradient, which is why Adam is relatively insensitive to the scale of the gradients.

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

**Reading this code line by line**

- `loss` and `grad` define the ravine from section 1 and its gradient. The starting point $(10, 1)$ has loss $\tfrac12(100 + 100) = 100$.
- `run` applies an optimiser for 100 steps. Each optimiser is a function taking the current parameters `p`, the gradient `g`, a dictionary `s` in which it can keep its running averages between steps, and the step number `t`. `s.get("v", 0)` reads a stored value, or 0 on the first step.
- `sgd`, `momentum`, `rmsprop` and `adam` are the four update rules above, written line for line from the formulas. Each has its own learning rate, chosen to work reasonably on this problem.
- The loop prints the loss each optimiser reaches.

Plain SGD ends at a loss of about 1.32, exactly the hand calculation: held back by the steep direction, it barely moves along the shallow one. Momentum reaches about 0.0015, Adam about 0.0015 and RMSProp about 0.41. Momentum and the adaptive methods get much further in the same number of steps. The problem *ml-adam-step* asks you to implement Adam's update.

### Which optimiser?

| optimiser | use it for | notes |
|---|---|---|
| SGD + momentum | convolutional networks for images | often generalises slightly better; needs a tuned learning rate and schedule |
| Adam | a robust default for most problems | converges fast with little tuning |
| **AdamW** | transformers and most modern deep learning | Adam with *decoupled* weight decay (section 5.1) |
| L-BFGS | small problems trained on the full dataset at once | scikit-learn's `lbfgs` solver; not suited to mini-batches |

This matches the book's advice for `MLPClassifier`: `adam` works well in most situations but is sensitive to the scaling of the data, `lbfgs` is robust but slow on large datasets, and `sgd` with momentum is what many deep-learning researchers use, at the cost of more settings to tune. (L-BFGS, "limited-memory Broyden–Fletcher–Goldfarb–Shanno", estimates the curvature of the loss from recent gradients to choose better steps.)

## 4. Learning-rate schedules

The learning rate is rarely kept constant during training. A **schedule** changes it step by step.

- **Warm-up**: start very small and grow linearly over the first few hundred or thousand steps. Early gradients are unreliable, and Adam's averages have not settled yet, so large early steps can wreck training.
- **Decay**: reduce the rate as training proceeds, so the parameters can settle into a minimum instead of bouncing around it. Common choices are step decay (divide by 10 at fixed epochs), **cosine annealing** (follow half a cosine wave from the full rate down to zero) and linear decay.
- `ReduceLROnPlateau`: cut the rate whenever the validation loss stops improving.

In words, the schedule below rises linearly for the first 100 steps, then follows a cosine curve down to zero by step 1,000. For a step $s$ after warm-up, with progress $q = (s - 100)/900$ running from 0 to 1, the rate is $\eta_{\max} \cdot \tfrac12(1 + \cos \pi q)$. Worked example: halfway through the decay, at step 550, $q = 0.5$, $\cos(\pi/2) = 0$, so the rate is half the maximum.

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

The printout shows the rate climbing from $10^{-5}$ at step 0 to the full $10^{-3}$ at step 99, holding near the top at first, reaching $5 \times 10^{-4}$ at step 550 as calculated, and falling to almost zero at step 999.

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

In PyTorch the schedule is a separate object: `OneCycleLR` warms up and then decays, and `scheduler.step()` advances it once per batch, after `optimizer.step()`. The `clip_grad_norm_` line is **gradient clipping**: if the length (norm) of the full gradient exceeds 1.0, it is scaled down to length 1.0, keeping its direction. Clipping is standard for recurrent networks and transformers, where an occasional huge gradient could otherwise wreck training in one step.

## 5. Regularisation: fighting overfitting

Large networks have enough parameters to memorise their training set. Regularisation is any technique that lowers the error on new data, possibly at the cost of a higher training error.

### 5.1 Weight decay (L2)

Add a penalty $\frac{\lambda}{2}\lVert w\rVert^2$ to the loss: $\lambda$ (lambda) times half the sum of all squared weights. Its gradient is $\lambda w$, so each step also pulls every weight a little towards zero. This is the `alpha` parameter of `MLPClassifier` and the same penalty as ridge regression. The book shows that raising `alpha` gives smoother decision boundaries.

Worked example: with $\lambda = 0.01$ and $\eta = 0.1$, the penalty's contribution to one SGD step is $-\eta \lambda w = -0.001\,w$: every weight shrinks by 0.1% per step, in addition to the normal update. That is why the technique is called **weight decay**.

With plain SGD, "add an L2 penalty to the loss" and "shrink the weights by a fixed fraction each step" are the same thing. With Adam they are not. The $\lambda w$ term becomes part of the gradient, so it gets divided by $\sqrt{\hat v}$, and weights with large gradients are regularised *less*. **AdamW** fixes this by applying the decay directly to the weights, outside the adaptive scaling:

$$\theta_t = \theta_{t-1} - \eta\left(\frac{\hat m_t}{\sqrt{\hat v_t}+\epsilon} + \lambda\,\theta_{t-1}\right).$$

Biases and the parameters of normalisation layers are usually excluded from weight decay.

### 5.2 Dropout

During training, **dropout** sets each activation (each unit's output) to zero with probability $p$, using a fresh random pattern for every sample at every step. The network cannot rely on any single unit, so it learns redundant, robust features. It also behaves like an **ensemble** (a combination of many models) of the many thinned sub-networks it samples.

To keep the expected value of each activation unchanged, the surviving activations are multiplied by $1/(1-p)$ during training. This is called **inverted dropout**. Worked example with $p = 0.5$: an activation of 1 becomes 0 or 2 with equal probability, and its average stays $0.5 \times 0 + 0.5 \times 2 = 1$. At test time dropout is switched off and nothing needs rescaling. That is why `model.eval()` matters.

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

`rng.rand(*h.shape)` draws a uniform random number between 0 and 1 for every activation; `>= p` keeps each one with probability $1-p$, giving True/False; dividing by `1 - p` turns True into 2 and False into 0. In training mode, two rows of ten 1s come out as a random mix of 0s and 2s. Averaged over a million activations the mean is 1.002, so the expected value is preserved. In evaluation mode the input passes through unchanged.

Typical dropout rates are 0.1 to 0.5. Dropout is used less in convolutional layers and widely in transformers.

### 5.3 Early stopping

**Early stopping** monitors the validation loss during training and **stops when it has not improved for a set number of epochs**, called the **patience**. The weights from the best epoch are kept. It costs nothing, and by limiting how far the weights can travel from their small starting values it has an effect similar to an L2 penalty. scikit-learn offers it as `early_stopping=True` in `MLPClassifier` and as `n_iter_no_change` in gradient boosting.

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

**Reading this code line by line**

- Only 60 noisy training points and a 64-unit hidden layer: a recipe for overfitting.
- `forward` and the gradient lines are the same network and backward pass as in the previous lesson's NumPy loop, here trained on the full training set at each step. `nll` ("negative log-likelihood") is the cross-entropy loss.
- After each update the code computes the validation loss `val`. If it beats the best so far by more than a tiny margin, it records the new best and resets the counter `wait`; otherwise it adds one to `wait`, and when `wait` reaches the patience of 200 it stops.

The training loss keeps falling (0.925, 0.451, 0.269 at epochs 10, 50 and 200) while the validation loss falls to its lowest point and then rises (0.892, 0.595, then 0.697 at epoch 200). That widening gap is overfitting. The loop stops at epoch 349 and reports that the best validation loss, 0.473, was at epoch 149; restoring the weights from that epoch would give the best model.

### 5.4 More data and data augmentation

More data is the most reliable regulariser. When you cannot collect more, **augment** what you have: create extra training examples by applying transformations that do not change the label. For images: random crops, flips and colour changes, or **mixup** (blending two images and their labels). For text: **back-translation** (translating to another language and back to get a paraphrase) and masking random words. For audio: shifts in time and pitch. Augmentation teaches the model the **invariances** you want, the changes it should ignore: a cat flipped left to right is still a cat.

### 5.5 Normalisation layers

**Batch normalisation** standardises each feature of a layer's output using the mean and variance of the current mini-batch, then applies a learned scale $\gamma$ (gamma) and shift $\beta$ (beta), so the network can undo the standardisation where that helps:

$$\hat x = \frac{x - \mu_{\text{batch}}}{\sqrt{\sigma^2_{\text{batch}} + \epsilon}},\qquad y = \gamma\hat x + \beta.$$

Worked example: one feature takes the values 2, 4 and 6 in a batch of three. The mean is 4 and the variance $\tfrac13(4 + 0 + 4) = 2.67$, so the standard deviation is 1.63 and the normalised values are $-1.22, 0, 1.22$. With $\gamma = 1$ and $\beta = 0$ these are the outputs.

Batch normalisation makes deep networks much easier to optimise, allows higher learning rates, and has a mild regularising effect, because each sample's output is perturbed by the statistics of whichever other samples share its batch. At test time it uses **running averages** of the mean and variance collected during training, so that a prediction does not depend on the rest of the batch. That is the second reason `model.eval()` matters.

**Layer normalisation** instead normalises across the features of each individual sample. It does not depend on the batch at all, which makes it the standard choice in transformers and recurrent networks.

```python-run
import numpy as np
rng = np.random.RandomState(0)
x = rng.randn(4, 3) * [1.0, 10.0, 100.0] + [0.0, 5.0, -50.0]     # a batch of 4 samples, 3 badly scaled features
bn = (x - x.mean(axis=0)) / np.sqrt(x.var(axis=0) + 1e-5)         # batch norm: statistics per feature, over the batch
ln = (x - x.mean(axis=1, keepdims=True)) / np.sqrt(x.var(axis=1, keepdims=True) + 1e-5)   # layer norm: per sample
print("batch norm -> per-feature mean:", bn.mean(axis=0).round(6), " std:", bn.std(axis=0).round(3))
print("layer norm -> per-sample mean: ", ln.mean(axis=1).round(6), " std:", ln.std(axis=1).round(3))
```

`x` is a batch of 4 samples with 3 features on wildly different scales. Batch norm computes the mean and variance down each column (`axis=0`, over the batch); layer norm computes them along each row (`axis=1`, over the features of one sample; `keepdims=True` keeps the shape so the subtraction lines up). The output confirms the difference: after batch norm each *feature* has mean 0 and standard deviation 1; after layer norm each *sample* does. (A `-0.` in the printout is a tiny negative number rounded to zero.)

### 5.6 Other tools

- **Smaller models**: fewer layers or units. The bluntest regulariser.
- **Label smoothing**: train towards targets such as 0.9 and 0.1 instead of 1 and 0, which discourages over-confident predictions.
- **Transfer learning**: start from weights pretrained on a large dataset and fine-tune them on your task. The pretrained features act as strong prior knowledge, which is why fine-tuning works with little data.
- **Ensembling**: average the predictions of several models, as random forests do.

## 6. Vanishing and exploding gradients

Backpropagation multiplies one factor per layer, each a **Jacobian**: the matrix of partial derivatives of a layer's outputs with respect to its inputs, saying how much each output changes when each input is nudged. If these factors mostly shrink vectors, the gradient becomes tiny by the time it reaches the early layers (**vanishing gradients**), and those layers stop learning. If they mostly stretch vectors, the gradient grows without limit (**exploding gradients**).

A worked example of vanishing: the sigmoid's slope is at most 0.25. Through 10 sigmoid layers, even in the best case the gradient is multiplied by $0.25^{10} \approx 10^{-6}$.

| remedy | how it helps |
|---|---|
| ReLU-family activations | slope exactly 1 for positive inputs (the sigmoid's is at most 0.25) |
| He / Xavier initialisation | keeps the size of the signal roughly constant through the layers |
| normalisation layers | re-centre and rescale activations at every layer |
| **residual (skip) connections** | $y = x + F(x)$: the block's input is added to its output, giving the gradient a direct path around each block |
| gradient clipping | caps exploding gradients |
| LSTM / GRU gating | an additive memory path for recurrent networks (lesson 82) |

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

**Reading this code line by line**

- `gradient_norm_at_first_layer` imitates the backward pass through 30 layers of width 64. Starting from a gradient of all ones at the top, each layer multiplies by the transposed weight matrix `W.T` (random, with spread `scale / sqrt(width)`) and then by the activation's slope at random inputs, exactly what the chain rule does.
- `sig` is the sigmoid's slope, $\sigma(a)(1 - \sigma(a))$; `relu` is ReLU's slope, 1 for positive inputs and 0 otherwise.
- `np.linalg.norm(g)` measures the size of the gradient that reaches the first layer.

With sigmoid layers the gradient arrives with a size of about $4 \times 10^{-20}$: it has vanished, and the first layers would never learn. With ReLU and He scaling ($\sqrt{2}$) it stays around 1.8. With weights three times too large it explodes to about $4 \times 10^{14}$.

> [!INTERVIEW]
> **"Your model overfits. What do you try, in order?"** (1) Check for leakage and confirm the gap between training and validation scores is real. (2) Get more data, or augment. (3) Add weight decay and dropout. (4) Stop early on the validation loss. (5) Reduce capacity, or start from a pretrained model. (6) Ensemble. Be ready to explain *how* each works: weight decay as a preference for small weights (equivalently, a Gaussian prior on them), dropout as an implicit ensemble with inverted scaling, and the different behaviour of dropout and batch norm in training and evaluation mode. A common follow-up is Adam versus AdamW: in AdamW the decay is decoupled from the adaptive gradient scaling.

## Summary

- SGD struggles with ravines and must use a learning rate small enough for the steepest direction. Momentum averages gradients; RMSProp and Adam scale the step per parameter. Adam = momentum + RMSProp + bias correction.
- AdamW decouples weight decay and is the default for transformers. SGD with momentum is still strong for image models.
- Use warm-up and decay schedules, and gradient clipping for sequence models.
- Regularise with weight decay, dropout (inverted, off at evaluation time), early stopping, augmentation and normalisation.
- Vanishing and exploding gradients are tamed by ReLU, good initialisation, normalisation and residual connections.

## Glossary

- **Optimiser**: the rule that turns gradients into parameter updates.
- **Regularisation**: any technique that improves performance on new data, possibly at the cost of training fit.
- **Ravine**: a loss surface much steeper in some directions than others.
- **Diverge**: grow without limit instead of settling down.
- **Momentum / velocity**: moving along a decaying sum of past gradients / that sum.
- **Exponential moving average**: a running average in which older values count geometrically less.
- **RMSProp**: dividing each parameter's step by the root of its average squared gradient.
- **Adam / bias correction**: momentum plus RMSProp / rescaling that removes the pull towards zero in early steps.
- **Learning-rate schedule (warm-up, cosine annealing)**: changing the step size during training.
- **Gradient clipping**: shrinking a gradient whose norm exceeds a threshold.
- **Weight decay (L2) / AdamW**: shrinking weights towards zero / Adam with the decay applied outside the adaptive scaling.
- **Dropout / inverted dropout**: randomly zeroing activations in training / rescaling survivors by 1/(1−p).
- **Ensemble**: a combination of several models' predictions.
- **Early stopping / patience**: stopping when validation stops improving / how many epochs to wait.
- **Data augmentation / invariance**: label-preserving transformations of training data / a change the model should ignore.
- **Batch / layer normalisation**: standardising each feature over the batch / each sample over its features.
- **Jacobian**: the matrix of partial derivatives of a layer's outputs with respect to its inputs.
- **Vanishing / exploding gradients**: gradients shrinking to nothing / growing without limit through many layers.
- **Residual (skip) connection**: adding a block's input to its output.

## Check yourself

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
