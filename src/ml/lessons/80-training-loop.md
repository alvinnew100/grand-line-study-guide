# Tensors, autograd and the training loop

Müller & Guido end their neural-network section by saying that scikit-learn's `MLPClassifier` only
scratches the surface, and that anyone who wants more flexible or larger models should move to a dedicated
deep-learning library. This module is that next step. It covers what you need to read and write modern
training code: tensors, automatic differentiation, and the five-line loop at the centre of every PyTorch
program. PyTorch does not run in the browser, so the PyTorch code here is shown as static listings, and
every idea is also demonstrated in runnable numpy.

## 1. Why deep learning needs different tools

Classical scikit-learn models take a fixed table of features. Deep learning differs in three ways:

- **The features are learned.** Layers transform raw pixels, audio samples or token ids into useful
  representations. This is why deep learning dominates perception and language tasks, where good
  hand-made features are hard to design.
- **Models are compositions of differentiable layers**, trained end to end by gradient descent. A library
  must compute gradients of arbitrary compositions automatically.
- **Scale.** Millions to billions of parameters and huge datasets need GPUs and mini-batch training.

For tabular data with mixed feature types, gradient-boosted trees usually remain the better first choice,
as the book already noted.

## 2. Tensors

A **tensor** is an n-dimensional array, the generalisation of scalars, vectors and matrices. It is the
only data structure a deep-learning library works with. A PyTorch tensor is like a numpy array with two
extras: it can live on a **GPU**, and it can **record the operations applied to it** so that gradients can
be computed.

| rank | name | typical shape | example |
|---|---|---|---|
| 0 | scalar | `()` | a loss value |
| 1 | vector | `(features,)` | one sample of tabular data |
| 2 | matrix | `(batch, features)` | a batch of tabular samples |
| 3 | 3-D tensor | `(batch, sequence, features)` | a batch of token embeddings |
| 4 | 4-D tensor | `(batch, channels, height, width)` | a batch of images |

The first axis is almost always the **batch** dimension.

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

The same shape rules apply as in numpy, including broadcasting. Most deep-learning bugs are shape bugs.

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

## 3. Automatic differentiation

In the calculus lesson we derived gradients by hand. For a network with dozens of layers that would be
hopeless. **Autograd** does it for us. While the forward pass runs, the library records a **computational
graph** of every operation. Calling `.backward()` on the final scalar walks the graph in reverse and
applies the chain rule at each node. This is **reverse-mode automatic differentiation**, the general form
of backpropagation.

```python
w = torch.tensor(0.5, requires_grad=True)       # a parameter: track operations on it
b = torch.tensor(0.0, requires_grad=True)
x, y = torch.tensor(2.0), torch.tensor(1.0)

loss = (torch.relu(w * x + b) * -1.0 + 0.5 - y) ** 2     # forward pass: builds the graph
loss.backward()                                          # backward pass: fills in .grad
print(w.grad, b.grad)                                    # tensor(6.) tensor(3.)
```

These are the values we computed by hand in the calculus lesson. To make the mechanism concrete, here is
a tiny scalar autograd engine in pure Python. It is about 30 lines and uses the same idea as PyTorch.

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

Things to remember about PyTorch's autograd:

- Gradients **accumulate** in `.grad`. You must reset them before each step with `optimizer.zero_grad()`.
- Wrap inference in `with torch.no_grad():`. It skips building the graph, which saves memory and time.
- `.detach()` cuts a tensor out of the graph. `loss.item()` returns a plain Python number.

## 4. Building a model with `nn.Module`

A model is a class that creates its layers in `__init__` and describes the forward computation in
`forward`. Parameters are registered automatically.

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

> [!WARNING]
> `nn.CrossEntropyLoss` expects **raw logits** and integer class labels. It applies log-softmax
> internally, in a numerically stable way. Adding your own softmax before it is a classic bug: the model
> still trains, but badly. For binary problems use `nn.BCEWithLogitsLoss`, again on logits.

## 5. Datasets and data loaders

A `Dataset` returns one sample by index. A `DataLoader` wraps it and yields shuffled **mini-batches**,
optionally loading in parallel worker processes.

```python
from torch.utils.data import TensorDataset, DataLoader

train_ds = TensorDataset(torch.tensor(X_train, dtype=torch.float32), torch.tensor(y_train, dtype=torch.long))
train_loader = DataLoader(train_ds, batch_size=32, shuffle=True)      # shuffle the training data every epoch
val_loader = DataLoader(val_ds, batch_size=256)                       # no shuffling needed for evaluation
```

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

### The same loop in numpy

Here is the identical procedure with everything written out: mini-batches, forward pass, loss, the
hand-derived backward pass from lesson 2.4, and an SGD update. It trains on the breast-cancer data and
runs in your browser.

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

## 7. Vocabulary of training

- **Epoch**: one full pass over the training data. **Iteration / step**: one parameter update on one
  mini-batch.
- **Batch size**: the number of samples per step. Larger batches give smoother gradients and use the GPU
  better, but need more memory. Smaller batches add noise, which often helps generalisation.
- **Learning rate**: the step size, and the single most important hyperparameter. It is usually changed
  during training by a **schedule** (warm-up, then cosine or step decay).
- **Loss curve**: the training and validation loss plotted over time. It is your main diagnostic tool.

| what you see | likely cause | what to try |
|---|---|---|
| loss is `nan` or explodes | learning rate too high; unstable loss; bad inputs | lower the learning rate; use losses that take logits; clip gradients; check for NaNs in the data |
| loss barely moves | learning rate too low; dead ReLUs; a bug (labels shuffled, gradients not flowing) | raise the learning rate; check that you can overfit one batch |
| training loss falls, validation loss rises | overfitting | regularise, add data or augmentation, stop early |
| both losses high and flat | underfitting | larger model, train longer, better features |

> [!TIP]
> **Overfit a single batch first.** Before a long run, check that the model can drive the loss to nearly
> zero on one small batch. If it can't, there is a bug in the model, the loss or the data pipeline. This is
> the same advice the book gives for MLPs: first make the network large enough to overfit, then regularise.

## 8. Initialisation and the role of scale

Weights must start random, to break the symmetry between units, and at the right scale. If they are too
small, the signal shrinks to nothing as it passes through the layers. If they are too large, it explodes.
**Xavier/Glorot** initialisation (variance $\approx 1/n_{in}$) suits tanh, and **He** initialisation
(variance $2/n_{in}$) suits ReLU. Both keep the variance of the activations roughly constant from layer to
layer. PyTorch layers use sensible defaults.

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

> [!INTERVIEW]
> **"Walk me through a PyTorch training step. Why `zero_grad`? Why `model.eval()`?"** A step is: zero the
> gradients, forward, loss, `backward`, `optimizer.step`. `zero_grad` is needed because `.grad`
> accumulates across backward calls (which is useful for gradient accumulation over several small
> batches). `model.eval()` switches dropout off and makes batch norm use its running statistics.
> `torch.no_grad()` separately disables graph building. Forgetting `eval()` gives noisy, worse validation
> numbers. Forgetting `train()` afterwards silently disables dropout for the rest of training.

## Summary

- A tensor is an n-dimensional array that can live on a GPU and record operations for differentiation.
- Autograd builds a computational graph in the forward pass, and `backward()` applies the chain rule in
  reverse.
- `nn.Module` holds layers and parameters. Loss functions take **logits**.
- The loop: `zero_grad → forward → loss → backward → step`, with `train()` / `eval()` modes and `no_grad`
  for evaluation.
- Watch the loss curves, overfit one batch first, scale inputs and use sound initialisation.

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
