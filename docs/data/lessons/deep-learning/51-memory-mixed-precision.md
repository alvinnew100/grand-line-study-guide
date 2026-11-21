# GPU memory and mixed precision (autocast, bf16, GradScaler)

> **Before this lesson:** you need dtypes (float32, float16, bfloat16) from [Tensors: creation, indexing, dtypes and broadcasting](#/lesson/deep-learning/tensors-basics), devices from [storage, strides, views and devices](#/lesson/deep-learning/tensor-storage), Adam's state from [Optimisers and validation](#/lesson/deep-learning/optimizers-validation), and gradient clipping from [Learning-rate schedules, warmup and gradient clipping](#/lesson/deep-learning/schedules-clipping).

## In plain words

A GPU has a fixed amount of fast memory, and training fills it with four things: the model's **parameters**, their **gradients**, the **optimiser's state** (Adam keeps two extra numbers per parameter), and the **activations**, the intermediate results of the forward pass that the backward pass needs. Running out produces the dreaded "CUDA out of memory" error. Knowing what uses memory, and how much, lets you predict whether a model fits and pick the right fix.

The biggest single lever is **mixed precision**: doing most arithmetic in 16-bit numbers instead of 32-bit ones. That halves the memory of activations and lets the GPU's specialised matrix units (**Tensor Cores**) run several times faster. "Mixed" because a few sensitive operations stay in 32-bit for accuracy. PyTorch automates the choice with `torch.autocast`, and, for the float16 format, protects tiny gradients from rounding to zero with a `GradScaler`.

Think of packing a suitcase. The parameters are the clothes you must bring; gradients and optimiser state are a second and third copy of everything for laundry and repairs; activations are souvenirs you pick up during the trip and must keep until you head home (the backward pass). Mixed precision is vacuum-packing: the same items in half the space, with fragile ones still wrapped individually.

Why it matters for a job: GPU time is the main cost of deep learning, and interviewers at AI-focused companies routinely ask you to estimate memory for a model ("how much memory to fine-tune a 7-billion-parameter model with Adam?"), explain bfloat16 versus float16, and describe what to do on an out-of-memory error.

## 1. Where the memory goes

For a model with $P$ parameters trained with Adam in plain float32:

| item | bytes per parameter | why |
|---|---|---|
| parameters | 4 | float32 weights |
| gradients | 4 | one per parameter |
| Adam first moment $m$ | 4 | running mean of gradients |
| Adam second moment $v$ | 4 | running mean of squared gradients |
| **total (before activations)** | **16** | |

Plain SGD without momentum needs 8 bytes per parameter; SGD with momentum 12.

**Activations** come on top, and for large inputs they dominate. Every layer saves what its backward pass needs (inputs to matrix multiplications, ReLU masks, normalisation statistics), so activation memory grows roughly as

$$\text{batch size} \times \text{(spatial positions or sequence length)} \times \text{width} \times \text{number of layers} \times \text{bytes per value}$$

For transformers, attention can add a term that grows with the square of the sequence length (modern fused attention kernels avoid storing it). There is also a fixed overhead: the CUDA context (a few hundred megabytes), temporary workspace for some kernels, and fragmentation in PyTorch's **caching allocator**, which keeps freed blocks reserved for reuse rather than returning them to the GPU driver.

```python-run
def training_memory_gb(params, optimizer="adam", grads=True, weight_bytes=4, state_bytes=4):
    per_param = weight_bytes + (weight_bytes if grads else 0)
    per_param += {"sgd": 0, "momentum": 1, "adam": 2}[optimizer] * state_bytes
    return params * per_param / 1e9, per_param

for name, n in [("ResNet-50", 25.6e6), ("BERT-base", 110e6), ("7B LLM", 7e9)]:
    full, bpp = training_memory_gb(n)
    infer = n * 2 / 1e9
    print(f"{name:10s} {n / 1e6:8.0f}M params | Adam fp32 training: {full:7.1f} GB ({bpp} B/param) "
          f"| bf16 inference weights: {infer:6.2f} GB")

# Activation estimate for a convnet layer: batch 64, 64 channels, 112 x 112 feature map, saved once
acts = 64 * 64 * 112 * 112
print(f"\none 64x64x112x112 activation tensor: {acts * 4 / 1e9:.2f} GB in fp32, {acts * 2 / 1e9:.2f} GB in 16-bit")
```

A 7-billion-parameter model needs about 112 GB for float32 weights, gradients and Adam state: more than any single GPU, before a single activation is stored. That is why large-model training uses lower precision for some of these, shards them across GPUs (FSDP, ZeRO), or fine-tunes only a small adapter (LoRA). By contrast, inference needs only the weights: 14 GB in 16-bit.

### Reading memory in PyTorch

```python
torch.cuda.memory_allocated() / 1e9        # GB currently held by live tensors
torch.cuda.max_memory_allocated() / 1e9    # peak since start (or since reset_peak_memory_stats())
torch.cuda.memory_reserved() / 1e9         # GB held by the caching allocator (includes free cached blocks)
print(torch.cuda.memory_summary())         # detailed breakdown
torch.cuda.empty_cache()                   # returns cached, unused blocks to the driver; does NOT free live tensors
```

The peak usually occurs at the end of the forward pass (all activations alive) or during the optimiser step (Adam state created lazily on the first step).

## 2. Number formats

| format | bits (sign, exponent, mantissa) | largest value | smallest normal value | significant decimal digits |
|---|---|---|---|---|
| float32 | 1, 8, 23 | about $3.4 \times 10^{38}$ | about $1.2 \times 10^{-38}$ | about 7 |
| float16 | 1, 5, 10 | 65,504 | about $6.1 \times 10^{-5}$ | about 3 |
| bfloat16 | 1, 8, 7 | about $3.4 \times 10^{38}$ | about $1.2 \times 10^{-38}$ | about 2 to 3 |
| TF32 (internal to matmuls) | 1, 8, 10 | as float32 | as float32 | about 3 |

The **exponent** bits set the range (how large or small numbers can be); the **mantissa** bits set the precision (how many digits). float16 has decent precision but a narrow range: values above 65,504 overflow to infinity, and gradients smaller than about $10^{-7}$ (even with subnormals, numbers below the smallest normal value stored with reduced precision) round to zero. **bfloat16** ("brain floating point", from Google) keeps float32's exponent, so it has the same range and never overflows where float32 would not, at the cost of fewer digits. Neural networks tolerate low precision well but are badly hurt by overflow and underflow, which is why bfloat16 has become the default on hardware that supports it (NVIDIA Ampere generation and newer, such as A100 and H100, and Google TPUs).

**TF32** is a format NVIDIA GPUs (Ampere and newer) can use inside float32 matrix multiplications, trading some precision for speed with no code changes; enable it with `torch.set_float32_matmul_precision("high")`.

```python-run
import numpy as np

def to_bfloat16(x):
    """Round float32 values to bfloat16 precision (keep the top 16 bits, round to nearest even)."""
    b = np.asarray(x, dtype=np.float32).view(np.uint32).astype(np.uint64)
    rounding = 0x7FFF + ((b >> 16) & 1)
    return ((b + rounding) >> 16 << 16).astype(np.uint32).view(np.float32)

values = np.array([1.0, 1.001, 3.14159265, 70000.0, 1e-8, 1e20], dtype=np.float32)
with np.errstate(over="ignore"):
    fp16 = values.astype(np.float16)
print(f"{'float32':>14} {'float16':>12} {'bfloat16':>12}")
for v, h, b in zip(values, fp16, to_bfloat16(values)):
    print(f"{v:>14.8g} {float(h):>12.6g} {float(b):>12.6g}")

grads = np.array([1e-3, 1e-5, 1e-7, 1e-9], dtype=np.float32)
print("\nsmall gradients in float16:          ", grads.astype(np.float16))
scale = 65536.0                                                    # GradScaler's default initial scale
scaled = (grads * scale).astype(np.float16)
print("scaled by 65536, stored in float16:   ", scaled)
print("unscaled back in float32:             ", scaled.astype(np.float32) / scale)
```

**Reading the output**

- float16 handles 1.001 and pi to about 3 digits, overflows 70,000 to infinity, and flushes $10^{-8}$ to 0.
- bfloat16 cannot tell 1.001 from 1.0 (too few digits), but represents 70,000, $10^{-8}$ and $10^{20}$ approximately: range is preserved.
- In float16, a gradient of $10^{-7}$ survives only as a coarse subnormal, and $10^{-9}$ vanishes entirely. Multiplying them by 65,536 before storing moves them into float16's representable range; dividing afterwards (in float32) recovers them. That is **loss scaling**, the job of `GradScaler`.

## 3. Autocast

`torch.autocast` is a context manager that runs each operation inside it in a dtype chosen per operation:

- **Lower precision** for operations that benefit and are numerically safe: matrix multiplications, convolutions, linear layers, attention.
- **float32** for operations that need range or accumulate many values: softmax, log, exp, reductions such as sum and mean, normalisation layers, and losses.

The model's parameters stay in float32 (the **master weights**); autocast casts copies on the fly. Activations saved for backward are mostly 16-bit, which is where the memory saving comes from.

```python
# bfloat16 (Ampere or newer GPUs, TPUs, recent CPUs): no scaler needed
for x, y in loader:
    optimizer.zero_grad(set_to_none=True)
    with torch.autocast(device_type="cuda", dtype=torch.bfloat16):
        logits = model(x)
        loss = loss_fn(logits, y)          # computed in float32 by autocast's rules
    loss.backward()                        # outside the context: backward reuses the forward's dtypes
    optimizer.step()
```

Rules from the documentation: wrap only the forward pass and the loss; do not call `.half()` or `.bfloat16()` on the model or inputs yourself; run `backward()` outside the context. Outputs produced inside autocast may be 16-bit, so cast them to float32 if you combine them with float32 tensors outside.

## 4. GradScaler for float16

With float16, small gradients underflow to zero. **Dynamic loss scaling** multiplies the loss by a large factor $S$ before `backward()`, so every gradient is $S$ times larger and stays representable, then divides the gradients by $S$ before the optimiser uses them. If the scaled gradients overflow to infinity or NaN, the step is skipped and $S$ is reduced; after a run of successful steps, $S$ is increased again to use as much of the range as possible.

```python
scaler = torch.amp.GradScaler("cuda")       # defaults: init_scale=65536, growth_factor=2, backoff_factor=0.5, growth_interval=2000

for x, y in loader:
    optimizer.zero_grad(set_to_none=True)
    with torch.autocast(device_type="cuda", dtype=torch.float16):
        loss = loss_fn(model(x), y)
    scaler.scale(loss).backward()           # backward on loss * S
    scaler.unscale_(optimizer)              # divide gradients by S in place (needed before clipping)
    torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
    scaler.step(optimizer)                  # skips the step if any gradient is inf or NaN
    scaler.update()                         # shrink S after an overflow, grow it after 2000 clean steps
```

- `scaler.step` unscales automatically if you did not call `unscale_` yourself; call `unscale_` explicitly only when you need true gradients first (clipping, logging norms).
- Occasional skipped steps early in training are normal: that is the scaler finding the largest safe scale.
- With bfloat16 you normally need no scaler, which is one more reason to prefer it.
- Save `scaler.state_dict()` in checkpoints.

## 5. Other ways to fit a model

When memory is tight, in rough order of how often you reach for them:

1. **Mixed precision** (above).
2. **Smaller batch plus gradient accumulation**: run $k$ micro-batches, divide each loss by $k$, call `backward()` each time, and step once (see [Autograd in depth](#/lesson/deep-learning/autograd)). Same effective batch, a fraction of the activation memory.
3. **Activation (gradient) checkpointing**: `torch.utils.checkpoint.checkpoint(block, x, use_reentrant=False)` stores only a block's input and recomputes its internals during backward. Trades roughly one extra forward pass of compute for a large activation saving; standard for long-sequence transformers.
4. **Evaluation without graphs**: always validate under `torch.inference_mode()` or `torch.no_grad()`.
5. **Memory-efficient optimisers**: 8-bit Adam states (bitsandbytes), Adafactor, or SGD with momentum.
6. **Sharding across GPUs**: Fully Sharded Data Parallel (FSDP) splits parameters, gradients and optimiser state across devices; DeepSpeed ZeRO does the same. Offloading moves some state to CPU memory.
7. **Parameter-efficient fine-tuning**: train small adapters (LoRA) and freeze the rest, so gradients and optimiser state exist only for a tiny fraction of parameters.

Lower-precision formats keep arriving: **FP8** training on H100-class GPUs (through libraries such as NVIDIA Transformer Engine or torchao) and 8-bit or 4-bit weights for inference ([quantisation in the serving lesson](#/lesson/deep-learning/serving-export)).

> [!INTERVIEW]
> **"How much GPU memory do you need to fine-tune a 7B-parameter model with AdamW, and how would you make it fit on one 80 GB GPU?"** Full fine-tuning in float32 needs about 16 bytes per parameter for weights, gradients and Adam's two moments: roughly 112 GB, before activations. It does not fit. Options: bf16 mixed precision with 8-bit optimiser states, activation checkpointing and small micro-batches with gradient accumulation; shard across GPUs with FSDP; or, most commonly, LoRA or QLoRA, which freeze the base weights (in bf16 or 4-bit) and train small adapters, bringing memory down to a fraction. Mention that activations scale with batch size and sequence length and must be budgeted too.

## Summary

- Training memory = parameters + gradients + optimiser state + activations + overhead; Adam in float32 costs 16 bytes per parameter before activations.
- Activations scale with batch size, spatial size or sequence length, width and depth, and usually dominate for large inputs.
- float16 has 5 exponent bits (narrow range); bfloat16 keeps float32's 8-bit exponent with fewer mantissa bits; TF32 speeds up float32 matmuls.
- `torch.autocast` runs matmuls and convolutions in 16-bit and keeps sensitive ops in float32; parameters stay float32; run backward outside it.
- `GradScaler` (needed for float16, not bfloat16) scales the loss to prevent gradient underflow, skips overflowed steps and adapts the scale; unscale before clipping.
- Other levers: gradient accumulation, activation checkpointing, no-grad evaluation, 8-bit optimisers, FSDP/ZeRO sharding, LoRA.

## Glossary

- **Activations**: intermediate forward-pass results saved for the backward pass.
- **Optimiser state**: extra per-parameter values an optimiser keeps (momentum, Adam moments).
- **Caching allocator**: PyTorch's GPU memory manager that keeps freed blocks for reuse.
- **Out of memory (OOM)**: failing to allocate because device memory is exhausted.
- **Exponent / mantissa**: the bits setting a float's range / its precision.
- **float16 / bfloat16 / TF32**: 16-bit IEEE half precision / 16-bit with float32's range / a reduced-precision mode for float32 matmuls.
- **Subnormal numbers**: tiny floats below the smallest normal value, stored with reduced precision.
- **Tensor Cores**: GPU units specialised for low-precision matrix multiplication.
- **Mixed precision**: computing mostly in 16-bit while keeping sensitive parts in 32-bit.
- **Autocast**: PyTorch's automatic per-operation choice of precision.
- **Master weights**: the float32 copy of parameters that optimiser updates are applied to.
- **Loss scaling / GradScaler**: multiplying the loss to keep float16 gradients representable / PyTorch's dynamic implementation.
- **Activation checkpointing**: recomputing activations in backward instead of storing them.
- **FSDP / ZeRO**: sharding parameters, gradients and optimiser state across GPUs.

## Check yourself

```quiz
[
  {"q": "Roughly how many bytes per parameter does float32 training with Adam need, before activations?", "options": ["16", "4", "8", "32"], "answer": 0,
   "explain": "Weights 4, gradients 4, and two Adam moments 4 each."},
  {"q": "Why is bfloat16 usually preferred over float16 for training on hardware that supports it?", "options": ["It keeps float32's exponent range, so overflow and underflow are rare and no loss scaling is needed", "It has more mantissa bits", "It uses less memory than float16", "It is exact"], "answer": 0,
   "explain": "bfloat16 trades precision for range; neural networks tolerate the former better."},
  {"q": "What does GradScaler do when the scaled gradients contain inf or NaN?", "options": ["Skips the optimizer step and reduces the scale", "Raises an error", "Clips the gradients to 1", "Switches to float32 permanently"], "answer": 0,
   "explain": "Then, after enough clean steps, it grows the scale again."},
  {"q": "Inside torch.autocast(dtype=torch.float16), in which precision does softmax typically run?", "options": ["float32", "float16", "int8", "bfloat16"], "answer": 0,
   "explain": "Autocast keeps range-sensitive ops such as softmax, log and reductions in float32."},
  {"q": "Where should loss.backward() be called when using autocast?", "options": ["Outside the autocast context", "Inside the autocast context", "Inside torch.no_grad()", "Before the forward pass"], "answer": 0,
   "explain": "Backward ops automatically use the dtypes chosen in the forward pass."},
  {"q": "What does torch.cuda.empty_cache() do?", "options": ["Releases cached but unused memory blocks back to the driver; live tensors are unaffected", "Deletes all tensors on the GPU", "Clears gradients", "Resets the optimizer"], "answer": 0,
   "explain": "It does not reduce memory used by tensors you still reference."},
  {"q": "What does activation checkpointing trade?", "options": ["Extra computation (recomputing activations in backward) for lower memory", "Accuracy for speed", "Memory for fewer parameters", "Precision for range"], "answer": 0,
   "explain": "Only block inputs are stored; internals are recomputed when needed."},
  {"q": "With mixed precision and gradient clipping using float16, what is the correct order?", "options": ["scale(loss).backward, unscale_, clip, scaler.step, scaler.update", "clip, backward, step", "scaler.step, unscale_, clip", "unscale_, backward, clip, step"], "answer": 0,
   "explain": "Clipping must see true (unscaled) gradients."}
]
```

> **Source:** Stevens, Antiga & Viehmann, *Deep Learning with PyTorch*, ch. 3 (element types, half precision) and ch. 15 (model efficiency, half precision); PyTorch documentation (docs.pytorch.org): "Automatic Mixed Precision package - torch.amp", "Automatic Mixed Precision examples" (autocast, GradScaler defaults and usage), "CUDA semantics" (memory management), `torch.utils.checkpoint`.
