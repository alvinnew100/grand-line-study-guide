import random as _random

_r = _random.Random(101)


def _floats(n, lo=0.0, hi=100.0):
    return [round(_r.uniform(lo, hi), 3) for _ in range(n)]


def _ints(n, lo=0, hi=100):
    return [_r.randint(lo, hi) for _ in range(n)]


PROBLEMS = [
# ---------------------------------------------------------------- trimmed mean
dict(
    id="stats-trimmed-mean",
    title="Trimmed Mean",
    difficulty="Easy",
    pattern="Estimates of Location",
    kind="function",
    entry="trimmed_mean",
    compare="float",
    description=r"""
Compute the **trimmed mean** of `values`: sort the values, drop `k = floor(prop * n)` values from **each** end
(where `n = len(values)`), and return the mean of what remains. This matches `scipy.stats.trim_mean`.

Constraints: `1 <= n <= 10^5`, `0 <= prop < 0.5`, and at least one value always remains.

**Example:** `values = [1, 2, 3, 4, 100], prop = 0.2` → `k = 1`, keep `[2, 3, 4]` → `3.0`

**Example:** `values = [5, 1, 3], prop = 0` → `3.0` (the ordinary mean)
""",
    starter='''def trimmed_mean(values, prop):
    pass
''',
    solution='''def trimmed_mean(values, prop):
    xs = sorted(values)
    n = len(xs)
    k = int(prop * n)
    kept = xs[k:n - k]
    return sum(kept) / len(kept)
''',
    tests=[
        [[1, 2, 3, 4, 100], 0.2],
        [[5, 1, 3], 0.0],
        [[12, 15, 18, 20, 22, 25, 27, 30, 34, 38, 41, 2400], 0.1],
        [[10, 9, 8, 7, 6, 5, 4, 3, 2, 1], 0.15],
        [[42], 0.3],
        [[-5, -1, 0, 1, 5, 1000, -1000], 0.25],
        [[2.5, 2.5, 2.5, 2.5], 0.2],
        [[3, 1], 0.49],
        [_floats(200), 0.05],
        [_ints(5001, -1000, 1000), 0.2],
    ],
    examples=2,
    wrong_solutions=[
        '''def trimmed_mean(values, prop):
    xs = sorted(values)
    k = round(prop * len(xs))
    kept = xs[k:len(xs) - k]
    return sum(kept) / len(kept)
''',
        '''def trimmed_mean(values, prop):
    k = int(prop * len(values))
    kept = values[k:len(values) - k]
    return sum(kept) / len(kept)
''',
    ],
    guide=dict(
        prereqs="Estimates of location: mean, median, trimmed mean (lesson *Data types and estimates of location*).",
        intuition=r"""The trimmed mean is a compromise between the mean (uses every value, fragile to outliers) and the median (robust
but ignores magnitudes). Cutting a fixed share from **both** ends removes the most extreme values on each side, then
the ordinary mean of the middle is taken.""",
        hints=[
            "Sort first: 'ends' means the smallest and largest values, not the first and last positions in the input.",
            "The number cut from each end is floor(prop * n); use int(), not round().",
            "Slice xs[k : n - k] and average it.",
        ],
        brute_force="Repeatedly remove the current min and max k times: O(k·n). Sorting once is simpler and O(n log n).",
        approach=r"""1. `xs = sorted(values)`.
2. `k = int(prop * n)` (floor for non-negative numbers).
3. `kept = xs[k : n - k]`, return `sum(kept) / len(kept)`.

Dry run: `[1, 2, 3, 4, 100]`, prop 0.2 → k = int(1.0) = 1 → kept `[2, 3, 4]` → 3.0.""",
        complexity="Time O(n log n) for the sort, space O(n) for the sorted copy.",
        pitfalls=r"""- Rounding instead of flooring: with n = 10 and prop = 0.15, floor gives 1 but round gives 2.
- Trimming the unsorted list.
- When k = 0 the slice `xs[0:n]` must return everything; `xs[k:-k]` would return an empty list.""",
        follow_up="Winsorising caps extreme values at the k-th smallest/largest instead of dropping them; try implementing it.",
    ),
),

# ---------------------------------------------------------------- weighted median
dict(
    id="stats-weighted-median",
    title="Weighted Median",
    difficulty="Medium",
    pattern="Estimates of Location",
    kind="function",
    entry="weighted_median",
    compare="float",
    description=r"""
Each `values[i]` has a positive weight `weights[i]`. Sort the pairs by value (ties may be in any order since equal values
are interchangeable), accumulate the weights in that order, and return the **first value at which the running total of
weights reaches at least half of the total weight**.

This is the *lower* weighted median: with equal weights and an even count it returns the lower of the two middle values.

Constraints: `1 <= n <= 10^5`, all weights `> 0`.

**Example:** `values = [0.021, 0.05, 0.06, 0.03, 0.1], weights = [12000, 800, 450, 3000, 150]` → `0.021`
(the first value alone carries 12,000 of 16,400 total weight).

**Example:** `values = [1, 2, 3, 4], weights = [1, 1, 1, 1]` → `2`
""",
    starter='''def weighted_median(values, weights):
    pass
''',
    solution='''def weighted_median(values, weights):
    pairs = sorted(zip(values, weights), key=lambda p: p[0])
    half = sum(weights) / 2
    run = 0.0
    for v, w in pairs:
        run += w
        if run >= half:
            return v
    return pairs[-1][0]
''',
    tests=[
        [[0.021, 0.05, 0.06, 0.03, 0.1], [12000, 800, 450, 3000, 150]],
        [[1, 2, 3, 4], [1, 1, 1, 1]],
        [[7], [3]],
        [[5, 1, 3], [1, 1, 10]],
        [[10, 20, 30], [1, 1, 1]],
        [[3, 3, 1, 9], [2, 2, 1, 1]],
        [[-4, -2, 0, 2], [0.5, 0.5, 0.5, 2.5]],
        [[100, 1], [1, 99]],
        [[1, 2], [1, 1]],
        [_floats(300, -50, 50), [round(_r.uniform(0.1, 5), 2) for _ in range(300)]],
        [_ints(20000, 0, 1000), [_r.randint(1, 20) for _ in range(20000)]],
    ],
    examples=2,
    wrong_solutions=[
        '''def weighted_median(values, weights):
    half = sum(weights) / 2
    run = 0
    for v, w in zip(values, weights):
        run += w
        if run >= half:
            return v
''',
        '''def weighted_median(values, weights):
    pairs = sorted(zip(values, weights))
    half = sum(weights) / 2
    run = 0
    for v, w in pairs:
        run += w
        if run > half:
            return v
''',
    ],
    guide=dict(
        prereqs="Weighted mean and weighted median (lesson *Data types and estimates of location*).",
        intuition=r"""Imagine each value as a stack of `weight` identical copies, laid out in sorted order. The weighted median is the
value sitting at the halfway point of that long line. Large weights make their value "wider", so it is more likely
to cover the midpoint.""",
        hints=[
            "Pair each value with its weight and sort the pairs by value.",
            "Walk through the sorted pairs adding weights until the running total reaches half the total.",
            "Use >= (at least half), not >, so equal weights give the lower middle value.",
        ],
        brute_force="Expand each value into weight copies and take the ordinary lower median: only works for integer weights and is O(total weight).",
        approach=r"""1. `pairs = sorted(zip(values, weights), key=value)`.
2. `half = sum(weights) / 2`.
3. Accumulate; return the first value where the running sum ≥ half.

Dry run `[1,2,3,4]` with weights 1: half = 2; running totals 1, 2 → return 2.""",
        complexity="O(n log n) time for sorting, O(n) space.",
        pitfalls=r"""- Accumulating in input order instead of sorted order.
- Using `>` instead of `>=`, which returns the upper middle value for even equal-weight data.
- Floating-point sums: compare with the half computed from the same sum.""",
        follow_up="Implement it in O(n) expected time with a quickselect-style partition on the weights.",
    ),
),

# ---------------------------------------------------------------- MAD and IQR
dict(
    id="stats-mad-iqr",
    title="Median Absolute Deviation and IQR",
    difficulty="Easy",
    pattern="Estimates of Variability",
    kind="function",
    entry="mad_iqr",
    compare="float",
    description=r"""
Return `[mad, iqr]` for a list of numbers:

- `mad` is the **median absolute deviation from the median**: the median of `|x - median(values)|` (no scaling constant).
- `iqr` is `Q3 - Q1`, where the quartiles use **linear interpolation**: for sorted values `x[0..n-1]` and fraction `p`,
  position `h = (n - 1) * p`, `j = floor(h)`, and the percentile is `x[j] + (h - j) * (x[j+1] - x[j])` (or `x[j]` when
  `j = n - 1`). This is NumPy's default rule.

Constraints: `1 <= n <= 10^5`.

**Example:** `values = [22, 25, 27, 28, 30, 31, 33, 35, 38, 41]` → `[4.0, 7.25]`
""",
    starter='''def mad_iqr(values):
    pass
''',
    solution='''def mad_iqr(values):
    def median(v):
        s = sorted(v)
        n = len(s)
        return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2
    def pct(s, p):
        h = (len(s) - 1) * p
        j = int(h)
        if j >= len(s) - 1:
            return float(s[-1])
        return s[j] + (h - j) * (s[j + 1] - s[j])
    m = median(values)
    mad = median([abs(x - m) for x in values])
    s = sorted(values)
    return [float(mad), float(pct(s, 0.75) - pct(s, 0.25))]
''',
    tests=[
        [[22, 25, 27, 28, 30, 31, 33, 35, 38, 41]],
        [[22, 25, 27, 28, 30, 31, 33, 35, 38, 410]],
        [[5]],
        [[1, 2]],
        [[3, 3, 3, 3]],
        [[1, 2, 3, 4, 10]],
        [[-10, 0, 10]],
        [[9, 1, 8, 2, 7, 3, 6, 4, 5]],
        [_floats(101, -20, 20)],
        [_ints(10000, 0, 500)],
    ],
    examples=2,
    wrong_solutions=[
        '''def mad_iqr(values):
    s = sorted(values)
    n = len(s)
    mean = sum(s) / n
    mad = sum(abs(x - mean) for x in s) / n
    return [mad, s[(3 * n) // 4] - s[n // 4]]
''',
    ],
    guide=dict(
        prereqs="Estimates of variability: MAD, percentiles and the IQR (lesson *Estimates of variability*).",
        intuition=r"""Both measures ignore the extremes. The MAD asks "how far is a typical value from the middle?" using medians twice.
The IQR is the width of the middle half of the data. One typo can wreck a standard deviation but leaves both unchanged.""",
        hints=[
            "Write a median helper that handles odd and even lengths.",
            "MAD: median of absolute deviations from the median (not from the mean).",
            "Percentile: h = (n - 1) * p, interpolate between sorted[j] and sorted[j + 1].",
        ],
        brute_force="Calling numpy.percentile and numpy.median is fine too; the point is knowing the definitions.",
        approach=r"""Dry run on the example: median = (30 + 31)/2 = 30.5; absolute deviations sorted are
0.5, 0.5, 2.5, 2.5, 3.5, 4.5, 5.5, 7.5, 8.5, 10.5 → median 4.0. For Q1: h = 9 × 0.25 = 2.25 → 27 + 0.25 × (28 − 27) =
27.25; Q3: h = 6.75 → 33 + 0.75 × 2 = 34.5; IQR = 7.25.""",
        complexity="O(n log n) for sorting.",
        pitfalls=r"""- Confusing the *mean* absolute deviation with the *median* absolute deviation.
- Using `n * p` instead of `(n - 1) * p` for the interpolation position.
- Single-element input: both quartiles equal that value, so the IQR is 0.""",
        follow_up="Multiply the MAD by 1.4826 to estimate the standard deviation of normal data robustly.",
    ),
),

# ---------------------------------------------------------------- percentile
dict(
    id="stats-percentile-linear",
    title="Percentile with Linear Interpolation",
    difficulty="Easy",
    pattern="Estimates of Variability",
    kind="function",
    entry="percentile",
    compare="float",
    description=r"""
Return the `q`-th percentile (`0 <= q <= 100`) of `values` using **linear interpolation** (NumPy's default):
sort the data into `x[0..n-1]`, compute `h = (n - 1) * q / 100`, `j = floor(h)`; the answer is
`x[j] + (h - j) * (x[j+1] - x[j])`, or `x[n-1]` when `j = n - 1`.

Do it without calling `numpy.percentile`.

**Example:** `values = [1, 2, 3, 4, 10], q = 30` → `h = 1.2` → `2 + 0.2 × (3 − 2) = 2.2`

**Example:** `values = [7, 3, 5], q = 100` → `7.0`
""",
    starter='''def percentile(values, q):
    pass
''',
    solution='''def percentile(values, q):
    s = sorted(values)
    h = (len(s) - 1) * q / 100
    j = int(h)
    if j >= len(s) - 1:
        return float(s[-1])
    return s[j] + (h - j) * (s[j + 1] - s[j])
''',
    tests=[
        [[1, 2, 3, 4, 10], 30],
        [[7, 3, 5], 100],
        [[7, 3, 5], 0],
        [[42], 73],
        [[10, 20], 50],
        [[10, 20], 25],
        [[5, 1, 4, 2, 3], 50],
        [[1, 1, 1, 9], 90],
        [[-3.5, 2.25, 0.0, 8.0, -1.0, 4.5], 62.5],
        [_floats(500), 99],
        [_ints(10001, -100, 100), 37],
    ],
    examples=2,
    wrong_solutions=[
        '''def percentile(values, q):
    s = sorted(values)
    h = len(s) * q / 100
    j = min(int(h), len(s) - 1)
    return float(s[j])
''',
    ],
    guide=dict(
        prereqs="Percentiles and quartiles (lesson *Estimates of variability*).",
        intuition=r"""Place the sorted values at positions 0, 1, ..., n − 1. The q-th percentile lives at position (n − 1)·q/100, which is
usually between two data points; move the fractional part of the way from the lower one to the upper one.""",
        hints=[
            "Sort a copy of the data.",
            "Position h = (n - 1) * q / 100; j = int(h) is the index below.",
            "Handle j == n - 1 (q = 100 or a single value) separately to avoid indexing past the end.",
        ],
        brute_force="numpy.percentile(values, q) gives the same answer; implementing it shows you know the rule.",
        approach=r"""`[1, 2, 3, 4, 10]`, q = 30: h = 4 × 0.3 = 1.2, j = 1 → 2 + 0.2 × (3 − 2) = 2.2.""",
        complexity="O(n log n) for the sort (O(n) with quickselect).",
        pitfalls=r"""- Using n instead of n − 1.
- Returning the nearest value rather than interpolating.
- Index error at q = 100.""",
        follow_up="Implement the other NumPy methods (lower, higher, nearest, midpoint) and compare them on small data.",
    ),
),

# ---------------------------------------------------------------- histogram
dict(
    id="stats-histogram-counts",
    title="Equal-Width Histogram Counts",
    difficulty="Easy",
    pattern="Exploring Distributions",
    kind="function",
    entry="histogram_counts",
    compare="exact",
    description=r"""
Split the interval `[lo, hi]` into `bins` equal-width bins and count how many `values` fall in each.
Every bin includes its **left** edge and excludes its right edge, **except the last bin, which includes `hi`**.
Values below `lo` or above `hi` are ignored. Return the list of `bins` counts (this matches `numpy.histogram(values,
bins, range=(lo, hi))`).

Constraints: `lo < hi`, `1 <= bins <= 1000`, `0 <= len(values) <= 10^5`.

**Example:** `values = [0, 1, 2, 2, 3, 5, 9, 10, 11], lo = 0, hi = 10, bins = 5` → `[2, 3, 1, 0, 2]`
(bins `[0,2) [2,4) [4,6) [6,8) [8,10]`; 11 is outside).
""",
    starter='''def histogram_counts(values, lo, hi, bins):
    pass
''',
    solution='''def histogram_counts(values, lo, hi, bins):
    counts = [0] * bins
    width = (hi - lo) / bins
    for x in values:
        if x < lo or x > hi:
            continue
        if x == hi:
            k = bins - 1
        else:
            k = int((x - lo) / width)
            k = min(k, bins - 1)
        counts[k] += 1
    return counts
''',
    tests=[
        [[0, 1, 2, 2, 3, 5, 9, 10, 11], 0, 10, 5],
        [[], 0, 1, 3],
        [[5], 0, 10, 1],
        [[10, 10, 10], 0, 10, 4],
        [[-1, 0, 100], 0, 99, 3],
        [[1, 2, 3, 4, 5, 6], 1, 6, 5],
        [[0, 3, 6, 9, 12, 15, 18, 21], 0, 24, 8],
        [_ints(2000, -10, 110), 0, 100, 10],
        [_ints(50000, 0, 999), 0, 1000, 25],
    ],
    examples=1,
    wrong_solutions=[
        '''def histogram_counts(values, lo, hi, bins):
    counts = [0] * bins
    width = (hi - lo) / bins
    for x in values:
        if lo <= x < hi:
            counts[int((x - lo) / width)] += 1
    return counts
''',
    ],
    guide=dict(
        prereqs="Frequency tables and histograms (lesson *Exploring distributions and categorical data*).",
        intuition=r"""Bin index = how many full bin-widths fit between `lo` and the value. The only special case is the right edge `hi`,
which belongs to the last bin so that the whole closed range is covered.""",
        hints=[
            "width = (hi - lo) / bins.",
            "Index = int((x - lo) / width) for lo <= x < hi.",
            "x == hi goes into bin bins - 1; skip values outside [lo, hi].",
        ],
        brute_force="For each value, loop over all bins and test membership: O(n·bins).",
        approach=r"""Example: width 2. 0, 1 → bin 0; 2, 2, 3 → bin 1; 5 → bin 2; 9 → bin 4; 10 == hi → bin 4; 11 skipped.""",
        complexity="O(n + bins) time, O(bins) space.",
        pitfalls=r"""- Dropping values equal to `hi`.
- Counting values outside the range.
- Floating-point edges: clamp the index to `bins - 1`.""",
        follow_up="Implement the Freedman-Diaconis rule for choosing the bin width: 2 × IQR / n^(1/3).",
    ),
),

# ---------------------------------------------------------------- robust z
dict(
    id="stats-robust-zscore",
    title="Robust Z-Score Outliers",
    difficulty="Easy",
    pattern="Estimates of Variability",
    kind="function",
    entry="robust_outliers",
    compare="exact",
    description=r"""
Flag outliers with the **robust z-score** `z_i = (x_i - median) / (1.4826 * MAD)`, where MAD is the median of
`|x_i - median|`. Return the **sorted list of indices** `i` with `|z_i| > threshold`.

If `MAD == 0` (more than half the values are identical), return the indices of all values that differ from the median.

**Example:** `values = [22, 25, 27, 28, 30, 31, 33, 35, 38, 410], threshold = 3.5` → `[9]`
(median 30.5, MAD 4.0, robust z of 410 is about 64).
""",
    starter='''def robust_outliers(values, threshold):
    pass
''',
    solution='''def robust_outliers(values, threshold):
    def median(v):
        s = sorted(v)
        n = len(s)
        return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2
    m = median(values)
    mad = median([abs(x - m) for x in values])
    if mad == 0:
        return [i for i, x in enumerate(values) if x != m]
    scale = 1.4826 * mad
    return [i for i, x in enumerate(values) if abs(x - m) / scale > threshold]
''',
    tests=[
        [[22, 25, 27, 28, 30, 31, 33, 35, 38, 410], 3.5],
        [[22, 25, 27, 28, 30, 31, 33, 35, 38, 41], 3.5],
        [[5, 5, 5, 5, 9], 3.0],
        [[1, 2, 3, 4, 5, -40, 6, 7, 8, 90], 3.0],
        [[7], 2.0],
        [[10, 12, 11, 13, 12, 11, 50, 12, -30], 2.5],
        [[1.0, 1.1, 0.9, 1.05, 0.95, 1.2, 3.0], 3.5],
        [_ints(500, 40, 60) + [500, -400, 61], 3.5],
    ],
    examples=2,
    wrong_solutions=[
        '''def robust_outliers(values, threshold):
    n = len(values)
    mean = sum(values) / n
    sd = (sum((x - mean) ** 2 for x in values) / (n - 1)) ** 0.5 if n > 1 else 0
    if sd == 0:
        return []
    return [i for i, x in enumerate(values) if abs(x - mean) / sd > threshold]
''',
    ],
    guide=dict(
        prereqs="MAD and robust z-scores (lesson *Estimates of variability*).",
        intuition=r"""An ordinary z-score uses the mean and standard deviation, which the outlier itself inflates, so big outliers can hide.
The robust version uses the median and the MAD, which barely notice extreme values; 1.4826 makes it comparable to a
standard deviation for normal data.""",
        hints=[
            "Compute the median, then the MAD.",
            "Guard against MAD == 0 before dividing.",
            "Return indices in increasing order (enumerate does this naturally).",
        ],
        brute_force="Same as the approach; the work is getting the definitions right.",
        approach=r"""Example: median 30.5, MAD 4.0, scale 5.93; z(410) = 379.5 / 5.93 ≈ 64 > 3.5; all others have |z| < 2.""",
        complexity="O(n log n) for the medians.",
        pitfalls=r"""- Using the mean/SD: with one huge typo the SD becomes so large that the typo's own z-score stays small.
- Division by zero when most values are equal.
- Returning values instead of indices.""",
        follow_up="Compare how many points the ordinary 3-SD rule and the robust rule flag on heavy-tailed data.",
    ),
),

# ---------------------------------------------------------------- correlations
dict(
    id="stats-pearson-spearman",
    title="Pearson and Spearman Correlation",
    difficulty="Medium",
    pattern="Correlation",
    kind="function",
    entry="correlations",
    compare="float",
    description=r"""
Return `[pearson, spearman]` for two equal-length lists `x` and `y` (length `>= 2`, neither constant).

- **Pearson** $r = \frac{\sum (x_i - \bar x)(y_i - \bar y)}{\sqrt{\sum (x_i - \bar x)^2 \sum (y_i - \bar y)^2}}$.
- **Spearman** is Pearson's $r$ computed on the **ranks** of `x` and of `y` (rank 1 = smallest). Tied values get the
  **average** of the ranks they span (e.g. two values tied for ranks 2 and 3 both get 2.5).

**Example:** `x = [1, 2, 3, 4, 5]`, `y = [2, 4, 5, 4, 5]` → `[0.7745966692, 0.7378647873]`

**Example:** `x = [1, 2, 3]`, `y = [1, 4, 9]` → `[0.9897433186, 1.0]`
""",
    starter='''def correlations(x, y):
    pass
''',
    solution='''def correlations(x, y):
    def pearson(a, b):
        n = len(a)
        ma, mb = sum(a) / n, sum(b) / n
        sab = sum((u - ma) * (v - mb) for u, v in zip(a, b))
        saa = sum((u - ma) ** 2 for u in a)
        sbb = sum((v - mb) ** 2 for v in b)
        return sab / (saa * sbb) ** 0.5
    def ranks(a):
        order = sorted(range(len(a)), key=lambda i: a[i])
        r = [0.0] * len(a)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and a[order[j + 1]] == a[order[i]]:
                j += 1
            avg = (i + j) / 2 + 1
            for k in range(i, j + 1):
                r[order[k]] = avg
            i = j + 1
        return r
    return [pearson(x, y), pearson(ranks(x), ranks(y))]
''',
    tests=[
        [[1, 2, 3, 4, 5], [2, 4, 5, 4, 5]],
        [[1, 2, 3], [1, 4, 9]],
        [[1, 2, 2, 3, 4, 5, 6, 7, 8, 9], [52, 55, 61, 58, 66, 70, 71, 78, 80, 86]],
        [[1, 2, 2, 3, 4, 5, 6, 7, 8, 9], [520, 55, 61, 58, 66, 70, 71, 78, 80, 86]],
        [[1, 2], [5, 3]],
        [[3, 1, 2, 3, 1], [10, 20, 30, 40, 50]],
        [[-3, -2, -1, 0, 1, 2, 3], [9, 4, 1, 0, 1, 4, 9]],
        [[0.5, 0.25, 0.125, 0.0625], [1, 2, 3, 4]],
        [_floats(300), _floats(300)],
        [_ints(2000, 0, 20), _ints(2000, 0, 20)],
    ],
    examples=2,
    wrong_solutions=[
        '''def correlations(x, y):
    def pearson(a, b):
        n = len(a)
        ma, mb = sum(a) / n, sum(b) / n
        sab = sum((u - ma) * (v - mb) for u, v in zip(a, b))
        saa = sum((u - ma) ** 2 for u in a)
        sbb = sum((v - mb) ** 2 for v in b)
        return sab / (saa * sbb) ** 0.5
    def ranks(a):
        order = sorted(range(len(a)), key=lambda i: a[i])
        r = [0] * len(a)
        for pos, i in enumerate(order):
            r[i] = pos + 1
        return r
    return [pearson(x, y), pearson(ranks(x), ranks(y))]
''',
    ],
    guide=dict(
        prereqs="Pearson and rank correlations (lesson *Correlation and exploring two or more variables*).",
        intuition=r"""Pearson measures straight-line association using the actual values. Spearman replaces values by their ranks first,
so it measures "goes up together" (monotonic association) and shrugs off outliers. Ties must share the average rank,
otherwise the result depends on the arbitrary order of equal values.""",
        hints=[
            "Write one pearson(a, b) helper and reuse it for Spearman.",
            "To rank: sort indices by value, then walk runs of equal values and assign each the average position + 1.",
            "Positions i..j (0-based) get rank (i + j) / 2 + 1.",
        ],
        brute_force="For each value, count how many are smaller and how many are equal: O(n²) ranking.",
        approach=r"""Ranking `[3, 1, 2, 3, 1]`: sorted values 1, 1, 2, 3, 3 → the two 1s share ranks 1 and 2 → 1.5 each; 2 gets 3;
the two 3s share 4 and 5 → 4.5. Ranks: `[4.5, 1.5, 3, 4.5, 1.5]`.""",
        complexity="O(n log n) for ranking, O(n) for the correlations.",
        pitfalls=r"""- Ranking ties by order of appearance (1, 2, ...) instead of averaging.
- Dividing by n in one place and n − 1 in another: in the ratio form above the divisors cancel, so use sums only.
- Mixing up which list's ranks go where.""",
        follow_up="Implement Kendall's tau by counting concordant and discordant pairs (O(n²), or O(n log n) with merge sort).",
    ),
),
]
