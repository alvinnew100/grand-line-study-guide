# PEFT, LoRA, model merging and hyperparameters

Full finetuning updates every weight. For a model with billions of parameters, the memory math from the previous lesson shows why that is out of reach for most teams. **Parameter-efficient finetuning (PEFT)** gets close to full-finetuning quality while training a tiny fraction of the parameters. **LoRA** is the most popular PEFT method. This lesson covers PEFT families, LoRA and QLoRA in detail, **model merging** as a complementary technique, and the practical tactics: choosing base models and methods, and the main hyperparameters.

## 1. Why PEFT?

Early on, models were small enough for **full finetuning**. As they grew, people tried **partial finetuning**, where earlier layers are frozen and only the last few are updated. That cuts memory, but it is **parameter-inefficient**. Houlsby et al. (2019) found that on BERT-large, partial finetuning needed about **25%** of the parameters to come close to full finetuning on GLUE.

The same paper introduced **adapters**: small modules inserted into each transformer block, with only the adapters trained. They reached within **0.4%** of full finetuning performance using about **3%** of the trainable parameters. This started PEFT. A method is parameter-efficient if it can approach full finetuning with several orders of magnitude fewer trainable parameters. PEFT methods also tend to be **sample-efficient**: a few thousand examples can be enough where full finetuning might want tens of thousands to millions.

The original adapters have one drawback. The extra layers add **inference latency**, because the forward pass has more to compute.

### PEFT families

- **Adapter-based (additive) methods** add trainable modules to the model's weights: the original adapters, **LoRA** and its variants (DoRA, QLoRA, LoRA+), BitFit and IA3.
- **Soft prompt-based methods** leave the architecture alone and add trainable **continuous vectors** ("soft prompts") to the input, or to every layer, that are optimized by backpropagation. Hard prompts are human-readable tokens. Soft prompts are learned embeddings that do not correspond to words. Variants are **prefix-tuning** (prepend at every layer), **P-tuning** and **prompt tuning** (prepend at the input embedding only).

Huyen's analysis of GitHub issues in Hugging Face's PEFT repository found LoRA dominating by a wide margin. Soft-prompt methods are less common but interest people who want more control than prompting without full finetuning.

## 2. LoRA

**LoRA (Low-Rank Adaptation)** (Hu et al., 2021) adds parameters in a way that incurs **no extra inference latency**, because its modules can be **merged back** into the original weights.

For a weight matrix $W \in \mathbb{R}^{n\times m}$:

1. Choose a rank $r$. Create $A \in \mathbb{R}^{n\times r}$ and $B \in \mathbb{R}^{r\times m}$. Their product $W_{AB} = AB$ has the same shape as $W$.
2. Use the adapted weight, with a scaling hyperparameter $\alpha$:

$$W' = W + \frac{\alpha}{r}\,AB$$

3. During finetuning, update only $A$ and $B$. $W$ stays **frozen**.

The trainable parameter count for one matrix falls from $n \times m$ to $r\,(n+m)$:

$$\text{LoRA params} = r \times (n + m)$$

Huyen's small example: a $9\times9$ matrix (81 parameters) factorized into $9\times1$ and $1\times9$ has 18. For a $4096\times4096$ matrix (16.8M parameters) and $r = 8$, LoRA trains $4096\times8\times2 = 65{,}536$ parameters, about 0.39%.

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

For GPT-3 the LoRA paper reports matching or beating full finetuning on several tasks with about **4.7M** trainable parameters, **0.0027%** of the full model.

### Why does LoRA work?

If a model needs billions of parameters to learn behaviors in pre-training, why can it be adapted with so few? Research (Li et al., 2018; Aghajanyan et al., 2020; Hu et al., 2021) argues that large pre-trained models have a very low **intrinsic dimension**. Pre-training implicitly compresses the model, and *larger* models tend to end up with *lower* intrinsic dimension. The better a model is pre-trained, the easier it is to finetune with few parameters and little data.

Could you pre-train with low-rank factorization from the start? Low-rank training works at small scale (SqueezeNet matched AlexNet with 50× fewer parameters), and ReLoRA and GaLore show progress up to about 1B to 7B parameters. If pre-training is what compresses the intrinsic dimension, though, full-rank pre-training may still be needed first.

