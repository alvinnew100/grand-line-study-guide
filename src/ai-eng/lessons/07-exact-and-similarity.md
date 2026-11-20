# Exact evaluation and similarity measures

Huyen separates evaluation methods into two families. **Exact evaluation** produces a judgment without ambiguity. A multiple-choice answer is either A or not, and code either passes its tests or doesn't. **Subjective evaluation**, such as essay grading or AI judges, can change with the judge or the prompt. This lesson covers the exact end of the spectrum: **functional correctness, exact match, lexical similarity and semantic similarity**, along with the embeddings that make semantic similarity possible. AI judges come next.

## 1. Functional correctness

**Functional correctness** asks whether the system does what it was supposed to do. Did the generated website meet the requirements? Did the agent book the right restaurant? Huyen calls it *the ultimate metric*. It is not always easy to automate, but for code it is.

**Code generation**: run the generated code against unit tests. This is *execution accuracy*. Benchmarks such as OpenAI's **HumanEval**, Google's **MBPP**, and text-to-SQL benchmarks (**Spider**, **BIRD-SQL**, **WikiSQL**) all work this way. Each problem comes with test cases, and a solution is correct if it passes them all.

### pass@k

Since generation is probabilistic, benchmarks sample $k$ solutions per problem. A problem counts as solved if **any** of the $k$ samples passes all tests. The fraction of problems solved is **pass@k**. A higher $k$ gives a higher score but costs more, and code models are often compared at pass@1, pass@10 and pass@100.

The unbiased estimator from the Codex paper samples $n \ge k$ solutions, counts the $c$ that are correct, and computes:

$$
\text{pass@}k = \mathbb{E}\left[1 - \frac{\binom{n-c}{k}}{\binom{n}{k}}\right]
$$

```python-run
from math import comb
def pass_at_k(n, c, k):
    """Probability at least one of k samples (drawn from n with c correct) is correct."""
    if n - c < k: return 1.0
    return 1 - comb(n - c, k) / comb(n, k)
for c in [0, 1, 5, 20]:
    print(f"n=20, correct={c:2d}:  pass@1={pass_at_k(20,c,1):.3f}  pass@5={pass_at_k(20,c,5):.3f}  pass@10={pass_at_k(20,c,10):.3f}")
```

Functional correctness extends beyond code. Game bots can be scored by game outcome, scheduling agents by whether the schedule is feasible and efficient, and data-processing pipelines by output checks. If the task has a measurable objective, measure it.

> [!TIP]
> Huyen notes that coding is the most common generative AI use case partly *because* it can be evaluated this way. When designing a product, ask whether success can be checked functionally. If it can, you can evaluate cheaply and at scale.

## 2. Similarity against reference data

When outputs cannot be executed, compare them with **reference responses** (ground truths, canonical answers). Reference data is costly: it needs humans (often experts) or AI to generate, and there can be many correct references per input. Huyen distinguishes four ways to measure similarity:

1. Ask an **evaluator** (human or AI) whether two texts are the same.
2. **Exact match**.
3. **Lexical similarity**.
4. **Semantic similarity**.

### Exact match

Exact match works for short, unambiguous answers: math results, trivia ("first US woman to win a Nobel Prize?"), multiple-choice options. Variations:

- Accept a response that **contains** the reference. "The answer is 1,975" for a reference "1975" may need normalization.
- **Normalize** before comparing: lowercase, strip punctuation and articles, collapse whitespace. This is the SQuAD convention.

Exact match breaks on longer or open-ended outputs. "Est-ce que vous allez bien?" and "Comment allez-vous?" are both correct French translations of "How are you?" but do not match.

For extractive QA, **token-level F1** is the standard companion to exact match. Normalize both strings, tokenize, count the overlapping tokens (as a multiset), and compute precision = overlap / |prediction|, recall = overlap / |reference|, and F1 as their harmonic mean. You will implement this in the `aie-qa-exact-f1` problem.

### Lexical similarity

**Lexical similarity** measures token overlap. Reference: "My cats scare the mice". "My cats eat the mice" shares 4 of 5 words (80%), and "Cats and mice fight all the time" shares 3 of 5 (60%).

