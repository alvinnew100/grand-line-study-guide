# Sampling, structured outputs and the probabilistic nature of AI

> **Before this lesson:** you should know what a token, a vocabulary and a probability distribution are (see [From language models to foundation models](#/lesson/ai-eng/aie-rise)) and have seen softmax once (see [Training data, architecture and scale](#/lesson/ai-eng/aie-data-arch-scale)); it is explained again here. The demos use NumPy arrays, and each new operation is described.

## In plain words

Picture a bag of coloured marbles: 50 blue, 30 green, 19 red and 1 yellow. Reach in without looking and you will usually pull out blue, sometimes green, rarely yellow. A language model writes text in the same way. For every position it prepares a "bag" in which each possible next token has a share, then one token is drawn. Drawing from the bag is called **sampling**.

That is why the same question can get two different answers: you reached into the same bag twice. It is also why you have controls. One dial, **temperature**, changes how lopsided the bag is. Others, **top-k** and **top-p**, throw the rarest marbles away before you draw. These few settings explain a surprising amount of what people find puzzling about AI products: creativity, inconsistency, made-up facts, broken output formats and cost.

Why this matters for a job: these settings are parameters on every model API call you will ever write, and choosing them badly produces bugs that look mysterious ("it worked yesterday"). Interviewers ask about them constantly: what temperature does, how top-k differs from top-p, how to get reliable JSON out of a model, why models hallucinate.

A model does not output text. It outputs a probability distribution over its vocabulary, and something has to turn that distribution into a token. Huyen calls sampling one of the most underrated concepts in AI. This lesson covers sampling fundamentals, strategies (temperature, top-k, top-p, stopping), test-time compute, structured outputs, and the consequences of probabilistic outputs.

## 1. Sampling fundamentals

For each position, the model's final layer produces a vector of **logits**: one raw score per vocabulary token, higher meaning "more suitable here". Logits are not probabilities: they can be negative and do not sum to 1. **Softmax** converts them. In words: raise the constant $e \approx 2.718$ to the power of each logit, which makes every number positive, then divide each by the total so that they add up to 1. With $x_i$ the logit of token $i$ and $p_i$ its probability (the symbol $\sum_j$ means "add up over all tokens $j$"):

$$
p_i = \operatorname{softmax}(x)_i = \frac{e^{x_i}}{\sum_j e^{x_j}}
$$

Worked example with two tokens whose logits are 1 and 2: $e^1 = 2.72$ and $e^2 = 7.39$, total $10.11$, so the probabilities are $2.72/10.11 = 0.27$ and $7.39/10.11 = 0.73$.

Given the probabilities, there are two ways to choose:

- **Greedy sampling** (also called greedy decoding) always picks the most likely token. That is fine for classification but makes generated text boring and repetitive. Ask "What's your favorite color?" and you get "green" every time.
- **Sampling** draws the next token at random according to the distribution. If "red" has 30% probability, it is chosen 30% of the time.

## 2. Temperature

**Temperature**, written $T$, is a number you pass with your request. Every logit is divided by it before the softmax:

$$
p_i = \frac{e^{x_i/T}}{\sum_j e^{x_j/T}}
$$

Dividing by a number below 1 makes the logits larger and pushes them further apart, so the favourite pulls ahead. Dividing by a number above 1 squeezes them together, so the tokens become more nearly equal.

- $T<1$ sharpens the distribution, so the top token dominates. Outputs are more consistent and more boring.
- $T>1$ flattens it, so rare tokens get a chance. Outputs are more creative and riskier.
- $T\to0$ (T approaching zero) approaches greedy. Dividing by exactly zero is impossible, so in practice $T=0$ is implemented as *argmax*, meaning "pick the position of the largest value".

Huyen's example has two tokens with logits [1, 2]. At $T=1$ the probabilities are [0.27, 0.73], as computed above. At $T=0.5$ the logits become [2, 4]: $e^2 = 7.39$, $e^4 = 54.6$, total $61.99$, giving [0.12, 0.88]. The favourite went from 73% to 88%. A common recommendation is about **0.7 for creative use cases**, which balances creativity and predictability.

```python-run
import numpy as np
def softmax_t(logits, T):
    z = np.asarray(logits, float) / T
    z -= z.max()                      # numerical stability
    e = np.exp(z); return e / e.sum()
logits = [1.0, 2.0]
for T in [0.1, 0.5, 0.7, 1.0, 2.0, 10.0]:
    print(f"T={T:<4} -> {softmax_t(logits, T).round(3)}")
```

**Reading this Python line by line**

- `def softmax_t(logits, T):` defines a function taking a list of logits and a temperature.
- `np.asarray(logits, float) / T` turns the list into a NumPy array of decimals and divides every entry by `T` in one step.
- `z -= z.max()` subtracts the largest value from every entry. This does not change the final probabilities (the same factor cancels on top and bottom of the fraction) but keeps `np.exp` from producing numbers too large for the computer to hold.
- `e = np.exp(z); return e / e.sum()` is the softmax: exponentiate, then divide by the total.
- The loop prints the result for six temperatures. Output: at `T=0.1` the split is `[0. 1.]`, effectively greedy. At `T=1.0` it is `[0.269 0.731]`. At `T=10.0` it is `[0.475 0.525]`, close to a coin flip even though the model clearly preferred the second token. Temperature never changes which token is the favourite; it changes how often the favourite wins.

### Logprobs

Computers store decimals with limited precision (the storage scheme is called *floating point*). A number that is too close to zero cannot be represented and is rounded to exactly zero, an error called **underflow**. The probability of a whole sentence is the product of many small token probabilities, so it underflows easily. To avoid this, providers work with **logprobs**: the logarithm of each probability, $\log p$. The log of a number between 0 and 1 is negative ($\log 0.5 = -0.69$, $\log 0.01 = -4.6$), never underflows, and turns multiplication into addition. Logprobs are useful for judging how confident a classification is, for evaluation (perplexity, Module 3) and for debugging. Many providers return logprobs for only the top few tokens, or none at all, partly to make it harder for others to copy their models.

## 3. Top-k, top-p, min-p and stopping

Sampling from the full distribution occasionally draws a very unlikely token, and one absurd word can derail a whole answer. These strategies trim the candidate list first. After trimming, the surviving probabilities are divided by their new total so they add up to 1 again (this is called *renormalizing*).

- **Top-k.** Keep only the $k$ tokens with the largest logits, apply softmax to those, then sample. Since softmax now runs over $k$ values instead of 100,000, this also saves computation. Typical $k$ is 50–500. Smaller $k$ gives more predictable, less interesting text.
- **Top-p (nucleus sampling).** Sort tokens from most to least probable and keep adding them to the candidate set until their running total (the *cumulative* probability) reaches $p$, typically 0.9–0.95. The size of the set adapts to the situation: after a yes/no question two tokens may already cover 90%, while after "What's the meaning of life?" it may take hundreds. Huyen notes that top-p does not necessarily reduce softmax computation, but it works well in practice.
- **Min-p.** Keep only tokens whose probability exceeds a minimum threshold.
- **Stopping conditions.** Generation ends when the model emits the end-of-sequence token `<EOS>`, when it produces a *stop string* you chose, or when it reaches the maximum number of output tokens you set. Limits cut latency and cost. The risk is truncated output, such as JSON missing its closing brace.

A hand calculation before the demo. Take five tokens with probabilities 0.50, 0.25, 0.12, 0.08, 0.05. Top-k with $k=2$ keeps 0.50 and 0.25, which total 0.75, and renormalizes them to $0.50/0.75 = 0.667$ and $0.25/0.75 = 0.333$. Top-p with $p=0.8$ adds 0.50 (running total 0.50), then 0.25 (0.75), then 0.12 (0.87, which passes 0.8) and stops with three tokens.

```python-run
import numpy as np
probs = np.array([0.50, 0.25, 0.12, 0.08, 0.05])   # already sorted, sums to 1
tokens = ["yes", "maybe", "no", "perhaps", "never"]

def top_k(p, k):
    idx = np.argsort(-p)[:k]
    out = np.zeros_like(p); out[idx] = p[idx]; return out / out.sum()

def top_p(p, thr):
    order = np.argsort(-p); cum = np.cumsum(p[order])
    keep = order[: np.searchsorted(cum, thr - 1e-12) + 1]   # smallest prefix reaching thr
    out = np.zeros_like(p); out[keep] = p[keep]; return out / out.sum()

print("top-k=2  :", dict(zip(tokens, top_k(probs, 2).round(3))))
print("top-p=0.8:", dict(zip(tokens, top_p(probs, 0.8).round(3))))
print("top-p=0.95:", dict(zip(tokens, top_p(probs, 0.95).round(3))))
```

**Reading this Python line by line**

- `np.argsort(-p)` returns the positions of the entries of `p` ordered from largest to smallest (the minus sign reverses NumPy's default ascending order). `[:k]` keeps the first `k` positions.
- `out = np.zeros_like(p); out[idx] = p[idx]` builds an all-zero array of the same length and copies in only the kept probabilities. `out / out.sum()` renormalizes.
- In `top_p`, `np.cumsum(p[order])` is the running total of the sorted probabilities: `[0.50, 0.75, 0.87, 0.95, 1.00]`.
- `np.searchsorted(cum, thr)` finds the first position where the running total reaches the threshold; `+ 1` turns a position into a count. The tiny `1e-12` guards against rounding errors when the total lands exactly on the threshold.
- `dict(zip(tokens, ...))` pairs each token name with its new probability for printing.
- Output: `top-k=2` leaves `yes` 0.667 and `maybe` 0.333, everything else 0. `top-p=0.8` keeps three tokens (`yes` 0.575, `maybe` 0.287, `no` 0.138). `top-p=0.95` keeps four and drops only `never`. These match the hand calculation.

On a hosted model you do not write this code; you pass the settings with the request. A static example of how that looks:

```python
reply = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Name a colour."}],
    temperature=0.2,     # sharpen the distribution: near-greedy
    top_p=0.9,           # nucleus sampling threshold
    max_tokens=5,        # stopping condition: at most 5 output tokens
    seed=42,             # ask for repeatable randomness where supported
)
```

> [!TIP]
> When outputs must be consistent (extraction, classification, evaluation), use low temperature and fix the other sampling variables. For brainstorming and creative writing, raise temperature or top-p. Change one knob at a time, and evaluate the effect.

## 4. Test-time compute

"Test time" is another name for inference: the moment the model is used, as opposed to trained. Instead of one response per query, you can generate several and pick the best. Spending extra computation at that moment to get a better answer is **test-time compute**.

- **Best-of-N.** Sample N outputs independently and select the best.
- **Beam search.** Build the answer token by token while keeping a fixed number B of the most promising partial answers (the *beams*) at each step, extending each and discarding the rest, instead of sampling whole answers independently.
- **Diversify.** Using different sampling settings for different candidates increases the chance that one is good.

How do you choose the winner?

- **Highest probability.** The probability of a sequence is the product of its token probabilities, so in logprobs it is a sum. Every extra token adds another negative number, so a longer answer always has a lower sum, however good it is. To avoid penalizing length, use the **average logprob**: the sum divided by the number of tokens. Worked example: a 2-token answer with token probabilities 0.9 and 0.95 has logprobs $-0.105$ and $-0.051$, sum $-0.156$, average $-0.078$. Huyen notes this is how OpenAI's `best_of` setting chose outputs.
- **A reward model or verifier.** A *verifier* is a model trained to check whether an answer is correct. OpenAI trained verifiers for maths problems. With a verifier, a 100M-parameter model matched a 3B-parameter model without one (reported by Cobbe and colleagues in 2021), a thirtyfold saving in model size. DeepMind found that scaling test-time compute can beat scaling parameters.
- **Application heuristics.** A rule suited to your product: pick the shortest candidate, or the one that is valid SQL (the language used to query databases).
- **Self-consistency (majority vote).** Sample many answers and return the most common one. Google reported Gemini's MMLU score using 32 samples per question (the CoT@32 setting from the planning lesson).

Diminishing returns apply. OpenAI found that accuracy rose with the number of samples up to about 400 and then fell, because more candidates also means more chances to fool the verifier. Two outputs cost roughly twice as much as one.

```python-run
# Selecting among candidates by average log-probability (length-normalized).
import math
cands = {
    "Paris.":                              [math.log(0.9), math.log(0.95)],
    "The capital of France is Paris.":     [math.log(0.8)] + [math.log(0.97)] * 6,
    "Lyon.":                               [math.log(0.05), math.log(0.95)],
}
for text, lps in cands.items():
    print(f"{text:35s} sum={sum(lps):7.3f}  avg={sum(lps)/len(lps):7.3f}")
print("\nSum favours the short answer; average logprob judges per-token confidence instead.")
```

What this demo does: `cands` is a dictionary mapping three candidate answers to the list of their token logprobs (`math.log(0.9)` is the logprob of a token that had 90% probability; `[math.log(0.97)] * 6` repeats one value six times). The loop prints each candidate's sum and average. The short "Paris." has sum $-0.157$ and average $-0.078$. The full sentence has a lower sum, $-0.406$, because it has seven tokens, yet its average, $-0.058$, is the best of the three: per token, the model was most confident in it. "Lyon." scores worst on both, because its first token had only 5% probability.

## 5. Structured outputs

**Structured output** is output that follows a strict format a program can read, as opposed to free prose. Production applications often need it: **JSON** (a widely used text format of named fields in curly braces, such as `{"name": "Ada", "age": 36}`) to hand to other code, SQL or regex (a pattern-matching notation) generated from plain language, or a classification into fixed labels. If your code expects JSON and the model replies "Sure! Here is the JSON you asked for: ...", the program crashes. Huyen lists techniques across the stack, from cheapest to most involved:

1. **Prompting.** State the format in the instructions and show examples. This is easy but gives no guarantee. You can use a second prompt or an AI judge to validate or fix the output, which adds cost and latency.
2. **Post-processing.** Fix the output with ordinary code after the model returns it. Models make *predictable* mistakes, such as a missing closing bracket or extra prose around the JSON, and short repair scripts work well. LinkedIn wrote a forgiving parser for YAML (another structured text format) that raised correct outputs from 90% to 99.99%. YAML uses fewer brackets and quotes than JSON, so it takes fewer tokens.
3. **Constrained sampling.** At each step, before sampling, remove (*mask out*) every token that would break the format, so only valid continuations can be drawn. If the output so far is `{"age": `, the next token must begin a number, so every other token's probability is set to zero. The allowed formats are described by a *grammar*, a formal set of rules for what may follow what. This guarantees correct syntax but needs a grammar per format and slows each token slightly. Some researchers argue the effort is better spent training models to follow instructions.
4. **Finetuning.** Train on examples in the desired format. This is the most reliable general approach. You can also change the architecture, for example replacing the vocabulary-sized output layer with a **classifier head**, a small output layer that has exactly one output per label, so the model cannot produce anything except one of the N labels.

Model providers bundle these techniques into API features: JSON mode, function calling and structured output. JSON mode guarantees valid JSON, not that the *contents* are correct, and a stopping condition can still cut it off in the middle.

Post-processing is often a few lines. The demo repairs two typical faults: prose wrapped around the JSON, and a missing closing brace.

```python-run
import json

def repair(text):
    start = text.find("{")                 # where the JSON begins
    if start == -1:
        return None
    body = text[start:]
    end = body.rfind("}")
    body = body[: end + 1] if end != -1 else body + "}"   # cut trailing prose, or close the brace
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        return None

for raw in ['{"city": "Hanoi", "temp": 31}',
            'Sure! Here you go: {"city": "Hanoi", "temp": 31} Hope that helps.',
            '{"city": "Hanoi", "temp": 31',
            'I cannot answer that.']:
    print(repair(raw))
```

`text.find("{")` returns the position of the first opening brace, or -1 when there is none. `rfind("}")` finds the last closing brace. `json.loads` converts JSON text into a Python dictionary and raises `JSONDecodeError` when the text is invalid; the `try`/`except` turns that failure into `None`. Output: the first three inputs all print `{'city': 'Hanoi', 'temp': 31}`, and the last prints `None`, the signal to retry the request.

> [!INTERVIEW]
> **"How do you guarantee an LLM returns valid JSON?"** Combine layers: a clear schema and examples in the prompt, the provider's structured-output or JSON mode (constrained decoding), a validating parser with repair logic and a retry policy, and, if failures persist at scale, finetuning on correctly formatted examples. Mention that valid syntax does not mean valid content, so validate against a schema and business rules.

## 6. The probabilistic nature of AI

If a model thinks Vietnamese cuisine is the best with 70% probability and Italian with 30%, it will answer "Vietnamese" 70% of the time. That is great for creativity and painful for everything else. Two symptoms follow.

### Inconsistency

- **Same input, different outputs.** Huyen asked the same essay-scoring prompt twice and got 3/5 and then 5/5. Mitigations: **cache** answers (store each answer the first time and return the stored copy when the same question comes again), fix temperature, top-p and top-k, and fix the **seed**. A computer's "random" numbers come from a formula started from a number called the seed; the same seed gives the same sequence of draws. Even then, different hardware can round calculations slightly differently and change outputs, and with API providers you may not control the hardware.
- **Slightly different input, very different output.** A capitalized letter changes the answer. Fixed sampling variables do not help here. Better prompts (Module 5) and memory systems (Module 6) do.

### Hallucination

A **hallucination** is a response that is not grounded in facts: it reads fluently and confidently but is false or invented. A law firm was fined in June 2023 for submitting court filings that cited cases ChatGPT had made up. Hallucination in text generation was documented as early as 2016. Sampling randomness alone does not explain it, because models state falsehoods even at temperature zero. Huyen presents two hypotheses:

1. **Self-delusion (proposed by Ortega and colleagues at DeepMind in 2021).** A model cannot tell the tokens it generated from the facts it was given. If it produces a slightly wrong token, it treats that token as true and builds on it. This is the "snowballing hallucinations" effect, where an early wrong assumption propagates. Huyen gives an example of a model describing an image of a shampoo bottle as a milk bottle and then continuing about milk. Zhang et al. (2023) proposed training to detect and correct this.
2. **Mismatched knowledge (John Schulman, OpenAI).** During SFT, models imitate labeler-written answers. If a labeler's answer uses knowledge the model lacks, the model learns to produce confident answers it cannot support, that is, to hallucinate. Proposed fixes include verification (asking the model to cite sources) and better reward functions that punish made-up content.

Practical mitigations at the application level: give the model the context it needs (RAG), ask it to answer *only* from that context and to say "I don't know", prefer concise answers (fewer tokens means fewer chances to go wrong), and evaluate factual consistency (Module 4).

> [!WARNING]
> No amount of sampling configuration makes a model deterministic and truthful. Design products assuming some outputs will be wrong: show sources, keep humans in the loop for high-stakes actions, and monitor.

## Summary

- Models output logits. Softmax turns them into probabilities, and sampling picks tokens. Greedy decoding is consistent but dull.
- **Temperature** scales logits. **Top-k** keeps a fixed number of candidates, **top-p** keeps a dynamic set by cumulative probability, and **stopping conditions** control length.
- **Test-time compute** (best-of-N, beam search, self-consistency, verifiers) trades cost for quality. Use average logprob or a verifier to select.
- **Structured outputs**: prompting, then post-processing, then constrained sampling, then finetuning.
- Probabilistic outputs cause **inconsistency** (fixable partly by fixing sampling variables and caching) and **hallucination** (explained by self-delusion and mismatched knowledge from SFT).

## Glossary

- **Logit**: the raw score a model gives each vocabulary token before conversion to a probability.
- **Softmax**: the function that turns logits into positive probabilities summing to 1.
- **Sampling**: choosing the next token at random according to its probability.
- **Greedy sampling (greedy decoding)**: always choosing the most probable token.
- **Temperature**: a number that divides the logits; below 1 sharpens the distribution, above 1 flattens it.
- **Argmax**: the position of the largest value in a list.
- **Underflow**: a number too close to zero being rounded to zero by the computer.
- **Logprob**: the logarithm of a probability; negative, safe from underflow, and additive.
- **Top-k**: keeping only the k most probable tokens before sampling.
- **Top-p (nucleus sampling)**: keeping the smallest set of top tokens whose probabilities add up to p.
- **Renormalize**: rescale kept probabilities so they add up to 1 again.
- **Stopping condition**: what ends generation: an end token, a stop string or a token limit.
- **Test-time compute**: extra computation spent while answering, such as generating several candidates.
- **Beam search**: generation that keeps the B best partial sequences at each step.
- **Self-consistency**: sampling many answers and returning the most frequent.
- **Verifier**: a model that checks whether an answer is correct.
- **Structured output**: output in a machine-readable format such as JSON.
- **Constrained sampling**: masking tokens that would violate a format so only valid ones can be chosen.
- **Classifier head**: an output layer with exactly one output per label.
- **Seed**: the starting number of a random-number generator; the same seed reproduces the same draws.
- **Cache**: a store of earlier results that can be returned again without recomputing.
- **Hallucination**: fluent, confident output that is not grounded in fact.

```quiz
[
  {"q": "Two tokens have logits [1, 2]. What happens to P(second token) when temperature drops from 1 to 0.5?", "options": ["Goes from 0.73 to 0.88", "Goes from 0.73 to 0.50", "Stays 0.73", "Goes from 0.27 to 0.88"], "answer": 0, "explain": "Lower temperature sharpens the distribution: softmax([2,4]) gives about [0.12, 0.88]."},
  {"q": "Why is top-p (nucleus) sampling often preferred to top-k?", "options": ["It is always cheaper", "It adapts the number of candidates to the context's uncertainty", "It is deterministic", "It removes the need for softmax"], "answer": 1, "explain": "Top-p keeps the smallest set whose cumulative probability reaches p, so a yes/no question keeps few tokens and an open question keeps many."},
  {"q": "Why do APIs expose logprobs rather than raw probabilities?", "options": ["Logprobs are smaller in JSON", "Very small probabilities underflow to zero; logs keep them representable", "Probabilities are secret", "Logprobs are faster to sample"], "answer": 1, "explain": "Log space avoids floating-point underflow and turns products of probabilities into sums."},
  {"q": "When choosing among candidate outputs by probability, why use average logprob instead of the sum?", "options": ["The sum can be positive", "The sum penalizes longer sequences because each token adds negative logprob", "Average is cheaper", "The API only returns averages"], "answer": 1, "explain": "Length normalization prevents always picking the shortest answer."},
  {"q": "Which structured-output technique guarantees syntactically valid output by masking invalid tokens during generation?", "options": ["Prompting", "Post-processing", "Constrained sampling", "Temperature = 0"], "answer": 2, "explain": "Constrained sampling filters logits so only grammar-valid tokens can be sampled."},
  {"q": "You fix temperature, top-p and seed, yet outputs still vary slightly across runs on an API. A plausible cause is…", "options": ["The tokenizer is random", "Hardware or numerical differences on the provider's side", "Logprobs are disabled", "Stopping conditions"], "answer": 1, "explain": "Huyen notes that different machines can execute the same computation differently, so fixed sampling settings don't guarantee 100% consistency."},
  {"q": "The 'self-delusion' hypothesis of hallucination says…", "options": ["Models hallucinate only at high temperature", "A model can't distinguish its own generated tokens from given facts, so early errors snowball", "Labelers lie on purpose", "Hallucinations are caused by tokenization"], "answer": 1, "explain": "Ortega et al. argue that the model treats its own (possibly wrong) outputs as evidence and builds on them."},
  {"q": "According to Schulman's hypothesis, how can SFT cause hallucinations?", "options": ["SFT uses too high a learning rate", "Labeler answers may contain knowledge the model lacks, teaching it to produce unsupported confident answers", "SFT removes the model's knowledge", "SFT data is always synthetic"], "answer": 1, "explain": "Imitating answers the model can't actually support teaches it to make things up."}
]
```

> **Source:** Huyen, *AI Engineering*, ch. 2 ("Sampling": fundamentals, strategies, test time compute, structured outputs, the probabilistic nature of AI).
