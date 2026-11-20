import numpy as _np

_rng = _np.random.default_rng(1234)


def _r(*shape, scale=1.0):
    return _np.round(_rng.standard_normal(shape) * scale, 3).tolist()


PROBLEMS = [
# ---------------------------------------------------------------------------------------------
dict(
    id="llm-scaled-dot-attention",
    title="Scaled Dot-Product Attention",
    difficulty="Medium",
    pattern="Transformers",
    entry="attention",
    compare="float",
    description=r"""
Implement scaled dot-product attention, the core operation of every transformer.

Given queries `Q` (shape $T_q \times d_k$), keys `K` ($T_k \times d_k$), values `V` ($T_k \times d_v$)
and an optional `mask` ($T_q \times T_k$, `1` = may attend, `0` = blocked), compute

$$\text{weights} = \text{softmax}\left(\frac{QK^\top}{\sqrt{d_k}} + M\right),\qquad \text{output} = \text{weights}\cdot V$$

where blocked positions get a very large negative score (use `-1e9`) before the softmax, and the
softmax runs over the **key** axis (each row sums to 1).

Return a dict `{"output": ..., "weights": ...}` (nested lists or numpy arrays).

**Constraints:** every row of the mask allows at least one key. Inputs are plain nested lists; `mask`
may be `None`. Your softmax must be numerically stable (scores can be around $\pm 1000$).

**Example:** `Q = [[1, 0]]`, `K = [[1, 0], [0, 1]]`, `V = [[1, 2], [3, 4]]`, no mask.
Scores are `[1, 0] / sqrt(2)`, weights are about `[0.670, 0.330]`, output is about `[1.660, 2.660]`.
""",
    starter=r'''import numpy as np

def attention(Q, K, V, mask=None):
    """Return {"output": (Tq, dv), "weights": (Tq, Tk)}."""
    pass
''',
    solution=r'''import numpy as np

def attention(Q, K, V, mask=None):
    Q, K, V = (np.asarray(a, dtype=float) for a in (Q, K, V))
    scores = Q @ K.T / np.sqrt(Q.shape[-1])
    if mask is not None:
        scores = np.where(np.asarray(mask) != 0, scores, -1e9)
    scores = scores - scores.max(axis=-1, keepdims=True)
    w = np.exp(scores)
    w = w / w.sum(axis=-1, keepdims=True)
    return {"output": w @ V, "weights": w}
''',
    tests=[
        [[[1, 0]], [[1, 0], [0, 1]], [[1, 2], [3, 4]], None],
        [[[1, 0], [0, 1]], [[1, 0], [0, 1]], [[1, 2], [3, 4]], [[1, 0], [1, 1]]],
        [_r(3, 4), _r(5, 4), _r(5, 2), None],
        [_r(4, 8), _r(4, 8), _r(4, 3), _np.tril(_np.ones((4, 4), dtype=int)).tolist()],
        [[[1000.0, 0.0]], [[1.0, 0.0], [-1.0, 0.0], [0.5, 0.0]], [[1.0], [2.0], [3.0]], None],
        [[[0, 0, 0]], [[1, 2, 3], [4, 5, 6]], [[10], [20]], None],
        [_r(1, 16), _r(6, 16), _r(6, 4), [[1, 1, 0, 0, 1, 0]]],
        [_r(2, 2), _r(1, 2), _r(1, 5), None],
        [_r(5, 6, scale=5), _r(7, 6, scale=5), _r(7, 3), None],
        [_r(3, 64), _r(3, 64), _r(3, 2), [[1, 0, 0], [0, 1, 0], [0, 0, 1]]],
    ],
    examples=2,
    wrong_solutions=[
        r'''import numpy as np
def attention(Q, K, V, mask=None):
    Q, K, V = (np.asarray(a, dtype=float) for a in (Q, K, V))
    s = Q @ K.T
    if mask is not None:
        s = np.where(np.asarray(mask) != 0, s, -1e9)
    s = s - s.max(axis=-1, keepdims=True)
    w = np.exp(s); w = w / w.sum(axis=-1, keepdims=True)
    return {"output": w @ V, "weights": w}
''',
        r'''import numpy as np
def attention(Q, K, V, mask=None):
    Q, K, V = (np.asarray(a, dtype=float) for a in (Q, K, V))
    s = Q @ K.T / np.sqrt(Q.shape[-1])
    if mask is not None:
        s = np.where(np.asarray(mask) != 0, s, -1e9)
    s = s - s.max(axis=0, keepdims=True)
    w = np.exp(s); w = w / w.sum(axis=0, keepdims=True)
    return {"output": w @ V, "weights": w}
''',
        r'''import numpy as np
def attention(Q, K, V, mask=None):
    Q, K, V = (np.asarray(a, dtype=float) for a in (Q, K, V))
    s = Q @ K.T / np.sqrt(Q.shape[-1])
    s = s - s.max(axis=-1, keepdims=True)
    w = np.exp(s); w = w / w.sum(axis=-1, keepdims=True)
    return {"output": w @ V, "weights": w}
''',
    ],
    guide=dict(
        prereqs="Lesson *From embeddings to scaled dot-product attention*: softmax, matrix shapes, masking.",
        intuition="Each query asks every key 'how relevant are you?' via a dot product. Softmax turns the scores into a weighting that sums to 1, and the output is that weighted average of the values. The $\\sqrt{d_k}$ keeps score variance near 1 so softmax does not saturate.",
        hints=[
            "The score matrix is `Q @ K.T`, shape (Tq, Tk). Divide by `sqrt(d_k)` where `d_k = Q.shape[-1]`.",
            "Apply the mask before the softmax: `np.where(mask != 0, scores, -1e9)`.",
            "Stable softmax: subtract the row max, exponentiate, divide by the row sum (`axis=-1, keepdims=True`). Then `weights @ V`.",
        ],
        brute_force="Three nested loops: for each query, compute each dot product, exponentiate, normalise, then accumulate values. $O(T_q T_k (d_k + d_v))$, the same asymptotic cost but far slower in Python.",
        approach="1. Convert inputs to float arrays.\n2. `scores = Q @ K.T / sqrt(d_k)`.\n3. Where the mask is 0, set the score to `-1e9`.\n4. Row-wise stable softmax.\n5. `output = weights @ V`.\n\n**Dry run** (example 1): scores `[0.7071, 0]`; after subtracting the max `[0, -0.7071]`; exp `[1, 0.493]`; weights `[0.670, 0.330]`; output `0.670*[1,2] + 0.330*[3,4] = [1.660, 2.660]`.",
        complexity="Time $O(T_q T_k d_k + T_q T_k d_v)$, space $O(T_q T_k)$ for the score matrix: the quadratic memory that FlashAttention avoids materialising.",
        pitfalls="- Softmax over the wrong axis (columns instead of rows).\n- Scaling by $d_k$ instead of $\\sqrt{d_k}$, or not scaling.\n- Naive `np.exp(scores)` overflows for large scores: subtract the max first.\n- Using `-np.inf` breaks if a row is fully masked (NaN); `-1e9` is the conventional safe choice.",
        follow_up="Add a batch dimension and heads (shape (B, h, T, d_h)); implement cross-attention; return attention entropy per query.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="llm-causal-attention",
    title="Causal Self-Attention",
    difficulty="Medium",
    pattern="Transformers",
    entry="causal_self_attention",
    compare="float",
    description=r"""
Implement single-head **causal** self-attention for a decoder-only language model.

Given token representations `X` ($T \times d$) and projection matrices `Wq`, `Wk` ($d \times d_k$) and
`Wv` ($d \times d_v$):

1. `Q = X @ Wq`, `K = X @ Wk`, `V = X @ Wv`
2. scores $= QK^\top / \sqrt{d_k}$
3. position $i$ may attend only to positions $j \le i$ (set other scores to `-1e9`)
4. softmax over keys, then multiply by `V`

Return the output matrix ($T \times d_v$).

A key property you can use to test yourself: the output at position $i$ must not change if you alter
any token after $i$.

**Example:** with `X = [[1, 0], [0, 1]]` and identity projections, row 0 attends only to itself, so
`output[0] = [1, 0]`; row 1 mixes both rows with weights about `[0.330, 0.670]`.
""",
    starter=r'''import numpy as np

def causal_self_attention(X, Wq, Wk, Wv):
    pass
''',
    solution=r'''import numpy as np

def causal_self_attention(X, Wq, Wk, Wv):
    X, Wq, Wk, Wv = (np.asarray(a, dtype=float) for a in (X, Wq, Wk, Wv))
    Q, K, V = X @ Wq, X @ Wk, X @ Wv
    T = X.shape[0]
    s = Q @ K.T / np.sqrt(Q.shape[-1])
    s = np.where(np.tril(np.ones((T, T), dtype=bool)), s, -1e9)
    s = s - s.max(axis=-1, keepdims=True)
    w = np.exp(s)
    w = w / w.sum(axis=-1, keepdims=True)
    return w @ V
''',
    tests=[
        [[[1, 0], [0, 1]], [[1, 0], [0, 1]], [[1, 0], [0, 1]], [[1, 0], [0, 1]]],
        [[[2.0, -1.0]], [[1, 0], [0, 1]], [[1, 0], [0, 1]], [[1, 2, 3], [4, 5, 6]]],
        [_r(4, 3), _r(3, 3), _r(3, 3), _r(3, 3)],
        [_r(6, 4), _r(4, 2), _r(4, 2), _r(4, 5)],
        [_r(5, 8), _r(8, 8), _r(8, 8), _r(8, 2)],
        [_r(3, 2, scale=10), _r(2, 2, scale=10), _r(2, 2, scale=10), _r(2, 2)],
        [_r(8, 4), _r(4, 4), _r(4, 4), _r(4, 4)],
        [[[1, 1], [1, 1], [1, 1]], [[1, 0], [0, 1]], [[1, 0], [0, 1]], [[1, 0], [0, 1]]],
        [_r(2, 6), _r(6, 3), _r(6, 3), _r(6, 1)],
        [_r(10, 3), _r(3, 4), _r(3, 4), _r(3, 3)],
    ],
    examples=2,
    wrong_solutions=[
        r'''import numpy as np
def causal_self_attention(X, Wq, Wk, Wv):
    X, Wq, Wk, Wv = (np.asarray(a, dtype=float) for a in (X, Wq, Wk, Wv))
    Q, K, V = X @ Wq, X @ Wk, X @ Wv
    s = Q @ K.T / np.sqrt(Q.shape[-1])
    s = s - s.max(axis=-1, keepdims=True)
    w = np.exp(s); w = w / w.sum(axis=-1, keepdims=True)
    return w @ V
''',
        r'''import numpy as np
def causal_self_attention(X, Wq, Wk, Wv):
    X, Wq, Wk, Wv = (np.asarray(a, dtype=float) for a in (X, Wq, Wk, Wv))
    Q, K, V = X @ Wq, X @ Wk, X @ Wv
    T = X.shape[0]
    s = Q @ K.T / np.sqrt(Q.shape[-1])
    s = np.where(np.triu(np.ones((T, T), dtype=bool)), s, -1e9)
    s = s - s.max(axis=-1, keepdims=True)
    w = np.exp(s); w = w / w.sum(axis=-1, keepdims=True)
    return w @ V
''',
        r'''import numpy as np
def causal_self_attention(X, Wq, Wk, Wv):
    X, Wq, Wk, Wv = (np.asarray(a, dtype=float) for a in (X, Wq, Wk, Wv))
    Q, K, V = X @ Wq, X @ Wk, X @ Wv
    T = X.shape[0]
    s = Q @ K.T / np.sqrt(Q.shape[-1])
    s = np.where(np.tril(np.ones((T, T), dtype=bool), k=-1) | np.eye(T, dtype=bool) * (np.arange(T) == 0)[:, None], s, -1e9)
    s = s - s.max(axis=-1, keepdims=True)
    w = np.exp(s); w = w / w.sum(axis=-1, keepdims=True)
    return w @ V
''',
    ],
    guide=dict(
        prereqs="Problem *Scaled Dot-Product Attention*; lesson section on causal masking.",
        intuition="Self-attention where Q, K and V all come from the same sequence, plus a lower-triangular mask so no position sees the future. That mask is what lets one forward pass train all next-token predictions in parallel.",
        hints=[
            "Project first: `Q, K, V = X @ Wq, X @ Wk, X @ Wv`.",
            "`np.tril(np.ones((T, T), dtype=bool))` is True exactly where j <= i.",
            "Mask with `np.where(mask, scores, -1e9)`, then a stable row-wise softmax and `@ V`.",
        ],
        brute_force="For each position i, loop over j <= i only, compute scores, softmax over that prefix, and sum the values. $O(T^2 d)$ with Python loops.",
        approach="1. Project X into Q, K, V.\n2. Compute the $T \\times T$ score matrix and scale by $\\sqrt{d_k}$ (the *projected* width).\n3. Keep the lower triangle (including the diagonal), set the rest to `-1e9`.\n4. Softmax rows, multiply by V.\n\n**Dry run** (example 1): row 0 sees only itself, weight 1, output `[1, 0]`. Row 1 has scores `[0, 0.7071]`, weights `[0.330, 0.670]`, output `[0.330, 0.670]`.",
        complexity="Time $O(T d\\,d_k + T^2 d_k + T^2 d_v)$, space $O(T^2)$.",
        pitfalls="- `np.triu` instead of `np.tril` (the model sees only the future).\n- Excluding the diagonal: a token must be able to attend to itself, otherwise row 0 has nothing to attend to.\n- Dividing by `sqrt(d)` of the input instead of `d_k` of the projected queries.\n- Forgetting the mask entirely: tests with random data catch this.",
        follow_up="Combine with a padding mask; verify causality programmatically by perturbing a later token and checking earlier outputs are unchanged; add an incremental (KV-cached) version.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="llm-multihead-split-merge",
    title="Multi-Head Split and Merge",
    difficulty="Easy",
    pattern="Transformers",
    entry="reshape_heads",
    compare="float",
    description=r"""
Multi-head attention uses one big projection and then **reshapes** it into heads. Implement both
directions:

- `mode == "split"`: `x` has shape `(B, T, d)`. Return shape `(B, h, T, d // h)`, where head `i` holds
  features `[i * d/h, (i+1) * d/h)` of every token.
- `mode == "merge"`: `x` has shape `(B, h, T, d_h)`. Return shape `(B, T, h * d_h)` (the exact inverse
  of split). `num_heads` is still passed and equals `h`.

`d` is always divisible by `num_heads`.

**Example:** `x = [[[0, 1, 2, 3], [4, 5, 6, 7]]]` (B=1, T=2, d=4), `num_heads = 2`, `"split"` gives
`[[[[0, 1], [4, 5]], [[2, 3], [6, 7]]]]`: head 0 has features 0-1 of both tokens, head 1 has
features 2-3.
""",
    starter=r'''import numpy as np

def reshape_heads(x, num_heads, mode):
    pass
''',
    solution=r'''import numpy as np

def reshape_heads(x, num_heads, mode):
    x = np.asarray(x)
    if mode == "split":
        B, T, d = x.shape
        return x.reshape(B, T, num_heads, d // num_heads).transpose(0, 2, 1, 3)
    B, h, T, dh = x.shape
    return x.transpose(0, 2, 1, 3).reshape(B, T, h * dh)
''',
    tests=[
        [[[[0, 1, 2, 3], [4, 5, 6, 7]]], 2, "split"],
        [[[[[0, 1], [4, 5]], [[2, 3], [6, 7]]]], 2, "merge"],
        [_np.arange(2 * 3 * 6).reshape(2, 3, 6).tolist(), 3, "split"],
        [_np.arange(2 * 3 * 4 * 2).reshape(2, 3, 4, 2).tolist(), 3, "merge"],
        [_np.arange(1 * 1 * 8).reshape(1, 1, 8).tolist(), 4, "split"],
        [_np.arange(1 * 5 * 4).reshape(1, 5, 4).tolist(), 1, "split"],
        [_np.arange(3 * 2 * 4).reshape(3, 2, 4).tolist(), 4, "split"],
        [_np.arange(2 * 4 * 3 * 1).reshape(2, 4, 3, 1).tolist(), 4, "merge"],
        [_r(2, 5, 8), 2, "split"],
        [_r(2, 2, 5, 4), 2, "merge"],
        [_np.arange(1 * 2 * 2 * 3).reshape(1, 2, 2, 3).tolist(), 2, "merge"],
    ],
    examples=2,
    wrong_solutions=[
        r'''import numpy as np
def reshape_heads(x, num_heads, mode):
    x = np.asarray(x)
    if mode == "split":
        B, T, d = x.shape
        return x.reshape(B, num_heads, T, d // num_heads)
    B, h, T, dh = x.shape
    return x.reshape(B, T, h * dh)
''',
        r'''import numpy as np
def reshape_heads(x, num_heads, mode):
    x = np.asarray(x)
    if mode == "split":
        B, T, d = x.shape
        return x.reshape(B, T, d // num_heads, num_heads).transpose(0, 3, 1, 2)
    B, h, T, dh = x.shape
    return x.transpose(0, 2, 3, 1).reshape(B, T, h * dh)
''',
    ],
    guide=dict(
        prereqs="Lesson *The transformer block*, section on multi-head attention; numpy `reshape` and `transpose`.",
        intuition="A reshape only re-labels how a flat buffer is chopped up; it never moves data. The features of one token are contiguous in memory, so you must first split the **last** axis into (heads, head_dim) and only then move the head axis in front of the time axis with a transpose.",
        hints=[
            "Split: `(B, T, d) -> reshape (B, T, h, d/h) -> transpose to (B, h, T, d/h)`.",
            "Merge is the inverse: transpose back to `(B, T, h, d_h)` first, then reshape to `(B, T, h*d_h)`.",
            "If you reshape straight to `(B, h, T, d/h)` the numbers come out in the wrong places even though the shape is right.",
        ],
        brute_force="Loop over batch, head and token and copy slices `x[b][t][i*dh:(i+1)*dh]` into the output. Correct, $O(BTd)$, just verbose.",
        approach="**Split:** `x.reshape(B, T, h, dh).transpose(0, 2, 1, 3)`.\n\n**Merge:** `x.transpose(0, 2, 1, 3).reshape(B, T, h * dh)`.\n\n**Dry run:** token 0 = `[0,1,2,3]`, token 1 = `[4,5,6,7]`, h = 2. After reshape: token 0 = `[[0,1],[2,3]]`, token 1 = `[[4,5],[6,7]]`. After transpose, head 0 = `[[0,1],[4,5]]`, head 1 = `[[2,3],[6,7]]`.",
        complexity="$O(BTd)$ time and space (numpy may return a view for the transpose; the final reshape copies).",
        pitfalls="- Right shape, wrong contents: reshape directly to `(B, h, T, dh)`.\n- Splitting the last axis as `(dh, h)` instead of `(h, dh)`.\n- In PyTorch, calling `.view` after `.transpose` without `.contiguous()` raises an error; `.reshape` handles it.",
        follow_up="Implement full multi-head attention using this helper and the attention function; extend to grouped-query attention where K/V have fewer heads than Q.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="llm-layer-norm",
    title="Layer Normalization",
    difficulty="Easy",
    pattern="Transformers",
    entry="layer_norm",
    compare="float",
    description=r"""
Implement LayerNorm over the **last axis** of `x`:

$$\text{LN}(x) = \gamma \odot \frac{x - \mu}{\sqrt{\sigma^2 + \epsilon}} + \beta$$

where $\mu$ and $\sigma^2$ are the mean and **population** variance (divide by $d$, not $d - 1$) of
each vector along the last axis, and `gamma`, `beta` are vectors of length $d$.

`x` may be 1-D, 2-D `(T, d)` or 3-D `(B, T, d)`. Return the same shape.

**Example:** `x = [[1, 2, 3, 4]]`, `gamma = [1,1,1,1]`, `beta = [0,0,0,0]`, `eps = 1e-5`
gives about `[[-1.3416, -0.4472, 0.4472, 1.3416]]`.
""",
    starter=r'''import numpy as np

def layer_norm(x, gamma, beta, eps=1e-5):
    pass
''',
    solution=r'''import numpy as np

def layer_norm(x, gamma, beta, eps=1e-5):
    x = np.asarray(x, dtype=float)
    mu = x.mean(axis=-1, keepdims=True)
    var = ((x - mu) ** 2).mean(axis=-1, keepdims=True)
    return np.asarray(gamma, dtype=float) * (x - mu) / np.sqrt(var + eps) + np.asarray(beta, dtype=float)
''',
    tests=[
        [[[1, 2, 3, 4]], [1, 1, 1, 1], [0, 0, 0, 0], 1e-5],
        [[[1, 2, 3, 4], [10, 10, 10, 10]], [1, 1, 1, 1], [0, 0, 0, 0], 1e-5],
        [[1.0, 3.0], [2.0, 2.0], [1.0, -1.0], 1e-5],
        [_r(3, 5), [1, 2, 3, 4, 5], [0.5, 0, -0.5, 0, 1], 1e-5],
        [_r(2, 3, 4), _r(4), _r(4), 1e-6],
        [[[5.0]], [3.0], [7.0], 1e-5],
        [[[0, 0, 0]], [1, 1, 1], [1, 2, 3], 1e-5],
        [_r(4, 2, scale=100), [1, 1], [0, 0], 1e-5],
        [[[1, 2, 3]], [1, 1, 1], [0, 0, 0], 0.1],
        [_r(6, 3), [1, 1, 1], [0, 0, 0], 1e-5],
        [[[-1, 1], [2, -2], [0.5, 0.25]], [1, 1], [0, 0], 1e-5],
    ],
    examples=2,
    wrong_solutions=[
        r'''import numpy as np
def layer_norm(x, gamma, beta, eps=1e-5):
    x = np.asarray(x, dtype=float)
    mu = x.mean(axis=-1, keepdims=True)
    var = x.var(axis=-1, keepdims=True, ddof=1) if x.shape[-1] > 1 else 0 * mu
    return np.asarray(gamma) * (x - mu) / np.sqrt(var + eps) + np.asarray(beta)
''',
        r'''import numpy as np
def layer_norm(x, gamma, beta, eps=1e-5):
    x = np.asarray(x, dtype=float)
    mu = x.mean(axis=0, keepdims=True)
    var = x.var(axis=0, keepdims=True)
    return np.asarray(gamma) * (x - mu) / np.sqrt(var + eps) + np.asarray(beta)
''',
        r'''import numpy as np
def layer_norm(x, gamma, beta, eps=1e-5):
    x = np.asarray(x, dtype=float)
    mu = x.mean(axis=-1, keepdims=True)
    std = x.std(axis=-1, keepdims=True)
    return np.asarray(gamma) * (x - mu) / (std + eps) + np.asarray(beta)
''',
    ],
    guide=dict(
        prereqs="Lesson *The transformer block*, section on normalisation.",
        intuition="Standardise each token vector on its own (zero mean, unit variance across its features), then let the model re-scale and shift with learned `gamma` and `beta`. No batch statistics are involved, so it works identically for any batch size.",
        hints=[
            "Use `axis=-1, keepdims=True` for the mean and the variance so broadcasting works for any number of leading dimensions.",
            "Population variance: `((x - mu) ** 2).mean(-1)`, which is numpy's default `ddof=0`.",
            "`eps` goes **inside** the square root: `sqrt(var + eps)`.",
        ],
        brute_force="Loop over every vector, compute its mean and variance with Python sums, and normalise element by element. Same $O(n)$ work, slower.",
        approach="1. `mu = x.mean(-1, keepdims=True)`\n2. `var = ((x - mu)**2).mean(-1, keepdims=True)`\n3. `y = (x - mu) / sqrt(var + eps)`\n4. `return gamma * y + beta`\n\n**Dry run:** `[1,2,3,4]`: mean 2.5, variance 1.25, std 1.118; normalised `[-1.342, -0.447, 0.447, 1.342]`. A constant row such as `[10,10,10,10]` has variance 0 and returns `beta` (the `eps` prevents 0/0).",
        complexity="$O(n)$ time and space in the number of elements.",
        pitfalls="- Sample variance (`ddof=1`) instead of population variance.\n- Normalising across the batch/time axis (that is BatchNorm-like behaviour).\n- Adding `eps` outside the square root: differs noticeably for small variances or large `eps`.\n- Forgetting `keepdims`, which breaks broadcasting for 3-D inputs.",
        follow_up="Implement RMSNorm (no mean subtraction, no bias) and compare outputs; implement pre-norm vs post-norm residual blocks.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="llm-sinusoidal-pe",
    title="Sinusoidal Positional Encoding",
    difficulty="Easy",
    pattern="Transformers",
    entry="sinusoidal_pe",
    compare="float",
    description=r"""
Build the fixed positional-encoding matrix from "Attention Is All You Need".

For position $pos \in [0, T)$ and dimension pair index $i$:

$$PE[pos, 2i] = \sin\left(\frac{pos}{base^{2i/d}}\right),\qquad PE[pos, 2i+1] = \cos\left(\frac{pos}{base^{2i/d}}\right)$$

Return a `T x d` matrix. `d` may be odd: then the last column is a sine column with no matching cosine.
`base` defaults to 10000.

**Example:** `T = 2, d = 4` gives

`[[0, 1, 0, 1], [0.8415, 0.5403, 0.01, 0.99995]]`

(row 0 is always `sin(0) = 0, cos(0) = 1` alternating).
""",
    starter=r'''import numpy as np

def sinusoidal_pe(T, d, base=10000.0):
    pass
''',
    solution=r'''import numpy as np

def sinusoidal_pe(T, d, base=10000.0):
    pe = np.zeros((T, d))
    pos = np.arange(T)[:, None]
    two_i = np.arange(0, d, 2)[None, :]
    angle = pos / (base ** (two_i / d))
    pe[:, 0::2] = np.sin(angle)
    pe[:, 1::2] = np.cos(angle[:, : d // 2])
    return pe
''',
    tests=[
        [2, 4],
        [1, 6],
        [4, 2],
        [3, 5],
        [5, 1],
        [10, 8],
        [6, 4, 100.0],
        [50, 16],
        [3, 3, 10.0],
        [0, 4],
        [7, 6, 2.0],
    ],
    examples=2,
    wrong_solutions=[
        r'''import numpy as np
def sinusoidal_pe(T, d, base=10000.0):
    pe = np.zeros((T, d))
    pos = np.arange(T)[:, None]
    two_i = np.arange(0, d, 2)[None, :]
    angle = pos / (base ** (two_i / d))
    pe[:, 0::2] = np.cos(angle)
    pe[:, 1::2] = np.sin(angle[:, : d // 2])
    return pe
''',
        r'''import numpy as np
def sinusoidal_pe(T, d, base=10000.0):
    pe = np.zeros((T, d))
    pos = np.arange(T)[:, None]
    i = np.arange(0, (d + 1) // 2)[None, :]
    angle = pos / (base ** (i / d))
    pe[:, 0::2] = np.sin(angle)
    pe[:, 1::2] = np.cos(angle[:, : d // 2])
    return pe
''',
        r'''import numpy as np
def sinusoidal_pe(T, d, base=10000.0):
    pe = np.zeros((T, d))
    for pos in range(T):
        for j in range(d):
            a = pos / (base ** (j / d))
            pe[pos, j] = np.sin(a) if j % 2 == 0 else np.cos(a)
    return pe
''',
    ],
    guide=dict(
        prereqs="Lesson *Positional encodings, RoPE, KV cache and architecture families*.",
        intuition="Each pair of columns is a clock hand rotating at its own speed: fast for early columns, very slow for late ones. Reading all the hands together identifies the position, and nearby positions have similar readings.",
        hints=[
            "The exponent uses the **even** index `2i`: columns 0 and 1 share exponent 0, columns 2 and 3 share exponent `2/d`, and so on.",
            "Build `angle` of shape `(T, ceil(d/2))` with broadcasting, then assign `pe[:, 0::2] = sin(angle)`.",
            "For odd `d` there is one fewer cosine column: `pe[:, 1::2] = cos(angle[:, :d // 2])`.",
        ],
        brute_force="Two nested loops over `pos` and column `j`, with `two_i = j - (j % 2)` and sin for even `j`, cos for odd `j`. $O(Td)$.",
        approach="1. `pos` column vector `(T, 1)`, even indices row vector `(1, ceil(d/2))`.\n2. `angle = pos / base ** (two_i / d)`.\n3. Even columns get `sin`, odd columns get `cos`.\n\n**Dry run** (`T=2, d=4`): frequencies `1` and `1/100`. Row 1: `sin(1) = 0.8415, cos(1) = 0.5403, sin(0.01) = 0.01, cos(0.01) = 0.99995`.",
        complexity="$O(Td)$ time and space.",
        pitfalls="- Using the column index `j` in the exponent for odd columns (the cosine must share its sine partner's frequency).\n- Using `i/d` instead of `2i/d`.\n- Swapping sin and cos.\n- Odd `d`: shape mismatch when assigning the cosine columns.",
        follow_up="Show numerically that `PE[pos + k]` is a rotation of `PE[pos]` per frequency pair; compare with learned absolute embeddings and RoPE.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="llm-rope-rotate",
    title="Rotary Position Embedding (RoPE)",
    difficulty="Medium",
    pattern="Transformers",
    entry="rope",
    compare="float",
    description=r"""
Apply rotary position embeddings to a matrix of query or key vectors.

`x` has shape `(T, d)` with `d` even, and `positions` is a list of `T` integer positions. Using the
**interleaved-pair** layout, for each pair index $i \in [0, d/2)$ with frequency
$\theta_i = base^{-2i/d}$ and position $m$:

$$x'_{2i} = x_{2i}\cos(m\theta_i) - x_{2i+1}\sin(m\theta_i)$$
$$x'_{2i+1} = x_{2i}\sin(m\theta_i) + x_{2i+1}\cos(m\theta_i)$$

Return the rotated `(T, d)` matrix. `base` defaults to 10000.

**Example:** `x = [[1, 0]]`, `positions = [1]` gives `[[cos 1, sin 1]] = [[0.5403, 0.8415]]`.
Position 0 always leaves a vector unchanged.
""",
    starter=r'''import numpy as np

def rope(x, positions, base=10000.0):
    pass
''',
    solution=r'''import numpy as np

def rope(x, positions, base=10000.0):
    x = np.asarray(x, dtype=float)
    T, d = x.shape
    theta = base ** (-np.arange(0, d, 2) / d)
    ang = np.asarray(positions, dtype=float)[:, None] * theta[None, :]
    cos, sin = np.cos(ang), np.sin(ang)
    x1, x2 = x[:, 0::2], x[:, 1::2]
    out = np.empty_like(x)
    out[:, 0::2] = x1 * cos - x2 * sin
    out[:, 1::2] = x1 * sin + x2 * cos
    return out
''',
    tests=[
        [[[1, 0]], [1]],
        [[[1, 2, 3, 4]], [0]],
        [[[1, 0, 1, 0]], [2]],
        [_r(3, 4), [0, 1, 2]],
        [_r(4, 8), [5, 6, 7, 8]],
        [_r(2, 6), [100, 1000]],
        [[[0, 1], [1, 0], [1, 1]], [3, 3, 3]],
        [_r(3, 4), [2, 0, 7], 100.0],
        [_r(1, 16), [42]],
        [_r(5, 2), [0, 1, 2, 3, 4]],
        [_r(2, 4), [1, 1], 2.0],
    ],
    examples=2,
    wrong_solutions=[
        r'''import numpy as np
def rope(x, positions, base=10000.0):
    x = np.asarray(x, dtype=float)
    T, d = x.shape
    theta = base ** (-np.arange(0, d, 2) / d)
    ang = np.asarray(positions, dtype=float)[:, None] * theta[None, :]
    cos, sin = np.cos(ang), np.sin(ang)
    x1, x2 = x[:, : d // 2], x[:, d // 2:]
    return np.concatenate([x1 * cos - x2 * sin, x1 * sin + x2 * cos], axis=1)
''',
        r'''import numpy as np
def rope(x, positions, base=10000.0):
    x = np.asarray(x, dtype=float)
    T, d = x.shape
    theta = base ** (-np.arange(0, d, 2) / d)
    ang = np.asarray(positions, dtype=float)[:, None] * theta[None, :]
    cos, sin = np.cos(ang), np.sin(ang)
    x1, x2 = x[:, 0::2], x[:, 1::2]
    out = np.empty_like(x)
    out[:, 0::2] = x1 * cos + x2 * sin
    out[:, 1::2] = -x1 * sin + x2 * cos
    return out
''',
        r'''import numpy as np
def rope(x, positions, base=10000.0):
    x = np.asarray(x, dtype=float)
    T, d = x.shape
    theta = base ** (-np.arange(0, d // 2) / d)
    ang = np.asarray(positions, dtype=float)[:, None] * theta[None, :]
    cos, sin = np.cos(ang), np.sin(ang)
    x1, x2 = x[:, 0::2], x[:, 1::2]
    out = np.empty_like(x)
    out[:, 0::2] = x1 * cos - x2 * sin
    out[:, 1::2] = x1 * sin + x2 * cos
    return out
''',
    ],
    guide=dict(
        prereqs="Lesson *Positional encodings, RoPE...*; 2-D rotation matrices.",
        intuition="Treat each consecutive pair of features as a point in the plane and spin it by an angle proportional to the token's position. Spinning both a query and a key means their dot product depends only on the *difference* of their angles, that is on relative position.",
        hints=[
            "Frequencies: `theta = base ** (-np.arange(0, d, 2) / d)` gives `d/2` values, the first being 1.",
            "Angles are an outer product: `positions[:, None] * theta[None, :]`, shape `(T, d/2)`.",
            "Even columns: `x1*cos - x2*sin`; odd columns: `x1*sin + x2*cos`, where `x1 = x[:, 0::2]` and `x2 = x[:, 1::2]`.",
        ],
        brute_force="Loop over tokens and pairs, building the 2x2 rotation matrix each time and multiplying. $O(Td)$, slow in Python.",
        approach="1. Compute `theta` and the `(T, d/2)` angle grid.\n2. Slice even and odd columns.\n3. Apply the rotation formulas and interleave the results back.\n\n**Dry run:** `x = [1, 0]`, `m = 1`, `theta_0 = 1`: `x' = [1*cos1 - 0*sin1, 1*sin1 + 0*cos1] = [0.5403, 0.8415]`. With `m = 0` every angle is 0 and the vector is unchanged. Rotations preserve the vector's norm.",
        complexity="$O(Td)$ time and space.",
        pitfalls="- Mixing the interleaved layout with the 'rotate half' layout (first half paired with second half) used by some implementations.\n- Rotating in the opposite direction (sign of the sine terms).\n- Using exponent `i/d` instead of `2i/d` for the frequencies.\n- Applying RoPE to values or to the residual stream: it is applied to Q and K only.",
        follow_up="Verify that `rope(q, [m]) @ rope(k, [n]).T` equals the score at positions `(m + s, n + s)` for any shift `s`; implement the rotate-half layout and find the permutation that maps one to the other.",
    ),
),
]
