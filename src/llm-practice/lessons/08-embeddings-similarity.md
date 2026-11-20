# Embeddings and similarity: from sentence-transformers to Matryoshka

Retrieval-augmented generation, semantic search, clustering, deduplication, recommendation and
"memory" for agents all rest on one primitive: map a piece of text to a vector such that **similar
meaning means nearby vectors**, then find neighbours fast. This lesson covers the first half (the
vectors and the metrics); the next covers fast neighbour search.

## 1. From token states to a sentence vector

A transformer produces one hidden vector per token. A **sentence embedding** needs one vector per
text. Options:

- **CLS pooling**: take the hidden state of a special first token (BERT-style).
- **Mean pooling**: average the token states, excluding padding (the default in many
  sentence-transformers models).
- **Last-token pooling**: for decoder-based embedders (e.g. Qwen3-Embedding, E5-Mistral), the last
  token has seen the whole text through causal attention.

But a raw pretrained model's pooled states are poor embeddings. Good embedders are **fine-tuned with
contrastive learning**: pull an anchor towards a positive (a paraphrase, the answer to a query) and
away from negatives. The standard loss is InfoNCE with **in-batch negatives**:

$$
\mathcal{L} = -\log \frac{\exp(\text{sim}(q, d^+)/\tau)}{\sum_{j} \exp(\text{sim}(q, d_j)/\tau)}
$$

where the sum runs over the positive and every other document in the batch. Larger batches mean more
negatives and better embeddings; **hard negatives** (similar-looking but wrong documents) help most.
In sentence-transformers this is `MultipleNegativesRankingLoss`.

```python-run
import numpy as np
rng = np.random.default_rng(0)
B, d, tau = 4, 8, 0.05
q = rng.standard_normal((B, d)); q /= np.linalg.norm(q, axis=1, keepdims=True)
docs = q + 0.3 * rng.standard_normal((B, d))      # positives: noisy copies of queries
docs /= np.linalg.norm(docs, axis=1, keepdims=True)
S = q @ docs.T / tau                              # (B, B) similarity matrix; diagonal = positives
logp = S - S.max(1, keepdims=True); logp -= np.log(np.exp(logp).sum(1, keepdims=True))
print("InfoNCE loss:", round(float(-np.diag(logp).mean()), 4))
print("argmax per row (should be 0..3):", S.argmax(1))
```

## 2. Using sentence-transformers

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("BAAI/bge-small-en-v1.5")      # or all-MiniLM-L6-v2, Qwen/Qwen3-Embedding-0.6B
docs = ["The KV cache stores keys and values.", "LoRA adds low-rank adapters.", "Paris is in France."]
D = model.encode(docs, normalize_embeddings=True, batch_size=64)
q = model.encode("How do adapters reduce trainable parameters?", normalize_embeddings=True)
scores = model.similarity(q, D)                              # cosine by default
print(scores)
```

Things that matter in practice:

- **Query/document prefixes.** Many models are trained asymmetrically and expect instructions such as
  `"query: "` / `"passage: "` (E5) or `"Represent this sentence for searching relevant passages: "`
  (BGE), or `prompt_name="query"` in sentence-transformers. Forgetting them costs several points of
  recall.
- **Max sequence length.** Many small embedders truncate at 256 or 512 tokens; text beyond that is
  silently ignored. This interacts with chunk size (module 5).
- **Choosing a model.** Start from the MTEB leaderboard filtered to your language and task (retrieval
  vs classification vs clustering), then evaluate on *your* queries. Consider dimension (storage),
  latency, license, multilingual support and context length. API embedders (OpenAI
  `text-embedding-3`, Voyage, Cohere) trade control for convenience.
- **Never mix models.** Vectors from different models (or versions) live in different spaces. Changing
  the embedder means re-embedding the whole corpus, so store the model id with each vector.

## 3. Similarity metrics

For vectors $a, b \in \mathbb{R}^d$:

$$
\text{cos}(a, b) = \frac{a \cdot b}{\|a\|\,\|b\|},\qquad
\text{dot}(a, b) = a \cdot b,\qquad
\|a - b\|_2^2 = \|a\|^2 + \|b\|^2 - 2\,a \cdot b
$$

If all vectors are **L2-normalised**, the three are equivalent for ranking:
$\|a - b\|^2 = 2 - 2\cos(a, b)$. That is why most systems normalise once at ingestion and then use the
fastest operation, the dot product (inner product, "IP" in FAISS).

When they differ: a model trained with an unnormalised dot product (some retrieval models) encodes
useful information such as "how generic is this document" in the vector's norm; normalising throws it
away. Use the metric the model card specifies.

```python-run
import numpy as np
rng = np.random.default_rng(1)
D = rng.standard_normal((8, 4)) * np.array([[0.2], [5], [0.3], [4], [1], [0.5], [3], [0.1]])   # very different norms
q = rng.standard_normal(4)

