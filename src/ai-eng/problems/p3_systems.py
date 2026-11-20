import random as _r

_g = _r.Random(11)


def _vec(d):
    return [round(_g.uniform(-1, 1), 3) for _ in range(d)]


_W = ["the", "quick", "brown", "fox", "jumps", "over", "lazy", "dog", "cat", "sat", "on", "mat", "a", "red", "pencil"]


def _sent(n):
    return " ".join(_g.choice(_W) for _ in range(n))


def _near(base):
    words = base.split()
    i = _g.randrange(len(words))
    words[i] = _g.choice(_W)
    return " ".join(words)


_bases = [_sent(12) for _ in range(15)]
_dedup_big = []
for _b in _bases:
    _dedup_big.append(_b)
    if _g.random() < 0.6:
        _dedup_big.append(_near(_b))
    if _g.random() < 0.3:
        _dedup_big.append(_b.upper() + "!")

_cache_stream = []
_centers = [_vec(6) for _ in range(8)]
for _i in range(120):
    _c = _g.choice(_centers)
    _cache_stream.append([[round(x + _g.uniform(-0.08, 0.08), 3) for x in _c], "ans%d" % _i])

_bucket_ops = ["TokenBucket"] + ["allow"] * 200
_t = 0.0
_bucket_args = [[1000, 250]]
for _i in range(200):
    _t = round(_t + _g.choice([0.0, 0.1, 0.25, 0.5, 2.0]), 2)
    _bucket_args.append([_t, _g.choice([50, 100, 300, 700, 1200])])

