# Overfitting and data augmentation

> **Before this lesson:** read [Rare positives: precision, recall, F1 and balanced sampling](#/lesson/deep-learning/imbalance-metrics), which ended with the balanced nodule classifier starting to memorise its few positives. You need overfitting and regularisation from [Training a convnet and fighting overfitting](#/lesson/deep-learning/regularisation), the fully connected shift experiment from [A first image classifier](#/lesson/deep-learning/image-classifier), and transforms from [Dataset, transforms and DataLoader](#/lesson/deep-learning/datasets-dataloaders).

## In plain words

**Data augmentation** creates new training examples by applying random, label-preserving changes to existing ones: flip a photo, shift it a little, rotate it, change its brightness, add a bit of noise. A nodule rotated by 20 degrees is still a nodule; a cat photo mirrored left-to-right is still a cat. Every epoch the model sees a fresh variant of each example, so it cannot memorise the exact pixels and has to learn what actually matters.

Imagine learning to recognise a friend only from one passport photo. You might latch onto the exact lighting and the angle of their head. If instead you see them in many photos (different rooms, angles, haircuts), you learn their face. Augmentation manufactures those extra photos from the one you have.

Why it matters for a job: augmentation is usually the single most effective regulariser for images, audio and other perceptual data, and it is how you encode domain knowledge about what should *not* change the answer. Interviewers ask which augmentations suit a task, which would be harmful (flipping a "6" makes a "9"), whether augmentation belongs in validation (no), and how to make it fast (do it on the GPU).

## 1. Overfitting, viewed as memorisation

A model with enough capacity can fit any fixed training set, including its noise and accidental details. After balancing, the nodule classifier saw each of roughly a thousand positive crops hundreds of times. It began to recognise *those specific crops*: their exact voxel patterns, the particular vessel passing nearby, the scanner noise. Training recall kept rising while validation recall and F1 fell: the textbook overfitting signature.

More data would help most, but labelled positives are expensive (each needs a radiologist). Augmentation is the next best thing: it multiplies the variety of the data we have, using our knowledge of which changes leave the label unchanged.

## 2. Choosing augmentations: what should not matter?

Every augmentation is a claim: "the correct answer is **invariant** to this change". Good choices come from the task:

| task | sensible | harmful |
|---|---|---|
| natural photos (cats, cars) | horizontal flip, crop and resize, small rotation, colour jitter | vertical flip (upside-down scenes are rare), heavy colour change when colour defines the class |
| digits and text | small rotation, slight shear, noise | flips (a "6" becomes a "9", a "b" a "d") |
| satellite or microscope images | flips and 90° rotations in any direction | changes in scale when physical size matters |
| CT nodules | flips along each axis, small shifts, rotations around the head-foot axis, mild scaling, noise | rotations that tilt slices (voxels are anisotropic), large scaling (nodule size matters for malignancy) |
| audio | time shift, small speed change, background noise, masking bands of a spectrogram | pitch shift when pitch is the label |

For the CT classifier, the book uses five augmentations on each candidate crop: **mirroring** along each axis, **shifting** by a few voxels, **scaling** slightly, **rotating** around the head-foot axis (only in-plane, because slices are farther apart than in-plane voxels, so tilting would mix resolutions), and adding **Gaussian noise**. Each is applied with random parameters every time a sample is fetched.

## 3. Implementing it: affine transforms

Flips, shifts, rotations and scalings are all **affine transformations**: each output position is a linear function of the input position plus an offset. They can be combined into one matrix and applied in a single resampling step. PyTorch provides `F.affine_grid`, which turns a matrix into a grid of sampling locations, and `F.grid_sample`, which reads the input at those locations (with interpolation), working on whole batches on the GPU:

```python
import math, random
import torch
import torch.nn.functional as F

def augment_crop(ct_t, flip=True, offset=0.1, scale=0.2, rotate=True, noise=25.0):
    """ct_t: (N, 1, D, H, W) float tensor of HU values. Returns a randomly transformed copy."""
    t = torch.eye(4)                                     # 4x4 homogeneous transform (x, y, z, 1)
    for i in range(3):
        if flip and random.random() > 0.5:
            t[i, i] *= -1                                # mirror along axis i
        t[i, 3] = offset * (random.random() * 2 - 1)     # shift: fraction of the half-width
        t[i, i] *= 1.0 + scale * (random.random() * 2 - 1)
    if rotate:
        a = random.random() * 2 * math.pi                # rotate in the x-y plane only
        rot = torch.tensor([[math.cos(a), -math.sin(a), 0, 0],
                            [math.sin(a),  math.cos(a), 0, 0],
                            [0, 0, 1, 0], [0, 0, 0, 1]])
        t = t @ rot
    grid = F.affine_grid(t[:3].unsqueeze(0).expand(ct_t.shape[0], -1, -1), ct_t.shape, align_corners=False)
    out = F.grid_sample(ct_t, grid, padding_mode="border", align_corners=False)
    return out + torch.randn_like(out) * noise          # Gaussian noise in HU
```

- `affine_grid` uses **normalised coordinates** from −1 to 1 across each axis, so a shift of 0.1 moves the content by 5% of the crop's width.
- `padding_mode="border"` repeats edge values when the transform pulls in positions from outside the crop, avoiding artificial black borders.
- Because these functions work on batched GPU tensors, the whole batch can be augmented on the GPU in one call. The book does this for the segmentation model by wrapping augmentation in an `nn.Module` that is called before the model, which is much faster than augmenting each sample in CPU workers. torchvision's `transforms.v2` classes also work on GPU tensors.

The NumPy demo below implements the same idea, a single matrix applied by looking up each output voxel's source position (nearest-neighbour instead of linear interpolation), and checks that flips and in-plane rotation keep a nodule-like blob intact.

```python-run
import numpy as np

rng = np.random.default_rng(0)

def affine_resample(vol, matrix, offset):
    """Nearest-neighbour version of affine_grid + grid_sample with border padding.
    Output voxel at position p (relative to the centre) reads input at matrix @ p + offset."""
    shape = np.array(vol.shape)
    centre = (shape - 1) / 2
    grid = np.stack(np.meshgrid(*[np.arange(n) for n in shape], indexing="ij"), axis=-1) - centre
    src = grid @ matrix.T + centre + offset
    src = np.clip(np.rint(src).astype(int), 0, shape - 1)     # border padding
    return vol[src[..., 0], src[..., 1], src[..., 2]]

def random_augment(vol):
    m = np.eye(3)
    for axis in range(3):
        if rng.random() < 0.5:
            m[axis, axis] = -1                                  # mirror
    a = rng.uniform(0, 2 * np.pi)                               # rotate around the slice axis only
    rot = np.array([[1, 0, 0], [0, np.cos(a), -np.sin(a)], [0, np.sin(a), np.cos(a)]])
    m = m @ rot
    shift = rng.uniform(-2, 2, size=3)                          # a couple of voxels
    out = affine_resample(vol, m, shift)
    return out + rng.normal(0, 25, out.shape), np.degrees(a)

# A crop with a bright ellipsoidal "nodule" slightly off-centre and a vessel-like line.
D, H, W = 16, 24, 24
z, y, x = np.ogrid[:D, :H, :W]
vol = np.full((D, H, W), -800.0)
vol[((z - 8) / 2.5) ** 2 + ((y - 12) / 4) ** 2 + ((x - 13) / 4) ** 2 <= 1] = 50.0
vol[:, 4, :] = 0.0                                              # a "vessel" along one row

for k in range(3):
    aug, angle = random_augment(vol)
    blob = aug > -300
    print(f"augmented copy {k}: rotated {angle:5.1f} deg, bright voxels {blob.sum():4d} "
          f"(original {int((vol > -300).sum())}), centre of brightness "
          f"{np.round(np.argwhere(aug > 25).mean(axis=0), 1)}")
```

Each augmented copy keeps a blob of similar size (counts vary a little because of nearest-neighbour rounding, the noise and the vessel line rotating with it) near the middle of the crop, while its exact voxels, orientation and position change. That is precisely the variety we want: the label "nodule" is still true, but memorising voxel patterns no longer works.

## 4. Does it work? A demonstration

Recall the fully connected classifier from [A first image classifier](#/lesson/deep-learning/image-classifier): trained on patterns that only appeared in the left half of the image, it scored about 50% (chance) when the same patterns appeared on the right. Fully connected layers have no built-in translation invariance, but augmentation can **teach** it. Here we train the same network twice, once plainly and once with random horizontal shifts, vertical flips and a little noise applied to every training batch.

```python-run
import numpy as np

rng = np.random.default_rng(0)
PLUS = np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]], float)
CROSS = np.array([[1, 0, 1], [0, 1, 0], [1, 0, 1]], float)

def make(n, cols):
    X = rng.normal(0, 0.2, (n, 12, 12)); y = rng.integers(0, 2, n)
    for i in range(n):
        r, c = rng.integers(0, 10), rng.choice(cols)
        X[i, r:r + 3, c:c + 3] += PLUS if y[i] == 0 else CROSS
    return X, y

X_tr, y_tr = make(2000, np.arange(0, 4))
X_val, y_val = make(500, np.arange(0, 4))
X_shift, y_shift = make(500, np.arange(6, 10))

def augment(batch):
    out = np.empty_like(batch)
    for i, img in enumerate(batch):
        img = np.roll(img, rng.integers(0, 7), axis=1)          # shift right by 0..6 columns
        if rng.random() < 0.5:
            img = img[::-1, :]                                   # vertical flip (both patterns are symmetric)
        out[i] = img + rng.normal(0, 0.05, img.shape)
    return out

def train(use_aug, epochs):
    r = np.random.default_rng(1)
    W1 = r.normal(0, np.sqrt(2 / 144), (144, 64)); b1 = np.zeros(64)
    W2 = r.normal(0, np.sqrt(1 / 64), (64, 2)); b2 = np.zeros(2)
    for _ in range(epochs):
        order = rng.permutation(len(X_tr))
        for s in range(0, len(order), 64):
            idx = order[s:s + 64]
            x, t = X_tr[idx], y_tr[idx]
            if use_aug:
                x = augment(x)                                   # a fresh random variant every time
            x = x.reshape(len(x), -1)
            z1 = x @ W1 + b1; h = np.maximum(z1, 0); logits = h @ W2 + b2
            p = np.exp(logits - logits.max(1, keepdims=True)); p /= p.sum(1, keepdims=True)
            p[np.arange(len(t)), t] -= 1; p /= len(t)
            gz = (p @ W2.T) * (z1 > 0)
            W2 -= 0.3 * h.T @ p; b2 -= 0.3 * p.sum(0); W1 -= 0.3 * x.T @ gz; b1 -= 0.3 * gz.sum(0)
    acc = lambda X, y: ((np.maximum(X.reshape(len(X), -1) @ W1 + b1, 0) @ W2 + b2).argmax(1) == y).mean()
    return acc(X_tr, y_tr), acc(X_val, y_val), acc(X_shift, y_shift)

for name, use_aug, epochs in [("no augmentation", False, 20), ("with augmentation", True, 40)]:
    tr, va, sh = train(use_aug, epochs)
    print(f"{name:18s} ({epochs} epochs)  train {tr:.3f}   validation {va:.3f}   shifted test {sh:.3f}")
```

**Reading the result**

- Without augmentation: perfect training accuracy, about 91% validation, and chance-level accuracy on shifted images: memorisation of positions.
- With augmentation: training accuracy is lower (the task got harder, which is the point), validation accuracy is in the high 80s and, crucially, accuracy on shifted images jumps from about 52% to about 87%. The network learned the patterns rather than their positions.
- Augmented training needed more epochs: each epoch shows harder, more varied examples. Expect slower convergence and budget for it.
- A convnet would get the shift invariance from its architecture; augmentation still helps it with rotations, scale, lighting and noise, which convolutions do not handle by themselves.

## 5. Augmentation in the CT project

Adding the augmentations one at a time and then all together, the book reports that each one helped and the combination helped most: validation F1 kept improving for longer instead of collapsing after a few epochs, and the gap between training and validation metrics shrank. Training metrics got *worse*, because the training task became harder, which is expected and fine.

General practice:

1. Add augmentations that encode true invariances first (flips, crops, small shifts).
2. Check visually that augmented samples still look like valid examples of their class.
3. Tune strength: too weak does nothing, too strong destroys the signal and causes underfitting.
4. Never augment validation or test data randomly; they must measure performance on real inputs.

## 6. The modern augmentation toolbox

- **torchvision.transforms.v2**: `RandomResizedCrop`, `RandomHorizontalFlip`, `RandomRotation`, `ColorJitter`, `RandomErasing` (blanks a random rectangle), and policies such as `RandAugment` and `TrivialAugmentWide` that pick random operations and strengths automatically. The v2 API also transforms bounding boxes and masks consistently with the image, which detection and segmentation need.
- **MixUp** (`v2.MixUp`): blend two images and their labels in the same proportion. **CutMix** (`v2.CutMix`): paste a patch from one image into another and mix labels by area. Both act on whole batches and are strong regularisers for classification.
- **Domain-specific**: SpecAugment for speech (mask time and frequency bands), elastic deformations for medical images, back-translation and token masking for text.
- **Test-time augmentation (TTA)**: at inference, average predictions over a few augmented versions of each input (for example, the image and its mirror). Often a small accuracy gain for a proportional increase in inference cost.
- **Where to run it**: CPU workers in the DataLoader for per-sample image decoding and cropping; GPU, batched, for heavy geometric or intensity transforms when CPU becomes the bottleneck.

> [!INTERVIEW]
> **"Which augmentations would you use for a defect-detection model on photos of circuit boards, and which would you avoid?"** Use those that match real variation: small shifts and rotations (boards are not perfectly aligned), brightness and contrast jitter (lighting), blur and noise (camera), flips only if the board layout's mirror image is still a plausible board and defects look the same. Avoid transforms that could erase or fabricate a defect (aggressive crops that cut out small defects, heavy blur that hides scratches, colour shifts if colour indicates the defect type). Verify by eye, and never augment the validation set.

## Summary

- Repeating a few positives many times leads to memorisation; augmentation shows a new variant each time.
- Every augmentation asserts an invariance; choose them from domain knowledge and avoid those that change the label.
- Flips, shifts, rotations and scalings combine into one affine matrix applied with `F.affine_grid` and `F.grid_sample`, efficiently on the GPU for whole batches.
- For CT nodules: mirroring, small shifts, mild scaling, in-plane rotation and noise; each helped and the combination helped most.
- Augmented training is harder and slower to converge; training metrics fall while generalisation improves.
- Modern tools: transforms.v2 (with boxes and masks), RandAugment, MixUp, CutMix, test-time augmentation.

## Glossary

- **Data augmentation**: random, label-preserving changes to training examples.
- **Invariance**: the correct output not changing under a transformation of the input.
- **Affine transformation**: a linear map plus an offset (flip, shift, rotation, scaling, shear).
- **Homogeneous coordinates**: adding a constant 1 so a shift can be written as matrix multiplication.
- **affine_grid / grid_sample**: PyTorch functions that build a sampling grid from a matrix / read an input at grid positions.
- **Normalised coordinates**: positions scaled to the range −1 to 1 across each axis.
- **Nearest-neighbour / linear interpolation**: reading the closest voxel / a distance-weighted blend of neighbours.
- **Gaussian noise**: random values from a normal distribution added to the input.
- **RandAugment / TrivialAugment**: automatic policies that sample augmentation operations and strengths.
- **MixUp / CutMix**: blending two images and labels / pasting a patch and mixing labels by area.
- **Random erasing**: blanking a random rectangle of the image.
- **Test-time augmentation (TTA)**: averaging predictions over augmented copies at inference.

## Check yourself

```quiz
[
  {"q": "Which augmentation is harmful for handwritten digit recognition?", "options": ["Flipping the image", "Rotating by a few degrees", "Adding slight noise", "Shifting by a pixel"], "answer": 0,
   "explain": "Flips can change the class (6 and 9) or create invalid digits."},
  {"q": "Why does the CT augmentation rotate only around the head-foot axis?", "options": ["Voxels are anisotropic, so tilting would mix the coarse slice spacing with the fine in-plane spacing", "3-D rotations are impossible in PyTorch", "Nodules are always vertical", "To save memory"], "answer": 0,
   "explain": "In-plane rotation keeps each slice's resolution consistent."},
  {"q": "Should validation data be randomly augmented?", "options": ["No: validation must measure performance on real, unaltered inputs", "Yes, always", "Only with flips", "Only for segmentation"], "answer": 0,
   "explain": "Random changes make validation noisy and unrepresentative; test-time augmentation is a deliberate, deterministic exception."},
  {"q": "After adding augmentation, training accuracy drops while validation improves. Is this a problem?", "options": ["No: the training task got harder, and generalisation improved", "Yes: augmentation is broken", "Yes: the learning rate must be raised", "Yes: the model is underfitting validation"], "answer": 0,
   "explain": "This shrinking gap is exactly the intended effect."},
  {"q": "What do F.affine_grid and F.grid_sample let you do?", "options": ["Apply a combined flip, shift, rotation and scaling to whole batches on the GPU", "Compute gradients of affine layers", "Load images from disk", "Normalise channels"], "answer": 0,
   "explain": "One matrix per sample produces a sampling grid; grid_sample interpolates the input at those positions."},
  {"q": "What does MixUp do?", "options": ["Blends two images and their labels with the same mixing weight", "Swaps the colour channels", "Mixes training and validation sets", "Averages model weights"], "answer": 0,
   "explain": "The soft labels match the blend proportion."},
  {"q": "In the demo, why did the augmented fully connected model handle shifted images while the plain one did not?", "options": ["Random shifts during training showed the patterns at many positions, teaching invariance", "Augmentation changed the architecture into a convnet", "The augmented model trained on the shifted test set", "Noise alone creates translation invariance"], "answer": 0,
   "explain": "Augmentation supplies through data the invariance a convnet gets from its structure."}
]
```

> **Source:** Stevens, Antiga & Viehmann, *Deep Learning with PyTorch*, ch. 12 (revisiting the problem of overfitting, preventing overfitting with data augmentation, specific techniques: mirroring, shifting, scaling, rotating, noise, seeing the improvement) and ch. 13 (augmenting on the GPU); PyTorch documentation, `F.affine_grid`, `F.grid_sample`; torchvision documentation, `transforms.v2`.