cos = D @ q / (np.linalg.norm(D, axis=1) * np.linalg.norm(q))
dot = D @ q
l2 = np.linalg.norm(D - q, axis=1)
print("rank by cosine:", np.argsort(-cos))
print("rank by dot   :", np.argsort(-dot))     # can differ: favours long vectors
print("rank by L2    :", np.argsort(l2))
Dn = D / np.linalg.norm(D, axis=1, keepdims=True); qn = q / np.linalg.norm(q)
print("after normalising, dot == cos ranking:", np.array_equal(np.argsort(-(Dn @ qn)), np.argsort(-cos)))
print("and L2 agrees too:", np.array_equal(np.argsort(np.linalg.norm(Dn - qn, axis=1)), np.argsort(-cos)))
```

### Exact top-k search

Exact search (also "brute force" or "flat") is one matrix-vector product plus a partial sort. With
`np.argpartition` the selection is $O(N)$ rather than $O(N \log N)$:

```python-run
import numpy as np
rng = np.random.default_rng(2)
N, d, k = 100_000, 64, 5
D = rng.standard_normal((N, d)).astype(np.float32)
D /= np.linalg.norm(D, axis=1, keepdims=True)
q = D[123] + 0.05 * rng.standard_normal(d).astype(np.float32); q /= np.linalg.norm(q)

scores = D @ q                                      # (N,)
idx = np.argpartition(-scores, k)[:k]               # unordered top-k in O(N)
idx = idx[np.argsort(-scores[idx])]                 # order just those k
print("top-k ids:", idx, " scores:", np.round(scores[idx], 3))
```

Exact search over 100k vectors takes milliseconds. Brute force is a legitimate production choice up to
around a million vectors (and is what FAISS `IndexFlatIP` does, highly optimised). ANN indexes matter
when $N$ is tens of millions or latency budgets are tight.

## 4. Dense, sparse and late interaction

| type | representation | strengths | examples |
|---|---|---|---|
| dense bi-encoder | one vector per text | semantic match, paraphrases, cross-lingual | BGE, E5, GTE, Qwen3-Embedding |
| sparse lexical | term weights over the vocabulary | exact terms, IDs, rare words, explainable | BM25, SPLADE |
| late interaction | one vector **per token**, MaxSim scoring | fine-grained matching, robust out of domain | ColBERT, ColPali (images of pages) |

Late interaction scores a query-document pair as $\sum_{i \in q} \max_{j \in d} q_i \cdot d_j$: each
query token finds its best-matching document token. It is more accurate than single-vector retrieval
but stores far more vectors. Module 5 combines dense and sparse retrieval with rank fusion.

## 5. Shrinking embeddings: Matryoshka and quantisation

Storage is $N \times d \times$ bytes. 100M documents at 1024 float32 dims is about 400 GB.

- **Matryoshka Representation Learning (MRL)** trains the model so that the *first* $m$ dimensions
  are themselves a good embedding. You can truncate 1024 to 256 dims (re-normalise!) and lose only a
  little quality. OpenAI's `dimensions` parameter and many open models support this.
- **Scalar quantisation** (float32 to int8): 4x smaller, tiny quality loss.
- **Binary quantisation** (sign bit per dimension): 32x smaller, search with Hamming distance, then
  **rescore** the top candidates with full-precision vectors to recover most of the quality.

```python-run
import numpy as np
rng = np.random.default_rng(3)
N, d = 20000, 256
C = rng.standard_normal((400, d))                     # clustered, like real embeddings
D = C[rng.integers(0, 400, N)] + 0.6 * rng.standard_normal((N, d))
D /= np.linalg.norm(D, axis=1, keepdims=True)
queries = D[:50] + (0.8 / np.sqrt(d)) * rng.standard_normal((50, d))
true_top = [set(np.argsort(-(D @ q))[:10]) for q in queries]

bits = D > 0                                         # binary codes
def recall(cands):
    return np.mean([len(set(c) & t) / 10 for c, t in zip(cands, true_top)])
ham = [np.argsort((bits != (q > 0)).sum(1))[:10] for q in queries]
resc = []
for q in queries:
    c = np.argsort((bits != (q > 0)).sum(1))[:100]   # 10x oversample with Hamming
    resc.append(c[np.argsort(-(D[c] @ q))[:10]])     # rescore with float vectors
