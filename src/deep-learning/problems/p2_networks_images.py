import numpy as _np

_rng = _np.random.RandomState(22)


def _r(*shape, scale=1.0):
    return (_rng.randn(*shape) * scale).round(3).tolist()


PROBLEMS = [
# ---------------------------------------------------------------- activations and their slopes
dict(
    id="dl-activation-grads",
    title="Activation Functions and Their Derivatives",
    difficulty="Easy",
    pattern="Neural Network Layers",
    kind="function",
    entry="activation",
    compare="float",
    description=r"""
Write `activation(name, z)` that returns `[f(z), f'(z)]` (two lists, element-wise over the list `z`) for:

| name | f(z) | f'(z) |
|---|---|---|
| `"relu"` | max(0, z) | 1 if z > 0 else 0 (so 0 at exactly 0) |
| `"leaky_relu"` | z if z > 0 else 0.01·z | 1 if z > 0 else 0.01 |
| `"sigmoid"` | 1/(1+e^(−z)) | σ(z)(1−σ(z)) |
| `"tanh"` | tanh z | 1 − tanh² z |
| `"softplus"` | ln(1 + e^z) | σ(z) |
| `"silu"` | z·σ(z) | σ(z)(1 + z(1 − σ(z))) |
| `"gelu"` | z·Φ(z) | Φ(z) + z·φ(z) |

where Φ is the standard normal CDF, Φ(z) = ½(1 + erf(z/√2)), and φ(z) = e^(−z²/2)/√(2π).

Your implementation must be **numerically stable**: inputs can be as large as ±1000 (no `inf` or `nan` allowed;
for example softplus(1000) is 1000).

**Example:** `activation("relu", [-1, 0, 2])` → `[[0, 0, 2], [0, 0, 1]]`
""",
    starter='''import math

def activation(name, z):
    pass
''',
    solution='''import math
import numpy as np

def _sigmoid(z):
    out = np.empty_like(z)
    pos = z >= 0
    out[pos] = 1.0 / (1.0 + np.exp(-z[pos]))
    e = np.exp(z[~pos])
    out[~pos] = e / (1.0 + e)
    return out

def activation(name, z):
    z = np.asarray(z, dtype=float)
    s = _sigmoid(z)
    if name == "relu":
        f, d = np.maximum(z, 0.0), (z > 0).astype(float)
    elif name == "leaky_relu":
        f, d = np.where(z > 0, z, 0.01 * z), np.where(z > 0, 1.0, 0.01)
    elif name == "sigmoid":
        f, d = s, s * (1 - s)
    elif name == "tanh":
        t = np.tanh(z)
        f, d = t, 1 - t * t
    elif name == "softplus":
        f, d = np.logaddexp(0.0, z), s
    elif name == "silu":
        f, d = z * s, s * (1 + z * (1 - s))
    elif name == "gelu":
        cdf = 0.5 * (1 + np.array([math.erf(v / math.sqrt(2)) for v in z]))
        pdf = np.exp(-0.5 * np.minimum(z * z, 1e4)) / math.sqrt(2 * math.pi)
        f, d = z * cdf, cdf + z * pdf
    else:
        raise ValueError(name)
    return [f, d]
''',
    tests=[
        ["relu", [-1, 0, 2]],
        ["leaky_relu", [-100, -0.5, 0, 0.5, 3]],
        ["sigmoid", [-1000, -5, 0, 5, 1000]],
        ["tanh", [-20, -1, 0, 0.3, 20]],
        ["softplus", [-1000, -2, 0, 2, 1000]],
        ["silu", [-1000, -3, -1, 0, 1, 3, 1000]],
        ["gelu", [-6, -1, -0.1, 0, 0.1, 1, 6]],
        ["gelu", [-1000, 1000]],
        ["relu", []],
        ["sigmoid", _r(12, scale=4)],
        ["silu", _r(12, scale=4)],
        ["softplus", _r(10, scale=30)],
    ],
    examples=2,
    wrong_solutions=[
        '''import math
def activation(name, z):
    sig = lambda v: 1 / (1 + math.exp(-v))           # overflows for v = -1000
    f, d = [], []
    for v in z:
        if name == "relu": f.append(max(v, 0)); d.append(1.0 if v >= 0 else 0.0)   # slope 1 at 0
        elif name == "leaky_relu": f.append(v if v > 0 else 0.01 * v); d.append(1.0 if v > 0 else 0.01)
        elif name == "sigmoid": s = sig(v); f.append(s); d.append(s * (1 - s))
        elif name == "tanh": t = math.tanh(v); f.append(t); d.append(1 - t * t)
        elif name == "softplus": f.append(math.log1p(math.exp(v))); d.append(sig(v))
        elif name == "silu": s = sig(v); f.append(v * s); d.append(s * (1 + v * (1 - s)))
        else:
            c = 0.5 * (1 + math.erf(v / math.sqrt(2))); f.append(v * c)
            d.append(c + v * math.exp(-v * v / 2) / math.sqrt(2 * math.pi))
    return [f, d]
''',
        '''import numpy as np
def activation(name, z):
    z = np.asarray(z, float); s = 1 / (1 + np.exp(-np.clip(z, -500, 500)))
    table = {"relu": (np.maximum(z, 0), (z > 0) * 1.0), "leaky_relu": (np.where(z > 0, z, 0.01 * z), np.where(z > 0, 1.0, 0.01)),
             "sigmoid": (s, s * (1 - s)), "tanh": (np.tanh(z), 1 - np.tanh(z) ** 2),
             "softplus": (np.logaddexp(0, z), s), "silu": (z * s, s),             # wrong silu slope
             "gelu": (z * s, s)}
    return list(table[name])
''',
    ],
    guide=dict(
        prereqs="*Neurons, layers and activation functions* (the activation table and the finite-difference check).",
        intuition=r"""Each activation's derivative can be written in terms of quantities you already computed in the forward
pass (σ, tanh, Φ), which is why frameworks save them for backward. Stability comes from never evaluating `exp` of a
large positive number.""",
        hints=[
            "Stable sigmoid: for z ≥ 0 use 1/(1+e^(−z)); for z < 0 use e^z/(1+e^z).",
            "Stable softplus: `np.logaddexp(0, z)` computes ln(e⁰ + e^z) without overflow.",
            "For GELU use `math.erf`; the density e^(−z²/2) underflows harmlessly to 0 for large |z|.",
        ],
        brute_force="Plain `math.exp` formulas: correct for moderate inputs, overflow (`OverflowError` or `inf`) at ±1000.",
        approach=r"""Convert `z` to a float array, compute a stable sigmoid once, then branch on `name` and apply the table.
Check: silu'(0) = σ(0)·(1 + 0) = 0.5; gelu'(0) = Φ(0) = 0.5; softplus(0) = ln 2 ≈ 0.6931.""",
        complexity="O(n) time and space.",
        pitfalls=r"""- ReLU slope at exactly 0 must be 0 (PyTorch's convention).
- `log1p(exp(1000))` overflows; use logaddexp.
- SiLU's derivative is not σ(z).
- An empty input returns two empty lists.""",
        follow_up="Add the tanh approximation of GELU (`approximate='tanh'`) and measure the maximum difference from the exact version.",
    ),
),

# ---------------------------------------------------------------- linear backward
dict(
    id="dl-linear-backward",
    title="nn.Linear Forward and Backward",
    difficulty="Medium",
    pattern="Neural Network Layers",
    kind="function",
    entry="linear_backward",
    compare="float",
    description=r"""
`nn.Linear` stores `weight` with shape `(out_features, in_features)` and computes `y = x @ weight.T + bias`.

Write `linear_backward(x, weight, bias, grad_out)` returning `[y, grad_x, grad_weight, grad_bias]`, where `grad_out`
is dL/dy (same shape as `y`) and the other three are dL/dx, dL/dweight, dL/dbias.

- `x` has shape `(N, in)` **or** `(in,)` for a single unbatched sample (then `y` and `grad_out` have shape `(out,)`).
- `bias` is a list of length `out`, or `None` (no bias: return `None` for `grad_bias`).
- Gradients must have exactly the shapes of the corresponding inputs.

**Example:** `x=[[1,2]]`, `weight=[[1,0],[0,1],[1,1]]`, `bias=[0,0,1]`, `grad_out=[[1,1,1]]` →
`y=[[1,2,4]]`, `grad_x=[[2,2]]`, `grad_weight=[[1,2],[1,2],[1,2]]`, `grad_bias=[1,1,1]`.
""",
    starter='''import numpy as np

def linear_backward(x, weight, bias, grad_out):
    pass
''',
    solution='''import numpy as np

def linear_backward(x, weight, bias, grad_out):
    x = np.asarray(x, dtype=float)
    W = np.asarray(weight, dtype=float)
    g = np.asarray(grad_out, dtype=float)
    single = x.ndim == 1
    if single:
        x, g = x[None, :], g[None, :]
    y = x @ W.T
    if bias is not None:
        y = y + np.asarray(bias, dtype=float)
    grad_x = g @ W
    grad_W = g.T @ x
    grad_b = g.sum(axis=0) if bias is not None else None
    if single:
        y, grad_x = y[0], grad_x[0]
    return [y, grad_x, grad_W, grad_b]
''',
    tests=[
        [[[1, 2]], [[1, 0], [0, 1], [1, 1]], [0, 0, 1], [[1, 1, 1]]],
        [_r(4, 3), _r(2, 3), _r(2), _r(4, 2)],
        [_r(5, 4), _r(3, 4), None, _r(5, 3)],
        [[0.5, -1.0, 2.0], _r(2, 3), [0.1, -0.1], [1.0, -2.0]],
        [_r(1, 1), _r(1, 1), _r(1), _r(1, 1)],
        [_r(8, 6), _r(5, 6), _r(5), _r(8, 5)],
        [[[0, 0, 0], [0, 0, 0]], _r(2, 3), [1, 2], [[1, 0], [0, 1]]],
        [_r(3, 2), _r(4, 2), _r(4), [[0, 0, 0, 0]] * 3],
        [_r(16, 10), _r(7, 10), None, _r(16, 7)],
    ],
    examples=2,
    wrong_solutions=[
        '''import numpy as np
def linear_backward(x, weight, bias, grad_out):
    x, W, g = (np.atleast_2d(np.asarray(a, float)) for a in (x, weight, grad_out))
    y = x @ W.T + (np.asarray(bias, float) if bias is not None else 0)
    return [y, g @ W, x.T @ g, g.sum(0) if bias is not None else None]   # grad_W transposed, 1-D shape lost
''',
        '''import numpy as np
def linear_backward(x, weight, bias, grad_out):
    x, W, g = np.asarray(x, float), np.asarray(weight, float), np.asarray(grad_out, float)
    one = x.ndim == 1
    if one: x, g = x[None], g[None]
    y = x @ W.T + (np.asarray(bias, float) if bias is not None else 0)
    gb = g.mean(0) if bias is not None else None                          # mean instead of sum
    gx = g @ W
    if one: y, gx = y[0], gx[0]
    return [y, gx, g.T @ x, gb]
''',
    ],
    guide=dict(
        prereqs="Matrix-multiplication gradients and unbroadcasting from *Autograd in depth*; `nn.Linear` layout from *nn.Module*.",
        intuition=r"""For `y = x Wᵀ + b`: every output depends on x through W, so dL/dx = grad_out @ W; each weight W[o, i]
multiplies x[:, i] and feeds y[:, o], so dL/dW = grad_outᵀ @ x; the bias was broadcast to every row, so its gradient
is the **sum** of grad_out over the batch.""",
        hints=[
            "Check shapes: grad_out (N, out), W (out, in) → grad_x (N, in) = grad_out @ W.",
            "grad_W must be (out, in): grad_out.T @ x.",
            "Treat a 1-D x as a batch of one, then squeeze y and grad_x back.",
        ],
        brute_force="Finite differences on every entry of x, W and b: O(parameters × forward cost) and approximate. Use it to test your answer.",
        approach=r"""Example: x = [1,2]; W rows [1,0], [0,1], [1,1]; b = [0,0,1] → y = [1, 2, 4]. With grad_out = [1,1,1]:
grad_x = [1,1,1] @ W = [2, 2]; grad_W = outer([1,1,1], [1,2]) = three rows of [1,2]; grad_b = [1,1,1].""",
        complexity="O(N · in · out) time, the same as the forward pass.",
        pitfalls=r"""- Using `x.T @ grad_out` gives (in, out), the transpose of what PyTorch's (out, in) weight needs.
- Averaging instead of summing for the bias (the loss already contains any 1/N factor).
- Forgetting the unbatched case or the `bias=None` case.""",
        follow_up="Extend to inputs with several leading dimensions (N, T, in): flatten the leading axes for the weight gradient, as PyTorch does for sequence models.",
    ),
),

# ---------------------------------------------------------------- parameter counting
dict(
    id="dl-param-count",
    title="Shapes and Parameter Count of a Model Spec",
    difficulty="Medium",
    pattern="Model Design",
    kind="function",
    entry="count_params",
    description=r"""
A model is described as a list of layer dicts applied in order to one sample of shape `input_shape` (no batch
axis): `[C, H, W]` for images or `[F]` for vectors. Write `count_params(input_shape, layers)` returning
`[total_trainable_parameters, output_shape]`.

Layer types (missing keys take the defaults shown):

| layer | effect on shape | parameters |
|---|---|---|
| `{"type": "conv2d", "out": O, "k": k, "stride": 1, "padding": 0, "bias": true}` | `[C,H,W]` → `[O,H',W']`, H' = ⌊(H+2p−k)/s⌋+1 | O·C·k² (+O if bias) |
| `{"type": "maxpool", "k": k, "stride": k}` | `[C,H,W]` → `[C,H',W']` (same formula, padding 0) | 0 |
| `{"type": "batchnorm"}` | unchanged | 2·C (C = first dimension) |
| `{"type": "relu"}` / `{"type": "dropout"}` | unchanged | 0 |
| `{"type": "flatten"}` | → `[product of all dims]` | 0 |
| `{"type": "gap"}` (global average pool) | `[C,H,W]` → `[C]` | 0 |
| `{"type": "linear", "out": O, "bias": true}` | `[F]` → `[O]` | F·O (+O if bias) |
| `{"type": "embedding", "num": V, "dim": D}` | `[L]` (token ids) → `[L, D]` | V·D |

Inputs are always valid (no shape errors).

**Example:** `input_shape=[3,32,32]`, layers conv(16, k=3, padding=1), relu, maxpool(2), flatten, linear(10) →
`[448 + 40970, [10]] = [41418, [10]]`.
""",
    starter='''def count_params(input_shape, layers):
    pass
''',
    solution='''def count_params(input_shape, layers):
    shape = list(input_shape)
    total = 0
    for L in layers:
        t = L["type"]
        if t == "conv2d":
            c, h, w = shape
            k, s, p = L["k"], L.get("stride", 1), L.get("padding", 0)
            o = L["out"]
            total += o * c * k * k + (o if L.get("bias", True) else 0)
            shape = [o, (h + 2 * p - k) // s + 1, (w + 2 * p - k) // s + 1]
        elif t == "maxpool":
            c, h, w = shape
            k = L["k"]
            s = L.get("stride", k)
            shape = [c, (h - k) // s + 1, (w - k) // s + 1]
        elif t == "batchnorm":
            total += 2 * shape[0]
        elif t in ("relu", "dropout"):
            pass
        elif t == "flatten":
            n = 1
            for d in shape:
                n *= d
            shape = [n]
        elif t == "gap":
            shape = [shape[0]]
        elif t == "linear":
            f, o = shape[-1], L["out"]
            total += f * o + (o if L.get("bias", True) else 0)
            shape = shape[:-1] + [o]
        elif t == "embedding":
            total += L["num"] * L["dim"]
            shape = shape + [L["dim"]]
    return [total, shape]
''',
    tests=[
        [[3, 32, 32], [{"type": "conv2d", "out": 16, "k": 3, "padding": 1}, {"type": "relu"}, {"type": "maxpool", "k": 2},
                       {"type": "flatten"}, {"type": "linear", "out": 10}]],
        [[3, 32, 32], [{"type": "conv2d", "out": 32, "k": 3, "padding": 1}, {"type": "relu"}, {"type": "maxpool", "k": 2},
                       {"type": "conv2d", "out": 16, "k": 3, "padding": 1}, {"type": "relu"}, {"type": "maxpool", "k": 2},
                       {"type": "flatten"}, {"type": "linear", "out": 64}, {"type": "relu"}, {"type": "linear", "out": 2}]],
        [[3, 224, 224], [{"type": "conv2d", "out": 64, "k": 7, "stride": 2, "padding": 3, "bias": False},
                         {"type": "batchnorm"}, {"type": "relu"}, {"type": "maxpool", "k": 3, "stride": 2}]],
        [[784], [{"type": "linear", "out": 128}, {"type": "relu"}, {"type": "dropout"}, {"type": "linear", "out": 10, "bias": False}]],
        [[1, 28, 28], [{"type": "conv2d", "out": 8, "k": 5}, {"type": "maxpool", "k": 2}, {"type": "conv2d", "out": 16, "k": 5},
                       {"type": "maxpool", "k": 2}, {"type": "flatten"}]],
        [[64, 7, 7], [{"type": "gap"}, {"type": "linear", "out": 1000}]],
        [[20], [{"type": "embedding", "num": 5000, "dim": 64}, {"type": "linear", "out": 32}]],
        [[3, 8, 8], []],
        [[3, 64, 64], [{"type": "conv2d", "out": 16, "k": 3, "stride": 2, "padding": 1}, {"type": "batchnorm"},
                       {"type": "conv2d", "out": 32, "k": 3, "stride": 2, "padding": 1}, {"type": "batchnorm"},
                       {"type": "gap"}, {"type": "linear", "out": 5}]],
        [[10], [{"type": "batchnorm"}, {"type": "linear", "out": 1}]],
        [[1, 9, 9], [{"type": "maxpool", "k": 2}]],
    ],
    examples=2,
    wrong_solutions=[
        '''def count_params(input_shape, layers):
    shape, total = list(input_shape), 0
    for L in layers:
        t = L["type"]
        if t == "conv2d":
            c, h, w = shape; k, s, p, o = L["k"], L.get("stride", 1), L.get("padding", 0), L["out"]
            total += o * c * k * k + o                       # always counts a bias
            shape = [o, (h + 2 * p - k) // s + 1, (w + 2 * p - k) // s + 1]
        elif t == "maxpool":
            c, h, w = shape; k = L["k"]; s = L.get("stride", k); shape = [c, (h - k) // s + 1, (w - k) // s + 1]
        elif t == "batchnorm": total += 2 * shape[0]
        elif t == "flatten":
            n = 1
            for d in shape: n *= d
            shape = [n]
        elif t == "gap": shape = [shape[0]]
        elif t == "linear":
            total += shape[-1] * L["out"] + (L["out"] if L.get("bias", True) else 0); shape = shape[:-1] + [L["out"]]
        elif t == "embedding": total += L["num"] * L["dim"]; shape = shape + [L["dim"]]
    return [total, shape]
''',
        '''def count_params(input_shape, layers):
    shape, total = list(input_shape), 0
    for L in layers:
        t = L["type"]
        if t == "conv2d":
            c, h, w = shape; k, s, p, o = L["k"], L.get("stride", 1), L.get("padding", 0), L["out"]
            total += o * c * k * k + (o if L.get("bias", True) else 0)
            shape = [o, (h + 2 * p - k) // s + 1, (w + 2 * p - k) // s + 1]
        elif t == "maxpool":
            c, h, w = shape; k = L["k"]; shape = [c, h // k, w // k]          # ignores a custom stride
        elif t == "batchnorm": total += 4 * shape[0]                          # counts running stats too
        elif t == "flatten":
            n = 1
            for d in shape: n *= d
            shape = [n]
        elif t == "gap": shape = [shape[0]]
        elif t == "linear":
            total += shape[-1] * L["out"] + (L["out"] if L.get("bias", True) else 0); shape = shape[:-1] + [L["out"]]
        elif t == "embedding": total += L["num"] * L["dim"]; shape = shape + [L["dim"]]
    return [total, shape]
''',
    ],
    guide=dict(
        prereqs="Parameter-count table in *nn.Module, state_dict and checkpointing*; output-size formula in *Convolutions, pooling and building a convnet*.",
        intuition=r"""Walk the layers once, carrying the current shape. Each layer contributes parameters computed from the
shape **entering** it, then updates the shape. Parameter-free layers only change (or keep) the shape.""",
        hints=[
            "Keep `shape` as a list and update it per layer.",
            "Conv: O·C·k² + O·bias; output size ⌊(H + 2p − k)/s⌋ + 1.",
            "Linear acts on the last dimension (so it also works after an embedding); BatchNorm's running statistics are buffers, not trainable parameters.",
        ],
        brute_force="Build real PyTorch modules and call `numel()`: not available here, and it hides the reasoning interviews want.",
        approach=r"""Example: [3,32,32] → conv(16,k3,p1): 16·3·9+16 = 448, shape [16,32,32] → relu → maxpool2 → [16,16,16]
→ flatten [4096] → linear(10): 4096·10+10 = 40,970. Total 41,418.""",
        complexity="O(number of layers).",
        pitfalls=r"""- `bias: false` convolutions (common before batch norm) have no bias parameters.
- Max-pool stride defaults to the kernel size, but a custom stride (3 with stride 2) changes the size.
- BatchNorm trains only γ and β (2·C).
- Linear after an embedding applies to the last axis, keeping the sequence length.""",
        follow_up="Also return the multiply-accumulate count (FLOPs) per layer; note how early convolutions dominate compute while linear layers dominate parameters.",
    ),
),

# ---------------------------------------------------------------- minibatch indices
dict(
    id="dl-minibatch-indices",
    title="DataLoader Batch Indices",
    difficulty="Easy",
    pattern="Data Loading",
    kind="function",
    entry="make_batches",
    description=r"""
Simulate the index lists a `DataLoader` produces for one epoch.

`make_batches(n, batch_size, drop_last, order)`:

- `n` examples with indices `0..n-1`; `order` is either `None` (sequential sampler: `0, 1, ..., n-1`) or a list
  giving the shuffled order (a permutation of `0..n-1`, as a random sampler would produce).
- Cut the order into consecutive chunks of `batch_size`. If `drop_last` is true, discard a final chunk shorter than
  `batch_size`.
- Return the list of chunks (each a list of indices).

**Examples:**
- `make_batches(5, 2, False, None)` → `[[0,1],[2,3],[4]]`
- `make_batches(5, 2, True, [4,2,0,3,1])` → `[[4,2],[0,3]]`
""",
    starter='''def make_batches(n, batch_size, drop_last, order):
    pass
''',
    solution='''def make_batches(n, batch_size, drop_last, order):
    idx = list(range(n)) if order is None else list(order)
    out = []
    for s in range(0, n, batch_size):
        chunk = idx[s:s + batch_size]
        if drop_last and len(chunk) < batch_size:
            break
        out.append(chunk)
    return out
''',
    tests=[
        [5, 2, False, None],
        [5, 2, True, [4, 2, 0, 3, 1]],
        [0, 4, False, None],
        [3, 5, False, None],
        [3, 5, True, None],
        [6, 3, True, [5, 4, 3, 2, 1, 0]],
        [6, 3, False, [1, 0, 3, 2, 5, 4]],
        [1, 1, True, None],
        [10, 4, False, [9, 1, 8, 2, 7, 3, 6, 4, 5, 0]],
        [100, 32, True, None],
        [100, 32, False, list(range(99, -1, -1))],
    ],
    examples=2,
    wrong_solutions=[
        '''def make_batches(n, batch_size, drop_last, order):
    idx = list(range(n)) if order is None else list(order)
    out = [idx[s:s + batch_size] for s in range(0, n, batch_size)]
    return out[:-1] if drop_last else out        # drops the last batch even when it is full
''',
        '''def make_batches(n, batch_size, drop_last, order):
    idx = list(range(n))                         # ignores the shuffled order
    out = [idx[s:s + batch_size] for s in range(0, n, batch_size)]
    if drop_last and out and len(out[-1]) < batch_size: out.pop()
    return out
''',
    ],
    guide=dict(
        prereqs="Sampler, batch sampler and `drop_last` in *Dataset, transforms and DataLoader*.",
        intuition="The sampler decides the order; the batch sampler only cuts that order into consecutive chunks.",
        hints=[
            "Start from `order` or `range(n)`.",
            "Slice in steps of `batch_size`.",
            "Only discard the last chunk when it is actually short.",
        ],
        brute_force="Already linear; nothing better is needed.",
        approach=r"""For n=5, bs=2, order [4,2,0,3,1]: chunks [4,2], [0,3], [1]; drop_last removes [1].
Number of batches: ⌈n/bs⌉ without drop_last, ⌊n/bs⌋ with it.""",
        complexity="O(n).",
        pitfalls=r"""- Dropping a full last batch when `n` is a multiple of `batch_size`.
- Ignoring the provided order.
- `n = 0` gives no batches.""",
        follow_up="Implement `WeightedRandomSampler` with replacement, or a bucketing sampler that groups sequences of similar length to reduce padding.",
    ),
),

# ---------------------------------------------------------------- log softmax
dict(
    id="dl-log-softmax",
    title="Numerically Stable log_softmax",
    difficulty="Easy",
    pattern="Losses",
    kind="function",
    entry="log_softmax",
    compare="float",
    description=r"""
Implement `torch.log_softmax(z, dim)` for a nested list `z` of any rank ≥ 1 and an axis `dim` (negative values count
from the end, like Python indexing).

`log_softmax(z)_i = z_i − log Σ_j exp(z_j)` along `dim`.

It must be **numerically stable**: values may be as large as ±10,000 and the result must never contain `inf` or
`nan`. Return the same shape as `z`.

**Examples:**
- `log_softmax([0, 0], 0)` → `[-0.6931, -0.6931]`
- `log_softmax([[1000, 1000, 1000]], -1)` → `[[-1.0986, -1.0986, -1.0986]]`
""",
    starter='''import numpy as np

def log_softmax(z, dim):
    pass
''',
    solution='''import numpy as np

def log_softmax(z, dim):
    a = np.asarray(z, dtype=float)
    m = a.max(axis=dim, keepdims=True)
    shifted = a - m
    return shifted - np.log(np.exp(shifted).sum(axis=dim, keepdims=True))
''',
    tests=[
        [[0, 0], 0],
        [[[1000, 1000, 1000]], -1],
        [[1, 2, 3], 0],
        [[[1, 2, 3], [4, 5, 6]], 0],
        [[[1, 2, 3], [4, 5, 6]], 1],
        [[[-10000, 0, 10000]], 1],
        [[5], 0],
        [_r(2, 3, 4, scale=50), 2],
        [_r(2, 3, 4, scale=50), -2],
        [_r(2, 3, 4, scale=50), 0],
        [[[-1e4, -1e4], [1e4, -1e4]], -1],
    ],
    examples=2,
    wrong_solutions=[
        '''import numpy as np
def log_softmax(z, dim):
    a = np.asarray(z, float)
    return np.log(np.exp(a) / np.exp(a).sum(axis=dim, keepdims=True))      # overflows
''',
        '''import numpy as np
def log_softmax(z, dim):
    a = np.asarray(z, float); m = a.max()                                    # global max, not per slice
    s = a - m
    return s - np.log(np.exp(s).sum(axis=dim, keepdims=True))
''',
    ],
    guide=dict(
        prereqs="Softmax, log-sum-exp and the max-subtraction trick in *A first image classifier*.",
        intuition=r"""Subtracting the maximum along the axis makes the largest exponent e⁰ = 1, so nothing overflows, and the
sum is at least 1, so its log is never −∞. The shift cancels mathematically.""",
        hints=[
            "Compute `m = a.max(axis=dim, keepdims=True)`.",
            "`shifted = a - m`; the answer is `shifted - log(sum(exp(shifted)))` along `dim`.",
            "NumPy accepts negative axes directly.",
        ],
        brute_force="`log(softmax(z))` overflows for large inputs and gives `log(0) = -inf` for very negative ones.",
        approach=r"""For [−10000, 0, 10000]: m = 10000, shifted = [−20000, −10000, 0], exp sum ≈ 1, log ≈ 0 → result
[−20000, −10000, 0]. The naive version computes exp(10000) = inf.""",
        complexity="O(size of z).",
        pitfalls=r"""- Using one global maximum: rows whose values are far below the global max underflow to all zeros, giving −∞.
- Forgetting `keepdims=True`, which breaks broadcasting along non-final axes.""",
        follow_up="Implement `logsumexp` itself and use it for the CTC or CRF losses, which are sums over exponentially many paths.",
    ),
),

# ---------------------------------------------------------------- cross entropy
dict(
    id="dl-cross-entropy",
    title="F.cross_entropy with ignore_index and Label Smoothing",
    difficulty="Medium",
    pattern="Losses",
    kind="function",
    entry="cross_entropy",
    compare="float",
    description=r"""
Re-implement `torch.nn.functional.cross_entropy(logits, targets, ignore_index=..., reduction=..., label_smoothing=...)`
for logits of shape `(N, C)` and integer class targets of shape `(N,)`.

`cross_entropy(logits, targets, reduction, ignore_index, label_smoothing)`:

- `logp = log_softmax(logits, dim=1)` (stable!).
- Per-sample loss with smoothing ε: `loss_i = (1 − ε)·(−logp[i, y_i]) + (ε / C)·Σ_c(−logp[i, c])`
  (ε = 0 gives the usual negative log-likelihood).
- Samples whose target equals `ignore_index` contribute **0** and are excluded from the average.
- `reduction`: `"none"` → list of per-sample losses (0 for ignored); `"sum"` → total; `"mean"` → total divided by the
  number of **non-ignored** samples. At least one sample is never ignored.

**Example:** `logits=[[2,0],[0,2]]`, `targets=[0,1]`, `"mean"`, `-100`, `0.0` → `0.126928`
(each sample: −log(e²/(e²+1)) = log(1+e⁻²)).
""",
    starter='''import numpy as np

def cross_entropy(logits, targets, reduction, ignore_index, label_smoothing):
    pass
''',
    solution='''import numpy as np

def cross_entropy(logits, targets, reduction, ignore_index, label_smoothing):
    z = np.asarray(logits, dtype=float)
    t = np.asarray(targets, dtype=np.int64)
    n, c = z.shape
    m = z.max(axis=1, keepdims=True)
    logp = (z - m) - np.log(np.exp(z - m).sum(axis=1, keepdims=True))
    keep = t != ignore_index
    safe_t = np.where(keep, t, 0)
    nll = -logp[np.arange(n), safe_t]
    smooth = -logp.sum(axis=1) / c
    eps = label_smoothing
    loss = np.where(keep, (1 - eps) * nll + eps * smooth, 0.0)
    if reduction == "none":
        return loss
    if reduction == "sum":
        return float(loss.sum())
    return float(loss.sum() / keep.sum())
''',
    tests=[
        [[[2, 0], [0, 2]], [0, 1], "mean", -100, 0.0],
        [[[2, 0], [0, 2]], [0, 1], "none", -100, 0.0],
        [[[1, 2, 3], [1, 2, 3], [5, 0, 0]], [2, 0, -100], "mean", -100, 0.0],
        [[[1, 2, 3], [1, 2, 3], [5, 0, 0]], [2, 0, -100], "sum", -100, 0.0],
        [[[1, 2, 3], [1, 2, 3], [5, 0, 0]], [2, 0, -100], "none", -100, 0.0],
        [[[1, 2, 3], [3, 2, 1]], [2, 2], "mean", -100, 0.1],
        [[[1000, -1000], [-1000, 1000]], [1, 1], "none", -100, 0.0],
        [[[0, 0, 0, 0]], [3], "mean", -100, 0.2],
        [_r(6, 5, scale=3), [0, 4, 2, 2, 1, 3], "mean", -100, 0.0],
        [_r(6, 5, scale=3), [0, 4, 2, 2, 1, 3], "mean", 2, 0.05],
        [_r(6, 5, scale=3), [0, 0, 0, 1, 1, 1], "none", 1, 0.3],
        [[[0.5, 0.5]], [0], "sum", -100, 1.0],
    ],
    examples=2,
    wrong_solutions=[
        '''import numpy as np
def cross_entropy(logits, targets, reduction, ignore_index, label_smoothing):
    z = np.asarray(logits, float); t = np.asarray(targets)
    n, c = z.shape; m = z.max(1, keepdims=True)
    logp = z - m - np.log(np.exp(z - m).sum(1, keepdims=True))
    keep = t != ignore_index
    nll = -logp[np.arange(n), np.where(keep, t, 0)]
    loss = np.where(keep, (1 - label_smoothing) * nll + label_smoothing * (-logp.sum(1) / c), 0.0)
    if reduction == "none": return loss
    if reduction == "sum": return float(loss.sum())
    return float(loss.mean())                                   # divides by N, including ignored samples
''',
        '''import numpy as np
def cross_entropy(logits, targets, reduction, ignore_index, label_smoothing):
    z = np.asarray(logits, float); t = np.asarray(targets)
    n, c = z.shape; m = z.max(1, keepdims=True)
    logp = z - m - np.log(np.exp(z - m).sum(1, keepdims=True))
    keep = t != ignore_index
    nll = -logp[np.arange(n), np.where(keep, t, 0)]
    loss = np.where(keep, nll, 0.0)                             # ignores label smoothing
    if reduction == "none": return loss
    if reduction == "sum": return float(loss.sum())
    return float(loss.sum() / keep.sum())
''',
    ],
    guide=dict(
        prereqs="Cross-entropy, log-sum-exp and the options list in *A first image classifier*; the `dl-log-softmax` problem.",
        intuition=r"""Cross-entropy is minus the log-probability of the true class. Label smoothing mixes in the loss against a
uniform target (the average of −log p over classes). Ignored samples behave as if they were never in the batch, so the
mean divides by the count of real targets.""",
        hints=[
            "Compute a stable `logp` first; pick `logp[np.arange(N), targets]` with a safe index for ignored rows.",
            "Smoothing term: `-logp.sum(axis=1) / C`.",
            "Mask with `targets != ignore_index`; for `mean`, divide the sum by the mask's count.",
        ],
        brute_force="Per-sample Python loops with `math.log(sum(math.exp(...)))`: overflows for logits like ±1000.",
        approach=r"""Example: logits [2,0], target 0 → logp₀ = 2 − log(e²+1) = −0.126928, loss 0.126928; the second row is the
same by symmetry, so the mean is 0.126928. With smoothing ε = 0.1 and C = 3, the per-sample loss becomes
0.9·nll + (0.1/3)·Σ(−logp).""",
        complexity="O(N·C) time, O(N·C) space for logp.",
        pitfalls=r"""- Averaging over N instead of the number of non-ignored targets.
- Indexing `logp` with −100 (wraps around to a real column) instead of masking.
- Applying smoothing as ε·(−logp averaged over the *other* classes only): PyTorch averages over all C.""",
        follow_up="Add the `weight=` argument: per-class weights multiply each sample's loss, and `mean` divides by the sum of the weights of non-ignored targets.",
    ),
),

# ---------------------------------------------------------------- conv output size
dict(
    id="dl-conv-output-size",
    title="Convolution Output Size",
    difficulty="Easy",
    pattern="Convolutions",
    kind="function",
    entry="conv_output_size",
    description=r"""
Write `conv_output_size(h, w, kernel, stride, padding, dilation)` returning `[H_out, W_out]` for `nn.Conv2d` (or
`nn.MaxPool2d`) applied to an `h × w` input. Each of `kernel`, `stride`, `padding`, `dilation` is either an int
(same for both dimensions) or a list `[for_height, for_width]`.

`out = ⌊(size + 2·padding − dilation·(kernel − 1) − 1) / stride⌋ + 1`

If either output size would be smaller than 1, return `None` (PyTorch raises an error in that case).

**Examples:**
- `conv_output_size(32, 32, 3, 1, 1, 1)` → `[32, 32]`
- `conv_output_size(224, 224, 7, 2, 3, 1)` → `[112, 112]`
- `conv_output_size(2, 2, 5, 1, 0, 1)` → `None`
""",
    starter='''def conv_output_size(h, w, kernel, stride, padding, dilation):
    pass
''',
    solution='''def conv_output_size(h, w, kernel, stride, padding, dilation):
    pair = lambda v: (v, v) if isinstance(v, int) else (v[0], v[1])
    k, s, p, d = pair(kernel), pair(stride), pair(padding), pair(dilation)
    out = []
    for i, size in enumerate((h, w)):
        num = size + 2 * p[i] - d[i] * (k[i] - 1) - 1
        if num < 0:
            return None
        o = num // s[i] + 1
        if o < 1:
            return None
        out.append(o)
    return out
''',
    tests=[
        [32, 32, 3, 1, 1, 1],
        [224, 224, 7, 2, 3, 1],
        [2, 2, 5, 1, 0, 1],
        [28, 28, 5, 1, 0, 1],
        [32, 32, 3, 2, 1, 1],
        [31, 31, 3, 2, 1, 1],
        [64, 48, [3, 5], [1, 2], [1, 2], 1],
        [32, 32, 3, 1, 2, 2],
        [10, 10, 3, 1, 0, 5],
        [7, 7, 7, 1, 0, 1],
        [1, 1, 1, 1, 0, 1],
        [512, 512, 2, 2, 0, 1],
        [5, 100, [5, 3], [3, 3], [0, 0], [1, 1]],
    ],
    examples=3,
    wrong_solutions=[
        '''def conv_output_size(h, w, kernel, stride, padding, dilation):
    pair = lambda v: (v, v) if isinstance(v, int) else tuple(v)
    k, s, p, d = map(pair, (kernel, stride, padding, dilation))
    out = [(size + 2 * p[i] - k[i]) // s[i] + 1 for i, size in enumerate((h, w))]   # ignores dilation
    return None if min(out) < 1 else out
''',
        '''import math
def conv_output_size(h, w, kernel, stride, padding, dilation):
    pair = lambda v: (v, v) if isinstance(v, int) else tuple(v)
    k, s, p, d = map(pair, (kernel, stride, padding, dilation))
    out = [math.ceil((size + 2 * p[i] - d[i] * (k[i] - 1) - 1) / s[i]) + 1 for i, size in enumerate((h, w))]  # ceil
    return None if min(out) < 1 else out
''',
    ],
    guide=dict(
        prereqs="Padding, stride, dilation and the output-size formula in *Convolutions, pooling and building a convnet*.",
        intuition=r"""A dilated kernel spans `d·(k−1) + 1` input pixels. After padding, the input has `size + 2p` positions,
so the kernel fits at `size + 2p − span + 1` starting positions with stride 1; stride keeps every s-th of them,
counting the first.""",
        hints=[
            "Normalise each argument to a (height, width) pair.",
            "Use floor division `//` (PyTorch's default `ceil_mode=False`).",
            "If the numerator is negative the kernel does not fit even once: return None.",
        ],
        brute_force="Simulate by enumerating start positions: O(size), fine but unnecessary.",
        approach=r"""224, k7, s2, p3: (224 + 6 − 6 − 1)//2 + 1 = 223//2 + 1 = 112. 31, k3, s2, p1: (31 + 2 − 2 − 1)//2 + 1 = 16.
Dilation 5 with k3 on 10 pixels: span 11 > 10 → numerator −1 → None.""",
        complexity="O(1).",
        pitfalls=r"""- Forgetting dilation.
- Rounding up instead of down.
- Python's `//` floors negative numbers towards −∞, so check the sign before dividing.""",
        follow_up="Write the inverse for `ConvTranspose2d`: out = (in − 1)·s − 2p + d·(k − 1) + output_padding + 1.",
    ),
),

# ---------------------------------------------------------------- conv2d forward
dict(
    id="dl-conv2d-forward",
    title="Naive conv2d Forward Pass",
    difficulty="Medium",
    pattern="Convolutions",
    kind="function",
    entry="conv2d",
    compare="float",
    description=r"""
Implement `torch.nn.functional.conv2d(x, weight, bias, stride, padding)` (cross-correlation, no kernel flip).

- `x`: shape `(N, C_in, H, W)`; `weight`: shape `(C_out, C_in, kH, kW)` (kernels may be rectangular);
  `bias`: list of length `C_out` or `None`.
- `stride` and `padding` are ints applied to both spatial dimensions; padding adds zeros.
- Output shape `(N, C_out, H_out, W_out)` with `H_out = ⌊(H + 2p − kH)/s⌋ + 1` (same for width).

`out[n, o, i, j] = bias[o] + Σ_c Σ_u Σ_v weight[o, c, u, v] · x_padded[n, c, i·s + u, j·s + v]`

**Example:** `x = [[[[1,2,3],[4,5,6],[7,8,9]]]]`, `weight = [[[[1,0],[0,-1]]]]`, `bias = [0]`, stride 1, padding 0 →
`[[[[-4,-4],[-4,-4]]]]`.
""",
    starter='''import numpy as np

def conv2d(x, weight, bias, stride, padding):
    pass
''',
    solution='''import numpy as np

def conv2d(x, weight, bias, stride, padding):
    x = np.asarray(x, dtype=float)
    w = np.asarray(weight, dtype=float)
    n, c, h, wd = x.shape
    o, _, kh, kw = w.shape
    xp = np.pad(x, ((0, 0), (0, 0), (padding, padding), (padding, padding)))
    ho = (h + 2 * padding - kh) // stride + 1
    wo = (wd + 2 * padding - kw) // stride + 1
    out = np.zeros((n, o, ho, wo))
    for i in range(ho):
        for j in range(wo):
            patch = xp[:, :, i * stride:i * stride + kh, j * stride:j * stride + kw]   # (N, C, kh, kw)
            out[:, :, i, j] = np.tensordot(patch, w, axes=([1, 2, 3], [1, 2, 3]))
    if bias is not None:
        out += np.asarray(bias, dtype=float)[None, :, None, None]
    return out
''',
    tests=[
        [[[[[1, 2, 3], [4, 5, 6], [7, 8, 9]]]], [[[[1, 0], [0, -1]]]], [0], 1, 0],
        [[[[[1, 2, 3], [4, 5, 6], [7, 8, 9]]]], [[[[1, 1, 1], [1, 1, 1], [1, 1, 1]]]], [1], 1, 1],
        [[[[[1, 2, 3], [4, 5, 6], [7, 8, 9]]]], [[[[1, 1, 1], [1, 1, 1], [1, 1, 1]]]], None, 2, 1],
        [_r(2, 3, 5, 5), _r(4, 3, 3, 3), _r(4), 1, 0],
        [_r(2, 3, 5, 5), _r(4, 3, 3, 3), _r(4), 2, 1],
        [_r(1, 2, 6, 4), _r(3, 2, 2, 3), None, 1, 0],
        [_r(1, 1, 4, 4), _r(1, 1, 1, 1), _r(1), 1, 0],
        [_r(3, 2, 7, 7), _r(2, 2, 5, 5), _r(2), 2, 2],
        [_r(1, 4, 3, 3), _r(5, 4, 3, 3), _r(5), 1, 0],
        [_r(1, 1, 8, 8), _r(2, 1, 3, 3), [0.5, -0.5], 3, 1],
    ],
    examples=2,
    wrong_solutions=[
        '''import numpy as np
def conv2d(x, weight, bias, stride, padding):
    x, w = np.asarray(x, float), np.asarray(weight, float)
    n, c, h, wd = x.shape; o, _, kh, kw = w.shape
    xp = np.pad(x, ((0, 0), (0, 0), (padding, padding), (padding, padding)))
    ho, wo = (h + 2 * padding - kh) // stride + 1, (wd + 2 * padding - kw) // stride + 1
    out = np.zeros((n, o, ho, wo)); wf = w[:, :, ::-1, ::-1]          # flips the kernel (true convolution)
    for i in range(ho):
        for j in range(wo):
            out[:, :, i, j] = np.tensordot(xp[:, :, i*stride:i*stride+kh, j*stride:j*stride+kw], wf, axes=([1,2,3],[1,2,3]))
    return out + (np.asarray(bias, float)[None, :, None, None] if bias is not None else 0)
''',
        '''import numpy as np
def conv2d(x, weight, bias, stride, padding):
    x, w = np.asarray(x, float), np.asarray(weight, float)
    n, c, h, wd = x.shape; o, _, kh, kw = w.shape
    xp = np.pad(x, ((0, 0), (0, 0), (padding, padding), (padding, padding)))
    ho, wo = (h + 2 * padding - kh) // stride + 1, (wd + 2 * padding - kw) // stride + 1
    out = np.zeros((n, o, ho, wo))
    for i in range(ho):
        for j in range(wo):
            out[:, :, i, j] = np.tensordot(xp[:, :, i:i+kh, j:j+kw], w, axes=([1,2,3],[1,2,3]))   # ignores stride in the window
    return out + (np.asarray(bias, float)[None, :, None, None] if bias is not None else 0)
''',
    ],
    guide=dict(
        prereqs="*Convolutions, pooling and building a convnet* (the formula and the naive NumPy version).",
        intuition=r"""Every output pixel is a dot product between one kernel and the patch beneath it, summed over **all**
input channels. Looping over output positions and doing the channel/kernel sums with one `tensordot` keeps the code
short and handles the batch and output channels at once.""",
        hints=[
            "Pad only the last two axes: `np.pad(x, ((0,0),(0,0),(p,p),(p,p)))`.",
            "The patch for output (i, j) starts at row `i*stride`, column `j*stride`.",
            "`np.tensordot(patch, w, axes=([1,2,3],[1,2,3]))` gives an (N, C_out) block.",
        ],
        brute_force="Six nested loops (n, o, i, j, c, u, v): correct, O(N·C_out·H_out·W_out·C_in·kH·kW), slow in Python.",
        approach=r"""Example: kernel [[1,0],[0,−1]] computes x[i,j] − x[i+1,j+1]: 1−5 = −4, 2−6 = −4, 4−8 = −4, 5−9 = −4.
With an all-ones 3×3 kernel, padding 1 and bias 1, the centre output is 45 + 1 = 46 and the corner is 1+2+4+5+1 = 13.""",
        complexity="O(N · C_out · H_out · W_out · C_in · kH · kW) multiply-adds; O(output) extra space.",
        pitfalls=r"""- Flipping the kernel: deep-learning 'convolution' is cross-correlation.
- Forgetting the stride when slicing the window.
- Rectangular kernels: use kH and kW separately.
- `bias=None` must not add anything.""",
        follow_up="Vectorise completely with `sliding_window_view` + `einsum` (im2col), then implement the backward pass: grad_x is a transposed convolution of grad_out with the kernels.",
    ),
),

# ---------------------------------------------------------------- max pool
dict(
    id="dl-maxpool2d",
    title="max_pool2d with Stride and Padding",
    difficulty="Medium",
    pattern="Convolutions",
    kind="function",
    entry="max_pool2d",
    compare="float",
    description=r"""
Implement `torch.nn.functional.max_pool2d(x, kernel_size, stride, padding)` for `x` of shape `(N, C, H, W)`.

- `stride` may be `None`, meaning "equal to `kernel_size`".
- `padding` pads both spatial dimensions with **−infinity** (padding never wins a max). It satisfies
  `padding ≤ kernel_size // 2`.
- Output size `⌊(H + 2p − k)/s⌋ + 1` (floor mode), same for width; each channel is pooled independently.

**Example:** `x = [[[[1,2,3,4],[5,6,7,8],[9,10,11,12],[13,14,15,16]]]]`, `kernel_size=2`, `stride=None`, `padding=0`
→ `[[[[6,8],[14,16]]]]`.
""",
    starter='''import numpy as np

def max_pool2d(x, kernel_size, stride, padding):
    pass
''',
    solution='''import numpy as np

def max_pool2d(x, kernel_size, stride, padding):
    x = np.asarray(x, dtype=float)
    k = kernel_size
    s = k if stride is None else stride
    p = padding
    n, c, h, w = x.shape
    xp = np.pad(x, ((0, 0), (0, 0), (p, p), (p, p)), constant_values=-np.inf)
    ho = (h + 2 * p - k) // s + 1
    wo = (w + 2 * p - k) // s + 1
    out = np.empty((n, c, ho, wo))
    for i in range(ho):
        for j in range(wo):
            out[:, :, i, j] = xp[:, :, i * s:i * s + k, j * s:j * s + k].max(axis=(2, 3))
    return out
''',
    tests=[
        [[[[[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12], [13, 14, 15, 16]]]], 2, None, 0],
        [[[[[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12], [13, 14, 15, 16]]]], 3, 1, 0],
        [[[[[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12], [13, 14, 15, 16]]]], 2, 2, 1],
        [[[[[-5, -4, -3], [-2, -1, -6], [-7, -8, -9]]]], 2, 1, 1],
        [_r(2, 3, 5, 5), 2, None, 0],
        [_r(2, 3, 5, 5), 3, 2, 1],
        [_r(1, 2, 7, 6), 3, 3, 0],
        [_r(1, 1, 1, 1), 1, None, 0],
        [_r(2, 2, 8, 8), 4, 2, 2],
        [_r(1, 3, 6, 9), 2, 1, 0],
    ],
    examples=2,
    wrong_solutions=[
        '''import numpy as np
def max_pool2d(x, kernel_size, stride, padding):
    x = np.asarray(x, float); k = kernel_size; s = k if stride is None else stride; p = padding
    n, c, h, w = x.shape
    xp = np.pad(x, ((0, 0), (0, 0), (p, p), (p, p)))                 # pads with 0, which can win the max
    ho, wo = (h + 2 * p - k) // s + 1, (w + 2 * p - k) // s + 1
    out = np.empty((n, c, ho, wo))
    for i in range(ho):
        for j in range(wo):
            out[:, :, i, j] = xp[:, :, i*s:i*s+k, j*s:j*s+k].max(axis=(2, 3))
    return out
''',
        '''import numpy as np
def max_pool2d(x, kernel_size, stride, padding):
    x = np.asarray(x, float); k = kernel_size; s = 1 if stride is None else stride   # wrong default stride
    p = padding; n, c, h, w = x.shape
    xp = np.pad(x, ((0, 0), (0, 0), (p, p), (p, p)), constant_values=-np.inf)
    ho, wo = (h + 2 * p - k) // s + 1, (w + 2 * p - k) // s + 1
    out = np.empty((n, c, ho, wo))
    for i in range(ho):
        for j in range(wo):
            out[:, :, i, j] = xp[:, :, i*s:i*s+k, j*s:j*s+k].max(axis=(2, 3))
    return out
''',
    ],
    guide=dict(
        prereqs="Pooling in *Convolutions, pooling and building a convnet*; the `dl-conv-output-size` problem.",
        intuition=r"""Max pooling is a convolution-shaped scan whose 'kernel' takes the maximum instead of a weighted sum, on
each channel separately. Padding uses −∞ so that a padded cell can never be the maximum, even when all real values
are negative.""",
        hints=[
            "Default stride: `s = kernel_size if stride is None else stride`.",
            "`np.pad(..., constant_values=-np.inf)` for the spatial axes only.",
            "Take `.max(axis=(2, 3))` over each window to handle all N and C at once.",
        ],
        brute_force="Loop over n, c, i, j and the window: O(N·C·H_out·W_out·k²), same order as the vectorised window loop.",
        approach=r"""Example 1: 2×2 blocks of the 4×4 grid give maxima 6, 8, 14, 16. Example with all-negative input and padding 1:
zero padding would wrongly return 0 in border windows; −∞ padding returns the true border maxima.""",
        complexity="O(N · C · H_out · W_out · k²) time.",
        pitfalls=r"""- Zero padding instead of −∞.
- Default stride is the kernel size, not 1.
- Floor mode: a partial window at the end is discarded unless padding makes it fit.""",
        follow_up="Return the argmax indices too (`return_indices=True`) and implement `max_unpool2d`, which U-Net-like decoders such as SegNet use.",
    ),
),

# ---------------------------------------------------------------- receptive field
dict(
    id="dl-receptive-field",
    title="Receptive Field of a Conv Stack",
    difficulty="Medium",
    pattern="Convolutions",
    kind="function",
    entry="receptive_field",
    description=r"""
Each layer of a stack is given as `[kernel, stride, dilation]` (pooling layers are layers too, with dilation 1).
Starting from the input with receptive field `r = 1` and jump `j = 1` (distance in input pixels between neighbouring
units), each layer updates

- effective kernel `k_eff = dilation · (kernel − 1) + 1`
- `r = r + (k_eff − 1) · j`
- `j = j · stride`

Write `receptive_field(layers)` returning `[r, j]` after the last layer, and also the receptive field after each
layer: return `[r_final, j_final, [r_after_layer_1, r_after_layer_2, ...]]`.

**Example:** two 3×3 convs (stride 1) then a 2×2 max-pool (stride 2) then a 3×3 conv:
`[[3,1,1],[3,1,1],[2,2,1],[3,1,1]]` → `[10, 2, [3, 5, 6, 10]]`.
""",
    starter='''def receptive_field(layers):
    pass
''',
    solution='''def receptive_field(layers):
    r, j = 1, 1
    history = []
    for k, s, d in layers:
        k_eff = d * (k - 1) + 1
        r = r + (k_eff - 1) * j
        j = j * s
        history.append(r)
    return [r, j, history]
''',
    tests=[
        [[[3, 1, 1], [3, 1, 1], [2, 2, 1], [3, 1, 1]]],
        [[]],
        [[[3, 1, 1]]],
        [[[7, 2, 1], [3, 2, 1]]],
        [[[3, 1, 1], [3, 1, 2], [3, 1, 4], [3, 1, 8]]],
        [[[3, 2, 1]] * 5],
        [[[1, 1, 1], [1, 1, 1]]],
        [[[5, 1, 1], [2, 2, 1], [5, 1, 1], [2, 2, 1]]],
        [[[7, 2, 1], [3, 2, 1], [3, 1, 1], [3, 1, 1], [3, 2, 1], [3, 1, 1], [3, 2, 1], [3, 1, 1], [3, 2, 1], [3, 1, 1]]],
        [[[2, 2, 1], [2, 2, 1], [2, 2, 1]]],
    ],
    examples=2,
    wrong_solutions=[
        '''def receptive_field(layers):
    r, j, hist = 1, 1, []
    for k, s, d in layers:
        r = r + (k - 1) * j                      # ignores dilation
        j = j * s
        hist.append(r)
    return [r, j, hist]
''',
        '''def receptive_field(layers):
    r, j, hist = 1, 1, []
    for k, s, d in layers:
        k_eff = d * (k - 1) + 1
        j = j * s                                # updates the jump too early
        r = r + (k_eff - 1) * j
        hist.append(r)
    return [r, j, hist]
''',
    ],
    guide=dict(
        prereqs="Receptive fields in *Convolutions, pooling and building a convnet*.",
        intuition=r"""A layer with kernel k looks at k neighbouring units of the previous layer. Neighbouring units of that
layer are `j` input pixels apart, so the new layer sees `(k − 1)·j` extra input pixels. Striding then spreads the new
layer's units `s` times further apart.""",
        hints=[
            "Start with r = 1, j = 1.",
            "Dilation spreads the kernel taps: k_eff = d(k − 1) + 1.",
            "Update r using the jump **before** multiplying the jump by this layer's stride.",
        ],
        brute_force="Propagate a single 'active' input pixel through the stack with real convolutions and measure the support: correct but O(image size × layers).",
        approach=r"""Example: conv3 → r = 1 + 2·1 = 3; conv3 → 5; pool2/s2 → 5 + 1·1 = 6, j = 2; conv3 → 6 + 2·2 = 10.
Dilated stack 1, 2, 4, 8 grows exponentially: 3, 7, 15, 31.""",
        complexity="O(number of layers).",
        pitfalls=r"""- Multiplying the jump before using it.
- Forgetting dilation.
- An empty stack has r = 1, j = 1.""",
        follow_up="Track the centre of the first unit's receptive field as well (it depends on padding), or compute the *effective* receptive field, which is much smaller than the theoretical one because central pixels dominate.",
    ),
),
]
