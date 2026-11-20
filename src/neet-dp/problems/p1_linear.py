import random

_R = random.Random(2024)


def _ints(n, lo, hi):
    return [_R.randint(lo, hi) for _ in range(n)]


PROBLEMS = [
dict(
    id="climbing-stairs",
    title="Climbing Stairs",
    difficulty="Easy",
    pattern="1-D DP",
    leetcode="https://leetcode.com/problems/climbing-stairs/",
    neetcode="https://neetcode.io/problems/climbing-stairs",
    entry="climbStairs",
    description=r"""
A staircase has `n` steps. Each move you climb either **1** or **2** steps. Count the number of
different ordered sequences of moves that take you from the ground (step 0) to exactly step `n`.

**Constraints**

- `1 <= n <= 45`

**Example 1:** `n = 2` → `2` (1+1, 2)

**Example 2:** `n = 3` → `3` (1+1+1, 1+2, 2+1)
""",
    starter='''class Solution:
    def climbStairs(self, n: int) -> int:
        pass
''',
    solution='''class Solution:
    def climbStairs(self, n):
        a, b = 1, 1          # ways(0), ways(1)
        for _ in range(n - 1):
            a, b = b, a + b
        return b
''',
    tests=[[2], [3], [1], [4], [5], [6], [10], [20], [30], [38], [44], [45]],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def climbStairs(self, n):
        return n
''',
        '''class Solution:
    def climbStairs(self, n):
        return 2 ** (n - 1)
''',
    ],
    guide=dict(
        prereqs="Fibonacci Number; the lesson *Linear DP: stairs, robbers and decoders*.",
        intuition=r"""
Think about the **last move**. Any way to reach step `n` ends with either a 1-step (from `n-1`)
or a 2-step (from `n-2`). These two groups don't overlap and together cover everything, so
`ways(n) = ways(n-1) + ways(n-2)` — Fibonacci, shifted by one.
""",
        hints=[
            "Classify every route by its final move.",
            "ways(n) = ways(n-1) + ways(n-2). What are ways(0) and ways(1)?",
            "ways(0) = 1 (the empty route), ways(1) = 1. Slide two variables forward.",
        ],
        brute_force=r"""
Recursively try both moves from every step: `go(i) = go(i+1) + go(i+2)`, returning 1 at `i == n`
and 0 past it. The call tree is a Fibonacci tree — several billion calls for `n = 45`. **O(φⁿ)**.
""",
        approach=r"""
**State:** `ways(i)` = number of move sequences from 0 that land exactly on step `i`.
**Recurrence:** `ways(i) = ways(i-1) + ways(i-2)`.
**Base:** `ways(0) = 1`, `ways(1) = 1`.
**Order:** `i = 2 … n`. **Answer:** `ways(n)`.

| i | 0 | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|---|
| ways | 1 | 1 | 2 | 3 | 5 | 8 |

Two rolling variables replace the table.
""",
        complexity="Time O(n), space O(1).",
        pitfalls=r"""
- Getting the base case `ways(0) = 1` wrong (it is the empty sequence, and it makes `ways(2) = 2` work out).
- Recursion without memoization times out long before `n = 45`.
""",
        follow_up="If you may climb any size in a set `S`, ways(i) = Σ ways(i−s) for s in S — that's the permutation-counting cousin of Coin Change II.",
    ),
),
dict(
    id="min-cost-climbing-stairs",
    title="Min Cost Climbing Stairs",
    difficulty="Easy",
    pattern="1-D DP",
    leetcode="https://leetcode.com/problems/min-cost-climbing-stairs/",
    neetcode="https://neetcode.io/problems/min-cost-climbing-stairs",
    entry="minCostClimbingStairs",
    description=r"""
You are given `cost`, where `cost[i]` is the toll you pay when you **leave** step `i`; after
paying you may move up 1 or 2 steps. You may begin on step `0` or step `1` for free. The "top" is
the position just past the last step (index `len(cost)`).

Return the minimum total toll needed to reach the top.

**Constraints**

- `2 <= len(cost) <= 1000`
- `0 <= cost[i] <= 999`

**Example 1:** `cost = [10, 15, 20]` → `15` (start on step 1, pay 15, jump 2 to the top)

**Example 2:** `cost = [1,100,1,1,1,100,1,1,100,1]` → `6`
""",
    starter='''class Solution:
    def minCostClimbingStairs(self, cost: List[int]) -> int:
        pass
''',
    solution='''class Solution:
    def minCostClimbingStairs(self, cost):
        a = b = 0                      # best cost to stand on step i-2, i-1
        for i in range(2, len(cost) + 1):
            a, b = b, min(b + cost[i - 1], a + cost[i - 2])
        return b
''',
    tests=[
        [[10, 15, 20]],
        [[1, 100, 1, 1, 1, 100, 1, 1, 100, 1]],
        [[0, 2, 3, 2]],
        [[5, 7]],
        [[0, 0]],
        [[1, 2, 3]],
        [[0, 1, 2, 2]],
        [[10, 1, 1, 10, 1, 1, 10]],
        [[999] * 10],
        [_ints(30, 0, 50)],
        [_ints(500, 0, 999)],
        [_ints(1000, 0, 999)],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def minCostClimbingStairs(self, cost):
        n = len(cost)
        p = 0 if cost[0] <= cost[1] else 1
        total = cost[p]
        while p < n - 2:
            p = p + 1 if cost[p + 1] < cost[p + 2] else p + 2
            total += cost[p]
        return total
''',
        '''class Solution:
    def minCostClimbingStairs(self, cost):
        a = b = 0
        for i in range(2, len(cost)):
            a, b = b, min(b + cost[i - 1], a + cost[i - 2])
        return b
''',
    ],
    guide=dict(
        prereqs="Climbing Stairs.",
        intuition=r"""
Same shape as Climbing Stairs, but instead of *counting* routes we *minimise* cost. To stand on
step `i` you came from `i-1` (paying `cost[i-1]`) or from `i-2` (paying `cost[i-2]`); take the
cheaper. The top is just "step `n`".
""",
        hints=[
            "Define best(i) = cheapest way to stand on position i (before paying its toll).",
            "best(0) = best(1) = 0 because you may start there for free.",
            "best(i) = min(best(i-1) + cost[i-1], best(i-2) + cost[i-2]); answer best(n).",
        ],
        brute_force="Try both jumps from every step recursively: O(2ⁿ) calls. For n = 1000 this never finishes.",
        approach=r"""
**State:** `best(i)` = minimum toll paid to *arrive* at position `i`.
**Recurrence:** `best(i) = min(best(i-1) + cost[i-1], best(i-2) + cost[i-2])`.
**Base:** `best(0) = best(1) = 0`. **Order:** `i = 2..n`. **Answer:** `best(n)`.

Dry run on `[10, 15, 20]`:

| i | 0 | 1 | 2 | 3 (top) |
|---|---|---|---|---|
| best | 0 | 0 | min(0+15, 0+10)=10 | min(10+20, 0+15)=15 |
""",
        complexity="Time O(n), space O(1) with two rolling variables.",
        pitfalls=r"""
- The top is index `n`, not `n-1`; stopping the loop one early returns the cost to stand on the last step.
- Greedy "always step to the cheaper of the next two" fails, e.g. `[0, 2, 3, 2]` (greedy 4, optimum 3).
""",
        follow_up="Equivalent formulation: dp[i] = cost[i] + min(dp[i-1], dp[i-2]) and answer min(dp[n-1], dp[n-2]).",
    ),
),
dict(
    id="house-robber",
    title="House Robber",
    difficulty="Medium",
    pattern="1-D DP",
    leetcode="https://leetcode.com/problems/house-robber/",
    neetcode="https://neetcode.io/problems/house-robber",
    entry="rob",
    description=r"""
Houses stand in a row; `nums[i]` is the cash in house `i`. You may take the cash from any set of
houses, **except** that you can never take from two houses that are next to each other (the
alarm links neighbours). Return the largest total you can collect.

**Constraints**

- `1 <= len(nums) <= 1000`
- `0 <= nums[i] <= 400`

**Example 1:** `nums = [1, 2, 3, 1]` → `4` (houses 0 and 2)

**Example 2:** `nums = [2, 7, 9, 3, 1]` → `12` (houses 0, 2, 4)
""",
    starter='''class Solution:
    def rob(self, nums: List[int]) -> int:
        pass
''',
    solution='''class Solution:
    def rob(self, nums):
        prev2 = prev1 = 0
        for x in nums:
            prev2, prev1 = prev1, max(prev1, prev2 + x)
        return prev1
''',
    tests=[
        [[1, 2, 3, 1]],
        [[2, 7, 9, 3, 1]],
        [[5]],
        [[2, 1]],
        [[1, 2]],
        [[2, 1, 1, 2]],
        [[0, 0, 0]],
        [[4, 1, 2, 7, 5, 3, 1]],
        [[100, 1, 1, 100]],
        [_ints(40, 0, 400)],
        [_ints(500, 0, 400)],
        [_ints(1000, 0, 400)],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def rob(self, nums):
        return max(sum(nums[::2]), sum(nums[1::2]))
''',
        '''class Solution:
    def rob(self, nums):
        taken = set()
        total = 0
        for i in sorted(range(len(nums)), key=lambda i: -nums[i]):
            if i - 1 not in taken and i + 1 not in taken:
                taken.add(i)
                total += nums[i]
        return total
''',
    ],
    guide=dict(
        prereqs="Climbing Stairs; lesson *Linear DP*.",
        intuition=r"""
At house `i` you make one decision: **take it** (then house `i-1` must have been skipped, so add
`nums[i]` to the best up to `i-2`) or **skip it** (keep the best up to `i-1`). This
"take-or-skip" pattern is the backbone of countless DP problems.
""",
        hints=[
            "Alternating houses (all even or all odd indices) is not always optimal — try `[2, 1, 1, 2]`.",
            "Let best(i) be the most cash using only houses 0..i. Consider whether house i is robbed.",
            "best(i) = max(best(i-1), best(i-2) + nums[i]). Keep two rolling values.",
        ],
        brute_force="Enumerate every subset with no two adjacent (Fibonacci-many, ~φⁿ) via recursion `max(go(i+1), nums[i] + go(i+2))` without memo. O(φⁿ) — hopeless at n = 1000.",
        approach=r"""
**State:** `best(i)` = max loot from houses `0..i`.
**Recurrence:** `best(i) = max(best(i-1), best(i-2) + nums[i])`.
**Base:** `best(-1) = best(-2) = 0`. **Order:** left to right. **Answer:** `best(n-1)`.

Dry run on `[2, 7, 9, 3, 1]`:

| i | nums | skip → best(i-1) | take → best(i-2)+x | best(i) |
|---|---|---|---|---|
| 0 | 2 | 0 | 0+2 | 2 |
| 1 | 7 | 2 | 0+7 | 7 |
| 2 | 9 | 7 | 2+9 | 11 |
| 3 | 3 | 11 | 7+3 | 11 |
| 4 | 1 | 11 | 11+1 | **12** |
""",
        complexity="Time O(n), space O(1).",
        pitfalls=r"""
- "Even vs odd indices" fails on `[2, 1, 1, 2]` (answer 4: houses 0 and 3).
- Greedy "biggest house first" fails on `[2, 3, 2]` (takes 3; optimum 4).
- Top-down recursion on n = 1000 is close to Python's default recursion limit; prefer the loop.
""",
        follow_up="House Robber II (circular street), House Robber III (houses on a binary tree), Delete and Earn (reduces to House Robber on value buckets).",
    ),
),
dict(
    id="house-robber-ii",
    title="House Robber II",
    difficulty="Medium",
    pattern="1-D DP",
    leetcode="https://leetcode.com/problems/house-robber-ii/",
    neetcode="https://neetcode.io/problems/house-robber-ii",
    entry="rob",
    description=r"""
Same rules as House Robber — never take from two neighbouring houses — but now the houses form a
**circle**: the first and the last house are also neighbours. Return the maximum loot.

**Constraints**

- `1 <= len(nums) <= 1000`
- `0 <= nums[i] <= 1000`

**Example 1:** `nums = [2, 3, 2]` → `3` (houses 0 and 2 are adjacent on the circle)

**Example 2:** `nums = [1, 2, 3, 1]` → `4`
""",
    starter='''class Solution:
    def rob(self, nums: List[int]) -> int:
        pass
''',
    solution='''class Solution:
    def rob(self, nums):
        def line(arr):
            a = b = 0
            for x in arr:
                a, b = b, max(b, a + x)
            return b
        if len(nums) == 1:
            return nums[0]
        return max(line(nums[1:]), line(nums[:-1]))
''',
    tests=[
        [[2, 3, 2]],
        [[1, 2, 3, 1]],
        [[1, 2, 3]],
        [[7]],
        [[1, 5]],
        [[5, 1, 1, 5]],
        [[200, 3, 140, 20, 10]],
        [[0, 0, 0, 0]],
        [[1, 3, 1, 3, 100]],
        [_ints(50, 0, 1000)],
        [_ints(999, 0, 1000)],
        [_ints(1000, 0, 1000)],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def rob(self, nums):
        a = b = 0
        for x in nums:
            a, b = b, max(b, a + x)
        return b
''',
        '''class Solution:
    def rob(self, nums):
        def line(arr):
            a = b = 0
            for x in arr:
                a, b = b, max(b, a + x)
            return b
        return max(line(nums[1:]), line(nums[:-1])) if len(nums) > 1 else 0
''',
    ],
    guide=dict(
        prereqs="House Robber.",
        intuition=r"""
The circle only adds one constraint: houses `0` and `n-1` can't both be robbed. So **at least one
of them is skipped**. Solve two ordinary (linear) robber problems — one without the first house,
one without the last — and take the better.
""",
        hints=[
            "What is the only new conflict introduced by the circle?",
            "Either house 0 is not robbed, or house n-1 is not robbed (or both).",
            "Answer = max(rob_line(nums[1:]), rob_line(nums[:-1])), with n = 1 as a special case.",
        ],
        brute_force="Enumerate valid subsets on the circle recursively: O(φⁿ).",
        approach=r"""
Reuse House Robber's `line(arr)` (take-or-skip with two rolling values).

- Case A: exclude the last house → `line(nums[:-1])`.
- Case B: exclude the first house → `line(nums[1:])`.

Any valid circular choice is valid in at least one of these lines, and every line choice is valid on
the circle, so the max of the two is exact.

`[2, 3, 2]`: `line([2,3]) = 3`, `line([3,2]) = 3` → **3**.
`[200, 3, 140, 20, 10]`: A = `line([200,3,140,20]) = 340`, B = `line([3,140,20,10]) = 150` → **340**.
""",
        complexity="Time O(n) (two linear passes), space O(1) besides the slices (use index ranges to make it truly O(1)).",
        pitfalls="- `n = 1`: both slices are empty and you'd return 0 — the answer is `nums[0]`.\n- Running the linear robber on the whole circle can take both ends.",
        follow_up="House Robber III — the street is a binary tree; DP returns a (rob, skip) pair per node.",
    ),
),
dict(
    id="longest-palindromic-substring",
    title="Longest Palindromic Substring",
    difficulty="Medium",
    pattern="1-D DP / Expand Around Center",
    leetcode="https://leetcode.com/problems/longest-palindromic-substring/",
    neetcode="https://neetcode.io/problems/longest-palindromic-substring",
    entry="longestPalindrome",
    checker='''def check(args, got, expected):
    s = args[0]
    return isinstance(got, str) and len(got) == len(expected) and got == got[::-1] and got in s
''',
    description=r"""
Given a string `s`, return a **contiguous** substring of `s` that reads the same forwards and
backwards and is as long as possible. If several palindromes tie for the longest length, any one
of them is accepted.

**Constraints**

- `1 <= len(s) <= 1000`
- `s` consists of English letters and digits

**Example 1:** `s = "babad"` → `"bab"` (`"aba"` is also accepted)

**Example 2:** `s = "cbbd"` → `"bb"`
""",
    starter='''class Solution:
    def longestPalindrome(self, s: str) -> str:
        pass
''',
    solution='''class Solution:
    def longestPalindrome(self, s):
        best_l, best_r = 0, 0
        n = len(s)
        for c in range(n):
            for l, r in ((c, c), (c, c + 1)):
                while l >= 0 and r < n and s[l] == s[r]:
                    l -= 1
                    r += 1
                if r - l - 1 > best_r - best_l:
                    best_l, best_r = l + 1, r
        return s[best_l:best_r]
''',
    tests=[
        ["babad"],
        ["cbbd"],
        ["a"],
        ["ac"],
        ["aa"],
        ["abba"],
        ["forgeeksskeegfor"],
        ["abacdfgdcaba"],
        ["racecar"],
        ["x" + "ab" * 40 + "y"],
        ["".join(_R.choice("ab") for _ in range(1000))],
        ["a" * 1000],
        ["".join(_R.choice("abcdefghij") for _ in range(997)) + "zz"],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def longestPalindrome(self, s):
        best = s[0]
        for c in range(len(s)):
            l = r = c
            while l >= 0 and r < len(s) and s[l] == s[r]:
                l -= 1; r += 1
            if r - l - 1 > len(best):
                best = s[l + 1:r]
        return best
''',
        '''class Solution:
    def longestPalindrome(self, s):
        r = s[::-1]
        best = ""
        for i in range(len(s)):
            for j in range(i + len(best) + 1, len(s) + 1):
                if s[i:j] in r:
                    best = s[i:j]
        return best
''',
    ],
    guide=dict(
        prereqs="String slicing; lesson *Palindromes, products and word breaks*.",
        intuition=r"""
A palindrome is symmetric around its **center**. There are only `2n - 1` possible centers — each
character (odd length) and each gap between neighbours (even length). From each center, expand
outward while the two ends match. Every palindrome is found from its own center, so trying all
centers finds the longest one.

The DP view: `pal[i][j]` is true iff `s[i] == s[j]` and `pal[i+1][j-1]`. Expanding from a center
just walks this recurrence outward without storing the table.
""",
        hints=[
            "Checking every substring is O(n³). Can you reuse the fact that `s[i+1..j-1]` is a palindrome?",
            "Every palindrome has a center: either a single character or the gap between two equal characters.",
            "For each of the 2n−1 centers, expand while `s[l] == s[r]` and track the longest window.",
        ],
        brute_force="Enumerate all O(n²) substrings and test each in O(n): **O(n³)** — about 1.7×10⁸ character comparisons at n = 1000, far too slow in the browser.",
        approach=r"""
**DP formulation.** `pal(i, j)` = is `s[i..j]` a palindrome?

- base: `pal(i, i) = True`, `pal(i, i+1) = (s[i] == s[i+1])`
- recurrence: `pal(i, j) = s[i] == s[j] and pal(i+1, j-1)`
- order: by increasing length `j - i`.

That's O(n²) time and space. **Expand around center** evaluates exactly the same recurrence but
for one center at a time, so it needs O(1) space:

```text
for each center c:
    odd:  l = r = c
    even: l = c, r = c + 1
    while in bounds and s[l] == s[r]: l -= 1; r += 1
    palindrome is s[l+1 : r]
```

Dry run `"cbbd"`: center 1 (odd) gives `"b"`, gap 1–2 (even) expands `b=b` → `"bb"`, then `c≠d` stops. Answer `"bb"`.
""",
        complexity="Time O(n²) worst case (e.g. all-equal strings), space O(1).",
        pitfalls=r"""
- Forgetting even-length centers: `"cbbd"` would return `"c"` instead of `"bb"`.
- "Longest common substring of `s` and reverse(`s`)" is a famous wrong idea: `"abacdfgdcaba"` has common substring `"abacd"` reversed but it isn't a palindrome.
- Off-by-one when converting the stopped `(l, r)` back to the window `s[l+1:r]`.
""",
        follow_up="Manacher's algorithm finds it in O(n). See also Palindromic Substrings (count instead of longest) and Longest Palindromic Subsequence (interval DP).",
    ),
),
dict(
    id="palindromic-substrings",
    title="Palindromic Substrings",
    difficulty="Medium",
    pattern="1-D DP / Expand Around Center",
    leetcode="https://leetcode.com/problems/palindromic-substrings/",
    neetcode="https://neetcode.io/problems/palindromic-substrings",
    entry="countSubstrings",
    description=r"""
Count how many **contiguous** substrings of `s` are palindromes. Substrings at different
positions count separately even if their text is identical.

**Constraints**

- `1 <= len(s) <= 1000`
- lowercase English letters

**Example 1:** `s = "abc"` → `3` (`"a"`, `"b"`, `"c"`)

**Example 2:** `s = "aaa"` → `6` (three `"a"`, two `"aa"`, one `"aaa"`)
""",
    starter='''class Solution:
    def countSubstrings(self, s: str) -> int:
        pass
''',
    solution='''class Solution:
    def countSubstrings(self, s):
        n, total = len(s), 0
        for c in range(n):
            for l, r in ((c, c), (c, c + 1)):
                while l >= 0 and r < n and s[l] == s[r]:
                    total += 1
                    l -= 1
                    r += 1
        return total
''',
    tests=[
        ["abc"],
        ["aaa"],
        ["a"],
        ["ab"],
        ["aa"],
        ["abba"],
        ["racecar"],
        ["abacaba"],
        ["ab" * 50],
        ["".join(_R.choice("ab") for _ in range(800))],
        ["a" * 1000],
        ["".join(_R.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(1000))],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def countSubstrings(self, s):
        n, total = len(s), 0
        for c in range(n):
            l = r = c
            while l >= 0 and r < n and s[l] == s[r]:
                total += 1
                l -= 1; r += 1
        return total
''',
        '''class Solution:
    def countSubstrings(self, s):
        seen = set()
        n = len(s)
        for c in range(n):
            for l, r in ((c, c), (c, c + 1)):
                while l >= 0 and r < n and s[l] == s[r]:
                    seen.add(s[l:r + 1]); l -= 1; r += 1
        return len(seen)
''',
    ],
    guide=dict(
        prereqs="Longest Palindromic Substring.",
        intuition="Every palindrome is discovered exactly once when expanding from its own center, and each successful expansion step *is* one new palindrome. So count the expansions.",
        hints=[
            "Single characters are palindromes, so the answer is at least n.",
            "Expanding from a center by one step on each side yields a new, longer palindrome — or stops.",
            "Sum, over all 2n−1 centers, the number of successful expansion steps.",
        ],
        brute_force="Test all n(n+1)/2 substrings for palindromicity: O(n³).",
        approach=r"""
DP view: `pal(i, j) = s[i] == s[j] and (j - i < 2 or pal(i+1, j-1))`, answer = number of true cells.
Table for `"aaa"` (rows i, cols j):

| | 0 | 1 | 2 |
|---|---|---|---|
| 0 | T | T | T |
| 1 | | T | T |
| 2 | | | T |

Six `T` cells → **6**. Expand-around-center visits the same cells center by center with O(1) memory:
each `while` iteration that passes the equality test adds one to the count.
""",
        complexity="Time O(n²), space O(1) (or O(n²) for the explicit table).",
        pitfalls="- Missing even centers undercounts (`\"aa\"` → 2 instead of 3).\n- Counting *distinct* palindromes is a different problem — positions matter here.",
        follow_up="Palindrome Partitioning II (min cuts) uses this pal table as a building block.",
    ),
),
dict(
    id="decode-ways",
    title="Decode Ways",
    difficulty="Medium",
    pattern="1-D DP",
    leetcode="https://leetcode.com/problems/decode-ways/",
    neetcode="https://neetcode.io/problems/decode-ways",
    entry="numDecodings",
    description=r"""
Letters are encoded as numbers: `'A' → "1"`, `'B' → "2"`, …, `'Z' → "26"`. Given a string of
digits `s`, count how many letter strings could have produced it. Each code is either one digit
`1`–`9` or two digits `10`–`26`; a code may **not** start with `0` (so `"06"` is not a code).

Return the count (return `0` if no decoding exists). Python integers are unbounded, so just return
the exact count even if it is large.

**Constraints**

- `1 <= len(s) <= 100`
- `s` contains only digits

**Example 1:** `s = "12"` → `2` (`"AB"` or `"L"`)

**Example 2:** `s = "226"` → `3` (`2 2 6`, `22 6`, `2 26`)

**Example 3:** `s = "06"` → `0`
""",
    starter='''class Solution:
    def numDecodings(self, s: str) -> int:
        pass
''',
    solution='''class Solution:
    def numDecodings(self, s):
        prev2, prev1 = 1, (0 if s[0] == "0" else 1)   # ways for prefixes of length i-2, i-1
        for i in range(2, len(s) + 1):
            cur = 0
            if s[i - 1] != "0":
                cur += prev1
            if s[i - 2] != "0" and int(s[i - 2:i]) <= 26:
                cur += prev2
            prev2, prev1 = prev1, cur
        return prev1
''',
    tests=[
        ["12"],
        ["226"],
        ["06"],
        ["0"],
        ["10"],
        ["27"],
        ["100"],
        ["2101"],
        ["11106"],
        ["1201234"],
        ["30"],
        ["1" * 100],
        ["".join(_R.choice("1226") for _ in range(100))],
        ["12" * 30 + "0" + "26" * 19],
    ],
    examples=3,
    wrong_solutions=[
        '''class Solution:
    def numDecodings(self, s):
        prev2, prev1 = 1, 1
        for i in range(2, len(s) + 1):
            cur = prev1
            if int(s[i - 2:i]) <= 26:
                cur += prev2
            prev2, prev1 = prev1, cur
        return prev1
''',
        '''class Solution:
    def numDecodings(self, s):
        prev2, prev1 = 1, (0 if s[0] == "0" else 1)
        for i in range(2, len(s) + 1):
            cur = 0
            if s[i - 1] != "0":
                cur += prev1
            if 10 <= int(s[i - 2:i]) <= 99:
                cur += prev2
            prev2, prev1 = prev1, cur
        return prev1
''',
    ],
    guide=dict(
        prereqs="Climbing Stairs (this is Climbing Stairs with conditions on each step).",
        intuition=r"""
Look at how a decoding of the prefix `s[:i]` **ends**: its last code is either the single digit
`s[i-1]` (allowed if it isn't `0`) or the pair `s[i-2:i]` (allowed if it's between 10 and 26).
So `ways(i) = [single ok]·ways(i-1) + [pair ok]·ways(i-2)` — Climbing Stairs where some steps are
forbidden.
""",
        hints=[
            "Let ways(i) be the number of decodings of the first i characters.",
            "The last code is one digit or two digits. When is each choice legal?",
            "Single: s[i-1] != '0'. Pair: s[i-2] != '0' and int(s[i-2:i]) <= 26. ways(0) = 1.",
        ],
        brute_force="Recursively try a one- and two-digit code at every position: O(2ⁿ) for strings like `\"111…1\"` (Fibonacci growth, ~10²⁰ paths at n = 100).",
        approach=r"""
**State:** `ways(i)` for prefix length `i`. **Base:** `ways(0) = 1`, `ways(1) = 1 if s[0] != '0' else 0`.
**Recurrence:** as above. **Order:** `i = 2..n`. **Answer:** `ways(n)`.

Dry run `"226"`:

| i | prefix | single ok? | pair ok? | ways |
|---|---|---|---|---|
| 0 | "" | | | 1 |
| 1 | "2" | 2 ✓ | | 1 |
| 2 | "22" | 2 ✓ (+1) | 22 ✓ (+1) | 2 |
| 3 | "226" | 6 ✓ (+2) | 26 ✓ (+1) | **3** |

Dry run `"100"`: ways = 1, 1 ("10"), then `"0"` can't stand alone and `"00"` isn't a code → **0**.
""",
        complexity="Time O(n), space O(1).",
        pitfalls=r"""
- `'0'` can never be decoded alone; `"06"` is not a valid pair either (leading zero).
- `"27"` … `"99"` are not pairs.
- An early `0` makes everything after it 0 — don't return early incorrectly for strings like `"10"`.
""",
        follow_up="Decode Ways II adds a `*` wildcard; same DP with multiplicities, answer mod 10⁹+7.",
    ),
),
dict(
    id="coin-change",
    title="Coin Change",
    difficulty="Medium",
    pattern="1-D DP / Unbounded Knapsack",
    leetcode="https://leetcode.com/problems/coin-change/",
    neetcode="https://neetcode.io/problems/coin-change",
    entry="coinChange",
    description=r"""
You have unlimited coins of each denomination in `coins`. Return the **fewest** coins whose values
add up exactly to `amount`, or `-1` if no combination works. An `amount` of `0` needs `0` coins.

**Constraints**

- `1 <= len(coins) <= 12`
- `1 <= coins[i] <= 2^31 - 1`
- `0 <= amount <= 10^4`

**Example 1:** `coins = [1, 2, 5], amount = 11` → `3` (5 + 5 + 1)

**Example 2:** `coins = [2], amount = 3` → `-1`

**Example 3:** `coins = [1, 3, 4], amount = 6` → `2` (3 + 3 — greedy 4 + 1 + 1 uses three)
""",
    starter='''class Solution:
    def coinChange(self, coins: List[int], amount: int) -> int:
        pass
''',
    solution='''class Solution:
    def coinChange(self, coins, amount):
        INF = amount + 1
        dp = [0] + [INF] * amount
        for a in range(1, amount + 1):
            for c in coins:
                if c <= a and dp[a - c] + 1 < dp[a]:
                    dp[a] = dp[a - c] + 1
        return dp[amount] if dp[amount] != INF else -1
''',
    tests=[
        [[1, 2, 5], 11],
        [[2], 3],
        [[1, 3, 4], 6],
        [[1], 0],
        [[1], 1],
        [[2], 1],
        [[2, 5, 10, 1], 27],
        [[186, 419, 83, 408], 6249],
        [[3, 7, 405, 436], 8839],
        [[2147483647], 2],
        [[1, 7, 10], 14],
        [[5, 7], 1],
        [[1, 2, 5, 10, 20, 50, 100, 200], 10000],
        [[37, 233, 417, 89, 7, 13], 9973],
    ],
    examples=3,
    wrong_solutions=[
        '''class Solution:
    def coinChange(self, coins, amount):
        count = 0
        for c in sorted(coins, reverse=True):
            count += amount // c
            amount %= c
        return count if amount == 0 else -1
''',
        '''class Solution:
    def coinChange(self, coins, amount):
        INF = float("inf")
        dp = [0] + [INF] * amount
        for c in coins:
            for a in range(amount, c - 1, -1):
                dp[a] = min(dp[a], dp[a - c] + 1)
        return dp[amount] if dp[amount] != INF else -1
''',
    ],
    guide=dict(
        prereqs="Lesson *Knapsack: 0/1 and unbounded*.",
        intuition=r"""
Greedy (largest coin first) works for "nice" coin systems like US cents but not in general:
`[1, 3, 4]` with amount 6 → greedy `4+1+1`, optimum `3+3`. Instead, think about the **last coin**:
if the optimal multiset for amount `a` contains coin `c`, removing it leaves an optimal multiset
for `a - c`. Try every possible last coin.
""",
        hints=[
            "Find a counter-example to greedy before writing code.",
            "Let dp[a] = fewest coins to make a. What's dp[0]? How does dp[a] relate to dp[a - c]?",
            "dp[a] = 1 + min(dp[a - c] for c in coins if c <= a); use a sentinel like amount + 1 for 'impossible'.",
        ],
        brute_force="Recursively try every coin as the next coin: `f(a) = 1 + min(f(a - c))`. The branching factor is `len(coins)` and depth up to `amount`, so O(kᵃ) — hopeless for amount 10⁴.",
        approach=r"""
**State:** `dp[a]` = minimum coins summing to `a` (∞ if impossible).
**Recurrence:** `dp[a] = min over c ≤ a of dp[a - c] + 1`.
**Base:** `dp[0] = 0`. **Order:** `a = 1..amount` (every `a - c` is smaller). **Answer:** `dp[amount]` or −1.

Table for `coins = [1, 3, 4]`, amount 6:

| a | 0 | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|---|
| dp | 0 | 1 | 2 | 1 | 1 | 2 | **2** |

`dp[6] = min(dp[5], dp[3], dp[2]) + 1 = min(2, 1, 2) + 1 = 2`.

This is an **unbounded knapsack**: each coin can be reused, so `dp[a - c]` may itself already use `c`.
""",
        complexity="Time O(amount · k), space O(amount).",
        pitfalls=r"""
- Greedy fails on non-canonical coin systems.
- Iterating capacity **downwards** per coin (0/1 knapsack order) forbids reusing a coin — wrong here.
- Using `float('inf')` is fine, but remember to convert ∞ to −1 at the end.
- Huge coin values (up to 2³¹−1): guard `c <= a` before indexing.
""",
        follow_up="Coin Change II counts the combinations instead (2-D DP module). BFS over amounts also gives the minimum (shortest path where each edge is a coin).",
    ),
),
dict(
    id="maximum-product-subarray",
    title="Maximum Product Subarray",
    difficulty="Medium",
    pattern="1-D DP / Kadane",
    leetcode="https://leetcode.com/problems/maximum-product-subarray/",
    neetcode="https://neetcode.io/problems/maximum-product-subarray",
    entry="maxProduct",
    description=r"""
Given an integer array `nums`, find the non-empty **contiguous** subarray whose elements have the
largest product and return that product.

**Constraints**

- `1 <= len(nums) <= 2 * 10^4`
- `-10 <= nums[i] <= 10`
- the product of every prefix/suffix and subarray fits in a 32-bit signed integer

**Example 1:** `nums = [2, 3, -2, 4]` → `6` (`[2, 3]`)

**Example 2:** `nums = [-2, 0, -1]` → `0`

**Example 3:** `nums = [-2, 3, -4]` → `24` (the whole array: two negatives cancel)
""",
    starter='''class Solution:
    def maxProduct(self, nums: List[int]) -> int:
        pass
''',
    solution='''class Solution:
    def maxProduct(self, nums):
        best = hi = lo = nums[0]
        for x in nums[1:]:
            cands = (x, hi * x, lo * x)
            hi, lo = max(cands), min(cands)
            best = max(best, hi)
        return best
''',
    tests=[
        [[2, 3, -2, 4]],
        [[-2, 0, -1]],
        [[-2, 3, -4]],
        [[-2]],
        [[0]],
        [[-1, -1]],
        [[0, 2]],
        [[3, -1, 4]],
        [[-2, -3, 7]],
        [[2, -5, -2, -4, 3]],
        [[-1, 0, -2, -3, 0, -4]],
        [[(_R.choice([-2, -1, 1, 2, 3]) if i % 20 else 0) for i in range(20000)]],
        [[(_R.choice([-2, -1, 1, 2]) if i % 25 else 0) for i in range(15000)]],
    ],
    examples=3,
    wrong_solutions=[
        '''class Solution:
    def maxProduct(self, nums):
        best = cur = nums[0]
        for x in nums[1:]:
            cur = max(x, cur * x)
            best = max(best, cur)
        return best
''',
        '''class Solution:
    def maxProduct(self, nums):
        best = cur = nums[0]
        for x in nums[1:]:
            cur = cur * x if cur != 0 else x
            best = max(best, cur, x)
        return best
''',
    ],
    guide=dict(
        prereqs="Kadane's algorithm for Maximum Subarray (sum).",
        intuition=r"""
For sums, Kadane keeps only "best subarray ending here". Products break that: a hugely *negative*
running product becomes hugely *positive* after one more negative number. So track **both** the
maximum and the minimum product of a subarray ending at the current index.
""",
        hints=[
            "Why does Kadane's `cur = max(x, cur * x)` fail on `[-2, 3, -4]`?",
            "A negative number swaps the roles of the largest and smallest products.",
            "Keep hi and lo ending at i: candidates are x, hi·x, lo·x; new hi = max, new lo = min.",
        ],
        brute_force="Try every (i, j) pair and multiply: O(n²) with a running product (O(n³) naively). n = 2·10⁴ means 2·10⁸ multiplications — too slow.",
        approach=r"""
**State:** `hi(i)`, `lo(i)` = max / min product of a subarray **ending at** `i`.
**Recurrence:** with `x = nums[i]`, `hi(i) = max(x, hi(i-1)·x, lo(i-1)·x)` and `lo(i) = min(...)`.
**Base:** `hi(0) = lo(0) = nums[0]`. **Answer:** `max_i hi(i)`.

Dry run `[2, 3, -2, 4]`:

| i | x | hi | lo | best |
|---|---|---|---|---|
| 0 | 2 | 2 | 2 | 2 |
| 1 | 3 | 6 | 3 | 6 |
| 2 | −2 | −2 | −12 | 6 |
| 3 | 4 | 4 | −48 | **6** |

Dry run `[-2, 3, -4]`: hi/lo go (−2,−2) → (3,−6) → (24,−12) → **24**.

A zero resets both to 0 automatically (the candidate `x = 0` and products 0).
""",
        complexity="Time O(n), space O(1).",
        pitfalls=r"""
- Updating `hi` before computing `lo` with the *old* `hi` — compute both from the same old pair.
- Initialising `best = 0` breaks `[-2]` (answer −2).
""",
        follow_up="Prefix/suffix trick: the answer is the max over all prefix products and suffix products (resetting at zeros).",
    ),
),
dict(
    id="word-break",
    title="Word Break",
    difficulty="Medium",
    pattern="1-D DP",
    leetcode="https://leetcode.com/problems/word-break/",
    neetcode="https://neetcode.io/problems/word-break",
    entry="wordBreak",
    description=r"""
Given a string `s` and a list of dictionary words `wordDict`, decide whether `s` can be cut into a
sequence of one or more dictionary words (words may be reused any number of times).

**Constraints**

- `1 <= len(s) <= 300`
- `1 <= len(wordDict) <= 1000`, `1 <= len(word) <= 20`
- all words are distinct; only lowercase letters

**Example 1:** `s = "leetcode", wordDict = ["leet", "code"]` → `True`

**Example 2:** `s = "applepenapple", wordDict = ["apple", "pen"]` → `True`

**Example 3:** `s = "catsandog", wordDict = ["cats", "dog", "sand", "and", "cat"]` → `False`
""",
    starter='''class Solution:
    def wordBreak(self, s: str, wordDict: List[str]) -> bool:
        pass
''',
    solution='''class Solution:
    def wordBreak(self, s, wordDict):
        words = set(wordDict)
        lens = sorted({len(w) for w in words})
        n = len(s)
        ok = [True] + [False] * n          # ok[i]: s[:i] can be segmented
        for i in range(1, n + 1):
            for L in lens:
                if L > i:
                    break
                if ok[i - L] and s[i - L:i] in words:
                    ok[i] = True
                    break
        return ok[n]
''',
    tests=[
        ["leetcode", ["leet", "code"]],
        ["applepenapple", ["apple", "pen"]],
        ["catsandog", ["cats", "dog", "sand", "and", "cat"]],
        ["a", ["a"]],
        ["a", ["b"]],
        ["goalspecial", ["go", "goal", "goals", "special"]],
        ["aaaaaaa", ["aaaa", "aaa"]],
        ["cars", ["car", "ca", "rs"]],
        ["bb", ["a", "b", "bbb", "bbbb"]],
        ["a" * 150 + "b", ["a" * k for k in range(1, 11)]],
        ["a" * 299 + "b", ["a", "aa", "aaa", "aaaa", "aaaaa", "aaaaaa", "ba"]],
        ["ab" * 150, ["a", "b", "ab", "aba", "bab"]],
        ["".join(_R.choice(["cat", "dog", "mouse", "catdog"]) for _ in range(60)), ["cat", "dog", "mouse"]],
    ],
    examples=3,
    wrong_solutions=[
        '''class Solution:
    def wordBreak(self, s, wordDict):
        i = 0
        words = sorted(wordDict, key=len, reverse=True)
        while i < len(s):
            for w in words:
                if s.startswith(w, i):
                    i += len(w)
                    break
            else:
                return False
        return True
''',
        '''class Solution:
    def wordBreak(self, s, wordDict):
        i = 0
        words = sorted(wordDict, key=len)
        while i < len(s):
            for w in words:
                if s.startswith(w, i):
                    i += len(w)
                    break
            else:
                return False
        return True
''',
    ],
    guide=dict(
        prereqs="Hash sets; lesson *Palindromes, products and word breaks*.",
        intuition=r"""
`s[:i]` is breakable iff some dictionary word `w` ends exactly at `i` **and** the part before it,
`s[:i-len(w)]`, is breakable. Greedy choices (take the longest or shortest matching word) can paint
you into a corner, so we record, for every prefix length, whether it is reachable.
""",
        hints=[
            "Why does greedily taking the longest matching word fail on `\"goalspecial\"`?",
            "Define ok[i] = can s[:i] be segmented? ok[0] = True.",
            "ok[i] = any(ok[i - len(w)] and s[i-len(w):i] == w). Only try lengths that occur in the dictionary.",
        ],
        brute_force=r"""
Try every dictionary word as the next piece and recurse on the remainder. With `s = "aaaa…ab"` and
words `a, aa, aaa, …`, the number of ways to split the `a`-run grows exponentially before the final
`b` fails each one — **O(2ⁿ)**.
""",
        approach=r"""
**State:** `ok[i]` — prefix `s[:i]` can be segmented. **Base:** `ok[0] = True`.
**Recurrence:** `ok[i] = OR over word lengths L: ok[i-L] and s[i-L:i] in words`.
**Order:** `i = 1..n`. **Answer:** `ok[n]`.

`s = "leetcode"`:

| i | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|---|---|---|---|---|---|---|---|---|---|
| ok | T | F | F | F | T ("leet") | F | F | F | T ("code" after ok[4]) |

Top-down equivalent: `@cache def can(i): return i == n or any(s.startswith(w, i) and can(i+len(w)) for w in words)`.
""",
        complexity="Time O(n · m · L) where m = number of distinct word lengths and L the cost of slicing/hashing (≤ 20); space O(n).",
        pitfalls=r"""
- Greedy longest-match fails (`"goalspecial"`), and greedy shortest-match fails (`"aaaaaaa"` with `aaaa`, `aaa`).
- Scanning the whole dictionary for each `i` is fine, but convert it to a `set` for O(1) lookups.
""",
        follow_up="Word Break II returns all segmentations (backtracking + memo). A trie over the dictionary speeds up the inner loop.",
    ),
),
dict(
    id="longest-increasing-subsequence",
    title="Longest Increasing Subsequence",
    difficulty="Medium",
    pattern="1-D DP / Patience Sorting",
    leetcode="https://leetcode.com/problems/longest-increasing-subsequence/",
    neetcode="https://neetcode.io/problems/longest-increasing-subsequence",
    entry="lengthOfLIS",
    description=r"""
Return the length of the longest **strictly increasing subsequence** of `nums`. A subsequence keeps
the original order but may skip elements.

**Constraints**

- `1 <= len(nums) <= 2500`
- `-10^4 <= nums[i] <= 10^4`

**Example 1:** `nums = [10, 9, 2, 5, 3, 7, 101, 18]` → `4` (e.g. `2, 3, 7, 101`)

**Example 2:** `nums = [0, 1, 0, 3, 2, 3]` → `4`

**Example 3:** `nums = [7, 7, 7, 7]` → `1` (strictly increasing)
""",
    starter='''class Solution:
    def lengthOfLIS(self, nums: List[int]) -> int:
        pass
''',
    solution='''from bisect import bisect_left

class Solution:
    def lengthOfLIS(self, nums):
        tails = []                  # tails[k] = smallest tail of an increasing subsequence of length k+1
        for x in nums:
            k = bisect_left(tails, x)
            if k == len(tails):
                tails.append(x)
            else:
                tails[k] = x
        return len(tails)
''',
    tests=[
        [[10, 9, 2, 5, 3, 7, 101, 18]],
        [[0, 1, 0, 3, 2, 3]],
        [[7, 7, 7, 7]],
        [[5]],
        [[1, 2]],
        [[2, 1]],
        [[4, 10, 4, 3, 8, 9]],
        [[1, 3, 6, 7, 9, 4, 10, 5, 6]],
        [[3, 5, 6, 2, 5, 4, 19, 5, 6, 7, 12]],
        [list(range(2500, 0, -1))],
        [list(range(-1250, 1250))],
        [_ints(2500, -10000, 10000)],
        [_ints(2500, 0, 50)],
    ],
    examples=3,
    wrong_solutions=[
        '''class Solution:
    def lengthOfLIS(self, nums):
        best = cur = 1
        for i in range(1, len(nums)):
            cur = cur + 1 if nums[i] > nums[i - 1] else 1
            best = max(best, cur)
        return best
''',
        '''from bisect import bisect_right

class Solution:
    def lengthOfLIS(self, nums):
        tails = []
        for x in nums:
            k = bisect_right(tails, x)
            if k == len(tails):
                tails.append(x)
            else:
                tails[k] = x
        return len(tails)
''',
        '''class Solution:
    def lengthOfLIS(self, nums):
        length, last = 0, float("-inf")
        for x in nums:
            if x > last:
                length += 1
                last = x
        return length
''',
    ],
    guide=dict(
        prereqs="Lesson *Longest increasing subsequence and patience sorting*; binary search (`bisect`).",
        intuition=r"""
O(n²) DP: `lis(i)` = longest increasing subsequence **ending at** `i` = 1 + max `lis(j)` over earlier
`j` with `nums[j] < nums[i]`.

O(n log n): for each possible length `k`, remember the **smallest possible tail** of an increasing
subsequence of that length. Smaller tails are always better (easier to extend). These tails form a
sorted list, so each new number finds its slot by binary search.
""",
        hints=[
            "Define lis(i) as the longest increasing subsequence that ends exactly at index i.",
            "lis(i) = 1 + max(lis(j) for j < i if nums[j] < nums[i]); the answer is max over all i. That's O(n²).",
            "For O(n log n), keep tails[k] = smallest tail of any length-(k+1) increasing subsequence; replace with bisect_left.",
        ],
        brute_force="Enumerate all 2ⁿ subsequences and check which are increasing: O(2ⁿ · n).",
        approach=r"""
**O(n²) DP.** State `lis(i)`, base `lis(i) ≥ 1`, order left→right, answer `max lis`.

| i | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
|---|---|---|---|---|---|---|---|---|
| nums | 10 | 9 | 2 | 5 | 3 | 7 | 101 | 18 |
| lis | 1 | 1 | 1 | 2 | 2 | 3 | 4 | 4 |

**O(n log n) patience sorting** on the same input:

| x | tails after |
|---|---|
| 10 | [10] |
| 9 | [9] |
| 2 | [2] |
| 5 | [2, 5] |
| 3 | [2, 3] |
| 7 | [2, 3, 7] |
| 101 | [2, 3, 7, 101] |
| 18 | [2, 3, 7, 18] |

`len(tails) = 4`. Note `tails` itself need not be a real subsequence; only its length is meaningful.
""",
        complexity="O(n log n) time with bisect, O(n) space. The O(n²) DP is also accepted at n = 2500.",
        pitfalls=r"""
- Strictly increasing → `bisect_left` (an equal element replaces, not extends). `bisect_right` counts non-decreasing runs.
- The longest *contiguous* increasing run is a different (easier) problem.
- Top-down recursion over i with n = 2500 exceeds Python's default recursion depth.
""",
        follow_up="Reconstruct the subsequence with parent pointers; Russian Doll Envelopes (sort + LIS); Number of LIS.",
    ),
),
dict(
    id="partition-equal-subset-sum",
    title="Partition Equal Subset Sum",
    difficulty="Medium",
    pattern="1-D DP / 0-1 Knapsack",
    leetcode="https://leetcode.com/problems/partition-equal-subset-sum/",
    neetcode="https://neetcode.io/problems/partition-equal-subset-sum",
    entry="canPartition",
    description=r"""
Can the positive integers in `nums` be split into two groups (every element used exactly once)
whose sums are equal? Return `True` or `False`.

**Constraints**

- `1 <= len(nums) <= 200`
- `1 <= nums[i] <= 100`

**Example 1:** `nums = [1, 5, 11, 5]` → `True` (`[1, 5, 5]` and `[11]`)

**Example 2:** `nums = [1, 2, 3, 5]` → `False`
""",
    starter='''class Solution:
    def canPartition(self, nums: List[int]) -> bool:
        pass
''',
    solution='''class Solution:
    def canPartition(self, nums):
        total = sum(nums)
        if total % 2:
            return False
        target = total // 2
        reach = [True] + [False] * target
        for x in nums:
            for s in range(target, x - 1, -1):     # downwards: each item used at most once
                if reach[s - x]:
                    reach[s] = True
            if reach[target]:
                return True
        return reach[target]
''',
    tests=[
        [[1, 5, 11, 5]],
        [[1, 2, 3, 5]],
        [[1]],
        [[2, 2]],
        [[1, 2]],
        [[3, 3, 2, 2, 2]],
        [[2, 2, 3, 5]],
        [[1, 1, 1, 1, 1, 1, 6]],
        [[100, 100, 100, 100, 100, 100, 100, 100, 99, 1]],
        [[1] * 199 + [100]],
        [[2] * 99 + [1, 99]],
        [_ints(200, 1, 100)],
        [[_R.randint(1, 50) * 2 for _ in range(199)] + [1]],
        [[97] * 100 + [3] * 99 + [5]],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def canPartition(self, nums):
        a = b = 0
        for x in sorted(nums, reverse=True):
            if a <= b:
                a += x
            else:
                b += x
        return a == b
''',
        '''class Solution:
    def canPartition(self, nums):
        total = sum(nums)
        if total % 2:
            return False
        target = total // 2
        reach = [True] + [False] * target
        for x in nums:
            for s in range(x, target + 1):
                if reach[s - x]:
                    reach[s] = True
        return reach[target]
''',
    ],
    guide=dict(
        prereqs="Lesson *Knapsack: 0/1 and unbounded*.",
        intuition=r"""
Two equal halves means one group sums to exactly `total / 2`. So the question becomes **subset
sum**: is there a subset hitting `target = total // 2`? That's a 0/1 knapsack where each number is
used at most once and we only care about reachability.
""",
        hints=[
            "If the total is odd, the answer is immediately False.",
            "Reframe: does some subset sum to total // 2?",
            "Keep a boolean array reach[s]; for each number x, update s from target down to x: reach[s] |= reach[s - x].",
        ],
        brute_force="Try including or excluding each element: O(2ⁿ) — 2²⁰⁰ subsets is out of the question.",
        approach=r"""
**State:** `reach[i][s]` — can some subset of the first `i` numbers sum to `s`?
**Recurrence:** `reach[i][s] = reach[i-1][s] or reach[i-1][s - x_i]`.
**Base:** `reach[0][0] = True`. **Answer:** `reach[n][target]`.

Collapse to one row by iterating `s` **downwards**, so `reach[s - x]` still refers to the previous row
(the number hasn't been used yet in this round).

`[1, 5, 11, 5]`, target 11:

| after | reachable sums |
|---|---|
| start | {0} |
| 1 | {0, 1} |
| 5 | {0, 1, 5, 6} |
| 11 | {0, 1, 5, 6, 11, …} → **True** |

Bitset trick: `bits |= bits << x` then test bit `target` — the same DP in one big-integer operation.
""",
        complexity="Time O(n · target) ≤ 200 · 10,000 = 2·10⁶; space O(target).",
        pitfalls=r"""
- Iterating `s` upward reuses the same number repeatedly (unbounded knapsack) — `[2, 2, 3, 5]` would wrongly reach 6 as 2+2+2.
- Greedy "put the next largest in the lighter group" fails on `[3, 3, 2, 2, 2]`.
""",
        follow_up="Partition to K Equal Sum Subsets (bitmask DP / backtracking); Last Stone Weight II (closest subset sum to total/2); Target Sum.",
    ),
),
]