### LoRA configurations

**Which matrices?** LoRA is mostly applied to the attention matrices: query $W_q$, key $W_k$, value $W_v$ and output projection $W_o$. It is usually applied uniformly, to the same kinds of matrix in every layer. With a fixed budget of 18M trainable parameters on GPT-3 175B (96 layers, model dimension 12,288), the LoRA paper found:

| Applied to | Rank | WikiSQL | MultiNLI |
|---|---|---|---|
| $W_q$ only | 8 | 70.4 | 91.0 |
| $W_k$ only | 8 | 70.0 | 90.8 |
| $W_v$ only | 8 | 73.0 | 91.0 |
| $W_q, W_v$ | 4 | 73.7 | 91.3 |
| $W_q, W_k, W_v, W_o$ | 2 | 73.7 | 91.7 |

Spreading a low rank over more matrices beat a high rank on one. Rank 2 on all four gives $(12{,}288 \times 2 \times 2)\times 4 = 196{,}608$ parameters per layer and 18,874,368 for the model. If you can pick only two, **query and value** are generally best. Later evidence suggests that applying LoRA to more matrices, including the **feedforward** layers, helps further (Databricks reported its biggest boost from that).

**Rank $r$.** A small $r$, between **4 and 64**, is usually enough. The LoRA authors found that raising $r$ did not improve results, and a higher rank can overfit. Some tasks do need more: Raschka found $r = 256$ best on his.

**Alpha $\alpha$.** This scales how much $AB$ contributes. Huyen has often seen the ratio $\alpha : r$ between 1:8 and 8:1. A small $r$ often pairs with a larger $\alpha$. Experiment.

### Serving LoRA adapters

1. **Merge** $A$ and $B$ into $W$ before serving. This adds no latency and is best when you serve one finetuned model.
2. **Keep the adapters separate** and combine at inference. This adds some latency but enables **multi-LoRA serving**, where many adapters share one base model.

With 100 customer-specific models on a $4096\times4096$ matrix and $r=8$: option 1 stores $16.8\text{M}\times100 = 1.68\text{B}$ parameters, and option 2 stores $16.8\text{M} + 65{,}536\times100 \approx 23.3\text{M}$. Switching customers means loading a small adapter rather than a whole model. Apple (2024) used several LoRA adapters on one 3B base model for different iPhone features. Adapters are modular and shareable, for example on Hugging Face or AdapterHub.

LoRA's downsides: it usually does not quite match full finetuning, and it requires modifying the model's implementation. For popular base models, PEFT frameworks (Hugging Face PEFT, Axolotl, unsloth, LitGPT) handle that for you.

### Quantized LoRA (QLoRA)

The LoRA adapter is tiny compared with the base weights. Huyen's table shows Llama 2 13B at 16 bits needs 26 GB of weights, while a rank-2 adapter on the query and key matrices has 3.28M parameters and takes 6.55 MB. For GPT-3 175B it is 350 GB versus 37.7 MB. Shrinking the adapter further barely helps. **Quantizing the base model does.**

**QLoRA** (Dettmers et al., 2023) stores the frozen base weights in **4 bits** using NF4 (4-bit NormalFloat, designed for the roughly normal distribution of pre-trained weights) and **dequantizes** them to BF16 on the fly for the forward and backward pass. This allowed finetuning a **65B** model on a single 48 GB GPU. Their Guanaco models were competitive at the time. On the paper's Elo comparison (May 2023), Guanaco 65B at 41 GB scored 1022 against ChatGPT's 966, and Guanaco 7B fit in 6 GB.

The limitation is that NF4 quantization and dequantization add compute, so QLoRA training can be slower even though it uses far less memory.

## 3. Model merging and multi-task finetuning

**Model merging** combines several models into one custom model. Finetuning changes one model, and merging creates a new one from existing ones. It needs no GPUs, which makes it attractive to independent developers. The merged model should be worth more than its parts: better on a task, or covering several tasks in a smaller total footprint.

Uses:

- **Multi-task finetuning without catastrophic forgetting.** Simultaneous finetuning needs more data. Sequential finetuning risks forgetting earlier tasks. With merging, you finetune separately and in parallel, then merge.
- **On-device deployment.** One merged model in place of several.
- **Federated learning.** Merge copies trained on different devices' data.
- **Model upscaling.** Build bigger models from smaller ones.

Merging is related to **ensembling**, which combines *outputs* of several models and keeps all of them. Merging combines *parameters* into one model.

### Summing

- **Linear combination**: a weighted average of parameters, $\text{Merge}(A,B) = \frac{w_A A + w_B B}{w_A + w_B}$. "Model soups" showed that averaging finetuned models can improve accuracy with no added inference cost. It works best for models finetuned from the **same base**, and is commonly applied to adapters.
- **Task vectors**: (finetuned model − base model) captures a task. **Task arithmetic** adds task vectors to combine skills, or subtracts one to remove a behaviour such as a bias or an unwanted capability.
- **SLERP (spherical linear interpolation)**: interpolates along the arc of a sphere instead of a straight line, treating each model's task vector as a point on the sphere. It merges only two at a time, though you can chain merges.
- **Pruning redundant parameters**: many finetuning changes are small and can be dropped. **TIES** resets small changes and resolves sign conflicts. **DARE** randomly drops and rescales. Pruning reduces interference when merging many models.

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

### Layer stacking

Take layers from different models and stack them. This is also called **passthrough** or **frankenmerging**. It can produce new architectures and sizes, and it usually needs further finetuning. Goliath-120B was built from two finetuned Llama 2-70B models. Layer stacking is also used to build **mixture-of-experts** models (MoE-style merges) and for **model upscaling**. SOLAR 10.7B duplicated layers of a 7B model (32 layers became 48) and then finetuned further.

### Concatenation

Concatenate parameters, for example two LoRA adapters of ranks $r_1$ and $r_2$ into one of rank $r_1 + r_2$. This does not reduce memory compared with serving the parts separately, so Huyen generally does not recommend it.

## 4. Finetuning tactics

### Base models: two development paths

- **Progression path.** Test your finetuning code on the cheapest, fastest model. Test your data on a middling model. Run a few experiments on the best model to see how far you can push. Then map the price–performance frontier and pick.
- **Distillation path.** Start with a small dataset and the **strongest** model you can afford. Finetune it, use it to **generate more training data**, and train a cheaper model on that data.

### Methods

Full finetuning generally needs far more data (at least thousands of examples) and compute. Adapter methods such as LoRA are a good default when you have a few hundred to a few thousand examples. With PEFT, each adapter can be shared across a base model. With full finetuning, each task has its own full model.

Finetuning **APIs** are the easiest route but limit base models and knobs. Frameworks (LLaMA-Factory, unsloth, PEFT, Axolotl, LitGPT) give more control, and you supply the compute. For distributed training, look at DeepSpeed, PyTorch Distributed and ColossalAI.

### Hyperparameters

- **Learning rate.** If it is too small, learning is slow. If it is too large, training does not converge. A typical range is **1e-7 to 1e-3**. A common practice is to take the learning rate at the end of pre-training and multiply by a constant between 0.1 and 1. Read the loss curve: large fluctuations mean the rate is too high, and stable but slow means it is too low. Use **learning rate schedules** (larger at first, smaller later).
- **Batch size.** Too small (under about 8) gives unstable training. Larger is more stable and faster but needs more memory. If memory is tight, use **gradient accumulation**: accumulate gradients over several small batches before each update.
- **Number of epochs.** Small datasets need more epochs. Millions of examples may need only 1–2, and thousands of examples may still improve after 4–10. If training and validation loss both keep falling, train longer. If training loss falls while validation loss rises, the model is **overfitting**, so reduce epochs.
- **Prompt loss weight.** In instruction finetuning, the prompt and the response both contribute to the loss, but at inference the model only generates responses. This weight sets how much prompt tokens count relative to response tokens. 100% means equal, 0% means responses only, and the typical default is **10%**.

