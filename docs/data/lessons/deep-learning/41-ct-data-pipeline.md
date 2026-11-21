# From raw CT files to a Dataset

> **Before this lesson:** read [Planning a large project](#/lesson/deep-learning/ct-project-plan) for the CT vocabulary (voxel, slice, Hounsfield units, candidates) and the five-step plan. You need the Dataset protocol from [Dataset, transforms and DataLoader](#/lesson/deep-learning/datasets-dataloaders) and group-wise splits from [Optimisers and validation](#/lesson/deep-learning/optimizers-validation). A **matrix-vector product** (multiplying a 3 × 3 grid of numbers by a list of 3 numbers) is used for coordinate conversion and explained below.

## In plain words

The first step of every real project is turning raw files into the tensors a model expects. For the CT project that means: read each scan's 3-D voxel array and its metadata, read two spreadsheets of candidate locations and radiologist annotations and merge them, clean the density values, convert positions from millimetres in the patient's body to row-and-column indexes in the array, cut out a small 3-D box around each candidate, and wrap all of it in a PyTorch `Dataset` with a sensible training/validation split and caching so it is fast.

Think of a museum receiving a crate of artefacts with a handwritten catalogue. Before anyone can study them, someone must unpack each item, match it to its catalogue entry, measure it in consistent units, note where in the storeroom it lives, and photograph it so researchers do not have to dig through the crate again. That unglamorous work decides whether the research is right.

Why it matters for a job: most of an applied ML engineer's time goes into data pipelines, and the costliest bugs live there: swapped axes, wrong units, a leaky split, a slow loader starving the GPU. Interviewers probe this with questions like "how do you split medical data?", "how would you cache expensive preprocessing?" and "how do you verify a coordinate transform?".

## 1. Reading a scan

LUNA scans come as a pair of files per scan: a small text header (`.mhd`, MetaImage format) listing the array size, data type and geometry, and a binary file (`.raw`) holding the voxels. Each scan is identified by a long **series UID** (unique identifier) string. The **SimpleITK** library reads them:

```python
import SimpleITK as sitk
import numpy as np

image = sitk.ReadImage(f"data/subset0/{series_uid}.mhd")
ct_a = np.array(sitk.GetArrayFromImage(image), dtype=np.float32)   # shape (slices, rows, cols)
origin_xyz = np.array(image.GetOrigin())          # millimetre position of voxel (0, 0, 0)
spacing_xyz = np.array(image.GetSpacing())        # millimetres per voxel along x, y, z
direction = np.array(image.GetDirection()).reshape(3, 3)   # orientation of the voxel axes
```

Note the axis order. The NumPy array is indexed **(index, row, column)**, called **IRC**: slice first, then row, then column. The metadata is given in **(x, y, z)** order, the reverse. Mixing the two orders is the single most common bug in medical imaging code, so the project names every variable with an `_irc` or `_xyz` suffix.

## 2. Cleaning densities: Hounsfield units

Voxel values are in **Hounsfield units (HU)**: air about −1000, fat around −100, water 0, soft tissue around +40, bone several hundred to over 1,000, and metal implants far higher. Two facts about the raw values:

- Anything below about −1000 is outside the patient (air around the body, or scanner padding values), and differences there carry no information.
- Very dense material (bone, metal, contrast agent) produces extreme values that are irrelevant to lung nodules but would dominate the input scale.

The simple fix is **clipping** to a window, here −1000 to +1000 HU, applied once when the scan is loaded:

```python
ct_a.clip(-1000, 1000, out=ct_a)     # in place: values below -1000 become -1000, above 1000 become 1000
```

Clipping keeps the range where lung tissue, nodules and vessels live, and bounds the scale for the network (the model can still be helped by dividing by 1000 or by a normalisation layer at its input). Radiologists do the same thing visually with "window" settings.

## 3. Parsing and merging the annotation files

Two CSV files describe what is in each scan:

- `candidates.csv`: series UID, centre (x, y, z) in millimetres, and a 0/1 nodule flag, for every candidate, about 551,000 rows.
- `annotations.csv`: series UID, centre, and **diameter in millimetres** for each radiologist-marked nodule, about 1,200 rows.

We want one list of candidates, each with its label and (for nodules) its diameter. The centres in the two files do not match exactly, because they came from different processes, so we match each nodule candidate to an annotation in the same scan whose centre is close relative to the nodule's size. Candidates with no matching annotation get diameter 0.

```python
from collections import namedtuple, defaultdict
import csv, functools

CandidateInfo = namedtuple("CandidateInfo", "is_nodule diameter_mm series_uid center_xyz")

@functools.lru_cache(maxsize=1)                     # parse the CSVs once per process
def get_candidate_info_list():
    diameters = defaultdict(list)
    for row in csv.DictReader(open("data/annotations.csv")):
        center = tuple(float(row[k]) for k in ("coordX", "coordY", "coordZ"))
        diameters[row["seriesuid"]].append((center, float(row["diameter_mm"])))
    out = []
    for row in csv.DictReader(open("data/candidates.csv")):
        uid = row["seriesuid"]
        center = tuple(float(row[k]) for k in ("coordX", "coordY", "coordZ"))
        diameter = 0.0
        for ann_center, ann_d in diameters[uid]:
            if all(abs(c - a) <= ann_d / 4 for c, a in zip(center, ann_center)):   # close enough
                diameter = ann_d
                break
        out.append(CandidateInfo(bool(int(row["class"])), diameter, uid, center))
    out.sort(reverse=True)                          # nodules first, then by size: handy for sampling
    return out
```

- A **namedtuple** is a lightweight immutable record with named fields; tuples sort field by field, so sorting puts nodules first and larger diameters first.
- `functools.lru_cache` memoises the function (remembers its result), so the expensive parse happens once per process.

## 4. Millimetres to voxels

Candidate positions are given in the **patient coordinate system**: millimetres, with axes defined relative to the patient's body (in DICOM convention, x increases towards the patient's left, y towards the back, z towards the head). To crop the array we need **voxel indices (I, R, C)**. The conversion uses the scan's metadata:

