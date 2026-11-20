# PEFT: LoRA, QLoRA and friends

The AI Engineering track discusses *when* to fine-tune (versus prompting or RAG) and the memory maths
of training. This lesson is the hands-on internals: what LoRA actually computes, why it works, how
QLoRA squeezes a 70B fine-tune onto one GPU, and the `peft` code you will write.

## 1. The problem with full fine-tuning

Full fine-tuning updates every weight. With Adam in mixed precision that costs about 16 bytes per
parameter for weights, gradients and optimizer state: about 112 GB for a 7B model before activations,
over 1 TB for 70B. Each task also produces a full-size copy of the model to store and serve.

**Parameter-efficient fine-tuning (PEFT)** freezes the pretrained weights and trains a small number of
new parameters. Families:

- **Additive / adapter**: insert small bottleneck MLPs between layers (Houlsby adapters).
- **Soft prompts**: learn virtual token embeddings prepended to the input (prompt tuning, prefix
  tuning, P-tuning).
- **Reparameterisation**: learn a low-rank *update* to existing weights: **LoRA** and its variants.
  This is the dominant approach because it adds **no inference latency** once merged.

## 2. LoRA: the idea

Hypothesis (Hu et al. 2021): the weight change needed to adapt a pretrained model has **low intrinsic
rank**. So instead of learning a full $\Delta W \in \mathbb{R}^{d_{out} \times d_{in}}$, learn

$$
\Delta W = \frac{\alpha}{r} B A,\qquad B \in \mathbb{R}^{d_{out} \times r},\; A \in \mathbb{R}^{r \times d_{in}},\; r \ll \min(d_{in}, d_{out})
$$

and compute the forward pass as

$$
h = W_0 x + \frac{\alpha}{r} B (A x)
$$

- $W_0$ is frozen. Only $A$ and $B$ are trained: $r(d_{in} + d_{out})$ parameters instead of
  $d_{in} d_{out}$.
- **Initialisation**: $A$ random (Kaiming/Gaussian), $B = 0$, so $\Delta W = 0$ at the start and training
  begins exactly at the pretrained model.
- **Scaling** $\alpha / r$: decouples the update's magnitude from the rank, so you can change $r$
  without retuning the learning rate much. Common: $\alpha = r$ or $\alpha = 2r$. **rsLoRA** uses
  $\alpha/\sqrt{r}$, which keeps learning stable at high ranks.
- **Merging**: after training, $W = W_0 + \frac{\alpha}{r}BA$ is a single matrix of the original shape,
  so inference cost is unchanged. Or keep adapters separate and hot-swap many per base model
  (multi-LoRA serving in vLLM and TGI/LoRAX).

```python-run
import numpy as np
rng = np.random.default_rng(0)
d_in, d_out, r, alpha = 512, 512, 8, 16
W0 = rng.standard_normal((d_out, d_in)) / np.sqrt(d_in)
A = rng.standard_normal((r, d_in)) / np.sqrt(d_in)
B = np.zeros((d_out, r))                      # zero init: no change at step 0
x = rng.standard_normal(d_in)
h = W0 @ x + (alpha / r) * B @ (A @ x)
print("identical to base at init:", np.allclose(h, W0 @ x))

B = rng.standard_normal((d_out, r)) * 0.01    # pretend we trained
merged = W0 + (alpha / r) * B @ A
print("merged forward == adapter forward:", np.allclose(merged @ x, W0 @ x + (alpha / r) * B @ (A @ x)))
print("rank of update:", np.linalg.matrix_rank(B @ A))
print(f"trainable: {r * (d_in + d_out):,} vs full {d_in * d_out:,}  ({100 * r * (d_in + d_out) / (d_in * d_out):.2f}%)")
```

### Counting LoRA parameters for a real model

For Llama 3 8B ($d = 4096$, 32 layers, GQA with 8 KV heads of dim 128 so $k, v$ project to 1024,
MLP intermediate 14336), LoRA with $r = 16$ on all linear layers:

