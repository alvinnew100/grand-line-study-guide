# Training data, architecture and scale

You do not need to train a foundation model to build with one. You do need to know how the model was made, because that explains its strengths, its blind spots and its quirks. Huyen groups the key design decisions into **training data**, **modeling** (architecture and size) and **post-training**, and adds **sampling** as the often-overlooked step that turns probabilities into output. This lesson covers data, architecture and scale. The next two cover post-training and sampling.

> [!NOTE]
> A deeper, code-level treatment of transformers (multi-head attention, positional encodings, implementing a block) lives in the **LLM Practice** track. Here we focus on what an AI engineer needs in order to reason about cost, capability and choice of model.

## 1. Training data: a model is only as good as its data

If there is no Vietnamese in the training data, the model cannot translate English into Vietnamese. Model developers often have to "use what we have, not what we want."

A common source is **Common Crawl**, a nonprofit's periodic crawl of the web (about 2–3 billion pages a month in 2022–2023). Google's cleaned subset is **C4**. The quality is questionable: clickbait, misinformation, propaganda and toxic content. Yet most models that disclose their sources use some version of it, including GPT-3 and Gemini. Many companies have stopped disclosing their training data at all. Heuristic filters help a little. GPT-2, for example, only used Reddit links with at least three upvotes.

### Multilingual models

English dominates the web. In Common Crawl, English is about **45.88%** of the data while English speakers are about 18% of the world population. Other languages are badly under-represented. Huyen's table (from Lai et al.) shows Punjabi, Swahili and Urdu with population-to-Common-Crawl ratios above 100. The consequences:

- GPT-4's MMLU scores are much worse in languages like Telugu, Marathi and Punjabi, which are among the most under-represented.
- On six Project Euler math problems, GPT-4 solved English versions more than three times as often as Armenian or Farsi, and failed all six in Burmese and Amharic.
- **Tokenization cost.** Under-represented languages need many more tokens for the same content. Huyen cites a median token length for the same text roughly ten times higher in Burmese than in English, which makes those users pay more and wait longer.
- Translating to English and back loses information. Vietnamese pronouns that encode the relationship between speakers all collapse to "I" and "you".

### Domain-specific models

General models know common domains (coding, law, science, business) but struggle with data that is rare on the public web: drug discovery, cancer screening, proprietary formats. Hence domain-specific models such as DeepMind's **AlphaFold** (protein structure), NVIDIA's **BioNeMo** (biomolecular data) and Google's **Med-PaLM2** (medical queries).

> [!TIP]
> When choosing a model for a non-English or niche-domain application, do not rely on English leaderboards. Evaluate on your own language and domain data (Module 4), and estimate token costs with that model's tokenizer on your actual text.

## 2. Architecture: why transformers won

### The problem transformers solved

Before transformers, **seq2seq** (2014) used an RNN **encoder** to compress the input into a final hidden state and an RNN **decoder** to generate output from it. It had two problems:

1. The decoder saw only the *final hidden state*. Huyen compares this to answering questions about a book using only its summary.
2. RNNs are **sequential**, so a 200-token input had to be processed one token at a time.

