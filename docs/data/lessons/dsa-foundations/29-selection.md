# Comparing sorts and selection

We now have seven sorting algorithms. This lesson compares them, looks at how Python's built-in sort
is used in practice (key functions, stability), and then tackles a closely related problem that does
*not* require sorting: **selection** — finding the $k$-th smallest element — in expected linear
time with **randomised quick-select**.

## 1. Comparing sorting algorithms

What matters when choosing a sort: running time (worst/average/best), **space**, **stability**,
whether the data fits in memory, and how the input tends to look.

| Algorithm | Best | Average | Worst | Extra space | Stable | Notes |
|---|---|---|---|---|---|---|
| Insertion-sort | $O(n)$ | $O(n^2)$ | $O(n^2)$ | $O(1)$ | yes | $O(n + m)$ for $m$ inversions; great for small or nearly sorted inputs |
| Selection-sort | $O(n^2)$ | $O(n^2)$ | $O(n^2)$ | $O(1)$ | no | minimal number of writes; otherwise rarely used |
| Heap-sort | $O(n\log n)$ | $O(n\log n)$ | $O(n\log n)$ | $O(1)$ | no | in place and guaranteed; poor cache behaviour |
| Merge-sort | $O(n\log n)$ | $O(n\log n)$ | $O(n\log n)$ | $O(n)$ | yes | sequential access: linked lists, external data |
| Quick-sort | $O(n\log n)$ | $O(n\log n)$ | $O(n^2)$ | $O(\log n)$ | no | fastest in practice in memory; randomise the pivot |
| Bucket-sort | $O(n+N)$ | $O(n+N)$ | $O(n+N)$ | $O(n+N)$ | yes | integer keys in $[0, N-1]$ |
| Radix-sort | $O(d(n+N))$ | same | same | $O(n+N)$ | yes | $d$-digit keys |

The book's guidance, in brief:

- **Insertion-sort** — excellent for small sequences (say, fewer than 50 elements) and for "almost
  sorted" sequences; used as the base case of faster sorts.
- **Heap-sort** — the natural choice when the input fits in memory and a guaranteed
  $O(n \log n)$ in-place sort is required (real-time constraints); slower than quick-sort and
  merge-sort on large inputs in practice.
- **Quick-sort** — historically the default general-purpose in-memory sort (C's `qsort`, Java's
  sort for primitives), because of its speed; not stable, and $O(n^2)$ worst case makes it risky
  where guarantees matter.
- **Merge-sort** — the choice when stability is required, or when data does not fit in main memory
  (it accesses data sequentially). Its hybrid descendant **Timsort** is the standard sort in Python
  and for objects in Java.
- **Bucket-/radix-sort** — when keys are small integers, character strings or $d$-tuples of small
  integers, these can beat everything else.

## 2. Python's built-in sorting

Python offers `list.sort()` (in place, returns `None`) and `sorted(iterable)` (returns a new list).
Both use Timsort: **stable**, $O(n \log n)$ worst case, $O(n)$ on already sorted or reverse-sorted
data.

### 2.1 Sorting according to a key function

By default elements are compared with `<`. Often we want a different order — strings by length,
records by a field. Rather than a comparison function, Python takes a one-parameter **key function**:
`key(e)` is computed **once per element**, and elements are ordered by their keys. This is the
**decorate–sort–undecorate** pattern done internally.

```python-run
colors = ['red', 'green', 'blue', 'cyan', 'magenta', 'yellow']
print(sorted(colors))                       # lexicographic
print(sorted(colors, key=len))              # by length; ties keep original order (stable)
print(sorted(colors, key=len, reverse=True))

from operator import itemgetter, attrgetter
staff = [("Ann", "eng", 120), ("Bob", "ops", 90), ("Cy", "eng", 95), ("Di", "ops", 130)]
print(sorted(staff, key=itemgetter(1, 2)))              # by dept, then salary (tuple key)
by_salary = sorted(staff, key=itemgetter(2), reverse=True)
print(sorted(by_salary, key=itemgetter(1)))             # stable: dept, salary descending within dept
```

The last two lines show the classic **multi-pass stable sort**: sort by the secondary criterion
first, then stably by the primary one — the same idea as LSD radix-sort.

## 3. Selection

The **selection problem**: given an unsorted collection of $n$ comparable elements, find the
$k$-th smallest (an **order statistic**). Minimum ($k = 1$) and maximum ($k = n$) are easy in
$O(n)$. The **median** ($k = \lceil n/2 \rceil$) is the interesting case.

The obvious approach — sort, then index — costs $O(n\log n)$. That is overkill: we want one element,
not a total order. Can we do it in $O(n)$?