| module | shape (out x in) | LoRA params $r(d_{in}+d_{out})$ |
|---|---|---|
| q_proj | 4096 x 4096 | 131,072 |
| k_proj | 1024 x 4096 | 81,920 |
| v_proj | 1024 x 4096 | 81,920 |
| o_proj | 4096 x 4096 | 131,072 |
| gate_proj | 14336 x 4096 | 294,912 |
| up_proj | 14336 x 4096 | 294,912 |
| down_proj | 4096 x 14336 | 294,912 |
| **per layer** | | **1,310,720** |

Times 32 layers is about 41.9M trainable parameters: roughly 0.5 percent of 8B. This module's
`llm-lora-params` problem automates exactly this calculation.

```python-run
layers = {"q": (4096, 4096), "k": (1024, 4096), "v": (1024, 4096), "o": (4096, 4096),
          "gate": (14336, 4096), "up": (14336, 4096), "down": (4096, 14336)}
for r in [8, 16, 64]:
    per_layer = sum(r * (i + o) for o, i in layers.values())
    total = 32 * per_layer
    print(f"r={r:3d}: {total/1e6:6.1f}M trainable  ({100*total/8.03e9:.2f}% of 8B)   adapter file ~{total*2/1e6:.0f} MB in bf16")
```

## 3. Practical LoRA hyperparameters