The **attention mechanism** fixes the first problem by letting the model weigh *any* input token when producing each output token, like looking up any page of the book. The transformer (Vaswani et al., 2017) dropped RNNs entirely, which fixed the second problem: input tokens are processed **in parallel**. (Attention itself predates the transformer. Google's GNMT used it with seq2seq in 2016.)

Output generation is still sequential, though. Transformer inference therefore has two phases, a distinction you will meet again in Module 9:

- **Prefill**: process all input tokens in parallel and build the key/value vectors. This is compute-bound.
- **Decode**: generate one token at a time. This is memory-bandwidth-bound.

### Attention in one formula

Each token is projected into a **query** $q = xW_Q$, a **key** $k = xW_K$ and a **value** $v = xW_V$. In the book analogy, the query is the person looking for information, each key is a page number, and each value is the page's content. Attention scores compare the query with every key, and the output is a weighted sum of values:

$$
\text{Attention}(Q,K,V) = \operatorname{softmax}\!\left(\frac{QK^\top}{\sqrt{d}}\right)V
$$

The $\sqrt{d}$ scaling keeps dot products from growing with dimension and saturating the softmax. Because every previous token's key and value must be kept for each new token, **longer contexts mean more K/V vectors to compute and store**. This is the KV cache that dominates inference memory (Module 9). In practice attention is **multi-headed**: Llama 2-7B, for example, has 32 heads of dimension 128 (4096 / 32), and the head outputs are concatenated and passed through an **output projection** matrix.

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

### The transformer block and the full model

A transformer is a stack of **transformer blocks**, and the number of blocks is the model's number of **layers**. Each block has:

- an **attention module** with four weight matrices: query, key, value and output projection.
- an **MLP (feedforward) module**: linear layers separated by nonlinear activations such as ReLU ($\max(0,x)$) or GELU, which GPT-2 and GPT-3 used.

Before the blocks sits an **embedding module** (token embeddings plus positional embeddings). Naively, the number of position indices sets the maximum context length, though there are tricks to extend it. After the blocks sits an **output layer**, also called the unembedding layer or *model head*, which maps hidden vectors to token probabilities.

Model size is driven by the model dimension, the number of blocks, the feedforward dimension and the vocabulary size. From the book's Llama table:

| Model | Blocks | Model dim | FFN dim | Vocab |
|---|---|---|---|---|
| Llama 2-7B | 32 | 4,096 | 11,008 | 32K |
| Llama 2-13B | 40 | 5,120 | 13,824 | 32K |
| Llama 2-70B | 80 | 8,192 | 22,016 | 32K |
| Llama 3-8B | 32 | 4,096 | 14,336 | 128K |
| Llama 3-70B | 80 | 8,192 | 28,672 | 128K |
| Llama 3-405B | 126 | 16,384 | 53,248 | 128K |

Context length affects memory but **not** the parameter count.

### Alternatives

Transformers have been dominant since 2017, longer than seq2seq (2014–2018) or GANs (2014–2019). Challengers include **RWKV** (an RNN that can be trained in parallel) and **state space models (SSMs)**: S4, H3, **Mamba** (which scales linearly with sequence length), and **Jamba**, a hybrid of transformer and Mamba layers with mixture-of-experts. Any replacement has to perform at the scale and on the hardware people care about. That is a high bar after years of transformer optimization.

## 3. Model size: parameters, tokens, FLOPs

Three numbers describe scale:

1. **Number of parameters**, a proxy for learning capacity. More parameters also means more memory. A 7B model at 2 bytes per parameter needs at least 14 GB just for its weights.
2. **Number of training tokens**, a proxy for how much the model learned. Dataset tokens and *training* tokens differ: two epochs over 1T tokens is 2T training tokens. Meta trained Llama 1, 2 and 3 on 1.4T, 2T and 15T tokens. RedPajama-v2 has 30T tokens, but much of it is low quality.
3. **Number of FLOPs**, the compute used to train. GPT-3-175B used about $3.14\times10^{23}$ FLOPs. Do not confuse **FLOPs** (an amount of work) with **FLOP/s** (a machine's speed).

### Sparse models and mixture-of-experts

A **sparse** model has many zero-valued parameters or activates only part of itself. In a **mixture-of-experts (MoE)** model, only some experts are active per token. Mixtral 8x7B has 46.7B total parameters (not 56B, because some are shared), but only **12.9B are active per token**, so its cost and speed match a 12.9B dense model.

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

The 6·N·D rule is a standard approximation (2 FLOPs for the forward pass and 4 for the backward pass, per parameter per token). It is useful for back-of-envelope budgeting. The demo's result for GPT-3 lands close to the $3.14\times10^{23}$ reported in the book.

### Scaling law: compute-optimal models

Given a fixed compute budget, what model size and how many tokens should you use? DeepMind's **Chinchilla** paper (2022) trained 400 models, from 70M to 16B parameters on 5B to 500B tokens, and found:

> For compute-optimal training, the number of training tokens should be about **20× the number of parameters**, and both should be scaled together. Double the model, double the data.

A 3B model therefore wants about 60B tokens. In the book's table, GPT-3 (175B parameters, 300B tokens) and Gopher (280B, 300B) were badly under-trained, while Chinchilla-70B was trained on 1.4T tokens and outperformed them.

$$
D_{\text{opt}} \approx 20\,N \qquad\text{and}\qquad C \approx 6 N D
$$

Caveats from the book:

- The law assumes data is much cheaper than compute. It was derived for **dense models on mostly human-generated data**. MoE models and synthetic data are open research questions.
- **Production is not only quality.** Llama's authors deliberately trained *smaller* models on *more* data than Chinchilla-optimal because smaller models are cheaper to serve. Sardana et al. (2023) adjusted the law to account for inference demand.
- **Diminishing returns.** Going from a 3% to a 2% error rate can need an order of magnitude more data or compute. Dropping language-modeling loss from about 3.4 to 2.8 nats needed 10× more data, though users do notice that difference.

```python-run
# Chinchilla-style allocation: given compute C, solve N, D with D = 20N and C = 6ND.
import math
for C in [1e21, 1e22, 1e23, 1e24, 1e25]:
    N = math.sqrt(C / (6 * 20))
    D = 20 * N
    print(f"C={C:.0e} FLOPs -> params ~{N/1e9:7.2f}B, tokens ~{D/1e9:9.1f}B")
```

### Scaling extrapolation and emergent abilities

Big models are too expensive to train many times, so researchers study hyperparameters on small models and **extrapolate** (hyperparameter transfer). Microsoft and OpenAI transferred hyperparameters from a 40M model to a 6.7B model. It is hard to do well: ten hyperparameters already give 1,024 combinations, and **emergent abilities**, which appear only at scale, make extrapolation less reliable.

### Scaling bottlenecks

Model size grew three orders of magnitude between 2018 and 2021 (GPT-1 at 117M to GPT-3 at 175B). Two bottlenecks are now visible:

1. **Data.** Training sets are growing faster than new data is produced (Villalobos et al.). Anything you post online probably will be training data. The web is also filling with AI-generated text. When Grok refused a request by citing OpenAI's policy, one of its developers said the web is full of ChatGPT outputs. Recursive training on AI data can cause **model collapse** (Module 8). Proprietary data such as books, contracts, medical records and conversations becomes a competitive advantage, and many publishers now restrict crawling.
2. **Electricity.** Data centers are estimated to use 1–2% of global electricity and are projected to reach 4–20% by 2030, which limits how far compute can grow.

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
