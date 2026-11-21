# Language modeling metrics: from entropy to perplexity

> **Before this lesson:** you should know what a token, a vocabulary and a probability distribution are (see [From language models to foundation models](#/lesson/ai-eng/aie-rise)), and what logits, softmax and logprobs are (see [Sampling, structured outputs and the probabilistic nature of AI](#/lesson/ai-eng/aie-sampling)). Logarithms are explained from scratch in section 1, so you do not need to remember them from school.

## In plain words

This lesson is about how to put a single number on the question "how good is this language model at predicting text?" There are four closely related numbers: **entropy**, **cross entropy**, **bits-per-byte** and **perplexity**. They are all built from one idea: how *surprised* the model is by each token that actually turns up.

An everyday picture: a friend reads a novel aloud and stops in the middle of a sentence, and you guess the next word. If you have read a lot of novels, you are rarely caught off guard. "Once upon a ..." is easy; the name of a new character is hard. A good guesser is surprised less often and less badly. **Perplexity** turns your average surprise into something you can picture: the number of equally likely words you were effectively torn between at each stop. A perplexity of 3 means that, on average, it was as if you were choosing between three words. A perplexity of 50,000 means you had no idea at all.

Why this matters for a job: the "loss" printed while a language model trains *is* cross entropy, and perplexity is quoted in research papers, model reports and data-cleaning pipelines. Interviewers like to ask "what is perplexity, and what does a perplexity of 1 mean?" or "why can't I compare the perplexity of two models with different tokenizers?". After this lesson you will be able to answer both, compute the numbers by hand, and know when not to trust them.

## Why evaluating AI is hard

Huyen opens her evaluation chapters with a warning: the more AI is used, the more chances there are for a failure that really hurts someone. She cites a man who died by suicide after a chatbot encouraged him, lawyers who filed AI-invented evidence in court, and Air Canada being ordered to honour a refund policy that its support chatbot made up. **Evaluation** means measuring how well a model or an AI product does its job, and for foundation models it is *harder* than it was for older machine-learning systems:

- **The smarter the model, the harder it is to check.** Anyone can spot a wrong answer to a first-grade sum. Checking a PhD-level proof or a long, plausible summary takes experts and time.
- **Outputs are open-ended.** An *open-ended* task has many acceptable answers, so you cannot compare the output with a single correct one.
- **Most models are black boxes.** A *black box* is a system you can use but cannot look inside: you do not know its architecture, its training data or how it was trained.
- **Public benchmarks saturate quickly.** A *benchmark* is a shared, fixed set of test questions used to compare models. It *saturates* when the best models score close to the maximum, so it can no longer tell good from better. GLUE, a language-understanding benchmark from 2018, saturated within about a year and was replaced by SuperGLUE in 2019.
- **New capabilities keep appearing**, and evaluation has to cover them as well as the old tasks.

Despite all this, investment in evaluation lags behind. Among the open source AI repositories Huyen surveyed, evaluation tools were one of the least represented categories. This module builds the vocabulary of evaluation from the ground up, and it starts with the oldest and most mathematical family of metrics: the ones used to train and compare language models themselves.

A **metric** is a rule that turns a model's behaviour into a number so that you can compare models or track progress. The four metrics in this lesson all measure *predictive accuracy*: how much probability the model gave to the tokens that really came next.

## 1. A short tour of logarithms

Every metric in this lesson uses a logarithm, so we start there.

A **logarithm** answers the question "what power do I raise a base to, to get this number?" With base 2: $\log_2 8 = 3$, because $2^3 = 8$. Likewise $\log_2 2 = 1$, $\log_2 4 = 2$ and $\log_2 1 = 0$ (because $2^0 = 1$).

For numbers between 0 and 1, which is where probabilities live, the logarithm is negative: $\log_2 0.5 = -1$, because $2^{-1} = 1/2$, and $\log_2 0.25 = -2$. The smaller the probability, the more negative its log.

Information theory, the branch of maths founded by Claude Shannon that measures information, defines the **surprise** of an event with probability $p$ as $-\log_2 p$. The minus sign makes the number positive. In words: surprise counts how many times you would have to halve your certainty to reach that probability.

| Probability of what happened | Surprise $-\log_2 p$ | Plain reading |
|---|---|---|
| 1 | 0 bits | you knew it would happen |
| 1/2 | 1 bit | a coin flip |
| 1/4 | 2 bits | one of four equal options |
| 1/8 | 3 bits | one of eight |
| 1/1024 | 10 bits | a real shock |

The unit is the **bit**, the same bit as in computer memory: one bit is enough to pick between two equally likely options, two bits between four, three bits between eight.

There is a second common base. The **natural logarithm**, written $\ln$, uses the base $e \approx 2.718$. Surprise measured with $\ln$ is in **nats** instead of bits. The two differ by a fixed factor: one bit equals $\ln 2 \approx 0.693$ nats, so to convert nats to bits you divide by 0.693. Example: a surprise of 1.386 nats is $1.386 / 0.693 = 2$ bits. Machine-learning libraries such as PyTorch and TensorFlow use natural logs, and that is why you will meet both units.

Last, one rule we will use constantly: the log of a product is the sum of the logs, $\log(a \times b) = \log a + \log b$. The probability of a whole sentence is a product of token probabilities, so its log is a sum of token logprobs. A **logprob** (from the previous lesson) is the natural log of a token's probability, $\ln p$.

```python-run
import math
for p in [1, 0.5, 0.25, 0.125, 0.01]:
    bits = math.log2(1 / p)      # same as -log2(p)
    nats = math.log(1 / p)       # same as -ln(p)
    print(f"p = {p:<6} surprise = {bits:5.2f} bits = {nats:5.2f} nats")
print("ln 2 =", round(math.log(2), 3), "-> nats / 0.693 = bits")
```

**Reading this Python line by line**

- `import math` loads Python's built-in maths module, which has the logarithm functions.
- `for p in [...]:` repeats the indented lines once for each probability in the list.
- `math.log2(1 / p)` is surprise in bits. Taking the log of $1/p$ gives the same value as $-\log_2 p$ (dividing inside a log becomes a minus sign outside), and it avoids Python printing an odd "-0.00" for $p = 1$. `math.log` with one argument is the natural log $\ln$, so `math.log(1 / p)` is surprise in nats.
- The `f"..."` string fills in the values; `:5.2f` means "five characters wide, two decimals".
- Output: probability 1 gives 0 bits, 0.5 gives 1.00 bit (0.69 nats), 0.25 gives 2.00 bits, 0.125 gives 3.00 bits, and 0.01 gives 6.64 bits (4.61 nats). Each nats value is the bits value times 0.693, which the last line confirms.

## 2. Entropy: how unpredictable the data is

**Entropy** is the *average* surprise of a source of tokens, when each token is scored with its own true probability. It tells you how much information a token carries on average, or, equivalently, how hard the next token is to predict even if you know the true odds perfectly. In words: for every possible token, multiply its probability by its surprise, then add the results. For a distribution $P$ (where $P(x)$ is the probability of token $x$ and $\sum_x$ means "add up over every token $x$"):

$$
H(P) = -\sum_{x} P(x)\log_2 P(x) \quad\text{(bits)}
$$

Worked example 1, a fair coin: $P(\text{heads}) = P(\text{tails}) = 0.5$. Each outcome has surprise 1 bit, so $H = 0.5 \times 1 + 0.5 \times 1 = 1$ bit.

Worked example 2, a bent coin that lands heads 90% of the time: heads has surprise $-\log_2 0.9 = 0.152$ bits and tails $-\log_2 0.1 = 3.322$ bits. $H = 0.9 \times 0.152 + 0.1 \times 3.322 = 0.137 + 0.332 = 0.469$ bits. The bent coin is more predictable, so its entropy is lower.

Huyen's example uses positions in a square. If you describe a position with two tokens, "upper" and "lower", both equally likely, you need 1 bit per token. If you use four tokens, "upper-left", "upper-right", "lower-left" and "lower-right", you need 2 bits. **More entropy means each token carries more information and the next token is harder to guess.** A language in which every next token was certain would have entropy 0.

## 3. Cross entropy: how well a model predicts the data

A language model never knows the true distribution $P$ of the text. It learns its own distribution $Q$ that tries to match $P$. **Cross entropy** is the average surprise when the tokens really come from $P$ but you measure surprise using the model's probabilities $Q$. In words: for each token, take how often it really occurs, multiply by how surprised *the model* is by it, and add up:

$$
H(P, Q) = -\sum_x P(x)\log Q(x) = H(P) + D_{KL}(P\,\|\,Q)
$$

The right-hand side splits cross entropy into two parts:

- $H(P)$, the data's own entropy: unpredictability that no model can remove. If a coin is fair, nobody can call it better than half the time.
- $D_{KL}(P\|Q)$, the **KL divergence** (named after Kullback and Leibler, the statisticians who introduced it). It measures how far the model's distribution is from the truth, and it is never negative. It is the *extra* surprise you pay for using the wrong probabilities.

If the model learns the data perfectly, $Q = P$, the KL term is 0 and cross entropy equals entropy. **Training a language model means minimising its cross entropy on the training data.** That is the "loss" printed while a model trains.

In practice nobody knows $P$, so cross entropy is estimated from a real text. Take a sequence of $n$ tokens $x_1, x_2, \ldots, x_n$. For each token, look up the probability the model gave it *given the tokens before it* (written $Q(x_i \mid x_{<i})$, read "Q of $x_i$ given everything before position $i$"), take the log, and average:

$$
H \approx -\frac{1}{n}\sum_{i=1}^{n} \log Q(x_i \mid x_{<i})
$$

This quantity has a name of its own: the **average negative log-likelihood** (NLL). "Likelihood" is the probability the model assigned to what actually happened, "log" turns the product into a sum, "negative" makes it positive, and "average" divides by the number of tokens.

Tiny worked example: a model gives the three tokens of a sentence probabilities 0.5, 0.25 and 1.0. Their surprises are 1, 2 and 0 bits, so the cross entropy on this sentence is $(1 + 2 + 0)/3 = 1$ bit per token.

## 4. Bits-per-character and bits-per-byte

Cross entropy is measured *per token*, but tokens differ between models. One model might use whole words as tokens and another single characters. A word-level model needs more bits per token than a character-level one, because each of its tokens carries more text, so comparing them per token is unfair. Two normalisations fix this.

- **BPC (bits-per-character)** divides the bits per token by the average number of characters per token. Huyen's example: 6 bits per token with tokens of 2 characters on average gives $6 / 2 = 3$ bits per character.
- **BPB (bits-per-byte)** goes one step further. Computers store characters as *bytes* (groups of 8 bits), and different text encodings use different amounts of storage per character. ASCII, an old encoding for English letters, uses 7 bits per character, while UTF-8, the encoding used on most of the web, uses between 8 and 32 bits. Normalising by bytes of the original text gives a number that is comparable no matter how the text is encoded or tokenized. Worked example: with 3 bits per character and ASCII characters of 7 bits, each character is $7/8 = 0.875$ of a byte, so BPB $= 3 / 0.875 = 3.43$.

BPB also connects language modelling to **compression**, which means storing data in fewer bits. A BPB of 3.43 says the model could encode each original 8-bit byte in about 3.43 bits, shrinking the text to less than half its size (8 / 3.43 is about 2.33 times smaller). A better predictor is a better compressor: if you can guess what comes next, you need fewer bits to write down what actually came.

## 5. Perplexity

**Perplexity**, abbreviated **PPL**, is the exponential of entropy or cross entropy. "Exponential" means you undo the logarithm: if cross entropy is $H$ bits, perplexity is $2^H$; if it is $H$ nats, perplexity is $e^H$.

$$
\text{PPL}(P) = 2^{H(P)}, \qquad \text{PPL}(P,Q) = 2^{H(P,Q)}\ \text{(bits)}\qquad\text{or}\qquad e^{H(P,Q)}\ \text{(nats)}
$$

Why undo the log? Because the result has a friendly meaning: **perplexity is the effective number of equally likely choices the model is hesitating between at each step.** A model that has perfectly learned the four-position square has cross entropy 2 bits and perplexity $2^2 = 4$: four equal options. A model with perplexity 1 is never surprised. A model that spreads its probability evenly over a vocabulary of $V$ tokens has perplexity exactly $V$. Lower is better.

Because PyTorch and TensorFlow report the loss in nats, perplexity from their loss is $e^{\text{loss}}$. A validation loss of 2.0 nats means perplexity $e^{2} \approx 7.39$. Since people mix up bits and nats, many reports give perplexity rather than cross entropy: the exponential gives the same answer in either unit, as long as you use the matching base.

Written directly in terms of the logprobs an API returns (natural logs):

$$
\text{PPL} = \exp\!\Big(-\frac{1}{n}\sum_{i=1}^{n}\ln Q(x_i\mid x_{<i})\Big)
$$

In words: average the token logprobs, flip the sign, and raise $e$ to that power.

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

**Reading this Python line by line**

- `import numpy as np` loads NumPy, a library for working with whole arrays of numbers at once, under the short name `np`.
- `np.log([0.5, 0.25, 0.9, 0.1, 0.6])` takes the natural log of each of five token probabilities and returns an array of five logprobs. These stand in for what an API would return for a five-token text.
- `-logprobs.mean()` averages the five logprobs and flips the sign: this is the average negative log-likelihood, the cross entropy in nats.
- `nll/np.log(2)` converts nats to bits by dividing by $\ln 2$.
- `np.exp(nll)` is $e^{H}$, the perplexity; `2**(...)` computes $2^{H}$ from the bits version to show they agree.
- The last two lines build a model that gives every one of 50,000 tokens probability $1/50000$. `np.log(1/V)` is that token's logprob, and the exponential of its negative is the perplexity.
- Output: cross entropy 0.9996 nats, which is 1.4422 bits; perplexity 2.7173 both ways; and the uniform model's perplexity is 50000 (printed with a tiny rounding tail such as `50000.00000000001`, because computers store decimals with limited precision). So this model was, on average, as unsure as someone choosing among about 2.7 options.

### Rules of thumb for "good" perplexity

What counts as a good perplexity depends on the data and on how the number was computed. Huyen gives three rules:

- **More structured data gives lower perplexity.** HTML, the markup language of web pages, is more predictable than everyday prose: after an opening `<head>` tag, a closing `</head>` will follow.
- **A bigger vocabulary gives higher perplexity.** More possible tokens means more ways to be wrong. Predicting the next character is easier than predicting the next word, and a children's book is easier to predict than *War and Peace*.
- **A longer context gives lower perplexity.** The **context** is the earlier text the model can see when it predicts. Shannon, in 1951, conditioned his predictions on at most 10 previous tokens. Modern models typically condition on hundreds to thousands of tokens, up to their maximum context length, so their perplexities are lower.

Perplexities of 3 or below are not unusual. Picture what that means: from a vocabulary of tens of thousands of tokens, the model behaves as if it were choosing among only three. That is remarkable predictive power.

### What perplexity is useful for

1. **A rough proxy for capability.** A model that predicts text badly is usually bad at downstream tasks too. OpenAI's GPT-2 report showed bigger models getting consistently lower perplexity on many datasets. On the LAMBADA dataset, perplexity fell from 35.13 for the 117-million-parameter model to 8.63 for the 1.5-billion-parameter one (Huyen's Table 3-1). Huyen notes that many providers, increasingly secretive, have stopped reporting perplexity.
2. **Spotting data contamination.** *Contamination* means a benchmark's test questions leaked into a model's training data, so a high score may be memory, not skill. If a model's perplexity on a benchmark is unusually low compared with similar text, it has probably seen that text before (Module 4 returns to this).
3. **Deduplication and data quality.** When gathering more training data, add new text mainly when the current model finds it *surprising* (high perplexity); low perplexity means the model already "knows" it. Extremely high perplexity, on the other hand, can flag gibberish or broken text, which is a form of **anomaly detection**: finding the inputs that do not look like the rest.

> [!WARNING]
> Perplexity is a poor quality measure for **post-trained** models. Post-training (supervised finetuning, SFT, and reinforcement learning from human feedback, RLHF; see [Post-training](#/lesson/ai-eng/aie-post-training)) teaches a model to give answers people prefer, not to predict raw text, so its perplexity often goes *up* afterwards even though it became more useful. **Quantization**, storing a model's numbers with fewer bits to save memory (Module 7), can also shift perplexity unexpectedly. Use perplexity mainly for base models, data work, and comparisons made with the same tokenizer and setup.

> [!NOTE]
> To compute a text's perplexity you need the logprob of every token given the tokens before it. Many commercial APIs return few or no logprobs, which limits these techniques to models you host yourself or to APIs that return full logprobs for a text you supply.

## 6. Worked example: comparing two models

Model A gives probabilities [0.4, 0.5, 0.2, 0.7] to the four tokens of a test sentence, and model B gives [0.6, 0.6, 0.1, 0.8].

- A: average NLL $= -(\ln 0.4 + \ln 0.5 + \ln 0.2 + \ln 0.7)/4 = (0.916 + 0.693 + 1.609 + 0.357)/4 \approx 0.894$ nats, so PPL $\approx e^{0.894} \approx 2.44$.
- B: $(0.511 + 0.511 + 2.303 + 0.223)/4 \approx 0.887$, so PPL $\approx 2.43$.

B was more confident and right on three tokens, yet the two models end up almost tied. The reason is the third token: B gave it only 0.1, and its surprise of 2.303 nats eats most of B's gains. Perplexity is a *geometric mean* of the inverse probabilities, a kind of average that multiplies instead of adds, so one confidently wrong prediction is expensive. Push B's 0.1 down to 0.01 and its perplexity jumps from 2.43 to 4.32.

```python-run
import numpy as np
def ppl(probs): return float(np.exp(-np.mean(np.log(probs))))
print("A:", round(ppl([0.4, 0.5, 0.2, 0.7]), 4))
print("B:", round(ppl([0.6, 0.6, 0.1, 0.8]), 4))
print("B with 0.1 -> 0.01:", round(ppl([0.6, 0.6, 0.01, 0.8]), 4))
```

`ppl` packs the whole recipe into one line: logs, mean, minus sign, exponential; `float(...)` turns NumPy's number type into a plain Python number for printing. Output: A 2.4446, B 2.4275, and B with the worse third token 4.3167.

> [!INTERVIEW]
> **"What's the relationship between cross-entropy loss and perplexity, and what's a perplexity of 1?"** Perplexity is exp(cross entropy) when the loss is in nats, or 2^(cross entropy) in bits. A perplexity of 1 means the model gives probability 1 to every correct token: it predicts perfectly and its cross entropy is 0. A uniform model over V tokens has perplexity V. Follow-up: perplexity is only comparable between models that share a tokenizer and evaluation setup; otherwise compare bits-per-byte.

## 7. Worked example: entropy, cross entropy and KL by hand

Suppose a tiny language has three tokens with true probabilities $P = (0.5, 0.25, 0.25)$.

- **Entropy**: the surprises are 1, 2 and 2 bits, so $H(P) = 0.5\cdot1 + 0.25\cdot2 + 0.25\cdot2 = 1.5$ bits. The best possible code spends 1 bit on the common token and 2 bits on each rare one.
- A model predicts $Q = (0.25, 0.25, 0.5)$. It has the right shape but puts the big share on the wrong token. Under $Q$ the surprises are 2, 2 and 1 bits, but we weight them by how often each token *really* occurs: **cross entropy** $H(P,Q) = 0.5\cdot2 + 0.25\cdot2 + 0.25\cdot1 = 1.75$ bits.
- **KL divergence**: $1.75 - 1.5 = 0.25$ bits. That is the price of the model's mistake, on top of the 1.5 bits nobody can avoid.
- **Perplexity**: the data's own perplexity is $2^{1.5} \approx 2.83$, and the model's is $2^{1.75} \approx 3.36$.

Two lessons follow. A model's cross entropy can never fall below the data's entropy, so every dataset has a floor that no model beats. And absolute perplexity values mean little across datasets: what separates two models on the *same* data is the gap above that floor, the KL term.

```python-run
import numpy as np
P = np.array([0.5, 0.25, 0.25])
def H(p): return float(-(p * np.log2(p)).sum())
def CE(p, q): return float(-(p * np.log2(q)).sum())
for name, Q in [("perfect model", P), ("wrong mass", np.array([0.25, 0.25, 0.5])),
                ("uniform guess", np.ones(3) / 3), ("overconfident", np.array([0.98, 0.01, 0.01]))]:
    ce = CE(P, Q)
    print(f"{name:14s} cross entropy {ce:.3f} bits  KL {ce - H(P):.3f}  perplexity {2**ce:.3f}")
```

**Reading this Python line by line**

- `P = np.array([...])` stores the true distribution as a NumPy array.
- `H(p)` multiplies each probability by its own log (base 2) element by element (`p * np.log2(p)`), adds them with `.sum()` and flips the sign: entropy.
- `CE(p, q)` is the same but takes the log of the *model's* probabilities `q`: cross entropy.
- The loop tries four models: a perfect one, the "wrong mass" model above, a uniform guess (`np.ones(3) / 3` is three entries of 1/3), and an overconfident model that puts 98% on the first token.
- Output: perfect 1.500 bits, KL 0, perplexity 2.828; wrong mass 1.750, KL 0.250, perplexity 3.364; uniform 1.585, KL 0.085, perplexity 3.000; overconfident 3.337, KL 1.837, perplexity 10.102.

The overconfident model is the worst of the four, even though it is right about which token is most likely. It gives 1% to tokens that occur 25% of the time, and cross entropy punishes confident mistakes heavily. It is the same effect that made one bad token dominate the comparison in section 6. Notice too that an honest uniform guess beats both wrong models: knowing what you do not know is rewarded.

## 8. Computing perplexity in practice

Turning the formula into a number you can trust takes care. A **context window** is the maximum number of tokens a model can look at in one go; keep that term in mind for step 4.

1. **Tokenize with the model's own tokenizer.** Perplexity is per token, and tokens are model-specific.
2. **Get a logprob for every token, conditioned on the tokens before it.** With a hosted model you need an API that returns logprobs for text *you* supply, not only for text it generates. Many chat APIs do not offer this.
3. **Decide what the first token is conditioned on.** With a beginning-of-sequence token (`<BOS>`) in front, the first real token gets a proper prediction. Without one, the first token is usually skipped. Either choice is fine if you apply it to every model you compare.
4. **Handle texts longer than the context window.** The naive approach cuts the text into separate windows, so the first tokens of each window are predicted with almost no context and perplexity comes out too high. A **sliding window with a stride** moves the window forward by a fixed number of tokens (the *stride*) each time and scores only the new tokens, so every scored token has a long left context. A smaller stride is more accurate and costs more computation.
5. **Aggregate over tokens, not over documents.** Add up all the negative logprobs, divide by the total number of tokens, then exponentiate. Averaging per-document perplexities gives short documents too much weight. You will implement this in the `aie-perplexity` problem.

The demo below uses a toy "model" whose surprise falls as it sees more context, then scores the same 400-token text in the two ways described in step 4.

```python-run
import numpy as np
rng = np.random.default_rng(0)
# Toy model: a token is easier to predict the more left context it has (up to 50 tokens).
def token_nll(context_len): return 3.0 - 2.0 * min(context_len, 50) / 50 + 0.05 * rng.normal()
T, window, stride = 400, 100, 50
chunked = [token_nll(i % window) for i in range(T)]                      # independent windows
sliding = [token_nll(i if i < window else window - stride + (i - window) % stride) for i in range(T)]
print(f"independent windows : perplexity {np.exp(np.mean(chunked)):.2f}")
print(f"sliding, stride {stride}  : perplexity {np.exp(np.mean(sliding)):.2f}  (same model, same text)")
```

**Reading this Python line by line**

- `rng = np.random.default_rng(0)` creates a random-number generator with seed 0, so every run gives the same numbers.
- `token_nll(context_len)` is the toy model: with no context a token costs about 3 nats; the cost falls linearly to about 1 nat once 50 or more tokens of context are visible; `0.05 * rng.normal()` adds a little noise.
- `T, window, stride = 400, 100, 50` sets a 400-token text, a 100-token context window and a stride of 50.
- `chunked`: in independent windows, token `i` sees only `i % window` earlier tokens (`%` is the remainder after division), so the context resets to 0 at tokens 100, 200 and 300.
- `sliding`: the first window is scored normally; after that each new token sees at least `window - stride` = 50 earlier tokens.
- Output: independent windows give perplexity 4.52 and the sliding window 3.09. Same model, same text, two very different numbers, because the evaluation setup changed how much context each token had.

When someone reports a perplexity, the evaluation setup is part of the number.

### What can go wrong

| Symptom | Likely cause | What to do |
|---|---|---|
| Model A beats model B on perplexity but is worse in use | Different tokenizers, or B is post-trained | Compare bits-per-byte, and evaluate the task itself |
| Perplexity rises after quantization | Lower precision changed the logits | Check task metrics before rejecting the quantized model |
| Perplexity is suspiciously low on a benchmark | The benchmark was in the training data | Treat the benchmark score as contaminated |
| Perplexity is `inf` (infinite) | Some token got probability 0, and $\ln 0$ is minus infinity | Check for a tokenizer mismatch or a truncated vocabulary |
| Numbers differ between two runs of the "same" evaluation | Different context length, stride or `<BOS>` handling | Fix and record the setup |

## Pitfalls

- Comparing perplexities across tokenizers or context lengths.
- Mixing bits and nats ($2^H$ versus $e^H$).
- Treating a chat model's high perplexity as low quality. It reflects post-training, not a worse model.
- Forgetting that perplexity measures prediction only, not truthfulness, helpfulness or safety. A model can predict text superbly and still give harmful advice.

## Summary

- **Surprise** of a token is $-\log p$: 0 for a certain token, large for an unlikely one. Measured in bits (base 2) or nats (base $e$).
- **Entropy** is the average surprise under the true distribution: the inherent unpredictability of the data.
- **Cross entropy** = entropy + KL divergence. It is what language-model training minimises, and in practice it is the average negative log-likelihood per token.
- **BPC/BPB** remove tokenizer differences, and BPB connects prediction to compression.
- **Perplexity** = exp(cross entropy): the effective number of choices per token. Lower is better. Structured data, smaller vocabularies and longer contexts lower it.
- Uses: a capability proxy for base models, contamination detection, data deduplication and filtering, anomaly detection. It says little about post-trained chat models, and the evaluation setup is part of every reported number.

## Glossary

- **Evaluation**: measuring how well a model or AI product does its job.
- **Metric**: a rule that turns behaviour into a number you can compare.
- **Benchmark**: a shared, fixed set of test questions for comparing models; it *saturates* when top models all score near the maximum.
- **Black box**: a system you can use but cannot inspect.
- **Logarithm**: the power you raise a base to in order to get a number; $\log_2 8 = 3$.
- **Bit / nat**: units of information using base 2 and base $e$; 1 bit = 0.693 nats.
- **Surprise**: $-\log p$ for an event of probability $p$.
- **Entropy**: the average surprise of a source scored with its true probabilities.
- **Cross entropy**: the average surprise when real data is scored with a model's probabilities.
- **KL divergence**: the extra surprise caused by using the model's distribution instead of the true one; never negative.
- **Negative log-likelihood (NLL)**: minus the log of the probability a model gave to what actually happened; its average is the practical cross entropy.
- **BPC / BPB**: cross entropy expressed per character or per byte of text, so models with different tokenizers can be compared.
- **Compression**: storing data in fewer bits; a better predictor compresses better.
- **Perplexity (PPL)**: exp of cross entropy; the effective number of equally likely choices per token.
- **Context window**: the maximum number of tokens a model can read at once.
- **Sliding window / stride**: scoring long text with overlapping windows that move forward by a fixed number of tokens.
- **Data contamination**: test data that leaked into training data.
- **Anomaly detection**: finding inputs that look unlike the rest.

```quiz
[
  {"q": "A model's cross entropy on a dataset is 3 bits per token. Its perplexity is…", "options": ["3", "6", "8", "9"], "answer": 2, "explain": "PPL = 2^H = 2^3 = 8: the model behaves as if choosing among eight equal options per token."},
  {"q": "Cross entropy H(P,Q) can be decomposed as…", "options": ["H(Q) - H(P)", "H(P) + KL(P||Q)", "KL(Q||P) only", "H(P) × H(Q)"], "answer": 1, "explain": "Cross entropy is the data's own entropy plus the KL divergence, the extra cost of the model's wrong probabilities."},
  {"q": "PyTorch reports a validation loss of 2.0 (natural log). Perplexity is about…", "options": ["4.0", "7.39", "2.0", "100"], "answer": 1, "explain": "The loss is in nats, so PPL = e^2 ≈ 7.39. Using 2^2 = 4 would mix up bits and nats."},
  {"q": "Why might bits-per-byte be preferred over per-token cross entropy for comparing models?", "options": ["It is always smaller", "It does not depend on each model's tokenizer", "It ignores rare tokens", "It measures latency"], "answer": 1, "explain": "Tokens differ across models, so bits per token are not comparable. Normalising by bytes of the original text makes the comparison fair."},
  {"q": "Which data would you expect a model to have the LOWEST perplexity on?", "options": ["Random strings", "Literary fiction", "HTML markup", "Poetry in a low-resource language"], "answer": 2, "explain": "Structured, predictable data such as HTML gives lower perplexity: closing tags follow opening tags."},
  {"q": "Why is perplexity a weak quality metric for chat models after RLHF?", "options": ["They have no logprobs", "Post-training optimises for preferred responses, not next-token prediction, often raising perplexity", "RLHF changes the tokenizer", "Perplexity only works for images"], "answer": 1, "explain": "Huyen warns that SFT and RLHF models can have higher perplexity while being more useful to people."},
  {"q": "A benchmark gets unusually LOW perplexity from a model compared with similar text. A likely explanation is…", "options": ["The benchmark is very hard", "Data contamination: the model saw the benchmark during training", "Temperature is too high", "The model is quantized"], "answer": 1, "explain": "Low perplexity means the text is easy for the model to predict, a heuristic sign that it was in the training data."},
  {"q": "Model X gives the correct tokens probabilities 0.9, 0.9, 0.9 and 0.001. Model Y gives 0.6 to each. Which has lower perplexity?", "options": ["X, because it is right with high confidence three times", "Y, because X's single near-zero probability adds a huge surprise", "They tie", "Perplexity cannot be computed with four tokens"], "answer": 1, "explain": "X's average NLL is (3 × 0.105 + 6.91)/4 ≈ 1.81 nats, PPL ≈ 6.1. Y's is 0.51 nats, PPL ≈ 1.67. One confident mistake dominates."}
]
```

> **Source:** Huyen, *AI Engineering*, ch. 3 ("Challenges of Evaluating Foundation Models", "Understanding Language Modeling Metrics": entropy, cross entropy, bits-per-character and bits-per-byte, perplexity and its uses).
