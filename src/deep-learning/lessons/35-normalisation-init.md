# Normalisation layers and weight initialisation

> **Before this lesson:** you need input standardisation from [Real-world data as tensors](#/lesson/deep-learning/data-as-tensors), the vanishing-gradient demo from [Neurons, layers and activation functions](#/lesson/deep-learning/neurons-activations), buffers and `train()`/`eval()` from [nn.Module, state_dict and checkpointing](#/lesson/deep-learning/nn-module), and regularisation from [Training a convnet and fighting overfitting](#/lesson/deep-learning/regularisation). **Variance** is the average squared distance from the mean, the square of the standard deviation.

## In plain words

We standardise a network's *inputs* so that gradient descent behaves. But inside a deep network, every layer's input is the previous layer's output, and nothing guarantees those intermediate values stay on a sensible scale. If they shrink a little at every layer, the signal fades to nothing; if they grow a little, it explodes. Two complementary tools keep the scale under control:

- **Initialisation** chooses the random starting weights with exactly the right spread, so that at the start of training the signal neither fades nor explodes as it passes through the layers.
- **Normalisation layers** re-standardise intermediate values during training, every step, so the scale stays healthy even as the weights change.

An analogy: a long chain of people passing a whispered message. If each person speaks slightly more quietly than they heard, the message is inaudible by the end; slightly louder, and it becomes a shout. Good initialisation is teaching everyone to repeat at the volume they heard. A normalisation layer is a sound engineer placed every few people who resets the volume to a standard level.

Why it matters for a job: batch normalisation's different behaviour in training and evaluation is behind a whole class of production bugs, and interviewers love asking "how does batch norm work at inference time?", "why do transformers use layer norm instead?", "why not initialise all weights to zero?" and "what is He initialisation?".

## 1. Why the starting weights matter

**Why not zeros?** If every weight in a layer starts equal, every unit computes the same output and receives the same gradient, so they stay identical forever: the layer behaves like a single unit. Random initialisation **breaks the symmetry**. (Biases can safely start at zero.)

**Why the scale?** Consider a linear layer with $n_{\text{in}}$ inputs, each with variance 1, and weights drawn independently with variance $\sigma^2$. Each output is a sum of $n_{\text{in}}$ products, so its variance is about $n_{\text{in}} \sigma^2$. To keep the variance at 1 from layer to layer we need $\sigma^2 = 1/n_{\text{in}}$. The input count $n_{\text{in}}$ is called the **fan-in** (for a convolution, $c_{\text{in}} \times k \times k$); the output count is the **fan-out**.

- **Xavier (Glorot) initialisation**: variance $\frac{2}{n_{\text{in}} + n_{\text{out}}}$, a compromise that keeps both forward signals and backward gradients stable. Designed for tanh and sigmoid networks.
- **Kaiming (He) initialisation**: variance $\frac{2}{n_{\text{in}}}$. ReLU zeroes about half of its inputs, halving the variance, so the factor 2 compensates. The standard choice for ReLU networks.
- **PyTorch's defaults**: `nn.Linear` and `nn.Conv2d` draw weights uniformly from $\pm 1/\sqrt{n_{\text{in}}}$ (variance $\frac{1}{3 n_{\text{in}}}$), which is somewhat smaller than He. It works fine with normalisation layers present; for deep plain ReLU stacks, explicit He initialisation is safer.

```python
from torch import nn

def init_weights(m):
    if isinstance(m, (nn.Conv2d, nn.Linear)):
        nn.init.kaiming_normal_(m.weight, nonlinearity="relu")   # He initialisation
        if m.bias is not None:
            nn.init.zeros_(m.bias)

model.apply(init_weights)          # calls init_weights on every submodule
```

The `nn.init` functions end with an underscore because they fill the tensor in place. Other useful ones: `xavier_uniform_`, `trunc_normal_` (used in vision transformers), `orthogonal_` (recurrent networks).

```python-run
import numpy as np

rng = np.random.default_rng(0)

def activation_spread(init, depth=20, width=256):
    x = rng.normal(size=(512, width))
    stds = []
    for _ in range(depth):
        if init == "small (std 0.01)":
            W = rng.normal(0, 0.01, (width, width))
        elif init == "pytorch default":
            bound = 1 / np.sqrt(width)
            W = rng.uniform(-bound, bound, (width, width))
        elif init == "xavier":
            W = rng.normal(0, np.sqrt(2 / (width + width)), (width, width))
        elif init == "kaiming (he)":
            W = rng.normal(0, np.sqrt(2 / width), (width, width))
        x = np.maximum(x @ W, 0)               # linear layer + ReLU
        stds.append(x.std())
    return stds

for init in ["small (std 0.01)", "pytorch default", "xavier", "kaiming (he)"]:
    s = activation_spread(init)
    print(f"{init:18s} std after layer 1: {s[0]:9.3e}   layer 10: {s[9]:9.3e}   layer 20: {s[19]:9.3e}")
```

Through 20 ReLU layers, a tiny fixed scale makes activations vanish entirely; PyTorch's default and Xavier both shrink the signal by roughly a constant factor per layer (by layer 20 it is orders of magnitude smaller); He initialisation keeps it roughly constant. Gradients flowing backwards suffer the same fate, which is why a deep plain network with the wrong initialisation may not train at all.

## 2. Batch normalisation

**Batch normalisation** (BatchNorm, Ioffe and Szegedy, 2015) standardises each channel using the statistics of the current mini-batch, then lets the network rescale it with two learned parameters. For a convolutional feature map of shape $(N, C, H, W)$, for each channel $c$:

$$\mu_c = \text{mean over } (N, H, W), \qquad \sigma_c^2 = \text{variance over } (N, H, W)$$

$$\hat{x} = \frac{x - \mu_c}{\sqrt{\sigma_c^2 + \epsilon}}, \qquad y = \gamma_c \hat{x} + \beta_c$$

- $\epsilon$ (default $10^{-5}$) avoids division by zero.
- $\gamma$ (scale, `weight`) and $\beta$ (shift, `bias`) are learned, so the layer can undo the normalisation if that is what works best; it is not forced to output mean 0 and variance 1.
- `nn.BatchNorm1d(features)` normalises over the batch for vectors of shape $(N, F)$; `nn.BatchNorm2d(channels)` over batch and pixels for images; `nn.BatchNorm3d` for volumes.

### Training mode versus evaluation mode

In training, BatchNorm uses the current batch's statistics, and it also keeps **running estimates** of the mean and variance in two buffers, updated every training step with an exponential moving average:

$$\text{running\_mean} \leftarrow (1 - m)\,\text{running\_mean} + m\,\mu_{\text{batch}}$$

with momentum $m = 0.1$ by default (PyTorch's "momentum" here is the weight of the *new* value, unlike the optimiser's momentum). The running variance is updated the same way using the **unbiased** batch variance (dividing by count − 1), while the normalisation itself uses the biased one.

In evaluation mode (`model.eval()`), BatchNorm uses the stored running statistics instead of the batch's. This makes a prediction independent of whatever else is in the batch, and works with a batch of one. It is also why forgetting `model.eval()` gives different, usually worse, results.

```python-run
import numpy as np

class BatchNorm2d:
    """Mirror of torch.nn.BatchNorm2d (affine=True, track_running_stats=True)."""
    def __init__(self, num_features, eps=1e-5, momentum=0.1):
        self.weight, self.bias = np.ones(num_features), np.zeros(num_features)       # gamma, beta
        self.running_mean, self.running_var = np.zeros(num_features), np.ones(num_features)  # buffers
        self.eps, self.momentum, self.training = eps, momentum, True
    def __call__(self, x):                                   # x: (N, C, H, W)
        if self.training:
            mean = x.mean(axis=(0, 2, 3))
            var = x.var(axis=(0, 2, 3))                      # biased: used to normalise
            n = x.size / x.shape[1]
            unbiased = var * n / (n - 1)                     # unbiased: used for the running estimate
            self.running_mean = (1 - self.momentum) * self.running_mean + self.momentum * mean
            self.running_var = (1 - self.momentum) * self.running_var + self.momentum * unbiased
        else:
            mean, var = self.running_mean, self.running_var
        x_hat = (x - mean[None, :, None, None]) / np.sqrt(var[None, :, None, None] + self.eps)
        return self.weight[None, :, None, None] * x_hat + self.bias[None, :, None, None]

rng = np.random.default_rng(0)
bn = BatchNorm2d(3)
for step in range(200):                                       # "training": batches with mean 5, std 2
    batch = rng.normal(5, 2, size=(16, 3, 4, 4))
    out = bn(batch)
print("train-mode output mean/std per channel:", out.mean(axis=(0, 2, 3)).round(3), out.std(axis=(0, 2, 3)).round(3))
print("running_mean:", bn.running_mean.round(2), " running_var:", bn.running_var.round(2))

single = rng.normal(5, 2, size=(1, 3, 4, 4))
bn.training = False
print("eval mode on a batch of ONE, mean per channel:", bn(single).mean(axis=(0, 2, 3)).round(2))
weird = np.full((4, 3, 4, 4), 7.0)                            # a batch where every value is 7
bn.training = True
print("train mode on a constant batch -> all zeros?", np.allclose(bn(weird), 0))
bn.training = False
print("eval mode on the same batch:", bn(weird)[0, :, 0, 0].round(3), "(about (7 - 5) / 2 = 1, using the estimated running statistics)")
```

**Reading this code line by line**

- In training mode the layer normalises with the batch's own mean and (biased) variance, and nudges the running buffers 10% of the way towards the batch values, using the unbiased variance.
- After 200 batches the running estimates approach the true mean 5 and variance 4.
- In eval mode a single example is normalised with the running statistics, giving sensible values even though a batch of one has no meaningful variance.
- The constant batch shows the danger of training-mode statistics: every value equals the batch mean, so the output is all zeros and carries no information. Eval mode maps 7 to roughly $(7-5)/2 = 1$ (slightly less, because the running estimates are not exactly 5 and 4).

### Practical notes

- Place it as `Conv → BatchNorm → ReLU`. The convolution's bias is then redundant (BatchNorm subtracts the mean and adds its own $\beta$), so write `nn.Conv2d(..., bias=False)`.
- Small batches (below about 8 to 16) give noisy statistics and hurt accuracy. Alternatives below avoid batch statistics entirely.
- When fine-tuning a pretrained model on small batches, it is common to keep BatchNorm layers in eval mode (frozen running statistics) or replace them with GroupNorm.
- With multiple GPUs each device sees only its share of the batch; `nn.SyncBatchNorm` computes statistics across all of them.
- BatchNorm makes training faster and more tolerant of high learning rates and poor initialisation; why exactly is still debated (the original "internal covariate shift" explanation is disputed; smoothing of the loss landscape is a leading alternative).

## 3. Layer normalisation and friends

**Layer normalisation** (LayerNorm) computes the mean and variance over the *features of each example separately*, not over the batch. It therefore behaves identically in training and evaluation, works with any batch size, and handles variable-length sequences, which is why **transformers use LayerNorm** (see the [transformer block lesson](#/lesson/llm-practice/transformer-block)).

| layer | statistics computed over | typical use |
|---|---|---|
| BatchNorm2d | batch, height, width (per channel) | convnets with reasonable batch sizes |
| LayerNorm | the feature dimensions of each example | transformers, recurrent nets |
| RMSNorm | like LayerNorm but only rescales by the root mean square, no mean subtraction | most recent large language models |
| GroupNorm | groups of channels within each example | detection and segmentation with small batches |
| InstanceNorm | each channel of each example | style transfer, some generative models |

```python
nn.LayerNorm(512)                 # normalise the last dimension of size 512, learned weight and bias
nn.GroupNorm(num_groups=32, num_channels=256)
nn.RMSNorm(512)                   # available in recent PyTorch versions
```

```python-run
import numpy as np

def layer_norm(x, eps=1e-5):
    mean = x.mean(axis=-1, keepdims=True)
    var = x.var(axis=-1, keepdims=True)
    return (x - mean) / np.sqrt(var + eps)        # (gamma = 1, beta = 0 here)

def rms_norm(x, eps=1e-6):
    return x / np.sqrt((x ** 2).mean(axis=-1, keepdims=True) + eps)

rng = np.random.default_rng(1)
tokens = rng.normal(3, 4, size=(2, 5, 8))          # 2 sentences, 5 tokens, 8 features
ln = layer_norm(tokens)
print("LayerNorm: per-token mean", ln.mean(axis=-1)[0].round(6), " std", ln.std(axis=-1)[0].round(3))
one = layer_norm(tokens[:1])
print("same result when the batch has a single sentence:", np.allclose(one, ln[:1]))
print("RMSNorm: per-token root mean square", np.sqrt((rms_norm(tokens) ** 2).mean(axis=-1))[0].round(3))
```

LayerNorm makes every token vector have mean 0 and standard deviation 1 regardless of what else is in the batch; RMSNorm only fixes the root-mean-square size, which is cheaper and works as well in practice for large language models.

## 4. Where normalisation goes in modern architectures

- **Convnets** (ResNet family): `Conv → BN → ReLU` inside each block; some designs zero-initialise the last BatchNorm $\gamma$ in each residual block so every block starts as an identity function, which stabilises very deep networks (see [residual connections](#/lesson/deep-learning/depth-residuals)).
- **Transformers**: the original design normalised *after* adding the residual ("post-norm"); nearly all modern models normalise the input of each sub-layer *before* it ("pre-norm"), which trains more stably at depth.
- Normalisation and good initialisation are complements: with normalisation, the network is much less sensitive to the initial scale; without it (some recent architectures remove it for speed), careful initialisation and residual scaling become critical.

> [!INTERVIEW]
> **"How does BatchNorm behave differently at training and inference, and what goes wrong in production?"** In training it normalises with the current batch's mean and variance and updates running averages; in inference (`eval()`) it uses those running averages. Failure modes: forgetting `eval()` (predictions depend on batch composition, and single-example batches break); running statistics computed on data unlike production data; tiny training batches giving noisy statistics; and fine-tuning with small batches that corrupts pretrained running statistics. Fixes: always call `eval()`, freeze BN statistics when fine-tuning with small batches, or use GroupNorm or LayerNorm.

## Summary

- Random initialisation breaks symmetry; its scale must keep activation variance roughly constant across layers.
- Xavier uses variance 2/(fan-in + fan-out); Kaiming/He uses 2/fan-in for ReLU; PyTorch defaults are uniform ±1/√fan-in.
- BatchNorm standardises each channel over the batch and pixels, then applies learned γ and β; it tracks running mean and variance (momentum 0.1, unbiased variance) for evaluation.
- Training mode uses batch statistics; eval mode uses running statistics; forgetting `eval()` is a classic bug.
- LayerNorm (per example), RMSNorm, GroupNorm and InstanceNorm avoid batch statistics; transformers use LayerNorm or RMSNorm, usually pre-norm.

## Glossary

- **Variance**: the average squared distance from the mean.
- **Symmetry breaking**: using random weights so units learn different features.
- **Fan-in / fan-out**: number of inputs / outputs of a unit or layer.
- **Xavier (Glorot) initialisation**: weight variance 2/(fan-in + fan-out).
- **Kaiming (He) initialisation**: weight variance 2/fan-in, suited to ReLU.
- **Batch normalisation**: per-channel standardisation with batch statistics plus learned scale and shift.
- **γ (gamma) / β (beta)**: the learned scale and shift of a normalisation layer.
- **Running statistics**: moving averages of mean and variance used in evaluation mode.
- **Unbiased variance**: dividing the sum of squared deviations by count − 1.
- **SyncBatchNorm**: batch normalisation with statistics shared across GPUs.
- **Layer normalisation**: standardisation over the features of each example.
- **RMSNorm**: rescaling by the root mean square without subtracting the mean.
- **GroupNorm / InstanceNorm**: normalising over channel groups / single channels of each example.
- **Pre-norm / post-norm**: normalising before a sub-layer / after the residual addition.

## Check yourself

```quiz
[
  {"q": "Why not initialise all weights of a layer to zero?", "options": ["All units would compute the same output and receive the same gradient, staying identical", "Zero weights cause NaN losses", "PyTorch forbids it", "It makes the bias useless"], "answer": 0,
   "explain": "Random initialisation breaks the symmetry between units."},
  {"q": "What weight variance does Kaiming (He) initialisation use for a ReLU layer with fan-in n?", "options": ["2/n", "1/n", "2/(n_in + n_out)", "1"], "answer": 0,
   "explain": "ReLU halves the variance, so the factor 2 compensates."},
  {"q": "During training, BatchNorm2d normalises each channel using statistics computed over which axes?", "options": ["Batch, height and width", "Channels only", "Height and width of each example", "The whole training set"], "answer": 0,
   "explain": "One mean and variance per channel, over all examples and pixels in the batch."},
  {"q": "In eval mode, BatchNorm normalises with…", "options": ["The running mean and variance accumulated during training", "The current batch statistics", "Mean 0 and variance 1 always", "Statistics of the first training batch"], "answer": 0,
   "explain": "This makes each prediction independent of the rest of the batch."},
  {"q": "Why is the convolution before a BatchNorm layer usually created with bias=False?", "options": ["BatchNorm subtracts the mean and adds its own β, making the bias redundant", "Biases slow down convolutions", "BatchNorm requires it", "To save GPU memory for activations"], "answer": 0,
   "explain": "Any constant added before mean subtraction is removed."},
  {"q": "Why do transformers use LayerNorm rather than BatchNorm?", "options": ["It normalises each example independently, so it works with any batch size and variable-length sequences", "It is the only normalisation that supports GPUs", "It has no learnable parameters", "BatchNorm cannot be used with attention"], "answer": 0,
   "explain": "No batch statistics means identical behaviour in training and inference."},
  {"q": "PyTorch's BatchNorm momentum=0.1 means…", "options": ["Each update moves the running statistic 10% towards the new batch value", "Gradients are scaled by 0.1", "The running statistic keeps 10% of its old value", "The learning rate of γ is 0.1"], "answer": 0,
   "explain": "running = 0.9 · running + 0.1 · batch_stat."},
  {"q": "You fine-tune a pretrained ResNet with batch size 2 and accuracy collapses. A likely fix?", "options": ["Freeze BatchNorm layers in eval mode or replace them with GroupNorm", "Increase dropout", "Use SGD without momentum", "Remove the classification head"], "answer": 0,
   "explain": "Batch statistics from two examples are too noisy and overwrite good running estimates."}
]
```

> **Source:** Stevens, Antiga & Viehmann, *Deep Learning with PyTorch*, ch. 8 (model design: keeping activations in check with batch normalisation, initialisation); PyTorch documentation, `nn.BatchNorm2d`, `nn.LayerNorm`, `nn.GroupNorm`, `nn.init`; Ioffe & Szegedy (2015); He et al., "Delving Deep into Rectifiers" (2015).
