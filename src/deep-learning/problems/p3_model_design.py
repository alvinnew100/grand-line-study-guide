import numpy as _np

_rng = _np.random.RandomState(33)


def _r(*shape, scale=1.0, shift=0.0):
    return (_rng.randn(*shape) * scale + shift).round(3).tolist()


def _mask(*shape, p=0.5):
    return (_rng.rand(*shape) >= p).astype(int).tolist()


PROBLEMS = [
# ---------------------------------------------------------------- dropout
dict(
    id="dl-dropout",
    title="Inverted Dropout (Train vs Eval)",
    difficulty="Easy",
    pattern="Regularisation",
    kind="function",
    entry="dropout",
    compare="float",
    description=r"""
Implement `torch.nn.functional.dropout(x, p, training)` with the random choice made explicit so results are
reproducible: `mask` has the same shape as `x` and holds 1 (keep) or 0 (drop).

`dropout(x, mask, p, training)`:

- If `training` is false, or `p == 0`, return `x` unchanged (the mask is ignored).
- If `p == 1`, every element is dropped: return zeros of the same shape.
- Otherwise return `x * mask / (1 - p)` (inverted dropout: survivors are scaled up so the expected value is unchanged).

`x` and `mask` are nested lists of any shape.

**Example:** `x=[1, 2, 3, 4]`, `mask=[1, 0, 1, 0]`, `p=0.5`, `training=True` → `[2, 0, 6, 0]`.
""",
    starter='''def dropout(x, mask, p, training):
    pass
''',
    solution='''import numpy as np

def dropout(x, mask, p, training):
    a = np.asarray(x, dtype=float)
    if not training or p == 0:
        return a
    if p == 1:
        return np.zeros_like(a)
    return a * np.asarray(mask, dtype=float) / (1.0 - p)
''',
    tests=[
        [[1, 2, 3, 4], [1, 0, 1, 0], 0.5, True],
        [[1, 2, 3, 4], [1, 0, 1, 0], 0.5, False],
        [[1, 2, 3, 4], [0, 0, 0, 0], 0.0, True],
        [[1, 2, 3, 4], [1, 1, 1, 1], 1.0, True],
        [[[1, -1], [2, -2]], [[1, 1], [0, 1]], 0.2, True],
        [_r(3, 4), _mask(3, 4, p=0.1), 0.1, True],
        [_r(2, 3, 4), _mask(2, 3, 4, p=0.75), 0.75, True],
        [_r(2, 3, 4), _mask(2, 3, 4, p=0.75), 0.75, False],
        [[], [], 0.5, True],
        [[5.0], [1], 0.9, True],
    ],
    examples=2,
    wrong_solutions=[
        '''import numpy as np
def dropout(x, mask, p, training):
    a = np.asarray(x, float)
    if not training: return a
    return a * np.asarray(mask, float)                  # no inverted scaling
''',
        '''import numpy as np
def dropout(x, mask, p, training):
    a = np.asarray(x, float)
    if p == 1: return np.zeros_like(a)
    return a * np.asarray(mask, float) / (1 - p)        # applies dropout in eval mode too
''',
    ],
    guide=dict(
        prereqs="Dropout and inverted scaling in *Training a convnet and fighting overfitting*.",
        intuition=r"""Each unit survives with probability 1 − p. Dividing survivors by 1 − p makes the expected output equal to
the input, so evaluation can use the network unchanged (dropout becomes the identity).""",
        hints=[
            "Handle the identity cases first: eval mode or p == 0.",
            "p == 1 would divide by zero: return zeros.",
            "Otherwise multiply by the mask and divide by (1 − p).",
        ],
        brute_force="Element-wise Python loops over nested lists: correct but awkward for arbitrary shapes; NumPy handles any shape.",
        approach="Example: [1,2,3,4]·[1,0,1,0]/0.5 = [2,0,6,0]. In eval mode the same call returns [1,2,3,4].",
        complexity="O(number of elements).",
        pitfalls=r"""- Forgetting the 1/(1 − p) scale (then eval-time activations are larger than training-time ones).
- Applying dropout when `training` is false.
- Dividing by zero for p = 1.""",
        follow_up="Implement Dropout2d: one mask value per (sample, channel) broadcast over height and width.",
    ),
),

# ---------------------------------------------------------------- batchnorm
dict(
    id="dl-batchnorm-forward",
    title="BatchNorm2d Forward in Train and Eval Mode",
    difficulty="Medium",
    pattern="Normalisation",
    kind="function",
    entry="batchnorm2d",
    compare="float",
    tolerance=1e-6,
    description=r"""
Implement the forward pass of `nn.BatchNorm2d` including its running-statistics update.

`batchnorm2d(x, gamma, beta, running_mean, running_var, training, momentum, eps)` with `x` of shape `(N, C, H, W)`
and the other vectors of length `C`. Return `[y, new_running_mean, new_running_var]`.

- **Training mode**: for each channel compute the mean and the **biased** variance (divide by `m = N·H·W`) over
  axes (N, H, W) and normalise with them: `x_hat = (x − mean)/sqrt(var + eps)`. Update the running statistics with
  `running = (1 − momentum)·running + momentum·stat`, where the variance used here is the **unbiased** one
  (`var · m/(m − 1)`). Every test has `m ≥ 2`.
- **Eval mode**: normalise with `running_mean` and `running_var`, and return them unchanged.
- In both modes, `y = gamma[c] · x_hat + beta[c]`.

**Example:** `x=[[[[1]],[[2]]],[[[3]],[[6]]]]` (N=2, C=2, 1×1), `gamma=[1,1]`, `beta=[0,0]`, running `[0,0]`/`[1,1]`,
training, momentum 0.1, eps 0 → channel 0 values (1, 3): mean 2, var 1 → y = −1, 1; channel 1 (2, 6): mean 4, var 4 →
y = −1, 1; new running mean `[0.2, 0.4]`, new running var `[0.9 + 0.1·2, 0.9 + 0.1·8] = [1.1, 1.7]`.
""",
    starter='''import numpy as np

def batchnorm2d(x, gamma, beta, running_mean, running_var, training, momentum, eps):
    pass
''',
    solution='''import numpy as np

def batchnorm2d(x, gamma, beta, running_mean, running_var, training, momentum, eps):
    x = np.asarray(x, dtype=float)
    g = np.asarray(gamma, dtype=float)[None, :, None, None]
    b = np.asarray(beta, dtype=float)[None, :, None, None]
    rm = np.asarray(running_mean, dtype=float)
    rv = np.asarray(running_var, dtype=float)
    if training:
        mean = x.mean(axis=(0, 2, 3))
        var = x.var(axis=(0, 2, 3))
        m = x.shape[0] * x.shape[2] * x.shape[3]
        rm = (1 - momentum) * rm + momentum * mean
        rv = (1 - momentum) * rv + momentum * var * m / (m - 1)
    else:
        mean, var = rm, rv
    x_hat = (x - mean[None, :, None, None]) / np.sqrt(var[None, :, None, None] + eps)
    return [g * x_hat + b, rm, rv]
''',
    tests=[
        [[[[[1]], [[2]]], [[[3]], [[6]]]], [1, 1], [0, 0], [0, 0], [1, 1], True, 0.1, 0.0],
        [[[[[1]], [[2]]], [[[3]], [[6]]]], [1, 1], [0, 0], [0, 0], [1, 1], False, 0.1, 0.0],
        [_r(4, 3, 2, 2, scale=2, shift=5), [1, 2, 0.5], [0, -1, 3], [0, 0, 0], [1, 1, 1], True, 0.1, 1e-5],
        [_r(4, 3, 2, 2, scale=2, shift=5), [1, 2, 0.5], [0, -1, 3], [5, 5, 5], [4, 4, 4], False, 0.1, 1e-5],
        [_r(2, 1, 3, 3), [1], [0], [0.5], [2.0], True, 0.5, 1e-5],
        [_r(8, 2, 1, 1), [0.3, -0.7], [0.1, 0.2], [1, -1], [0.5, 2], True, 0.01, 1e-3],
        [[[[[7, 7], [7, 7]]]], [1], [0], [0], [1], True, 0.1, 1e-5],
        [[[[[7, 7], [7, 7]]]], [1], [0], [5], [4], False, 0.1, 1e-5],
        [_r(3, 4, 5, 5, scale=10), [1, 1, 1, 1], [0, 0, 0, 0], [0, 0, 0, 0], [1, 1, 1, 1], True, 1.0, 1e-5],
        [_r(16, 2, 4, 4, scale=0.1), [2, 3], [1, 1], [0, 0], [1, 1], True, 0.1, 1e-5],
    ],
    examples=2,
    wrong_solutions=[
        '''import numpy as np
def batchnorm2d(x, gamma, beta, running_mean, running_var, training, momentum, eps):
    x = np.asarray(x, float); g = np.asarray(gamma, float)[None, :, None, None]; b = np.asarray(beta, float)[None, :, None, None]
    rm, rv = np.asarray(running_mean, float), np.asarray(running_var, float)
    mean, var = x.mean(axis=(0, 2, 3)), x.var(axis=(0, 2, 3))           # batch stats even in eval mode
    if training:
        m = x.shape[0] * x.shape[2] * x.shape[3]
        rm = (1 - momentum) * rm + momentum * mean; rv = (1 - momentum) * rv + momentum * var * m / (m - 1)
    xh = (x - mean[None, :, None, None]) / np.sqrt(var[None, :, None, None] + eps)
    return [g * xh + b, rm, rv]
''',
        '''import numpy as np
def batchnorm2d(x, gamma, beta, running_mean, running_var, training, momentum, eps):
    x = np.asarray(x, float); g = np.asarray(gamma, float)[None, :, None, None]; b = np.asarray(beta, float)[None, :, None, None]
    rm, rv = np.asarray(running_mean, float), np.asarray(running_var, float)
    if training:
        mean, var = x.mean(axis=(0, 2, 3)), x.var(axis=(0, 2, 3))
        rm = (1 - momentum) * rm + momentum * mean; rv = (1 - momentum) * rv + momentum * var   # biased running var
    else:
        mean, var = rm, rv
    xh = (x - mean[None, :, None, None]) / np.sqrt(var[None, :, None, None] + eps)
    return [g * xh + b, rm, rv]
''',
    ],
    guide=dict(
        prereqs="Batch normalisation, running statistics and train/eval behaviour in *Normalisation layers and weight initialisation*.",
        intuition=r"""Training mode standardises each channel with the current batch and nudges the running averages towards
the batch statistics; eval mode freezes those averages and uses them instead, so predictions do not depend on the
rest of the batch. γ and β then rescale and shift each channel.""",
        hints=[
            "Reduce over axes (0, 2, 3); reshape per-channel vectors to (1, C, 1, 1) to broadcast.",
            "Normalise with the biased variance, but update `running_var` with the unbiased one (× m/(m−1)).",
            "In eval mode return the running statistics untouched.",
        ],
        brute_force="Loop over channels collecting values into lists: same O(N·C·H·W) work, more code.",
        approach=r"""Example channel 1 values 2 and 6: mean 4, biased var 4 → x_hat = ∓1. Unbiased var = 4·2/1 = 8, so
running_var = 0.9·1 + 0.1·8 = 1.7; running_mean = 0.9·0 + 0.1·4 = 0.4.""",
        complexity="O(N·C·H·W).",
        pitfalls=r"""- Using batch statistics in eval mode.
- Updating the running variance with the biased estimate.
- Forgetting eps inside the square root (a constant channel then divides by zero).
- `momentum` weights the **new** value (PyTorch's convention), unlike optimiser momentum.""",
        follow_up="Write the backward pass (gradients for x, γ, β); the x-gradient has three terms because the batch mean and variance depend on every element.",
    ),
),

# ---------------------------------------------------------------- early stopping
dict(
    id="dl-early-stopping",
    title="Early Stopping with Patience and min_delta",
    difficulty="Easy",
    pattern="Training Loop",
    kind="function",
    entry="early_stopping",
    description=r"""
Simulate an early-stopping monitor on a list of validation losses (one per epoch, epochs numbered from 0).

`early_stopping(val_losses, patience, min_delta)`:

- Keep `best` (initially +infinity), `best_epoch` (initially −1) and a counter `bad` (initially 0).
- For each epoch `i`: if `val_losses[i] < best − min_delta`, it is an improvement: `best = val_losses[i]`,
  `best_epoch = i`, `bad = 0`. Otherwise `bad += 1`, and if `bad >= patience`, training stops **at epoch `i`**.
- Return `[stop_epoch, best_epoch]`, where `stop_epoch` is the epoch at which training stopped, or the last epoch
  index if it never stopped. The list is non-empty.

**Example:** `[1.0, 0.8, 0.85, 0.9, 0.95]`, `patience=2`, `min_delta=0` → improvements at 0 and 1; epochs 2 and 3
are not → stop at 3 → `[3, 1]`.
""",
    starter='''def early_stopping(val_losses, patience, min_delta):
    pass
''',
    solution='''def early_stopping(val_losses, patience, min_delta):
    best, best_epoch, bad = float("inf"), -1, 0
    for i, loss in enumerate(val_losses):
        if loss < best - min_delta:
            best, best_epoch, bad = loss, i, 0
        else:
            bad += 1
            if bad >= patience:
                return [i, best_epoch]
    return [len(val_losses) - 1, best_epoch]
''',
    tests=[
        [[1.0, 0.8, 0.85, 0.9, 0.95], 2, 0.0],
        [[1.0, 0.9, 0.8, 0.7], 2, 0.0],
        [[0.5], 1, 0.0],
        [[1.0, 1.0, 1.0, 1.0], 3, 0.0],
        [[1.0, 0.99, 0.985, 0.98, 0.979], 2, 0.01],
        [[1.0, 0.8, 0.9, 0.7, 0.75, 0.76, 0.6], 2, 0.0],
        [[1.0, 0.8, 0.9, 0.7, 0.75, 0.76, 0.6], 3, 0.0],
        [[2.0, 1.0, 1.5, 0.5], 1, 0.0],
        [[3, 2, 1, 2, 3, 4, 5, 6], 10, 0.0],
        [[0.7, 0.6999, 0.6998], 1, 0.001],
        [[1.0, 0.8, 0.8, 0.8], 2, 0.0],
    ],
    examples=2,
    wrong_solutions=[
        '''def early_stopping(val_losses, patience, min_delta):
    best, best_epoch, bad = float("inf"), -1, 0
    for i, loss in enumerate(val_losses):
        if loss < best - min_delta:
            best, best_epoch = loss, i                    # never resets the counter
        else:
            bad += 1
            if bad >= patience: return [i, best_epoch]
    return [len(val_losses) - 1, best_epoch]
''',
        '''def early_stopping(val_losses, patience, min_delta):
    best, best_epoch, bad = float("inf"), -1, 0
    for i, loss in enumerate(val_losses):
        if loss <= best - min_delta:                      # ties count as improvements
            best, best_epoch, bad = loss, i, 0
        else:
            bad += 1
            if bad >= patience: return [i, best_epoch]
    return [len(val_losses) - 1, best_epoch]
''',
    ],
    guide=dict(
        prereqs="Early stopping in *Training a convnet and fighting overfitting* and *Optimisers and validation*.",
        intuition=r"""Validation loss is noisy, so you wait `patience` non-improving epochs before giving up, and only count
improvements bigger than `min_delta`. The checkpoint to restore is the best epoch, not the stopping epoch.""",
        hints=[
            "Strict inequality: `loss < best - min_delta`.",
            "Reset `bad` to 0 on every improvement.",
            "Stop in the same epoch that makes `bad` reach `patience`.",
        ],
        brute_force="Already a single pass; nothing simpler exists.",
        approach=r"""[1.0, 0.8, 0.9, 0.7, 0.75, 0.76, 0.6] with patience 2: improvements at 0, 1, 3; epochs 4 and 5 are bad → stop
at 5 with best epoch 3. With patience 3 training reaches epoch 6, which improves, so the result is [6, 6].""",
        complexity="O(epochs).",
        pitfalls=r"""- Not resetting the counter after an improvement.
- Treating an equal loss as an improvement.
- Forgetting `min_delta` (tiny noisy improvements would keep training alive forever).""",
        follow_up="Monitor a metric to maximise (accuracy, F1) by flipping the comparison, as PyTorch Lightning's `mode='max'` does.",
    ),
),
]