- **Fuzzy matching / edit distance**: the number of insertions, deletions and substitutions (sometimes transpositions) needed to turn one string into the other. "bad" is 1 edit from "bard" and 3 from "cash".
- **n-gram similarity**: overlap of sequences of $n$ tokens. "My cats scare the mice" has 4 bigrams.
- Common metrics are **BLEU** (precision-oriented n-gram overlap with a brevity penalty, from translation), **ROUGE** (recall-oriented, from summarization; ROUGE-L uses the longest common subsequence), METEOR++, TER and CIDEr.

ROUGE-L with the **longest common subsequence (LCS)**:

$$
P = \frac{\text{LCS}}{|\text{cand}|},\quad R = \frac{\text{LCS}}{|\text{ref}|},\quad F = \frac{2PR}{P+R}
$$

```python-run
def lcs(a, b):
    dp = [[0]*(len(b)+1) for _ in range(len(a)+1)]
    for i in range(1, len(a)+1):
        for j in range(1, len(b)+1):
            dp[i][j] = dp[i-1][j-1]+1 if a[i-1]==b[j-1] else max(dp[i-1][j], dp[i][j-1])
    return dp[-1][-1]

def edit_distance(a, b):
    prev = list(range(len(b)+1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j]+1, cur[j-1]+1, prev[j-1]+(ca!=cb)))
        prev = cur
    return prev[-1]

ref = "my cats scare the mice".split()
for cand in ["my cats eat the mice", "cats and mice fight all the time", "the mice scare my cats"]:
    c = cand.split(); L = lcs(c, ref)
    P, R = L/len(c), L/len(ref); F = 0 if L == 0 else 2*P*R/(P+R)
    print(f"{cand:35s} unigram-overlap={len(set(c)&set(ref))}/{len(ref)}  ROUGE-L F={F:.3f}")
print("edit distance bad->bard:", edit_distance("bad","bard"), " bad->cash:", edit_distance("bad","cash"))
```

**Drawbacks.** You need a comprehensive set of references, or a good answer scores low simply because it differs. References can also be wrong: Huyen notes the WMT 2023 organizers found many bad reference translations. Higher lexical similarity does not mean better output. On HumanEval-style tasks, OpenAI found that incorrect and correct solutions had similar BLEU scores. With foundation models, fewer benchmarks rely on these metrics.

## 3. Semantic similarity and embeddings

**Semantic similarity** compares meaning rather than surface form. "What's up?" and "How are you?" are lexically different but semantically close, while "Let's eat, grandma" and "Let's eat grandma" are lexically almost identical with very different meanings.

Texts are first converted into **embeddings**, numerical vectors that capture meaning, and then compared, usually with **cosine similarity**:

$$
\cos(A, B) = \frac{A\cdot B}{\|A\|\,\|B\|} \in [-1, 1]
$$

A value of 1 means the vectors point the same way, and −1 means opposite. Metrics built on this idea include **BERTScore** (embeddings from BERT) and **MoverScore** (embeddings plus a mix of algorithms).

```python-run
import numpy as np
# Toy embeddings: in practice you'd call an embedding model.
emb = {
    "How are you?":         np.array([0.9, 0.1, 0.0, 0.2]),
    "What's up?":           np.array([0.8, 0.2, 0.1, 0.3]),
    "The cat sat on a mat": np.array([0.0, 0.9, 0.4, 0.0]),
}
def cos(a, b): return float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b)))
names = list(emb)
for i in range(len(names)):
    for j in range(i+1, len(names)):
        print(f"{names[i]:22s} vs {names[j]:22s} cos={cos(emb[names[i]], emb[names[j]]):.3f}")
```

### Introduction to embeddings

An **embedding** is a vector representation intended to capture the meaning of the original data. Typical sizes run from 100 to 10,000 dimensions. Huyen's table lists BERT at 768 (base) and 1,024 (large), OpenAI's text-embedding-3-small at 1,536 and text-embedding-3-large at 3,072, and Cohere's Embed v3 at 1,024 (or 384 for light).

