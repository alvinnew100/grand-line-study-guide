import random

_r = random.Random(250)

_concat_big = [_r.randint(1, 1000) for _ in range(15000)]
_replace_big = [_r.randint(1, 10**5) for _ in range(20000)]
_subseq_t = "".join(_r.choice("abc") for _ in range(50000))
_subseq_s_yes = _subseq_t[::500]
_subseq_s_no = _subseq_t[::500] + "d"

_maj_big = [7] * 15001 + [_r.randint(-10**9, 10**9) for _ in range(14999)]
random.Random(9).shuffle(_maj_big)

_colors_big = [_r.choice([0, 1, 2]) for _ in range(30000)]

_sub_big = [_r.randint(-3, 3) for _ in range(20000)]

_fmp_perm = list(range(1, 20001))
_fmp_perm.remove(13579)
random.Random(11).shuffle(_fmp_perm)
_fmp_full = list(range(1, 15001))
random.Random(12).shuffle(_fmp_full)
_fmp_full += [-5, 0, 10**9, 15000, 1]

# NumMatrix large case: 80 x 80 matrix and 3000 queries
_mat_big = [[_r.randint(-100, 100) for _ in range(80)] for _ in range(80)]
_q_big = []
for _ in range(3000):
    r1, r2 = sorted(_r.randint(0, 79) for _ in range(2))
    c1, c2 = sorted(_r.randint(0, 79) for _ in range(2))
    _q_big.append([r1, c1, r2, c2])

_M1 = [[3, 0, 1, 4, 2], [5, 6, 3, 2, 1], [1, 2, 0, 1, 5], [4, 1, 0, 1, 7], [1, 0, 3, 0, 5]]


def _nm(matrix, queries):
    return [["NumMatrix"] + ["sumRegion"] * len(queries), [[matrix]] + queries]


