# Deep learning interview essentials

> **Before this lesson:** this is a review of the whole track. It assumes you have worked through the earlier modules; every answer links back to the lesson that explains it from scratch. For classic ML questions (bias-variance, cross-validation, trees) see the ML track's [ML interview essentials](#/lesson/ml/interview-essentials); for transformers and LLMs see [LLM Practice](#/lesson/llm-practice/attention-from-scratch).

## In plain words

Deep-learning interviews at large technology companies and AI teams in Singapore tend to probe four things: whether you understand the **mechanics** (what happens in a training step, why each line is there), whether you can **reason quantitatively** (shapes, parameter counts, memory, compute), whether you can **diagnose** problems (a loss that will not fall, overfitting, NaNs, a slow job), and whether you can make sound **engineering trade-offs** (which optimiser, which loss, how to deploy). This lesson collects the questions that come up most, with short model answers, and a small calculator for the numbers interviewers like to ask about.

Think of it as the summary sheet a pilot reviews before a check ride: nothing new, but everything in one place, phrased the way you would say it out loud.

How to answer well:

1. **State the core idea in one sentence**, then add mechanism, then trade-offs. ("AdamW decouples weight decay from the adaptive update. Because Adam divides by the root of the second moment, an L2 term in the gradient gets rescaled unevenly; AdamW applies decay directly to the weights.")
2. **Use numbers** when you can: shapes, parameter counts, bytes per parameter, typical learning rates.
3. **Name the failure mode and the fix** for every technique: it shows you have used it.
4. **Say what you would measure** before changing anything.

## 1. Fundamentals

