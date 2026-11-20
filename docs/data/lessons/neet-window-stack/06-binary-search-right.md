# Binary search done right

Binary search is the algorithm everyone "knows" and almost everyone gets subtly wrong. Goodrich et al. note
that although binary search was first published in 1946, a fully correct version did not appear until 1962.
Jon Bentley later reported that most professional programmers he tested could not write a bug-free version.
The bugs are always the same: an off-by-one in the bounds, a loop that never terminates, or returning the wrong
side of the boundary.

This lesson replaces folklore with **invariants**. Once you can state exactly what `lo` and `hi` mean, the
code writes itself and every off-by-one question has a definite answer.

## 1. The idea

On a **sorted** sequence, comparing the target with the middle element tells you which half cannot contain the
target. Discard it. Each step halves the candidate range, so after about $\log_2 n$ steps the range is empty or
the target has been found. For $n = 10^9$ that is about 30 comparisons, versus up to a billion for a linear scan.

Goodrich et al. (§4.1.3) phrase it with *candidates*: the indices we cannot yet rule out, always forming a
contiguous range `[low, high]`. Initially every index is a candidate. Their recursive version:

```python-run
def binary_search(data, target, low, high):
    """Return True if target is in data[low..high] (inclusive)."""
    if low > high:
        return False                         # no candidates left
    mid = (low + high) // 2
    if target == data[mid]:
        return True
    elif target < data[mid]:
        return binary_search(data, target, low, mid - 1)
    else:
        return binary_search(data, target, mid + 1, high)

data = [2, 4, 5, 7, 8, 9, 12, 14, 17, 19, 22, 25, 27, 28, 33, 37]
print(binary_search(data, 22, 0, len(data) - 1), binary_search(data, 23, 0, len(data) - 1))
```

The recursion is a tail call, so it converts directly into a loop — which is what you should write in Python
(no recursion-depth limits, less overhead).

### 1.1 Why O(log n)?

After each comparison the number of candidates `r = high - low + 1` goes from `r` to at most
$\lfloor r/2 \rfloor$. Starting from `n`, after `k` steps at most $n / 2^k$ remain; the search stops once fewer
than one remains, i.e. after at most $\lfloor \log_2 n \rfloor + 1$ steps.

## 2. Template A — closed interval `[lo, hi]`, find an exact match

**Invariant:** *if the target exists, its index is in `[lo, hi]`.*

```python
def search(nums, target):
    lo, hi = 0, len(nums) - 1          # every index is a candidate
    while lo <= hi:                    # candidates remain
        mid = (lo + hi) // 2
        if nums[mid] == target:
            return mid
        if nums[mid] < target:
            lo = mid + 1               # mid and everything left of it are too small
        else:
            hi = mid - 1               # mid and everything right of it are too big
    return -1                          # range empty
```

Every line is forced by the invariant:

- `hi = len(nums) - 1` because the interval is **closed** (contains `hi`).
- `while lo <= hi` because `[lo, hi]` is non-empty exactly when `lo <= hi`.
- `lo = mid + 1` / `hi = mid - 1` because `mid` has been checked and ruled out. Using `hi = mid` here would
  keep a ruled-out index and can loop forever when `lo == hi`.

Use template A only when you are looking for **one specific value** and "not found" is a valid answer.

## 3. Template B — half-open `[lo, hi)`, find a boundary

Most real binary-search problems are not "is `x` present?" but "where is the **first** index where some
condition becomes true?". Reformulate everything as a **predicate** `P(i)` that is

$$\underbrace{\text{False, False, …, False}}_{\text{prefix}},\ \underbrace{\text{True, True, …, True}}_{\text{suffix}}$$

over the index range, and search for the first True.

**Invariant:** *every index `< lo` is False; every index `>= hi` is True; `[lo, hi)` is undecided.*