- Every language model produces embeddings internally, and the input to the transformer is an embedding. Dedicated **embedding models** are trained specifically to produce useful ones, sometimes as part of a larger model.
- **Multimodal embeddings** put several modalities in one **joint embedding space**. CLIP trains a text encoder and an image encoder with a contrastive objective, so matching (image, text) pairs are close and mismatched ones are far apart. ULIP (text, image, 3D) and ImageBind (six modalities) extend the idea.
- Embeddings are judged by usefulness on tasks: retrieval, classification, clustering, deduplication and similarity. The **MTEB** benchmark covers many of these.

Semantic similarity's weaknesses: its quality depends on the embedding model, computing embeddings costs latency and money, and a high similarity score is a proxy, not a guarantee of correctness.

> [!INTERVIEW]
> **"BLEU/ROUGE vs embedding similarity vs exact match: when would you use each?"** Exact match (with normalization) for short, closed-form answers such as math, entities and labels. Token F1 for extractive QA. Lexical metrics when wording matters and references are comprehensive (legacy translation and summarization). Embedding similarity when paraphrases should count. Functional correctness whenever the output can be executed or checked. For open-ended quality, none of these is enough on its own, so add AI judges or humans.

## Pitfalls

- Using exact match without normalization ("Paris" vs "paris.").
- Trusting lexical scores when the references are incomplete or wrong.
- Treating cosine similarity as accuracy. Two responses can be semantically close and both wrong.
- Forgetting that pass@k depends on k. Compare at the same k.

## Summary

- **Exact evaluation** gives unambiguous judgments. **Functional correctness** is the ultimate metric and is easy to automate for code (unit tests, pass@k).
- With reference data: **exact match** (normalize, consider "contains"), **token F1**, **lexical similarity** (edit distance, n-grams, BLEU, ROUGE-L) and **semantic similarity** (embeddings plus cosine, BERTScore).
- Embeddings map data to vectors that capture meaning. Joint embedding spaces (CLIP) make cross-modal similarity possible. They power evaluation, search and RAG.

```quiz
[
  {"q": "A model solves a coding problem if ANY of its k samples passes all tests. This metric is…", "options": ["BLEU@k", "pass@k", "top-k accuracy", "Recall@k"], "answer": 1, "explain": "pass@k is the fraction of problems where at least one of k sampled solutions is functionally correct."},
  {"q": "Why can exact match fail for translation?", "options": ["Translations are always wrong", "Many different correct translations exist, so a correct one may not match the reference", "Exact match is too slow", "It needs embeddings"], "answer": 1, "explain": "Open-ended outputs have many valid forms, and exact match accepts only one."},
  {"q": "Edit distance between 'bad' and 'bard' is…", "options": ["0", "1", "2", "3"], "answer": 1, "explain": "One insertion ('r') turns 'bad' into 'bard'."},
  {"q": "Which pair has HIGH lexical similarity but very different meaning?", "options": ["'How are you?' / 'What's up?'", "'Let's eat, grandma' / 'Let's eat grandma'", "'cat' / 'feline'", "'big' / 'large'"], "answer": 1, "explain": "Nearly identical tokens, very different meaning. This is why semantic similarity exists."},
  {"q": "Cosine similarity of 1 between two embeddings means…", "options": ["They are orthogonal", "They point in the same direction", "They are opposite", "One is zero"], "answer": 1, "explain": "Cosine measures the angle between vectors: 1 is the same direction, 0 is orthogonal, −1 is opposite."},
  {"q": "How does CLIP place images and text in a joint embedding space?", "options": ["By training on ImageNet labels", "Contrastive training so matching image-text pairs are close and mismatched pairs are far", "By averaging pixels", "By RLHF"], "answer": 1, "explain": "CLIP trains an image encoder and a text encoder jointly with a contrastive objective."},
  {"q": "Which observation undermines BLEU for code evaluation?", "options": ["BLEU needs GPUs", "Correct and incorrect solutions can have similar BLEU scores", "BLEU only works for Python", "BLEU is always zero for code"], "answer": 1, "explain": "Lexical overlap does not capture functional correctness."}
]
```

> **Source:** Huyen, *AI Engineering*, ch. 3 ("Exact Evaluation": functional correctness, similarity measurements against reference data, introduction to embeddings).
