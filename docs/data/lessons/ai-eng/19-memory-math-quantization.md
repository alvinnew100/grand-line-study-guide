# Memory math, numerical formats and quantization

Huyen identifies **memory** as the practical bottleneck of working with foundation models, for both inference and finetuning. Many finetuning techniques exist mainly to reduce memory. If you can estimate how much memory a model needs, you can answer everyday questions quickly. Will this model fit on a 24 GB GPU? Can we finetune it on one A100? What do we gain from 4-bit weights? This lesson covers backpropagation and trainable parameters, the memory formulas, numerical representations, and quantization.

## 1. Backpropagation and trainable parameters

Training a neural network repeats two phases per step:

1. **Forward pass**: compute the output from the input.
2. **Backward pass**: compare the output with the target to get the **loss**, compute each trainable parameter's **gradient** (how much it contributed to the error), and update parameters with an **optimizer** such as SGD or Adam.

A **trainable parameter** is one that can be updated during finetuning. Parameters that are not updated are **frozen**. During **inference** only the forward pass runs. During training, the backward pass needs to store gradients and optimizer state, and it reuses stored activations from the forward pass. That is why **training needs much more memory than inference**, and why memory grows with the number of *trainable* parameters. Reducing trainable parameters is the idea behind PEFT (next lesson).

## 2. Memory math

These are approximations. They ignore many optimizations and workload details, but they give the right order of magnitude.

### Inference

Let $N$ be the parameter count and $M$ the bytes per parameter. The weights need:

$$\text{weights} = N \times M$$

The forward pass also needs memory for **activations**, and transformers need **key-value vectors** for attention. Both grow with sequence length and batch size. Huyen's rule of thumb is to assume this overhead is **20%** of the weight memory:

$$\text{inference memory} \approx N \times M \times 1.2$$

Example: a **13B** model at 2 bytes per parameter needs $13\text{B}\times 2 = 26$ GB for weights and $26 \times 1.2 = 31.2$ GB in total. A 70B model at 2 bytes needs 140 GB for weights alone. Longer contexts and larger batches push the real number higher.

### Training

$$\text{training memory} = \text{weights} + \text{activations} + \text{gradients} + \text{optimizer states}$$

Each **trainable** parameter needs one value for its gradient plus zero to two values of optimizer state:

- vanilla **SGD**: 0 extra values,
- **momentum**: 1 extra value,
- **Adam**: 2 extra values.

Updating all 13B parameters with Adam at 2 bytes per value:

$$13\text{B} \times 3 \times 2\ \text{bytes} = 78\ \text{GB}$$

for gradients and optimizer state alone. With only **1B trainable** parameters it is $1\text{B}\times3\times2 = 6$ GB.

Activations can be much larger than weights during training, because they are stored for gradient computation. Huyen cites Korthikanti et al. (2022) on Megatron models. **Gradient checkpointing** (activation recomputation) avoids storing them all by recomputing when needed. This uses less memory and takes more training time.

```python-run
GB = 1e9
def inference_gb(params, bytes_per_param, overhead=0.2):
    return params * bytes_per_param * (1 + overhead) / GB
def training_gb(params, trainable, bytes_per_value, optimizer="adam", overhead=0.2):
    extra = {"sgd": 0, "momentum": 1, "adam": 2}[optimizer]
    return (params * bytes_per_value * (1 + overhead) + trainable * (1 + extra) * bytes_per_value) / GB

for name, n in [("7B", 7e9), ("13B", 13e9), ("70B", 70e9)]:
    print(f"{name}: inference FP16 {inference_gb(n, 2):6.1f} GB | INT8 {inference_gb(n, 1):6.1f} GB | 4-bit {inference_gb(n, 0.5):6.1f} GB")
print(f"13B full finetune (Adam, FP16): {training_gb(13e9, 13e9, 2):.1f} GB")
print(f"13B with 1B trainable params  : {training_gb(13e9, 1e9, 2):.1f} GB")
print(f"13B with 3.28M LoRA params    : {training_gb(13e9, 3.28e6, 2):.2f} GB")
```

> [!INTERVIEW]
> **"Can we run a 13B model on a 24 GB GPU?"** At FP16, weights are 26 GB and about 31 GB with overhead, so no. At 8-bit (1 byte per parameter) it is about 15.6 GB, so yes. At 4-bit it is about 7.8 GB. Then mention that context length and batch size increase KV-cache and activation memory, so leave headroom. For finetuning, add (1 + optimizer states) values per **trainable** parameter. Full finetuning with Adam adds 3× the parameter count in values, which is why PEFT exists.

## 3. Numerical representations

Each value's size feeds directly into memory. Neural networks traditionally use **floating point** numbers in IEEE 754 formats:

