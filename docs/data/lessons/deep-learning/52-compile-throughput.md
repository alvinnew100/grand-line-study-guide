# torch.compile, input pipelines and multi-GPU basics

> **Before this lesson:** you need the DataLoader options from [Dataset, transforms and DataLoader](#/lesson/deep-learning/datasets-dataloaders), asynchronous GPU execution from [storage, strides, views and devices](#/lesson/deep-learning/tensor-storage), mixed precision from [GPU memory and mixed precision](#/lesson/deep-learning/memory-mixed-precision), and gradient accumulation from [Autograd in depth](#/lesson/deep-learning/autograd).

## In plain words

Once a model trains correctly, the next question is how fast. Speed decides how many experiments you can run per day and how much the training bill is. A training step is slow for one of four reasons: the GPU is **waiting for data**, Python is **launching too many tiny operations**, the GPU is **moving memory** more than computing, or the GPU is genuinely **busy with arithmetic** (the good case). Each has its own fix.

This lesson covers the main tools: **torch.compile**, which turns your Python model into optimised fused GPU code with one line; the **profiler**, which tells you where time goes; input-pipeline and memory-layout settings; and **DistributedDataParallel**, which spreads training over several GPUs.

Think of a restaurant kitchen that is slow at dinner time. Maybe the ingredients arrive late (data loading), the head chef shouts one tiny instruction at a time (Python overhead), cooks keep walking to the pantry for each item (memory traffic), or the stoves really are full (compute). Hiring more cooks (more GPUs) helps only in the last case; otherwise you reorganise the kitchen first.

Why it matters for a job: ML engineers are expected to make training efficient, and "how would you speed up this training job?" is a standard interview question. Knowing what `torch.compile` does (and when it does not help), how to profile, and how data-parallel training synchronises gradients separates practitioners from tutorial-followers.

## 1. Where does the time go?

| bottleneck | symptom | typical fixes |
|---|---|---|
| input pipeline | GPU utilisation low and spiky; iterating the DataLoader alone is as slow as training | more workers, pinned memory, faster decoding, caching, GPU augmentation |
| Python / launch overhead | many small operations; GPU idle between tiny kernels; small batches or small models | larger batches, `torch.compile`, CUDA graphs (`mode="reduce-overhead"`) |
| memory bandwidth | element-wise operations (activations, normalisation, adds) dominate the profile | kernel fusion via `torch.compile`, mixed precision, channels_last |
| compute | big matrix multiplications and convolutions dominate | mixed precision and Tensor Cores, TF32, better algorithms; then more GPUs |

Every GPU operation is a **kernel**: a small program launched by the CPU. Launching costs a few microseconds. A large matrix multiplication runs long enough that launch cost is negligible, but an element-wise operation on a small tensor may run for less time than it took to launch. Element-wise operations are also **memory-bound**: they read and write every element once and do almost no arithmetic per byte, so their speed is limited by memory bandwidth rather than by the GPU's arithmetic power.

```python-run
import time
import numpy as np

rng = np.random.default_rng(0)
tiny = [rng.random(16) for _ in range(20_000)]
stacked = np.stack(tiny)                                   # the same data as one (20000, 16) array

t0 = time.perf_counter()
out_loop = [np.maximum(t * 2.0 + 1.0, 0.0) for t in tiny]  # 20,000 separate small "launches"
t_loop = time.perf_counter() - t0
t0 = time.perf_counter()
out_batched = np.maximum(stacked * 2.0 + 1.0, 0.0)          # one large operation
t_batch = time.perf_counter() - t0
print(f"20,000 small ops: {t_loop * 1e3:7.1f} ms   one batched op: {t_batch * 1e3:6.2f} ms   "
      f"same result: {np.allclose(np.stack(out_loop), out_batched)}")

n = 50_000_000
unfused = 3 * 2 * n * 4                                     # three separate passes, each reads and writes the array
fused = 2 * n * 4                                           # one pass: read once, write once
print(f"memory traffic for y = relu(x * 2 + 1) on {n:,} float32 values:")
print(f"   three separate kernels: {unfused / 1e9:.1f} GB    one fused kernel: {fused / 1e9:.1f} GB")
```

The first measurement is an analogy for launch overhead: the same arithmetic done as 20,000 tiny operations is far slower than one batched operation, because per-call overhead dominates. The second is a back-of-the-envelope calculation: computing `relu(x * 2 + 1)` as three separate kernels reads and writes the whole array three times; a single **fused** kernel does it once, moving a third of the bytes. Fusing chains of element-wise operations is the main thing `torch.compile` does for you.

## 2. torch.compile

Introduced in PyTorch 2.0, `torch.compile` speeds up existing models without rewriting them:

```python
model = MyModel().cuda()
compiled = torch.compile(model)                # or decorate a function: @torch.compile
for x, y in loader:
    loss = loss_fn(compiled(x), y)             # the first call compiles (slow); later calls are fast
    loss.backward()
    optimizer.step(); optimizer.zero_grad()
```

What happens underneath:

1. **TorchDynamo** watches Python execute your `forward` (at the bytecode level) and captures the sequence of tensor operations into a **graph**. Python code that is not tensor maths (logging, data-dependent `if` statements, calls to `.item()`, unsupported libraries) causes a **graph break**: the graph ends, that code runs normally in Python, and a new graph starts afterwards.
2. **AOTAutograd** traces the backward pass ahead of time so training is compiled too.
3. **TorchInductor**, the default backend, generates optimised kernels (Triton code on GPUs, C++ on CPUs), **fusing** chains of operations so intermediate results stay in fast on-chip memory.
4. The compiled code is cached and reused while input properties (shapes, dtypes, devices) match; a mismatch triggers a **recompilation**. After a shape changes, PyTorch by default tries to compile a version that accepts varying sizes ("dynamic shapes").

Modes:

- `mode="default"`: a good balance of compile time and speed.
- `mode="reduce-overhead"`: also uses **CUDA graphs**, which record a sequence of kernel launches once and replay them with a single launch, removing Python and launch overhead; best for small batches and inference. Needs stable shapes and uses some extra memory.
- `mode="max-autotune"`: benchmarks alternative kernel implementations to pick the fastest; much longer compile time.
- `fullgraph=True`: raise an error at any graph break, useful when you need one complete graph (for example before exporting).

Practical notes:

- Expect the first iterations to be slow while compiling (seconds to minutes); benchmark after warmup.
- Typical training speedups range from modest to large depending on how much time was overhead or memory-bound; compute-bound large matrix multiplications gain the least.
- Find graph breaks and recompilations with the environment variable `TORCH_LOGS="graph_breaks,recompiles"` or `torch._dynamo.explain(model)(x)`.
- The compiled module wraps the original; its state_dict keys gain an `_orig_mod.` prefix, so save `model.state_dict()` from the original module.
- Variable-length inputs (text) can trigger many recompilations; pad to a few fixed bucket lengths, or mark dimensions as dynamic.

## 3. Profiling

Measure before optimising. Because GPU work is asynchronous, naive wall-clock timing measures queuing, not execution; synchronise first.

```python
import time
torch.cuda.synchronize(); t0 = time.perf_counter()
for _ in range(20):
    step()
torch.cuda.synchronize(); print("ms per step:", (time.perf_counter() - t0) / 20 * 1e3)

from torch.profiler import profile, ProfilerActivity, record_function
with profile(activities=[ProfilerActivity.CPU, ProfilerActivity.CUDA], record_shapes=True) as prof:
    with record_function("train_step"):          # a named region that appears in the results
        step()
print(prof.key_averages().table(sort_by="cuda_time_total", row_limit=15))
prof.export_chrome_trace("trace.json")           # timeline viewable in a trace viewer such as Perfetto
```

The table lists operations by total GPU time; the trace shows gaps where the GPU sits idle (waiting for data or for Python). `torch.utils.benchmark.Timer` handles warmup and synchronisation for micro-benchmarks.

## 4. Settings that often help

- **DataLoader**: `num_workers` > 0, `pin_memory=True` with `non_blocking=True` transfers, `persistent_workers=True`, enough `prefetch_factor` ([data lesson](#/lesson/deep-learning/datasets-dataloaders)).
- **Mixed precision** with `torch.autocast` (bfloat16 where supported), and `torch.set_float32_matmul_precision("high")` to allow TF32 for remaining float32 matmuls.
- **channels_last** memory format for convnets: `model = model.to(memory_format=torch.channels_last)` and the same for inputs. It stores images as N × H × W × C in memory (the logical shape stays N × C × H × W), which Tensor Core convolution kernels prefer.
- **cuDNN autotuning**: `torch.backends.cudnn.benchmark = True` makes cuDNN (NVIDIA's deep-learning kernel library) try several convolution algorithms on the first batch and keep the fastest; helpful when input sizes are fixed, harmful when they change every batch.
- **Avoid synchronisation in the loop**: `.item()`, `print(tensor)`, `.cpu()` and Python `if` on tensor values force the CPU to wait for the GPU. Accumulate metrics on the GPU and read them occasionally.
- **zero_grad(set_to_none=True)** (the default) avoids writing zeros.
- **Bigger batches** improve GPU utilisation, within memory limits and with learning-rate adjustments ([schedules lesson](#/lesson/deep-learning/schedules-clipping)).

## 5. Training on several GPUs: DistributedDataParallel

**Data parallelism** gives each GPU a full copy of the model and a different slice of each batch. After each backward pass, the gradients are averaged across GPUs so every copy takes the identical optimiser step and the copies stay in sync.

PyTorch's **DistributedDataParallel (DDP)** runs one process per GPU:

```python
# launched with:  torchrun --nproc_per_node=4 train.py
import os, torch, torch.distributed as dist
from torch.nn.parallel import DistributedDataParallel as DDP
from torch.utils.data.distributed import DistributedSampler

dist.init_process_group(backend="nccl")              # NCCL: NVIDIA's fast GPU communication library
local_rank = int(os.environ["LOCAL_RANK"])           # set by torchrun: which GPU this process owns
torch.cuda.set_device(local_rank)

model = DDP(MyModel().cuda(local_rank), device_ids=[local_rank])
sampler = DistributedSampler(train_set, shuffle=True) # each process sees a different shard
loader = DataLoader(train_set, batch_size=64, sampler=sampler, num_workers=8, pin_memory=True)

for epoch in range(epochs):
    sampler.set_epoch(epoch)                          # different shuffle every epoch
    for x, y in loader:
        loss = loss_fn(model(x.cuda()), y.cuda())
        optimizer.zero_grad(); loss.backward()        # gradients are all-reduced during backward
        optimizer.step()
    if dist.get_rank() == 0:                          # only one process writes checkpoints and logs
        torch.save(model.module.state_dict(), "ckpt.pt")
dist.destroy_process_group()
```

- **All-reduce** is the collective operation that sums (then averages) a tensor across all processes so each ends with the same result. DDP groups gradients into **buckets** and all-reduces each bucket as soon as its gradients are ready, overlapping communication with the rest of the backward pass.
- The **effective batch size** is the per-GPU batch times the number of GPUs (the **world size**); adjust the learning rate accordingly.
- `DistributedSampler` shards the data; forgetting `set_epoch` gives the same order every epoch.
- `nn.DataParallel` (single process, multiple threads) is older and slower; prefer DDP even on one machine.
- When the model itself does not fit on one GPU, **FSDP** (Fully Sharded Data Parallel) shards parameters, gradients and optimiser state across GPUs, gathering each layer's parameters only while it computes. Beyond that lie tensor and pipeline parallelism for the largest models.

The demo checks the central claim of data parallelism: averaging the gradients computed on equal shards gives exactly the full-batch gradient (for a mean loss), so four GPUs each processing 64 examples behave like one GPU processing 256.

```python-run
import numpy as np

rng = np.random.default_rng(0)
X = rng.normal(size=(256, 5)); y = rng.normal(size=256)
w = rng.normal(size=5)

def grad_mse(Xb, yb, w):                                # gradient of mean((Xb @ w - yb)^2)
    return 2 * Xb.T @ (Xb @ w - yb) / len(yb)

full = grad_mse(X, y, w)                                # one GPU, batch 256
shards = np.split(np.arange(256), 4)                    # 4 GPUs, 64 examples each
local = [grad_mse(X[s], y[s], w) for s in shards]       # each process computes its own gradient
all_reduced = sum(local) / len(local)                   # all-reduce (sum) then divide by world size
print("full-batch gradient:  ", full.round(5))
print("DDP averaged gradient:", all_reduced.round(5))
print("identical:", np.allclose(full, all_reduced))

uneven = [np.arange(0, 100), np.arange(100, 256)]       # unequal shards break the equivalence
avg_uneven = sum(grad_mse(X[s], y[s], w) for s in uneven) / 2
print("unequal shards still match?", np.allclose(full, avg_uneven))
```

With equal shards the averaged gradient matches the full-batch gradient exactly. With unequal shards it does not, because a simple average gives each shard equal weight regardless of its size, which is one reason `DistributedSampler` pads or drops samples so every process gets the same number.

> [!INTERVIEW]
> **"Training is slower than expected. Walk me through speeding it up."** Measure first: time the DataLoader alone, then profile a few steps with `torch.profiler` (synchronising for timings). If data-bound: workers, pinned memory, caching, GPU augmentation. If overhead-bound (small kernels, idle gaps): larger batches, `torch.compile` (fusion) and CUDA graphs via `mode="reduce-overhead"`, remove `.item()` calls in the loop. If compute-bound: bf16 autocast, TF32, channels_last for convnets. Only then scale out with DDP and `torchrun`, scaling the learning rate with the effective batch size, and FSDP if the model does not fit.

## Summary

- Step time is limited by data loading, launch overhead, memory bandwidth or compute; diagnose before optimising.
- `torch.compile` captures graphs with TorchDynamo (breaking at unsupported Python), traces backward with AOTAutograd, and generates fused kernels with TorchInductor; modes trade compile time for speed; recompiles on new shapes.
- Profile with synchronised timings and `torch.profiler`; avoid synchronising calls in the loop.
- Helpful settings: DataLoader workers and pinning, bf16 autocast, TF32, channels_last, `cudnn.benchmark` for fixed sizes.
- DDP runs one process per GPU, all-reduces gradients in buckets during backward, and needs `DistributedSampler` with `set_epoch`; FSDP shards models that do not fit.

## Glossary

- **Throughput**: samples processed per second.
- **Kernel / kernel launch**: a program run on the GPU / the CPU-side cost of starting it.
- **Memory-bound / compute-bound**: limited by data movement / by arithmetic.
- **Kernel fusion**: combining several operations into one kernel to avoid extra memory traffic.
- **torch.compile**: PyTorch 2's just-in-time compiler for models and functions.
- **TorchDynamo / AOTAutograd / TorchInductor**: graph capture / ahead-of-time backward tracing / kernel generation.
- **Graph break**: a point where graph capture stops and Python runs normally.
- **Recompilation / dynamic shapes**: compiling again for new input properties / compiled code that accepts varying sizes.
- **CUDA graphs**: recording and replaying a sequence of kernel launches as one.
- **Profiler / trace**: a tool measuring time per operation / a timeline of execution.
- **channels_last**: storing image tensors with channels as the fastest-varying axis in memory.
- **Data parallelism / DDP**: replicating the model and splitting batches across GPUs / PyTorch's multi-process implementation.
- **All-reduce**: summing a tensor across processes so all receive the result.
- **World size / rank**: number of processes / the index of one process.
- **FSDP**: sharding parameters, gradients and optimiser state across GPUs.

## Check yourself

```quiz
[
  {"q": "What is the main source of speedup from torch.compile for element-wise-heavy models?", "options": ["Fusing many small operations into fewer kernels, reducing memory traffic and launches", "Using a different optimizer", "Reducing the number of parameters", "Skipping the backward pass"], "answer": 0,
   "explain": "Fused kernels keep intermediates in fast memory and launch less often."},
  {"q": "What causes a graph break in torch.compile?", "options": ["Python code it cannot capture, such as .item() or data-dependent control flow", "Using nn.Linear", "Calling the model twice", "Using float32"], "answer": 0,
   "explain": "Execution falls back to Python at that point, then a new graph begins."},
  {"q": "Why must you call torch.cuda.synchronize() before reading the clock when timing GPU code?", "options": ["GPU operations are asynchronous; without it you time only the queuing", "It clears the cache", "It compiles the model", "It moves tensors to the CPU"], "answer": 0,
   "explain": "Synchronising waits for queued kernels to finish."},
  {"q": "Which torch.compile mode uses CUDA graphs to cut launch overhead?", "options": ["reduce-overhead", "default", "max-autotune only", "fullgraph"], "answer": 0,
   "explain": "CUDA graphs replay a recorded kernel sequence with one launch."},
  {"q": "In DDP with 8 GPUs and a per-GPU batch of 32, what is the effective batch size?", "options": ["256", "32", "4", "8"], "answer": 0,
   "explain": "Gradients are averaged over all 8 × 32 examples each step."},
  {"q": "What does DDP do with gradients during backward?", "options": ["All-reduces them in buckets, overlapping communication with computation", "Sends them to GPU 0 to apply the update", "Discards all but one GPU's gradients", "Nothing until the epoch ends"], "answer": 0,
   "explain": "Every process ends with the same averaged gradient and takes the same step."},
  {"q": "You forget sampler.set_epoch(epoch) with DistributedSampler. What happens?", "options": ["Each epoch uses the same shuffled order", "Training crashes", "Each GPU sees all the data", "Gradients are not averaged"], "answer": 0,
   "explain": "The sampler's shuffle is seeded by the epoch number."},
  {"q": "When is torch.backends.cudnn.benchmark = True a bad idea?", "options": ["When input sizes change from batch to batch", "When training convnets", "When using mixed precision", "When using DDP"], "answer": 0,
   "explain": "It re-benchmarks algorithms for every new shape, wasting time."}
]
```

> **Source:** Stevens, Antiga & Viehmann, *Deep Learning with PyTorch*, ch. 11 (data loader workers, multiple GPUs with DataParallel) and ch. 15 (the dual nature of PyTorch as interface and backend, JIT compilation); PyTorch documentation (docs.pytorch.org): `torch.compile` and the torch.compiler user guide, `torch.profiler`, "Getting Started with Distributed Data Parallel", `torchrun`, FSDP.