print("binary-only recall@10:", round(recall(ham), 3))
print("binary + rescore recall@10:", round(recall(resc), 3))
```

## 6. Pitfalls

- Mixing normalised and unnormalised vectors in one index.
- Comparing similarity scores across models ("0.8 means relevant") instead of calibrating thresholds
  on labelled data. Cosine values are model-specific and often compressed into a narrow band.
- Embedding very long documents into one vector: the vector becomes a blurry average. Chunk first.
- Forgetting the query instruction prefix for asymmetric models.
- Evaluating embedders on public benchmarks only. Build a small labelled set of your own queries and
  measure recall@k (module 5).

## 7. Worked example: pooling with a padding mask

The most common implementation bug in hand-rolled embedding code is averaging over padding. Here are
token states for a batch of two sentences, the second padded from two tokens to four:

```python-run
import numpy as np
rng = np.random.default_rng(0)
h = rng.standard_normal((2, 4, 3))            # (batch, tokens, hidden)
mask = np.array([[1, 1, 1, 1],
                 [1, 1, 0, 0]])               # sentence 2 has two real tokens
h[1, 2:] = 9.0                                # padding positions hold arbitrary junk

wrong = h.mean(axis=1)
m = mask[:, :, None]
right = (h * m).sum(axis=1) / m.sum(axis=1)   # sum real tokens, divide by their count
last = h[np.arange(2), mask.sum(1) - 1]       # last-token pooling: index of the final real token
np.set_printoptions(precision=3, suppress=True)
print("naive mean, sentence 2 :", wrong[1])
print("masked mean, sentence 2:", right[1])
print("check                  :", h[1, :2].mean(axis=0))
print("last real token        :", last[1], "== h[1, 1]:", np.allclose(last[1], h[1, 1]))
```

The naive mean is dominated by the junk at padded positions. Worse, with real models the bug is
*silent*: embeddings still look plausible, but a sentence's vector changes depending on what else was in
its batch, so retrieval quality degrades in a way that is hard to trace. A good regression test: embed a
sentence alone and inside a batch with a much longer sentence, and assert the two vectors match.

Last-token pooling has its own trap: it needs **right** padding (or an explicit index as above); with
left padding the last position is always a real token, with right padding the last position is padding.

## 8. Measuring an embedding model on your own data

Leaderboard rank is a starting point, not a decision. The experiment that matters takes an afternoon:
collect 50 to 200 real queries, label the passage(s) that answer each, and compute recall@k for every
candidate model. The demo simulates two embedders of different quality to show the harness.

```python-run
import numpy as np
rng = np.random.default_rng(1)
n_docs, n_q, d = 2000, 150, 64
truth = rng.standard_normal((n_docs, d))                  # "true meaning" of each document
gold = rng.integers(0, n_docs, n_q)                       # the relevant document for each query

def embedder(noise):                                      # a weaker model = noisier view of the meaning
    D = truth + noise * rng.standard_normal((n_docs, d))
    Q = truth[gold] + noise * 1.5 * rng.standard_normal((n_q, d))   # queries are short and vaguer
    norm = lambda M: M / np.linalg.norm(M, axis=1, keepdims=True)
    return norm(Q), norm(D)

def evaluate(Q, D, ks=(1, 5, 20)):
    ranks = np.argsort(-(Q @ D.T), axis=1)
    pos = np.array([int(np.where(ranks[i] == gold[i])[0][0]) + 1 for i in range(n_q)])
    return {f"recall@{k}": round(float((pos <= k).mean()), 3) for k in ks} | {"MRR": round(float((1 / pos).mean()), 3)}

for name, noise in [("model A (strong)", 0.8), ("model B (weak)  ", 1.15)]:
    print(name, evaluate(*embedder(noise)))
```

Things to vary in the real version of this harness, one at a time: the model, the query prefix, the
chunk size, Matryoshka truncation, and quantisation. Report recall at the depth you actually pass to the
reranker, and keep the per-query results so you can read the failures.

## 9. Similarity thresholds are model-specific

"Return results with cosine above 0.8" is a frequent requirement and a frequent mistake. Different models
squeeze scores into very different ranges: for some, unrelated texts already score 0.6 and near
duplicates 0.9; for others the same pairs score 0.1 and 0.7. A threshold must be **calibrated per model**
on labelled pairs, choosing the operating point from a precision-recall trade-off:

```python-run
import numpy as np
rng = np.random.default_rng(2)
pos = np.clip(rng.normal(0.78, 0.07, 500), 0, 1)          # cosine of truly relevant pairs for this model
neg = np.clip(rng.normal(0.62, 0.06, 5000), 0, 1)         # cosine of irrelevant pairs: high baseline!
print("threshold  precision  recall")
for th in [0.60, 0.70, 0.75, 0.80, 0.85]:
    tp, fp = (pos >= th).sum(), (neg >= th).sum()
    print(f"  {th:.2f}      {tp / max(tp + fp, 1):.3f}     {tp / len(pos):.3f}")
