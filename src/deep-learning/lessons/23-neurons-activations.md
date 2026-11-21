# Neurons, layers and activation functions

> **Before this lesson:** you need the linear model, loss, gradients and gradient descent from [Learning as parameter estimation](#/lesson/deep-learning/learning-from-data), and matrix multiplication with broadcasting from [Tensors](#/lesson/deep-learning/tensors-basics). The chain rule from [Autograd in depth](#/lesson/deep-learning/autograd) explains why activation slopes matter.

## In plain words

An **artificial neuron** (also called a **unit**) is the smallest building block of a neural network. It takes several input numbers, multiplies each by its own weight, adds them up together with a bias, and passes the total through a fixed bend-or-squash rule called an **activation function**. A **layer** is many neurons side by side, each looking at the same inputs with its own weights. A **network** stacks layers, feeding each layer's outputs into the next.

Picture a panel of judges at a talent show. Each judge (neuron) weighs the performance features differently: one cares most about singing, another about stage presence. Each produces a score, but only scores above some threshold count as enthusiasm (the activation). A second panel then reads the first panel's verdicts and forms a higher-level opinion. Stack enough panels and the final verdict can depend on the performance in remarkably subtle ways.

Why it matters for a job: activation functions control whether gradients flow through deep networks, so they decide whether a model trains at all. Interviewers regularly ask "why do we need non-linearities?", "why ReLU rather than sigmoid?", "what is a dead ReLU?", "why do transformers use GELU?". This lesson answers each with a runnable demonstration.

## 1. One neuron

With inputs $x_1, \ldots, x_n$, weights $w_1, \ldots, w_n$, bias $b$ and activation $f$, a neuron computes

$$o = f\left(\sum_{i=1}^{n} w_i x_i + b\right) = f(\mathbf{w} \cdot \mathbf{x} + b)$$

The part inside the brackets is a **pre-activation** (a linear score); $f$ turns it into the neuron's output. Without $f$, a neuron is the linear model from the previous lessons. With $f$, it becomes a building block that can bend.

A **layer** of $m$ neurons uses a weight matrix $W$ of shape $(m, n)$, one row per neuron, and a bias vector of length $m$. For a batch of inputs $X$ with shape $(\text{batch}, n)$, the whole layer is one matrix product: $f(X W^\top + b)$, of shape $(\text{batch}, m)$. This is exactly `nn.Linear(n, m)` followed by an activation module.

## 2. Why non-linearity is essential

Stacking linear layers without activations gains nothing. Two layers compute $W_2(W_1 x + b_1) + b_2 = (W_2 W_1) x + (W_2 b_1 + b_2)$, which is again a single linear layer with weight $W_2 W_1$. A hundred linear layers in a row still draw only straight lines (flat planes in higher dimensions).

With a non-linear activation between layers, each hidden neuron contributes a "bend", and the network's output becomes a sum of bent pieces. For ReLU, $f(z) = \max(0, z)$, every hidden unit is a hinge: zero on one side of a line, rising linearly on the other. A sum of hinges is a **piecewise-linear** function: straight segments joined at corners. With enough hinges, piecewise-linear functions can approximate any reasonable curve as closely as you like. This is the content of the **universal approximation theorem**: a network with one hidden layer and a suitable non-linearity can approximate any continuous function on a bounded region to any accuracy, given enough hidden units. The theorem says nothing about how many units are needed or whether gradient descent will find them; depth usually makes the approximation far more efficient.

The demo builds that intuition directly. We pick 30 hinge positions at random (fixed first-layer weights), and solve for the output-layer weights by least squares, which finds the best combination of hinges to match a wiggly target.

```python-run
import numpy as np

rng = np.random.default_rng(0)
x = np.linspace(-3, 3, 200)[:, None]                     # 200 inputs, one feature
target = np.sin(2 * x[:, 0]) + 0.3 * x[:, 0]             # a curve no straight line can follow

def hidden_layer(x, n_units):
    W1 = rng.choice([-1.0, 1.0], size=(1, n_units))       # each hinge faces left or right
    b1 = rng.uniform(-3, 3, size=n_units)                 # where the hinge's corner sits
    return np.maximum(x @ W1 + b1, 0)                     # ReLU: (200, n_units)

for n_units in (0, 3, 10, 30):
    H = hidden_layer(x, n_units) if n_units else np.zeros((200, 0))
    A = np.hstack([H, x, np.ones((200, 1))])              # hinges + a linear part + bias
    w2, *_ = np.linalg.lstsq(A, target, rcond=None)       # best output weights
    err = np.sqrt(((A @ w2 - target) ** 2).mean())
    print(f"{n_units:3d} hidden ReLU units -> root-mean-square error {err:.4f}")
```

**Reading the result**

- With 0 hidden units the model is linear and cannot follow the sine wave; the error stays large.
- Each added hinge lets the fitted line change slope at one more place; with 30 hinges the error is a small fraction of what it was.
- Real training adjusts the hinge positions (first-layer weights and biases) too, which is far more efficient than placing them at random.

## 3. The activation function zoo

| activation | formula | output range | slope (derivative) | where used |
|---|---|---|---|---|
| identity | $z$ | any | 1 | regression output layers |
| sigmoid | $\sigma(z) = \frac{1}{1+e^{-z}}$ | (0, 1) | $\sigma(z)(1-\sigma(z))$, at most 0.25 | binary-probability outputs, gates in LSTMs |
| tanh | $\frac{e^z - e^{-z}}{e^z + e^{-z}}$ | (−1, 1) | $1 - \tanh^2 z$, at most 1 | recurrent networks, some older models |
| ReLU | $\max(0, z)$ | [0, ∞) | 0 for $z<0$, 1 for $z>0$ | the default for convnets and MLPs |
| LeakyReLU | $z$ if $z>0$ else $\alpha z$ ($\alpha$ about 0.01) | any | 1 or $\alpha$ | avoiding dead units |
| GELU | $z\,\Phi(z)$, $\Phi$ the normal CDF | about [−0.17, ∞) | smooth | transformers (BERT, GPT families) |
| SiLU / Swish | $z\,\sigma(z)$ | about [−0.28, ∞) | smooth | modern convnets, LLaMA-style feed-forward blocks |
| softplus | $\ln(1 + e^z)$ | (0, ∞) | $\sigma(z)$ | smooth ReLU; forcing positive outputs |

Some properties to know by name:

- **Saturation**: sigmoid and tanh flatten out for large positive or negative inputs, so their slope approaches zero there. A saturated unit passes almost no gradient back.
- **Zero-centred**: tanh outputs are centred on 0; sigmoid outputs are always positive, which makes the next layer's gradient updates all share a sign and slows learning a little.
- **Sparsity**: ReLU outputs exact zeros for half its input range, so many units are inactive for a given input, which is computationally cheap and often helpful.
- **Dead ReLU**: a unit whose pre-activation is negative for every input outputs 0 always, receives zero gradient and never recovers. Too-high learning rates or bad initialisation can kill many units. LeakyReLU, GELU and SiLU keep a small slope for negative inputs.
- **Smoothness**: GELU and SiLU are smooth curves, which tends to help optimisation in very deep models; they cost slightly more to compute.

The demo evaluates each activation and checks its analytic slope against a finite difference, a habit worth keeping whenever you write a derivative by hand.

```python-run
import math
import numpy as np

erf = np.vectorize(math.erf)
sigmoid = lambda z: 1 / (1 + np.exp(-z))
acts = {
    "sigmoid":   (sigmoid,                               lambda z: sigmoid(z) * (1 - sigmoid(z))),
    "tanh":      (np.tanh,                               lambda z: 1 - np.tanh(z) ** 2),
    "relu":      (lambda z: np.maximum(z, 0),            lambda z: (z > 0).astype(float)),
    "leaky_relu":(lambda z: np.where(z > 0, z, 0.01 * z), lambda z: np.where(z > 0, 1.0, 0.01)),
    "gelu":      (lambda z: z * 0.5 * (1 + erf(z / math.sqrt(2))),
                  lambda z: 0.5 * (1 + erf(z / math.sqrt(2))) + z * np.exp(-z * z / 2) / math.sqrt(2 * math.pi)),
    "silu":      (lambda z: z * sigmoid(z),              lambda z: sigmoid(z) * (1 + z * (1 - sigmoid(z)))),
    "softplus":  (lambda z: np.log1p(np.exp(z)),         sigmoid),
}
z = np.array([-4.0, -1.0, -0.1, 0.5, 2.0, 6.0])
print("z:          ", z)
for name, (f, df) in acts.items():
    eps = 1e-5
    numeric = (f(z + eps) - f(z - eps)) / (2 * eps)
    ok = np.allclose(numeric, df(z), atol=1e-6)
    print(f"{name:11s} f(z) = {np.round(f(z), 3)}   slope ok: {ok}")
print("sigmoid slope at 0 (its maximum):", sigmoid(0.0) * (1 - sigmoid(0.0)))
```

## 4. Why ReLU replaced sigmoid in hidden layers

During backpropagation, the gradient reaching an early layer is a product of one factor per layer above it, and each factor includes the activation's slope. The sigmoid's slope is at most 0.25. Ten sigmoid layers multiply ten numbers no larger than 0.25, which shrinks the gradient by a factor of at least $0.25^{10} \approx 10^{-6}$: the early layers barely learn. This is the **vanishing gradient problem**. ReLU's slope is exactly 1 for active units, so it passes gradients through unchanged (gated by whether the unit is on).

```python-run
import numpy as np

rng = np.random.default_rng(1)
sigmoid = lambda z: 1 / (1 + np.exp(-z))

def gradient_reaching_layer_1(act, dact, depth, width=64):
    """Forward through `depth` layers, then push a gradient of ones back and report its size."""
    x = rng.normal(size=(256, width))
    Ws, zs = [], []
    for _ in range(depth):
        W = rng.normal(0, np.sqrt(2.0 / width) if act is relu else np.sqrt(1.0 / width), (width, width))
        z = x @ W
        Ws.append(W); zs.append(z)
        x = act(z)
    g = np.ones_like(x)
    for W, z in zip(reversed(Ws), reversed(zs)):
        g = (g * dact(z)) @ W.T                     # chain rule through activation, then the linear layer
    return np.abs(g).mean()

relu = lambda z: np.maximum(z, 0)
for depth in (2, 5, 10, 20):
    gs = gradient_reaching_layer_1(sigmoid, lambda z: sigmoid(z) * (1 - sigmoid(z)), depth)
    gr = gradient_reaching_layer_1(relu, lambda z: (z > 0).astype(float), depth)
    print(f"depth {depth:2d}:  sigmoid net gradient {gs:.2e}    relu net gradient {gr:.2e}")
```

With sigmoid activations the gradient reaching the first layer collapses by orders of magnitude as depth grows; with ReLU (and an initialisation matched to it, explained in the [initialisation lesson](#/lesson/deep-learning/normalisation-init)) it stays roughly the same size. This single effect is why ReLU, combined with good initialisation, made deep networks practical.

## 5. What a hidden layer learns

It helps to think of each hidden unit as a **feature detector**. In the first layer of an image model, a unit's weights form a little template; its pre-activation is large when the input matches the template, and ReLU keeps only the positive matches. Later units combine earlier detectors: "edge here AND edge there" can mean a corner. The network learns which detectors are useful because their weights receive gradient whenever adjusting them would lower the loss.

Two consequences:

- **Width** (units per layer) sets how many detectors one stage can hold; **depth** sets how many stages of composition the network can perform. Deeper networks can represent some functions with exponentially fewer units than shallow ones.
- The loss landscape of a network with hidden layers is **non-convex**: swapping two hidden units gives exactly the same function, so there are always many equivalent minima, plus saddle points and plateaus. Gradient descent from a random start finds one good solution; different seeds find different ones.

## 6. Activations at the output: matching the task

The last layer's activation (or lack of one) must match what you predict, and it pairs with a particular loss:

| task | output layer | activation | PyTorch loss |
|---|---|---|---|
| regression (a number) | `Linear(h, 1)` | none | `nn.MSELoss` or `nn.L1Loss` |
| binary classification | `Linear(h, 1)` | sigmoid, **inside the loss** | `nn.BCEWithLogitsLoss` |
| multi-class, one label | `Linear(h, C)` | softmax, **inside the loss** | `nn.CrossEntropyLoss` |
| multi-label (several can be true) | `Linear(h, C)` | sigmoid per class, inside the loss | `nn.BCEWithLogitsLoss` |

"Inside the loss" is important: the loss functions that end in "WithLogits", and `CrossEntropyLoss`, take raw **logits** and apply the sigmoid or log-softmax themselves in a numerically stable combined form. Applying softmax in the model and then `CrossEntropyLoss` applies it twice and quietly hurts training. You apply sigmoid or softmax yourself only when you need probabilities for reporting or decisions. The [image classifier lesson](#/lesson/deep-learning/image-classifier) works through this in detail.

## 7. In PyTorch

Activations exist both as modules and as functions:

```python
import torch
from torch import nn
import torch.nn.functional as F

model = nn.Sequential(
    nn.Linear(2, 16),
    nn.ReLU(),            # module form: fits inside Sequential
    nn.Linear(16, 16),
    nn.GELU(),            # exact by default; nn.GELU(approximate="tanh") for the faster approximation
    nn.Linear(16, 1),     # no activation: raw score (a logit or a regression value)
)
z = torch.linspace(-3, 3, 7)
F.relu(z), torch.sigmoid(z), F.silu(z), F.leaky_relu(z, negative_slope=0.01)   # functional forms
```

- Module forms (`nn.ReLU()`) are objects you place in a model; they hold no parameters (except `nn.PReLU`, whose negative slope is learned).
- Functional forms (`F.relu`) are used inside a custom `forward` method, covered in the [next lesson](#/lesson/deep-learning/nn-module).
- `nn.ReLU(inplace=True)` overwrites its input to save memory; this is safe in most convnet positions but can trigger the in-place autograd error when the input is needed elsewhere.

> [!INTERVIEW]
> **"Why not use sigmoid everywhere?"** Its slope is at most 0.25 and near zero when saturated, so gradients vanish geometrically with depth; its outputs are not zero-centred; and the exponential costs more than a comparison. ReLU passes gradients with slope 1, is cheap and gives sparse activations. Mention its weakness (dead units) and the fixes (LeakyReLU, careful learning rates, He initialisation), and that transformers favour smooth GELU or SiLU. Keep sigmoid for outputs that are probabilities and for gates.

## Summary

- A neuron computes an activation of a weighted sum plus bias; a layer is a matrix product plus bias followed by an activation.
- Without non-linear activations, any stack of linear layers collapses into one linear layer.
- ReLU networks build piecewise-linear functions from hinges; the universal approximation theorem says one wide hidden layer suffices in principle, depth makes it efficient.
- Sigmoid and tanh saturate and shrink gradients (vanishing gradients); ReLU passes them at slope 1 but can die; GELU and SiLU are smooth modern defaults in transformers.
- Output activations and losses come in pairs; PyTorch's cross-entropy and "WithLogits" losses take raw logits.

## Glossary

- **Artificial neuron (unit)**: computes an activation of a weighted sum of inputs plus a bias.
- **Pre-activation**: the weighted sum before the activation is applied.
- **Activation function**: the non-linear function applied to the pre-activation.
- **Hidden layer**: a layer between the input and the output.
- **Piecewise-linear function**: a function made of straight segments joined at corners.
- **Universal approximation theorem**: one hidden layer with enough units can approximate any continuous function on a bounded region.
- **Sigmoid / tanh**: S-shaped squashing functions with ranges (0, 1) / (−1, 1).
- **ReLU / LeakyReLU**: max(0, z) / a version with a small slope for negatives.
- **GELU / SiLU (Swish)**: smooth ReLU-like activations, z·Φ(z) / z·σ(z).
- **Softplus**: a smooth version of ReLU, ln(1 + eᶻ).
- **Saturation**: the flat region of an activation where its slope is near zero.
- **Dead ReLU**: a unit stuck outputting zero with zero gradient.
- **Vanishing gradient**: gradients shrinking geometrically as they pass back through many layers.
- **Feature detector**: a unit that responds strongly to a particular input pattern.
- **Logit**: a raw score before sigmoid or softmax.

## Check yourself

```quiz
[
  {"q": "Two linear layers are stacked with no activation between them. What can the combination represent?", "options": ["Only a linear function, the same as one layer", "Any continuous function", "Only quadratic functions", "Only step functions"], "answer": 0,
   "explain": "W2(W1x + b1) + b2 = (W2W1)x + (W2b1 + b2)."},
  {"q": "What is the maximum value of the sigmoid's derivative?", "options": ["0.25", "1", "0.5", "It is unbounded"], "answer": 0,
   "explain": "σ(z)(1−σ(z)) peaks at z = 0 where both factors are 0.5."},
  {"q": "What is a dead ReLU unit?", "options": ["A unit whose pre-activation is negative for all inputs, so it outputs 0 and gets no gradient", "A unit with all-zero weights", "A unit in the output layer", "A unit that outputs NaN"], "answer": 0,
   "explain": "With zero gradient it can never move back into the active region; LeakyReLU and careful learning rates help."},
  {"q": "Which activation family is standard in transformer feed-forward blocks?", "options": ["Smooth ReLU-like functions such as GELU or SiLU", "Sigmoid", "Step function", "Identity"], "answer": 0,
   "explain": "BERT and GPT-style models use GELU; LLaMA-style models use SiLU-based gated units."},
  {"q": "For multi-class classification with nn.CrossEntropyLoss, the final layer should output…", "options": ["Raw logits with no activation", "Softmax probabilities", "Sigmoid probabilities", "ReLU outputs"], "answer": 0,
   "explain": "The loss applies log-softmax internally; adding softmax yourself applies it twice."},
  {"q": "A task allows several labels to be true at once (e.g. tags on a photo). Which loss fits?", "options": ["BCEWithLogitsLoss with one logit per label", "CrossEntropyLoss", "MSELoss on class indices", "NLLLoss"], "answer": 0,
   "explain": "Each label is an independent yes/no decision with its own sigmoid."},
  {"q": "What does the universal approximation theorem NOT tell you?", "options": ["How many units are needed or whether gradient descent will find good weights", "That one hidden layer can approximate continuous functions", "That a non-linearity is needed", "That approximation is on a bounded region"], "answer": 0,
   "explain": "It is an existence result; efficiency and trainability are separate questions."}
]
```

> **Source:** Stevens, Antiga & Viehmann, *Deep Learning with PyTorch*, ch. 6 (artificial neurons, composing a multilayer network, the error function, activation functions and choosing one, what learning means for a neural network); PyTorch documentation, `torch.nn` non-linear activations.
