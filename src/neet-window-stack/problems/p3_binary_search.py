import random

R = random.Random(42424242)

LC = "https://leetcode.com/problems/{}/"
NC = "https://neetcode.io/problems/{}"

# ---------- big inputs ----------
_bs_big = sorted(R.sample(range(-10 ** 5, 10 ** 5), 10000))


def _matrix(m, n, rng):
    vals = sorted(rng.sample(range(-10 ** 5, 10 ** 5), m * n))
    return [vals[i * n:(i + 1) * n] for i in range(m)]


_mat_big = _matrix(100, 120, R)
_koko_big = [R.randint(1, 10 ** 9) for _ in range(10000)]


def _rotate(a, k):
    return a[k:] + a[:k]


_rot_base = sorted(R.sample(range(-10 ** 6, 10 ** 6), 10000))
_rot_big = _rotate(_rot_base, 7237)
_rot_big2 = _rotate(_rot_base, 1)


def _timemap_ops(n, rng):
    ops, args = ["TimeMap"], [[]]
    keys = ["k%d" % i for i in range(5)]
    ts = 0
    for _ in range(n):
        if rng.random() < 0.5:
            ts += rng.randint(1, 5)
            ops.append("set")
            args.append([rng.choice(keys), "v%d" % rng.randint(0, 999), ts])
        else:
            ops.append("get")
            args.append([rng.choice(keys + ["missing"]), rng.randint(0, ts + 3)])
    return [ops, args]


def _timemap_one_key(n):
    ops, args = ["TimeMap"], [[]]
    for t in range(1, n + 1):
        ops.append("set")
        args.append(["a", "x%d" % (t % 97), 2 * t])
    for t in range(1, n + 1):
        ops.append("get")
        args.append(["a", 2 * t + 1])
    return [ops, args]


_med_a = sorted(R.randint(-10 ** 6, 10 ** 6) for _ in range(15000))
_med_b = sorted(R.randint(-10 ** 6, 10 ** 6) for _ in range(14001))

_range_big = sorted(R.randint(0, 2000) for _ in range(20000))

_ship_big = [R.randint(1, 500) for _ in range(20000)]
_split_big = [R.randint(0, 10 ** 6) for _ in range(10000)]


