import random

_R = random.Random(4242)


def _s(n, alpha):
    return "".join(_R.choice(alpha) for _ in range(n))


def _ints(n, lo, hi):
    return [_R.randint(lo, hi) for _ in range(n)]


PROBLEMS = [
dict(
    id="longest-common-subsequence",
    title="Longest Common Subsequence",
    difficulty="Medium",
    pattern="2-D DP / Strings",
    leetcode="https://leetcode.com/problems/longest-common-subsequence/",
    neetcode="https://neetcode.io/problems/longest-common-subsequence",
    entry="longestCommonSubsequence",
    description=r"""
A **subsequence** of a string is what remains after deleting zero or more characters without
reordering the rest (`"ace"` is a subsequence of `"abcde"`). Given `text1` and `text2`, return the
length of the longest string that is a subsequence of **both**; return `0` if they share no
character.

**Constraints**

- `1 <= len(text1), len(text2) <= 1000`
- lowercase English letters

**Example 1:** `text1 = "abcde", text2 = "ace"` → `3` (`"ace"`)

**Example 2:** `text1 = "abc", text2 = "def"` → `0`
""",
    starter='''class Solution:
    def longestCommonSubsequence(self, text1: str, text2: str) -> int:
        pass
''',
    solution='''class Solution:
    def longestCommonSubsequence(self, text1, text2):
        if len(text2) > len(text1):
            text1, text2 = text2, text1
        prev = [0] * (len(text2) + 1)
        for a in text1:
            cur = [0]
            for k, b in enumerate(text2):
                if a == b:
                    cur.append(prev[k] + 1)
                else:
                    cur.append(cur[k] if cur[k] > prev[k + 1] else prev[k + 1])
            prev = cur
        return prev[-1]
''',
    tests=[
        ["abcde", "ace"],
        ["abc", "def"],
        ["abc", "abc"],
        ["a", "a"],
        ["a", "b"],
        ["zab", "abz"],
        ["bsbininm", "jmjkbkjkv"],
        ["GTTCCTAATA".lower(), "CGATAATTGAGA".lower()],
        ["oxcpqrsvwf", "shmtulqrypy"],
        ["ab" * 20, "ba" * 20],
        [_s(600, "acgt"), _s(600, "acgt")],
        [_s(1000, "abcdefghijklmnopqrstuvwxyz"), _s(400, "abcdefghijklmnopqrstuvwxyz")],
        ["a" * 700, "a" * 300 + "b" * 300],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def longestCommonSubsequence(self, text1, text2):
        j = c = 0
        for ch in text1:
            k = text2.find(ch, j)
            if k != -1:
                c += 1
                j = k + 1
        return c
''',
        '''class Solution:
    def longestCommonSubsequence(self, text1, text2):
        return len(set(text1) & set(text2))
''',
    ],
    guide=dict(
        prereqs="Lesson *String DP: LCS, edit distance and friends* (Goodrich §13.3.2 walkthrough).",
        intuition=r"""
Compare the **last characters** of two prefixes. If they match, that character can end the common
subsequence: `1 + LCS(shorter both)`. If not, at least one of them is unused, so drop one or the
other and take the better: `max(LCS(drop from text1), LCS(drop from text2))`.
""",
        hints=[
            "Greedily matching the first available character fails on `\"zab\"` / `\"abz\"`.",
            "Let L[j][k] = LCS of text1[:j] and text2[:k]. Case-split on text1[j-1] == text2[k-1].",
            "Match: L[j-1][k-1] + 1. No match: max(L[j-1][k], L[j][k-1]). Row 0 and column 0 are 0.",
        ],
        brute_force="Enumerate all 2ⁿ subsequences of text1 and test each against text2 in O(m): O(2ⁿ·m). Naive recursion on the two cases is also exponential (~3^(n+m) calls in the worst case).",
        approach=r"""
**State:** `L[j][k]`. **Base:** `L[0][k] = L[j][0] = 0`.
**Recurrence:** `L[j][k] = L[j-1][k-1] + 1` if `x[j-1] == y[k-1]`, else `max(L[j-1][k], L[j][k-1])`.
**Order:** row-major. **Answer:** `L[n][m]`.

`"abcde"` vs `"ace"`:

| | ∅ | a | c | e |
|---|---|---|---|---|
| ∅ | 0 | 0 | 0 | 0 |
| a | 0 | **1** | 1 | 1 |
| b | 0 | 1 | 1 | 1 |
| c | 0 | 1 | **2** | 2 |
| d | 0 | 1 | 2 | 2 |
| e | 0 | 1 | 2 | **3** |

Each row depends only on the previous row, so two rows of length `min(n, m) + 1` suffice.
""",
        complexity="Time O(n·m) = 10⁶ cells at the limit; space O(min(n, m)).",
        pitfalls=r"""
- Confusing subsequence (gaps allowed) with substring (contiguous — that recurrence resets to 0 on mismatch).
- Off-by-one: table is `(n+1) × (m+1)`; character for row `j` is `text1[j-1]`.
- Recursive memo with depth n + m ≈ 2000 can exceed the recursion limit.
""",
        follow_up="Reconstruct the subsequence by walking back from L[n][m]. Related: Edit Distance, Shortest Common Supersequence, Delete Operation for Two Strings (n + m − 2·LCS).",
    ),
),
dict(
    id="best-time-to-buy-and-sell-stock-with-cooldown",
    title="Best Time to Buy and Sell Stock with Cooldown",
    difficulty="Medium",
    pattern="2-D DP / State Machine",
    leetcode="https://leetcode.com/problems/best-time-to-buy-and-sell-stock-with-cooldown/",
    neetcode="https://neetcode.io/problems/buy-and-sell-crypto-with-cooldown",
    entry="maxProfit",
    description=r"""
`prices[i]` is a stock's price on day `i`. You may trade as many times as you like, subject to:

- you hold at most one share at a time (sell before buying again);
- after you **sell**, you must wait one full day (a cooldown) before you may buy again.

Return the maximum total profit.

**Constraints**

- `1 <= len(prices) <= 5000`
- `0 <= prices[i] <= 1000`

**Example 1:** `prices = [1, 2, 3, 0, 2]` → `3` (buy 1, sell 2, cool down, buy 0, sell 2)

**Example 2:** `prices = [1]` → `0`
""",
    starter='''class Solution:
    def maxProfit(self, prices: List[int]) -> int:
        pass
''',
    solution='''class Solution:
    def maxProfit(self, prices):
        hold, sold, rest = float("-inf"), 0, 0
        for p in prices:
            hold, sold, rest = max(hold, rest - p), hold + p, max(rest, sold)
        return max(sold, rest)
''',
    tests=[
        [[1, 2, 3, 0, 2]],
        [[1]],
        [[2, 1]],
        [[1, 2]],
        [[1, 2, 4]],
        [[6, 1, 3, 2, 4, 7]],
        [[1, 4, 2, 7]],
        [[5, 4, 3, 2, 1]],
        [[3, 3, 5, 0, 0, 3, 1, 4]],
        [[1, 2, 1, 2, 1, 2, 1, 2]],
        [_ints(100, 0, 50)],
        [_ints(5000, 0, 1000)],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def maxProfit(self, prices):
        return sum(max(0, b - a) for a, b in zip(prices, prices[1:]))
''',
        '''class Solution:
    def maxProfit(self, prices):
        best, lo = 0, float("inf")
        for p in prices:
            lo = min(lo, p)
            best = max(best, p - lo)
        return best
''',
    ],
    guide=dict(
        prereqs="Best Time to Buy and Sell Stock I/II; lesson *Counting knapsacks and state machines*.",
        intuition=r"""
The extra index is a **mode**: at the end of each day you are either *holding* a share, have
*just sold* (so tomorrow is a forced rest), or are *resting* free to buy. Track the best profit in
each mode; each day's transitions are tiny.
""",
        hints=[
            "Summing every upward move ignores the cooldown (`[1,2,3,0,2]` gives 4, not 3).",
            "Model the day-end states: hold, sold (today), rest (not holding, may buy).",
            "hold' = max(hold, rest − p); sold' = hold + p; rest' = max(rest, sold). Answer max(sold, rest).",
        ],
        brute_force="On each day choose buy/sell/wait recursively: O(3ⁿ)-ish branching, hopeless at 5000 days.",
        approach=r"""
```mermaid
stateDiagram-v2
    rest --> rest: wait
    rest --> hold: buy (-p)
    hold --> hold: wait
    hold --> sold: sell (+p)
    sold --> rest: cooldown
```

**State:** `(day, mode)`. **Base:** before day 0: `hold = −∞`, `sold = rest = 0`.

Dry run `[1, 2, 3, 0, 2]`:

| day | p | hold | sold | rest |
|---|---|---|---|---|
| 0 | 1 | −1 | −∞ | 0 |
| 1 | 2 | −1 | 1 | 0 |
| 2 | 3 | −1 | 2 | 1 |
| 3 | 0 | 1 | −1 | 2 |
| 4 | 2 | 1 | **3** | 2 |

Answer `max(sold, rest) = 3`. All three updates must use the **previous** day's values (tuple assignment does this).
""",
        complexity="Time O(n), space O(1).",
        pitfalls=r"""
- Updating `rest` before `hold` in separate statements leaks today's values into today's buy.
- `hold` must start at −∞ (or `-prices[0]` on day 0), not 0.
""",
        follow_up="The same state-machine template solves the fee variant, at-most-k-transactions (state = (day, k, holding)), and Stock III.",
    ),
),
dict(
    id="coin-change-ii",
    title="Coin Change II",
    difficulty="Medium",
    pattern="2-D DP / Unbounded Knapsack (counting)",
    leetcode="https://leetcode.com/problems/coin-change-ii/",
    neetcode="https://neetcode.io/problems/coin-change-ii",
    entry="change",
    description=r"""
Given an `amount` and distinct coin denominations `coins` (each available in unlimited supply),
count the number of **combinations** — multisets, so order doesn't matter — of coins that add up to
exactly `amount`. `1 + 2` and `2 + 1` are the same combination. Python ints are unbounded; return
the exact count.

**Constraints**

- `0 <= amount <= 5000`
- `1 <= len(coins) <= 300`, `1 <= coins[i] <= 5000`, all distinct

**Example 1:** `amount = 5, coins = [1, 2, 5]` → `4` (5, 2+2+1, 2+1+1+1, 1×5)

**Example 2:** `amount = 3, coins = [2]` → `0`

**Example 3:** `amount = 0, coins = [7]` → `1` (the empty combination)
""",
    starter='''class Solution:
    def change(self, amount: int, coins: List[int]) -> int:
        pass
''',
    solution='''class Solution:
    def change(self, amount, coins):
        ways = [1] + [0] * amount
        for c in coins:                       # coins OUTER -> combinations, not permutations
            for a in range(c, amount + 1):
                ways[a] += ways[a - c]
        return ways[amount]
''',
    tests=[
        [5, [1, 2, 5]],
        [3, [2]],
        [0, [7]],
        [10, [10]],
        [1, [2, 3]],
        [4, [1, 2, 3]],
        [12, [3, 5, 7]],
        [100, [1, 5, 10, 25, 50]],
        [500, [3, 5, 7, 8, 9, 10, 11]],
        [5000, [11, 24, 37, 50, 63, 76, 89, 102]],
        [5000, list(range(50, 350))],
        [4681, [2, 7, 13, 19, 31, 47, 61, 97, 101, 199]],
    ],
    examples=3,
    wrong_solutions=[
        '''class Solution:
    def change(self, amount, coins):
        ways = [1] + [0] * amount
        for a in range(1, amount + 1):
            for c in coins:
                if c <= a:
                    ways[a] += ways[a - c]
        return ways[amount]
''',
        '''class Solution:
    def change(self, amount, coins):
        ways = [1] + [0] * amount
        for c in coins:
            for a in range(amount, c - 1, -1):
                ways[a] += ways[a - c]
        return ways[amount]
''',
    ],
    guide=dict(
        prereqs="Coin Change; lesson *Counting knapsacks and state machines*.",
        intuition=r"""
To count each multiset once, fix an order in which coin types are *considered*: first decide how
many of coin 0 to use, then coin 1, and so on. State `(i, a)` = ways to make `a` using only the
first `i` coin types: either use none of coin `i` (`ways(i-1, a)`) or use at least one
(`ways(i, a - c_i)`).
""",
        hints=[
            "Looping over amounts outside and coins inside counts 1+2 and 2+1 separately. Why?",
            "Let ways(i, a) = combinations of the first i coin types making a.",
            "ways(i, a) = ways(i-1, a) + ways(i, a - c_i). In 1-D: for each coin, for a from c up: ways[a] += ways[a-c].",
        ],
        brute_force="Recurse over coin index and remaining amount, trying 0, 1, 2, … copies: exponential without memo.",
        approach=r"""
**State:** `ways(i, a)`. **Base:** `ways(·, 0) = 1`, `ways(0, a>0) = 0`.
**Recurrence:** `ways(i, a) = ways(i-1, a) + ways(i, a - c_i)`. **Answer:** `ways(n, amount)`.

`amount = 5, coins = [1, 2, 5]`:

| coins used \ a | 0 | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|---|
| none | 1 | 0 | 0 | 0 | 0 | 0 |
| {1} | 1 | 1 | 1 | 1 | 1 | 1 |
| {1,2} | 1 | 1 | 2 | 2 | 3 | 3 |
| {1,2,5} | 1 | 1 | 2 | 2 | 3 | **4** |

The 1-D loop iterates `a` **upward** because `ways(i, a - c)` is the *current* row (coin `i` may be reused).
""",
        complexity="Time O(len(coins) · amount), space O(amount).",
        pitfalls=r"""
- Swapping the loops counts **permutations** (that's Combination Sum IV).
- Iterating `a` downward allows each coin at most once (0/1) — undercounts.
- `amount = 0` → 1, not 0.
""",
        follow_up="Combination Sum IV (ordered — swap the loops on purpose). Bounded counts per coin → 0/1 expansion or sliding-window sums.",
    ),
),
dict(
    id="target-sum",
    title="Target Sum",
    difficulty="Medium",
    pattern="2-D DP / Subset Sum (counting)",
    leetcode="https://leetcode.com/problems/target-sum/",
    neetcode="https://neetcode.io/problems/target-sum",
    entry="findTargetSumWays",
    description=r"""
Put a `+` or `-` sign in front of every number in `nums` (all numbers must be used, in order) and
evaluate the expression. Count how many of the `2^n` sign assignments evaluate to `target`.

**Constraints**

- `1 <= len(nums) <= 20`
- `0 <= nums[i] <= 1000`, `sum(nums) <= 1000`
- `-1000 <= target <= 1000`

**Example 1:** `nums = [1, 1, 1, 1, 1], target = 3` → `5` (choose which one of the five gets `-`)

**Example 2:** `nums = [1], target = 1` → `1`
""",
    starter='''class Solution:
    def findTargetSumWays(self, nums: List[int], target: int) -> int:
        pass
''',
    solution='''class Solution:
    def findTargetSumWays(self, nums, target):
        ways = {0: 1}
        for x in nums:
            nxt = {}
            for s, c in ways.items():
                nxt[s + x] = nxt.get(s + x, 0) + c
                nxt[s - x] = nxt.get(s - x, 0) + c
            ways = nxt
        return ways.get(target, 0)
''',
    tests=[
        [[1, 1, 1, 1, 1], 3],
        [[1], 1],
        [[1], 2],
        [[1, 1, 1], 2],
        [[0, 0, 0, 0, 0, 0, 0, 0, 1], 1],
        [[0], 0],
        [[2, 3, 5], 0],
        [[7, 9, 3, 8, 0, 2, 4, 8, 3, 9], 0],
        [[100], -200],
        [[1, 2, 3, 4, 5], -15],
        [[1] * 20, 0],
        [_ints(20, 0, 50), 7],
        [[_R.randint(1, 50) * 2 for _ in range(20)], 40],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def findTargetSumWays(self, nums, target):
        P = (sum(nums) + target) // 2
        if P < 0:
            return 0
        dp = [1] + [0] * P
        for x in nums:
            for s in range(P, x - 1, -1):
                dp[s] += dp[s - x]
        return dp[P]
''',
        '''class Solution:
    def findTargetSumWays(self, nums, target):
        total = sum(nums)
        if (total + target) % 2 or abs(target) > total:
            return 0
        P = (total + target) // 2
        dp = [1] + [0] * P
        for x in nums:
            if x == 0:
                continue
            for s in range(P, x - 1, -1):
                dp[s] += dp[s - x]
        return dp[P]
''',
    ],
    guide=dict(
        prereqs="Partition Equal Subset Sum; lesson *Counting knapsacks and state machines*.",
        intuition=r"""
Process numbers left to right, keeping a map **running sum → number of ways** to reach it. Each
number splits every entry into `s + x` and `s − x`. Sums stay within `[-1000, 1000]`, so the map
has at most 2001 keys — tiny compared to 2²⁰ sign patterns.

Algebra gives a second view: if `P` is the sum of the `+` numbers, then `P − (total − P) = target`,
so `P = (total + target) / 2` — a **subset-sum count**.
""",
        hints=[
            "Brute force is 2ⁿ ≈ 10⁶ for n = 20 — borderline; many partial sums repeat.",
            "State (index, running sum). How many distinct running sums can there be?",
            "Either DP over a dict of sums, or count subsets summing to (total + target) / 2 (check parity and range!).",
        ],
        brute_force="Recurse `go(i, s) = go(i+1, s+x) + go(i+1, s−x)`: exactly 2ⁿ leaves — about a million calls at n = 20, several seconds in the browser.",
        approach=r"""
**State:** `ways_i[s]` = sign assignments of the first `i` numbers summing to `s`.
**Recurrence:** `ways_{i}[s] = ways_{i-1}[s − x] + ways_{i-1}[s + x]`. **Base:** `ways_0 = {0: 1}`.

`[1, 1, 1, 1, 1]`, target 3:

| after i | ways |
|---|---|
| 0 | {0:1} |
| 1 | {1:1, −1:1} |
| 2 | {2:1, 0:2, −2:1} |
| 3 | {3:1, 1:3, −1:3, −3:1} |
| 4 | {4:1, 2:4, 0:6, −2:4, −4:1} |
| 5 | {5:1, **3:5**, 1:10, …} |

Subset-sum route: `total = 5`, `P = (5+3)/2 = 4` → number of 4-element subsets of five ones = C(5,4) = 5.
""",
        complexity="Time O(n · S) where S ≤ 2·sum + 1; space O(S).",
        pitfalls=r"""
- Subset-sum route: if `total + target` is odd or `|target| > total`, the answer is 0 — skipping this check gives garbage.
- Zeros double the count (`+0` and `−0` are different assignments); don't skip them.
""",
        follow_up="Last Stone Weight II; Ones and Zeroes; counting with a fixed number of minus signs (3-D state).",
    ),
),
dict(
    id="interleaving-string",
    title="Interleaving String",
    difficulty="Medium",
    pattern="2-D DP / Strings",
    leetcode="https://leetcode.com/problems/interleaving-string/",
    neetcode="https://neetcode.io/problems/interleaving-string",
    entry="isInterleave",
    description=r"""
Decide whether `s3` can be formed by **interleaving** `s1` and `s2`: walking through `s3` from left
to right, each character is taken from either the front of what remains of `s1` or the front of what
remains of `s2`, and in the end both are fully used. (The relative order inside `s1` and inside `s2`
is preserved.)

**Constraints**

- `0 <= len(s1), len(s2) <= 100`, `0 <= len(s3) <= 200`
- lowercase letters

**Example 1:** `s1 = "aabcc", s2 = "dbbca", s3 = "aadbbcbcac"` → `True`

**Example 2:** `s1 = "aabcc", s2 = "dbbca", s3 = "aadbbbaccc"` → `False`

**Example 3:** `s1 = "", s2 = "", s3 = ""` → `True`
""",
    starter='''class Solution:
    def isInterleave(self, s1: str, s2: str, s3: str) -> bool:
        pass
''',
    solution='''class Solution:
    def isInterleave(self, s1, s2, s3):
        n, m = len(s1), len(s2)
        if n + m != len(s3):
            return False
        ok = [False] * (m + 1)           # ok[j]: s1[:i] and s2[:j] interleave to s3[:i+j]
        for i in range(n + 1):
            for j in range(m + 1):
                if i == 0 and j == 0:
                    ok[j] = True
                    continue
                c = s3[i + j - 1]
                from_s1 = i > 0 and ok[j] and s1[i - 1] == c
                from_s2 = j > 0 and ok[j - 1] and s2[j - 1] == c
                ok[j] = from_s1 or from_s2
        return ok[m]
''',
    tests=[
        ["aabcc", "dbbca", "aadbbcbcac"],
        ["aabcc", "dbbca", "aadbbbaccc"],
        ["", "", ""],
        ["", "abc", "abc"],
        ["abc", "", "abd"],
        ["a", "b", "ab"],
        ["a", "b", "ba"],
        ["a", "b", "a"],
        ["ab", "ab", "abab"],
        ["aa", "ab", "aaba"],
        ["a" * 100, "a" * 99 + "b", "a" * 199 + "b"],
        ["a" * 100, "a" * 100, "a" * 199 + "b"],
        ["ab" * 50, "ba" * 50, "".join(p + q for p, q in zip("ab" * 50, "ba" * 50))],
    ],
    examples=3,
    wrong_solutions=[
        '''class Solution:
    def isInterleave(self, s1, s2, s3):
        if len(s1) + len(s2) != len(s3):
            return False
        i = j = 0
        for c in s3:
            if i < len(s1) and s1[i] == c:
                i += 1
            elif j < len(s2) and s2[j] == c:
                j += 1
            else:
                return False
        return True
''',
        '''class Solution:
    def isInterleave(self, s1, s2, s3):
        return sorted(s1 + s2) == sorted(s3)
''',
    ],
    guide=dict(
        prereqs="Longest Common Subsequence (same two-prefix table shape).",
        intuition=r"""
After consuming `i` characters of `s1` and `j` of `s2`, you have produced exactly `s3[:i+j]`. So
the pair `(i, j)` is the whole state; the next character of `s3` must come from `s1[i]` or `s2[j]`.
When both match, greedy has to guess — DP explores both.
""",
        hints=[
            "Check `len(s1) + len(s2) == len(s3)` first.",
            "State (i, j): can s1[:i] and s2[:j] interleave into s3[:i+j]?",
            "ok[i][j] = (ok[i-1][j] and s1[i-1]==s3[i+j-1]) or (ok[i][j-1] and s2[j-1]==s3[i+j-1]).",
        ],
        brute_force="Recurse choosing s1 or s2 whenever both match: up to C(n+m, n) paths — with all-`a` strings ending in a mismatch, about 10⁵⁹ for n = m = 100.",
        approach=r"""
**State:** `ok[i][j]`. **Base:** `ok[0][0] = True`. **Order:** row-major. **Answer:** `ok[n][m]`.

`s1 = "ab"`, `s2 = "cd"`, `s3 = "acbd"`:

| i \ j | 0 (∅) | 1 (c) | 2 (d) |
|---|---|---|---|
| 0 (∅) | T | F | F |
| 1 (a) | T | T | F |
| 2 (b) | F | T | **T** |

Path: a (s1) → c (s2) → b (s1) → d (s2). A single row suffices: `ok[j]` holds the row above (`ok[i-1][j]`) until overwritten, `ok[j-1]` already holds the current row.
""",
        complexity="Time O(n·m), space O(m).",
        pitfalls="- Greedy \"prefer s1\" fails on Example 1.\n- Indexing s3 at `i + j - 1`, not `i + j`.\n- Empty strings are legal inputs.",
        follow_up="Can you also output which characters came from s1? Keep parent pointers.",
    ),
),
dict(
    id="distinct-subsequences",
    title="Distinct Subsequences",
    difficulty="Hard",
    pattern="2-D DP / Strings",
    leetcode="https://leetcode.com/problems/distinct-subsequences/",
    neetcode="https://neetcode.io/problems/count-subsequences",
    entry="numDistinct",
    description=r"""
Count the number of different ways to pick positions in `s` (keeping their order) so that the picked
characters spell exactly `t`. Two ways differ if they use a different set of positions. Python ints
are unbounded; return the exact count.

**Constraints**

- `1 <= len(s), len(t) <= 1000`
- English letters

**Example 1:** `s = "rabbbit", t = "rabbit"` → `3` (drop any one of the three `b`s)

**Example 2:** `s = "babgbag", t = "bag"` → `5`
""",
    starter='''class Solution:
    def numDistinct(self, s: str, t: str) -> int:
        pass
''',
    solution='''class Solution:
    def numDistinct(self, s, t):
        m = len(t)
        if m > len(s):
            return 0
        ways = [1] + [0] * m            # ways[j]: ways to form t[:j] from the prefix of s seen so far
        for ch in s:
            for j in range(m, 0, -1):   # downwards so each s-char is used once per subsequence
                if t[j - 1] == ch:
                    ways[j] += ways[j - 1]
        return ways[m]
''',
    tests=[
        ["rabbbit", "rabbit"],
        ["babgbag", "bag"],
        ["a", "a"],
        ["a", "b"],
        ["abc", "abcd"],
        ["aaa", "a"],
        ["aaaa", "aa"],
        ["abcabc", "abc"],
        ["xyz", "xyz"],
        ["a" * 30, "a" * 15],
        [_s(1000, "ab"), "abba"],
        [_s(1000, "abc"), _s(8, "abc")],
        ["a" * 500 + "b" * 500, "ab"],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def numDistinct(self, s, t):
        m = len(t)
        ways = [1] + [0] * m
        for ch in s:
            for j in range(1, m + 1):
                if t[j - 1] == ch:
                    ways[j] += ways[j - 1]
        return ways[m]
''',
        '''class Solution:
    def numDistinct(self, s, t):
        n, m = len(s), len(t)
        dp = [[0] * (m + 1) for _ in range(n + 1)]
        for i in range(n + 1):
            dp[i][0] = 1
        for i in range(1, n + 1):
            for j in range(1, m + 1):
                if s[i - 1] == t[j - 1]:
                    dp[i][j] = dp[i - 1][j - 1]
                else:
                    dp[i][j] = dp[i - 1][j]
        return dp[n][m]
''',
    ],
    guide=dict(
        prereqs="Longest Common Subsequence.",
        intuition=r"""
Walk through `s`. For each character, every way to build `t[:j]` either **ignores** this character
or — if it equals `t[j-1]` — **uses** it to extend a way of building `t[:j-1]`. Counting DP adds
the two options instead of taking a max.
""",
        hints=[
            "Define D[i][j] = ways to form t[:j] from s[:i]. What is D[i][0]?",
            "If s[i-1] != t[j-1] you must skip s[i-1]. If they are equal you may skip it or use it.",
            "D[i][j] = D[i-1][j] + (D[i-1][j-1] if s[i-1] == t[j-1] else 0). D[i][0] = 1.",
        ],
        brute_force="Enumerate all C(n, m) position subsets, or recurse use/skip per character without memo: exponential (C(1000, 4) ≈ 4·10¹⁰ already for t of length 4).",
        approach=r"""
**State:** `D[i][j]`. **Base:** `D[i][0] = 1` (empty `t` — one way: pick nothing), `D[0][j>0] = 0`.
**Recurrence:** above. **Answer:** `D[n][m]`.

`s = "babgbag"`, `t = "bag"` (columns: ∅, b, ba, bag):

| s prefix | ∅ | b | ba | bag |
|---|---|---|---|---|
| ∅ | 1 | 0 | 0 | 0 |
| b | 1 | 1 | 0 | 0 |
| ba | 1 | 1 | 1 | 0 |
| bab | 1 | 2 | 1 | 0 |
| babg | 1 | 2 | 1 | 1 |
| babgb | 1 | 3 | 1 | 1 |
| babgba | 1 | 3 | 4 | 1 |
| babgbag | 1 | 3 | 4 | **5** |

One row: iterate `j` **downward** so `ways[j-1]` is still the previous row's value.
""",
        complexity="Time O(n·m), space O(m).",
        pitfalls=r"""
- Upward `j` loop lets one character of `s` play two roles (`"aaa"`/`"aa"` would give too much).
- On a match you must **add** the skip option, not replace it.
""",
        follow_up="Distinct Subsequences II (count distinct subsequence *strings*), Number of Matching Subsequences.",
    ),
),
dict(
    id="edit-distance",
    title="Edit Distance",
    difficulty="Medium",
    pattern="2-D DP / Strings",
    leetcode="https://leetcode.com/problems/edit-distance/",
    neetcode="https://neetcode.io/problems/edit-distance",
    entry="minDistance",
    description=r"""
You can transform a string with three single-character operations: **insert** a character,
**delete** a character, or **replace** one character with another. Return the minimum number of
operations to turn `word1` into `word2` (the Levenshtein distance).

**Constraints**

- `0 <= len(word1), len(word2) <= 500`
- lowercase letters

**Example 1:** `word1 = "horse", word2 = "ros"` → `3` (horse → rorse → rose → ros)

**Example 2:** `word1 = "intention", word2 = "execution"` → `5`
""",
    starter='''class Solution:
    def minDistance(self, word1: str, word2: str) -> int:
        pass
''',
    solution='''class Solution:
    def minDistance(self, word1, word2):
        m = len(word2)
        prev = list(range(m + 1))               # row for empty prefix of word1
        for i, a in enumerate(word1, 1):
            cur = [i] + [0] * m
            for j in range(1, m + 1):
                if a == word2[j - 1]:
                    cur[j] = prev[j - 1]
                else:
                    cur[j] = 1 + min(prev[j - 1], prev[j], cur[j - 1])
            prev = cur
        return prev[m]
''',
    tests=[
        ["horse", "ros"],
        ["intention", "execution"],
        ["", ""],
        ["", "abc"],
        ["abc", ""],
        ["a", "a"],
        ["a", "b"],
        ["ab", "ba"],
        ["kitten", "sitting"],
        ["sunday", "saturday"],
        ["abcdef", "azced"],
        [_s(300, "abcd"), _s(300, "abcd")],
        [_s(500, "abcdefghij"), _s(450, "abcdefghij")],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def minDistance(self, word1, word2):
        diff = sum(a != b for a, b in zip(word1, word2))
        return diff + abs(len(word1) - len(word2))
''',
        '''class Solution:
    def minDistance(self, word1, word2):
        n, m = len(word1), len(word2)
        prev = [0] * (m + 1)
        for i in range(1, n + 1):
            cur = [0] * (m + 1)
            for j in range(1, m + 1):
                cur[j] = prev[j - 1] + 1 if word1[i - 1] == word2[j - 1] else max(prev[j], cur[j - 1])
            prev = cur
        return max(n, m) - prev[m]
''',
    ],
    guide=dict(
        prereqs="Longest Common Subsequence; lesson *String DP*.",
        intuition=r"""
Look at the last characters of the two prefixes. If equal, no operation is needed for them. Otherwise
the last operation on an optimal script either **replaces** `a→b` (both shrink), **deletes** `a`
(word1 shrinks) or **inserts** `b` (word2 shrinks). Take the cheapest plus one.
""",
        hints=[
            "Position-by-position comparison fails as soon as one insertion shifts everything (`horse`/`ros`).",
            "E[i][j] = distance between word1[:i] and word2[:j]. E[i][0] = i, E[0][j] = j.",
            "Match: E[i-1][j-1]. Else 1 + min(E[i-1][j-1] (replace), E[i-1][j] (delete), E[i][j-1] (insert)).",
        ],
        brute_force="Try all three operations recursively at every mismatch: O(3^(n+m)).",
        approach=r"""
**State:** `E[i][j]`. **Base:** first row `0..m`, first column `0..n`.
**Recurrence:** as above. **Order:** row-major. **Answer:** `E[n][m]`.

`"horse"` → `"ros"`:

| | ∅ | r | o | s |
|---|---|---|---|---|
| ∅ | 0 | 1 | 2 | 3 |
| h | 1 | 1 | 2 | 3 |
| o | 2 | 2 | 1 | 2 |
| r | 3 | 2 | 2 | 2 |
| s | 4 | 3 | 3 | 2 |
| e | 5 | 4 | 4 | **3** |

Reading moves back from the bottom-right recovers an optimal script (diagonal = keep/replace, up = delete, left = insert).
""",
        complexity="Time O(n·m), space O(m) with two rows.",
        pitfalls=r"""
- Base row/column must be `0, 1, 2, …` (deleting/inserting everything), not zeros.
- `n + m − 2·LCS` is the distance **without** replacement; it overestimates here.
""",
        follow_up="One Edit Distance (O(n) check), weighted operations, Damerau distance (adjacent transpositions), Hirschberg for O(min) space with reconstruction.",
    ),
),
dict(
    id="burst-balloons",
    title="Burst Balloons",
    difficulty="Hard",
    pattern="2-D DP / Interval",
    leetcode="https://leetcode.com/problems/burst-balloons/",
    neetcode="https://neetcode.io/problems/burst-balloons",
    entry="maxCoins",
    description=r"""
Balloons in a row carry numbers `nums[i]`. Bursting balloon `i` earns
`left × nums[i] × right` coins, where `left` and `right` are the numbers on the balloons
**currently** adjacent to it (treat a missing neighbour past either end as `1`). After a burst the
neighbours become adjacent. Burst all balloons in the best order and return the maximum coins.

**Constraints**

- `1 <= len(nums) <= 300`
- `0 <= nums[i] <= 100`

**Example 1:** `nums = [3, 1, 5, 8]` → `167`
(burst 1: 3·1·5=15, then 5: 3·5·8=120, then 3: 1·3·8=24, then 8: 1·8·1=8)

**Example 2:** `nums = [1, 5]` → `10`
""",
    starter='''class Solution:
    def maxCoins(self, nums: List[int]) -> int:
        pass
''',
    solution='''class Solution:
    def maxCoins(self, nums):
        a = [1] + nums + [1]
        n = len(a)
        dp = [[0] * n for _ in range(n)]      # dp[l][r]: best for balloons strictly between l and r
        for length in range(2, n):
            for l in range(0, n - length):
                r = l + length
                al, ar = a[l], a[r]
                row_l = dp[l]
                best = 0
                for k in range(l + 1, r):     # k = LAST balloon burst inside (l, r)
                    v = row_l[k] + dp[k][r] + al * a[k] * ar
                    if v > best:
                        best = v
                row_l[r] = best
        return dp[0][n - 1]
''',
    tests=[
        [[3, 1, 5, 8]],
        [[1, 5]],
        [[7]],
        [[0]],
        [[0, 0, 0]],
        [[2, 3]],
        [[9, 76, 64, 21]],
        [[1, 2, 3, 4, 5]],
        [[5, 4, 3, 2, 1]],
        [[8, 2, 6, 8, 9, 8, 1, 4, 1, 5, 3, 0, 7, 7, 0, 4, 2]],
        [_ints(40, 0, 100)],
        [_ints(120, 0, 100)],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def maxCoins(self, nums):
        a = list(nums)
        total = 0
        while a:
            k = min(range(len(a)), key=lambda i: a[i])
            left = a[k - 1] if k > 0 else 1
            right = a[k + 1] if k + 1 < len(a) else 1
            total += left * a[k] * right
            a.pop(k)
        return total
''',
        '''class Solution:
    def maxCoins(self, nums):
        a = [1] + nums + [1]
        n = len(a)
        dp = [[0] * n for _ in range(n)]
        for length in range(2, n):
            for l in range(0, n - length):
                r = l + length
                dp[l][r] = max(dp[l][k] + dp[k][r] + a[k - 1] * a[k] * a[k + 1] for k in range(l + 1, r))
        return dp[0][n - 1]
''',
    ],
    guide=dict(
        prereqs="Lesson *Interval DP: matrix chains and burst balloons*.",
        intuition=r"""
Choosing the **first** balloon to burst is messy — afterwards its neighbours change. Flip it: choose
the **last** balloon `k` to burst inside an open interval `(l, r)`. When `k` goes last, everything
else in `(l, r)` is already gone, so its neighbours are exactly `l` and `r`, and the left part
`(l, k)` and right part `(k, r)` are independent subproblems.
""",
        hints=[
            "Pad the array with 1 at both ends so boundaries need no special case.",
            "Instead of which balloon to burst first, ask which one is burst last within an interval.",
            "dp[l][r] = max over l<k<r of dp[l][k] + dp[k][r] + a[l]·a[k]·a[r]; fill by increasing interval length.",
        ],
        brute_force="Try every burst order: n! orders (memo over remaining-sets is 2ⁿ). Even n = 12 is 479 million orders.",
        approach=r"""
**State:** `dp[l][r]` = max coins from bursting all balloons strictly between `l` and `r` (padded indices).
**Recurrence:** last-burst split as above. **Base:** `dp[l][l+1] = 0` (nothing inside).
**Order:** increasing `r − l`. **Answer:** `dp[0][n+1]`.

`[3, 1, 5, 8]` → padded `[1, 3, 1, 5, 8, 1]`. A few cells:

| interval (values) | best last k | dp |
|---|---|---|
| (1,·,1) around 3 | 3 | 1·3·1 = 3 |
| (3,·,5) around 1 | 1 | 3·1·5 = 15 |
| (3, 1 5, 8) | 5 last: dp(3..5)=15 + 3·5·8 = 135 | 135 |
| whole (1 … 1) | 8 last: dp(1..8)=159 + 1·8·1 | **167** |
""",
        complexity="Time O(n³) ≈ n³/6 inner steps (4.5·10⁶ at n = 300), space O(n²).",
        pitfalls=r"""
- Using the **original** neighbours `a[k-1]·a[k]·a[k+1]` is wrong — neighbours change as balloons pop.
- Greedy "pop the smallest first" fails on Example 1.
- Iterate by interval length (or `l` descending, `r` ascending) so subintervals are ready.
""",
        follow_up="Matrix Chain Multiplication (Goodrich §13.3.1), Minimum Cost to Cut a Stick, Strange Printer, Remove Boxes.",
    ),
),
dict(
    id="regular-expression-matching",
    title="Regular Expression Matching",
    difficulty="Hard",
    pattern="2-D DP / Strings",
    leetcode="https://leetcode.com/problems/regular-expression-matching/",
    neetcode="https://neetcode.io/problems/regular-expression-matching",
    entry="isMatch",
    description=r"""
Implement a tiny regular-expression matcher. The pattern `p` may contain lowercase letters and two
special symbols:

- `.` matches any single character;
- `*` means *zero or more copies of the element right before it* (every `*` is guaranteed to follow a
  letter or `.`).

The match must cover the **entire** string `s`, not just a part of it. Return `True` or `False`.
(Please don't just call Python's `re` module — the point is to build the DP.)

**Constraints**

- `1 <= len(s) <= 20`, `1 <= len(p) <= 20`
- `s` has lowercase letters; `p` has lowercase letters, `.` and `*`

**Example 1:** `s = "aa", p = "a"` → `False`

**Example 2:** `s = "aa", p = "a*"` → `True`

**Example 3:** `s = "aab", p = "c*a*b"` → `True` (`c*` matches nothing)
""",
    starter='''class Solution:
    def isMatch(self, s: str, p: str) -> bool:
        pass
''',
    solution='''class Solution:
    def isMatch(self, s, p):
        n, m = len(s), len(p)
        # dp[i][j]: does s[i:] match p[j:] ?
        dp = [[False] * (m + 1) for _ in range(n + 1)]
        dp[n][m] = True
        for i in range(n, -1, -1):
            for j in range(m - 1, -1, -1):
                first = i < n and p[j] in (s[i], ".")
                if j + 1 < m and p[j + 1] == "*":
                    dp[i][j] = dp[i][j + 2] or (first and dp[i + 1][j])
                else:
                    dp[i][j] = first and dp[i + 1][j + 1]
        return dp[0][0]
''',
    tests=[
        ["aa", "a"],
        ["aa", "a*"],
        ["aab", "c*a*b"],
        ["ab", ".*"],
        ["mississippi", "mis*is*p*."],
        ["mississippi", "mis*is*ip*."],
        ["a", "ab*"],
        ["ab", ".*c"],
        ["aaa", "a*a"],
        ["aaa", "ab*a*c*a"],
        ["a", ".*..a*"],
        ["bbbba", ".*a*a"],
        ["aaaaaaaaaaaaaaaaaaab", "a*a*a*a*a*a*a*a*a*c"],
        ["aaaaaaaaaaaaaaaaaaaa", "a*a*a*a*a*a*a*a*a*a"],
    ],
    examples=3,
    wrong_solutions=[
        '''from fnmatch import fnmatchcase
class Solution:
    def isMatch(self, s, p):
        return fnmatchcase(s, p.replace(".", "?"))
''',
        '''class Solution:
    def isMatch(self, s, p):
        i = j = 0
        while j < len(p):
            if j + 1 < len(p) and p[j + 1] == "*":
                while i < len(s) and p[j] in (s[i], "."):
                    i += 1
                j += 2
            else:
                if i >= len(s) or p[j] not in (s[i], "."):
                    return False
                i += 1
                j += 1
        return i == len(s)
''',
    ],
    guide=dict(
        prereqs="Edit Distance / LCS table shape; lesson *String DP*.",
        intuition=r"""
State = how much of `s` and of `p` remain. Without `*`, the first characters must match and you move
both pointers. With `x*` at the front of the pattern you have exactly two options: **skip** `x*`
entirely (zero copies), or — if the current character matches `x` — **consume one character** of `s`
and stay on `x*` (more copies may follow).
""",
        hints=[
            "Greedy `*` (eat as much as possible) fails on `\"aaa\"` vs `\"a*a\"`.",
            "Let dp[i][j] = s[i:] matches p[j:]. Look at whether p[j+1] is '*'.",
            "Star: dp[i][j] = dp[i][j+2] or (first_match and dp[i+1][j]). Else: first_match and dp[i+1][j+1].",
        ],
        brute_force=r"""
Plain backtracking over the two choices for each `x*` explodes on patterns like `a*a*a*…a*c` against
`aaaa…ab`: every way of distributing the `a`s among the stars is tried before failing — exponential.
""",
        approach=r"""
**State:** `dp[i][j]` — suffix `s[i:]` matches suffix `p[j:]`.
**Base:** `dp[n][m] = True` (both empty); `dp[i][m] = False` for `i < n`.
**Order:** `i` from `n` down to 0, `j` from `m − 1` down to 0. **Answer:** `dp[0][0]`.

`s = "aab"`, `p = "c*a*b"` (rows i = suffix of s, columns j = suffix of p):

| | c*a*b | *a*b | a*b | *b | b | ∅ |
|---|---|---|---|---|---|---|
| aab | **T** | – | T | – | F | F |
| ab | T | – | T | – | F | F |
| b | T | – | T | – | T | F |
| ∅ | F | – | F | – | F | T |

(`–` cells start on a `*` and are never queried.) `c*` is skipped (column jump by 2), `a*` eats two `a`s, `b` matches `b`.
""",
        complexity="Time O(n·m), space O(n·m) (O(m) with two rows).",
        pitfalls=r"""
- `*` binds to the **previous** element, not to anything: `a*` can be empty.
- Patterns like `a*` can match an empty string — the empty-`s` row isn't all False.
- Don't confuse with Wildcard Matching, where `*` alone matches any sequence.
""",
        follow_up="Wildcard Matching (glob `?`/`*`), adding `+` and `?` quantifiers, Thompson NFA simulation.",
    ),
),
]
