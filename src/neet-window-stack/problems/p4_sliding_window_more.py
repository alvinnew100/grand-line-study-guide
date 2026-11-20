import random

R = random.Random(77001)
LC = "https://leetcode.com/problems/{}/"

_avg_big = [R.randint(-10000, 10000) for _ in range(20000)]
_bits_big = [1 if R.random() < 0.7 else 0 for _ in range(40000)]
_bits_big2 = [1 if R.random() < 0.97 else 0 for _ in range(40000)]
_thr_big = [R.randint(1, 10000) for _ in range(20000)]
_ops_big = [R.randint(1, 10000) for _ in range(15000)]
_freq_big = [R.randint(1, 100000) for _ in range(15000)]
_kd_big = [R.randint(1, 40) for _ in range(20000)]

PROBLEMS = [
# ---------------------------------------------------------------- 643
dict(
    id="maximum-average-subarray-i",
    title="Maximum Average Subarray I",
    difficulty="Easy",
    pattern="Sliding Window",
    leetcode=LC.format("maximum-average-subarray-i"),
    entry="findMaxAverage",
    compare="float",
    description=r"""
Given a list of integers `nums` and a window length `k`, look at every run of exactly `k` neighbouring values.
Return the largest **average** (mean) among those runs, as a float.

**Constraints**

- `1 <= k <= len(nums) <= 10^5`
- `-10^4 <= nums[i] <= 10^4`

**Example 1:** `nums = [1,12,-5,-6,50,3], k = 4` → `12.75` (the run `[12,-5,-6,50]` sums to 51).

**Example 2:** `nums = [5], k = 1` → `5.0`.
""",
    starter='''class Solution:
    def findMaxAverage(self, nums: List[int], k: int) -> float:
        pass
''',
    solution='''class Solution:
    def findMaxAverage(self, nums, k):
        window = sum(nums[:k])
        best = window
        for i in range(k, len(nums)):
            window += nums[i] - nums[i - k]
            if window > best:
                best = window
        return best / k
''',
    tests=[
        [[1, 12, -5, -6, 50, 3], 4],
        [[5], 1],
        [[-1], 1],
        [[-3, -2, -5], 2],
        [[0, 4, 0, 3, 2], 1],
        [[1, 2, 3, 4], 4],
        [[7, 7, 7, 7], 2],
        [[4, 2, 1, 3, 3], 2],
        [[-10000, 10000, -10000, 10000], 3],
        [[8, 1, 1, 1, 9], 5],
        [_avg_big, 5000],
        [_avg_big, 1],
        [[-1] * 20000, 777],
    ],
    wrong_solutions=[
        '''class Solution:
    def findMaxAverage(self, nums, k):
        best = 0                               # bug: fails when every window is negative
        window = 0
        for i, x in enumerate(nums):
            window += x
            if i >= k:
                window -= nums[i - k]
            if i >= k - 1:
                best = max(best, window)
        return best / k
''',
        '''class Solution:
    def findMaxAverage(self, nums, k):
        window = sum(nums[:k])
        best = window
        for i in range(k, len(nums) - 1):      # bug: skips the last window
            window += nums[i] - nums[i - k]
            best = max(best, window)
        return best / k
''',
    ],
    guide=dict(
        prereqs="Lesson *Sliding windows: fixed vs variable* (fixed-size template).",
        intuition="""
The average of a run is its sum divided by `k`, and `k` never changes — so the run with the largest **sum** also
has the largest average. Neighbouring runs share all but one value, so you get the next sum from the previous
one by adding the value that enters and subtracting the value that leaves.
""",
        hints=[
            "Maximising the average of k numbers is the same as maximising their sum.",
            "Compute the sum of the first k values once. How does the sum change when the window moves one step right?",
            "window += nums[i] - nums[i-k]; track the best sum; divide by k once at the end.",
        ],
        brute_force="Call `sum(nums[i:i+k])` for every start `i`: **O(n·k)**. With `n = 20 000` and `k = 5000` that is about 10⁸ additions.",
        approach="""
1. `window = sum(nums[:k])`, `best = window`.
2. For `i = k … n-1`: `window += nums[i] - nums[i-k]`; `best = max(best, window)`.
3. Return `best / k`.

**Dry run** `[1,12,-5,-6,50,3]`, `k = 4`: first sum 2 → slide: +50 −1 = 51 → slide: +3 −12 = 42. Best 51 → 12.75.
""",
        complexity="Time **O(n)**, space **O(1)**.",
        pitfalls="""
- Starting `best` at 0 is wrong when all sums are negative; start with the first window.
- Dividing inside the loop adds floating-point noise and work; divide once.
- Make sure the loop reaches the last index.
""",
        follow_up="*Maximum Average Subarray II* (length **at least** k) needs binary search on the answer over real numbers.",
    ),
),
# ---------------------------------------------------------------- 1004
dict(
    id="max-consecutive-ones-iii",
    title="Max Consecutive Ones III",
    difficulty="Medium",
    pattern="Sliding Window",
    leetcode=LC.format("max-consecutive-ones-iii"),
    entry="longestOnes",
    description=r"""
`nums` contains only `0`s and `1`s. You may change **at most `k`** of the zeros into ones. Return the length of
the longest run of consecutive ones you can obtain.

**Constraints**

- `1 <= len(nums) <= 10^5`
- `0 <= k <= len(nums)`

**Example 1:** `nums = [1,1,1,0,0,0,1,1,1,1,0], k = 2` → `6`.

**Example 2:** `nums = [0,0,1,1,0,0,1,1,1,0,1,1,0,0,0,1,1,1,1], k = 3` → `10`.
""",
    starter='''class Solution:
    def longestOnes(self, nums: List[int], k: int) -> int:
        pass
''',
    solution='''class Solution:
    def longestOnes(self, nums, k):
        left = zeros = best = 0
        for right, x in enumerate(nums):
            if x == 0:
                zeros += 1
            while zeros > k:
                if nums[left] == 0:
                    zeros -= 1
                left += 1
            if right - left + 1 > best:
                best = right - left + 1
        return best
''',
    tests=[
        [[1, 1, 1, 0, 0, 0, 1, 1, 1, 1, 0], 2],
        [[0, 0, 1, 1, 0, 0, 1, 1, 1, 0, 1, 1, 0, 0, 0, 1, 1, 1, 1], 3],
        [[0], 0],
        [[0], 1],
        [[1], 0],
        [[0, 0, 0], 0],
        [[1, 1, 0, 0, 1, 1, 1, 0, 1], 1],
        [[1, 0, 1, 0, 1], 5],
        [[0, 1, 1, 0], 0],
        [[1, 0, 0, 1, 0, 1, 1], 2],
        [_bits_big, 100],
        [_bits_big2, 0],
        [_bits_big2, 50],
    ],
    wrong_solutions=[
        '''class Solution:
    def longestOnes(self, nums, k):
        best = run = 0
        for x in nums:
            run = run + 1 if x else 0
            best = max(best, run)
        return min(len(nums), best + k)        # longest run plus k: ignores where the zeros are
''',
        '''class Solution:
    def longestOnes(self, nums, k):
        left = zeros = best = 0
        for right, x in enumerate(nums):
            if x == 0:
                zeros += 1
            while zeros >= k and left <= right:   # bug: allows only k-1 flips
                if nums[left] == 0:
                    zeros -= 1
                left += 1
            best = max(best, right - left + 1)
        return best
''',
    ],
    guide=dict(
        prereqs="Variable-size window, *longest valid window* template (lesson 1).",
        intuition="""
Rephrase: find the longest stretch that contains **at most `k` zeros** — those are the zeros you would flip.
Grow the stretch to the right; when it holds more than `k` zeros, move the left edge forward until it is legal again.
""",
        hints=[
            "Which zeros would you flip? Only the ones inside the final run.",
            "So the task is: longest window with at most k zeros.",
            "Count zeros in the window; while zeros > k, advance left (decrementing the count when a zero leaves).",
        ],
        brute_force="For every start, extend while counting zeros: **O(n²)** — 2.5·10⁹ steps for n = 40 000.",
        approach="""
**Dry run** `[1,1,1,0,0,0,1,1,1,1,0]`, `k = 2`: the window grows to index 4 (two zeros). At index 5 a third zero
enters → advance `left` past the first zero (index 3) to 4. The window then grows to index 10: it covers indices
4..9 = `[0,0,1,1,1,1]`, length **6**; index 10 would be a third zero again.
""",
        complexity="Time **O(n)** (each index enters and leaves once), space **O(1)**.",
        pitfalls="""
- "Longest run + k" ignores that the flipped zeros must connect the ones.
- The window is legal with **exactly** `k` zeros: shrink only when `zeros > k`.
- `k = 0` must still work (plain longest run of ones).
""",
        follow_up="*Longest Repeating Character Replacement* is the same idea with 26 letters instead of 2 symbols.",
    ),
),
# ---------------------------------------------------------------- 1493
dict(
    id="longest-subarray-of-1s-after-deleting-one-element",
    title="Longest Subarray of 1's After Deleting One Element",
    difficulty="Medium",
    pattern="Sliding Window",
    leetcode=LC.format("longest-subarray-of-1s-after-deleting-one-element"),
    entry="longestSubarray",
    description=r"""
`nums` contains only `0`s and `1`s. You **must delete exactly one element**. Afterwards, what is the longest run of
consecutive `1`s in the remaining list? Return its length (`0` if there is none).

**Constraints**

- `1 <= len(nums) <= 10^5`

**Example 1:** `nums = [1,1,0,1]` → `3` (delete the zero).

**Example 2:** `nums = [0,1,1,1,0,1,1,0,1]` → `5`.

**Example 3:** `nums = [1,1,1]` → `2` (one element has to go).
""",
    starter='''class Solution:
    def longestSubarray(self, nums: List[int]) -> int:
        pass
''',
    solution='''class Solution:
    def longestSubarray(self, nums):
        left = zeros = best = 0
        for right, x in enumerate(nums):
            if x == 0:
                zeros += 1
            while zeros > 1:
                if nums[left] == 0:
                    zeros -= 1
                left += 1
            if right - left > best:
                best = right - left          # window length minus the one deleted element
        return best
''',
    tests=[
        [[1, 1, 0, 1]],
        [[0, 1, 1, 1, 0, 1, 1, 0, 1]],
        [[1, 1, 1]],
        [[0]],
        [[1]],
        [[0, 0, 0]],
        [[1, 0, 0, 1]],
        [[0, 1, 0]],
        [[1, 1, 0, 0, 1, 1, 1, 0, 1]],
        [[1, 0, 1, 1, 0, 1, 1, 1]],
        [_bits_big],
        [_bits_big2],
        [[1] * 40000],
    ],
    wrong_solutions=[
        '''class Solution:
    def longestSubarray(self, nums):
        left = zeros = best = 0
        for right, x in enumerate(nums):
            if x == 0:
                zeros += 1
            while zeros > 1:
                if nums[left] == 0:
                    zeros -= 1
                left += 1
            best = max(best, right - left + 1 - zeros)   # bug: all-ones input keeps every element
        return best
''',
        '''class Solution:
    def longestSubarray(self, nums):
        best = run = 0
        for x in nums:
            run = run + 1 if x else 0
            best = max(best, run)
        return best                                       # never joins two runs
''',
    ],
    guide=dict(
        prereqs="*Max Consecutive Ones III* — this is the same window with `k = 1`.",
        intuition="""
Deleting one element can glue two runs of ones together if exactly one zero sits between them. So look for the
longest window with **at most one zero**; the answer is that window's length **minus one**, because one element
(the zero, or a one if there is no zero) is always removed.
""",
        hints=[
            "What does the kept run look like in the original list? Ones with at most a single zero inside.",
            "Find the longest window containing at most one zero.",
            "Answer = window length − 1 (you always delete one element), i.e. right − left.",
        ],
        brute_force="Try deleting each index and rescan for the longest run: **O(n²)**.",
        approach="""
**Dry run** `[1,1,0,1]`: the window grows over all four values (one zero), length 4 → answer 4 − 1 = **3**.
`[1,1,1]`: window length 3, no zero; one `1` still has to be deleted → **2**.
""",
        complexity="Time **O(n)**, space **O(1)**.",
        pitfalls="""
- All ones: the answer is `n − 1`, not `n`.
- Subtracting the number of zeros instead of exactly one gives the all-ones case wrong.
""",
        follow_up="Alternative without a window: keep the lengths of the previous and current run of ones and add them at each zero.",
    ),
),
# ---------------------------------------------------------------- 1343
dict(
    id="number-of-sub-arrays-of-size-k-and-average-greater-than-or-equal-to-threshold",
    title="Number of Sub-arrays of Size K and Average Greater than or Equal to Threshold",
    difficulty="Medium",
    pattern="Sliding Window",
    leetcode=LC.format("number-of-sub-arrays-of-size-k-and-average-greater-than-or-equal-to-threshold"),
    entry="numOfSubarrays",
    description=r"""
Given a list `arr`, a length `k` and a number `threshold`, count the runs of exactly `k` neighbouring values whose
average is **at least** `threshold`.

**Constraints**

- `1 <= k <= len(arr) <= 10^5`
- `1 <= arr[i] <= 10^4`, `0 <= threshold <= 10^4`

**Example 1:** `arr = [2,2,2,2,5,5,5,8], k = 3, threshold = 4` → `3`
(the runs `[2,5,5]`, `[5,5,5]`, `[5,5,8]` have averages 4, 5 and 6).

**Example 2:** `arr = [11,13,17,23,29,31,7,5,2,3], k = 3, threshold = 5` → `6`.
""",
    starter='''class Solution:
    def numOfSubarrays(self, arr: List[int], k: int, threshold: int) -> int:
        pass
''',
    solution='''class Solution:
    def numOfSubarrays(self, arr, k, threshold):
        need = k * threshold
        window = sum(arr[:k])
        count = 1 if window >= need else 0
        for i in range(k, len(arr)):
            window += arr[i] - arr[i - k]
            if window >= need:
                count += 1
        return count
''',
    tests=[
        [[2, 2, 2, 2, 5, 5, 5, 8], 3, 4],
        [[11, 13, 17, 23, 29, 31, 7, 5, 2, 3], 3, 5],
        [[1], 1, 1],
        [[1], 1, 2],
        [[5, 5, 5], 3, 5],
        [[5, 5, 4], 3, 5],
        [[1, 1, 1, 1, 1], 1, 0],
        [[7, 7, 7, 7, 7, 7, 7], 7, 7],
        [[4, 4, 4, 4], 2, 4],
        [[1, 2, 3, 4, 5, 6], 2, 3],
        [_thr_big, 4000, 5000],
        [_thr_big, 1, 5000],
        [_thr_big, 20000, 4990],
    ],
    wrong_solutions=[
        '''class Solution:
    def numOfSubarrays(self, arr, k, threshold):
        need = k * threshold
        window = sum(arr[:k])
        count = 1 if window > need else 0          # bug: strict comparison
        for i in range(k, len(arr)):
            window += arr[i] - arr[i - k]
            if window > need:
                count += 1
        return count
''',
        '''class Solution:
    def numOfSubarrays(self, arr, k, threshold):
        need = k * threshold
        window = sum(arr[:k])
        count = 0                                   # bug: the first window is never tested
        for i in range(k, len(arr)):
            window += arr[i] - arr[i - k]
            if window >= need:
                count += 1
        return count
''',
    ],
    guide=dict(
        prereqs="Fixed-size window (lesson 1); *Maximum Average Subarray I*.",
        intuition="""
"Average ≥ threshold" for `k` values is the same as "sum ≥ k × threshold". That removes division (and
floating-point worries) completely. Slide a window of size `k`, keep its sum, and count the windows that reach
the required sum.
""",
        hints=[
            "Multiply both sides of average >= threshold by k.",
            "Keep a running sum of the current k values.",
            "Don't forget to test the very first window before sliding.",
        ],
        brute_force="Recompute each window's sum from scratch: **O(n·k)** — 6·10⁷ for the big test.",
        approach="""
**Dry run** `[2,2,2,2,5,5,5,8]`, `k = 3`, need = 12: sums 6, 6, 9, **12**, **15**, **18** → 3 windows qualify.
""",
        complexity="Time **O(n)**, space **O(1)**.",
        pitfalls="- `>=`, not `>`.\n- Count the first window.\n- Compare sums with `k * threshold` rather than dividing.",
        follow_up="Counting windows by any sum condition works the same way; with a *variable* length you need prefix sums.",
    ),
),
# ---------------------------------------------------------------- 1658
dict(
    id="minimum-operations-to-reduce-x-to-zero",
    title="Minimum Operations to Reduce X to Zero",
    difficulty="Medium",
    pattern="Sliding Window",
    leetcode=LC.format("minimum-operations-to-reduce-x-to-zero"),
    entry="minOperations",
    description=r"""
You have a list of positive integers `nums` and a number `x`. In one operation you remove either the **first** or
the **last** element of the list and subtract its value from `x`. Return the fewest operations that bring `x` to
exactly `0`, or `-1` if that is impossible.

**Constraints**

- `1 <= len(nums) <= 10^5`
- `1 <= nums[i] <= 10^4`, `1 <= x <= 10^9`

**Example 1:** `nums = [1,1,4,2,3], x = 5` → `2` (remove 3, then 2 from the right).

**Example 2:** `nums = [5,6,7,8,9], x = 4` → `-1`.

**Example 3:** `nums = [3,2,20,1,1,3], x = 10` → `5`.
""",
    starter='''class Solution:
    def minOperations(self, nums: List[int], x: int) -> int:
        pass
''',
    solution='''class Solution:
    def minOperations(self, nums, x):
        target = sum(nums) - x           # sum of the middle part that stays
        if target < 0:
            return -1
        best = -1
        total = left = 0
        for right, v in enumerate(nums):
            total += v
            while total > target:
                total -= nums[left]
                left += 1
            if total == target and right - left + 1 > best:
                best = right - left + 1
        return -1 if best < 0 else len(nums) - best
''',
    tests=[
        [[1, 1, 4, 2, 3], 5],
        [[5, 6, 7, 8, 9], 4],
        [[3, 2, 20, 1, 1, 3], 10],
        [[1, 1], 2],
        [[1, 1], 3],
        [[5], 5],
        [[5], 4],
        [[2, 3, 1, 1, 1], 5],
        [[8828, 9581, 49, 9818, 9974, 9869, 9991, 10000, 10000, 10000, 9999, 9993, 9904, 8819, 1231, 6309], 134365],
        [[1, 2, 3, 4, 5], 15],
        [_ops_big, sum(_ops_big[:2000]) + sum(_ops_big[-3500:])],
        [_ops_big, sum(_ops_big)],
        [_ops_big, 10 ** 9],
        [[1] * 20000, 12345],
    ],
    wrong_solutions=[
        '''class Solution:
    def minOperations(self, nums, x):
        target = sum(nums) - x
        best = 0                              # bug: 0 doubles as "not found" and "keep nothing"
        total = left = 0
        for right, v in enumerate(nums):
            total += v
            while total > target and left <= right:
                total -= nums[left]
                left += 1
            if total == target:
                best = max(best, right - left + 1)
        return len(nums) - best if best else -1
''',
        '''class Solution:
    def minOperations(self, nums, x):
        i, j, ops = 0, len(nums) - 1, 0
        while x > 0 and i <= j:               # greedy: always take the larger end
            if nums[i] >= nums[j]:
                x -= nums[i]; i += 1
            else:
                x -= nums[j]; j -= 1
            ops += 1
        return ops if x == 0 else -1
''',
    ],
    guide=dict(
        prereqs="Variable-size window on positive numbers (lesson 1, *Minimum Size Subarray Sum*).",
        intuition="""
Removing values from both ends leaves a **contiguous middle piece** untouched. The removed values sum to `x`,
so the middle piece sums to `total − x`. Fewest removals = **longest** middle piece with that sum. Since all
numbers are positive, a sliding window finds the longest subarray with a given sum.
""",
        hints=[
            "Think about what is left over, not what is removed.",
            "The leftover is a contiguous subarray with sum total − x. You want it as long as possible.",
            "Window on positives: grow right, shrink while the sum is too big, record the length when the sum matches. Answer n − longest (or −1).",
        ],
        brute_force="Try every pair (take `i` from the left, `j` from the right) with prefix sums: **O(n²)** — 4·10⁸ for n = 20 000.",
        approach="""
**Dry run** `[1,1,4,2,3]`, `x = 5`: total 11, target 6. The window `[1,1,4]` sums to 6 (length 3) → answer 5 − 3 = **2**.

Edge: `target == 0` (remove everything) is found by the empty window, giving `n`; `target < 0` → `-1`.
""",
        complexity="Time **O(n)**, space **O(1)**.",
        pitfalls="""
- `x` equal to the total sum: the answer is `n`, not `-1` — don't use length 0 as the "not found" marker.
- `x` larger than the total: return `-1` before running the window.
- Greedily taking the larger end does not work.
""",
        follow_up="With negative numbers the window breaks; use a hash map of prefix sums (longest subarray with sum k).",
    ),
),
# ---------------------------------------------------------------- 1838
dict(
    id="frequency-of-the-most-frequent-element",
    title="Frequency of the Most Frequent Element",
    difficulty="Medium",
    pattern="Sliding Window",
    leetcode=LC.format("frequency-of-the-most-frequent-element"),
    entry="maxFrequency",
    description=r"""
You may perform **at most `k`** operations on the list `nums`; one operation picks an element and **adds 1** to it.
Afterwards, how many copies of the same value can the list contain at most? Return that maximum count.

**Constraints**

- `1 <= len(nums) <= 10^5`
- `1 <= nums[i] <= 10^5`, `1 <= k <= 10^5` (tests here also use `k = 0`)

**Example 1:** `nums = [1,2,4], k = 5` → `3` (raise 1 by 3 and 2 by 2 to get `[4,4,4]`).

**Example 2:** `nums = [1,4,8,13], k = 5` → `2`.
""",
    starter='''class Solution:
    def maxFrequency(self, nums: List[int], k: int) -> int:
        pass
''',
    solution='''class Solution:
    def maxFrequency(self, nums, k):
        nums = sorted(nums)
        left = total = best = 0
        for right, x in enumerate(nums):
            total += x
            while x * (right - left + 1) - total > k:
                total -= nums[left]
                left += 1
            if right - left + 1 > best:
                best = right - left + 1
        return best
''',
    tests=[
        [[1, 2, 4], 5],
        [[1, 4, 8, 13], 5],
        [[3, 9, 6], 2],
        [[5], 100],
        [[9, 1, 1, 9], 0],
        [[4, 1, 2], 5],
        [[1, 1, 1, 1], 0],
        [[10, 1, 10, 1, 10], 3],
        [[1, 2, 3, 4, 5], 6],
        [[100000, 1], 99998],
        [_freq_big, 100000],
        [_freq_big, 0],
        [list(range(20000, 0, -1)), 50000],
    ],
    wrong_solutions=[
        '''class Solution:
    def maxFrequency(self, nums, k):
        left = total = best = 0                 # bug: forgot to sort
        for right, x in enumerate(nums):
            total += x
            while x * (right - left + 1) - total > k:
                total -= nums[left]
                left += 1
            best = max(best, right - left + 1)
        return best
''',
        '''class Solution:
    def maxFrequency(self, nums, k):
        nums = sorted(nums)
        best = 1
        for i in range(1, len(nums)):           # only ever raises one neighbour
            if nums[i] - nums[i - 1] <= k:
                best = 2
        return best
''',
    ],
    guide=dict(
        prereqs="Sorting; variable-size window with a running sum.",
        intuition="""
You can only **increase** values, so the final repeated value should be one that already exists, and the cheapest
elements to raise to it are the ones just below it. After sorting, those are its left neighbours — a window
ending at that value. Raising every element of the window `[left..right]` to `nums[right]` costs

$$\\text{nums[right]} \\times \\text{length} - \\text{sum of the window}.$$

Keep the window as long as that cost is at most `k`.
""",
        hints=[
            "Sort first. Which elements are cheapest to turn into nums[right]?",
            "The ones immediately to its left. Cost = nums[right] * window_length − window_sum.",
            "Grow right; while cost > k, drop nums[left]. Track the largest window.",
        ],
        brute_force="For each target value, walk left accumulating cost until `k` runs out: **O(n²)** after sorting.",
        approach="""
**Dry run** sorted `[1,2,4]`, `k = 5`: right=0 cost 0; right=1 cost 2·2−3 = 1; right=2 cost 4·3−7 = 5 ≤ 5 → window 3.

`[1,4,8,13]`, `k = 5`: at 4 cost 3 ✓ (size 2); at 8 cost 24−13 = 11 → drop 1 → 16−12 = 4 ✓ (size 2); at 13: 39−25 = 14 → drop 4 → 26−21 = 5 ✓ (size 2). Answer 2.
""",
        complexity="Time **O(n log n)** for sorting + O(n) window. Space O(n) for the sorted copy.",
        pitfalls="""
- Forgetting to sort — the cost formula assumes `nums[right]` is the window maximum.
- The cost can be large (`10^5 × 10^5`); fine in Python, overflow risk in 32-bit languages.
""",
        follow_up="A binary-search variant: for each `right`, binary-search the smallest `left` using prefix sums — O(n log n) as well.",
    ),
),
# ---------------------------------------------------------------- 992
dict(
    id="subarrays-with-k-different-integers",
    title="Subarrays with K Different Integers",
    difficulty="Hard",
    pattern="Sliding Window",
    leetcode=LC.format("subarrays-with-k-different-integers"),
    entry="subarraysWithKDistinct",
    description=r"""
Count the contiguous subarrays of `nums` that contain **exactly `k` distinct values**.

**Constraints**

- `1 <= len(nums) <= 2·10^4`
- `1 <= nums[i], k <= len(nums)`

**Example 1:** `nums = [1,2,1,2,3], k = 2` → `7`
(`[1,2]`, `[2,1]`, `[1,2]`, `[2,3]`, `[1,2,1]`, `[2,1,2]`, `[1,2,1,2]`).

**Example 2:** `nums = [1,2,1,3,4], k = 3` → `3`.
""",
    starter='''class Solution:
    def subarraysWithKDistinct(self, nums: List[int], k: int) -> int:
        pass
''',
    solution='''class Solution:
    def subarraysWithKDistinct(self, nums, k):
        def at_most(limit):
            if limit < 0:
                return 0
            count = {}
            left = total = 0
            for right, x in enumerate(nums):
                count[x] = count.get(x, 0) + 1
                while len(count) > limit:
                    y = nums[left]
                    count[y] -= 1
                    if count[y] == 0:
                        del count[y]
                    left += 1
                total += right - left + 1
            return total
        return at_most(k) - at_most(k - 1)
''',
    tests=[
        [[1, 2, 1, 2, 3], 2],
        [[1, 2, 1, 3, 4], 3],
        [[1], 1],
        [[1, 1, 1], 1],
        [[1, 2], 1],
        [[1, 2], 2],
        [[1, 2, 3], 3],
        [[2, 1, 1, 1, 2], 1],
        [[1, 2, 3, 1, 2, 3], 3],
        [[5, 5, 5, 5], 2],
        [_kd_big, 10],
        [_kd_big, 40],
        [[i % 7 + 1 for i in range(20000)], 7],
    ],
    wrong_solutions=[
        '''class Solution:
    def subarraysWithKDistinct(self, nums, k):
        count, left, total = {}, 0, 0
        for right, x in enumerate(nums):          # counts "at most k", not "exactly k"
            count[x] = count.get(x, 0) + 1
            while len(count) > k:
                count[nums[left]] -= 1
                if count[nums[left]] == 0:
                    del count[nums[left]]
                left += 1
            total += right - left + 1
        return total
''',
        '''class Solution:
    def subarraysWithKDistinct(self, nums, k):
        count, left, total = {}, 0, 0
        for right, x in enumerate(nums):          # counts only the longest window per right edge
            count[x] = count.get(x, 0) + 1
            while len(count) > k:
                count[nums[left]] -= 1
                if count[nums[left]] == 0:
                    del count[nums[left]]
                left += 1
            if len(count) == k:
                total += 1
        return total
''',
    ],
    guide=dict(
        prereqs="Lesson *Counting windows* §4 (at most K distinct, and the exactly-K trick). *Fruit Into Baskets*.",
        intuition="""
"Exactly `k` distinct" is awkward for a window: adding an element can make a window valid *or* invalid, so the
condition is not one-directional. "**At most** `k` distinct" *is* one-directional, and

$$\\text{exactly}(k) = \\text{atMost}(k) - \\text{atMost}(k-1).$$

Counting at-most-`k` subarrays: for each right edge, once the window `[left, right]` is the longest legal one,
**every** start from `left` to `right` gives a legal subarray — that is `right − left + 1` of them.
""",
        hints=[
            "Can you count subarrays with AT MOST k distinct values using a window?",
            "For each right edge, the number of valid starts is right − left + 1.",
            "Answer = atMost(k) − atMost(k − 1).",
        ],
        brute_force="For each start, extend with a set and count while the set has exactly `k` values: **O(n²)** — 2·10⁸ set operations at n = 20 000.",
        approach="""
**Dry run** `[1,2,1,2,3]`: `atMost(2)` adds 1+2+3+4+2 = 12; `atMost(1)` adds 1+1+1+1+1 = 5; 12 − 5 = **7**.
""",
        complexity="Time **O(n)** (two window passes), space **O(k)**.",
        pitfalls="""
- Returning `atMost(k)` alone.
- Adding 1 per right edge instead of `right − left + 1`.
- Not deleting zero-count keys, which corrupts `len(count)`.
""",
        follow_up="A single-pass version keeps two left pointers (for `k` and `k−1`). The same subtraction trick solves *Count Number of Nice Subarrays* (1248) and *Binary Subarrays With Sum* (930).",
    ),
),
]