PROBLEMS = [
# ---------------------------------------------------------------- model memory
dict(
    id="aie-model-memory",
    title="Model Memory for Inference and Training",
    difficulty="Easy",
    pattern="Finetuning",
    entry="model_memory",
    compare="float",
    description=r"""
Estimate a model's memory footprint with the back-of-envelope formulas from the finetuning module.
Use **1 GB = 10⁹ bytes**.

`model_memory(num_params, bytes_per_param, trainable_params, optimizer, overhead)` returns
`[inference_gb, training_gb]`:

- **Inference** = `num_params × bytes_per_param × (1 + overhead)` (weights plus activations / KV vectors;
  the book's rule of thumb is `overhead = 0.2`).
- **Training** = inference memory **plus** gradients and optimizer states for the *trainable* parameters:
  `trainable_params × (1 + states) × bytes_per_param`, where `states` is `0` for `"sgd"`, `1` for
  `"momentum"` and `2` for `"adam"`.

**Example:** `model_memory(13e9, 2, 13e9, "adam", 0.2)` → `[31.2, 109.2]`
(26 GB weights × 1.2 = 31.2 GB; plus 13B × 3 × 2 bytes = 78 GB).

**Example:** `model_memory(13e9, 2, 1e9, "adam", 0.2)` → `[31.2, 37.2]`
""",
    starter='''def model_memory(num_params, bytes_per_param, trainable_params, optimizer, overhead):
    pass
''',
    solution='''def model_memory(num_params, bytes_per_param, trainable_params, optimizer, overhead):
    states = {"sgd": 0, "momentum": 1, "adam": 2}[optimizer]
    inference = num_params * bytes_per_param * (1 + overhead)
    training = inference + trainable_params * (1 + states) * bytes_per_param
    return [inference / 1e9, training / 1e9]
''',
    tests=[
        [13e9, 2, 13e9, "adam", 0.2],
        [13e9, 2, 1e9, "adam", 0.2],
        [7e9, 2, 0, "adam", 0.2],
        [70e9, 2, 70e9, "sgd", 0.2],
        [70e9, 0.5, 4.7e6, "adam", 0.2],
        [10e9, 4, 10e9, "momentum", 0.0],
        [3e9, 1, 3.28e6, "adam", 0.5],
        [175e9, 2, 18874368, "adam", 0.2],
        [1, 1, 1, "sgd", 0],
        [8e9, 2, 8e9, "momentum", 0.2],
    ],
    examples=2,
    wrong_solutions=[
        '''def model_memory(num_params, bytes_per_param, trainable_params, optimizer, overhead):
    states = {"sgd": 0, "momentum": 1, "adam": 2}[optimizer]
    inference = num_params * bytes_per_param * (1 + overhead)
    return [inference / 1e9, (inference + trainable_params * states * bytes_per_param) / 1e9]
''',
        '''def model_memory(num_params, bytes_per_param, trainable_params, optimizer, overhead):
    states = {"sgd": 0, "momentum": 1, "adam": 2}[optimizer]
    inference = num_params * bytes_per_param * (1 + overhead)
    return [inference / 1e9, (inference + num_params * (1 + states) * bytes_per_param) / 1e9]
''',
    ],
    guide=dict(
        prereqs="Memory math lesson: inference vs training memory, optimizer states.",
        intuition="Inference only stores weights and some working memory. Training additionally stores, for every "
                  "parameter you update, its gradient and whatever the optimizer remembers about it. Fewer "
                  "trainable parameters means much less extra memory, which is the idea behind PEFT.",
        hints=["Map the optimizer name to 0, 1 or 2 extra values.",
               "Each trainable parameter needs 1 gradient value plus the optimizer states.",
               "Divide bytes by 1e9, not 2**30."],
        brute_force="This is a direct formula.",
        approach="inference = N·M·(1+overhead). training = inference + T·(1+states)·M. Convert to GB.",
        complexity="O(1).",
        pitfalls="- Forgetting the gradient itself (the `1 +`).\n- Using all parameters instead of trainable ones.\n- GiB vs GB.",
        follow_up="Add activation memory that scales with batch size and sequence length, or model gradient checkpointing as a reduced activation term.",
    ),
),
# ---------------------------------------------------------------- LoRA params
dict(
    id="aie-lora-params",
    title="LoRA Trainable Parameters",
    difficulty="Easy",
    pattern="Finetuning",
    entry="lora_stats",
    compare="float",
    description=r"""
LoRA replaces the update of an $n \times m$ weight matrix by two matrices $A$ ($n \times r$) and
$B$ ($r \times m$), which have $r\,(n+m)$ parameters in total.

`lora_stats(shapes, r, num_layers, total_params, bytes_per_param)`:
- `shapes` lists the `[n, m]` shapes of the matrices LoRA is applied to **in each layer** (for example
  the query and value matrices);
- the same matrices are adapted in each of the `num_layers` layers.

Return `[trainable, percent, adapter_mb]` where
- `trainable` = total LoRA parameters (an integer),
- `percent` = `100 × trainable / total_params`,
- `adapter_mb` = adapter size in megabytes (`trainable × bytes_per_param / 10⁶`).

**Example (GPT-3 in the LoRA paper):** four attention matrices of `12288 × 12288`, `r = 2`, 96 layers
→ `(12288 × 2 × 2) × 4 × 96 = 18,874,368` trainable parameters:
`lora_stats([[12288,12288]]*4, 2, 96, 175e9, 2)` → `[18874368, 0.010785, 37.748736]`

**Example:** `lora_stats([[4096, 4096]], 8, 1, 16777216, 2)` → `[65536, 0.390625, 0.131072]`
""",
    starter='''def lora_stats(shapes, r, num_layers, total_params, bytes_per_param):
    pass
''',
    solution='''def lora_stats(shapes, r, num_layers, total_params, bytes_per_param):
    per_layer = sum(r * (n + m) for n, m in shapes)
    trainable = per_layer * num_layers
    return [trainable, 100.0 * trainable / total_params, trainable * bytes_per_param / 1e6]
''',
    tests=[
        [[[12288, 12288]] * 4, 2, 96, 175e9, 2],
        [[[4096, 4096]], 8, 1, 16777216, 2],
        [[[5120, 5120], [5120, 5120]], 2, 40, 13e9, 2],
        [[[4096, 4096], [4096, 4096], [4096, 11008], [11008, 4096]], 16, 32, 7e9, 2],
        [[], 8, 12, 1e9, 2],
        [[[9, 9]], 1, 1, 81, 4],
        [[[768, 768], [768, 3072]], 64, 12, 110e6, 4],
        [[[4096, 1024]], 4, 32, 8e9, 0.5],
        [[[100, 200], [300, 50]], 256, 3, 1e6, 2],
        [[[8192, 8192]] * 4, 8, 80, 70e9, 2],
    ],
    examples=2,
    wrong_solutions=[
        '''def lora_stats(shapes, r, num_layers, total_params, bytes_per_param):
    t = sum(r * n * m for n, m in shapes) * num_layers
    return [t, 100.0 * t / total_params, t * bytes_per_param / 1e6]
''',
        '''def lora_stats(shapes, r, num_layers, total_params, bytes_per_param):
    t = sum(r * (n + m) for n, m in shapes)
    return [t, 100.0 * t / total_params, t * bytes_per_param / 1e6]
''',
    ],
    guide=dict(
        prereqs="PEFT/LoRA lesson: W' = W + (α/r)·AB.",
        intuition="A rank-r update of an n×m matrix is described by n·r + r·m numbers instead of n·m. "
                  "Sum that over every adapted matrix in every layer.",
        hints=["A has n·r parameters and B has r·m.", "Multiply the per-layer total by num_layers.", "Megabytes use 1e6 bytes."],
        brute_force="Direct formula.",
        approach="per_layer = Σ r(n+m); trainable = per_layer × layers; percent and MB follow.",
        complexity="O(len(shapes)).",
        pitfalls="- Using r·n·m.\n- Forgetting the layer multiplier.\n- Percent vs fraction.",
        follow_up="Compare storage for 100 customers: merged full matrices versus one base plus 100 adapters (multi-LoRA serving).",
    ),
),
# ---------------------------------------------------------------- int8 quant
dict(
    id="aie-int8-quant",
    title="Symmetric Integer Quantize / Dequantize",
    difficulty="Medium",
    pattern="Finetuning",
    entry="quantize_roundtrip",
    compare="float",
    description=r"""
Implement symmetric linear quantization of a list of weights to signed `bits`-bit integers.

`quantize_roundtrip(weights, bits)` returns `[q, scale, dequantized, max_abs_error]`:

- `qmax = 2^(bits-1) - 1` (127 for 8 bits, 7 for 4 bits).
- `scale = max(|w|) / qmax`. If all weights are zero (or the list is empty) use `scale = 1.0`.
- `q_i = clip(round_half_away(w_i / scale), -qmax, qmax)` as integers, where
  `round_half_away(x) = sign(x) × floor(|x| + 0.5)`.
- `dequantized_i = q_i × scale`.
- `max_abs_error = max |w_i - dequantized_i|` (0.0 for an empty list).

**Example:** `quantize_roundtrip([0.5, -1.0, 0.25], 8)` → scale = 1/127;
`q = [64, -127, 32]`; dequantized ≈ `[0.50394, -1.0, 0.25197]`; max error ≈ `0.003937`.
""",
    starter='''import math

def quantize_roundtrip(weights, bits):
    pass
''',
    solution='''import math
def quantize_roundtrip(weights, bits):
    qmax = 2 ** (bits - 1) - 1
    mx = max((abs(w) for w in weights), default=0.0)
    scale = mx / qmax if mx > 0 else 1.0
    q = []
    for w in weights:
        x = w / scale
        v = int(math.floor(abs(x) + 0.5))
        v = -v if x < 0 else v
        q.append(max(-qmax, min(qmax, v)))
    deq = [v * scale for v in q]
    err = max((abs(w - d) for w, d in zip(weights, deq)), default=0.0)
    return [q, scale, deq, err]
''',
    tests=[
        [[0.5, -1.0, 0.25], 8],
        [[0.5, -1.0, 0.25], 4],
        [[0.0, 0.0, 0.0], 8],
        [[], 8],
        [[3.0], 8],
        [[1.0, 0.5, -0.5, 0.25, -0.75], 2],
        [[127, 63.5, -63.5, 0.5, -0.5, 1.5, 2.5], 8],
        [[0.001, -0.002, 0.0005, 5.0], 8],
        [[round(_g.gauss(0, 0.05), 5) for _ in range(500)], 8],
        [[round(_g.gauss(0, 0.05), 5) for _ in range(500)], 4],
        [[-7, -3.5, 0, 3.5, 7], 4],
        [[1e-9, -1e-9], 16],
    ],
    examples=1,
    wrong_solutions=[
        # banker's rounding (Python round)
        '''def quantize_roundtrip(weights, bits):
    qmax = 2 ** (bits - 1) - 1
    mx = max((abs(w) for w in weights), default=0.0)
    scale = mx / qmax if mx > 0 else 1.0
    q = [max(-qmax, min(qmax, int(round(w / scale)))) for w in weights]
    deq = [v * scale for v in q]
    return [q, scale, deq, max((abs(w - d) for w, d in zip(weights, deq)), default=0.0)]
''',
        # asymmetric range: uses 2^(bits-1) as the divisor
        '''import math
def quantize_roundtrip(weights, bits):
    qmax = 2 ** (bits - 1)
    mx = max((abs(w) for w in weights), default=0.0)
    scale = mx / qmax if mx > 0 else 1.0
    q = []
    for w in weights:
        x = w / scale; v = int(math.floor(abs(x) + 0.5)); v = -v if x < 0 else v
        q.append(max(-qmax, min(qmax, v)))
    deq = [v * scale for v in q]
    return [q, scale, deq, max((abs(w - d) for w, d in zip(weights, deq)), default=0.0)]
''',
    ],
    guide=dict(
        prereqs="Quantization lesson (PTQ, INT8/INT4), basic rounding.",
        intuition="Map the largest magnitude to the largest integer and space everything else evenly. Each weight "
                  "moves to the nearest grid point, so the error is at most half a step (scale / 2). Fewer bits "
                  "mean a coarser grid.",
        hints=["Compute scale from the max absolute value, guarding against zero.",
               "Python's round() uses banker's rounding. Implement half-away-from-zero yourself.",
               "Dequantize by multiplying back and compare with the original."],
        brute_force="Direct computation.",
        approach="qmax → scale → q (round, clip) → dequantize → max error. Dry run [0.5,-1,0.25] at 8 bits: "
                 "scale = 1/127; 0.5·127 = 63.5 → 64; -127; 31.75 → 32.",
        complexity="O(n).",
        pitfalls="- Banker's rounding at .5.\n- Division by zero for all-zero input.\n- Using 128 as the positive max (symmetric uses ±127).",
        follow_up="Add percentile clipping to limit the effect of outliers, or per-channel scales, and compare the mean error.",
    ),
),
# ---------------------------------------------------------------- near dedup
dict(
    id="aie-near-dedup",
    title="Near-Duplicate Removal with N-gram Jaccard",
    difficulty="Medium",
    pattern="Dataset Engineering",
    entry="dedup",
    description=r"""
Duplicates skew a training set and can leak test examples into training. Implement a simple
near-duplicate filter.

`dedup(texts, n, threshold)` returns the list of **kept indices**:

1. Tokenise each text with `re.findall(r"[a-z0-9]+", text.lower())`.
2. Its **shingle set** is the set of all n-grams (tuples of `n` consecutive tokens). If the text has
   fewer than `n` tokens but at least one, the set contains one shingle: the tuple of all its tokens.
   A text with no tokens has an empty set.
3. Jaccard similarity $J(A,B) = |A\cap B| / |A\cup B|$; define $J = 1$ when both sets are empty.
4. Go through texts **in order**. Keep a text only if its similarity with **every previously kept**
   text is **strictly less than** `threshold`.

**Example:** `dedup(["The cat sat on the mat", "the cat sat on the mat!", "A dog barked"], 2, 0.8)`
→ `[0, 2]` (the second is an exact duplicate after normalisation).
""",
    starter='''import re

def dedup(texts, n, threshold):
    pass
''',
    solution='''import re
def dedup(texts, n, threshold):
    def shingles(t):
        toks = re.findall(r"[a-z0-9]+", t.lower())
        if not toks:
            return frozenset()
        if len(toks) < n:
            return frozenset([tuple(toks)])
        return frozenset(tuple(toks[i:i + n]) for i in range(len(toks) - n + 1))
    kept, kept_sets = [], []
    for i, t in enumerate(texts):
        s = shingles(t)
        dup = False
        for k in kept_sets:
            union = len(s | k)
            j = 1.0 if union == 0 else len(s & k) / union
            if j >= threshold:
                dup = True
                break
        if not dup:
            kept.append(i)
            kept_sets.append(s)
    return kept
''',
    tests=[
        [["The cat sat on the mat", "the cat sat on the mat!", "A dog barked"], 2, 0.8],
        [["a b c d e", "a b c d f", "x y z"], 2, 0.5],
        [["a b c d e", "a b c d f", "x y z"], 2, 0.7],
        [[], 3, 0.5],
        [["", "   ", "!!!", "word"], 2, 0.9],
        [["hi", "hi", "hi there", "there hi"], 3, 1.0],
        [["one two three", "three two one", "one two three four"], 1, 0.75],
        [["one two three", "three two one", "one two three four"], 2, 0.75],
        [["same", "SAME", "Same."], 1, 0.01],
        [["a b", "c d", "a b c d"], 2, 0.3],
        [_dedup_big, 3, 0.6],
        [_dedup_big, 2, 0.9],
        [_dedup_big, 1, 0.5],
    ],
    examples=1,
    wrong_solutions=[
        # exact-match dedup only
        '''def dedup(texts, n, threshold):
    seen, kept = set(), []
    for i, t in enumerate(texts):
        if t not in seen:
            seen.add(t); kept.append(i)
    return kept
''',
        # compares with ALL previous texts (including dropped ones)
        '''import re
def dedup(texts, n, threshold):
    def sh(t):
        toks = re.findall(r"[a-z0-9]+", t.lower())
        if not toks: return frozenset()
        if len(toks) < n: return frozenset([tuple(toks)])
        return frozenset(tuple(toks[i:i + n]) for i in range(len(toks) - n + 1))
    sets = [sh(t) for t in texts]; kept = []
    for i, s in enumerate(sets):
        ok = True
        for k in sets[:i]:
            u = len(s | k); j = 1.0 if u == 0 else len(s & k) / u
            if j >= threshold: ok = False; break
        if ok: kept.append(i)
    return kept
''',
    ],
    guide=dict(
        prereqs="Sets, n-grams, the dataset engineering lesson on deduplication.",
        intuition="Two texts that share most of their word n-grams are near duplicates even if punctuation, case "
                  "or one word differs. Jaccard similarity on shingle sets measures that overlap. Comparing only "
                  "with kept items makes the result a set of mutually distinct representatives.",
        hints=["Build each text's shingle set once.", "Handle short and empty texts explicitly.",
               "Compare with kept sets only, and stop at the first match."],
        brute_force="This pairwise comparison IS the simple approach: O(k) set operations per text, O(N²) overall.",
        approach="For each text compute shingles; scan the kept sets; keep it if all similarities are below the threshold.",
        complexity="O(N·K·S) for K kept items and shingle sets of size S. Fine for small data and too slow for web-scale data.",
        pitfalls="- Comparing against dropped items (chains of near-duplicates then delete too much).\n- `>=` vs `>` at the threshold.\n- Empty union.",
        follow_up="Scale it with MinHash signatures and locality-sensitive hashing so only texts in the same bucket are compared.",
    ),
),
# ---------------------------------------------------------------- KV cache
dict(
    id="aie-kv-cache",
    title="KV-Cache Memory Estimate",
    difficulty="Easy",
    pattern="Inference Optimization",
    entry="kv_cache_gb",
    compare="float",
    description=r"""
During decoding a transformer caches a **key** and a **value** vector per token, per layer. Without
optimisation the cache needs

$$2 \times B \times S \times L \times H \times M \ \text{bytes}$$

with batch size $B$, sequence length $S$, layers $L$, model dimension $H$ and $M$ bytes per value.

Implement `kv_cache_gb(batch, seq_len, layers, model_dim, bytes_per_value, num_heads, num_kv_heads, window)`
returning the size in **GB (10⁹ bytes)** with two common optimisations:

- **Grouped-query / multi-query attention**: only `num_kv_heads` of the `num_heads` heads store keys
  and values, so the cache is multiplied by `num_kv_heads / num_heads`.
- **Local windowed attention**: if `window > 0`, only the last `window` tokens are cached, so the
  effective sequence length is `min(seq_len, window)`. `window == 0` means full attention.

**Example (Llama 2 13B in the book):** `kv_cache_gb(32, 2048, 40, 5120, 2, 40, 40, 0)` → `53.6871`
(about 54 GB).

**Example:** the same model with 8 KV heads out of 40 and a 1,024-token window:
`kv_cache_gb(32, 2048, 40, 5120, 2, 40, 8, 1024)` → `5.3687`
""",
    starter='''def kv_cache_gb(batch, seq_len, layers, model_dim, bytes_per_value, num_heads, num_kv_heads, window):
    pass
''',
    solution='''def kv_cache_gb(batch, seq_len, layers, model_dim, bytes_per_value, num_heads, num_kv_heads, window):
    s = min(seq_len, window) if window > 0 else seq_len
    total = 2 * batch * s * layers * model_dim * bytes_per_value * num_kv_heads / num_heads
    return total / 1e9
''',
    tests=[
        [32, 2048, 40, 5120, 2, 40, 40, 0],
        [32, 2048, 40, 5120, 2, 40, 8, 1024],
        [1, 4096, 32, 4096, 2, 32, 32, 0],
        [1, 4096, 32, 4096, 2, 32, 8, 0],
        [8, 10000, 80, 8192, 2, 64, 8, 1000],
        [8, 500, 80, 8192, 2, 64, 8, 1000],
        [64, 8192, 32, 4096, 1, 32, 1, 0],
        [1, 1, 1, 1, 4, 1, 1, 0],
        [16, 128000, 126, 16384, 2, 128, 8, 0],
        [4, 2048, 24, 2048, 4, 16, 4, 2048],
    ],
    examples=2,
    wrong_solutions=[
        '''def kv_cache_gb(batch, seq_len, layers, model_dim, bytes_per_value, num_heads, num_kv_heads, window):
    s = min(seq_len, window) if window > 0 else seq_len
    return batch * s * layers * model_dim * bytes_per_value * num_kv_heads / num_heads / 1e9
''',
        '''def kv_cache_gb(batch, seq_len, layers, model_dim, bytes_per_value, num_heads, num_kv_heads, window):
    s = window if window > 0 else seq_len
    return 2 * batch * s * layers * model_dim * bytes_per_value * num_kv_heads / num_heads / 1e9
''',
    ],
    guide=dict(
        prereqs="Inference optimization lesson: KV cache, multi-query and grouped-query attention, windowed attention.",
        intuition="Every token leaves behind one key and one value vector in every layer, so the cache grows "
                  "linearly with batch, context and depth. Sharing K/V across heads or attending to a window "
                  "shrinks it proportionally.",
        hints=["The leading 2 is for keys AND values.", "The window only matters when it is smaller than the sequence.",
               "Scale by num_kv_heads / num_heads."],
        brute_force="Direct formula.",
        approach="effective S → 2·B·S·L·H·M → × kv_heads/heads → ÷ 1e9.",
        complexity="O(1).",
        pitfalls="- Forgetting the factor 2.\n- Using the window even when the sequence is shorter.\n- GiB vs GB.",
        follow_up="Given a GPU with X GB free after loading weights, compute the maximum batch size for a target context length.",
    ),
),
# ---------------------------------------------------------------- semantic cache
dict(
    id="aie-semantic-cache",
    title="Semantic Cache with Threshold and LRU Eviction",
    difficulty="Medium",
    pattern="AI Architecture",
    entry="run_semantic_cache",
    compare="float",
    description=r"""
A **semantic cache** reuses the answer of a previous query when a new query is similar enough.

`run_semantic_cache(queries, threshold, capacity)`: `queries` is a list of `[embedding, fresh_answer]`
processed in order, where `fresh_answer` is what the model would answer if it had to be called.

For each query:
1. Compute the cosine similarity between its embedding and every cached embedding (similarity with a
   zero-norm vector is `0`). Take the entry with the **highest** similarity (ties: the entry that was
   **inserted earliest**).
2. If that similarity is `>= threshold`: **hit**. Return the cached answer and mark the entry as most
   recently used.
3. Otherwise: **miss**. Return `fresh_answer` and insert `(embedding, fresh_answer)` as the most
   recently used entry. If the cache then holds more than `capacity` entries, evict the **least
   recently used** one. (`capacity >= 1`.)

Return `[answers, hit_rate]` with `hit_rate = hits / len(queries)` (`0.0` for no queries).

**Example:** `queries = [[[1,0],"Hanoi"], [[0.99,0.05],"Ha Noi"], [[0,1],"Paris"]]`, `threshold=0.95`,
`capacity=10` → `[["Hanoi", "Hanoi", "Paris"], 0.3333]`
""",
    starter='''import math

def run_semantic_cache(queries, threshold, capacity):
    pass
''',
    solution='''import math
def run_semantic_cache(queries, threshold, capacity):
    def cos(a, b):
        na = math.sqrt(sum(x * x for x in a)); nb = math.sqrt(sum(x * x for x in b))
        if na == 0 or nb == 0:
            return 0.0
        return sum(x * y for x, y in zip(a, b)) / (na * nb)
    entries = []   # each: [insert_id, last_used, emb, answer]
    clock = 0
    next_id = 0
    answers, hits = [], 0
    for emb, fresh in queries:
        clock += 1
        best, best_sim = None, None
        for e in sorted(entries, key=lambda e: e[0]):
            s = cos(emb, e[2])
            if best is None or s > best_sim:
                best, best_sim = e, s
        if best is not None and best_sim >= threshold:
            hits += 1
            best[1] = clock
            answers.append(best[3])
        else:
            answers.append(fresh)
            entries.append([next_id, clock, emb, fresh])
            next_id += 1
            if len(entries) > capacity:
                victim = min(entries, key=lambda e: e[1])
                entries.remove(victim)
    return [answers, hits / len(queries) if queries else 0.0]
''',
    tests=[
        [[[[1, 0], "Hanoi"], [[0.99, 0.05], "Ha Noi"], [[0, 1], "Paris"]], 0.95, 10],
        [[], 0.9, 3],
        [[[[1, 0], "a"], [[1, 0], "b"], [[1, 0], "c"]], 1.0, 1],
        [[[[1, 0], "a"], [[0, 1], "b"], [[1, 0], "c"], [[0, 1], "d"]], 0.9, 1],
        [[[[1, 0], "a"], [[0, 1], "b"], [[1, 0], "c"], [[1, 1], "d"], [[0, 1], "e"]], 0.9, 2],
        [[[[1, 0], "a"], [[0, 1], "b"], [[1, 1], "c"]], 0.7, 5],
        [[[[0, 0], "zero"], [[0, 0], "zero2"], [[1, 0], "one"]], 0.5, 5],
        [[[[1, 0], "a"], [[0, 1], "b"], [[-1, 0], "c"], [[1, 0.1], "d"], [[0.1, 1], "e"], [[-1, 0.1], "f"], [[0, -1], "g"], [[1, 0], "h"]], 0.98, 3],
        [_cache_stream, 0.97, 5],
        [_cache_stream, 0.9, 3],
        [_cache_stream, 0.999, 50],
        [[[[2, 0], "x"], [[5, 0], "y"]], 0.99, 2],
    ],
    examples=1,
    wrong_solutions=[
        # FIFO eviction instead of LRU, hits do not refresh
        '''import math
def run_semantic_cache(queries, threshold, capacity):
    def cos(a, b):
        na = math.sqrt(sum(x * x for x in a)); nb = math.sqrt(sum(x * x for x in b))
        return 0.0 if na == 0 or nb == 0 else sum(x * y for x, y in zip(a, b)) / (na * nb)
    entries, answers, hits = [], [], 0
    for emb, fresh in queries:
        best, bs = None, None
        for e in entries:
            s = cos(emb, e[0])
            if best is None or s > bs: best, bs = e, s
        if best is not None and bs >= threshold:
            hits += 1; answers.append(best[1])
        else:
            answers.append(fresh); entries.append((emb, fresh))
            if len(entries) > capacity: entries.pop(0)
    return [answers, hits / len(queries) if queries else 0.0]
''',
        # exact-match cache only
        '''def run_semantic_cache(queries, threshold, capacity):
    cache, answers, hits = {}, [], 0
    for emb, fresh in queries:
        k = tuple(emb)
        if k in cache: hits += 1; answers.append(cache[k])
        else: cache[k] = fresh; answers.append(fresh)
    return [answers, hits / len(queries) if queries else 0.0]
''',
    ],
    guide=dict(
        prereqs="Cosine similarity, LRU caches, the architecture lesson (exact vs semantic caching).",
        intuition="An exact cache only helps for identical queries. A semantic cache also serves paraphrases, at "
                  "the risk of serving a wrong answer if the threshold is too low. A bounded cache needs an "
                  "eviction policy, and LRU keeps the entries that are still being asked about.",
        hints=["Track a logical clock: set an entry's last-used time on insert and on hit.",
               "Find the best match first, then decide hit or miss.",
               "Evict the entry with the smallest last-used time after inserting."],
        brute_force="Scanning all cached embeddings per query is the straightforward approach: O(N·C·d).",
        approach="Maintain entries with (insert order, last used, embedding, answer). Per query: best similarity → "
                 "hit (refresh, return cached) or miss (return fresh, insert, maybe evict).",
        complexity="O(Q·C·d) for Q queries, capacity C and dimension d.",
        pitfalls="- Returning the fresh answer on a hit.\n- Not refreshing recency on hits.\n- Evicting before inserting.\n- Zero vectors.",
        follow_up="Per Huyen's warning, never cache user-specific answers. Add a 'cacheable' flag per query and measure how the hit rate changes.",
    ),
),
# ---------------------------------------------------------------- token bucket
dict(
    id="aie-token-bucket",
    title="Token Bucket for an LLM Gateway",
    difficulty="Medium",
    pattern="AI Architecture",
    kind="class",
    entry="TokenBucket",
    description=r"""
A model gateway enforces **rate limits** such as tokens per minute. Implement a token bucket.

```
TokenBucket(capacity, refill_rate)   # bucket starts FULL; refill_rate is tokens per second
allow(now, tokens) -> bool           # now is a timestamp in seconds, non-decreasing across calls
```

`allow` first refills: `level = min(capacity, level + (now - last_time) * refill_rate)` and sets
`last_time = now` (the first call refills from time `now`, i.e. adds nothing). Then:

- if `tokens <= level + 1e-9`: subtract `tokens` from the level and return `True`;
- otherwise return `False` and leave the level unchanged (the request is rejected, not queued).

A request larger than `capacity` can never be allowed.

**Example:**
```
b = TokenBucket(100, 10)
b.allow(0, 60)   -> True    (40 left)
b.allow(1, 60)   -> False   (50 available)
b.allow(2, 60)   -> True    (60 available -> 0 left)
b.allow(2, 1)    -> False
```
""",
    starter='''class TokenBucket:
    def __init__(self, capacity, refill_rate):
        pass

    def allow(self, now, tokens):
        pass
''',
    solution='''class TokenBucket:
    def __init__(self, capacity, refill_rate):
        self.capacity = capacity
        self.rate = refill_rate
        self.level = float(capacity)
        self.last = None

    def allow(self, now, tokens):
        if self.last is not None:
            self.level = min(self.capacity, self.level + (now - self.last) * self.rate)
        self.last = now
        if tokens <= self.level + 1e-9:
            self.level -= tokens
            return True
        return False
''',
    tests=[
        [["TokenBucket", "allow", "allow", "allow", "allow"], [[100, 10], [0, 60], [1, 60], [2, 60], [2, 1]]],
        [["TokenBucket", "allow", "allow"], [[10, 1], [5, 11], [1000, 11]]],
        [["TokenBucket", "allow", "allow", "allow"], [[10, 1], [0, 10], [100, 10], [100, 0]]],
        [["TokenBucket", "allow", "allow", "allow", "allow"], [[5, 0], [0, 3], [10, 3], [20, 2], [30, 1]]],
        [["TokenBucket", "allow", "allow", "allow", "allow", "allow"], [[1000, 100], [0, 1000], [0.5, 50], [0.5, 1], [5, 500], [5.1, 10]]],
        [["TokenBucket", "allow", "allow", "allow"], [[3, 0.1], [0, 3], [10, 1], [20, 2]]],
        [["TokenBucket"] + ["allow"] * 12, [[10, 2]] + [[i * 0.5, 2] for i in range(12)]],
        [_bucket_ops, _bucket_args],
        [["TokenBucket", "allow", "allow", "allow"], [[100, 10], [50, 100], [50, 1], [50.1, 1]]],
    ],
    examples=1,
    wrong_solutions=[
        # no capacity cap on refill
        '''class TokenBucket:
    def __init__(self, capacity, refill_rate):
        self.c, self.r, self.level, self.last = capacity, refill_rate, float(capacity), None
    def allow(self, now, tokens):
        if self.last is not None: self.level += (now - self.last) * self.r
        self.last = now
        if tokens <= self.level + 1e-9:
            self.level -= tokens; return True
        return False
''',
        # deducts even when rejecting (level can go negative)
        '''class TokenBucket:
    def __init__(self, capacity, refill_rate):
        self.c, self.r, self.level, self.last = capacity, refill_rate, float(capacity), None
    def allow(self, now, tokens):
        if self.last is not None: self.level = min(self.c, self.level + (now - self.last) * self.r)
        self.last = now
        ok = tokens <= self.level + 1e-9
        self.level -= tokens
        return ok
''',
    ],
    guide=dict(
        prereqs="The architecture lesson (model gateway: access control, rate limiting, cost management).",
        intuition="The bucket holds permission to spend tokens. It refills at a steady rate up to a cap, so "
                  "short bursts are allowed (up to capacity) while the long-run average is limited by the rate.",
        hints=["Refill lazily, only when a request arrives, using the elapsed time.",
               "Cap the level at capacity after refilling.",
               "Only deduct when the request is allowed."],
        brute_force="Simulating the refill tick by tick is slower and less accurate than the lazy formula.",
        approach="Store level and last timestamp. On each call: refill, cap, compare, deduct or reject.",
        complexity="O(1) per call.",
        pitfalls="- Unbounded refill after a long idle period.\n- Charging rejected requests.\n- Float comparison at the boundary (hence the 1e-9).",
        follow_up="Keep one bucket per API key and per model, and add fallback routing to another model when the primary bucket is empty.",
    ),
),
# ---------------------------------------------------------------- cost estimator
dict(
    id="aie-cost-estimator",
    title="LLM API Cost Estimator",
    difficulty="Easy",
    pattern="AI Architecture",
    entry="estimate_cost",
    compare="float",
    description=r"""
Model APIs charge per token, with different prices for input, **cached** input (prompt caching) and
output tokens. Build the cost report a gateway would log.

`estimate_cost(requests, prices)`:
- each request is a dict `{"model", "input_tokens", "cached_tokens", "output_tokens"}`;
  `cached_tokens` is the part of `input_tokens` that was read from the prompt cache
  (`0 <= cached_tokens <= input_tokens`);
- `prices[model]` is a dict `{"input", "cached_input", "output"}` in **dollars per 1,000,000 tokens**.

Cost of a request =
`((input_tokens - cached_tokens) × input + cached_tokens × cached_input + output_tokens × output) / 1e6`.

Requests whose model is not in `prices` are not charged but are counted.

Return a dict:
- `"total"`: total cost;
- `"by_model"`: `{model: cost}` for every priced model that appears in the requests;
- `"unpriced"`: number of requests with an unknown model;
- `"most_expensive"`: the model with the highest cost (ties: alphabetically first), or `None` if
  `by_model` is empty.

**Example:** one request with 1,000,000 input tokens (900,000 cached) and 100,000 output tokens, prices
`{"input": 3, "cached_input": 0.3, "output": 15}` → `0.1×3 + 0.9×0.3 + 0.1×15 = 2.07`.
""",
    starter='''def estimate_cost(requests, prices):
    pass
''',
    solution='''def estimate_cost(requests, prices):
    by_model, unpriced = {}, 0
    for r in requests:
        m = r["model"]
        if m not in prices:
            unpriced += 1
            continue
        p = prices[m]
        cost = ((r["input_tokens"] - r["cached_tokens"]) * p["input"]
                + r["cached_tokens"] * p["cached_input"]
                + r["output_tokens"] * p["output"]) / 1e6
        by_model[m] = by_model.get(m, 0.0) + cost
    top = min(by_model, key=lambda m: (-by_model[m], m)) if by_model else None
    return {"total": sum(by_model.values()), "by_model": by_model, "unpriced": unpriced, "most_expensive": top}
''',
    tests=[
        [[{"model": "big", "input_tokens": 1000000, "cached_tokens": 900000, "output_tokens": 100000}],
         {"big": {"input": 3, "cached_input": 0.3, "output": 15}}],
        [[], {"big": {"input": 3, "cached_input": 0.3, "output": 15}}],
        [[{"model": "mystery", "input_tokens": 10, "cached_tokens": 0, "output_tokens": 10}], {}],
        [[{"model": "small", "input_tokens": 1200, "cached_tokens": 0, "output_tokens": 300},
          {"model": "big", "input_tokens": 1200, "cached_tokens": 1000, "output_tokens": 300},
          {"model": "small", "input_tokens": 500, "cached_tokens": 500, "output_tokens": 0}],
         {"small": {"input": 0.15, "cached_input": 0.075, "output": 0.6}, "big": {"input": 3, "cached_input": 0.3, "output": 15}}],
        [[{"model": "b", "input_tokens": 1000, "cached_tokens": 0, "output_tokens": 0},
          {"model": "a", "input_tokens": 1000, "cached_tokens": 0, "output_tokens": 0}],
         {"a": {"input": 1, "cached_input": 1, "output": 1}, "b": {"input": 1, "cached_input": 1, "output": 1}}],
        [[{"model": "a", "input_tokens": 0, "cached_tokens": 0, "output_tokens": 0}],
         {"a": {"input": 1, "cached_input": 1, "output": 1}}],
        [[{"model": _g.choice(["small", "big", "local", "old"]), "input_tokens": (i := _g.randint(100, 20000)),
           "cached_tokens": _g.randint(0, i), "output_tokens": _g.randint(0, 4000)} for _ in range(300)],
         {"small": {"input": 0.15, "cached_input": 0.075, "output": 0.6}, "big": {"input": 3, "cached_input": 0.3, "output": 15},
          "local": {"input": 0, "cached_input": 0, "output": 0}}],
        [[{"model": "x", "input_tokens": 1000, "cached_tokens": 1000, "output_tokens": 200000}] * 1000,
         {"x": {"input": 2.5, "cached_input": 1.25, "output": 10}}],
        [[{"model": "big", "input_tokens": 1000, "cached_tokens": 0, "output_tokens": 0},
          {"model": "nope", "input_tokens": 5, "cached_tokens": 0, "output_tokens": 5},
          {"model": "nope2", "input_tokens": 5, "cached_tokens": 0, "output_tokens": 5}],
         {"big": {"input": 3, "cached_input": 0.3, "output": 15}}],
    ],
    examples=1,
    wrong_solutions=[
        # charges cached tokens twice (full input price + cached price)
        '''def estimate_cost(requests, prices):
    by, un = {}, 0
    for r in requests:
        m = r["model"]
        if m not in prices: un += 1; continue
        p = prices[m]
        c = (r["input_tokens"] * p["input"] + r["cached_tokens"] * p["cached_input"] + r["output_tokens"] * p["output"]) / 1e6
        by[m] = by.get(m, 0.0) + c
    top = min(by, key=lambda m: (-by[m], m)) if by else None
    return {"total": sum(by.values()), "by_model": by, "unpriced": un, "most_expensive": top}
''',
        # same price for input and output
        '''def estimate_cost(requests, prices):
    by, un = {}, 0
    for r in requests:
        m = r["model"]
        if m not in prices: un += 1; continue
        p = prices[m]
        c = ((r["input_tokens"] - r["cached_tokens"]) * p["input"] + r["cached_tokens"] * p["cached_input"] + r["output_tokens"] * p["input"]) / 1e6
        by[m] = by.get(m, 0.0) + c
    top = min(by, key=lambda m: (-by[m], m)) if by else None
    return {"total": sum(by.values()), "by_model": by, "unpriced": un, "most_expensive": top}
''',
    ],
    guide=dict(
        prereqs="Inference metrics and prompt caching lessons; the gateway section (cost management).",
        intuition="Output tokens usually cost several times more than input tokens, and cached input tokens "
                  "cost a fraction of normal input. A cost report must split tokens into those three groups.",
        hints=["Uncached input = input_tokens - cached_tokens.", "Prices are per million tokens.",
               "Accumulate per model in a dict; pick the max with a (−cost, name) key."],
        brute_force="A single pass is already optimal.",
        approach="Loop over requests, skip unknown models (count them), compute the cost, accumulate, summarise.",
        complexity="O(n).",
        pitfalls="- Double-charging cached tokens.\n- Forgetting the 1e6 divisor.\n- Tie-breaking for the most expensive model.",
        follow_up="Add a budget per team and return which teams exceeded it, or compute the saving attributable to caching.",
    ),
),
]
