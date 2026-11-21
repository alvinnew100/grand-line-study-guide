# nn.Module, state_dict and checkpointing

> **Before this lesson:** you need layers and activations from [Neurons, layers and activation functions](#/lesson/deep-learning/neurons-activations), the training loop and `torch.optim` from [Optimisers and validation](#/lesson/deep-learning/optimizers-validation), and devices from [storage, strides, views and devices](#/lesson/deep-learning/tensor-storage). Python classes, `__init__` and inheritance (a class building on another class) are used and explained briefly.

## In plain words

`nn.Module` is the base class for every layer and every model in PyTorch. A **module** is an object that holds parameters (and possibly other modules inside it) and defines how to turn inputs into outputs in a method called `forward`. A whole network is a module made of smaller modules, which are made of smaller modules, down to individual layers, like Russian nesting dolls.

Why have a base class at all? Because a lot of bookkeeping is identical for every model: finding all the parameters to hand to the optimiser, moving them all to the GPU, switching dropout and batch normalisation between training and evaluation behaviour, saving and loading the learned numbers. `nn.Module` does all of it for anything you build, as long as you follow a few rules.

The **state_dict** is the module's memory in a portable form: an ordered dictionary from names such as `"encoder.0.weight"` to tensors. Saving it to disk is a **checkpoint**. Analogy: the module class is the blueprint of a house, the state_dict is the furniture inventory with every item's position. To rebuild the house elsewhere you need both the blueprint (your code) and the inventory (the file).

Why it matters for a job: reading and writing `nn.Module` subclasses is daily work, and production bugs often come from checkpoints: loading into a mismatched architecture, missing optimiser state on resume, a model left in training mode, or a "module." prefix from a multi-GPU wrapper. Interviewers ask "what is the difference between `__call__` and `forward`?", "what does `state_dict` contain?", "how do you resume training exactly?".

## 1. Using built-in modules

```python
import torch
from torch import nn

linear = nn.Linear(in_features=4, out_features=3)     # weight (3, 4), bias (3,)
x = torch.randn(10, 4)                                 # a batch of 10 samples
y = linear(x)                                          # shape (10, 3)
print(linear.weight.shape, linear.bias.shape)          # torch.Size([3, 4]) torch.Size([3])
print(sum(p.numel() for p in linear.parameters()))     # 15
```

- Modules expect a **batch dimension first**. A single sample of 4 features must be passed as shape `(1, 4)`: add it with `x.unsqueeze(0)`. Most modules accept any number of leading dimensions and apply to the last one; convolution layers expect `(N, C, H, W)` and also accept an unbatched `(C, H, W)`.
- The weights are `nn.Parameter` objects: tensors that are automatically registered as parameters and have `requires_grad=True`.
- `nn.Linear` initialises its weights and bias with uniform random numbers scaled by $1/\sqrt{\text{in\_features}}$ (a variant of Kaiming initialisation), so two freshly created layers differ. Call `torch.manual_seed` first for reproducibility.

### Call the module, not forward

Always write `linear(x)`, never `linear.forward(x)`. Calling the module runs `nn.Module.__call__`, which runs registered **hooks** (functions attached to inspect or modify inputs and outputs, used by profilers, visualisation tools and some libraries) around `forward`. Calling `forward` directly skips them and silently breaks those tools.

## 2. Sequential models

`nn.Sequential` chains modules, passing each output to the next:

```python
from collections import OrderedDict

model = nn.Sequential(OrderedDict([
    ("hidden", nn.Linear(4, 16)),
    ("act", nn.ReLU()),
    ("output", nn.Linear(16, 3)),
]))
print(model)                         # readable summary with the names above
model.hidden.weight.shape            # access by name: torch.Size([16, 4])
model[0]                             # or by position
for name, p in model.named_parameters():
    print(name, tuple(p.shape))      # hidden.weight (16, 4), hidden.bias (16,), output.weight (3, 16), output.bias (3,)
```

Passing an `OrderedDict` (a dictionary that remembers insertion order) gives submodules meaningful names; without it they are named `"0"`, `"1"`, `"2"`. Names appear in `named_parameters()`, in error messages and in the state_dict keys, so good names pay off.

## 3. Writing your own module

`Sequential` cannot express branches, skip connections or reused layers. For anything beyond a straight chain, subclass `nn.Module`:

```python
import torch.nn.functional as F

class SmallNet(nn.Module):
    def __init__(self, in_features, hidden, n_classes, p_drop=0.1):
        super().__init__()                         # must come first: sets up the registries
        self.fc1 = nn.Linear(in_features, hidden)  # assigning a module registers it
        self.fc2 = nn.Linear(hidden, hidden)
        self.head = nn.Linear(hidden, n_classes)
        self.dropout = nn.Dropout(p_drop)
        self.register_buffer("input_mean", torch.zeros(in_features))   # saved, not trained

    def forward(self, x):
        x = x - self.input_mean
        h = F.relu(self.fc1(x))
        h = h + F.relu(self.fc2(h))                # a skip connection: impossible in Sequential
        return self.head(self.dropout(h))          # raw logits

net = SmallNet(4, 32, 3)
```

The rules that make the bookkeeping work:

- Call `super().__init__()` before assigning any submodule, or you get an error about the module not being initialised.
- **Assign submodules as attributes** (`self.fc1 = ...`). `nn.Module` intercepts attribute assignment and registers modules and `nn.Parameter`s. A plain Python list of layers is **not** registered: its parameters are invisible to `parameters()`, to `.to(device)` and to the state_dict, so they never train or save. Use `nn.ModuleList` (or `nn.ModuleDict`) for collections of layers.
- Stateless operations (ReLU, pooling, reshaping) can be called through `torch.nn.functional` inside `forward`; layers with parameters must be modules created in `__init__`.
- A **buffer** (`register_buffer`) is a tensor that belongs to the module's state (it moves with `.to(device)` and appears in the state_dict) but is not a parameter and gets no gradient. Batch normalisation's running mean and variance are buffers.

### Modes, devices and other module-wide operations

- `model.train()` and `model.eval()` set a `training` flag on every submodule. Dropout and batch normalisation read it. `eval()` does **not** turn off gradients; that is `torch.no_grad()`'s job.
- `model.to(device)` (or `.cuda()`, `.half()`) converts every parameter and buffer, in place, and returns the module.
- `model.apply(fn)` calls `fn` on every submodule, the standard way to apply a custom initialisation.
- `model.zero_grad()` clears gradients like `optimizer.zero_grad()`.

## 4. Building the machinery in NumPy

To see that none of this is magic, here is a minimal module system in NumPy that registers parameters through attribute assignment, finds them recursively, toggles modes and round-trips a state_dict. The names match PyTorch.

```python-run
import io
import numpy as np
from collections import OrderedDict

class Parameter(np.ndarray):
    """Marks an array as trainable, like nn.Parameter."""
    def __new__(cls, data):
        return np.asarray(data, dtype=np.float64).view(cls)

class Module:
    def __init__(self):
        object.__setattr__(self, "_parameters", OrderedDict())
        object.__setattr__(self, "_modules", OrderedDict())
        object.__setattr__(self, "training", True)
    def __setattr__(self, name, value):               # the registration trick
        if isinstance(value, Parameter):
            self._parameters[name] = value
        elif isinstance(value, Module):
            self._modules[name] = value
        object.__setattr__(self, name, value)
    def named_parameters(self, prefix=""):
        for name, p in self._parameters.items():
            yield prefix + name, p
        for mname, m in self._modules.items():
            yield from m.named_parameters(prefix + mname + ".")
    def parameters(self):
        return [p for _, p in self.named_parameters()]
    def train(self, mode=True):
        object.__setattr__(self, "training", mode)
        for m in self._modules.values():
            m.train(mode)
        return self
    def eval(self):
        return self.train(False)
    def state_dict(self):
        return OrderedDict((k, np.array(v)) for k, v in self.named_parameters())
    def load_state_dict(self, sd):
        own = dict(self.named_parameters())
        missing, unexpected = sorted(set(own) - set(sd)), sorted(set(sd) - set(own))
        if missing or unexpected:
            raise KeyError(f"missing keys {missing}, unexpected keys {unexpected}")
        for k, v in sd.items():
            if own[k].shape != v.shape:
                raise ValueError(f"size mismatch for {k}: {v.shape} vs {own[k].shape}")
            own[k][...] = v                           # copy in place, like param.copy_()
    def __call__(self, *args):
        return self.forward(*args)                    # (PyTorch also runs hooks here)

rng = np.random.default_rng(0)

class Linear(Module):
    def __init__(self, n_in, n_out):
        super().__init__()
        k = 1 / np.sqrt(n_in)
        self.weight = Parameter(rng.uniform(-k, k, (n_out, n_in)))
        self.bias = Parameter(rng.uniform(-k, k, n_out))
    def forward(self, x):
        return x @ self.weight.T + self.bias

class Dropout(Module):
    def __init__(self, p):
        super().__init__(); self.p = p
    def forward(self, x):
        if not self.training:
            return x                                  # identity in eval mode
        keep = rng.random(x.shape) >= self.p
        return x * keep / (1 - self.p)

class SmallNet(Module):
    def __init__(self):
        super().__init__()
        self.fc1 = Linear(4, 8)
        self.drop = Dropout(0.5)
        self.head = Linear(8, 3)
        self.not_registered = [Linear(8, 8)]          # a plain list: invisible to parameters()!
    def forward(self, x):
        return self.head(self.drop(np.maximum(self.fc1(x), 0)))

net = SmallNet()
for name, p in net.named_parameters():
    print(f"{name:12s} {p.shape}")
print("parameter count:", sum(p.size for p in net.parameters()), "(the list's 72 parameters are missing)")

x = rng.normal(size=(2, 4))
net.train(); a, b = net(x), net(x)
print("train mode, two calls equal?", np.allclose(a, b))
net.eval(); a, b = net(x), net(x)
print("eval mode, two calls equal? ", np.allclose(a, b))

buffer = io.BytesIO()
np.savez(buffer, **net.state_dict())                  # like torch.save(net.state_dict(), f)
buffer.seek(0)
loaded = OrderedDict(np.load(buffer).items())
fresh = SmallNet(); fresh.eval()
print("fresh net matches before loading?", np.allclose(fresh(x), net(x)))
fresh.load_state_dict(loaded)
print("fresh net matches after loading? ", np.allclose(fresh(x), net(x)))
try:
    fresh.load_state_dict({k: v for k, v in loaded.items() if k != "head.bias"})
except KeyError as e:
    print("strict loading caught:", e)
```

**Reading this code line by line**

- `Parameter` is an array subclass, used only as a marker, like `nn.Parameter` wrapping a tensor.
- `Module.__setattr__` checks every attribute assignment: parameters go into `_parameters`, submodules into `_modules`. This is the mechanism PyTorch uses too, which is why a plain list of layers is invisible.
- `named_parameters` walks the tree recursively, building dotted names like `fc1.weight` from attribute names: exactly how state_dict keys are formed.
- `train` and `eval` set the flag on every submodule; `Dropout` reads it.
- `state_dict` copies parameters into an ordered dictionary; saving and loading it through a byte buffer imitates `torch.save` and `torch.load`.
- `load_state_dict` refuses missing or unexpected keys and shape mismatches, like PyTorch's default `strict=True`, and copies values into the existing arrays in place.
- The output shows 67 registered parameters, random outputs in training mode, deterministic outputs in eval mode, and an exact match after loading.

## 5. state_dict and checkpoints in PyTorch

```python
torch.save(model.state_dict(), "weights.pt")        # recommended: save only tensors

model = SmallNet(4, 32, 3)                           # rebuild the architecture from code
state = torch.load("weights.pt", map_location="cpu", weights_only=True)
missing, unexpected = model.load_state_dict(state, strict=True)
model.eval()
```

- Save the **state_dict**, not the whole model object. `torch.save(model)` pickles the class by reference, so loading needs the exact same code at the same import path, and it breaks after refactoring.
- `map_location` puts tensors on the device you choose, which lets you load GPU-trained weights on a CPU-only server.
- `strict=False` skips missing and unexpected keys and reports them; it is useful when you deliberately load only part of a model (for example a pretrained backbone with a new head), and dangerous when used to hide a mismatch.
- Common key mismatch: models wrapped in `nn.DataParallel` or `DistributedDataParallel` prefix every key with `module.`. Save `model.module.state_dict()` from the wrapper, or strip the prefix when loading. Compiled models (`torch.compile`) prefix keys with `_orig_mod.`; save the original module's state_dict.

### Resumable training checkpoints

To continue training exactly where you stopped, saving model weights is not enough. Adam's moment estimates, the learning-rate scheduler's position and the mixed-precision scaler all carry state:

```python
checkpoint = {
    "epoch": epoch,
    "model": model.state_dict(),
    "optimizer": optimizer.state_dict(),
    "scheduler": scheduler.state_dict(),
    "scaler": scaler.state_dict(),           # if using float16 mixed precision
    "best_val_loss": best_val_loss,
    "config": vars(args),                    # hyperparameters, for reproducibility
}
torch.save(checkpoint, f"ckpt_epoch{epoch:03d}.pt")

ckpt = torch.load(path, map_location=device, weights_only=True)
model.load_state_dict(ckpt["model"])
optimizer.load_state_dict(ckpt["optimizer"])
scheduler.load_state_dict(ckpt["scheduler"])
start_epoch = ckpt["epoch"] + 1
```

Good practice: write the file to a temporary name and rename it when complete (so a crash mid-write never leaves a corrupt "latest" checkpoint), keep the best-validation checkpoint separately from the latest one, and record the code version (a git commit hash) alongside. (A `weights_only=True` load accepts plain Python numbers, strings, lists and dicts, so a checkpoint of this shape loads fine; custom objects would need `weights_only=False` from a trusted file.)

## 6. Counting parameters

Interviewers often ask for parameter counts. The rules for common layers:

| layer | parameters |
|---|---|
| `Linear(n, m)` | $n m + m$ |
| `Conv2d(c_in, c_out, k)` | $c_{in} c_{out} k^2 + c_{out}$ |
| `Embedding(V, d)` | $V d$ |
| `BatchNorm2d(c)` / `LayerNorm(c)` | $2c$ learned (plus $2c$ running-statistic buffers for BatchNorm) |
| activations, pooling, dropout | 0 |

In code: `sum(p.numel() for p in model.parameters() if p.requires_grad)`. Memory for float32 weights is 4 bytes per parameter; training with Adam roughly needs 16 bytes per parameter before counting activations (weights, gradients and two moment buffers), as the [GPU memory lesson](#/lesson/deep-learning/memory-mixed-precision) explains.

> [!INTERVIEW]
> **"You trained on 4 GPUs with DistributedDataParallel, and loading the checkpoint into a single-GPU model fails with unexpected keys. Why?"** The wrapper stores the real model as `.module`, so every key starts with `module.`. Fix it by saving `model.module.state_dict()` in the first place, or by stripping the prefix (`{k.removeprefix("module."): v for k, v in sd.items()}`) before loading. Then mention resuming properly: optimizer, scheduler and scaler state plus the epoch counter, and calling `model.eval()` before inference.

## Summary

- Every layer and model subclasses `nn.Module`; call modules (`model(x)`), never `forward` directly, so hooks run.
- Assigning `nn.Parameter`s and submodules as attributes registers them; plain lists are invisible, so use `nn.ModuleList` or `nn.ModuleDict`.
- `nn.Sequential` (optionally with an `OrderedDict` of names) covers straight chains; subclass for branches, skips and reuse.
- Buffers are saved and moved but not trained; `train()` and `eval()` switch layer behaviour, not gradient tracking.
- Save `state_dict`s, load with `map_location` and `weights_only=True`; resumable checkpoints also store optimiser, scheduler and scaler state.
- Watch for `module.` and `_orig_mod.` key prefixes from wrappers.

## Glossary

- **Module**: an object holding parameters and submodules with a `forward` method.
- **forward**: the method defining a module's computation.
- **Hook**: a function attached to a module that runs before or after `forward` or `backward`.
- **nn.Parameter**: a tensor registered as a trainable parameter of a module.
- **Submodule**: a module stored as an attribute of another module.
- **nn.Sequential**: a module that applies its children in order.
- **nn.ModuleList / nn.ModuleDict**: containers that register a list or dict of modules.
- **Functional API (`torch.nn.functional`)**: stateless function forms of operations.
- **Buffer**: module state that is saved and moved but not trained.
- **state_dict**: an ordered mapping from parameter and buffer names to tensors.
- **Checkpoint**: a saved state_dict (and often optimiser and scheduler state) used to resume or deploy.
- **strict loading**: requiring the state_dict keys to match the model exactly.
- **map_location**: the device to place loaded tensors on.
- **DataParallel / DistributedDataParallel**: wrappers that train a model across several GPUs.

## Check yourself

```quiz
[
  {"q": "Why should you call model(x) rather than model.forward(x)?", "options": ["__call__ runs registered hooks around forward", "forward is private and raises an error", "model(x) is faster", "forward does not compute gradients"], "answer": 0,
   "explain": "Skipping __call__ silently bypasses hooks used by profilers, wrappers and debugging tools."},
  {"q": "You store layers in self.layers = [nn.Linear(8, 8) for _ in range(3)]. What goes wrong?", "options": ["Their parameters are not registered, so they are not trained, moved or saved", "PyTorch raises an error at construction", "Only the first layer trains", "Nothing"], "answer": 0,
   "explain": "Use nn.ModuleList so the module system can see them."},
  {"q": "What does model.eval() do?", "options": ["Sets training=False so dropout and batch norm switch to inference behaviour", "Disables gradient computation", "Freezes the weights permanently", "Moves the model to CPU"], "answer": 0,
   "explain": "Gradient tracking is controlled separately by torch.no_grad() or inference_mode()."},
  {"q": "How many parameters does nn.Linear(100, 10) have?", "options": ["1,010", "1,000", "110", "10"], "answer": 0,
   "explain": "100 × 10 weights plus 10 biases."},
  {"q": "What is a buffer in nn.Module?", "options": ["A tensor saved in the state_dict and moved with the module but not trained", "A queue of input batches", "A gradient accumulator", "A temporary GPU cache"], "answer": 0,
   "explain": "Batch norm's running mean and variance are buffers."},
  {"q": "To resume Adam training exactly, what must the checkpoint contain besides model weights?", "options": ["The optimizer state_dict (and scheduler/scaler state if used) and the epoch", "Only the learning rate", "The training data", "The gradients of the last batch"], "answer": 0,
   "explain": "Adam's moment buffers and the step count shape every future update."},
  {"q": "Why is torch.save(model.state_dict()) preferred over torch.save(model)?", "options": ["Saving the whole object pickles a reference to its class, which breaks when code moves or changes", "state_dict files are encrypted", "torch.save(model) loses the weights", "state_dict saving is required for GPUs"], "answer": 0,
   "explain": "A state_dict is plain named tensors; you rebuild the architecture from code and load the numbers."},
  {"q": "Loading a checkpoint fails because every key starts with 'module.'. What produced it?", "options": ["The model was saved while wrapped in DataParallel or DistributedDataParallel", "The model used dropout", "The weights were saved in float16", "The optimizer was Adam"], "answer": 0,
   "explain": "Save model.module.state_dict() or strip the prefix before loading."}
]
```

> **Source:** Stevens, Antiga & Viehmann, *Deep Learning with PyTorch*, ch. 6 (the PyTorch nn module, using `__call__` rather than `forward`, batching inputs, `nn.Sequential` and `OrderedDict` names, inspecting parameters) and ch. 8 (subclassing `nn.Module`, how PyTorch keeps track of parameters and submodules, the functional API, saving and loading models); PyTorch documentation, "Saving and loading models", `nn.Module`.
