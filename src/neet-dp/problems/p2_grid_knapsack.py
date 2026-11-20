import random

_R = random.Random(77)


def _grid(m, n, lo, hi):
    return [[_R.randint(lo, hi) for _ in range(n)] for _ in range(m)]


def _bin_grid(m, n, p_one):
    return [["1" if _R.random() < p_one else "0" for _ in range(n)] for _ in range(m)]


def _snake(m, n):
    g, v = [], 0
    for i in range(m):
        row = list(range(v, v + n))
        v += n
        g.append(row if i % 2 == 0 else row[::-1])
    return g


PROBLEMS = [
dict(
    id="unique-paths",
    title="Unique Paths",
    difficulty="Medium",
    pattern="2-D DP / Grid",
    leetcode="https://leetcode.com/problems/unique-paths/",
    neetcode="https://neetcode.io/problems/count-paths",
    entry="uniquePaths",
    description=r"""
A robot starts in the top-left cell of an `m × n` grid and wants to reach the bottom-right cell.
Each move goes exactly one cell **right** or one cell **down**. How many different routes are
there?

**Constraints**

- `1 <= m, n <= 100`
- tests are chosen so the answer is at most `2 * 10^9`

**Example 1:** `m = 3, n = 7` → `28`

**Example 2:** `m = 3, n = 2` → `3` (R-D-D, D-R-D, D-D-R)
""",
    starter='''class Solution:
    def uniquePaths(self, m: int, n: int) -> int:
        pass
''',
    solution='''class Solution:
    def uniquePaths(self, m, n):
        row = [1] * n
        for _ in range(1, m):
            for j in range(1, n):
                row[j] += row[j - 1]
        return row[-1]
''',
    tests=[[3, 7], [3, 2], [1, 1], [1, 100], [100, 1], [2, 2], [3, 3], [7, 3], [10, 10], [17, 17], [23, 12], [51, 9], [100, 3]],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def uniquePaths(self, m, n):
        return m * n
''',
        '''import math
class Solution:
    def uniquePaths(self, m, n):
        return math.comb(m + n, m)
''',
    ],
    guide=dict(
        prereqs="Lesson *Grid DP and DP on DAGs*.",
        intuition=r"""
The last move into cell `(i, j)` came from above or from the left, so
`paths(i, j) = paths(i-1, j) + paths(i, j-1)`. The first row and column each have exactly one route.
(Combinatorially: you make `m-1` downs and `n-1` rights in some order → $\binom{m+n-2}{m-1}$.)
""",
        hints=[
            "How many ways are there to reach any cell in the top row? In the left column?",
            "paths(i, j) = paths(i-1, j) + paths(i, j-1).",
            "One row of length n suffices: row[j] += row[j-1], repeated m-1 times.",
        ],
        brute_force="Recursively explore both moves from each cell: the number of calls equals the number of paths (times a constant) — 6·10⁸ for a 17×17 grid. Exponential in m + n.",
        approach=r"""
**State:** `paths(i, j)`. **Base:** `paths(0, j) = paths(i, 0) = 1`.
**Recurrence:** sum of top and left. **Order:** row by row, left to right. **Answer:** `paths(m-1, n-1)`.

`m = 3, n = 4`:

| | 0 | 1 | 2 | 3 |
|---|---|---|---|---|
| 0 | 1 | 1 | 1 | 1 |
| 1 | 1 | 2 | 3 | 4 |
| 2 | 1 | 3 | 6 | **10** |

Space optimisation: when processing row `i`, `row[j]` still holds the value from row `i-1` (the "top")
and `row[j-1]` was just updated (the "left"), so `row[j] += row[j-1]` is exactly the recurrence.
""",
        complexity="Time O(m·n), space O(n). The binomial formula is O(min(m, n)).",
        pitfalls="- `m = 1` or `n = 1` → exactly one path.\n- Off-by-one in the binomial: it's C(m+n−2, m−1), not C(m+n, m).",
        follow_up="Unique Paths II (obstacles: set a cell to 0), Minimum Path Sum (min instead of +), Dungeon Game (DP from the bottom-right).",
    ),
),
dict(
    id="minimum-path-sum",
    title="Minimum Path Sum",
    difficulty="Medium",
    pattern="2-D DP / Grid",
    leetcode="https://leetcode.com/problems/minimum-path-sum/",
    entry="minPathSum",
    description=r"""
A grid of non-negative integers is given. Walk from the top-left to the bottom-right cell moving
only **right** or **down**, and minimise the sum of all numbers on the cells you visit (both ends
included). Return that minimum sum.

**Constraints**

- `1 <= m, n <= 200`
- `0 <= grid[i][j] <= 200`

**Example 1:** `grid = [[1,3,1],[1,5,1],[4,2,1]]` → `7` (1→3→1→1→1)

**Example 2:** `grid = [[1,2,3],[4,5,6]]` → `12`
""",
    starter='''class Solution:
    def minPathSum(self, grid: List[List[int]]) -> int:
        pass
''',
    solution='''class Solution:
    def minPathSum(self, grid):
        n = len(grid[0])
        INF = float("inf")
        row = [INF] * n
        row[0] = 0
        for r in grid:
            row[0] += r[0]
            for j in range(1, n):
                row[j] = min(row[j], row[j - 1]) + r[j]
        return row[-1]
''',
    tests=[
        [[[1, 3, 1], [1, 5, 1], [4, 2, 1]]],
        [[[1, 2, 3], [4, 5, 6]]],
        [[[0]]],
        [[[7]]],
        [[[1, 2, 3, 4]]],
        [[[1], [2], [3]]],
        [[[1, 2], [5, 6], [1, 1]]],
        [[[1, 1, 9, 9], [9, 1, 9, 9], [9, 1, 1, 1], [9, 9, 9, 1]]],
        [[[1, 9, 1, 1, 1], [1, 9, 1, 9, 1], [1, 1, 1, 9, 1]]],
        [[[2, 1, 100], [100, 100, 100], [1, 1, 1]]],
        [_grid(20, 30, 0, 9)],
        [_grid(200, 200, 0, 200)],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def minPathSum(self, grid):
        m, n = len(grid), len(grid[0])
        i = j = 0
        total = grid[0][0]
        while (i, j) != (m - 1, n - 1):
            if i == m - 1:
                j += 1
            elif j == n - 1:
                i += 1
            elif grid[i + 1][j] < grid[i][j + 1]:
                i += 1
            else:
                j += 1
            total += grid[i][j]
        return total
''',
        '''class Solution:
    def minPathSum(self, grid):
        m, n = len(grid), len(grid[0])
        return min(sum(grid[0]) + sum(grid[i][-1] for i in range(1, m)),
                   sum(grid[i][0] for i in range(m)) + sum(grid[-1][1:]))
''',
    ],
    guide=dict(
        prereqs="Unique Paths.",
        intuition="Identical structure to Unique Paths, but each cell keeps the **cheapest** way to reach it: `best(i, j) = grid[i][j] + min(best(i-1, j), best(i, j-1))`.",
        hints=[
            "Greedily stepping to the cheaper neighbour can lead into an expensive region later.",
            "best(i, j) depends only on the cell above and the cell to the left.",
            "Fill row by row; the first row and column only have one predecessor each.",
        ],
        brute_force="Enumerate all C(m+n−2, m−1) monotone paths recursively — astronomically many for a 200×200 grid.",
        approach=r"""
**State:** `best(i, j)` = min sum of a path from (0,0) to (i,j), inclusive.
**Recurrence:** `grid[i][j] + min(best(i-1, j), best(i, j-1))` (missing neighbours count as ∞).
**Base:** `best(0,0) = grid[0][0]`. **Answer:** `best(m-1, n-1)`.

For `[[1,3,1],[1,5,1],[4,2,1]]`:

| | 0 | 1 | 2 |
|---|---|---|---|
| 0 | 1 | 4 | 5 |
| 1 | 2 | 7 | 6 |
| 2 | 6 | 8 | **7** |

One row is enough: `row[j] = min(row[j] (top), row[j-1] (left)) + grid[i][j]`.
""",
        complexity="Time O(m·n), space O(n) (or O(1) by overwriting the grid, if mutation is allowed).",
        pitfalls="- Initialising the first row/column with 0 instead of prefix sums.\n- Greedy neighbour choice fails (see the test with a cheap first step into an expensive row).",
        follow_up="Triangle (same DP on a triangle, bottom-up), Dungeon Game, Cherry Pickup (two walkers → 3-D state).",
    ),
),
dict(
    id="maximal-square",
    title="Maximal Square",
    difficulty="Medium",
    pattern="2-D DP / Grid",
    leetcode="https://leetcode.com/problems/maximal-square/",
    entry="maximalSquare",
    description=r"""
`matrix` is a 2-D grid of the characters `"0"` and `"1"`. Find the largest axis-aligned square that
contains only `"1"` cells and return its **area**.

**Constraints**

- `1 <= m, n <= 300`
- `matrix[i][j]` is `"0"` or `"1"`

**Example 1:**
```
1 0 1 0 0
1 0 1 1 1
1 1 1 1 1
1 0 0 1 0
```
→ `4` (a 2×2 block of ones)

**Example 2:** `matrix = [["0","1"],["1","0"]]` → `1`
""",
    starter='''class Solution:
    def maximalSquare(self, matrix: List[List[str]]) -> int:
        pass
''',
    solution='''class Solution:
    def maximalSquare(self, matrix):
        n = len(matrix[0])
        prev = [0] * (n + 1)
        best = 0
        for row in matrix:
            cur = [0] * (n + 1)
            for j in range(1, n + 1):
                if row[j - 1] == "1":
                    cur[j] = 1 + min(prev[j], cur[j - 1], prev[j - 1])
                    if cur[j] > best:
                        best = cur[j]
            prev = cur
        return best * best
''',
    tests=[
        [[["1", "0", "1", "0", "0"], ["1", "0", "1", "1", "1"], ["1", "1", "1", "1", "1"], ["1", "0", "0", "1", "0"]]],
        [[["0", "1"], ["1", "0"]]],
        [[["0"]]],
        [[["1"]]],
        [[["0", "1"], ["1", "1"]]],
        [[["1", "1"], ["1", "1"]]],
        [[["1", "1", "1", "0"], ["1", "1", "1", "0"], ["1", "1", "0", "0"]]],
        [[["1", "1", "1", "1", "1"]]],
        [[["1", "1", "0", "1"], ["1", "1", "0", "1"], ["1", "1", "1", "1"]]],
        [[["1"] * 6 for _ in range(6)]],
        [_bin_grid(50, 60, 0.8)],
        [_bin_grid(130, 130, 0.93)],
        [[["1"] * 120 for _ in range(110)]],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def maximalSquare(self, matrix):
        n = len(matrix[0])
        prev = [0] * (n + 1)
        best = 0
        for row in matrix:
            cur = [0] * (n + 1)
            for j in range(1, n + 1):
                if row[j - 1] == "1":
                    cur[j] = 1 + min(prev[j], cur[j - 1])
                    best = max(best, cur[j])
            prev = cur
        return best * best
''',
        '''class Solution:
    def maximalSquare(self, matrix):
        best = 0
        for row in matrix:
            run = 0
            for c in row:
                run = run + 1 if c == "1" else 0
                best = max(best, run)
        return min(best, len(matrix)) ** 2
''',
    ],
    guide=dict(
        prereqs="Unique Paths; lesson *Grid DP and DP on DAGs*.",
        intuition=r"""
Let `side(i, j)` be the side of the largest all-ones square whose **bottom-right corner** is
`(i, j)`. Such a square of side `k` exists iff the squares ending at the top, left and top-left
neighbours all have side ≥ `k-1`. Hence `side = 1 + min(top, left, diag)`.
""",
        hints=[
            "Anchor squares by their bottom-right corner.",
            "A k×k square at (i, j) contains (k−1)×(k−1) squares at (i−1, j), (i, j−1) and (i−1, j−1).",
            "side(i, j) = 1 + min(side(i-1, j), side(i, j-1), side(i-1, j-1)) when the cell is '1'; return best².",
        ],
        brute_force="For every cell, try growing a square while all cells are '1': O((mn)²) in the worst case — billions of checks on a 300×300 grid of ones.",
        approach=r"""
**State:** `side(i, j)`. **Base:** padding row/column of zeros. **Recurrence:** above (0 if the cell is "0").
**Answer:** `(max side)²` — remember the problem asks for the **area**.

Example 1 side table:

| | 0 | 1 | 2 | 3 | 4 |
|---|---|---|---|---|---|
| 0 | 1 | 0 | 1 | 0 | 0 |
| 1 | 1 | 0 | 1 | 1 | 1 |
| 2 | 1 | 1 | 1 | **2** | **2** |
| 3 | 1 | 0 | 0 | 1 | 0 |

Max side 2 → area **4**.
""",
        complexity="Time O(m·n), space O(n) with two rows.",
        pitfalls=r"""
- Forgetting the diagonal neighbour: `[["0","1"],["1","1"]]` would give 4 instead of 1.
- Returning the side instead of the area.
- Cells are strings `"1"`, not integers.
""",
        follow_up="Count Square Submatrices with All Ones (sum the side table), Maximal Rectangle (histogram + stack per row).",
    ),
),
dict(
    id="dp-knapsack-01",
    title="0/1 Knapsack",
    difficulty="Medium",
    pattern="2-D DP / 0-1 Knapsack",
    entry="knapsack",
    description=r"""
You have `n` items; item `i` weighs `weights[i]` and is worth `values[i]`. Your bag holds a total
weight of at most `capacity`. Each item can be packed **at most once** (you can't take a
fraction). Return the maximum total value you can carry.

**Constraints**

- `0 <= n <= 200`, `len(weights) == len(values) == n`
- `1 <= weights[i] <= 1000`, `0 <= values[i] <= 10^4`
- `0 <= capacity <= 10^4`
- `n * capacity <= 10^6`

**Example 1:** `weights = [1, 3, 4, 5], values = [1, 4, 5, 7], capacity = 7` → `9` (items 1 and 2: weight 7, value 9)

**Example 2:** `weights = [10, 20, 30], values = [60, 100, 120], capacity = 50` → `220` (the best value-per-weight item, 60, is *not* in the optimum)
""",
    starter='''class Solution:
    def knapsack(self, weights: List[int], values: List[int], capacity: int) -> int:
        pass
''',
    solution='''class Solution:
    def knapsack(self, weights, values, capacity):
        best = [0] * (capacity + 1)        # best[c]: max value with weight <= c
        for w, v in zip(weights, values):
            for c in range(capacity, w - 1, -1):
                cand = best[c - w] + v
                if cand > best[c]:
                    best[c] = cand
        return best[capacity]
''',
    tests=[
        [[1, 3, 4, 5], [1, 4, 5, 7], 7],
        [[10, 20, 30], [60, 100, 120], 50],
        [[], [], 10],
        [[5], [10], 4],
        [[5], [10], 5],
        [[1, 1, 1], [10, 20, 30], 2],
        [[2, 3, 4, 5], [3, 4, 5, 6], 5],
        [[4, 5, 1], [1, 2, 3], 4],
        [[1, 2, 3], [6, 10, 12], 5],
        [[3, 3, 3, 3], [5, 5, 5, 5], 0],
        [[_R.randint(1, 30) for _ in range(30)], [_R.randint(0, 100) for _ in range(30)], 200],
        [[_R.randint(1, 1000) for _ in range(100)], [_R.randint(0, 10000) for _ in range(100)], 10000],
        [[_R.randint(20, 80) for _ in range(200)], [_R.randint(10, 500) for _ in range(200)], 5000],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def knapsack(self, weights, values, capacity):
        items = sorted(zip(weights, values), key=lambda wv: wv[1] / wv[0], reverse=True)
        total = 0
        for w, v in items:
            if w <= capacity:
                capacity -= w
                total += v
        return total
''',
        '''class Solution:
    def knapsack(self, weights, values, capacity):
        best = [0] * (capacity + 1)
        for w, v in zip(weights, values):
            for c in range(w, capacity + 1):
                best[c] = max(best[c], best[c - w] + v)
        return best[capacity]
''',
    ],
    guide=dict(
        prereqs="Lesson *Knapsack: 0/1 and unbounded* (this problem is its worked example).",
        intuition=r"""
Process items one at a time. For item `i` and remaining capacity `c` there are only two options:
**skip it** (value of the best packing of the earlier items with capacity `c`) or **take it** (its
value plus the best packing of earlier items with capacity `c - w_i`). The pair (items considered,
capacity) is the whole state.
""",
        hints=[
            "Greedy by value/weight ratio fails — see Example 2.",
            "Define best(i, c) = max value using the first i items with capacity c. Take or skip item i.",
            "best(i, c) = max(best(i-1, c), best(i-1, c-w) + v). One array works if c runs from capacity down to w.",
        ],
        brute_force="Include/exclude each item: 2ⁿ subsets. n = 200 is impossible; even n = 40 is 10¹².",
        approach=r"""
**State:** `best(i, c)`. **Base:** `best(0, c) = 0`.
**Recurrence:** `best(i, c) = max(best(i-1, c), best(i-1, c - w_i) + v_i)` (second term only if `w_i ≤ c`).
**Order:** items outer, capacities inner. **Answer:** `best(n, capacity)`.

Example 1 (`w = [1,3,4,5]`, `v = [1,4,5,7]`, capacity 7):

| items \ c | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
|---|---|---|---|---|---|---|---|---|
| none | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| +(1,1) | 0 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| +(3,4) | 0 | 1 | 1 | 4 | 5 | 5 | 5 | 5 |
| +(4,5) | 0 | 1 | 1 | 4 | 5 | 6 | 6 | 9 |
| +(5,7) | 0 | 1 | 1 | 4 | 5 | 7 | 8 | **9** |

**1-D version:** iterate `c` **downward** so `best[c - w]` still holds the previous item-row (item `i` not yet used).
""",
        complexity="Time O(n · capacity) — pseudo-polynomial (polynomial in the *value* of capacity, not its bit length). Space O(capacity).",
        pitfalls=r"""
- Upward inner loop = unbounded knapsack (items reused). On Example 1 that would pack item (1,1) seven times... and on `[1,1,1]/[10,20,30]` cap 2 it returns 60 instead of 50.
- `capacity = 0` or no items → 0.
- Greedy ratio is only optimal for the *fractional* knapsack.
""",
        follow_up="Reconstruct the chosen items by walking the 2-D table backwards. Variants: Partition Equal Subset Sum, Target Sum, Ones and Zeroes (two capacities), unbounded = Coin Change.",
    ),
),
dict(
    id="longest-increasing-path-in-a-matrix",
    title="Longest Increasing Path in a Matrix",
    difficulty="Hard",
    pattern="2-D DP / DAG + Memo DFS",
    leetcode="https://leetcode.com/problems/longest-increasing-path-in-a-matrix/",
    neetcode="https://neetcode.io/problems/longest-increasing-path-in-matrix",
    entry="longestIncreasingPath",
    description=r"""
Given an `m × n` integer matrix, find the length (number of cells) of the longest path in which
each step moves to one of the four orthogonal neighbours (up, down, left, right — no diagonals,
no wrapping) and every step goes to a **strictly larger** value.

**Constraints**

- `1 <= m, n <= 200`
- `0 <= matrix[i][j] <= 2^31 - 1`

**Example 1:** `matrix = [[9,9,4],[6,6,8],[2,1,1]]` → `4` (1 → 2 → 6 → 9)

**Example 2:** `matrix = [[3,4,5],[3,2,6],[2,2,1]]` → `4` (3 → 4 → 5 → 6)
""",
    starter='''class Solution:
    def longestIncreasingPath(self, matrix: List[List[int]]) -> int:
        pass
''',
    solution='''from collections import deque

class Solution:
    def longestIncreasingPath(self, matrix):
        m, n = len(matrix), len(matrix[0])
        out = [[0] * n for _ in range(m)]         # number of strictly larger neighbours
        dirs = ((1, 0), (-1, 0), (0, 1), (0, -1))
        for i in range(m):
            for j in range(n):
                v = matrix[i][j]
                for di, dj in dirs:
                    a, b = i + di, j + dj
                    if 0 <= a < m and 0 <= b < n and matrix[a][b] > v:
                        out[i][j] += 1
        layer = deque((i, j) for i in range(m) for j in range(n) if out[i][j] == 0)
        depth = 0
        while layer:                               # peel local maxima layer by layer
            depth += 1
            for _ in range(len(layer)):
                i, j = layer.popleft()
                v = matrix[i][j]
                for di, dj in dirs:
                    a, b = i + di, j + dj
                    if 0 <= a < m and 0 <= b < n and matrix[a][b] < v:
                        out[a][b] -= 1
                        if out[a][b] == 0:
                            layer.append((a, b))
        return depth
''',
    tests=[
        [[[9, 9, 4], [6, 6, 8], [2, 1, 1]]],
        [[[3, 4, 5], [3, 2, 6], [2, 2, 1]]],
        [[[1]]],
        [[[7, 7], [7, 7]]],
        [[[1, 2, 3, 4, 5]]],
        [[[5], [4], [3], [2], [1]]],
        [[[1, 2], [4, 3]]],
        [[[7, 8, 9], [9, 7, 6], [7, 2, 3]]],
        [_snake(4, 5)],
        [_snake(20, 20)],
        [_grid(30, 30, 0, 50)],
        [[[i * 120 + j for j in range(120)] for i in range(120)]],
        [_grid(110, 110, 0, 10 ** 6)],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def longestIncreasingPath(self, matrix):
        m, n = len(matrix), len(matrix[0])
        dp = [[1] * n for _ in range(m)]
        for i in range(m):
            for j in range(n):
                if i and matrix[i - 1][j] < matrix[i][j]:
                    dp[i][j] = max(dp[i][j], dp[i - 1][j] + 1)
                if j and matrix[i][j - 1] < matrix[i][j]:
                    dp[i][j] = max(dp[i][j], dp[i][j - 1] + 1)
        return max(map(max, dp))
''',
        '''class Solution:
    def longestIncreasingPath(self, matrix):
        m, n = len(matrix), len(matrix[0])
        best = 1
        for i in range(m):
            run = 1
            for j in range(1, n):
                run = run + 1 if matrix[i][j] > matrix[i][j - 1] else 1
                best = max(best, run)
        return best
''',
    ],
    guide=dict(
        prereqs="DFS on grids; lesson *Grid DP and DP on DAGs*.",
        intuition=r"""
Draw an edge from each cell to every strictly larger neighbour. Because values strictly increase
along edges, this graph has **no cycles** — it's a DAG. The longest path starting at a cell is
`1 + max(longest from each larger neighbour)`, and there's no circular dependency, so memoized DFS
(or a topological order) computes it once per cell.
""",
        hints=[
            "Unlike Unique Paths, moves go in all four directions, so a simple row-by-row fill doesn't work.",
            "Can an increasing path ever revisit a cell? What does that say about the dependency graph?",
            "lip(i, j) = 1 + max(lip(a, b) for larger neighbours); memoize with @cache or process cells in decreasing value order.",
        ],
        brute_force="DFS from every cell exploring all increasing paths without memo: exponential in the worst case (many branching increasing paths), and O((mn)²) even on simple snakes.",
        approach=r"""
**State:** `lip(i, j)` = length of the longest increasing path **starting** at `(i, j)`.
**Recurrence:** `1 + max(lip(nbr))` over neighbours with a larger value (or 1 if none).
**Order:** any topological order of the DAG — e.g. cells sorted by value **descending**, or the
memoized DFS's natural post-order. **Answer:** `max lip`.

The reference uses Kahn-style **layer peeling** (no recursion, so no recursion-depth limits):
local maxima form layer 1; removing them exposes the next layer; the number of layers equals the
longest path.

Dry run Example 1 (`[[9,9,4],[6,6,8],[2,1,1]]`):

| layer | cells peeled (value@row,col) |
|---|---|
| 1 | 9@0,0 · 9@0,1 · 8@1,2 (no larger neighbour) |
| 2 | 6@1,0 · 6@1,1 · 4@0,2 · 1@2,2 |
| 3 | 2@2,0 |
| 4 | 1@2,1 |

Four layers → answer **4** (the path 1 → 2 → 6 → 9 visits one cell per layer).

Memo DFS version:

```python
@cache
def lip(i, j):
    return 1 + max((lip(a, b) for a, b in nbrs(i, j) if M[a][b] > M[i][j]), default=0)
```
""",
        complexity="Time O(m·n) — each cell and edge is processed a constant number of times. Space O(m·n).",
        pitfalls=r"""
- Only scanning right/down misses paths that turn left or up.
- No `visited` set is needed — strictness already forbids cycles. Equal neighbours are **not** edges.
- Recursive DFS on a 200×200 snake can go 40,000 deep: raise `sys.setrecursionlimit` or use an iterative order.
""",
        follow_up="Longest path in any DAG; Number of Increasing Paths in a Grid (count instead of max, mod 1e9+7).",
    ),
),
]
