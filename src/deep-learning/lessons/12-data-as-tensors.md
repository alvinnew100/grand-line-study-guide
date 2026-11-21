# Real-world data as tensors: images, tables, time series, text

> **Before this lesson:** you need shapes, indexing, dtypes, reductions and broadcasting from [Tensors: creation, indexing, dtypes and broadcasting](#/lesson/deep-learning/tensors-basics), and views and `permute` from [storage, strides, views and devices](#/lesson/deep-learning/tensor-storage). Mean and standard deviation are re-explained below.

## In plain words

A neural network only understands tensors of floating-point numbers. The real world gives us JPEG files, spreadsheets, sensor logs and sentences. The first job of every project is translation: deciding which numbers represent each piece of data, in which shape, and on what scale. This step is called **data representation** or **encoding**, and it has more influence on the result than most choices of architecture.

Think of it like preparing ingredients for a professional kitchen. The chef (the model) is skilled but only accepts ingredients washed, cut to a standard size and laid out in a standard tray. Hand the chef a whole unwashed cabbage and the dish fails, no matter how good the chef is.

Why it matters for a job: interviewers love "how would you feed this data into a network?" questions, and in real teams most bugs and most quality wins live in the data pipeline: wrong channel order, unscaled columns, categories encoded as meaningless integers, or time steps in the wrong axis. This lesson gives you a standard recipe for each common kind of data.

## 1. Two ideas used everywhere

**Standardisation.** Networks train best when every input feature has a similar scale, centred near zero. For a feature with mean $\mu$ (the average) and standard deviation $\sigma$ (the typical distance from the average), we replace each value $x$ by

$$x' = \frac{x - \mu}{\sigma}$$

so the feature ends up with mean 0 and standard deviation 1. The reason is mechanical: gradient descent uses one learning rate for all weights, and if one input is in the thousands while another is between 0 and 1, the weights attached to them need wildly different step sizes. Compute $\mu$ and $\sigma$ **on the training data only** and reuse them for validation, test and production inputs; computing them on everything leaks information from the test set (see [data leakage](#/lesson/ml/columntransformer-leakage)).

**One-hot encoding.** A **categorical** feature takes one of a fixed set of values with no natural order, such as a city or a colour. Encoding "Singapore = 0, Kuala Lumpur = 1, Jakarta = 2" as a single number tells the network that Jakarta is "twice" Kuala Lumpur, which is nonsense. Instead, a **one-hot** vector has one position per category, with a 1 in the position of the actual value and 0 elsewhere: Kuala Lumpur becomes `[0, 1, 0]`. For categories with thousands of values (words, product ids), one-hot vectors become huge, so we use a learned **embedding** instead (section 5).

## 2. Images

An image file decodes to an array of **pixels**, each holding brightness values for one or more channels. Standard photos have three channels (red, green, blue) stored as 8-bit unsigned integers from 0 to 255.

- Image libraries return shape **height × width × channels** (HWC).
- PyTorch layers expect **channels × height × width** (CHW), and a batch adds a leading dimension: **N × C × H × W** (N is the batch size).
- Grayscale images have one channel; you must still keep the channel axis, giving shape `(N, 1, H, W)`.
- Medical scanners and video produce **volumetric** data with an extra depth or time axis: `(N, C, D, H, W)`. A CT scan, the subject of the [project module](#/lesson/deep-learning/ct-project-plan), is a stack of 2-D slices forming a 3-D volume with one channel of density values.

Converting to floats and scaling comes next. The common options are dividing by 255 to get values between 0 and 1, or standardising each channel with its mean and standard deviation over the training set, which is what pretrained ImageNet models expect.

```python-run
import numpy as np

rng = np.random.default_rng(0)
# Pretend we decoded 4 photos of 32 x 32 pixels: each H x W x C uint8.
photos = [rng.integers(0, 256, size=(32, 32, 3), dtype=np.uint8) for _ in range(4)]

batch = np.stack(photos)                       # (N, H, W, C)
batch = batch.transpose(0, 3, 1, 2)            # like tensor.permute(0, 3, 1, 2): (N, C, H, W)
batch = batch.astype(np.float32) / 255.0       # scale to [0, 1]
print("batch shape:", batch.shape, " min/max:", batch.min(), batch.max().round(3))

mean = batch.mean(axis=(0, 2, 3))              # one mean per channel over images, rows, columns
std = batch.std(axis=(0, 2, 3))
print("channel means:", mean.round(3), " channel stds:", std.round(3))
standardised = (batch - mean[None, :, None, None]) / std[None, :, None, None]
print("after standardising, channel means:", standardised.mean(axis=(0, 2, 3)).round(6))
print("and stds:", standardised.std(axis=(0, 2, 3)).round(6))

volume = rng.normal(size=(1, 1, 40, 64, 64)).astype(np.float32)  # one scan: N, C, depth, H, W
print("volumetric batch shape:", volume.shape, "  bytes:", volume.nbytes)
```

**Reading this code line by line**

- `np.stack` joins the four HWC arrays along a new first axis, giving `(4, 32, 32, 3)`.
- `transpose(0, 3, 1, 2)` reorders axes to put channels second, the equivalent of `permute` in PyTorch. Remember from the storage lesson that this creates a non-contiguous view; converting dtype afterwards makes a fresh contiguous array anyway.
- `astype(np.float32) / 255.0` converts to decimals between 0 and 1.
- `mean(axis=(0, 2, 3))` averages over every axis except channels, producing three numbers. Reshaping them to `(1, 3, 1, 1)` with `None` lets them broadcast over the batch.
- After standardising, each channel has mean 0 and standard deviation 1 (up to rounding).
- A modest CT volume of 40 slices of 64 × 64 already needs 655 KB in float32; full scans are hundreds of megabytes, which is why 3-D projects crop small regions.

> [!WARNING]
> OpenCV, a popular image library, loads colour images in **BGR** order (blue first). A model trained on RGB input will see swapped colours and lose accuracy without any error. Convert with `img[..., ::-1]` or OpenCV's colour conversion function.

## 3. Tables

Tabular data, rows of records with columns of features, needs a decision per column. Columns come in three kinds:

- **Continuous** (also called interval or ratio): quantities where differences and ratios make sense, such as income or age. Standardise them.
- **Ordinal**: ordered categories where the spacing is not meaningful, such as "small, medium, large" or a 1 to 5 satisfaction rating. Encode as integers if order matters and the model can handle it, or one-hot if you do not want to assume equal spacing.
- **Categorical** (nominal): unordered categories such as payment method. One-hot encode, or use an embedding for many categories.

The **target** (what we predict) needs the same thought. For classification, PyTorch's standard loss takes **class indices** (an int64 tensor of shape `(N,)`) rather than one-hot vectors. For regression, the target is a float tensor, usually of shape `(N, 1)` to match the model's output (recall the broadcasting trap).

PyTorch builds one-hot vectors either with `torch.nn.functional.one_hot(labels, num_classes)` or with the in-place `scatter_` method, which writes a value at given indices along a dimension:

```python
labels = torch.tensor([2, 0, 1])
onehot = torch.zeros(3, 4)
onehot.scatter_(1, labels.unsqueeze(1), 1.0)    # in each row i, set column labels[i] to 1
# tensor([[0., 0., 1., 0.], [1., 0., 0., 0.], [0., 1., 0., 0.]])
torch.nn.functional.one_hot(labels, num_classes=4)  # same values, dtype int64
```

`scatter_(dim, index, value)` reads "for every position of `index`, write `value` into `onehot` at that position, but with the coordinate along `dim` replaced by the index". The `unsqueeze(1)` turns the labels into a column of shape `(3, 1)` so there is one index per row.

Here is a whole small table encoded in NumPy, with an invented customer dataset.

```python-run
import numpy as np

rows = [  # monthly_spend, tenure_months, plan, payment, churned
    (42.0, 3,  "basic",   "card"),
    (120.5, 40, "premium", "bank"),
    (65.0, 12, "standard", "wallet"),
    (30.0, 1,  "basic",   "wallet"),
    (99.9, 25, "premium", "card"),
]
churned = np.array([1, 0, 0, 1, 0])

continuous = np.array([[r[0], r[1]] for r in rows], dtype=np.float32)
mu, sigma = continuous.mean(axis=0), continuous.std(axis=0)
continuous = (continuous - mu) / sigma                       # standardise each column

plan_order = {"basic": 0, "standard": 1, "premium": 2}       # ordinal: keep the order as a number
plan = np.array([[plan_order[r[2]]] for r in rows], dtype=np.float32) / 2.0

payments = sorted({r[3] for r in rows})                       # vocabulary of categories
idx = np.array([payments.index(r[3]) for r in rows])
onehot = np.zeros((len(rows), len(payments)), dtype=np.float32)
np.put_along_axis(onehot, idx[:, None], 1.0, axis=1)          # mirrors onehot.scatter_(1, idx.unsqueeze(1), 1.0)

X = np.concatenate([continuous, plan, onehot], axis=1)
print("payment vocabulary:", payments)
print("feature matrix shape:", X.shape)
print(X.round(2))
print("target (class indices):", churned, churned.dtype)
```

The final feature matrix has 6 columns: two standardised continuous features, one scaled ordinal feature, and three one-hot payment columns. In a real project, `mu`, `sigma` and the vocabulary are computed on the training split and stored alongside the model, because the same transformation must be applied at prediction time.

> [!TIP]
> For tables, deep networks are often beaten by gradient-boosted trees. When you do use a network on tabular data, the usual recipe is: standardise continuous columns, embed each high-cardinality categorical column with `nn.Embedding`, concatenate everything and pass it through a small multilayer network.

## 4. Time series

A **time series** is a sequence of measurements taken at regular intervals, such as hourly electricity use of a building or per-minute stock prices. The new ingredient is **order**: neighbouring time steps are related, and a model that uses this structure (a 1-D convolution, a recurrent network or a transformer) needs time as an explicit axis.

Raw logs usually arrive as a flat table: one row per time step, one column per feature. Suppose we have 14 days of hourly readings with 3 features each (power used, outdoor temperature, a holiday flag): shape `(336, 3)`. To learn daily patterns we reshape to `(days, hours, features)` = `(14, 24, 3)`, and then, because PyTorch's 1-D convolution expects **N × C × L** (batch, channels, length), transpose to `(14, 3, 24)`: each day is one sample, each feature a channel, each hour a position along the length.

Time itself is often an input. Hour of day is **cyclical**: hour 23 is next to hour 0, but as raw numbers they are 23 apart. A standard encoding uses two features, $\sin(2\pi h/24)$ and $\cos(2\pi h/24)$, which place the hours on a circle so that 23 and 0 end up close together. Alternatively, one-hot encode the hour (24 columns) or the weekday (7 columns).

```python-run
import numpy as np

rng = np.random.default_rng(1)
hours = np.arange(14 * 24)
hour_of_day = hours % 24
power = 50 + 30 * np.sin(2 * np.pi * (hour_of_day - 6) / 24) + rng.normal(0, 3, hours.size)  # daily rhythm
temp = 27 + 4 * np.sin(2 * np.pi * (hour_of_day - 9) / 24) + rng.normal(0, 0.5, hours.size)
holiday = np.zeros(hours.size); holiday[5 * 24:6 * 24] = 1.0                                 # day 6 is a holiday
flat = np.stack([power, temp, holiday], axis=1)        # (336, 3): one row per hour
print("flat log:", flat.shape)

daily = flat.reshape(14, 24, 3)                        # (days, hours, features)
conv_ready = daily.transpose(0, 2, 1)                  # (N, C, L) for a 1-D convolution
print("per-day samples for Conv1d:", conv_ready.shape)

angle = 2 * np.pi * hour_of_day / 24
cyc = np.stack([np.sin(angle), np.cos(angle)], axis=1)
d = lambda a, b: np.linalg.norm(cyc[a] - cyc[b]).round(3)
print("distance hour 23 -> hour 0:", d(23, 0), "  hour 11 -> hour 12:", d(11, 12), "  hour 0 -> hour 12:", d(0, 12))
print("raw-number distance 23 -> 0:", abs(23 - 0))
```

The cyclical encoding puts hour 23 as close to hour 0 as hour 11 is to hour 12, while midnight and noon are maximally far apart, which is the intended geometry. The raw hour number puts 23 and 0 at opposite extremes.

When building training samples from one long series, slice **windows**: the input is, say, the past 7 days and the target the next day. Split train and validation **by time** (train on earlier weeks, validate on later weeks), never randomly, or the model peeks at the future.

## 5. Text

Text must become numbers too. The pipeline is:

1. **Tokenise**: split text into units called **tokens**. Units can be characters, words, or **subwords** (frequent word pieces, the approach used by modern language models; see [subword tokenizers](#/lesson/llm-practice/subword-tokenizers)).
2. **Build a vocabulary**: assign each distinct token an integer id. Unknown tokens map to a special id.
3. **Encode**: replace each token by its id, giving an int64 tensor of shape `(sequence_length,)`, or `(N, L)` for a padded batch.
4. **Represent**: turn ids into vectors, either one-hot or, in practice, with an embedding.

One-hot word vectors have the length of the vocabulary, often 50,000 or more, and every pair of words is equally far apart, so "cat" is no closer to "kitten" than to "carburettor". An **embedding** fixes both problems: it is a learned table of shape `(vocabulary_size, embedding_dim)`, and a token's vector is the row at its id. `nn.Embedding(num_embeddings, embedding_dim)` is that table. Mathematically, looking up a row equals multiplying a one-hot vector by the table, but the lookup is far cheaper. During training, related words drift to nearby vectors because they appear in similar contexts.

```python-run
import numpy as np

text = "the cat sat on the mat. the kitten sat too."
chars = sorted(set(text))
char_to_id = {c: i for i, c in enumerate(chars)}
char_ids = np.array([char_to_id[c] for c in text])
char_onehot = np.eye(len(chars))[char_ids]               # one row of the identity per character
print("character vocabulary size:", len(chars), " one-hot shape:", char_onehot.shape)

words = text.replace(".", " .").split()
vocab = ["<unk>"] + sorted(set(words))
word_to_id = {w: i for i, w in enumerate(vocab)}
encode = lambda s: np.array([word_to_id.get(w, 0) for w in s.replace(".", " .").split()])
ids = encode("the dog sat on the mat.")
print("vocabulary:", vocab)
print("ids for 'the dog sat on the mat.':", ids, "  ('dog' is unknown -> 0)")

rng = np.random.default_rng(0)
embedding_weight = rng.normal(size=(len(vocab), 4)).round(2)  # nn.Embedding(len(vocab), 4).weight
vectors = embedding_weight[ids]                                # nn.Embedding forward = row lookup
print("embedded sentence shape:", vectors.shape)
onehots = np.eye(len(vocab))[ids]
print("lookup equals one-hot @ table:", np.allclose(vectors, onehots @ embedding_weight))
```

The demo builds a character vocabulary (a one-hot row per character), then a word vocabulary with an `<unk>` token for unseen words, encodes a sentence, and embeds it. The last line confirms that an embedding lookup is the same as a one-hot vector multiplied by the table, without ever building the one-hot vectors.

> [!INTERVIEW]
> **"You have a column with 2 million distinct user ids. How do you feed it to a network?"** Not one-hot (2 million columns, and no generalisation between users). Use an embedding table, possibly with the **hashing trick** (map ids into a fixed number of buckets with a hash function to bound memory), reserve an id for unseen users, and consider replacing raw ids with aggregate features (counts, recency) that generalise to new users. Mention the memory cost: 2 million × 64 floats × 4 bytes ≈ 512 MB, plus optimiser state.

## 6. A checklist for any new data source

1. What is one **sample**, and what is the **target**?
2. Which axes exist (batch, channel, space, time, sequence), and in what order does the layer you will use expect them?
3. Which columns are continuous, ordinal or categorical? Which categorical ones have many values?
4. What scaling will you apply, and are its statistics computed on training data only?
5. How will you split data so validation reflects production (by time, by patient, by user)?
6. What dtype does each tensor need (float32 inputs, int64 class targets)?

## Summary

- Standardise continuous inputs with training-set mean and standard deviation; one-hot or embed categorical inputs.
- Images: decode to HWC uint8, permute to CHW, convert to float, scale or standardise per channel; batches are N × C × H × W; volumes add depth.
- Tables: decide per column whether it is continuous, ordinal or categorical; classification targets are int64 class indices.
- Time series: reshape flat logs into windows with an explicit time axis, encode cyclical time with sine and cosine, and split by time.
- Text: tokenise, map tokens to ids with a vocabulary, then embed; an embedding lookup equals a one-hot vector times a table.

## Glossary

- **Data representation (encoding)**: the choice of numbers and shapes used to present data to a model.
- **Standardisation**: subtracting the mean and dividing by the standard deviation.
- **Mean / standard deviation**: the average / the typical distance from the average.
- **Categorical / ordinal / continuous**: unordered categories / ordered categories / measured quantities.
- **One-hot vector**: all zeros except a 1 at the position of the category.
- **Embedding**: a learned table mapping each id to a dense vector.
- **Pixel / channel**: one point of an image / one colour or measurement layer.
- **HWC / CHW / NCHW**: axis orders height-width-channel, channel-height-width, batch-channel-height-width.
- **Volumetric data**: 3-D grids of values, such as CT scans.
- **scatter_**: an in-place write of values at index positions along a dimension.
- **Time series**: measurements taken at regular intervals.
- **Cyclical encoding**: representing periodic values like hours as sine and cosine.
- **Window**: a fixed-length slice of a time series used as one sample.
- **Token / vocabulary**: a unit of text / the mapping from tokens to integer ids.
- **Hashing trick**: mapping a huge set of ids into a fixed number of buckets with a hash function.

## Check yourself

```quiz
[
  {"q": "An image library returns an array of shape (480, 640, 3). What shape does a PyTorch Conv2d expect for a batch containing this one image?", "options": ["(1, 3, 480, 640)", "(1, 480, 640, 3)", "(3, 480, 640)", "(480, 640, 3, 1)"], "answer": 0,
   "explain": "Permute HWC to CHW, then add the batch dimension first: N × C × H × W."},
  {"q": "Why not encode the cities Singapore, Kuala Lumpur and Jakarta as 0, 1 and 2 in one column?", "options": ["It invents an order and spacing that do not exist", "Integers cannot be stored in tensors", "It uses too much memory", "Networks cannot read the number 0"], "answer": 0,
   "explain": "One-hot (or an embedding) avoids implying that one city is 'between' or 'twice' another."},
  {"q": "When should standardisation statistics be computed?", "options": ["On the training split only, then reused everywhere", "On the full dataset including test", "Separately on each batch", "On the test set only"], "answer": 0,
   "explain": "Using validation or test data to compute them leaks information and inflates scores."},
  {"q": "Why encode hour of day as sin and cos of 2π·h/24?", "options": ["So hours 23 and 0 end up close together", "To make the values integers", "Because networks cannot read numbers above 12", "To reduce the dataset size"], "answer": 0,
   "explain": "Placing hours on a circle preserves their cyclical neighbourhood."},
  {"q": "Hourly logs of shape (336, 3) cover 14 days. Which shape suits nn.Conv1d with one sample per day?", "options": ["(14, 3, 24)", "(14, 24, 3)", "(336, 3, 1)", "(3, 336)"], "answer": 0,
   "explain": "Conv1d expects N × C × L: days as the batch, features as channels, hours as the length."},
  {"q": "What does nn.Embedding(10000, 64) do with an input of token ids of shape (8, 20)?", "options": ["Returns a (8, 20, 64) tensor by looking up rows", "Returns a (8, 20, 10000) one-hot tensor", "Returns a (64,) vector", "Raises an error because ids are integers"], "answer": 0,
   "explain": "Each id selects one row of the 10000 × 64 table."},
  {"q": "For a time series forecasting model, how should you split training and validation data?", "options": ["By time: earlier periods for training, later for validation", "Randomly across all time steps", "By alternating hours", "It does not matter"], "answer": 0,
   "explain": "A random split lets the model see the future around each validation point."}
]
```

> **Source:** Stevens, Antiga & Viehmann, *Deep Learning with PyTorch*, ch. 4 (images and volumetric data, tabular data with continuous, ordinal and categorical values, one-hot encoding with scatter, time series, text with one-hot characters, words and embeddings); PyTorch documentation for `torch.nn.functional.one_hot` and `nn.Embedding`.
