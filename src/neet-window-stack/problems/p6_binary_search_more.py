import random

R = random.Random(99003)
LC = "https://leetcode.com/problems/{}/"

_peak_big = [R.randint(-10 ** 6, 10 ** 6) for _ in range(12000)]
for _i in range(1, len(_peak_big)):               # neighbours must differ
    if _peak_big[_i] == _peak_big[_i - 1]:
        _peak_big[_i] += 1
_peak_inc = list(range(12000))


def _single(n_pairs, pos, rng):
    vals = sorted(rng.sample(range(-10 ** 6, 10 ** 6), n_pairs + 1))
    out = []
    for i, v in enumerate(vals):
        out.append(v)
        if i != pos:
            out.append(v)
    return out


_single_big = _single(6000, 4321, R)
_single_first = _single(6000, 0, R)
_single_last = _single(6000, 6000, R)

_rot2_base = sorted(R.randint(0, 3000) for _ in range(15000))
_rot2_big = _rot2_base[9000:] + _rot2_base[:9000]
_rot2_flat = [1] * 12000 + [0] + [1] * 3000

_mountain_big = list(range(0, 15000)) + list(range(15000, 5000, -2))
_mountain_left = [0] + list(range(20000, 0, -1))

_kc_big = sorted(R.randint(-10 ** 4, 10 ** 4) for _ in range(12000))

_spells_big = [R.randint(1, 10 ** 5) for _ in range(6000)]
_potions_big = [R.randint(1, 10 ** 5) for _ in range(6000)]

_mag_big = R.sample(range(1, 10 ** 9), 10000)
_bloom_big = [R.randint(1, 10 ** 9) for _ in range(8000)]

_PEAK_CHECKER = '''
def check(args, got, expected):
    nums = args[0]
    if not isinstance(got, int) or isinstance(got, bool) or not (0 <= got < len(nums)):
        return False
    left_ok = got == 0 or nums[got] > nums[got - 1]
    right_ok = got == len(nums) - 1 or nums[got] > nums[got + 1]
    return left_ok and right_ok
'''

