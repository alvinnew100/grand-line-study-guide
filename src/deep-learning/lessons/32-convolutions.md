# Convolutions, pooling and building a convnet

> **Before this lesson:** read [A first image classifier](#/lesson/deep-learning/image-classifier), whose fully connected model failed on shifted images; this lesson fixes that. You need the N × C × H × W layout from [Real-world data as tensors](#/lesson/deep-learning/data-as-tensors), strides and views from [storage, strides, views and devices](#/lesson/deep-learning/tensor-storage), and `nn.Module` from [nn.Module, state_dict and checkpointing](#/lesson/deep-learning/nn-module).

## In plain words

A **convolution** slides a small grid of weights, called a **kernel** or **filter**, across an image. At every position it multiplies the kernel with the patch of pixels underneath and adds everything up, producing one output number. Sliding it everywhere produces a new image, called a **feature map**, that is bright wherever the patch resembled the kernel. A **convolutional layer** learns many kernels at once, each detecting a different local pattern, and a **convolutional neural network (convnet or CNN)** stacks such layers so that later ones detect patterns made of earlier patterns.

Picture inspecting a large fabric for a specific stitch flaw using a small cardboard window with a picture of the flaw drawn on it. You move the window across the fabric, square by square, and mark how well each square matches. The same window is used everywhere, so you only had to draw the flaw once, and you find it wherever it occurs. That is weight sharing, and it is why convnets recognise an object regardless of where it appears.

Why it matters for a job: convnets remain the workhorse for images, video, medical scans, audio spectrograms and on-device vision, and their ideas (locality, weight sharing, pooling, receptive fields) reappear in every architecture. Interviewers routinely ask you to compute output sizes and parameter counts, explain padding and stride, or implement a naive `conv2d` in NumPy, which this lesson does.

## 1. The two ideas: locality and weight sharing

The fully connected layer gave every pixel its own weight to every output. A convolution makes two restrictions that match how images work:

- **Locality**: each output depends only on a small neighbourhood (say 3 × 3) of the input, because nearby pixels are what form edges, corners and textures.
- **Weight sharing**: the same kernel weights are used at every position, because a vertical edge is a vertical edge wherever it appears.

Together they slash the parameter count (a 3 × 3 kernel on a one-channel image has 9 weights plus a bias, whatever the image size) and give **translation equivariance**: shifting the input shifts the output feature map by the same amount. Add a pooling step at the end that ignores position and you get the translation invariance that the fully connected model lacked.

## 2. The operation, step by step

For a one-channel input $x$ and a $k \times k$ kernel $w$ with bias $b$, the output at row $i$, column $j$ is

$$y_{i,j} = b + \sum_{u=0}^{k-1} \sum_{v=0}^{k-1} w_{u,v} \; x_{i+u,\, j+v}$$

(Mathematicians would call this **cross-correlation**; true convolution flips the kernel first. Deep-learning libraries skip the flip, and since kernels are learned it makes no difference.)

With **multiple input channels**, a kernel has one $k \times k$ slice per input channel, and the products are summed over all channels too. So one output channel always looks at *all* input channels. With $C_{\text{out}}$ kernels you get $C_{\text{out}}$ output channels. In PyTorch:

```python
from torch import nn
conv = nn.Conv2d(in_channels=3, out_channels=16, kernel_size=3, padding=1)
conv.weight.shape        # torch.Size([16, 3, 3, 3])  -> (out_channels, in_channels, kH, kW)
conv.bias.shape          # torch.Size([16])
# parameters: 16 * 3 * 3 * 3 + 16 = 448
```

### Padding, stride and the output size

- **Padding** $p$ adds $p$ rows and columns of zeros around the border. Without it, a 3 × 3 kernel cannot centre on edge pixels and the output shrinks by 2 in each dimension. With `padding=1` (generally $p = (k-1)/2$ for odd $k$) the output keeps the input size; PyTorch also accepts `padding="same"` for stride 1.
- **Stride** $s$ is the step between positions. Stride 2 skips every other position and halves the output size.
- **Dilation** $d$ spaces out the kernel's taps, letting a 3 × 3 kernel cover a 5 × 5 area with gaps; it enlarges the view without more parameters.

The output height (and likewise width) is

$$H_{\text{out}} = \left\lfloor \frac{H + 2p - d(k-1) - 1}{s} \right\rfloor + 1$$

where $\lfloor \cdot \rfloor$ rounds down. Examples for $H = 32$: $k=3, p=0, s=1$ gives 30; $k=3, p=1, s=1$ gives 32; $k=3, p=1, s=2$ gives 16; $k=5, p=2, s=1$ gives 32.

## 3. Writing conv2d in NumPy

Here is a naive convolution, a fast one built from a strided **sliding-window view** (the zero-copy trick from the storage lesson), and two hand-made kernels applied to a synthetic image.

```python-run
import numpy as np
from numpy.lib.stride_tricks import sliding_window_view

def conv2d_naive(x, weight, bias, stride=1, padding=0):
    """x: (C_in, H, W); weight: (C_out, C_in, k, k); bias: (C_out,). Mirrors F.conv2d for one image."""
    x = np.pad(x, ((0, 0), (padding, padding), (padding, padding)))
    c_out, c_in, k, _ = weight.shape
    H_out = (x.shape[1] - k) // stride + 1
    W_out = (x.shape[2] - k) // stride + 1
    out = np.zeros((c_out, H_out, W_out))
    for o in range(c_out):
        for i in range(H_out):
            for j in range(W_out):
                patch = x[:, i * stride:i * stride + k, j * stride:j * stride + k]
                out[o, i, j] = (patch * weight[o]).sum() + bias[o]
    return out

def conv2d_fast(x, weight, bias, stride=1, padding=0):
    x = np.pad(x, ((0, 0), (padding, padding), (padding, padding)))
    k = weight.shape[-1]
    windows = sliding_window_view(x, (k, k), axis=(1, 2))[:, ::stride, ::stride]   # (C_in, H_out, W_out, k, k), no copy
    return np.einsum("chwuv,ocuv->ohw", windows, weight) + bias[:, None, None]

img = np.zeros((1, 8, 8)); img[0, :, 4:] = 1.0            # dark left half, bright right half
vertical_edge = np.array([[[[-1, 0, 1], [-1, 0, 1], [-1, 0, 1]]]], float)   # (1, 1, 3, 3)
blur = np.full((1, 1, 3, 3), 1 / 9)
for name, kern in [("vertical edge", vertical_edge), ("blur", blur)]:
    y = conv2d_fast(img, kern, np.zeros(1), padding=1)
    print(f"{name} kernel, output row 3:", y[0, 3].round(2))

rng = np.random.default_rng(0)
x = rng.normal(size=(3, 9, 9)); w = rng.normal(size=(4, 3, 3, 3)); b = rng.normal(size=4)
for stride, pad in [(1, 0), (1, 1), (2, 1)]:
    a, f = conv2d_naive(x, w, b, stride, pad), conv2d_fast(x, w, b, stride, pad)
    print(f"stride {stride} padding {pad}: output {a.shape}, naive == fast: {np.allclose(a, f)}")
```

**Reading this code line by line**

- `np.pad` adds `padding` zeros on both sides of the height and width axes, leaving the channel axis alone.
- The naive version loops over output channels and positions, takes the `(C_in, k, k)` patch, multiplies it element-wise by that output channel's kernel and sums: exactly the formula.
- `sliding_window_view` creates a view whose last two axes are every $k \times k$ window, without copying; `[:, ::stride, ::stride]` keeps every `stride`-th window. `einsum` then multiplies each window by each kernel and sums over channel and kernel axes. This is the "im2col" idea that real libraries use to turn convolution into one big matrix multiplication.
- The vertical-edge kernel responds (value 3) only at the columns where dark meets bright and is 0 on flat regions; the blur kernel averages neighbourhoods, softening the boundary. Zero padding creates artificial edges at the image border, which is why the edge row also shows a negative response at the last column.
- Both implementations agree for every stride and padding, and the output sizes follow the formula (7, 9 and 5).

## 4. Equivariance, demonstrated

Shifting the input and then convolving gives the same result as convolving and then shifting (away from the borders). That is translation equivariance, and it is what the fully connected layer lacked. Combine it with a **global max pool** (take the largest value of each feature map, discarding position) and the result no longer depends on position at all.

```python-run
import numpy as np
from numpy.lib.stride_tricks import sliding_window_view

def conv2d(x, w):                                   # one channel in, many out, no padding
    win = sliding_window_view(x, w.shape[1:])
    return np.einsum("hwuv,ouv->ohw", win, w)

rng = np.random.default_rng(0)
PLUS = np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]], float)
CROSS = np.array([[1, 0, 1], [0, 1, 0], [1, 0, 1]], float)
filters = np.stack([PLUS - PLUS.mean(), CROSS - CROSS.mean()])   # pretend these were learned

img = rng.normal(0, 0.2, (12, 12)); img[2:5, 1:4] += PLUS
shifted = np.roll(img, 6, axis=1)                    # move everything 6 columns right
a = conv2d(img, filters); b = conv2d(shifted, filters)
print("conv(shift(x)) equals shift(conv(x)) in the interior:", np.allclose(np.roll(a, 6, axis=2)[:, :, 6:], b[:, :, 6:]))

def make(n, cols):
    X = rng.normal(0, 0.2, (n, 12, 12)); y = rng.integers(0, 2, n)
    for i in range(n):
        r, c = rng.integers(0, 10), rng.choice(cols)
        X[i, r:r + 3, c:c + 3] += PLUS if y[i] == 0 else CROSS
    return X, y

for label, cols in [("left half", np.arange(0, 4)), ("right half", np.arange(6, 10))]:
    X, y = make(500, cols)
    pooled = np.array([conv2d(x, filters).max(axis=(1, 2)) for x in X])   # global max pool: (500, 2)
    acc = (pooled.argmax(axis=1) == y).mean()
    print(f"patterns in the {label}: accuracy {acc:.3f}")
```

With two pattern detectors applied by convolution and a global max pool, the classifier is equally accurate whether the patterns are on the left or the right, unlike the fully connected model of the previous lesson. A trained convnet learns its filters instead of being handed them, but the position-independence comes from the architecture.

## 5. Pooling and downsampling

Images are large, and we want later layers to see wider regions without huge kernels. **Pooling** reduces the spatial size:

- **Max pooling** (`nn.MaxPool2d(2)`) splits each feature map into 2 × 2 blocks and keeps the maximum of each, halving height and width. It keeps the strongest detection in each block and adds a little tolerance to small shifts.
- **Average pooling** keeps the mean instead.
- **Strided convolution** (stride 2) downsamples while learning how; many modern networks use it instead of pooling.
- **Global average pooling** (`nn.AdaptiveAvgPool2d(1)`) averages each whole feature map to one number. Placing it before the final linear layer makes the network accept any input size and removes the large flatten-then-linear layer.

Pooling has no parameters. Its output size follows the same formula as convolution (with `kernel_size` and `stride`, default stride equal to the kernel size).

## 6. Receptive fields: seeing more with depth

The **receptive field** of a unit is the region of the original input that can influence it. A 3 × 3 convolution has a 3 × 3 receptive field. Stack another 3 × 3 convolution on it and each unit sees 5 × 5 of the input; after a 2 × 2 pooling, each further 3 × 3 convolution adds twice as much. The recurrence, walking from the input to the output with $r$ the receptive field and $j$ the **jump** (the distance in input pixels between neighbouring units of the current layer):

$$r \leftarrow r + (k - 1)\, j, \qquad j \leftarrow j \cdot s$$

starting from $r = 1, j = 1$. Depth plus downsampling lets a network built from tiny kernels end up seeing the whole image, composing edges into textures, parts and objects. You will implement this recurrence as a problem.

## 7. A complete small convnet

```python
import torch
from torch import nn
import torch.nn.functional as F

class SmallConvNet(nn.Module):
    def __init__(self, n_classes=2):
        super().__init__()
        self.conv1 = nn.Conv2d(3, 32, kernel_size=3, padding=1)   # (N, 32, 32, 32)
        self.conv2 = nn.Conv2d(32, 16, kernel_size=3, padding=1)  # (N, 16, 16, 16) after pool
        self.fc1 = nn.Linear(16 * 8 * 8, 64)
        self.fc2 = nn.Linear(64, n_classes)

    def forward(self, x):                                  # x: (N, 3, 32, 32)
        x = F.max_pool2d(F.relu(self.conv1(x)), 2)         # (N, 32, 16, 16)
        x = F.max_pool2d(F.relu(self.conv2(x)), 2)         # (N, 16, 8, 8)
        x = torch.flatten(x, 1)                            # (N, 1024)
        x = F.relu(self.fc1(x))                            # (N, 64)
        return self.fc2(x)                                 # (N, n_classes) logits

model = SmallConvNet()
sum(p.numel() for p in model.parameters())                 # 71,250
```

Shapes and parameters layer by layer:

| layer | output shape | parameters |
|---|---|---|
| input | (N, 3, 32, 32) | 0 |
| conv1 3 → 32, 3 × 3, pad 1 | (N, 32, 32, 32) | 3·32·9 + 32 = 896 |
| ReLU, max pool 2 | (N, 32, 16, 16) | 0 |
| conv2 32 → 16, 3 × 3, pad 1 | (N, 16, 16, 16) | 32·16·9 + 16 = 4,624 |
| ReLU, max pool 2 | (N, 16, 8, 8) | 0 |
| flatten | (N, 1024) | 0 |
| fc1 1024 → 64 | (N, 64) | 65,600 |
| fc2 64 → 2 | (N, 2) | 130 |
| **total** | | **71,250** |

That is about 22 times fewer parameters than the 1.57 million of the fully connected classifier, and it generalises better because its structure matches images. Notice that even here most parameters sit in the first fully connected layer; replacing flatten with global average pooling would shrink the model further.

The common failure when writing such a model is a shape mismatch at `fc1`: if you change the input size or the number of pooling layers, `16 * 8 * 8` is no longer right. Print shapes during development, or use `nn.LazyLinear(64)`, which infers its input size on the first call.

## 8. Other convolutions you will meet

- **1 × 1 convolution**: mixes channels at each pixel without looking at neighbours, a cheap way to change the number of channels.
- **Depthwise separable convolution** (`groups=in_channels` followed by a 1 × 1 convolution): filters each channel separately, then mixes channels; far fewer parameters and operations, used in mobile networks.
- **3-D convolution** (`nn.Conv3d`): kernels of shape $k \times k \times k$ for volumes such as CT scans, used in the [project module](#/lesson/deep-learning/training-application).
- **1-D convolution** (`nn.Conv1d`): for sequences such as audio or time series.
- **Transposed convolution** (`nn.ConvTranspose2d`): upsamples feature maps, used in segmentation decoders such as U-Net ([segmentation lesson](#/lesson/deep-learning/segmentation)).

> [!INTERVIEW]
> **"Input 3 × 224 × 224, `Conv2d(3, 64, kernel_size=7, stride=2, padding=3)`. Output shape and parameter count?"** Output height $= \lfloor (224 + 6 - 6 - 1)/2 \rfloor + 1 = \lfloor 223/2 \rfloor + 1 = 112$, so $(N, 64, 112, 112)$. Parameters $= 64 \times 3 \times 7 \times 7 + 64 = 9{,}472$. Then add: the multiply-adds are about $112 \times 112 \times 64 \times 147 \approx 118$ million per image, which is why early layers dominate compute while late layers dominate parameters.

## Summary

- Convolution slides shared kernels over local neighbourhoods; each output channel sums over all input channels.
- `Conv2d` weights have shape (out, in, k, k); parameters = out·in·k² + out, independent of image size.
- Output size = ⌊(H + 2p − d(k−1) − 1)/s⌋ + 1; padding preserves size, stride downsamples, dilation widens the view.
- Convolutions are translation equivariant; with pooling they become tolerant or invariant to position.
- Pooling and strided convolutions downsample; the receptive field grows with depth via r ← r + (k−1)j, j ← j·s.
- A small convnet beats a far larger fully connected network on images because its structure fits the data.

## Glossary

- **Convolution (cross-correlation)**: sliding a kernel across an input and summing element-wise products.
- **Kernel / filter**: the small learned weight grid of a convolution.
- **Feature map**: the output grid of one convolution channel.
- **Convnet (CNN)**: a network built mainly from convolutional layers.
- **Locality**: each output depends on a small neighbourhood.
- **Weight sharing**: using the same weights at every position.
- **Translation equivariance**: shifting the input shifts the output the same way.
- **Padding / stride / dilation**: border zeros / step between positions / spacing between kernel taps.
- **Sliding-window view / im2col**: a zero-copy view of all patches / unrolling patches so convolution becomes a matrix product.
- **Max / average pooling**: downsampling by block maximum / block mean.
- **Global average pooling**: averaging each whole feature map to one value.
- **Receptive field / jump**: the input region affecting a unit / the input distance between neighbouring units.
- **1 × 1, depthwise separable, transposed convolution**: channel mixing / per-channel filtering plus mixing / learned upsampling.

## Check yourself

```quiz
[
  {"q": "What is the output height of Conv2d(kernel_size=3, stride=1, padding=0) on a 28-pixel-high input?", "options": ["26", "28", "27", "14"], "answer": 0,
   "explain": "(28 + 0 − 2 − 1)/1 + 1 = 26."},
  {"q": "How many parameters does nn.Conv2d(16, 32, kernel_size=3) have?", "options": ["4,640", "4,608", "512", "48"], "answer": 0,
   "explain": "32 × 16 × 3 × 3 = 4,608 weights plus 32 biases."},
  {"q": "Does the parameter count of a Conv2d layer depend on the input image size?", "options": ["No: the same kernels are shared across all positions", "Yes: it grows with height × width", "Only when padding is used", "Only for stride 2"], "answer": 0,
   "explain": "Weight sharing makes the count independent of spatial size."},
  {"q": "What does translation equivariance of convolution mean?", "options": ["Shifting the input shifts the feature map by the same amount", "The output is identical for any shift", "The kernel moves during training", "The image is translated before training"], "answer": 0,
   "explain": "Invariance (identical output) requires adding pooling over positions."},
  {"q": "Input (N, 8, 32, 32) goes through MaxPool2d(2). Output shape?", "options": ["(N, 8, 16, 16)", "(N, 4, 32, 32)", "(N, 8, 31, 31)", "(N, 4, 16, 16)"], "answer": 0,
   "explain": "Pooling acts on each channel separately and halves height and width."},
  {"q": "Two stacked 3 × 3 convolutions with stride 1 have what receptive field?", "options": ["5 × 5", "6 × 6", "9 × 9", "3 × 3"], "answer": 0,
   "explain": "r = 1 + 2 + 2 = 5."},
  {"q": "What padding keeps the output the same size for a 5 × 5 kernel with stride 1?", "options": ["2", "5", "1", "0"], "answer": 0,
   "explain": "p = (k − 1)/2 = 2."},
  {"q": "In a typical small convnet, where are most parameters?", "options": ["In the fully connected layer after flattening", "In the first convolution", "In the pooling layers", "In the ReLU layers"], "answer": 0,
   "explain": "Flatten-then-linear layers connect every feature to every unit; global average pooling avoids this."}
]
```

> **Source:** Stevens, Antiga & Viehmann, *Deep Learning with PyTorch*, ch. 8 (the case for convolutions, convolutions in action, padding the boundary, detecting features with convolutions, depth and pooling, putting it together into a network, subclassing nn.Module for a convnet); PyTorch documentation, `nn.Conv2d` and `nn.MaxPool2d` (output-shape formulas).
