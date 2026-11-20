# Language modeling metrics: from entropy to perplexity

Huyen opens her evaluation chapters with a warning: the more AI is used, the more chances there are for catastrophic failure. She mentions a man who died by suicide after a chatbot encouraged him, lawyers who submitted AI-invented evidence, and Air Canada being ordered to honor a refund policy its chatbot made up. Evaluating foundation models is **harder** than evaluating classic ML models, for several reasons:

- The more intelligent a model, the harder it is to evaluate. Anyone can spot a nonsensical first-grade math answer, but checking a PhD-level proof or a long summary takes experts and time.
- **Open-ended outputs** cannot be compared against a fixed list of correct answers.
- Most models are **black boxes**. You do not know the architecture, data or training process.
- **Public benchmarks saturate** quickly. GLUE (2018) saturated within a year and was replaced by SuperGLUE (2019).
- Evaluation must cover new **capabilities** as well as existing tasks.

Despite this, evaluation investment lags. Huyen notes that evaluation tooling was one of the least represented categories among the repos she surveyed. This module builds the vocabulary. This lesson covers the metrics used to train and compare language models: **entropy, cross entropy, bits-per-character/byte and perplexity**.

## 1. Entropy: how much information per token

**Entropy** measures, on average, how much information a token carries, or equivalently how hard the next token is to predict. For a distribution $P$ over tokens:

$$
H(P) = -\sum_{x} P(x)\log_2 P(x) \quad\text{(bits)}
$$

Huyen's example: to describe positions in a square you can use two tokens (upper/lower) or four tokens (upper-left, upper-right, lower-left, lower-right). With two equally likely tokens you need 1 bit, and with four you need 2 bits. **More entropy means more information per token and more uncertainty about what comes next.** A perfectly predictable language has entropy 0.

## 2. Cross entropy: how well a model predicts the data

A language model learns a distribution $Q$ that approximates the true data distribution $P$. Its **cross entropy** on the data is:

$$
H(P, Q) = -\sum_x P(x)\log Q(x) = H(P) + D_{KL}(P\,\|\,Q)
$$

It has two parts:

- $H(P)$, the data's inherent unpredictability, which no model can remove.
- $D_{KL}(P\|Q)$, the **KL divergence**: how far the model's distribution is from the truth.

If the model learns the data perfectly, $Q=P$, the KL term is 0 and cross entropy equals entropy. Training a language model *minimizes cross entropy* on the training data. In practice, on a sequence of tokens $x_1..x_n$:

$$
H \approx -\frac{1}{n}\sum_{i=1}^{n} \log Q(x_i \mid x_{<i})
$$

which is simply the **average negative log-likelihood** of the observed tokens.

## 3. Bits-per-character and bits-per-byte

Cross entropy per *token* depends on the tokenizer. One model's token is not another's, so comparing them per token is unfair. Two normalizations help:

- **BPC (bits-per-character)**: if a model's cross entropy is 6 bits per token and tokens average 2 characters, BPC is 6/2 = 3.
- **BPB (bits-per-byte)**: characters vary in byte length (UTF-8), so normalizing by bytes is more comparable. With 3 BPC on ASCII text, where each character is 1 byte of 8 bits, BPB is 3. A BPB of 3.43 means the model can compress 8 bits into 3.43, about 2.33× compression. This links language modeling to **compression**: a better predictor is a better compressor.

## 4. Perplexity

**Perplexity (PPL)** is the exponential of (cross) entropy:

$$
\text{PPL}(P) = 2^{H(P)}, \qquad \text{PPL}(P,Q) = 2^{H(P,Q)}\ \text{(bits)}\qquad\text{or}\qquad e^{H(P,Q)}\ \text{(nats)}
$$

Interpretation: perplexity is the effective number of equally likely choices the model is hesitating between at each step. A model that has perfectly learned the 4-position square has cross entropy 2 bits and perplexity $2^2 = 4$. Frameworks such as PyTorch and TensorFlow use natural logs (**nats**), so perplexity is $e^{\text{loss}}$. Because bits and nats get mixed up, many people report perplexity rather than cross entropy.

Computed from token logprobs (natural log):

$$
\text{PPL} = \exp\!\Big(-\frac{1}{n}\sum_{i=1}^{n}\ln Q(x_i\mid x_{<i})\Big)
$$

```python-run
import numpy as np
# Perplexity from per-token log-probabilities (natural log), as returned by an API.
logprobs = np.log([0.5, 0.25, 0.9, 0.1, 0.6])
nll = -logprobs.mean()
print(f"avg NLL (cross entropy) = {nll:.4f} nats = {nll/np.log(2):.4f} bits")
print(f"perplexity = e^H = {np.exp(nll):.4f}  (same as 2^bits = {2**(nll/np.log(2)):.4f})")

# Uniform guess over a vocabulary of V tokens has perplexity exactly V
V = 50_000
print("uniform model over 50k vocab -> PPL", np.exp(-np.log(1/V)))
```

### Rules of thumb (Huyen)

What counts as a "good" perplexity depends on the data and on how it was computed:

- **More structured data gives lower perplexity.** HTML is more predictable than prose: after `<head>` comes `</head>`.
- **A bigger vocabulary gives higher perplexity.** Character-level perplexity is lower than word-level. A children's book is lower than *War and Peace*.
- **A longer context gives lower perplexity.** Shannon conditioned on up to 10 previous tokens. Modern models condition on thousands.

Perplexities as low as 3 are not unusual. That is like a 1-in-3 guess over a vocabulary of tens of thousands, which is remarkable.

### What perplexity is useful for