- **Target modules**: the original paper adapted only `q_proj` and `v_proj`, but later work (QLoRA,
  "LoRA Learns Less and Forgets Less", Thinking Machines' "LoRA Without Regret") found that adapting
  **all linear layers, especially the MLPs**, matters most. In `peft`: `target_modules="all-linear"`.
- **Rank**: 8 to 64 is typical. Higher rank gives more capacity, needed for larger datasets or harder
  shifts (new language, heavy reasoning). For small instruction datasets, rank barely matters.
- **Learning rate**: about 10x the full fine-tuning LR, e.g. 1e-4 to 2e-4 (TRL suggests about 1e-4 for
  adapters).
- **Dropout** on the LoRA path: 0 to 0.1.
- **What LoRA is good at**: style, format, domain tone, task specialisation, tool-call formats. It is
  less sample-efficient than full fine-tuning for injecting lots of new knowledge, and it "forgets less"
  of the base model's abilities, which is often what you want.

## 4. QLoRA: fine-tuning on a quantised base

QLoRA (Dettmers et al. 2023) keeps the frozen base in **4-bit** and trains LoRA adapters in bf16 on top:

1. **NF4 (4-bit NormalFloat)**: a 4-bit data type whose 16 levels are quantiles of a normal
   distribution, information-theoretically suited to normally distributed weights. Weights are
   quantised in blocks (e.g. 64) with a per-block scale.
2. **Double quantisation**: the per-block scales are themselves quantised (to 8-bit), saving about 0.37
   bits per parameter.
3. **Paged optimizers**: optimizer state can spill to CPU memory via unified memory paging to survive
   memory spikes.
4. During the forward pass, each 4-bit block is **dequantised to bf16 on the fly** for the matmul;
   gradients flow through the frozen dequantised weights into the LoRA matrices only.

Result: a 65B model fine-tuned on a single 48 GB GPU, matching 16-bit LoRA quality in the paper.
Memory for the base drops from 2 bytes to about 0.5 bytes per parameter, at the cost of slower steps
(dequantisation overhead).

```python-run
import numpy as np
from math import erf, sqrt

# Build NF4-like levels: quantiles of N(0,1), normalised to [-1, 1] (simplified vs the paper's asymmetric construction)
from statistics import NormalDist
nd = NormalDist()
probs = np.linspace(0.02, 0.98, 16)
levels = np.array([nd.inv_cdf(p) for p in probs]); levels /= np.abs(levels).max()

rng = np.random.default_rng(0)
w = rng.standard_normal(64 * 1000) * 0.02           # weights ~ normal
blocks = w.reshape(-1, 64)
scale = np.abs(blocks).max(1, keepdims=True)        # absmax per block of 64
codes = np.abs(blocks[..., None] / scale[..., None] - levels).argmin(-1)   # 4-bit codes
deq = levels[codes] * scale
uniform = np.linspace(-1, 1, 16)
codes_u = np.abs(blocks[..., None] / scale[..., None] - uniform).argmin(-1)
deq_u = uniform[codes_u] * scale
print("NF4-like  mean abs error:", float(np.abs(deq - blocks).mean()))
print("uniform-4 mean abs error:", float(np.abs(deq_u - blocks).mean()))
```

Normal-quantile levels spend more resolution near zero, where most weights live, so the error is lower
than uniform 4-bit levels.

## 5. The code: peft + bitsandbytes

```python
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training

model_id = "meta-llama/Llama-3.1-8B-Instruct"
bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                         bnb_4bit_use_double_quant=True, bnb_4bit_compute_dtype=torch.bfloat16)
model = AutoModelForCausalLM.from_pretrained(model_id, quantization_config=bnb, device_map="auto")
model = prepare_model_for_kbit_training(model)        # casts norms to fp32, enables input grads

lora = LoraConfig(r=16, lora_alpha=32, lora_dropout=0.05, bias="none",
                  target_modules="all-linear", task_type="CAUSAL_LM")
model = get_peft_model(model, lora)
model.print_trainable_parameters()
# trainable params: 41,943,040 || all params: 8,072,204,288 || trainable%: 0.5196

# ... train (next lesson) ...
model.save_pretrained("llama3-8b-support-lora")       # saves only the adapter (~80 MB)
```

Loading and merging later:

```python
from peft import PeftModel, AutoPeftModelForCausalLM

base = AutoModelForCausalLM.from_pretrained(model_id, dtype=torch.bfloat16, device_map="auto")
model = PeftModel.from_pretrained(base, "me/llama3-8b-support-lora")
merged = model.merge_and_unload()                     # plain model, no adapter overhead
merged.save_pretrained("llama3-8b-support-merged")

# or serve many adapters on one base with vLLM:
#   vllm serve meta-llama/Llama-3.1-8B-Instruct --enable-lora --lora-modules support=me/llama3-8b-support-lora
```

> [!WARNING]
> Merge adapters into a **bf16** copy of the base, not into the 4-bit quantised weights; merging into
> a quantised model and re-quantising introduces rounding error that can noticeably change behaviour.

## 6. The LoRA family

- **DoRA**: decomposes weights into magnitude and direction, applies LoRA to the direction; often a
  small quality bump (`use_dora=True`).
- **rsLoRA**: rank-stabilised scaling $\alpha/\sqrt{r}$ (`use_rslora=True`).
- **PiSSA / LoftQ**: initialise $A, B$ from the principal singular vectors of $W_0$ (or to compensate
  quantisation error) instead of zero/random.
- **LoRA+**: different learning rates for $A$ and $B$.
- **VeRA, LoKr, LoHa, IA3**: even fewer parameters via shared random matrices, Kronecker or Hadamard
  products, or learned rescaling vectors.
- **Prompt / prefix tuning**: train virtual tokens only; tiny, but usually weaker than LoRA on LLMs.

## 7. Training a LoRA adapter by hand

To see LoRA learn, we fit an adapter with plain gradient descent in numpy. The frozen base $W_0$ should
have been a different matrix $W^\star = W_0 + \Delta^\star$, where the true change $\Delta^\star$ has
rank 2. We minimise the squared error of the adapted layer's outputs and compare ranks. The gradients
follow from the chain rule with $\Delta W = sBA$, $s = \alpha/r$:

$$
G = \frac{\partial \mathcal{L}}{\partial \Delta W},\qquad
\frac{\partial \mathcal{L}}{\partial B} = s\,G A^\top,\qquad
\frac{\partial \mathcal{L}}{\partial A} = s\,B^\top G
$$

```python-run
import numpy as np
rng = np.random.default_rng(0)
d_out, d_in, n = 32, 32, 512
W0 = rng.standard_normal((d_out, d_in)) / np.sqrt(d_in)
delta_true = rng.standard_normal((d_out, 2)) @ rng.standard_normal((2, d_in)) * 0.3    # rank-2 task shift
X = rng.standard_normal((n, d_in))
Y = X @ (W0 + delta_true).T

def train_lora(r, alpha, steps=1500, lr=0.02):
    A = rng.standard_normal((r, d_in)) / np.sqrt(d_in)       # random init
    B = np.zeros((d_out, r))                                 # zero init: start at the base model
    s = alpha / r
    for _ in range(steps):
        err = X @ (W0 + s * B @ A).T - Y                     # (n, d_out)
        G = err.T @ X / n                                    # dL/d(deltaW)
        B, A = B - lr * s * G @ A.T, A - lr * s * B.T @ G    # simultaneous update
    return float(((X @ (W0 + s * B @ A).T - Y) ** 2).mean()), r * (d_in + d_out)

print(f"base model loss: {float(((X @ W0.T - Y) ** 2).mean()):.4f}   (full fine-tune would train {d_in * d_out} params)")
for r in [1, 2, 4, 8]:
    loss, params = train_lora(r, alpha=2 * r)
    print(f"rank {r}: loss {loss:.5f}   trainable params {params}")
```

What to notice:

- **Rank 1 cannot fit a rank-2 change**: the loss plateaus well above zero. Capacity is a hard limit.
- **Rank 2 suffices**, and higher ranks add parameters without improving the fit. On real tasks the
  required rank is unknown, which is why people sweep 8, 16, 32, 64 and watch validation metrics.
- At step 0 only $B$ receives a non-zero gradient (because $B = 0$ makes $\partial\mathcal{L}/\partial A = 0$);
  $A$ starts moving once $B$ is non-zero. This asymmetry is what LoRA+ exploits with a larger learning
  rate for $B$.
- Keeping `alpha = 2r` fixed the effective step size across ranks, so one learning rate worked for all.

## 8. Choosing among adaptation methods

| situation | reasonable choice |
|---|---|
| style, format or tone; small dataset; one GPU | LoRA, r 8 to 16, all linear layers |
| the model does not fit in memory even for inference at 16-bit | QLoRA (4-bit base) |
| large dataset, substantial new skill or language | higher rank (64+), rsLoRA or DoRA; consider full fine-tuning |
| many customers or tasks on one deployment | one adapter each, hot-swapped on a shared base |
| adding new special tokens | LoRA plus `modules_to_save=["embed_tokens", "lm_head"]` (or `trainable_token_indices`) so the new rows train |
| need zero added latency | merge the adapter before serving |
| tiny budgets, classification-style behaviour | prompt tuning or IA3, accepting lower quality |

## 9. Debugging LoRA runs

- **`trainable params: 0`** or a tiny number: `target_modules` did not match any layer names. Print
  `[n for n, _ in model.named_modules()]` and compare; names differ across families (`q_proj` versus
  `query`, `c_attn` in GPT-2, `Wqkv` in some encoders).
- **Loss is NaN with a 4-bit base**: missing `prepare_model_for_kbit_training`, or fp16 instead of
  bf16 for the compute dtype.
- **The adapter "does nothing" at inference**: it was saved but never loaded (you are running the bare
  base model), or it was loaded onto a different base revision than it was trained on.
- **Quality drops after merging**: merged into a quantised model; merge into the bf16 base instead and
  quantise afterwards if needed.
- **New tokens produce garbage**: embeddings were resized but the new rows were left frozen.
- **Outputs degrade on unrelated tasks**: rank or learning rate too high, or too many epochs; LoRA
  forgets less than full fine-tuning but is not immune.

> [!INTERVIEW]
> **"Explain LoRA and QLoRA."** LoRA freezes $W_0$ and learns $\Delta W = \frac{\alpha}{r}BA$ with
> $r \ll d$, $B$ zero-initialised so training starts at the base model; trainable parameters drop from
> $d_{in}d_{out}$ to $r(d_{in}+d_{out})$ per matrix, and the adapter can be merged for zero inference
> overhead. QLoRA stores the frozen base in 4-bit NF4 with double-quantised block scales, dequantises on
> the fly for each matmul, and trains bf16 LoRA adapters, with paged optimizers to absorb memory spikes.
> Mention targeting all linear layers and a ~1e-4 learning rate.

## Summary

- PEFT trains a tiny set of parameters on a frozen base; LoRA learns a low-rank update and merges away.
- LoRA params per matrix: $r(d_{in} + d_{out})$; for an 8B model at $r = 16$ on all linear layers, about 0.5 percent.
- Zero-init $B$, scale by $\alpha/r$, target all linear layers, use a higher LR than full fine-tuning.
- QLoRA: NF4 4-bit base with double quantisation and paged optimizers plus bf16 adapters.
- Many variants (DoRA, rsLoRA, PiSSA, LoftQ) refine initialisation and scaling.

```quiz
[
  {"q": "How many trainable parameters does LoRA with rank r add to a d_out x d_in weight matrix?",
   "options": ["r(d_in + d_out)", "r * d_in * d_out", "d_in * d_out / r", "2r"], "answer": 0,
   "explain": "A is r x d_in and B is d_out x r."},
  {"q": "Why is B initialised to zero in LoRA?",
   "options": ["So the update BA is zero and training starts exactly at the pretrained model", "To save memory", "To make the matrix sparse", "To speed up merging"], "answer": 0,
   "explain": "With B = 0, the adapted model initially behaves identically to the base."},
  {"q": "What does merging a LoRA adapter achieve?",
   "options": ["Folds alpha/r * BA into W so inference has no extra cost", "Quantises the model", "Increases the rank", "Combines two base models"], "answer": 0,
   "explain": "The merged weight has the original shape; the extra adapter matmuls disappear."},
  {"q": "What is NF4 in QLoRA?",
   "options": ["A 4-bit type whose levels are normal-distribution quantiles", "A 4-bit integer format", "A float format with 4 exponent bits", "A LoRA rank of 4"], "answer": 0,
   "explain": "Matching levels to the weight distribution lowers quantisation error."},
  {"q": "In QLoRA, which parameters receive gradient updates?",
   "options": ["Only the bf16 LoRA adapter matrices", "The 4-bit base weights", "Both", "Only layer norms"], "answer": 0,
   "explain": "The quantised base is frozen; gradients pass through it to the adapters."},
  {"q": "Which target_modules choice is usually best for LLM LoRA quality?",
   "options": ["All linear layers, including the MLP projections", "Only q_proj", "Only the embeddings", "Only the LM head"], "answer": 0,
   "explain": "Later studies found adapting MLPs and all projections clearly outperforms attention-only LoRA."},
  {"q": "What is the role of the alpha/r scaling factor?",
   "options": ["Keeps the update's magnitude roughly independent of rank, reducing LR retuning", "Sets the dropout", "Controls quantisation", "Fixes the number of layers"], "answer": 0,
   "explain": "Without it, changing r would change the effective step size of the update."}
]
```

> **Source:** Hu et al., "LoRA" (2021); Dettmers et al., "QLoRA" (2023); PEFT docs
> (https://huggingface.co/docs/peft, LoRA conceptual guide and developer guide); TRL docs, "Train adapters
> with PEFT" (https://huggingface.co/docs/trl/sft_trainer); bitsandbytes docs; Huyen, *AI Engineering*,
> ch. 7 "Finetuning" (memory bottlenecks, PEFT, LoRA, QLoRA, model merging).