| Format | Bits | Notes |
|---|---|---|
| FP64 (double) | 64 | NumPy and pandas default. Rare in neural networks |
| FP32 (single) | 32 | long the standard for training |
| FP16 (half) | 16 | common for inference |
| BF16 (bfloat16) | 16 | from Google, for AI on TPUs. Same bits as FP16, with more for range and fewer for precision |
| TF32 | 19 significant | from NVIDIA, for GPUs |
| INT8 / INT4 | 8 / 4 | integer formats used for quantized models |

A float uses 1 **sign** bit, and the remaining bits are split between **range** (exponent) and **precision** (significand). More range bits represent larger and smaller magnitudes, and more precision bits distinguish closer values.

Converting to a lower-precision format changes values. From Huyen's table, 1234.56789 becomes 1235.0 in FP16 (a 0.035% change) and 1232.0 in BF16 (a 0.208% change). BF16 is less precise but has more range: 123456.789 becomes INF in FP16 and stays representable in BF16.

```python-run
import numpy as np
vals = np.array([0.0123456789, 1.23456789, 1234.56789, 123456.789], dtype=np.float64)
with np.errstate(over="ignore"):
    f16 = vals.astype(np.float16)
for v, a in zip(vals, f16):
    print(f"FP64 {v:>14.7f} -> FP16 {float(a):>14.7f}   rel. change {abs(float(a)-v)/v:.4%}" if np.isfinite(a) else f"FP64 {v:>14.7f} -> FP16 INF (out of range)")
```

> [!WARNING]
> Load a model in the format it was meant for. Llama 2 was released with BF16 weights, and many teams loaded it in FP16 and got noticeably worse quality than advertised. The right format depends on your value ranges, your sensitivity to small numerical changes, and your hardware.

## 4. Quantization

Fewer bits per value means a smaller model. A 10B model takes 40 GB at 32 bits and 20 GB at 16 bits. **Quantization** is a cheap and very effective way to cut the memory footprint. It is easy to apply and works across tasks and architectures.

> [!NOTE]
> Strictly speaking, "quantization" means converting to an **integer** format, and going from FP32 to FP16 is "reduced precision". In practice, and in the book, quantization refers to any conversion to a lower-precision format.

Two decisions:

- **What to quantize.** Ideally whatever uses the most memory: weights and activations. **Weight quantization** is more common because it affects accuracy more stably.
- **When to quantize.** During training, or **post-training quantization (PTQ)**, which quantizes an already trained model. PTQ is by far the most common and the most relevant to application developers.

### Inference quantization

Serving in 16 bits became common in the late 2010s, and lower is now routine. LLM.int8() quantizes to 8 bits and QLoRA uses 4 bits (Dettmers et al.). Models can be served in **mixed precision**. Apple (2024) used a mix of 2-bit and 4-bit formats averaging **3.5 bits per weight** for on-device models. NVIDIA's Blackwell architecture supports 4-bit float inference.

At 8 bits and below, values are usually converted to **integers** (INT8, INT4), though minifloat formats (FP8, FP4) exist. The floor is 1 bit per value: BinaryConnect, XNOR-Net and BitNet. Microsoft's **BitNet b1.58** (2024) uses ternary weights of −1, 0 and 1, which is about 1.58 bits per parameter. It reported performance comparable to 16-bit Llama 2 at sizes up to 3.9B parameters, with large efficiency gains.

Reduced precision cuts memory and often **speeds up computation**. Larger batches fit, and lower-precision arithmetic is faster. An addition in 16 bits takes roughly half the time of one in 32 bits. The downsides are that each conversion introduces small errors that can accumulate into a quality drop, and values outside the representable range can become infinity or get clipped to arbitrary values.

**How integer quantization works (symmetric linear).** Choose a scale from the largest absolute value, then round:

$$s = \frac{\max|x|}{127},\qquad q = \operatorname{clip}\!\big(\operatorname{round}(x/s),\,-127,\,127\big),\qquad \hat{x} = q\cdot s$$

```python-run
import numpy as np
rng = np.random.default_rng(0)
w = rng.normal(0, 0.05, size=10_000).astype(np.float32)
def quantize(w, bits):
    qmax = 2 ** (bits - 1) - 1
    scale = np.abs(w).max() / qmax
    q = np.clip(np.round(w / scale), -qmax, qmax)
    return q * scale
for bits in [8, 4, 2]:
    err = np.abs(quantize(w, bits) - w)
    print(f"{bits}-bit: {32 // bits:>2}x smaller than FP32, mean abs error {err.mean():.5f}, max {err.max():.5f}")
w_out = w.copy(); w_out[0] = 5.0            # a single outlier stretches the scale and wastes resolution
print("8-bit with one outlier: mean abs error", np.abs(quantize(w_out, 8) - w_out).mean().round(5))
```