1. Flip IRC to CRI so the order matches x, y, z.
2. Multiply by the voxel spacing to get millimetre offsets along the voxel axes.
3. Rotate those offsets into patient axes with the **direction matrix** (a 3 × 3 matrix whose columns say which patient direction each voxel axis points along; for most scans it is the identity, sometimes with a sign flip).
4. Add the origin.

$$\text{xyz} = \text{origin} + D \cdot (\text{cri} \odot \text{spacing})$$

where $\odot$ is element-wise multiplication. A **matrix-vector product** $D \cdot v$ computes three weighted sums: output component $i$ is $\sum_j D_{ij} v_j$. Going back, from millimetres to voxels, inverts each step and rounds to whole indices:

$$\text{cri} = \text{round}\left( \frac{D^{-1} (\text{xyz} - \text{origin})}{\text{spacing}} \right), \qquad \text{irc} = \text{reverse}(\text{cri})$$

```python-run
import numpy as np

def irc2xyz(irc, origin_xyz, spacing_xyz, direction):
    cri = np.array(irc, dtype=float)[::-1]                 # IRC -> CRI (same order as XYZ)
    return origin_xyz + direction @ (cri * spacing_xyz)

def xyz2irc(xyz, origin_xyz, spacing_xyz, direction):
    cri = (np.linalg.inv(direction) @ (np.array(xyz) - origin_xyz)) / spacing_xyz
    return tuple(int(v) for v in np.round(cri)[::-1])

origin = np.array([-195.3, -170.0, -334.5])                # made-up metadata for one scan
spacing = np.array([0.703, 0.703, 2.5])                    # x, y in-plane; z between slices
direction = np.diag([1.0, 1.0, 1.0])

irc = (57, 260, 301)
xyz = irc2xyz(irc, origin, spacing, direction)
print("voxel", irc, "-> patient mm", xyz.round(2))
print("and back:", xyz2irc(xyz, origin, spacing, direction))

flipped = np.diag([1.0, -1.0, 1.0])                        # a scan stored with the y axis reversed
xyz_f = irc2xyz(irc, origin, spacing, flipped)
print("with a flipped y axis -> mm", xyz_f.round(2), " back:", xyz2irc(xyz_f, origin, spacing, flipped))

rng = np.random.default_rng(0)
ok = all(xyz2irc(irc2xyz(v, origin, spacing, flipped), origin, spacing, flipped) == tuple(v)
         for v in rng.integers(0, 500, size=(1000, 3)))
print("1,000 random round trips exact:", ok)
```

**Reading this code line by line**

- `[::-1]` reverses IRC to CRI so the components line up with x, y and z.
- `cri * spacing_xyz` converts voxel steps to millimetres along each voxel axis; `direction @ ...` rotates or flips them into patient axes; adding the origin positions them.
- The inverse undoes each step in reverse order and rounds, since indices are whole numbers.
- The round-trip test on 1,000 random voxels is the kind of check you should always write for a coordinate transform: cheap, and it catches swapped axes or a missing flip immediately.

## 5. Cropping a candidate

The classifier does not see whole scans; it sees a small box around each candidate. The project uses a box of **32 slices × 48 rows × 48 columns**. Fewer slices than rows or columns compensates for the larger slice spacing, so the box is closer to a cube in millimetres (about 80 × 34 × 34 mm with the spacing above, still taller than wide).

