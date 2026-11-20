import random as _r

_g = _r.Random(42)


def _rand_logits(n, scale=3.0):
    return [round(_g.uniform(-scale, scale), 3) for _ in range(n)]


def _rand_probs(n):
    w = [_g.random() + 0.01 for _ in range(n)]
    s = sum(w)
    return [round(x / s, 6) for x in w]


PROBLEMS = [
# ---------------------------------------------------------------- softmax with temperature
dict(
    id="aie-softmax-temperature",
    title="Softmax with Temperature",
    difficulty="Easy",
    pattern="Sampling",
    entry="softmax_temperature",
    compare="float",
    description=r"""
A language model outputs **logits**. Before sampling, they are divided by a temperature $T$ and turned
into probabilities with softmax:

$$p_i = \frac{e^{x_i/T}}{\sum_j e^{x_j/T}}$$

Implement `softmax_temperature(logits, temperature)` that returns the probability list.

Rules:
- `temperature > 0`: return the softmax of `logits / temperature`. It must be **numerically stable**:
  logits can be as large as `1000` or as small as `-1000`.
- `temperature == 0`: greedy decoding. Return a one-hot list with `1.0` at the index of the largest
  logit (the **first** one if there are ties) and `0.0` elsewhere.
- `logits` has at least one element.

**Example:** `logits = [1, 2], temperature = 1` → `[0.2689, 0.7311]`

**Example:** `logits = [1, 2], temperature = 0.5` → `[0.1192, 0.8808]` (lower T sharpens)
""",
    starter='''def softmax_temperature(logits, temperature):
    pass
''',
    solution='''import math
def softmax_temperature(logits, temperature):
    if temperature == 0:
        best = max(range(len(logits)), key=lambda i: (logits[i], -i))
        return [1.0 if i == best else 0.0 for i in range(len(logits))]
    z = [x / temperature for x in logits]
    m = max(z)
    e = [math.exp(v - m) for v in z]
    s = sum(e)
    return [v / s for v in e]
''',
    tests=[
        [[1, 2], 1],
        [[1, 2], 0.5],
        [[1, 2, 3], 2.0],
        [[5.0], 0.7],
        [[0, 0, 0, 0], 1],
        [[1000, 999, -1000], 1],
        [[-1000, -1001], 0.1],
        [[3, 7, 7, 1], 0],
        [[2.5, -1, 0.3], 0],
        [[1, 2, 3, 4], 100],
        [[1, 2, 3, 4], 0.01],
        [_rand_logits(50), 0.7],
        [_rand_logits(200, 10), 1.3],
    ],
    examples=2,
    wrong_solutions=[
        '''import math
def softmax_temperature(logits, temperature):
    if temperature == 0:
        best = logits.index(max(logits))
        return [1.0 if i == best else 0.0 for i in range(len(logits))]
    e = [math.exp(x / temperature) for x in logits]
    s = sum(e)
    return [v / s for v in e]
''',
        '''import math
def softmax_temperature(logits, temperature):
    if temperature == 0:
        best = logits.index(max(logits))
        return [1.0 if i == best else 0.0 for i in range(len(logits))]
    z = [x * temperature for x in logits]
    m = max(z)
    e = [math.exp(v - m) for v in z]
    s = sum(e)
    return [v / s for v in e]
''',
    ],
    guide=dict(
        prereqs="Softmax, exponentials, the sampling lesson (temperature).",
        intuition="Dividing logits by T < 1 stretches the gaps between them, so the biggest logit dominates. "
                  "T > 1 shrinks the gaps and flattens the distribution. Softmax only cares about differences "
                  "between logits, so subtracting the max changes nothing mathematically and prevents overflow.",
        hints=[
            "Handle temperature == 0 separately: it is argmax, not a division by zero.",
            "exp(1000) overflows a float. What can you subtract from every logit without changing the result?",
            "Subtract max(z) after scaling, exponentiate, then normalize by the sum.",
        ],
        brute_force="Directly computing `exp(x/T)` works for small logits but returns `inf`/`nan` for large ones.",
        approach="1. If T == 0 return one-hot at the first argmax.\n2. Scale: `z = x / T`.\n"
                 "3. Stabilize: `z -= max(z)`, so the largest term is `exp(0) = 1`.\n4. `p = exp(z) / sum(exp(z))`.\n\n"
                 "Dry run `[1,2], T=0.5`: z = [2,4], minus max gives [-2,0], exp gives [0.135, 1], normalized gives [0.119, 0.881].",
        complexity="O(n) time and O(n) space for n logits.",
        pitfalls="- Overflow without max-subtraction.\n- Multiplying by T instead of dividing.\n"
                 "- For ties at T=0 the brief asks for the first index.",
        follow_up="Implement sampling with a seeded RNG from these probabilities, or return log-probabilities "
                  "with log-sum-exp for even better numerical behaviour.",
    ),
),
# ---------------------------------------------------------------- top-k + top-p
dict(
    id="aie-top-k-top-p",
    title="Top-k and Top-p (Nucleus) Filtering",
    difficulty="Medium",
    pattern="Sampling",
    entry="filter_probs",
    compare="float",
    description=r"""
Given a next-token probability distribution `probs` (non-negative, sums to 1), apply **top-k** and then
**top-p** filtering, and return the **renormalised** distribution (same length, filtered tokens get `0.0`).

Order tokens by probability **descending**, breaking ties by **smaller index first**.

1. **Top-k**: if `k > 0`, keep only the first `k` tokens in that order (if `k >= len(probs)` keep all).
   `k == 0` means "no top-k". Renormalise what is kept.
2. **Top-p**: on the (renormalised) result of step 1, walk tokens in the same order, accumulating
   probability, and keep the **smallest prefix whose cumulative probability is ≥ p**. Use a tolerance:
   treat `cum >= p - 1e-9` as reaching p. If `p >= 1`, keep everything left after step 1.
3. Renormalise the kept tokens so they sum to 1.

**Example:** `probs=[0.5,0.25,0.12,0.08,0.05], k=0, p=0.8` → keep 0.5, 0.25, 0.12 (cum 0.87 ≥ 0.8)
→ `[0.5747, 0.2874, 0.1379, 0.0, 0.0]`

**Example:** same probs, `k=2, p=1.0` → `[0.6667, 0.3333, 0, 0, 0]`
""",
    starter='''def filter_probs(probs, k, p):
    pass
''',
    solution='''def filter_probs(probs, k, p):
    n = len(probs)
    order = sorted(range(n), key=lambda i: (-probs[i], i))
    keep = order if k <= 0 or k >= n else order[:k]
    total = sum(probs[i] for i in keep)
    q = {i: probs[i] / total for i in keep}
    if p < 1:
        chosen, cum = [], 0.0
        for i in keep:
            chosen.append(i)
            cum += q[i]
            if cum >= p - 1e-9:
                break
        keep = chosen
    total = sum(q[i] for i in keep)
    out = [0.0] * n
    for i in keep:
        out[i] = q[i] / total
    return out
''',
    tests=[
        [[0.5, 0.25, 0.12, 0.08, 0.05], 0, 0.8],
        [[0.5, 0.25, 0.12, 0.08, 0.05], 2, 1.0],
        [[0.5, 0.25, 0.12, 0.08, 0.05], 3, 0.6],
        [[0.05, 0.08, 0.5, 0.12, 0.25], 0, 0.9],
        [[0.25, 0.25, 0.25, 0.25], 0, 0.5],
        [[0.25, 0.25, 0.25, 0.25], 3, 0.9],
        [[1.0], 5, 0.9],
        [[0.6, 0.4], 0, 0.6],
        [[0.6, 0.4], 0, 0.01],
        [[0.1, 0.2, 0.3, 0.4], 10, 1.0],
        [[0.1, 0.2, 0.3, 0.4], 1, 0.5],
        [_rand_probs(30), 10, 0.9],
        [_rand_probs(100), 0, 0.95],
        [_rand_probs(100), 50, 0.5],
    ],
    examples=2,
    wrong_solutions=[
        # top-p applied on original probs (not renormalised after top-k)
        '''def filter_probs(probs, k, p):
    n = len(probs)
    order = sorted(range(n), key=lambda i: (-probs[i], i))
    keep = order if k <= 0 or k >= n else order[:k]
    if p < 1:
        chosen, cum = [], 0.0
        for i in keep:
            chosen.append(i); cum += probs[i]
            if cum >= p - 1e-9: break
        keep = chosen
    total = sum(probs[i] for i in keep)
    out = [0.0] * n
    for i in keep: out[i] = probs[i] / total
    return out
''',
        # stops BEFORE reaching p (keeps tokens while cum < p)
        '''def filter_probs(probs, k, p):
    n = len(probs)
    order = sorted(range(n), key=lambda i: (-probs[i], i))
    keep = order if k <= 0 or k >= n else order[:k]
    total = sum(probs[i] for i in keep)
    q = {i: probs[i] / total for i in keep}
    if p < 1:
        chosen, cum = [], 0.0
        for i in keep:
            if cum + q[i] > p and chosen: break
            chosen.append(i); cum += q[i]
        keep = chosen
    total = sum(q[i] for i in keep)
    out = [0.0] * n
    for i in keep: out[i] = q[i] / total
    return out
''',
    ],
    guide=dict(
        prereqs="Sorting with a custom key, cumulative sums, the sampling lesson.",
        intuition="Top-k fixes the number of candidates. Top-p fixes the probability mass, so it keeps few tokens "
                  "when the model is confident and many when it is unsure. Chaining them means top-p sees the "
                  "distribution that top-k left behind.",
        hints=[
            "Sort indices, not values, so you can write results back into the right positions.",
            "After top-k, renormalise before measuring cumulative mass for top-p.",
            "Include the token that pushes the cumulative sum past p (smallest prefix reaching p).",
        ],
        brute_force="There is no meaningfully slower approach. The core is a sort plus a linear scan.",
        approach="1. `order = sorted(range(n), key=lambda i: (-probs[i], i))`.\n2. Truncate to k if 0 < k < n and renormalise.\n"
                 "3. If p < 1, walk `order` accumulating mass and stop after the first index where `cum >= p - 1e-9`.\n"
                 "4. Renormalise the kept set and scatter into a zero list.\n\nDry run `[0.5,.25,.12,.08,.05], p=.8`: cum = .5, .75, .87 → stop; kept mass .87 → .5/.87 = .5747.",
        complexity="O(n log n) for the sort, O(n) extra space.",
        pitfalls="- Forgetting to renormalise between the two filters.\n- Off-by-one: the boundary token must be kept.\n"
                 "- Float accumulation such as 0.1+0.2+0.3 = 0.6000000000000001, hence the tolerance.\n- Tie-breaking must be deterministic.",
        follow_up="Implement min-p (keep tokens with p ≥ min_p × p_max), or apply these filters to logits with -inf masking.",
    ),
),
# ---------------------------------------------------------------- beam search
dict(
    id="aie-beam-search",
    title="Greedy vs Beam Search on a Toy LM",
    difficulty="Medium",
    pattern="Sampling",
    entry="beam_search",
    compare="float",
    description=r"""
A toy language model is given as a **next-token table**: `table[context]` is a dict `{token: prob}`,
where `context` is the tokens generated so far joined by a single space (`""` at the start).

Implement `beam_search(table, beam_width, max_len)` returning `[best_tokens, best_logprob]` where the
score of a sequence is the **sum of natural-log probabilities** of its tokens.

Algorithm (follow exactly):
- Start with one active hypothesis: `([], 0.0)`.
- Repeat up to `max_len` steps while there are active hypotheses:
  - For each active hypothesis, look up `table.get(context)`. If missing or empty, the hypothesis is
    **finished as is**. Otherwise create one candidate per token with `prob > 0`.
  - Pool all candidates, sort by **(-logprob, tokens list)** and keep the top `beam_width`.
  - Kept candidates whose last token is `"<eos>"` become **finished**; the rest stay active.
- After the loop, any still-active hypotheses are also finished.
- Return the finished hypothesis with the highest logprob (ties: smallest tokens list in Python ordering).

`beam_width = 1` is greedy decoding. `<eos>` stays in the returned token list.

**Example:** with the classic trap table below, greedy picks `the` (0.5) but beam width 2 finds
`a dog <eos>` with total probability 0.4·0.9·1.0 = 0.36 > 0.5·0.4·1.0 = 0.2.
""",
    starter='''def beam_search(table, beam_width, max_len):
    pass
''',
    solution='''import math
def beam_search(table, beam_width, max_len):
    active = [([], 0.0)]
    finished = []
    for _ in range(max_len):
        if not active:
            break
        cands = []
        for seq, lp in active:
            dist = table.get(" ".join(seq))
            if not dist:
                finished.append((seq, lp))
                continue
            for tok, p in dist.items():
                if p > 0:
                    cands.append((seq + [tok], lp + math.log(p)))
        cands.sort(key=lambda c: (-c[1], c[0]))
        active = []
        for seq, lp in cands[:beam_width]:
            if seq[-1] == "<eos>":
                finished.append((seq, lp))
            else:
                active.append((seq, lp))
    finished.extend(active)
    best = min(finished, key=lambda c: (-c[1], c[0]))
    return [best[0], best[1]]
''',
    tests=[
        [{"": {"the": 0.5, "a": 0.4, "<eos>": 0.1},
          "the": {"cat": 0.4, "dog": 0.3, "<eos>": 0.3}, "the cat": {"<eos>": 1.0}, "the dog": {"<eos>": 1.0},
          "a": {"dog": 0.9, "<eos>": 0.1}, "a dog": {"<eos>": 1.0}}, 1, 5],
        [{"": {"the": 0.5, "a": 0.4, "<eos>": 0.1},
          "the": {"cat": 0.4, "dog": 0.3, "<eos>": 0.3}, "the cat": {"<eos>": 1.0}, "the dog": {"<eos>": 1.0},
          "a": {"dog": 0.9, "<eos>": 0.1}, "a dog": {"<eos>": 1.0}}, 2, 5],
        [{"": {"x": 0.6, "y": 0.4}, "x": {"<eos>": 0.5, "z": 0.5}, "y": {"<eos>": 1.0}, "x z": {"<eos>": 1.0}}, 1, 5],
        [{"": {"x": 0.6, "y": 0.4}, "x": {"<eos>": 0.5, "z": 0.5}, "y": {"<eos>": 1.0}, "x z": {"<eos>": 1.0}}, 3, 5],
        [{"": {"a": 1.0}, "a": {"a": 1.0}, "a a": {"a": 1.0}, "a a a": {"a": 1.0}}, 2, 3],
        [{"": {"hi": 0.7, "<eos>": 0.3}}, 2, 4],
        [{"": {"b": 0.5, "a": 0.5}, "a": {"<eos>": 1.0}, "b": {"<eos>": 1.0}}, 2, 3],
        [{"": {"<eos>": 0.2, "go": 0.8}, "go": {"left": 0.5, "right": 0.5}, "go left": {"<eos>": 0.9},
          "go right": {"<eos>": 0.95}}, 1, 6],
        [{"": {"<eos>": 0.2, "go": 0.8}, "go": {"left": 0.5, "right": 0.5}, "go left": {"<eos>": 0.9},
          "go right": {"<eos>": 0.95}}, 4, 6],
        [{"": {"p": 0.3, "q": 0.3, "r": 0.4}, "p": {"<eos>": 1.0}, "q": {"s": 1.0}, "q s": {"<eos>": 1.0},
          "r": {"t": 0.2, "u": 0.2, "v": 0.6}, "r v": {"<eos>": 0.5}}, 2, 5],
        [{"": {"p": 0.3, "q": 0.3, "r": 0.4}, "p": {"<eos>": 1.0}, "q": {"s": 1.0}, "q s": {"<eos>": 1.0},
          "r": {"t": 0.2, "u": 0.2, "v": 0.6}, "r v": {"<eos>": 0.5}}, 1, 5],
        [{"": {"m": 0.9, "n": 0.1, "zero": 0.0}, "m": {"<eos>": 0.1, "o": 0.9}, "n": {"<eos>": 1.0},
          "m o": {"<eos>": 0.05, "o2": 0.95}, "m o o2": {"<eos>": 0.05}}, 2, 2],
    ],
    examples=2,
    wrong_solutions=[
        # pure greedy regardless of beam width
        '''import math
def beam_search(table, beam_width, max_len):
    seq, lp = [], 0.0
    for _ in range(max_len):
        dist = table.get(" ".join(seq))
        if not dist: break
        tok, p = max(dist.items(), key=lambda kv: (kv[1], [-ord(c) for c in kv[0]]))
        seq = seq + [tok]; lp += math.log(p)
        if tok == "<eos>": break
    return [seq, lp]
''',
        # length-normalised score (average log prob) instead of sum
        '''import math
def beam_search(table, beam_width, max_len):
    active = [([], 0.0)]; finished = []
    for _ in range(max_len):
        if not active: break
        cands = []
        for seq, lp in active:
            dist = table.get(" ".join(seq))
            if not dist:
                finished.append((seq, lp)); continue
            for tok, p in dist.items():
                if p > 0: cands.append((seq + [tok], lp + math.log(p)))
        cands.sort(key=lambda c: (-c[1] / len(c[0]), c[0]))
        active = []
        for seq, lp in cands[:beam_width]:
            (finished if seq[-1] == "<eos>" else active).append((seq, lp))
    finished.extend(active)
    best = min(finished, key=lambda c: (-c[1] / max(1, len(c[0])), c[0]))
    return [best[0], best[1]]
''',
    ],
    guide=dict(
        prereqs="Log probabilities, sorting tuples, the sampling lesson (test-time compute, beam search).",
        intuition="Greedy commits to the locally best token and can walk into a dead end (`the` is likely but "
                  "its continuations are weak). Beam search keeps the B best partial sequences, so a slightly "
                  "worse first token with a much better continuation survives.",
        hints=[
            "Work in log space and add logprobs instead of multiplying probabilities.",
            "Pool candidates from every active beam before pruning to beam_width.",
            "A kept candidate ending in <eos> stops expanding but still competes at the end.",
        ],
        brute_force="Enumerate every path up to max_len and take the best. That is exponential in length, "
                    "which is exactly what beam search approximates.",
        approach="Maintain `active` and `finished`. Each step: expand active, pool, sort by `(-lp, seq)`, keep top B, "
                 "move `<eos>` endings to finished. At the end, merge active into finished and take the max.\n\n"
                 "Trap table: greedy gives `the`(.5) then `cat`(.4) then `<eos>` with total .2. "
                 "Beam 2 keeps `the`, `a`; next pool: `a dog`(.36), `the cat`(.2), … → `a dog <eos>` wins with .36.",
        complexity="O(max_len · B · V log(B·V)) for vocabulary V per context.",
        pitfalls="- Pruning per beam instead of over the pooled candidates.\n- Dropping finished hypotheses.\n"
                 "- Using probabilities directly (underflow for long sequences).",
        follow_up="Add length normalisation (average logprob) as discussed in the lesson and see how the chosen "
                  "sequence changes. Huyen notes this is how `best_of` picked outputs.",
    ),
),
# ---------------------------------------------------------------- perplexity
dict(
    id="aie-perplexity",
    title="Perplexity from Token Log-Probs",
    difficulty="Easy",
    pattern="Evaluation",
    entry="perplexity",
    compare="float",
    tolerance=1e-6,
    description=r"""
You evaluated a language model on several sequences. For each sequence you have the model's
**natural-log** probability for every token: `seqs = [[lp_1, lp_2, ...], ...]` (every sequence is non-empty).

Return `[corpus_ppl, per_sequence_ppl]` where

- per-sequence perplexity is $\exp\big(-\tfrac{1}{n}\sum_i \ln p_i\big)$ over that sequence's tokens;
- **corpus perplexity is token-weighted**: average the negative log-likelihood over **all tokens of all
  sequences together**, then exponentiate (it is *not* the mean of the per-sequence perplexities).

**Example:** `[[ln 0.5, ln 0.5], [ln 0.25]]` → per-sequence `[2.0, 4.0]`; corpus NLL = (0.693+0.693+1.386)/3
→ `exp(0.924) ≈ 2.5198`.
""",
    starter='''def perplexity(seqs):
    pass
''',
    solution='''import math
def perplexity(seqs):
    per = [math.exp(-sum(s) / len(s)) for s in seqs]
    total = sum(sum(s) for s in seqs)
    count = sum(len(s) for s in seqs)
    return [math.exp(-total / count), per]
''',
    tests=[
        [[[-0.6931471805599453, -0.6931471805599453], [-1.3862943611198906]]],
        [[[0.0, 0.0, 0.0]]],
        [[[-2.302585092994046]]],
        [[[-0.1, -0.2, -0.3], [-1.5], [-0.05, -0.05, -0.05, -0.05]]],
        [[[-10.0, -0.01], [-0.01, -0.01, -0.01, -0.01, -0.01]]],
        [[[-0.916, -0.693, -1.609, -0.357], [-0.511, -0.511, -2.303, -0.223]]],
        [[[round(-_g.uniform(0, 3), 4) for _ in range(_g.randint(1, 30))] for _ in range(20)]],
        [[[round(-_g.uniform(0, 0.5), 4) for _ in range(200)]]],
        [[[-5.0] * 3, [-0.001] * 300]],
        [[[-0.6931471805599453]] * 7],
    ],
    examples=2,
    wrong_solutions=[
        '''import math
def perplexity(seqs):
    per = [math.exp(-sum(s) / len(s)) for s in seqs]
    return [sum(per) / len(per), per]
''',
        '''import math
def perplexity(seqs):
    per = [2 ** (-sum(s) / len(s)) for s in seqs]
    total = sum(sum(s) for s in seqs); count = sum(len(s) for s in seqs)
    return [2 ** (-total / count), per]
''',
    ],
    guide=dict(
        prereqs="Language modeling metrics lesson: cross entropy, nats vs bits, perplexity.",
        intuition="Perplexity is exp(average negative log-likelihood per token). A corpus metric must weight every "
                  "token equally, so long sequences count more than short ones.",
        hints=["Natural logs mean you exponentiate with e, not 2.",
               "Corpus perplexity: sum all logprobs and divide by the total token count.",
               "Averaging per-sequence perplexities over-weights short sequences and is wrong."],
        brute_force="Already linear. The only trap is the aggregation.",
        approach="per = exp(-mean(seq)) for each seq; corpus = exp(-(sum of all lps)/(total tokens)).",
        complexity="O(T) for T total tokens.",
        pitfalls="- Mixing 2^H and e^H.\n- Averaging perplexities.\n- Sign errors: logprobs are ≤ 0, so negate.",
        follow_up="Convert to bits-per-token (divide NLL by ln 2) and to bits-per-byte given byte counts.",
    ),
),
# ---------------------------------------------------------------- ROUGE-L
dict(
    id="aie-rouge-l",
    title="ROUGE-L (LCS-based) Similarity",
    difficulty="Medium",
    pattern="Evaluation",
    entry="rouge_l",
    compare="float",
    description=r"""
Implement **ROUGE-L**, a lexical similarity metric based on the **longest common subsequence (LCS)**
of tokens.

Tokenise both strings by lowercasing and extracting `re.findall(r"[a-z0-9]+", text.lower())`.
Let `L = LCS(cand, ref)` on these token lists. Then

$$P = \frac{L}{|cand|},\qquad R = \frac{L}{|ref|},\qquad F_1 = \frac{2PR}{P+R}$$

Return `[P, R, F1]`. If either token list is empty, or `L == 0`, return `[0.0, 0.0, 0.0]`.

**Example:** `cand = "My cats eat the mice"`, `ref = "My cats scare the mice"` → LCS = 4 →
`[0.8, 0.8, 0.8]`.
""",
    starter='''def rouge_l(candidate, reference):
    pass
''',
    solution='''import re
def rouge_l(candidate, reference):
    a = re.findall(r"[a-z0-9]+", candidate.lower())
    b = re.findall(r"[a-z0-9]+", reference.lower())
    if not a or not b:
        return [0.0, 0.0, 0.0]
    prev = [0] * (len(b) + 1)
    for x in a:
        cur = [0]
        for j, y in enumerate(b, 1):
            cur.append(prev[j - 1] + 1 if x == y else max(prev[j], cur[j - 1]))
        prev = cur
    L = prev[-1]
    if L == 0:
        return [0.0, 0.0, 0.0]
    P, R = L / len(a), L / len(b)
    return [P, R, 2 * P * R / (P + R)]
''',
    tests=[
        ["My cats eat the mice", "My cats scare the mice"],
        ["Cats and mice fight all the time", "My cats scare the mice"],
        ["the mice scare my cats", "my cats scare the mice"],
        ["", "anything"],
        ["hello", ""],
        ["completely different", "nothing shared here"],
        ["The quick brown fox!!", "the QUICK brown fox"],
        ["a b c d e f", "a c e"],
        ["police killed the gunman", "the gunman killed police"],
        ["one two three two one", "one two one"],
        [" ".join(_g.choice("abcdefgh") for _ in range(120)), " ".join(_g.choice("abcdefgh") for _ in range(100))],
        ["it is 2024 and gpt-4 is out", "In 2024, GPT 4 was out"],
    ],
    examples=2,
    wrong_solutions=[
        # unigram overlap instead of LCS (ignores order)
        '''import re
def rouge_l(candidate, reference):
    a = re.findall(r"[a-z0-9]+", candidate.lower()); b = re.findall(r"[a-z0-9]+", reference.lower())
    if not a or not b: return [0.0, 0.0, 0.0]
    L = len(set(a) & set(b))
    if L == 0: return [0.0, 0.0, 0.0]
    P, R = L / len(a), L / len(b)
    return [P, R, 2 * P * R / (P + R)]
''',
        # longest common substring (contiguous) instead of subsequence
        '''import re
def rouge_l(candidate, reference):
    a = re.findall(r"[a-z0-9]+", candidate.lower()); b = re.findall(r"[a-z0-9]+", reference.lower())
    if not a or not b: return [0.0, 0.0, 0.0]
    best = 0
    prev = [0] * (len(b) + 1)
    for x in a:
        cur = [0]
        for j, y in enumerate(b, 1):
            cur.append(prev[j - 1] + 1 if x == y else 0)
        best = max(best, max(cur)); prev = cur
    if best == 0: return [0.0, 0.0, 0.0]
    P, R = best / len(a), best / len(b)
    return [P, R, 2 * P * R / (P + R)]
''',
    ],
    guide=dict(
        prereqs="Dynamic programming (LCS), the exact-evaluation lesson on lexical similarity.",
        intuition="LCS rewards tokens that appear in the same order, without requiring them to be adjacent. "
                  "That captures sentence-level structure better than bag-of-words overlap.",
        hints=["dp[i][j] = LCS of a[:i] and b[:j].",
               "If a[i-1]==b[j-1] then dp[i-1][j-1]+1, else max(dp[i-1][j], dp[i][j-1]).",
               "Keep only the previous row for O(|b|) memory."],
        brute_force="Enumerate all subsequences: exponential.",
        approach="Tokenise, run the LCS DP, compute P = L/|cand|, R = L/|ref| and their harmonic mean.",
        complexity="O(|a|·|b|) time, O(|b|) space.",
        pitfalls="- Confusing subsequence with substring.\n- Forgetting the lowercase and punctuation tokenisation.\n- Division by zero when L = 0.",
        follow_up="Implement BLEU-1 (clipped unigram precision with brevity penalty) and compare on paraphrases.",
    ),
),
# ---------------------------------------------------------------- Elo
dict(
    id="aie-elo-ratings",
    title="Elo Ratings from Pairwise Judgments",
    difficulty="Easy",
    pattern="Evaluation",
    entry="elo_ratings",
    compare="float",
    tolerance=1e-6,
    description=r"""
A Chatbot-Arena-style evaluation produced a sequence of matches. Compute **Elo** ratings.

`elo_ratings(models, matches, k)`:
- every model starts at **1000**;
- `matches` is a list of `[a, b, s]` processed **in order**, with `s = 1` (a wins), `0` (b wins) or `0.5` (tie);
- expected score $E_a = 1/(1 + 10^{(R_b - R_a)/400})$, $E_b = 1 - E_a$;
- update **both** players using ratings from **before** this match:
  $R_a \mathrel{+}= k(s - E_a)$, $R_b \mathrel{+}= k((1-s) - E_b)$.

Return the final ratings as a list in the order of `models`.

**Example:** `models=["A","B"], matches=[["A","B",1]], k=32` → `[1016.0, 984.0]`.
""",
    starter='''def elo_ratings(models, matches, k):
    pass
''',
    solution='''def elo_ratings(models, matches, k):
    r = {m: 1000.0 for m in models}
    for a, b, s in matches:
        ea = 1 / (1 + 10 ** ((r[b] - r[a]) / 400))
        eb = 1 - ea
        r[a], r[b] = r[a] + k * (s - ea), r[b] + k * ((1 - s) - eb)
    return [r[m] for m in models]
''',
    tests=[
        [["A", "B"], [["A", "B", 1]], 32],
        [["A", "B"], [["A", "B", 0.5]], 32],
        [["A", "B", "C"], [["A", "B", 1], ["B", "C", 1], ["A", "C", 1], ["C", "A", 0.5], ["B", "A", 1]], 32],
        [["x"], [], 16],
        [["A", "B"], [["A", "B", 1]] * 20, 32],
        [["A", "B"], [["B", "A", 0]] * 5, 10],
        [["A", "B", "C", "D"], [["A", "B", 1], ["C", "D", 0], ["A", "D", 0.5], ["B", "C", 1]], 24],
        [["m1", "m2", "m3", "m4", "m5"],
         [[_g.choice(["m1", "m2"]), _g.choice(["m3", "m4", "m5"]), _g.choice([0, 0.5, 1])] for _ in range(200)], 16],
        [["A", "B"], [["A", "B", 0]], 40],
        [["A", "B", "C"], [["C", "A", 1], ["C", "B", 1], ["A", "B", 0.5]] * 10, 32],
    ],
    examples=2,
    wrong_solutions=[
        # sequential update bug: B's expectation computed with A's NEW rating
        '''def elo_ratings(models, matches, k):
    r = {m: 1000.0 for m in models}
    for a, b, s in matches:
        ea = 1 / (1 + 10 ** ((r[b] - r[a]) / 400))
        r[a] += k * (s - ea)
        eb = 1 / (1 + 10 ** ((r[a] - r[b]) / 400))
        r[b] += k * ((1 - s) - eb)
    return [r[m] for m in models]
''',
        # wrong scale (natural exp / no 400 divisor)
        '''def elo_ratings(models, matches, k):
    r = {m: 1000.0 for m in models}
    for a, b, s in matches:
        ea = 1 / (1 + 10 ** ((r[b] - r[a]) / 100))
        r[a], r[b] = r[a] + k * (s - ea), r[b] + k * ((1 - s) - (1 - ea))
    return [r[m] for m in models]
''',
    ],
    guide=dict(
        prereqs="AI as a judge and comparative evaluation lesson.",
        intuition="Elo predicts how likely A is to beat B from their rating gap, then moves both ratings toward "
                  "the observed result. Upsets move ratings a lot and expected results move them a little.",
        hints=["Compute both expectations before changing any rating.",
               "E_b is just 1 - E_a.",
               "Total rating is conserved in every match: A's gain equals B's loss."],
        brute_force="This is a direct simulation. There is nothing to optimise.",
        approach="Loop over matches in order, compute E_a from the current ratings, then do a simultaneous update.",
        complexity="O(M) for M matches.",
        pitfalls="- Updating A first and then using A's new rating for B.\n- Using 10 vs e or a wrong divisor.\n- Forgetting ties (0.5).",
        follow_up="Elo depends on match order. Fit Bradley-Terry by maximum likelihood to get order-independent "
                  "ratings, which is what Chatbot Arena moved to.",
    ),
),
# ---------------------------------------------------------------- judge position bias
dict(
    id="aie-judge-position-bias",
    title="LLM-Judge Position-Bias Check",
    difficulty="Easy",
    pattern="Evaluation",
    entry="position_bias_report",
    compare="float",
    description=r"""
To check an AI judge for **position bias**, each pair of responses (A, B) was judged twice:

- `v1`: judge's verdict when **A is shown first**;
- `v2`: judge's verdict when **B is shown first**.

Each verdict is `"first"`, `"second"` or `"tie"` (which *position* won). Given `trials = [[v1, v2], ...]`,
return `[consistency, first_rate, decisions]`:

- map each verdict to a response: for `v1`, `"first"`→A, `"second"`→B; for `v2`, `"first"`→B,
  `"second"`→A; `"tie"`→tie.
- a trial is **consistent** if both mappings give the same result (A&A, B&B or tie&tie). Its decision
  is `"A"`, `"B"` or `"tie"`; otherwise the decision is `"inconsistent"`.
- `consistency` = consistent trials / trials.
- `first_rate` = fraction of **all individual verdicts** (2 per trial) that are `"first"`.
- If `trials` is empty return `[0.0, 0.0, []]`.

**Example:** `[["first","first"]]` → the judge picked A then B: inconsistent, and it always picks the first slot
→ `[0.0, 1.0, ["inconsistent"]]`.
""",
    starter='''def position_bias_report(trials):
    pass
''',
    solution='''def position_bias_report(trials):
    if not trials:
        return [0.0, 0.0, []]
    m1 = {"first": "A", "second": "B", "tie": "tie"}
    m2 = {"first": "B", "second": "A", "tie": "tie"}
    decisions, consistent, firsts = [], 0, 0
    for v1, v2 in trials:
        a, b = m1[v1], m2[v2]
        firsts += (v1 == "first") + (v2 == "first")
        if a == b:
            consistent += 1
            decisions.append(a)
        else:
            decisions.append("inconsistent")
    return [consistent / len(trials), firsts / (2 * len(trials)), decisions]
''',
    tests=[
        [[["first", "first"]]],
        [[["first", "second"]]],
        [[["second", "first"], ["tie", "tie"], ["first", "tie"]]],
        [[]],
        [[["first", "first"]] * 7 + [["first", "second"]] * 3],
        [[["second", "second"], ["second", "first"]]],
        [[["tie", "first"], ["tie", "second"], ["tie", "tie"]]],
        [[[_g.choice(["first", "second", "tie"]), _g.choice(["first", "second", "tie"])] for _ in range(300)]],
        [[["first", "second"], ["second", "first"], ["first", "second"], ["second", "first"]]],
        [[["first", "first"], ["second", "second"]]],
    ],
    examples=2,
    wrong_solutions=[
        # forgets to swap the mapping for the second ordering
        '''def position_bias_report(trials):
    if not trials: return [0.0, 0.0, []]
    m = {"first": "A", "second": "B", "tie": "tie"}
    d, c, f = [], 0, 0
    for v1, v2 in trials:
        f += (v1 == "first") + (v2 == "first")
        if m[v1] == m[v2]: c += 1; d.append(m[v1])
        else: d.append("inconsistent")
    return [c / len(trials), f / (2 * len(trials)), d]
''',
    ],
    guide=dict(
        prereqs="AI-as-a-judge biases (first-position bias vs human recency bias).",
        intuition="A bias-free judge's preference follows the *content*, so swapping the order flips the position "
                  "label but keeps the same winner. A judge that says 'first' both times is following the slot.",
        hints=["Translate positions into response identities separately for each ordering.",
               "In the swapped run, 'first' means B.",
               "first_rate counts verdicts, so divide by 2·n."],
        brute_force="A single pass over the trials is already optimal.",
        approach="Build two dictionaries, map v1 and v2, compare, then count.",
        complexity="O(n).",
        pitfalls="- Using the same mapping for both orders.\n- Dividing first_rate by n instead of 2n.\n- Empty input.",
        follow_up="Only keep consistent verdicts when computing win rates, or count an inconsistent pair as a tie, "
                  "as several judge frameworks do.",
    ),
),
# ---------------------------------------------------------------- QA exact match + F1
dict(
    id="aie-qa-exact-f1",
    title="QA Exact Match and Token F1",
    difficulty="Medium",
    pattern="Evaluation",
    entry="qa_scores",
    compare="float",
    description=r"""
Implement the SQuAD-style metrics for extractive question answering.

**Normalise** a string by: lowercasing; removing every character in `string.punctuation`; removing the
whole words `a`, `an`, `the`; and splitting on whitespace into tokens.

For a prediction and **one** reference:
- **EM** = 1 if the normalised token lists are equal, else 0.
- **F1**: count common tokens as a multiset (`Counter(p) & Counter(r)`). If either token list is empty,
  F1 = 1 if both are empty else 0. If there are no common tokens, F1 = 0. Otherwise
  precision = common/|p|, recall = common/|r|, F1 = 2PR/(P+R).

Each question can have several acceptable references: take the **max** EM and the **max** F1 over them.

`qa_scores(predictions, references)` (lists of equal length ≥ 1, `references[i]` is a list of strings)
returns `[100 * mean EM, 100 * mean F1]`.

**Example:** `predictions=["The Eiffel Tower!"], references=[["eiffel tower"]]` → `[100.0, 100.0]`.
""",
    starter='''import string
from collections import Counter

def qa_scores(predictions, references):
    pass
''',
    solution='''import string, re
from collections import Counter
def _norm(s):
    s = s.lower()
    s = "".join(ch for ch in s if ch not in set(string.punctuation))
    return [w for w in s.split() if w not in ("a", "an", "the")]
def _f1(p, r):
    if not p or not r:
        return float(p == r)
    common = sum((Counter(p) & Counter(r)).values())
    if common == 0:
        return 0.0
    P, R = common / len(p), common / len(r)
    return 2 * P * R / (P + R)
def qa_scores(predictions, references):
    em = f1 = 0.0
    for pred, refs in zip(predictions, references):
        p = _norm(pred)
        em += max(float(p == _norm(r)) for r in refs)
        f1 += max(_f1(p, _norm(r)) for r in refs)
    n = len(predictions)
    return [100 * em / n, 100 * f1 / n]
''',
    tests=[
        [["The Eiffel Tower!"], [["eiffel tower"]]],
        [["Paris, France"], [["Paris"]]],
        [["1975"], [["in 1975", "1975"]]],
        [["the the the"], [["a"]]],
        [["Marie Curie", "blue whale", "Mount Everest"], [["Marie Curie"], ["the blue whale"], ["K2"]]],
        [["New York New York"], [["New York"]]],
        [["", "x"], [[""], ["y"]]],
        [["Albert Einstein's theory"], [["theory of relativity", "Einstein's theory"]]],
        [["no overlap at all"], [["completely different words"]]],
        [["an apple a day"], [["Apple day"]]],
        [["Washington D.C."], [["Washington DC", "D.C."]]],
        [[" ".join(_g.choice(["red", "blue", "green", "the", "a"]) for _ in range(8)) for _ in range(40)],
         [[" ".join(_g.choice(["red", "blue", "green", "the"]) for _ in range(5))] for _ in range(40)]],
    ],
    examples=2,
    wrong_solutions=[
        # set intersection instead of multiset
        '''import string
def _n(s):
    s = "".join(c for c in s.lower() if c not in string.punctuation)
    return [w for w in s.split() if w not in ("a", "an", "the")]
def _f(p, r):
    if not p or not r: return float(p == r)
    c = len(set(p) & set(r))
    if c == 0: return 0.0
    P, R = c / len(p), c / len(r); return 2 * P * R / (P + R)
def qa_scores(predictions, references):
    em = f1 = 0.0
    for pred, refs in zip(predictions, references):
        p = _n(pred)
        em += max(float(p == _n(r)) for r in refs); f1 += max(_f(p, _n(r)) for r in refs)
    return [100 * em / len(predictions), 100 * f1 / len(predictions)]
''',
        # averages over references instead of max
        '''import string
from collections import Counter
def _n(s):
    s = "".join(c for c in s.lower() if c not in string.punctuation)
    return [w for w in s.split() if w not in ("a", "an", "the")]
def _f(p, r):
    if not p or not r: return float(p == r)
    c = sum((Counter(p) & Counter(r)).values())
    if c == 0: return 0.0
    P, R = c / len(p), c / len(r); return 2 * P * R / (P + R)
def qa_scores(predictions, references):
    em = f1 = 0.0
    for pred, refs in zip(predictions, references):
        p = _n(pred)
        em += sum(float(p == _n(r)) for r in refs) / len(refs); f1 += sum(_f(p, _n(r)) for r in refs) / len(refs)
    return [100 * em / len(predictions), 100 * f1 / len(predictions)]
''',
    ],
    guide=dict(
        prereqs="Exact evaluation lesson (exact match, normalisation, token F1), collections.Counter.",
        intuition="Exact match is strict: any extra word fails. Token F1 gives partial credit for overlapping "
                  "words. Normalisation stops trivial differences (case, punctuation, articles) from counting.",
        hints=["Write a normalise helper once and reuse it for both metrics.",
               "Counter(p) & Counter(r) keeps min counts, which gives multiset overlap.",
               "With several references, the prediction gets credit for its best match."],
        brute_force="Already linear in the text length.",
        approach="Normalise, compute EM and F1 against each reference, take the max per question, average, multiply by 100.",
        complexity="O(total tokens) per reference.",
        pitfalls="- Using sets (duplicates matter).\n- Removing 'a' as a substring instead of as a word.\n- Empty normalised strings.",
        follow_up="Add a 'contains' variant (prediction contains the reference) and compare how lenient it is.",
    ),
),
]
