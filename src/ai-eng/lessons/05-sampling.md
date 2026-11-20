# Sampling, structured outputs and the probabilistic nature of AI

A model does not output text. It outputs a **probability distribution** over its vocabulary, and something has to turn that distribution into a token. That something is **sampling**. Huyen calls sampling one of the most underrated concepts in AI, because it explains a surprising number of behaviors: creativity, inconsistency, hallucination, malformed JSON, and how much an answer costs. This lesson covers sampling fundamentals, strategies (temperature, top-k, top-p, stopping), test-time compute, structured outputs, and the consequences of probabilistic outputs.

## 1. Sampling fundamentals

For each position, the model's final layer produces a **logit** vector, one number per vocabulary token. Logits are not probabilities: they can be negative and do not sum to 1. **Softmax** converts them:

$$
p_i = \operatorname{softmax}(x)_i = \frac{e^{x_i}}{\sum_j e^{x_j}}
$$

- **Greedy sampling** always picks the most likely token. That is fine for classification but makes generated text boring and repetitive. Ask "What's your favorite color?" and you get "green" every time.
- **Sampling** draws the next token according to the distribution. If "red" has 30% probability, it is chosen 30% of the time.

## 2. Temperature

**Temperature** $T$ divides logits before the softmax:

$$
p_i = \frac{e^{x_i/T}}{\sum_j e^{x_j/T}}
$$

- $T<1$ sharpens the distribution, so the top token dominates. Outputs are more consistent and more boring.
- $T>1$ flattens it, so rare tokens get a chance. Outputs are more creative and riskier.
- $T\to0$ approaches greedy. In practice $T=0$ is implemented as argmax.

Huyen's example has two tokens with logits [1, 2]. At $T=1$ the probabilities are [0.27, 0.73]. At $T=0.5$ they are [0.12, 0.88]. A common recommendation is about **0.7 for creative use cases**, which balances creativity and predictability.

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

### Logprobs

Probabilities of rare tokens can be tiny enough to **underflow** to zero in floating point, so providers expose **logprobs**, $\log p$. Logprobs are very useful for classification confidence, evaluation (perplexity, Module 3) and debugging. Many providers return logprobs for only the top tokens, or none at all, partly to make it harder to replicate their models.

## 3. Top-k, top-p, min-p and stopping

- **Top-k.** Keep only the $k$ largest logits, softmax over them, then sample. This cuts computation for large vocabularies. Typical $k$ is 50–500. Smaller $k$ gives more predictable, less interesting text.
- **Top-p (nucleus sampling).** Sort tokens by probability and keep the smallest set whose cumulative probability reaches $p$ (typically 0.9–0.95). The candidate set adapts to context: a yes/no question keeps 2 tokens, and "What's the meaning of life?" keeps many. Huyen notes that top-p does not necessarily reduce softmax computation, but it works well in practice.
- **Min-p.** Keep tokens whose probability exceeds a minimum threshold.
- **Stopping conditions.** Limit the maximum number of tokens or stop at a stop token or string (for example `<EOS>`). This cuts latency and cost. The risk is truncated output, such as JSON missing its closing brace.

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

> [!TIP]
> When outputs must be consistent (extraction, classification, evaluation), use low temperature and fix the other sampling variables. For brainstorming and creative writing, raise temperature or top-p. Change one knob at a time, and evaluate the effect.

## 4. Test-time compute

Instead of one response per query, generate several and pick the best. This is **test-time compute**.

- **Best-of-N.** Sample N outputs independently and select the best.
- **Beam search.** Keep the B most promising partial sequences at each step instead of sampling them all independently.
- **Diversify.** Varying sampling variables across candidates increases the chance that one is good.

How do you choose the winner?

- **Highest probability.** A sequence's probability is the product of its token probabilities, so in logprobs it is a sum. Longer sequences accumulate more negative logprob, so use the **average logprob** (sum divided by length) to avoid penalizing length. Huyen notes this is how OpenAI's `best_of` parameter chose outputs.
- **A reward model or verifier.** OpenAI trained verifiers for math. With a verifier, a 100M model matched a 3B model without one (Cobbe et al. 2021). DeepMind found that scaling test-time compute can beat scaling parameters.
- **Application heuristics.** Pick the shortest, or pick valid SQL.
- **Self-consistency (majority vote).** Sample many answers and return the most common. Google reported Gemini's MMLU score using 32 samples per question (CoT@32).

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

## 5. Structured outputs

Production applications often need structured output: JSON for downstream code, SQL or regex from natural language, classification into fixed labels. Huyen lists techniques across the stack, from cheapest to most involved:

1. **Prompting.** Instruct the format and show examples. This is easy but has no guarantee. You can use a second prompt or AI judge to validate or fix the output, which adds cost and latency.
2. **Post-processing.** Models make *predictable* mistakes, such as a missing closing bracket or extra prose around the JSON. Simple repair scripts work well. LinkedIn wrote a defensive YAML parser that raised correct outputs from 90% to 99.99%. YAML is less verbose than JSON, so it uses fewer tokens.
3. **Constrained sampling.** At each step, mask out tokens that would violate a grammar (JSON schema, regex), so only valid continuations are sampled. Formats are often given as context-free grammars. This guarantees syntax but needs a grammar per format and adds per-token overhead. Some researchers argue the effort is better spent training models to follow instructions.
4. **Finetuning.** Train on examples in the desired format. This is the most reliable general approach. You can also change the architecture, for example adding a **classifier head** to guarantee one of N labels.

Tool APIs from model providers (JSON mode, function calling, structured output) combine these techniques. JSON mode guarantees valid JSON, not that the *contents* are correct, and a stopping condition can still cut it off.

> [!INTERVIEW]
> **"How do you guarantee an LLM returns valid JSON?"** Combine layers: a clear schema and examples in the prompt, the provider's structured-output or JSON mode (constrained decoding), a validating parser with repair logic and a retry policy, and, if failures persist at scale, finetuning on correctly formatted examples. Mention that valid syntax does not mean valid content, so validate against a schema and business rules.

## 6. The probabilistic nature of AI

If a model thinks Vietnamese cuisine is the best with 70% probability and Italian with 30%, it will answer "Vietnamese" 70% of the time. That is great for creativity and painful for everything else. Two symptoms follow.

### Inconsistency

- **Same input, different outputs.** Huyen asked the same essay-scoring prompt twice and got 3/5 and then 5/5. Mitigations: cache answers, fix temperature, top-p and top-k, and fix the **seed**. Even then, hardware differences can change outputs, and with API providers you may not control the hardware.
- **Slightly different input, very different output.** A capitalized letter changes the answer. Fixed sampling variables do not help here. Better prompts (Module 5) and memory systems (Module 6) do.

### Hallucination

Hallucination is a response not grounded in facts. A law firm was fined in June 2023 for submitting fictitious, ChatGPT-generated case citations. Hallucination in text generation was documented as early as 2016. Sampling randomness alone does not explain it. Huyen presents two hypotheses:

1. **Self-delusion (Ortega et al., DeepMind 2021).** A model cannot tell the tokens it generated from the facts it was given. If it produces a slightly wrong token, it treats that token as true and builds on it. This is the "snowballing hallucinations" effect, where an early wrong assumption propagates. Huyen gives an example of a model describing an image of a shampoo bottle as a milk bottle and then continuing about milk. Zhang et al. (2023) proposed training to detect and correct this.
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
