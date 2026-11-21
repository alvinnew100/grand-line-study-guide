# Memory math, numerical formats and quantization

> **Before this lesson:** read [When (and when not) to finetune](#/lesson/ai-eng/aie-when-finetune). You should know that a model's size is measured in **parameters** (its learned numbers; see [From language models to foundation models](#/lesson/ai-eng/aie-rise)) and roughly what a transformer is (see [Training data, architecture and scale](#/lesson/ai-eng/aie-data-arch-scale)). All arithmetic here is multiplication and division, done step by step; bits and bytes are explained in section 3.

## In plain words

A model is, physically, a huge list of numbers. To run it, every one of those numbers must sit in the memory of a **GPU** (graphics processing unit, the chip that runs models), and GPU memory is small and expensive: common sizes are 16, 24, 48 and 80 gigabytes. Huyen identifies **memory** as the practical bottleneck of working with foundation models, for both running them (**inference**) and finetuning them. Many finetuning techniques exist mainly to save memory.

This lesson gives you the arithmetic to answer everyday questions in seconds: Will this model fit on a 24 GB GPU? Can we finetune it on one 80 GB card? What do we gain by storing each number in 4 bits instead of 16? It also explains how numbers are stored in a computer and what **quantization**, storing numbers with fewer bits, costs in accuracy.

An everyday picture: packing for a flight with a strict luggage limit. The number of items (parameters) matters, but so does how bulky each one is (bytes per number). You can fit far more if you roll your clothes tightly (fewer bits per number), at the cost of a few creases (small rounding errors). And training is like packing for a work trip where you also need a second bag of notes about every item (gradients and optimiser state), so the same wardrobe needs much more luggage.

Why this matters for a job: these back-of-the-envelope calculations come up constantly in design discussions and interviews ("Can we run a 13B model on a 24 GB GPU?"). Getting them right saves weeks of failed experiments and wrong hardware orders.

## 1. Backpropagation and trainable parameters

A **neural network** (the kind of model behind foundation models) is trained by repeating two phases for each batch of examples:

1. **Forward pass**: feed the input through the network to compute its output.
2. **Backward pass** (**backpropagation**): compare the output with the target to get the **loss** (a number measuring how wrong the output was), work out each parameter's **gradient** (which direction, and how strongly, changing that parameter would reduce the loss), and update the parameters with an **optimiser**, an algorithm such as **SGD** (stochastic gradient descent, which steps each parameter a little against its gradient) or **Adam** (a popular variant that also keeps running averages of past gradients to adapt each step).

A **trainable parameter** is one that is allowed to change during finetuning. Parameters that are kept fixed are **frozen**. During inference only the forward pass runs. During training, the backward pass needs room for each trainable parameter's gradient and optimiser state, and it reuses **activations** (the intermediate results computed in the forward pass) that must be kept in memory until then. That is why **training needs much more memory than inference**, and why training memory grows with the number of *trainable* parameters. Cutting the number of trainable parameters is the idea behind parameter-efficient finetuning (PEFT), the topic of the next lesson.

## 2. Memory math

The formulas below are approximations. They ignore many optimisations and details of real workloads, but they get the order of magnitude right, which is what you need for planning.

### Inference

In words: the memory for the weights is the number of parameters times the bytes used to store each one. With $N$ parameters and $M$ bytes per parameter:

$$\text{weights} = N \times M$$

Running the model needs more than the weights. The forward pass stores **activations**, and transformers also store **key-value vectors** (the *KV cache*, saved intermediate results for every token so far, covered in Module 9). Both grow with the **sequence length** (how many tokens are processed) and the **batch size** (how many requests are processed together). Huyen's rule of thumb is to add **20%** of the weight memory for this overhead:

$$\text{inference memory} \approx N \times M \times 1.2$$

Worked example: a **13B** model (13 billion parameters) stored at 2 bytes per parameter needs $13 \times 10^9 \times 2 = 26 \times 10^9$ bytes, which is 26 GB for the weights, and $26 \times 1.2 = 31.2$ GB in total. A 70B model at 2 bytes needs 140 GB for its weights alone, more than any single common GPU holds. Long contexts and large batches push the real number higher than 20%.

### Training

In words: training memory is everything inference needs, plus a gradient and some optimiser state for every trainable parameter.

$$\text{training memory} = \text{weights} + \text{activations} + \text{gradients} + \text{optimiser states}$$

Each **trainable** parameter needs one value for its gradient plus zero to two values of optimiser state:

- plain **SGD**: 0 extra values;
- SGD with **momentum** (a running average of past gradients): 1 extra value;
- **Adam**: 2 extra values (running averages of the gradient and of its square).

So with Adam, every trainable parameter needs 3 extra values. Updating all 13B parameters with Adam, storing each value in 2 bytes:

$$13 \times 10^9 \times 3 \times 2\ \text{bytes} = 78\ \text{GB}$$

for gradients and optimiser state alone, on top of the 31 GB for the model. If only **1B** parameters are trainable, that part shrinks to $1 \times 10^9 \times 3 \times 2 = 6$ GB.

During training, activations can take far more memory than the weights, because the forward pass's intermediate results must be kept for computing gradients. Huyen cites Korthikanti and colleagues (2022) on NVIDIA's Megatron models. **Gradient checkpointing** (also called activation recomputation) avoids storing them all by recomputing some when they are needed: less memory, more training time.

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

**Reading this Python line by line**

- `GB = 1e9` defines a gigabyte as one billion bytes (`1e9` means $1 \times 10^9$).
- `inference_gb` is the inference formula: parameters times bytes per parameter times 1.2, converted to gigabytes.
- `training_gb` adds the training term. `{"sgd": 0, "momentum": 1, "adam": 2}[optimizer]` looks up how many optimiser values each trainable parameter needs; `(1 + extra)` adds the gradient. Note it still uses the 20% inference overhead for activations, so real training needs more.
- The loop prints three model sizes at 2 bytes (FP16), 1 byte (INT8) and half a byte (4-bit) per parameter.
- Output: a 7B model needs 16.8 GB at FP16, 8.4 GB at INT8 and 4.2 GB at 4-bit; a 13B model 31.2, 15.6 and 7.8 GB; a 70B model 168, 84 and 42 GB. Full finetuning of the 13B model with Adam needs about 109 GB (31.2 + 78), which does not fit on one 80 GB GPU. With 1B trainable parameters it drops to 37.2 GB, and with only 3.28 million trainable parameters (a LoRA setup from the next lesson) to 31.22 GB, barely more than inference.

> [!INTERVIEW]
> **"Can we run a 13B model on a 24 GB GPU?"** At FP16 the weights are 26 GB, about 31 GB with overhead, so no. At 8-bit (1 byte per parameter) it is about 15.6 GB, so yes. At 4-bit it is about 7.8 GB. Then mention that longer contexts and bigger batches increase KV-cache and activation memory, so leave headroom. For finetuning, add (1 + optimiser states) values per **trainable** parameter. Full finetuning with Adam adds three values per parameter, which is why PEFT exists.

## 3. Numerical representations

How big is each stored number? Computers store everything in **bits** (binary digits, 0 or 1); eight bits make a **byte**. A format with more bits can represent more distinct values. Neural networks traditionally use **floating-point** numbers, a scientific-notation-like format standardised as IEEE 754. A float has three parts:

- 1 **sign** bit (positive or negative);
- **exponent** bits, which set the **range**: how large or small a magnitude can be represented;
- **significand** (also called mantissa or fraction) bits, which set the **precision**: how finely nearby values can be told apart.

It is like writing $1.2345 \times 10^{3}$: the "3" is the exponent (range) and "1.2345" the significand (precision). With a fixed number of bits, giving more to one leaves fewer for the other.

| Format | Bits | Notes |
|---|---|---|
| FP64 (double precision) | 64 | NumPy and pandas default; rare in neural networks |
| FP32 (single precision) | 32 | long the standard for training |
| FP16 (half precision) | 16 | common for inference; 5 exponent bits, 10 significand bits |
| BF16 (bfloat16) | 16 | from Google, for AI on its TPU chips; 8 exponent bits, 7 significand bits: FP32's range with less precision |
| TF32 | 19 significant | from NVIDIA, used inside its GPUs |
| INT8 / INT4 | 8 / 4 | whole-number formats used for quantized models |

Converting to a format with fewer bits changes values. From Huyen's table: 1234.56789 becomes 1235.0 in FP16 (a 0.035% change) and 1232.0 in BF16 (a 0.208% change), so BF16 is less precise. But BF16 has more range: 123456.789 is too large for FP16 (whose maximum is 65,504) and becomes infinity (`INF`), while BF16 can still represent it approximately.

```python-run
import numpy as np
vals = np.array([0.0123456789, 1.23456789, 1234.56789, 123456.789], dtype=np.float64)
with np.errstate(over="ignore"):
    f16 = vals.astype(np.float16)
for v, a in zip(vals, f16):
    print(f"FP64 {v:>14.7f} -> FP16 {float(a):>14.7f}   rel. change {abs(float(a)-v)/v:.4%}" if np.isfinite(a) else f"FP64 {v:>14.7f} -> FP16 INF (out of range)")
```

**Reading this Python line by line**

- `np.array([...], dtype=np.float64)` stores four values in 64-bit floats.
- `vals.astype(np.float16)` converts them to 16-bit floats. `with np.errstate(over="ignore"):` silences the overflow warning NumPy would print for the value that is too big.
- For each pair, the **relative change** is the size of the error divided by the original value, printed as a percentage. `np.isfinite(a)` is false for infinity, which triggers the "out of range" message instead.
- Output: relative changes of about 0.011%, 0.016% and 0.035% for the first three values, and `INF (out of range)` for 123456.789.

NumPy has no BF16 type, but BF16 is exactly the top 16 bits of an FP32 number, so it can be simulated by manipulating bits:

```python-run
import numpy as np

def to_bf16(x):
    """Simulate bfloat16: keep the top 16 bits of a float32 (sign, 8 exponent bits, 7 fraction bits)."""
    bits = np.asarray(x, dtype=np.float32).view(np.uint32)
    rounding = np.uint32(0x7FFF) + ((bits >> np.uint32(16)) & np.uint32(1))   # round to nearest, ties to even
    bits = ((bits + rounding) >> np.uint32(16)) << np.uint32(16)
    return bits.view(np.float32)

vals = np.array([1234.56789, 123456.789, 0.0001234], dtype=np.float32)
with np.errstate(over="ignore"):
    fp16 = vals.astype(np.float16).astype(np.float32)
bf16 = to_bf16(vals)
for v, a, b in zip(vals, fp16, bf16):
    fa = "INF" if not np.isfinite(a) else f"{a:.6g}"
    print(f"value {v:<12.6g} FP16 -> {fa:<10} BF16 -> {b:.6g}")
print("largest FP16:", float(np.finfo(np.float16).max), "  largest BF16 is about 3.4e38 (same range as FP32)")
```

**Reading this Python line by line**

- `.view(np.uint32)` reinterprets the 32 bits of each float as an unsigned whole number, without changing the bits, so we can manipulate them.
- `>> 16` shifts the bits 16 places to the right, dropping the bottom 16; `<< 16` shifts them back, filling with zeros. Together they keep only the top 16 bits: the sign, the 8 exponent bits and 7 significand bits, which is BF16. The `rounding` term adds a little under half of the dropped part first, so values round to the nearest BF16 number instead of always rounding down.
- `.view(np.float32)` turns the bits back into a float.
- Output: 1234.57 becomes 1235 in FP16 and 1232 in BF16 (matching Huyen's table); 123457 becomes INF in FP16 but 123392 in BF16; a tiny value keeps more digits in FP16 than in BF16. The final line shows FP16's ceiling of 65,504.

> [!WARNING]
> Load a model in the format it was made for. Llama 2 was released with BF16 weights, and many teams loaded it in FP16 and got noticeably worse quality than advertised. The right format depends on your values' range, how sensitive the model is to small numerical changes, and what your hardware supports.

## 4. Quantization

Fewer bits per value means a smaller model: a 10B model takes 40 GB at 32 bits per parameter and 20 GB at 16. **Quantization** is a cheap and very effective way to cut memory. It is easy to apply and works across tasks and architectures.

> [!NOTE]
> Strictly speaking, "quantization" means converting to an **integer** format, and going from FP32 to FP16 is "reduced precision". In practice, and in the book, quantization means any conversion to a lower-precision format.

Two decisions:

- **What to quantize.** Ideally whatever uses the most memory: weights and activations. **Weight quantization** is more common because its effect on accuracy is more stable.
- **When to quantize.** During training, or after: **post-training quantization (PTQ)** quantizes a model that has already been trained. PTQ is by far the most common and the most relevant to application developers.

### Inference quantization

Serving models at 16 bits became common in the late 2010s, and lower is now routine. LLM.int8() quantizes to 8 bits and QLoRA uses 4 bits (both from Dettmers and colleagues). Models can also be served in **mixed precision**, with different parts at different bit widths: Apple (2024) used a mix of 2-bit and 4-bit formats averaging **3.5 bits per weight** for on-device models. NVIDIA's Blackwell GPUs support 4-bit floating-point inference.

At 8 bits and below, values are usually converted to **integers** (INT8, INT4), though tiny float formats (FP8, FP4) exist. The floor is 1 bit per value: BinaryConnect, XNOR-Net and BitNet. Microsoft's **BitNet b1.58** (2024) restricts every weight to one of three values, −1, 0 or 1, which takes about 1.58 bits per parameter ($\log_2 3 = 1.58$). It reported performance comparable to 16-bit Llama 2 at sizes up to 3.9B parameters, with large efficiency gains.

Reduced precision cuts memory and often **speeds up computation**: larger batches fit, and lower-precision arithmetic is faster (an addition in 16 bits takes roughly half the time of one in 32 bits). The downsides: each conversion introduces a small error, and errors can accumulate into a quality drop; and values outside the representable range can become infinity or be clipped to the nearest representable value.

**How integer quantization works (symmetric linear quantization).** In words: find the largest absolute value, divide it by the largest integer you can store (127 for 8 bits) to get a **scale**, divide every value by the scale and round to the nearest integer, clipping anything out of range. To use a value again, multiply its integer by the scale.

$$s = \frac{\max|x|}{127},\qquad q = \operatorname{clip}\!\big(\operatorname{round}(x/s),\,-127,\,127\big),\qquad \hat{x} = q\cdot s$$

Worked example: weights $[0.5, -1.0, 0.25]$. The largest absolute value is 1.0, so $s = 1.0/127 = 0.007874$. Then $0.5/s = 63.5$, which rounds to 64; $-1.0/s = -127$; $0.25/s = 31.75$, which rounds to 32. Stored integers: $[64, -127, 32]$, one byte each. Restored: $64 \times 0.007874 = 0.504$, $-1.0$ and $0.252$. Small errors, a quarter of the memory of FP32.

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

**Reading this Python line by line**

- `w` is 10,000 fake weights drawn from a bell curve centred on 0 with a spread of 0.05, typical of real weights.
- `qmax = 2 ** (bits - 1) - 1` is the largest storable integer: 127 for 8 bits, 7 for 4 bits, 1 for 2 bits (one bit is used for the sign).
- `quantize` applies the formula and immediately restores the values, so we can measure the error.
- `32 // bits` is how many times smaller than FP32 each format is (`//` is whole-number division).
- Output: 8-bit has a mean absolute error of about 0.0004, 4-bit about 0.007, 2-bit about 0.038, for 4, 8 and 16 times less memory. The last line adds one extreme value (5.0, a hundred times the typical size): the scale stretches to cover it, every other weight gets far fewer distinct levels, and the 8-bit error jumps about 25-fold to 0.0099.

That last line is why real quantizers clip extreme values, quantize **per channel** (a separate scale for each row or column of a weight matrix), or use **calibration data** (sample inputs used to choose good ranges). One outlier can ruin the resolution for everything else.

PTQ is widely supported and nearly free to apply: PyTorch, TensorFlow and Hugging Face Transformers offer it, as do on-device toolkits such as TensorFlow Lite, PyTorch Mobile and ONNX Runtime. A static example of loading a model with 4-bit weights through Hugging Face (it needs a GPU and a model download):

```python
from transformers import AutoModelForCausalLM, BitsAndBytesConfig
cfg = BitsAndBytesConfig(load_in_4bit=True)                      # quantize weights to 4 bits on load
model = AutoModelForCausalLM.from_pretrained("meta-llama/Llama-2-13b-hf", quantization_config=cfg)
```

### Training quantization

- **Quantization-aware training (QAT)** simulates low-precision behaviour, for example 8-bit, during training, so the model learns to produce good outputs at that precision. It improves the quantized model's quality. It does not shorten training and can lengthen it.
- **Training directly in lower precision** saves memory and time. Models have been trained in reduced precision for years. Character.AI (2024) trained models entirely in INT8, which removed any mismatch between training and serving precision and improved efficiency. It is harder, because backpropagation is more sensitive to low precision.
- **Mixed precision** is the practical middle ground: a higher-precision copy of the weights is kept, while operations run at lower precision where that is safe. Frameworks offer **automatic mixed precision (AMP)**, which picks a precision for each operation.

A common pattern is to train in higher precision, such as FP16 or BF16, and quantize afterwards for serving.

## Pitfalls

- Estimating memory from parameter count alone and forgetting activations, the KV cache, batch size and context length.
- Forgetting that training memory scales with *trainable* parameters times (1 + optimiser states).
- Loading weights in the wrong format (BF16 versus FP16).
- Assuming quantization is free. Evaluate quality after quantizing, especially below 8 bits.
- Confusing GB ($10^9$ bytes) with GiB ($2^{30}$ bytes, about 7% more) when you are close to a hardware limit.

## Summary

- Training runs a forward and a backward pass. The backward pass needs a gradient and optimiser state for each **trainable** parameter, plus stored activations.
- **Inference memory** ≈ $N \times M \times 1.2$. **Training memory** = weights + activations + gradients + optimiser states; Adam means three extra values per trainable parameter.
- Numerical formats trade range and precision against size: FP32, FP16, BF16, INT8, INT4. Load models in their intended format.
- **Quantization** reduces bits per value. **PTQ** is the default; 8-bit and 4-bit are common and 1.58-bit is possible. Outliers hurt; per-channel scales and calibration help. **QAT**, low-precision training and **mixed precision (AMP)** apply quantization during training.

## Glossary

- **GPU**: the processor that runs AI models; its memory limits model size.
- **Inference**: running a trained model to get outputs.
- **Neural network**: a model made of layers of parameters, trained by gradient descent.
- **Forward pass / backward pass (backpropagation)**: computing the output / computing gradients from the loss.
- **Loss**: a number measuring how wrong the output was.
- **Gradient**: the direction and strength with which a parameter should change to reduce the loss.
- **Optimiser (SGD, momentum, Adam)**: the algorithm that updates parameters from gradients.
- **Trainable / frozen parameter**: one updated during training / one kept fixed.
- **Activations**: intermediate results of the forward pass.
- **KV cache**: saved key-value vectors for tokens already processed.
- **Sequence length / batch size**: tokens per request / requests processed together.
- **Gradient checkpointing**: recomputing activations instead of storing them all.
- **Bit / byte**: a binary digit / eight bits.
- **Floating point**: a number format with sign, exponent (range) and significand (precision).
- **FP32, FP16, BF16**: 32-bit and two 16-bit float formats; BF16 keeps FP32's range with less precision.
- **INT8 / INT4**: 8-bit and 4-bit integer formats.
- **Quantization**: storing values with fewer bits.
- **Scale**: the factor that maps real values to integers and back.
- **Post-training quantization (PTQ)**: quantizing an already trained model.
- **Outlier**: a value far larger than the rest.
- **Per-channel quantization / calibration data**: a separate scale per row or column / sample inputs used to choose ranges.
- **Quantization-aware training (QAT)**: simulating low precision during training.
- **Mixed precision / AMP**: using different precisions for different operations / doing so automatically.

```quiz
[
  {"q": "Approximate inference memory for a 13B-parameter model at 2 bytes/param with Huyen's 20% overhead?", "options": ["13 GB", "26 GB", "31.2 GB", "78 GB"], "answer": 2, "explain": "13B × 2 bytes = 26 GB; × 1.2 = 31.2 GB."},
  {"q": "With Adam, how many values per trainable parameter are needed for gradients and optimiser states?", "options": ["1", "2", "3", "4"], "answer": 2, "explain": "One gradient plus two Adam states (running averages of the gradient and its square)."},
  {"q": "Full finetuning of a 13B model with Adam at 2 bytes/value needs how much for gradients + optimiser states?", "options": ["6 GB", "26 GB", "52 GB", "78 GB"], "answer": 3, "explain": "13B × 3 × 2 bytes = 78 GB, on top of weights and activations."},
  {"q": "What does gradient checkpointing trade?", "options": ["Accuracy for speed", "Less activation memory for more training time (recomputation)", "Disk for RAM", "Precision for range"], "answer": 1, "explain": "Activations are recomputed when needed instead of stored."},
  {"q": "BF16 compared with FP16 has…", "options": ["More bits overall", "More range (exponent) bits and fewer precision bits", "Fewer range bits", "Integer values only"], "answer": 1, "explain": "Same 16 bits, split differently: BF16 covers a larger range but is less precise."},
  {"q": "Why did some teams get poor quality from Llama 2 at release?", "options": ["Wrong tokenizer", "They loaded BF16 weights as FP16", "Too little RAM", "Missing system prompt"], "answer": 1, "explain": "Loading a model in a format it wasn't intended for can change its values significantly."},
  {"q": "Post-training quantization (PTQ) means…", "options": ["Training with simulated low precision", "Quantizing a model after it has been fully trained", "Training entirely in INT8", "Pruning weights"], "answer": 1, "explain": "PTQ is the most common approach and the one most relevant to application developers."},
  {"q": "Quantization-aware training (QAT) primarily…", "options": ["Reduces training time", "Improves the quality of the model when later run at low precision", "Removes the need for GPUs", "Increases model size"], "answer": 1, "explain": "QAT simulates low precision during training. It can even add training time."}
]
```

> **Source:** Huyen, *AI Engineering*, ch. 7 ("Memory Bottlenecks": backpropagation and trainable parameters, memory math, numerical representations, quantization).