1. **A proxy for capability.** Bigger GPT-2 models had consistently lower perplexity across datasets (Table 3-1: on LAMBADA, PPL fell from 35.13 for 117M to 8.63 for 1.5B parameters). Huyen notes that many providers have stopped reporting perplexity.
2. **Data contamination detection.** Unusually low perplexity on a benchmark suggests the model saw it during training (Module 4).
3. **Deduplication and data quality.** Add new training data only when its perplexity is high, since low perplexity means the model already "knows" it. Very high perplexity can flag gibberish or unusual text, which helps with **anomaly detection**.

> [!WARNING]
> Perplexity is a poor proxy for **post-trained** models. SFT and RLHF teach a model to produce responses people prefer, not to predict text, so perplexity often goes *up* after post-training. Quantization can also shift perplexity unexpectedly. Use perplexity mainly for base models, data work and relative comparisons with the same tokenizer and setup.

> [!NOTE]
> To compute a text's perplexity with a model, you need the probability (logprob) of each token given the previous ones. Many commercial APIs expose few or no logprobs, which limits these techniques to models you host or APIs that return full logprobs.

## 5. Worked example: comparing two models

Model A assigns probabilities [0.4, 0.5, 0.2, 0.7] to the 4 tokens of a test sentence, and Model B assigns [0.6, 0.6, 0.1, 0.8].

- A: mean NLL = −(ln .4 + ln .5 + ln .2 + ln .7)/4 = (0.916 + 0.693 + 1.609 + 0.357)/4 ≈ 0.894, so PPL ≈ $e^{0.894}$ ≈ 2.44.
- B: (0.511 + 0.511 + 2.303 + 0.223)/4 ≈ 0.887, so PPL ≈ 2.43.

B is better on three tokens but badly wrong on one. Because perplexity is a *geometric* mean of inverse probabilities, a single confident mistake costs a lot. That is why very low-probability tokens hurt perplexity disproportionately.

```python-run
import numpy as np
def ppl(probs): return float(np.exp(-np.mean(np.log(probs))))
print("A:", round(ppl([0.4, 0.5, 0.2, 0.7]), 4))
print("B:", round(ppl([0.6, 0.6, 0.1, 0.8]), 4))
print("B with 0.1 -> 0.01:", round(ppl([0.6, 0.6, 0.01, 0.8]), 4))
```

> [!INTERVIEW]
> **"What's the relationship between cross-entropy loss and perplexity, and what's a perplexity of 1?"** Perplexity is exp(cross entropy) in nats, or 2^(cross entropy) in bits. A perplexity of 1 means the model assigns probability 1 to every correct token, so it predicts perfectly (cross entropy 0). A uniform model over V tokens has perplexity V. Follow-up: perplexity is only comparable across models with the same tokenizer and evaluation context. Otherwise use bits-per-byte.

## Pitfalls

- Comparing perplexities across tokenizers or context lengths.
- Mixing bits and nats ($2^H$ vs $e^H$).
- Treating a chat model's high perplexity as low quality. It reflects post-training.
- Forgetting that perplexity measures prediction, not truthfulness, helpfulness or safety.

## Summary

- **Entropy** is the information per token, or the inherent unpredictability of the data.
- **Cross entropy** = entropy + KL divergence. It is what language model training minimizes, and in practice it is the average negative log-likelihood per token.
- **BPC/BPB** normalize away tokenizer differences, and BPB connects to compression.
- **Perplexity** = exp(cross entropy): the effective number of choices. Lower is better. Structured data, smaller vocabularies and longer contexts lower it.
- Uses: capability proxy for base models, contamination detection, data dedup and filtering, anomaly detection. It is less meaningful for post-trained models.

```quiz
[
  {"q": "A model's cross entropy on a dataset is 3 bits per token. Its perplexity is…", "options": ["3", "6", "8", "9"], "answer": 2, "explain": "PPL = 2^H = 2^3 = 8."},
  {"q": "Cross entropy H(P,Q) can be decomposed as…", "options": ["H(Q) - H(P)", "H(P) + KL(P||Q)", "KL(Q||P) only", "H(P) × H(Q)"], "answer": 1, "explain": "Cross entropy is the data's entropy plus the KL divergence from the model's distribution to the true one."},
  {"q": "PyTorch reports a validation loss of 2.0 (natural log). Perplexity is about…", "options": ["4.0", "7.39", "2.0", "100"], "answer": 1, "explain": "With nats, PPL = e^2 ≈ 7.39."},
  {"q": "Why might BPB be preferred over per-token cross entropy for comparing models?", "options": ["It is always smaller", "It is independent of each model's tokenizer", "It ignores rare tokens", "It measures latency"], "answer": 1, "explain": "Tokens differ across models. Normalizing by bytes makes the comparison fair."},
  {"q": "Which data would you expect a model to have the LOWEST perplexity on?", "options": ["Random strings", "Literary fiction", "HTML markup", "Poetry in a low-resource language"], "answer": 2, "explain": "Structured, predictable data like HTML gives lower perplexity."},
  {"q": "Why is perplexity a weak quality metric for chat models after RLHF?", "options": ["They have no logprobs", "Post-training optimizes for preferred responses, not next-token prediction, often raising perplexity", "RLHF changes the tokenizer", "Perplexity only works for images"], "answer": 1, "explain": "Huyen warns that SFT/RLHF models can have higher perplexity while being more useful."},
  {"q": "A benchmark gets unusually LOW perplexity from a model compared with similar text. A likely explanation is…", "options": ["The benchmark is very hard", "Data contamination: the model saw the benchmark during training", "Temperature is too high", "The model is quantized"], "answer": 1, "explain": "Low perplexity means the text is easy to predict, which is a heuristic signal that it was in the training data."}
]
```

> **Source:** Huyen, *AI Engineering*, ch. 3 ("Challenges of Evaluating Foundation Models", "Understanding Language Modeling Metrics": entropy, cross entropy, BPC/BPB, perplexity).
