# Exact evaluation and similarity measures

> **Before this lesson:** you should know what a token and an embedding are (see [From language models to foundation models](#/lesson/ai-eng/aie-rise)) and why AI outputs vary from run to run (see [Sampling, structured outputs and the probabilistic nature of AI](#/lesson/ai-eng/aie-sampling)). The previous lesson, [Language modeling metrics](#/lesson/ai-eng/aie-lm-metrics), explains what a metric is and why evaluating AI is hard. Every formula here is introduced in words first, and the code uses only basic Python and a little NumPy.

## In plain words

Once a model has answered, how do you score the answer automatically? This lesson covers the methods that give a clear, repeatable score: running the answer to see if it works, checking whether it matches a known correct answer, counting the words it shares with that answer, and comparing meanings with lists of numbers called embeddings.

An everyday picture: a teacher marking a test. A maths answer is right or wrong (an exact check). A spelling test can give partial credit for "recieve" (counting shared letters). An essay question is harder: two students can write completely different sentences that mean the same thing, so the teacher compares *ideas*, not words. And for a woodworking class, the best test is whether the chair holds your weight (does it *work*?). Each of these has a counterpart in AI evaluation, with the same strengths and blind spots.

Why this matters for a job: every AI team needs automated scores to compare prompts, models and versions without reading thousands of answers by hand. Interviewers ask "how would you evaluate a code generator?" (pass@k), "BLEU or embedding similarity?", and "what is cosine similarity?". Knowing what each score rewards, and what it misses, is what separates a trustworthy evaluation from a misleading one.

## Exact versus subjective evaluation

Huyen sorts evaluation methods into two families. **Exact evaluation** gives a verdict with no room for opinion: a multiple-choice answer is option A or it is not; code passes its tests or it does not. **Subjective evaluation**, such as essay grading or an AI judge, can change with who (or what) does the judging and how they are asked. This lesson covers the exact end of the spectrum: **functional correctness, exact match, lexical similarity and semantic similarity**, plus the embeddings that make semantic similarity possible. AI judges come in the next lesson.

## 1. Functional correctness

**Functional correctness** asks one question: does the output do what it was supposed to do? Did the generated website meet the requirements? Did the agent book the right restaurant? Huyen calls it the ultimate metric. It is not always easy to automate, but for code it is.

A **unit test** is a small piece of code that calls a function with a chosen input and checks that the result is what was expected. For **code generation**, you run the model's code against unit tests; the share of tasks where the code passes is called **execution accuracy**. Well-known **benchmarks** (shared sets of test problems) work this way: OpenAI's **HumanEval** and Google's **MBPP** (Mostly Basic Python Problems) for Python, and **Spider**, **BIRD-SQL** and **WikiSQL** for turning questions into **SQL** (Structured Query Language, the language used to query databases). Each problem comes with test cases, and a solution counts as correct only if it passes all of them.

Here is the idea in miniature. Suppose a model was asked for a function that adds up a list of numbers, and you check its answer like this:

```python
def total(xs):            # the model's generated code
    return sum(xs)

assert total([1, 2, 3]) == 6      # unit test 1
assert total([]) == 0             # unit test 2: an empty list
assert total([-5, 5]) == 0        # unit test 3: negatives
```

`assert` stops the program with an error if its condition is false. If all three lines pass, the answer is functionally correct for these tests. Notice the edge cases (the empty list, negative numbers): weak tests let wrong code through, a point we return to under failure modes.

### pass@k

Because generation is random, a model may solve a problem on one try and fail on the next. Benchmarks therefore draw $k$ solutions per problem, and count the problem as solved if **any one** of the $k$ passes every test. The share of problems solved this way is **pass@k** ("pass at k"). A larger $k$ gives a higher score and costs more, and code models are often compared at pass@1, pass@10 and pass@100.

Estimating pass@k by drawing exactly $k$ samples is noisy. The paper that introduced OpenAI's Codex model gave a better recipe: draw $n$ samples (with $n \ge k$), count how many, $c$, are correct, and work out the chance that a random group of $k$ of those $n$ contains at least one correct one. It uses the **binomial coefficient** $\binom{a}{b}$, read "a choose b": the number of ways to pick $b$ items from $a$. In words: the chance that *all* $k$ picks come from the $n-c$ wrong samples is $\binom{n-c}{k} / \binom{n}{k}$, so the chance of at least one right pick is one minus that. Averaged over problems (the $\mathbb{E}$ means "average"):

$$
\text{pass@}k = \mathbb{E}\left[1 - \frac{\binom{n-c}{k}}{\binom{n}{k}}\right]
$$

Worked example: $n = 5$ samples, $c = 2$ correct, $k = 2$. There are $\binom{5}{2} = 10$ ways to pick two samples, and $\binom{3}{2} = 3$ of them use only wrong samples. So pass@2 $= 1 - 3/10 = 0.7$.

```python-run
from math import comb
def pass_at_k(n, c, k):
    """Probability at least one of k samples (drawn from n with c correct) is correct."""
    if n - c < k: return 1.0
    return 1 - comb(n - c, k) / comb(n, k)
for c in [0, 1, 5, 20]:
    print(f"n=20, correct={c:2d}:  pass@1={pass_at_k(20,c,1):.3f}  pass@5={pass_at_k(20,c,5):.3f}  pass@10={pass_at_k(20,c,10):.3f}")
```

**Reading this Python line by line**

- `from math import comb` loads `comb(a, b)`, Python's built-in "a choose b".
- `def pass_at_k(n, c, k):` defines the estimator. The text in triple quotes is a *docstring*, a description of the function that Python stores but does not run.
- `if n - c < k: return 1.0` handles the case where there are fewer wrong samples than picks, so every group of $k$ must include a correct one.
- `return 1 - comb(n - c, k) / comb(n, k)` is the formula.
- The loop prints pass@1, pass@5 and pass@10 for 20 samples with 0, 1, 5 and 20 correct.
- Output: with 1 correct out of 20, pass@1 is 0.050, pass@5 is 0.250 and pass@10 is 0.500. With 5 correct, pass@10 is already 0.984. The same model looks far better at pass@10 than at pass@1, which is why you must compare models at the same $k$.

Functional correctness reaches beyond code. A game-playing bot can be scored by whether it wins, a scheduling agent by whether its schedule is feasible and efficient, a data pipeline by checks on its output. If the task has a measurable goal, measure it.

> [!TIP]
> Huyen notes that coding is the most common generative AI use case partly *because* it can be evaluated this way. When designing a product, ask whether success can be checked functionally. If it can, you can evaluate cheaply and at scale.

## 2. Similarity against reference data

When an output cannot be run, you can compare it with a **reference response**: a known good answer, also called a *ground truth* or *canonical answer*. Reference data is costly. It has to be written by people (often experts) or generated by AI, and a single input may have many correct references. Huyen lists four ways to measure how close an output is to a reference:

1. Ask an **evaluator** (a human or an AI) whether the two texts say the same thing.
2. **Exact match**: are they identical?
3. **Lexical similarity**: how many words or characters do they share?
4. **Semantic similarity**: how close are their meanings?

### Exact match

Exact match works for short, unambiguous answers: the result of a sum, a trivia answer ("Who was the first US woman to win a Nobel Prize?"), the letter of a multiple-choice option. Two common relaxations:

- Accept a response that **contains** the reference. "The answer is 1,975" against a reference of "1975" also needs the comma removed first.
- **Normalize** both strings before comparing: lowercase everything, strip punctuation and the articles "a", "an" and "the", and squeeze repeated spaces into one. This is the convention of SQuAD (the Stanford Question Answering Dataset), a famous reading-comprehension benchmark.

Exact match breaks down on longer or open-ended outputs. "Est-ce que vous allez bien?" and "Comment allez-vous?" are both correct French for "How are you?", yet they do not match.

For **extractive question answering**, where the answer is a span copied out of a given passage, **token-level F1** is the standard companion to exact match. It needs two ideas:

- **Precision**: of the tokens the model produced, what fraction are in the reference? It punishes padding.
- **Recall**: of the tokens in the reference, what fraction did the model produce? It punishes leaving things out.

**F1** combines them with the *harmonic mean*, $F_1 = \frac{2PR}{P+R}$, a kind of average that stays low if either part is low. The recipe: normalize both strings, split them into tokens, count the shared tokens (counting duplicates as often as they appear in both, which is called a *multiset* overlap), then compute precision = shared / tokens in prediction and recall = shared / tokens in reference. You will implement this in the `aie-qa-exact-f1` problem.

### Lexical similarity

**Lexical similarity** measures overlap in surface form: shared words, word sequences or characters. "Lexical" means "to do with words". Take the reference "My cats scare the mice". "My cats eat the mice" shares 4 of its 5 words (80%), and "Cats and mice fight all the time" shares 3 of 5 (60%).

- **Fuzzy matching**, also called **edit distance**, counts the insertions, deletions and substitutions (sometimes also swaps of neighbouring characters) needed to turn one string into the other. "bad" is 1 edit from "bard" (insert "r") and 3 from "cash" (change b to c, change d to s, add h).
- **n-gram similarity** compares sequences of $n$ consecutive tokens. Single tokens are *unigrams*, pairs are *bigrams*. "My cats scare the mice" has 4 bigrams: "my cats", "cats scare", "scare the", "the mice".
- Named metrics built on these ideas include **BLEU** (Bilingual Evaluation Understudy, precision-based n-gram overlap from machine translation), **ROUGE** (Recall-Oriented Understudy for Gisting Evaluation, recall-based, from summarization), METEOR++, TER (Translation Edit Rate) and CIDEr (used for image captions).

**ROUGE-L** is built on the **longest common subsequence (LCS)**: the longest list of tokens that appears in both texts in the same order, though not necessarily side by side. For "my cats eat the mice" against "my cats scare the mice", the LCS is "my cats the mice", length 4. In words: precision is the LCS length over the candidate's length, recall is the LCS length over the reference's length, and the score is their F1:

$$
P = \frac{\text{LCS}}{|\text{cand}|},\quad R = \frac{\text{LCS}}{|\text{ref}|},\quad F = \frac{2PR}{P+R}
$$

Here $|\text{cand}|$ means "the number of tokens in the candidate". For the example: $P = 4/5$, $R = 4/5$, so $F = 0.8$.

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

**Reading this Python line by line**

- `lcs(a, b)` uses a technique called **dynamic programming**: solve small versions of the problem first and store their answers in a table so larger versions can reuse them. `dp[i][j]` holds the LCS length of the first `i` tokens of `a` and the first `j` tokens of `b`. The table starts full of zeros.
- In the double loop: if the current tokens match (`a[i-1]==b[j-1]`), the LCS grows by one from the diagonal cell; otherwise it is the better of skipping a token from `a` or from `b`. `dp[-1][-1]` (the last row, last column) is the answer for the full lists.
- `edit_distance(a, b)` uses the same table idea but keeps only one row at a time (`prev` and `cur`). Each new cell is the cheapest of a deletion (`prev[j]+1`), an insertion (`cur[j-1]+1`) or a substitution (`prev[j-1]` plus 1 if the characters differ; `(ca!=cb)` counts as 1 when true and 0 when false).
- `set(c) & set(ref)` keeps the distinct words found in both lists; `len(...)` counts them.
- Output: "my cats eat the mice" has overlap 4/5 and ROUGE-L 0.800; "cats and mice fight all the time" has 3/5 and 0.333; "the mice scare my cats" shares all 5 words but in a different order, so its longest in-order match is only two words long ("my cats" or "the mice") and ROUGE-L is 0.400. The edit distances are 1 and 3, as worked out above.

The third line shows what word order adds: identical vocabulary, a changed meaning (the mice now scare the cats), and a lower ROUGE-L than the unordered word count would suggest.

**Drawbacks of lexical similarity.** You need a full set of references, or a good answer scores low only because it is worded differently. References can be wrong too: Huyen notes that the organisers of WMT 2023, a major machine-translation competition, found many poor reference translations in their own data. And higher overlap does not mean a better answer: on HumanEval-style coding tasks, OpenAI found that correct and incorrect solutions had similar BLEU scores. As foundation models took over, fewer benchmarks rely on these metrics.

## 3. Semantic similarity and embeddings

**Semantic similarity** compares meaning rather than surface form. "What's up?" and "How are you?" share no words but mean nearly the same. "Let's eat, grandma" and "Let's eat grandma" are lexically almost identical but mean very different things.

To compare meanings, each text is first turned into an **embedding**: a list of numbers, also called a **vector**, produced by a model so that texts with similar meanings get similar lists. Each position in the list is a **dimension**. You can picture a 2-dimensional embedding as an arrow on a sheet of paper; real embeddings have hundreds or thousands of dimensions, but the geometry works the same way.

Two embeddings are usually compared with **cosine similarity**, which measures the angle between the two arrows and ignores their lengths. It needs two pieces:

- The **dot product** $A \cdot B$: multiply the vectors position by position and add the results.
- The **norm** (length) $\|A\|$: the square root of the dot product of a vector with itself.

In words: cosine similarity is the dot product divided by the two lengths.

$$
\cos(A, B) = \frac{A\cdot B}{\|A\|\,\|B\|} \in [-1, 1]
$$

Worked example: $A = (1, 0)$ and $B = (1, 1)$. The dot product is $1\cdot1 + 0\cdot1 = 1$. The lengths are $\|A\| = 1$ and $\|B\| = \sqrt{2} \approx 1.414$. So $\cos = 1 / 1.414 = 0.707$, which is the cosine of a 45-degree angle. A value of 1 means the arrows point the same way, 0 means they are at right angles (unrelated), and −1 means they point in opposite directions. Metrics built on this idea include **BERTScore** (which compares embeddings from the BERT model token by token) and **MoverScore** (embeddings plus a mix of algorithms).

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

**Reading this Python line by line**

- `emb = {...}` is a dictionary mapping three sentences to made-up 4-dimensional embeddings. A real embedding model would produce hundreds of dimensions; here we invent small ones whose first number loosely means "greeting" and second "animals".
- In `cos`, `a @ b` is NumPy's dot product, and `np.linalg.norm(a)` is the length of `a`. `float(...)` converts the result to a plain Python number.
- The two nested loops visit every pair of sentences once (`j` starts at `i+1`, so no pair is repeated and no sentence is compared with itself).
- Output: the two greetings score 0.977, very close in meaning; "How are you?" against the cat sentence scores 0.099, nearly unrelated; "What's up?" against the cat sentence scores 0.253.

With a real model the code looks like this (static, because it needs a downloaded model or a network connection):

```python
from sentence_transformers import SentenceTransformer   # a popular embedding library
model = SentenceTransformer("all-MiniLM-L6-v2")          # a small open embedding model
vecs = model.encode(["How are you?", "What's up?"])      # one 384-number vector per text
```

### Introduction to embeddings

An **embedding** is a vector meant to capture the meaning of the original data. Typical sizes run from 100 to 10,000 dimensions. Huyen's examples: BERT produces 768 dimensions (base size) or 1,024 (large size); OpenAI's text-embedding-3-small produces 1,536 and text-embedding-3-large 3,072; Cohere's Embed v3 produces 1,024 (384 for its light version).

- Every language model computes embeddings internally: the first thing a transformer does is turn each token into a vector. Dedicated **embedding models** are trained specifically so that their vectors are useful for comparison, and some are trained as part of a larger model.
- **Multimodal embeddings** place several kinds of data in one **joint embedding space**, so a photo and a sentence can be compared directly. CLIP has two **encoders** (models that turn an input into an embedding), one for text and one for images, and trains them with a **contrastive** objective: matching (image, caption) pairs are pulled close together and mismatched pairs are pushed apart. ULIP (text, image and 3D shapes) and ImageBind (six kinds of data) extend the idea.
- Embeddings are judged by how useful they are for tasks: retrieval (finding related documents), classification, clustering (grouping similar items), deduplication and similarity scoring. The **MTEB** benchmark (Massive Text Embedding Benchmark) measures many of these at once.

Semantic similarity has weaknesses of its own: its quality depends entirely on the embedding model, computing embeddings adds latency and cost, and a high similarity score is a proxy for "says the same thing", not a guarantee of correctness.

> [!INTERVIEW]
> **"BLEU/ROUGE vs embedding similarity vs exact match: when would you use each?"** Exact match (with normalization) for short, closed-form answers such as numbers, entities and labels. Token F1 for extractive QA. Lexical metrics when wording matters and references are comprehensive (older translation and summarization work). Embedding similarity when paraphrases should count. Functional correctness whenever the output can be executed or checked. For open-ended quality none of these is enough on its own, so add AI judges or human review.

## 4. Worked example: one answer, four metrics

The question is "Who developed the theory of general relativity?" and the reference is "Albert Einstein". Here are four model outputs.

| Output | Exact match | Token F1 | ROUGE-L F | Likely embedding similarity |
|---|---|---|---|---|
| "Albert Einstein" | 1 | 1.00 | 1.00 | very high |
| "Einstein" | 0 | 0.67 | 0.67 | high |
| "It was developed by Albert Einstein in 1915." | 0 | 0.40 | 0.40 | high |
| "Isaac Newton" | 0 | 0.00 | 0.00 | moderate (both are famous physicists) |

Token F1 for the second row: the prediction has 1 token and the reference 2, with 1 shared. Precision is 1/1 = 1, recall is 1/2, and F1 is $2 \cdot 1 \cdot 0.5 / 1.5 = 0.67$. For the third row the prediction has 8 tokens after normalization, 2 of them shared: precision 2/8 = 0.25, recall 2/2 = 1.0, and F1 $= 2 \cdot 0.25 \cdot 1 / 1.25 = 0.40$.

The table shows the trade-offs. Exact match rejects two correct answers. Token F1 and ROUGE-L give partial credit but **penalize a correct, complete sentence more than a terse fragment**, because extra words lower precision. Embedding similarity forgives wording but gives "Isaac Newton" a noticeable score, because the two answers are about the same topic. No single column says the third answer is right and the fourth wrong. That gap is what "contains the reference" checks and AI judges fill.

```python-run
import string
from collections import Counter
def norm(s):
    s = "".join(c for c in s.lower() if c not in string.punctuation)
    return [w for w in s.split() if w not in ("a", "an", "the")]
def f1(pred, ref):
    p, r = norm(pred), norm(ref)
    common = sum((Counter(p) & Counter(r)).values())
    if common == 0: return 0.0
    P, R = common / len(p), common / len(r)
    return 2 * P * R / (P + R)
ref = "Albert Einstein"
for out in ["Albert Einstein", "Einstein", "It was developed by Albert Einstein in 1915.", "Isaac Newton"]:
    em = int(norm(out) == norm(ref)); contains = int(" ".join(norm(ref)) in " ".join(norm(out)))
    print(f"EM={em}  contains={contains}  F1={f1(out, ref):.2f}  | {out}")
```

**Reading this Python line by line**

- `string.punctuation` is a ready-made string of punctuation characters. `norm` lowercases the text, keeps only characters that are not punctuation, splits on spaces and drops the three articles.
- `Counter(p)` counts how many times each token appears, for example `Counter(["the", "cat", "the"])` is `{"the": 2, "cat": 1}`. `Counter(p) & Counter(r)` keeps, for each token, the smaller of its two counts: that is the multiset overlap. `.values()` and `sum` add up those counts.
- `f1` returns 0 when nothing is shared (to avoid dividing by zero), otherwise the harmonic mean of precision and recall.
- `em` is 1 when the normalized token lists are identical. `contains` joins the tokens back into strings and checks whether the reference appears inside the output.
- Output: `EM=1 contains=1 F1=1.00` for "Albert Einstein"; `EM=0 contains=0 F1=0.67` for "Einstein"; `EM=0 contains=1 F1=0.40` for the long sentence; `EM=0 contains=0 F1=0.00` for "Isaac Newton". The "contains" check is the only one that marks the long correct sentence as right.

## 5. BLEU in a little more detail

BLEU is still quoted often, so it is worth knowing what it computes. For each n-gram size (usually 1 to 4) it takes the **clipped precision**: the fraction of the candidate's n-grams that appear in a reference, where each reference n-gram can be matched only as many times as it occurs there. Clipping stops a candidate such as "the the the the" from scoring perfect unigram precision against "the cat sat on the mat", which contains "the" only twice. The precisions for different $n$ are combined with a geometric mean, and a **brevity penalty** lowers the score of candidates shorter than the reference, because precision alone would reward saying almost nothing. In words, the penalty is 1 when the candidate is at least as long as the reference and $e^{1 - r/c}$ otherwise, where $r$ and $c$ are the reference and candidate lengths.

Worked example for the candidate "the cat" against the six-token reference: precision is 2/2 = 1, but the penalty is $e^{1 - 6/2} = e^{-2} \approx 0.14$, so BLEU-1 is 0.14.

```python-run
import math
from collections import Counter
def bleu1(cand, ref):
    c, r = cand.lower().split(), ref.lower().split()
    clipped = sum((Counter(c) & Counter(r)).values())          # a reference word is matched at most once per occurrence
    precision = clipped / len(c)
    bp = 1.0 if len(c) >= len(r) else math.exp(1 - len(r) / len(c))
    return precision, bp, precision * bp
ref = "the cat sat on the mat"
for cand in ["the cat sat on the mat", "the the the the the the", "the cat", "a feline rested on a rug"]:
    p, bp, s = bleu1(cand, ref)
    print(f"precision {p:.2f}  brevity penalty {bp:.2f}  BLEU-1 {s:.2f} | {cand}")
```

This is a simplified BLEU with unigrams only. The `Counter(c) & Counter(r)` trick from the previous demo does the clipping. Output: the exact copy scores 1.00; "the the the the the the" gets precision 0.33 (only two of its six "the"s can be matched); "the cat" has perfect precision but a 0.14 brevity penalty; and "a feline rested on a rug", a perfectly reasonable paraphrase, scores 0.17 because only "on" is shared. That last line is the central weakness of every lexical metric: it measures shared surface form, and meaning can survive with very few shared words.

## 6. Choosing a method

| Situation | Reasonable first choice | Watch out for |
|---|---|---|
| Code, SQL, anything executable | Functional correctness (tests, execution accuracy) | Weak tests pass wrong code |
| Short factual answers, labels, numbers | Exact match after normalization, plus "contains" | Formatting differences such as "1,975" vs "1975" |
| Extractive QA | Exact match and token F1, best score over all references | Long correct answers get low precision |
| Translation or summarization with good references | ROUGE or BLEU as a regression signal | Paraphrases score low, and references may be poor |
| Paraphrase-tolerant comparison, retrieval, deduplication | Embedding cosine similarity | Topically close but wrong answers score high |
| Open-ended quality with no reference | AI judge or human review (next lesson) | Judge bias and inconsistency |

A *regression signal* here means a score you watch for sudden drops between versions, rather than a measure of absolute quality. A practical pattern is to layer the methods: run the cheapest exact check that applies to every example, add similarity scores as a trend signal, and save AI judges and human reviewers for a sample and for cases where the cheap metrics disagree.

### Common failure modes

- **A metric improves while the product gets worse.** The model learned to copy reference phrasing, which raises ROUGE, while becoming less accurate. Keep at least one metric tied to correctness.
- **Unit tests that are too weak.** pass@k counts a solution as correct when it passes the tests you wrote. Add edge cases, and review a sample of passing solutions by hand.
- **One reference where many answers are valid.** Scores then measure agreement with one annotator's wording. Collect several references or switch to a judge.
- **Thresholds copied from another embedding model.** A cosine of 0.8 means different things for different models. Calibrate thresholds on labelled pairs from your own data.
- **Comparing scores computed with different normalization.** Record the tokenizer, the normalization and the metric implementation with every result.

## Pitfalls

- Using exact match without normalization ("Paris" versus "paris.").
- Trusting lexical scores when the references are incomplete or wrong.
- Treating cosine similarity as accuracy. Two responses can be close in meaning and both wrong.
- Forgetting that pass@k depends on k. Compare at the same k.

## Summary

- **Exact evaluation** gives unambiguous verdicts. **Functional correctness** is the ultimate metric and easy to automate for code (unit tests, pass@k).
- With reference data you can use **exact match** (normalize, consider "contains"), **token F1**, **lexical similarity** (edit distance, n-grams, BLEU, ROUGE-L) and **semantic similarity** (embeddings plus cosine, BERTScore).
- Lexical metrics reward shared wording; semantic metrics reward shared meaning; neither proves correctness.
- **Embeddings** map data to vectors that capture meaning. Joint embedding spaces (CLIP) make cross-modal comparison possible, and the same vectors power search and RAG later in the track.

## Glossary

- **Exact evaluation**: scoring with no room for judgement, such as a test that passes or fails.
- **Subjective evaluation**: scoring that depends on the judge, such as essay grading.
- **Functional correctness**: whether the output actually does the intended job.
- **Unit test**: a small check that runs code on a chosen input and compares the result with the expected one.
- **Execution accuracy**: the share of generated programs that pass their tests.
- **pass@k**: the share of problems where at least one of k sampled solutions passes.
- **Binomial coefficient**: "a choose b", the number of ways to pick b items from a.
- **Reference response (ground truth)**: a known good answer to compare against.
- **Exact match**: the output equals the reference, usually after normalization.
- **Normalization**: tidying text (lowercase, strip punctuation and articles) before comparing.
- **Precision / recall / F1**: share of produced tokens that are correct; share of reference tokens that were produced; their harmonic mean.
- **Lexical similarity**: overlap in surface form (shared words or characters).
- **Edit distance**: the number of single-character edits that turn one string into another.
- **n-gram**: a run of n consecutive tokens.
- **BLEU / ROUGE**: n-gram overlap metrics from translation (precision-based) and summarization (recall-based).
- **Longest common subsequence (LCS)**: the longest token sequence found in both texts in the same order.
- **Dynamic programming**: solving a problem by filling a table of answers to smaller sub-problems.
- **Semantic similarity**: closeness of meaning.
- **Embedding / vector / dimension**: a list of numbers representing meaning; the list itself; one position in it.
- **Cosine similarity**: dot product divided by the two lengths; 1 same direction, 0 unrelated, −1 opposite.
- **Joint embedding space**: one space shared by several kinds of data, such as images and text.
- **Contrastive training**: pulling matching pairs together and pushing mismatched pairs apart.

```quiz
[
  {"q": "A model solves a coding problem if ANY of its k samples passes all tests. This metric is…", "options": ["BLEU@k", "pass@k", "top-k accuracy", "Recall@k"], "answer": 1, "explain": "pass@k is the fraction of problems where at least one of k sampled solutions is functionally correct."},
  {"q": "Why can exact match fail for translation?", "options": ["Translations are always wrong", "Many different correct translations exist, so a correct one may not match the reference", "Exact match is too slow", "It needs embeddings"], "answer": 1, "explain": "Open-ended outputs have many valid forms, and exact match accepts only one."},
  {"q": "Edit distance between 'bad' and 'bard' is…", "options": ["0", "1", "2", "3"], "answer": 1, "explain": "One insertion ('r') turns 'bad' into 'bard'."},
  {"q": "Which pair has HIGH lexical similarity but very different meaning?", "options": ["'How are you?' / 'What's up?'", "'Let's eat, grandma' / 'Let's eat grandma'", "'cat' / 'feline'", "'big' / 'large'"], "answer": 1, "explain": "Nearly identical tokens, very different meaning. This is why semantic similarity exists."},
  {"q": "Cosine similarity of 1 between two embeddings means…", "options": ["They are at right angles", "They point in the same direction", "They are opposite", "One is zero"], "answer": 1, "explain": "Cosine measures the angle between vectors: 1 is the same direction, 0 is at right angles, −1 is opposite."},
  {"q": "How does CLIP place images and text in a joint embedding space?", "options": ["By training on ImageNet labels", "Contrastive training so matching image-text pairs are close and mismatched pairs are far", "By averaging pixels", "By RLHF"], "answer": 1, "explain": "CLIP trains an image encoder and a text encoder together with a contrastive objective."},
  {"q": "Which observation undermines BLEU for code evaluation?", "options": ["BLEU needs GPUs", "Correct and incorrect solutions can have similar BLEU scores", "BLEU only works for Python", "BLEU is always zero for code"], "answer": 1, "explain": "Lexical overlap does not capture functional correctness."},
  {"q": "You sampled n = 5 solutions and c = 2 are correct. What is the unbiased pass@2?", "options": ["0.4", "0.6", "0.7", "1.0"], "answer": 2, "explain": "There are C(5,2) = 10 pairs, C(3,2) = 3 of which are all wrong, so pass@2 = 1 - 3/10 = 0.7."}
]
```

> **Source:** Huyen, *AI Engineering*, ch. 3 ("Exact Evaluation": functional correctness, similarity measurements against reference data, introduction to embeddings). The pass@k estimator is from Chen et al., "Evaluating Large Language Models Trained on Code" (2021).
