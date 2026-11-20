import numpy as _np

_rng = _np.random.RandomState(6)


def _r(*shape, scale=1.0):
    return (_rng.randn(*shape) * scale).round(3).tolist()


def _with_missing(n, d, frac=0.2, scale=5.0):
    X = (_rng.randn(n, d) * scale).round(2).tolist()
    for i in range(n):
        for j in range(d):
            if _rng.rand() < frac:
                X[i][j] = None
    # guarantee each column has at least one observed train value
    for j in range(d):
        X[0][j] = X[0][j] if X[0][j] is not None else 1.0
    return X


PROBLEMS = [
# ---------------------------------------------------------------- impute + scale pipeline
dict(
    id="ml-impute-scale-pipeline",
    title="Leak-Free Impute-then-Scale Pipeline",
    difficulty="Medium",
    pattern="Pipelines",
    kind="function",
    entry="impute_scale",
    compare="float",
    description=r"""
Implement the two-step pipeline `make_pipeline(SimpleImputer(strategy="mean"), StandardScaler())` by hand.
Missing values are `None`.

**fit (on `train` only)**
1. Imputer: for each column, the mean of the *observed* (non-`None`) training values. Every column has at least
   one observed training value.
2. Replace missing training values with those means; then the scaler learns the column mean and **population**
   std of this *imputed* training matrix (std 0 → use 1).

**transform** `test`: impute its missing values with the **training** means, then scale with the **training**
scaler statistics.

Return the transformed test matrix.

**Example:** `train=[[1],[None],[3]]`, `test=[[None],[5]]` → imputed train `[1,2,3]` (mean 2, std 0.8165) → `[[0.0],[3.6742]]`
""",
    starter='''import numpy as np

def impute_scale(train, test):
    pass
''',
    solution='''import numpy as np

def _to_arr(M):
    return np.array([[np.nan if v is None else float(v) for v in row] for row in M], dtype=float)

def impute_scale(train, test):
    A = _to_arr(train)
    B = _to_arr(test).reshape(-1, A.shape[1])
    fill = np.nanmean(A, axis=0)                       # imputer.fit(train)
    A = np.where(np.isnan(A), fill, A)                 # imputer.transform(train)
    mu, sd = A.mean(axis=0), A.std(axis=0)             # scaler.fit(imputed train)
    sd[sd == 0] = 1.0
    B = np.where(np.isnan(B), fill, B)                 # imputer.transform(test)
    return (B - mu) / sd                               # scaler.transform(test)
''',
    tests=[
        [[[1], [None], [3]], [[None], [5]]],
        [[[1, 10], [2, None], [3, 30]], [[None, None], [2, 20]]],
        [[[5, 1], [5, 2]], [[None, 3], [7, None]]],
        [[[1, None], [None, 4], [3, 8]], [[0, 0]]],
        [[[2.5]], [[None], [2.5], [3.5]]],
        [[[1, 2], [3, 4], [5, 6]], [[None, 6], [1, None]]],
        [_with_missing(20, 3), _with_missing(6, 3)],
        [_with_missing(50, 5, 0.3), _with_missing(10, 5, 0.3)],
        [_with_missing(10, 2, 0.5), _with_missing(10, 2, 0.5)],
        [[[0, 100], [None, 200], [10, None], [20, 400]], [[None, None], [5, 250]]],
    ],
    wrong_solutions=[
        '''import numpy as np
def impute_scale(train, test):
    f = lambda M: np.array([[np.nan if v is None else float(v) for v in r] for r in M])
    A = f(train); B = f(test).reshape(-1, A.shape[1])
    allx = np.vstack([A, B]); fill = np.nanmean(allx, 0)        # leak: test used in fit
    A = np.where(np.isnan(A), fill, A); B = np.where(np.isnan(B), fill, B)
    mu, sd = A.mean(0), A.std(0); sd[sd == 0] = 1
    return (B - mu) / sd
''',
        '''import numpy as np
def impute_scale(train, test):
    f = lambda M: np.array([[np.nan if v is None else float(v) for v in r] for r in M])
    A = f(train); B = f(test).reshape(-1, A.shape[1])
    fill = np.nanmean(A, 0)
    mu, sd = np.nanmean(A, 0), np.nanstd(A, 0); sd[sd == 0] = 1   # scaler fit before imputing
    B = np.where(np.isnan(B), fill, B)
    return (B - mu) / sd
''',
    ],
    guide=dict(
        prereqs="StandardScaler problem; Pipelines module (both lessons).",
        intuition=r"""A pipeline chains transformers: `fit` calls `fit_transform` on each step in turn, feeding each step the
**output of the previous step**, and the final `transform`/`predict` replays the learned steps. Two consequences you
implement here: (1) every statistic is learned from training data only — no leakage; (2) the scaler sees the *imputed*
data, so its standard deviation is slightly smaller than the std of the observed values.""",
        hints=[
            "Convert None to `np.nan`, then `np.nanmean(A, axis=0)` gives the imputer means.",
            "`np.where(np.isnan(A), fill, A)` imputes with broadcasting.",
            "Fit the scaler on the imputed training matrix, then transform the imputed test matrix.",
        ],
        brute_force="Per-column loops; same complexity.",
        approach=r"""Example: train column [1, None, 3] → mean 2 → imputed [1,2,3] → μ=2, σ=√(2/3)=0.8165.
Test [None] → 2 → (2−2)/σ = 0; test [5] → (5−2)/0.8165 = 3.674.""",
        complexity="O((n_train + n_test)·d).",
        pitfalls=r"""- Computing imputation means on train+test (leakage; with cross-validation this inflates scores).
- Fitting the scaler on the raw data with NaNs instead of the imputer's output.
- A test row that is entirely missing should still work (it becomes the training means → zeros after scaling).""",
        follow_up="Add a missing-indicator column (`SimpleImputer(add_indicator=True)`), or route numeric and categorical columns differently with ColumnTransformer.",
    ),
),

# ---------------------------------------------------------------- tf-idf
dict(
    id="ml-tfidf",
    title="TF-IDF Vectorizer (scikit-learn defaults)",
    difficulty="Medium",
    pattern="Text",
    kind="function",
    entry="tfidf",
    compare="float",
    description=r"""
Reproduce `TfidfVectorizer()` with its default settings on a small `corpus` (list of strings):

1. **Tokenise**: lowercase, then tokens are matches of the regex `\b\w\w+\b` (words of 2+ word characters; single
   letters are dropped).
2. **Vocabulary**: all distinct tokens, sorted alphabetically (these are the columns).
3. **tf** = raw count of the term in the document; **idf** (smoothed)
   $$\operatorname{idf}(t)=\ln\frac{1+N}{1+\operatorname{df}(t)}+1$$
   where $N$ is the number of documents and df the number of documents containing $t$.
4. Each row tf·idf is **L2-normalised** (a row of all zeros stays zeros).

Return `[vocabulary, matrix]`.

**Example:** `["the cat", "the dog"]` → vocab `["cat","dog","the"]`, rows `[[0.8148,0,0.5797],[0,0.8148,0.5797]]`
""",
    starter='''import numpy as np
import re

def tfidf(corpus):
    pass
''',
    solution='''import numpy as np
import re

def tfidf(corpus):
    tok = re.compile(r"(?u)\\b\\w\\w+\\b")
    docs = [tok.findall(d.lower()) for d in corpus]
    vocab = sorted({t for d in docs for t in d})
    pos = {t: i for i, t in enumerate(vocab)}
    N = len(docs)
    tf = np.zeros((N, len(vocab)))
    for i, d in enumerate(docs):
        for t in d:
            tf[i, pos[t]] += 1
    df = (tf > 0).sum(axis=0)
    idf = np.log((1 + N) / (1 + df)) + 1
    X = tf * idf
    norms = np.linalg.norm(X, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return [vocab, X / norms]
''',
    tests=[
        [["the cat", "the dog"]],
        [["a b c dd"]],
        [["Hello hello world"]],
        [["The quick brown fox", "jumped over the lazy dog", "The dog sleeps"]],
        [["spam spam spam eggs", "eggs and ham", "ham"]],
        [["I", "x y", "ok ok"]],
        [["This movie was great!", "This movie was terrible...", "Great acting, great plot."]],
        [["data science is fun", "machine learning is fun", "deep learning is a subset of machine learning",
          "data data data"]],
        [["it's 2024 and C3PO says hi", "R2D2: beep_boop beep"]],
        [["same text", "same text", "same text"]],
    ],
    wrong_solutions=[
        '''import numpy as np, re
def tfidf(corpus):
    docs = [re.findall(r"\\b\\w\\w+\\b", d.lower()) for d in corpus]
    vocab = sorted({t for d in docs for t in d}); pos = {t: i for i, t in enumerate(vocab)}; N = len(docs)
    tf = np.zeros((N, len(vocab)))
    for i, d in enumerate(docs):
        for t in d: tf[i, pos[t]] += 1
    idf = np.log(N / (tf > 0).sum(0))
    X = tf * idf; n = np.linalg.norm(X, axis=1, keepdims=True); n[n == 0] = 1
    return [vocab, X / n]
''',
        '''import numpy as np, re
def tfidf(corpus):
    docs = [d.lower().split() for d in corpus]
    vocab = sorted({t for d in docs for t in d}); pos = {t: i for i, t in enumerate(vocab)}; N = len(docs)
    tf = np.zeros((N, len(vocab)))
    for i, d in enumerate(docs):
        for t in d: tf[i, pos[t]] += 1
    idf = np.log((1 + N) / (1 + (tf > 0).sum(0))) + 1
    X = tf * idf; n = np.linalg.norm(X, axis=1, keepdims=True); n[n == 0] = 1
    return [vocab, X / n]
''',
    ],
    guide=dict(
        prereqs="Bag of words and tf-idf (Working with text, lesson 1); cosine similarity problem.",
        intuition=r"""Bag-of-words counts words and throws away order. tf-idf then re-weights: a word that appears in every
document ("the") carries little information, so its idf is small; a word that appears in few documents is
distinctive. L2-normalising each row makes long and short documents comparable — the dot product of two rows is
then their cosine similarity.""",
        hints=[
            "`re.findall(r'(?u)\\b\\w\\w+\\b', text.lower())` is exactly scikit-learn's default token pattern.",
            "df(t) = number of documents with count > 0, i.e. `(tf > 0).sum(axis=0)`.",
            "Smoothed idf = ln((1+N)/(1+df)) + 1; finish with row-wise L2 normalisation.",
        ],
        brute_force="Python dicts of dicts work identically — the matrix is just tidier.",
        approach=r"""Example: N=2. "the" has df=2 → idf = ln(3/3)+1 = 1; "cat"/"dog" have df=1 → idf = ln(3/2)+1 = 1.405.
Row 1 = [1.405, 0, 1] / ‖·‖ = [1.405, 0, 1]/1.7247 = [0.8148, 0, 0.5797].""",
        complexity="O(total tokens + N·V) with a dense matrix (scikit-learn uses a sparse matrix, O(nnz)).",
        pitfalls=r"""- Splitting on whitespace keeps punctuation ("great!" ≠ "great") and single letters.
- The unsmoothed idf ln(N/df) gives 0 weight to words in every document and divides by zero at transform time for unseen words.
- Fit the vocabulary and idf on training documents only (use a Pipeline in cross-validation).""",
        follow_up="Add `ngram_range=(1,2)`, `min_df`, `stop_words='english'`, or `sublinear_tf=True` (tf → 1 + ln tf).",
    ),
),

# ---------------------------------------------------------------- Adam
dict(
    id="ml-adam-step",
    title="Adam Optimizer Updates",
    difficulty="Medium",
    pattern="Deep Learning",
    kind="function",
    entry="adam",
    compare="float",
    description=r"""
Apply Adam to a parameter vector `theta` for a sequence of precomputed gradients `grads` (a list of $T$ gradient
vectors; step $t$ uses `grads[t-1]`). With $m_0=v_0=0$:

$$m_t=\beta_1 m_{t-1}+(1-\beta_1)g_t,\quad v_t=\beta_2 v_{t-1}+(1-\beta_2)g_t^2,$$
$$\hat m_t=\frac{m_t}{1-\beta_1^t},\quad \hat v_t=\frac{v_t}{1-\beta_2^t},\quad \theta_t=\theta_{t-1}-\eta\frac{\hat m_t}{\sqrt{\hat v_t}+\epsilon}.$$

Return the final `theta` (list). `T` may be 0.

**Example:** `theta=[1.0], grads=[[0.5]], lr=0.1, beta1=0.9, beta2=0.999, eps=1e-8` → `[0.9]` (the first Adam step moves each coordinate by ≈ lr·sign(g))
""",
    starter='''import numpy as np

def adam(theta, grads, lr, beta1, beta2, eps):
    pass
''',
    solution='''import numpy as np

def adam(theta, grads, lr, beta1, beta2, eps):
    th = np.asarray(theta, dtype=float).copy()
    m = np.zeros_like(th)
    v = np.zeros_like(th)
    for t, g in enumerate(grads, start=1):
        g = np.asarray(g, dtype=float)
        m = beta1 * m + (1 - beta1) * g
        v = beta2 * v + (1 - beta2) * g * g
        mh = m / (1 - beta1 ** t)
        vh = v / (1 - beta2 ** t)
        th -= lr * mh / (np.sqrt(vh) + eps)
    return th.tolist()
''',
    tests=[
        [[1.0], [[0.5]], 0.1, 0.9, 0.999, 1e-8],
        [[1.0, -1.0], [], 0.1, 0.9, 0.999, 1e-8],
        [[0.0, 0.0], [[1, -100], [1, -100]], 0.01, 0.9, 0.999, 1e-8],
        [[2.0], [[1.0], [-1.0], [1.0], [-1.0]], 0.1, 0.9, 0.999, 1e-8],
        [[0.5, 0.5, 0.5], [[0.1, 0.0, -0.2]] * 5, 0.05, 0.9, 0.99, 1e-8],
        [[1.0], [[0.0], [0.0]], 0.1, 0.9, 0.999, 1e-8],
        [_r(4), _r(10, 4), 0.001, 0.9, 0.999, 1e-8],
        [_r(6), _r(50, 6, scale=10), 0.01, 0.8, 0.95, 1e-6],
        [[3.0], [[1e-6]] * 3, 0.1, 0.9, 0.999, 1e-8],
        [_r(3), _r(20, 3), 0.1, 0.0, 0.0, 1e-8],
    ],
    wrong_solutions=[
        '''import numpy as np
def adam(theta, grads, lr, beta1, beta2, eps):
    th = np.asarray(theta, float).copy(); m = np.zeros_like(th); v = np.zeros_like(th)
    for g in grads:
        g = np.asarray(g, float)
        m = beta1 * m + (1 - beta1) * g; v = beta2 * v + (1 - beta2) * g * g
        th -= lr * m / (np.sqrt(v) + eps)          # no bias correction
    return th.tolist()
''',
        '''import numpy as np
def adam(theta, grads, lr, beta1, beta2, eps):
    th = np.asarray(theta, float).copy(); m = np.zeros_like(th); v = np.zeros_like(th)
    for t, g in enumerate(grads, 1):
        g = np.asarray(g, float)
        m = beta1 * m + (1 - beta1) * g; v = beta2 * v + (1 - beta2) * g * g
        th -= lr * (m / (1 - beta1 ** t)) / np.sqrt(v / (1 - beta2 ** t) + eps)
    return th.tolist()
''',
    ],
    guide=dict(
        prereqs="Gradient descent (Math, lesson 2); optimizers (Deep learning, lesson 1).",
        intuition=r"""Adam combines **momentum** ($m$: an exponential moving average of gradients, which smooths noisy directions)
with **per-parameter step sizes** ($v$: a moving average of squared gradients — parameters with consistently large gradients
take smaller steps, rarely-updated ones take larger steps). Because $m$ and $v$ start at 0, early averages are biased
toward 0; dividing by $1-\beta^t$ corrects that bias.""",
        hints=[
            "Keep m and v as arrays the same shape as theta, starting at 0.",
            "t starts at 1 for the bias correction.",
            "eps is added to sqrt(v_hat), not inside the square root.",
        ],
        brute_force="Not applicable; it is a direct recurrence.",
        approach=r"""Step 1 with g=0.5: m=0.05, v=0.00025; m̂=0.5, v̂=0.25 → update = 0.1·0.5/0.5 = 0.1 → θ=0.9.
In general the first step is ≈ lr·sign(g), independent of gradient scale — Adam is scale-invariant per coordinate.""",
        complexity="O(T·p) time, O(p) extra memory (two moment vectors — that's why Adam triples optimizer memory compared with plain SGD's parameters alone).",
        pitfalls=r"""- Missing bias correction makes early steps far too small.
- Putting eps inside the sqrt (that's a different variant).
- AdamW ≠ Adam + L2: AdamW decays weights directly ($\theta \leftarrow \theta - \eta\lambda\theta$) instead of adding $\lambda\theta$ to the gradient.""",
        follow_up="Implement SGD with momentum and RMSProp, and AdamW's decoupled weight decay.",
    ),
),

# ---------------------------------------------------------------- attention
dict(
    id="ml-attention",
    title="Scaled Dot-Product Attention",
    difficulty="Medium",
    pattern="Deep Learning",
    kind="function",
    entry="attention",
    compare="float",
    description=r"""
Implement single-head scaled dot-product attention

$$\operatorname{Attn}(Q,K,V)=\operatorname{softmax}\!\left(\frac{QK^\top}{\sqrt{d_k}}\right)V$$

with `Q` ($n\times d_k$), `K` ($m\times d_k$), `V` ($m\times d_v$). If `causal` is true ($n = m$), query $i$ may only attend
to keys $j\le i$: set the other scores to $-\infty$ before the softmax. Use a stable softmax. Return the $n\times d_v$ output.

**Example:** `Q=[[1,0]]`, `K=[[1,0],[0,1]]`, `V=[[1,2],[3,4]]`, `causal=False` → `[[1.6604, 2.6604]]`
""",
    starter='''import numpy as np

def attention(Q, K, V, causal):
    pass
''',
    solution='''import numpy as np

def attention(Q, K, V, causal):
    Q, K, V = (np.asarray(a, dtype=float) for a in (Q, K, V))
    S = Q @ K.T / np.sqrt(Q.shape[1])
    if causal:
        n, m = S.shape
        S = np.where(np.tril(np.ones((n, m), dtype=bool)), S, -np.inf)
    S = S - S.max(axis=1, keepdims=True)
    W = np.exp(S)
    W /= W.sum(axis=1, keepdims=True)
    return W @ V
''',
    tests=[
        [[[1, 0]], [[1, 0], [0, 1]], [[1, 2], [3, 4]], False],
        [[[0, 0]], [[1, 0], [0, 1]], [[1, 2], [3, 4]], False],
        [[[1, 0], [0, 1]], [[1, 0], [0, 1]], [[1, 2], [3, 4]], True],
        [[[100, 0]], [[100, 0], [-100, 0]], [[5], [7]], False],
        [[[1, 2, 3], [4, 5, 6], [7, 8, 9]], [[1, 0, 0], [0, 1, 0], [0, 0, 1]], [[1], [2], [3]], True],
        [_r(4, 8), _r(6, 8), _r(6, 5), False],
        [_r(5, 4), _r(5, 4), _r(5, 3), True],
        [_r(10, 16, scale=3), _r(10, 16, scale=3), _r(10, 16), True],
        [_r(3, 64, scale=2), _r(7, 64, scale=2), _r(7, 2), False],
        [[[2]], [[3]], [[9, -9]], True],
    ],
    wrong_solutions=[
        '''import numpy as np
def attention(Q, K, V, causal):
    Q, K, V = (np.asarray(a, float) for a in (Q, K, V))
    S = Q @ K.T
    if causal: S = np.where(np.tril(np.ones(S.shape, bool)), S, -np.inf)
    W = np.exp(S - S.max(1, keepdims=True)); W /= W.sum(1, keepdims=True)
    return W @ V
''',
        '''import numpy as np
def attention(Q, K, V, causal):
    Q, K, V = (np.asarray(a, float) for a in (Q, K, V))
    S = Q @ K.T / np.sqrt(Q.shape[1])
    W = np.exp(S - S.max(1, keepdims=True)); W /= W.sum(1, keepdims=True)
    return W @ V
''',
    ],
    guide=dict(
        prereqs="Softmax problem; embeddings and attention (Deep learning, lesson 3).",
        intuition=r"""Each query asks "which keys are relevant to me?" via dot products; softmax turns relevance scores into
weights summing to 1; the output is the weighted average of the values. Dividing by $\sqrt{d_k}$ keeps the
scores' variance ≈ 1 when components are unit-variance (a dot product of $d_k$ such terms has variance $d_k$), which
stops the softmax from saturating into a near one-hot with vanishing gradients.""",
        hints=[
            "Scores: `Q @ K.T / sqrt(d_k)` → shape (n, m).",
            "Causal mask: `np.tril` of ones gives the allowed (j ≤ i) positions; fill the rest with -inf.",
            "Row-wise stable softmax, then multiply by V.",
        ],
        brute_force="Loops over queries computing weights one at a time: same O(n·m·d).",
        approach=r"""Example: scores $[1,0]/\sqrt2 = [0.707, 0]$ → weights $[0.670, 0.330]$ → output $0.670[1,2]+0.330[3,4]=[1.660,2.660]$.
With the causal mask the first query sees only the first key, so its output is exactly $V_0$.""",
        complexity="O(n·m·(d_k + d_v)) time, O(n·m) memory for the score matrix — the quadratic cost that motivates FlashAttention and sparse/linear attention.",
        pitfalls=r"""- Forgetting the $\sqrt{d_k}$ scale.
- Masking after the softmax (the weights then no longer sum to 1).
- Softmax over the wrong axis (must normalise over keys, axis=1).""",
        follow_up="Multi-head attention: project Q, K, V into h subspaces, attend in each, concatenate, project back.",
    ),
),
]