### 3.1 Prune-and-search

**Prune-and-search** (or *decrease-and-conquer*): solve a problem on $n$ elements by **pruning away
a fraction** of them and recursively solving the smaller problem; when the problem is of constant
size, use brute force. Binary search is the simplest example (prune half each time). Unlike
divide-and-conquer, only **one** subproblem is solved.

### 3.2 Randomised quick-select

Pick a pivot at random and partition, exactly as in quick-sort, into $L$ (less), $E$ (equal), $G$
(greater). Then the $k$-th smallest lies in exactly one of them:

- if $k \le |L|$: it is the $k$-th smallest of $L$ — recurse on $L$;
- else if $k \le |L| + |E|$: it **is the pivot** — done;
- else: it is the $(k - |L| - |E|)$-th smallest of $G$ — recurse on $G$.

```python-run
import random
def quick_select(S, k):
    """Return the kth smallest element of list S, for k from 1 to len(S)."""
    if len(S) == 1:
        return S[0]
    pivot = random.choice(S)                 # pick random pivot element from S
    L = [x for x in S if x < pivot]          # elements less than pivot
    E = [x for x in S if x == pivot]         # elements equal to pivot
    G = [x for x in S if pivot < x]          # elements greater than pivot
    if k <= len(L):
        return quick_select(L, k)            # kth smallest lies in L
    elif k <= len(L) + len(E):
        return pivot                         # kth smallest equal to pivot
    else:
        j = k - len(L) - len(E)              # new selection parameter
        return quick_select(G, j)            # kth smallest is jth in G

data = [7, 4, 9, 3, 2, 6, 5, 1, 8, 5]
print([quick_select(data, k) for k in range(1, len(data) + 1)])
print("median of 1..999 shuffled:", quick_select(random.sample(range(1, 1000), 999), 500))
```

### Dry run

`S = [7, 4, 9, 3, 2, 6, 5, 1, 8]`, $k = 4$. Suppose the pivot is 6: $L = [4, 3, 2, 5, 1]$,
$E = [6]$, $G = [7, 9, 8]$. Since $k = 4 \le |L| = 5$, recurse on $L$ with $k = 4$. Pivot 2:
$L = [1]$, $E = [2]$, $G = [4, 3, 5]$; $k = 4 > 1 + 1$, so recurse on $G$ with $k = 2$. Pivot 4:
$L = [3]$, $E = [4]$ → $k = 2 \le 1 + 1$ → answer **4**.

### 3.3 Analysis

**Worst case:** unlucky pivots prune only one element at a time: $O(n^2)$.

**Expected case:** let $t(n)$ be the running time. Call a recursive call **good** if it leaves at
most $3n/4$ elements (the pivot is in the middle half — probability at least $1/2$). Let $g(n)$ be
the number of consecutive calls made, including the present one, before we get a good one. Then

$$t(n) \le b\,n \cdot g(n) + t(3n/4),$$

and since $E[g(n)] \le 2$ (coin flips until heads),

$$E[t(n)] \le 2bn + E[t(3n/4)].$$

Unrolling gives a **geometric series**:

$$E[t(n)] \le 2bn\left(1 + \tfrac34 + \left(\tfrac34\right)^2 + \cdots\right) = 8bn.$$

> **Proposition.** The expected running time of randomised quick-select on a sequence of size $n$ is
> $O(n)$.

The contrast with quick-sort is instructive: quick-sort recurses on *both* parts, giving $n$ work
per level for $\log n$ levels; quick-select recurses on *one* part, so the work shrinks
geometrically: $n + \tfrac34 n + \cdots = O(n)$.

### 3.4 In-place quick-select and deterministic selection

Using the in-place partition from quick-sort, selection needs $O(1)$ extra space with a loop (the
recursion is a tail call):

```python-run
import random
def kth_smallest_inplace(A, k):
    """k is 1-based. Rearranges A; expected O(n) time, O(1) extra space."""
    lo, hi, target = 0, len(A) - 1, k - 1
    while True:
        if lo == hi: return A[lo]
        p = A[random.randint(lo, hi)]
        lt, i, gt = lo, lo, hi                   # three-way partition around p
        while i <= gt:
            if A[i] < p: A[lt], A[i] = A[i], A[lt]; lt += 1; i += 1
            elif A[i] > p: A[i], A[gt] = A[gt], A[i]; gt -= 1
            else: i += 1
        if target < lt: hi = lt - 1
        elif target > gt: lo = gt + 1
        else: return p
print(kth_smallest_inplace([7, 4, 9, 3, 2, 6, 5, 1, 8], 4))
```

