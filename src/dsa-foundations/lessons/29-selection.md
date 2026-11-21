# Comparing sorts and selection

> **Before this lesson:** You should know the sorting algorithms of this track: insertion-sort
> ([Using arrays](#/lesson/dsa-foundations/using-arrays)), heap-sort
> ([PQ sorting, heap-sort and adaptable priority queues](#/lesson/dsa-foundations/heap-sort-adaptable)),
> [merge-sort](#/lesson/dsa-foundations/merge-sort),
> [quick-sort](#/lesson/dsa-foundations/quick-sort) with its partition step, and
> [bucket-sort and radix-sort](#/lesson/dsa-foundations/lower-bound-linear).

## In plain words

This lesson has two halves. The first is a buyer's guide: with seven sorting algorithms on the
shelf, which do you pick for which job, and how do you use the one built into Python?

The second half is about a different question that people often answer by sorting when they do
not need to. Suppose you want the median house price in a city, the value with half the prices
below it and half above. You could sort all the prices and take the middle one. But that
arranges *everything* in order when you wanted a single value. Finding the item that would be
in position $k$ if the list were sorted, without sorting it, is called **selection**, and it
can be done faster than sorting. The trick is quick-sort's partition step, followed by throwing
away the side that cannot contain the answer.

Why it matters for a job: "which sort would you use here, and why?" tests judgement, and the
table in section 1 is the answer key. "Find the $k$-th largest element" is among the most
frequently asked interview questions; this lesson gives its three standard solutions and when
each is the right one.

## 1. Comparing sorting algorithms

What matters when choosing a sort: its running time (in the best, average and worst cases), its
**extra space**, whether it is **stable**, whether the data fits in memory, and what the input
tends to look like. In the table, $N$ is the size of the key range for bucket-sort and $d$ the
number of digits for radix-sort.

| Algorithm | Best | Average | Worst | Extra space | Stable | Notes |
|---|---|---|---|---|---|---|
| Insertion-sort | $O(n)$ | $O(n^2)$ | $O(n^2)$ | $O(1)$ | yes | $O(n + m)$ for $m$ inversions; great for small or nearly sorted inputs |
| Selection-sort | $O(n^2)$ | $O(n^2)$ | $O(n^2)$ | $O(1)$ | no | minimal number of writes; otherwise rarely used |
| Heap-sort | $O(n\log n)$ | $O(n\log n)$ | $O(n\log n)$ | $O(1)$ | no | in place and guaranteed; poor cache behaviour |
| Merge-sort | $O(n\log n)$ | $O(n\log n)$ | $O(n\log n)$ | $O(n)$ | yes | sequential access: linked lists, external data |
| Quick-sort | $O(n\log n)$ | $O(n\log n)$ | $O(n^2)$ | $O(\log n)$ | no | fastest in practice in memory; randomise the pivot |
| Bucket-sort | $O(n+N)$ | $O(n+N)$ | $O(n+N)$ | $O(n+N)$ | yes | integer keys in $[0, N-1]$ |
| Radix-sort | $O(d(n+N))$ | same | same | $O(n+N)$ | yes | $d$-digit keys |

How to choose, in brief:

- **Insertion-sort** is excellent for short lists (up to a few dozen items) and for lists that
  are already almost in order. Faster sorts use it to finish off their small pieces.
- **Heap-sort** is the natural choice when the data fits in memory and you need a guaranteed
  $O(n \log n)$ sort that uses no extra space, for example in software with strict timing
  requirements. On large inputs it is slower in practice than quick-sort and merge-sort.
- **Quick-sort** has long been the default general-purpose sort for data in memory (C's `qsort`
  is named after it, and Java uses a variant for its basic numeric types), because it is so
  fast. It is not stable, and its $O(n^2)$ worst case makes it risky where a guarantee matters.
- **Merge-sort** is the choice when stability is required, or when the data is too large for
  memory, since it reads its input in order. Its refined descendant **Timsort** is the standard
  sort in Python, and in Java for lists of objects.
- **Bucket-sort and radix-sort** apply when keys are small whole numbers, strings, or tuples of
  small numbers, and in those cases they can beat everything else.

## 2. Python's built-in sorting

Python offers two ways to sort: `my_list.sort()` rearranges the list in place and returns
`None`, and `sorted(anything_iterable)` leaves its argument alone and returns a new sorted
list. Both use Timsort, so both are **stable**, take $O(n \log n)$ in the worst case, and take
only $O(n)$ on data that is already sorted or sorted in reverse.

### 2.1 Sorting according to a key function

By default items are compared with `<`. Often a different order is wanted: strings by length,
records by one of their fields. Python handles this with a **key function**, a function of one
argument passed as `key=`. Python calls it **once per item**, and then orders the items by the
values it returned. (Internally each item is paired with its key, the pairs are sorted, and the
keys are discarded; this is known as *decorate, sort, undecorate*.)

In the demo, `key=len` sorts strings by length; `reverse=True` reverses the order;
`itemgetter(1, 2)` builds a key function that returns fields 1 and 2 of a record as a tuple, so
that records are ordered by department and then by salary.

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

The last two lines show a classic technique, the **multi-pass stable sort**. To order by
department, and by salary from highest to lowest within each department, sort by the *less*
important criterion first (salary, descending) and then sort stably by the more important one
(department). Stability keeps the salary order inside each department. It is the idea of LSD
radix-sort applied to records.

## 3. Selection

The **selection problem**: given an unsorted collection of $n$ items that can be compared,
find the $k$-th smallest, that is, the item that would be at position $k$ if the collection
were sorted. Such an item is called an **order statistic**. The smallest ($k = 1$) and the
largest ($k = n$) are easy to find in $O(n)$ with one scan. The interesting case is the
**median**, the middle one, $k = \lceil n/2 \rceil$.

The obvious approach is to sort and then read off position $k$, which costs $O(n\log n)$. That
does far more than was asked: it puts every item in order when we wanted one item. Can
selection be done in $O(n)$?

### 3.1 Prune-and-search

The design pattern that achieves it is **prune-and-search** (also called *decrease and
conquer*): throw away a sizeable fraction of the items, known not to contain the answer, and
solve the same problem on what is left; when only a handful of items remain, solve it
directly. Binary search is the simplest example, discarding half the items at each step. The
difference from divide and conquer is that only **one** smaller problem is solved, not two.

### 3.2 Randomised quick-select

Choose a pivot at random and partition, exactly as in quick-sort, into $L$ (items less than
the pivot), $E$ (items equal to it) and $G$ (items greater). In sorted order, all of $L$ comes
first, then all of $E$, then all of $G$. So the sizes of the three groups tell us which group
holds the $k$-th smallest item. Writing $|L|$ for the number of items in $L$:

- if $k \le |L|$, it is among the first $|L|$ items: it is the $k$-th smallest of $L$, so
  recurse on $L$;
- otherwise, if $k \le |L| + |E|$, it falls in the block of items equal to the pivot: the
  answer **is the pivot**, and we are done;
- otherwise it is in $G$. The $|L| + |E|$ smaller items are skipped, so it is the
  $(k - |L| - |E|)$-th smallest of $G$; recurse on $G$.

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

**Worst case.** If every pivot is an extreme value, each step discards only one item, and the
cost is $n + (n-1) + \cdots = O(n^2)$.

**Expected case.** Let $t(n)$ be the running time on $n$ items. As in the quick-sort analysis,
call a step **good** if it leaves at most $3n/4$ items; that happens whenever the pivot comes
from the middle half of the sorted order, so with probability at least $1/2$. Let $g(n)$ be the
number of steps taken until a good one occurs. Each step costs at most $bn$ for some constant
$b$, so

$$t(n) \le b\,n \cdot g(n) + t(3n/4).$$

Waiting for a good step is like tossing a coin until it shows heads, which takes 2 tosses on
average. So $E[g(n)] \le 2$, and taking expected values,

$$E[t(n)] \le 2bn + E[t(3n/4)].$$

Unrolling this gives a **geometric sum** in which each term is three quarters of the one
before:

$$E[t(n)] \le 2bn\left(1 + \tfrac34 + \left(\tfrac34\right)^2 + \cdots\right) = 8bn.$$

(The bracket adds up to $1/(1 - \tfrac34) = 4$.)

> **Claim.** The expected running time of randomised quick-select on $n$ items is $O(n)$.

The contrast with quick-sort is worth stating. Quick-sort recurses on *both* parts, so every
level of its recursion handles all $n$ items, for $\log n$ levels. Quick-select recurses on
*one* part, so the work shrinks from level to level: $n + \tfrac34 n + \cdots = O(n)$. The
first level dominates.

### 3.4 In-place quick-select and deterministic selection

With quick-sort's in-place partition, selection needs only $O(1)$ extra space. And since the
recursive call is the last thing the function does (a tail call), it can be written as a loop
that narrows the range `lo..hi`:

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

There is also a **deterministic** algorithm, one that uses no random choices, with $O(n)$
running time in the worst case. It is called *median of medians* and is due to Blum, Floyd,
Pratt, Rivest and Tarjan. Split the items into groups of 5, take the median of each group, and
recursively select the median of those medians to use as the pivot; this guarantees a split no
worse than about 30% to 70%. It is elegant but has large constant factors, so in practice
people use randomised quick-select, or *introselect*, which starts as quick-select and falls
back to median of medians if it is going badly. NumPy's `np.partition` and C++'s
`std::nth_element` are implementations. Section 4 goes through the algorithm in full.

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

- **Mixing up counting from 0 and from 1.** "The $k$-th smallest" usually counts from 1, while
  list positions count from 0. Decide which you mean and convert in one place.
- **Forgetting the group of equal items.** With many duplicates, a partition into only "less"
  and "not less" can fail to shrink the problem, and the selection never ends.
- **Expecting `list.sort()` to return the list.** It returns `None`; use `sorted(...)` when you
  want a value back.
- **Passing a two-argument comparison function as `key`.** A `key` function takes one item. An
  expensive key is fine, since it is called once per item. If you only have an old-style
  comparison function, wrap it with `functools.cmp_to_key`.
- **Assuming quick-select leaves the array sorted.** It puts the $k$-th item in place, with
  smaller items before it and larger ones after, and nothing more.

## 6. Summary

- Choose a sort by input size, available memory, the need for stability and the structure of
  the keys. Python's built-in Timsort is stable and adaptive, and is customised with `key=`.
- Selection, finding the $k$-th smallest item, is easier than sorting. Randomised quick-select
  takes expected $O(n)$ time, by a geometric-sum argument.
- Prune-and-search solves one smaller problem where divide and conquer solves two.
- Median of medians achieves $O(n)$ in the worst case by computing a pivot that is guaranteed
  to be reasonably central.

> **Source:** Goodrich, Tamassia & Goldwasser, *Data Structures and Algorithms in Python*, ch. 12.5–12.7.

## Glossary

- **Key function**: a one-argument function whose result is used to order the items.
- **Decorate, sort, undecorate**: pairing each item with its key, sorting the pairs, then
  dropping the keys.
- **Multi-pass stable sort**: sorting by the least important criterion first and finishing,
  stably, with the most important.
- **Selection problem**: finding the $k$-th smallest item of an unsorted collection.
- **Order statistic**: the item at a given position in sorted order.
- **Median**: the middle order statistic.
- **Prune-and-search (decrease and conquer)**: discarding part of the input and recursing on
  the rest.
- **Quick-select**: selection by partitioning around a pivot and continuing into one side.
- **Deterministic algorithm**: an algorithm that makes no random choices.
- **Median of medians**: a pivot rule that guarantees worst-case linear-time selection.
- **Introselect**: quick-select with a fall-back to median of medians.

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
