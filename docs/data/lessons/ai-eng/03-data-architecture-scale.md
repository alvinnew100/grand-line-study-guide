# Training data, architecture and scale

> **Before this lesson:** you should know what a token, a parameter (weight), training, self-supervision and an autoregressive language model are. All of them are explained in [From language models to foundation models](#/lesson/ai-eng/aie-rise). The demos use Python lists, loops and a little NumPy; each new NumPy operation is explained where it appears.

## In plain words

Three things decide what a foundation model is like, in the same way three things decide what a graduate is like: **what they studied** (the training data), **how their brain is wired** (the architecture, meaning the layout of the calculations inside the model) and **how long and how hard they studied** (the scale: how many parameters, how much text, how much computing work).

A student who only ever read English newspapers will be weak at Vietnamese poetry and at chemistry, however clever they are. A model is the same: it is good at what was plentiful in its reading and poor at what was rare. The wiring matters too. Today's language models almost all use a design called the **transformer**, whose key trick, **attention**, lets the model look back at any earlier word while choosing the next one, the way you glance back up a page to check a name. And size has a price: bigger models read more, cost more to train, and cost more every time they answer.

Why this matters for a job: you will rarely train a foundation model, but you will choose between them, pay for them and explain their failures. "Why is the model worse in Hindi?", "why does a longer prompt cost more memory?", "what does 70B mean and what will it cost to run?" and "explain attention" are everyday questions at work and stock questions in interviews. This lesson gives you the vocabulary and the back-of-envelope arithmetic to answer them.

Huyen groups the key design decisions behind a model into **training data**, **modeling** (architecture and size) and **post-training**, and adds **sampling** as the often-overlooked step that turns probabilities into output. This lesson covers data, architecture and scale. The next two cover post-training and sampling.

> [!NOTE]
> A deeper, code-level treatment of transformers (multi-head attention, positional encodings, implementing a block) lives in the **LLM Practice** track. Here we focus on what an AI engineer needs in order to reason about cost, capability and choice of model.

## 1. Training data: a model is only as good as its data

A model that never saw Vietnamese text during training cannot translate into Vietnamese. Model developers often have to work with whatever data is available, even when it is not the data they would choose.

A common source is **Common Crawl**. To *crawl* the web is to have a program visit pages automatically, follow their links and save what it finds. Common Crawl is a nonprofit that does this regularly and publishes the result (about 2–3 billion pages a month in 2022–2023). Google's cleaned subset is called **C4**. The quality is questionable: clickbait, misinformation, propaganda and toxic content. Yet most models that disclose their sources use some version of it, including GPT-3 and Gemini. Many companies have stopped disclosing their training data at all. Rough rules of thumb, called *heuristic* filters, help a little. GPT-2, for example, only used pages linked from the forum Reddit when the link had at least three upvotes, on the theory that people do not upvote rubbish.

### Multilingual models

English dominates the web. In Common Crawl, English is about **45.88%** of the data while English speakers are about 18% of the world population. Other languages are badly under-represented, and a language with little training text available is called a **low-resource language**. Huyen's table (from a study by Lai and colleagues) divides each language's share of the world's speakers by its share of Common Crawl. A ratio of 1 would be fair representation. Punjabi, Swahili and Urdu have ratios above 100: their speakers are more than a hundred times more numerous than their share of the text would suggest. The consequences:

- GPT-4's scores on MMLU (the multiple-choice benchmark from the previous lesson) are much worse in languages like Telugu, Marathi and Punjabi, which are among the most under-represented.
- On six maths puzzles from the Project Euler website, GPT-4 solved English versions more than three times as often as Armenian or Farsi, and failed all six in Burmese and Amharic.
- **Tokenization cost.** A tokenizer learns its vocabulary from the same lopsided data, so it has whole-word tokens for common English words and must spell rarer languages out in many small pieces. Under-represented languages therefore need many more tokens for the same content. Huyen cites a median token count for the same text roughly ten times higher in Burmese than in English. Since providers charge per token and models generate one token at a time, those users pay about ten times more and wait about ten times longer for the same message.
- Translating to English and back loses information. Vietnamese pronouns that encode the relationship between speakers all collapse to "I" and "you".

### Domain-specific models

A **domain** is a subject area with its own vocabulary and kinds of documents. General models know common domains (coding, law, science, business) but struggle with data that is rare on the public web: drug discovery, cancer screening, a company's private (*proprietary*) file formats. Hence domain-specific models such as DeepMind's **AlphaFold** (protein structure), NVIDIA's **BioNeMo** (biomolecular data) and Google's **Med-PaLM2** (medical queries).

> [!TIP]
> When choosing a model for a non-English or niche-domain application, do not rely on English leaderboards (public rankings of models by benchmark score). Evaluate on your own language and domain data (Module 4), and estimate token costs with that model's tokenizer on your actual text.

## 2. Architecture: why transformers won

A model's **architecture** is its blueprint: which calculations happen, in what order, and where the adjustable parameters sit. The models in this track are **neural networks**: programs that take in numbers, pass them through a long chain of multiply-and-add steps whose multipliers are the parameters, and output numbers. Three pieces of vocabulary carry the rest of this section:

- A **vector** is an ordered list of numbers, such as `[0.2, -1.3, 0.7]`. Inside a model every token is represented by a vector, and the count of numbers in it is its **dimension**. A model whose "model dimension" is 4,096 keeps 4,096 numbers per token.
- A **matrix** is a grid of numbers with rows and columns. Multiplying a vector by a matrix produces a new vector; it is the basic "transform these numbers" step, and the entries of the matrix are parameters.
- The **dot product** of two vectors of equal length multiplies them position by position and adds the results: for `[1, 2]` and `[3, 4]` it is $1 \times 3 + 2 \times 4 = 11$. A large dot product means the two vectors point the same way, so it serves as a similarity score.

### The problem transformers solved

Before transformers, the leading design for tasks such as translation was **seq2seq** (sequence-to-sequence, 2014). It was built from **RNNs** (recurrent neural networks), which read text one token at a time while updating a running summary vector called the **hidden state**. In seq2seq, one RNN, the **encoder**, read the whole input and squeezed it into a final hidden state. A second RNN, the **decoder**, generated the output from that one vector. It had two problems:

1. The decoder saw only the *final hidden state*. Huyen compares this to answering questions about a book using only its summary.
2. RNNs are **sequential**, so a 200-token input had to be processed one token after another. Step 200 cannot start until step 199 is done, which wastes hardware that could do many things at once.

The **attention mechanism** fixes the first problem by letting the model weigh *any* input token when producing each output token, like looking up any page of the book instead of trusting the summary. The transformer (introduced by Vaswani and colleagues at Google in 2017) dropped RNNs entirely, which fixed the second problem: input tokens are processed **in parallel**, all at the same time. (Attention itself predates the transformer. Google's translation system GNMT used it together with seq2seq in 2016.)

Output generation is still sequential, though, because each new token depends on the ones already written. Transformer inference therefore has two phases, a distinction you will meet again in Module 9:

- **Prefill**: process all input tokens in parallel and build the key/value vectors described next. This phase is *compute-bound*: its speed is limited by how many calculations the chip can do per second.
- **Decode**: generate one token at a time. This phase is *memory-bandwidth-bound*: its speed is limited by how fast data can be moved in and out of the chip's memory, because every step must re-read a large store of saved vectors.

### Attention in one formula

In words first. To decide what the current token should pay attention to, the model gives every token three vectors, each made by multiplying the token's vector $x$ by a different learned matrix: a **query** $q = xW_Q$ ("what am I looking for?"), a **key** $k = xW_K$ ("what do I contain?") and a **value** $v = xW_V$ ("what do I hand over if chosen?"). In the book analogy, the query is the reader hunting for information, each key is a page number, and each value is the page's content. The current token's query is compared with every token's key by a dot product, giving one score per token. Those scores are turned into percentages that add up to 100%, and the output is the average of the values weighted by those percentages.

The step that turns scores into percentages is called **softmax**. It raises the constant $e \approx 2.718$ to the power of each score (which makes everything positive and exaggerates the gaps) and divides each result by their total. For scores $[2, 1, 0]$: $e^2 = 7.39$, $e^1 = 2.72$, $e^0 = 1$, total $11.11$, so the weights are $[0.67, 0.24, 0.09]$. The highest score gets the biggest share, but nothing is discarded.

Putting it together, with $Q$, $K$ and $V$ holding the queries, keys and values of all tokens as the rows of three matrices, $K^\top$ meaning "K turned on its side so the dot products line up", and $d$ the dimension of the vectors:

$$
\text{Attention}(Q,K,V) = \operatorname{softmax}\!\left(\frac{QK^\top}{\sqrt{d}}\right)V
$$

Dividing by $\sqrt{d}$ keeps the scores from growing as the vectors get longer. Without it, long vectors give huge scores, softmax hands nearly 100% to one token, and the model can no longer blend information. Because every previous token's key and value must be kept for each new token, **longer contexts mean more key and value vectors to compute and store**. This store is the **KV cache**, and it dominates memory use during inference (Module 9). In practice attention is **multi-headed**: the model runs several attention calculations side by side, each with its own matrices, so that one head can track grammar while another tracks who "she" refers to. Llama 2-7B, for example, has 32 heads of dimension 128 ($4096 / 32$), and the head outputs are joined end to end and passed through one more matrix, the **output projection**.

The demo runs this calculation on three made-up tokens.

```python-run
import numpy as np
np.random.seed(0)
d = 4                       # head dimension
x = np.random.randn(3, d)   # 3 token representations
Wq, Wk, Wv = (np.random.randn(d, d) for _ in range(3))
Q, K, V = x @ Wq, x @ Wk, x @ Wv
scores = Q @ K.T / np.sqrt(d)
# causal mask: token i can only attend to tokens <= i (autoregressive)
mask = np.triu(np.ones_like(scores), k=1).astype(bool)
scores[mask] = -np.inf
weights = np.exp(scores - scores.max(axis=1, keepdims=True))
weights /= weights.sum(axis=1, keepdims=True)
print("attention weights (rows sum to 1, upper triangle is 0):\n", weights.round(3))
print("output shape:", (weights @ V).shape)
```

**Reading this Python line by line**

- `np.random.seed(0)` fixes the random-number generator so that everyone who runs the demo sees the same numbers.
- `x = np.random.randn(3, d)` makes a 3-by-4 grid of random numbers: three tokens, each a vector of dimension 4. In a real model these come from the layers below.
- `Wq, Wk, Wv = (...)` creates three random 4-by-4 matrices standing in for the learned ones.
- `@` is NumPy's matrix-multiplication operator. `x @ Wq` turns every token vector into its query; the next two do the same for keys and values.
- `Q @ K.T / np.sqrt(d)` computes every query-key dot product at once (`K.T` is the sideways-turned K) and scales it. `scores` is 3 by 3: row *i*, column *j* is how much token *i* wants to look at token *j*.
- `np.triu(..., k=1)` marks the cells above the diagonal, the ones where *j* is later than *i*. Setting those scores to minus infinity is the **causal mask**: an autoregressive model must not look at tokens that come after the one it is predicting from.
- The two `weights` lines are softmax, row by row. Subtracting the row maximum first changes nothing mathematically and avoids numeric overflow. $e^{-\infty} = 0$, so masked cells get weight 0.
- Output: a 3-by-3 table. Row 1 is `[1, 0, 0]` because the first token can only look at itself. Row 2 splits its attention between tokens 1 and 2; row 3 spreads over all three. Each row sums to 1. `weights @ V` blends the value vectors accordingly, giving a new 4-number vector per token: shape `(3, 4)`.

### The transformer block and the full model

A transformer is a stack of identical units called **transformer blocks**, and the number of blocks is the model's number of **layers**. A token's vector enters the first block, is refined, passes to the second, and so on. Each block has:

- an **attention module** holding four weight matrices: one each for queries, keys and values, plus an output projection. This is where tokens exchange information with each other.
- an **MLP module** (multilayer perceptron, also called the feedforward network or FFN). It processes each token's vector on its own: multiply by a matrix (a *linear layer*), apply a simple bend called a **nonlinear activation**, multiply by another matrix. Common activations are ReLU, which replaces negative numbers with zero ($\max(0,x)$), and GELU, a smoother version that GPT-2 and GPT-3 used. The bend matters: without it, a stack of matrix multiplications collapses into a single multiplication and the model could only learn straight-line relationships.

Before the blocks sits an **embedding module**. It holds a table with one learned vector per vocabulary token (the token embedding) and, in the original design, one learned vector per position in the text (the positional embedding), so the model can tell "dog bites man" from "man bites dog". With a table of position vectors, the number of rows in that table sets the maximum **context length**, the most tokens the model can take in at once, though there are tricks to extend it. After the blocks sits an **output layer**, also called the unembedding layer or *model head*, which turns the final vector into one score per vocabulary token; softmax turns those scores into the next-token probabilities.

Model size is driven by the model dimension, the number of blocks, the feedforward dimension (the width of the middle of the MLP) and the vocabulary size. From the book's table of Meta's Llama models (K is thousand, B is billion):

| Model | Vocab | Model dim | FFN dim | Blocks |
|---|---|---|---|---|
| Llama 2-7B | 32K | 4,096 | 11,008 | 32 |
| Llama 2-13B | 32K | 5,120 | 13,824 | 40 |
| Llama 2-70B | 32K | 8,192 | 22,016 | 80 |
| Llama 3-8B | 128K | 4,096 | 14,336 | 32 |
| Llama 3-70B | 128K | 8,192 | 28,672 | 80 |
| Llama 3-405B | 128K | 16,384 | 53,248 | 126 |

Context length affects memory but **not** the parameter count: a longer prompt means more saved key and value vectors, not more dials.

### Alternatives

Transformers have been dominant since 2017, longer than seq2seq (2014–2018) or GANs (generative adversarial networks, an image-generation design popular from 2014 to 2019). Challengers include **RWKV** (an RNN redesigned so it can be trained in parallel) and **state space models (SSMs)**, a family that keeps a compact running state instead of attending over every earlier token: S4, H3, **Mamba** (whose cost grows in direct proportion to the text length, where attention's grows with its square), and **Jamba**, a hybrid of transformer and Mamba layers with mixture-of-experts (explained below). Any replacement has to perform at the scale and on the hardware people care about. That is a high bar after years of transformer tuning.

## 3. Model size: parameters, tokens, FLOPs

Three numbers describe scale:

1. **Number of parameters**, a rough indicator of learning capacity. More parameters also means more memory, and the arithmetic is one multiplication: parameters times bytes per parameter. A model with 7 billion parameters ("7B") stored at 2 bytes each needs $7 \times 10^9 \times 2 = 14 \times 10^9$ bytes, which is at least 14 GB (gigabytes) for its weights alone, before any working memory.
2. **Number of training tokens**, a rough indicator of how much the model learned. Dataset tokens and *training* tokens differ. One full pass over the training data is called an **epoch**; two epochs over a dataset of 1 trillion tokens ("1T") is 2T training tokens. Meta trained Llama 1, 2 and 3 on 1.4T, 2T and 15T tokens. The open dataset RedPajama-v2 has 30T tokens, but much of it is low quality.
3. **Number of FLOPs**, the amount of computing work used to train. A **FLOP** is one floating-point operation: a single addition or multiplication of two decimal numbers. Training GPT-3 (175B parameters) took about $3.14\times10^{23}$ of them, a 3 followed by 23 digits. Do not confuse **FLOPs** (an amount of work, like kilometres) with **FLOP/s** (a machine's speed, like kilometres per hour).

### Sparse models and mixture-of-experts

A **dense** model uses every parameter for every token. A **sparse** model has many zero-valued parameters or activates only part of itself each time. A **mixture-of-experts (MoE)** model is the common sparse design: inside each block there are several alternative MLPs called *experts*, and a small routing step sends each token to only a few of them. Mixtral 8x7B has eight experts and 46.7B total parameters (not $8 \times 7 = 56$B, because the attention parts are shared), but each token passes through only two experts, so only **12.9B parameters are active per token**. Its cost and speed therefore match a 12.9B dense model, while it must still hold all 46.7B in memory.

The next demo estimates training compute and cost. In words, the rule of thumb says: the work to train a model is about six operations for every parameter, for every training token. With $N$ parameters and $D$ training tokens:

$$C \approx 6 \times N \times D$$

Worked example for GPT-3: $6 \times 175 \times 10^{9} \times 300 \times 10^{9} = 3.15 \times 10^{23}$ FLOPs. To turn work into time, divide by the speed of your machines; to turn time into money, multiply by the rental price.

```python-run
# Rough training compute and cost (rule of thumb: ~6 FLOPs per parameter per training token).
def train_flops(params, tokens):
    return 6 * params * tokens

for name, N, D in [("GPT-3 175B", 175e9, 300e9), ("Chinchilla 70B", 70e9, 1.4e12), ("Llama 3 70B", 70e9, 15e12)]:
    F = train_flops(N, D)
    # assume 256 H100s at 1e15 FLOP/s peak, 40% utilization, 2 USD/h each
    seconds = F / (256 * 1e15 * 0.40)
    cost = seconds / 3600 * 256 * 2
    print(f"{name:14s} {F:9.2e} FLOPs  ~{seconds/86400:6.1f} days on 256 GPUs  ~{cost/1e6:5.1f}M USD")
```

**Reading this Python line by line**

- `def train_flops(params, tokens):` defines a small function; `return 6 * params * tokens` is the rule above.
- `175e9` is Python's scientific notation for $175 \times 10^9$. The `for` line walks through three (name, parameters, tokens) triples and unpacks each into `name, N, D`.
- `seconds = F / (256 * 1e15 * 0.40)` divides the work by the speed of the cluster. The comment states the assumptions: 256 Nvidia H100 GPUs, each capable of $10^{15}$ FLOP/s at its peak, but achieving only 40% of that in real training (the fraction achieved is called **utilization**).
- `cost = seconds / 3600 * 256 * 2` converts seconds to hours, then multiplies by 256 GPUs at 2 US dollars per GPU-hour.
- Output: GPT-3 needs about $3.15 \times 10^{23}$ FLOPs, roughly 36 days on this cluster and about 0.4 million dollars; Chinchilla about 67 days and 0.8 million; Llama 3 70B, trained on 15T tokens, about $6.3 \times 10^{24}$ FLOPs, around 712 days and 8.8 million dollars. The numbers are rough, but they show why training tokens matter as much as parameters: Llama 3 70B is smaller than GPT-3 and costs twenty times more to train.

The 6·N·D rule is a standard approximation. Training has two halves for every example: the **forward pass**, where the model computes its prediction (about 2 FLOPs per parameter per token), and the **backward pass**, where it works out how to adjust each parameter (about 4). It is useful for back-of-envelope budgeting. The demo's result for GPT-3 lands close to the $3.14\times10^{23}$ reported in the book.

### Scaling law: compute-optimal models

Given a fixed compute budget, what model size and how many tokens should you use? A huge model shown too little text wastes its capacity; a tiny model shown endless text cannot absorb it. A **scaling law** is an experimentally found rule for how these quantities should grow together. DeepMind's **Chinchilla** paper (2022) trained 400 models, from 70M to 16B parameters on 5B to 500B tokens, and found:

> For compute-optimal training, the number of training tokens should be about **20× the number of parameters**, and both should be scaled together. Double the model, double the data.

"Compute-optimal" means: the best quality you can get for a given amount of training compute. A 3B model therefore wants about $20 \times 3\text{B} = 60$B tokens. In the book's table, GPT-3 (175B parameters, 300B tokens, a ratio under 2) and DeepMind's Gopher (280B, 300B) were badly under-trained, while Chinchilla-70B was trained on 1.4T tokens (ratio 20) and outperformed them despite being smaller.

$$
D_{\text{opt}} \approx 20\,N \qquad\text{and}\qquad C \approx 6 N D
$$

Here $D_{\text{opt}}$ is the best number of training tokens for a model of $N$ parameters, and $C$ is the compute from the rule above. Substituting the first into the second gives $C \approx 6 \times N \times 20N = 120N^2$, so $N = \sqrt{C / 120}$: from a budget you can solve for the model size. With $C = 10^{22}$ FLOPs, $N = \sqrt{10^{22}/120} \approx 9.1 \times 10^{9}$, a 9B model trained on about 183B tokens. The second demo below does this for five budgets.

Caveats from the book:

- The law assumes data is much cheaper than compute. It was derived for **dense models on mostly human-generated data**. MoE models and **synthetic data** (data generated by AI instead of written by people) are open research questions.
- **Production is not only quality.** Llama's authors deliberately trained *smaller* models on *more* data than Chinchilla-optimal because smaller models are cheaper to serve. Sardana and colleagues (2023) adjusted the law to account for how much inference a model will do over its life.
- **Diminishing returns.** Going from a 3% to a 2% error rate can need an *order of magnitude* (ten times) more data or compute. A model's **loss** is the number training tries to push down, a measure of how surprised the model is by the true next token; for language models it is measured in units called nats (Module 3 explains them). Lowering it from roughly 3.4 nats to 2.8 took ten times as much data, though users do notice that difference.

```python-run
# Chinchilla-style allocation: given compute C, solve N, D with D = 20N and C = 6ND.
import math
for C in [1e21, 1e22, 1e23, 1e24, 1e25]:
    N = math.sqrt(C / (6 * 20))
    D = 20 * N
    print(f"C={C:.0e} FLOPs -> params ~{N/1e9:7.2f}B, tokens ~{D/1e9:9.1f}B")
```

Here `math.sqrt` takes the square root from the formula $N = \sqrt{C/120}$ (written as `6 * 20` in the code), and `D = 20 * N` applies the 20-to-1 rule. The output starts at about 2.89B parameters and 57.7B tokens for $10^{21}$ FLOPs and ends near 289B parameters and 5,774B tokens for $10^{25}$. Notice the pattern: a budget 100 times larger buys a model only 10 times larger, because the data has to grow along with it.

### Scaling extrapolation and emergent abilities

Big models are too expensive to train many times, so researchers tune hyperparameters (the settings chosen before training, such as learning speed) on small models and **extrapolate**, meaning they assume the best settings carry over to the big one. This is called hyperparameter transfer. Microsoft and OpenAI showed that settings tuned on a 40M-parameter model carried over to one with 6.7B parameters. It is hard to do well: ten hyperparameters with only two options each already give $2^{10} = 1{,}024$ combinations, and **emergent abilities**, skills that appear only once a model is large enough and are absent in small ones, make extrapolation less reliable.

### Scaling bottlenecks

A **bottleneck** is the narrowest point in a process, the one that limits everything else. Model size grew three orders of magnitude (a factor of about a thousand) between 2018 and 2021, from GPT-1 at 117M parameters to GPT-3 at 175B. Two bottlenecks are now visible:

1. **Data.** Training sets are growing faster than new data is produced (a finding by Villalobos and colleagues). Anything you post online probably will be training data. The web is also filling with AI-generated text. When Grok, the chatbot from the company xAI, refused a request by citing OpenAI's policy, one of its developers explained that the web is full of ChatGPT outputs and Grok had picked some up. Training models on the output of earlier models, round after round, can cause **model collapse**, a gradual loss of quality and variety (Module 8). Private data such as books, contracts, medical records and conversations becomes a competitive advantage, and many publishers now forbid crawlers.
2. **Electricity.** Data centers (the buildings full of computers that run these models) are estimated to use 1–2% of global electricity and are projected to reach 4–20% by 2030, which limits how far compute can grow.

> [!INTERVIEW]
> **"Explain the Chinchilla scaling law and why Llama ignored it."** For a fixed compute budget, the loss-optimal split is about 20 training tokens per parameter, scaling both together. Chinchilla-optimal minimizes *training* compute for a given quality. Llama's authors trained smaller models on far more tokens because inference cost over a model's lifetime dominates. A smaller over-trained model is cheaper to serve and easier to adopt.

## Pitfalls

- Treating parameter count as quality. An under-trained large model can lose to a smaller, well-trained one, and a 13B model trained on one sentence is useless.
- Comparing MoE and dense models on total parameters. Compare **active** parameters for cost and speed.
- Mixing up FLOPs and FLOP/s.
- Ignoring tokenizer differences when estimating cost across languages.

## Summary

- Training data decides what a model can do. Web data is dominated by English and has quality problems, which hurts low-resource languages (worse quality, higher token cost) and niche domains.
- Transformers replaced seq2seq by using attention (look anywhere in the input) and parallel input processing. Inference splits into parallel prefill and sequential decode.
- A model is embedding + N transformer blocks (attention + MLP) + output layer. Size comes from model dimension, number of layers, FFN dimension and vocabulary.
- Scale is parameters, tokens and FLOPs. Chinchilla says about 20 tokens per parameter for compute-optimal training, but production often favours smaller models trained longer.
- Scaling now runs into limits on data (and AI-generated contamination) and electricity.

## Glossary

- **Common Crawl / C4**: a public archive of crawled web pages, and Google's cleaned subset of it; common training-data sources.
- **Low-resource language**: a language with little text available for training.
- **Domain**: a subject area with its own vocabulary and documents, such as medicine or law.
- **Architecture**: the blueprint of a model's calculations and where its parameters sit.
- **Neural network**: a model built from chains of multiply-and-add steps with learned multipliers.
- **Vector / dimension**: an ordered list of numbers; how many numbers it holds.
- **Matrix**: a grid of numbers; multiplying a vector by it transforms the vector.
- **Dot product**: multiply two vectors position by position and add; used as a similarity score.
- **RNN / hidden state**: a network that reads one token at a time; its running summary vector.
- **seq2seq, encoder, decoder**: the pre-transformer design in which one RNN reads the input and another writes the output.
- **Attention**: the mechanism that lets a token draw information from any other token, weighted by relevance.
- **Query, key, value**: the three vectors per token that attention compares and blends.
- **Softmax**: the function that turns a list of scores into positive weights adding up to 1.
- **Causal mask**: the rule that a token may attend only to itself and earlier tokens.
- **Transformer block / layer**: one attention module plus one MLP module; models stack many.
- **MLP (feedforward network)**: the per-token part of a block: matrix, activation, matrix.
- **Activation function**: a simple nonlinear bend such as ReLU or GELU.
- **Context length**: the maximum number of tokens a model can take in at once.
- **Prefill / decode**: processing the input in parallel; generating output one token at a time.
- **KV cache**: the saved key and value vectors of earlier tokens.
- **Epoch**: one full pass over the training data.
- **FLOP / FLOP/s**: one floating-point operation (work); operations per second (speed).
- **Dense / sparse model**: all parameters used for every token; only part of them used.
- **Mixture-of-experts (MoE)**: a sparse design that routes each token to a few of several expert modules.
- **Scaling law (Chinchilla)**: about 20 training tokens per parameter gives the best quality for a fixed training budget.
- **Loss**: the number training minimizes; how surprised the model is by the right answer.
- **Emergent ability**: a skill that appears only in sufficiently large models.
- **Model collapse**: quality decay from training repeatedly on AI-generated data.

```quiz
[
  {"q": "What two seq2seq limitations did the transformer address?", "options": ["Too many parameters and too little data", "The decoder only saw the final hidden state, and RNN processing was sequential", "No tokenizer and no softmax", "It could not do translation"], "answer": 1, "explain": "Attention lets the decoder look at any input token, and removing RNNs lets input tokens be processed in parallel."},
  {"q": "Why is the decode phase of transformer inference sequential?", "options": ["Because of the tokenizer", "Each output token depends on previously generated tokens (autoregression)", "Because attention cannot be parallelized at all", "Because GPUs are slow"], "answer": 1, "explain": "Inputs can be prefilled in parallel, but each new output token is conditioned on the ones before it."},
  {"q": "According to the Chinchilla scaling law, a compute-optimal 10B-parameter model should be trained on roughly…", "options": ["10B tokens", "200B tokens", "2T tokens", "20T tokens"], "answer": 1, "explain": "About 20 tokens per parameter: 20 × 10B = 200B tokens."},
  {"q": "Mixtral 8x7B has 46.7B parameters. Why does it cost about the same to run as a 12.9B model?", "options": ["It is quantized to 4 bits", "Only 2 experts (about 12.9B params) are active per token", "It uses a smaller vocabulary", "It skips the attention layers"], "answer": 1, "explain": "In a mixture-of-experts model only a subset of experts processes each token, so active parameters determine cost and speed."},
  {"q": "What is the difference between FLOPs and FLOP/s?", "options": ["They are synonyms", "FLOPs measure a task's compute requirement; FLOP/s measure a machine's speed", "FLOP/s measure memory", "FLOPs only apply to inference"], "answer": 1, "explain": "FLOPs is a quantity of work, and FLOP/s is a rate. Mixing them up is a common source of wrong estimates."},
  {"q": "Why did Meta train Llama models smaller (and on more tokens) than Chinchilla-optimal?", "options": ["They had no data", "Smaller models are cheaper and easier to serve, which helps adoption", "Chinchilla's law was not published yet", "Larger models cannot be trained"], "answer": 1, "explain": "Chinchilla minimizes training compute for a given quality. Production also cares about inference cost, which favors smaller over-trained models."},
  {"q": "Which effect does under-representation of a language in training data NOT typically have?", "options": ["Worse benchmark performance in that language", "More tokens needed for the same content, raising cost", "Lower perplexity on that language", "Higher latency for those users"], "answer": 2, "explain": "Under-representation usually makes the model worse (higher perplexity) and more expensive in tokens for that language."},
  {"q": "Does increasing a model's maximum context length increase its parameter count?", "options": ["Yes, linearly", "Not necessarily; it raises memory (e.g., KV cache) but parameters are set by dimensions, layers and vocab", "Yes, quadratically", "Only for MoE models"], "answer": 1, "explain": "Huyen notes that context length affects the memory footprint but not the total parameter count."}
]
```

> **Source:** Huyen, *AI Engineering*, ch. 2 ("Training Data", "Modeling": model architecture, model size, scaling law and bottlenecks).