The outlier line shows why real quantizers clip ranges, quantize per channel, or use calibration data. One extreme value can ruin the resolution for all the others.

PTQ is widely supported. Major frameworks offer it nearly for free: PyTorch, TensorFlow and Hugging Face Transformers, plus on-device stacks such as TensorFlow Lite, PyTorch Mobile and ONNX Runtime.

### Training quantization

- **Quantization-aware training (QAT)** simulates low-precision behaviour, for example 8-bit, during training so that the model learns to produce good outputs at low precision. It helps the quality of the quantized model. It does not shorten training and can lengthen it.
- **Training directly in lower precision** saves memory and time. Models have been trained at reduced precision for years. Character.AI (2024) trained models entirely in INT8, which removed the training/serving mismatch and improved efficiency. It is harder, because backpropagation is more sensitive to low precision.
- **Mixed precision** is the practical middle ground. A higher-precision copy of the weights is kept, while operations run at lower precision where that is safe. Frameworks offer **automatic mixed precision (AMP)**, which picks precisions per operation.

A common pattern is to train in higher precision, for example FP16 or BF16, and quantize afterwards for serving.

## Pitfalls

- Estimating memory from parameter count alone and forgetting activations, the KV cache, batch size and context length.
- Forgetting that training memory scales with *trainable* parameters times (1 + optimizer state).
- Loading weights in the wrong format (BF16 vs FP16).
- Assuming quantization is free. Evaluate quality after quantizing, especially below 8 bits.
- Confusing GB (1e9 bytes) with GiB (2^30 bytes) when you are close to a hardware limit.

## Summary

- Training runs a forward and a backward pass. The backward pass needs gradients and optimizer state for each **trainable** parameter.
- **Inference memory** ≈ $N \times M \times 1.2$. **Training memory** = weights + activations + gradients + optimizer states. Adam means 3 values per trainable parameter.
- Numerical formats trade range and precision against size: FP32, FP16, BF16, INT8, INT4. Load models in their intended format.
- **Quantization** reduces bits per value. **PTQ** is the default. 8-bit and 4-bit are common, and 1.58-bit is possible. **QAT**, low-precision training and **mixed precision (AMP)** apply quantization during training.

```quiz
[
  {"q": "Approximate inference memory for a 13B-parameter model at 2 bytes/param with Huyen's 20% overhead?", "options": ["13 GB", "26 GB", "31.2 GB", "78 GB"], "answer": 2, "explain": "13B × 2 bytes = 26 GB; × 1.2 = 31.2 GB."},
  {"q": "With Adam, how many values per trainable parameter are needed for gradients and optimizer states?", "options": ["1", "2", "3", "4"], "answer": 2, "explain": "One gradient plus two Adam states (first and second moment)."},
  {"q": "Full finetuning of a 13B model with Adam at 2 bytes/value needs how much for gradients + optimizer states?", "options": ["6 GB", "26 GB", "52 GB", "78 GB"], "answer": 3, "explain": "13B × 3 × 2 bytes = 78 GB, on top of weights and activations."},
  {"q": "What does gradient checkpointing trade?", "options": ["Accuracy for speed", "Less activation memory for more training time (recomputation)", "Disk for RAM", "Precision for range"], "answer": 1, "explain": "Activations are recomputed when needed instead of stored."},
  {"q": "BF16 compared with FP16 has…", "options": ["More bits overall", "More range bits and fewer precision bits", "Fewer range bits", "Integer values only"], "answer": 1, "explain": "Same 16 bits, split differently: BF16 covers a larger range but is less precise."},
  {"q": "Why did some teams get poor quality from Llama 2 at release?", "options": ["Wrong tokenizer", "They loaded BF16 weights as FP16", "Too little RAM", "Missing system prompt"], "answer": 1, "explain": "Loading a model in a format it wasn't intended for can change its values significantly."},
  {"q": "Post-training quantization (PTQ) means…", "options": ["Training with simulated low precision", "Quantizing a model after it has been fully trained", "Training entirely in INT8", "Pruning weights"], "answer": 1, "explain": "PTQ is the most common approach and the one most relevant to application developers."},
  {"q": "Quantization-aware training (QAT) primarily…", "options": ["Reduces training time", "Improves the quality of the model when later run at low precision", "Removes the need for GPUs", "Increases model size"], "answer": 1, "explain": "QAT simulates low precision during training. It can even add training time."}
]
```

> **Source:** Huyen, *AI Engineering*, ch. 7 ("Memory Bottlenecks": backpropagation and trainable parameters, memory math, numerical representations, quantization).