Near the edge of the scan a centred box would run off the array. The usual fix is to **shift the box** back inside the volume rather than pad it, so every crop has the same size and contains only real data:

```python-run
import numpy as np

def get_raw_candidate(ct_a, center_irc, width_irc=(32, 48, 48)):
    """Crop a box of size width_irc around center_irc, shifting it to stay inside the volume."""
    slices = []
    for axis, (c, w) in enumerate(zip(center_irc, width_irc)):
        start = int(round(c - w / 2))
        start = max(0, min(start, ct_a.shape[axis] - w))      # clamp so the box fits
        slices.append(slice(start, start + w))
    return ct_a[tuple(slices)], tuple(s.start for s in slices)

rng = np.random.default_rng(1)
ct_a = rng.normal(-600, 300, size=(120, 256, 256)).astype(np.float32)   # fake HU values
ct_a[60:64, 100:106, 100:106] = 40.0                                     # a small dense blob
ct_a.clip(-1000, 1000, out=ct_a)
print("value range after clipping:", ct_a.min(), ct_a.max())

for center in [(62, 103, 103), (2, 5, 250), (119, 255, 0)]:
    chunk, start = get_raw_candidate(ct_a, center)
    print(f"center {center} -> chunk {chunk.shape} starting at {start}")

chunk, _ = get_raw_candidate(ct_a, (62, 103, 103))
tensor_like = chunk[None]                                  # add the channel axis: (1, 32, 48, 48)
print("model input per candidate:", tensor_like.shape, " mean HU in the box: %.1f" % chunk.mean())
```

The first candidate is well inside the scan; the second and third sit at corners, and their boxes are shifted so they still have the full shape. Adding a channel axis gives `(1, 32, 48, 48)`, and a batch becomes `(N, 1, 32, 48, 48)`: the input of a 3-D convolution.

## 6. The Dataset

Putting it together:

```python
import torch
from torch.utils.data import Dataset

class LunaDataset(Dataset):
    def __init__(self, val_stride=10, is_val=False, series_uid=None):
        infos = list(get_candidate_info_list())
        uids = sorted({c.series_uid for c in infos})
        val_uids = set(uids[::val_stride])                    # every 10th scan goes to validation
        keep = val_uids if is_val else set(uids) - val_uids
        self.infos = [c for c in infos if c.series_uid in keep]

    def __len__(self):
        return len(self.infos)

    def __getitem__(self, i):
        info = self.infos[i]
        chunk, center_irc = get_ct_raw_candidate(info.series_uid, info.center_xyz, (32, 48, 48))
        x = torch.from_numpy(chunk).unsqueeze(0).to(torch.float32)     # (1, 32, 48, 48)
        y = torch.tensor(int(info.is_nodule), dtype=torch.long)          # class index 0 or 1
        return x, y, info.series_uid, torch.tensor(center_irc)
```

Design points:

- **Split by scan, not by candidate.** Neighbouring candidates in one scan overlap and share anatomy. If some go to training and others to validation, validation measures memorisation of that patient. Every candidate of a given series UID must land on the same side. (The book's first version strides over the candidate list and later moves to splitting by series; splitting by scan from the start is the safe habit.) Use a fixed rule or seed so the split is identical across runs.
- **Return extra fields** (series UID, centre) alongside the tensor; they are invaluable for debugging specific mistakes and for logging which candidates the model gets wrong.
- **Labels as class indices** for `CrossEntropyLoss` (the book uses a two-element one-hot tensor; either works with the matching loss).

## 7. Caching: making epochs fast

Loading and decompressing a full scan takes on the order of a second; cropping from a loaded scan is nearly instant. An epoch touches hundreds of thousands of candidates spread across hundreds of scans, so naive loading would spend hours per epoch reading the same files. Two layers of caching fix this:

- **In memory**: `functools.lru_cache(maxsize=1)` on a `get_ct(series_uid)` function keeps the most recent scan, so consecutive candidates from the same scan reuse it (sorting or grouping samples by scan makes this effective).
- **On disk**: cache each candidate's crop the first time it is computed (the book uses the `diskcache` library), so later epochs read small arrays instead of whole scans. A one-time "prep cache" script can fill the cache using many DataLoader workers before training starts.

Remember that a cache keyed on parameters must be invalidated whenever preprocessing changes (a different clip window, crop size or resampling), or you will silently train on stale data. Include a version string in the cache key.

## 8. Look at your data

Before training, render a few crops as images: the centre slice of a positive candidate should show a round bright blob; a negative might show a vessel, a bit of chest wall or nothing. Also render whole slices with the candidate centre marked. Many bugs (IRC versus XYZ swapped, a flipped axis, clipping applied twice) are invisible in loss curves and obvious in a picture.

> [!INTERVIEW]
> **"How would you split a medical-imaging dataset into training and validation sets?"** By patient (or scan, or study), never by image or crop, because samples from one patient are strongly correlated and a random split leaks patient-specific features into validation. Keep the split deterministic (hash of the patient id or a fixed seed), stratify so both sides have similar positive rates, and keep a held-out test set from a different time period or hospital if possible to check generalisation across scanners. Mention checking for duplicate scans of the same patient under different ids.

## Summary

- MetaImage `.mhd`/`.raw` scans are read with SimpleITK into (index, row, column) arrays plus origin, spacing and direction metadata given in (x, y, z) order.
- Clip Hounsfield units to about −1000 to +1000 to remove irrelevant extremes.
- Merge candidates with annotations by matching nearby centres within a scan; sort and cache the parsed list.
- Convert between patient millimetres and voxel indices with origin, spacing and the direction matrix; verify with round-trip tests.
- Crop fixed-size boxes (32 × 48 × 48) around candidates, shifting them inside the volume; add a channel axis.
- Split by scan or patient, return debugging metadata, cache scans in memory and crops on disk, and look at the data.

## Glossary

- **MetaImage (.mhd/.raw)**: a medical image format with a text header and a binary voxel file.
- **Series UID**: the unique identifier of one CT series (scan).
- **SimpleITK**: a library for reading and processing medical images.
- **IRC / XYZ**: voxel (index, row, column) order / patient (x, y, z) millimetre order.
- **Clipping (windowing)**: limiting values to a range.
- **namedtuple**: a lightweight immutable record with named fields.
- **Memoisation (lru_cache)**: storing a function's results to reuse them.
- **Patient coordinate system**: millimetre coordinates relative to the patient's body.
- **Origin / spacing / direction matrix**: position of voxel (0,0,0) / millimetres per voxel / orientation of voxel axes.
- **Matrix-vector product**: weighted sums of a vector's components using a matrix's rows.
- **Crop (chunk)**: a sub-box of a volume around a point.
- **Disk cache**: storing computed results on disk for reuse across runs.
- **Cache invalidation**: discarding cached results when the computation that produced them changes.

## Check yourself

```quiz
[
  {"q": "SimpleITK returns an array indexed as (slice, row, column). In what order is the spacing metadata given?", "options": ["(x, y, z), the reverse order", "(slice, row, column)", "(row, column, slice)", "Spacing has no order"], "answer": 0,
   "explain": "Flip between IRC and CRI/XYZ explicitly and name variables with their order."},
  {"q": "Why clip CT values to roughly −1000..1000 HU?", "options": ["To remove irrelevant extremes (outside air, bone, metal) and bound the input scale", "To convert them to probabilities", "Because PyTorch cannot store larger numbers", "To make the scan smaller on disk"], "answer": 0,
   "explain": "Lung tissue, nodules and vessels live within that range."},
  {"q": "Converting a voxel index to patient millimetres requires…", "options": ["Origin, voxel spacing and the direction matrix", "Only the voxel spacing", "Only the origin", "The diameter of the nodule"], "answer": 0,
   "explain": "xyz = origin + direction · (cri ⊙ spacing)."},
  {"q": "Why is the crop 32 × 48 × 48 rather than a cube of voxels?", "options": ["Slices are farther apart than in-plane voxels, so fewer slices cover a similar physical extent", "3-D convolutions require it", "To save disk space only", "Because nodules are flat"], "answer": 0,
   "explain": "Anisotropic spacing: millimetres, not voxel counts, describe the anatomy."},
  {"q": "What should happen when a candidate lies near the edge of the scan?", "options": ["Shift the crop window to stay inside the volume so its size is unchanged", "Drop the candidate", "Return a smaller crop", "Wrap around to the opposite edge"], "answer": 0,
   "explain": "Constant crop sizes let crops batch together."},
  {"q": "Why must the training/validation split be done by scan rather than by candidate?", "options": ["Candidates from one scan are correlated, so splitting them leaks patient-specific information", "Scans are easier to count", "Candidates have no labels", "PyTorch requires it"], "answer": 0,
   "explain": "Validation would reward recognising the patient rather than nodules."},
  {"q": "You change the clipping window but training still sees the old values. A likely cause?", "options": ["A stale disk cache keyed without a preprocessing version", "The DataLoader shuffle", "The optimizer state", "Dropout"], "answer": 0,
   "explain": "Include preprocessing parameters or a version in cache keys."}
]
```

> **Source:** Stevens, Antiga & Viehmann, *Deep Learning with PyTorch*, ch. 10 (raw CT data files, parsing LUNA's annotation data, unifying annotation and candidate data, loading individual CT scans, Hounsfield units, the patient coordinate system, converting between millimetres and voxel addresses, extracting a nodule, caching, constructing the dataset and its training/validation split, rendering the data); SimpleITK documentation.
