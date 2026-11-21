# Deep learning interview problems, worked

> **Before this lesson:** read [Deep learning interview essentials](#/lesson/deep-learning/interview-essentials). The problems below draw on the whole track: cross-entropy from [A first image classifier](#/lesson/deep-learning/image-classifier), backpropagation from [Autograd in depth](#/lesson/deep-learning/autograd), DataLoader and collate functions from [Dataset, transforms and DataLoader](#/lesson/deep-learning/datasets-dataloaders), IoU from [Segmentation](#/lesson/deep-learning/segmentation), and memory estimates from [GPU memory and mixed precision](#/lesson/deep-learning/memory-mixed-precision).

## In plain words

Coding rounds for machine-learning roles rarely ask for a full model in PyTorch from memory. They ask you to implement a **small, well-defined piece** from scratch (usually in NumPy), to **read and fix** a broken training script, or to **estimate** sizes and costs on a whiteboard. The interviewer is watching how you reason: do you track shapes, check edge cases, test with a tiny example, and explain trade-offs?

This lesson works through the problems that come up most often, each with the approach an interviewer hopes to hear and runnable code. The module's 30 practice problems (spread across the earlier modules) drill the individual pieces; here we combine them the way a 45-minute interview does.

A useful routine for every problem, like a pilot's checklist before take-off:

1. **Restate** the task and confirm inputs, outputs and shapes.
2. **Work a tiny example** by hand.
3. **Write the straightforward version** first, then optimise if asked.
4. **Test** edge cases (empty input, a single element, extreme values) and, for gradients, check numerically.
5. **State complexity** and what would change at scale.

## Problem 1: Train a two-layer network from scratch

*"Using only NumPy, implement and train a classifier with one hidden layer on this toy dataset."* This is the most common deep-learning coding question. The interviewer checks the forward pass, a numerically stable loss, the backward pass with correct shapes, and the update.

```python-run
import numpy as np

rng = np.random.default_rng(0)

def make_spirals(n_per_class=100, classes=3):
    X, y = [], []
    for c in range(classes):
        r = np.linspace(0.05, 1, n_per_class)
        t = np.linspace(c * 4, (c + 1) * 4, n_per_class) + rng.normal(0, 0.2, n_per_class)
        X.append(np.c_[r * np.sin(t), r * np.cos(t)]); y.append(np.full(n_per_class, c))
    return np.vstack(X), np.concatenate(y)

X, y = make_spirals()                                   # 300 points, 3 interleaved spirals
N, D, H, C = len(X), 2, 64, 3
W1 = rng.normal(0, np.sqrt(2 / D), (D, H)); b1 = np.zeros(H)
W2 = rng.normal(0, np.sqrt(1 / H), (H, C)); b2 = np.zeros(C)
lr, wd = 1.0, 1e-3

for step in range(3001):
    z1 = X @ W1 + b1                                    # (N, H)
    h = np.maximum(z1, 0)                               # ReLU
    logits = h @ W2 + b2                                # (N, C)
    shifted = logits - logits.max(axis=1, keepdims=True)
    log_probs = shifted - np.log(np.exp(shifted).sum(axis=1, keepdims=True))
    loss = -log_probs[np.arange(N), y].mean() + 0.5 * wd * ((W1 ** 2).sum() + (W2 ** 2).sum())

    d_logits = np.exp(log_probs); d_logits[np.arange(N), y] -= 1; d_logits /= N   # softmax - onehot
    dW2 = h.T @ d_logits + wd * W2; db2 = d_logits.sum(axis=0)
    dz1 = (d_logits @ W2.T) * (z1 > 0)                  # back through ReLU
    dW1 = X.T @ dz1 + wd * W1; db1 = dz1.sum(axis=0)

    W1 -= lr * dW1; b1 -= lr * db1; W2 -= lr * dW2; b2 -= lr * db2
    if step % 1000 == 0:
        acc = (logits.argmax(axis=1) == y).mean()
        print(f"step {step:4d}  loss {loss:.4f}  train accuracy {acc:.3f}")
print("no straight-line boundary can separate interleaved spirals; the hidden layer bends the boundaries")
```

What to say while writing it: the loss starts near $\ln 3 \approx 1.10$ (a sanity check), the gradient of softmax cross-entropy is "probabilities minus one-hot, divided by N", bias gradients sum over the batch, the ReLU gradient is a mask, weight decay adds $\lambda W$ to the weight gradients only, and you would verify the backward pass with finite differences on a tiny input. Follow-ups: add momentum or Adam, mini-batches, a validation split, early stopping.

## Problem 2: Non-maximum suppression

*"An object detector outputs many overlapping boxes with confidence scores. Implement non-maximum suppression (NMS)."* A classic computer-vision question. **NMS** keeps the highest-scoring box, removes all remaining boxes that overlap it by more than an IoU threshold (they are likely duplicates of the same object), and repeats with the next highest survivor.

The building block is **IoU** for axis-aligned boxes given as `(x1, y1, x2, y2)`: the intersection rectangle is from the larger of the left/top edges to the smaller of the right/bottom edges, clamped at zero width and height.

```python-run
import numpy as np

def box_iou(box, boxes):
    """IoU of one box with many. Boxes are (x1, y1, x2, y2) with x2 > x1 and y2 > y1."""
    x1 = np.maximum(box[0], boxes[:, 0]); y1 = np.maximum(box[1], boxes[:, 1])
    x2 = np.minimum(box[2], boxes[:, 2]); y2 = np.minimum(box[3], boxes[:, 3])
    inter = np.clip(x2 - x1, 0, None) * np.clip(y2 - y1, 0, None)
    area = lambda b: (b[..., 2] - b[..., 0]) * (b[..., 3] - b[..., 1])
    return inter / (area(box) + area(boxes) - inter)

def nms(boxes, scores, iou_threshold=0.5):
    order = np.argsort(-scores)                       # highest score first
    keep = []
    while order.size:
        best = order[0]
        keep.append(int(best))
        if order.size == 1:
            break
        ious = box_iou(boxes[best], boxes[order[1:]])
        order = order[1:][ious <= iou_threshold]        # drop boxes overlapping the kept one too much
    return keep

boxes = np.array([[10, 10, 50, 50], [12, 12, 52, 48], [100, 100, 140, 150],
                  [11, 9, 49, 51], [102, 98, 138, 149], [60, 60, 70, 70]], dtype=float)
scores = np.array([0.90, 0.75, 0.80, 0.60, 0.85, 0.30])
print("IoU of box 0 with all:", box_iou(boxes[0], boxes).round(3))
print("kept boxes:", nms(boxes, scores, 0.5))
```

Two objects each received several overlapping boxes; NMS keeps the best box for each object (indices 0 and 4) plus the small separate box 5, and suppresses the duplicates. Points to mention: complexity is $O(n^2)$ in the worst case, so detectors keep only the top few thousand boxes before NMS; NMS is usually run **per class**; `torchvision.ops.nms` and `batched_nms` provide fast versions; "soft-NMS" lowers scores instead of deleting boxes; transformer detectors such as DETR avoid NMS altogether.

## Problem 3: Padding variable-length sequences

*"Write a `collate_fn` that batches token sequences of different lengths, and compute the mean embedding of each sequence ignoring padding."* This tests DataLoader knowledge and masking, which is everywhere in NLP and recommendation models.

```python-run
import numpy as np

PAD = 0

def collate(batch):
    """batch: list of (token_id_list, label). Returns padded ids (B, T), mask (B, T), labels (B,)."""
    lengths = [len(seq) for seq, _ in batch]
    T = max(lengths)
    ids = np.full((len(batch), T), PAD, dtype=np.int64)
    for i, (seq, _) in enumerate(batch):
        ids[i, :len(seq)] = seq
    mask = np.arange(T)[None, :] < np.array(lengths)[:, None]        # True where a real token sits
    labels = np.array([lab for _, lab in batch])
    return ids, mask, labels

batch = [([5, 8, 2], 1), ([7], 0), ([3, 3, 9, 4, 1], 1)]
ids, mask, labels = collate(batch)
print("padded ids:\n", ids)
print("mask:\n", mask.astype(int))

rng = np.random.default_rng(0)
emb_table = rng.normal(size=(10, 4))
emb = emb_table[ids]                                                 # (B, T, 4)
wrong = emb.mean(axis=1)                                             # averages the padding too
right = (emb * mask[..., None]).sum(axis=1) / mask.sum(axis=1, keepdims=True)
print("sequence 2 mean, naive  :", wrong[1].round(3))
print("sequence 2 mean, masked :", right[1].round(3), " = its only token:", emb_table[7].round(3))
```

The masked mean divides by each sequence's true length; the naive mean drags short sequences towards the padding embedding. In PyTorch the same `collate` returns tensors (`torch.nn.utils.rnn.pad_sequence` does the padding), and attention layers take the mask (or its inverse, a key-padding mask) so padded positions receive no attention. Mention bucketing by length to reduce wasted padding.

## Problem 4: Write the training loop from memory

*"In PyTorch, write a complete training loop with validation, mixed precision, checkpointing and early stopping."* Interviewers look for the right order of calls and the modes.

```python
def train(model, train_loader, val_loader, epochs, device, patience=5):
    model.to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=3e-4, weight_decay=0.01)
    total = epochs * len(train_loader)
    scheduler = torch.optim.lr_scheduler.OneCycleLR(optimizer, max_lr=3e-4, total_steps=total)
    loss_fn = nn.CrossEntropyLoss()
    best, bad = float("inf"), 0
    for epoch in range(epochs):
        model.train()
        for x, y in train_loader:
            x, y = x.to(device, non_blocking=True), y.to(device, non_blocking=True)
            with torch.autocast(device_type="cuda", dtype=torch.bfloat16):
                loss = loss_fn(model(x), y)
            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            scheduler.step()                                   # per iteration for OneCycleLR
        model.eval()
        val_loss, n = 0.0, 0
        with torch.inference_mode():
            for x, y in val_loader:
                x, y = x.to(device), y.to(device)
                with torch.autocast(device_type="cuda", dtype=torch.bfloat16):
                    val_loss += loss_fn(model(x), y).item() * len(y)
                n += len(y)
        val_loss /= n
        if val_loss < best - 1e-4:
            best, bad = val_loss, 0
            torch.save({"model": model.state_dict(), "optimizer": optimizer.state_dict(),
                        "scheduler": scheduler.state_dict(), "epoch": epoch}, "best.pt")
        else:
            bad += 1
            if bad >= patience:
                break
    return best
```

Things to call out: `zero_grad` before `backward`; `autocast` around forward and loss only; clipping after backward and before step; scheduler stepped at the granularity it was built for; `eval()` plus `inference_mode()` for validation; per-sample weighting of the validation loss so the last smaller batch counts correctly; checkpointing optimiser and scheduler state; early stopping on validation. With float16 instead of bfloat16 you would add a `GradScaler` and `unscale_` before clipping.

## Problem 5: Find the bugs

*"This script trains but the model is poor. Find the problems."* A favourite format. Read carefully, line by line:

```python
model = nn.Sequential(nn.Linear(784, 256), nn.ReLU(), nn.Linear(256, 10), nn.Softmax(dim=1))   # (1)
optimizer = torch.optim.Adam(model.parameters(), lr=0.1)                                        # (2)
loss_fn = nn.CrossEntropyLoss()
train_loader = DataLoader(train_set, batch_size=64, shuffle=False)                              # (3)
for epoch in range(10):
    for x, y in train_loader:
        loss = loss_fn(model(x.view(-1, 784)), y.float())                                       # (4)
        loss.backward()                                                                          # (5)
        optimizer.step()
        total_loss += loss                                                                       # (6)
    acc = (model(val_x).argmax(1) == val_y).float().mean()                                      # (7)
```

1. `nn.Softmax` before `CrossEntropyLoss` applies softmax twice; remove it (output logits).
2. A learning rate of 0.1 is far too high for Adam; use about 1e-3.
3. `shuffle=False` for training means batches follow the dataset order (possibly sorted by class).
4. Class-index targets must be `long` (int64), not float; with float targets the loss interprets them as class probabilities and fails on shape.
5. `optimizer.zero_grad()` is missing, so gradients accumulate across steps.
6. `total_loss += loss` keeps every graph alive (memory leak) and `total_loss` was never initialised; use `loss.item()`.
7. Validation runs without `model.eval()` and without `torch.no_grad()`, and in one huge batch; wrap it properly and batch it.

Being systematic (model, optimiser, data, loss inputs, update, logging, evaluation) finds them faster than reading top to bottom once.

## Problem 6: Back-of-the-envelope estimates

*"Estimate the compute and time to train a 1-billion-parameter transformer on 20 billion tokens using 8 GPUs that each sustain 150 TFLOP/s."* A widely used approximation: training a dense transformer costs about $6 N D$ floating-point operations, where $N$ is the parameter count and $D$ the number of training tokens (about 2 per parameter per token for the forward pass and 4 for the backward pass).

```python-run
N, D = 1e9, 20e9                                  # parameters, training tokens
flops = 6 * N * D
gpus, per_gpu = 8, 150e12                         # sustained FLOP/s per GPU (well below the peak)
seconds = flops / (gpus * per_gpu)
print(f"training compute: {flops:.2e} FLOPs")
print(f"time on {gpus} GPUs: {seconds / 3600:.1f} hours")

mem_train = N * 16 / 1e9
print(f"weights + grads + Adam states (fp32-style accounting): {mem_train:.0f} GB total, "
      f"{mem_train / gpus:.0f} GB per GPU if sharded with FSDP")

h, w = 224, 224
macs = 3 * 64 * 7 * 7 * (h // 2) * (w // 2)
print(f"ResNet stem convolution: {macs / 1e6:.0f}M MACs per image -> {2 * macs / 1e9:.2f} GFLOPs")
```

About $1.2 \times 10^{20}$ FLOPs, roughly 28 hours on 8 such GPUs, and 16 GB of training state that fits comfortably when sharded. State assumptions out loud: sustained throughput is a fraction of the GPU's peak, activations need extra memory, and data loading, evaluation and failures add time.

## Problem 7: Implement layers that behave differently in training

*"Implement Dropout and BatchNorm forward passes with training and evaluation modes."* Covered by this track's problems `dl-dropout` and `dl-batchnorm-forward`. The essential points: inverted dropout scales survivors by $1/(1-p)$ in training and is the identity in evaluation; BatchNorm normalises with batch statistics (biased variance) in training, updates running statistics with momentum 0.1 using the unbiased variance, and uses the running statistics in evaluation.

## What strong answers have in common

- They track **shapes** aloud: "logits are (N, C), so the gradient is (N, C), and W2's gradient is (H, C) = hᵀ (H, N) times (N, C)".
- They handle **numerical stability** without being asked: subtract the maximum before exponentiating, add epsilons to denominators.
- They **test** on a tiny example and name edge cases: empty batch, a single box, all-padding sequences, IoU of disjoint boxes.
- They connect to **practice**: "in production I would use `torchvision.ops.nms`", "`pad_sequence` and a key-padding mask", "`torch.compile` would fuse these element-wise operations".

> [!INTERVIEW]
> **"You have 45 minutes: implement logistic regression with gradient descent in NumPy, then extend it to a small neural network."** Spend five minutes on the interface and a toy dataset, write the forward pass and a stable binary cross-entropy (via `logaddexp` or the logits form), derive the gradient (predictions minus labels, times inputs, divided by N), train and print the loss, then add a hidden layer with ReLU and backpropagate through it, checking one gradient with finite differences. Talk through each shape and finish with how you would add mini-batches, regularisation and a validation split.

## Summary

- Interview coding problems are small, precise components: a NumPy network, NMS, masking and padding, a full PyTorch loop, bug hunts, and estimates.
- Follow a routine: restate, tiny example, simple version, edge cases and numerical checks, complexity.
- Two-layer network: stable log-softmax, gradient probabilities minus one-hot over N, ReLU mask, summed bias gradients.
- NMS: sort by score, keep the best, drop boxes with IoU above a threshold, repeat; run per class.
- Padding: collate to (B, T) with a mask; use masked means and attention masks.
- Estimates: training compute ≈ 6·N·D for transformers; Adam training state ≈ 16 bytes per parameter.

## Glossary

- **Non-maximum suppression (NMS)**: removing lower-scoring boxes that overlap a higher-scoring box too much.
- **Bounding box**: an axis-aligned rectangle (x1, y1, x2, y2) around an object.
- **Padding / mask**: filler tokens that make sequences equal length / a boolean array marking real positions.
- **Masked mean**: an average over real positions only.
- **Bucketing**: grouping similar-length sequences into the same batch to reduce padding.
- **6ND rule**: training a dense transformer costs about 6 × parameters × tokens FLOPs.
- **Sustained throughput**: the operations per second actually achieved, typically well below a GPU's peak.
- **Bug hunt**: an interview format where you find errors in a given script.

## Check yourself

```quiz
[
  {"q": "In a NumPy two-layer network with softmax cross-entropy averaged over N samples, what is the gradient with respect to the logits?", "options": ["(softmax probabilities − one-hot targets) / N", "softmax probabilities", "one-hot targets / N", "(logits − targets)²"], "answer": 0,
   "explain": "The derivative of the mean cross-entropy combined with softmax."},
  {"q": "NMS keeps a box with score 0.9. Another box of the same class overlaps it with IoU 0.7 and the threshold is 0.5. What happens to the second box?", "options": ["It is suppressed", "It is kept", "Its score is doubled", "Both are removed"], "answer": 0,
   "explain": "Overlap above the threshold marks it as a duplicate detection."},
  {"q": "Why compute a masked mean over padded sequences?", "options": ["So padding tokens do not distort the average of short sequences", "To make sequences longer", "Because NumPy cannot average integers", "To speed up embedding lookups"], "answer": 0,
   "explain": "Divide by the true length and zero out padded positions."},
  {"q": "Roughly how many FLOPs does training a 1B-parameter transformer on 20B tokens take?", "options": ["1.2 × 10^20", "1.2 × 10^12", "2 × 10^10", "6 × 10^9"], "answer": 0,
   "explain": "6 × 10^9 × 2 × 10^10."},
  {"q": "In the bug-hunt script, what is wrong with y.float() for nn.CrossEntropyLoss?", "options": ["Class-index targets must be int64 (long)", "Targets must be on the CPU", "Targets must be one-hot", "Nothing"], "answer": 0,
   "explain": "Float targets are interpreted as class probabilities with shape (N, C)."},
  {"q": "Which call order is correct inside a mixed-precision (bfloat16) training step?", "options": ["autocast forward and loss, zero_grad, backward, clip, optimizer.step, scheduler.step", "backward inside autocast, then zero_grad", "scheduler.step before optimizer.step", "clip before backward"], "answer": 0,
   "explain": "Clip after gradients exist; step the scheduler after the optimizer."},
  {"q": "What is the worst-case time complexity of greedy NMS on n boxes?", "options": ["O(n²)", "O(n)", "O(log n)", "O(n³)"], "answer": 0,
   "explain": "Each kept box may be compared with all remaining boxes; detectors cap n first."}
]
```

> **Source:** Stevens, Antiga & Viehmann, *Deep Learning with PyTorch*, ch. 5–8 (training from scratch, losses, the training loop) and ch. 12–14 (metrics, segmentation, IoU-style overlap); PyTorch and torchvision documentation (`torchvision.ops.nms`, `torch.nn.utils.rnn.pad_sequence`); Kaplan et al., "Scaling Laws for Neural Language Models" (2020) for the 6ND compute approximation.