```

With this model, 0.80 keeps under half of the relevant pairs, while 0.70 lets in a flood of irrelevant
ones because negatives are ten times more common. In retrieval pipelines it is usually better to take a
fixed top-k and let a reranker (whose scores are designed to be thresholded) decide what is relevant.

## 10. Hard negatives in one paragraph

Random negatives are too easy: after a few steps the model separates "parental leave policy" from
"GPU memory" and learns nothing more. **Hard negatives** are passages that look relevant but are not,
for example the top BM25 or dense hits for a query that are not labelled positive. Mining them with the
current model, filtering out likely false negatives (unlabelled passages that actually answer the
query, typically by dropping candidates that score above the positive), and retraining is the standard
recipe behind strong retrievers and is supported directly by `sentence_transformers.util.mine_hard_negatives`.
When you fine-tune an embedder on your own domain, a few thousand (query, positive, hard negative)
triples usually give a larger gain than switching to a bigger general-purpose model.

> [!INTERVIEW]
> **"Cosine vs dot product vs Euclidean?"** For L2-normalised vectors they produce identical rankings
> because $\|a-b\|^2 = 2 - 2\cos$. Use dot product on normalised vectors for speed; use raw dot
> product only when the model was trained that way, since the norm then carries signal. Mention
> in-batch negatives and hard negatives for training, MRL and binary quantisation with rescoring for
> scale.

## Summary

- Sentence embeddings come from pooled token states fine-tuned contrastively (InfoNCE, in-batch and hard
  negatives).
- Use the model's prescribed prefixes, metric and max length; never mix embedding models in one index.
- Normalise and use dot product: cosine, dot and L2 rankings then coincide.
- Exact search is fine to about a million vectors; beyond that use ANN (next lesson).
- MRL truncation and int8/binary quantisation (with rescoring) shrink storage dramatically.

```quiz
[
  {"q": "For L2-normalised vectors, how is squared Euclidean distance related to cosine similarity?",
   "options": ["||a-b||^2 = 2 - 2 cos(a,b)", "||a-b||^2 = cos(a,b)", "||a-b||^2 = 1 - cos(a,b)^2", "They are unrelated"], "answer": 0,
   "explain": "Expand ||a||^2 + ||b||^2 - 2ab with unit norms; the rankings are therefore identical."},
  {"q": "What are in-batch negatives in contrastive embedding training?",
   "options": ["The other examples' positives in the same batch, used as negatives", "Randomly generated vectors", "Documents with negative labels", "Padding tokens"], "answer": 0,
   "explain": "Each query's positive is every other query's negative, giving B-1 free negatives per example."},
  {"q": "You swap the embedding model for a better one. What must you do?",
   "options": ["Re-embed the entire corpus", "Nothing", "Only re-embed new documents", "Retrain the LLM"], "answer": 0,
   "explain": "Different models produce incompatible vector spaces."},
  {"q": "What does Matryoshka Representation Learning enable?",
   "options": ["Truncating embeddings to fewer leading dimensions with small quality loss", "Multilingual embeddings", "Binary codes", "Token-level vectors"], "answer": 0,
   "explain": "MRL trains nested prefixes of the vector to be useful embeddings on their own."},
  {"q": "Binary quantisation of embeddings is usually combined with...",
   "options": ["Oversampling candidates then rescoring with full-precision vectors", "Larger chunk sizes", "Higher temperature", "Removing normalisation"], "answer": 0,
   "explain": "Hamming search is cheap but approximate; rescoring the top candidates restores most of the recall."},
  {"q": "How does ColBERT score a query against a document?",
   "options": ["Sum over query tokens of the max similarity to any document token", "Cosine of mean-pooled vectors", "BM25", "A cross-encoder forward pass"], "answer": 0,
   "explain": "Late interaction (MaxSim) keeps per-token vectors and matches each query token to its best document token."},
  {"q": "Why is np.argpartition useful for exact top-k?",
   "options": ["It selects the k best in O(N) without fully sorting", "It normalises vectors", "It builds an HNSW graph", "It is required for cosine"], "answer": 0,
   "explain": "Only the k winners then need sorting, which is O(k log k)."}
]
```

> **Source:** Sentence Transformers docs (https://sbert.net), including training losses and embedding
> quantization; Hugging Face blog "Matryoshka embeddings" and "Embedding quantization"; MTEB leaderboard
> (https://huggingface.co/spaces/mteb/leaderboard); Khattab & Zaharia 2020 (ColBERT); Huyen, *AI
> Engineering*, ch. 6 "RAG and Agents" (embedding-based retrieval) and ch. 3 (embeddings).
