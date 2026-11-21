import numpy as _np

_rng = _np.random.RandomState(11)


def _imgs(n, c, h, w, scale=1.0, shift=0.0):
    return (_rng.rand(n, c, h, w) * scale + shift).round(3).tolist()


def _grads(steps, d, scale=1.0):
    return (_rng.randn(steps, d) * scale).round(3).tolist()


PROBLEMS = [
# ---------------------------------------------------------------- channel normalize
dict(
    id="dl-channel-normalize",
    title="Per-Channel Normalisation with Training Statistics",
    difficulty="Easy",
    pattern="Data Preparation",
    kind="function",
    entry="normalize_with_train_stats",
    compare="float",
    description=r"""
Image models expect every colour channel to be standardised with the **training set's** per-channel mean and
standard deviation (this is what `transforms.Normalize(mean, std)` applies).

Write `normalize_with_train_stats(train, x)`:

- `train` and `x` are batches of images as nested lists of shape `(N, C, H, W)` (same `C`, `H`, `W`).
- For each channel `c`, compute the mean and the **population** standard deviation (divide by the count, like
  `np.std`) over **all** training images, rows and columns of that channel.
- If a channel's standard deviation is 0, use 1 instead.
- Return `x` normalised as `(x - mean[c]) / std[c]`, same shape as `x`.

**Example:** `train = [[[[0, 2]]], [[[4, 6]]]]` (2 images, 1 channel, 1×2) has mean 3 and std √5 ≈ 2.2361, so
`x = [[[[3, 8]]]]` → `[[[[0.0, 2.2361]]]]`.
""",
    starter='''import numpy as np

def normalize_with_train_stats(train, x):
    pass
''',
    solution='''import numpy as np

def normalize_with_train_stats(train, x):
    t = np.asarray(train, dtype=float)
    a = np.asarray(x, dtype=float)
    mean = t.mean(axis=(0, 2, 3))
    std = t.std(axis=(0, 2, 3))
    std[std == 0] = 1.0
    return (a - mean[None, :, None, None]) / std[None, :, None, None]
''',
    tests=[
        [[[[[0, 2]]], [[[4, 6]]]], [[[[3, 8]]]]],
        [[[[[1, 1], [1, 1]], [[0, 10], [20, 30]]]], [[[[1, 2], [0, 1]], [[15, 15], [0, 30]]]]],
        [[[[[5]]]], [[[[5]]], [[[7]]]]],
        [_imgs(4, 3, 4, 4, 255), _imgs(2, 3, 4, 4, 255)],
        [_imgs(8, 1, 3, 5), _imgs(3, 1, 3, 5)],
        [_imgs(2, 4, 2, 2, 10, -5), _imgs(1, 4, 2, 2, 10, -5)],
        [_imgs(5, 3, 6, 6, 1.0), _imgs(5, 3, 6, 6, 1.0)],
        [[[[[2, 2]], [[1, 3]]], [[[2, 2]], [[5, 7]]]], [[[[0, 4]], [[4, 4]]]]],
        [_imgs(16, 2, 8, 8, 100, 50), _imgs(4, 2, 8, 8, 100, 50)],
    ],
    examples=2,
    wrong_solutions=[
        '''import numpy as np
def normalize_with_train_stats(train, x):
    a = np.asarray(x, dtype=float)
    mean, std = a.mean(axis=(0, 2, 3)), a.std(axis=(0, 2, 3))   # stats from x: leakage
    std[std == 0] = 1.0
    return (a - mean[None, :, None, None]) / std[None, :, None, None]
''',
        '''import numpy as np
def normalize_with_train_stats(train, x):
    t, a = np.asarray(train, float), np.asarray(x, float)
    mean, std = t.mean(), t.std()                                 # one global mean, not per channel
    return (a - mean) / (std if std else 1.0)
''',
    ],
    guide=dict(
        prereqs="Standardisation and the N × C × H × W layout from the *Real-world data as tensors* lesson; broadcasting from the *Tensors* lesson.",
        intuition=r"""Each channel is a different measurement (red, green, blue), so each gets its own mean and spread. The
statistics are a property of the **training** data and are reused unchanged on every future input; computing them on
the data being normalised would leak information and make validation scores optimistic.""",
        hints=[
            "Convert both inputs with `np.asarray(..., dtype=float)`.",
            "Reduce over every axis except the channel: `axis=(0, 2, 3)`.",
            "Reshape the per-channel vectors to `(1, C, 1, 1)` (e.g. `mean[None, :, None, None]`) so they broadcast.",
        ],
        brute_force="Loop over channels and pixels in Python, summing values per channel: same O(N·C·H·W) work, far slower.",
        approach=r"""1. `t = np.asarray(train, float)`; `mean = t.mean(axis=(0,2,3))`; `std = t.std(axis=(0,2,3))`.
2. Replace zero stds with 1 to avoid dividing by zero (a constant channel then becomes `x - mean`).
3. Return `(x - mean[None,:,None,None]) / std[None,:,None,None]`.

Dry run on the example: training values 0, 2, 4, 6 → mean 3, variance (9+1+1+9)/4 = 5, std 2.2361. For x = 3 → 0;
x = 8 → 5/2.2361 = 2.2361.""",
        complexity="O(N·C·H·W) time for the statistics and the transform; O(size of x) extra space.",
        pitfalls=r"""- Computing statistics on `x` instead of `train` (leakage).
- Using one global mean instead of one per channel.
- Using the sample standard deviation (`ddof=1`): the spec asks for the population version.
- Forgetting the zero-std guard.""",
        follow_up="Real pipelines compute these statistics once over the training set (streaming over batches with running sums of x and x²) and store them with the model.",
    ),
),

# ---------------------------------------------------------------- broadcast shape
dict(
    id="dl-broadcast-shape",
    title="Broadcast Result Shape",
    difficulty="Easy",
    pattern="Tensors",
    kind="function",
    entry="broadcast_shape",
    description=r"""
Implement the broadcasting rule shared by NumPy and PyTorch. Given two shapes `a` and `b` (lists of non-negative
integers, possibly empty for scalars), return the shape of the result of an element-wise operation, or `None` if the
shapes cannot be broadcast.

Rule: compare sizes from the **rightmost** dimension leftwards, treating missing dimensions as size 1. Two sizes are
compatible when they are equal or when one of them is 1; the result size is the other one (so `1` with `0` gives `0`).
Any incompatible pair makes the whole broadcast fail.

**Examples:**
- `a = [8, 1, 6], b = [7, 1]` → `[8, 7, 6]`
- `a = [3, 4], b = [3]` → `None`
- `a = [], b = [2, 3]` → `[2, 3]`
""",
    starter='''def broadcast_shape(a, b):
    pass
''',
    solution='''def broadcast_shape(a, b):
    out = []
    n = max(len(a), len(b))
    for i in range(1, n + 1):
        da = a[-i] if i <= len(a) else 1
        db = b[-i] if i <= len(b) else 1
        if da == db or db == 1:
            out.append(da)
        elif da == 1:
            out.append(db)
        else:
            return None
    return out[::-1]
''',
    tests=[
        [[8, 1, 6], [7, 1]],
        [[3, 4], [3]],
        [[], [2, 3]],
        [[32, 10], [10]],
        [[3, 224, 224], [3, 1, 1]],
        [[4], [4, 1]],
        [[], []],
        [[1], [0]],
        [[0], [3]],
        [[2, 1, 3, 1], [5, 1, 4]],
        [[5, 1, 4], [2, 1, 3, 1]],
        [[1, 1, 1], [1]],
        [[6, 7], [6, 7]],
        [[2, 3], [3, 2]],
        [[1, 2, 3, 4, 5, 6], [6]],
    ],
    examples=3,
    wrong_solutions=[
        '''def broadcast_shape(a, b):
    out = []
    for x, y in zip(a, b):            # aligns from the LEFT and drops extra dims
        if x == y or y == 1: out.append(x)
        elif x == 1: out.append(y)
        else: return None
    return out
''',
        '''def broadcast_shape(a, b):
    out = []
    n = max(len(a), len(b))
    for i in range(1, n + 1):
        da = a[-i] if i <= len(a) else 1
        db = b[-i] if i <= len(b) else 1
        if da != db and 1 not in (da, db): return None
        out.append(max(da, db))       # wrong when one size is 0 and the other 1
    return out[::-1]
''',
    ],
    guide=dict(
        prereqs="Broadcasting section of the *Tensors: creation, indexing, dtypes and broadcasting* lesson.",
        intuition=r"""Line the two shapes up on the **right**, pad the shorter one with 1s on the left, then decide each column
independently: equal sizes pass through, a 1 stretches to the other size, anything else is an error.""",
        hints=[
            "Iterate `i` from 1 to `max(len(a), len(b))` and read `a[-i]` (or 1 if out of range).",
            "Compatibility: `da == db or da == 1 or db == 1`.",
            "Careful with zeros: the result is the size that is **not** the stretched 1, so `1` with `0` gives `0`, not `max`.",
        ],
        brute_force="Build arrays of these shapes and try adding them: correct but allocates memory and does not show the rule.",
        approach=r"""Walk from the right. For `[8,1,6]` and `[7,1]`: (6,1) → 6; (1,7) → 7; (8, padded 1) → 8. Reverse the collected
list to get `[8,7,6]`. For `[3,4]` and `[3]`: (4,3) clash → `None`.""",
        complexity="O(max(len(a), len(b))) time and space.",
        pitfalls=r"""- Aligning from the left (a very common mistake when reasoning quickly).
- Using `max(da, db)`: wrong for a size-0 dimension paired with size 1.
- Forgetting that `[]` is a valid scalar shape.""",
        follow_up="Extend to any number of shapes (fold the function over the list), as `np.broadcast_shapes` does.",
    ),
),

# ---------------------------------------------------------------- view strides
dict(
    id="dl-tensor-view-strides",
    title="Permute a Strided View",
    difficulty="Medium",
    pattern="Tensors",
    kind="function",
    entry="permute_view",
    description=r"""
A tensor view is described by `shape`, `stride` (in elements) and `offset` into flat storage. The storage position
of index `(i0, i1, ...)` is `offset + sum(i_k * stride_k)`.

Write `permute_view(shape, stride, offset, dims, index)` that simulates `t.permute(*dims)` and returns a list
`[new_shape, new_stride, position, contiguous]`:

- `new_shape[k] = shape[dims[k]]` and `new_stride[k] = stride[dims[k]]` (the offset is unchanged).
- `position` is the storage position of `index` **in the permuted view**.
- `contiguous` follows PyTorch's `is_contiguous()`: a tensor with zero elements is contiguous; otherwise, walking
  dimensions from the last to the first and **skipping dimensions of size 1**, each stride must equal the product of
  the sizes of the (non-skipped) dimensions to its right, starting from 1.

`dims` is a permutation of `0..len(shape)-1`, and `index` is valid for the new shape (use `[]` for a 0-d tensor).

**Example:** `shape=[2,3], stride=[3,1], offset=0, dims=[1,0], index=[2,1]` → `[[3,2],[1,3],5,False]`
(element `[2,1]` of the transpose is element `[1,2]` of the original, at position 5).
""",
    starter='''def permute_view(shape, stride, offset, dims, index):
    pass
''',
    solution='''def permute_view(shape, stride, offset, dims, index):
    new_shape = [shape[d] for d in dims]
    new_stride = [stride[d] for d in dims]
    position = offset + sum(i * s for i, s in zip(index, new_stride))
    numel = 1
    for n in new_shape:
        numel *= n
    contiguous = True
    if numel != 0:
        expected = 1
        for n, s in zip(reversed(new_shape), reversed(new_stride)):
            if n == 1:
                continue
            if s != expected:
                contiguous = False
                break
            expected *= n
    return [new_shape, new_stride, position, contiguous]
''',
    tests=[
        [[2, 3], [3, 1], 0, [1, 0], [2, 1]],
        [[2, 3], [3, 1], 0, [0, 1], [1, 2]],
        [[2, 3, 4], [12, 4, 1], 0, [2, 0, 1], [3, 1, 2]],
        [[2, 3, 4], [12, 4, 1], 5, [0, 2, 1], [1, 3, 2]],
        [[3, 1, 4], [4, 4, 1], 0, [1, 0, 2], [0, 2, 3]],
        [[4, 1], [1, 4], 0, [1, 0], [0, 3]],
        [[1, 5], [99, 1], 7, [0, 1], [0, 4]],
        [[2, 0, 3], [0, 3, 1], 0, [2, 1, 0], [0, 0, 0]],
        [[], [], 4, [], []],
        [[2, 2], [2, 1], 0, [1, 0], [1, 1]],
        [[3, 2], [1, 3], 0, [1, 0], [1, 2]],
        [[2, 3, 4, 5], [60, 20, 5, 1], 0, [0, 2, 3, 1], [1, 3, 4, 2]],
        [[6], [2], 1, [0], [5]],
    ],
    examples=2,
    wrong_solutions=[
        '''def permute_view(shape, stride, offset, dims, index):
    ns = [shape[d] for d in dims]; st = [stride[d] for d in dims]
    pos = offset + sum(i * s for i, s in zip(index, st))
    exp, ok = 1, True
    for n, s in zip(reversed(ns), reversed(st)):      # does not skip size-1 dims
        if s != exp: ok = False
        exp *= n
    return [ns, st, pos, ok]
''',
        '''def permute_view(shape, stride, offset, dims, index):
    ns = [shape[d] for d in dims]; st = [stride[d] for d in dims]
    pos = sum(i * s for i, s in zip(index, st))         # forgets the offset
    exp, ok = 1, True
    for n, s in zip(reversed(ns), reversed(st)):
        if n == 1: continue
        if s != exp: ok = False
        exp *= n
    return [ns, st, pos, ok]
''',
    ],
    guide=dict(
        prereqs="Offset, shape and stride; contiguity; `permute` returning a view (*Under the hood: storage, strides, views and devices*).",
        intuition=r"""`permute` never moves data: it reorders the shape and stride lists together. Everything else (the storage
position of an element, whether the layout is row-major) follows from those two lists plus the offset.""",
        hints=[
            "Build `new_shape` and `new_stride` by indexing with `dims`.",
            "Position = offset + Σ index_k · new_stride_k.",
            "For contiguity walk from the right with `expected = 1`, skip size-1 dims, compare, then multiply `expected` by the size.",
        ],
        brute_force="Materialise the storage as a list and actually copy the permuted tensor, then compare layouts: wasteful and unnecessary.",
        approach=r"""Example: shape (2,3) stride (3,1), dims (1,0) → shape (3,2), stride (1,3). Index (2,1) → 0 + 2·1 + 1·3 = 5.
Contiguity: last dim size 2, stride 3 ≠ expected 1 → False.

Why skip size-1 dims? Moving along a dimension of size 1 never happens, so its stride is irrelevant to memory order;
PyTorch ignores it too (that is why a `(4,1)` tensor viewed as `(1,4)` can still be contiguous).""",
        complexity="O(d) for d dimensions.",
        pitfalls=r"""- Forgetting the offset in the position.
- Not skipping size-1 dimensions in the contiguity check.
- Zero-element tensors count as contiguous.
- A 0-d tensor (`shape = []`) is contiguous and its position is the offset.""",
        follow_up="Add `view(new_shape)`: decide whether it is possible without a copy (the stride-compatibility rule), which is what raises the famous 'not contiguous' error.",
    ),
),

# ---------------------------------------------------------------- one hot
dict(
    id="dl-one-hot-encode",
    title="One-Hot Encoding for Any Shape",
    difficulty="Easy",
    pattern="Data Preparation",
    kind="function",
    entry="one_hot",
    description=r"""
Re-implement `torch.nn.functional.one_hot(labels, num_classes=-1)`.

- `labels` is a nested list of non-negative integers of any shape (a flat list, a list of lists, ...), possibly empty.
- If `num_classes` is `-1`, use `max(labels) + 1`. (When `labels` is empty, `num_classes` is always given.)
- Return a nested list of 0/1 integers whose shape is `labels`' shape plus one trailing axis of length
  `num_classes`, with a 1 at each label's position.

All labels are guaranteed to be smaller than `num_classes`.

**Examples:**
- `one_hot([2, 0, 1], -1)` → `[[0,0,1],[1,0,0],[0,1,0]]`
- `one_hot([[1], [0]], 3)` → `[[[0,1,0]],[[1,0,0]]]`
""",
    starter='''def one_hot(labels, num_classes=-1):
    pass
''',
    solution='''import numpy as np

def one_hot(labels, num_classes=-1):
    a = np.asarray(labels, dtype=np.int64)
    if num_classes == -1:
        num_classes = int(a.max()) + 1
    out = np.zeros(a.shape + (num_classes,), dtype=np.int64)
    np.put_along_axis(out, a[..., None], 1, axis=-1)
    return out.tolist()
''',
    tests=[
        [[2, 0, 1], -1],
        [[[1], [0]], 3],
        [[0], -1],
        [[], 4],
        [[3, 3, 3], 5],
        [[[0, 1], [2, 3]], -1],
        [[1, 0, 1, 0], 2],
        [[[[0]]], 2],
        [[4, 0], -1],
        [list(range(10)), 10],
        [[[5, 1, 2], [0, 0, 9]], 12],
    ],
    examples=2,
    wrong_solutions=[
        '''def one_hot(labels, num_classes=-1):
    if num_classes == -1:
        num_classes = max(labels)                      # off by one
    return [[1 if j == y else 0 for j in range(num_classes)] for y in labels]
''',
        '''def one_hot(labels, num_classes=-1):
    flat = labels if all(isinstance(v, int) for v in labels) else [v for row in labels for v in row]
    if num_classes == -1:
        num_classes = max(flat) + 1
    return [[1 if j == y else 0 for j in range(num_classes)] for y in flat]   # loses the shape
''',
    ],
    guide=dict(
        prereqs="One-hot encoding and `scatter_` from *Real-world data as tensors*.",
        intuition=r"""A one-hot vector is a row of the identity matrix: label `k` becomes row `k` of `eye(C)`. Doing this for
every element adds one trailing axis to whatever shape the labels already have.""",
        hints=[
            "`np.asarray(labels)` gives you the shape for free, including nested lists.",
            "`np.eye(C, dtype=int)[a]` indexes the identity with the whole label array.",
            "Handle `num_classes == -1` with `a.max() + 1`; an empty input always comes with an explicit count.",
        ],
        brute_force="Recursive Python over nested lists building each vector: O(elements × C), fine but fiddly.",
        approach=r"""Convert to an int array `a` of shape S, allocate zeros of shape S + (C,), and write 1 at `[..., a]` with
`np.put_along_axis(out, a[..., None], 1, axis=-1)` (the NumPy twin of `scatter_`). Or simply `np.eye(C, dtype=int)[a]`.
An empty `[]` has shape (0,), so the result has shape (0, C), which `tolist()` turns into `[]`.""",
        complexity="O(elements × C) time and output space.",
        pitfalls=r"""- `max + 1`, not `max`.
- Preserving nested shape instead of flattening.
- Returning booleans or floats instead of 0/1 integers (the torch version returns int64).""",
        follow_up="Add `ignore_index`: labels equal to -100 produce an all-zero row (useful for padding tokens).",
    ),
),

# ---------------------------------------------------------------- linear GD fit
dict(
    id="dl-linear-gd-fit",
    title="Fit a Line with Full-Batch Gradient Descent",
    difficulty="Easy",
    pattern="Training Loop",
    kind="function",
    entry="fit_line",
    compare="float",
    tolerance=1e-6,
    description=r"""
Train the model `pred = w * x + b` with mean squared error `L = mean((pred - y)**2)` by full-batch gradient descent.

Write `fit_line(x, y, lr, epochs, w0, b0)`:

- start from `w = w0`, `b = b0`;
- each epoch: compute predictions for **all** points, the gradients
  `dL/dw = (2/n) Σ (pred - y)·x` and `dL/db = (2/n) Σ (pred - y)`, then update **both** parameters simultaneously:
  `w -= lr * dL/dw`, `b -= lr * dL/db`;
- return `[w, b, final_loss]`, where `final_loss` is the MSE with the final parameters.

`x` and `y` have the same length `n ≥ 1`; `epochs ≥ 0`.

**Example:** `x=[1,2], y=[3,5], lr=0.1, epochs=1, w0=0, b0=0`: predictions 0, errors -3, -5,
`dL/dw = (2/2)(-3·1 - 5·2) = -13`, `dL/db = -8` → `w = 1.3, b = 0.8`, loss `((2.1-3)² + (3.4-5)²)/2 = 1.685`.
""",
    starter='''def fit_line(x, y, lr, epochs, w0, b0):
    pass
''',
    solution='''import numpy as np

def fit_line(x, y, lr, epochs, w0, b0):
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    w, b = float(w0), float(b0)
    n = x.size
    for _ in range(epochs):
        err = w * x + b - y
        gw = 2.0 * (err * x).sum() / n
        gb = 2.0 * err.sum() / n
        w, b = w - lr * gw, b - lr * gb
    loss = float(((w * x + b - y) ** 2).mean())
    return [w, b, loss]
''',
    tests=[
        [[1, 2], [3, 5], 0.1, 1, 0, 0],
        [[1, 2, 3, 4], [3, 5, 7, 9], 0.05, 500, 0, 0],
        [[1.2, 2.5, 3.1, 4.8, 5.5, 7.0, 8.2, 9.9, 12.4, 15.0], [4.6, 5.9, 6.5, 7.6, 8.6, 9.6, 10.7, 12.6, 14.3, 17.2], 0.01, 300, 1.0, 0.0],
        [[0, 0, 0], [1, 2, 3], 0.1, 50, 5, 0],
        [[3], [7], 0.05, 20, 0, 0],
        [[1, 2, 3], [2, 4, 6], 0.1, 0, 0.5, 0.5],
        [[-1, 0, 1], [1, 0, 1], 0.2, 100, 0, 0],
        [[1, 2, 3, 4, 5], [10, 8, 6, 4, 2], 0.3, 5, 0, 0],
        [[0.5, 1.5, -2.0, 3.0], [0.0, 1.0, -1.5, 2.2], 0.02, 1000, -1, 2],
    ],
    examples=2,
    wrong_solutions=[
        '''import numpy as np
def fit_line(x, y, lr, epochs, w0, b0):
    x, y = np.asarray(x, float), np.asarray(y, float); w, b = float(w0), float(b0)
    for _ in range(epochs):
        err = w * x + b - y
        w -= lr * 2 * (err * x).mean()
        err = w * x + b - y                 # recomputed: b uses the NEW w (not simultaneous)
        b -= lr * 2 * err.mean()
    return [w, b, float(((w * x + b - y) ** 2).mean())]
''',
        '''import numpy as np
def fit_line(x, y, lr, epochs, w0, b0):
    x, y = np.asarray(x, float), np.asarray(y, float); w, b = float(w0), float(b0)
    for _ in range(epochs):
        err = w * x + b - y
        w, b = w - lr * (err * x).mean(), b - lr * err.mean()     # missing the factor 2
    return [w, b, float(((w * x + b - y) ** 2).mean())]
''',
    ],
    guide=dict(
        prereqs="*Learning as parameter estimation: loss and gradient descent* (MSE, chain rule, update rule).",
        intuition=r"""The gradient tells each parameter which way is uphill; subtracting `lr × gradient` walks downhill. Both
gradients must come from the **same** predictions, i.e. the update is simultaneous, exactly like `optimizer.step()`
updating all parameters from gradients computed in one backward pass.""",
        hints=[
            "Vectorise with NumPy: `err = w*x + b - y`.",
            "`gw = 2*(err*x).sum()/n`, `gb = 2*err.sum()/n`.",
            "Update with a tuple assignment so `b` uses the old gradient: `w, b = w - lr*gw, b - lr*gb`.",
        ],
        brute_force="Python loops over points to accumulate the sums: identical maths, O(n) per epoch either way.",
        approach=r"""Loop `epochs` times: errors, two gradients, simultaneous update. After the loop compute the MSE once more.
Dry run (example): see the statement — after one epoch w = 1.3, b = 0.8, loss 1.685.""",
        complexity="O(n · epochs) time, O(n) space.",
        pitfalls=r"""- Updating `w` first and recomputing errors before updating `b` (that is a different algorithm).
- Forgetting the factor 2 or dividing by n twice.
- `epochs = 0` should return the initial parameters and their loss.
- When all x are 0, the w-gradient is always 0: only b moves.""",
        follow_up="Switch to mini-batches (SGD) with a fixed shuffle, or add momentum; then compare the number of epochs needed with and without standardising x.",
    ),
),

# ---------------------------------------------------------------- tiny autograd (class)
dict(
    id="dl-tiny-autograd",
    title="A Scalar Autograd Engine",
    difficulty="Hard",
    pattern="Autograd",
    kind="class",
    entry="Graph",
    compare="float",
    description=r"""
Build a miniature reverse-mode autodiff engine for scalars. Nodes are identified by integer ids assigned in creation
order, starting at 0.

Implement class `Graph` with:

- `leaf(value)` → id of a new input node holding `value`.
- `add(a, b)`, `mul(a, b)` → id of a new node (sum / product of nodes `a` and `b`; `a` may equal `b`).
- `pow(a, k)` → node for `value(a) ** k` where `k` is a plain number (assume the result is defined).
- `relu(a)` (derivative 0 at exactly 0), `tanh(a)`, `exp(a)` → new nodes.
- `value(a)` → the node's value (a float).
- `backward(out)` → first resets **every** node's gradient to 0, then sets d(out)/d(out) = 1 and propagates gradients
  to every node `out` depends on via the chain rule. Returns `None`.
- `grad(a)` → d(out)/d(a) from the most recent `backward` (0 if `a` does not influence `out`).

A node used several times must receive the **sum** of the gradients from all its uses.

**Example:** `x = leaf(3)`, `y = mul(x, x)` (=9), `z = add(y, x)` (=12), `backward(z)` → `grad(x) = 2·3 + 1 = 7`.

Tests are given as `[operations, arguments]` and compare the list of return values.
""",
    starter='''class Graph:
    def __init__(self):
        pass

    def leaf(self, value):
        pass

    def add(self, a, b):
        pass

    def mul(self, a, b):
        pass

    def pow(self, a, k):
        pass

    def relu(self, a):
        pass

    def tanh(self, a):
        pass

    def exp(self, a):
        pass

    def value(self, a):
        pass

    def backward(self, out):
        pass

    def grad(self, a):
        pass
''',
    solution='''import math

class Graph:
    def __init__(self):
        self.vals = []      # value of each node
        self.parents = []   # list of (parent_id, local_derivative) per node
        self.grads = []

    def _new(self, v, parents):
        self.vals.append(float(v))
        self.parents.append(parents)
        self.grads.append(0.0)
        return len(self.vals) - 1

    def leaf(self, value):
        return self._new(value, [])

    def add(self, a, b):
        return self._new(self.vals[a] + self.vals[b], [(a, 1.0), (b, 1.0)])

    def mul(self, a, b):
        va, vb = self.vals[a], self.vals[b]
        return self._new(va * vb, [(a, vb), (b, va)])

    def pow(self, a, k):
        va = self.vals[a]
        return self._new(va ** k, [(a, k * va ** (k - 1))])

    def relu(self, a):
        va = self.vals[a]
        return self._new(max(va, 0.0), [(a, 1.0 if va > 0 else 0.0)])

    def tanh(self, a):
        t = math.tanh(self.vals[a])
        return self._new(t, [(a, 1.0 - t * t)])

    def exp(self, a):
        e = math.exp(self.vals[a])
        return self._new(e, [(a, e)])

    def value(self, a):
        return self.vals[a]

    def backward(self, out):
        self.grads = [0.0] * len(self.vals)
        self.grads[out] = 1.0
        # ids are created in topological order (parents always have smaller ids),
        # so walking ids downwards visits each node after all of its consumers.
        for node in range(out, -1, -1):
            g = self.grads[node]
            if g == 0.0:
                continue
            for p, local in self.parents[node]:
                self.grads[p] += g * local
        return None

    def grad(self, a):
        return self.grads[a]
''',
    tests=[
        [["Graph", "leaf", "mul", "add", "value", "backward", "grad", "grad"],
         [[], [3], [0, 0], [1, 0], [2], [2], [0], [1]]],
        [["Graph", "leaf", "leaf", "mul", "leaf", "add", "relu", "backward", "grad", "grad", "grad", "value"],
         [[], [0.5], [2.0], [0, 1], [-0.25], [2, 3], [4], [5], [0], [1], [3], [5]]],
        [["Graph", "leaf", "leaf", "mul", "leaf", "add", "relu", "backward", "grad", "grad"],
         [[], [0.5], [-2.0], [0, 1], [0.1], [2, 3], [4], [5], [0], [1]]],
        [["Graph", "leaf", "tanh", "backward", "grad", "value"],
         [[], [0.7], [0], [1], [0], [1]]],
        [["Graph", "leaf", "exp", "leaf", "mul", "backward", "grad", "grad"],
         [[], [1.0], [0], [2.0], [1, 2], [3], [0], [2]]],
        [["Graph", "leaf", "pow", "pow", "add", "backward", "grad", "value"],
         [[], [2.0], [0, 3], [0, -1], [1, 2], [3], [0], [3]]],
        [["Graph", "leaf", "leaf", "add", "mul", "backward", "grad", "grad", "backward", "grad", "grad"],
         [[], [1.0], [2.0], [0, 1], [2, 2], [3], [0], [1], [2], [0], [1]]],
        [["Graph", "leaf", "leaf", "mul", "backward", "grad", "grad"],
         [[], [4.0], [5.0], [0, 1], [0], [0], [1]]],
        [["Graph", "leaf", "relu", "backward", "grad"],
         [[], [0.0], [0], [1], [0]]],
        [["Graph", "leaf", "leaf", "leaf", "mul", "add", "tanh", "leaf", "add", "pow", "backward", "grad", "grad", "grad", "value"],
         [[], [0.3], [-1.2], [0.8], [0, 1], [3, 2], [4], [-0.5], [5, 6], [7, 2], [8], [0], [1], [2], [8]]],
        [["Graph", "leaf", "mul", "mul", "mul", "backward", "grad"],
         [[], [1.5], [0, 0], [1, 0], [2, 1], [3], [0]]],
    ],
    examples=2,
    wrong_solutions=[
        '''import math
class Graph:
    def __init__(self): self.v, self.p, self.g = [], [], []
    def _n(self, v, p): self.v.append(float(v)); self.p.append(p); self.g.append(0.0); return len(self.v) - 1
    def leaf(self, value): return self._n(value, [])
    def add(self, a, b): return self._n(self.v[a] + self.v[b], [(a, 1.0), (b, 1.0)])
    def mul(self, a, b): return self._n(self.v[a] * self.v[b], [(a, self.v[b]), (b, self.v[a])])
    def pow(self, a, k): return self._n(self.v[a] ** k, [(a, k * self.v[a] ** (k - 1))])
    def relu(self, a): return self._n(max(self.v[a], 0.0), [(a, 1.0 if self.v[a] > 0 else 0.0)])
    def tanh(self, a): t = math.tanh(self.v[a]); return self._n(t, [(a, 1 - t * t)])
    def exp(self, a): e = math.exp(self.v[a]); return self._n(e, [(a, e)])
    def value(self, a): return self.v[a]
    def backward(self, out):
        self.g = [0.0] * len(self.v); self.g[out] = 1.0
        for node in range(out, -1, -1):
            for p, local in self.p[node]:
                self.g[p] = self.g[node] * local          # overwrites instead of accumulating
    def grad(self, a): return self.g[a]
''',
        '''import math
class Graph:
    def __init__(self): self.v, self.p, self.g = [], [], []
    def _n(self, v, p): self.v.append(float(v)); self.p.append(p); self.g.append(0.0); return len(self.v) - 1
    def leaf(self, value): return self._n(value, [])
    def add(self, a, b): return self._n(self.v[a] + self.v[b], [(a, 1.0), (b, 1.0)])
    def mul(self, a, b): return self._n(self.v[a] * self.v[b], [(a, self.v[b]), (b, self.v[a])])
    def pow(self, a, k): return self._n(self.v[a] ** k, [(a, k * self.v[a] ** (k - 1))])
    def relu(self, a): return self._n(max(self.v[a], 0.0), [(a, 1.0 if self.v[a] > 0 else 0.0)])
    def tanh(self, a): t = math.tanh(self.v[a]); return self._n(t, [(a, 1 - t)])   # wrong derivative
    def exp(self, a): e = math.exp(self.v[a]); return self._n(e, [(a, e)])
    def value(self, a): return self.v[a]
    def backward(self, out):
        self.g[out] = 1.0                                  # never resets old gradients
        for node in range(out, -1, -1):
            for p, local in self.p[node]:
                self.g[p] += self.g[node] * local
    def grad(self, a): return self.g[a]
''',
    ],
    guide=dict(
        prereqs="*Autograd in depth* (computational graph, chain rule, accumulation, topological order).",
        intuition=r"""During the forward pass each node stores its value and, for each parent, the **local derivative** of the
node with respect to that parent. Backward then pushes gradient from the output towards the inputs: a parent receives
`grad(node) × local`, **added** to whatever it already received from other uses.""",
        hints=[
            "Store per node: value, a list of `(parent_id, local_derivative)` pairs, and a gradient.",
            "Local derivatives: add → 1 and 1; mul → (b, a); pow → k·a^(k−1); relu → 1 if a>0 else 0; tanh → 1−t²; exp → e^a.",
            "Because ids grow in creation order, every parent has a smaller id than its child, so iterating ids from `out` down to 0 is a valid reverse topological order.",
        ],
        brute_force="Recompute each gradient by finite differences, rebuilding the expression with nudged leaves: slow, approximate and needs the expression as a function.",
        approach=r"""Example `x=3, y=x·x, z=y+x`: node 1 (mul) stores parents [(0,3),(0,3)]; node 2 (add) stores [(1,1),(0,1)].
Backward from 2: grad2 = 1 → grad1 += 1, grad0 += 1. Then node 1: grad0 += 1·3 twice → grad0 = 1 + 6 = 7.

Reset all gradients at the start of `backward` (the spec), so repeated calls on different outputs do not mix.""",
        complexity="Each operation O(1); backward O(number of nodes + edges).",
        pitfalls=r"""- Assigning instead of adding gradients (breaks `mul(x, x)` and any reuse).
- Forgetting to reset gradients between backward calls.
- `tanh` derivative is 1 − tanh², not 1 − tanh.
- ReLU at exactly 0 has derivative 0 by convention (matching PyTorch).""",
        follow_up="Make it vectorised (NumPy arrays per node, with unbroadcasting), as in the lesson's Tensor engine, or add `sigmoid` and `log`.",
    ),
),

# ---------------------------------------------------------------- SGD momentum
dict(
    id="dl-sgd-momentum-step",
    title="torch.optim.SGD Update Rule",
    difficulty="Medium",
    pattern="Optimisers",
    kind="function",
    entry="sgd_run",
    compare="float",
    description=r"""
Reproduce `torch.optim.SGD` exactly for one parameter vector over several steps.

`sgd_run(params, grads, lr, momentum, dampening, nesterov, weight_decay)`:

- `params`: the initial parameter vector (list of floats).
- `grads`: a list of gradient vectors, one per step (`grads[t]` is the gradient observed at step `t`).
- For each step with gradient `g`:
  1. if `weight_decay != 0`: `g = g + weight_decay * p`
  2. if `momentum != 0`: on the **first** step `buf = g` (no dampening); afterwards
     `buf = momentum * buf + (1 - dampening) * g`. Then `g = g + momentum * buf` if `nesterov` else `g = buf`.
  3. `p = p - lr * g`
- Return the final parameter vector.

**Example:** `params=[1.0], grads=[[1.0],[1.0]], lr=0.1, momentum=0.9, dampening=0, nesterov=False, weight_decay=0`:
step 1: buf = 1 → p = 0.9; step 2: buf = 0.9·1 + 1 = 1.9 → p = 0.9 − 0.19 = 0.71.
""",
    starter='''def sgd_run(params, grads, lr, momentum, dampening, nesterov, weight_decay):
    pass
''',
    solution='''import numpy as np

def sgd_run(params, grads, lr, momentum, dampening, nesterov, weight_decay):
    p = np.asarray(params, dtype=float).copy()
    buf = None
    for g in grads:
        g = np.asarray(g, dtype=float)
        if weight_decay != 0:
            g = g + weight_decay * p
        if momentum != 0:
            if buf is None:
                buf = g.copy()
            else:
                buf = momentum * buf + (1 - dampening) * g
            g = g + momentum * buf if nesterov else buf
        p = p - lr * g
    return p
''',
    tests=[
        [[1.0], [[1.0], [1.0]], 0.1, 0.9, 0.0, False, 0.0],
        [[1.0, -2.0], [[0.5, 0.5], [0.5, -1.0], [1.0, 0.0]], 0.1, 0.0, 0.0, False, 0.0],
        [[1.0, -2.0], [[0.5, 0.5], [0.5, -1.0], [1.0, 0.0]], 0.1, 0.9, 0.0, True, 0.0],
        [[1.0, -2.0], [[0.5, 0.5], [0.5, -1.0], [1.0, 0.0]], 0.1, 0.9, 0.5, False, 0.0],
        [[2.0, 3.0], [[0.0, 0.0], [0.0, 0.0], [0.0, 0.0]], 0.5, 0.0, 0.0, False, 0.1],
        [[2.0, 3.0], [[0.1, -0.1], [0.2, 0.0], [0.0, 0.3], [-0.1, 0.1]], 0.05, 0.9, 0.1, True, 0.01],
        [[0.3, -0.7, 1.1], _grads(10, 3), 0.01, 0.95, 0.0, False, 0.0005],
        [[0.3, -0.7, 1.1], _grads(10, 3), 0.01, 0.95, 0.0, True, 0.0005],
        [[5.0], [], 0.1, 0.9, 0.0, False, 0.0],
        [[1.0], [[2.0]], 0.1, 0.9, 0.9, False, 0.0],
        [[0.0, 0.0, 0.0, 0.0], _grads(25, 4, 2.0), 0.003, 0.9, 0.0, False, 0.01],
    ],
    examples=2,
    wrong_solutions=[
        '''import numpy as np
def sgd_run(params, grads, lr, momentum, dampening, nesterov, weight_decay):
    p = np.asarray(params, float); buf = np.zeros_like(p)
    for g in grads:
        g = np.asarray(g, float) + weight_decay * p
        if momentum:
            buf = momentum * buf + (1 - dampening) * g      # dampens the first step too
            g = g + momentum * buf if nesterov else buf
        p = p - lr * g
    return p
''',
        '''import numpy as np
def sgd_run(params, grads, lr, momentum, dampening, nesterov, weight_decay):
    p = np.asarray(params, float); buf = None
    for g in grads:
        g = np.asarray(g, float)
        if momentum:
            buf = g.copy() if buf is None else momentum * buf + (1 - dampening) * g
            g = g + momentum * buf if nesterov else buf
        p = p - lr * (g + weight_decay * p)                 # decay added after momentum
    return p
''',
    ],
    guide=dict(
        prereqs="Momentum, Nesterov and weight decay in *Optimisers (SGD, momentum, Adam, AdamW) and validation*.",
        intuition=r"""The momentum buffer is a running sum of past (decayed) gradients, so consistent directions accelerate.
PyTorch initialises the buffer with the very first gradient, untouched by dampening, and folds weight decay into the
gradient **before** momentum sees it.""",
        hints=[
            "Keep `buf = None` and create it on the first step with `g.copy()`.",
            "Weight decay first: `g = g + weight_decay * p` using the current parameters.",
            "Nesterov uses `g + momentum * buf` (with the freshly updated buffer) as the step direction.",
        ],
        brute_force="There is no cheaper alternative: the update is O(d) per step; the challenge is matching the exact order of operations.",
        approach=r"""Per step: decay → (buffer init or update) → choose direction (nesterov or buffer) → `p -= lr * direction`.
Example: g=1, momentum 0.9 → step 1 buf=1, p=1−0.1=0.9; step 2 buf=0.9+1=1.9, p=0.9−0.19=0.71.""",
        complexity="O(steps × d) time, O(d) extra space for the buffer.",
        pitfalls=r"""- Applying dampening on the first step (PyTorch does not).
- Applying weight decay after momentum, or using it on the buffer.
- Forgetting that `momentum == 0` means plain SGD (no buffer at all).
- An empty gradient list returns the initial parameters.""",
        follow_up="Add `maximize=True` (gradient ascent) or implement the same rule over a dict of named parameters, as the real optimizer state does.",
    ),
),

# ---------------------------------------------------------------- Adam / AdamW
dict(
    id="dl-adamw-step",
    title="Adam vs AdamW Update Rule",
    difficulty="Medium",
    pattern="Optimisers",
    kind="function",
    entry="adam_run",
    compare="float",
    tolerance=1e-7,
    description=r"""
Reproduce PyTorch's `Adam` and `AdamW` for one parameter vector over several steps.

`adam_run(params, grads, lr, beta1, beta2, eps, weight_decay, decoupled)` with step counter `t = 1, 2, ...`:

1. If `decoupled` (AdamW): `p = p * (1 - lr * weight_decay)`.
   Else (Adam) if `weight_decay != 0`: `g = g + weight_decay * p`.
2. `m = beta1 * m + (1 - beta1) * g`, `v = beta2 * v + (1 - beta2) * g**2` (both start at 0).
3. `m_hat = m / (1 - beta1**t)`, `v_hat = v / (1 - beta2**t)`.
4. `p = p - lr * m_hat / (sqrt(v_hat) + eps)`.

Return the final parameter vector.

**Example:** `params=[1.0], grads=[[0.5]], lr=0.1, beta1=0.9, beta2=0.999, eps=1e-8, weight_decay=0, decoupled=False`:
m = 0.05, v = 0.00025, m_hat = 0.5, v_hat = 0.25 → p = 1 − 0.1·0.5/0.5 ≈ 0.9 (the first Adam step moves every
coordinate by about `lr`).
""",
    starter='''def adam_run(params, grads, lr, beta1, beta2, eps, weight_decay, decoupled):
    pass
''',
    solution='''import numpy as np

def adam_run(params, grads, lr, beta1, beta2, eps, weight_decay, decoupled):
    p = np.asarray(params, dtype=float).copy()
    m = np.zeros_like(p)
    v = np.zeros_like(p)
    for t, g in enumerate(grads, start=1):
        g = np.asarray(g, dtype=float)
        if decoupled:
            p = p * (1 - lr * weight_decay)
        elif weight_decay != 0:
            g = g + weight_decay * p
        m = beta1 * m + (1 - beta1) * g
        v = beta2 * v + (1 - beta2) * g * g
        m_hat = m / (1 - beta1 ** t)
        v_hat = v / (1 - beta2 ** t)
        p = p - lr * m_hat / (np.sqrt(v_hat) + eps)
    return p
''',
    tests=[
        [[1.0], [[0.5]], 0.1, 0.9, 0.999, 1e-8, 0.0, False],
        [[1.0, -1.0], [[0.5, -0.2], [0.4, 0.1], [0.3, 0.3]], 0.01, 0.9, 0.999, 1e-8, 0.0, False],
        [[1.0, -1.0], [[0.5, -0.2], [0.4, 0.1], [0.3, 0.3]], 0.01, 0.9, 0.999, 1e-8, 0.1, False],
        [[1.0, -1.0], [[0.5, -0.2], [0.4, 0.1], [0.3, 0.3]], 0.01, 0.9, 0.999, 1e-8, 0.1, True],
        [[3.0, -2.0], [[0.0, 0.0], [0.0, 0.0]], 0.1, 0.9, 0.999, 1e-8, 0.5, True],
        [[3.0, -2.0], [[0.0, 0.0], [0.0, 0.0]], 0.1, 0.9, 0.999, 1e-8, 0.5, False],
        [[0.2, 0.4, -0.6], _grads(20, 3), 0.001, 0.9, 0.999, 1e-8, 0.01, True],
        [[0.2, 0.4, -0.6], _grads(20, 3), 0.001, 0.8, 0.99, 1e-6, 0.0, False],
        [[1.0], [], 0.1, 0.9, 0.999, 1e-8, 0.1, True],
        [[1e-3, -1e-3], [[1e-6, -1e-6], [2e-6, 0.0]], 0.01, 0.9, 0.999, 1e-8, 0.0, False],
        [[0.0] * 5, _grads(30, 5, 0.1), 0.003, 0.95, 0.98, 1e-8, 0.05, True],
    ],
    examples=2,
    wrong_solutions=[
        '''import numpy as np
def adam_run(params, grads, lr, beta1, beta2, eps, weight_decay, decoupled):
    p = np.asarray(params, float); m = np.zeros_like(p); v = np.zeros_like(p)
    for g in grads:
        g = np.asarray(g, float) + weight_decay * p           # treats AdamW like Adam
        m = beta1 * m + (1 - beta1) * g; v = beta2 * v + (1 - beta2) * g * g
        p = p - lr * m / (np.sqrt(v) + eps)                   # and no bias correction
    return p
''',
        '''import numpy as np
def adam_run(params, grads, lr, beta1, beta2, eps, weight_decay, decoupled):
    p = np.asarray(params, float); m = np.zeros_like(p); v = np.zeros_like(p)
    for t, g in enumerate(grads, 1):
        g = np.asarray(g, float)
        if decoupled: p = p * (1 - lr * weight_decay)
        elif weight_decay: g = g + weight_decay * p
        m = beta1 * m + (1 - beta1) * g; v = beta2 * v + (1 - beta2) * g * g
        p = p - lr * (m / (1 - beta1 ** t)) / np.sqrt(v / (1 - beta2 ** t) + eps)   # eps inside the sqrt
    return p
''',
    ],
    guide=dict(
        prereqs="Adam, bias correction and AdamW in *Optimisers (SGD, momentum, Adam, AdamW) and validation*.",
        intuition=r"""Adam divides a smoothed gradient by a smoothed gradient magnitude, so each coordinate moves about `lr`
per step regardless of its scale. AdamW's decay multiplies the weights by `1 − lr·wd` directly, so the shrinkage is
the same for every coordinate; Adam's L2 term is instead divided by `sqrt(v_hat)` and becomes uneven.""",
        hints=[
            "Use `enumerate(grads, start=1)` to get `t`.",
            "Decay first: decoupled → scale `p`; coupled → add `wd * p` to `g`.",
            "Bias-correct both moments, then `p -= lr * m_hat / (sqrt(v_hat) + eps)`: eps outside the square root.",
        ],
        brute_force="Not applicable: the update is already O(d) per step; the task is getting every detail of the formula right.",
        approach=r"""Example: g = 0.5 → m = 0.05, v = 0.00025; m_hat = 0.05/0.1 = 0.5, v_hat = 0.00025/0.001 = 0.25;
step = 0.1 · 0.5/(0.5 + 1e−8) ≈ 0.1 → p ≈ 0.9.

With zero gradients, AdamW still shrinks the weights by `(1 − lr·wd)` each step, while Adam's coupled decay produces
a gradient `wd·p` that the normalisation turns into a step of about `lr` towards zero: compare tests 5 and 6.""",
        complexity="O(steps × d) time, O(d) extra space for m and v.",
        pitfalls=r"""- Forgetting bias correction (early steps become far too small).
- Putting eps inside the square root (PyTorch adds it after).
- Applying decoupled decay after the Adam step instead of before (PyTorch decays first, using the pre-step weights).
- Starting `t` at 0 (division by zero in the correction).""",
        follow_up="Add `amsgrad=True` (keep the running maximum of v_hat) or compute the memory cost of Adam state for a 7B-parameter model in fp32.",
    ),
),
]
