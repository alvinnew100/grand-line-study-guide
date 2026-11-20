import random as _r

_r.seed(41)

PROBLEMS = [
dict(
    id="dsaf-merge-sort-inversions",
    title="Merge-Sort and Count Inversions",
    difficulty="Medium",
    pattern="Sorting and Selection",
    entry="merge_sort_count",
    description=r"""
Implement merge-sort (Goodrich ch. 12.2) on a list of integers and, while merging, count the
**inversions**: pairs of indices `i < j` with `A[i] > A[j]`.

Return `[sorted_list, inversions]`. Do not modify the input, do not call `sorted`/`list.sort`, and
run in $O(n \log n)$ — the quadratic pair check is too slow for the large tests.

**Example:** `A = [5, 2, 4, 6, 1, 3]` → `[[1, 2, 3, 4, 5, 6], 9]`

**Example:** `A = [1, 2, 3]` → `[[1, 2, 3], 0]`
""",
    starter='''def merge_sort_count(A):
    pass
''',
    solution='''def merge_sort_count(A):
    def rec(S):
        if len(S) < 2:
            return list(S), 0
        mid = len(S) // 2
        L, a = rec(S[:mid])
        R, b = rec(S[mid:])
        out, i, j, inv = [], 0, 0, a + b
        while i < len(L) and j < len(R):
            if L[i] <= R[j]:
                out.append(L[i]); i += 1
            else:
                out.append(R[j]); j += 1
                inv += len(L) - i
        out.extend(L[i:]); out.extend(R[j:])
        return out, inv
    s, inv = rec(A)
    return [s, inv]
''',
    tests=[
        [[5, 2, 4, 6, 1, 3]],
        [[1, 2, 3]],
        [[]],
        [[7]],
        [[2, 1]],
        [[3, 3, 3]],
        [[2, 2, 1, 1]],
        [[4, 3, 2, 1]],
        [[-1, -3, 0, 5, -3]],
        [list(range(200, 0, -1))],
        [[_r.randint(0, 30) for _ in range(400)]],
        [[_r.randint(-10**6, 10**6) for _ in range(6000)]],
    ],
    examples=2,
    wrong_solutions=[
        '''def merge_sort_count(A):
    def rec(S):
        if len(S) < 2:
            return list(S), 0
        mid = len(S) // 2
        L, a = rec(S[:mid]); R, b = rec(S[mid:])
        out, i, j, inv = [], 0, 0, a + b
        while i < len(L) and j < len(R):
            if L[i] < R[j]:
                out.append(L[i]); i += 1
            else:
                out.append(R[j]); j += 1
                inv += len(L) - i
        out.extend(L[i:]); out.extend(R[j:])
        return out, inv
    s, inv = rec(A)
    return [s, inv]
''',
        '''def merge_sort_count(A):
    def rec(S):
        if len(S) < 2:
            return list(S), 0
        mid = len(S) // 2
        L, a = rec(S[:mid]); R, b = rec(S[mid:])
        out, i, j, inv = [], 0, 0, a + b
        while i < len(L) and j < len(R):
            if L[i] <= R[j]:
                out.append(L[i]); i += 1
            else:
                out.append(R[j]); j += 1
                inv += 1
        out.extend(L[i:]); out.extend(R[j:])
        return out, inv
    s, inv = rec(A)
    return [s, inv]
''',
    ],
    guide=dict(
        prereqs="Lesson *Divide and conquer: merge-sort*.",
        intuition="Inversions come in three kinds: both elements in the left half, both in the right half, or one in each. The first two are counted recursively. The cross inversions fall out of the merge: when an element of the right run is output before the remaining left elements, it is smaller than ALL of them.",
        hints=["Have the recursive function return (sorted list, inversion count).",
               "In the merge, when you take R[j], add len(L) - i to the count.",
               "Take from the left run on ties (<=): equal elements are not inversions."],
        brute_force="Check every pair i < j: O(n^2) — fine for n = 100, hopeless for n = 10^5.",
        approach="""
`rec(S)`: base case len < 2 → (S, 0). Otherwise split at mid, recurse on both halves, merge with two indices, counting `len(L) - i` each time the right element wins.

Dry run `[5,2,4 | 6,1,3]`: left half sorts to [2,4,5] with 2 inversions; right half to [1,3,6] with 2. Merge: 1 jumps over 3 left elements (+3), 2, 3 jumps over [4,5] (+2), 4, 5, 6. Total 2 + 2 + 5 = 9.
""",
        complexity="Time O(n log n): O(n) merge work per level, log n levels. Space O(n) for the temporary runs.",
        pitfalls="Using `<` counts equal pairs as inversions (first wrong solution); adding 1 instead of len(L) - i (second); mutating the input list.",
        follow_up="Insertion sort performs exactly this many shifts — check with the insertion-sort exercise. Variants: count pairs with A[i] > 2*A[j].",
    ),
),
dict(
    id="dsaf-quicksort-inplace",
    title="In-Place Quick-Sort",
    difficulty="Medium",
    pattern="Sorting and Selection",
    entry="quick_sort",
    inplace_arg=0,
    description=r"""
Sort the list `S` **in place** in nondecreasing order with quick-sort (Goodrich ch. 12.3): choose a
pivot, partition the range around it using swaps, and recurse on the two sides. No auxiliary lists,
no `sorted` / `list.sort`.

The tests include already-sorted input, reverse-sorted input and inputs with many duplicates, so:

- choose the pivot **at random** (or median-of-three) — a fixed first/last pivot goes quadratic and
  overflows the recursion stack on sorted input;
- make sure equal keys do not cause quadratic behaviour (three-way partitioning is the simplest way).

The function returns nothing; the grader inspects `S`.

**Example:** `S = [85, 24, 63, 45, 17, 31, 96, 50]` → `S` becomes `[17, 24, 31, 45, 50, 63, 85, 96]`
""",
    starter='''import random


def quick_sort(S):
    def sort(a, b):
        # sort S[a..b] inclusive, in place
        pass
    sort(0, len(S) - 1)
''',
    solution='''import random


def quick_sort(S):
    def sort(a, b):
        while a < b:
            p = S[random.randint(a, b)]
            lt, i, gt = a, a, b
            while i <= gt:
                if S[i] < p:
                    S[lt], S[i] = S[i], S[lt]
                    lt += 1
                    i += 1
                elif S[i] > p:
                    S[i], S[gt] = S[gt], S[i]
                    gt -= 1
                else:
                    i += 1
            if lt - a < b - gt:
                sort(a, lt - 1)
                a = gt + 1
            else:
                sort(gt + 1, b)
                b = lt - 1
    sort(0, len(S) - 1)
''',
    tests=[
        [[85, 24, 63, 45, 17, 31, 96, 50]],
        [[]],
        [[1]],
        [[2, 1]],
        [[3, 3, 3, 3, 3]],
        [[5, 1, 5, 1, 5, 1]],
        [[-2, 9, 0, -7, 4, 4, -2]],
        [list(range(3000))],
        [list(range(3000, 0, -1))],
        [[7] * 3000],
        [[_r.randint(0, 5) for _ in range(3000)]],
        [[_r.randint(-10**6, 10**6) for _ in range(5000)]],
    ],
    examples=2,
    wrong_solutions=[
        '''def quick_sort(S):
    def sort(a, b):
        if a >= b:
            return
        pivot, left, right = S[b], a, b - 1
        while left <= right:
            while left <= right and S[left] < pivot:
                left += 1
            while left <= right and pivot < S[right]:
                right -= 1
            if left <= right:
                S[left], S[right] = S[right], S[left]
                left, right = left + 1, right - 1
        S[left], S[b] = S[b], S[left]
        sort(a, left - 1)
        sort(left + 1, b)
    sort(0, len(S) - 1)
''',
        '''import random
def quick_sort(S):
    def sort(a, b):
        if a >= b:
            return
        p = S[random.randint(a, b)]
        i = a
        for j in range(a, b + 1):
            if S[j] < p:
                S[i], S[j] = S[j], S[i]
                i += 1
        sort(a, i - 1)
        sort(i + 1, b)
    sort(0, len(S) - 1)
''',
    ],
    guide=dict(
        prereqs="Lesson *Quick-sort and randomisation* (in-place partition, three-way partition, optimisations).",
        intuition="After partitioning around a pivot value p, the array looks like [< p | == p | > p]. The middle block is finished; sort the outer blocks the same way.",
        hints=["Three-way partition with indices lt, i, gt: S[a:lt] < p, S[lt:i] == p, S[gt+1:b+1] > p.",
               "When S[i] > p, swap with S[gt] and decrement gt but do NOT advance i (the swapped-in element is unexamined).",
               "Pick p = S[random.randint(a, b)]. Recurse on the smaller side and loop on the larger to bound the stack."],
        brute_force="Building new lists L, E, G at each level is correct but uses O(n) extra memory per level; a fixed last-element pivot is O(n^2) on sorted input and recurses n deep (the first wrong solution dies with RecursionError).",
        approach="""
`sort(a, b)` while a < b:
1. p = random element of S[a..b].
2. lt, i, gt = a, a, b; scan: smaller → swap to lt (lt++, i++); larger → swap to gt (gt--); equal → i++.
3. Now S[lt..gt] == p. Recurse on the smaller of [a, lt-1] and [gt+1, b], continue the loop on the other.

Example `[5,1,5,1,5,1]`, p = 5: after partition `[1,1,1,5,5,5]`; left side is sorted in one more pass; nothing to do on the right.
""",
        complexity="Expected O(n log n) time for any input; O(n) when there are O(1) distinct keys. Expected O(log n) stack (guaranteed O(log n) with the smaller-side-first trick). Not stable.",
        pitfalls="Fixed pivot on sorted input; advancing i after swapping with gt; excluding too little (recursing on a range that still contains the pivot block → infinite recursion); Lomuto without placing the pivot (second wrong solution loses track of where the pivot is).",
        follow_up="Add an insertion-sort cutoff for ranges shorter than 16 and measure; turn it into quick-select.",
    ),
),
dict(
    id="dsaf-quickselect",
    title="Quick-Select: k-th Smallest",
    difficulty="Medium",
    pattern="Sorting and Selection",
    entry="kth_smallest",
    description=r"""
Return the `k`-th smallest element (1-based: `k = 1` is the minimum) of the unsorted list `nums`,
using **randomised quick-select** (Goodrich ch. 12.7): partition around a random pivot and continue
only in the part that contains the answer. Expected $O(n)$ time — do not sort.

`1 <= k <= len(nums)`. Duplicates count separately: in `[2, 2, 3]` the 2nd smallest is `2`.

**Example:** `nums = [7, 4, 9, 3, 2, 6, 5, 1, 8], k = 4` → `4`

**Example:** `nums = [2, 2, 3], k = 2` → `2`
""",
    starter='''import random


def kth_smallest(nums, k):
    pass
''',
    solution='''import random


def kth_smallest(nums, k):
    S = list(nums)
    while True:
        if len(S) == 1:
            return S[0]
        pivot = random.choice(S)
        L = [x for x in S if x < pivot]
        E = [x for x in S if x == pivot]
        if k <= len(L):
            S = L
        elif k <= len(L) + len(E):
            return pivot
        else:
            k -= len(L) + len(E)
            S = [x for x in S if x > pivot]
''',
    tests=[
        [[7, 4, 9, 3, 2, 6, 5, 1, 8], 4],
        [[2, 2, 3], 2],
        [[5], 1],
        [[3, 1], 1],
        [[3, 1], 2],
        [[4, 4, 4, 4], 3],
        [[-5, 10, 0, -5, 7], 1],
        [[-5, 10, 0, -5, 7], 5],
        [[1, 2, 2, 2, 3, 3, 9], 5],
        [list(range(2000, 0, -1)), 1000],
        [[_r.randint(0, 20) for _ in range(3000)], 1500],
        [[_r.randint(-10**6, 10**6) for _ in range(8000)], 6000],
    ],
    examples=2,
    wrong_solutions=[
        '''def kth_smallest(nums, k):
    return sorted(set(nums))[min(k, len(set(nums))) - 1]
''',
        '''import random
def kth_smallest(nums, k):
    S = list(nums)
    while True:
        if len(S) == 1:
            return S[0]
        pivot = random.choice(S)
        L = [x for x in S if x < pivot]
        E = [x for x in S if x == pivot]
        if k < len(L):
            S = L
        elif k <= len(L) + len(E):
            return pivot
        else:
            k -= len(L) + len(E)
            S = [x for x in S if x > pivot]
''',
    ],
    guide=dict(
        prereqs="Lessons *Quick-sort and randomisation* and *Comparing sorts and selection*.",
        intuition="After partitioning around a pivot, you know exactly how many elements are smaller (|L|) and equal (|E|). That tells you which group holds rank k — the other groups can be thrown away.",
        hints=["Split into L (< pivot), E (== pivot), G (> pivot).",
               "k <= |L| → continue in L with the same k.",
               "k <= |L| + |E| → the pivot is the answer; otherwise continue in G with k - |L| - |E|."],
        brute_force="Sort and index: O(n log n). A min-heap of all elements popped k times: O(n + k log n).",
        approach="""
Loop (the recursion is a tail call):
1. pivot = random.choice(S).
2. Build L and E (and G only if needed).
3. Narrow S and adjust k as above.

Dry run k = 4 on `[7,4,9,3,2,6,5,1,8]`: pivot 6 → L = [4,3,2,5,1] (5 ≥ 4, go left); pivot 2 → L = [1], E = [2], so k becomes 2 in G = [4,3,5]; pivot 4 → L = [3], E = [4] → return 4.
""",
        complexity="Expected O(n): the surviving part shrinks geometrically, n + 3n/4 + ... Worst case O(n^2) with consistently bad pivots. Space O(n) for this list-building version; O(1) with in-place partitioning.",
        pitfalls="Deduplicating (first wrong solution treats duplicates as one rank); off-by-one `k < len(L)` (second); forgetting to subtract |L| + |E| when moving right; mutating the caller's list.",
        follow_up="k-th largest = (n - k + 1)-th smallest. Deterministic O(n): median of medians. Streaming version: heap of size k.",
    ),
),
dict(
    id="dsaf-radix-sort",
    title="LSD Radix-Sort",
    difficulty="Medium",
    pattern="Sorting and Selection",
    entry="radix_sort",
    description=r"""
Sort a list of **non-negative integers** with least-significant-digit radix-sort
(Goodrich ch. 12.4.2) and return the sorted list.

Process the keys digit by digit (any base you like — 10, 256, …), from least to most significant,
using a **stable** bucket/counting sort for each digit. No comparisons between keys, no
`sorted` / `list.sort`.

Values are below $2^{31}$.

**Example:** `[170, 45, 75, 90, 802, 24, 2, 66]` → `[2, 24, 45, 66, 75, 90, 170, 802]`
""",
    starter='''def radix_sort(nums):
    pass
''',
    solution='''def radix_sort(nums):
    nums = list(nums)
    if not nums:
        return nums
    biggest = max(nums)
    shift = 0
    while (biggest >> shift) > 0:
        buckets = [[] for _ in range(256)]
        for x in nums:
            buckets[(x >> shift) & 255].append(x)
        nums = [x for b in buckets for x in b]
        shift += 8
    return nums
''',
    tests=[
        [[170, 45, 75, 90, 802, 24, 2, 66]],
        [[]],
        [[0]],
        [[5, 5, 5]],
        [[10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0]],
        [[1000, 1, 100, 10, 0, 10000]],
        [[255, 256, 257, 65535, 65536, 1, 0]],
        [[2**31 - 1, 0, 2**30, 12345678, 2**31 - 1]],
        [[_r.randint(0, 9) for _ in range(500)]],
        [[_r.randint(0, 999) for _ in range(3000)]],
        [[_r.randint(0, 2**31 - 1) for _ in range(5000)]],
    ],
    examples=1,
    wrong_solutions=[
        '''def radix_sort(nums):
    nums = list(nums)
    if not nums:
        return nums
    place, biggest = 1, max(nums)
    while biggest // place > 0:
        buckets = [[] for _ in range(10)]
        for x in nums:
            buckets[(x // place) % 10].insert(0, x)
        nums = [x for b in buckets for x in b]
        place *= 10
    return nums
''',
        '''def radix_sort(nums):
    nums = list(nums)
    if not nums:
        return nums
    digits = len(str(max(nums)))
    for d in range(digits - 1, -1, -1):
        place = 10 ** d
        buckets = [[] for _ in range(10)]
        for x in nums:
            buckets[(x // place) % 10].append(x)
        nums = [x for b in buckets for x in b]
    return nums
''',
    ],
    guide=dict(
        prereqs="Lesson *The sorting lower bound and linear-time sorts*.",
        intuition="Sort by the last digit, then stably by the next digit, and so on. Each stable pass preserves the order created by earlier passes among keys that tie on the current digit, so after the most significant pass everything is in order.",
        hints=["One pass: distribute into `base` buckets by the current digit (append keeps it stable), then concatenate the buckets.",
               "Loop while the largest value still has digits at the current place.",
               "Base 256 with shifts and masks needs only 4 passes for 31-bit values."],
        brute_force="Comparison sorts need Omega(n log n); counting sort over the whole value range needs an array of 2^31 counters. Radix-sort is counting sort applied digit-wise.",
        approach="""
```
shift = 0
while (max >> shift) > 0:
    buckets = 256 empty lists
    for x in nums: buckets[(x >> shift) & 255].append(x)
    nums = concatenation of buckets
    shift += 8
```
Base-10 trace of the example: ones → 170 90 802 2 24 45 75 66; tens → 802 2 24 45 66 170 75 90; hundreds → 2 24 45 66 75 90 170 802.
""",
        complexity="O(d (n + N)) time for d digits in base N — here d <= 4, N = 256, i.e. O(n). Space O(n + N).",
        pitfalls="An unstable per-digit pass (first wrong solution inserts at the front of each bucket); processing the most significant digit first with full passes (second wrong solution); `max([])` on empty input; an all-zero list must still return correctly.",
        follow_up="Handle negative integers (offset, or a final pass on the sign); MSD radix-sort for variable-length strings.",
    ),
),
]
