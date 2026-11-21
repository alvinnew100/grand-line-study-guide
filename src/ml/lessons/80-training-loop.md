# Tensors, autograd and the training loop

> **Before this lesson:** you need gradients, the chain rule, backpropagation and gradient descent from [Calculus, gradients and gradient descent](#/lesson/ml/calculus-optimization), especially its worked example of a tiny network in section 5, which this lesson reuses. Array shapes and matrix products come from [Linear algebra for ML](#/lesson/ml/linear-algebra), and the multilayer perceptron (a small neural network) from [Kernel SVMs, neural networks and uncertainty](#/lesson/ml/svm-mlp-uncertainty). Softmax and cross-entropy are re-explained below.

## In plain words

**Deep learning** means training neural networks with many layers. Every such program, from a digit recogniser to a large language model, is built from the same three ingredients: **tensors** (arrays of numbers that hold the data and the weights), **automatic differentiation** (the library works out every gradient for you), and a short **training loop** that repeats "predict, measure the error, compute gradients, nudge the weights" thousands of times.

Think of learning to throw darts in the dark with a friend calling out how far off each throw was and in which direction. You throw (the forward pass), hear the miss (the loss), work out which way to adjust your arm (the gradients) and adjust a little (the update). Then you throw again. The training loop is exactly that cycle, run by a computer over millions of throws, adjusting millions of "arm muscles" at once.

Why this matters for a job: PyTorch is the most widely used deep-learning library, and every ML engineering interview that touches neural networks expects you to read and write its training loop, explain why `zero_grad()` is needed, and debug a loss that becomes "nan". Müller & Guido end their neural-network section by noting that scikit-learn's `MLPClassifier` only scratches the surface and that larger or more flexible models need a dedicated library; this module is that next step. PyTorch does not run in the browser, so its code appears as static listings, and every idea is also demonstrated in runnable NumPy.

## 1. Why deep learning needs different tools

Classical scikit-learn models take a fixed table of features. Deep learning differs in three ways:

- **The features are learned.** The layers transform raw inputs (pixels, audio samples, word ids) into useful representations, step by step. That is why deep learning dominates images, speech and language, where good hand-made features are hard to design.
- **Models are chains of differentiable layers**, trained all together ("end to end") by gradient descent. A function is **differentiable** when its slope can be computed everywhere it matters, which gradient descent needs. The library must compute gradients of any chain you build, automatically.
- **Scale.** Models have millions to billions of **parameters** (the weights that training adjusts) and train on huge datasets, which needs GPUs and training on small batches of data at a time.

For tables with mixed feature types, gradient-boosted trees (lesson 22) usually remain the better first choice.

## 2. Tensors

A **tensor** is an array of numbers with any number of dimensions. It generalises a single number (a **scalar**), a list of numbers (a **vector**) and a table (a **matrix**). The number of dimensions is the tensor's **rank**, and the size along each dimension is its **shape**. Tensors are the only data structure a deep-learning library works with.

A PyTorch tensor is like a NumPy array with two extras: it can live on a **GPU** (graphics processing unit, a chip that performs thousands of arithmetic operations in parallel), and it can **record the operations applied to it** so that gradients can be computed later.

| rank | name | typical shape | example |
|---|---|---|---|
| 0 | scalar | `()` | a loss value |
| 1 | vector | `(features,)` | one sample of tabular data |
| 2 | matrix | `(batch, features)` | a batch of tabular samples |
| 3 | 3-D tensor | `(batch, sequence, features)` | a batch of sentences, each word represented by a vector |
| 4 | 4-D tensor | `(batch, channels, height, width)` | a batch of colour images |

The first axis is almost always the **batch** dimension: the number of samples processed together. A colour image has three **channels** (red, green and blue intensity), each a grid of height × width pixels.

```python
import torch

x = torch.tensor([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])   # shape (2, 3), dtype float32
x.shape, x.dtype, x.device                              # torch.Size([2, 3]), torch.float32, cpu
x.T @ x                                                 # matrix product, like numpy
x.mean(dim=0)                                           # 'dim' is numpy's 'axis'
x.reshape(3, 2); x.unsqueeze(0).shape                   # (1, 2, 3): add a batch dimension
x_gpu = x.to("cuda")                                    # move to the GPU, if one is available
torch.from_numpy(np_array); x.numpy()                   # conversion to and from numpy
```

Line by line: `torch.tensor` builds a tensor from nested lists; `.shape`, `.dtype` (data type, here 32-bit decimals) and `.device` (where it lives) describe it; `@` is matrix multiplication as in NumPy; `dim=0` means "along the first axis"; `reshape` changes the shape without changing the data, and `unsqueeze(0)` adds a new axis of size 1 at the front; `.to("cuda")` copies the tensor to an NVIDIA GPU ("CUDA" is NVIDIA's GPU programming platform). The same shape rules apply as in NumPy, including **broadcasting** (automatically stretching a smaller array to match a larger one, such as adding a bias vector to every row). Most deep-learning bugs are shape bugs.

```python-run
import numpy as np
batch = np.zeros((32, 3, 28, 28))            # 32 RGB images of 28 x 28 pixels: (batch, channels, height, width)
print("image batch:", batch.shape)
flat = batch.reshape(32, -1)                 # flatten everything except the batch axis
print("flattened for a dense layer:", flat.shape)
W, b = np.zeros((flat.shape[1], 10)), np.zeros(10)
print("logits:", (flat @ W + b).shape, "<- one row of 10 class scores per image")
tokens = np.zeros((8, 128, 512))             # 8 sentences, 128 tokens each, 512-dimensional embeddings
print("sequence batch:", tokens.shape, " mean over the sequence axis:", tokens.mean(axis=1).shape)
```

**Reading this code line by line**

- `np.zeros((32, 3, 28, 28))` makes a 4-D array standing in for 32 small colour images.
- `reshape(32, -1)` keeps the batch axis and flattens the rest; `-1` means "work out this size yourself", which is $3 \times 28 \times 28 = 2352$.
- A **dense layer** (also called fully connected or linear) multiplies by a weight matrix and adds a bias. `W` has shape (2352, 10), so `flat @ W + b` has shape (32, 10): ten scores per image. Raw scores like these, before any conversion to probabilities, are called **logits**.
- `tokens` imitates 8 sentences of 128 tokens, each token a vector of 512 numbers. Averaging over axis 1 (the sequence) leaves one 512-number summary per sentence: shape (8, 512).

Tracking shapes through a model like this, on paper or with `print`, catches most errors before they happen.

## 3. Automatic differentiation

In the calculus lesson we derived gradients by hand. For a network with dozens of layers that would be hopeless. **Autograd**, short for automatic differentiation, does it for us. While the forward pass runs, the library records a **computational graph**: every operation, with its inputs and output. Calling `.backward()` on the final number (the loss) walks that graph in reverse and applies the chain rule at each step. This is **reverse-mode automatic differentiation**, the general form of backpropagation.

```python
w = torch.tensor(0.5, requires_grad=True)       # a parameter: track operations on it
b = torch.tensor(0.0, requires_grad=True)
x, y = torch.tensor(2.0), torch.tensor(1.0)

loss = (torch.relu(w * x + b) * -1.0 + 0.5 - y) ** 2     # forward pass: builds the graph
loss.backward()                                          # backward pass: fills in .grad
print(w.grad, b.grad)                                    # tensor(6.) tensor(3.)
```

`requires_grad=True` marks `w` and `b` as parameters whose gradients we want. The loss line computes the calculus lesson's tiny network, $L = (v \cdot \text{relu}(wx + b) + c - y)^2$ with $v = -1$ and $c = 0.5$, and builds the graph as it goes. After `loss.backward()`, `w.grad` holds $\partial L/\partial w = 6$ and `b.grad` holds $\partial L/\partial b = 3$: the same values we computed by hand there.

To show there is no magic, here is a tiny autograd engine for single numbers in pure Python. It uses the same idea as PyTorch, in about 30 lines.

```python-run
class Value:
    """A scalar that remembers how it was computed, so it can backpropagate."""
    def __init__(self, data, parents=(), backward=lambda: None):
        self.data, self.grad, self._parents, self._backward = data, 0.0, parents, backward
    def __add__(self, other):
        other = other if isinstance(other, Value) else Value(other)
        out = Value(self.data + other.data, (self, other))
        def backward():
            self.grad += out.grad; other.grad += out.grad
        out._backward = backward
        return out
    def __mul__(self, other):
        other = other if isinstance(other, Value) else Value(other)
        out = Value(self.data * other.data, (self, other))
        def backward():
            self.grad += other.data * out.grad; other.grad += self.data * out.grad
        out._backward = backward
        return out
    def relu(self):
        out = Value(max(0.0, self.data), (self,))
        def backward():
            self.grad += (out.data > 0) * out.grad
        out._backward = backward
        return out
    def backward(self):
        order, seen = [], set()
        def visit(v):                       # topological order: a node comes after everything it depends on
            if v not in seen:
                seen.add(v)
                for p in v._parents: visit(p)
                order.append(v)
        visit(self)
        self.grad = 1.0
        for v in reversed(order): v._backward()

w, b, v, c = Value(0.5), Value(0.0), Value(-1.0), Value(0.5)
x, y = 2.0, 1.0
z = (w * x + b).relu() * v + c
diff = z + (-y)
loss = diff * diff
loss.backward()
print("loss =", loss.data)
print("dL/dw =", w.grad, " dL/db =", b.grad, " dL/dv =", v.grad, " dL/dc =", c.grad)
```

**Reading this code line by line**

- Each `Value` stores its number (`data`), its gradient (`grad`, starting at 0), the values it was computed from (`_parents`) and a small function (`_backward`) that knows how to pass gradient back to those parents.
- `__add__` and `__mul__` are special method names that Python calls for `+` and `*`, so writing `w * x` runs `w.__mul__(x)`. Each creates the result `out` and attaches a `backward` function encoding the local rule: for addition, the gradient passes through unchanged to both inputs; for multiplication, each input receives the gradient times the *other* input's value. These are the chain-rule factors from the calculus lesson.
- `relu` passes the gradient through only if its output was positive.
- `backward()` first lists every value in **topological order** (each value after all the values it depends on) using the recursive helper `visit`. It sets the loss's own gradient to 1 (since $\partial L/\partial L = 1$) and then calls each value's `_backward` in reverse order, so that every gradient is complete before it is passed further back.
- Gradients are added with `+=`, not assigned, because a value used in two places receives gradient from both. That is also why PyTorch gradients **accumulate**.
- The bottom lines build the same tiny network and run it.

The output is a loss of 2.25 and gradients $\partial L/\partial w = 6$, $\partial L/\partial b = 3$, $\partial L/\partial v = -3$, $\partial L/\partial c = -3$, exactly the hand calculation. PyTorch does the same with tensors instead of single numbers and with hundreds of operation types.

Things to remember about PyTorch's autograd:

- Gradients **accumulate** in `.grad`, so they must be reset before each step, with `optimizer.zero_grad()`.
- Wrap prediction-only code in `with torch.no_grad():`. It skips building the graph, saving memory and time.
- `.detach()` returns a copy of a tensor cut out of the graph; `loss.item()` returns a plain Python number.

## 4. Building a model with `nn.Module`

In PyTorch a model is a Python class that inherits from `nn.Module`. It creates its layers in `__init__` and describes the computation in a method called `forward`. Any layer stored as an attribute has its parameters registered automatically, so the optimiser can find them.

```python
import torch
from torch import nn

class MLP(nn.Module):
    def __init__(self, n_in, n_hidden, n_classes):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(n_in, n_hidden),     # computes x @ W.T + b
            nn.ReLU(),
            nn.Linear(n_hidden, n_classes) # outputs raw scores (logits): no softmax here
        )

    def forward(self, x):                  # x: (batch, n_in)
        return self.net(x)                 # (batch, n_classes)

model = MLP(n_in=30, n_hidden=64, n_classes=2)
sum(p.numel() for p in model.parameters()) # 30*64 + 64 + 64*2 + 2 = 2114 parameters
```

Line by line: `super().__init__()` runs `nn.Module`'s own setup; `nn.Sequential` chains layers so that each one's output feeds the next; `nn.Linear(30, 64)` is a dense layer with a 30 × 64 weight matrix and 64 biases; `nn.ReLU()` applies $\max(0, x)$ to every number; the last layer produces two logits per sample. Calling `model(x)` runs `forward`. The parameter count: $30 \times 64 + 64$ for the first layer plus $64 \times 2 + 2$ for the second, $1920 + 64 + 128 + 2 = 2114$.

### From logits to a loss

For classification the logits are turned into probabilities by the **softmax** function: in words, exponentiate every score, then divide each by the total so they add up to 1. For logits $z_1, \dots, z_K$,

$$p_k = \frac{e^{z_k}}{\sum_{j} e^{z_j}}.$$

Worked example: logits $(2, 1, 0)$ give $e^2 = 7.39$, $e^1 = 2.72$, $e^0 = 1$, with total 11.11, so the probabilities are $0.665, 0.245, 0.090$.

The **cross-entropy loss** then measures how much probability the model gave to the correct class: it is minus the logarithm of that probability, averaged over the batch,

$$L = -\frac{1}{n}\sum_{i=1}^{n} \ln p_{i, y_i}.$$

Worked example: if the correct class gets probability 0.9 for one sample and 0.2 for another, the losses are $-\ln 0.9 = 0.105$ and $-\ln 0.2 = 1.609$, averaging 0.857. Confident correct answers cost almost nothing; confident wrong answers cost a lot.

> [!WARNING]
> `nn.CrossEntropyLoss` expects **raw logits** and integer class labels. It applies softmax and the logarithm internally, combined in a numerically stable way. Adding your own softmax before it is a classic bug: softmax gets applied twice, and the model still trains, but badly. For binary problems use `nn.BCEWithLogitsLoss`, again on logits.

## 5. Datasets and data loaders

A `Dataset` returns one sample, given its index. A `DataLoader` wraps a dataset and hands out shuffled **mini-batches**, small groups of samples (often 32 to 512) processed together in one step, optionally loading them in parallel background processes.

```python
from torch.utils.data import TensorDataset, DataLoader

train_ds = TensorDataset(torch.tensor(X_train, dtype=torch.float32), torch.tensor(y_train, dtype=torch.long))
train_loader = DataLoader(train_ds, batch_size=32, shuffle=True)      # shuffle the training data every epoch
val_loader = DataLoader(val_ds, batch_size=256)                       # no shuffling needed for evaluation
```

`TensorDataset` pairs a feature tensor with a label tensor (labels as 64-bit integers, `torch.long`, which the loss requires). Iterating over `train_loader` yields `(xb, yb)` pairs of 32 samples each, in a new random order every pass.

## 6. The training loop

Every PyTorch training script contains this loop in some form:

```python
device = "cuda" if torch.cuda.is_available() else "cpu"
model = MLP(30, 64, 2).to(device)
loss_fn = nn.CrossEntropyLoss()
optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)

for epoch in range(20):
    model.train()                              # training mode: enables dropout, batch-norm updates
    for xb, yb in train_loader:
        xb, yb = xb.to(device), yb.to(device)
        optimizer.zero_grad()                  # 1. clear old gradients
        logits = model(xb)                     # 2. forward pass
        loss = loss_fn(logits, yb)             # 3. compute the loss
        loss.backward()                        # 4. backward pass: compute gradients
        optimizer.step()                       # 5. update the parameters

    model.eval()                               # evaluation mode: disables dropout, uses running batch-norm stats
    correct = total = 0
    with torch.no_grad():                      # no graph needed for evaluation
        for xb, yb in val_loader:
            pred = model(xb.to(device)).argmax(dim=1)
            correct += (pred.cpu() == yb).sum().item(); total += len(yb)
    print(f"epoch {epoch}: validation accuracy {correct / total:.3f}")

torch.save(model.state_dict(), "model.pt")     # save the weights
```

Reading it from the top: pick the GPU if there is one; build the model on that device; choose the loss; create an **optimiser**, the object that updates the parameters from their gradients (Adam is a popular choice, lesson 81) with a **learning rate** `lr` that sets the step size. Then, for each **epoch** (one full pass over the training data), switch to training mode and run the five steps for every mini-batch. After each epoch, switch to evaluation mode, turn off graph building, and count correct predictions on the validation data (`argmax(dim=1)` picks the class with the highest logit). Finally save the learned weights. `model.train()` and `model.eval()` matter for layers that behave differently during training, such as dropout and batch normalisation (lesson 81).

```mermaid
flowchart LR
  B[Get a mini-batch] --> Z[zero_grad]
  Z --> F[Forward pass: logits]
  F --> L[Loss]
  L --> BW[backward: gradients]
  BW --> S[optimizer.step: update weights]
  S --> B
  S -.->|after each epoch| E[Evaluate on validation data in eval mode]
```

The simplest update rule, **stochastic gradient descent** (SGD), moves every parameter a small step against its gradient: in words, new weight = old weight minus learning rate times gradient,

$$w \leftarrow w - \eta \, \frac{\partial L}{\partial w}.$$

Here $\eta$ (eta) is the learning rate. Worked example: with $w = 0.5$, gradient 6 (from the tiny network) and $\eta = 0.05$, the new weight is $0.5 - 0.05 \times 6 = 0.2$. "Stochastic" (random) refers to computing the gradient on a random mini-batch instead of the whole dataset, which is cheaper and noisier.

### The same loop in NumPy

Here is the identical procedure with everything written out: mini-batches, forward pass, loss, the backward pass derived by hand (as in the problem *ml-mlp-backprop*), and an SGD update. It trains a one-hidden-layer network on the breast-cancer data, in your browser.

```python-run
import numpy as np
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

X, y = load_breast_cancer(return_X_y=True)
X_tr, X_va, y_tr, y_va = train_test_split(X, y, stratify=y, random_state=0)
scaler = StandardScaler().fit(X_tr)                      # networks need scaled inputs
X_tr, X_va = scaler.transform(X_tr), scaler.transform(X_va)

rng = np.random.RandomState(0)
n_in, n_hidden, n_classes = X_tr.shape[1], 32, 2
W1 = rng.randn(n_in, n_hidden) * np.sqrt(2 / n_in); b1 = np.zeros(n_hidden)      # He initialisation
W2 = rng.randn(n_hidden, n_classes) * np.sqrt(2 / n_hidden); b2 = np.zeros(n_classes)

def forward(X):
    A1 = X @ W1 + b1
    H = np.maximum(0, A1)
    Z = H @ W2 + b2
    Z = Z - Z.max(axis=1, keepdims=True)
    P = np.exp(Z); P /= P.sum(axis=1, keepdims=True)
    return A1, H, P

lr, batch_size = 0.05, 32
for epoch in range(1, 16):
    order = rng.permutation(len(X_tr))                   # shuffle every epoch
    for start in range(0, len(order), batch_size):
        idx = order[start:start + batch_size]
        xb, yb = X_tr[idx], y_tr[idx]
        A1, H, P = forward(xb)                           # forward pass
        dZ = P.copy(); dZ[np.arange(len(yb)), yb] -= 1; dZ /= len(yb)     # backward pass
        dW2, db2 = H.T @ dZ, dZ.sum(axis=0)
        dA1 = (dZ @ W2.T) * (A1 > 0)
        dW1, db1 = xb.T @ dA1, dA1.sum(axis=0)
        W1 -= lr * dW1; b1 -= lr * db1; W2 -= lr * dW2; b2 -= lr * db2    # SGD step
    if epoch in (1, 2, 5, 10, 15):
        _, _, P_tr = forward(X_tr); _, _, P_va = forward(X_va)
        loss = -np.log(P_tr[np.arange(len(y_tr)), y_tr] + 1e-12).mean()
        print(f"epoch {epoch:2d}  train loss {loss:.4f}  validation accuracy {(P_va.argmax(1) == y_va).mean():.3f}")
```

**Reading this code line by line**

- The data is split and standardised. Networks train badly on unscaled inputs, because features with large numbers dominate the early gradients.
- `W1` (30 × 32) and `W2` (32 × 2) start as random numbers scaled by $\sqrt{2/n_{in}}$ (He initialisation, section 8); the biases start at zero.
- `forward` computes the hidden layer `A1 = X @ W1 + b1`, applies ReLU to get `H`, computes the logits `Z`, and turns them into probabilities with softmax. Subtracting each row's maximum before `np.exp` does not change the result (it cancels in the division) but prevents overflow when logits are large.
- Each epoch shuffles the row order with `rng.permutation` and walks through it 32 rows at a time.
- The backward pass starts from a neat fact: for softmax followed by cross-entropy, the gradient with respect to the logits is "probabilities minus the one-hot correct answer", divided by the batch size. `dZ[np.arange(len(yb)), yb] -= 1` subtracts 1 at each sample's correct class. For example, probabilities $(0.665, 0.245, 0.090)$ with correct class 0 give $(-0.335, 0.245, 0.090)$.
- The chain rule then gives the layer gradients: `dW2 = H.T @ dZ`; the gradient flowing into the hidden layer is `dZ @ W2.T`, multiplied by `(A1 > 0)` because ReLU passes gradient only where its input was positive; and `dW1 = xb.T @ dA1`. Bias gradients are sums over the batch.
- The SGD step subtracts `lr` times each gradient, in place.
- At selected epochs the code reports the training loss (cross-entropy over all training rows; adding `1e-12` avoids taking the log of exactly 0) and the validation accuracy.

The training loss falls from 0.234 after the first epoch to 0.059 after the fifteenth, and validation accuracy rises from 0.881 to 0.930 by epoch 5 and stays there. This is the PyTorch loop with nothing hidden.

## 7. Vocabulary of training

- **Epoch**: one full pass over the training data. **Iteration** or **step**: one parameter update on one mini-batch. With 10,000 samples and batches of 100, an epoch is 100 steps.
- **Batch size**: the number of samples per step. Larger batches give smoother gradients and use the GPU more efficiently, but need more memory. Smaller batches add noise, which often helps generalisation.
- **Learning rate**: the step size, and the single most important hyperparameter. It is often changed during training by a **schedule**, for example a short **warm-up** (rising from near zero) followed by a gradual decay.
- **Loss curve**: the training and validation loss plotted against epochs. It is your main diagnostic tool.

| what you see | likely cause | what to try |
|---|---|---|
| loss is `nan` ("not a number") or explodes | learning rate too high; unstable loss computation; bad inputs | lower the learning rate; use losses that take logits; clip gradients; check the data for missing values |
| loss barely moves | learning rate too low; "dead" ReLU units that output 0 for every input; a bug (labels shuffled, gradients not flowing) | raise the learning rate; check that you can overfit one batch |
| training loss falls, validation loss rises | overfitting | regularise, add data or augmentation, stop early (lesson 81) |
| both losses high and flat | underfitting | larger model, train longer, better features |

> [!TIP]
> **Overfit a single batch first.** Before a long run, check that the model can drive the loss to nearly zero on one small batch of, say, 32 samples. If it cannot, there is a bug in the model, the loss or the data pipeline. This matches the book's advice for MLPs: first make the network large enough to overfit, then regularise.

## 8. Initialisation and the role of scale

Weights must start random, so that different units in a layer learn different things (if all started equal, they would all receive the same gradient and stay equal forever). They must also start at the right **scale**. Too small, and the signal shrinks towards zero as it passes through the layers; too large, and it explodes.

Two standard rules choose the spread of the initial weights from $n_{in}$, the number of inputs to the layer. In words: the more inputs a unit adds up, the smaller each weight should be, so that the sum stays a sensible size. **Xavier** (or Glorot) initialisation uses a variance of about $1/n_{in}$ and suits tanh activations; **He** initialisation uses $2/n_{in}$ and suits ReLU, where the factor 2 compensates for ReLU setting about half the values to zero. Worked example: a layer with 256 inputs gets He weights with standard deviation $\sqrt{2/256} = 0.088$. PyTorch's layers use sensible defaults.

```python-run
import numpy as np
rng = np.random.RandomState(0)
x = rng.randn(1000, 256)
for name, scale in [("too small (0.01)", 0.01), ("He: sqrt(2/n)", np.sqrt(2 / 256)), ("too large (1.0)", 1.0)]:
    h = x
    for layer in range(10):
        h = np.maximum(0, h @ (rng.randn(256, 256) * scale))
    print(f"{name:18s} activation std after 10 ReLU layers: {h.std():.3g}")
```

The demo pushes 1,000 random inputs through 10 ReLU layers of width 256, with weights drawn at three scales, and prints the spread (standard deviation) of the final layer's outputs. With weights of scale 0.01 the signal has shrunk to about $3 \times 10^{-10}$, effectively zero; with scale 1.0 it has grown to about $3 \times 10^{10}$; with He scaling it stays near 0.8. Vanishing or exploding activations mean vanishing or exploding gradients too, and a network that will not train.

> [!INTERVIEW]
> **"Walk me through a PyTorch training step. Why `zero_grad`? Why `model.eval()`?"** A step is: zero the gradients, forward pass, loss, `backward`, `optimizer.step`. `zero_grad` is needed because `.grad` accumulates across backward calls (which is useful for gradient accumulation, summing gradients over several small batches before one update). `model.eval()` switches dropout off and makes batch normalisation use its stored running statistics. `torch.no_grad()` separately disables graph building. Forgetting `eval()` gives noisy, worse validation numbers; forgetting `train()` afterwards silently disables dropout for the rest of training.

## Summary

- A tensor is an n-dimensional array that can live on a GPU and record operations for differentiation. The first axis is usually the batch.
- Autograd builds a computational graph in the forward pass, and `backward()` applies the chain rule in reverse; gradients accumulate.
- `nn.Module` holds layers and parameters. Loss functions such as `CrossEntropyLoss` take **logits**.
- The loop: `zero_grad → forward → loss → backward → step`, with `train()` / `eval()` modes and `no_grad` for evaluation.
- Watch the loss curves, overfit one batch first, scale the inputs and use sound initialisation.

## Glossary

- **Deep learning**: training neural networks with many layers.
- **Tensor / rank / shape**: an n-dimensional array / its number of dimensions / its size along each dimension.
- **GPU**: a processor that performs many arithmetic operations in parallel.
- **Batch / mini-batch**: the samples processed together in one step.
- **Channel**: one colour component (or feature map) of an image.
- **Broadcasting**: automatically stretching a smaller array to match a larger one.
- **Dense (linear, fully connected) layer**: multiply by a weight matrix and add a bias.
- **Logits**: raw class scores before softmax.
- **Softmax**: turns scores into probabilities that add up to 1.
- **Cross-entropy loss**: minus the log of the probability given to the correct class, averaged.
- **Autograd (automatic differentiation)**: the library computing gradients by recording operations.
- **Computational graph**: the record of operations linking inputs to the loss.
- **Topological order**: an ordering in which each item comes after everything it depends on.
- **Optimiser**: the object that updates parameters from gradients.
- **Learning rate**: the size of each update step.
- **Stochastic gradient descent (SGD)**: gradient descent using random mini-batches.
- **Epoch / iteration**: one pass over the training data / one update.
- **Initialisation (Xavier, He)**: rules for the scale of the starting weights.

## Check yourself

```quiz
[
  {"q": "What is the conventional shape of a batch of 32 RGB images of 64×64 pixels in PyTorch?", "options": ["(32, 3, 64, 64)", "(64, 64, 3, 32)", "(3, 32, 64, 64)", "(32, 64, 64)"], "answer": 0,
   "explain": "PyTorch uses (batch, channels, height, width)."},
  {"q": "Why must you call optimizer.zero_grad() in every iteration?", "options": ["Gradients accumulate in .grad across backward() calls", "It resets the model weights", "It clears the GPU memory", "It shuffles the data"], "answer": 0,
   "explain": "Without it, the new gradient is added to the gradient of the previous batch."},
  {"q": "nn.CrossEntropyLoss expects as its first argument…", "options": ["raw logits", "probabilities after softmax", "one-hot labels", "log-probabilities only"], "answer": 0,
   "explain": "It applies log-softmax internally; passing softmax outputs applies softmax twice."},
  {"q": "What does model.eval() change?", "options": ["Layer behaviour: dropout is disabled and batch norm uses running statistics", "It stops gradient computation", "It moves the model to the CPU", "It freezes the weights permanently"], "answer": 0,
   "explain": "Gradient tracking is turned off separately with torch.no_grad()."},
  {"q": "What does loss.backward() do?", "options": ["Computes the gradient of the loss with respect to every parameter that requires grad", "Updates the parameters", "Runs the forward pass in reverse to reconstruct the input", "Resets the loss to zero"], "answer": 0,
   "explain": "The update itself is done by optimizer.step()."},
  {"q": "With 10,000 training samples and batch size 100, one epoch consists of…", "options": ["100 iterations", "10,000 iterations", "1 iteration", "100,000 iterations"], "answer": 0,
   "explain": "An epoch is one pass over the data: 10,000 / 100 parameter updates."},
  {"q": "Your training loss becomes NaN after a few steps. The most likely first fix is…", "options": ["lower the learning rate (and check the loss is computed from logits)", "increase the batch size to the full dataset", "remove the validation set", "add more layers"], "answer": 0,
   "explain": "Too-large steps make the loss diverge; unstable log/exp computations are the other common cause."},
  {"q": "Why is He initialisation used with ReLU networks?", "options": ["It keeps the variance of activations roughly constant across layers", "It makes all weights equal", "It guarantees convexity", "It removes the need for biases"], "answer": 0,
   "explain": "Weights that are too small make signals vanish and too large make them explode; variance 2/n_in compensates for ReLU zeroing half the units."}
]
```

> **Source:** Müller & Guido, *Introduction to Machine Learning with Python*, ch. 2 ("Neural Networks (Deep Learning)") and ch. 8 ("Where to Go from Here": neural networks, other frameworks); PyTorch documentation, "Learn the Basics" (tensors, autograd, building models, optimisation loop); Goodfellow, Bengio & Courville, *Deep Learning*, ch. 6 and 8.
