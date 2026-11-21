import random

_r = random.Random(42)

_half = "".join(_r.choice("abcXYZ09 ,.!:") for _ in range(25000))
_pal_big = _half + "q" + _half[::-1]
_pal_big_bad = _half + "q" + _half[::-1][:-40] + "w" + _half[::-1][-39:]

_m1 = sorted(_r.randint(-999, 999) for _ in range(6000))
_m2 = sorted(_r.randint(-999, 999) for _ in range(6000))

_mz_big = [_r.choice([0, 0, 1, 2, 3, -4, 5]) for _ in range(20000)]

_rd_big = sorted(_r.randint(-100, 100) for _ in range(30000))

_ts2_big = sorted(_r.sample(range(-10**6, 10**6, 2), 20000))      # all even
_ts2_big[0] = -10**6 - 1                                            # the only odd value
_ts2_big.sort()
_ts2_target = _ts2_big[0] + _ts2_big[-1] + 0                        # first + last
_ts2_big2 = list(range(1, 20001))

_rot_big = [_r.randint(-10**4, 10**4) for _ in range(20000)]

_3sum_big = [_r.randint(-10**5, 10**5) for _ in range(1000)]
_3sum_big[:6] = [5, -2, -3, 7, -7, 0]

_4sum_big = [_r.randint(-50, 50) for _ in range(150)]

_cw_big = [_r.randint(0, 10**4) for _ in range(20000)]
_tr_big = [_r.randint(0, 1000) for _ in range(20000)]


