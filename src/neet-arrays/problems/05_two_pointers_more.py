import random

_r = random.Random(77)
_L = "abcdefghijklmnopqrstuvwxyz"


def _lc(slug):
    return f"https://leetcode.com/problems/{slug}/"


def _nc(slug):
    return f"https://neetcode.io/problems/{slug}"


_rev_big = [_r.choice(_L) for _ in range(30001)]

_re_big = [_r.randint(0, 50) for _ in range(30000)]

_half = "".join(_r.choice(_L) for _ in range(25000))
_vp2_pal = _half + _half[::-1]
_vp2_one = _half + "#" + "q" + _half[::-1]              # two extra characters -> not fixable
_vp2_del = _half[:20000] + "z" + _half[20000:] + _half[::-1]   # delete the single 'z' ... if it breaks symmetry

_sq_big = sorted(_r.randint(-10**4, 10**4) for _ in range(12000))

_bs_a = "".join(_r.choice("abc#") for _ in range(50000))
_bs_b = "xy##" + _bs_a
_bs_c = _bs_a + "q"

_3c_big = [_r.randint(-1000, 1000) for _ in range(800)]

_ns_big = [_r.randint(1, 10**6) for _ in range(20000)]
_ns_small = [1] * 5000


PROBLEMS = [
# ---------------------------------------------------------------------------
dict(
    id="reverse-string",
    title="Reverse String",
    difficulty="Easy",
    pattern="Two Pointers",
    leetcode=_lc("reverse-string"),
    neetcode=_nc("reverse-string"),
    entry="reverseString",
    inplace_arg=0,
    description=r"""
A string is given as a list of single characters `s`. Reverse the order of the characters **in place** —
change the list you were given, using only O(1) extra memory — and return nothing. The judge looks at `s`
after your method finishes.

**Constraints**

- `1 <= len(s) <= 10^5`; every item is one printable character

**Example 1:** `s = ["h","e","l","l","o"]` → `["o","l","l","e","h"]`

**Example 2:** `s = ["H","a","n","n","a","h"]` → `["h","a","n","n","a","H"]`
""",
    starter='''class Solution:
    def reverseString(self, s: List[str]) -> None:
        """
        Do not return anything, modify s in-place instead.
        """
        pass
''',
    solution='''class Solution:
    def reverseString(self, s):
        l, r = 0, len(s) - 1
        while l < r:
            s[l], s[r] = s[r], s[l]
            l += 1
            r -= 1
''',
    tests=[
        [["h", "e", "l", "l", "o"]],
        [["H", "a", "n", "n", "a", "h"]],
        [["a"]],
        [["a", "b"]],
        [["a", "b", "c"]],
        [["x", "x", "x"]],
        [["1", "2", "3", "4"]],
        [[" ", "a", " "]],
        [["A", "b", "C", "d", "E", "f", "G"]],
        [list("two pointers")],
        [_rev_big],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def reverseString(self, s):
        s = s[::-1]                       # new list bound to the local name; the caller's list is unchanged
''',
        '''class Solution:
    def reverseString(self, s):
        for i in range(len(s) // 2):
            s[i], s[-i] = s[-i], s[i]     # off by one: the mirror of i is -(i + 1)
''',
    ],
    guide=dict(
        prereqs="List indexing; swapping two values with `a, b = b, a`; the converging-pointers shape from *The Two Pointers pattern*.",
        intuition="Reversing means the first and last items trade places, then the second and second-to-last, and so on toward the middle. Two indices walking inward do exactly those trades.",
        hints=[
            "Which element must end up where the first one is?",
            "Put one index at each end and swap what they point to.",
            "Move both inward; stop when they meet or cross (`l < r`).",
        ],
        brute_force="Build a reversed copy (`s[::-1]`) and copy it back with `s[:] = ...` — O(n) time but O(n) extra memory, which the task forbids.",
        approach="""
1. `l = 0`, `r = len(s) - 1`.
2. While `l < r`: swap `s[l]` and `s[r]`; `l += 1`; `r -= 1`.

**Dry run** `["h","e","l","l","o"]`:

| l | r | after swap |
|---|---|---|
| 0 | 4 | o e l l h |
| 1 | 3 | o l l e h |
| 2 | 2 | stop (`l < r` is false) |
""",
        complexity="Time **O(n)** — n/2 swaps. Space **O(1)**.",
        pitfalls="- `s = s[::-1]` creates a new list; the judge's list stays the same.\n- With negative indices the partner of `i` is `-(i + 1)`, not `-i` (`s[-0]` is `s[0]`).\n- The middle element of an odd-length list stays put.",
        follow_up="*Reverse String II* (LC 541), *Reverse Words in a String* (LC 151), and the three-reversal trick in *Rotate Array*.",
    ),
),
# ---------------------------------------------------------------------------
dict(
    id="remove-element",
    title="Remove Element",
    difficulty="Easy",
    pattern="Two Pointers",
    leetcode=_lc("remove-element"),
    neetcode=_nc("remove-element"),
    entry="removeElement",
    inplace_arg=0,
    checker='''def check(args, got, expected):
    original, val = args[0], args[1]
    keep = sorted(x for x in original if x != val)
    k = len(keep)
    return isinstance(got, list) and len(got) == len(original) and sorted(got[:k]) == keep
''',
    description=r"""
Given a list `nums` and a value `val`, remove **every occurrence of `val`** from `nums` **in place** and
return `k`, the number of elements that remain.

After your method returns, the first `k` slots of `nums` must contain the remaining elements (in **any**
order). Whatever sits in the slots after that is ignored. Do not create a second list. (Our judge checks
the contents of `nums`; still return `k` as LeetCode expects.)

**Constraints**

- `0 <= len(nums) <= 100` on LeetCode (our judge uses 3·10^4)
- `0 <= nums[i] <= 50`, `0 <= val <= 100`

**Example 1:** `nums = [3, 2, 2, 3], val = 3` → return `2`, `nums` starts with `[2, 2]`

**Example 2:** `nums = [0, 1, 2, 2, 3, 0, 4, 2], val = 2` → return `5`, first five slots hold `0, 1, 3, 0, 4` in some order
""",
    starter='''class Solution:
    def removeElement(self, nums: List[int], val: int) -> int:
        pass
''',
    solution='''class Solution:
    def removeElement(self, nums, val):
        w = 0                              # next free slot for a kept element
        for x in nums:
            if x != val:
                nums[w] = x
                w += 1
        return w
''',
    tests=[
        [[3, 2, 2, 3], 3],
        [[0, 1, 2, 2, 3, 0, 4, 2], 2],
        [[], 0],
        [[1], 1],
        [[1], 2],
        [[4, 4, 4], 4],
        [[1, 2, 3], 9],
        [[2, 1, 2, 1, 2], 2],
        [[5, 0, 5, 0, 0], 0],
        [[7, 7, 1], 7],
        [[1, 7, 7], 7],
        [_re_big, 17],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def removeElement(self, nums, val):
        return len(nums) - nums.count(val)        # correct count, array untouched
''',
        '''class Solution:
    def removeElement(self, nums, val):
        w = 0
        for i in range(len(nums) - 1):            # never reads the last element
            if nums[i] != val:
                nums[w] = nums[i]
                w += 1
        return w
''',
    ],
    guide=dict(
        prereqs="The reader/writer shape from *The Two Pointers pattern*; *Move Zeroes*.",
        intuition="Read every element once. Keep a separate **write position** that only moves when you decide to keep an element. Kept elements get copied down to the write position, so they end up packed at the front.",
        hints=[
            "You don't need to delete anything — overwrite instead.",
            "One index reads, another marks where the next kept value goes.",
            "If nums[r] != val: nums[w] = nums[r]; w += 1. Return w.",
        ],
        brute_force="Call `nums.remove(val)` until it fails, or `del nums[i]` in a loop: every deletion shifts the rest of the list, giving **O(n²)**.",
        approach="""
1. `w = 0`.
2. For each `x` in `nums` (the reader): if `x != val`, write `nums[w] = x` and `w += 1`.
3. Return `w`.

Writing while iterating is safe because `w` never gets ahead of the reader.

**Dry run** `[3, 2, 2, 3]`, `val = 3`:

| x | keep? | w before → after | nums |
|---|---|---|---|
| 3 | no | 0 → 0 | [3,2,2,3] |
| 2 | yes | 0 → 1 | [2,2,2,3] |
| 2 | yes | 1 → 2 | [2,2,2,3] |
| 3 | no | 2 → 2 | [2,2,2,3] |

Return **2**; first two slots are `[2, 2]`.
""",
        complexity="Time **O(n)**, space **O(1)**.",
        pitfalls="- Returning the count without rearranging the list.\n- Deleting inside an index loop skips elements and is slow.\n- Empty list → 0.",
        follow_up="When `val` is rare, swap each occurrence with the last element and shrink the length instead — fewer writes. Same template: *Remove Duplicates from Sorted Array*, *Move Zeroes*.",
    ),
),
# ---------------------------------------------------------------------------
dict(
    id="valid-palindrome-ii",
    title="Valid Palindrome II",
    difficulty="Easy",
    pattern="Two Pointers",
    leetcode=_lc("valid-palindrome-ii"),
    neetcode=_nc("valid-palindrome-ii"),
    entry="validPalindrome",
    description=r"""
A **palindrome** reads the same forwards and backwards. Given a string `s`, return `True` if it is a
palindrome already **or can become one by deleting at most one character**; otherwise return `False`.

**Constraints**

- `1 <= len(s) <= 10^5`, lowercase English letters

**Example 1:** `s = "aba"` → `True`

**Example 2:** `s = "abca"` → `True` (delete `b` or `c`)

**Example 3:** `s = "abc"` → `False`
""",
    starter='''class Solution:
    def validPalindrome(self, s: str) -> bool:
        pass
''',
    solution='''class Solution:
    def validPalindrome(self, s):
        def is_pal(l, r):
            while l < r:
                if s[l] != s[r]:
                    return False
                l += 1
                r -= 1
            return True

        l, r = 0, len(s) - 1
        while l < r:
            if s[l] != s[r]:
                # one deletion allowed: drop the left char or the right char
                return is_pal(l + 1, r) or is_pal(l, r - 1)
            l += 1
            r -= 1
        return True
''',
    tests=[
        ["aba"],
        ["abca"],
        ["abc"],
        ["a"],
        ["ab"],
        ["cbbcc"],
        ["ccbbc"],
        ["deeee"],
        ["abcdba"],
        ["abccbxa"],
        ["eeccccbebaeeabebccceea"],
        ["aguokepatgbnvfqmgmlcupuufxoohdfpgjdmysgvhmvffcnqxjjxqncffvmhvgsymdjgpfdhooxfuupuculmgmqfvnbgtapekouga"],
        [_vp2_pal],
        [_vp2_one],
        [_vp2_del],
    ],
    wrong_solutions=[
        '''class Solution:
    def validPalindrome(self, s):
        l, r = 0, len(s) - 1
        used = False
        while l < r:
            if s[l] != s[r]:
                if used:
                    return False
                used = True
                l += 1                    # always deletes on the LEFT
                continue
            l += 1
            r -= 1
        return True
''',
        '''class Solution:
    def validPalindrome(self, s):
        mismatches = sum(1 for i in range(len(s) // 2) if s[i] != s[-1 - i])
        return mismatches <= 1            # a mismatch is not the same as a deletion
''',
    ],
    guide=dict(
        prereqs="*Valid Palindrome* (converging pointers).",
        intuition="Walk inward from both ends while the characters match. At the **first mismatch**, the one allowed deletion must remove either the left character or the right one — nothing else can repair this pair. Try both: is the rest a plain palindrome after skipping left, or after skipping right?",
        hints=[
            "Deleting each character in turn and re-checking is O(n²). Where must the deleted character be?",
            "Only the two characters at the first mismatch are candidates.",
            "Write a helper is_pal(l, r); answer is is_pal(l+1, r) or is_pal(l, r-1).",
        ],
        brute_force="For each index, delete it and test for a palindrome: **O(n²)** — 10¹⁰ steps at n = 10⁵.",
        approach="""
1. `l = 0`, `r = n - 1`. While `l < r` and `s[l] == s[r]`: move inward.
2. On a mismatch return `is_pal(l + 1, r) or is_pal(l, r - 1)`.
3. If the pointers meet without a mismatch → `True`.

**Dry run** `"cbbcc"`:

- `c` vs `c` ✓ → `l=1, r=3`
- `b` vs `c` ✗ → try skipping left: `s[2..3] = "bc"` ✗; try skipping right: `s[1..2] = "bb"` ✓ → **True**

A solution that always skips on the left would wrongly answer `False` here.
""",
        complexity="Time **O(n)** — the main scan plus at most two helper scans. Space **O(1)**.",
        pitfalls="- Greedily choosing one side at the mismatch (`\"cbbcc\"` vs `\"ccbbc\"` need opposite choices).\n- Counting mismatched pairs ≤ 1 is wrong: `\"abc\"` has one mismatched pair but can't be fixed.",
        follow_up="*Valid Palindrome III* (LC 1216): up to k deletions → dynamic programming (longest palindromic subsequence).",
    ),
),
# ---------------------------------------------------------------------------
dict(
    id="squares-of-a-sorted-array",
    title="Squares of a Sorted Array",
    difficulty="Easy",
    pattern="Two Pointers",
    leetcode=_lc("squares-of-a-sorted-array"),
    neetcode=_nc("squares-of-a-sorted-array"),
    entry="sortedSquares",
    description=r"""
`nums` is sorted in non-decreasing order and may contain negative numbers. Return a new list with the
**square of every number, also sorted** in non-decreasing order.

**Constraints**

- `1 <= len(nums) <= 10^4` (our judge uses 12,000)
- `-10^4 <= nums[i] <= 10^4`

**Example 1:** `nums = [-4, -1, 0, 3, 10]` → `[0, 1, 9, 16, 100]`

**Example 2:** `nums = [-7, -3, 2, 3, 11]` → `[4, 9, 9, 49, 121]`

**Follow-up:** squaring then sorting is O(n log n); find an O(n) method.
""",
    starter='''class Solution:
    def sortedSquares(self, nums: List[int]) -> List[int]:
        pass
''',
    solution='''class Solution:
    def sortedSquares(self, nums):
        n = len(nums)
        res = [0] * n
        l, r = 0, n - 1
        for w in range(n - 1, -1, -1):        # fill the answer from the back
            if abs(nums[l]) > abs(nums[r]):
                res[w] = nums[l] * nums[l]
                l += 1
            else:
                res[w] = nums[r] * nums[r]
                r -= 1
        return res
''',
    tests=[
        [[-4, -1, 0, 3, 10]],
        [[-7, -3, 2, 3, 11]],
        [[0]],
        [[-5]],
        [[1, 2, 3]],
        [[-3, -2, -1]],
        [[-2, 2]],
        [[-1, 0, 0, 1]],
        [[-10000, 10000]],
        [[-5, -3, -2, -1]],
        [[-3, -3, 3, 3, 4]],
        [_sq_big],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def sortedSquares(self, nums):
        return [x * x for x in nums]          # squares of negatives are out of order
''',
        '''class Solution:
    def sortedSquares(self, nums):
        n = len(nums)
        res = [0] * n
        l, r = 0, n - 1
        for w in range(n):                    # fills from the FRONT with the largest squares
            if abs(nums[l]) > abs(nums[r]):
                res[w] = nums[l] * nums[l]
                l += 1
            else:
                res[w] = nums[r] * nums[r]
                r -= 1
        return res
''',
    ],
    guide=dict(
        prereqs="Converging pointers; *Merge Sorted Array* (filling a result from the back).",
        intuition="Squaring makes big negatives big positives, so the **largest squares sit at the two ends** of the sorted input and the smallest are somewhere in the middle. Compare the two ends, take the larger square, and place it in the last free slot of the answer.",
        hints=[
            "Where in a sorted list like [-7, -3, 2, 3, 11] is the largest absolute value?",
            "Use one pointer at each end and compare absolute values.",
            "Fill the output from right to left with the larger square, moving that pointer inward.",
        ],
        brute_force="Square everything and sort: **O(n log n)**. Correct and short, but it ignores that the input is already sorted.",
        approach="""
1. `res = [0] * n`, `l = 0`, `r = n - 1`.
2. For `w` from `n - 1` down to `0`: if `abs(nums[l]) > abs(nums[r])` write `nums[l]²` and `l += 1`; else write `nums[r]²` and `r -= 1`.

**Dry run** `[-4, -1, 0, 3, 10]`:

| w | l (value) | r (value) | write |
|---|---|---|---|
| 4 | 0 (−4) | 4 (10) | 100 |
| 3 | 0 (−4) | 3 (3) | 16 |
| 2 | 1 (−1) | 3 (3) | 9 |
| 1 | 1 (−1) | 2 (0) | 1 |
| 0 | 2 (0) | 2 (0) | 0 |

Result `[0, 1, 9, 16, 100]`.
""",
        complexity="Time **O(n)**, space **O(n)** for the output (O(1) extra).",
        pitfalls="- Returning the squares in input order.\n- Filling from the front puts the largest first (descending output).\n- Compare absolute values (or squares), not raw values.",
        follow_up="*Sort Transformed Array* (LC 360): apply a quadratic `ax² + bx + c` — same two-ended merge, direction depends on the sign of `a`.",
    ),
),
# ---------------------------------------------------------------------------
dict(
    id="backspace-string-compare",
    title="Backspace String Compare",
    difficulty="Easy",
    pattern="Two Pointers",
    leetcode=_lc("backspace-string-compare"),
    neetcode=_nc("backspace-string-compare"),
    entry="backspaceCompare",
    description=r"""
Two strings `s` and `t` are typed into empty text editors, where the character `#` means **backspace**:
it deletes the character before it (pressing backspace on empty text does nothing). Return `True` if both
editors show the same text at the end.

**Constraints**

- `1 <= len(s), len(t) <= 200` on LeetCode (our judge uses 5·10^4)
- lowercase letters and `#`

**Example 1:** `s = "ab#c", t = "ad#c"` → `True` (both become `"ac"`)

**Example 2:** `s = "ab##", t = "c#d#"` → `True` (both become `""`)

**Example 3:** `s = "a#c", t = "b"` → `False`

**Follow-up:** O(n) time and O(1) extra space.
""",
    starter='''class Solution:
    def backspaceCompare(self, s: str, t: str) -> bool:
        pass
''',
    solution='''class Solution:
    def backspaceCompare(self, s, t):
        def next_char(text, i):
            """Index of the next surviving character at or before i (or -1)."""
            skip = 0
            while i >= 0:
                if text[i] == "#":
                    skip += 1
                elif skip:
                    skip -= 1
                else:
                    break
                i -= 1
            return i

        i, j = len(s) - 1, len(t) - 1
        while True:
            i, j = next_char(s, i), next_char(t, j)
            if i < 0 or j < 0:
                return i < 0 and j < 0
            if s[i] != t[j]:
                return False
            i -= 1
            j -= 1
''',
    tests=[
        ["ab#c", "ad#c"],
        ["ab##", "c#d#"],
        ["a#c", "b"],
        ["a", "a"],
        ["#", "#"],
        ["a##c", "#a#c"],
        ["y#fo##f", "y#f#o##f"],
        ["bxj##tw", "bxo#j##tw"],
        ["abc#", "ab"],
        ["nzp#o#g", "b#nzp#o#g"],
        ["a#b", "b#a"],
        ["####", "#"],
        [_bs_a, _bs_b],
        [_bs_a, _bs_c],
    ],
    wrong_solutions=[
        '''class Solution:
    def backspaceCompare(self, s, t):
        return s.replace("#", "") == t.replace("#", "")      # '#' must also delete a letter
''',
        '''class Solution:
    def backspaceCompare(self, s, t):
        def build(text):
            out = []
            for ch in text:
                if ch == "#":
                    out.pop()                               # crashes on backspace with nothing typed
                else:
                    out.append(ch)
            return out
        return build(s) == build(t)
''',
    ],
    guide=dict(
        prereqs="Lists used as stacks (`append` / `pop`); one pointer per sequence from *The Two Pointers pattern*.",
        intuition="""
Typing with backspace is a **stack**: letters are pushed, `#` pops. Build both final texts and compare —
that's the clear O(n)-space answer. For O(1) space, read each string **from the right**: a `#` tells you
to skip the next letter you meet, so scanning backwards you can produce the surviving characters one at
a time and compare them as you go.
""",
        hints=[
            "Simulate the editor with a list: append letters, pop on '#' (if not empty).",
            "Reading left to right you can't know whether a letter survives. What about right to left?",
            "Keep a skip counter per string; find the next surviving char in each, compare, repeat.",
        ],
        brute_force="Build each string with repeated slicing (`text = text[:-1]`), which copies the string each time: O(n²). The stack version is O(n) time and O(n) space.",
        approach="""
**Stack version** — `build(text)`: for each `ch`, if `ch != '#'` append it; else pop **if the list is non-empty**. Compare the two lists.

**Two-pointer version:**
1. `i`, `j` start at the ends.
2. `next_char` moves an index left: every `#` adds 1 to `skip`; a letter with `skip > 0` is deleted (`skip -= 1`); a letter with `skip == 0` survives — stop there.
3. If both ran out → `True`; if only one → `False`; if the surviving letters differ → `False`; else step both left.

**Dry run** `s = "ab#c"`, `t = "ad#c"` (from the right):

- survivors: `c` and `c` ✓
- s: `#` (skip 1), `b` (deleted), `a` survives; t: `#`, `d` deleted, `a` survives ✓
- both exhausted → **True**
""",
        complexity="Two-pointer: time **O(n + m)**, space **O(1)**. Stack: O(n + m) time and space.",
        pitfalls="- Backspace on empty text must do nothing (`\"a##c\"`).\n- Removing the `#` characters is not the same as applying them.\n- One string finishing before the other means different texts.",
        follow_up="Same stack idea: *Removing Stars From a String* (LC 2390), *Make The String Great* (LC 1544).",
    ),
),
# ---------------------------------------------------------------------------
dict(
    id="3sum-closest",
    title="3Sum Closest",
    difficulty="Medium",
    pattern="Two Pointers",
    leetcode=_lc("3sum-closest"),
    neetcode=_nc("3sum-closest"),
    entry="threeSumClosest",
    description=r"""
Given an integer list `nums` and an integer `target`, choose **three numbers at different positions**
whose sum is as **close to `target` as possible**, and return that sum. The inputs are built so that the
closest sum is unique.

**Constraints**

- `3 <= len(nums) <= 500` (our judge uses 800)
- `-1000 <= nums[i] <= 1000`, `-10^4 <= target <= 10^4`

**Example 1:** `nums = [-1, 2, 1, -4], target = 1` → `2` (`-1 + 2 + 1`)

**Example 2:** `nums = [0, 0, 0], target = 1` → `0`
""",
    starter='''class Solution:
    def threeSumClosest(self, nums: List[int], target: int) -> int:
        pass
''',
    solution='''class Solution:
    def threeSumClosest(self, nums, target):
        nums = sorted(nums)
        n = len(nums)
        best = nums[0] + nums[1] + nums[2]
        for i in range(n - 2):
            l, r = i + 1, n - 1
            while l < r:
                s = nums[i] + nums[l] + nums[r]
                if abs(s - target) < abs(best - target):
                    best = s
                if s == target:
                    return s
                if s < target:
                    l += 1
                else:
                    r -= 1
        return best
''',
    tests=[
        [[-1, 2, 1, -4], 1],
        [[0, 0, 0], 1],
        [[1, 1, 1], 0],
        [[4, 5, 6], -2],
        [[1, 1, 1, 0], 100],
        [[-5, -4, -3], 0],
        [[1, 2, 5, 10, 11], 12],
        [[0, 1, 2], 3],
        [[-1000, -1000, -1000, 1000], 10000],
        [[4, 0, 5, -5, 3, 3, 0, -4, -5], -2],
        [[2, 3, 8, 9, 10], 16],
        [_3c_big, 2999],
        [_3c_big, -77],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def threeSumClosest(self, nums, target):
        nums = sorted(nums)
        n = len(nums)
        best = 0                               # 0 may not be a reachable sum
        for i in range(n - 2):
            l, r = i + 1, n - 1
            while l < r:
                s = nums[i] + nums[l] + nums[r]
                if abs(s - target) < abs(best - target):
                    best = s
                if s < target:
                    l += 1
                else:
                    r -= 1
        return best
''',
        '''class Solution:
    def threeSumClosest(self, nums, target):
        n = len(nums)                          # forgot to sort: pointer moves are meaningless
        best = nums[0] + nums[1] + nums[2]
        for i in range(n - 2):
            l, r = i + 1, n - 1
            while l < r:
                s = nums[i] + nums[l] + nums[r]
                if abs(s - target) < abs(best - target):
                    best = s
                if s < target:
                    l += 1
                else:
                    r -= 1
        return best
''',
    ],
    guide=dict(
        prereqs="*3Sum* (sort, fix one value, converge two pointers).",
        intuition="Same skeleton as 3Sum, but instead of looking for an exact hit you **track the best sum seen so far**. Sorting still tells you which way to move: sum too small → move the left pointer right to increase it; too large → move the right pointer left.",
        hints=[
            "All triples is O(n³). Reuse the 3Sum structure.",
            "Keep `best`, initialised to a real triple's sum, and update when |s − target| is smaller.",
            "If s == target you can return immediately — nothing is closer than distance 0.",
        ],
        brute_force="Three nested loops over all triples: **O(n³)** — 8.5·10⁷ triples for n = 800.",
        approach="""
1. Sort. `best = nums[0] + nums[1] + nums[2]`.
2. For each `i`: `l = i + 1`, `r = n - 1`; while `l < r`:
   - `s = nums[i] + nums[l] + nums[r]`; update `best` if closer.
   - `s == target` → return; `s < target` → `l += 1`; else `r -= 1`.

**Dry run** `[-1, 2, 1, -4]`, target 1 → sorted `[-4, -1, 1, 2]`, best = −4:

| i | l | r | s | distance | best |
|---|---|---|---|---|---|
| −4 | −1 | 2 | −3 | 4 | −3 |
| −4 | 1 | 2 | −1 | 2 | −1 |
| −1 | 1 | 2 | 2 | 1 | **2** |

Return **2**.
""",
        complexity="Time **O(n²)** after an O(n log n) sort. Space O(1) besides the sorted copy.",
        pitfalls="- Initialising `best` to 0 or infinity carelessly: 0 might not be achievable (`[1,1,1], 0`).\n- Forgetting to sort.\n- Return the **sum**, not the distance.",
        follow_up="*3Sum Smaller* (count triples below target), *4Sum*, and *Two Sum Less Than K*.",
    ),
),
# ---------------------------------------------------------------------------
dict(
    id="number-of-subsequences-that-satisfy-the-given-sum-condition",
    title="Number of Subsequences That Satisfy the Given Sum Condition",
    difficulty="Medium",
    pattern="Two Pointers",
    leetcode=_lc("number-of-subsequences-that-satisfy-the-given-sum-condition"),
    neetcode=_nc("number-of-subsequences-that-satisfy-the-given-sum-condition"),
    entry="numSubseq",
    description=r"""
A **subsequence** of a list is what you get by deleting zero or more elements (the rest keep their order).
Given a list `nums` and an integer `target`, count the **non-empty** subsequences in which

`(smallest element) + (largest element) <= target`.

Subsequences are counted by the positions chosen, so equal values at different positions give different
subsequences. The count can be astronomically large, so return it **modulo `10^9 + 7`** (the remainder
after dividing by 1,000,000,007).

**Constraints**

- `1 <= len(nums) <= 10^5` (our judge uses 2·10^4)
- `1 <= nums[i], target <= 10^6`

**Example 1:** `nums = [3, 5, 6, 7], target = 9` → `4` (`[3]`, `[3,5]`, `[3,5,6]`, `[3,6]`)

**Example 2:** `nums = [3, 3, 6, 8], target = 10` → `6`

**Example 3:** `nums = [2, 3, 3, 4, 6, 7], target = 12` → `61`
""",
    starter='''class Solution:
    def numSubseq(self, nums: List[int], target: int) -> int:
        pass
''',
    solution='''class Solution:
    def numSubseq(self, nums, target):
        MOD = 10**9 + 7
        nums = sorted(nums)
        n = len(nums)
        pow2 = [1] * n                       # pow2[k] = 2^k mod MOD
        for k in range(1, n):
            pow2[k] = pow2[k - 1] * 2 % MOD
        res = 0
        l, r = 0, n - 1
        while l <= r:
            if nums[l] + nums[r] <= target:
                res = (res + pow2[r - l]) % MOD   # nums[l] is the minimum; any subset of the r-l others
                l += 1
            else:
                r -= 1
        return res
''',
    tests=[
        [[3, 5, 6, 7], 9],
        [[3, 3, 6, 8], 10],
        [[2, 3, 3, 4, 6, 7], 12],
        [[1], 2],
        [[1], 1],
        [[5, 5], 9],
        [[5, 5], 10],
        [[7, 6, 5, 3], 9],
        [[1, 2, 3], 100],
        [[9, 1, 8, 2, 7, 3], 10],
        [[14, 4, 6, 6, 20, 8, 5, 6, 8, 12, 6, 10, 14, 9, 17, 16, 9, 7, 14, 11, 14, 15, 13, 11, 10, 18, 13, 17, 17, 14, 17, 7, 9, 5, 10, 13, 8, 5, 18, 20, 7, 5, 5, 15, 19, 14], 22],
        [_ns_small, 2],
        [_ns_big, 1000000],
    ],
    wrong_solutions=[
        '''class Solution:
    def numSubseq(self, nums, target):
        MOD = 10**9 + 7
        n = len(nums)                         # forgot to sort
        res = 0
        l, r = 0, n - 1
        while l <= r:
            if nums[l] + nums[r] <= target:
                res = (res + pow(2, r - l, MOD)) % MOD
                l += 1
            else:
                r -= 1
        return res
''',
        '''class Solution:
    def numSubseq(self, nums, target):
        nums = sorted(nums)
        res = 0
        l, r = 0, len(nums) - 1
        while l <= r:
            if nums[l] + nums[r] <= target:
                res += 2 ** (r - l)
                l += 1
            else:
                r -= 1
        return res                            # forgot the modulo
''',
    ],
    guide=dict(
        prereqs="*Two Sum II* (converging pointers on sorted data); powers of two; the modulo operator `%`.",
        intuition="""
Only the smallest and largest element of a subsequence matter, and they don't depend on order — so
**sorting is allowed**. After sorting, fix `nums[l]` as the minimum and find the furthest `r` with
`nums[l] + nums[r] <= target`. Every element between `l+1` and `r` can be freely included or left out
(each is ≥ the minimum and ≤ `nums[r]`), giving `2^(r − l)` subsequences that contain `nums[l]`.
""",
        hints=[
            "Does the order of elements affect a subsequence's min and max? Can you sort?",
            "Fix the minimum at index l. Which elements may join it?",
            "If nums[l] + nums[r] <= target add 2^(r−l) and move l; otherwise move r left. Precompute powers of 2 modulo 1e9+7.",
        ],
        brute_force="Enumerate all 2ⁿ − 1 subsequences and check min + max: exponential — hopeless beyond about 20 elements.",
        approach="""
1. Sort; precompute `pow2[k] = 2^k % MOD`.
2. `l = 0`, `r = n - 1`. While `l <= r`:
   - if `nums[l] + nums[r] <= target`: add `pow2[r - l]`; `l += 1`
   - else `r -= 1`.

Why `2^(r − l)`: `nums[l]` must be in (it is the minimum); each of the `r − l` elements after it up to `r` is an independent yes/no choice.

**Dry run** `[3, 5, 6, 7]`, target 9:

| l | r | sum | action | res |
|---|---|---|---|---|
| 0 (3) | 3 (7) | 10 | r−− | 0 |
| 0 (3) | 2 (6) | 9 | + 2² = 4, l++ | 4 |
| 1 (5) | 2 (6) | 11 | r−− | 4 |
| 1 (5) | 1 (5) | 10 | r−− | 4 |

Answer **4**.
""",
        complexity="Time **O(n log n)** for the sort plus O(n) for the scan. Space O(n) for the power table.",
        pitfalls="- Loop condition is `l <= r`: a single element can be both min and max (`[1], target 2`).\n- Computing `2 ** k` without the modulus builds numbers with thousands of digits — slow, and the wrong answer.\n- Not sorting.",
        follow_up="Why is sorting valid here but not for *subarray* problems? (Subarrays depend on position; min/max of a subsequence do not.) Related: *Count the Number of Fair Pairs* (LC 2563).",
    ),
),
]