PROBLEMS = [
# ---------------------------------------------------------------- 704
dict(
    id="binary-search",
    title="Binary Search",
    difficulty="Easy",
    pattern="Binary Search",
    leetcode=LC.format("binary-search"),
    neetcode=NC.format("binary-search"),
    entry="search",
    description=r"""
`nums` is sorted in strictly increasing order. Return the index of `target` in `nums`, or `-1` if it is not
there. Your algorithm must run in **O(log n)** time.

**Constraints**

- `1 <= len(nums) <= 10^4` (big tests go to 10^4)
- all values distinct, `-10^4 < nums[i], target < 10^4` in LeetCode

**Example 1:** `nums = [-1,0,3,5,9,12], target = 9` → `4`.

**Example 2:** `nums = [-1,0,3,5,9,12], target = 2` → `-1`.
""",
    starter='''class Solution:
    def search(self, nums: List[int], target: int) -> int:
        pass
''',
    solution='''class Solution:
    def search(self, nums, target):
        lo, hi = 0, len(nums) - 1
        while lo <= hi:
            mid = (lo + hi) // 2
            if nums[mid] == target:
                return mid
            if nums[mid] < target:
                lo = mid + 1
            else:
                hi = mid - 1
        return -1
''',
    tests=[
        [[-1, 0, 3, 5, 9, 12], 9],
        [[-1, 0, 3, 5, 9, 12], 2],
        [[5], 5],
        [[5], -5],
        [[1, 3], 3],
        [[1, 3], 1],
        [[1, 3], 2],
        [[-1, 0, 3, 5, 9, 12], 12],
        [[-1, 0, 3, 5, 9, 12], -1],
        [[-1, 0, 3, 5, 9, 12], 13],
        [_bs_big, _bs_big[-1]],
        [_bs_big, _bs_big[4321]],
        [_bs_big, _bs_big[0] - 1],
    ],
    wrong_solutions=[
        '''class Solution:
    def search(self, nums, target):
        lo, hi = 0, len(nums) - 1
        while lo < hi:                      # misses the last candidate
            mid = (lo + hi) // 2
            if nums[mid] == target: return mid
            if nums[mid] < target: lo = mid + 1
            else: hi = mid - 1
        return -1
''',
        '''class Solution:
    def search(self, nums, target):
        lo, hi = 0, len(nums)
        while lo < hi:
            mid = (lo + hi) // 2
            if nums[mid] < target: lo = mid + 1
            else: hi = mid
        return lo                           # forgets to check that target is really there
''',
    ],
    guide=dict(
        prereqs="Sorted arrays; the *Binary search done right* lesson (closed interval `[lo, hi]`).",
        intuition="""
Comparing `target` with the middle element of a sorted range tells you which half **cannot** contain it.
Throw that half away; the candidate range halves each step, so after about `log₂ n` steps it is empty or you
found the target.
""",
        hints=[
            "What does comparing target with nums[mid] tell you about the left and right halves?",
            "Keep the invariant: if target exists, its index is in [lo, hi]. Loop while that range is non-empty (lo <= hi).",
            "If nums[mid] < target set lo = mid + 1, else hi = mid - 1 — always exclude mid, or the loop may not shrink.",
        ],
        brute_force="Linear scan: **O(n)**. For one query on 3·10⁴ numbers that is still fast; the point is the O(log n) pattern you will reuse everywhere.",
        approach="""
**Dry run** `[-1,0,3,5,9,12]`, target 9:

| lo | hi | mid | nums[mid] | decision |
|---|---|---|---|---|
| 0 | 5 | 2 | 3 | 3 < 9 → lo = 3 |
| 3 | 5 | 4 | 9 | found → 4 |

Target 2: (0,5,mid 2: 3 > 2 → hi 1) → (0,1,mid 0: −1 < 2 → lo 1) → (1,1,mid 1: 0 < 2 → lo 2) → lo > hi → −1.
""",
        complexity="Time **O(log n)**, space **O(1)**.",
        pitfalls="""
- `while lo < hi` with a closed interval skips the final one-element range.
- `hi = mid` (instead of `mid - 1`) with `lo <= hi` can loop forever.
- In languages with fixed-width ints write `mid = lo + (hi - lo) // 2`; Python ints don't overflow.
""",
        follow_up="`bisect.bisect_left(nums, target)` does the same in C: check `i < len(nums) and nums[i] == target`.",
    ),
),
# ---------------------------------------------------------------- 74
dict(
    id="search-a-2d-matrix",
    title="Search a 2D Matrix",
    difficulty="Medium",
    pattern="Binary Search",
    leetcode=LC.format("search-a-2d-matrix"),
    neetcode=NC.format("search-2d-matrix"),
    entry="searchMatrix",
    description=r"""
An `m × n` integer matrix has two properties:

- each row is sorted in increasing order;
- the first value of each row is larger than the last value of the row above.

Return `True` if `target` is in the matrix, otherwise `False`, in **O(log(m·n))** time.

**Constraints**

- `1 <= m, n <= 100` (one big test is 100 × 120)
- `-10^4 <= matrix[i][j], target <= 10^4` in LeetCode

**Example 1:** `matrix = [[1,3,5,7],[10,11,16,20],[23,30,34,60]], target = 3` → `True`.

**Example 2:** same matrix, `target = 13` → `False`.
""",
    starter='''class Solution:
    def searchMatrix(self, matrix: List[List[int]], target: int) -> bool:
        pass
''',
    solution='''class Solution:
    def searchMatrix(self, matrix, target):
        m, n = len(matrix), len(matrix[0])
        lo, hi = 0, m * n - 1
        while lo <= hi:
            mid = (lo + hi) // 2
            v = matrix[mid // n][mid % n]
            if v == target:
                return True
            if v < target:
                lo = mid + 1
            else:
                hi = mid - 1
        return False
''',
    tests=[
        [[[1, 3, 5, 7], [10, 11, 16, 20], [23, 30, 34, 60]], 3],
        [[[1, 3, 5, 7], [10, 11, 16, 20], [23, 30, 34, 60]], 13],
        [[[1]], 1],
        [[[1]], 2],
        [[[1, 3]], 3],
        [[[1], [3]], 3],
        [[[1], [3], [5]], 4],
        [[[1, 3, 5, 7], [10, 11, 16, 20], [23, 30, 34, 60]], 60],
        [[[1, 3, 5, 7], [10, 11, 16, 20], [23, 30, 34, 60]], 0],
        [[[1, 3, 5], [7, 9, 11]], 9],
        [[[1, 2, 3, 4, 5, 6]], 6],
        [_mat_big, _mat_big[77][119]],
        [_mat_big, _mat_big[0][0]],
        [_mat_big, _mat_big[60][3] + 1 if _mat_big[60][3] + 1 != _mat_big[60][4] else 10 ** 6],
    ],
    wrong_solutions=[
        '''class Solution:
    def searchMatrix(self, matrix, target):
        m, n = len(matrix), len(matrix[0])
        lo, hi = 0, m * n - 1
        while lo <= hi:
            mid = (lo + hi) // 2
            v = matrix[mid // m][mid % m]      # bug: divides by the row count
            if v == target: return True
            if v < target: lo = mid + 1
            else: hi = mid - 1
        return False
''',
        '''class Solution:
    def searchMatrix(self, matrix, target):
        for row in matrix:
            if row[0] <= target <= row[-1]:
                return target in row[1:-1]     # forgets the row's endpoints
        return False
''',
    ],
    guide=dict(
        prereqs="Binary search on an index range; row-major indexing `i = k // n, j = k % n`.",
        intuition="""
Read the matrix row by row and you get **one sorted list** of `m·n` numbers. You don't need to build it: the
`k`-th element of that virtual list lives at `matrix[k // n][k % n]`. Binary-search `k` over `[0, m·n − 1]`.
""",
        hints=[
            "If you concatenated the rows, what would the result look like?",
            "A single sorted array of length m·n. Index k maps to row k // n and column k % n.",
            "Run the standard closed-interval binary search on k, reading matrix[k // n][k % n].",
        ],
        brute_force="Scan everything: **O(m·n)**. Slightly better: find the row by scanning first elements, then binary-search the row — O(m + log n). Two binary searches give O(log m + log n) = O(log mn), equal to the virtual-array approach.",
        approach="""
**Dry run** 3×4 matrix, target 3: lo=0, hi=11 → mid 5 → (1,1)=11 > 3 → hi 4 → mid 2 → (0,2)=5 > 3 → hi 1 → mid 0 → 1 < 3 → lo 1 → mid 1 → (0,1)=3 → True.
""",
        complexity="Time **O(log(m·n))**, space **O(1)**.",
        pitfalls="""
- Divide by the number of **columns** `n`, not rows `m` (only matters when the matrix is not square).
- Empty matrix checks if your inputs allow them.
""",
        follow_up="*Search a 2D Matrix II* (240) only sorts rows and columns separately — the trick there is a staircase walk from the top-right corner in O(m + n).",
    ),
),
# ---------------------------------------------------------------- 875
dict(
    id="koko-eating-bananas",
    title="Koko Eating Bananas",
    difficulty="Medium",
    pattern="Binary Search on Answer",
    leetcode=LC.format("koko-eating-bananas"),
    neetcode=NC.format("eating-bananas"),
    entry="minEatingSpeed",
    description=r"""
There are piles of bananas, `piles[i]` bananas in pile `i`, and `h` hours until the guards return. Koko picks an
integer eating speed `k` (bananas per hour). Every hour she chooses one pile and eats `k` bananas from it — or the
whole pile if it has fewer than `k` left, in which case she idles for the rest of that hour.

Return the **smallest** `k` that lets her finish every pile within `h` hours.

**Constraints**

- `1 <= len(piles) <= 10^4`
- `len(piles) <= h <= 10^9`
- `1 <= piles[i] <= 10^9`

**Example 1:** `piles = [3,6,7,11], h = 8` → `4`.

**Example 2:** `piles = [30,11,23,4,20], h = 5` → `30`.
""",
    starter='''class Solution:
    def minEatingSpeed(self, piles: List[int], h: int) -> int:
        pass
''',
    solution='''class Solution:
    def minEatingSpeed(self, piles, h):
        lo, hi = 1, max(piles)
        while lo < hi:
            k = (lo + hi) // 2
            hours = 0
            for p in piles:
                hours += (p + k - 1) // k
            if hours <= h:
                hi = k
            else:
                lo = k + 1
        return lo
''',
    tests=[
        [[3, 6, 7, 11], 8],
        [[30, 11, 23, 4, 20], 5],
        [[30, 11, 23, 4, 20], 6],
        [[1], 1],
        [[1000000000], 2],
        [[312884470], 312884469],
        [[1, 1, 1, 1], 4],
        [[2, 2], 2],
        [[2, 2], 3],
        [[5, 10, 15], 1000000000],
        [[805306368, 805306368, 805306368], 1000000000],
        [_koko_big, 10000],
        [_koko_big, 10 ** 9],
        [_koko_big, 123456789],
    ],
    wrong_solutions=[
        '''class Solution:
    def minEatingSpeed(self, piles, h):
        lo, hi = 1, max(piles)
        while lo < hi:
            k = (lo + hi) // 2
            if sum(p // k for p in piles) <= h:     # floor instead of ceiling
                hi = k
            else:
                lo = k + 1
        return lo
''',
        '''class Solution:
    def minEatingSpeed(self, piles, h):
        return max(1, -(-sum(piles) // h))          # ignores that a pile can't be shared between hours
''',
    ],
    guide=dict(
        prereqs="Lesson *Binary search on the answer*; ceiling division `(a + b - 1) // b`.",
        intuition="""
Ask a yes/no question about a candidate speed `k`: *"can she finish within `h` hours?"* That answer is
**monotone** — if speed `k` works, every faster speed works too. So the answers look like
`no no no … no yes yes yes`, and we want the first `yes`: a lower-bound binary search over `k ∈ [1, max(piles)]`.

At speed `k` pile `p` takes `⌈p / k⌉` hours.
""",
        hints=[
            "Given a speed k, how many hours does she need? Is that easy to compute?",
            "hours(k) = Σ ceil(p / k) is non-increasing in k. The answer is the smallest k with hours(k) <= h.",
            "Binary search k in [1, max(piles)] with lo < hi: if feasible(mid) then hi = mid else lo = mid + 1.",
        ],
        brute_force="Try `k = 1, 2, 3, …` until feasible: up to `max(piles)` = 10⁹ candidates × n piles. Hopeless.",
        approach="""
**Dry run** `[3,6,7,11], h = 8`, range [1, 11]:

| lo | hi | k | hours | feasible? |
|---|---|---|---|---|
| 1 | 11 | 6 | 1+1+2+2 = 6 | yes → hi = 6 |
| 1 | 6 | 3 | 1+2+3+4 = 10 | no → lo = 4 |
| 4 | 6 | 5 | 1+2+2+3 = 8 | yes → hi = 5 |
| 4 | 5 | 4 | 1+2+2+3 = 8 | yes → hi = 4 |

`lo == hi == 4` → answer 4.
""",
        complexity="Time **O(n · log(max(piles)))** ≈ 10⁴ × 30. Space **O(1)**.",
        pitfalls="""
- Ceiling division, not floor: a pile of 7 at speed 4 takes 2 hours.
- Lower bound is 1 (not 0 — division by zero); upper bound `max(piles)` always works because `h >= len(piles)`.
- With `lo < hi` and `hi = mid`, use `mid = (lo + hi) // 2` (rounds down) so the range always shrinks.
""",
        follow_up="Identical skeleton: *Capacity to Ship Packages* (1011), *Split Array Largest Sum* (410), *Minimum Number of Days to Make m Bouquets* (1482).",
    ),
),
# ---------------------------------------------------------------- 153
dict(
    id="find-minimum-in-rotated-sorted-array",
    title="Find Minimum in Rotated Sorted Array",
    difficulty="Medium",
    pattern="Binary Search",
    leetcode=LC.format("find-minimum-in-rotated-sorted-array"),
    neetcode=NC.format("find-minimum-in-rotated-sorted-array"),
    entry="findMin",
    description=r"""
A strictly increasing list was **rotated** some number of times (possibly zero): rotating once moves the last
element to the front, so `[0,1,2,4,5,6,7]` can become `[4,5,6,7,0,1,2]`. Given the rotated list `nums` (all
values distinct), return its minimum in **O(log n)** time.

**Constraints**

- `1 <= len(nums) <= 5000` (big tests go to 10^4)
- values distinct

**Example 1:** `[3,4,5,1,2]` → `1`.

**Example 2:** `[11,13,15,17]` → `11` (not rotated at all).
""",
    starter='''class Solution:
    def findMin(self, nums: List[int]) -> int:
        pass
''',
    solution='''class Solution:
    def findMin(self, nums):
        lo, hi = 0, len(nums) - 1
        while lo < hi:
            mid = (lo + hi) // 2
            if nums[mid] > nums[hi]:
                lo = mid + 1
            else:
                hi = mid
        return nums[lo]
''',
    tests=[
        [[3, 4, 5, 1, 2]],
        [[4, 5, 6, 7, 0, 1, 2]],
        [[11, 13, 15, 17]],
        [[1]],
        [[2, 1]],
        [[1, 2]],
        [[5, 1, 2, 3, 4]],
        [[2, 3, 4, 5, 1]],
        [[3, 1, 2]],
        [[-5, -3, -10, -8]],
        [_rot_big],
        [_rot_big2],
        [_rot_base],
    ],
    wrong_solutions=[
        '''class Solution:
    def findMin(self, nums):
        lo, hi = 0, len(nums) - 1
        while lo < hi:
            mid = (lo + hi) // 2
            if nums[mid] >= nums[lo]:          # compares with the left end
                lo = mid + 1
            else:
                hi = mid
        return nums[lo]
''',
        '''class Solution:
    def findMin(self, nums):
        for i in range(1, len(nums)):
            if nums[i] < nums[i - 1]:
                return nums[i]
        return nums[-1]                        # bug: unrotated array returns the max
''',
    ],
    guide=dict(
        prereqs="Binary search with the `lo < hi`, `hi = mid` template (lesson 3: rotated arrays).",
        intuition="""
A rotated sorted array is two increasing runs, and every value of the left run is larger than every value of
the right run. Compare `nums[mid]` with `nums[hi]`:

- `nums[mid] > nums[hi]` → `mid` is in the left (high) run, the minimum is strictly to the right: `lo = mid + 1`;
- otherwise `mid` is in the right run (or the array is unrotated), the minimum is at `mid` or to its left: `hi = mid`.

The range shrinks until `lo == hi` — that index is the minimum.
""",
        hints=[
            "Draw the array as two rising slopes. Where is the minimum?",
            "Compare nums[mid] with nums[hi]. Which comparison reliably tells you which slope mid is on?",
            "lo < hi loop; if nums[mid] > nums[hi]: lo = mid + 1 else hi = mid. Return nums[lo].",
        ],
        brute_force="`min(nums)` — **O(n)**. Correct but ignores the O(log n) requirement.",
        approach="""
**Dry run** `[4,5,6,7,0,1,2]`: (0,6) mid 3: 7 > 2 → lo 4; (4,6) mid 5: 1 ≤ 2 → hi 5; (4,5) mid 4: 0 ≤ 1 → hi 4. Answer `nums[4] = 0`.
""",
        complexity="Time **O(log n)**, space **O(1)**.",
        pitfalls="""
- Comparing with `nums[lo]` is ambiguous: in an unrotated array `nums[mid] >= nums[lo]` holds but the minimum is on the left.
- With `hi = mid` you must loop on `lo < hi`, not `lo <= hi` (infinite loop).
- With duplicates (LeetCode 154) the `nums[mid] == nums[hi]` case forces `hi -= 1`, degrading to O(n) worst case.
""",
        follow_up="The minimum's index is the **rotation count** — the first step of the two-pass solution to *Search in Rotated Sorted Array*.",
    ),
),
# ---------------------------------------------------------------- 33
dict(
    id="search-in-rotated-sorted-array",
    title="Search in Rotated Sorted Array",
    difficulty="Medium",
    pattern="Binary Search",
    leetcode=LC.format("search-in-rotated-sorted-array"),
    neetcode=NC.format("find-target-in-rotated-sorted-array"),
    entry="search",
    description=r"""
`nums` is a strictly increasing list of distinct integers that may have been rotated at an unknown pivot
(e.g. `[0,1,2,4,5,6,7]` → `[4,5,6,7,0,1,2]`). Return the index of `target`, or `-1` if absent, in
**O(log n)** time.

**Constraints**

- `1 <= len(nums) <= 5000` (big tests go to 10^4)
- values distinct

**Example 1:** `nums = [4,5,6,7,0,1,2], target = 0` → `4`.

**Example 2:** `nums = [4,5,6,7,0,1,2], target = 3` → `-1`.
""",
    starter='''class Solution:
    def search(self, nums: List[int], target: int) -> int:
        pass
''',
    solution='''class Solution:
    def search(self, nums, target):
        lo, hi = 0, len(nums) - 1
        while lo <= hi:
            mid = (lo + hi) // 2
            if nums[mid] == target:
                return mid
            if nums[lo] <= nums[mid]:                 # left half sorted
                if nums[lo] <= target < nums[mid]:
                    hi = mid - 1
                else:
                    lo = mid + 1
            else:                                     # right half sorted
                if nums[mid] < target <= nums[hi]:
                    lo = mid + 1
                else:
                    hi = mid - 1
        return -1
''',
    tests=[
        [[4, 5, 6, 7, 0, 1, 2], 0],
        [[4, 5, 6, 7, 0, 1, 2], 3],
        [[1], 0],
        [[1], 1],
        [[3, 1], 1],
        [[3, 1], 3],
        [[1, 3], 3],
        [[5, 1, 3], 5],
        [[5, 1, 3], 3],
        [[4, 5, 6, 7, 8, 1, 2, 3], 8],
        [[6, 7, 1, 2, 3, 4, 5], 6],
        [_rot_big, _rot_base[5]],
        [_rot_big, _rot_base[9000]],
        [_rot_big2, _rot_base[0] - 1],
    ],
    wrong_solutions=[
        '''class Solution:
    def search(self, nums, target):
        lo, hi = 0, len(nums) - 1
        while lo <= hi:
            mid = (lo + hi) // 2
            if nums[mid] == target: return mid
            if nums[lo] < nums[mid]:                  # bug: should be <=
                if nums[lo] <= target < nums[mid]: hi = mid - 1
                else: lo = mid + 1
            else:
                if nums[mid] < target <= nums[hi]: lo = mid + 1
                else: hi = mid - 1
        return -1
''',
        '''class Solution:
    def search(self, nums, target):
        import bisect
        i = bisect.bisect_left(nums, target)       # pretends the array is sorted
        return i if i < len(nums) and nums[i] == target else -1
''',
    ],
    guide=dict(
        prereqs="*Find Minimum in Rotated Sorted Array*; closed-interval binary search.",
        intuition="""
Cut a rotated array at `mid` and **at least one half is perfectly sorted**. Detect which: if
`nums[lo] <= nums[mid]` the left half `[lo..mid]` is sorted, otherwise the right half `[mid..hi]` is. For the
sorted half you can test with a simple range check whether `target` is inside; if yes, search there, otherwise
search the other half.
""",
        hints=[
            "Split at mid. Can both halves contain the rotation point?",
            "No — at least one half is sorted. You can tell which by comparing nums[lo] with nums[mid].",
            "If the left half is sorted and nums[lo] <= target < nums[mid], go left; else go right. Mirror for a sorted right half.",
        ],
        brute_force="`nums.index(target)` — **O(n)**. Alternative O(log n) approach: find the rotation point (minimum) first, then binary-search the correct run.",
        approach="""
**Dry run** `[4,5,6,7,0,1,2]`, target 0:

| lo | hi | mid | nums[mid] | sorted half | target in it? | next |
|---|---|---|---|---|---|---|
| 0 | 6 | 3 | 7 | left [4..7] | no | lo = 4 |
| 4 | 6 | 5 | 1 | left [0..1] | 0 ≤ 0 < 1 yes | hi = 4 |
| 4 | 4 | 4 | 0 | found | | return 4 |
""",
        complexity="Time **O(log n)**, space **O(1)**.",
        pitfalls="""
- `nums[lo] <= nums[mid]` needs `<=`: when `lo == mid` (two elements left) the one-element left half is sorted.
- Range checks are half-open on the `mid` side because `mid` was already compared.
- Duplicates (LeetCode 81) break the "which half is sorted" test.
""",
        follow_up="*Search in Rotated Sorted Array II* (81, duplicates) and searching a rotated array for the first element ≥ target.",
    ),
),
# ---------------------------------------------------------------- 981
dict(
    id="time-based-key-value-store",
    title="Time Based Key-Value Store",
    difficulty="Medium",
    pattern="Binary Search",
    leetcode=LC.format("time-based-key-value-store"),
    neetcode=NC.format("time-based-key-value-store"),
    kind="class",
    entry="TimeMap",
    description=r"""
Design a class `TimeMap` that stores several values per key, each stamped with a time, and can answer "what was
the value at time `t`?":

- `TimeMap()` — initialise.
- `set(key, value, timestamp)` — store `value` for `key` at `timestamp`.
- `get(key, timestamp)` — return the value stored for `key` at the **largest stored timestamp `<= timestamp`**;
  return `""` if there is none.

Timestamps passed to `set` are **strictly increasing** across all calls.

**Constraints**

- `1 <= timestamp <= 10^7`, up to `2·10^5` calls in total

**Example:**

```
ops  = ["TimeMap","set",            "get",      "get",      "set",             "get",      "get"]
args = [[],       ["foo","bar",1],  ["foo",1],  ["foo",3],  ["foo","bar2",4],  ["foo",4],  ["foo",5]]
out  = [null,     null,             "bar",      "bar",      null,              "bar2",     "bar2"]
```
""",
    starter='''class TimeMap:

    def __init__(self):
        pass

    def set(self, key: str, value: str, timestamp: int) -> None:
        pass

    def get(self, key: str, timestamp: int) -> str:
        pass
''',
    solution='''import bisect

class TimeMap:
    def __init__(self):
        self.times = {}
        self.vals = {}

    def set(self, key, value, timestamp):
        self.times.setdefault(key, []).append(timestamp)
        self.vals.setdefault(key, []).append(value)

    def get(self, key, timestamp):
        ts = self.times.get(key)
        if not ts:
            return ""
        i = bisect.bisect_right(ts, timestamp) - 1
        return self.vals[key][i] if i >= 0 else ""
''',
    tests=[
        [["TimeMap", "set", "get", "get", "set", "get", "get"],
         [[], ["foo", "bar", 1], ["foo", 1], ["foo", 3], ["foo", "bar2", 4], ["foo", 4], ["foo", 5]]],
        [["TimeMap", "get"], [[], ["a", 1]]],
        [["TimeMap", "set", "get"], [[], ["a", "x", 5], ["a", 4]]],
        [["TimeMap", "set", "set", "get", "get", "get"], [[], ["a", "x", 2], ["b", "y", 3], ["a", 3], ["b", 2], ["c", 9]]],
        [["TimeMap", "set", "set", "set", "get", "get", "get", "get"],
         [[], ["k", "v1", 10], ["k", "v2", 20], ["k", "v3", 30], ["k", 9], ["k", 10], ["k", 25], ["k", 1000]]],
        [["TimeMap", "set", "set", "get", "get", "get", "get", "get", "get"],
         [[], ["love", "high", 10], ["love", "low", 20], ["love", 5], ["love", 10], ["love", 15], ["love", 20], ["love", 25], ["hate", 25]]],
        _timemap_ops(300, R),
        _timemap_ops(4000, R),
        _timemap_one_key(3000),
    ],
    wrong_solutions=[
        '''class TimeMap:
    def __init__(self):
        self.d = {}
    def set(self, key, value, timestamp):
        self.d[(key, timestamp)] = value
    def get(self, key, timestamp):
        return self.d.get((key, timestamp), "")      # exact timestamps only
''',
        '''import bisect
class TimeMap:
    def __init__(self):
        self.d = {}
    def set(self, key, value, timestamp):
        self.d.setdefault(key, []).append((timestamp, value))
    def get(self, key, timestamp):
        a = self.d.get(key, [])
        i = bisect.bisect_left([t for t, _ in a], timestamp) - 1   # misses equal timestamps
        return a[i][1] if i >= 0 else ""
''',
    ],
    guide=dict(
        prereqs="Dicts of lists; `bisect_right` / upper bound (lesson *Binary search done right*).",
        intuition="""
Because `set` timestamps arrive in increasing order, each key's list of timestamps is **already sorted** —
appending keeps it sorted for free. A `get` is then "find the last timestamp `<= t`", which is
`bisect_right(ts, t) - 1`: the upper bound minus one.
""",
        hints=[
            "Per key, store (timestamp, value) pairs. In what order do they arrive?",
            "Sorted by time — so you can binary-search them instead of scanning.",
            "Keep parallel lists per key: times and values. get → i = bisect_right(times, t) - 1; return values[i] if i >= 0 else ''.",
        ],
        brute_force="Scan a key's list backwards in `get`: **O(n)** per query, O(n²) overall. The one-key test with 3 000 sets and 3 000 gets makes that ~8·10⁶ steps; LeetCode's 2·10⁵ calls would be ~10¹⁰.",
        approach="""
**Dry run** `love`: times `[10, 20]`, values `[high, low]`.

| get t | bisect_right | i | answer |
|---|---|---|---|
| 5 | 0 | −1 | "" |
| 10 | 1 | 0 | high |
| 15 | 1 | 0 | high |
| 20 | 2 | 1 | low |
| 25 | 2 | 1 | low |

Keeping separate `times` lists avoids building `[t for t, _ in pairs]` on every query (that would be O(n)).
""",
        complexity="`set` **O(1)** amortized, `get` **O(log n)**. Space **O(total sets)**.",
        pitfalls="""
- `bisect_left` finds the first timestamp `>= t`; you want the last `<= t` → `bisect_right - 1`.
- Rebuilding a list of timestamps inside `get` silently turns it into O(n).
- Unknown keys return `""`.
""",
        follow_up="If timestamps could arrive out of order you'd need a sorted container (e.g. `sortedcontainers.SortedList`) or a balanced BST — see *Stock Price Fluctuation* (2034).",
    ),
),
# ---------------------------------------------------------------- 4
dict(
    id="median-of-two-sorted-arrays",
    title="Median of Two Sorted Arrays",
    difficulty="Hard",
    pattern="Binary Search",
    leetcode=LC.format("median-of-two-sorted-arrays"),
    neetcode=NC.format("median-of-two-sorted-arrays"),
    entry="findMedianSortedArrays",
    compare="float",
    description=r"""
Given two sorted lists `nums1` (length `m`) and `nums2` (length `n`), return the **median** of all `m + n` values
together, as a float. (For an even total, the median is the mean of the two middle values.)

Aim for **O(log(min(m, n)))** time.

**Constraints**

- `0 <= m, n <= 1000` in LeetCode (big tests are larger), `1 <= m + n`
- `-10^6 <= value <= 10^6`

**Example 1:** `nums1 = [1,3], nums2 = [2]` → `2.0`.

**Example 2:** `nums1 = [1,2], nums2 = [3,4]` → `2.5`.
""",
    starter='''class Solution:
    def findMedianSortedArrays(self, nums1: List[int], nums2: List[int]) -> float:
        pass
''',
    solution='''class Solution:
    def findMedianSortedArrays(self, nums1, nums2):
        A, B = nums1, nums2
        if len(A) > len(B):
            A, B = B, A
        m, n = len(A), len(B)
        half = (m + n + 1) // 2
        lo, hi = 0, m
        INF = float("inf")
        while True:
            i = (lo + hi) // 2          # elements taken from A
            j = half - i                # elements taken from B
            a_left = A[i - 1] if i > 0 else -INF
            a_right = A[i] if i < m else INF
            b_left = B[j - 1] if j > 0 else -INF
            b_right = B[j] if j < n else INF
            if a_left <= b_right and b_left <= a_right:
                if (m + n) % 2:
                    return float(max(a_left, b_left))
                return (max(a_left, b_left) + min(a_right, b_right)) / 2
            if a_left > b_right:
                hi = i - 1
            else:
                lo = i + 1
''',
    tests=[
        [[1, 3], [2]],
        [[1, 2], [3, 4]],
        [[], [1]],
        [[2], []],
        [[1, 1], [1, 1]],
        [[1, 2, 3], [4, 5, 6, 7]],
        [[4, 5, 6, 7], [1, 2, 3]],
        [[-5, 3, 6, 12, 15], [-12, -10, -6, -3, 4, 10]],
        [[1, 3, 5], [2, 4, 6]],
        [[100], [1, 2, 3, 4, 5]],
        [[0, 0], [0, 0, 0]],
        [_med_a, _med_b],
        [_med_a[:1], _med_b],
    ],
    wrong_solutions=[
        '''class Solution:
    def findMedianSortedArrays(self, nums1, nums2):
        def med(a):
            n = len(a)
            return a[n // 2] if n % 2 else (a[n // 2 - 1] + a[n // 2]) / 2
        if not nums1: return float(med(nums2))
        if not nums2: return float(med(nums1))
        return (med(nums1) + med(nums2)) / 2      # mean of the medians
''',
        '''class Solution:
    def findMedianSortedArrays(self, nums1, nums2):
        c = sorted(nums1 + nums2)
        return float(c[len(c) // 2])               # ignores even totals
''',
    ],
    guide=dict(
        prereqs="Lesson *Rotated arrays, 2-D matrices and partitions* (partition binary search); comfort with ±∞ sentinels.",
        intuition="""
The median splits the merged list into a **left half** and a **right half** of equal size (left gets the extra
one when the total is odd). Suppose the left half takes `i` elements from `A` and `j = half − i` from `B`. The
split is correct exactly when everything on the left is ≤ everything on the right — and since `A` and `B` are
sorted, that reduces to two **cross** checks:

$$A[i-1] \\le B[j] \\quad\\text{and}\\quad B[j-1] \\le A[i].$$

If `A[i-1] > B[j]` we took too many from `A` → decrease `i`; otherwise increase it. Binary-search `i` over
`[0, m]` on the **shorter** array.
""",
        hints=[
            "Merging costs O(m+n). Instead, think about choosing how many elements of the left half come from nums1.",
            "If i come from A, then half − i come from B. The choice is valid when A[i−1] <= B[j] and B[j−1] <= A[i].",
            "Binary-search i in [0, len(shorter)] using ±infinity for out-of-range neighbours. Median = max(left sides) or the average with min(right sides).",
        ],
        brute_force="Merge both arrays (two pointers) and pick the middle: **O(m + n)** time and space. Perfectly acceptable in practice, but not the O(log) the problem asks for.",
        approach="""
**Dry run** `A = [1,3]`, `B = [2]` (swap so A is shorter: A = [2], B = [1,3]); total 3, half 2.

| lo | hi | i | j | a_left | a_right | b_left | b_right | valid? |
|---|---|---|---|---|---|---|---|---|
| 0 | 1 | 0 | 2 | −∞ | 2 | 3 | ∞ | b_left 3 > a_right 2 → lo = 1 |
| 1 | 1 | 1 | 1 | 2 | ∞ | 1 | 3 | yes |

Odd total → median = max(2, 1) = **2.0**.
""",
        complexity="Time **O(log min(m, n))**, space **O(1)**.",
        pitfalls="""
- Always search the **shorter** array, otherwise `j` can go negative.
- Use −∞/+∞ when `i` or `j` is 0 or at the end.
- Return a float even for odd totals.
- `half = (m + n + 1) // 2` puts the extra element on the left, so the odd-total median is `max(left)`.
""",
        follow_up="The general tool is *k-th smallest of two sorted arrays* (eliminate k/2 elements per step). *Find Median from Data Stream* (295) uses two heaps instead.",
    ),
),
# ---------------------------------------------------------------- 35
dict(
    id="search-insert-position",
    title="Search Insert Position",
    difficulty="Easy",
    pattern="Binary Search",
    leetcode=LC.format("search-insert-position"),
    entry="searchInsert",
    description=r"""
`nums` is sorted in increasing order with distinct values. Return the index of `target` if it is present;
otherwise return the index where it would have to be inserted to keep the list sorted. Run in **O(log n)**.

**Constraints**

- `1 <= len(nums) <= 10^4` (big tests go to 10^4)

**Example 1:** `nums = [1,3,5,6], target = 5` → `2`.

**Example 2:** `nums = [1,3,5,6], target = 2` → `1`.

**Example 3:** `nums = [1,3,5,6], target = 7` → `4`.
""",
    starter='''class Solution:
    def searchInsert(self, nums: List[int], target: int) -> int:
        pass
''',
    solution='''class Solution:
    def searchInsert(self, nums, target):
        lo, hi = 0, len(nums)
        while lo < hi:
            mid = (lo + hi) // 2
            if nums[mid] < target:
                lo = mid + 1
            else:
                hi = mid
        return lo
''',
    tests=[
        [[1, 3, 5, 6], 5],
        [[1, 3, 5, 6], 2],
        [[1, 3, 5, 6], 7],
        [[1, 3, 5, 6], 0],
        [[1], 0],
        [[1], 1],
        [[1], 2],
        [[1, 3], 3],
        [[-10, -3, 0, 9], -4],
        [[2, 4, 6, 8, 10], 9],
        [_bs_big, _bs_big[-1] + 5],
        [_bs_big, _bs_big[7000] + 1 if _bs_big[7000] + 1 != _bs_big[7001] else _bs_big[7000]],
        [_bs_big, _bs_big[0]],
    ],
    wrong_solutions=[
        '''class Solution:
    def searchInsert(self, nums, target):
        lo, hi = 0, len(nums) - 1
        while lo < hi:                       # hi starts one too small: can't return len(nums)
            mid = (lo + hi) // 2
            if nums[mid] < target: lo = mid + 1
            else: hi = mid
        return lo
''',
        '''class Solution:
    def searchInsert(self, nums, target):
        lo, hi = 0, len(nums) - 1
        while lo <= hi:
            mid = (lo + hi) // 2
            if nums[mid] == target: return mid
            if nums[mid] < target: lo = mid + 1
            else: hi = mid - 1
        return hi                            # should return lo
''',
    ],
    guide=dict(
        prereqs="The **lower bound** template from lesson *Binary search done right*.",
        intuition="The answer is the **first index whose value is `>= target`** — that's `lower_bound`, a.k.a. `bisect.bisect_left`. If the target exists, that is its index; if not, that's where it slots in.",
        hints=[
            "Is 'index of target or insertion point' a single question?",
            "Yes: the first index i with nums[i] >= target (len(nums) if none).",
            "Half-open search lo=0, hi=len(nums); while lo < hi: if nums[mid] < target: lo = mid+1 else hi = mid. Return lo.",
        ],
        brute_force="Scan for the first `nums[i] >= target`: **O(n)**.",
        approach="""
**Dry run** `[1,3,5,6]`, target 2: (0,4) mid 2: 5 ≥ 2 → hi 2; (0,2) mid 1: 3 ≥ 2 → hi 1; (0,1) mid 0: 1 < 2 → lo 1. Return **1**.

Target 7: lo keeps moving right until lo = hi = 4 → return 4 (append position).
""",
        complexity="Time **O(log n)**, space **O(1)**.",
        pitfalls="- `hi` must start at `len(nums)` so the answer *after the last element* is reachable.\n- If you use the closed-interval search, the insertion point after the loop is `lo`, not `hi`.",
        follow_up="One-liner: `return bisect.bisect_left(nums, target)`.",
    ),
),
# ---------------------------------------------------------------- 34
dict(
    id="find-first-and-last-position-of-element-in-sorted-array",
    title="Find First and Last Position of Element in Sorted Array",
    difficulty="Medium",
    pattern="Binary Search",
    leetcode=LC.format("find-first-and-last-position-of-element-in-sorted-array"),
    entry="searchRange",
    description=r"""
`nums` is sorted in non-decreasing order and may contain **duplicates**. Return `[first, last]` — the first and
last index where `target` occurs — or `[-1, -1]` if it does not occur. Run in **O(log n)**.

**Constraints**

- `0 <= len(nums) <= 10^5`

**Example 1:** `nums = [5,7,7,8,8,10], target = 8` → `[3,4]`.

**Example 2:** `nums = [5,7,7,8,8,10], target = 6` → `[-1,-1]`.

**Example 3:** `nums = [], target = 0` → `[-1,-1]`.
""",
    starter='''class Solution:
    def searchRange(self, nums: List[int], target: int) -> List[int]:
        pass
''',
    solution='''class Solution:
    def searchRange(self, nums, target):
        def lower(x):
            lo, hi = 0, len(nums)
            while lo < hi:
                mid = (lo + hi) // 2
                if nums[mid] < x:
                    lo = mid + 1
                else:
                    hi = mid
            return lo
        a = lower(target)
        if a == len(nums) or nums[a] != target:
            return [-1, -1]
        return [a, lower(target + 1) - 1]
''',
    tests=[
        [[5, 7, 7, 8, 8, 10], 8],
        [[5, 7, 7, 8, 8, 10], 6],
        [[], 0],
        [[1], 1],
        [[1], 0],
        [[2, 2], 2],
        [[1, 2, 3], 3],
        [[1, 1, 1, 1, 1], 1],
        [[1, 2, 2, 2, 3], 2],
        [[1, 3], 2],
        [[0, 0, 1, 1, 1, 4, 5, 5], 5],
        [_range_big, _range_big[15000]],
        [_range_big, 2001],
        [[7] * 20000, 7],
    ],
    wrong_solutions=[
        '''class Solution:
    def searchRange(self, nums, target):
        import bisect
        a = bisect.bisect_left(nums, target)
        if a == len(nums) or nums[a] != target:
            return [-1, -1]
        return [a, bisect.bisect_right(nums, target)]     # off by one
''',
        '''class Solution:
    def searchRange(self, nums, target):
        lo, hi = 0, len(nums) - 1
        while lo <= hi:
            mid = (lo + hi) // 2
            if nums[mid] == target:
                return [mid, mid]                          # any occurrence, not first/last
            if nums[mid] < target: lo = mid + 1
            else: hi = mid - 1
        return [-1, -1]
''',
    ],
    guide=dict(
        prereqs="`lower_bound` / `upper_bound` (lesson *Binary search done right*).",
        intuition="""
- first occurrence = **lower bound**: first index with `nums[i] >= target`;
- last occurrence = **upper bound − 1**: (first index with `nums[i] > target`) − 1.

For integers, `upper_bound(t) == lower_bound(t + 1)`, so one helper suffices.
""",
        hints=[
            "Finding *an* occurrence is easy. What exact boundary does 'first occurrence' correspond to?",
            "first = lower_bound(target). last = upper_bound(target) − 1.",
            "Write one lower-bound function; call it with target and target+1. Check nums[first] == target before trusting it.",
        ],
        brute_force="Find any occurrence by binary search and then walk left and right: **O(log n + k)** where k is the number of copies — O(n) on `[7,7,7,…]`.",
        approach="""
**Dry run** `[5,7,7,8,8,10]`, target 8: `lower(8)` → 3; `nums[3] == 8` ✓; `lower(9)` → 5, minus 1 → 4. Answer `[3,4]`.
""",
        complexity="Time **O(log n)** (two searches), space **O(1)**.",
        pitfalls="""
- `bisect_right` returns one past the last occurrence — subtract 1.
- Check `a < len(nums)` before reading `nums[a]`.
- Empty list.
""",
        follow_up="Count of occurrences = `bisect_right − bisect_left`. Same idea answers range-count queries on a sorted list.",
    ),
),
# ---------------------------------------------------------------- 1011
dict(
    id="capacity-to-ship-packages-within-d-days",
    title="Capacity To Ship Packages Within D Days",
    difficulty="Medium",
    pattern="Binary Search on Answer",
    leetcode=LC.format("capacity-to-ship-packages-within-d-days"),
    entry="shipWithinDays",
    description=r"""
Packages on a conveyor belt must be shipped **in the given order**; `weights[i]` is the weight of package `i`.
Each day the ship is loaded with a consecutive run of packages whose total weight does not exceed the ship's
capacity, then departs. Return the **smallest capacity** that ships everything within `days` days.

**Constraints**

- `1 <= days <= len(weights) <= 5·10^4`
- `1 <= weights[i] <= 500`

**Example 1:** `weights = [1,2,3,4,5,6,7,8,9,10], days = 5` → `15`
(`[1..5] [6,7] [8] [9] [10]`).

**Example 2:** `weights = [3,2,2,4,1,4], days = 3` → `6`.
""",
    starter='''class Solution:
    def shipWithinDays(self, weights: List[int], days: int) -> int:
        pass
''',
    solution='''class Solution:
    def shipWithinDays(self, weights, days):
        def need(cap):
            d, load = 1, 0
            for w in weights:
                if load + w > cap:
                    d += 1
                    load = 0
                load += w
            return d
        lo, hi = max(weights), sum(weights)
        while lo < hi:
            mid = (lo + hi) // 2
            if need(mid) <= days:
                hi = mid
            else:
                lo = mid + 1
        return lo
''',
    tests=[
        [[1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 5],
        [[3, 2, 2, 4, 1, 4], 3],
        [[1, 2, 3, 1, 1], 4],
        [[5], 1],
        [[1, 1, 1, 1], 4],
        [[1, 1, 1, 1], 1],
        [[10, 50, 100, 100, 50, 100, 100, 100], 5],
        [[500, 1, 1, 1], 2],
        [[1, 2, 3, 4, 5], 2],
        [_ship_big, 1],
        [_ship_big, 37],
        [_ship_big, 20000],
        [_ship_big, 777],
    ],
    wrong_solutions=[
        '''class Solution:
    def shipWithinDays(self, weights, days):
        def need(cap):
            d, load = 1, 0
            for w in weights:
                if load + w > cap:
                    d += 1; load = 0
                load += w
            return d
        lo, hi = 1, sum(weights)                 # lower bound too small: need() ignores w > cap
        while lo < hi:
            mid = (lo + hi) // 2
            if need(mid) <= days: hi = mid
            else: lo = mid + 1
        return lo
''',
        '''class Solution:
    def shipWithinDays(self, weights, days):
        return max(max(weights), -(-sum(weights) // days))   # average load ignores ordering
''',
    ],
    guide=dict(
        prereqs="*Koko Eating Bananas*; lesson *Binary search on the answer*.",
        intuition="""
Given a capacity, the **greedy** loading (fill each day until the next package would overflow) uses the
fewest days — so `need(cap)` is easy to compute in O(n). It is monotone: more capacity never needs more days.
Binary-search the smallest capacity with `need(cap) <= days`. The search space is `[max(weights), sum(weights)]`:
below the heaviest package nothing works, and the total weight always works in one day.
""",
        hints=[
            "If someone tells you the capacity, can you compute the number of days needed?",
            "Greedy: pack packages in order until the next one would exceed capacity, then start a new day. More capacity → fewer or equal days.",
            "Binary search capacity in [max(weights), sum(weights)] for the first value with need(cap) <= days.",
        ],
        brute_force="Try every capacity from `max(weights)` upward: up to `sum(weights)` ≈ 5·10⁶ candidates × O(n) each.",
        approach="""
**Dry run** `[3,2,2,4,1,4]`, days 3, range [4, 16]:

| lo | hi | mid | groups | days | |
|---|---|---|---|---|---|
| 4 | 16 | 10 | [3,2,2] [4,1,4] | 2 | hi = 10 |
| 4 | 10 | 7 | [3,2,2] [4,1] [4] | 3 | hi = 7 |
| 4 | 7 | 5 | [3,2] [2] [4,1] [4] | 4 | lo = 6 |
| 6 | 7 | 6 | [3,2] [2,4] [1,4] | 3 | hi = 6 |

Answer **6**.
""",
        complexity="Time **O(n · log(sum))**, space **O(1)**.",
        pitfalls="""
- Lower bound must be `max(weights)`; otherwise the greedy check must reject capacities smaller than a package.
- Order matters — you cannot rearrange packages, so `ceil(sum/days)` is only a lower bound, not the answer.
- Start the day counter at 1.
""",
        follow_up="*Split Array Largest Sum* (410) is the same problem with different words (and allows zeros).",
    ),
),
# ---------------------------------------------------------------- 410
dict(
    id="split-array-largest-sum",
    title="Split Array Largest Sum",
    difficulty="Hard",
    pattern="Binary Search on Answer",
    leetcode=LC.format("split-array-largest-sum"),
    entry="splitArray",
    description=r"""
Split the list `nums` of non-negative integers into exactly `k` non-empty **contiguous** pieces. Among all ways
to do this, minimise the largest piece-sum. Return that minimum.

**Constraints**

- `1 <= len(nums) <= 1000` (big tests go to 10^4)
- `0 <= nums[i] <= 10^6`
- `1 <= k <= min(50, len(nums))`

**Example 1:** `nums = [7,2,5,10,8], k = 2` → `18` (`[7,2,5] [10,8]`).

**Example 2:** `nums = [1,2,3,4,5], k = 2` → `9` (`[1,2,3] [4,5]`).
""",
    starter='''class Solution:
    def splitArray(self, nums: List[int], k: int) -> int:
        pass
''',
    solution='''class Solution:
    def splitArray(self, nums, k):
        def pieces(limit):
            cnt, s = 1, 0
            for x in nums:
                if s + x > limit:
                    cnt += 1
                    s = 0
                s += x
            return cnt
        lo, hi = max(nums), sum(nums)
        while lo < hi:
            mid = (lo + hi) // 2
            if pieces(mid) <= k:
                hi = mid
            else:
                lo = mid + 1
        return lo
''',
    tests=[
        [[7, 2, 5, 10, 8], 2],
        [[1, 2, 3, 4, 5], 2],
        [[1, 4, 4], 3],
        [[5], 1],
        [[0, 0, 0], 2],
        [[1, 2, 3, 4, 5], 5],
        [[1, 2, 3, 4, 5], 1],
        [[2, 3, 1, 2, 4, 3], 5],
        [[10, 5, 13, 4, 8, 4, 5, 11, 14, 9, 16, 10, 20, 8], 8],
        [[0, 7, 0, 0, 7, 0], 2],
        [_split_big, 50],
        [_split_big, 1],
        [_split_big, 7],
    ],
    wrong_solutions=[
        '''class Solution:
    def splitArray(self, nums, k):
        target = sum(nums) / k
        best, s = 0, 0
        for x in nums:                    # greedy "close to average" cut
            if s + x > target and s > 0:
                best = max(best, s); s = 0
            s += x
        return max(best, s)
''',
        '''class Solution:
    def splitArray(self, nums, k):
        def pieces(limit):
            cnt, s = 1, 0
            for x in nums:
                if s + x > limit:
                    cnt += 1; s = 0
                s += x
            return cnt
        lo, hi = 0, sum(nums)
        while lo < hi:
            mid = (lo + hi) // 2
            if pieces(mid) <= k: hi = mid
            else: lo = mid + 1
        return lo
''',
    ],
    guide=dict(
        prereqs="*Capacity To Ship Packages* — this is the same problem; lesson *Binary search on the answer*.",
        intuition="""
Turn the optimisation into a decision: *"can we split into at most `k` pieces with every sum ≤ `L`?"* Greedy
answers it (extend the current piece until it would exceed `L`). Feasibility is monotone in `L`, so binary-search
the smallest feasible `L` in `[max(nums), sum(nums)]`. "At most `k`" is enough: any split into fewer pieces can be
cut further without increasing the maximum (pieces are non-empty because `k <= len(nums)`).
""",
        hints=[
            "Guessing the answer L — can you check if it's achievable?",
            "Greedy: start a new piece whenever adding the next number would exceed L. Count pieces; feasible if count <= k.",
            "Binary search L over [max(nums), sum(nums)] for the smallest feasible value.",
        ],
        brute_force="DP over (prefix, pieces): `dp[i][j] = min over p of max(dp[p][j-1], sum(p..i))` — **O(k · n²)**, 5·10⁹ for the large test. (Fine for the original 1000×50 constraints, but the binary search is far simpler.)",
        approach="""
**Dry run** `[7,2,5,10,8]`, k = 2, range [10, 32]:

| lo | hi | mid | pieces | |
|---|---|---|---|---|
| 10 | 32 | 21 | [7,2,5] [10,8] → 2 | hi = 21 |
| 10 | 21 | 15 | [7,2,5] [10] [8] → 3 | lo = 16 |
| 16 | 21 | 18 | [7,2,5] [10,8] → 2 | hi = 18 |
| 16 | 18 | 17 | [7,2,5] [10] [8] → 3 | lo = 18 |

Answer **18**.
""",
        complexity="Time **O(n · log(sum))**, space **O(1)**.",
        pitfalls="""
- Lower bound 0 breaks the greedy check when one element exceeds the limit.
- Splitting near `sum/k` greedily is not optimal.
- Zeros are allowed — pieces can have sum 0.
""",
        follow_up="*Minimize the maximum* / *maximize the minimum* phrases almost always signal binary search on the answer: *Magnetic Force Between Two Balls* (1552), *Minimized Maximum of Products Distributed to Any Store* (2064).",
    ),
),
# ---------------------------------------------------------------- 69
dict(
    id="sqrtx",
    title="Sqrt(x)",
    difficulty="Easy",
    pattern="Binary Search on Answer",
    leetcode=LC.format("sqrtx"),
    entry="mySqrt",
    description=r"""
Given a non-negative integer `x`, return $\lfloor \sqrt{x} \rfloor$ — the square root rounded **down** to an
integer. Do not use a built-in exponent or square-root function (`x ** 0.5`, `math.sqrt`, `math.isqrt`).

**Constraints**

- `0 <= x <= 2^31 - 1` (one test goes further to punish floating point)

**Example 1:** `x = 4` → `2`.

**Example 2:** `x = 8` → `2` (√8 ≈ 2.83).
""",
    starter='''class Solution:
    def mySqrt(self, x: int) -> int:
        pass
''',
    solution='''class Solution:
    def mySqrt(self, x):
        lo, hi = 0, x
        while lo < hi:
            mid = (lo + hi + 1) // 2      # upper mid: we search the LAST k with k*k <= x
            if mid * mid <= x:
                lo = mid
            else:
                hi = mid - 1
        return lo
''',
    tests=[
        [4], [8], [0], [1], [2], [3], [15], [16], [17], [2147395599], [2147483647],
        [10 ** 18 - 1], [999999999999999999999999999999],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def mySqrt(self, x):
        return int(x ** 0.5)               # float rounding fails on huge x
''',
        '''class Solution:
    def mySqrt(self, x):
        lo, hi = 0, x
        while lo < hi:
            mid = (lo + hi) // 2
            if mid * mid < x: lo = mid + 1
            else: hi = mid
        return lo                          # this is ceil(sqrt) for non-squares
''',
    ],
    guide=dict(
        prereqs="Binary search for the *last* true value (upper-mid template).",
        intuition="""
`k*k <= x` is true for `k = 0, 1, …, ⌊√x⌋` and false afterwards: `yes yes … yes no no`. We want the **last
yes**. That's the mirror image of lower bound, and it needs the *upper* midpoint `(lo + hi + 1) // 2` so that
`lo = mid` always makes progress.
""",
        hints=[
            "For which k is k*k <= x true? What shape does that set have?",
            "A prefix of 0, 1, 2, …: you want its last element.",
            "lo=0, hi=x; while lo < hi: mid=(lo+hi+1)//2; if mid*mid <= x: lo = mid else hi = mid-1.",
        ],
        brute_force="Increment `k` while `(k+1)² <= x`: **O(√x)** — 46 341 steps for 2³¹, 10¹⁵ steps for the 10³⁰ test.",
        approach="""
**Dry run** `x = 8`: (0,8) mid 4: 16 > 8 → hi 3; (0,3) mid 2: 4 ≤ 8 → lo 2; (2,3) mid 3: 9 > 8 → hi 2. Answer **2**.

With the *lower* midpoint `(lo+hi)//2`, the state `(2,3)` would pick mid 2, set `lo = 2` and loop forever.
""",
        complexity="Time **O(log x)**, space **O(1)**. (Newton's method converges faster: `r = (r + x // r) // 2`.)",
        pitfalls="""
- `int(x ** 0.5)` is off by one for large `x` because doubles have 53 bits of precision.
- With `lo = mid` you must use the upper midpoint.
- `x = 0` and `x = 1` should return themselves.
""",
        follow_up="*Valid Perfect Square* (367); integer k-th roots; Newton's method.",
    ),
),
]
