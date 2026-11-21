# Tensors: creation, indexing, dtypes and broadcasting

> **Before this lesson:** read [What deep learning is and where PyTorch fits](#/lesson/deep-learning/why-deep-learning). You should be able to read a Python list and a `for` loop. NumPy arrays are explained here as we go; if you want a slower introduction to vectors and matrices, see [Linear algebra for ML](#/lesson/ml/linear-algebra).

## In plain words

A **tensor** is a block of numbers arranged in a grid with any number of directions. A single number is a tensor with zero directions; a list of numbers has one direction; a spreadsheet table has two (rows and columns); a colour photo has three (height, width and colour); a batch of colour photos has four. Each direction is called a **dimension** (or **axis**), the number of dimensions is the tensor's **rank**, and the list of sizes along each dimension is its **shape**.

Think of a hotel. A single room is a scalar. A corridor of rooms is a vector. A floor (corridors side by side) is a matrix. The whole building (floors stacked) is a 3-D tensor. A street of identical hotels is 4-D. To find a guest, you give one number per level: hotel, floor, corridor, room.

Every input, output, weight and gradient in deep learning is a tensor. PyTorch's `torch.Tensor` behaves almost exactly like a NumPy array, plus two abilities: it can live on a GPU, and it can record the operations applied to it so gradients can be computed. Why this matters for a job: most deep-learning bugs are **shape bugs**, and interviewers regularly ask "what is the shape of this result?" or "why did this addition silently produce a 1000 × 1000 matrix?". Fluency with tensors is the foundation for everything else.

## 1. Why not plain Python lists?

You could store an image as a list of lists of lists of integers. It would work, and it would be hopelessly slow:

- A Python list stores **pointers** to separate Python objects scattered around memory. Each number carries extra bookkeeping (its type, a reference count), so a list of a million floats uses several times the memory of the raw numbers.
- Adding two lists element by element runs a Python loop, which executes one interpreted instruction at a time.
- A tensor instead stores raw numbers **contiguously**, packed side by side in one block of memory, and its operations run as compiled C, C++ or CUDA code over the whole block at once. This is called **vectorisation**.

```python-run
import time
import numpy as np

n = 1_000_000
a_list, b_list = list(range(n)), list(range(n))
t0 = time.perf_counter()
c_list = [x + y for x, y in zip(a_list, b_list)]
t_list = time.perf_counter() - t0

a, b = np.arange(n, dtype=np.float32), np.arange(n, dtype=np.float32)
t0 = time.perf_counter()
c = a + b
t_vec = time.perf_counter() - t0

print(f"python list loop: {t_list * 1000:7.1f} ms")
print(f"vectorised add  : {t_vec * 1000:7.1f} ms   (about {t_list / max(t_vec, 1e-9):.0f}x faster)")
print("bytes per float32 element:", a.itemsize, "  total MB:", a.nbytes / 1e6)
```

The exact timings depend on your machine (and run slower in the browser), but the vectorised version is typically tens to hundreds of times faster. `itemsize` shows each float32 takes exactly 4 bytes. On a GPU the gap grows further because thousands of additions happen simultaneously.

## 2. Creating tensors

PyTorch offers the same constructors as NumPy, with nearly the same names:

```python
import torch

a = torch.tensor([[1.0, 2.0], [3.0, 4.0]])  # from nested lists; shape (2, 2), dtype float32
z = torch.zeros(3, 4)                       # all zeros, shape (3, 4)
o = torch.ones(2, 3, dtype=torch.int64)     # all ones, as 64-bit integers
r = torch.arange(0, 10, 2)                  # tensor([0, 2, 4, 6, 8])
u = torch.rand(2, 2)                        # uniform random numbers in [0, 1)
g = torch.randn(2, 2)                       # standard normal random numbers (mean 0, std 1)
f = torch.full((2, 2), 7.0)                 # every element 7.0
i = torch.eye(3)                            # 3 x 3 identity matrix
like = torch.zeros_like(a)                  # same shape and dtype as a, filled with zeros
a.shape, a.dtype, a.device, a.ndim          # torch.Size([2, 2]), torch.float32, device(type='cpu'), 2
```

- `torch.tensor(...)` copies data from a Python list (or NumPy array) into a new tensor. Note the lowercase `tensor`: it is a function that infers the type.
- `zeros`, `ones`, `rand`, `randn` and `full` take the shape as separate numbers or as a tuple.
- `dtype=` sets the **data type**, the kind of number stored (section 4).
- `.shape` (or `.size()`) is the shape; `.ndim` is the rank; `.device` says where the data lives (CPU or a GPU).
- `torch.manual_seed(0)` fixes the random number generator so random tensors are reproducible, the equivalent of NumPy's seeded generator.

## 3. Indexing and slicing

Indexing follows Python and NumPy rules. Counting starts at 0, negative indices count from the end, and a **slice** `start:stop:step` selects a range that includes `start` and excludes `stop`.

```python-run
import numpy as np

x = np.arange(24).reshape(2, 3, 4)   # 2 blocks, each 3 rows x 4 columns
print("shape:", x.shape)
print("x[1]          ->", x[1].shape, "  the second block")
print("x[1, 2]       ->", x[1, 2], "  row 2 of block 1")
print("x[1, 2, 3]    ->", x[1, 2, 3], "  a single element")
print("x[:, 0, :]    ->", x[:, 0, :].shape, "  row 0 of every block")
print("x[..., -1]    ->", x[..., -1], "  last column everywhere")
print("x[0, ::2]     ->", x[0, ::2].shape, "  every other row of block 0")
mask = x % 5 == 0
print("x[mask]       ->", x[mask], "  boolean mask picks matching elements (1-D result)")
print("x[0, [2, 0]]  ->", x[0, [2, 0]].shape, "  index with a list: rows 2 then 0")
print("x[None].shape ->", x[None].shape, "  None inserts a new axis of size 1")
```

**Reading the output**

- Each integer index removes one dimension; a slice keeps it. `x[1]` drops the first axis, leaving `(3, 4)`.
- `...` (ellipsis) means "all the remaining axes", so `x[..., -1]` takes the last column of every row of every block.
- A boolean **mask** of the same shape selects the elements where it is `True` and returns them as a flat 1-D array.
- Indexing with a list (called **advanced** or **fancy indexing**) picks specific positions in the order you list them, and returns a copy rather than a view (views are explained in the [next lesson](#/lesson/deep-learning/tensor-storage)).
- `None` inserts an axis of size 1; in PyTorch you would usually write `x.unsqueeze(0)`.

## 4. Data types

Every tensor has a single **dtype**, shared by all its elements. The ones you will meet:

| dtype | bits | typical use |
|---|---|---|
| `torch.float32` (`float`) | 32 | default for weights, activations and inputs |
| `torch.float64` (`double`) | 64 | rarely in deep learning; useful for gradient checking |
| `torch.float16` (`half`) | 16 | mixed-precision training and inference on GPUs |
| `torch.bfloat16` | 16 | mixed precision with float32's range, preferred on modern GPUs and TPUs |
| `torch.int64` (`long`) | 64 | class labels and indices; required by `CrossEntropyLoss` targets |
| `torch.uint8` | 8 | raw image pixels 0 to 255 |
| `torch.bool` | 8 | masks |

Key facts:

- **The default floating type is float32.** NumPy's default is float64, so `torch.from_numpy(np.array([0.5]))` gives a float64 tensor. Mixing float64 inputs with float32 weights raises a dtype mismatch error; convert with `.float()`.
- A float32 has about 7 significant decimal digits; float16 about 3 and a maximum value of 65,504; bfloat16 keeps float32's huge range (up to about $3.4 \times 10^{38}$) but only 2 to 3 significant digits. Why that trade-off suits training is covered in the [mixed precision lesson](#/lesson/deep-learning/memory-mixed-precision).
- Convert with `x.to(torch.float16)`, `x.float()`, `x.long()`, `x.bool()`.
- **Type promotion**: combining types picks a type that can hold both. An integer tensor plus a float tensor gives a float tensor. Integer division with `/` returns floats; use `//` for floor division.

```python-run
import numpy as np

labels = np.array([0, 2, 1])
print("default int dtype:", labels.dtype)
probs = np.array([0.1, 0.7, 0.2])
print("default float dtype in NumPy:", probs.dtype, "(PyTorch would use float32)")
print("int + float ->", (labels + probs).dtype)
with np.errstate(over="ignore"):
    big = np.float16(60000) * np.float16(2)
print("float16 overflow:", big, "  max float16 is", np.finfo(np.float16).max)
print("float32 digits:", np.finfo(np.float32).precision, " float16 digits:", np.finfo(np.float16).precision)
print("1 + 1e-8 in float32 == 1 ?", np.float32(1) + np.float32(1e-8) == np.float32(1))
```

The last line shows **rounding**: adding a number smaller than float32's precision to 1 changes nothing. Tiny effects like this explain why very small gradient updates can vanish in low precision.

## 5. The tensor API in one tour

PyTorch has hundreds of operations; they fall into a few families. Each exists as a function (`torch.sum(x)`) and usually as a method (`x.sum()`).

- **Element-wise maths**: `+ - * /`, `**`, `torch.exp`, `torch.log`, `torch.sqrt`, `torch.abs`, `torch.clamp(x, min, max)`. They apply to every element independently.
- **Reductions**: `sum`, `mean`, `max`, `min`, `argmax`, `std`, `prod`, `norm`. The `dim` argument chooses the axis to collapse; `keepdim=True` keeps it with size 1 so the result still broadcasts against the original.
- **Linear algebra**: `@` or `torch.matmul` for matrix multiplication, `torch.linalg.*` for inverses, norms and decompositions.
- **Shape changes**: `reshape`, `view`, `flatten`, `squeeze` (remove size-1 axes), `unsqueeze` (add one), `permute` (reorder axes), `transpose` (swap two), `expand` (stretch size-1 axes without copying).
- **Joining and splitting**: `torch.cat` joins along an existing axis; `torch.stack` creates a new axis; `split` and `chunk` cut a tensor into pieces.
- **Comparison and selection**: `==`, `>`, `torch.where(cond, a, b)`, `topk`, `sort`.
- **In-place versions** end with an underscore: `x.add_(1)`, `x.zero_()`, `x.clamp_(0, 1)`. They modify `x` instead of creating a new tensor. They save memory, but they can break gradient computation if autograd needs the old value, so use them sparingly in models.

```python-run
import numpy as np

scores = np.array([[1.0, 4.0, 2.0],
                   [3.0, 0.5, 5.0]])           # 2 examples x 3 classes
print("sum over everything:", scores.sum())
print("sum(dim=0):", scores.sum(axis=0), "  per class, shape", scores.sum(axis=0).shape)
print("sum(dim=1):", scores.sum(axis=1), "  per example")
print("sum(dim=1, keepdim=True) shape:", scores.sum(axis=1, keepdims=True).shape)
print("argmax(dim=1):", scores.argmax(axis=1), "  predicted class per example")
row_share = scores / scores.sum(axis=1, keepdims=True)
print("each row divided by its own total:\n", row_share.round(3))

a, b = np.ones((2, 3)), np.zeros((2, 3))
print("cat along dim 0:", np.concatenate([a, b], axis=0).shape, "  stack -> new dim:", np.stack([a, b]).shape)
```

`keepdim=True` (NumPy: `keepdims`) is the detail that makes `scores / scores.sum(axis=1, keepdims=True)` work: the row sums have shape `(2, 1)` and broadcast across the three columns. Without it they would have shape `(2,)`, and the division would try to align with the *columns*, which fails here and silently does the wrong thing when the sizes happen to match.

## 6. Broadcasting: the rule that saves and bites

**Broadcasting** lets you combine tensors of different shapes without copying data. The rule, applied by comparing shapes **from the rightmost dimension leftwards**:

1. If one tensor has fewer dimensions, pretend it has extra size-1 dimensions on the left.
2. Two sizes are compatible if they are equal or one of them is 1.
3. A size-1 dimension is stretched (virtually, without copying) to match the other.
4. If any pair is incompatible, the operation fails.

The result's size in each dimension is the larger of the two.

| shape A | shape B | result | why |
|---|---|---|---|
| `(32, 10)` | `(10,)` | `(32, 10)` | bias added to every row |
| `(3, 224, 224)` | `(3, 1, 1)` | `(3, 224, 224)` | per-channel mean subtracted |
| `(8, 1, 5)` | `(7, 1)` | `(8, 7, 5)` | both stretch |
| `(4,)` | `(4, 1)` | `(4, 4)` | the classic accidental outer product |
| `(3, 4)` | `(3,)` | error | rightmost sizes 4 and 3 clash |

The fourth row is the famous trap. Suppose predictions come out of a model with shape `(n, 1)` and your targets have shape `(n,)`. Computing `(pred - target) ** 2` silently gives an `(n, n)` matrix and the mean of that is a meaningless number. Training runs, the loss decreases a little, and the model learns nothing useful. PyTorch's `nn.MSELoss` prints a warning in exactly this case, but your own loss code will not.

```python-run
import numpy as np

def broadcast_shape(a, b):
    """Return the broadcast result shape, or raise ValueError, using the right-to-left rule."""
    result = []
    for i in range(1, max(len(a), len(b)) + 1):
        da = a[-i] if i <= len(a) else 1
        db = b[-i] if i <= len(b) else 1
        if da != db and 1 not in (da, db):
            raise ValueError(f"cannot broadcast {a} and {b}: sizes {da} and {db}")
        result.append(max(da, db))
    return tuple(reversed(result))

for a, b in [((32, 10), (10,)), ((3, 224, 224), (3, 1, 1)), ((8, 1, 5), (7, 1)), ((4,), (4, 1))]:
    mine = broadcast_shape(a, b)
    numpy_says = np.broadcast_shapes(a, b)
    print(f"{str(a):>14} + {str(b):<10} -> {mine}  (numpy agrees: {mine == numpy_says})")
try:
    broadcast_shape((3, 4), (3,))
except ValueError as e:
    print("error:", e)

pred = np.array([[1.0], [2.0], [3.0]])        # shape (3, 1), as a model often returns
target = np.array([1.0, 2.0, 3.0])            # shape (3,)
wrong = ((pred - target) ** 2).mean()
right = ((pred.squeeze(1) - target) ** 2).mean()
print("buggy loss (silent 3x3):", round(wrong, 4), "  correct loss:", right)
```

The demo implements the rule and checks it against NumPy's own `np.broadcast_shapes`. The final lines reproduce the trap: the "perfect" predictions should give loss 0, but the buggy version reports about 1.333 because it compared every prediction with every target. Squeezing the size-1 axis fixes it. You will implement this rule in the module problem "Broadcast result shape".

> [!TIP]
> Make shapes explicit. Assert them in code (`assert pred.shape == target.shape`), write the expected shape as a comment beside each line of a model, and print `x.shape` liberally while developing.

## 7. Naming dimensions: einsum

Code full of `transpose(1, 2)` and `sum(-1)` is hard to read because the reader must remember what each axis means. The source book experiments with PyTorch's **named tensors**, which attach names like `"channels"` to dimensions. That feature has stayed an experimental prototype and is rarely used in practice. Two tools are common instead:

- **`torch.einsum`** (Einstein summation) describes an operation with letters for axes. `torch.einsum("bik,bkj->bij", A, B)` is a batch of matrix multiplications: for every batch index `b`, multiply `A[b]` (i × k) by `B[b]` (k × j). Letters that appear in the inputs but not in the output are summed over.
- The third-party **einops** library offers readable reshapes such as `rearrange(x, "b c h w -> b (h w) c")`.

```python-run
import numpy as np

rng = np.random.default_rng(0)
img = rng.random((2, 3, 4, 4))                    # batch, channels, height, width
weights = np.array([0.299, 0.587, 0.114])         # red, green, blue contribution to brightness
gray = np.einsum("bchw,c->bhw", img, weights)     # weighted sum over the channel axis
print("grayscale batch:", gray.shape)
same = (img * weights[None, :, None, None]).sum(axis=1)
print("matches the broadcasting version:", np.allclose(gray, same))

A, B = rng.random((5, 2, 3)), rng.random((5, 3, 4))
print("batched matmul via einsum:", np.einsum("bik,bkj->bij", A, B).shape, " same as A @ B:", (A @ B).shape)
```

The grayscale conversion multiplies each channel by its weight and sums over channels; the einsum string documents that intent, and the broadcasting version gives the same answer.

> [!INTERVIEW]
> **"What is the shape of `torch.zeros(8, 1, 6) + torch.zeros(7, 1)`?"** Align from the right: `(8, 1, 6)` and `(1, 7, 1)`. Sizes pair as 6 with 1 → 6, 1 with 7 → 7, 8 with 1 → 8. Answer: `(8, 7, 6)`. Then say what goes wrong if you meant element-wise: nothing errors, so check shapes with assertions.

## Summary

- A tensor is an n-dimensional grid of numbers of one dtype; rank is the number of axes, shape lists their sizes.
- Tensors store raw numbers contiguously and run vectorised compiled code, which is why they are vastly faster than lists.
- Indexing follows NumPy: integers drop an axis, slices keep it, masks and lists select elements (and copy).
- float32 is the default float; labels are int64; float16 and bfloat16 trade precision for speed and memory.
- Reductions take `dim` and `keepdim`; in-place methods end in `_`.
- Broadcasting aligns shapes from the right, stretching size-1 axes; the `(n,)` versus `(n, 1)` mismatch is the classic silent bug.
- `einsum` makes multi-axis operations readable.

## Glossary

- **Tensor**: an n-dimensional array of numbers sharing one data type.
- **Dimension / axis**: one direction of a tensor.
- **Rank**: the number of dimensions.
- **Shape**: the size along each dimension.
- **Scalar / vector / matrix**: tensors of rank 0 / 1 / 2.
- **Contiguous**: stored as one unbroken block of memory in the expected order.
- **Vectorisation**: running an operation over a whole array in compiled code instead of a Python loop.
- **dtype (data type)**: the kind of number stored, such as float32 or int64.
- **Type promotion**: choosing a result dtype that can represent both inputs.
- **Slice**: a `start:stop:step` range selection.
- **Mask**: a boolean tensor used to select elements.
- **Advanced (fancy) indexing**: indexing with lists or tensors of positions.
- **Reduction**: an operation that collapses an axis, such as sum or max.
- **keepdim**: keeping a reduced axis with size 1.
- **In-place operation**: one that overwrites its input; named with a trailing underscore.
- **Broadcasting**: the rule for combining tensors of different shapes by stretching size-1 axes.
- **einsum**: a notation that names axes with letters and sums the ones missing from the output.

## Check yourself

```quiz
[
  {"q": "What is the shape of the result of adding tensors of shapes (5, 1, 4) and (3, 1)?", "options": ["(5, 3, 4)", "(5, 3, 1)", "Error", "(5, 1, 4)"], "answer": 0,
   "explain": "Pad (3, 1) to (1, 3, 1); then 4 with 1 → 4, 1 with 3 → 3, 5 with 1 → 5."},
  {"q": "pred has shape (100, 1) and target has shape (100,). What does (pred - target) produce?", "options": ["A (100, 100) tensor", "A (100,) tensor", "A (100, 1) tensor", "An error"], "answer": 0,
   "explain": "(100,) is treated as (1, 100); both size-1 axes stretch, producing an accidental outer difference."},
  {"q": "What is PyTorch's default floating-point dtype?", "options": ["float32", "float64", "float16", "bfloat16"], "answer": 0,
   "explain": "NumPy defaults to float64, which is why converting NumPy arrays often needs .float()."},
  {"q": "Which dtype should class labels passed to CrossEntropyLoss usually have?", "options": ["int64 (long)", "float32", "uint8", "bool"], "answer": 0,
   "explain": "Class-index targets must be integer indices; int64 is the standard."},
  {"q": "x has shape (2, 3, 4). What is the shape of x[:, 1]?", "options": ["(2, 4)", "(2, 1, 4)", "(3, 4)", "(2, 3)"], "answer": 0,
   "explain": "The integer index removes the second axis; the slice keeps the first; the last axis is untouched."},
  {"q": "Why use scores.sum(dim=1, keepdim=True) when normalising each row?", "options": ["The (n, 1) result broadcasts across columns correctly", "It is faster", "It changes the dtype to float64", "It sorts the rows"], "answer": 0,
   "explain": "Without keepdim the (n,) sums would align with the column axis instead of the rows."},
  {"q": "What does a trailing underscore, as in x.add_(1), mean?", "options": ["The operation modifies x in place", "The operation runs on the GPU", "The operation is private", "The operation is differentiable"], "answer": 0,
   "explain": "In-place ops overwrite the tensor; they can interfere with autograd if the old value is needed."},
  {"q": "In `torch.einsum('bik,bkj->bij', A, B)`, which letter is summed over?", "options": ["k", "b", "i", "j"], "answer": 0,
   "explain": "Letters present in the inputs but absent from the output are summed: this is a batched matrix multiplication."}
]
```

> **Source:** Stevens, Antiga & Viehmann, *Deep Learning with PyTorch*, ch. 3 (tensors as the world in floating-point numbers, indexing, named tensors, element types, the tensor API); PyTorch documentation, "Tensor attributes" and "Broadcasting semantics"; NumPy documentation on broadcasting.