PROBLEMS = [
# ---------------------------------------------------------------- 367
dict(
    id="valid-perfect-square",
    title="Valid Perfect Square",
    difficulty="Easy",
    pattern="Binary Search on Answer",
    leetcode=LC.format("valid-perfect-square"),
    entry="isPerfectSquare",
    description=r"""
Given a positive integer `num`, return `True` if it is a **perfect square** — that is, if some whole number
multiplied by itself gives exactly `num` — and `False` otherwise. Do not use a built-in square-root function or
the `** 0.5` operator.

**Constraints**

- `1 <= num <= 2^31 - 1` (a few tests here are much larger to defeat floating-point shortcuts)

**Example 1:** `num = 16` → `True` (4 × 4).

**Example 2:** `num = 14` → `False`.
""",
    starter='''class Solution:
    def isPerfectSquare(self, num: int) -> bool:
        pass
''',
    solution='''class Solution:
    def isPerfectSquare(self, num):
        lo, hi = 1, num
        while lo <= hi:
            mid = (lo + hi) // 2
            sq = mid * mid
            if sq == num:
                return True
            if sq < num:
                lo = mid + 1
            else:
                hi = mid - 1
        return False
''',
    tests=[
        [16], [14], [1], [2], [3], [4], [9], [808201], [2147483647], [2147395600],
        [(10 ** 15 + 7) ** 2], [(10 ** 15 + 7) ** 2 - 1], [(10 ** 15 + 7) ** 2 + 1], [(2 ** 53 + 1) ** 2], [(2 ** 60 + 3) ** 2],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def isPerfectSquare(self, num):
        lo, hi = 1, num // 2                # bug: num = 1 has an empty search range
        while lo <= hi:
            mid = (lo + hi) // 2
            if mid * mid == num: return True
            if mid * mid < num: lo = mid + 1
            else: hi = mid - 1
        return False
''',
        '''class Solution:
    def isPerfectSquare(self, num):
        r = int(num ** 0.5)                 # float rounding breaks for very large numbers
        return r * r == num
''',
        '''class Solution:
    def isPerfectSquare(self, num):
        lo, hi = 1, num
        while lo < hi:                      # bug: never tests the final candidate
            mid = (lo + hi) // 2
            if mid * mid == num: return True
            if mid * mid < num: lo = mid + 1
            else: hi = mid - 1
        return False
''',
    ],
    guide=dict(
        prereqs="Lesson *Binary search done right* (template A: closed interval, exact match).",
        intuition="""
The squares `1, 4, 9, 16, …` grow as the base grows, so "is `k × k` smaller than, equal to, or bigger than
`num`?" tells you whether the base you want is above or below `k`. That is binary search on the numbers
`1 … num`, with `k × k` playing the role of the sorted array's value.
""",
        hints=[
            "If k*k is too small, can any number below k work?",
            "Binary-search k in [1, num], comparing k*k with num.",
            "Closed interval, lo <= hi; return True on equality, otherwise move lo or hi past mid; return False when the range is empty.",
        ],
        brute_force="Try `k = 1, 2, 3, …` until `k × k >= num`: **O(√num)** — fine for 2³¹ (46 341 steps), about 10¹⁵ steps for the largest test.",
        approach="""
**Dry run** `num = 16`: (1,16) mid 8 → 64 too big → hi 7; (1,7) mid 4 → 16 = num → `True`.

`num = 14`: (1,14) mid 7 → 49 → hi 6; mid 3 → 9 → lo 4; (4,6) mid 5 → 25 → hi 4; (4,4) mid 4 → 16 → hi 3; empty → `False`.
""",
        complexity="Time **O(log num)**, space **O(1)**.",
        pitfalls="""
- `num = 1`: starting `hi` at `num // 2` skips it.
- Floating-point square roots lose precision above about 2⁵³.
- In fixed-width languages `mid * mid` can overflow; Python integers do not.
""",
        follow_up="*Sqrt(x)* returns the rounded-down root instead of a yes/no. Newton's method also works: `r = (r + num // r) // 2`.",
    ),
),
# ---------------------------------------------------------------- 162
dict(
    id="find-peak-element",
    title="Find Peak Element",
    difficulty="Medium",
    pattern="Binary Search",
    leetcode=LC.format("find-peak-element"),
    entry="findPeakElement",
    checker=_PEAK_CHECKER,
    description=r"""
A **peak** is an element strictly greater than both of its neighbours. Positions outside the list count as
minus infinity, so the first or last element can be a peak too.

Given `nums`, in which neighbouring values are never equal, return the **index of any peak**. If there are
several, any one of them is accepted. Your algorithm should run in **O(log n)**.

**Constraints**

- `1 <= len(nums) <= 1000` (1.2·10^4 in the tests here)
- `nums[i] != nums[i + 1]` for every valid `i`

**Example 1:** `nums = [1,2,3,1]` → `2`.

**Example 2:** `nums = [1,2,1,3,5,6,4]` → `1` or `5` (both are peaks).
""",
    starter='''class Solution:
    def findPeakElement(self, nums: List[int]) -> int:
        pass
''',
    solution='''class Solution:
    def findPeakElement(self, nums):
        lo, hi = 0, len(nums) - 1
        while lo < hi:
            mid = (lo + hi) // 2
            if nums[mid] < nums[mid + 1]:
                lo = mid + 1          # going uphill: a peak lies to the right
            else:
                hi = mid              # going downhill: mid itself or something to the left
        return lo
''',
    tests=[
        [[1, 2, 3, 1]],
        [[1, 2, 1, 3, 5, 6, 4]],
        [[1]],
        [[1, 2]],
        [[2, 1]],
        [[1, 2, 3, 4, 5]],
        [[5, 4, 3, 2, 1]],
        [[1, 3, 2, 4, 1]],
        [[-5, -3, -4]],
        [[3, 1, 2]],
        [_peak_big],
        [_peak_inc],
        [_peak_inc[::-1]],
    ],
    wrong_solutions=[
        '''class Solution:
    def findPeakElement(self, nums):
        return len(nums) // 2
''',
        '''class Solution:
    def findPeakElement(self, nums):
        lo, hi = 0, len(nums) - 1
        while lo < hi:
            mid = (lo + hi) // 2
            if nums[mid] < nums[mid + 1]:
                hi = mid                  # bug: walks downhill instead of uphill
            else:
                lo = mid + 1
        return lo
''',
        '''class Solution:
    def findPeakElement(self, nums):
        for i in range(1, len(nums) - 1):  # bug: the two ends are never considered
            if nums[i - 1] < nums[i] > nums[i + 1]:
                return i
        return 0
''',
    ],
    guide=dict(
        prereqs="Lesson *Binary search done right* (first-True template). The list is **not** sorted — read the intuition carefully.",
        intuition="""
Stand at `mid` and look one step to the right. If the ground rises (`nums[mid] < nums[mid+1]`), keep walking
uphill to the right: the values cannot rise forever, because past the end the height is minus infinity — so a
peak must exist on the right. If the ground falls, the same argument says a peak exists at `mid` or to its left.
Either way, half of the list can be thrown away, even though the list is unsorted.
""",
        hints=[
            "You don't need the highest peak — any peak. Compare nums[mid] with nums[mid + 1].",
            "If the slope goes up to the right, a peak is guaranteed on the right side. Why?",
            "lo < hi loop: uphill → lo = mid + 1, downhill → hi = mid. Return lo.",
        ],
        brute_force="Scan for the first index whose right neighbour is smaller (or the last index): **O(n)**. Correct, but not logarithmic.",
        approach="""
**Invariant:** the range `[lo, hi]` always contains a peak.

**Dry run** `[1,2,1,3,5,6,4]`: (0,6) mid 3: 3 < 5 uphill → lo 4; (4,6) mid 5: 6 > 4 downhill → hi 5;
(4,5) mid 4: 5 < 6 uphill → lo 5. Return **5**.
""",
        complexity="Time **O(log n)**, space **O(1)**.",
        pitfalls="""
- `mid + 1` is always a valid index because `mid < hi` while `lo < hi`.
- Moving toward the *lower* neighbour loses the guarantee.
- The ends can be peaks; a single element is a peak.
""",
        follow_up="*Peak Index in a Mountain Array* (852) is the special case with exactly one peak. *Find a Peak Element II* (1901) does it on a grid.",
    ),
),
# ---------------------------------------------------------------- 540
dict(
    id="single-element-in-a-sorted-array",
    title="Single Element in a Sorted Array",
    difficulty="Medium",
    pattern="Binary Search",
    leetcode=LC.format("single-element-in-a-sorted-array"),
    entry="singleNonDuplicate",
    description=r"""
In the sorted list `nums` every value appears **exactly twice**, except for one value that appears **once**.
Return that single value in **O(log n)** time and O(1) extra space.

**Constraints**

- `1 <= len(nums) <= 10^5` (the length is always odd)

**Example 1:** `nums = [1,1,2,3,3,4,4,8,8]` → `2`.

**Example 2:** `nums = [3,3,7,7,10,11,11]` → `10`.
""",
    starter='''class Solution:
    def singleNonDuplicate(self, nums: List[int]) -> int:
        pass
''',
    solution='''class Solution:
    def singleNonDuplicate(self, nums):
        lo, hi = 0, len(nums) - 1
        while lo < hi:
            mid = (lo + hi) // 2
            if mid % 2 == 1:
                mid -= 1                  # make mid the first index of a would-be pair
            if nums[mid] == nums[mid + 1]:
                lo = mid + 2              # pairs are intact up to here: single is to the right
            else:
                hi = mid                  # the pattern is already broken: single is at mid or left
        return nums[lo]
''',
    tests=[
        [[1, 1, 2, 3, 3, 4, 4, 8, 8]],
        [[3, 3, 7, 7, 10, 11, 11]],
        [[1]],
        [[1, 2, 2]],
        [[1, 1, 2]],
        [[1, 1, 2, 2, 3]],
        [[0, 1, 1, 2, 2]],
        [[1, 1, 2, 2, 3, 4, 4]],
        [[-3, -3, -1, 0, 0]],
        [[5, 5, 6, 6, 7, 8, 8, 9, 9]],
        [_single_big],
        [_single_first],
        [_single_last],
    ],
    wrong_solutions=[
        '''class Solution:
    def singleNonDuplicate(self, nums):
        lo, hi = 0, len(nums) - 1
        while lo < hi:
            mid = (lo + hi) // 2          # bug: mid may be odd, so the pair test is meaningless
            if nums[mid] == nums[mid + 1]:
                lo = mid + 2
            else:
                hi = mid
        return nums[lo]
''',
        '''class Solution:
    def singleNonDuplicate(self, nums):
        for i in range(0, len(nums) - 1, 2):
            if nums[i] != nums[i + 1]:
                return nums[i + 1]        # bug: returns the wrong member of the broken pair
        return nums[-1]
''',
    ],
    guide=dict(
        prereqs="Lesson *Binary search done right* (first-True template with a custom predicate).",
        intuition="""
Before the single element, pairs sit at indices `(0,1), (2,3), (4,5) …` — each pair **starts at an even
index**. The single element shifts everything after it by one, so from there on pairs start at **odd** indices.

So for an even index `i`, ask: "is `nums[i] == nums[i+1]`?" Left of the single element the answer is yes; from
the single element onward it is no. That yes…yes no…no pattern is what binary search needs.
""",
        hints=[
            "Look at the index parity of the first element of each pair, before and after the single element.",
            "For even i: nums[i] == nums[i+1] means the single element is further right.",
            "Round mid down to an even index; equal pair → lo = mid + 2, otherwise hi = mid.",
        ],
        brute_force="XOR all values together, or step through pairs: **O(n)**. Both ignore the sorted order and miss the O(log n) requirement.",
        approach="""
**Dry run** `[1,1,2,3,3,4,4,8,8]`: (0,8) mid 4: `nums[4]=3`, `nums[5]=4` differ → hi 4; (0,4) mid 2: `2` vs `3`
differ → hi 2; (0,2) mid 1 → 0: `1 == 1` → lo 2. Return `nums[2] = 2`.
""",
        complexity="Time **O(log n)**, space **O(1)**.",
        pitfalls="""
- Forgetting to force `mid` even makes the comparison meaningless.
- `mid + 1 <= hi` always holds because `mid` is even, `mid < hi` and `hi` is even.
- The single element may be first or last.
""",
        follow_up="Without sorting (LeetCode 136) only the XOR trick gives O(1) space.",
    ),
),
# ---------------------------------------------------------------- 81
dict(
    id="search-in-rotated-sorted-array-ii",
    title="Search in Rotated Sorted Array II",
    difficulty="Medium",
    pattern="Binary Search",
    leetcode=LC.format("search-in-rotated-sorted-array-ii"),
    entry="search",
    description=r"""
`nums` was sorted in non-decreasing order — it **may contain repeated values** — and then rotated at an unknown
position (for example `[0,0,1,2,2,5,6]` → `[2,5,6,0,0,1,2]`). Return `True` if `target` occurs in `nums`, else
`False`. Do as few comparisons as you can.

**Constraints**

- `1 <= len(nums) <= 5000` (1.5·10^4 in the tests here)

**Example 1:** `nums = [2,5,6,0,0,1,2], target = 0` → `True`.

**Example 2:** `nums = [2,5,6,0,0,1,2], target = 3` → `False`.
""",
    starter='''class Solution:
    def search(self, nums: List[int], target: int) -> bool:
        pass
''',
    solution='''class Solution:
    def search(self, nums, target):
        lo, hi = 0, len(nums) - 1
        while lo <= hi:
            mid = (lo + hi) // 2
            if nums[mid] == target:
                return True
            if nums[lo] == nums[mid] == nums[hi]:
                lo += 1                       # cannot tell which half is sorted: shrink both ends
                hi -= 1
            elif nums[lo] <= nums[mid]:       # left half sorted
                if nums[lo] <= target < nums[mid]:
                    hi = mid - 1
                else:
                    lo = mid + 1
            else:                             # right half sorted
                if nums[mid] < target <= nums[hi]:
                    lo = mid + 1
                else:
                    hi = mid - 1
        return False
''',
    tests=[
        [[2, 5, 6, 0, 0, 1, 2], 0],
        [[2, 5, 6, 0, 0, 1, 2], 3],
        [[1], 1],
        [[1], 0],
        [[1, 0, 1, 1, 1], 0],
        [[1, 1, 1, 0, 1], 0],
        [[1, 1, 1, 1, 1], 2],
        [[3, 1], 1],
        [[1, 3, 1, 1, 1], 3],
        [[2, 2, 2, 3, 2, 2, 2], 3],
        [[4, 5, 6, 6, 7, 0, 1, 2, 4, 4], 7],
        [_rot2_big, _rot2_base[100]],
        [_rot2_big, 3001],
        [_rot2_flat, 0],
        [_rot2_flat, 2],
    ],
    wrong_solutions=[
        '''class Solution:
    def search(self, nums, target):
        lo, hi = 0, len(nums) - 1
        while lo <= hi:                        # the no-duplicates algorithm, unchanged
            mid = (lo + hi) // 2
            if nums[mid] == target: return True
            if nums[lo] <= nums[mid]:
                if nums[lo] <= target < nums[mid]: hi = mid - 1
                else: lo = mid + 1
            else:
                if nums[mid] < target <= nums[hi]: lo = mid + 1
                else: hi = mid - 1
        return False
''',
        '''class Solution:
    def search(self, nums, target):
        import bisect
        i = bisect.bisect_left(nums, target)   # ignores the rotation
        return i < len(nums) and nums[i] == target
''',
    ],
    guide=dict(
        prereqs="*Search in Rotated Sorted Array* and lesson *Rotated arrays, 2-D matrices and partitions* (§1.2 and §1.4).",
        intuition="""
The version without repeats relies on one test: "if `nums[lo] <= nums[mid]`, the left half is sorted". Repeats
break it. In `[1,0,1,1,1]` you have `nums[lo] = nums[mid] = nums[hi] = 1` and the left half `[1,0,1]` is *not*
sorted. When all three are equal there is no information about where the drop is — so discard the two end
values (they equal `nums[mid]`, which is not the target) and try again. In every other situation the usual
reasoning is valid.
""",
        hints=[
            "Run the no-duplicates algorithm on [1,0,1,1,1] with target 0. Where does it go wrong?",
            "The trouble is nums[lo] == nums[mid] == nums[hi]. What can you safely do then?",
            "In that case do lo += 1 and hi -= 1; otherwise use the usual 'one half is sorted' logic.",
        ],
        brute_force="`target in nums` — **O(n)**. Interestingly this is also the worst case of the best possible algorithm (see complexity).",
        approach="""
**Dry run** `[1,0,1,1,1]`, target 0: (0,4) mid 2: all three equal 1 → lo 1, hi 3; (1,3) mid 2: `nums[lo]=0 <= 1`
→ left half `[0,1]` sorted, `0 <= 0 < 1` → hi 1; (1,1) mid 1: found → `True`.
""",
        complexity="Average **O(log n)**; worst case **O(n)** (e.g. all values equal except one) — unavoidable, because such inputs give no hint where the odd value hides. Space O(1).",
        pitfalls="""
- Reusing the distinct-values algorithm unchanged fails on `[1,0,1,1,1]`.
- Shrink **only** when all three are equal; otherwise you lose the logarithmic behaviour.
- The function returns a boolean, not an index.
""",
        follow_up="*Find Minimum in Rotated Sorted Array II* (154) needs the same `hi -= 1` idea.",
    ),
),
# ---------------------------------------------------------------- 852
dict(
    id="peak-index-in-a-mountain-array",
    title="Peak Index in a Mountain Array",
    difficulty="Medium",
    pattern="Binary Search",
    leetcode=LC.format("peak-index-in-a-mountain-array"),
    entry="peakIndexInMountainArray",
    description=r"""
A *mountain array* strictly increases up to one highest element and then strictly decreases; the highest
element is neither the first nor the last. Given such a list `arr`, return the **index of the highest
element** in O(log n) time.

**Constraints**

- `3 <= len(arr) <= 10^5`
- `arr` is guaranteed to be a mountain array

**Example 1:** `arr = [0,1,0]` → `1`.

**Example 2:** `arr = [0,10,5,2]` → `1`.

**Example 3:** `arr = [3,4,5,1]` → `2`.
""",
    starter='''class Solution:
    def peakIndexInMountainArray(self, arr: List[int]) -> int:
        pass
''',
    solution='''class Solution:
    def peakIndexInMountainArray(self, arr):
        lo, hi = 0, len(arr) - 1
        while lo < hi:
            mid = (lo + hi) // 2
            if arr[mid] < arr[mid + 1]:
                lo = mid + 1
            else:
                hi = mid
        return lo
''',
    tests=[
        [[0, 1, 0]],
        [[0, 10, 5, 2]],
        [[3, 4, 5, 1]],
        [[0, 2, 1, 0]],
        [[1, 2, 3, 4, 5, 3]],
        [[1, 9, 8, 7, 6, 5]],
        [[24, 69, 100, 99, 79, 78, 67, 36, 26, 19]],
        [[3, 5, 3, 2, 0]],
        [[-10, -5, -7]],
        [[1, 2, 3, 2, 1]],
        [_mountain_big],
        [_mountain_left],
        [_mountain_left[::-1]],
    ],
    wrong_solutions=[
        '''class Solution:
    def peakIndexInMountainArray(self, arr):
        return max(arr)                    # returns the value, not the index
''',
        '''class Solution:
    def peakIndexInMountainArray(self, arr):
        lo, hi = 0, len(arr) - 1
        while lo < hi:
            mid = (lo + hi) // 2
            if arr[mid] < arr[mid + 1]:
                lo = mid + 1
            else:
                hi = mid - 1               # bug: may step past the peak
        return lo
''',
    ],
    guide=dict(
        prereqs="First-True template (lesson *Binary search done right*); *Find Peak Element*.",
        intuition="""
Ask each index "is the next value smaller than you?" (`arr[i] > arr[i+1]`). On the way up the answer is no; from
the top onward it is yes. The top is the **first yes** — a boundary search.
""",
        hints=[
            "Compare arr[mid] with arr[mid + 1]: are you on the rising or the falling side?",
            "Rising → the peak is to the right of mid. Falling → the peak is mid or to its left.",
            "lo < hi; rising: lo = mid + 1; falling: hi = mid. Return lo.",
        ],
        brute_force="`arr.index(max(arr))` or a scan for the first drop: **O(n)**.",
        approach="""
**Dry run** `[0,2,1,0]`: (0,3) mid 1: 2 > 1 falling → hi 1; (0,1) mid 0: 0 < 2 rising → lo 1. Return **1**.
""",
        complexity="Time **O(log n)**, space **O(1)**.",
        pitfalls="""
- `hi = mid - 1` can discard the peak itself.
- Return the index, not the value.
""",
        follow_up="*Find in Mountain Array* (1095, Hard): find the peak, then binary-search each side (one ascending, one descending).",
    ),
),
# ---------------------------------------------------------------- 658
dict(
    id="find-k-closest-elements",
    title="Find K Closest Elements",
    difficulty="Medium",
    pattern="Binary Search",
    leetcode=LC.format("find-k-closest-elements"),
    entry="findClosestElements",
    description=r"""
Given a **sorted** list `arr` and integers `k` and `x`, return the `k` values of `arr` that are closest to `x`,
in ascending order.

Value `a` is closer than value `b` when `|a - x| < |b - x|`; on a tie the **smaller value** counts as closer.

**Constraints**

- `1 <= k <= len(arr) <= 10^4` (1.2·10^4 in the tests here)
- `-10^4 <= arr[i], x <= 10^4`

**Example 1:** `arr = [1,2,3,4,5], k = 4, x = 3` → `[1,2,3,4]`.

**Example 2:** `arr = [1,1,2,3,4,5], k = 4, x = -1` → `[1,1,2,3]`.
""",
    starter='''class Solution:
    def findClosestElements(self, arr: List[int], k: int, x: int) -> List[int]:
        pass
''',
    solution='''class Solution:
    def findClosestElements(self, arr, k, x):
        lo, hi = 0, len(arr) - k          # possible start positions of the answer window
        while lo < hi:
            mid = (lo + hi) // 2
            if x - arr[mid] > arr[mid + k] - x:
                lo = mid + 1              # arr[mid + k] is strictly closer than arr[mid]: shift right
            else:
                hi = mid
        return arr[lo:lo + k]
''',
    tests=[
        [[1, 2, 3, 4, 5], 4, 3],
        [[1, 1, 2, 3, 4, 5], 4, -1],
        [[1], 1, 7],
        [[1, 3], 1, 2],
        [[1, 2, 3, 4, 5], 4, 10],
        [[1, 2, 3, 4, 5], 5, 3],
        [[0, 0, 1, 2, 3, 3, 4, 7, 7, 8], 3, 5],
        [[1, 1, 1, 10, 10, 10], 1, 9],
        [[1, 5, 10], 1, 4],
        [[2, 4, 6, 8], 2, 5],
        [[-5, -3, 0, 2, 9], 3, -4],
        [_kc_big, 4000, 123],
        [_kc_big, 1, -10000],
        [_kc_big, 11999, 10000],
    ],
    wrong_solutions=[
        '''class Solution:
    def findClosestElements(self, arr, k, x):
        lo, hi = 0, len(arr) - k
        while lo < hi:
            mid = (lo + hi) // 2
            if x - arr[mid] >= arr[mid + k] - x:    # bug: ties should keep the smaller value
                lo = mid + 1
            else:
                hi = mid
        return arr[lo:lo + k]
''',
        '''class Solution:
    def findClosestElements(self, arr, k, x):
        import bisect
        i = bisect.bisect_left(arr, x)              # just takes k values starting at x's position
        i = min(i, len(arr) - k)
        return arr[i:i + k]
''',
    ],
    guide=dict(
        prereqs="First-True template; thinking of the answer as a *window position* (lessons 1 and 6).",
        intuition="""
The answer is always `k` **neighbouring** values of the sorted list — a window `arr[s : s+k]`. So the real
question is "where does the window start?", and `s` ranges over `0 … n−k`.

Compare the value just left inside a candidate window, `arr[mid]`, with the value just outside on the right,
`arr[mid + k]`. Only one of them can be in the answer. If the right one is strictly closer to `x`, the window
must move right (`s > mid`). Otherwise the window starts at `mid` or further left. That is a boundary search.
""",
        hints=[
            "The k closest values form a contiguous block in the sorted list. Binary-search its start.",
            "For a start s, compare arr[s] with arr[s + k]: which one deserves to be in the block?",
            "if x − arr[mid] > arr[mid + k] − x: lo = mid + 1 else hi = mid. Return arr[lo:lo+k].",
        ],
        brute_force="Sort all values by `(|a − x|, a)`, take the first `k`, sort them again: **O(n log n)**. A two-pointer shrink from both ends is O(n − k).",
        approach="""
**Dry run** `[1,2,3,4,5]`, `k = 4`, `x = 3`: starts range over (0,1). mid 0: `x − arr[0] = 2`, `arr[4] − x = 2`;
2 > 2 is false → hi 0. Window starts at 0 → `[1,2,3,4]` (the tie between 1 and 5 keeps the smaller value).

Note the comparison deliberately avoids `abs()`: when `x` lies outside `[arr[mid], arr[mid+k]]` the signed
differences still point the right way.
""",
        complexity="Time **O(log(n − k) + k)** — the `+ k` is for copying the answer. Space O(1) besides the output.",
        pitfalls="""
- Ties must prefer the smaller value: use `>` (strict) when deciding to move right.
- `hi` starts at `n − k`, not `n − 1`, so `mid + k` is always a valid index.
- Using `abs()` on both sides breaks when duplicates make both distances equal on the same side of `x`.
""",
        follow_up="*K Closest Points to Origin* (973) has no sorted order to exploit — it needs a heap or quickselect.",
    ),
),
# ---------------------------------------------------------------- 2300
dict(
    id="successful-pairs-of-spells-and-potions",
    title="Successful Pairs of Spells and Potions",
    difficulty="Medium",
    pattern="Binary Search",
    leetcode=LC.format("successful-pairs-of-spells-and-potions"),
    entry="successfulPairs",
    description=r"""
You have two lists of positive integers: `spells` (strengths of spells) and `potions` (strengths of potions).
A spell and a potion form a **successful pair** when the product of their strengths is at least `success`.

Return a list with one number per spell, in the given order: how many potions pair successfully with that
spell.

**Constraints**

- `1 <= len(spells), len(potions) <= 10^5` (6000 each in the tests here)
- `1 <= spells[i], potions[i] <= 10^5`, `1 <= success <= 10^10`

**Example 1:** `spells = [5,1,3], potions = [1,2,3,4,5], success = 7` → `[4,0,3]`.

**Example 2:** `spells = [3,1,2], potions = [8,5,8], success = 16` → `[2,0,2]`.
""",
    starter='''class Solution:
    def successfulPairs(self, spells: List[int], potions: List[int], success: int) -> List[int]:
        pass
''',
    solution='''import bisect

class Solution:
    def successfulPairs(self, spells, potions, success):
        potions = sorted(potions)
        n = len(potions)
        out = []
        for s in spells:
            need = (success + s - 1) // s            # smallest potion strength that works (ceiling)
            out.append(n - bisect.bisect_left(potions, need))
        return out
''',
    tests=[
        [[5, 1, 3], [1, 2, 3, 4, 5], 7],
        [[3, 1, 2], [8, 5, 8], 16],
        [[1], [1], 1],
        [[1], [1], 2],
        [[3], [1, 2, 3, 4, 5], 7],
        [[2, 2], [5, 5, 5], 10],
        [[100000], [100000], 10 ** 10],
        [[100000], [99999], 10 ** 10],
        [[4, 7, 1], [9, 3, 3, 12, 1], 12],
        [[1, 2, 3, 4, 5, 6, 7], [1, 2, 3, 4, 5, 6, 7], 25],
        [_spells_big, _potions_big, 10 ** 9],
        [_spells_big, _potions_big, 1],
        [_spells_big, _potions_big, 10 ** 10],
    ],
    wrong_solutions=[
        '''import bisect
class Solution:
    def successfulPairs(self, spells, potions, success):
        potions = sorted(potions)
        n = len(potions)
        return [n - bisect.bisect_left(potions, success // s) for s in spells]   # floor instead of ceiling
''',
        '''import bisect
class Solution:
    def successfulPairs(self, spells, potions, success):
        n = len(potions)                                                          # bug: potions not sorted
        return [n - bisect.bisect_left(potions, (success + s - 1) // s) for s in spells]
''',
        '''import bisect
class Solution:
    def successfulPairs(self, spells, potions, success):
        potions = sorted(potions)
        n = len(potions)
        return [n - bisect.bisect_right(potions, (success + s - 1) // s) for s in spells]  # excludes exact matches
''',
    ],
    guide=dict(
        prereqs="`lower_bound` / `bisect_left` and ceiling division (lessons 6 and 7).",
        intuition="""
For one spell of strength `s`, a potion `p` works when `s × p >= success`, i.e. when `p >= success / s`. Since
`p` is a whole number, that means `p >= ceil(success / s)`. If the potions are **sorted**, all the potions that
work sit together at the right end, and the first one is found with a lower-bound search. The count is
"everything from that position to the end".
""",
        hints=[
            "Fix a spell. Which potions succeed? Those at or above some threshold.",
            "Sort the potions once; for each spell binary-search the first potion >= ceil(success / spell).",
            "count = len(potions) − bisect_left(potions, (success + s − 1) // s).",
        ],
        brute_force="Check all pairs: **O(n·m)** — 3.6·10⁷ multiplications for the big tests, 10¹⁰ at LeetCode's limits.",
        approach="""
**Dry run** spells `[5,1,3]`, potions `[1,2,3,4,5]`, success 7:

| spell | need = ceil(7 / s) | first index with potion ≥ need | count |
|---|---|---|---|
| 5 | 2 | 1 | 5 − 1 = 4 |
| 1 | 7 | 5 | 0 |
| 3 | 3 | 2 | 3 |
""",
        complexity="Time **O((n + m) log m)** — sort the `m` potions, then one binary search per spell. Space O(m).",
        pitfalls="""
- Floor division (`success // s`) accepts potions that are slightly too weak when the division is not exact.
- Avoid float division: `10^10 / s` can round badly; `(success + s − 1) // s` is exact.
- Sort a copy — the answer order follows `spells`, which must stay unsorted.
""",
        follow_up="Sorting both lists allows a two-pointer sweep; the binary search version is easier to get right.",
    ),
),
# ---------------------------------------------------------------- 1552
dict(
    id="magnetic-force-between-two-balls",
    title="Magnetic Force Between Two Balls",
    difficulty="Medium",
    pattern="Binary Search on Answer",
    leetcode=LC.format("magnetic-force-between-two-balls"),
    entry="maxDistance",
    description=r"""
There are baskets at the distinct coordinates listed in `position`, and you must place `m` balls into `m`
different baskets. The *force* between two balls is the distance between their baskets. Place the balls so that
the **smallest** force between any two balls is as **large** as possible, and return that value.

**Constraints**

- `2 <= len(position) <= 10^5` (10^4 in the tests here)
- `1 <= position[i] <= 10^9`, all distinct
- `2 <= m <= len(position)`

**Example 1:** `position = [1,2,3,4,7], m = 3` → `3` (baskets 1, 4 and 7).

**Example 2:** `position = [5,4,3,2,1,1000000000], m = 2` → `999999999`.
""",
    starter='''class Solution:
    def maxDistance(self, position: List[int], m: int) -> int:
        pass
''',
    solution='''class Solution:
    def maxDistance(self, position, m):
        pos = sorted(position)

        def can(gap):
            placed, last = 1, pos[0]
            for p in pos:
                if p - last >= gap:
                    placed += 1
                    if placed == m:
                        return True
                    last = p
            return placed >= m

        lo, hi = 1, (pos[-1] - pos[0]) // (m - 1)
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if can(mid):
                lo = mid
            else:
                hi = mid - 1
        return lo
''',
    tests=[
        [[1, 2, 3, 4, 7], 3],
        [[5, 4, 3, 2, 1, 1000000000], 2],
        [[1, 2], 2],
        [[1, 100], 2],
        [[1, 2, 3, 4, 5], 5],
        [[10, 1, 5], 2],
        [[10, 1, 5], 3],
        [[79, 74, 57, 22], 4],
        [[1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 4],
        [[4, 8, 15, 16, 23, 42], 3],
        [_mag_big, 2],
        [_mag_big, 137],
        [_mag_big, 10000],
    ],
    wrong_solutions=[
        '''class Solution:
    def maxDistance(self, position, m):
        pos = position                              # bug: not sorted
        def can(gap):
            placed, last = 1, pos[0]
            for p in pos:
                if p - last >= gap:
                    placed += 1; last = p
            return placed >= m
        lo, hi = 1, max(pos) - min(pos)
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if can(mid): lo = mid
            else: hi = mid - 1
        return lo
''',
        '''class Solution:
    def maxDistance(self, position, m):
        pos = sorted(position)
        return (pos[-1] - pos[0]) // (m - 1)        # the ideal even spacing is only an upper bound
''',
    ],
    guide=dict(
        prereqs="Lesson *Binary search on the answer* (§6, maximise → last True, upper midpoint).",
        intuition="""
Guess a gap `d` and ask: "can I place all `m` balls so that every two neighbours are at least `d` apart?"
Checking a guess is easy with a **greedy** walk over the sorted baskets: put a ball in the first basket, then in
every basket that is at least `d` beyond the last ball. If that places `m` balls, `d` is achievable.

A smaller gap is never harder, so the answers read `yes yes … yes no no …`. We want the **last yes**.
""",
        hints=[
            "Maximise the minimum → binary search on the answer.",
            "Write can(d): greedily place balls left to right at least d apart; count them.",
            "Search d in [1, span // (m − 1)] with the upper midpoint: can(mid) → lo = mid, else hi = mid − 1.",
        ],
        brute_force="Try every `d` from 1 upward until placement fails: up to 10⁹ candidates × O(n). Choosing baskets by brute force is exponential.",
        approach="""
**Dry run** sorted `[1,2,3,4,7]`, `m = 3`, range [1, 3]:

| lo | hi | mid | greedy placement | can? |
|---|---|---|---|---|
| 1 | 3 | 2 | 1, 3, 7 | yes → lo = 2 |
| 2 | 3 | 3 | 1, 4, 7 | yes → lo = 3 |

Answer **3**.

Why is greedy right for the check? Placing each ball as far **left** as allowed leaves the most room for the
remaining balls.
""",
        complexity="Time **O(n log n + n log(span))**, space O(n) for the sorted copy.",
        pitfalls="""
- Sort first.
- `lo = mid` requires the **upper** midpoint, or the loop never ends.
- `span // (m − 1)` is only an upper bound on the answer, not the answer.
""",
        follow_up="Same shape: *Aggressive Cows* (classic), *Maximum Tastiness of Candy Basket* (2517).",
    ),
),
# ---------------------------------------------------------------- 1482
dict(
    id="minimum-number-of-days-to-make-m-bouquets",
    title="Minimum Number of Days to Make m Bouquets",
    difficulty="Medium",
    pattern="Binary Search on Answer",
    leetcode=LC.format("minimum-number-of-days-to-make-m-bouquets"),
    entry="minDays",
    description=r"""
A garden has a row of flowers; flower `i` opens on day `bloomDay[i]` and stays open afterwards. You want to make
`m` bouquets, and each bouquet needs `k` open flowers that stand **next to each other** in the row. A flower can
be used in only one bouquet.

Return the earliest day on which `m` bouquets can be made, or `-1` if it is never possible.

**Constraints**

- `1 <= len(bloomDay) <= 10^5` (8000 in the tests here)
- `1 <= bloomDay[i] <= 10^9`, `1 <= m <= 10^6`, `1 <= k <= len(bloomDay)`

**Example 1:** `bloomDay = [1,10,3,10,2], m = 3, k = 1` → `3`.

**Example 2:** `bloomDay = [1,10,3,10,2], m = 3, k = 2` → `-1` (6 flowers would be needed).

**Example 3:** `bloomDay = [7,7,7,7,12,7,7], m = 2, k = 3` → `12`.
""",
    starter='''class Solution:
    def minDays(self, bloomDay: List[int], m: int, k: int) -> int:
        pass
''',
    solution='''class Solution:
    def minDays(self, bloomDay, m, k):
        if m * k > len(bloomDay):
            return -1

        def bouquets(day):
            made = run = 0
            for b in bloomDay:
                if b <= day:
                    run += 1
                    if run == k:
                        made += 1
                        run = 0
                else:
                    run = 0
            return made

        lo, hi = min(bloomDay), max(bloomDay)
        while lo < hi:
            mid = (lo + hi) // 2
            if bouquets(mid) >= m:
                hi = mid
            else:
                lo = mid + 1
        return lo
''',
    tests=[
        [[1, 10, 3, 10, 2], 3, 1],
        [[1, 10, 3, 10, 2], 3, 2],
        [[7, 7, 7, 7, 12, 7, 7], 2, 3],
        [[5], 1, 1],
        [[5], 2, 1],
        [[1000000000, 1000000000], 1, 1],
        [[1, 10, 2, 9, 3, 8, 4, 7, 5, 6], 4, 2],
        [[1, 2, 3, 4, 5, 6], 2, 3],
        [[6, 5, 4, 3, 2, 1], 3, 2],
        [[1, 1, 1, 9, 1, 1], 2, 2],
        [_bloom_big, 50, 40],
        [_bloom_big, 8000, 1],
        [_bloom_big, 1, 8000],
        [_bloom_big, 300, 27],
    ],
    wrong_solutions=[
        '''class Solution:
    def minDays(self, bloomDay, m, k):
        if m * k > len(bloomDay):
            return -1
        lo, hi = min(bloomDay), max(bloomDay)
        while lo < hi:
            mid = (lo + hi) // 2
            if sum(b <= mid for b in bloomDay) // k >= m:   # bug: ignores adjacency
                hi = mid
            else:
                lo = mid + 1
        return lo
''',
        '''class Solution:
    def minDays(self, bloomDay, m, k):
        def bouquets(day):
            made = run = 0
            for b in bloomDay:
                if b <= day:
                    run += 1
                    if run == k:
                        made += 1; run = 0
                else:
                    run = 0
            return made
        lo, hi = min(bloomDay), max(bloomDay)             # bug: no impossibility check
        while lo < hi:
            mid = (lo + hi) // 2
            if bouquets(mid) >= m: hi = mid
            else: lo = mid + 1
        return lo
''',
        '''class Solution:
    def minDays(self, bloomDay, m, k):
        if m * k > len(bloomDay):
            return -1
        def bouquets(day):
            made = run = 0
            for b in bloomDay:
                if b <= day:
                    run += 1
                else:
                    made += run // k; run = 0
            return made                                    # bug: the final run is never counted
        lo, hi = min(bloomDay), max(bloomDay)
        while lo < hi:
            mid = (lo + hi) // 2
            if bouquets(mid) >= m: hi = mid
            else: lo = mid + 1
        return lo
''',
    ],
    guide=dict(
        prereqs="Lesson *Binary search on the answer*; *Koko Eating Bananas*.",
        intuition="""
Pick a day `d` and ask "are `m` bouquets possible by day `d`?" To check, walk the row counting **runs** of
flowers that are already open (`bloomDay[i] <= d`); every time a run reaches `k`, that is one bouquet and the
run counter restarts. Waiting longer only opens more flowers, so once the answer is yes it stays yes — search
for the **first yes** between the earliest and latest bloom day.
""",
        hints=[
            "If you can make the bouquets on day d, can you on day d + 1?",
            "Check a day by counting groups of k adjacent open flowers in one pass.",
            "Return −1 if m·k > n. Otherwise binary-search the day in [min(bloomDay), max(bloomDay)] for the first feasible one.",
        ],
        brute_force="Test every distinct bloom day in increasing order: up to n days × O(n) per check = **O(n²)** (6·10⁷ for n = 8000).",
        approach="""
**Dry run** `[7,7,7,7,12,7,7]`, `m = 2`, `k = 3`, range [7, 12]:

| lo | hi | mid | open flowers (x = open) | bouquets | |
|---|---|---|---|---|---|
| 7 | 12 | 9 | x x x x _ x x | 1 | lo = 10 |
| 10 | 12 | 11 | x x x x _ x x | 1 | lo = 12 |

`lo == hi == 12` → on day 12 all seven are open → 2 bouquets. Answer **12**.
""",
        complexity="Time **O(n log(max day))**, space **O(1)**.",
        pitfalls="""
- Adjacency matters: counting open flowers and dividing by `k` is wrong.
- Reset the run after completing a bouquet (a flower is used once).
- Handle the impossible case `m × k > n` up front; otherwise the search returns `max(bloomDay)` wrongly.
""",
        follow_up="The same check-then-search structure solves *Capacity To Ship Packages*, *Split Array Largest Sum* and *Minimum Time to Complete Trips* (2187).",
    ),
),
]
