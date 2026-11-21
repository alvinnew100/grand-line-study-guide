# Under the hood: storage, strides, views and devices

> **Before this lesson:** you need shapes, indexing, dtypes and broadcasting from [Tensors: creation, indexing, dtypes and broadcasting](#/lesson/deep-learning/tensors-basics). Multiplying a few small whole numbers in your head is the only maths required.

## In plain words

A tensor looks like a grid, but computer memory is a single long row of numbered boxes. So every tensor is really two things: a flat block of numbers called the **storage**, and a small description that says how to read that block as a grid. The description holds the **shape**, a starting position called the **offset**, and the **strides**: for each dimension, how many boxes to jump in storage to move one step along that dimension.

Picture a cinema whose seats are numbered 0 to 99 in one long sequence, ten seats per row. To find "row 3, seat 4" you compute $3 \times 10 + 4 = 34$. The "10" is the stride for rows and "1" is the stride for seats. Now imagine reading the seating chart sideways (columns become rows): you do not move a single person, you only swap the strides to 1 and 10. That is exactly how PyTorch transposes a tensor instantly, without copying any data.

Why this matters for a job: understanding storage explains a whole family of surprising behaviours and error messages. Why did changing a slice change the original? Why does `view` complain that the tensor "is not contiguous"? Why did an innocent-looking `.T` make the next operation slower? Why does moving a tensor to the GPU take time? Interviewers use these questions to separate people who have read PyTorch code from people who have debugged it.

## 1. Storage: one flat block of numbers

When you create `torch.tensor([[1, 2, 3], [4, 5, 6]])`, PyTorch allocates one contiguous block holding `1 2 3 4 5 6` and a tensor object that describes it as 2 rows by 3 columns. Several tensor objects can share one storage, each describing a different "window" onto it. Such a window is called a **view**.

Operations that only change the description, never the numbers, return views. They are almost free, no matter how big the tensor is:

- slicing with ranges (`x[1:]`, `x[:, ::2]`), and indexing with a single integer (`x[0]`),
- `transpose`, `permute`, `t`, `mT`,
- `view`, `unsqueeze`, `squeeze`, `expand`, `narrow`, and `reshape` when no copy is needed.

Operations that compute new numbers allocate new storage: arithmetic (`x + 1`), reductions, `clone()`, indexing with a list or mask, and `contiguous()` on a non-contiguous tensor.

The consequence that surprises people: **writing through a view changes the original**.

```python
x = torch.tensor([[1, 2, 3], [4, 5, 6]])
row = x[1]          # a view of the second row
row[0] = 40         # writes into the shared storage
print(x)            # tensor([[ 1,  2,  3], [40,  5,  6]])
safe = x[1].clone() # an independent copy with its own storage
```

`clone()` makes a deep copy. Use it whenever you plan to modify a piece of a tensor without affecting the whole.

## 2. Offset, shape and stride

Three numbers describe how a view reads storage:

- **offset**: the storage position of the element at index `[0, 0, ...]` of the view,
- **shape**: the size of each dimension,
- **stride**: for each dimension, the number of storage positions to skip to move by one along it.

The storage position of the element at index $(i_0, i_1, \ldots)$ is

$$\text{position} = \text{offset} + \sum_k i_k \cdot \text{stride}_k$$

For a freshly created tensor of shape $(d_0, d_1, \ldots, d_{n-1})$, numbers are laid out **row-major**: the last index changes fastest. Its strides are the products of the sizes to the right: $\text{stride}_k = d_{k+1} \times d_{k+2} \times \cdots \times d_{n-1}$, and the last stride is 1. A tensor laid out this way is called **contiguous**.

| tensor | shape | stride | offset |
|---|---|---|---|
| `x` (fresh) | (2, 3) | (3, 1) | 0 |
| `x[1]` | (3,) | (1,) | 3 |
| `x[:, 1]` | (2,) | (3,) | 1 |
| `x.t()` | (3, 2) | (1, 3) | 0 |
| `x[:, ::2]` | (2, 2) | (3, 2) | 0 |

In PyTorch, `x.stride()` and `x.storage_offset()` show these values, and `x.is_contiguous()` reports whether the layout is row-major with no gaps. Note that PyTorch counts strides in **elements**, while NumPy's `.strides` counts **bytes** (so a float32 NumPy array of shape (2, 3) reports strides (12, 4)).

Let us build a miniature strided tensor in plain Python to see that the formula is the whole story.

```python-run
from math import prod

class StridedView:
    """A toy tensor: flat storage + offset + shape + stride, like torch.Tensor's metadata."""
    def __init__(self, storage, shape, stride=None, offset=0):
        self.storage, self.shape, self.offset = storage, tuple(shape), offset
        self.stride = tuple(stride) if stride else tuple(prod(shape[k + 1:]) for k in range(len(shape)))
    def position(self, idx):
        return self.offset + sum(i * s for i, s in zip(idx, self.stride))
    def __getitem__(self, idx):
        return self.storage[self.position(idx)]
    def select(self, dim, i):               # like x.select(dim, i) or x[i] for dim 0
        shape = self.shape[:dim] + self.shape[dim + 1:]
        stride = self.stride[:dim] + self.stride[dim + 1:]
        return StridedView(self.storage, shape, stride, self.offset + i * self.stride[dim])
    def transpose(self, d0, d1):            # swap two entries of shape and stride, no data moved
        sh, st = list(self.shape), list(self.stride)
        sh[d0], sh[d1], st[d0], st[d1] = sh[d1], sh[d0], st[d1], st[d0]
        return StridedView(self.storage, sh, st, self.offset)
    def is_contiguous(self):
        expected = tuple(prod(self.shape[k + 1:]) for k in range(len(self.shape)))
        return all(st == ex for st, ex, n in zip(self.stride, expected, self.shape) if n > 1)
    def tolist(self):
        if not self.shape:
            return self.storage[self.offset]
        return [self.select(0, i).tolist() for i in range(self.shape[0])]

storage = [1, 2, 3, 4, 5, 6]
x = StridedView(storage, (2, 3))
print("x       ", x.tolist(), " stride", x.stride, " contiguous", x.is_contiguous())
row = x.select(0, 1)
print("x[1]    ", row.tolist(), " offset", row.offset, " stride", row.stride)
xt = x.transpose(0, 1)
print("x.t()   ", xt.tolist(), " stride", xt.stride, " contiguous", xt.is_contiguous())
storage[3] = 40                          # modify the shared storage directly
print("after storage[3] = 40:  x =", x.tolist(), "  x.t() =", xt.tolist())
```

**Reading this code line by line**

- `StridedView` holds a reference to the same Python list `storage`; no numbers are ever copied.
- The default stride uses the row-major rule: for shape (2, 3) it is (3, 1).
- `select(0, 1)` (row 1) removes dimension 0 and moves the offset forward by `1 × 3 = 3`, giving a view that starts at the number 4.
- `transpose` swaps the shape and stride entries. The transposed view has stride (1, 3): moving down a row of the transposed tensor steps one position in storage, moving across a column steps three.
- `is_contiguous` is false for the transpose because its strides are not the row-major ones for its shape.
- Changing `storage[3]` changes what both `x` and its transpose show, because they are windows onto the same block.

## 3. Contiguity, view and reshape

Many fast kernels (the compiled routines that do the arithmetic) assume contiguous memory, and some operations require it:

- `x.view(new_shape)` reinterprets the same storage with a new shape. It **never copies**, so it only works when the requested shape can be expressed with strides over the existing layout. On a transposed tensor, `view(-1)` fails with an error telling you the tensor is not contiguous.
- `x.reshape(new_shape)` returns a view when possible and silently makes a contiguous copy otherwise. It is the safe default.
- `x.contiguous()` returns `x` itself if already contiguous, or a row-major copy otherwise.

```python
x = torch.arange(6).reshape(2, 3)
xt = x.t()                    # shape (3, 2), stride (1, 3), not contiguous
xt.view(-1)                   # RuntimeError: view size is not compatible with input tensor's size and stride ...
xt.reshape(-1)                # tensor([0, 3, 1, 4, 2, 5])  (a copy, in the transposed order)
xt.contiguous().view(-1)      # same values; now explicit about the copy
```

Why the order `0, 3, 1, 4, 2, 5`? Flattening always follows the *logical* row-major order of the view: first row of the transpose is column 0 of `x`, which is 0 and 3, and so on.

A related trick: `expand` stretches a size-1 dimension by giving it **stride 0**, so every index along it reads the same storage position. `torch.zeros(3, 1).expand(3, 1000)` uses no extra memory. This is how broadcasting works internally. Writing in place into an expanded tensor is an error, because many logical elements share one box.

```python-run
import numpy as np

x = np.arange(6, dtype=np.float32).reshape(2, 3)
print("numpy strides are in BYTES:", x.strides, "-> elements:", tuple(s // x.itemsize for s in x.strides))
xt = x.T
print("transpose strides (elements):", tuple(s // x.itemsize for s in xt.strides),
      " C-contiguous?", xt.flags["C_CONTIGUOUS"], " shares memory with x?", np.shares_memory(x, xt))
flat = np.ascontiguousarray(xt).reshape(-1)         # like xt.contiguous().view(-1)
print("flattened transpose:", flat)
stretched = np.broadcast_to(np.array([[1.0], [2.0], [3.0]]), (3, 1000))
print("expanded shape:", stretched.shape, " strides (bytes):", stretched.strides, " -> stride 0 on the stretched axis")
sl = x[:, ::2]
print("every other column:", sl.tolist(), " strides (elements):", tuple(s // 4 for s in sl.strides))
```

NumPy exposes the same machinery: `x.T` shares memory with `x`, is not C-contiguous ("C order" is NumPy's name for row-major), and `np.broadcast_to` creates a zero-stride view.

> [!TIP]
> Performance rule of thumb: a non-contiguous tensor is fine as input to most PyTorch operations, which handle arbitrary strides. But reading memory with large jumps is slower than reading it in order, so after a `permute` that will be followed by many operations (or before a `view`), call `.contiguous()` once.

## 4. In-place operations and autograd

In-place operations (`add_`, `mul_`, `relu_`, slicing assignment `x[0] = ...`) modify storage directly. They save memory, but they interact with gradient computation. During the forward pass, autograd may save a tensor because the backward pass needs its value (for example, the backward of `y = x * w` needs `x`). If you then overwrite `x` in place, the saved value is wrong. PyTorch tracks a **version counter** on each tensor and raises an error ("one of the variables needed for gradient computation has been modified by an inplace operation") instead of silently computing wrong gradients. Prefer out-of-place operations inside models unless memory is critical.

## 5. Devices: CPU and GPU

Every tensor lives on a **device**. The CPU uses the computer's main memory (RAM). A GPU has its own separate memory (VRAM), connected to the CPU by a bus called **PCIe**, which is much slower than the GPU's internal memory.

```python
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
x = torch.randn(1000, 1000)              # created on the CPU
x_gpu = x.to(device)                     # copy to the GPU (no-op if device is cpu)
y = x_gpu @ x_gpu                        # runs on the GPU
y_cpu = y.cpu()                          # copy back, e.g. to convert to NumPy or print
torch.randn(3, device=device)            # create directly on the device: no transfer
```

Rules worth memorising:

- **Operands must be on the same device.** `x_gpu + x` raises "Expected all tensors to be on the same device". The model's parameters and each batch must both be moved.
- `.to(device)` returns a new tensor (or the same one if already there); it does not move the original in place. For modules, `model.to(device)` moves parameters in place and returns the module.
- With several GPUs, devices are named `"cuda:0"`, `"cuda:1"` and so on.
- GPU operations are **asynchronous**: Python queues work and continues immediately. Calls that need a result on the CPU, such as `.item()`, `print`, or `.cpu()`, force Python to wait. Timing GPU code without `torch.cuda.synchronize()` measures only the queuing.
- Transfers are expensive relative to arithmetic. Move data once per batch, keep everything on the GPU during the step, and avoid calling `.item()` inside tight loops. Pinned memory and `non_blocking=True` let transfers overlap with computation, covered in the [DataLoader lesson](#/lesson/deep-learning/datasets-dataloaders).

## 6. NumPy interoperability

Converting between NumPy and PyTorch can be free or a copy:

| call | copies? | notes |
|---|---|---|
| `torch.from_numpy(a)` | no | shares memory; dtype preserved (float64 stays float64) |
| `torch.tensor(a)` | yes | always copies |
| `torch.as_tensor(a)` | no if possible | copies only when dtype or device must change |
| `t.numpy()` | no | CPU tensors only; shares memory |
| `t.detach().cpu().numpy()` | maybe | the standard idiom for a GPU tensor that requires gradients |

`detach()` returns a view that is cut off from gradient tracking; NumPy knows nothing about autograd, so PyTorch refuses to convert a tensor that requires gradients without it. Because `from_numpy` and `.numpy()` share memory, modifying one changes the other.

## 7. Saving tensors to disk

- `torch.save(obj, "file.pt")` writes tensors, or dictionaries and lists of tensors, using Python's pickle format plus a compact tensor encoding. `torch.load("file.pt", map_location="cpu")` reads them back; `map_location` lets you load GPU-saved tensors on a machine without a GPU. Since PyTorch 2.6 `torch.load` defaults to `weights_only=True`, which refuses arbitrary Python objects for safety.
- **safetensors** (`safetensors.torch.save_file(dict_of_tensors, "model.safetensors")`) stores raw tensors with a small header. It cannot execute code, supports memory mapping (reading only the parts you touch), and is the preferred format for sharing weights.
- **HDF5** (through the `h5py` library) stores large named arrays on disk with compression and lets you read slices without loading everything, which is useful for big scientific datasets. The source book uses it for this purpose.
- When saving a view, `torch.save` stores the whole underlying storage. Saving `big[0:10]` of a huge tensor writes the huge tensor. Call `.clone()` first to save only the slice.

> [!INTERVIEW]
> **"What is the difference between `view` and `reshape`?"** Both return a tensor with a new shape. `view` never copies and therefore requires a stride-compatible (typically contiguous) input, raising an error otherwise; `reshape` returns a view when it can and copies when it must. Then add the follow-up they want to hear: `transpose` and `permute` only swap strides, which is why a `view` right after them fails, and why calling `.contiguous()` is the fix.

## Summary

- A tensor is flat storage plus metadata: offset, shape and stride. Position = offset + Σ index × stride.
- Slicing, transpose, permute, view and expand return views that share storage; writing through a view changes the original. Use `clone()` for an independent copy.
- Contiguous means row-major with the standard strides. `view` needs a compatible layout; `reshape` copies when necessary; `contiguous()` forces a row-major copy.
- `expand` and broadcasting use stride 0.
- In-place writes can invalidate values saved for backward; PyTorch detects this with version counters.
- Tensors live on a device; operands must share it; GPU calls are asynchronous; transfers are costly.
- `from_numpy` and `.numpy()` share memory; `torch.save` pickles, safetensors is the safe format, and saving a view writes its whole storage.

## Glossary

- **Storage**: the flat block of memory holding a tensor's numbers.
- **View**: a tensor that shares another tensor's storage with different metadata.
- **Offset**: the storage position of a view's first element.
- **Stride**: per dimension, how many storage positions to skip to move one step.
- **Row-major (C order)**: layout where the last index varies fastest.
- **Contiguous**: stored in row-major order with no gaps.
- **Kernel**: a compiled routine that performs an operation on a device.
- **clone**: an operation returning a copy with new storage.
- **Version counter**: a per-tensor count of in-place modifications, used by autograd to detect stale saved values.
- **Device**: where a tensor's memory lives (CPU or a specific GPU).
- **VRAM**: a GPU's own memory.
- **PCIe**: the bus connecting CPU and GPU.
- **Asynchronous execution**: queuing GPU work and continuing without waiting for it.
- **detach**: a view of a tensor excluded from gradient tracking.
- **map_location**: the `torch.load` option choosing where loaded tensors go.
- **safetensors / HDF5**: a safe raw-tensor file format / a format for large arrays with partial reads.

## Check yourself

```quiz
[
  {"q": "A contiguous tensor has shape (4, 5, 6). What is its stride?", "options": ["(30, 6, 1)", "(1, 4, 20)", "(6, 5, 4)", "(120, 30, 6)"], "answer": 0,
   "explain": "Each stride is the product of the sizes to its right: 5 × 6 = 30, then 6, then 1."},
  {"q": "x is contiguous with shape (2, 3). What are the shape and stride of x.t()?", "options": ["shape (3, 2), stride (1, 3)", "shape (3, 2), stride (2, 1)", "shape (2, 3), stride (1, 2)", "shape (3, 2), stride (3, 1)"], "answer": 0,
   "explain": "Transposing swaps both shape and stride entries; no data moves."},
  {"q": "Why does x.t().view(-1) raise an error?", "options": ["The transpose is not contiguous, and view never copies", "view only works on GPU tensors", "-1 is not allowed in view", "Transposed tensors have no storage"], "answer": 0,
   "explain": "Use reshape(-1) or contiguous().view(-1)."},
  {"q": "row = x[1]; row[0] = 99. What happens to x?", "options": ["x[1, 0] becomes 99 because row is a view", "Nothing; row is a copy", "An error is raised", "Only row changes until you call sync()"], "answer": 0,
   "explain": "Integer indexing and slicing return views sharing storage; use clone() for an independent copy."},
  {"q": "What stride does torch.zeros(3, 1).expand(3, 1000) have along the expanded dimension?", "options": ["0", "1", "1000", "3"], "answer": 0,
   "explain": "A zero stride makes every index read the same element, so no memory is allocated."},
  {"q": "You time a GPU matrix multiplication with time.time() before and after and get 0.05 ms for a huge matrix. Why is this misleading?", "options": ["GPU calls are asynchronous; you measured queuing, not computation", "The GPU cached the result", "time.time() is in seconds", "PyTorch runs matmul on the CPU"], "answer": 0,
   "explain": "Call torch.cuda.synchronize() before reading the clock, or use the profiler."},
  {"q": "Which conversion shares memory with the NumPy array a?", "options": ["torch.from_numpy(a)", "torch.tensor(a)", "torch.tensor(a.tolist())", "torch.tensor(a).clone()"], "answer": 0,
   "explain": "from_numpy wraps the same buffer; torch.tensor always copies."},
  {"q": "You save big[:10] where big has a billion elements. What gets written?", "options": ["The whole underlying storage of big", "Only the 10 rows", "Nothing; views cannot be saved", "A compressed diff"], "answer": 0,
   "explain": "torch.save keeps view relationships by saving the storage; clone() first to save only the slice."}
]
```

> **Source:** Stevens, Antiga & Viehmann, *Deep Learning with PyTorch*, ch. 3 (storage, in-place operations, size, offset and stride, transposing without copying, contiguous tensors, moving to the GPU, NumPy interoperability, serialisation and HDF5); PyTorch documentation, "Tensor Views" and `torch.load`.