PROBLEMS = [
# ---------------------------------------------------------------------------
dict(
    id="concatenation-of-array",
    title="Concatenation of Array",
    difficulty="Easy",
    pattern="Arrays & Hashing",
    leetcode="https://leetcode.com/problems/concatenation-of-array/",
    neetcode="https://neetcode.io/problems/concatenation-of-array",
    entry="getConcatenation",
    description=r"""
Given an integer list `nums` of length `n`, return a new list `ans` of length `2n` that is `nums`
written twice in a row: `ans[i] == nums[i]` and `ans[i + n] == nums[i]` for every `0 <= i < n`.

Try writing it **without** the `+`/`*` list shortcuts first (allocate the result and fill it by index) —
that's the version an interviewer in a lower-level language would expect.

**Constraints**

- `1 <= n <= 1000` on LeetCode (our judge also tries a much bigger list)
- `1 <= nums[i] <= 1000`

**Example 1:** `nums = [1, 2, 1]` → `[1, 2, 1, 1, 2, 1]`

**Example 2:** `nums = [1, 3, 2, 1]` → `[1, 3, 2, 1, 1, 3, 2, 1]`
""",
    starter='''class Solution:
    def getConcatenation(self, nums: List[int]) -> List[int]:
        pass
''',
    solution='''class Solution:
    def getConcatenation(self, nums):
        n = len(nums)
        ans = [0] * (2 * n)
        for i, x in enumerate(nums):
            ans[i] = x
            ans[i + n] = x
        return ans
''',
    tests=[
        [[1, 2, 1]],
        [[1, 3, 2, 1]],
        [[7]],
        [[1000, 1]],
        [[5, 5, 5]],
        [[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]],
        [[2, 1]],
        [[9, 8, 7, 6]],
        [_concat_big],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def getConcatenation(self, nums):
        return nums + nums[1:]          # off by one: drops the first element of the copy
''',
        '''class Solution:
    def getConcatenation(self, nums):
        return nums + nums[::-1]        # second half reversed
''',
    ],
    guide=dict(
        prereqs="List indexing; how Python lists are dynamic arrays (see *The Arrays & Hashing pattern*).",
        intuition="Element `i` of the input lands in two places of the output: position `i` and position `i + n`.",
        hints=[
            "How long is the output? Allocate it up front.",
            "Where does nums[i] go in the second copy?",
            "One loop writing ans[i] and ans[i + n] — or simply `nums + nums` / `nums * 2` in Python.",
        ],
        brute_force="Appending element-by-element to an empty list twice is also O(n) amortised (dynamic-array doubling), so there is no slow approach here — the point is index arithmetic and knowing what `+` costs.",
        approach="""
1. `n = len(nums)`, `ans = [0] * (2n)`.
2. For each `i`: `ans[i] = nums[i]` and `ans[i + n] = nums[i]`.

**Dry run** `[1, 2, 1]`, n = 3: i=0 → ans[0]=ans[3]=1; i=1 → ans[1]=ans[4]=2; i=2 → ans[2]=ans[5]=1 →
`[1, 2, 1, 1, 2, 1]`.

In Python, `nums + nums` or `nums * 2` does exactly this in C speed; both are O(n).
""",
        complexity="Time **O(n)**, space **O(n)** for the output (unavoidable — you must return 2n values).",
        pitfalls="- `nums * 2` on a list of *lists* copies references, not the inner lists (shallow copy). Not an issue for ints.\n- Don't return `nums.extend(nums)` — `extend` returns `None` (and mutates the input).",
        follow_up="*Shuffle the Array* (LC 1470) and *Build Array from Permutation* (LC 1920) are similar index-mapping warm-ups.",
    ),
),
# ---------------------------------------------------------------------------
dict(
    id="replace-elements-with-greatest-element-on-right",
    title="Replace Elements with Greatest Element on Right Side",
    difficulty="Easy",
    pattern="Arrays & Hashing",
    leetcode="https://leetcode.com/problems/replace-elements-with-greatest-element-on-right-side/",
    neetcode="https://neetcode.io/problems/replace-elements-with-greatest-element-on-right-side",
    entry="replaceElements",
    description=r"""
Given an integer list `arr`, replace every element with the **largest value strictly to its right**.
The last element has nothing to its right, so it becomes `-1`. Return the resulting list.

**Constraints**

- `1 <= len(arr) <= 10^4`
- `1 <= arr[i] <= 10^5`

**Example 1:** `arr = [17, 18, 5, 4, 6, 1]` → `[18, 6, 6, 6, 1, -1]`

**Example 2:** `arr = [400]` → `[-1]`
""",
    starter='''class Solution:
    def replaceElements(self, arr: List[int]) -> List[int]:
        pass
''',
    solution='''class Solution:
    def replaceElements(self, arr):
        right_max = -1
        for i in range(len(arr) - 1, -1, -1):
            arr[i], right_max = right_max, max(right_max, arr[i])
        return arr
''',
    tests=[
        [[17, 18, 5, 4, 6, 1]],
        [[400]],
        [[1, 2]],
        [[2, 1]],
        [[5, 5, 5, 5]],
        [[1, 2, 3, 4, 5]],
        [[5, 4, 3, 2, 1]],
        [[3, 1, 3, 1, 3]],
        [[100000, 1, 99999]],
        [_replace_big],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def replaceElements(self, arr):
        right_max = -1
        for i in range(len(arr) - 1, -1, -1):
            right_max = max(right_max, arr[i])   # updated too early: includes arr[i] itself
            arr[i] = right_max
        arr[-1] = -1
        return arr
''',
        '''class Solution:
    def replaceElements(self, arr):
        return arr[1:] + [-1]                    # neighbour, not the maximum
''',
    ],
    guide=dict(
        prereqs="Reverse iteration with `range(n-1, -1, -1)`; the suffix-maximum idea.",
        intuition="Scanning from the **right**, you always know the maximum of everything you've already passed — which is exactly 'the greatest element to the right' of the current position.",
        hints=[
            "Recomputing max(arr[i+1:]) for every i is O(n²). Which direction makes the answer easy to maintain?",
            "Walk from the end; keep a running maximum, starting at -1.",
            "At each step: save arr[i], overwrite it with the running max, then update the running max with the saved value.",
        ],
        brute_force="For each `i`, compute `max(arr[i+1:])` → **O(n²)** time. On 2·10⁴ elements that's 2·10⁸ comparisons.",
        approach="""
1. `right_max = -1`.
2. For `i` from `n-1` down to `0`: `arr[i], right_max = right_max, max(right_max, arr[i])`.
   (Tuple assignment evaluates the right side first, so the old `arr[i]` feeds into the new max.)

**Dry run** `[17, 18, 5, 4, 6, 1]`:

| i | arr[i] | right_max before | write | right_max after |
|---|---|---|---|---|
| 5 | 1 | -1 | -1 | 1 |
| 4 | 6 | 1 | 1 | 6 |
| 3 | 4 | 6 | 6 | 6 |
| 2 | 5 | 6 | 6 | 6 |
| 1 | 18 | 6 | 6 | 18 |
| 0 | 17 | 18 | 18 | 18 |

Result `[18, 6, 6, 6, 1, -1]`.
""",
        complexity="Time **O(n)**, extra space **O(1)** (in place).",
        pitfalls="- Updating the max *before* writing includes the element itself.\n- Without tuple assignment, you must save `arr[i]` in a temp before overwriting it.",
        follow_up="This 'suffix max' is half of *Trapping Rain Water*. *Next Greater Element* asks for the *nearest* greater element instead → monotonic stack.",
    ),
),
# ---------------------------------------------------------------------------
dict(
    id="is-subsequence",
    title="Is Subsequence",
    difficulty="Easy",
    pattern="Arrays & Hashing",
    leetcode="https://leetcode.com/problems/is-subsequence/",
    neetcode="https://neetcode.io/problems/is-subsequence",
    entry="isSubsequence",
    description=r"""
A **subsequence** of a string is what remains after deleting zero or more characters without reordering
the rest (`"ace"` is a subsequence of `"abcde"`, `"aec"` is not).

Given strings `s` and `t`, return `True` if `s` is a subsequence of `t`.

**Constraints**

- `0 <= len(s) <= 100`
- `0 <= len(t) <= 10^4` (our large test is longer)
- lowercase English letters only

**Example 1:** `s = "abc", t = "ahbgdc"` → `True`

**Example 2:** `s = "axc", t = "ahbgdc"` → `False`

**Follow-up:** if there were billions of different `s` strings to test against the same `t`, how would you preprocess `t`?
""",
    starter='''class Solution:
    def isSubsequence(self, s: str, t: str) -> bool:
        pass
''',
    solution='''class Solution:
    def isSubsequence(self, s, t):
        i = 0
        for ch in t:
            if i < len(s) and s[i] == ch:
                i += 1
        return i == len(s)
''',
    tests=[
        ["abc", "ahbgdc"],
        ["axc", "ahbgdc"],
        ["", "ahbgdc"],
        ["", ""],
        ["a", ""],
        ["acb", "ahbgdc"],
        ["aaaaaa", "bbaaaa"],
        ["b", "abc"],
        ["abc", "abc"],
        ["abcd", "abc"],
        ["leeeeetcode", "yyyyylyyyyyeyyyyeyyyeyyeytcode"],
        [_subseq_s_yes, _subseq_t],
        [_subseq_s_no, _subseq_t],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def isSubsequence(self, s, t):
        return all(c in t for c in s)          # ignores order and multiplicity
''',
        '''class Solution:
    def isSubsequence(self, s, t):
        i = 0
        for ch in t:
            if s[i] == ch:                     # crashes / misbehaves when s is empty or fully matched
                i += 1
        return i == len(s)
''',
    ],
    guide=dict(
        prereqs="Two indices walking two sequences (a preview of *The Two Pointers pattern*).",
        intuition="Greedily match: scan `t` once, and every time its character equals the **next unmatched** character of `s`, consume it. Matching as early as possible never hurts, because it leaves the most of `t` for the rest of `s`.",
        hints=[
            "You need one index into s and one into t.",
            "When t[j] == s[i], advance both; otherwise advance only j.",
            "s is a subsequence iff you consumed all of s by the time t runs out.",
        ],
        brute_force="Enumerate all 2^|t| subsequences of `t` and compare — exponential. Or a DP on (i, j) — O(|s|·|t|). The greedy scan beats both.",
        approach="""
1. `i = 0` (next char of `s` to match).
2. For each `ch` in `t`: if `i < len(s)` and `s[i] == ch`, do `i += 1`.
3. Return `i == len(s)`.

**Dry run** `s = "abc"`, `t = "ahbgdc"`: a✓ (i=1) → h → b✓ (i=2) → g → d → c✓ (i=3). `i == 3` → **True**.

With `s = "axc"`: a✓ → then no `x` ever appears → i stays 1 → **False**.
""",
        complexity="Time **O(|t|)**, space **O(1)**.",
        pitfalls="- Guard `i < len(s)` before reading `s[i]` (empty `s` or all of `s` already matched).\n- `c in t` checks ignore order and repeated letters.",
        follow_up="Many queries: precompute for each letter the sorted list of its positions in `t`, then for each char of `s` binary-search (`bisect`) the next position after the current one → O(|s| log |t|) per query.",
    ),
),
# ---------------------------------------------------------------------------
dict(
    id="majority-element",
    title="Majority Element",
    difficulty="Easy",
    pattern="Arrays & Hashing",
    leetcode="https://leetcode.com/problems/majority-element/",
    neetcode="https://neetcode.io/problems/majority-element",
    entry="majorityElement",
    description=r"""
A list `nums` of length `n` is guaranteed to contain a **majority element** — a value that occupies
**more than** `n / 2` of the positions. Return it.

**Constraints**

- `1 <= n <= 5 * 10^4`
- `-10^9 <= nums[i] <= 10^9`
- a majority element always exists

**Example 1:** `nums = [3, 2, 3]` → `3`

**Example 2:** `nums = [2, 2, 1, 1, 1, 2, 2]` → `2`

**Follow-up:** solve it in O(n) time and **O(1)** extra space.
""",
    starter='''class Solution:
    def majorityElement(self, nums: List[int]) -> int:
        pass
''',
    solution='''class Solution:
    def majorityElement(self, nums):
        candidate, votes = None, 0
        for x in nums:
            if votes == 0:
                candidate = x
            votes += 1 if x == candidate else -1
        return candidate
''',
    tests=[
        [[3, 2, 3]],
        [[2, 2, 1, 1, 1, 2, 2]],
        [[1]],
        [[5, 5]],
        [[6, 5, 5]],
        [[1, 2, 1, 2, 1]],
        [[-1, -1, 2147483647]],
        [[4, 4, 4, 1, 2, 3, 4]],
        [[9, 8, 9, 7, 9, 6, 9]],
        [[2, 1, 2, 1, 2, 1, 2, 1, 2]],
        [_maj_big],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def majorityElement(self, nums):
        return nums[len(nums) // 2]           # only valid AFTER sorting
''',
        '''class Solution:
    def majorityElement(self, nums):
        # counts only the first half of the list
        half = nums[:len(nums) // 2] or nums
        best = collections.Counter(half).most_common(1)[0][0]
        candidate = best
        return candidate
''',
    ],
    guide=dict(
        prereqs="Counting with a dict; the Boyer–Moore voting algorithm (taught here).",
        intuition="""
Pair off each occurrence of the majority value with a *different* value and cancel them. Because the
majority has more than half the slots, it can't be completely cancelled — something of it survives.
Boyer–Moore voting performs this cancellation in a single pass with one candidate and one counter.
""",
        hints=[
            "A dict of counts solves it in O(n) time — but O(n) space. Can you do O(1) space?",
            "If you sort the list, which index is guaranteed to hold the majority?",
            "Keep a candidate and a vote counter: +1 for a match, -1 otherwise, and adopt a new candidate when the counter hits 0.",
        ],
        brute_force="Count each element by scanning the whole list: **O(n²)**. Dict counting: O(n) time/O(n) space. Sorting and taking `nums[n // 2]`: O(n log n).",
        approach="""
1. `candidate = None`, `votes = 0`.
2. For each `x`: if `votes == 0`, set `candidate = x`. Then `votes += 1` if `x == candidate` else `votes -= 1`.
3. Return `candidate` (the majority is guaranteed, so no verification pass is needed).

**Dry run** `[2, 2, 1, 1, 1, 2, 2]`:

| x | candidate | votes |
|---|---|---|
| 2 | 2 | 1 |
| 2 | 2 | 2 |
| 1 | 2 | 1 |
| 1 | 2 | 0 |
| 1 | 1 | 1 |
| 2 | 1 | 0 |
| 2 | 2 | 1 |

Answer **2**.
""",
        complexity="Time **O(n)**, space **O(1)**.",
        pitfalls="- `nums[n // 2]` is only the answer after sorting.\n- If the majority were *not* guaranteed, you'd need a second pass to verify the candidate's count.",
        follow_up="*Majority Element II* (LC 229): elements appearing more than n/3 times — run voting with **two** candidates and verify.",
    ),
),
# ---------------------------------------------------------------------------
dict(
    id="sort-colors",
    title="Sort Colors",
    difficulty="Medium",
    pattern="Arrays & Hashing",
    leetcode="https://leetcode.com/problems/sort-colors/",
    neetcode="https://neetcode.io/problems/sort-colors",
    entry="sortColors",
    inplace_arg=0,
    description=r"""
`nums` holds only the values `0`, `1` and `2` (think red, white, blue). Rearrange it **in place** so all
0s come first, then all 1s, then all 2s. Do not call a library sort and do not return anything — the
judge inspects `nums` after your method returns.

**Constraints**

- `1 <= len(nums) <= 300` on LeetCode (our judge also uses a much longer list)
- `nums[i]` is `0`, `1` or `2`

**Example 1:** `nums = [2, 0, 2, 1, 1, 0]` → `nums` becomes `[0, 0, 1, 1, 2, 2]`

**Example 2:** `nums = [2, 0, 1]` → `[0, 1, 2]`

**Follow-up:** a single pass with O(1) extra space.
""",
    starter='''class Solution:
    def sortColors(self, nums: List[int]) -> None:
        """
        Do not return anything, modify nums in-place instead.
        """
        pass
''',
    solution='''class Solution:
    def sortColors(self, nums):
        lo, mid, hi = 0, 0, len(nums) - 1
        while mid <= hi:
            if nums[mid] == 0:
                nums[lo], nums[mid] = nums[mid], nums[lo]
                lo += 1
                mid += 1
            elif nums[mid] == 1:
                mid += 1
            else:
                nums[mid], nums[hi] = nums[hi], nums[mid]
                hi -= 1              # do NOT advance mid: the swapped-in value is unexamined
''',
    tests=[
        [[2, 0, 2, 1, 1, 0]],
        [[2, 0, 1]],
        [[0]],
        [[1]],
        [[2, 2, 0]],
        [[2, 2, 2, 1, 1, 0, 0]],
        [[0, 0, 0]],
        [[1, 0]],
        [[1, 2, 0, 2, 1, 0, 1]],
        [[2, 1, 2, 0, 0, 2, 1, 1, 0, 2]],
        [_colors_big],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def sortColors(self, nums):
        lo, mid, hi = 0, 0, len(nums) - 1
        while mid <= hi:
            if nums[mid] == 0:
                nums[lo], nums[mid] = nums[mid], nums[lo]
                lo += 1
                mid += 1
            elif nums[mid] == 1:
                mid += 1
            else:
                nums[mid], nums[hi] = nums[hi], nums[mid]
                hi -= 1
                mid += 1             # bug: skips the value just swapped in
''',
        '''class Solution:
    def sortColors(self, nums):
        nums = sorted(nums)          # rebinds the local name; caller's list is untouched
''',
    ],
    guide=dict(
        prereqs="Counting sort (see *Prefix sums, counting and bucket tricks*); in-place swaps; loop invariants.",
        intuition="""
Two easy ideas: **count** the 0s, 1s and 2s and overwrite (two passes), or Dijkstra's **Dutch national
flag** partition — three pointers that grow a 0-zone at the front and a 2-zone at the back in one pass.
""",
        hints=[
            "With only three possible values, counting sort is O(n). Can you do one pass?",
            "Maintain regions: [0, lo) are 0s, [lo, mid) are 1s, (hi, end] are 2s, [mid, hi] unknown.",
            "Swap 0s to lo and 2s to hi. After swapping with hi, don't advance mid — you haven't examined the new value.",
        ],
        brute_force="Any comparison sort (bubble/insertion O(n²), or `nums.sort()` O(n log n)). Counting: count each colour, then rewrite — O(n), two passes.",
        approach="""
Invariant: `nums[:lo]` all 0, `nums[lo:mid]` all 1, `nums[hi+1:]` all 2, `nums[mid:hi+1]` unexamined.

While `mid <= hi`:
- `0` → swap with `lo`; `lo += 1`, `mid += 1` (what comes back from `lo` is a known 1, or mid==lo).
- `1` → `mid += 1`.
- `2` → swap with `hi`; `hi -= 1` (keep `mid` — the arriving value is unknown).

**Dry run** `[2, 0, 1]`:

| lo | mid | hi | nums | action |
|---|---|---|---|---|
| 0 | 0 | 2 | [2,0,1] | 2 → swap(0,2) → [1,0,2], hi=1 |
| 0 | 0 | 1 | [1,0,2] | 1 → mid=1 |
| 0 | 1 | 1 | [1,0,2] | 0 → swap(0,1) → [0,1,2], lo=1, mid=2 |

mid > hi → done: `[0, 1, 2]`.
""",
        complexity="Time **O(n)** — each step either advances `mid` or shrinks `hi`. Space **O(1)**.",
        pitfalls="""
- Advancing `mid` after a swap with `hi` skips an unexamined element (`[2,2,0]` stays wrong).
- `nums = sorted(nums)` only rebinds the local variable; use `nums[:] = ...` or `nums.sort()` to mutate.
- Loop condition is `mid <= hi`, not `mid < hi`.
""",
        follow_up="This 3-way partition is the core of quicksort with many duplicates (and quickselect). *Sort Colors II* (k colours) → counting sort or recursive partitioning.",
    ),
),
# ---------------------------------------------------------------------------
dict(
    id="subarray-sum-equals-k",
    title="Subarray Sum Equals K",
    difficulty="Medium",
    pattern="Arrays & Hashing",
    leetcode="https://leetcode.com/problems/subarray-sum-equals-k/",
    neetcode="https://neetcode.io/problems/subarray-sum-equals-k",
    entry="subarraySum",
    description=r"""
Given an integer list `nums` (values can be **negative**) and an integer `k`, count how many
**contiguous, non-empty** subarrays have a sum of exactly `k`.

**Constraints**

- `1 <= len(nums) <= 2 * 10^4`
- `-1000 <= nums[i] <= 1000`
- `-10^7 <= k <= 10^7`

**Example 1:** `nums = [1, 1, 1], k = 2` → `2` (`[1,1]` starting at index 0, and at index 1)

**Example 2:** `nums = [1, 2, 3], k = 3` → `2` (`[1,2]` and `[3]`)

**Example 3:** `nums = [1, -1, 0], k = 0` → `3`
""",
    starter='''class Solution:
    def subarraySum(self, nums: List[int], k: int) -> int:
        pass
''',
    solution='''class Solution:
    def subarraySum(self, nums, k):
        seen = {0: 1}          # prefix sum -> how many times it has occurred
        total = count = 0
        for x in nums:
            total += x
            count += seen.get(total - k, 0)
            seen[total] = seen.get(total, 0) + 1
        return count
''',
    tests=[
        [[1, 1, 1], 2],
        [[1, 2, 3], 3],
        [[1, -1, 0], 0],
        [[1], 1],
        [[1], 0],
        [[0, 0, 0], 0],
        [[-1, -1, 1], 0],
        [[3, 4, 7, 2, -3, 1, 4, 2], 7],
        [[1, 2, 1, 2, 1], 3],
        [[-5, 5, -5, 5], 0],
        [[1000] * 50, 5000],
        [_sub_big, 5],
        [[0] * 3000, 0],
    ],
    wrong_solutions=[
        '''class Solution:
    def subarraySum(self, nums, k):
        # sliding window: only valid for non-negative numbers
        l = total = count = 0
        for r, x in enumerate(nums):
            total += x
            while l <= r and total > k:
                total -= nums[l]
                l += 1
            if total == k:
                count += 1
        return count
''',
        '''class Solution:
    def subarraySum(self, nums, k):
        seen = {}                      # forgot the empty prefix {0: 1}
        total = count = 0
        for x in nums:
            total += x
            count += seen.get(total - k, 0)
            seen[total] = seen.get(total, 0) + 1
        return count
''',
    ],
    guide=dict(
        prereqs="Prefix sums and the 'complement lookup' from *Two Sum* (see *Prefix sums, counting and bucket tricks*).",
        intuition="""
Let `P[j]` be the sum of the first `j` elements. The subarray `nums[i:j]` sums to `P[j] - P[i]`. So the
number of good subarrays ending at `j` equals the number of earlier prefix sums equal to `P[j] - k` —
a *Two Sum*-style lookup in a dict of prefix-sum counts.
""",
        hints=[
            "Express the sum of nums[i..j] using prefix sums.",
            "Sliding windows fail here — why? (Hint: negative numbers.)",
            "Store counts of prefix sums seen so far (starting with {0: 1}); at each step add count[total - k].",
        ],
        brute_force="""
Fix a start `i`, extend `j` and keep a running sum: **O(n²)** time, O(1) space. With n = 2·10⁴ that is
2·10⁸ additions — tens of seconds in Python. A sliding window is O(n) but **wrong** with negatives, since
shrinking the window no longer reliably decreases the sum.
""",
        approach="""
1. `seen = {0: 1}` — the empty prefix, so subarrays starting at index 0 are counted.
2. For each `x`: `total += x`; add `seen.get(total - k, 0)` to the answer; then increment `seen[total]`.

**Dry run** `nums = [1, 2, 3]`, `k = 3`:

| x | total | total - k | seen before | +count | seen after |
|---|---|---|---|---|---|
| 1 | 1 | -2 | {0:1} | 0 | {0:1,1:1} |
| 2 | 3 | 0 | {0:1,1:1} | 1 (`[1,2]`) | {…,3:1} |
| 3 | 6 | 3 | {0:1,1:1,3:1} | 1 (`[3]`) | {…,6:1} |

Answer **2**.
""",
        complexity="Time **O(n)** average, space **O(n)** for the dict.",
        pitfalls="""
- Forgetting `{0: 1}` misses every subarray that starts at index 0.
- Look up **before** inserting the current prefix, or `k = 0` would count the empty subarray.
- Store *counts*, not just presence — the same prefix sum can occur many times (e.g. zeros).
""",
        follow_up="*Continuous Subarray Sum* (LC 523) keys on `total % k`; *Subarray Sums Divisible by K* (LC 974) counts remainders; *Path Sum III* applies the same trick on tree paths.",
    ),
),
# ---------------------------------------------------------------------------
dict(
    id="range-sum-query-2d-immutable",
    title="Range Sum Query 2D - Immutable",
    difficulty="Medium",
    pattern="Arrays & Hashing",
    leetcode="https://leetcode.com/problems/range-sum-query-2d-immutable/",
    neetcode="https://neetcode.io/problems/range-sum-query-2d-immutable",
    kind="class",
    entry="NumMatrix",
    description=r"""
Build a class `NumMatrix` that is constructed from a fixed 2-D integer matrix and then answers many
queries of the form `sumRegion(row1, col1, row2, col2)`: the sum of every cell inside the rectangle whose
upper-left corner is `(row1, col1)` and lower-right corner is `(row2, col2)`, **inclusive**.

Each `sumRegion` call must run in **O(1)** time. The matrix never changes after construction.

**Constraints**

- `1 <= rows, cols <= 200`
- `-10^4 <= matrix[r][c] <= 10^5`
- `0 <= row1 <= row2 < rows`, `0 <= col1 <= col2 < cols`
- up to `10^4` calls to `sumRegion`

**Example:**

```
NumMatrix([[3,0,1,4,2],[5,6,3,2,1],[1,2,0,1,5],[4,1,0,1,7],[1,0,3,0,5]])
sumRegion(2, 1, 4, 3)  -> 8
sumRegion(1, 1, 2, 2)  -> 11
sumRegion(1, 2, 2, 4)  -> 12
```

Tests are given LeetCode-style as `[operations, arguments]`; the output is the list of return values
(`None` for the constructor).
""",
    starter='''class NumMatrix:

    def __init__(self, matrix: List[List[int]]):
        pass

    def sumRegion(self, row1: int, col1: int, row2: int, col2: int) -> int:
        pass
''',
    solution='''class NumMatrix:
    def __init__(self, matrix):
        R, C = len(matrix), len(matrix[0])
        # P[r][c] = sum of matrix[0..r-1][0..c-1]; padded with a zero row and column
        P = [[0] * (C + 1) for _ in range(R + 1)]
        for r in range(R):
            row_sum = 0
            for c in range(C):
                row_sum += matrix[r][c]
                P[r + 1][c + 1] = P[r][c + 1] + row_sum
        self.P = P

    def sumRegion(self, row1, col1, row2, col2):
        P = self.P
        return (P[row2 + 1][col2 + 1] - P[row1][col2 + 1]
                - P[row2 + 1][col1] + P[row1][col1])
''',
    tests=[
        _nm(_M1, [[2, 1, 4, 3], [1, 1, 2, 2], [1, 2, 2, 4]]),
        _nm([[7]], [[0, 0, 0, 0]]),
        _nm([[-4, -5]], [[0, 0, 0, 0], [0, 0, 0, 1], [0, 1, 0, 1]]),
        _nm([[1], [2], [3]], [[0, 0, 2, 0], [1, 0, 2, 0], [2, 0, 2, 0]]),
        _nm(_M1, [[0, 0, 4, 4], [0, 0, 0, 0], [4, 4, 4, 4], [0, 4, 4, 4], [4, 0, 4, 4]]),
        _nm([[1, 2, 3], [4, 5, 6], [7, 8, 9]], [[1, 1, 1, 1], [0, 0, 1, 1], [1, 1, 2, 2], [0, 1, 2, 1]]),
        _nm([[0, 0], [0, 0]], [[0, 0, 1, 1]]),
        _nm([[10**5] * 3] * 3, [[0, 0, 2, 2], [1, 0, 1, 2]]),
        _nm([[-10**4, 10**5], [3, -3]], [[0, 0, 1, 1], [1, 0, 1, 1], [0, 1, 1, 1]]),
        _nm(_mat_big, _q_big),
    ],
    examples=1,
    wrong_solutions=[
        '''class NumMatrix:
    def __init__(self, matrix):
        R, C = len(matrix), len(matrix[0])
        P = [[0] * (C + 1) for _ in range(R + 1)]
        for r in range(R):
            for c in range(C):
                P[r + 1][c + 1] = P[r][c + 1] + P[r + 1][c] - P[r][c] + matrix[r][c]
        self.P = P

    def sumRegion(self, row1, col1, row2, col2):
        P = self.P
        # forgot to add back the doubly-subtracted corner
        return P[row2 + 1][col2 + 1] - P[row1][col2 + 1] - P[row2 + 1][col1]
''',
        '''class NumMatrix:
    def __init__(self, matrix):
        R, C = len(matrix), len(matrix[0])
        P = [[0] * (C + 1) for _ in range(R + 1)]
        for r in range(R):
            for c in range(C):
                P[r + 1][c + 1] = P[r][c + 1] + P[r + 1][c] - P[r][c] + matrix[r][c]
        self.P = P

    def sumRegion(self, row1, col1, row2, col2):
        P = self.P
        # exclusive upper bounds: drops the last row and column of the rectangle
        return P[row2][col2] - P[row1][col2] - P[row2][col1] + P[row1][col1]
''',
    ],
    guide=dict(
        prereqs="1-D prefix sums and inclusion–exclusion (see *Prefix sums, counting and bucket tricks*); LeetCode design-problem format.",
        intuition="""
Precompute `P[r][c]` = sum of the rectangle from the top-left corner `(0,0)` down to `(r-1, c-1)`. Any
rectangle is then the big corner rectangle **minus** the strip above, **minus** the strip to the left,
**plus** the top-left corner that was subtracted twice — four lookups, O(1).
""",
        hints=[
            "In 1-D, sum(i..j) = P[j+1] - P[i]. What's the 2-D analogue?",
            "Pad the prefix table with an extra zero row and column so you never index -1.",
            "sum = P[r2+1][c2+1] - P[r1][c2+1] - P[r2+1][c1] + P[r1][c1].",
        ],
        brute_force="Loop over the rectangle on every query: **O(rows·cols)** per query, up to 4·10⁸ cell reads for 10⁴ queries on a 200×200 matrix. Row-wise prefix sums give O(rows) per query — better, still not O(1).",
        approach="""
**Build** (O(R·C)): `P` is `(R+1) × (C+1)` of zeros. Then
`P[r+1][c+1] = matrix[r][c] + P[r][c+1] + P[r+1][c] - P[r][c]` (or the running-row-sum version in the reference).

**Query** (O(1)): `P[r2+1][c2+1] - P[r1][c2+1] - P[r2+1][c1] + P[r1][c1]`.

```mermaid
graph LR
  A["Big = P r2+1, c2+1"] --> B["minus Top strip = P r1, c2+1"]
  B --> C["minus Left strip = P r2+1, c1"]
  C --> D["plus Corner = P r1, c1 (removed twice)"]
```

**Dry run** on the example, `sumRegion(1, 1, 2, 2)` — cells `6,3 / 2,0` = 11:
- `P[3][3]` = sum of rows 0–2, cols 0–2 = 3+0+1+5+6+3+1+2+0 = 21
- `P[1][3]` = row 0, cols 0–2 = 4; `P[3][1]` = col 0, rows 0–2 = 9; `P[1][1]` = 3
- 21 − 4 − 9 + 3 = **11** ✓
""",
        complexity="Construction **O(R·C)** time and space; each `sumRegion` **O(1)**.",
        pitfalls="""
- Forgetting to add the corner back (inclusion–exclusion).
- Off-by-one between inclusive query bounds and the padded table: use `r2 + 1`, `c2 + 1`.
- `[[0] * (C+1)] * (R+1)` creates R+1 references to the **same** row — build rows in a comprehension.
""",
        follow_up="*Range Sum Query - Immutable* (1-D, LC 303). With updates (*Range Sum Query 2D - Mutable*, LC 308) you need a 2-D Fenwick tree. *Matrix Block Sum* (LC 1314) is a direct application.",
    ),
),
# ---------------------------------------------------------------------------
dict(
    id="first-missing-positive",
    title="First Missing Positive",
    difficulty="Hard",
    pattern="Arrays & Hashing",
    leetcode="https://leetcode.com/problems/first-missing-positive/",
    neetcode="https://neetcode.io/problems/first-missing-positive",
    entry="firstMissingPositive",
    description=r"""
Given an unsorted integer list `nums`, return the **smallest positive integer** (1, 2, 3, …) that does
not occur in it.

You must use **O(n)** time and **O(1)** auxiliary space — so no sorting and no extra set. (You *may*
modify `nums`.)

**Constraints**

- `1 <= len(nums) <= 10^5`
- `-2^31 <= nums[i] <= 2^31 - 1`

**Example 1:** `nums = [1, 2, 0]` → `3`

**Example 2:** `nums = [3, 4, -1, 1]` → `2`

**Example 3:** `nums = [7, 8, 9, 11, 12]` → `1`
""",
    starter='''class Solution:
    def firstMissingPositive(self, nums: List[int]) -> int:
        pass
''',
    solution='''class Solution:
    def firstMissingPositive(self, nums):
        n = len(nums)
        for i in range(n):
            # keep swapping nums[i] into its home slot (value v belongs at index v-1)
            while 1 <= nums[i] <= n and nums[nums[i] - 1] != nums[i]:
                j = nums[i] - 1
                nums[i], nums[j] = nums[j], nums[i]
        for i in range(n):
            if nums[i] != i + 1:
                return i + 1
        return n + 1
''',
    tests=[
        [[1, 2, 0]],
        [[3, 4, -1, 1]],
        [[7, 8, 9, 11, 12]],
        [[1]],
        [[2]],
        [[-1]],
        [[1, 1]],
        [[2, 2, 2, 1]],
        [[1, 2, 3, 4, 5]],
        [[0, -2147483648, 2147483647]],
        [[2, 3, 4, 5, 1, 7]],
        [_fmp_perm],
        [_fmp_full],
    ],
    wrong_solutions=[
        '''class Solution:
    def firstMissingPositive(self, nums):
        n = len(nums)
        for i in range(n):
            # 'if' instead of 'while': the value swapped in is never placed
            if 1 <= nums[i] <= n and nums[nums[i] - 1] != nums[i]:
                j = nums[i] - 1
                nums[i], nums[j] = nums[j], nums[i]
        for i in range(n):
            if nums[i] != i + 1:
                return i + 1
        return n + 1
''',
        '''class Solution:
    def firstMissingPositive(self, nums):
        pos = [x for x in nums if x > 0]
        return min(pos) - 1 if pos and min(pos) > 1 else max(pos, default=0) + 1
''',
    ],
    guide=dict(
        prereqs="*Contains Duplicate* (sets) and cyclic/in-place index tricks (see *Prefix sums, counting and bucket tricks*).",
        intuition="""
The answer is always in `1..n+1` (n slots can hold at most the values 1..n). So use the array **itself**
as the hash set: put value `v` at index `v - 1`. After that, the first index `i` whose slot doesn't hold
`i + 1` reveals the missing number.
""",
        hints=[
            "With a set it's easy: try 1, 2, 3, … What's the largest possible answer for an array of length n?",
            "Values ≤ 0 or > n can never affect the answer. Can the array itself record which of 1..n are present?",
            "Cyclic sort: while nums[i] is in 1..n and not already at index nums[i]-1, swap it home. Then scan.",
        ],
        brute_force="""
- Try `1, 2, 3, …` and scan the array for each: **O(n²)**.
- Sort and scan: O(n log n).
- Put everything in a set and try 1, 2, …: O(n) time but **O(n) space** — fine in practice, violates the follow-up.
""",
        approach="""
**Phase 1 — place.** For each `i`, *while* `1 <= nums[i] <= n` and `nums[nums[i]-1] != nums[i]`, swap
`nums[i]` with `nums[nums[i]-1]`. Each swap puts one value permanently at home, so there are at most n
swaps in total → O(n) despite the nested loop. The `!=` check also stops infinite loops on duplicates.

**Phase 2 — scan.** Return the first `i + 1` with `nums[i] != i + 1`, or `n + 1` if all are home.

**Dry run** `[3, 4, -1, 1]` (n = 4):

- i=0: 3 → swap with idx 2 → `[-1, 4, 3, 1]`; -1 out of range → stop
- i=1: 4 → swap with idx 3 → `[-1, 1, 3, 4]`; 1 → swap with idx 0 → `[1, -1, 3, 4]`; -1 → stop
- i=2: 3 is home. i=3: 4 is home.
- Scan: idx 1 holds -1 ≠ 2 → **2**.

(Alternative O(1)-space trick: replace non-positives by n+1, then mark presence of `v` by making
`nums[v-1]` negative.)
""",
        complexity="Time **O(n)** — at most n successful swaps overall plus two linear scans. Space **O(1)**.",
        pitfalls="""
- Using `if` instead of `while`: the value swapped *into* position i never gets placed.
- Without the `nums[nums[i]-1] != nums[i]` guard, duplicates (like `[1, 1]`) loop forever.
- In Python, `nums[i], nums[nums[i]-1] = ...` evaluates the left targets in order and changes `nums[i]` first — compute `j` before swapping.
""",
        follow_up="*Missing Number* (LC 268), *Find All Numbers Disappeared in an Array* (LC 448) and *Find the Duplicate Number* (LC 287) all use 'index as hash key' ideas.",
    ),
),
]