> [!INTERVIEW]
> **"Explain LoRA and why it adds no inference latency."** LoRA freezes $W$ and learns a low-rank update $\frac{\alpha}{r}AB$ with $A\in\mathbb{R}^{n\times r}$ and $B\in\mathbb{R}^{r\times m}$, training $r(n+m)$ parameters instead of $nm$. It works because pre-trained models have low intrinsic dimension. After training, $AB$ is added into $W$ once, so the served model has the same shape and cost. Follow-ups: keep adapters unmerged for multi-LoRA serving (one base, many small adapters). QLoRA quantizes the frozen base to 4-bit NF4 to cut memory, at some speed cost. Typical ranks are 4 to 64, usually applied to query and value matrices or more.

## Summary

- **PEFT** matches full finetuning closely with orders of magnitude fewer trainable parameters. Families are adapter-based (LoRA and others) and soft prompt-based (prefix, prompt and P-tuning).
- **LoRA**: $W' = W + \frac{\alpha}{r}AB$, with $r(n+m)$ parameters per matrix, mergeable so there is no added latency. Low intrinsic dimension explains why it works. Rank 4–64, applied to attention and often feedforward matrices.
- **Multi-LoRA serving** shares one base across many adapters. **QLoRA** adds a 4-bit base model so that very large models can be finetuned on one GPU.
- **Model merging**: summing (linear, task arithmetic, SLERP, with TIES or DARE pruning), layer stacking (frankenmerges, upscaling) and concatenation. Useful for multi-task, on-device and federated settings.
- **Tactics**: progression or distillation paths. Tune learning rate, batch size (with gradient accumulation), epochs and prompt loss weight.

```quiz
[
  {"q": "A weight matrix is 4096 × 4096. With LoRA rank 8, how many trainable parameters does it get?", "options": ["32,768", "65,536", "16,777,216", "262,144"], "answer": 1, "explain": "r × (n + m) = 8 × (4096 + 4096) = 65,536."},
  {"q": "Why does LoRA add no inference latency (unlike the original adapters)?", "options": ["It uses GPUs better", "AB can be merged into W, so the served model has the same architecture", "It removes layers", "It quantizes weights"], "answer": 1, "explain": "The original adapters add layers. LoRA's update is folded into the existing matrix."},
  {"q": "The 'intrinsic dimension' argument says…", "options": ["Large models can't be finetuned", "Pre-trained models can be adapted in a low-dimensional subspace, so few parameters suffice", "LoRA requires rank 1024", "Finetuning needs more data than pre-training"], "answer": 1, "explain": "Pre-training compresses the model's intrinsic dimension, and better pre-training makes low-rank adaptation easier."},
  {"q": "With a fixed parameter budget on GPT-3, which LoRA configuration performed best in the paper?", "options": ["Rank 8 on W_q only", "Rank 8 on W_k only", "Rank 2 spread over all four attention matrices", "No LoRA"], "answer": 2, "explain": "Adapting more matrices at lower rank beat a higher rank on a single matrix."},
  {"q": "What does QLoRA add on top of LoRA?", "options": ["Larger adapters", "A 4-bit quantized (NF4) frozen base model, dequantized on the fly", "Soft prompts", "Layer stacking"], "answer": 1, "explain": "The base weights dominate memory, and quantizing them lets a 65B model be finetuned on one 48 GB GPU."},
  {"q": "A task vector is…", "options": ["The embedding of a prompt", "Finetuned weights minus base weights", "A LoRA rank", "A learning-rate schedule"], "answer": 1, "explain": "Task vectors (delta parameters) can be added or subtracted: task arithmetic."},
  {"q": "Model merging helps multi-task finetuning mainly by…", "options": ["Increasing the learning rate", "Letting tasks be finetuned separately in parallel, avoiding catastrophic forgetting from sequential finetuning", "Removing the need for data", "Doubling context length"], "answer": 1, "explain": "Each task gets its own finetune, and merging combines them."},
  {"q": "Your GPU only fits batch size 2 and training is unstable. Which technique helps?", "options": ["Gradient accumulation", "Higher temperature", "Larger vocabulary", "SLERP"], "answer": 0, "explain": "Accumulate gradients over several small batches before updating to simulate a larger batch."}
]
```

> **Source:** Huyen, *AI Engineering*, ch. 7 ("Finetuning Techniques": parameter-efficient finetuning, LoRA, model merging and multi-task finetuning, finetuning tactics).
