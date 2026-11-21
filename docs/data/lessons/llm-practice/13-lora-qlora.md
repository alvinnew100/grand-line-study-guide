# PEFT: LoRA, QLoRA and friends

> **Before this lesson:** you should know how a model is trained with an optimizer such as Adam, and
> why full fine-tuning needs about 16 bytes per parameter
> ([Datasets, Trainer, Accelerate and serving](#/lesson/llm-practice/datasets-trainer-serving)); how
> a model is loaded in 4-bit with bitsandbytes
> ([Hub, pipelines, Auto classes and generate()](#/lesson/llm-practice/hub-pipelines-generate)); and
> what the linear layers inside a transformer block are (the attention projections and the MLP),
> from [The transformer block](#/lesson/llm-practice/transformer-block). Matrix multiplication with
> numpy's `@` is used throughout.

## In plain words

**Fine-tuning** means taking a model that has already been trained on general text and training it a
little more on your own examples, so it adopts your style, format or specialty. Doing that the
straightforward way changes all of the model's billions of numbers and needs a room full of
expensive GPUs. **LoRA** (low-rank adaptation) is the trick that made fine-tuning affordable: leave
the original numbers untouched and train a tiny add-on, often under one percent of the size, that
nudges the model's behaviour. **QLoRA** goes further by storing the untouched original in a
compressed 4-bit form, so even a very large model fits on one GPU.

An analogy: you inherit a huge, excellent cookbook and want it to suit your family. Rewriting every
page is slow and leaves you with a second huge cookbook per family member. Instead you write short
notes on sticky slips ("use half the salt", "swap butter for olive oil") and attach them. The book
stays intact, the slips are small, you can keep a different set of slips for each person, and you
can even copy the slips' changes permanently into a fresh printing if you like. LoRA adapters are
those slips.

Why it matters for a job: almost every company that customises an open model uses LoRA or QLoRA, and
interviewers ask candidates to explain the formula, count the trainable parameters, and say why the
$B$ matrix starts at zero. It is also where the memory arithmetic of earlier lessons pays off.

## Fine-tuning in context

The AI Engineering track discusses *when* to fine-tune (versus prompting or RAG) and the memory maths
of training. This lesson is the hands-on internals: what LoRA actually computes, why it works, how
QLoRA squeezes a 70B fine-tune onto one GPU, and the `peft` code you will write. (`peft` is Hugging
Face's parameter-efficient fine-tuning library.)

## 1. The problem with full fine-tuning

**Full fine-tuning** updates every weight. With Adam in mixed precision that costs about 16 bytes per
parameter for weights, gradients and optimizer state: about 112 GB for a 7B model before activations,
over 1 TB for 70B. Each task also produces a full-size copy of the model to store and serve.

**Parameter-efficient fine-tuning (PEFT)** **freezes** the pretrained weights (they are used but never
changed, so they need no gradients and no optimizer state) and trains a small number of new
parameters. Families:

- **Additive / adapter**: insert small **bottleneck MLPs** between layers (Houlsby adapters). An MLP
  (multi-layer perceptron) is a small stack of matrix multiplications; "bottleneck" means it squeezes
  the vector down to a few numbers and expands it back.
- **Soft prompts**: learn virtual token embeddings prepended to the input (prompt tuning, prefix
  tuning, P-tuning). These are vectors that act like extra prompt words but do not correspond to any
  real word.
- **Reparameterisation**: learn a low-rank *update* to existing weights: **LoRA** and its variants.
  This is the dominant approach because it adds **no inference latency** once merged.

## 2. LoRA: the idea

First, one piece of linear algebra. The **rank** of a matrix is the number of truly independent
directions it contains. A 4096 x 4096 matrix can have rank up to 4096, but if every row is a
combination of only 8 basic rows, its rank is 8. A key fact: any matrix of rank $r$ can be written as
the product of a tall, thin matrix with $r$ columns and a short, wide matrix with $r$ rows. Storing
those two thin matrices takes far fewer numbers than storing the big one.

Hypothesis (Hu et al. 2021): the weight change needed to adapt a pretrained model has **low intrinsic
rank**, meaning it can be captured well by a low-rank matrix even though the weight itself is huge. So
instead of learning a full $\Delta W \in \mathbb{R}^{d_{out} \times d_{in}}$ (the Greek capital delta
$\Delta$ means "change in"), learn

$$
\Delta W = \frac{\alpha}{r} B A,\qquad B \in \mathbb{R}^{d_{out} \times r},\; A \in \mathbb{R}^{r \times d_{in}},\; r \ll \min(d_{in}, d_{out})
$$

and compute the forward pass as

$$
h = W_0 x + \frac{\alpha}{r} B (A x)
$$

Here $x$ is the layer's input vector and $h$ its output. The first term is the original layer; the
second is the adapter's correction, computed as "multiply by $A$, then by $B$", which never forms the
big matrix at all.

- $W_0$ is frozen. Only $A$ and $B$ are trained: $r(d_{in} + d_{out})$ parameters instead of
  $d_{in} d_{out}$. With $d_{in} = d_{out} = 4096$ and $r = 16$ that is about 131,000 numbers instead
  of about 16.8 million.
- **Initialisation** (the starting values before training): $A$ random (Kaiming/Gaussian, meaning
  drawn from a bell curve scaled to the layer size), $B = 0$, so $\Delta W = 0$ at the start and
  training begins exactly at the pretrained model.
- **Scaling** $\alpha / r$: decouples the update's magnitude from the rank, so you can change $r$
  without retuning the learning rate much. Common: $\alpha = r$ or $\alpha = 2r$. **rsLoRA** uses
  $\alpha/\sqrt{r}$, which keeps learning stable at high ranks.
- **Merging**: after training, $W = W_0 + \frac{\alpha}{r}BA$ is a single matrix of the original shape,
  so inference cost is unchanged. Or keep adapters separate and **hot-swap** many per base model
  (switch between them per request without reloading the base; multi-LoRA serving in vLLM and
  TGI/LoRAX).

The demo checks these claims on one 512 x 512 layer:

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

**Reading this code line by line**

- `W0` is the frozen base weight. Dividing by `np.sqrt(d_in)` keeps its outputs at a sensible size.
- `A` is random and `B` is all zeros, exactly the LoRA initialisation.
- `h = W0 @ x + (alpha / r) * B @ (A @ x)` is the adapted forward pass. Because `B` is zero, the
  correction is zero, and the first print says `identical to base at init: True`.
- Next `B` is filled with small random numbers to pretend training happened. `merged` folds the
  correction into one matrix, and the second print confirms that the merged layer gives the same
  output as base-plus-adapter (`True`).
- `np.linalg.matrix_rank(B @ A)` reports 8: however big the product is (512 x 512), its rank cannot
  exceed $r$.
- The last line counts parameters: 8,192 trainable numbers against 262,144 for the full matrix, about
  3 percent. For larger layers the percentage is far smaller, because $r(d_{in} + d_{out})$ grows
  linearly while $d_{in} d_{out}$ grows quadratically.

### Counting LoRA parameters for a real model

For Llama 3 8B ($d = 4096$, 32 layers, **GQA** (grouped-query attention, lesson 2) with 8 KV heads of
dim 128 so $k, v$ project to 1024, MLP intermediate size 14336), LoRA with $r = 16$ on all linear
layers. Each block has seven linear layers: the four attention projections (query, key, value,
output) and the three MLP matrices (`gate` and `up` expand the vector to 14,336 numbers, `down`
shrinks it back):

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

The loop applies $r(d_{in} + d_{out})$ to each of the seven shapes (stored as `(out, in)` pairs) and
multiplies by 32 layers. The output: rank 8 gives about 21M trainable parameters (0.26 percent), rank
16 about 41.9M (0.52 percent) and rank 64 about 168M (2.09 percent). The adapter file is 2 bytes per
parameter in bf16, so even rank 64 is a few hundred megabytes against 16 GB for the base model.

## 3. Practical LoRA hyperparameters

A **hyperparameter** is a setting chosen before training rather than learned. LoRA has a handful:

- **Target modules** (which linear layers get an adapter): the original paper adapted only `q_proj`
  and `v_proj`, but later work (QLoRA,
  "LoRA Learns Less and Forgets Less", Thinking Machines' "LoRA Without Regret") found that adapting
  **all linear layers, especially the MLPs**, matters most. In `peft`: `target_modules="all-linear"`.
- **Rank**: 8 to 64 is typical. Higher rank gives more capacity, needed for larger datasets or harder
  shifts (new language, heavy reasoning). For small instruction datasets, rank barely matters.
- **Learning rate**: about 10x the full fine-tuning LR, e.g. 1e-4 to 2e-4 (TRL suggests about 1e-4 for
  adapters).
- **Dropout** on the LoRA path: 0 to 0.1. Dropout randomly zeroes a fraction of values during training
  so the model cannot lean too hard on any one of them, a guard against overfitting.
- **What LoRA is good at**: style, format, domain tone, task specialisation, tool-call formats. It is
  less sample-efficient than full fine-tuning for injecting lots of new knowledge, and it "forgets less"
  of the base model's abilities, which is often what you want.

## 4. QLoRA: fine-tuning on a quantised base

**Quantisation** (lesson 6) stores each number with fewer bits. With 4 bits there are only $2^4 = 16$
possible values, called **levels**, so every weight is rounded to the nearest of 16 levels. The art is
choosing where the levels sit. Trained weights follow a **normal distribution** (the bell curve): most
are close to zero, few are large. A **quantile** of a distribution is a cut point below which a given
fraction of values fall; for example the 50 percent quantile of a bell curve centred on zero is zero.

QLoRA (Dettmers et al. 2023) keeps the frozen base in **4-bit** and trains LoRA adapters in bf16 on top:

1. **NF4 (4-bit NormalFloat)**: a 4-bit data type whose 16 levels are quantiles of a normal
   distribution, information-theoretically suited to normally distributed weights (each level is
   used about equally often, so no level is wasted). Weights are quantised in **blocks** of
   consecutive values (e.g. 64) with a per-block **scale**: the block is divided by its largest
   absolute value, so every block fits the range -1 to 1 before rounding.
2. **Double quantisation**: the per-block scales are themselves quantised (to 8-bit), saving about 0.37
   bits per parameter.
3. **Paged optimizers**: optimizer state can spill to CPU memory via **unified memory** paging (the GPU
   driver moves data between GPU and CPU memory automatically, page by page) to survive sudden
   memory spikes, for example from an unusually long training example.
4. During the forward pass, each 4-bit block is **dequantised** (expanded back) **to bf16 on the fly**
   for the **matmul** (matrix multiplication); gradients flow through the frozen dequantised weights
   into the LoRA matrices only.

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

**Reading this code line by line**

- `NormalDist().inv_cdf(p)` returns the quantile of the standard bell curve at probability `p`. Taking
  16 probabilities evenly from 0.02 to 0.98 gives 16 levels that are crowded near zero and sparse at
  the edges; dividing by the largest makes them span -1 to 1.
- `w` holds 64,000 normally distributed "weights", reshaped into 1,000 blocks of 64.
- `scale` is each block's **absmax** (largest absolute value). Dividing by it maps the block into
  -1 to 1.
- `codes = np.abs(... - levels).argmin(-1)` finds, for each weight, the index (0 to 15) of the nearest
  level: that index is the 4-bit code that would be stored. `deq` turns codes back into numbers.
- The same steps run with 16 evenly spaced levels (`uniform`) for comparison.
- The output: the NF4-like levels give a mean absolute error of about 0.00147, the uniform levels
  about 0.00171, roughly 17 percent higher.

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

**Reading this code line by line**

- `BitsAndBytesConfig(...)` describes QLoRA's storage: 4-bit NF4, double quantisation, and bf16 for
  the arithmetic. Passing it as `quantization_config` makes `from_pretrained` quantise the weights as
  they load.
- `prepare_model_for_kbit_training` gets a quantised model ready for training: it keeps the small
  normalisation layers in 32-bit for stability and switches on the plumbing that lets gradients flow
  back through the frozen layers to the adapters.
- `LoraConfig` holds the adapter settings: rank 16, `lora_alpha=32` (so the scale $\alpha/r$ is 2),
  5 percent dropout, no trainable biases, adapters on every linear layer, and `task_type="CAUSAL_LM"`
  to say this is a text-generation model.
- `get_peft_model(model, lora)` inserts the $A$ and $B$ matrices next to each targeted layer and
  freezes everything else. `print_trainable_parameters()` prints the line shown in the comment: about
  41.9 million trainable out of about 8.07 billion, 0.52 percent, matching the table above.
- `save_pretrained` writes only the adapter weights and their config, about 80 MB.

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

Here the base model is loaded in ordinary bf16, `PeftModel.from_pretrained(base, adapter_id)` attaches
the trained adapter, and `merge_and_unload()` adds $\frac{\alpha}{r}BA$ into each weight and removes
the adapter modules, leaving a plain model that any tool can serve. The commented `vllm serve` line
shows the alternative: keep the base unmerged and let vLLM apply the adapter named `support` to the
requests that ask for it.

> [!WARNING]
> Merge adapters into a **bf16** copy of the base, not into the 4-bit quantised weights; merging into
> a quantised model and re-quantising introduces rounding error that can noticeably change behaviour.

## 6. The LoRA family

LoRA spawned many variants. You do not need their internals for most work, but you should recognise
the names and know which `peft` switch turns each on:

- **DoRA**: decomposes each weight into a **magnitude** (how long each column vector is) and a
  **direction** (where it points), applies LoRA to the direction and trains the magnitude separately;
  often a small quality bump (`use_dora=True`).
- **rsLoRA**: rank-stabilised scaling $\alpha/\sqrt{r}$ (`use_rslora=True`).
- **PiSSA / LoftQ**: initialise $A, B$ from the **principal singular vectors** of $W_0$ (the few
  directions that carry most of the matrix's weight, found by a standard factorisation called the
  SVD), or to compensate quantisation error, instead of zero/random.
- **LoRA+**: different learning rates for $A$ and $B$.
- **VeRA, LoKr, LoHa, IA3**: even fewer parameters via shared random matrices, Kronecker or Hadamard
  products (two other ways of building a big matrix from small ones), or learned rescaling vectors.
- **Prompt / prefix tuning**: train virtual tokens only; tiny, but usually weaker than LoRA on LLMs.

## 7. Training a LoRA adapter by hand

To see LoRA learn, we fit an adapter with plain **gradient descent** (repeatedly move each trainable
number a small step against its gradient) in numpy. The frozen base $W_0$ should have been a different
matrix $W^\star = W_0 + \Delta^\star$, where the true change $\Delta^\star$ has rank 2. We minimise the
squared error of the adapted layer's outputs and compare ranks. The gradients follow from the **chain
rule** (the calculus rule for the gradient of a function of a function) with $\Delta W = sBA$,
$s = \alpha/r$. In words: first compute $G$, the gradient with respect to the whole change $\Delta W$;
then $B$'s gradient is $G$ multiplied by $A$ turned on its side, and $A$'s gradient is $B$ turned on
its side multiplied by $G$:

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

How the code works: `delta_true` is built as a 32 x 2 matrix times a 2 x 32 matrix, so it has rank 2
by construction. `Y` holds the outputs the adapted layer should produce for 512 random inputs. Inside
`train_lora`, `err` is the difference between the current outputs and the targets, `G` is the gradient
of the mean squared error with respect to $\Delta W$, and the update line moves `B` and `A` together
(the right-hand side is computed with the old values of both before either is replaced). The function
returns the final loss and the number of trainable parameters. The output: the base model's loss is
about 5.81; rank 1 gets stuck at about 2.51; ranks 2, 4 and 8 all reach 0.00000.

What to notice:

- **Rank 1 cannot fit a rank-2 change**: the loss plateaus well above zero. Capacity is a hard limit.
- **Rank 2 suffices**, and higher ranks add parameters without improving the fit. On real tasks the
  required rank is unknown, which is why people sweep 8, 16, 32, 64 and watch validation metrics.
- At step 0 only $B$ receives a non-zero gradient (because $B = 0$ makes $\partial\mathcal{L}/\partial A = 0$);
  $A$ starts moving once $B$ is non-zero. This asymmetry is what LoRA+ exploits with a larger learning
  rate for $B$.
- Keeping `alpha = 2r` fixed the effective step size across ranks, so one learning rate worked for all.

## 8. Choosing among adaptation methods

The table maps common situations to a sensible first choice. In it, `modules_to_save` tells `peft` to
train full copies of the listed modules (here the embedding table and the LM head) alongside the
adapters, which is needed when new tokens get new rows.

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

## Glossary

- **Fine-tuning / full fine-tuning**: further training of a pretrained model / training that updates
  every weight.
- **PEFT**: parameter-efficient fine-tuning, training a small set of new parameters on a frozen model.
- **Frozen weights**: weights used in the forward pass but never updated.
- **Adapter**: the small trainable add-on that PEFT methods attach to a frozen model.
- **Matrix rank / low rank**: the number of independent directions in a matrix / few such directions.
- **LoRA**: learning a weight change as the product of two thin matrices, $\frac{\alpha}{r}BA$.
- **Rank $r$ / alpha $\alpha$**: the inner width of $A$ and $B$ / the scale applied to their product.
- **Target modules**: the layers that receive adapters.
- **Merging**: adding the adapter's change into the base weights so no adapter remains.
- **Hot-swapping**: switching adapters per request on one shared base model.
- **Quantisation level / quantile**: one of the few values a quantised number may take / a cut point
  of a distribution.
- **NF4**: a 4-bit format whose 16 levels are bell-curve quantiles.
- **Block-wise absmax scaling**: dividing each block by its largest absolute value before rounding.
- **Double quantisation**: also quantising the per-block scales.
- **Paged optimizer**: optimizer state that can spill from GPU to CPU memory during spikes.
- **QLoRA**: LoRA adapters in bf16 trained on top of a frozen 4-bit NF4 base.
- **Dropout**: randomly zeroing values during training to reduce overfitting.
- **DoRA / rsLoRA / PiSSA / LoftQ**: LoRA variants that change the decomposition, scaling or starting
  values.

## Check yourself

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