PROBLEMS = [
# ---------------------------------------------------------------------------
dict(
    id="valid-palindrome",
    title="Valid Palindrome",
    difficulty="Easy",
    pattern="Two Pointers",
    leetcode="https://leetcode.com/problems/valid-palindrome/",
    neetcode="https://neetcode.io/problems/is-palindrome",
    entry="isPalindrome",
    description=r"""
A phrase counts as a **palindrome** if, after throwing away every character that is not a letter or a
digit and ignoring upper/lower case, it reads the same forwards and backwards.

Given a string `s`, return `True` if it is a palindrome under that rule. An input with no letters or digits
at all counts as a palindrome.

**Constraints**

- `1 <= len(s) <= 2 * 10^5` (printable ASCII)

**Example 1:** `s = "A man, a plan, a canal: Panama"` → `True` (`"amanaplanacanalpanama"`)

**Example 2:** `s = "race a car"` → `False`

**Example 3:** `s = " "` → `True`

**Follow-up:** do it with O(1) extra space (no cleaned copy).
""",
    starter='''class Solution:
    def isPalindrome(self, s: str) -> bool:
        pass
''',
    solution='''class Solution:
    def isPalindrome(self, s):
        l, r = 0, len(s) - 1
        while l < r:
            while l < r and not s[l].isalnum():
                l += 1
            while l < r and not s[r].isalnum():
                r -= 1
            if s[l].lower() != s[r].lower():
                return False
            l += 1
            r -= 1
        return True
''',
    tests=[
        ["A man, a plan, a canal: Panama"],
        ["race a car"],
        [" "],
        ["a"],
        [".,"],
        ["0P"],
        ["ab_a"],
        ["Was it a car or a cat I saw?"],
        ["No 'x' in Nixon"],
        ["1b1"],
        ["abcba!!!"],
        [_pal_big],
        [_pal_big_bad],
    ],
    wrong_solutions=[
        '''class Solution:
    def isPalindrome(self, s):
        return s == s[::-1]                         # forgets to clean the string
''',
        '''class Solution:
    def isPalindrome(self, s):
        t = [c for c in s if c.isalpha()]           # drops digits and keeps case
        return t == t[::-1]
''',
    ],
    guide=dict(
        prereqs="String methods `isalnum()` / `lower()`; the converging two-pointer template (see *The Two Pointers pattern*).",
        intuition="A palindrome mirrors around its centre, so compare the outermost *relevant* characters and walk inward. Skip junk characters on either side as you go.",
        hints=[
            "Easiest version: build a cleaned lowercase string and compare it with its reverse.",
            "To avoid the copy, put one index at each end.",
            "Advance each pointer past non-alphanumerics, compare lowercase characters, then move both inward.",
        ],
        brute_force="`t = ''.join(c.lower() for c in s if c.isalnum()); return t == t[::-1]` — O(n) time, **O(n) extra space**. Perfectly good; the two-pointer version just removes the copy.",
        approach="""
1. `l = 0`, `r = len(s) - 1`.
2. While `l < r`: skip non-alphanumerics from the left, then from the right (both guarded by `l < r`).
3. If `s[l].lower() != s[r].lower()` → `False`. Otherwise `l += 1`, `r -= 1`.
4. Pointers met → `True`.

**Dry run** `"race a car"`: r/r ✓, a/a ✓, c/c ✓, e/(skip space) a ✗ → **False**.

`"0P"`: `'0'` vs `'p'` → **False** (digits matter!).
""",
        complexity="Time **O(n)** — each index is visited at most once by one of the pointers. Space **O(1)**.",
        pitfalls="""
- Digits count: `"0P"` is not a palindrome. `isalpha()` would wrongly drop them.
- Guard the inner skip loops with `l < r` so a string of only punctuation doesn't run off the end.
- Compare case-insensitively.
""",
        follow_up="*Valid Palindrome II* (LC 680): allowed to delete one character — on the first mismatch try skipping either side.",
    ),
),
# ---------------------------------------------------------------------------
dict(
    id="merge-sorted-array",
    title="Merge Sorted Array",
    difficulty="Easy",
    pattern="Two Pointers",
    leetcode="https://leetcode.com/problems/merge-sorted-array/",
    neetcode="https://neetcode.io/problems/merge-sorted-array",
    entry="merge",
    inplace_arg=0,
    description=r"""
You get two lists sorted in non-decreasing order: `nums1` and `nums2`, plus their logical sizes `m` and
`n`. `nums1` has length `m + n`: its first `m` slots hold real values and its last `n` slots are
placeholder zeros reserved for you. Merge `nums2` into `nums1` **in place** so that `nums1` ends up as
one sorted list of all `m + n` values. Return nothing — the judge reads `nums1` afterwards.

**Constraints**

- `nums1.length == m + n`, `nums2.length == n`
- `0 <= m, n <= 200` on LeetCode (our big test uses 6000 each)
- `-10^9 <= values <= 10^9`

**Example 1:** `nums1 = [1,2,3,0,0,0], m = 3, nums2 = [2,5,6], n = 3` → `nums1 = [1,2,2,3,5,6]`

**Example 2:** `nums1 = [0], m = 0, nums2 = [1], n = 1` → `[1]`

**Follow-up:** O(m + n) time and O(1) extra space.
""",
    starter='''class Solution:
    def merge(self, nums1: List[int], m: int, nums2: List[int], n: int) -> None:
        """
        Do not return anything, modify nums1 in-place instead.
        """
        pass
''',
    solution='''class Solution:
    def merge(self, nums1, m, nums2, n):
        i, j, w = m - 1, n - 1, m + n - 1      # fill from the back
        while j >= 0:
            if i >= 0 and nums1[i] > nums2[j]:
                nums1[w] = nums1[i]
                i -= 1
            else:
                nums1[w] = nums2[j]
                j -= 1
            w -= 1
''',
    tests=[
        [[1, 2, 3, 0, 0, 0], 3, [2, 5, 6], 3],
        [[0], 0, [1], 1],
        [[1], 1, [], 0],
        [[4, 5, 6, 0, 0, 0], 3, [1, 2, 3], 3],
        [[1, 2, 3, 0, 0, 0], 3, [4, 5, 6], 3],
        [[2, 0], 1, [1], 1],
        [[-1, 0, 0, 3, 3, 3, 0, 0, 0], 6, [1, 2, 2], 3],
        [[0, 0, 0], 0, [-5, -5, 7], 3],
        [[1, 1, 0, 0], 2, [1, 1], 2],
        [[-10**9, 10**9, 0], 2, [0], 1],
        [_m1 + [0] * len(_m2), len(_m1), _m2, len(_m2)],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def merge(self, nums1, m, nums2, n):
        nums1[m:] = nums2                      # appends but never sorts
''',
        '''class Solution:
    def merge(self, nums1, m, nums2, n):
        i, j, w = m - 1, n - 1, m + n - 1
        while i >= 0 and j >= 0:               # stops when nums1 runs out, leaving nums2 leftovers
            if nums1[i] > nums2[j]:
                nums1[w] = nums1[i]
                i -= 1
            else:
                nums1[w] = nums2[j]
                j -= 1
            w -= 1
''',
    ],
    guide=dict(
        prereqs="Merging two sorted lists (the merge step of merge sort); in-place modification.",
        intuition="The free space is at the **end** of `nums1`, so merge from the back: repeatedly place the larger of the two current tails into the last free slot. You never overwrite a value you still need.",
        hints=[
            "Merging from the front would overwrite unread values of nums1. Where is the free space?",
            "Use three indices: last real value of nums1, last value of nums2, and the write position.",
            "Loop while nums2 still has values; leftovers of nums1 are already in place.",
        ],
        brute_force="Copy `nums2` into the tail and call `nums1.sort()` → O((m+n) log(m+n)). Or merge into a new list and copy back → O(m+n) time but O(m+n) extra space.",
        approach="""
1. `i = m-1`, `j = n-1`, `w = m+n-1`.
2. While `j >= 0`: if `i >= 0` and `nums1[i] > nums2[j]`, write `nums1[i]` at `w` and `i -= 1`; else write `nums2[j]` and `j -= 1`. Then `w -= 1`.

**Dry run** `nums1 = [1,2,3,0,0,0]`, `nums2 = [2,5,6]`:

| i | j | w | compare | nums1 |
|---|---|---|---|---|
| 2 | 2 | 5 | 3 vs 6 → 6 | [1,2,3,0,0,6] |
| 2 | 1 | 4 | 3 vs 5 → 5 | [1,2,3,0,5,6] |
| 2 | 0 | 3 | 3 vs 2 → 3 | [1,2,3,3,5,6] |
| 1 | 0 | 2 | 2 vs 2 → take nums2 | [1,2,2,3,5,6] |

j < 0 → done.
""",
        complexity="Time **O(m + n)**, space **O(1)**.",
        pitfalls="- Looping `while i >= 0 and j >= 0` forgets nums2 leftovers (e.g. `[4,5,6,0,0,0]` + `[1,2,3]`).\n- No need to copy nums1 leftovers — they are already in place.\n- `m = 0` and `n = 0` edge cases.",
        follow_up="*Merge Two Sorted Lists* (linked lists), *Merge k Sorted Lists* (heap), *Squares of a Sorted Array* (fill from the back too).",
    ),
),
# ---------------------------------------------------------------------------
dict(
    id="move-zeroes",
    title="Move Zeroes",
    difficulty="Easy",
    pattern="Two Pointers",
    leetcode="https://leetcode.com/problems/move-zeroes/",
    neetcode="https://neetcode.io/problems/move-zeroes",
    entry="moveZeroes",
    inplace_arg=0,
    description=r"""
Rearrange the integer list `nums` **in place** so every `0` is moved to the end, while the non-zero values
keep their **original relative order**. Don't build a new list; return nothing.

**Constraints**

- `1 <= len(nums) <= 10^4`
- `-2^31 <= nums[i] <= 2^31 - 1`

**Example 1:** `nums = [0, 1, 0, 3, 12]` → `[1, 3, 12, 0, 0]`

**Example 2:** `nums = [0]` → `[0]`

**Follow-up:** minimise the total number of writes.
""",
    starter='''class Solution:
    def moveZeroes(self, nums: List[int]) -> None:
        """
        Do not return anything, modify nums in-place instead.
        """
        pass
''',
    solution='''class Solution:
    def moveZeroes(self, nums):
        w = 0                                  # next slot for a non-zero
        for r in range(len(nums)):
            if nums[r] != 0:
                nums[w], nums[r] = nums[r], nums[w]
                w += 1
''',
    tests=[
        [[0, 1, 0, 3, 12]],
        [[0]],
        [[1]],
        [[1, 2, 3]],
        [[0, 0, 0, 1]],
        [[1, 0, 0, 0]],
        [[4, 2, 4, 0, 0, 3, 0, 5, 1, 0]],
        [[-1, 0, -2, 0, 0, -3]],
        [[0, 0, 1, 0, 2, 0, 3]],
        [[2, 1]],
        [_mz_big],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def moveZeroes(self, nums):
        end = len(nums) - 1
        i = 0
        while i < end:                          # swaps zeros with the END: breaks relative order
            if nums[i] == 0:
                nums[i], nums[end] = nums[end], nums[i]
                end -= 1
            else:
                i += 1
''',
        '''class Solution:
    def moveZeroes(self, nums):
        for i in range(len(nums) - 1):          # one bubble pass is not enough
            if nums[i] == 0:
                nums[i], nums[i + 1] = nums[i + 1], nums[i]
''',
    ],
    guide=dict(
        prereqs="Reader/writer (same-direction) two pointers — see *The Two Pointers pattern*.",
        intuition="Use a **writer** index `w` for where the next non-zero belongs. A reader scans everything; each non-zero is swapped down to `w`. Zeros naturally pile up behind the writer.",
        hints=[
            "Think of building the 'compacted' list of non-zeros at the front of the same array.",
            "Keep a write index that only advances when you see a non-zero.",
            "Swap nums[r] with nums[w] whenever nums[r] != 0 — the zeros end up at the back automatically.",
        ],
        brute_force="Repeatedly bubble zeros rightwards — O(n²). Or copy non-zeros to a new list and pad zeros — O(n) time, O(n) space (violates 'in place').",
        approach="""
Invariant: `nums[:w]` holds the non-zeros seen so far in order; `nums[w:r]` are all zeros.

For each `r`: if `nums[r] != 0`, swap `nums[w]`, `nums[r]`, then `w += 1`.

**Dry run** `[0, 1, 0, 3, 12]`:

| r | nums[r] | w before | nums after |
|---|---|---|---|
| 0 | 0 | 0 | [0,1,0,3,12] |
| 1 | 1 | 0 | [1,0,0,3,12] (w=1) |
| 2 | 0 | 1 | unchanged |
| 3 | 3 | 1 | [1,3,0,0,12] (w=2) |
| 4 | 12 | 2 | [1,3,12,0,0] (w=3) |
""",
        complexity="Time **O(n)**, space **O(1)**.",
        pitfalls="- Swapping zeros to the end breaks the order of non-zeros.\n- Two-pass variant (copy non-zeros forward, then fill zeros) also works; don't forget the fill pass.",
        follow_up="Same template: *Remove Element* (LC 27), *Remove Duplicates from Sorted Array*, partition steps of quicksort.",
    ),
),
# ---------------------------------------------------------------------------
dict(
    id="remove-duplicates-from-sorted-array",
    title="Remove Duplicates from Sorted Array",
    difficulty="Easy",
    pattern="Two Pointers",
    leetcode="https://leetcode.com/problems/remove-duplicates-from-sorted-array/",
    neetcode="https://neetcode.io/problems/remove-duplicates-from-sorted-array",
    entry="removeDuplicates",
    inplace_arg=0,
    checker='''def check(args, got, expected):
    original = args[0]
    uniq = sorted(set(original))
    k = len(uniq)
    return isinstance(got, list) and len(got) == len(original) and got[:k] == uniq
''',
    description=r"""
`nums` is sorted in non-decreasing order. Remove the repeated values **in place** so that each distinct
value appears once, keeping the original order, and return `k`, the number of distinct values.

After your method returns, the first `k` slots of `nums` must hold the distinct values in sorted order.
Whatever is left in slots `k` and beyond does not matter. (Our judge checks the contents of `nums`; you
should still return `k` exactly as LeetCode expects.)

**Constraints**

- `1 <= len(nums) <= 3 * 10^4`
- `-100 <= nums[i] <= 100`, sorted non-decreasing

**Example 1:** `nums = [1, 1, 2]` → return `2`, `nums` starts with `[1, 2, ...]`

**Example 2:** `nums = [0,0,1,1,1,2,2,3,3,4]` → return `5`, `nums` starts with `[0, 1, 2, 3, 4, ...]`
""",
    starter='''class Solution:
    def removeDuplicates(self, nums: List[int]) -> int:
        pass
''',
    solution='''class Solution:
    def removeDuplicates(self, nums):
        w = 1                                  # nums[:w] is the deduplicated prefix
        for r in range(1, len(nums)):
            if nums[r] != nums[w - 1]:
                nums[w] = nums[r]
                w += 1
        return w
''',
    tests=[
        [[1, 1, 2]],
        [[0, 0, 1, 1, 1, 2, 2, 3, 3, 4]],
        [[1]],
        [[1, 2, 3]],
        [[5, 5, 5, 5]],
        [[-100, -100, 0, 100, 100]],
        [[1, 1, 1, 2]],
        [[1, 2, 2, 2]],
        [[-3, -1, -1, 0, 0, 0, 7]],
        [list(range(-100, 101))],
        [_rd_big],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def removeDuplicates(self, nums):
        return len(set(nums))                  # right count, array untouched
''',
        '''class Solution:
    def removeDuplicates(self, nums):
        w = 1
        for r in range(1, len(nums)):
            if nums[r] != nums[r - 1]:
                nums[w] = nums[r]
                w += 1
            # compares with the ORIGINAL neighbour - fine - but forgets the first element:
        nums[0] = nums[-1]
        return w
''',
    ],
    guide=dict(
        prereqs="Reader/writer two pointers; *Move Zeroes*.",
        intuition="Because equal values are adjacent in a sorted list, a value is new exactly when it differs from the last value you **kept**. Keep a writer index for the deduplicated prefix and copy each new value to it.",
        hints=[
            "In a sorted array, where are the copies of a value?",
            "Keep `w` = length of the deduplicated prefix. When is nums[r] worth keeping?",
            "Copy nums[r] to nums[w] whenever nums[r] != nums[w-1]; return w.",
        ],
        brute_force="`nums[:] = sorted(set(nums))` — O(n log n), extra space. Or `del` duplicates one by one — each deletion shifts the tail, O(n²).",
        approach="""
1. `w = 1` (the first element is always kept).
2. For `r` in `1..n-1`: if `nums[r] != nums[w-1]`, set `nums[w] = nums[r]`, `w += 1`.
3. Return `w`.

**Dry run** `[0,0,1,1,1,2,2,3,3,4]`:

- r=1: 0 == kept 0 → skip
- r=2: 1 → write at 1 → `[0,1,…]`, w=2
- r=3,4: 1 → skip
- r=5: 2 → write at 2, w=3; r=6 skip
- r=7: 3 → write at 3, w=4; r=8 skip
- r=9: 4 → write at 4, w=5

Return **5**, prefix `[0,1,2,3,4]`.
""",
        complexity="Time **O(n)**, space **O(1)**.",
        pitfalls="- Returning the count without compacting the array fails the judge.\n- Don't call `del nums[i]` inside a loop over indices — it shifts elements under you and is O(n) each.",
        follow_up="*Remove Duplicates from Sorted Array II* (LC 80): allow each value at most twice → compare with `nums[w-2]` instead.",
    ),
),
# ---------------------------------------------------------------------------
dict(
    id="two-sum-ii-input-array-is-sorted",
    title="Two Sum II - Input Array Is Sorted",
    difficulty="Medium",
    pattern="Two Pointers",
    leetcode="https://leetcode.com/problems/two-sum-ii-input-array-is-sorted/",
    neetcode="https://neetcode.io/problems/two-integer-sum-ii",
    entry="twoSum",
    description=r"""
`numbers` is sorted in non-decreasing order. Find the two **different positions** whose values sum to
`target` and return them **1-indexed** as `[index1, index2]` with `index1 < index2`. Exactly one
solution exists. You must use only **O(1)** extra space.

**Constraints**

- `2 <= len(numbers) <= 3 * 10^4`
- `-1000 <= numbers[i] <= 1000` on LeetCode (our big test uses wider values)
- exactly one solution

**Example 1:** `numbers = [2, 7, 11, 15], target = 9` → `[1, 2]`

**Example 2:** `numbers = [2, 3, 4], target = 6` → `[1, 3]`

**Example 3:** `numbers = [-1, 0], target = -1` → `[1, 2]`
""",
    starter='''class Solution:
    def twoSum(self, numbers: List[int], target: int) -> List[int]:
        pass
''',
    solution='''class Solution:
    def twoSum(self, numbers, target):
        l, r = 0, len(numbers) - 1
        while l < r:
            s = numbers[l] + numbers[r]
            if s == target:
                return [l + 1, r + 1]
            if s < target:
                l += 1          # need a bigger sum
            else:
                r -= 1          # need a smaller sum
''',
    tests=[
        [[2, 7, 11, 15], 9],
        [[2, 3, 4], 6],
        [[-1, 0], -1],
        [[1, 2], 3],
        [[0, 0, 3, 4], 0],
        [[1, 3, 3, 9], 6],
        [[-5, -3, -1, 0, 2], -8],
        [[1, 2, 3, 4, 4, 9, 56, 90], 8],
        [[5, 25, 75], 100],
        [[-1000, 1, 2, 1000], 0],
        [_ts2_big, _ts2_target],
        [_ts2_big2, 39999],
    ],
    wrong_solutions=[
        '''class Solution:
    def twoSum(self, numbers, target):
        l, r = 0, len(numbers) - 1
        while l < r:
            s = numbers[l] + numbers[r]
            if s == target:
                return [l, r]                  # forgot to convert to 1-indexed
            if s < target:
                l += 1
            else:
                r -= 1
''',
        '''class Solution:
    def twoSum(self, numbers, target):
        l, r = 0, len(numbers) - 1
        while l < r:
            s = numbers[l] + numbers[r]
            if s == target:
                return [l + 1, r + 1]
            if s < target:
                r -= 1                         # moves the wrong pointer
            else:
                l += 1
        return [1, 2]
''',
    ],
    guide=dict(
        prereqs="*Two Sum*; the converging pointers template and why it's correct (see *k-Sum, greedy pointer moves and proofs*).",
        intuition="""
Start with the smallest and largest values. If their sum is too small, the smallest value can't be part of
the answer with *anything* (it's already paired with the biggest) → drop it. If too big, the largest can't
be used → drop it. Each step discards one candidate, so it takes at most n steps.
""",
        hints=[
            "The hash-map Two Sum works, but uses O(n) space. What does sortedness give you?",
            "Put pointers at both ends and look at the sum.",
            "Sum too small → move left pointer right; too big → move right pointer left.",
        ],
        brute_force="All pairs: O(n²). For each element, binary-search the complement: O(n log n), O(1) space. Hash map: O(n) time, O(n) space.",
        approach="""
1. `l = 0`, `r = n - 1`.
2. While `l < r`: `s = numbers[l] + numbers[r]`.
   - `s == target` → return `[l+1, r+1]`.
   - `s < target` → `l += 1`. `s > target` → `r -= 1`.

**Dry run** `[2, 3, 4]`, target 6: (2,4)=6 → **[1, 3]**.
`[2, 7, 11, 15]`, target 9: 2+15=17 → r=2; 2+11=13 → r=1; 2+7=9 → **[1, 2]**.
""",
        complexity="Time **O(n)**, space **O(1)**.",
        pitfalls="- Answer is **1-indexed**.\n- Moving the wrong pointer can skip the answer.\n- `l < r` (strict) — the same element can't be used twice.",
        follow_up="Becomes the inner loop of *3Sum* and *4Sum*. *Two Sum IV* (BST) and *Two Sum Less Than K* are variants.",
    ),
),
# ---------------------------------------------------------------------------
dict(
    id="rotate-array",
    title="Rotate Array",
    difficulty="Medium",
    pattern="Two Pointers",
    leetcode="https://leetcode.com/problems/rotate-array/",
    neetcode="https://neetcode.io/problems/rotate-array",
    entry="rotate",
    inplace_arg=0,
    description=r"""
Shift every element of `nums` to the **right by `k` positions**, wrapping around: an element that falls off
the end re-enters at the front. Modify `nums` in place and return nothing. `k` can be larger than the
length of the list.

**Constraints**

- `1 <= len(nums) <= 10^5`
- `-2^31 <= nums[i] <= 2^31 - 1`
- `0 <= k <= 10^5`

**Example 1:** `nums = [1,2,3,4,5,6,7], k = 3` → `[5,6,7,1,2,3,4]`

**Example 2:** `nums = [-1,-100,3,99], k = 2` → `[3,99,-1,-100]`

**Follow-up:** O(1) extra space.
""",
    starter='''class Solution:
    def rotate(self, nums: List[int], k: int) -> None:
        """
        Do not return anything, modify nums in-place instead.
        """
        pass
''',
    solution='''class Solution:
    def rotate(self, nums, k):
        n = len(nums)
        k %= n

        def reverse(l, r):
            while l < r:
                nums[l], nums[r] = nums[r], nums[l]
                l += 1
                r -= 1

        reverse(0, n - 1)        # whole array
        reverse(0, k - 1)        # first k
        reverse(k, n - 1)        # the rest
''',
    tests=[
        [[1, 2, 3, 4, 5, 6, 7], 3],
        [[-1, -100, 3, 99], 2],
        [[1], 0],
        [[1], 5],
        [[1, 2], 3],
        [[1, 2, 3], 3],
        [[1, 2, 3, 4, 5, 6], 0],
        [[1, 2, 3, 4, 5, 6], 4],
        [[1, 2, 3, 4, 5, 6], 13],
        [[9, 8, 7, 6, 5], 1],
        [_rot_big, 12345],
        [_rot_big[:4000], 100000],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def rotate(self, nums, k):
        nums[:] = nums[-k:] + nums[:-k]          # forgets k %= n (and breaks for k > n)
''',
        '''class Solution:
    def rotate(self, nums, k):
        k %= len(nums)
        nums[:] = nums[k:] + nums[:k]            # rotates LEFT instead of right
''',
    ],
    guide=dict(
        prereqs="Reversing a range with two pointers; modular arithmetic.",
        intuition="""
Rotating right by `k` moves the **last k** elements to the front. Reversing the whole array puts them at
the front but backwards; reversing each of the two blocks again fixes their internal order. Three
reversals, each a simple converging two-pointer swap loop.
""",
        hints=[
            "Rotating by n is the identity. Simplify k first.",
            "Slicing `nums[-k:] + nums[:-k]` works with O(n) extra space. For O(1), think about reversals.",
            "Reverse all, then reverse the first k, then reverse the remaining n-k.",
        ],
        brute_force="Rotate by one step, `k` times: **O(n·k)** — with n = 2·10⁴ and k = 12345 that's 2.5·10⁸ moves. A copy `nums[:] = nums[-k:] + nums[:-k]` is O(n) time but O(n) extra space.",
        approach="""
1. `k %= n`.
2. `reverse(0, n-1)`, `reverse(0, k-1)`, `reverse(k, n-1)`.

**Dry run** `[1,2,3,4,5,6,7]`, k=3:

- reverse all → `[7,6,5,4,3,2,1]`
- reverse first 3 → `[5,6,7,4,3,2,1]`
- reverse last 4 → `[5,6,7,1,2,3,4]` ✓
""",
        complexity="Time **O(n)** (each element swapped about twice). Space **O(1)**.",
        pitfalls="""
- Without `k %= n`, `k > n` breaks slicing/reversal ranges.
- `k = 0` after the modulo: `reverse(0, -1)` must be a no-op — the `l < r` check handles it.
- `nums = ...` rebinds a local; write `nums[:] = ...` when using slices.
""",
        follow_up="Cyclic-replacement method (follow each element to its destination, gcd(n, k) cycles). *Rotate List* (linked list), *Rotate Image* (matrix).",
    ),
),
# ---------------------------------------------------------------------------
dict(
    id="3sum",
    title="3Sum",
    difficulty="Medium",
    pattern="Two Pointers",
    leetcode="https://leetcode.com/problems/3sum/",
    neetcode="https://neetcode.io/problems/three-integer-sum",
    entry="threeSum",
    compare="unordered_nested",
    description=r"""
Given an integer list `nums`, find **every distinct triple of values** `[a, b, c]` taken from three
different positions such that `a + b + c == 0`. Two triples are the same if they contain the same values
(in any order); report each such triple only once. The order of triples and the order inside each triple
don't matter.

**Constraints**

- `3 <= len(nums) <= 3000`
- `-10^5 <= nums[i] <= 10^5`

**Example 1:** `nums = [-1, 0, 1, 2, -1, -4]` → `[[-1, -1, 2], [-1, 0, 1]]`

**Example 2:** `nums = [0, 1, 1]` → `[]`

**Example 3:** `nums = [0, 0, 0]` → `[[0, 0, 0]]`
""",
    starter='''class Solution:
    def threeSum(self, nums: List[int]) -> List[List[int]]:
        pass
''',
    solution='''class Solution:
    def threeSum(self, nums):
        nums = sorted(nums)
        n, res = len(nums), []
        for i in range(n - 2):
            a = nums[i]
            if a > 0:
                break                          # smallest value positive -> no more zeros
            if i > 0 and a == nums[i - 1]:
                continue                       # same first value -> same triples
            l, r = i + 1, n - 1
            while l < r:
                s = a + nums[l] + nums[r]
                if s < 0:
                    l += 1
                elif s > 0:
                    r -= 1
                else:
                    res.append([a, nums[l], nums[r]])
                    l += 1
                    r -= 1
                    while l < r and nums[l] == nums[l - 1]:
                        l += 1
        return res
''',
    tests=[
        [[-1, 0, 1, 2, -1, -4]],
        [[0, 1, 1]],
        [[0, 0, 0]],
        [[0, 0, 0, 0, 0]],
        [[-2, 0, 1, 1, 2]],
        [[1, 2, -2, -1]],
        [[-4, -2, -2, -2, 0, 1, 2, 2, 2, 3, 3, 4, 4, 6, 6]],
        [[3, 0, -2, -1, 1, 2]],
        [[-1, 0, 1, 0]],
        [[100000, -100000, 0, -50000, 50000]],
        [[1, 1, -2]],
        [_3sum_big],
        [[0] * 3000],
    ],
    wrong_solutions=[
        '''class Solution:
    def threeSum(self, nums):
        nums = sorted(nums)
        n, res = len(nums), []
        for i in range(n - 2):                # no duplicate skipping at all
            l, r = i + 1, n - 1
            while l < r:
                s = nums[i] + nums[l] + nums[r]
                if s < 0:
                    l += 1
                elif s > 0:
                    r -= 1
                else:
                    res.append([nums[i], nums[l], nums[r]])
                    l += 1
                    r -= 1
                    while l < r and nums[l] == nums[l - 1]:
                        l += 1
        return res
''',
        '''class Solution:
    def threeSum(self, nums):
        nums = sorted(nums)
        n, res = len(nums), []
        for i in range(n - 2):
            if i > 0 and nums[i] == nums[i - 1]:
                continue
            l, r = i + 1, n - 1
            while l < r:
                s = nums[i] + nums[l] + nums[r]
                if s < 0:
                    l += 1
                elif s > 0:
                    r -= 1
                else:
                    res.append([nums[i], nums[l], nums[r]])
                    break                      # stops after the first match for this i
        return res
''',
    ],
    guide=dict(
        prereqs="*Two Sum II* (converging pointers on a sorted array); duplicate-skipping (see *k-Sum, greedy pointer moves and proofs*).",
        intuition="""
Sort the array. Fix the first value `a = nums[i]`; now you need two values after it summing to `-a` —
that's *Two Sum II* on the suffix, solved with two pointers in O(n). Sorting also makes duplicates
adjacent, so skipping repeated values for each position removes duplicate triples without a set.
""",
        hints=[
            "Triple loop is O(n³). If you fix one number, what problem remains?",
            "Sort first. The remaining pair-sum on a sorted suffix is Two Sum II.",
            "Skip i when nums[i] == nums[i-1]; after a hit, move l past equal values. Break once nums[i] > 0.",
        ],
        brute_force="""
Three nested loops and a set of sorted tuples to dedupe: **O(n³)**. With n = 1000 that's ~1.7·10⁸
iterations. Fix-one + hash set for the pair: O(n²) time but dedup is awkward.
""",
        approach="""
1. Sort.
2. For each `i` (stop when `nums[i] > 0`; skip if equal to `nums[i-1]`):
   - `l = i+1`, `r = n-1`. While `l < r`: compute `s`.
   - `s < 0` → `l += 1`; `s > 0` → `r -= 1`;
   - `s == 0` → record, move both, then advance `l` past duplicates.

**Dry run** `[-1,0,1,2,-1,-4]` → sorted `[-4,-1,-1,0,1,2]`:

- i=0 (−4): need 4; best pair 1+2=3 → none.
- i=1 (−1): l=2(−1), r=5(2) → 0 ✓ record `[-1,-1,2]`; l=3(0), r=4(1) → 0 ✓ record `[-1,0,1]`.
- i=2 (−1): same as previous → skip.
- i=3 (0): l=4(1), r=5(2) → 3 > 0 → r=4 → stop.

Result `[[-1,-1,2], [-1,0,1]]`.
""",
        complexity="Time **O(n²)** (sort O(n log n) + n two-pointer scans). Space O(1) besides the output and the sort's copy.",
        pitfalls="""
- Without skipping equal `nums[i]`, triples repeat.
- After a match, move **both** pointers and skip duplicates of `l` — otherwise infinite loop or repeats.
- Don't stop after the first match for a given `i`; there may be several.
""",
        follow_up="*3Sum Closest* (LC 16), *3Sum Smaller*, *4Sum* (one more outer loop), *k-Sum* recursion.",
    ),
),
# ---------------------------------------------------------------------------
dict(
    id="4sum",
    title="4Sum",
    difficulty="Medium",
    pattern="Two Pointers",
    leetcode="https://leetcode.com/problems/4sum/",
    neetcode="https://neetcode.io/problems/4sum",
    entry="fourSum",
    compare="unordered_nested",
    description=r"""
Given an integer list `nums` and an integer `target`, return **every distinct quadruple of values**
`[a, b, c, d]` taken from four different positions with `a + b + c + d == target`. Each multiset of
values must appear only once; ordering of quadruples and inside a quadruple doesn't matter.

**Constraints**

- `1 <= len(nums) <= 200`
- `-10^9 <= nums[i], target <= 10^9`

**Example 1:** `nums = [1, 0, -1, 0, -2, 2], target = 0` → `[[-2,-1,1,2], [-2,0,0,2], [-1,0,0,1]]`

**Example 2:** `nums = [2, 2, 2, 2, 2], target = 8` → `[[2, 2, 2, 2]]`
""",
    starter='''class Solution:
    def fourSum(self, nums: List[int], target: int) -> List[List[int]]:
        pass
''',
    solution='''class Solution:
    def fourSum(self, nums, target):
        nums = sorted(nums)
        n, res = len(nums), []
        for i in range(n - 3):
            if i > 0 and nums[i] == nums[i - 1]:
                continue
            for j in range(i + 1, n - 2):
                if j > i + 1 and nums[j] == nums[j - 1]:
                    continue
                need = target - nums[i] - nums[j]
                l, r = j + 1, n - 1
                while l < r:
                    s = nums[l] + nums[r]
                    if s < need:
                        l += 1
                    elif s > need:
                        r -= 1
                    else:
                        res.append([nums[i], nums[j], nums[l], nums[r]])
                        l += 1
                        r -= 1
                        while l < r and nums[l] == nums[l - 1]:
                            l += 1
        return res
''',
    tests=[
        [[1, 0, -1, 0, -2, 2], 0],
        [[2, 2, 2, 2, 2], 8],
        [[1], 1],
        [[1, 2, 3], 6],
        [[0, 0, 0, 0], 0],
        [[0, 0, 0, 0], 1],
        [[-3, -1, 0, 2, 4, 5], 2],
        [[1000000000, 1000000000, 1000000000, 1000000000], -294967296],
        [[1000000000, 1000000000, 1000000000, 1000000000], 4000000000],
        [[-2, -1, -1, 1, 1, 2, 2], 0],
        [[1, -2, -5, -4, -3, 3, 3, 5], -11],
        [_4sum_big, 7],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def fourSum(self, nums, target):
        nums = sorted(nums)
        n, res = len(nums), []
        for i in range(n - 3):
            for j in range(i + 1, n - 2):      # no duplicate skipping for i and j
                need = target - nums[i] - nums[j]
                l, r = j + 1, n - 1
                while l < r:
                    s = nums[l] + nums[r]
                    if s < need:
                        l += 1
                    elif s > need:
                        r -= 1
                    else:
                        res.append([nums[i], nums[j], nums[l], nums[r]])
                        l += 1
                        r -= 1
                        while l < r and nums[l] == nums[l - 1]:
                            l += 1
        return res
''',
        '''class Solution:
    def fourSum(self, nums, target):
        nums = sorted(nums)
        n, res = len(nums), []
        for i in range(n - 3):
            if i > 0 and nums[i] == nums[i - 1]:
                continue
            for j in range(i + 1, n - 2):
                if j > 0 and nums[j] == nums[j - 1]:   # bug: should be j > i + 1
                    continue
                need = target - nums[i] - nums[j]
                l, r = j + 1, n - 1
                while l < r:
                    s = nums[l] + nums[r]
                    if s < need:
                        l += 1
                    elif s > need:
                        r -= 1
                    else:
                        res.append([nums[i], nums[j], nums[l], nums[r]])
                        l += 1
                        r -= 1
                        while l < r and nums[l] == nums[l - 1]:
                            l += 1
        return res
''',
    ],
    guide=dict(
        prereqs="*3Sum* — this is the same idea with one more fixed index.",
        intuition="Sort; fix the first **two** values with nested loops; the last two come from a converging two-pointer scan. Skip duplicates at every level.",
        hints=[
            "How did 3Sum reduce to Two Sum II? Do the same reduction once more.",
            "Two outer loops (i, j) and two pointers (l, r) → O(n³).",
            "The duplicate check for j is `j > i + 1 and nums[j] == nums[j-1]` — not `j > 0`.",
        ],
        brute_force="Four nested loops with a set of sorted tuples: **O(n⁴)** — for n = 150 that is ~2·10⁷ iterations, several seconds in Python.",
        approach="""
1. Sort.
2. For `i` (skip equal to previous), for `j > i` (skip if `j > i+1` and equal to previous):
   two-pointer search for pairs summing to `target - nums[i] - nums[j]` in `nums[j+1:]`, skipping duplicate `l` after each hit.

**Dry run** `[1,0,-1,0,-2,2]`, target 0 → sorted `[-2,-1,0,0,1,2]`:

- i=−2, j=−1: need 3 → (1,2) ✓ `[-2,-1,1,2]`
- i=−2, j=0: need 2 → (0,2) ✓ `[-2,0,0,2]`
- i=−2, j=0 (second 0): skipped (duplicate j)
- i=−1, j=0: need 1 → (0,1) ✓ `[-1,0,0,1]`
- …no more.
""",
        complexity="Time **O(n³)**, space O(1) besides output/sort. General k-Sum: O(n^(k−1)).",
        pitfalls="""
- `j` duplicate check must be relative to `i + 1`, else `[2,2,2,2,2]` loses `[2,2,2,2]`.
- In languages with 32-bit ints the sum overflows (`10^9 * 4`); Python ints don't, but mention it.
- Remember the case where fewer than 4 numbers exist.
""",
        follow_up="Write a recursive `kSum(nums, target, k)` that bottoms out at Two Sum II. *4Sum II* (LC 454, four separate arrays) is a hashing problem: count pair sums of A+B, look up −(C+D).",
    ),
),
# ---------------------------------------------------------------------------
dict(
    id="container-with-most-water",
    title="Container With Most Water",
    difficulty="Medium",
    pattern="Two Pointers",
    leetcode="https://leetcode.com/problems/container-with-most-water/",
    neetcode="https://neetcode.io/problems/max-water-container",
    entry="maxArea",
    description=r"""
`height[i]` is the height of a vertical wall standing at x-coordinate `i`. Choose **two** walls; together
with the x-axis they form a container whose water level is limited by the **shorter** wall. Its capacity
is `min(height[i], height[j]) * (j - i)`. Return the largest capacity achievable. (Walls in between don't
matter — they don't block anything.)

**Constraints**

- `2 <= len(height) <= 10^5`
- `0 <= height[i] <= 10^4`

**Example 1:** `height = [1,8,6,2,5,4,8,3,7]` → `49` (walls at index 1 and 8: `min(8,7) * 7`)

**Example 2:** `height = [1, 1]` → `1`
""",
    starter='''class Solution:
    def maxArea(self, height: List[int]) -> int:
        pass
''',
    solution='''class Solution:
    def maxArea(self, height):
        l, r = 0, len(height) - 1
        best = 0
        while l < r:
            h = min(height[l], height[r])
            best = max(best, h * (r - l))
            if height[l] < height[r]:
                l += 1          # the shorter wall can't do better with any closer partner
            else:
                r -= 1
        return best
''',
    tests=[
        [[1, 8, 6, 2, 5, 4, 8, 3, 7]],
        [[1, 1]],
        [[4, 3, 2, 1, 4]],
        [[1, 2, 1]],
        [[0, 0]],
        [[1, 2, 4, 3]],
        [[2, 3, 10, 5, 7, 8, 9]],
        [[10000, 1, 10000]],
        [[1, 3, 2, 5, 25, 24, 5]],
        [[6, 1, 1, 1, 1, 1, 1, 6]],
        [_cw_big],
        [list(range(1, 15001))],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def maxArea(self, height):
        l, r = 0, len(height) - 1
        best = 0
        while l < r:
            best = max(best, min(height[l], height[r]) * (r - l))
            if height[l] > height[r]:          # moves the TALLER wall
                l += 1
            else:
                r -= 1
        return best
''',
        '''class Solution:
    def maxArea(self, height):
        best = 0
        for i in range(len(height) - 1):       # only adjacent walls
            best = max(best, min(height[i], height[i + 1]))
        return best
''',
    ],
    guide=dict(
        prereqs="Converging pointers; the 'discard a candidate' proof style (see *k-Sum, greedy pointer moves and proofs*).",
        intuition="""
Start with the widest container. To possibly do better with a narrower one, the limiting (shorter) wall
must be replaced — keeping it, any inner partner gives width smaller **and** height still capped by it.
So always move the pointer at the shorter wall inward.
""",
        hints=[
            "Brute force tries every pair. Which pair has maximum width?",
            "If you shrink the width, what must increase for the area to grow?",
            "Move the pointer at the shorter wall; the shorter wall has already achieved its best possible container.",
        ],
        brute_force="All pairs: **O(n²)**. With 2·10⁴ walls that's 2·10⁸ area computations — far too slow in Python.",
        approach="""
1. `l = 0`, `r = n-1`, `best = 0`.
2. While `l < r`: update `best` with `min(h[l], h[r]) * (r - l)`; move the pointer with the smaller height (either on a tie).

**Why it's safe:** say `h[l] <= h[r]`. Any container `(l, k)` with `k < r` has width `< r - l` and height `<= h[l]`, so it's no better than `(l, r)` which we already measured. Wall `l` is done — discard it.

**Dry run** `[1,8,6,2,5,4,8,3,7]`:

| l | r | area | move |
|---|---|---|---|
| 0 (1) | 8 (7) | 1·8 = 8 | l |
| 1 (8) | 8 (7) | 7·7 = **49** | r |
| 1 (8) | 7 (3) | 3·6 = 18 | r |
| 1 (8) | 6 (8) | 8·5 = 40 | r (tie) |
| 1 | 5 (4) | 4·4 = 16 | r |
| … | … | smaller | … |

Answer **49**.
""",
        complexity="Time **O(n)**, space **O(1)**.",
        pitfalls="- Moving the taller wall can skip the optimum.\n- Area uses the **distance** `r - l`, not the count of walls.\n- Don't confuse with *Trapping Rain Water* (which sums water over all positions).",
        follow_up="*Trapping Rain Water* (sum of water above every bar). *Largest Rectangle in Histogram* (monotonic stack).",
    ),
),
# ---------------------------------------------------------------------------
dict(
    id="trapping-rain-water",
    title="Trapping Rain Water",
    difficulty="Hard",
    pattern="Two Pointers",
    leetcode="https://leetcode.com/problems/trapping-rain-water/",
    neetcode="https://neetcode.io/problems/trapping-rain-water",
    entry="trap",
    description=r"""
`height` describes an elevation map: bar `i` has width 1 and height `height[i]`. After heavy rain, water
settles on top of the bars wherever it is held in by higher bars on **both** sides. Return the total
volume of trapped water (in unit squares).

**Constraints**

- `1 <= len(height) <= 2 * 10^4`
- `0 <= height[i] <= 10^5`

**Example 1:** `height = [0,1,0,2,1,0,1,3,2,1,2,1]` → `6`

**Example 2:** `height = [4,2,0,3,2,5]` → `9`
""",
    starter='''class Solution:
    def trap(self, height: List[int]) -> int:
        pass
''',
    solution='''class Solution:
    def trap(self, height):
        l, r = 0, len(height) - 1
        left_max = right_max = 0
        water = 0
        while l < r:
            if height[l] < height[r]:
                left_max = max(left_max, height[l])
                water += left_max - height[l]      # bounded by left_max (right side is taller)
                l += 1
            else:
                right_max = max(right_max, height[r])
                water += right_max - height[r]
                r -= 1
        return water
''',
    tests=[
        [[0, 1, 0, 2, 1, 0, 1, 3, 2, 1, 2, 1]],
        [[4, 2, 0, 3, 2, 5]],
        [[1]],
        [[2, 0]],
        [[2, 0, 2]],
        [[3, 2, 1]],
        [[1, 2, 3]],
        [[5, 4, 1, 2]],
        [[0, 0, 0]],
        [[5, 0, 0, 0, 0, 5]],
        [[4, 2, 3]],
        [[6, 4, 2, 0, 3, 2, 0, 3, 1, 4, 5, 3, 2, 7, 5, 3, 0, 1, 2, 1, 3, 4, 6, 8, 1, 3]],
        [_tr_big],
    ],
    wrong_solutions=[
        '''class Solution:
    def trap(self, height):
        water, left_max = 0, 0
        for h in height:                          # only looks left
            left_max = max(left_max, h)
            water += left_max - h
        return water
''',
        '''class Solution:
    def trap(self, height):
        n = len(height)
        water = 0
        for i in range(1, n - 1):                 # only the immediate neighbours
            bound = min(height[i - 1], height[i + 1])
            water += max(0, bound - height[i])
        return water
''',
    ],
    guide=dict(
        prereqs="Prefix/suffix maxima (*Replace Elements with Greatest Element on Right*); *Container With Most Water*.",
        intuition="""
Water above bar `i` = `min(max height to the left, max height to the right) − height[i]`. Computing both
maxima with prefix/suffix arrays is O(n) space. The two-pointer trick: whichever side currently has the
**smaller** wall, that side's running max is the true bound (the other side is guaranteed to have
something at least as tall), so you can settle that bar immediately.
""",
        hints=[
            "Write the formula for water above a single bar.",
            "Precompute left_max[i] and right_max[i] in two passes — that's O(n) time, O(n) space.",
            "With pointers at both ends, process the side with the lower height; its running max is the binding limit.",
        ],
        brute_force="""
For each bar, scan left and right for the maxima: **O(n²)**. The prefix/suffix version is O(n) time and
O(n) space:

```python
left = list(itertools.accumulate(height, max))
right = list(itertools.accumulate(reversed(height), max))[::-1]
return sum(min(a, b) - h for a, b, h in zip(left, right, height))
```
""",
        approach="""
1. `l = 0`, `r = n-1`, `left_max = right_max = 0`.
2. While `l < r`:
   - if `height[l] < height[r]`: update `left_max`, add `left_max - height[l]`, `l += 1`.
   - else: update `right_max`, add `right_max - height[r]`, `r -= 1`.

**Why it's safe:** a pointer only moves off a bar that is no taller than the bar under the other
pointer, so the tallest bar visited so far always sits under one of the pointers. If `height[l] < height[r]`,
that tallest bar is at `r`, so the real right-side maximum for `l` is at least `height[r] ≥ left_max`.
Therefore `min(maxLeft, maxRight) = left_max` for bar `l`, and its water is exactly `left_max - height[l]`.
The right side is symmetric.

**Dry run** `[4,2,0,3,2,5]`:

| l | r | side | max | water += | total |
|---|---|---|---|---|---|
| 0(4) | 5(5) | L | 4 | 0 | 0 |
| 1(2) | 5 | L | 4 | 2 | 2 |
| 2(0) | 5 | L | 4 | 4 | 6 |
| 3(3) | 5 | L | 4 | 1 | 7 |
| 4(2) | 5 | L | 4 | 2 | 9 |

l = r → **9**.
""",
        complexity="Time **O(n)**, space **O(1)**.",
        pitfalls="""
- Using only one side's max overcounts water that would spill out the other side.
- Neighbour-only bounds miss water held by distant tall bars.
- Update the running max **before** adding water so the result is never negative.
""",
        follow_up="Monotonic-stack solution (fills water layer by layer). *Trapping Rain Water II* (2-D) needs a min-heap BFS from the border.",
    ),
),
]