There is also a **deterministic** $O(n)$ worst-case algorithm, *median of medians* (Blum, Floyd,
Pratt, Rivest, Tarjan): split into groups of 5, take each group's median, recursively select the
median of those medians and use it as the pivot — guaranteeing a 30/70 split at worst. It is
elegant but has large constants; in practice randomised quick-select (or *introselect*, which falls
back to median-of-medians) is used. NumPy's `np.partition` and C++'s `std::nth_element` are
implementations.

> [!INTERVIEW]
> "Find the $k$-th largest element": three standard answers. (1) Sort: $O(n \log n)$. (2) Min-heap of
> size $k$: $O(n\log k)$, works on streams. (3) Quick-select: $O(n)$ expected, $O(n^2)$ worst case,
> needs all data in memory and mutates it. State the trade-offs; mention median-of-medians for the
> worst-case guarantee.

## 4. Deterministic selection: median of medians, step by step

Randomised quick-select is expected $O(n)$, but an unlucky run is $O(n^2)$. The *median of medians*
algorithm removes the luck by **computing** a pivot that is guaranteed to be reasonably central.
It is worth seeing in full once, because the analysis shows how a recurrence with two recursive
calls can still be linear.

**Choosing the pivot.**

1. Split the $n$ elements into groups of 5 (the last group may be smaller).
2. Find the median of each group directly — sorting 5 elements takes constant time — giving about
   $n/5$ medians.
3. **Recursively select** the median of those medians. Use it as the pivot.

Then partition into $L$, $E$, $G$ and recurse into one side, exactly as in quick-select.

**Why the pivot is good.** Let $p$ be the median of medians. Half of the $n/5$ groups — about
$n/10$ of them — have a median $\le p$, and in each of those groups three elements (the median and
the two below it) are $\le p$. So at least about $3n/10$ elements are $\le p$, and symmetrically at
least $3n/10$ are $\ge p$. Whichever side we recurse into therefore contains **at most about
$7n/10$** elements.

**The recurrence.**

$$T(n) \le \underbrace{T(n/5)}_{\text{median of the medians}} + \underbrace{T(7n/10)}_{\text{recursive selection}} + cn.$$

Guess $T(n) \le an$ and substitute:
$T(n) \le a\tfrac{n}{5} + a\tfrac{7n}{10} + cn = \tfrac{9}{10}an + cn$, which is $\le an$ as soon as
$a \ge 10c$. So $T(n) = O(n)$ **in the worst case**. The proof works because the two subproblem
sizes sum to $\tfrac15 + \tfrac7{10} = \tfrac9{10} < 1$ of the input: the total work per level of
the recursion tree shrinks geometrically. (With groups of 3 the fractions are
$\tfrac13 + \tfrac23 = 1$ and the argument fails; with groups of 7 it works again.)

```python-run
import random
calls = 0
def select(S, k):
    """Deterministic k-th smallest (k is 1-based), worst-case O(n)."""
    global calls
    calls += 1
    if len(S) <= 10:
        return sorted(S)[k - 1]                              # constant-size base case
    groups = [sorted(S[i:i + 5]) for i in range(0, len(S), 5)]
    medians = [g[len(g) // 2] for g in groups]
    pivot = select(medians, (len(medians) + 1) // 2)         # median of the medians
    L = [x for x in S if x < pivot]
    E = [x for x in S if x == pivot]
    if k <= len(L):
        return select(L, k)
    if k <= len(L) + len(E):
        return pivot
    return select([x for x in S if x > pivot], k - len(L) - len(E))

def worst_split(S):
    """Fraction of elements on the larger side of the median-of-medians pivot."""
    groups = [sorted(S[i:i + 5]) for i in range(0, len(S), 5)]
    medians = [g[len(g) // 2] for g in groups]
    pivot = select(medians, (len(medians) + 1) // 2)
    smaller = sum(x < pivot for x in S)
    larger = sum(x > pivot for x in S)
    return max(smaller, larger) / len(S)

for name, data in [("random", random.sample(range(10**6), 20001)),
                   ("sorted", list(range(20001))),
                   ("reverse", list(range(20001, 0, -1)))]:
    calls = 0
    med = select(data, 10001)
    print(f"{name:8s}: median {med:7d} correct={med == sorted(data)[10000]}  "
          f"recursive calls {calls:4d}  larger side after first split: {worst_split(data):.2f} of n")
```

Whatever the input order — including the sorted and reverse-sorted inputs that ruin a
fixed-pivot quick-select — the larger side never exceeds about 70% of the elements, as the analysis
promised.

### Dry run on 15 elements

