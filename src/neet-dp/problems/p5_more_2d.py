import random

_R = random.Random(31337)


def _s(n, alpha):
    return "".join(_R.choice(alpha) for _ in range(n))


def _ints(n, lo, hi):
    return [_R.randint(lo, hi) for _ in range(n)]


def _grid(m, n, lo, hi):
    return [[_R.randint(lo, hi) for _ in range(n)] for _ in range(m)]


def _tri(rows, lo, hi):
    return [[_R.randint(lo, hi) for _ in range(r + 1)] for r in range(rows)]


def _obst(m, n, p):
    g = [[1 if _R.random() < p else 0 for _ in range(n)] for _ in range(m)]
    g[0][0] = g[m - 1][n - 1] = 0
    return g


_SCS_CHECKER = '''def check(args, got, expected):
    a, b = args
    if not isinstance(got, str) or len(got) != len(expected):
        return False
    def is_subseq(small, big):
        it = iter(big)
        return all(ch in it for ch in small)
    return is_subseq(a, got) and is_subseq(b, got)
'''


PROBLEMS = [
dict(
    id="triangle",
    title="Triangle",
    difficulty="Medium",
    pattern="2-D DP / Grid",
    leetcode="https://leetcode.com/problems/triangle/",
    entry="minimumTotal",
    description=r"""
`triangle` is a list of rows where row `r` has `r + 1` numbers. Start at the single number on top and
walk down to the bottom row. From position `j` in one row you may step to position `j` or `j + 1` in
the row below. Return the smallest possible sum of the numbers you step on.

**Constraints**

- `1 <= len(triangle) <= 200`
- `-10^4 <= triangle[r][j] <= 10^4`

**Example 1:** `triangle = [[2],[3,4],[6,5,7],[4,1,8,3]]` → `11` (2 → 3 → 5 → 1)

**Example 2:** `triangle = [[-10]]` → `-10`
""",
    starter='''class Solution:
    def minimumTotal(self, triangle: List[List[int]]) -> int:
        pass
''',
    solution='''class Solution:
    def minimumTotal(self, triangle):
        best = list(triangle[-1])                 # best[j]: min sum from this cell down to the bottom
        for r in range(len(triangle) - 2, -1, -1):
            row = triangle[r]
            for j in range(r + 1):
                best[j] = row[j] + min(best[j], best[j + 1])
        return best[0]
''',
    tests=[
        [[[2], [3, 4], [6, 5, 7], [4, 1, 8, 3]]],
        [[[-10]]],
        [[[1], [2, 3], [9, 9, 1]]],
        [[[-1], [2, 3], [1, -1, -3]]],
        [[[1], [1, 1]]],
        [[[5], [9, 1], [1, 9, 9], [1, 9, 9, 9]]],
        [[[0], [0, 0], [0, 0, 0]]],
        [[[3], [-5, 2], [4, -6, 7], [1, 1, -20, 1]]],
        [[[7], [3, 8], [8, 1, 0], [2, 7, 4, 4], [4, 5, 2, 6, 5]]],
        [_tri(12, -9, 9)],
        [_tri(60, -100, 100)],
        [_tri(200, -10000, 10000)],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def minimumTotal(self, triangle):
        j, total = 0, triangle[0][0]
        for row in triangle[1:]:
            if row[j + 1] < row[j]:
                j += 1
            total += row[j]
        return total
''',
        '''class Solution:
    def minimumTotal(self, triangle):
        return sum(min(row) for row in triangle)
''',
    ],
    guide=dict(
        prereqs="Minimum Path Sum; lesson *Grid DP and DP on DAGs*.",
        intuition=r"""
From a cell you have two choices below you. Greedily stepping to the smaller one can lead away from a
very small number further down. Instead compute, for every cell, the cheapest way to finish **from
that cell to the bottom**. Working from the bottom row upward, each cell needs only the two cells
under it.
""",
        hints=[
            "Try the greedy choice on [[1],[2,3],[9,9,1]].",
            "Let best(r, j) be the minimum sum from cell (r, j) down to the last row.",
            "best(r, j) = triangle[r][j] + min(best(r+1, j), best(r+1, j+1)); start from the last row.",
        ],
        brute_force="Follow every path from the top: each row doubles the number of paths, so 2¹⁹⁹ paths for 200 rows.",
        approach=r"""
**State:** `best(r, j)` = min path sum starting at `(r, j)` and ending in the bottom row.
**Recurrence:** `best(r, j) = t[r][j] + min(best(r+1, j), best(r+1, j+1))`.
**Base case:** the bottom row is its own value. **Order:** rows bottom to top. **Answer:** `best(0, 0)`.

Example 1 (one array reused for every row):

| after row | best |
|---|---|
| 3 (bottom) | [4, 1, 8, 3] |
| 2 | [6+1, 5+1, 7+3] = [7, 6, 10] |
| 1 | [3+6, 4+6] = [9, 10] |
| 0 | [2+9] = [**11**] |
""",
        complexity="Time O(n²) for n rows (every number once); extra space O(n).",
        pitfalls="- Greedy top-down fails.\n- You can only move to `j` or `j+1`, not `j-1`.\n- Going top-down works too, but then the answer is the minimum of the last row and the edges need care.",
        follow_up="Minimum Falling Path Sum is the square-grid version with three choices per step.",
    ),
),
dict(
    id="unique-paths-ii",
    title="Unique Paths II",
    difficulty="Medium",
    pattern="2-D DP / Grid",
    leetcode="https://leetcode.com/problems/unique-paths-ii/",
    neetcode="https://neetcode.io/problems/unique-paths-ii",
    entry="uniquePathsWithObstacles",
    description=r"""
A robot stands in the top-left cell of a grid and wants to reach the bottom-right cell, moving only
one step **right** or **down** at a time. Some cells contain an obstacle (`1` in `obstacleGrid`) and
cannot be entered; free cells are `0`. Count the different routes. (Python integers have no size
limit; return the exact count.)

**Constraints**

- `1 <= m, n <= 100`
- every cell is `0` or `1`

**Example 1:** `obstacleGrid = [[0,0,0],[0,1,0],[0,0,0]]` → `2`

**Example 2:** `obstacleGrid = [[0,1],[0,0]]` → `1`
""",
    starter='''class Solution:
    def uniquePathsWithObstacles(self, obstacleGrid: List[List[int]]) -> int:
        pass
''',
    solution='''class Solution:
    def uniquePathsWithObstacles(self, obstacleGrid):
        n = len(obstacleGrid[0])
        ways = [0] * n
        ways[0] = 1
        for row in obstacleGrid:
            for c in range(n):
                if row[c] == 1:
                    ways[c] = 0                  # nothing can pass through an obstacle
                elif c > 0:
                    ways[c] += ways[c - 1]       # from above (old value) + from the left
        return ways[-1]
''',
    tests=[
        [[[0, 0, 0], [0, 1, 0], [0, 0, 0]]],
        [[[0, 1], [0, 0]]],
        [[[0]]],
        [[[1]]],
        [[[0, 1, 0], [0, 0, 0]]],
        [[[0, 0], [1, 0], [0, 0]]],
        [[[0, 0, 0, 0]]],
        [[[0, 0, 1, 0]]],
        [[[0, 0], [0, 1]]],
        [[[1, 0], [0, 0]]],
        [[[0, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1], [1, 0, 0, 0]]],
        [_obst(12, 12, 0.15)],
        [[[0] * 18 for _ in range(18)]],
        [_obst(100, 100, 0.03)],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def uniquePathsWithObstacles(self, g):
        m, n = len(g), len(g[0])
        dp = [[0] * n for _ in range(m)]
        for i in range(m):
            for j in range(n):
                if g[i][j] == 1:
                    dp[i][j] = 0
                elif i == 0 or j == 0:
                    dp[i][j] = 1
                else:
                    dp[i][j] = dp[i - 1][j] + dp[i][j - 1]
        return dp[-1][-1]
''',
        '''import math
class Solution:
    def uniquePathsWithObstacles(self, g):
        m, n = len(g), len(g[0])
        return math.comb(m + n - 2, m - 1) - sum(map(sum, g))
''',
    ],
    guide=dict(
        prereqs="Unique Paths.",
        intuition=r"""
Same counting rule as Unique Paths — routes into a cell come from above or from the left — with one
change: an obstacle cell has **zero** routes. Zeros then flow onward naturally, so a blocked cell
automatically removes every route that would have passed through it.
""",
        hints=[
            "What is the number of routes to a cell that contains an obstacle?",
            "Be careful with the first row and column: an obstacle there blocks every cell after it.",
            "Use one row: ways[c] = 0 on an obstacle, else ways[c] += ways[c-1]. Start with ways[0] = 1.",
        ],
        brute_force="Recursively explore right and down from every cell: the number of calls equals the number of routes, e.g. about 2.3 billion for an empty 18×18 grid.",
        approach=r"""
**State:** `ways(r, c)` = routes from the start to `(r, c)`.
**Recurrence:** `0` if the cell is an obstacle, else `ways(r-1, c) + ways(r, c-1)`.
**Base case:** `ways(0, 0) = 1` if free. **Order:** row by row. **Answer:** bottom-right cell.

Example 1:

| | c0 | c1 | c2 |
|---|---|---|---|
| r0 | 1 | 1 | 1 |
| r1 | 1 | 0 (obstacle) | 1 |
| r2 | 1 | 1 | **2** |

`[[0,1,0],[0,0,0]]`: the top row is `1, 0, 0` — the cell after the obstacle has **0** routes, not 1.
""",
        complexity="Time O(m·n), space O(n).",
        pitfalls="- Setting the whole first row/column to 1: cells behind an obstacle in the first row are unreachable.\n- A blocked start or end cell means the answer is 0.",
        follow_up="Unique Paths III (visit every free cell exactly once) needs backtracking or bitmask DP instead.",
    ),
),
dict(
    id="minimum-falling-path-sum",
    title="Minimum Falling Path Sum",
    difficulty="Medium",
    pattern="2-D DP / Grid",
    leetcode="https://leetcode.com/problems/minimum-falling-path-sum/",
    entry="minFallingPathSum",
    description=r"""
Given an `n × n` grid of integers, a **falling path** starts at any cell of the first row and moves
down one row at a time; from column `c` it may land on column `c - 1`, `c` or `c + 1` of the next
row (staying inside the grid). Return the smallest possible sum of a falling path.

**Constraints**

- `1 <= n <= 100`
- `-100 <= matrix[r][c] <= 100`

**Example 1:** `matrix = [[2,1,3],[6,5,4],[7,8,9]]` → `13` (1 → 5 → 7 or 1 → 4 → 8)

**Example 2:** `matrix = [[-19,57],[-40,-5]]` → `-59`
""",
    starter='''class Solution:
    def minFallingPathSum(self, matrix: List[List[int]]) -> int:
        pass
''',
    solution='''class Solution:
    def minFallingPathSum(self, matrix):
        n = len(matrix)
        prev = list(matrix[0])                     # best sum of a path ending at each column
        for r in range(1, n):
            row = matrix[r]
            cur = [0] * n
            for c in range(n):
                m = prev[c]
                if c > 0 and prev[c - 1] < m:
                    m = prev[c - 1]
                if c + 1 < n and prev[c + 1] < m:
                    m = prev[c + 1]
                cur[c] = row[c] + m
            prev = cur
        return min(prev)
''',
    tests=[
        [[[2, 1, 3], [6, 5, 4], [7, 8, 9]]],
        [[[-19, 57], [-40, -5]]],
        [[[7]]],
        [[[1, 2], [3, 4]]],
        [[[1, 9, 9], [9, 9, 1], [9, 9, 1]]],
        [[[5, 1, 5], [5, 9, 5], [-50, 9, 9]]],
        [[[0, 0, 0], [0, 0, 0], [0, 0, 0]]],
        [[[100, -42, -46, -41], [31, 97, 10, -10], [-58, -51, 82, 89], [51, 81, 69, -51]]],
        [[[-80, -13, 22], [83, 94, -5], [73, -48, 61]]],
        [_grid(15, 15, -9, 9)],
        [_grid(60, 60, -100, 100)],
        [_grid(100, 100, -100, 100)],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def minFallingPathSum(self, matrix):
        n = len(matrix)
        c = min(range(n), key=lambda j: matrix[0][j])
        total = matrix[0][c]
        for r in range(1, n):
            c = min((j for j in (c - 1, c, c + 1) if 0 <= j < n), key=lambda j: matrix[r][j])
            total += matrix[r][c]
        return total
''',
        '''class Solution:
    def minFallingPathSum(self, matrix):
        n = len(matrix)
        prev = list(matrix[0])
        for r in range(1, n):
            prev = [matrix[r][c] + min(prev[c], prev[c - 1] if c else prev[c]) for c in range(n)]
        return min(prev)
''',
    ],
    guide=dict(
        prereqs="Triangle; Minimum Path Sum.",
        intuition=r"""
The best path ending at a cell must have come from one of the (up to) three cells above it, and the
part before that must itself be a best path. So each row is computed from the previous row only.
Because the path may start and end in any column, take the minimum over the whole last row.
""",
        hints=[
            "Let best(r, c) be the smallest sum of a falling path that ends at (r, c).",
            "It arrives from (r-1, c-1), (r-1, c) or (r-1, c+1) — skip the ones outside the grid.",
            "Keep only the previous row; answer = min of the final row.",
        ],
        brute_force="Follow every path: n starting columns and up to 3 choices per row, about n·3ⁿ⁻¹ paths.",
        approach=r"""
**State:** `best(r, c)` = min falling-path sum ending at `(r, c)`.
**Recurrence:** `best(r, c) = m[r][c] + min(best(r-1, c-1), best(r-1, c), best(r-1, c+1))`.
**Base case:** row 0 is the grid's first row. **Answer:** `min(best(n-1, ·))`.

Example 1:

| row | grid | best |
|---|---|---|
| 0 | 2, 1, 3 | 2, 1, 3 |
| 1 | 6, 5, 4 | 6+1, 5+1, 4+1 = 7, 6, 5 |
| 2 | 7, 8, 9 | 7+6, 8+5, 9+5 = 13, 13, 14 |

Minimum of the last row: **13**.
""",
        complexity="Time O(n²), space O(n).",
        pitfalls="- Index −1 in Python silently wraps to the last column — guard the left edge.\n- Greedy from the smallest top cell fails.\n- Forgetting the diagonal to the right.",
        follow_up="Minimum Falling Path Sum II forbids staying in the same column: keep the smallest and second-smallest of the previous row.",
    ),
),
dict(
    id="dungeon-game",
    title="Dungeon Game",
    difficulty="Hard",
    pattern="2-D DP / Grid (backwards)",
    leetcode="https://leetcode.com/problems/dungeon-game/",
    entry="calculateMinimumHP",
    description=r"""
A knight enters a dungeon grid at the top-left room and must reach the princess in the bottom-right
room, moving only **right** or **down**. Each room changes the knight's health by the number written
in it (negative = damage, positive = healing, zero = nothing), including the first and last rooms.
The knight dies the moment health drops to `0` or below.

Return the smallest starting health that lets the knight reach the princess alive.

**Constraints**

- `1 <= m, n <= 200`
- `-1000 <= dungeon[r][c] <= 1000`

**Example 1:** `dungeon = [[-2,-3,3],[-5,-10,1],[10,30,-5]]` → `7` (right, right, down, down)

**Example 2:** `dungeon = [[0]]` → `1`
""",
    starter='''class Solution:
    def calculateMinimumHP(self, dungeon: List[List[int]]) -> int:
        pass
''',
    solution='''class Solution:
    def calculateMinimumHP(self, dungeon):
        m, n = len(dungeon), len(dungeon[0])
        INF = float("inf")
        need = [INF] * (n + 1)            # need[c]: health required on ENTERING cell (r, c)
        need[n - 1] = 1                   # virtual cell after the princess: must still have 1
        for r in range(m - 1, -1, -1):
            row = dungeon[r]
            for c in range(n - 1, -1, -1):
                after = min(need[c], need[c + 1])     # below (old value) or right
                need[c] = max(1, after - row[c])
        return need[0]
''',
    tests=[
        [[[-2, -3, 3], [-5, -10, 1], [10, 30, -5]]],
        [[[0]]],
        [[[100]]],
        [[[-5]]],
        [[[1, -3, 3], [0, -2, 0], [-3, -3, -3]]],
        [[[0, 5], [-2, -3]]],
        [[[-3, 5]]],
        [[[2], [-7], [3]]],
        [[[1, -4, 5, -99], [2, -2, -2, -1]]],
        [[[0, -74, -47, -20, -23, -39, -48], [37, -30, 37, -65, -82, 28, -27], [-76, -33, 7, 42, 3, 49, -93]]],
        [_grid(10, 10, -20, 10)],
        [_grid(60, 60, -100, 60)],
        [_grid(120, 120, -1000, 1000)],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def calculateMinimumHP(self, d):
        m, n = len(d), len(d[0])
        best = [[0] * n for _ in range(m)]
        for i in range(m):
            for j in range(n):
                prev = max(best[i - 1][j] if i else float("-inf"), best[i][j - 1] if j else float("-inf"))
                best[i][j] = d[i][j] + (prev if (i or j) else 0)
        return max(1, 1 - best[-1][-1])
''',
        '''class Solution:
    def calculateMinimumHP(self, d):
        m, n = len(d), len(d[0])
        INF = float("inf")
        need = [[INF] * (n + 1) for _ in range(m + 1)]
        need[m][n - 1] = need[m - 1][n] = 0
        for r in range(m - 1, -1, -1):
            for c in range(n - 1, -1, -1):
                need[r][c] = max(0, min(need[r + 1][c], need[r][c + 1]) - d[r][c])
        return need[0][0]
''',
    ],
    guide=dict(
        prereqs="Minimum Path Sum; lesson *Grid DP and DP on DAGs*.",
        intuition=r"""
Going forward you would need to track two things at once (current health and the lowest it has ever
been), and the path with the best total is not always the safest. Going **backwards** needs one
number per room: "how much health must I have when I *enter* this room so that I survive from here
to the end?" That depends only on the room's value and the cheaper of the two next rooms.
""",
        hints=[
            "The path with the largest total sum is not necessarily the answer — health must stay positive at every step.",
            "Define need(r, c) = minimum health when entering room (r, c). Fill from the princess back to the start.",
            "need(r, c) = max(1, min(need(r+1, c), need(r, c+1)) - dungeon[r][c]).",
        ],
        brute_force="Enumerate every right/down path and simulate it, or binary-search the starting health and test each path: both exponential in m + n.",
        approach=r"""
**State:** `need(r, c)` = least health on entering `(r, c)` that guarantees survival to the end.
**Recurrence:** `need(r, c) = max(1, min(need(r+1, c), need(r, c+1)) − d[r][c])`.
**Base case:** after the last room you must still have 1 health. **Order:** bottom-right to top-left.
**Answer:** `need(0, 0)`.

Example 1:

| need | c0 | c1 | c2 |
|---|---|---|---|
| r0 | **7** | 5 | 2 |
| r1 | 6 | 11 | 5 |
| r2 | 1 | 1 | 6 |

Bottom-right: `max(1, 1 − (−5)) = 6`. Cell (1,2): `max(1, 6 − 1) = 5`. Cell (0,2): `max(1, 5 − 3) = 2`.
Top-left: `max(1, min(6, 5) − (−2)) = 7`.
""",
        complexity="Time O(m·n), space O(n).",
        pitfalls="- Health must be at least **1**, not 0, at all times (`max(1, …)`).\n- A big healing room late in the path cannot rescue a death earlier — which is why forward 'max sum' DP is wrong.\n- The start room's own value counts.",
        follow_up="This 'work backwards from the goal' trick appears whenever a constraint must hold at every prefix (e.g. minimum initial fuel/energy problems).",
    ),
),
dict(
    id="longest-palindromic-subsequence",
    title="Longest Palindromic Subsequence",
    difficulty="Medium",
    pattern="2-D DP / Interval",
    leetcode="https://leetcode.com/problems/longest-palindromic-subsequence/",
    entry="longestPalindromeSubseq",
    description=r"""
A subsequence is what is left of a string after deleting some characters (possibly none) without
changing the order of the rest. Return the length of the longest subsequence of `s` that reads the
same forwards and backwards.

**Constraints**

- `1 <= len(s) <= 1000`
- lowercase English letters

**Example 1:** `s = "bbbab"` → `4` (`"bbbb"`)

**Example 2:** `s = "cbbd"` → `2` (`"bb"`)
""",
    starter='''class Solution:
    def longestPalindromeSubseq(self, s: str) -> int:
        pass
''',
    solution='''class Solution:
    def longestPalindromeSubseq(self, s):
        n = len(s)
        dp = [0] * n                       # dp[j] = answer for s[i..j] for the current i
        for i in range(n - 1, -1, -1):
            diag = 0                       # value for s[i+1..j-1]
            dp[i] = 1
            si = s[i]
            for j in range(i + 1, n):
                old = dp[j]                # value for s[i+1..j]
                if si == s[j]:
                    dp[j] = diag + 2
                elif dp[j - 1] > old:
                    dp[j] = dp[j - 1]      # value for s[i..j-1]
                diag = old
        return dp[n - 1]
''',
    tests=[
        ["bbbab"],
        ["cbbd"],
        ["a"],
        ["ab"],
        ["aa"],
        ["abcba"],
        ["character"],
        ["abcdefg"],
        ["aabaa"],
        ["agbdba"],
        [_s(60, "abc")],
        [_s(500, "abcdefgh")],
        [_s(800, "ab")],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def longestPalindromeSubseq(self, s):
        n, best = len(s), 1
        for c in range(n):
            for l, r in ((c, c), (c, c + 1)):
                while l >= 0 and r < n and s[l] == s[r]:
                    best = max(best, r - l + 1)
                    l -= 1; r += 1
        return best
''',
        '''class Solution:
    def longestPalindromeSubseq(self, s):
        from collections import Counter
        cnt = Counter(s)
        pairs = sum(v // 2 for v in cnt.values())
        return 2 * pairs + (1 if any(v % 2 for v in cnt.values()) else 0)
''',
    ],
    guide=dict(
        prereqs="Longest Common Subsequence; lesson *Interval DP*.",
        intuition=r"""
Look at the two **ends** of the string. If they are the same letter, both can be the outer pair of a
palindrome: answer = 2 + answer for the inside. If they differ, at least one of them is not used:
drop the left end or drop the right end and keep the better result.
""",
        hints=[
            "A substring must be contiguous; a subsequence may skip letters. 'bbbab' → 'bbbb'.",
            "Let L(i, j) be the answer for s[i..j]. Compare s[i] and s[j].",
            "Equal: L(i+1, j-1) + 2. Different: max(L(i+1, j), L(i, j-1)). L(i, i) = 1.",
        ],
        brute_force="Generate all 2ⁿ subsequences and test each for being a palindrome.",
        approach=r"""
**State:** `L(i, j)` = longest palindromic subsequence inside `s[i..j]`.
**Recurrence:** see hints. **Base case:** `L(i, i) = 1`, empty range = 0.
**Order:** `i` from right to left, `j` from left to right (shorter ranges first). **Answer:** `L(0, n-1)`.

`s = "bbbab"` (rows `i`, columns `j`):

| | b | b | b | a | b |
|---|---|---|---|---|---|
| b (0) | 1 | 2 | 3 | 3 | **4** |
| b (1) | | 1 | 2 | 2 | 3 |
| b (2) | | | 1 | 1 | 3 |
| a (3) | | | | 1 | 1 |
| b (4) | | | | | 1 |

`L(0,4)`: ends `b = b` → `L(1,3) + 2 = 2 + 2 = 4`.
""",
        complexity="Time O(n²), space O(n) with one rolling row (O(n²) for the full table).",
        pitfalls="- Confusing it with the longest palindromic **substring**.\n- Counting letter pairs ignores order: `\"abcabc\"` has three pairs of letters, yet its answer is only 3 (for example `\"aba\"`), because the pairs must mirror each other in position.\n- Wrong fill order (L(i+1, ·) must be ready before L(i, ·)).",
        follow_up="It equals LCS(s, reverse(s)). Minimum insertions/deletions to make a string a palindrome = n − this value.",
    ),
),
dict(
    id="minimum-ascii-delete-sum-for-two-strings",
    title="Minimum ASCII Delete Sum for Two Strings",
    difficulty="Medium",
    pattern="2-D DP / Strings",
    leetcode="https://leetcode.com/problems/minimum-ascii-delete-sum-for-two-strings/",
    entry="minimumDeleteSum",
    description=r"""
You may delete characters from either of two strings `s1` and `s2`. Deleting a character costs its
ASCII code (for example `ord('a') = 97`). Return the smallest total cost that makes the two strings
equal.

**Constraints**

- `1 <= len(s1), len(s2) <= 1000`
- lowercase English letters

**Example 1:** `s1 = "sea", s2 = "eat"` → `231` (delete `s` = 115 from "sea" and `t` = 116 from "eat")

**Example 2:** `s1 = "delete", s2 = "leet"` → `403`
""",
    starter='''class Solution:
    def minimumDeleteSum(self, s1: str, s2: str) -> int:
        pass
''',
    solution='''class Solution:
    def minimumDeleteSum(self, s1, s2):
        m = len(s2)
        b = [ord(ch) for ch in s2]
        prev = [0] * (m + 1)
        for j in range(m):
            prev[j + 1] = prev[j] + b[j]          # delete all of s2[:j+1]
        for ch in s1:
            a = ord(ch)
            cur = [prev[0] + a] + [0] * m
            for j in range(m):
                if a == b[j]:
                    cur[j + 1] = prev[j]
                else:
                    x, y = prev[j + 1] + a, cur[j] + b[j]
                    cur[j + 1] = x if x < y else y
            prev = cur
        return prev[m]
''',
    tests=[
        ["sea", "eat"],
        ["delete", "leet"],
        ["a", "a"],
        ["a", "b"],
        ["abc", "abc"],
        ["az", "za"],
        ["ab", "ba"],
        ["zzzb", "bzzz"],
        ["aab", "baa"],
        ["xnbteodleejrzeo", "gaouojqkkk"],
        [_s(40, "abz"), _s(40, "abz")],
        [_s(400, "abcxyz"), _s(400, "abcxyz")],
        [_s(700, "az"), _s(500, "az")],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def minimumDeleteSum(self, s1, s2):
        n, m = len(s1), len(s2)
        L = [[0] * (m + 1) for _ in range(n + 1)]
        for i in range(n):
            for j in range(m):
                L[i + 1][j + 1] = L[i][j] + 1 if s1[i] == s2[j] else max(L[i][j + 1], L[i + 1][j])
        keep, i, j = 0, n, m
        while i and j:
            if s1[i - 1] == s2[j - 1]:
                keep += ord(s1[i - 1]); i -= 1; j -= 1
            elif L[i - 1][j] >= L[i][j - 1]:
                i -= 1
            else:
                j -= 1
        return sum(map(ord, s1)) + sum(map(ord, s2)) - 2 * keep
''',
        '''class Solution:
    def minimumDeleteSum(self, s1, s2):
        from collections import Counter
        a, b = Counter(s1), Counter(s2)
        return sum(ord(ch) * abs(a[ch] - b[ch]) for ch in set(a) | set(b))
''',
    ],
    guide=dict(
        prereqs="Edit Distance and Longest Common Subsequence.",
        intuition=r"""
What survives the deletions is a common subsequence of the two strings. Deleting cheaply means
**keeping the common subsequence with the largest total ASCII value** — not necessarily the longest
one. The table has the Edit Distance shape with only "delete" moves, each priced by the letter.
""",
        hints=[
            "The remaining string is a common subsequence. Which one do you want to keep?",
            "cost(i, j) = cheapest way to make s1[:i] and s2[:j] equal. What if the last letters match?",
            "Match: cost(i-1, j-1). Else: min(cost(i-1, j) + ord(s1[i-1]), cost(i, j-1) + ord(s2[j-1])).",
        ],
        brute_force="Try deleting or keeping each character of both strings: 2^(n+m) possibilities.",
        approach=r"""
**State:** `cost(i, j)` for prefixes `s1[:i]`, `s2[:j]`.
**Base case:** `cost(i, 0)` = sum of ASCII of `s1[:i]` (delete everything); similarly `cost(0, j)`.
**Recurrence:** match → diagonal; otherwise the cheaper of deleting from `s1` or from `s2`.
**Answer:** `cost(n, m)`.

`"sea"` vs `"eat"` (s=115, e=101, a=97, t=116):

| | ∅ | e | a | t |
|---|---|---|---|---|
| ∅ | 0 | 101 | 198 | 314 |
| s | 115 | 216 | 313 | 429 |
| e | 216 | 115 | 212 | 328 |
| a | 313 | 212 | 115 | **231** |
""",
        complexity="Time O(n·m), space O(m).",
        pitfalls="- The longest common subsequence is not always the most valuable one to keep (`\"az\"` vs `\"za\"`: keep `z`, not `a`).\n- The base row/column are running sums, not zeros.",
        follow_up="Delete Operation for Two Strings is the same with every deletion costing 1.",
    ),
),
dict(
    id="shortest-common-supersequence",
    title="Shortest Common Supersequence",
    difficulty="Hard",
    pattern="2-D DP / Strings (reconstruction)",
    leetcode="https://leetcode.com/problems/shortest-common-supersequence/",
    entry="shortestCommonSupersequence",
    checker=_SCS_CHECKER,
    description=r"""
A string `T` is a **supersequence** of `S` if you can delete some characters of `T` (keeping the
order of the rest) and obtain `S`. Given `str1` and `str2`, return a shortest string that is a
supersequence of both. If several shortest answers exist, any one is accepted.

**Constraints**

- `1 <= len(str1), len(str2) <= 1000` (tests here use up to 300)
- lowercase English letters

**Example 1:** `str1 = "abac", str2 = "cab"` → `"cabac"`

**Example 2:** `str1 = "aaaa", str2 = "aaaa"` → `"aaaa"`
""",
    starter='''class Solution:
    def shortestCommonSupersequence(self, str1: str, str2: str) -> str:
        pass
''',
    solution='''class Solution:
    def shortestCommonSupersequence(self, str1, str2):
        n, m = len(str1), len(str2)
        L = [[0] * (m + 1) for _ in range(n + 1)]          # LCS lengths of prefixes
        for i in range(n):
            a, Li, Li1 = str1[i], L[i], L[i + 1]
            for j in range(m):
                if a == str2[j]:
                    Li1[j + 1] = Li[j] + 1
                else:
                    Li1[j + 1] = Li[j + 1] if Li[j + 1] > Li1[j] else Li1[j]
        out, i, j = [], n, m
        while i and j:                                     # walk back, emitting characters
            if str1[i - 1] == str2[j - 1]:
                out.append(str1[i - 1]); i -= 1; j -= 1    # shared letter: write it once
            elif L[i - 1][j] >= L[i][j - 1]:
                out.append(str1[i - 1]); i -= 1
            else:
                out.append(str2[j - 1]); j -= 1
        out.reverse()
        return str1[:i] + str2[:j] + "".join(out)
''',
    tests=[
        ["abac", "cab"],
        ["aaaa", "aaaa"],
        ["a", "b"],
        ["a", "a"],
        ["abc", "def"],
        ["abc", "abc"],
        ["bbbaaaba", "bbababbb"],
        ["geek", "eke"],
        ["aggtab", "gxtxayb"],
        ["ab", "ba"],
        [_s(30, "abc"), _s(25, "abc")],
        [_s(200, "abcd"), _s(180, "abcd")],
        [_s(300, "ab"), _s(300, "ab")],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def shortestCommonSupersequence(self, a, b):
        out, i, j = [], 0, 0
        while i < len(a) and j < len(b):
            if a[i] == b[j]:
                out.append(a[i]); i += 1; j += 1
            else:
                out.append(a[i]); i += 1
        return "".join(out) + a[i:] + b[j:]
''',
        '''class Solution:
    def shortestCommonSupersequence(self, a, b):
        k = 0
        for t in range(1, min(len(a), len(b)) + 1):
            if a.endswith(b[:t]):
                k = t
        return a + b[k:]
''',
    ],
    guide=dict(
        prereqs="Longest Common Subsequence, including walking the table backwards to rebuild the answer.",
        intuition=r"""
Letters that the two strings can **share** need to be written only once. The most letters they can
share, in order, is their longest common subsequence (LCS). So the shortest supersequence has length
`len(str1) + len(str2) − LCS`, and you build it by walking the LCS table backwards: shared letters
are written once, all other letters are written when you pass them.
""",
        hints=[
            "What is the length of the answer in terms of the LCS length?",
            "Build the full LCS table (you need all of it to reconstruct).",
            "Walk back from the bottom-right: equal letters → emit once, move diagonally; else emit the letter of the side you move away from.",
        ],
        brute_force="Try every interleaving of the two strings that merges equal letters: exponential (about C(n+m, n) interleavings).",
        approach=r"""
1. `L[i][j]` = LCS length of `str1[:i]`, `str2[:j]` (standard recurrence).
2. Start at `(n, m)` and repeat:
   - letters equal → output it once, go to `(i-1, j-1)`;
   - else if `L[i-1][j] >= L[i][j-1]` → output `str1[i-1]`, go up;
   - else → output `str2[j-1]`, go left.
3. Prepend whatever is left of either string, and reverse the collected letters.

`str1 = "abac"`, `str2 = "cab"`, LCS = `"ab"` (length 2) → answer length `4 + 3 − 2 = 5`.

| step | (i, j) | letters | action | output so far (reversed) |
|---|---|---|---|---|
| 1 | (4, 3) | c vs b | L up 2 ≥ L left 1 → take `c` from str1 | c |
| 2 | (3, 3) | a vs b | up 2 ≥ left 1 → take `a` | c a |
| 3 | (2, 3) | b vs b | equal → take `b` once | c a b |
| 4 | (1, 2) | a vs a | equal → take `a` once | c a b a |
| 5 | (0, 1) | – | leftover of str2: `c` | **cabac** |
""",
        complexity="Time O(n·m), space O(n·m) (the whole table is needed for reconstruction).",
        pitfalls="- Greedy merging with two pointers produces a valid but not shortest supersequence.\n- Forgetting the leftover prefix of one string when the other runs out.\n- Building the answer by repeated string concatenation in the loop is quadratic; collect in a list.",
        follow_up="If only the length is needed, two rows suffice. The same walk-back prints an actual LCS or an edit script.",
    ),
),
dict(
    id="ones-and-zeroes",
    title="Ones and Zeroes",
    difficulty="Medium",
    pattern="2-D DP / 0-1 Knapsack (two budgets)",
    leetcode="https://leetcode.com/problems/ones-and-zeroes/",
    entry="findMaxForm",
    description=r"""
`strs` is a list of binary strings. Pick as many strings as you can so that, counted over all picked
strings, there are **at most `m` zeros and at most `n` ones**. Each string can be picked at most
once. Return the largest number of strings you can pick.

**Constraints**

- `1 <= len(strs) <= 600`, `1 <= len(strs[i]) <= 100`
- `1 <= m, n <= 100`

**Example 1:** `strs = ["10","0001","111001","1","0"], m = 5, n = 3` → `4`
(`"10"`, `"0001"`, `"1"`, `"0"` use 5 zeros and 3 ones)

**Example 2:** `strs = ["10","0","1"], m = 1, n = 1` → `2`
""",
    starter='''class Solution:
    def findMaxForm(self, strs: List[str], m: int, n: int) -> int:
        pass
''',
    solution='''class Solution:
    def findMaxForm(self, strs, m, n):
        best = [[0] * (n + 1) for _ in range(m + 1)]     # best[z][o]: max strings with z zeros, o ones allowed
        for s in strs:
            zeros = s.count("0")
            ones = len(s) - zeros
            for z in range(m, zeros - 1, -1):            # both budgets DOWNWARD: each string once
                row, src = best[z], best[z - zeros]
                for o in range(n, ones - 1, -1):
                    if src[o - ones] + 1 > row[o]:
                        row[o] = src[o - ones] + 1
        return best[m][n]
''',
    tests=[
        [["10", "0001", "111001", "1", "0"], 5, 3],
        [["10", "0", "1"], 1, 1],
        [["11", "100", "001"], 4, 2],
        [["10"], 2, 2],
        [["111"], 5, 2],
        [["0", "0", "0", "0"], 2, 5],
        [["10", "01", "10", "01"], 2, 2],
        [["0", "1", "00", "11", "000", "111"], 3, 3],
        [["0001", "0101", "1000", "1000"], 9, 3],
        [["011", "1", "11", "0", "010", "1", "10", "1", "1", "0", "0", "0", "01111", "011", "11", "00", "11", "10", "1", "0"], 9, 9],
        [[_s(_R.randint(1, 8), "01") for _ in range(60)], 20, 20],
        [[_s(_R.randint(1, 30), "01") for _ in range(200)], 100, 100],
        [[_s(_R.randint(1, 12), "01") for _ in range(300)], 60, 45],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def findMaxForm(self, strs, m, n):
        count = 0
        for s in sorted(strs, key=len):
            z = s.count("0"); o = len(s) - z
            if z <= m and o <= n:
                m -= z; n -= o; count += 1
        return count
''',
        '''class Solution:
    def findMaxForm(self, strs, m, n):
        best = [[0] * (n + 1) for _ in range(m + 1)]
        for s in strs:
            zeros = s.count("0"); ones = len(s) - zeros
            for z in range(zeros, m + 1):
                for o in range(ones, n + 1):
                    best[z][o] = max(best[z][o], best[z - zeros][o - ones] + 1)
        return best[m][n]
''',
    ],
    guide=dict(
        prereqs="0/1 Knapsack (`dp-knapsack-01`); lesson *Knapsack: 0/1 and unbounded*.",
        intuition=r"""
This is a 0/1 knapsack with **two** capacities instead of one: a budget of zeros and a budget of
ones. Each string "weighs" (its zeros, its ones) and is worth 1. The state simply gets a second
capacity index.
""",
        hints=[
            "Count the zeros and ones of each string first; the letters' order no longer matters.",
            "best[z][o] = most strings you can take with at most z zeros and o ones.",
            "For each string, update z from m down to zeros and o from n down to ones: best[z][o] = max(best[z][o], best[z-zeros][o-ones] + 1).",
        ],
        brute_force="Try every subset of strings: 2⁶⁰⁰ subsets.",
        approach=r"""
**State:** `best(i, z, o)` = most strings among the first `i` using ≤ `z` zeros and ≤ `o` ones.
**Recurrence:** skip → `best(i-1, z, o)`; take → `1 + best(i-1, z − zeros_i, o − ones_i)`.
**Base case:** 0 strings → 0. **Answer:** `best(len, m, n)`.

The string index is dropped by iterating both budgets **downward** (exactly the 1-D knapsack trick, in
two dimensions).

`strs = ["10", "0", "1"]`, `m = 1, n = 1` — table `best[z][o]` after each string:

| after | best[0][0] | best[0][1] | best[1][0] | best[1][1] |
|---|---|---|---|---|
| "10" (1 zero, 1 one) | 0 | 0 | 0 | 1 |
| "0" (1 zero) | 0 | 0 | 1 | 1 |
| "1" (1 one) | 0 | 1 | 1 | **2** |

Final cell: take `"1"` on top of `best[1][0] = 1` → 2.
""",
        complexity="Time O(len(strs) · m · n) — at most 600 · 100 · 100 = 6·10⁶ simple steps; space O(m · n).",
        pitfalls="- Iterating the budgets upward lets one string be used many times.\n- Greedy 'shortest strings first' fails: with `[\"11\",\"100\",\"001\"]`, m = 4, n = 2 it takes `\"11\"` and is stuck at 1, while the other two give 2.",
        follow_up="Any knapsack with k independent resource limits adds k capacity indices; cost grows as the product of the limits.",
    ),
),
dict(
    id="last-stone-weight-ii",
    title="Last Stone Weight II",
    difficulty="Medium",
    pattern="2-D DP / Subset Sum",
    leetcode="https://leetcode.com/problems/last-stone-weight-ii/",
    neetcode="https://neetcode.io/problems/last-stone-weight-ii",
    entry="lastStoneWeightII",
    description=r"""
You have stones with positive integer weights. Repeatedly choose **any** two stones and smash them
together: if they weigh the same both vanish; otherwise the lighter one vanishes and the heavier one
loses the lighter one's weight. Continue until at most one stone is left. Return the smallest
possible weight of that last stone (0 if none remains).

**Constraints**

- `1 <= len(stones) <= 30`
- `1 <= stones[i] <= 100`

**Example 1:** `stones = [2, 7, 4, 1, 8, 1]` → `1`

**Example 2:** `stones = [31, 26, 33, 21, 40]` → `5`
""",
    starter='''class Solution:
    def lastStoneWeightII(self, stones: List[int]) -> int:
        pass
''',
    solution='''class Solution:
    def lastStoneWeightII(self, stones):
        total = sum(stones)
        half = total // 2
        reach = [True] + [False] * half          # reach[s]: some group of stones weighs exactly s
        for w in stones:
            for s in range(half, w - 1, -1):
                if reach[s - w]:
                    reach[s] = True
        best = max(s for s in range(half + 1) if reach[s])
        return total - 2 * best
''',
    tests=[
        [[2, 7, 4, 1, 8, 1]],
        [[31, 26, 33, 21, 40]],
        [[1]],
        [[1, 2]],
        [[5, 5]],
        [[1, 1, 1]],
        [[100, 1, 1, 1]],
        [[3, 3, 3, 3, 3]],
        [[10, 20, 30, 40, 50]],
        [[89, 23, 100, 93, 82, 98, 91, 85, 33, 95, 72, 98, 63, 46, 17, 91, 92, 72, 77, 79, 99, 96, 55, 72, 24, 98, 79, 93, 88, 92]],
        [_ints(30, 1, 100)],
        [_ints(30, 50, 100)],
        [[97] * 15 + [89] * 15],
    ],
    examples=2,
    wrong_solutions=[
        '''import heapq
class Solution:
    def lastStoneWeightII(self, stones):
        h = [-x for x in stones]
        heapq.heapify(h)
        while len(h) > 1:
            a, b = -heapq.heappop(h), -heapq.heappop(h)
            if a != b:
                heapq.heappush(h, -(a - b))
        return -h[0] if h else 0
''',
        '''class Solution:
    def lastStoneWeightII(self, stones):
        a = b = 0
        for w in sorted(stones, reverse=True):
            if a <= b:
                a += w
            else:
                b += w
        return abs(a - b)
''',
    ],
    guide=dict(
        prereqs="Partition Equal Subset Sum.",
        intuition=r"""
Every smash subtracts one weight from another, so in the end each stone's weight has been either
**added or subtracted**: the last stone weighs `|sum of group A − sum of group B|` for some split of
the stones into two groups — and every split can be achieved. So: split the stones into two groups
whose sums are as close as possible. That is "find the largest subset sum not exceeding total / 2".
""",
        hints=[
            "Always smashing the two heaviest stones (the Last Stone Weight I rule) is not optimal here.",
            "Think of putting + or − in front of each stone. What does the final weight equal?",
            "Find the largest reachable subset sum s ≤ total // 2 (0/1 knapsack), then answer total − 2·s.",
        ],
        brute_force="Try both signs for every stone: 2³⁰ ≈ 10⁹ assignments.",
        approach=r"""
**State:** `reach[s]` = some subset of the stones seen so far sums to `s` (only `s ≤ total // 2`).
**Recurrence:** for each stone `w`, `reach[s] |= reach[s − w]`, `s` going **down**.
**Base case:** `reach[0] = True`. **Answer:** `total − 2 · max{s : reach[s]}`.

`stones = [2, 7, 4, 1, 8, 1]`, total 23, half 11:

| after stone | reachable sums ≤ 11 |
|---|---|
| 2 | 0, 2 |
| 7 | 0, 2, 7, 9 |
| 4 | 0, 2, 4, 6, 7, 9, 11 |
| 1, 8, 1 | every value 0 … 11 |

Largest is 11 → `23 − 22 = 1`.
""",
        complexity="Time O(n · total/2) ≤ 30 · 1500; space O(total).",
        pitfalls="- Simulating with a max-heap answers a different question (Last Stone Weight I) and fails on Example 2 (gives 9).\n- Upward loop reuses a stone.",
        follow_up="Target Sum counts the sign assignments; Partition Equal Subset Sum asks whether the difference can be 0.",
    ),
),
dict(
    id="best-time-to-buy-and-sell-stock-with-transaction-fee",
    title="Best Time to Buy and Sell Stock with Transaction Fee",
    difficulty="Medium",
    pattern="2-D DP / State Machine",
    leetcode="https://leetcode.com/problems/best-time-to-buy-and-sell-stock-with-transaction-fee/",
    entry="maxProfit",
    description=r"""
`prices[i]` is a share's price on day `i`. You may buy and sell as often as you like, holding at
most one share at a time, but every completed buy-and-sell pair costs a fixed `fee`. Return the
largest profit you can end with.

**Constraints**

- `1 <= len(prices) <= 5 * 10^4`
- `1 <= prices[i] < 5 * 10^4`, `0 <= fee < 5 * 10^4`

**Example 1:** `prices = [1, 3, 2, 8, 4, 9], fee = 2` → `8`
(buy at 1, sell at 8: 8 − 1 − 2 = 5; buy at 4, sell at 9: 9 − 4 − 2 = 3)

**Example 2:** `prices = [1, 3, 7, 5, 10, 3], fee = 3` → `6`
""",
    starter='''class Solution:
    def maxProfit(self, prices: List[int], fee: int) -> int:
        pass
''',
    solution='''class Solution:
    def maxProfit(self, prices, fee):
        hold = float("-inf")     # best profit while owning a share
        cash = 0                 # best profit while owning nothing
        for p in prices:
            hold, cash = max(hold, cash - p), max(cash, hold + p - fee)
        return cash
''',
    tests=[
        [[1, 3, 2, 8, 4, 9], 2],
        [[1, 3, 7, 5, 10, 3], 3],
        [[5], 1],
        [[1, 2], 0],
        [[1, 2], 5],
        [[9, 8, 7, 1, 2], 3],
        [[1, 4, 6, 2, 8, 3, 10, 14], 3],
        [[2, 1, 4, 4, 2, 3, 2, 5, 1, 2], 1],
        [[1, 5, 9], 2],
        [[4, 5, 2, 4, 3, 3, 1, 2, 5, 4], 1],
        [_ints(200, 1, 100), 7],
        [_ints(20000, 1, 49999), 1500],
        [_ints(20000, 1, 1000), 0],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def maxProfit(self, prices, fee):
        return sum(max(0, b - a - fee) for a, b in zip(prices, prices[1:]))
''',
        '''class Solution:
    def maxProfit(self, prices, fee):
        hold, cash = float("-inf"), 0
        for p in prices:
            hold = max(hold, cash - p)
            cash = max(cash, hold + p)
        return max(0, cash - fee)
''',
    ],
    guide=dict(
        prereqs="Best Time to Buy and Sell Stock with Cooldown; lesson *Counting knapsacks and state machines*.",
        intuition=r"""
At the end of each day you are in one of two situations: **holding** a share or holding **cash**
only. Each day you either stay as you are, buy (cash → hold, paying the price) or sell (hold → cash,
receiving the price minus the fee). Keep the best profit for each situation.
""",
        hints=[
            "Without a fee you would take every upward step. With a fee, small wiggles are not worth trading.",
            "Track two numbers per day: best profit if holding, best profit if not holding.",
            "hold = max(hold, cash - p); cash = max(cash, hold + p - fee) — computed from yesterday's values.",
        ],
        brute_force="Decide buy / sell / wait on every day recursively: up to 2ⁿ useful decision sequences.",
        approach=r"""
**State:** `(day, mode)` with mode ∈ {hold, cash}.
**Recurrence:** `hold' = max(hold, cash − p)`, `cash' = max(cash, hold + p − fee)`.
**Base case:** `hold = −∞`, `cash = 0`. **Answer:** final `cash`.

`prices = [1, 3, 2, 8, 4, 9]`, `fee = 2`:

| day | price | hold | cash |
|---|---|---|---|
| 0 | 1 | −1 | 0 |
| 1 | 3 | −1 | 0 |
| 2 | 2 | −1 | 0 |
| 3 | 8 | −1 | 5 |
| 4 | 4 | 1 | 5 |
| 5 | 9 | 1 | **8** |

On day 1 selling would give −1 + 3 − 2 = 0, no better than waiting.
""",
        complexity="Time O(n), space O(1).",
        pitfalls="- The fee is paid once per completed trade, not per day and not once overall.\n- Use simultaneous assignment so today's `cash` is not built from today's `hold` (here it happens to be harmless, but it is a bad habit in the cooldown variant).",
        follow_up="Charging the fee at buy time instead (`cash − p − fee`) gives the same answer. Adding a limit of k trades adds an index to the state.",
    ),
),
dict(
    id="best-time-to-buy-and-sell-stock-iii",
    title="Best Time to Buy and Sell Stock III",
    difficulty="Hard",
    pattern="2-D DP / State Machine",
    leetcode="https://leetcode.com/problems/best-time-to-buy-and-sell-stock-iii/",
    entry="maxProfit",
    description=r"""
`prices[i]` is a share's price on day `i`. You may complete **at most two** buy-then-sell
transactions, and you must sell before buying again. Return the largest total profit (0 if no trade
is worthwhile).

**Constraints**

- `1 <= len(prices) <= 10^5`
- `0 <= prices[i] <= 10^5`

**Example 1:** `prices = [3, 3, 5, 0, 0, 3, 1, 4]` → `6` (buy 0 sell 3, buy 1 sell 4)

**Example 2:** `prices = [1, 2, 3, 4, 5]` → `4` (one trade: buy 1 sell 5)

**Example 3:** `prices = [7, 6, 4, 3, 1]` → `0`
""",
    starter='''class Solution:
    def maxProfit(self, prices: List[int]) -> int:
        pass
''',
    solution='''class Solution:
    def maxProfit(self, prices):
        NEG = float("-inf")
        buy1 = buy2 = NEG      # best balance while holding the 1st / 2nd share
        sell1 = sell2 = 0      # best balance after 1 / 2 completed trades
        for p in prices:
            buy1, sell1, buy2, sell2 = (
                max(buy1, -p),
                max(sell1, buy1 + p),
                max(buy2, sell1 - p),
                max(sell2, buy2 + p),
            )
        return sell2
''',
    tests=[
        [[3, 3, 5, 0, 0, 3, 1, 4]],
        [[1, 2, 3, 4, 5]],
        [[7, 6, 4, 3, 1]],
        [[1]],
        [[1, 2]],
        [[2, 1]],
        [[1, 2, 4, 2, 5, 7, 2, 4, 9, 0]],
        [[6, 1, 3, 2, 4, 7]],
        [[1, 4, 2, 7, 2, 9]],
        [[2, 1, 2, 0, 1]],
        [_ints(100, 0, 50)],
        [_ints(20000, 0, 100000)],
        [[(i * 7919) % 1000 for i in range(20000)]],
    ],
    examples=3,
    wrong_solutions=[
        '''class Solution:
    def maxProfit(self, prices):
        return sum(max(0, b - a) for a, b in zip(prices, prices[1:]))
''',
        '''class Solution:
    def maxProfit(self, prices):
        runs, lo = [], prices[0]
        for a, b in zip(prices, prices[1:]):
            if b < a:
                runs.append(a - lo)
                lo = b
        runs.append(prices[-1] - lo)
        return sum(sorted(runs, reverse=True)[:2])
''',
    ],
    guide=dict(
        prereqs="The stock state-machine pattern (cooldown / fee problems).",
        intuition=r"""
Walk through the days keeping four "best balance so far" numbers, one for each stage of the plan:
holding the first share, having sold it, holding the second share, having sold that too. Each stage
can only be entered from the stage before it, so one pass updates all four.
""",
        hints=[
            "Unlimited trades would be easy (take every rise). The limit of two is what needs extra state.",
            "Stages: buy1 → sell1 → buy2 → sell2. Keep the best money balance at each stage.",
            "buy1 = max(buy1, -p); sell1 = max(sell1, buy1 + p); buy2 = max(buy2, sell1 - p); sell2 = max(sell2, buy2 + p).",
        ],
        brute_force="Choose up to four days (buy, sell, buy, sell) in every possible way: O(n⁴) — 10²⁰ for n = 10⁵. Recursing over buy/sell/wait decisions is exponential.",
        approach=r"""
**State:** `(day, stage)` with four stages. **Base case:** `buy = −∞`, `sell = 0`.
**Recurrence:** as in the hints. **Answer:** `sell2` (it also covers "one trade" and "no trade").

`prices = [3, 3, 5, 0, 0, 3, 1, 4]`:

| price | buy1 | sell1 | buy2 | sell2 |
|---|---|---|---|---|
| 3 | −3 | 0 | −3 | 0 |
| 3 | −3 | 0 | −3 | 0 |
| 5 | −3 | 2 | −3 | 2 |
| 0 | 0 | 2 | 2 | 2 |
| 0 | 0 | 2 | 2 | 2 |
| 3 | 0 | 3 | 2 | 5 |
| 1 | 0 | 3 | 2 | 5 |
| 4 | 0 | 4 | 2 | **6** |
""",
        complexity="Time O(n), space O(1).",
        pitfalls="- Summing every rise ignores the two-trade limit.\n- 'Take the two biggest rising runs' fails when the best trade spans a small dip (e.g. `[1, 4, 2, 7, 2, 9]`).\n- You cannot hold two shares at once.",
        follow_up="Stock IV allows k trades: arrays `buy[1..k]`, `sell[1..k]` with the same updates, O(n·k).",
    ),
),
dict(
    id="count-vowels-permutation",
    title="Count Vowels Permutation",
    difficulty="Hard",
    pattern="2-D DP / State Machine (counting)",
    leetcode="https://leetcode.com/problems/count-vowels-permutation/",
    entry="countVowelPermutation",
    description=r"""
Count the strings of length `n` made only of the lowercase vowels `a, e, i, o, u` that obey these
rules about which letter may come **next**:

- after `a` only `e` may follow;
- after `e` only `a` or `i`;
- after `i` anything except another `i`;
- after `o` only `i` or `u`;
- after `u` only `a`.

Return the count modulo `1_000_000_007` (that is, the remainder after dividing by 10⁹ + 7).

**Constraints**

- `1 <= n <= 2 * 10^4`

**Example 1:** `n = 1` → `5`

**Example 2:** `n = 2` → `10` (ae, ea, ei, ia, ie, io, iu, oi, ou, ua)

**Example 3:** `n = 5` → `68`
""",
    starter='''class Solution:
    def countVowelPermutation(self, n: int) -> int:
        pass
''',
    solution='''class Solution:
    def countVowelPermutation(self, n):
        MOD = 1_000_000_007
        a = e = i = o = u = 1                 # strings of the current length ENDING in each vowel
        for _ in range(n - 1):
            a, e, i, o, u = (
                (e + i + u) % MOD,            # 'a' can come after e, i, u
                (a + i) % MOD,                # 'e' can come after a, i
                (e + o) % MOD,                # 'i' can come after e, o
                i % MOD,                      # 'o' can come after i
                (i + o) % MOD,                # 'u' can come after i, o
            )
        return (a + e + i + o + u) % MOD
''',
    tests=[[1], [2], [5], [3], [4], [6], [10], [50], [144], [1000], [5000], [19999], [20000]],
    examples=3,
    wrong_solutions=[
        '''class Solution:
    def countVowelPermutation(self, n):
        a = e = i = o = u = 1
        for _ in range(n - 1):
            a, e, i, o, u = e + i + u, a + i, e + o, i, i + o
        return a + e + i + o + u
''',
        '''class Solution:
    def countVowelPermutation(self, n):
        MOD = 1_000_000_007
        a = e = i = o = u = 1
        for _ in range(n - 1):
            a, e, i, o, u = (e + i + u) % MOD, (a + i) % MOD, (e + i + o) % MOD, i % MOD, (i + o) % MOD
        return (a + e + i + o + u) % MOD
''',
    ],
    guide=dict(
        prereqs="State-machine DP; counting with `+`.",
        intuition=r"""
Whether a letter may be appended depends only on the **last letter** of the string so far. So you
never need the whole string — only how many valid strings of the current length end in each of the
five vowels. Extending by one letter turns those five counts into five new counts.
""",
        hints=[
            "What information about a partial string decides which letters may come next?",
            "Keep five counters: number of valid strings of length L ending in a, e, i, o, u.",
            "Turn the 'what may follow X' rules around into 'what may come before X'. E.g. 'a' may follow e, i or u.",
        ],
        brute_force="Generate strings letter by letter following the rules. The count roughly doubles every couple of letters, so n = 20,000 is unimaginably large.",
        approach=r"""
Reverse the rules to "which letters can be **before** X":

| new last letter | previous letter may be |
|---|---|
| a | e, i, u |
| e | a, i |
| i | e, o |
| o | i |
| u | i, o |

**State:** `cnt[L][v]` = valid strings of length `L` ending in vowel `v`.
**Recurrence:** e.g. `cnt[L][a] = cnt[L-1][e] + cnt[L-1][i] + cnt[L-1][u]`.
**Base case:** `cnt[1][v] = 1`. **Answer:** sum of the five counts for length `n`, modulo 10⁹ + 7.

| L | a | e | i | o | u | total |
|---|---|---|---|---|---|---|
| 1 | 1 | 1 | 1 | 1 | 1 | 5 |
| 2 | 3 | 2 | 2 | 1 | 2 | 10 |
| 3 | 6 | 5 | 3 | 2 | 3 | 19 |
""",
        complexity="Time O(n), space O(1).",
        pitfalls="- Mixing up 'may follow' and 'may precede'.\n- Forgetting the modulo: counts have thousands of digits for large n and the expected answer is the remainder.\n- Updating the five counters one after another instead of all at once.",
        follow_up="Knight Dialer is the same idea with 10 states. For enormous n, raise the 5×5 transition matrix to the (n−1)-th power in O(log n).",
    ),
),
dict(
    id="out-of-boundary-paths",
    title="Out of Boundary Paths",
    difficulty="Medium",
    pattern="2-D DP / Grid + Steps",
    leetcode="https://leetcode.com/problems/out-of-boundary-paths/",
    entry="findPaths",
    description=r"""
A ball sits on cell `(startRow, startColumn)` of an `m × n` grid. One move pushes it to one of the
four neighbouring cells (up, down, left, right); a move across the edge takes the ball **out** of
the grid, where it stays. Count the different move sequences of length **at most** `maxMove` that
take the ball out of the grid. Return the count modulo `1_000_000_007`.

**Constraints**

- `1 <= m, n <= 50`, `0 <= maxMove <= 50`
- the start cell is inside the grid

**Example 1:** `m = 2, n = 2, maxMove = 2, startRow = 0, startColumn = 0` → `6`

**Example 2:** `m = 1, n = 3, maxMove = 3, startRow = 0, startColumn = 1` → `12`
""",
    starter='''class Solution:
    def findPaths(self, m: int, n: int, maxMove: int, startRow: int, startColumn: int) -> int:
        pass
''',
    solution='''class Solution:
    def findPaths(self, m, n, maxMove, startRow, startColumn):
        MOD = 1_000_000_007
        cur = [[0] * n for _ in range(m)]       # cur[r][c]: ways to be at (r, c) after k moves
        cur[startRow][startColumn] = 1
        out = 0
        for _ in range(maxMove):
            nxt = [[0] * n for _ in range(m)]
            for r in range(m):
                row = cur[r]
                for c in range(n):
                    w = row[c]
                    if not w:
                        continue
                    for a, b in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
                        if 0 <= a < m and 0 <= b < n:
                            nxt[a][b] = (nxt[a][b] + w) % MOD
                        else:
                            out = (out + w) % MOD      # this move leaves the grid
            cur = nxt
        return out
''',
    tests=[
        [2, 2, 2, 0, 0],
        [1, 3, 3, 0, 1],
        [1, 1, 0, 0, 0],
        [1, 1, 1, 0, 0],
        [1, 1, 5, 0, 0],
        [3, 3, 1, 1, 1],
        [3, 3, 2, 1, 1],
        [2, 3, 8, 1, 0],
        [8, 7, 16, 1, 5],
        [10, 10, 11, 5, 5],
        [8, 50, 23, 5, 26],
        [36, 5, 50, 15, 3],
        [50, 50, 50, 0, 0],
        [45, 35, 47, 20, 31],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def findPaths(self, m, n, maxMove, startRow, startColumn):
        cur = [[0] * n for _ in range(m)]
        cur[startRow][startColumn] = 1
        out = 0
        for _ in range(maxMove):
            nxt = [[0] * n for _ in range(m)]
            for r in range(m):
                for c in range(n):
                    w = cur[r][c]
                    if not w:
                        continue
                    for a, b in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
                        if 0 <= a < m and 0 <= b < n:
                            nxt[a][b] += w
                        else:
                            out += w
            cur = nxt
        return out
''',
        '''class Solution:
    def findPaths(self, m, n, maxMove, startRow, startColumn):
        MOD = 1_000_000_007
        cur = [[0] * n for _ in range(m)]
        cur[startRow][startColumn] = 1
        out = 0
        for _ in range(maxMove):
            nxt = [[0] * n for _ in range(m)]
            out = 0
            for r in range(m):
                for c in range(n):
                    w = cur[r][c]
                    for a, b in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
                        if 0 <= a < m and 0 <= b < n:
                            nxt[a][b] = (nxt[a][b] + w) % MOD
                        else:
                            out = (out + w) % MOD
            cur = nxt
        return out
''',
    ],
    guide=dict(
        prereqs="Unique Paths; lesson *Grid DP and DP on DAGs*.",
        intuition=r"""
Moves go in all four directions, so the grid position alone is not a valid DP state (you could walk
in circles). Add the **number of moves made** to the state: every move increases it by one, so the
states can never loop. Advance one move at a time, keeping how many ways the ball can be on each
cell; whenever a move would cross the edge, add those ways to the answer.
""",
        hints=[
            "Why can't dp[r][c] alone work here, when it did for Unique Paths?",
            "Let ways[k][r][c] = number of ways to be on (r, c) after exactly k moves without having left.",
            "For each of maxMove rounds, push every cell's count to its four neighbours; counts pushed off the grid are added to the answer.",
        ],
        brute_force="Explore all 4 directions for up to maxMove moves: 4⁵⁰ ≈ 10³⁰ sequences.",
        approach=r"""
**State:** `ways(k, r, c)` after exactly `k` moves, still inside.
**Recurrence:** `ways(k+1, r', c') += ways(k, r, c)` for each inside neighbour; outside neighbours add to `out`.
**Base case:** `ways(0, start) = 1`. **Order:** `k` increasing. **Answer:** `out` (mod 10⁹ + 7).

`m = 1, n = 3, maxMove = 3`, start in the middle (cells c0, c1, c2):

| move | ways before | leaves the grid on this move | ways after |
|---|---|---|---|
| 1 | [0, 1, 0] | 2 (up, down) | [1, 0, 1] |
| 2 | [1, 0, 1] | 3 + 3 = 6 | [0, 2, 0] |
| 3 | [0, 2, 0] | 2 · 2 = 4 | [2, 0, 2] |

Total 2 + 6 + 4 = **12**.
""",
        complexity="Time O(maxMove · m · n), space O(m · n).",
        pitfalls="- 'At most maxMove' means exits on **every** move count are added, not only the last.\n- Forgetting the modulo.\n- Once out, the ball stops — do not keep moving it.",
        follow_up="Knight Probability in Chessboard is the same layered DP with probabilities instead of counts.",
    ),
),
]