**Why do we need non-linear activations?** Without them, any stack of linear layers equals a single linear layer, so depth adds nothing. Non-linearities (ReLU, GELU) let networks represent complex functions. ([Neurons and activations](#/lesson/deep-learning/neurons-activations))

**What is backpropagation?** Reverse-mode automatic differentiation: after the forward pass records the computational graph, the chain rule is applied from the loss backwards, multiplying local derivatives, to get the gradient for every parameter at roughly the cost of one extra forward pass. ([Autograd](#/lesson/deep-learning/autograd))

**Vanishing and exploding gradients: causes and fixes?** The gradient at an early layer is a product of per-layer factors; factors below 1 shrink it exponentially, above 1 blow it up. Fixes: ReLU-family activations, He/Xavier initialisation, normalisation layers, residual connections, gradient clipping, and for recurrent nets LSTM/GRU gating. ([Going deeper](#/lesson/deep-learning/depth-residuals))

**Why do residual connections work?** Blocks learn corrections around the identity, so extra depth can default to "do nothing", and the gradient flows directly through the additions ($\partial(x + F(x))/\partial x = I + \partial F/\partial x$).

**Why convolutions for images?** Locality and weight sharing: far fewer parameters than fully connected layers, translation equivariance, and features that compose hierarchically. ([Convolutions](#/lesson/deep-learning/convolutions))

**Why initialise randomly, and at what scale?** Equal weights keep units identical (symmetry); the scale must keep activation variance stable across layers: Kaiming variance 2/fan-in for ReLU, Xavier 2/(fan-in + fan-out) for tanh. ([Initialisation](#/lesson/deep-learning/normalisation-init))

## 2. PyTorch mechanics

**Walk through a training step.** `optimizer.zero_grad()`, forward `out = model(x)`, `loss = loss_fn(out, y)`, `loss.backward()`, optional `clip_grad_norm_`, `optimizer.step()`, `scheduler.step()`. Validation in `model.eval()` under `torch.no_grad()`.

**Why `zero_grad()`?** `.grad` accumulates across backward calls (useful for gradient accumulation); without clearing, each step uses the sum of all previous gradients.

**`model.eval()` versus `torch.no_grad()`?** `eval()` changes layer behaviour (dropout off, batch norm uses running statistics); `no_grad()` (or `inference_mode()`) stops recording the graph. You usually need both for evaluation.

**`detach()` versus `.item()` versus `.data`?** `detach()` returns a tensor sharing storage but cut from the graph; `.item()` returns a Python number from a one-element tensor (and synchronises with the GPU); `.data` is a legacy, unsafe way to bypass autograd. Log with `.item()`.

**`view` versus `reshape`; what is contiguity?** `view` never copies and needs a compatible stride layout; `reshape` copies when needed. `transpose`/`permute` only swap strides, so the result is non-contiguous. ([Storage and strides](#/lesson/deep-learning/tensor-storage))

**What is in a `state_dict`, and how do you checkpoint?** Named parameter and buffer tensors. Save model, optimiser, scheduler and scaler state dicts plus the epoch; load with `map_location` and `weights_only=True`. Watch for `module.` (DDP) and `_orig_mod.` (compile) prefixes. ([nn.Module](#/lesson/deep-learning/nn-module))

**Why must layers be registered, and how?** Assign `nn.Module`s and `nn.Parameter`s as attributes (or use `nn.ModuleList`/`ModuleDict`); plain Python lists are invisible to `parameters()`, `.to()` and the state_dict.

**DataLoader speed knobs?** `num_workers`, `pin_memory` with `non_blocking=True`, `persistent_workers`, `prefetch_factor`, a custom `collate_fn` for variable-length data, a `sampler` for balancing or sharding. ([DataLoader](#/lesson/deep-learning/datasets-dataloaders))

## 3. Optimisation

**SGD versus Adam versus AdamW?** SGD with momentum: cheap, strong with a schedule, especially for convnets. Adam: per-parameter adaptive steps, robust defaults. AdamW: Adam with decoupled weight decay, the modern default for transformers and fine-tuning. ([Optimisers](#/lesson/deep-learning/optimizers-validation))

**What does momentum do?** Accumulates a velocity so consistent gradient directions speed up and oscillating ones cancel; helps in narrow valleys.

**Why learning-rate schedules and warmup?** Decay shrinks the noise cloud around the minimum; warmup protects the unstable start (large initial gradients, unreliable Adam statistics, large batches). Default: linear warmup then cosine decay. ([Schedules](#/lesson/deep-learning/schedules-clipping))

**Batch size effects?** Larger batches give less noisy gradients and better hardware use, but need larger learning rates (linear scaling heuristic, with warmup) and can generalise slightly worse; beyond a critical batch size the benefit per step fades. Gradient accumulation simulates large batches.

**What is gradient clipping for?** Capping the global gradient norm so a single bad batch cannot produce a destructive update; standard at max norm 1.0 for transformers. Log the pre-clip norm.

## 4. Generalisation and regularisation

**How do you detect and reduce overfitting?** Training metric improving while validation worsens. Data augmentation, weight decay, dropout, early stopping, more data or pretrained models, smaller capacity. ([Regularisation](#/lesson/deep-learning/regularisation), [Augmentation](#/lesson/deep-learning/augmentation))

**How does dropout work at training and test time?** Training: zero units with probability p and scale survivors by 1/(1−p) (inverted dropout). Test: identity.

**How does batch norm work, and its pitfalls?** Normalise each channel with batch statistics during training while tracking running averages; use the running averages at inference. Pitfalls: forgetting `eval()`, tiny batches, fine-tuning with small batches; alternatives LayerNorm, GroupNorm, RMSNorm.

**Why LayerNorm in transformers?** Per-example statistics, independent of batch size and sequence length, identical in training and inference.

**Transfer learning strategy with little data?** Pretrained backbone, new head, train the head with the backbone frozen, then fine-tune with smaller, discriminative learning rates; strong augmentation; early stopping. ([Fine-tuning](#/lesson/deep-learning/end-to-end-finetuning))

## 5. Losses and metrics

**Why cross-entropy rather than MSE for classification?** It is the negative log-likelihood of a categorical model; its gradient with respect to logits is probabilities minus one-hot, large when confidently wrong. MSE on probabilities gives vanishing gradients when saturated. ([Image classifier](#/lesson/deep-learning/image-classifier))

**Why do PyTorch losses take logits?** Combining log-softmax (or sigmoid) with the loss in one function uses the stable log-sum-exp form; separate softmax then log can underflow to log(0).

**Handling class imbalance?** Measure with precision, recall, F1, PR-AUC; train with balanced sampling, class weights (`weight`, `pos_weight`), or focal loss; tune the threshold on validation; recalibrate if probabilities matter. ([Imbalance](#/lesson/deep-learning/imbalance-metrics))

**ROC AUC versus PR AUC?** ROC AUC is the probability that a random positive outranks a random negative, insensitive to class balance; PR AUC focuses on the positive class and is more informative when positives are rare.

**Segmentation metrics and losses?** IoU and Dice (Dice = 2·IoU/(1+IoU)); soft Dice loss for small structures, often combined with cross-entropy. ([Segmentation](#/lesson/deep-learning/segmentation))

## 6. Performance and scale

**Memory for training a model with Adam?** About 16 bytes per parameter in float32 (weights, gradients, two moments) plus activations, which scale with batch × size × depth. ([Memory](#/lesson/deep-learning/memory-mixed-precision))

**float16 versus bfloat16?** Same 16 bits; float16 has a 5-bit exponent (narrow range, needs loss scaling), bfloat16 an 8-bit exponent (float32's range, no scaler needed, less precision).

**What does `torch.compile` do?** Captures graphs from Python with TorchDynamo and generates fused kernels with TorchInductor, reducing launch overhead and memory traffic; first call compiles; graph breaks and recompilations limit gains. ([torch.compile](#/lesson/deep-learning/compile-throughput))

**How does DDP work?** One process per GPU with a full model copy and a data shard; gradients are all-reduced in buckets during backward so all copies take identical steps; launch with `torchrun`; use `DistributedSampler.set_epoch`.

**Out of memory: what do you try?** Smaller micro-batch plus gradient accumulation, bf16 autocast, activation checkpointing, no-grad evaluation, 8-bit optimiser states, FSDP sharding, LoRA for large models.

## 7. Deployment

**How do you export a PyTorch model today?** `torch.export` to an ExportedProgram, then AOTInductor for servers, ExecuTorch for devices, or ONNX (`torch.onnx.export(..., dynamo=True)`) for other runtimes. TorchScript is deprecated. Verify outputs against the original. ([Serving and export](#/lesson/deep-learning/serving-export))

**Latency versus throughput?** Dynamic batching raises throughput at some latency cost; tune maximum batch size and wait time against p99 targets.

**How do you make a model smaller?** Quantisation (int8 or 4-bit weights), pruning, distillation, efficient architectures, lower-precision inference.

## 8. Debugging

**Loss not decreasing?** Inspect inputs, check the initial loss ≈ ln C, confirm gradients reach every parameter, overfit one batch; if that fails, suspect the loss inputs, label alignment or optimiser setup. **Loss becomes NaN?** Learning rate, unstable log/exp/sqrt/division, float16 overflow, bad data; use stable functions, epsilons, clipping and anomaly detection. ([Debugging](#/lesson/deep-learning/debugging-training))

## 9. Numbers worth knowing, and a calculator

| quantity | value |
|---|---|
| initial cross-entropy with C classes | ln C (2.30 for 10, 6.91 for 1000) |
| ImageNet normalisation mean / std | [0.485, 0.456, 0.406] / [0.229, 0.224, 0.225] |
| Adam defaults | lr 1e-3, betas (0.9, 0.999), eps 1e-8; AdamW weight decay default 0.01 |
| BatchNorm defaults | momentum 0.1, eps 1e-5 |
| GradScaler defaults | init scale 65,536, growth 2, backoff 0.5, interval 2,000 |
| float16 max | 65,504 |
| training memory, Adam fp32 | ~16 bytes/parameter + activations |
| inference memory, bf16 weights | 2 bytes/parameter |
| Linear(n, m) params | nm + m |
| Conv2d(c_in, c_out, k) params | c_in·c_out·k² + c_out |

```python-run
import math

def conv_out(size, k, s=1, p=0, d=1):
    return (size + 2 * p - d * (k - 1) - 1) // s + 1

def conv_params(c_in, c_out, k, bias=True):
    return c_in * c_out * k * k + (c_out if bias else 0)

def conv_macs(c_in, c_out, k, h_out, w_out):
    return c_in * c_out * k * k * h_out * w_out          # multiply-accumulates per image

print("initial CE for 10 / 1000 classes:", round(math.log(10), 3), round(math.log(1000), 3))

h = conv_out(224, k=7, s=2, p=3)
print(f"Conv2d(3, 64, 7, stride 2, pad 3) on 224x224 -> {h}x{h}, params {conv_params(3, 64, 7):,}, "
      f"MACs {conv_macs(3, 64, 7, h, h) / 1e6:.0f}M per image")
print(f"Linear(4096, 4096): {4096 * 4096 + 4096:,} params")
print(f"Embedding(50000, 768): {50000 * 768:,} params")

for name, n in [("ResNet-50", 25.6e6), ("ViT-B/16", 86e6), ("7B LLM", 7e9), ("70B LLM", 70e9)]:
    print(f"{name:9s} Adam fp32 training ~{n * 16 / 1e9:7.1f} GB (+activations); bf16 weights {n * 2 / 1e9:7.2f} GB; "
          f"int4 weights {n * 0.5 / 1e9:6.2f} GB")
```

The calculator reproduces the most common back-of-the-envelope answers: initial losses, a ResNet stem's output size, parameters and multiply-accumulate operations (MACs; one multiply plus one add, often counted as two floating-point operations), and memory for well-known model sizes in different precisions.

> [!INTERVIEW]
> **"Tell me about a deep learning model you trained that did not work at first."** Structure it: the goal and metric, the data, the first result and how you discovered it was wrong (a per-class metric, a curve, a visual check), the hypotheses you tested in order, the fix, and the measured improvement. The CT project in this track is a model story: 99.7% accuracy that found no nodules, fixed by per-class metrics, balanced sampling and augmentation, then a segmentation stage tuned for recall.

## Summary

- Answer in layers: one-sentence idea, mechanism, trade-offs, numbers, failure mode and fix.
- Mechanics: the training step, `zero_grad`, `eval` versus `no_grad`, `detach`/`item`, view/reshape, state dicts and checkpoints, module registration.
- Optimisation: SGD/momentum/Adam/AdamW, schedules with warmup, batch size scaling, gradient clipping.
- Generalisation: augmentation, weight decay, dropout, normalisation, early stopping, transfer learning.
- Losses and metrics: cross-entropy from logits, imbalance handling, ROC versus PR AUC, Dice and IoU.
- Scale and deployment: memory budgets, bf16, `torch.compile`, DDP, `torch.export`, quantisation, batching; debugging checklists.

## Glossary

- **MAC (multiply-accumulate)**: one multiplication followed by one addition, the basic unit of layer compute.
- **FLOPs**: floating-point operations; often about two per MAC.
- **Back-of-the-envelope estimate**: a quick approximate calculation used to sanity-check feasibility.
- **Model answer**: a concise, structured response covering idea, mechanism and trade-offs.
- **Critical batch size**: the batch size beyond which larger batches give diminishing returns per step.
- **Training-serving skew**: mismatch between training and production preprocessing or data.
- **Calibration**: agreement between predicted probabilities and observed frequencies.
- **Failure mode**: the characteristic way a technique goes wrong.

## Check yourself

```quiz
[
  {"q": "Which pair do you typically need for correct evaluation in PyTorch?", "options": ["model.eval() and torch.no_grad() (or inference_mode)", "model.train() and torch.no_grad()", "model.eval() only", "torch.no_grad() only"], "answer": 0,
   "explain": "eval() changes layer behaviour; no_grad() stops graph recording."},
  {"q": "A 1000-class classifier starts training with loss 6.9. What does that suggest?", "options": ["Near-uniform predictions, as expected at initialisation", "A bug in the loss", "The model has converged", "Labels are one-hot encoded"], "answer": 0,
   "explain": "ln(1000) ≈ 6.91."},
  {"q": "Why does AdamW usually beat Adam with L2 regularisation?", "options": ["Decay is applied directly to weights rather than being rescaled by the adaptive denominator", "It uses a larger learning rate", "It has no second moment", "It clips gradients automatically"], "answer": 0,
   "explain": "Coupled L2 in Adam decays parameters unevenly."},
  {"q": "Roughly how much memory do float32 weights, gradients and Adam states of a 1-billion-parameter model need?", "options": ["16 GB", "4 GB", "1 GB", "64 GB"], "answer": 0,
   "explain": "About 16 bytes per parameter, before activations."},
  {"q": "Which metric best summarises a detector for very rare positives?", "options": ["Precision-recall AUC (average precision)", "Accuracy", "Mean squared error", "Top-5 accuracy"], "answer": 0,
   "explain": "It focuses on how well positives are ranked and found."},
  {"q": "What is the modern recommended path to export a PyTorch model for a C++ server?", "options": ["torch.export then AOTInductor", "torch.jit.trace", "pickle the model object", "Save only the optimizer"], "answer": 0,
   "explain": "TorchScript is deprecated; torch.export underpins current deployment paths."},
  {"q": "How many parameters does Conv2d(64, 128, kernel_size=3) have?", "options": ["73,856", "73,728", "1,152", "8,192"], "answer": 0,
   "explain": "64 × 128 × 9 = 73,728 weights plus 128 biases."},
  {"q": "Your first debugging experiment when a loss will not decrease?", "options": ["Overfit a single small batch with augmentation and dropout off", "Add more layers", "Double the dataset", "Switch frameworks"], "answer": 0,
   "explain": "If the setup cannot memorise one batch, there is a bug in the loss, labels, update or model."}
]
```

> **Source:** Stevens, Antiga & Viehmann, *Deep Learning with PyTorch*, ch. 1–15 (review); PyTorch documentation (docs.pytorch.org) for current defaults (Adam, AdamW, BatchNorm, GradScaler) and APIs (`torch.compile`, `torch.export`, `torch.amp`).
