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
