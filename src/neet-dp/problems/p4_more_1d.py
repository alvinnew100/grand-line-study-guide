import random

_R = random.Random(909)


def _ints(n, lo, hi):
    return [_R.randint(lo, hi) for _ in range(n)]


def _jobs(n, horizon, maxlen, maxprofit):
    starts = [_R.randint(1, horizon) for _ in range(n)]
    ends = [s + _R.randint(1, maxlen) for s in starts]
    profits = [_R.randint(1, maxprofit) for _ in range(n)]
    return [starts, ends, profits]


def _chain_words(n):
    words = set()
    while len(words) < n:
        w = "".join(_R.choice("abc") for _ in range(_R.randint(1, 10)))
        words.add(w)
        # add a few predecessors so chains exist
        while len(w) > 1 and _R.random() < 0.7:
            k = _R.randrange(len(w))
            w = w[:k] + w[k + 1:]
            words.add(w)
    return sorted(words, key=lambda w: _R.random())[:n]


PROBLEMS = [
dict(
    id="perfect-squares",
    title="Perfect Squares",
    difficulty="Medium",
    pattern="1-D DP / Unbounded Knapsack",
    leetcode="https://leetcode.com/problems/perfect-squares/",
    neetcode="https://neetcode.io/problems/perfect-squares",
    entry="numSquares",
    description=r"""
A perfect square is a whole number multiplied by itself: 1, 4, 9, 16, … Given a positive integer
`n`, return the smallest count of perfect squares whose sum is exactly `n`. The same square may be
used several times.

**Constraints**

- `1 <= n <= 10^4`

**Example 1:** `n = 12` → `3` (4 + 4 + 4)

**Example 2:** `n = 13` → `2` (4 + 9)
""",
    starter='''class Solution:
    def numSquares(self, n: int) -> int:
        pass
''',
    solution='''class Solution:
    def numSquares(self, n):
        dp = [0] + [n] * n                  # n ones always works
        k = 1
        while k * k <= n:
            sq = k * k
            for a in range(sq, n + 1):
                if dp[a - sq] + 1 < dp[a]:
                    dp[a] = dp[a - sq] + 1
            k += 1
        return dp[n]
''',
    tests=[[12], [13], [1], [2], [3], [4], [7], [18], [43], [48], [100], [999], [7168], [9999]],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def numSquares(self, n):
        count = 0
        while n:
            k = int(n ** 0.5)
            n -= k * k
            count += 1
        return count
''',
        '''class Solution:
    def numSquares(self, n):
        k = int(n ** 0.5)
        if k * k == n:
            return 1
        return 2 if n % 2 == 1 else 3
''',
    ],
    guide=dict(
        prereqs="Coin Change (this is Coin Change where the coins are 1, 4, 9, 16, …).",
        intuition=r"""
Treat every perfect square not larger than `n` as a coin you may reuse. The question "fewest squares
summing to `n`" is then exactly "fewest coins making amount `n`". Taking the biggest square first
(greedy) fails: `12 = 9 + 1 + 1 + 1` uses four squares, but `4 + 4 + 4` uses three.
""",
        hints=[
            "Try the greedy idea on n = 12. Does it give the best answer?",
            "Let dp[a] be the fewest squares that sum to a. Which square could be the last one used?",
            "dp[a] = 1 + min(dp[a - k*k]) over all k with k*k <= a; dp[0] = 0.",
        ],
        brute_force="Recursively try every square as the next one: `f(a) = 1 + min f(a - k²)`. Without storing results the same amounts are recomputed endlessly — exponential in n.",
        approach=r"""
**State:** `dp[a]` = fewest perfect squares summing to `a`.
**Recurrence:** `dp[a] = 1 + min(dp[a - s])` over squares `s ≤ a`.
**Base case:** `dp[0] = 0`. **Order:** amounts increasing. **Answer:** `dp[n]`.

| a | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| dp | 0 | 1 | 2 | 3 | 1 | 2 | 3 | 4 | 2 | 1 | 2 | 3 | **3** | **2** |

`dp[12] = 1 + min(dp[11], dp[8], dp[3]) = 1 + min(3, 2, 3) = 3`.
""",
        complexity="Time O(n·√n) — about 100 squares for n = 10⁴. Space O(n).",
        pitfalls="- Greedy largest-square-first is wrong (12, 18, 48 …).\n- Forgetting that 1 is a square, so an answer always exists.",
        follow_up="Lagrange's four-square theorem says the answer is never more than 4, which gives an O(√n) maths solution. BFS over remaining amounts also works (each square is an edge).",
    ),
),
dict(
    id="integer-break",
    title="Integer Break",
    difficulty="Medium",
    pattern="1-D DP",
    leetcode="https://leetcode.com/problems/integer-break/",
    neetcode="https://neetcode.io/problems/integer-break",
    entry="integerBreak",
    description=r"""
Split the integer `n` into a sum of **at least two** positive integers so that the product of those
parts is as large as possible. Return that largest product.

**Constraints**

- `2 <= n <= 58`

**Example 1:** `n = 2` → `1` (1 + 1, product 1)

**Example 2:** `n = 10` → `36` (3 + 3 + 4, product 36)
""",
    starter='''class Solution:
    def integerBreak(self, n: int) -> int:
        pass
''',
    solution='''class Solution:
    def integerBreak(self, n):
        best = [0] * (n + 1)          # best[i]: max product splitting i into >= 2 parts
        best[1] = 1
        for i in range(2, n + 1):
            for first in range(1, i):
                rest = i - first
                cand = first * max(rest, best[rest])   # keep rest whole, or split it further
                if cand > best[i]:
                    best[i] = cand
        return best[n]
''',
    tests=[[2], [10], [3], [4], [5], [6], [7], [8], [9], [11], [20], [35], [50], [58]],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def integerBreak(self, n):
        return (n // 2) * (n - n // 2)
''',
        '''class Solution:
    def integerBreak(self, n):
        best = [0] * (n + 1)
        best[1] = 1
        for i in range(2, n + 1):
            for first in range(1, i):
                best[i] = max(best[i], first * best[i - first])
        return best[n]
''',
    ],
    guide=dict(
        prereqs="Lesson *The DP framework*.",
        intuition=r"""
Decide the **first part** `first`. What remains, `rest = n − first`, can either stay as one part or
be split further — and if it is split, it should be split in the best possible way, which is the
same problem on a smaller number.
""",
        hints=[
            "Try every size for the first part.",
            "The remainder can be kept whole (value rest) or broken again (value best[rest]). Use the larger.",
            "best[i] = max over first of first * max(i - first, best[i - first]).",
        ],
        brute_force="Enumerate every way to write n as an ordered sum (there are 2ⁿ⁻¹ of them) and multiply. For n = 58 that is about 10¹⁷ sums.",
        approach=r"""
**State:** `best[i]` = largest product from splitting `i` into at least two parts.
**Recurrence:** `best[i] = max(first × max(i − first, best[i − first]))` for `first = 1 … i−1`.
**Base case:** `best[1] = 1`. **Order:** `i` increasing. **Answer:** `best[n]`.

| i | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|
| best | 1 | 2 | 4 | 6 | 9 | 12 | 18 | 27 | **36** |

`best[10]`: with `first = 3`, `rest = 7`, `max(7, best[7] = 12) = 12` → `3 × 12 = 36`.

The inner `max(rest, best[rest])` matters: `best[3] = 2` but the number 3 kept whole is worth 3.
""",
        complexity="Time O(n²), space O(n).",
        pitfalls="- Using only `best[rest]` forces the remainder to be split, which loses value for small remainders (2 and 3).\n- Splitting into two equal halves is not optimal (10 → 5·5 = 25 < 36).",
        follow_up="Maths shortcut: use as many 3s as possible, with a remainder of 1 turned into 2 + 2. Proving it is a good exercise.",
    ),
),
dict(
    id="ugly-number-ii",
    title="Ugly Number II",
    difficulty="Medium",
    pattern="1-D DP / Multiple Pointers",
    leetcode="https://leetcode.com/problems/ugly-number-ii/",
    entry="nthUglyNumber",
    description=r"""
Call a positive integer *ugly* when its only prime factors are 2, 3 and 5 (so it can be written as
`2^a · 3^b · 5^c`). By convention `1` is ugly. The ugly numbers in order begin
`1, 2, 3, 4, 5, 6, 8, 9, 10, 12, …` (7, 11, 13 and 14 are missing).

Return the `n`-th ugly number (1-indexed).

**Constraints**

- `1 <= n <= 1690`

**Example 1:** `n = 10` → `12`

**Example 2:** `n = 1` → `1`
""",
    starter='''class Solution:
    def nthUglyNumber(self, n: int) -> int:
        pass
''',
    solution='''class Solution:
    def nthUglyNumber(self, n):
        ugly = [1]
        i2 = i3 = i5 = 0                 # next ugly number to be multiplied by 2, 3, 5
        while len(ugly) < n:
            a, b, c = ugly[i2] * 2, ugly[i3] * 3, ugly[i5] * 5
            nxt = min(a, b, c)
            ugly.append(nxt)
            if nxt == a:
                i2 += 1
            if nxt == b:
                i3 += 1
            if nxt == c:
                i5 += 1
        return ugly[-1]
''',
    tests=[[10], [1], [2], [5], [6], [7], [11], [15], [50], [150], [500], [1352], [1690]],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def nthUglyNumber(self, n):
        ugly = [1]
        i2 = i3 = i5 = 0
        while len(ugly) < n:
            a, b, c = ugly[i2] * 2, ugly[i3] * 3, ugly[i5] * 5
            nxt = min(a, b, c)
            ugly.append(nxt)
            if nxt == a:
                i2 += 1
            elif nxt == b:
                i3 += 1
            else:
                i5 += 1
        return ugly[-1]
''',
        '''class Solution:
    def nthUglyNumber(self, n):
        x = count = 0
        while count < n:
            x += 1
            if x % 7 and x % 11 and x % 13:
                count += 1
        return x
''',
    ],
    guide=dict(
        prereqs="Merging sorted lists; lesson *From recursion to dynamic programming*.",
        intuition=r"""
Every ugly number except 1 is a **smaller ugly number times 2, 3 or 5**. So the sorted list of ugly
numbers is the merge of three sorted lists: (ugly × 2), (ugly × 3) and (ugly × 5). Keep one pointer
into the list for each multiplier and always take the smallest candidate.
""",
        hints=[
            "Testing every integer for ugliness is far too slow — the 1690th ugly number is over two billion.",
            "Each new ugly number is an earlier ugly number multiplied by 2, 3 or 5.",
            "Keep three indices. Next = min(ugly[i2]*2, ugly[i3]*3, ugly[i5]*5); advance EVERY index that produced it.",
        ],
        brute_force="Check 1, 2, 3, … one by one by dividing out 2s, 3s and 5s. The 1690th ugly number is 2,123,366,400, so this needs billions of checks.",
        approach=r"""
**State:** `ugly[k]` = the (k+1)-th ugly number.
**Recurrence:** `ugly[k] = min(2·ugly[i2], 3·ugly[i3], 5·ugly[i5])`, then advance the pointers that matched.
**Base case:** `ugly[0] = 1`. **Answer:** `ugly[n-1]`.

| step | 2·ugly[i2] | 3·ugly[i3] | 5·ugly[i5] | chosen | list |
|---|---|---|---|---|---|
| 1 | 2 | 3 | 5 | 2 | 1, 2 |
| 2 | 4 | 3 | 5 | 3 | 1, 2, 3 |
| 3 | 4 | 6 | 5 | 4 | …, 4 |
| 4 | 6 | 6 | 5 | 5 | …, 5 |
| 5 | **6** | **6** | 10 | 6 | …, 6 (advance both i2 and i3) |
| 6 | 8 | 9 | 10 | 8 | …, 8 |
""",
        complexity="Time O(n), space O(n).",
        pitfalls="- Using `elif` when advancing pointers: 6 = 2·3 = 3·2 is produced twice, so both pointers must move or 6 appears twice.\n- Thinking 'not divisible by 7' is enough: 121 = 11² and 49 are not ugly either.",
        follow_up="Super Ugly Number generalises to any list of primes (one pointer per prime, or a heap).",
    ),
),
dict(
    id="delete-and-earn",
    title="Delete and Earn",
    difficulty="Medium",
    pattern="1-D DP / House Robber",
    leetcode="https://leetcode.com/problems/delete-and-earn/",
    entry="deleteAndEarn",
    description=r"""
You repeatedly pick a number `x` from the array `nums`, earn `x` points and remove it — but picking
`x` also wipes out **every** copy of `x - 1` and `x + 1` (those earn nothing). Continue until the
array is empty. Return the largest total you can earn.

**Constraints**

- `1 <= len(nums) <= 2 * 10^4`
- `1 <= nums[i] <= 10^4`

**Example 1:** `nums = [3, 4, 2]` → `6` (take 4, which deletes 3; then take 2)

**Example 2:** `nums = [2, 2, 3, 3, 3, 4]` → `9` (take the three 3s)
""",
    starter='''class Solution:
    def deleteAndEarn(self, nums: List[int]) -> int:
        pass
''',
    solution='''class Solution:
    def deleteAndEarn(self, nums):
        gain = [0] * (max(nums) + 1)      # gain[v] = total points available from value v
        for x in nums:
            gain[x] += x
        prev2 = prev1 = 0                 # House Robber over values 0..max
        for g in gain:
            prev2, prev1 = prev1, max(prev1, prev2 + g)
        return prev1
''',
    tests=[
        [[3, 4, 2]],
        [[2, 2, 3, 3, 3, 4]],
        [[5]],
        [[1, 1, 1, 2]],
        [[1, 3, 5, 7]],
        [[8, 10, 4, 9, 1, 3, 5, 9, 4, 10]],
        [[1, 2, 3, 4, 5, 6]],
        [[10000, 9999, 9998]],
        [[4, 4, 4, 5, 5, 3]],
        [[1, 10, 2, 9]],
        [_ints(200, 1, 30)],
        [_ints(20000, 1, 10000)],
        [_ints(20000, 1, 60)],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def deleteAndEarn(self, nums):
        from collections import Counter
        cnt = Counter(nums)
        prev2 = prev1 = 0
        for v in sorted(cnt):
            prev2, prev1 = prev1, max(prev1, prev2 + v * cnt[v])
        return prev1
''',
        '''class Solution:
    def deleteAndEarn(self, nums):
        return max(sum(x for x in nums if x % 2), sum(x for x in nums if x % 2 == 0))
''',
    ],
    guide=dict(
        prereqs="House Robber.",
        intuition=r"""
Once you take one copy of `x`, its neighbours `x−1` and `x+1` are already gone, so taking **all**
other copies of `x` costs nothing extra. Group the points by value: `gain[v] = v × (count of v)`.
Now "taking value `v` forbids values `v−1` and `v+1`" is House Robber on the array `gain`.
""",
        hints=[
            "If you take one 3, should you take the other 3s too?",
            "Build gain[v] = total points from all copies of v. Which values conflict with v?",
            "Run House Robber over gain[0..max]: best[v] = max(best[v-1], best[v-2] + gain[v]).",
        ],
        brute_force="Try every order of picks recursively. With 20,000 numbers the number of orders is astronomically large; even choosing a subset of distinct values is 2^(distinct values).",
        approach=r"""
**State:** `best[v]` = most points using only values `0..v`.
**Recurrence:** `best[v] = max(best[v-1], best[v-2] + gain[v])`.
**Base case:** `best[-1] = best[-2] = 0`. **Order:** `v` increasing. **Answer:** `best[max]`.

`nums = [2, 2, 3, 3, 3, 4]`:

| v | 0 | 1 | 2 | 3 | 4 |
|---|---|---|---|---|---|
| gain[v] | 0 | 0 | 4 | 9 | 4 |
| best[v] | 0 | 0 | 4 | 9 | **9** |

`best[4] = max(best[3], best[2] + 4) = max(9, 8) = 9`.
""",
        complexity="Time O(n + M) where M is the largest value; space O(M).",
        pitfalls="- Running House Robber over the sorted **distinct** values treats 1 and 10 as neighbours even though they don't conflict — gaps must count as empty houses.\n- Forgetting that all copies of a value come together.",
        follow_up="If values can be huge (10⁹), sort the distinct values and only apply the 'skip' rule when consecutive values differ by exactly 1.",
    ),
),
dict(
    id="combination-sum-iv",
    title="Combination Sum IV",
    difficulty="Medium",
    pattern="1-D DP / Counting (ordered)",
    leetcode="https://leetcode.com/problems/combination-sum-iv/",
    neetcode="https://neetcode.io/problems/combination-sum-iv",
    entry="combinationSum4",
    description=r"""
`nums` holds distinct positive integers. Count the **ordered sequences** of numbers from `nums`
(each number may be used any number of times) that add up to `target`. Different orders count as
different sequences: `1, 2` and `2, 1` are two sequences.

Python integers have no size limit, so return the exact count.

**Constraints**

- `1 <= len(nums) <= 200`, `1 <= nums[i] <= 1000`, all distinct
- `1 <= target <= 1000`

**Example 1:** `nums = [1, 2, 3], target = 4` → `7`
(1111, 112, 121, 211, 13, 31, 22)

**Example 2:** `nums = [9], target = 3` → `0`
""",
    starter='''class Solution:
    def combinationSum4(self, nums: List[int], target: int) -> int:
        pass
''',
    solution='''class Solution:
    def combinationSum4(self, nums, target):
        ways = [1] + [0] * target
        for t in range(1, target + 1):       # amounts OUTER -> order matters
            total = 0
            for x in nums:
                if x <= t:
                    total += ways[t - x]
            ways[t] = total
        return ways[target]
''',
    tests=[
        [[1, 2, 3], 4],
        [[9], 3],
        [[1], 1],
        [[2], 4],
        [[2, 3], 7],
        [[1, 2], 10],
        [[3, 5, 7], 2],
        [[4, 2, 1], 32],
        [[10, 20, 30], 100],
        [[1, 2, 3], 35],
        [[3, 4, 5, 6, 7, 8, 9, 10], 200],
        [list(range(1, 201)), 1000],
        [[7, 11, 13, 17, 19, 23], 999],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def combinationSum4(self, nums, target):
        ways = [1] + [0] * target
        for x in nums:
            for t in range(x, target + 1):
                ways[t] += ways[t - x]
        return ways[target]
''',
        '''class Solution:
    def combinationSum4(self, nums, target):
        ways = [0] * (target + 1)
        for t in range(1, target + 1):
            ways[t] = sum(ways[t - x] for x in nums if x <= t)
        return ways[target]
''',
    ],
    guide=dict(
        prereqs="Climbing Stairs; Coin Change II (the unordered cousin).",
        intuition=r"""
Because order matters, classify sequences by their **last number**. If the last number is `x`, what
comes before is any sequence summing to `target − x`. This is Climbing Stairs where the allowed
step sizes are the numbers in `nums`.
""",
        hints=[
            "With nums = [1, 2] this is exactly Climbing Stairs.",
            "ways[t] = number of ordered sequences summing to t. Which number was added last?",
            "ways[t] = sum(ways[t - x] for x in nums if x <= t), ways[0] = 1.",
        ],
        brute_force="Recursively try every number as the next element: the number of calls equals the number of sequences, which grows exponentially (already over 10⁹ for nums = [1,2,3], target = 35).",
        approach=r"""
**State:** `ways[t]` = ordered sequences summing to `t`.
**Recurrence:** `ways[t] = Σ ways[t − x]`. **Base case:** `ways[0] = 1` (the empty sequence).
**Order:** `t` increasing. **Answer:** `ways[target]`.

`nums = [1, 2, 3]`:

| t | 0 | 1 | 2 | 3 | 4 |
|---|---|---|---|---|---|
| ways | 1 | 1 | 2 | 4 | **7** |

`ways[4] = ways[3] + ways[2] + ways[1] = 4 + 2 + 1`.
""",
        complexity="Time O(target · len(nums)), space O(target).",
        pitfalls="- Putting the loop over `nums` outside counts each multiset once (that is Coin Change II) — here it gives 4 instead of 7.\n- `ways[0]` must be 1, otherwise everything stays 0.",
        follow_up="If negative numbers were allowed the count could be infinite; you would need a limit on sequence length (add it to the state).",
    ),
),
dict(
    id="number-of-longest-increasing-subsequence",
    title="Number of Longest Increasing Subsequence",
    difficulty="Medium",
    pattern="1-D DP / LIS",
    leetcode="https://leetcode.com/problems/number-of-longest-increasing-subsequence/",
    entry="findNumberOfLIS",
    description=r"""
Given an integer array `nums`, count how many **strictly increasing subsequences** have the maximum
possible length. Two subsequences are different if they use different index sets, even if the values
are the same.

**Constraints**

- `1 <= len(nums) <= 2000`
- `-10^6 <= nums[i] <= 10^6`

**Example 1:** `nums = [1, 3, 5, 4, 7]` → `2` (1-3-5-7 and 1-3-4-7)

**Example 2:** `nums = [2, 2, 2, 2, 2]` → `5` (the longest length is 1; five single elements)
""",
    starter='''class Solution:
    def findNumberOfLIS(self, nums: List[int]) -> int:
        pass
''',
    solution='''class Solution:
    def findNumberOfLIS(self, nums):
        n = len(nums)
        length = [1] * n        # longest increasing subsequence ending at i
        count = [1] * n         # how many of that length end at i
        for i in range(n):
            x = nums[i]
            li, ci = 1, 1
            for j in range(i):
                if nums[j] < x:
                    lj = length[j] + 1
                    if lj > li:
                        li, ci = lj, count[j]
                    elif lj == li:
                        ci += count[j]
            length[i], count[i] = li, ci
        best = max(length)
        return sum(c for l, c in zip(length, count) if l == best)
''',
    tests=[
        [[1, 3, 5, 4, 7]],
        [[2, 2, 2, 2, 2]],
        [[7]],
        [[1, 2]],
        [[2, 1]],
        [[1, 2, 4, 3, 5, 4, 7, 2]],
        [[1, 1, 1, 2, 2, 2, 3, 3, 3]],
        [[5, 4, 3, 2, 1]],
        [[1, 2, 3, 4, 5]],
        [[3, 1, 2]],
        [_ints(60, 0, 20)],
        [_ints(900, -1000, 1000)],
        [[v for k in range(1, 30) for v in (2 * k, 2 * k - 1)]],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def findNumberOfLIS(self, nums):
        n = len(nums)
        length = [1] * n
        for i in range(n):
            for j in range(i):
                if nums[j] < nums[i]:
                    length[i] = max(length[i], length[j] + 1)
        return length.count(max(length))
''',
        '''class Solution:
    def findNumberOfLIS(self, nums):
        n = len(nums)
        length, count = [1] * n, [1] * n
        for i in range(n):
            for j in range(i):
                if nums[j] < nums[i]:
                    if length[j] + 1 > length[i]:
                        length[i], count[i] = length[j] + 1, count[j]
                    elif length[j] + 1 == length[i]:
                        count[i] += count[j]
        return count[length.index(max(length))]
''',
    ],
    guide=dict(
        prereqs="Longest Increasing Subsequence (the O(n²) version); lesson on LIS.",
        intuition=r"""
The O(n²) LIS table stores, for each index, the best **length** ending there. To count, carry a
second number per index: **how many** subsequences of that best length end there. When an earlier
index offers a strictly better length, replace both; when it offers an equal length, add its count.
""",
        hints=[
            "First compute length[i] = longest increasing subsequence ending at i.",
            "Add count[i]. If j gives a longer chain, count[i] = count[j]; if it ties, count[i] += count[j].",
            "The answer is the sum of count[i] over all i whose length[i] equals the maximum.",
        ],
        brute_force="Enumerate all 2ⁿ subsequences, keep the increasing ones, find the maximum length and count. Impossible beyond n ≈ 25.",
        approach=r"""
**State:** `length[i]`, `count[i]` for subsequences ending at `i`.
**Recurrence:** for each `j < i` with `nums[j] < nums[i]`: longer → replace, equal → add.
**Base case:** `length[i] = count[i] = 1`. **Answer:** `Σ count[i]` where `length[i]` is maximal.

`nums = [1, 3, 5, 4, 7]`:

| i | 0 | 1 | 2 | 3 | 4 |
|---|---|---|---|---|---|
| nums | 1 | 3 | 5 | 4 | 7 |
| length | 1 | 2 | 3 | 3 | 4 |
| count | 1 | 1 | 1 | 1 | **2** |

At `i = 4`, both `j = 2` (5) and `j = 3` (4) give length 4, so the counts add: 1 + 1 = 2.
""",
        complexity="Time O(n²), space O(n).",
        pitfalls="- Counting the number of *indices* with the maximum length instead of summing their counts.\n- Returning the count of only one best index.\n- Using `<=` instead of `<` (the subsequence must be strictly increasing).",
        follow_up="A segment tree or Fenwick tree over values storing (length, count) pairs brings it down to O(n log n).",
    ),
),
dict(
    id="russian-doll-envelopes",
    title="Russian Doll Envelopes",
    difficulty="Hard",
    pattern="1-D DP / LIS",
    leetcode="https://leetcode.com/problems/russian-doll-envelopes/",
    entry="maxEnvelopes",
    description=r"""
Each envelope is `[width, height]`. Envelope A fits inside envelope B only when A is **strictly**
narrower **and** strictly shorter than B (no rotating). Return the largest number of envelopes you
can nest one inside another, like Russian dolls.

**Constraints**

- `1 <= len(envelopes) <= 10^5`
- `1 <= width, height <= 10^5`

**Example 1:** `envelopes = [[5,4],[6,4],[6,7],[2,3]]` → `3` (`[2,3]` → `[5,4]` → `[6,7]`)

**Example 2:** `envelopes = [[1,1],[1,1],[1,1]]` → `1`
""",
    starter='''class Solution:
    def maxEnvelopes(self, envelopes: List[List[int]]) -> int:
        pass
''',
    solution='''from bisect import bisect_left

class Solution:
    def maxEnvelopes(self, envelopes):
        # width ascending; equal widths by height DESCENDING so they can't chain
        envelopes = sorted(envelopes, key=lambda e: (e[0], -e[1]))
        tails = []
        for _, h in envelopes:
            k = bisect_left(tails, h)
            if k == len(tails):
                tails.append(h)
            else:
                tails[k] = h
        return len(tails)
''',
    tests=[
        [[[5, 4], [6, 4], [6, 7], [2, 3]]],
        [[[1, 1], [1, 1], [1, 1]]],
        [[[3, 3]]],
        [[[1, 2], [2, 3], [3, 4], [4, 5]]],
        [[[4, 5], [4, 6], [6, 7], [2, 3], [1, 1]]],
        [[[1, 3], [3, 5], [6, 7], [6, 8], [8, 4], [9, 5]]],
        [[[2, 100], [3, 200], [4, 300], [5, 500], [5, 400], [5, 250], [6, 370], [6, 360], [7, 380]]],
        [[[10, 1], [9, 2], [8, 3], [7, 4]]],
        [[[1, 5], [2, 5], [3, 5]]],
        [[[5, 1], [5, 2], [5, 3]]],
        [[[_R.randint(1, 30), _R.randint(1, 30)] for _ in range(200)]],
        [[[_R.randint(1, 10 ** 5), _R.randint(1, 10 ** 5)] for _ in range(6000)]],
        [[[i, i] for i in range(1, 4001)]],
    ],
    examples=2,
    wrong_solutions=[
        '''from bisect import bisect_left

class Solution:
    def maxEnvelopes(self, envelopes):
        envelopes = sorted(envelopes)
        tails = []
        for _, h in envelopes:
            k = bisect_left(tails, h)
            if k == len(tails):
                tails.append(h)
            else:
                tails[k] = h
        return len(tails)
''',
        '''class Solution:
    def maxEnvelopes(self, envelopes):
        envelopes = sorted(envelopes)
        count, w, h = 0, 0, 0
        for a, b in envelopes:
            if a > w and b > h:
                count, w, h = count + 1, a, b
        return count
''',
    ],
    guide=dict(
        prereqs="Longest Increasing Subsequence with binary search (patience sorting).",
        intuition=r"""
Sort by width so that any valid nesting order reads left to right. Then you only need the heights
to increase — that is a Longest Increasing Subsequence on heights. One trap: envelopes with the
**same width** cannot nest, yet their heights might increase. Sorting equal widths by height
**descending** makes it impossible for LIS to pick two of them.
""",
        hints=[
            "Sort by width. What remains to be checked for a chain?",
            "It's LIS on heights — but two envelopes with equal width must not both be chosen.",
            "Sort by (width ascending, height descending), then run the O(n log n) LIS with bisect_left.",
        ],
        brute_force="Try every subset or every ordering of envelopes: exponential. The plain O(n²) 'ending at i' DP is correct but needs 10¹⁰ steps for n = 10⁵.",
        approach=r"""
1. Sort: `key = (width, -height)`.
2. **State:** `tails[k]` = smallest last height of a chain of `k+1` envelopes.
3. For each height `h`: `k = bisect_left(tails, h)`; append if `k` is past the end, else `tails[k] = h`.
4. **Answer:** `len(tails)`.

Example 1 sorted: `[2,3], [5,4], [6,7], [6,4]` → heights `3, 4, 7, 4`:

| h | tails |
|---|---|
| 3 | [3] |
| 4 | [3, 4] |
| 7 | [3, 4, 7] |
| 4 | [3, 4, 7] (replaces the 4 with 4) |

Length **3**. With ascending heights inside a width, an input such as `[5,1], [5,2], [5,3]` would give heights `1, 2, 3` and LIS would report 3, even though equal widths cannot nest. Descending order turns that into `3, 2, 1`, whose LIS is 1.
""",
        complexity="Time O(n log n) for the sort and the binary searches; space O(n).",
        pitfalls="- Sorting equal widths by ascending height lets `[5,1],[5,2],[5,3]` count as a chain of 3.\n- Using `bisect_right` allows equal heights to nest.\n- Greedy 'take the next envelope that fits' fails.",
        follow_up="Maximum Height by Stacking Cuboids (3-D boxes) and Box Stacking are the higher-dimensional versions and need the O(n²) DP.",
    ),
),
dict(
    id="longest-string-chain",
    title="Longest String Chain",
    difficulty="Medium",
    pattern="1-D DP / Hash Map",
    leetcode="https://leetcode.com/problems/longest-string-chain/",
    neetcode="https://neetcode.io/problems/longest-string-chain",
    entry="longestStrChain",
    description=r"""
Word A is a **predecessor** of word B when you can insert exactly one letter anywhere into A
(without reordering the others) and get B. For example `"abc"` is a predecessor of `"abac"`.

A **word chain** is a sequence of words where each word is a predecessor of the next one. A single
word is a chain of length 1. Given a list of lowercase words, return the length of the longest chain
you can form using words from the list.

**Constraints**

- `1 <= len(words) <= 1000`
- `1 <= len(words[i]) <= 16`

**Example 1:** `words = ["a","b","ba","bca","bda","bdca"]` → `4` (`a → ba → bda → bdca`)

**Example 2:** `words = ["abcd","dbqca"]` → `1`
""",
    starter='''class Solution:
    def longestStrChain(self, words: List[str]) -> int:
        pass
''',
    solution='''class Solution:
    def longestStrChain(self, words):
        best = {}                         # best[w] = longest chain ending at w
        for w in sorted(set(words), key=len):
            longest = 1
            for i in range(len(w)):
                pred = w[:i] + w[i + 1:]  # delete one letter -> a possible predecessor
                if pred in best and best[pred] + 1 > longest:
                    longest = best[pred] + 1
            best[w] = longest
        return max(best.values())
''',
    tests=[
        [["a", "b", "ba", "bca", "bda", "bdca"]],
        [["abcd", "dbqca"]],
        [["xbc", "pcxbcf", "xb", "cxbc", "pcxbc"]],
        [["a"]],
        [["a", "aa", "aaa", "aaaa"]],
        [["bdca", "bda", "ca", "dca", "a"]],
        [["ab", "ba", "abc", "bac"]],
        [["zz", "z", "zzz", "y", "yz", "xyz", "wxyz"]],
        [["abc", "abd", "abe"]],
        [["a", "ab", "ac", "bd", "abc", "abd", "abdd"]],
        [_chain_words(200)],
        [_chain_words(1000)],
        [["a" * k for k in range(1, 17)] + ["b" * k for k in range(1, 17)]],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def longestStrChain(self, words):
        best = {}
        for w in sorted(set(words), key=len):
            best[w] = best.get(w[:-1], 0) + 1
        return max(best.values())
''',
        '''class Solution:
    def longestStrChain(self, words):
        lens = sorted({len(w) for w in words})
        best = cur = 1
        for a, b in zip(lens, lens[1:]):
            cur = cur + 1 if b == a + 1 else 1
            best = max(best, cur)
        return best
''',
    ],
    guide=dict(
        prereqs="LIS 'ending at' DP; dictionaries (hash maps).",
        intuition=r"""
A chain always goes from shorter words to longer words, so process words in order of length. For
each word, its predecessors are the words you get by **deleting one letter** — at most 16
candidates. Look each up in a dictionary of results computed so far.
""",
        hints=[
            "Sort the words by length; predecessors are always processed first.",
            "Instead of comparing a word with all shorter words, generate its possible predecessors by deleting one letter.",
            "best[w] = 1 + max(best.get(w without letter i, 0)); answer is the largest value.",
        ],
        brute_force="Try every subset/order of words as a chain: exponential. Comparing every pair of words is O(n²·L), workable but slower than the hash-map approach.",
        approach=r"""
**State:** `best[w]` = longest chain ending with word `w`.
**Recurrence:** `best[w] = 1 + max(best[p])` over predecessors `p` of `w` that are in the list (0 if none).
**Order:** words by increasing length. **Answer:** `max(best.values())`.

Example 1:

| word | predecessors found | best |
|---|---|---|
| a | – | 1 |
| b | – | 1 |
| ba | a, b | 2 |
| bca | ba | 3 |
| bda | ba | 3 |
| bdca | bca, bda | **4** |
""",
        complexity="Time O(n log n + n·L²) (L ≤ 16: L deletions, each building a string of length L). Space O(n·L).",
        pitfalls="- The inserted letter can be anywhere, not only at the end.\n- Words are not given sorted.\n- Having all lengths 1, 2, 3, … present does not mean a chain exists.",
        follow_up="This is a longest path in a DAG whose edges go from each word to its one-letter extensions.",
    ),
),
dict(
    id="minimum-cost-for-tickets",
    title="Minimum Cost For Tickets",
    difficulty="Medium",
    pattern="1-D DP",
    leetcode="https://leetcode.com/problems/minimum-cost-for-tickets/",
    neetcode="https://neetcode.io/problems/minimum-cost-for-tickets",
    entry="mincostTickets",
    description=r"""
You will travel on certain days of the year, listed in increasing order in `days` (each between 1
and 365). Train passes come in three kinds: a **1-day** pass costs `costs[0]`, a **7-day** pass costs
`costs[1]` and a **30-day** pass costs `costs[2]`. A pass bought on day `d` covers `d` and the
following consecutive days (a 7-day pass bought on day 2 covers days 2 through 8).

Return the least money needed to be covered on every travel day.

**Constraints**

- `1 <= len(days) <= 365`, strictly increasing, `1 <= days[i] <= 365`
- `1 <= costs[i] <= 1000`

**Example 1:** `days = [1,4,6,7,8,20], costs = [2,7,15]` → `11`
(1-day on day 1, 7-day on day 4 covering 4–10, 1-day on day 20)

**Example 2:** `days = [1,2,3,4,5,6,7,8,9,10,30,31], costs = [2,7,15]` → `17`
""",
    starter='''class Solution:
    def mincostTickets(self, days: List[int], costs: List[int]) -> int:
        pass
''',
    solution='''class Solution:
    def mincostTickets(self, days, costs):
        n = len(days)
        dp = [0] * (n + 1)           # dp[i]: min cost to cover the first i travel days
        j7 = j30 = 0                 # first travel day still inside a 7 / 30 day window ending today
        for i in range(n):
            while days[i] - days[j7] >= 7:
                j7 += 1
            while days[i] - days[j30] >= 30:
                j30 += 1
            dp[i + 1] = min(dp[i] + costs[0], dp[j7] + costs[1], dp[j30] + costs[2])
        return dp[n]
''',
    tests=[
        [[1, 4, 6, 7, 8, 20], [2, 7, 15]],
        [[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 30, 31], [2, 7, 15]],
        [[1], [5, 3, 1]],
        [[1, 8], [2, 3, 100]],
        [[1, 7], [2, 3, 100]],
        [[1, 30], [10, 15, 16]],
        [[1, 31], [10, 15, 16]],
        [[1, 365], [3, 10, 20]],
        [[3, 5, 6, 8, 9, 10, 11, 12, 13, 14, 15, 16, 20, 25], [3, 14, 50]],
        [[1, 4, 6, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 20, 21, 22, 23, 27, 28], [3, 13, 45]],
        [list(range(1, 366)), [2, 7, 15]],
        [list(range(1, 366)), [1, 100, 1000]],
        [sorted(_R.sample(range(1, 366), 180)), [7, 30, 90]],
        [sorted(_R.sample(range(1, 366), 60)), [9, 38, 134]],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def mincostTickets(self, days, costs):
        n = len(days)
        dp = [0] * (n + 1)
        j7 = j30 = 0
        for i in range(n):
            while days[i] - days[j7] > 7:
                j7 += 1
            while days[i] - days[j30] > 30:
                j30 += 1
            dp[i + 1] = min(dp[i] + costs[0], dp[j7] + costs[1], dp[j30] + costs[2])
        return dp[n]
''',
        '''class Solution:
    def mincostTickets(self, days, costs):
        return min(len(days) * costs[0], -(-(days[-1] - days[0] + 1) // 7) * costs[1],
                   -(-(days[-1] - days[0] + 1) // 30) * costs[2])
''',
    ],
    guide=dict(
        prereqs="Min Cost Climbing Stairs; lesson *Linear DP*.",
        intuition=r"""
Think about the pass that covers the **last** travel day. It is a 1-day, 7-day or 30-day pass, and in
the best plan it ends exactly on that day (ending later wastes coverage). Everything before the
pass's first covered day is a smaller copy of the same problem.
""",
        hints=[
            "Let dp[i] be the cheapest way to cover the first i travel days.",
            "A 7-day pass ending on days[i] covers every travel day d with days[i] - d < 7.",
            "dp[i+1] = min(dp[i] + c1, dp[j7] + c7, dp[j30] + c30), where j7/j30 is the first travel index inside the window.",
        ],
        brute_force="At each travel day try all three passes recursively without remembering results: 3 branches per day, up to 3³⁶⁵ paths.",
        approach=r"""
**State:** `dp[i]` = min cost to cover travel days `0 … i−1`.
**Recurrence:** `dp[i+1] = min(dp[i] + c₁, dp[j7] + c₇, dp[j30] + c₃₀)` where `j7` is the smallest index with `days[i] − days[j7] < 7` (similarly `j30`).
**Base case:** `dp[0] = 0`. **Answer:** `dp[n]`.

`days = [1,4,6,7,8,20]`, `costs = [2,7,15]`:

| i | day | 1-day | 7-day (j7) | 30-day (j30) | dp[i+1] |
|---|---|---|---|---|---|
| 0 | 1 | 0+2 | 0+7 (0) | 0+15 (0) | 2 |
| 1 | 4 | 2+2 | 0+7 (0) | 15 | 4 |
| 2 | 6 | 4+2 | 0+7 (0) | 15 | 6 |
| 3 | 7 | 6+2 | 0+7 (0) | 15 | 7 |
| 4 | 8 | 7+2 | 2+7 (1) | 15 | 9 |
| 5 | 20 | 9+2 | 9+7 (5) | 15 | **11** |
""",
        complexity="Time O(n) (the two window pointers only move forward), space O(n). A DP over all 365 calendar days is equally fine.",
        pitfalls="- Off by one on the window: a 7-day pass bought on day 1 covers days 1–7, **not** day 8.\n- Assuming one pass type is always best.",
        follow_up="With arbitrary pass lengths, keep one pointer per pass type, or binary-search the window start.",
    ),
),
dict(
    id="maximum-profit-in-job-scheduling",
    title="Maximum Profit in Job Scheduling",
    difficulty="Hard",
    pattern="1-D DP / Sort + Binary Search",
    leetcode="https://leetcode.com/problems/maximum-profit-in-job-scheduling/",
    entry="jobScheduling",
    description=r"""
There are `n` jobs. Job `i` runs from `startTime[i]` to `endTime[i]` and pays `profit[i]`. You can
work on only one job at a time, but a job may begin at the exact moment another one ends. Choose a
set of non-overlapping jobs with the largest total profit and return that profit.

**Constraints**

- `1 <= n <= 5 * 10^4`
- `1 <= startTime[i] < endTime[i] <= 10^9`
- `1 <= profit[i] <= 10^4`

**Example 1:** `startTime = [1,2,3,3], endTime = [3,4,5,6], profit = [50,10,40,70]` → `120`
(jobs 0 and 3: 50 + 70)

**Example 2:** `startTime = [1,2,3,4,6], endTime = [3,5,10,6,9], profit = [20,20,100,70,60]` → `150`
""",
    starter='''class Solution:
    def jobScheduling(self, startTime: List[int], endTime: List[int], profit: List[int]) -> int:
        pass
''',
    solution='''from bisect import bisect_right

class Solution:
    def jobScheduling(self, startTime, endTime, profit):
        jobs = sorted(zip(endTime, startTime, profit))
        ends = [0]          # end times at which the best profit improved
        best = [0]          # best[k]: max profit using jobs that end by ends[k]
        for e, s, p in jobs:
            k = bisect_right(ends, s) - 1          # last record whose end time <= s
            cand = best[k] + p
            if cand > best[-1]:
                ends.append(e)
                best.append(cand)
        return best[-1]
''',
    tests=[
        [[1, 2, 3, 3], [3, 4, 5, 6], [50, 10, 40, 70]],
        [[1, 2, 3, 4, 6], [3, 5, 10, 6, 9], [20, 20, 100, 70, 60]],
        [[1, 1, 1], [2, 3, 4], [5, 6, 4]],
        [[5], [9], [7]],
        [[1, 2, 3], [2, 3, 4], [1, 1, 1]],
        [[1, 1], [10, 2], [5, 1]],
        [[4, 2, 4, 8, 2], [5, 5, 5, 10, 8], [1, 2, 8, 10, 4]],
        [[6, 15, 7, 11, 1, 3, 16, 2], [19, 18, 19, 16, 10, 8, 19, 8], [2, 9, 1, 19, 5, 7, 3, 19]],
        [[1, 3, 6], [100, 5, 9], [10, 4, 4]],
        [[1, 2], [1000000000, 3], [3, 4]],
        _jobs(60, 100, 20, 50),
        _jobs(3000, 10 ** 6, 5000, 10 ** 4),
        _jobs(3000, 2000, 400, 100),
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def jobScheduling(self, startTime, endTime, profit):
        total, free = 0, 0
        for e, s, p in sorted(zip(endTime, startTime, profit)):
            if s >= free:
                total += p
                free = e
        return total
''',
        '''class Solution:
    def jobScheduling(self, startTime, endTime, profit):
        total, free = 0, 0
        taken = []
        for p, s, e in sorted(zip(profit, startTime, endTime), reverse=True):
            if all(e <= a or s >= b for a, b in taken[:50]):
                taken.append((s, e))
                total += p
        return total
''',
    ],
    guide=dict(
        prereqs="House Robber (take or skip); binary search with `bisect`.",
        intuition=r"""
Sort the jobs by end time. For the job that ends last you either **skip** it (answer = best without
it) or **take** it (its profit + the best you can do with jobs that finish no later than its start).
"The best among jobs ending by time t" is found by binary search because the records are sorted by
end time.
""",
        hints=[
            "Without profits, earliest-end-time greedy works. With profits it does not — Example 1.",
            "Sort by end time. dp[i] = best profit using the first i jobs. Take or skip job i.",
            "If you take job i, add dp[k] where k is the number of jobs with end <= start_i (binary search).",
        ],
        brute_force="Try every subset of jobs and check for overlaps: 2ⁿ subsets — hopeless beyond about 25 jobs.",
        approach=r"""
**State:** `dp[i]` = max profit using only the first `i` jobs in end-time order.
**Recurrence:** `dp[i] = max(dp[i-1], profit_i + dp[k])`, `k` = number of earlier jobs ending at or before `start_i`.
**Base case:** `dp[0] = 0`. **Answer:** `dp[n]`.

Example 1 sorted by end: (1,3,50), (2,4,10), (3,5,40), (3,6,70):

| job (start, end, profit) | k (jobs ending ≤ start) | take | skip | dp |
|---|---|---|---|---|
| (1, 3, 50) | 0 | 50 | 0 | 50 |
| (2, 4, 10) | 0 | 10 | 50 | 50 |
| (3, 5, 40) | 1 | 50 + 40 | 50 | 90 |
| (3, 6, 70) | 1 | 50 + 70 | 90 | **120** |

The reference keeps only the records where the best value improves, which keeps both lists sorted.
""",
        complexity="Time O(n log n) (sort + one binary search per job), space O(n).",
        pitfalls="- A job may start exactly when another ends: use `end <= start` (hence `bisect_right`).\n- Greedy by earliest end, or by largest profit, both fail.\n- Times go up to 10⁹, so you cannot index a table by time.",
        follow_up="Weighted interval scheduling is the textbook name. Variants: at most k jobs (add k to the state), or two workers.",
    ),
),
]