```python
def first_true(lo, hi, P):             # search in [lo, hi); returns hi if none is True
    while lo < hi:                      # undecided range non-empty
        mid = (lo + hi) // 2            # lo <= mid < hi
        if P(mid):
            hi = mid                    # mid is True -> it is in the True region
        else:
            lo = mid + 1                # mid is False -> everything up to mid is False
    return lo                           # lo == hi: first True
```

Why it terminates: `mid` rounds down, so `lo <= mid < hi`. Either `hi` drops to `mid < hi`, or `lo` rises to
`mid + 1 > lo`. The range strictly shrinks every step.

Why it's correct: when the loop ends, `lo == hi`; everything left of it is False, everything from it on is
True. So `lo` is the first True (or the original `hi` if nothing is True).

> [!TIP]
> Template B never compares for equality and never returns from inside the loop. That makes it the safest
> template: one exit, one answer, one invariant. Prefer it for anything other than plain membership.

## 4. lower_bound and upper_bound

Two predicates cover almost every sorted-array question:

| Name | Predicate | Returns | Python |
|---|---|---|---|
| **lower_bound(x)** | `nums[i] >= x` | first index with value `>= x` | `bisect.bisect_left(nums, x)` |
| **upper_bound(x)** | `nums[i] > x` | first index with value `> x` | `bisect.bisect_right(nums, x)` |

```python-run
def lower_bound(nums, x):
    lo, hi = 0, len(nums)
    while lo < hi:
        mid = (lo + hi) // 2
        if nums[mid] >= x: hi = mid
        else: lo = mid + 1
    return lo

def upper_bound(nums, x):
    lo, hi = 0, len(nums)
    while lo < hi:
        mid = (lo + hi) // 2
        if nums[mid] > x: hi = mid
        else: lo = mid + 1
    return lo

import bisect
nums = [1, 2, 2, 2, 5, 7]
for x in [0, 2, 3, 7, 8]:
    print(x, lower_bound(nums, x), bisect.bisect_left(nums, x),
             upper_bound(nums, x), bisect.bisect_right(nums, x))
```

Everything else is derived from these two:

| Question | Answer |
|---|---|
| Is `x` present? | `i = lower_bound(x)`; `i < n and nums[i] == x` |
| Insertion point keeping order (*Search Insert Position*) | `lower_bound(x)` |
| First occurrence of `x` | `lower_bound(x)` if present |
| Last occurrence of `x` | `upper_bound(x) - 1` if present |
| Count of `x` | `upper_bound(x) - lower_bound(x)` |
| Number of elements `< x` | `lower_bound(x)` |
| Number of elements `<= x` | `upper_bound(x)` |
| Largest element `<= x` (floor) | `nums[upper_bound(x) - 1]` if index ≥ 0 |
| Smallest element `>= x` (ceiling) | `nums[lower_bound(x)]` if index < n |

*Time Based Key-Value Store* is the floor query: the latest timestamp `<= t` is at `bisect_right(ts, t) - 1`.

## 5. The `bisect` module

Python ships these searches in C:

```python-run
import bisect
a = [10, 20, 20, 30]
print(bisect.bisect_left(a, 20), bisect.bisect_right(a, 20))   # 1 3
bisect.insort(a, 25)                                            # insert keeping order (O(n) shift)
print(a)
# Python 3.10+: key= lets you search records by a field
records = [(1, "a"), (4, "b"), (9, "c")]
print(bisect.bisect_left(records, 4, key=lambda r: r[0]))
# lo/hi restrict the search range
print(bisect.bisect_left([1, 3, 5, 7, 9], 6, lo=1, hi=4))
```

> [!WARNING]
> `bisect.insort` finds the position in O(log n) but **inserting** into a list shifts elements: O(n). For many
> inserts, use a balanced structure (e.g. `sortedcontainers.SortedList`) or a heap if you only need the minimum.

In interviews, using `bisect` is usually fine — but be ready to write `lower_bound` by hand, and say which
one you're using and why.

## 6. Template C — the last True (upper midpoint)

Sometimes the predicate is True-then-False and you want the **last** True — e.g. *Sqrt(x)*: `k*k <= x`
is True for `k = 0..⌊√x⌋`. Either negate the predicate and use template B (first False, minus one), or use the
mirror template:

```python
lo, hi = 0, x                      # answer is in [lo, hi]
while lo < hi:
    mid = (lo + hi + 1) // 2        # UPPER midpoint: lo < mid <= hi
    if mid * mid <= x:
        lo = mid                    # mid is True: answer >= mid
    else:
        hi = mid - 1                # mid is False: answer < mid
return lo
```

The upper midpoint matters: with `lo = mid` and the lower midpoint, the state `lo = 2, hi = 3` gives
`mid = 2`, `lo` stays 2, and the loop never ends.

> **Rule of thumb:** if a branch assigns `lo = mid`, round the midpoint **up**; if a branch assigns `hi = mid`,
> round it **down**. Never both in one loop.

```python-run
def my_sqrt(x):
    lo, hi = 0, x
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if mid * mid <= x: lo = mid
        else: hi = mid - 1
    return lo

print([my_sqrt(x) for x in [0, 1, 2, 3, 4, 8, 15, 16, 17]])
print(my_sqrt(10**30 - 1), int((10**30 - 1) ** 0.5))   # float sqrt is off for huge numbers
```

## 7. Searching a virtual array: the 2-D matrix

The search space doesn't have to be a list. *Search a 2D Matrix* has rows sorted and each row starting above
the previous row's end, so the matrix read row by row is one sorted sequence of length `m·n`. Element `k` of
that virtual sequence is `matrix[k // n][k % n]` — no flattening needed:

```python-run
def search_matrix(matrix, target):
    m, n = len(matrix), len(matrix[0])
    lo, hi = 0, m * n - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        v = matrix[mid // n][mid % n]          # divide by the number of COLUMNS
        if v == target: return True
        if v < target: lo = mid + 1
        else: hi = mid - 1
    return False

M = [[1, 3, 5, 7], [10, 11, 16, 20], [23, 30, 34, 60]]
print(search_matrix(M, 3), search_matrix(M, 13), search_matrix(M, 60))
```

Any **monotone function of an index** can be binary-searched without materialising the array — the gateway to
the next lesson, "binary search on the answer".

## 8. Overflow and the midpoint

In C, Java or C++, `(lo + hi) / 2` can overflow when `lo + hi` exceeds the integer range — exactly the bug found
in Java's library binary search in 2006. The fix is `lo + (hi - lo) / 2`. Python integers are arbitrary
precision, so `(lo + hi) // 2` is safe, but writing `lo + (hi - lo) // 2` is a good habit when you switch
languages. With negative bounds, note that Python's `//` floors, so `(lo + hi) // 2` still lies in `[lo, hi]`.

## 9. The off-by-one checklist

Before trusting a binary search, answer each question explicitly:

1. **What does the search space contain?** Indices `0..n-1`? Insertion points `0..n`? Answer values
   `lo..hi`? (Insertion points need `hi = n`.)
2. **Closed or half-open?** `[lo, hi]` ⇒ `while lo <= hi`, `hi = mid - 1`. `[lo, hi)` ⇒ `while lo < hi`,
   `hi = mid`.
3. **What is the predicate, and is it monotone?** Write it as False…False True…True (or the reverse).
4. **Do you want the first True or the last True?** First ⇒ lower midpoint and `hi = mid`. Last ⇒ upper
   midpoint and `lo = mid`.
5. **Does every branch shrink the range?** Check the two-element case `hi = lo + 1` by hand.
6. **What is returned when nothing satisfies the predicate?** `n`, `-1`, `""`? Check `i < n` before reading
   `nums[i]`.
7. **Test tiny inputs:** empty, one element (present/absent), two elements (target at each position, below
   both, above both), all duplicates.