Find the median (8th smallest) of
`[12, 3, 17, 8, 5, 1, 20, 9, 14, 6, 11, 2, 15, 7, 4]`.

| step | result |
|---|---|
| groups of 5 | `[12, 3, 17, 8, 5]`, `[1, 20, 9, 14, 6]`, `[11, 2, 15, 7, 4]` |
| sorted groups | `[3, 5, 8, 12, 17]`, `[1, 6, 9, 14, 20]`, `[2, 4, 7, 11, 15]` |
| group medians | 8, 9, 7 |
| median of medians | **8** → pivot |
| partition | $L$ = `[3, 5, 1, 6, 2, 7, 4]` (7 elements), $E$ = `[8]`, $G$ = 7 elements |
| decide | $k = 8$ and $\lvert L\rvert + \lvert E\rvert = 8$ → the pivot is the answer: **8** |

### Which selection method should you use?

| Method | Time | Extra space | Notes |
|---|---|---|---|
| sort, then index | $O(n\log n)$ | $O(1)$–$O(n)$ | simplest; fine when you need many order statistics |
| heap of size $k$ | $O(n\log k)$ | $O(k)$ | works on streams; ideal for small $k$ |
| randomised quick-select | $O(n)$ expected, $O(n^2)$ worst | $O(1)$ in place | fastest in practice |
| median of medians | $O(n)$ worst case | $O(n)$ here; $O(\log n)$ in place | large constants |
| introselect | $O(n)$ worst case | $O(1)$ | quick-select that falls back to median of medians; `std::nth_element`, `numpy.partition` |

In Python, `sorted(data)[k - 1]` is usually fastest for moderate sizes because the sort runs in C;
`heapq.nsmallest(k, data)` is the right tool when $k$ is small, and `statistics.median` hides the
choice entirely.

## 5. Pitfalls

- Mixing 0-based and 1-based $k$.
- Forgetting the $E$ group: with many duplicates, a two-way partition can fail to make progress.
- Using `list.sort()` and expecting a return value (it returns `None`).
- Passing an expensive `key` function is fine (called once per element); passing a `cmp`-style
  function is not supported directly — use `functools.cmp_to_key`.
- Assuming quick-select leaves the array sorted — it only places the $k$-th element (and partitions
  around it).

## 6. Summary

- Choose a sort by size, memory, stability and input structure; Python's Timsort is stable and
  adaptive, customised via `key=`.
- Selection is easier than sorting: randomised quick-select is expected $O(n)$ by a geometric-series
  argument; prune-and-search solves one subproblem instead of two.

> **Source:** Goodrich, Tamassia & Goldwasser, *Data Structures and Algorithms in Python*, ch. 12.5–12.7.

## Check yourself

```quiz
[
  {"q": "Which algorithm is the best choice for a small, nearly sorted list?",
   "options": ["Heap-sort", "Insertion-sort", "Radix-sort", "Selection-sort"], "answer": 1,
   "explain": "Its running time is O(n + inversions) with tiny constants."},
  {"q": "Which sorts in the table are both O(n log n) worst case and stable?",
   "options": ["Heap-sort", "Quick-sort", "Merge-sort", "Selection-sort"], "answer": 2,
   "explain": "Heap-sort is not stable; quick-sort is neither stable nor worst-case O(n log n)."},
  {"q": "How often does sorted(data, key=f) call f?",
   "options": ["Once per comparison", "Once per element", "n log n times", "Never"], "answer": 1,
   "explain": "Keys are precomputed (decorate-sort-undecorate) and then compared."},
  {"q": "Expected running time of randomised quick-select?",
   "options": ["O(log n)", "O(n)", "O(n log n)", "O(n^2)"], "answer": 1,
   "explain": "Expected work is n + (3/4)n + (3/4)^2 n + ... = O(n)."},
  {"q": "Why is quick-select faster than quick-sort?",
   "options": ["It uses a better pivot", "It recurses into only one of the parts", "It does not partition", "It uses a heap"], "answer": 1,
   "explain": "Prune-and-search discards the part that cannot contain the answer."},
  {"q": "In quick_select, if k > len(L) + len(E), we recurse on G with parameter...",
   "options": ["k", "k - len(L)", "k - len(L) - len(E)", "len(G) - k"], "answer": 2,
   "explain": "The len(L) + len(E) smaller-or-equal elements are skipped."},
  {"q": "To sort records by department, and by salary descending within each department, using stable sorts you...",
   "options": ["sort by department, then by salary", "sort by salary descending, then stably by department", "cannot do it", "sort twice by department"], "answer": 1,
   "explain": "Secondary criterion first; the stable primary sort preserves it among ties."}
]
```
