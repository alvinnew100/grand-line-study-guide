# Embeddings and similarity: from sentence-transformers to Matryoshka

> **Before this lesson:** you should know what a vector, a dot product, an embedding, softmax and
> temperature are; all are taught in
> [From embeddings to scaled dot-product attention](#/lesson/llm-practice/attention-from-scratch).
> The hidden states a model outputs, mean pooling and the attention mask are shown in code in
> [Hub, pipelines, Auto classes and generate()](#/lesson/llm-practice/hub-pipelines-generate).
> The demos use numpy only.

## In plain words

An **embedding model** reads a piece of text and returns a list of numbers (a vector) that captures
its meaning. Texts that mean similar things get vectors that point in similar directions, even when
they share no words: "How do I reset my password?" and "I forgot my login" land close together.
Once text is turned into vectors, "find documents about this question" becomes "find the nearest
points", which a computer does very quickly.

Think of a huge library where books are shelved by topic instead of by title. Walk to the spot for
"gardening in dry climates" and every useful book is within arm's reach, whatever words its title
uses. An embedding model is the librarian who decides where each book goes; similarity search is
walking to the right spot and looking around.

Why it matters for a job: this is the engine under **RAG** (retrieval-augmented generation, where a
model looks up documents before answering; module 5), semantic search, recommendation, clustering,
duplicate detection and "memory" for agents. Interviewers routinely ask about cosine versus dot
product, how embedders are trained, and how to cut the storage bill for a hundred million vectors.

## Why vectors?

Retrieval-augmented generation, **semantic search** (search by meaning rather than exact words),
**clustering** (grouping similar items), **deduplication** (finding near-copies), recommendation and
"memory" for agents all rest on one primitive: map a piece of text to a vector such that **similar
meaning means nearby vectors**, then find the **nearest neighbours** (the stored vectors closest to a
query vector) fast. This lesson covers the first half (the vectors and the ways of measuring
closeness); the next covers fast neighbour search.

## 1. From token states to a sentence vector

A transformer produces one hidden vector per token (lesson 1 calls these contextual embeddings or
hidden states). A **sentence embedding** needs one vector per text, so the token vectors must be
combined, a step called **pooling**. Options:

- **CLS pooling**: take the hidden state of a special first token (BERT-style). BERT puts a `[CLS]`
  token at the start of every input and is trained so that this position summarises the text.
- **Mean pooling**: average the token states, excluding padding (the default in many
  sentence-transformers models).
- **Last-token pooling**: for decoder-based embedders (e.g. Qwen3-Embedding, E5-Mistral), the last
  token has seen the whole text through causal attention, so its state already summarises
  everything before it.

But a raw pretrained model's pooled states are poor embeddings: the model was trained to predict
words, not to place similar meanings close together. Good embedders are **fine-tuned with
contrastive learning**, which trains by comparison. Each training example has an **anchor** (for
example a search query), a **positive** (a text that should be close to it: a paraphrase, or the
passage that answers the query) and one or more **negatives** (texts that should be far away). The
loss rewards the model for pulling the anchor towards its positive and pushing it away from the
negatives.

The standard loss is called **InfoNCE** (from "noise-contrastive estimation"), used with **in-batch
negatives**: in a batch of $B$ query-positive pairs, each query's negatives are the other $B - 1$
queries' positives, so no extra negatives need to be collected. In symbols, with $q$ the query,
$d^+$ its positive, $d_j$ every document in the batch and $\tau$ a temperature:

$$
\mathcal{L} = -\log \frac{\exp(\text{sim}(q, d^+)/\tau)}{\sum_{j} \exp(\text{sim}(q, d_j)/\tau)}
$$

where the sum runs over the positive and every other document in the batch. Read it as a
classification problem: "out of all $B$ documents in the batch, which one belongs to this query?" The
fraction is the softmax probability given to the right answer, and the loss is small when that
probability is close to 1. Larger batches mean more negatives and better embeddings; **hard
negatives** (similar-looking but wrong documents) help most. In sentence-transformers this is
`MultipleNegativesRankingLoss`.

The demo below builds four queries and four positives, computes the loss and checks that each query's
best match is its own positive:

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

**Reading this code line by line**

- `q` holds four random query vectors of length 8. `q /= np.linalg.norm(q, axis=1, keepdims=True)`
  divides each row by its length, so every vector has length 1 (this is called normalising; section
  3 explains why).
- `docs = q + 0.3 * ...` makes each positive a slightly noisy copy of its query, then normalises it.
- `S = q @ docs.T / tau` is the 4 x 4 grid of dot products divided by the temperature 0.05. Row $i$
  compares query $i$ with every document, and the diagonal holds the query-positive pairs.
- The next line is a numerically stable **log-softmax** of each row (the max-subtraction trick from
  lesson 1, then subtracting the log of the row total).
- `-np.diag(logp).mean()` averages minus the log-probability of the right document, which is exactly
  the InfoNCE formula. The printed loss is tiny (about `0.0015`) because each positive is very close
  to its query, and `argmax per row` prints `[0 1 2 3]`: every query ranks its own positive first.

## 2. Using sentence-transformers

**sentence-transformers** is the standard Python library for embedding models. It handles
tokenization, pooling and normalisation for you:

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("BAAI/bge-small-en-v1.5")      # or all-MiniLM-L6-v2, Qwen/Qwen3-Embedding-0.6B
docs = ["The KV cache stores keys and values.", "LoRA adds low-rank adapters.", "Paris is in France."]
D = model.encode(docs, normalize_embeddings=True, batch_size=64)
q = model.encode("How do adapters reduce trainable parameters?", normalize_embeddings=True)
scores = model.similarity(q, D)                              # cosine by default
print(scores)
```

Line by line: `SentenceTransformer(name)` downloads an embedding model. `model.encode(docs, ...)`
turns the three sentences into a matrix with one row per sentence; `normalize_embeddings=True` makes
every row length 1, and `batch_size=64` controls how many texts go through the model at once. The
query is encoded the same way. `model.similarity(q, D)` returns a 1 x 3 grid of cosine scores, and
the LoRA sentence should score highest because it is about adapters, even though the query never uses
the word "LoRA".

Things that matter in practice:

- **Query/document prefixes.** Many models are trained **asymmetrically**: queries (short questions)
  and documents (long passages) are marked differently during training, so the model expects
  instructions such as `"query: "` / `"passage: "` (E5) or
  `"Represent this sentence for searching relevant passages: "` (BGE), or `prompt_name="query"` in
  sentence-transformers. Forgetting them costs several points of **recall** (the share of the truly
  relevant documents that the search actually returns).
- **Max sequence length.** Many small embedders truncate at 256 or 512 tokens; text beyond that is
  silently ignored. This interacts with chunk size (module 5).
- **Choosing a model.** Start from the **MTEB** leaderboard (Massive Text Embedding Benchmark, a
  public scoreboard of embedders on dozens of tasks) filtered to your language and task (retrieval
  vs classification vs clustering), then evaluate on *your* queries. Consider dimension (storage),
  latency, license, multilingual support and context length. API embedders (OpenAI
  `text-embedding-3`, Voyage, Cohere) trade control for convenience.
- **Never mix models.** Vectors from different models (or versions) live in different spaces. Changing
  the embedder means re-embedding the whole corpus, so store the model id with each vector.

## 3. Similarity metrics

A **similarity metric** is the formula that turns two vectors into one closeness score. Three are
common. The **norm** (or length) of a vector, written $\|a\|$, is the square root of the sum of its
squared entries, the ordinary straight-line length. **Cosine similarity** divides the dot product by
both lengths, so it measures only the angle between the vectors: 1 for the same direction, 0 for
unrelated, -1 for opposite. The **dot product** keeps the lengths in. **Euclidean (L2) distance** is
the straight-line distance between the two points; here it is written squared. For vectors
$a, b \in \mathbb{R}^d$:

$$
\text{cos}(a, b) = \frac{a \cdot b}{\|a\|\,\|b\|},\qquad
\text{dot}(a, b) = a \cdot b,\qquad
\|a - b\|_2^2 = \|a\|^2 + \|b\|^2 - 2\,a \cdot b
$$

If all vectors are **L2-normalised** (divided by their norm so each has length 1), the three are
equivalent for ranking: $\|a - b\|^2 = 2 - 2\cos(a, b)$. To see why, put $\|a\| = \|b\| = 1$ into the
third formula: it becomes $1 + 1 - 2\,a \cdot b$, and for unit vectors $a \cdot b$ *is* the cosine.
A bigger cosine therefore always means a smaller distance. That is why most systems normalise once at
**ingestion** (when documents are added) and then use the fastest operation, the dot product (also
called the **inner product**, "IP" in **FAISS**, Meta's widely used library for vector search).

When they differ: a model trained with an unnormalised dot product (some retrieval models) encodes
useful information such as "how generic is this document" in the vector's norm; normalising throws it
away. Use the metric the model card specifies.

The demo gives eight document vectors wildly different lengths and ranks them against one query with
each metric:

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

The multiplication by `np.array([[0.2], [5], ...])` stretches each row by a different factor, so some
vectors are 50 times longer than others. `np.argsort(-cos)` lists document numbers from most to least
similar (the minus sign turns ascending order into descending). The three printed rankings disagree:
cosine puts document 2 first, dot product puts document 1 (one of the long vectors) first, and L2
also differs. After normalising every vector to length 1, the last two lines print `True`: dot
product, cosine and L2 now give the same order.

### Exact top-k search

**Top-k search** returns the $k$ stored vectors most similar to a query. **Exact** search (also
"brute force" or "flat") compares the query with every stored vector: one matrix-vector product plus
a partial sort. The notation $O(N)$ ("order N") means the work grows in proportion to the number of
vectors $N$; a full sort costs $O(N \log N)$, a little more. With `np.argpartition` the selection is
$O(N)$:

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

The demo stores 100,000 random unit vectors as `float32` (4 bytes per number), then builds a query
that is a slightly noisy copy of vector 123. `D @ q` scores all 100,000 vectors in one operation.
`np.argpartition(-scores, k)[:k]` moves the five best scores to the front without sorting the rest,
and the next line sorts only those five. The output lists vector 123 first with a score of about
0.92, followed by four unrelated vectors at about 0.48.

Exact search over 100k vectors takes milliseconds. Brute force is a legitimate production choice up to
around a million vectors (and is what FAISS `IndexFlatIP` does, highly optimised). **ANN**
(approximate nearest neighbour) indexes, the subject of the next lesson, matter when $N$ is tens of
millions or latency budgets are tight.

## 4. Dense, sparse and late interaction

Embeddings come in three families. A **dense** vector has a few hundred to a few thousand entries,
almost all non-zero, and each entry has no meaning on its own. A **sparse** vector has one entry per
vocabulary word, almost all zero, with weights on the words that appear (or, for learned sparse
models, on related words too). A **bi-encoder** encodes the query and the document separately, which
is what allows documents to be embedded once in advance. **BM25** is the classic keyword-scoring
formula used by search engines (lesson 11 builds it).

| type | representation | strengths | examples |
|---|---|---|---|
| dense bi-encoder | one vector per text | semantic match, paraphrases, cross-lingual | BGE, E5, GTE, Qwen3-Embedding |
| sparse lexical | term weights over the vocabulary | exact terms, IDs, rare words, explainable | BM25, SPLADE |
| late interaction | one vector **per token**, MaxSim scoring | fine-grained matching, robust out of domain | ColBERT, ColPali (images of pages) |

Late interaction scores a query-document pair as $\sum_{i \in q} \max_{j \in d} q_i \cdot d_j$: each
query token finds its best-matching document token (the "max", hence the name **MaxSim**), and those
best matches are added up. It is more accurate than single-vector retrieval but stores far more
vectors, one per token instead of one per document. Module 5 combines dense and sparse retrieval with
rank fusion.

## 5. Shrinking embeddings: Matryoshka and quantisation

Storage is $N \times d \times$ bytes. 100M documents at 1024 float32 dims is
$10^8 \times 1024 \times 4$ bytes, about 400 GB. Three techniques shrink it:

- **Matryoshka Representation Learning (MRL)**, named after Russian nesting dolls, trains the model
  so that the *first* $m$ dimensions are themselves a good embedding. You can truncate 1024 to 256
  dims (re-normalise!) and lose only a little quality. OpenAI's `dimensions` parameter and many open
  models support this.
- **Scalar quantisation** (float32 to **int8**, whole numbers from -128 to 127 stored in one byte):
  4x smaller, tiny quality loss.
- **Binary quantisation** (keep only the sign of each dimension as one bit): 32x smaller. Search
  uses **Hamming distance**, the number of bit positions where two codes differ, which computers
  count extremely fast. Then **rescore**: re-rank the best candidates with the full-precision vectors
  to recover most of the quality.

The demo builds 20,000 clustered vectors, finds each query's true top 10 by exact search, and
measures how many of them binary search recovers on its own and with rescoring. **recall@10** is the
fraction of the true top 10 that appear in the returned 10:

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

How it works: `bits = D > 0` turns each vector into a row of `True`/`False` signs.
`(bits != (q > 0)).sum(1)` counts, for every document, how many signs differ from the query's: the
Hamming distance. The `ham` line keeps the 10 documents with the fewest differences. The rescoring
loop first keeps 100 candidates by Hamming distance (10 times more than needed, called
**oversampling**), then re-sorts those 100 by the real dot product and keeps 10. The output shows
binary search alone recovering only about 47 percent of the true top 10, while binary plus rescoring
recovers 100 percent here, for the cost of 100 full-precision dot products per query.

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

What the code does: `h` holds random token states of shape (2 sentences, 4 tokens, 3 numbers), and
the second sentence's padded positions are filled with 9.0 to make the bug visible. `mask[:, :, None]`
adds a third axis so the mask lines up with `h` for multiplication. `right` sums only real tokens and
divides by their count. `last` uses `mask.sum(1) - 1` (the index of each sentence's final real token)
to pick one vector per sentence. The output shows the naive mean at about `[3.7 4.3 4.1]`, pulled
towards 9, while the masked mean `[-1.529 -0.382 -0.781]` equals the hand check on the next line.

The naive mean is dominated by the junk at padded positions. Worse, with real models the bug is
*silent*: embeddings still look plausible, but a sentence's vector changes depending on what else was in
its batch, so retrieval quality degrades in a way that is hard to trace. A good regression test: embed a
sentence alone and inside a batch with a much longer sentence, and assert the two vectors match.

Last-token pooling has its own trap: it needs **right** padding (or an explicit index as above); with
left padding the last position is always a real token, with right padding the last position is padding.

## 8. Measuring an embedding model on your own data

Leaderboard rank is a starting point, not a decision. The experiment that matters takes an afternoon:
collect 50 to 200 real queries, label the passage(s) that answer each, and compute recall@k for every
candidate model. Here recall@k means "the share of queries whose correct passage appears in the top
$k$ results". A second useful number is **MRR** (mean reciprocal rank): for each query take 1 divided
by the rank of the correct passage (1 if first, 1/2 if second, 1/10 if tenth) and average. It rewards
putting the answer near the very top. The demo simulates two embedders of different quality to show
the **harness** (the reusable test program).

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

In the code, `truth` stands for the real meaning of each document and `embedder(noise)` imitates a
model that sees that meaning through a blur: more noise, worse model. `evaluate` ranks all documents
for every query, finds the position of the gold document (`pos`, counted from 1), and computes
recall@1, 5 and 20 and MRR. The strong model finds the right document first for about 79 percent of
queries (MRR 0.86); the weak one for only 19 percent (MRR 0.28), and still misses it in the top 20
for 40 percent of queries.

Things to vary in the real version of this harness, one at a time: the model, the query prefix, the
chunk size, Matryoshka truncation, and quantisation. Report recall at the depth you actually pass to the
reranker, and keep the per-query results so you can read the failures.

## 9. Similarity thresholds are model-specific

"Return results with cosine above 0.8" is a frequent requirement and a frequent mistake. Different models
squeeze scores into very different ranges: for some, unrelated texts already score 0.6 and near
duplicates 0.9; for others the same pairs score 0.1 and 0.7. A threshold must be **calibrated per model**
on labelled pairs, choosing the operating point from a precision-recall trade-off. **Precision** is
the share of returned pairs that are truly relevant; recall is the share of truly relevant pairs that
are returned. Raising the threshold raises precision and lowers recall:

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

The demo invents cosine scores for 500 relevant pairs (centred on 0.78) and 5,000 irrelevant pairs
(centred on 0.62, a high baseline that is realistic for many models). For each threshold, `tp` (true
positives) counts relevant pairs at or above it and `fp` (false positives) counts irrelevant ones.
The table shows the trade-off: at 0.60 recall is 0.996 but precision only 0.136; at 0.80 precision is
0.974 but recall falls to 0.370.

With this model, 0.80 keeps under half of the relevant pairs, while 0.70 lets in a flood of irrelevant
ones because negatives are ten times more common. In retrieval pipelines it is usually better to take a
fixed top-k and let a **reranker** (a slower, more accurate model that scores each query-document pair
together, lesson 11, and whose scores are designed to be thresholded) decide what is relevant.

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

## Glossary

- **Embedding model (embedder)**: a model that turns text into a vector capturing its meaning.
- **Sentence embedding**: one vector for a whole text.
- **Pooling (CLS, mean, last-token)**: combining per-token vectors into one vector.
- **Contrastive learning**: training by pulling matching pairs together and pushing others apart.
- **Anchor / positive / negative**: the item being trained on / one that should be close / one that
  should be far.
- **InfoNCE**: the softmax-based contrastive loss; **in-batch negatives** reuse other pairs' positives.
- **Hard negative**: a wrong document that looks right; the most useful kind to train on.
- **Norm / L2-normalised**: a vector's length / scaled to length 1.
- **Cosine similarity / dot product / Euclidean distance**: angle-only closeness / closeness that
  includes length / straight-line distance.
- **Nearest neighbours / top-k**: the stored vectors closest to a query / the best $k$ of them.
- **Exact (brute-force) search / ANN**: comparing with every vector / approximate nearest-neighbour
  search with an index.
- **Dense / sparse vector**: a short vector of non-zero numbers / a vocabulary-sized vector of mostly
  zeros.
- **Bi-encoder / late interaction (MaxSim)**: query and document embedded separately / one vector
  per token, matched token by token.
- **Matryoshka (MRL)**: embeddings whose leading dimensions are usable on their own.
- **Scalar / binary quantisation**: storing each number as int8 / as one sign bit.
- **Hamming distance**: the number of differing bits between two codes.
- **Rescoring / oversampling**: re-ranking candidates with full vectors / fetching more candidates
  than needed first.
- **Recall@k / precision / MRR**: share of relevant items found in the top $k$ / share of returned
  items that are relevant / average of 1 over the rank of the right answer.
- **MTEB**: the Massive Text Embedding Benchmark leaderboard.

## Check yourself

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