```python-run
# A tiny brute-force harness: compare your function with a linear scan on many small arrays.
import random, bisect

def first_ge(nums, x):          # under test
    lo, hi = 0, len(nums)
    while lo < hi:
        mid = (lo + hi) // 2
        if nums[mid] >= x: hi = mid
        else: lo = mid + 1
    return lo

for trial in range(2000):
    nums = sorted(random.randint(0, 5) for _ in range(random.randint(0, 6)))
    x = random.randint(-1, 6)
    expected = next((i for i, v in enumerate(nums) if v >= x), len(nums))
    assert first_ge(nums, x) == expected == bisect.bisect_left(nums, x), (nums, x)
print("all 2000 random tests passed")
```

Randomised testing against a brute force is the fastest way to catch off-by-ones — use it when practising.

## 10. Summary

- Binary search needs a **monotone** predicate over a contiguous search space; each step halves it:
  O(log n).
- **Template A** (closed `[lo, hi]`, `lo <= hi`, `mid ± 1`) finds an exact value.
- **Template B** (half-open `[lo, hi)`, `lo < hi`, `hi = mid`) finds the first True — the safest default.
- **lower_bound** (`>= x`) and **upper_bound** (`> x`) answer first/last occurrence, counts, floors and
  ceilings; Python provides them as `bisect_left` / `bisect_right`.
- To find the last True, round the midpoint **up**.
- Always check the two-element case and the "not found" return value.

```quiz
[
  {"q": "With the closed interval [lo, hi] template, what is the loop condition?",
   "options": ["while lo < hi", "while lo <= hi", "while hi - lo > 1", "while mid != target"], "answer": 1,
   "explain": "The closed interval [lo, hi] is non-empty exactly when lo <= hi."},
  {"q": "bisect.bisect_left([1, 2, 2, 2, 5], 2) returns:",
   "options": ["0", "1", "3", "4"], "answer": 1,
   "explain": "bisect_left is lower_bound: the first index whose value is >= 2."},
  {"q": "How do you get the index of the LAST occurrence of x in a sorted list (if present)?",
   "options": ["bisect_left(a, x)", "bisect_right(a, x)", "bisect_right(a, x) - 1", "bisect_left(a, x) - 1"], "answer": 2,
   "explain": "bisect_right returns the first index with value > x, so one before it is the last x."},
  {"q": "A loop uses `lo = mid` in one branch and `hi = mid - 1` in the other. Which midpoint must it use?",
   "options": ["(lo + hi) // 2", "(lo + hi + 1) // 2", "Either", "lo + 1"], "answer": 1,
   "explain": "With the lower midpoint, lo = mid can leave the range unchanged when hi = lo + 1, causing an infinite loop."},
  {"q": "Search Insert Position must be able to return len(nums). What initial hi does the half-open template need?",
   "options": ["len(nums) - 1", "len(nums)", "len(nums) + 1", "0"], "answer": 1,
   "explain": "The search space is insertion points 0..n, so the half-open range is [0, n)... with the answer possibly equal to n = hi."},
  {"q": "In a 2-D matrix with m rows and n columns read row by row, virtual index k maps to:",
   "options": ["matrix[k // m][k % m]", "matrix[k // n][k % n]", "matrix[k % n][k // n]", "matrix[k][k]"], "answer": 1,
   "explain": "Each row holds n elements, so the row is k // n and the column is k % n."},
  {"q": "Why is (lo + hi) // 2 safe in Python but (lo + hi) / 2 risky in Java?",
   "options": ["Python is slower", "Python integers never overflow; Java ints can overflow when lo + hi is large", "Java rounds up", "It is not risky in Java"], "answer": 1,
   "explain": "This exact overflow bug was found in Java's library binary search; lo + (hi - lo) / 2 avoids it."},
  {"q": "What is the maximum number of iterations of binary search on 1,000,000 sorted elements?",
   "options": ["About 10", "About 20", "About 1000", "About 500000"], "answer": 1,
   "explain": "log2(10^6) is about 19.9, so at most 20 halvings."}
]
```

> **Source:** Goodrich, Tamassia & Goldwasser, *Data Structures and Algorithms in Python*, §4.1.3 (binary
> search) and §4.2 (analysis), plus the chapter notes on its history; Python `bisect` module documentation.
