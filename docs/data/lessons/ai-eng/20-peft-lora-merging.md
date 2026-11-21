# PEFT, LoRA, model merging and hyperparameters

> **Before this lesson:** read [Memory math, numerical formats and quantization](#/lesson/ai-eng/aie-memory-quant), which explains trainable versus frozen parameters, why full finetuning needs so much memory, and what 4-bit quantization is. [When (and when not) to finetune](#/lesson/ai-eng/aie-when-finetune) explains why you would finetune at all. A little matrix arithmetic is introduced from scratch in section 2.

## In plain words

Full finetuning updates every one of a model's billions of weights, and the previous lesson's memory math shows why that is out of reach for most teams. **Parameter-efficient finetuning (PEFT)** gets close to the quality of full finetuning while training only a tiny fraction of the parameters, often less than 1%. **LoRA** is by far the most popular PEFT method. This lesson also covers **model merging** (combining several finetuned models into one without further training) and the practical tactics: choosing a base model and method, and setting the main **hyperparameters** (the settings you choose before training, such as how fast the model learns).

An everyday picture: you have a printed encyclopaedia (the pre-trained model) and want it to reflect your company's way of doing things. Reprinting every page (full finetuning) is enormously expensive. Instead you add a slim booklet of sticky-note corrections that sit on top of the original pages (LoRA). The encyclopaedia is untouched, the booklet is tiny, you can keep a different booklet for each customer, and you can even reprint a page with its notes merged in once you are sure. Model merging is like combining two colleagues' correction booklets into one.

Why this matters for a job: LoRA and QLoRA are how most teams finetune open models today, and "explain LoRA and why it adds no inference latency" is a standard interview question. Knowing the parameter arithmetic, the typical settings and the serving options lets you plan a finetuning project realistically.

## 1. Why PEFT?

Early models were small enough for **full finetuning**. As they grew, people tried **partial finetuning**: freeze the earlier **layers** (the stacked processing stages of a neural network) and update only the last few. That saves memory but is **parameter-inefficient**. Houlsby and colleagues (2019) found that on BERT-large, partial finetuning had to update about **25%** of the parameters to come close to full finetuning on the GLUE benchmark.

The same paper introduced **adapters**: small extra modules inserted into each transformer block, with only the adapters trained. They came within **0.4%** of full finetuning's performance while training about **3%** of the parameters. That started PEFT. A method counts as parameter-efficient if it approaches full finetuning with orders of magnitude fewer trainable parameters. PEFT methods also tend to be **sample-efficient**: a few thousand examples can be enough where full finetuning might want tens of thousands to millions.

The original adapters have one drawback: their extra layers add **inference latency**, because every forward pass has more to compute.

### PEFT families

- **Adapter-based (additive) methods** add trainable modules to the model's weights: the original adapters, **LoRA** and its variants (DoRA, QLoRA, LoRA+), BitFit and IA3.
- **Soft-prompt methods** leave the model's architecture alone and add trainable **continuous vectors**, called *soft prompts*, to the input (or to every layer), which are optimised by backpropagation. A *hard prompt* is ordinary text made of tokens you can read; a soft prompt is a list of learned numbers that does not correspond to any words. Variants are **prefix-tuning** (vectors added at every layer), **P-tuning** and **prompt tuning** (vectors added only at the input).

Huyen's analysis of GitHub issues in Hugging Face's PEFT library found LoRA dominating by a wide margin. Soft-prompt methods are less common but appeal to people who want more control than prompting offers without full finetuning.

## 2. LoRA

**LoRA (Low-Rank Adaptation)** (Hu and colleagues, 2021) adds trainable parameters in a way that costs **no extra inference latency**, because its modules can be **merged back** into the original weights after training.

### A little matrix arithmetic first

A **matrix** is a rectangular grid of numbers; its **shape** $n \times m$ means $n$ rows and $m$ columns. Most of a transformer's weights live in matrices. The **product** of an $n \times r$ matrix $A$ and an $r \times m$ matrix $B$ is an $n \times m$ matrix $AB$, where each entry is a row of $A$ dotted with a column of $B$. Small example:

$$A = \begin{bmatrix}1\\ 2\end{bmatrix},\quad B = \begin{bmatrix}3 & 4\end{bmatrix},\quad AB = \begin{bmatrix}1\cdot3 & 1\cdot4\\ 2\cdot3 & 2\cdot4\end{bmatrix} = \begin{bmatrix}3 & 4\\ 6 & 8\end{bmatrix}$$

$A$ and $B$ together hold 4 numbers and produce a 2-by-2 matrix of 4 numbers, so no saving yet. But a $9 \times 1$ times a $1 \times 9$ produces a $9 \times 9$ matrix (81 numbers) from only 18. The **rank** of a matrix is, informally, how many independent patterns it contains; a matrix built as a product through a middle dimension $r$ has rank at most $r$. A **low-rank** matrix can be stored very cheaply as two thin factors.

### How LoRA works

For one weight matrix $W$ of shape $n \times m$:

1. Choose a small rank $r$. Create $A$ of shape $n \times r$ and $B$ of shape $r \times m$. Their product $AB$ has the same shape as $W$.
2. Use the adapted weight, where $\alpha$ (alpha) is a scaling hyperparameter:

$$W' = W + \frac{\alpha}{r}\,AB$$

3. During finetuning, update only $A$ and $B$. $W$ stays **frozen**.

In words: the model's behaviour is changed by adding a low-rank correction to each chosen matrix, and only the correction is trained. The trainable parameter count for one matrix falls from $n \times m$ to $r\,(n+m)$:

$$\text{LoRA params} = r \times (n + m)$$

Worked example: for a $4096 \times 4096$ matrix (16.8 million parameters) and $r = 8$, LoRA trains $8 \times (4096 + 4096) = 65{,}536$ parameters, about 0.39% of the matrix.

```python-run
import numpy as np
rng = np.random.default_rng(0)
n, m, r, alpha = 512, 512, 8, 16
W = rng.normal(0, 0.02, (n, m))
A = rng.normal(0, 0.01, (n, r))          # one factor random
B = np.zeros((r, m))                     # the other zero => AB = 0, so training starts exactly at W
x = rng.normal(size=m)
print("before training, outputs identical:", np.allclose(W @ x, (W + alpha / r * A @ B) @ x))
B = rng.normal(0, 0.01, (r, m))          # pretend training updated B
W_merged = W + alpha / r * A @ B         # merge once -> no extra inference latency
print("merged == unmerged path:", np.allclose(W_merged @ x, W @ x + alpha / r * A @ (B @ x)))
print(f"full params {n*m:,}  LoRA params {r*(n+m):,}  ({r*(n+m)/(n*m):.2%})  rank of update = {np.linalg.matrix_rank(A @ B)}")
```

**Reading this Python line by line**

- `W` is a frozen 512-by-512 weight matrix with small random values; `x` is an input vector.
- `A` starts random and `B` starts as all zeros (`np.zeros((r, m))`). That makes $AB = 0$, so at the start of training the adapted model behaves exactly like the original. This is the standard LoRA initialisation.
- `@` is matrix multiplication. `np.allclose(p, q)` checks that two arrays are equal up to tiny rounding differences. The first print confirms identical outputs before training.
- `B = rng.normal(...)` pretends training has changed `B`. `W_merged` folds the update into the weights once. The second print shows that the merged matrix gives the same output as computing the original path plus the low-rank path separately, which is why merging adds no latency.
- `np.linalg.matrix_rank(A @ B)` computes the rank of the update.
- Output: `True`, `True`, then 262,144 full parameters versus 8,192 LoRA parameters (3.12%; the share is larger than 0.39% because this matrix is small), and the update's rank is 8.

For GPT-3, the LoRA paper reports matching or beating full finetuning on several tasks while training about **4.7 million** parameters, **0.0027%** of the full model.

With the Hugging Face PEFT library, applying LoRA takes a few lines (static example; it needs a downloaded model):

```python
from peft import LoraConfig, get_peft_model
config = LoraConfig(r=8, lora_alpha=16, target_modules=["q_proj", "v_proj"], lora_dropout=0.05)
model = get_peft_model(base_model, config)     # wraps the chosen matrices with A and B
model.print_trainable_parameters()             # e.g. a fraction of a percent of all parameters
```

`r` and `lora_alpha` are the rank and $\alpha$; `target_modules` names the matrices to adapt (here the query and value projections); `lora_dropout` randomly ignores some adapter outputs during training to reduce overfitting.

### Why does LoRA work?

If a model needs billions of parameters to learn its behaviour in pre-training, why can it be adapted with so few? Research (Li and colleagues, 2018; Aghajanyan and colleagues, 2020; Hu and colleagues, 2021) argues that large pre-trained models have a very low **intrinsic dimension**: the changes needed to adapt them lie in a small subspace, so a few well-chosen directions are enough. Pre-training implicitly compresses the model, and *larger* models tend to end up with *lower* intrinsic dimension. The better a model is pre-trained, the easier it is to finetune with few parameters and little data.

Could you pre-train with low-rank factors from the start? Low-rank training works at small scale (SqueezeNet matched AlexNet's accuracy with 50 times fewer parameters), and ReLoRA and GaLore show progress up to roughly 1B to 7B parameters. But if it is pre-training that lowers the intrinsic dimension, full-rank pre-training may still be needed first.

### LoRA configurations

**Which matrices?** LoRA is mostly applied to the **attention** matrices, the weights a transformer uses to decide which earlier tokens to focus on: the query matrix $W_q$, key $W_k$, value $W_v$ and output projection $W_o$. It is usually applied uniformly, to the same kinds of matrix in every layer. With a fixed budget of 18 million trainable parameters on GPT-3 175B (96 layers, model dimension 12,288), the LoRA paper found:

| Applied to | Rank | WikiSQL | MultiNLI |
|---|---|---|---|
| $W_q$ only | 8 | 70.4 | 91.0 |
| $W_k$ only | 8 | 70.0 | 90.8 |
| $W_v$ only | 8 | 73.0 | 91.0 |
| $W_q, W_v$ | 4 | 73.7 | 91.3 |
| $W_q, W_k, W_v, W_o$ | 2 | 73.7 | 91.7 |

Spreading a low rank over more matrices beat a high rank on one. Check the budget: rank 2 on a $12{,}288 \times 12{,}288$ matrix is $2 \times (12{,}288 + 12{,}288) = 49{,}152$ parameters; four matrices make 196,608 per layer, and 96 layers make 18,874,368. If you can adapt only two matrices, **query and value** are generally best. Later evidence suggests adapting more matrices, including the **feedforward** layers (the part of each transformer block that processes each token on its own), helps further; Databricks reported its biggest improvement from that.

**Rank $r$.** A small rank, between **4 and 64**, is usually enough. The LoRA authors found that raising $r$ did not improve results, and a higher rank can overfit. Some tasks need more: Raschka found $r = 256$ best on his.

**Alpha $\alpha$.** This scales how strongly $AB$ affects the output. Huyen has often seen the ratio $\alpha : r$ between 1:8 and 8:1, and a small $r$ often pairs with a larger $\alpha$. Experiment.

### Serving LoRA adapters

1. **Merge** $A$ and $B$ into $W$ before serving. This adds no latency and is best when you serve one finetuned model.
2. **Keep the adapters separate** and combine them at inference time. This adds a little latency but enables **multi-LoRA serving**, where many adapters share one copy of the base model.

Worked example: 100 customer-specific models, each adapting one $4096 \times 4096$ matrix with $r = 8$. Option 1 stores $16.8\text{M} \times 100 = 1.68$ billion parameters. Option 2 stores the base once plus 100 adapters: $16.8\text{M} + 65{,}536 \times 100 \approx 23.3\text{M}$. Switching customers means loading a small adapter, not a whole model. Apple (2024) used several LoRA adapters on one 3B base model for different iPhone features. Adapters are modular and shareable, for example on Hugging Face or AdapterHub.

LoRA's downsides: it usually does not quite match full finetuning, and it requires changing the model's code. For popular base models, PEFT frameworks (Hugging Face PEFT, Axolotl, unsloth, LitGPT) handle that for you.

### Quantized LoRA (QLoRA)

The LoRA adapter is tiny compared with the base weights. Huyen's table: Llama 2 13B at 16 bits needs 26 GB of weights, while a rank-2 adapter on the query and key matrices has 3.28 million parameters taking 6.55 MB. For GPT-3 175B it is 350 GB versus 37.7 MB. Shrinking the adapter further barely helps. **Quantizing the base model does.**

**QLoRA** (Dettmers and colleagues, 2023) stores the frozen base weights in **4 bits** using **NF4** (4-bit NormalFloat, a format whose levels are spaced to suit the bell-shaped spread of pre-trained weights) and **dequantizes** them (converts them back) to BF16 on the fly for each forward and backward pass. This made it possible to finetune a **65B** model on a single 48 GB GPU. Their Guanaco models were competitive at the time: on the paper's Elo comparison (May 2023), Guanaco 65B, taking 41 GB, scored 1022 against ChatGPT's 966, and Guanaco 7B fit in 6 GB.

The cost: quantizing and dequantizing add computation, so QLoRA training can be slower even though it uses far less memory.

## 3. Model merging and multi-task finetuning

**Model merging** combines several models into one custom model. Finetuning changes one model; merging creates a new one from existing ones. It needs no GPUs, which makes it popular with independent developers. The merged model should be worth more than its parts: better at a task, or covering several tasks in a smaller total footprint.

Uses:

- **Multi-task finetuning without catastrophic forgetting.** **Catastrophic forgetting** is a model losing earlier skills when trained on a new task. Finetuning on all tasks at once needs more data; finetuning on them one after another risks forgetting. With merging, you finetune separately and in parallel, then merge.
- **On-device deployment**: one merged model in place of several on a phone.
- **Federated learning**: training copies of a model on data that stays on different devices, then merging the copies.
- **Model upscaling**: building bigger models from smaller ones.

Merging differs from **ensembling**, which combines the *outputs* of several models and must run all of them. Merging combines the *parameters* into a single model.

### Summing

- **Linear combination**: a weighted average of the parameters, $\text{Merge}(A,B) = \frac{w_A A + w_B B}{w_A + w_B}$. "Model soups" showed that averaging finetuned models can improve accuracy at no extra inference cost. It works best for models finetuned from the **same base** and is commonly applied to adapters.
- **Task vectors**: a finetuned model minus its base model captures what finetuning added for that task. **Task arithmetic** adds task vectors to combine skills, or subtracts one to remove a behaviour such as a bias or an unwanted capability.
- **SLERP (spherical linear interpolation)**: instead of averaging along a straight line, it moves along the arc of a sphere between two models, treating each as a point on the sphere. It merges only two models at a time, though merges can be chained.
- **Pruning redundant parameters**: many finetuning changes are tiny and can be dropped. **TIES** resets small changes and resolves conflicts where models changed a parameter in opposite directions. **DARE** randomly drops changes and rescales the rest. Pruning reduces interference when merging many models.

```python-run
import numpy as np
rng = np.random.default_rng(1)
base = rng.normal(size=6)
ft_a = base + np.array([0.5, 0, 0, 0.2, 0, 0])     # finetuned for task A
ft_b = base + np.array([0, 0, 0.4, 0, 0, -0.3])    # finetuned for task B
tv_a, tv_b = ft_a - base, ft_b - base              # task vectors (delta parameters)
print("average          :", ((ft_a + ft_b) / 2 - base).round(2))
print("task arithmetic  :", ((base + tv_a + tv_b) - base).round(2), "(both skills at full strength)")
def slerp(u, v, t):
    cos = np.clip(u @ v / (np.linalg.norm(u) * np.linalg.norm(v)), -1, 1); w = np.arccos(cos)
    return (np.sin((1 - t) * w) * u + np.sin(t * w) * v) / np.sin(w) if w > 1e-6 else (1 - t) * u + t * v
print("SLERP(t=0.5) norm:", np.linalg.norm(slerp(ft_a, ft_b, 0.5)).round(3), "vs linear:", np.linalg.norm((ft_a + ft_b) / 2).round(3))
```

**Reading this Python line by line**

- `base` is a toy "model" of six parameters. `ft_a` and `ft_b` are two finetuned versions that changed different parameters.
- `tv_a` and `tv_b` are the task vectors: what each finetune added.
- The first print shows a plain average, minus the base: each skill survives at **half** strength (0.25 instead of 0.5, and so on).
- The second print adds both task vectors to the base: each skill at **full** strength, because the two tasks touched different parameters and do not interfere.
- `slerp` measures the angle `w` between the two parameter vectors with `np.arccos` of their cosine similarity, then blends along the arc; if the angle is almost zero it falls back to a straight-line blend. `np.clip` guards against rounding pushing the cosine slightly outside −1 to 1.
- Output: the average gives `[0.25 0. 0.2 0.1 0. -0.15]`, task arithmetic `[0.5 0. 0.4 0.2 0. -0.3]`, and the SLERP midpoint has length 1.95 versus 1.915 for the straight-line average. Averaging pulls the midpoint toward the centre and shrinks it slightly; SLERP keeps the length more like the originals.

### Layer stacking

Take layers from different models and stack them, also called **passthrough** or **frankenmerging**. It can produce new architectures and sizes, and usually needs further finetuning afterwards. Goliath-120B was built from two finetuned Llama 2-70B models. Layer stacking is also used to build **mixture-of-experts** models (models with several specialised sub-networks, of which only some run for each token) and for **model upscaling**: SOLAR 10.7B duplicated layers of a 7B model (32 layers became 48) and then finetuned further.

### Concatenation

Join parameters side by side, for example two LoRA adapters of ranks $r_1$ and $r_2$ into one of rank $r_1 + r_2$. This saves no memory compared with serving the parts separately, so Huyen generally does not recommend it.

## 4. Finetuning tactics

### Base models: two development paths

- **Progression path.** Test your finetuning code on the cheapest, fastest model; test your data on a middling model; run a few experiments on the best model to see how far you can push. Then map the price–performance trade-off and choose.
- **Distillation path.** Start with a small dataset and the **strongest** model you can afford. Finetune it, use it to **generate more training data**, and train a cheaper model on that data.

### Methods

Full finetuning generally needs far more data (at least thousands of examples) and compute. Adapter methods such as LoRA are a good default when you have a few hundred to a few thousand examples. With PEFT, many adapters can share one base model; with full finetuning, each task gets its own full copy.

Finetuning **APIs** from model providers are the easiest route but limit which base models and settings you can use. Frameworks (LLaMA-Factory, unsloth, PEFT, Axolotl, LitGPT) give more control, and you supply the hardware. For training across many GPUs (*distributed training*), look at DeepSpeed, PyTorch Distributed and ColossalAI.

### Hyperparameters

- **Learning rate**: how big a step each update takes. Too small and learning is slow; too large and training does not **converge** (settle on a good solution) or blows up. A typical range is **1e-7 to 1e-3** ($10^{-7}$ to $10^{-3}$). A common practice is to take the learning rate at the end of pre-training and multiply it by a constant between 0.1 and 1. Read the **loss curve** (the loss plotted over training steps): large swings mean the rate is too high; smooth but slow progress means it is too low. **Learning rate schedules** change the rate during training, usually larger at first and smaller later.
- **Batch size**: how many examples are used for each update. Too small (below about 8) gives unstable training. Larger is more stable and faster but needs more memory. If memory is tight, use **gradient accumulation**: compute gradients over several small batches, add them up, and update the weights once, which gives the same update as one big batch.
- **Number of epochs**: an **epoch** is one full pass over the training data. Small datasets need more epochs: millions of examples may need only 1–2, while thousands may still improve after 4–10. Keep a **validation set** (examples held back from training) and watch both losses. If training and validation loss both keep falling, train longer. If training loss falls while validation loss rises, the model is **overfitting** (memorising the training examples), so use fewer epochs.
- **Prompt loss weight**: in instruction finetuning, both the prompt tokens and the response tokens can contribute to the loss, but at inference the model only generates responses. This weight sets how much prompt tokens count relative to response tokens: 100% means equally, 0% means responses only. The typical default is **10%**.

Gradient accumulation is easy to check with a tiny model, because averaging the gradients of four small batches gives exactly the gradient of one large batch:

```python-run
import numpy as np
rng = np.random.default_rng(0)
X = rng.normal(size=(8, 3))                  # a batch of 8 examples, 3 features each
y = rng.normal(size=8)
w = np.zeros(3)                              # current weights of a tiny linear model

def grad(Xb, yb, w):
    # gradient of the mean squared error 0.5 * mean((Xb @ w - yb)^2) with respect to w
    return Xb.T @ (Xb @ w - yb) / len(yb)

full = grad(X, y, w)                         # one batch of 8 (needs memory for 8 at once)
acc = np.zeros(3)
for i in range(0, 8, 2):                     # four micro-batches of 2 (memory for 2 at once)
    acc += grad(X[i:i+2], y[i:i+2], w)
acc /= 4                                     # average the accumulated gradients
print("full-batch gradient :", full.round(4))
print("accumulated gradient:", acc.round(4))
print("identical:", np.allclose(full, acc))
```

`grad` computes the gradient of the squared error for a tiny linear model (the formula is standard calculus; what matters here is that it averages over the examples in the batch). `full` uses all 8 examples at once. The loop processes four *micro-batches* of 2 (`X[i:i+2]` takes rows `i` and `i+1`), adds their gradients into `acc`, and divides by 4 at the end. Output: both gradients are `[-0.0652 0.1541 -0.2068]`, and `identical: True`. Real models behave the same way (apart from layers that look across the batch), which is why gradient accumulation lets a small GPU imitate a large batch at the cost of time.

> [!INTERVIEW]
> **"Explain LoRA and why it adds no inference latency."** LoRA freezes $W$ and learns a low-rank update $\frac{\alpha}{r}AB$ with $A$ of shape $n \times r$ and $B$ of shape $r \times m$, training $r(n+m)$ parameters instead of $nm$. It works because pre-trained models have low intrinsic dimension. After training, $AB$ is added into $W$ once, so the served model has the same shape and cost. Follow-ups: keep adapters unmerged for multi-LoRA serving (one base, many small adapters). QLoRA quantizes the frozen base to 4-bit NF4 to cut memory, at some speed cost. Typical ranks are 4 to 64, applied at least to the query and value matrices.

## Pitfalls

- Choosing a high LoRA rank by default; it costs memory and can overfit with no gain.
- Adapting only one attention matrix when the budget allows spreading a lower rank over several.
- Merging models finetuned from different base models and expecting averaging to work.
- Judging training only by training loss, without a validation set to catch overfitting.
- Forgetting that QLoRA saves memory but can slow training down.

## Summary

- **PEFT** comes close to full finetuning with orders of magnitude fewer trainable parameters. Families: adapter-based (LoRA and others) and soft-prompt-based (prefix, prompt and P-tuning).
- **LoRA**: $W' = W + \frac{\alpha}{r}AB$, with $r(n+m)$ parameters per matrix, mergeable so there is no added latency. Low intrinsic dimension explains why it works. Rank 4–64, applied to attention and often feedforward matrices.
- **Multi-LoRA serving** shares one base across many adapters. **QLoRA** adds a 4-bit base model so very large models can be finetuned on one GPU.
- **Model merging**: summing (linear, task arithmetic, SLERP, with TIES or DARE pruning), layer stacking (frankenmerges, upscaling) and concatenation. Useful for multi-task, on-device and federated settings.
- **Tactics**: progression or distillation paths. Tune learning rate, batch size (with gradient accumulation), epochs (watch validation loss) and prompt loss weight.

## Glossary

- **Parameter-efficient finetuning (PEFT)**: finetuning that trains only a small fraction of parameters.
- **Hyperparameter**: a setting chosen before training, such as learning rate or LoRA rank.
- **Layer**: one processing stage in a neural network.
- **Partial finetuning**: updating only the last layers.
- **Adapter**: a small trainable module added to a frozen model.
- **Soft prompt / prefix-tuning / prompt tuning**: learned input vectors instead of words; added at every layer; added at the input only.
- **Matrix / shape / rank**: a grid of numbers / its rows by columns / informally, how many independent patterns it holds.
- **LoRA**: learning a low-rank update AB to frozen weights, W' = W + (α/r)AB.
- **Alpha (α)**: the LoRA scaling factor for the update.
- **Intrinsic dimension**: the small number of directions needed to adapt a model.
- **Attention matrices (query, key, value, output)**: the weights a transformer uses to relate tokens.
- **Feedforward layer**: the per-token processing part of a transformer block.
- **Multi-LoRA serving**: many adapters sharing one base model at inference.
- **QLoRA / NF4 / dequantize**: LoRA on a 4-bit base / a 4-bit format suited to weight distributions / convert back to higher precision.
- **Model merging**: combining several models' parameters into one.
- **Catastrophic forgetting**: losing old skills when trained on a new task.
- **Federated learning**: training on data that stays on separate devices, then combining.
- **Ensembling**: combining outputs of several models that all run.
- **Task vector / task arithmetic**: finetuned minus base weights / adding or subtracting task vectors.
- **SLERP**: interpolating between two models along an arc.
- **TIES / DARE**: pruning methods that reduce interference when merging.
- **Layer stacking (frankenmerging) / upscaling**: building a model from layers of others / making a larger model from a smaller one.
- **Mixture of experts**: a model with several sub-networks, only some used per token.
- **Learning rate / schedule**: update step size / how it changes during training.
- **Batch size / gradient accumulation**: examples per update / summing gradients over small batches before one update.
- **Epoch**: one full pass over the training data.
- **Validation set**: held-back examples used to detect overfitting.
- **Prompt loss weight**: how much prompt tokens count in the loss relative to response tokens.

```quiz
[
  {"q": "A weight matrix is 4096 × 4096. With LoRA rank 8, how many trainable parameters does it get?", "options": ["32,768", "65,536", "16,777,216", "262,144"], "answer": 1, "explain": "r × (n + m) = 8 × (4096 + 4096) = 65,536."},
  {"q": "Why does LoRA add no inference latency (unlike the original adapters)?", "options": ["It uses GPUs better", "AB can be merged into W, so the served model has the same architecture", "It removes layers", "It quantizes weights"], "answer": 1, "explain": "The original adapters add layers. LoRA's update is folded into the existing matrix."},
  {"q": "The 'intrinsic dimension' argument says…", "options": ["Large models can't be finetuned", "Pre-trained models can be adapted in a low-dimensional subspace, so few parameters suffice", "LoRA requires rank 1024", "Finetuning needs more data than pre-training"], "answer": 1, "explain": "Pre-training compresses the model's intrinsic dimension, and better pre-training makes low-rank adaptation easier."},
  {"q": "With a fixed parameter budget on GPT-3, which LoRA configuration performed best in the paper?", "options": ["Rank 8 on W_q only", "Rank 8 on W_k only", "Rank 2 spread over all four attention matrices", "No LoRA"], "answer": 2, "explain": "Adapting more matrices at lower rank beat a higher rank on a single matrix."},
  {"q": "What does QLoRA add on top of LoRA?", "options": ["Larger adapters", "A 4-bit quantized (NF4) frozen base model, dequantized on the fly", "Soft prompts", "Layer stacking"], "answer": 1, "explain": "The base weights dominate memory, and quantizing them lets a 65B model be finetuned on one 48 GB GPU."},
  {"q": "A task vector is…", "options": ["The embedding of a prompt", "Finetuned weights minus base weights", "A LoRA rank", "A learning-rate schedule"], "answer": 1, "explain": "Task vectors (delta parameters) can be added or subtracted: task arithmetic."},
  {"q": "Model merging helps multi-task finetuning mainly by…", "options": ["Increasing the learning rate", "Letting tasks be finetuned separately in parallel, avoiding catastrophic forgetting from sequential finetuning", "Removing the need for data", "Doubling context length"], "answer": 1, "explain": "Each task gets its own finetune, and merging combines them."},
  {"q": "Your GPU only fits batch size 2 and training is unstable. Which technique helps?", "options": ["Gradient accumulation", "Higher temperature", "Larger vocabulary", "SLERP"], "answer": 0, "explain": "Accumulate gradients over several small batches before updating to imitate a larger batch."}
]
```

> **Source:** Huyen, *AI Engineering*, ch. 7 ("Finetuning Techniques": parameter-efficient finetuning, LoRA, model merging and multi-task finetuning, finetuning tactics).
