# Learning-rate schedules, warmup and gradient clipping

> **Before this lesson:** you need SGD, momentum, Adam and AdamW from [Optimisers and validation](#/lesson/deep-learning/optimizers-validation), divergence from [Learning as parameter estimation](#/lesson/deep-learning/learning-from-data), and residual networks from [Going deeper](#/lesson/deep-learning/depth-residuals). The cosine function is used: $\cos(0) = 1$, $\cos(\pi) = -1$, and it falls smoothly in between.

## In plain words

The learning rate is the most important hyperparameter, and the best value changes during training. Early on, large steps make fast progress across the loss landscape; later, small steps settle precisely into a good minimum instead of bouncing around it. A **learning-rate schedule** changes the learning rate automatically as training proceeds. **Warmup** starts with a tiny learning rate and ramps it up over the first steps, because the very beginning of training is fragile. **Gradient clipping** caps the size of each update so that one freak batch cannot throw the model off a cliff.

Picture parking a car. You drive at normal speed down the street (high learning rate), slow down as you approach the space (decay), and creep the last metre (a tiny learning rate). And when you first start the engine on an icy morning, you pull away gently (warmup). Clipping is the speed limiter that stops you flooring the accelerator by accident.

Why it matters for a job: every modern training recipe, from ResNets to large language models, uses a schedule (typically linear warmup then cosine decay) and gradient clipping. Interviewers ask "why warm up?", "when do you call `scheduler.step()`?", "what does `clip_grad_norm_` return?", and "your loss spikes at step 30,000; what do you check?".

## 1. Why decay the learning rate?

With stochastic gradients, each step follows a noisy estimate of the true gradient. Near a minimum the true gradient becomes small but the noise does not, so with a fixed learning rate the parameters keep jittering in a cloud around the minimum whose size grows with the learning rate. Shrinking the learning rate shrinks the cloud, letting the model settle. Starting large and ending small gets both speed and precision.

There is a second, subtler benefit: large learning rates early on keep the model away from sharp, narrow minima (it bounces out of them) and towards wide, flat ones, which tend to generalise better.

## 2. Schedules in torch.optim.lr_scheduler

```python
from torch.optim import lr_scheduler as S

opt = torch.optim.SGD(model.parameters(), lr=0.1, momentum=0.9, weight_decay=5e-4)

S.StepLR(opt, step_size=30, gamma=0.1)             # multiply lr by 0.1 every 30 epochs
S.MultiStepLR(opt, milestones=[60, 80], gamma=0.1) # drops at chosen epochs (the classic ResNet recipe)
S.ExponentialLR(opt, gamma=0.95)                   # multiply by 0.95 every step
S.CosineAnnealingLR(opt, T_max=100, eta_min=1e-5)  # smooth half-cosine from lr down to eta_min over T_max steps
S.OneCycleLR(opt, max_lr=0.1, total_steps=10_000)  # warm up to max_lr, then anneal far below the start
S.ReduceLROnPlateau(opt, mode="min", factor=0.5, patience=5)   # halve lr when val loss stalls 5 epochs
S.LinearLR(opt, start_factor=0.01, total_iters=1000)            # linear ramp (useful for warmup)
S.SequentialLR(opt, schedulers=[warmup, cosine], milestones=[1000])   # chain them
S.LambdaLR(opt, lr_lambda=lambda step: my_multiplier(step))     # any custom curve
```

Each scheduler multiplies (or sets) the learning rate stored in each of the optimiser's parameter groups. Rules that cause real bugs:

- **Order**: call `optimizer.step()` first, then `scheduler.step()`. Since PyTorch 1.1, calling them the other way round skips the first value of the schedule and prints a warning.
- **Granularity**: decide whether the schedule counts **epochs** or **iterations** (optimiser steps) and call `scheduler.step()` accordingly: once per epoch for `StepLR(step_size=30)` in epochs, once per batch for `OneCycleLR` and most warmup schedules.
- `ReduceLROnPlateau` is different: you pass it the monitored metric, `scheduler.step(val_loss)`.
- Read the current value with `scheduler.get_last_lr()` and log it; a wrong schedule is invisible unless you plot it.
- Save `scheduler.state_dict()` in checkpoints, or resumed training restarts the schedule from the beginning.

### Cosine annealing

The most popular smooth decay sets, for step $t$ out of $T$ total,

$$\eta_t = \eta_{\min} + \frac{1}{2}(\eta_{\max} - \eta_{\min})\left(1 + \cos\frac{\pi t}{T}\right)$$

At $t = 0$ the cosine is 1 and $\eta = \eta_{\max}$; at $t = T$ it is $-1$ and $\eta = \eta_{\min}$; in between it falls slowly at first, fastest in the middle, and slowly again at the end. It has only one extra knob ($\eta_{\min}$, often 0 or a small fraction of the peak) and works well across tasks.

## 3. Warmup

**Warmup** increases the learning rate from near zero to its target over the first few hundred or thousand steps. Why is the start fragile?

- Randomly initialised networks produce large, poorly scaled gradients at first; full-size steps can push weights into bad regions (dead ReLUs, saturated units, exploded activations) from which they never recover.
- Adam's second-moment estimate $v$ is built from only a handful of gradients at the start, so its per-parameter step sizes are noisy; a small learning rate covers that period.
- Large-batch training uses large learning rates (see below), which are only safe once the model has moved away from its chaotic initial state.
- Transformers are notoriously sensitive: the original transformer paper and essentially every large language model since use warmup.

The standard modern recipe, **linear warmup then cosine decay**:

$$\eta_t = \begin{cases} \eta_{\max} \cdot \dfrac{t + 1}{W} & t < W \\[6pt] \eta_{\min} + \dfrac{1}{2}(\eta_{\max} - \eta_{\min})\left(1 + \cos\left(\pi\dfrac{t - W}{T - W}\right)\right) & t \ge W \end{cases}$$

with $W$ warmup steps and $T$ total steps. (Conventions differ by one step on whether warmup starts at $\eta_{\max}/W$ or at 0; the problem for this module fixes one precisely.)

```python-run
import math

def warmup_cosine(step, max_lr, min_lr, warmup, total):
    if step < warmup:
        return max_lr * (step + 1) / warmup
    progress = min(1.0, (step - warmup) / max(1, total - warmup))
    return min_lr + 0.5 * (max_lr - min_lr) * (1 + math.cos(math.pi * progress))

def step_decay(step, base_lr, every, gamma):
    return base_lr * gamma ** (step // every)

def one_cycle_like(step, max_lr, total, pct_start=0.3, div=25, final_div=1e4):
    up = int(total * pct_start)
    start, end = max_lr / div, max_lr / final_div
    if step < up:
        return start + (max_lr - start) * (1 - math.cos(math.pi * step / up)) / 2
    p = (step - up) / (total - up)
    return end + (max_lr - end) * (1 + math.cos(math.pi * p)) / 2

total = 1000
print(f"{'step':>5} {'warmup+cosine':>14} {'step decay':>11} {'one-cycle':>10}")
for s in [0, 50, 99, 100, 250, 500, 750, 999]:
    print(f"{s:>5} {warmup_cosine(s, 3e-4, 3e-5, 100, total):>14.2e} {step_decay(s, 0.1, 300, 0.1):>11.2e} "
          f"{one_cycle_like(s, 0.1, total):>10.2e}")

bar = lambda v, vmax: "#" * int(40 * v / vmax)
print("\nwarmup + cosine, sketched:")
for s in range(0, total, 100):
    v = warmup_cosine(s, 3e-4, 3e-5, 100, total)
    print(f"{s:>4} {bar(v, 3e-4)}")
```

The table shows the three shapes side by side: warmup-cosine climbs to its peak at step 99, then glides down to its floor; step decay holds flat and drops tenfold every 300 steps; the one-cycle-like curve rises over the first 30% to a high peak and then anneals far below where it started. The little bar chart is the curve you should always plot from `get_last_lr()` before trusting a long run.

In PyTorch, the same warmup-cosine schedule is a `SequentialLR` of `LinearLR` and `CosineAnnealingLR`, stepped every iteration:

```python
warmup = S.LinearLR(opt, start_factor=1e-3, end_factor=1.0, total_iters=W)
cosine = S.CosineAnnealingLR(opt, T_max=T - W, eta_min=min_lr)
scheduler = S.SequentialLR(opt, schedulers=[warmup, cosine], milestones=[W])
for step, batch in enumerate(loader):
    ...
    optimizer.step()
    scheduler.step()
```

## 4. Choosing the peak learning rate and the batch size

- **Learning-rate range test**: train briefly while increasing the learning rate exponentially each step (for example from $10^{-7}$ to 10), plot loss against learning rate, and pick a peak somewhat below the value where the loss is falling fastest, well before it blows up. Cheap and surprisingly reliable.
- **Batch size and learning rate**: doubling the batch halves the gradient noise. A widely used heuristic for SGD is the **linear scaling rule**: multiply the learning rate by the same factor as the batch size (with warmup to make the larger rate safe). For Adam-type optimisers, a square-root scaling is a common starting point. Both are heuristics; past a "critical batch size" larger batches stop helping per step.
- **Typical peaks**: SGD with momentum around 0.1 for ResNets at batch 256; AdamW around $10^{-3}$ to $3 \times 10^{-4}$ for small transformers, lower for large ones and for fine-tuning ($10^{-5}$ to $5 \times 10^{-5}$).

## 5. Gradient clipping

Even with a good schedule, an occasional batch produces an enormous gradient: an unusual example, a numerical spike, or the steep "cliff" regions that recurrent networks and deep transformers sometimes encounter. One huge step can undo hours of training or produce `nan`s.

**Clipping by global norm** treats all parameter gradients as one long vector, computes its length (the **L2 norm**, the square root of the sum of all squared entries), and if it exceeds `max_norm`, scales every gradient down by the same factor so the length equals `max_norm`:

$$g \leftarrow g \cdot \min\left(1, \frac{\text{max\_norm}}{\lVert g \rVert_2 + \epsilon}\right)$$

The direction is preserved; only the step size is capped.

```python
loss.backward()
total_norm = torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)   # returns the norm BEFORE clipping
optimizer.step()
writer.add_scalar("grad_norm", total_norm, step)      # log it: spikes warn you before the loss does
```

- `clip_grad_norm_` modifies `.grad` in place (hence the underscore) and returns the total norm measured **before** clipping, which is the number you want to monitor.
- A `max_norm` of 1.0 is the near-universal default for transformers; for convnets clipping is often unnecessary but harmless.
- `clip_grad_value_` instead clamps each element to $[-c, c]$, which changes the gradient's direction; norm clipping is usually preferred.
- With mixed precision and a `GradScaler`, gradients are scaled up, so you must call `scaler.unscale_(optimizer)` **before** clipping ([next lesson](#/lesson/deep-learning/memory-mixed-precision)).

```python-run
import numpy as np

def clip_grad_norm_(grads, max_norm, eps=1e-6):
    """grads: list of arrays, modified in place. Returns the total norm before clipping (like PyTorch)."""
    total = np.sqrt(sum((g ** 2).sum() for g in grads))
    coef = max_norm / (total + eps)
    if coef < 1:
        for g in grads:
            g *= coef
    return total

grads = [np.array([3.0, 4.0]), np.array([[12.0]])]          # total norm sqrt(9 + 16 + 144) = 13
before = clip_grad_norm_(grads, max_norm=1.0)
after = np.sqrt(sum((g ** 2).sum() for g in grads))
print(f"norm before {before:.3f}, after {after:.3f}, direction kept: {grads[0] / grads[0][0]}")

# A steep loss f(x) = x^4 from x = 3 with learning rate 0.1: the first gradient is 108.
for max_norm in (None, 1.0):
    x = 3.0
    for step in range(100):
        g = [np.array([4 * x ** 3])]
        if max_norm is not None:
            clip_grad_norm_(g, max_norm)
        x -= 0.1 * g[0][0]
        if abs(x) > 1e6:
            break
    status = f"diverged at step {step}" if abs(x) > 1e6 else f"x = {x:.4f}, loss = {x ** 4:.2e}"
    print(f"max_norm {max_norm}: {status}")
```

The first part reproduces PyTorch's behaviour on two "parameters": a total norm of 13 is scaled to 1 while the relative direction of each gradient is unchanged. The second part shows why clipping exists: on a steep function, the unclipped first step overshoots wildly and the iterate explodes within a few steps; with clipping, each step is at most 0.1 and the iterate walks steadily to the minimum.

## 6. Putting it together: a modern training step

```python
for step, (x, y) in enumerate(loader):
    with torch.autocast(device_type="cuda", dtype=torch.bfloat16):
        loss = loss_fn(model(x), y)
    loss.backward()
    grad_norm = torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
    optimizer.step()
    scheduler.step()
    optimizer.zero_grad(set_to_none=True)
    if step % 100 == 0:
        log(step=step, loss=loss.item(), lr=scheduler.get_last_lr()[0], grad_norm=grad_norm.item())
```

(Autocast with bfloat16 is explained in the next lesson.)

> [!INTERVIEW]
> **"Your training loss suddenly spikes at step 30,000 and then recovers slowly (or turns into NaN). What do you look at?"** The logged gradient norm and learning rate around that step: a gradient-norm spike points to a bad batch or an unstable region; check that gradient clipping is on and applied after unscaling in mixed precision; look at the offending batch (corrupt data, extreme values, an all-padding sequence); check the schedule (did warmup end, or a restart raise the learning rate?); consider lowering the peak learning rate, adding warmup, raising Adam's epsilon, or skipping batches whose gradient norm is anomalous. Resume from the last good checkpoint rather than continuing from a damaged state.

## Summary

- Decaying the learning rate shrinks the noise cloud around the minimum; large early rates favour flat minima.
- PyTorch schedulers (StepLR, MultiStepLR, CosineAnnealingLR, OneCycleLR, LinearLR, SequentialLR, ReduceLROnPlateau, LambdaLR) adjust each parameter group's learning rate; call `scheduler.step()` after `optimizer.step()` at the intended granularity and checkpoint its state.
- Warmup protects the fragile start; linear warmup then cosine decay is the default recipe for transformers and most modern models.
- Find peak learning rates with a range test; scale the learning rate with batch size heuristically, with warmup.
- `clip_grad_norm_` rescales all gradients so their global L2 norm is at most `max_norm` and returns the pre-clip norm; log it; unscale first under mixed precision.

## Glossary

- **Learning-rate schedule**: a rule changing the learning rate during training.
- **Step decay / multi-step decay**: dropping the rate by a factor at fixed intervals / chosen milestones.
- **Cosine annealing**: decaying the rate along a half cosine to a minimum.
- **OneCycle**: rising to a peak learning rate, then annealing far below the start.
- **ReduceLROnPlateau**: cutting the rate when a monitored metric stops improving.
- **Warmup**: ramping the learning rate up from near zero at the start.
- **SequentialLR / LambdaLR**: chaining schedulers / a custom multiplier function.
- **Learning-rate range test (finder)**: a short sweep to find a good peak learning rate.
- **Linear scaling rule**: scaling the learning rate in proportion to the batch size.
- **Critical batch size**: the batch size beyond which larger batches give diminishing returns per step.
- **Gradient clipping (by norm / by value)**: capping the global gradient length / each element.
- **L2 norm**: the square root of the sum of squared entries.
- **Gradient norm**: the L2 norm of all gradients together, a key health signal.

## Check yourself

```quiz
[
  {"q": "In which order should you call these each iteration?", "options": ["optimizer.step() then scheduler.step()", "scheduler.step() then optimizer.step()", "scheduler.step() then loss.backward()", "Order does not matter"], "answer": 0,
   "explain": "Reversing them skips the first scheduled value and triggers a PyTorch warning."},
  {"q": "With cosine annealing from 0.1 to 0 over T steps, what is the learning rate at t = T/2?", "options": ["0.05", "0.1", "0.0", "0.0707"], "answer": 0,
   "explain": "cos(π/2) = 0, so η = 0 + 0.5 · 0.1 · (1 + 0) = 0.05."},
  {"q": "Why is warmup especially helpful with Adam at the start of training?", "options": ["Its second-moment estimates come from very few gradients and are unreliable, so step sizes are noisy", "Adam cannot compute gradients without it", "It reduces memory use", "It replaces weight decay"], "answer": 0,
   "explain": "A small learning rate covers the period when the adaptive scaling is poorly estimated."},
  {"q": "What does torch.nn.utils.clip_grad_norm_ return?", "options": ["The total gradient norm before clipping", "The clipped gradients", "The new learning rate", "Nothing"], "answer": 0,
   "explain": "Logging it reveals gradient spikes."},
  {"q": "Gradients have global norm 13 and max_norm is 1. What happens?", "options": ["Every gradient is multiplied by about 1/13, preserving direction", "Each element is clamped to [−1, 1]", "The step is skipped", "Only the largest gradient is reduced"], "answer": 0,
   "explain": "Norm clipping rescales uniformly; value clipping would clamp element-wise."},
  {"q": "You use OneCycleLR with total_steps equal to the number of batches over all epochs, but call scheduler.step() once per epoch. What goes wrong?", "options": ["The schedule barely advances: the learning rate stays near its starting value all run", "It finishes too early", "Nothing", "The optimizer stops updating"], "answer": 0,
   "explain": "Schedules counted in iterations must be stepped every iteration."},
  {"q": "Using mixed precision with GradScaler, what must happen before gradient clipping?", "options": ["scaler.unscale_(optimizer)", "scaler.update()", "optimizer.zero_grad()", "scheduler.step()"], "answer": 0,
   "explain": "Gradients are still multiplied by the loss scale until unscaled, so clipping would use the wrong threshold."},
  {"q": "You multiply the batch size by 8 for SGD training. A common first adjustment?", "options": ["Multiply the learning rate by about 8 and add warmup", "Divide the learning rate by 8", "Remove the schedule", "Turn off momentum"], "answer": 0,
   "explain": "The linear scaling rule, made safe by warmup; verify on validation."}
]
```

> **Source:** Stevens, Antiga & Viehmann, *Deep Learning with PyTorch*, ch. 5 and 8 (learning rate choice and its effect on training) and ch. 14 (ideas for better training); PyTorch documentation, `torch.optim.lr_scheduler` and `torch.nn.utils.clip_grad_norm_`; Goyal et al., "Accurate, Large Minibatch SGD" (2017); Loshchilov & Hutter, "SGDR" (2017).
