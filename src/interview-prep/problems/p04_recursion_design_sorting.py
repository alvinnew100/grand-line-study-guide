import random

R = random.Random(53)
G = ("prereqs", "intuition", "hints", "brute_force", "approach", "complexity", "pitfalls", "follow_up")


def _starter(sol):
    out = []
    for ln in sol.splitlines():
        s = ln.strip()
        if ln.startswith("class "):
            out.append(ln)
        elif s.startswith("def ") and (ln.startswith("    def ") or ln.startswith("def ")) and (
                not s.startswith("def _") or s.startswith("def __init__")):
            out.append(ln)
            out.append(ln[:len(ln) - len(ln.lstrip())] + "    pass")
    return "\n".join(out) + "\n"


def P(id, title, diff, pattern, entry, desc, sol, tests, wrong, guide, **kw):
    if "class Solution" not in sol:
        kw.setdefault("kind", "class")
    return dict(id="ctci-" + id, title=title, difficulty=diff, pattern=pattern, entry=entry,
                description=desc.strip() + "\n", starter=_starter(sol), solution=sol, tests=tests,
                wrong_solutions=wrong, guide=dict(zip(G, guide)), **kw)


def _ops(name, n, makers):
    ops, args = [name[0]], [name[1]]
    for _ in range(n):
        op, fn = R.choice(makers)
        ops.append(op)
        args.append(fn())
    return [ops, args]


def _maze(n, m, p):
    g = [[1 if R.random() < p else 0 for _ in range(m)] for _ in range(n)]
    g[0][0] = g[n - 1][m - 1] = 0
    return g


def _sparse(n, gap):
    words, out = sorted({"".join(R.choice("abcdefgh") for _ in range(R.randint(1, 6))) for _ in range(n)}), []
    for w in words:
        out.extend([""] * R.randint(0, gap))
        out.append(w)
    out.extend([""] * R.randint(0, gap))
    return out


_SP = _sparse(1500, 4)
_SPW = [w for w in _SP if w]
_stair = [[r * 100 + c * 3 for c in range(33)] for r in range(60)]
_times = sorted(R.randint(0, 4000) for _ in range(4000))
_people = 6000
_links = [[R.randrange(_people), R.randrange(_people)] for _ in range(7000)]
_words = ["".join(R.choice("abc") for _ in range(R.randint(1, 4))) for _ in range(1500)]

PROBLEMS = [
P("token-trail", "Token Trail", "Easy", "Recursion & DP", "countRoutes",
"""
In a board game a token starts in front of a trail of `n` squares and must finish **exactly on the last square**. Every move advances the token by **1, 2 or 3 squares**; it never moves backwards and may not overshoot.

How many different sequences of moves bring the token to the last square? Two sequences are different if they differ in any move, so `1 then 2` and `2 then 1` both count.

Return the count modulo `1_000_000_007`. A trail of zero squares has one sequence: the empty one.

**Constraints:** `0 <= n <= 10^5`.

**Example 1:** `n = 3` → `4` (1+1+1, 1+2, 2+1, 3)

**Example 2:** `n = 4` → `7`
""",
'''class Solution:
    def countRoutes(self, n: int) -> int:
        MOD = 1_000_000_007
        a, b, c = 1, 0, 0
        for _ in range(n):
            a, b, c = (a + b + c) % MOD, a, b
        return a
''',
[[3], [4], [0], [1], [2], [5], [6], [10], [36], [37], [1000], [99999], [100000]],
['''class Solution:
    def countRoutes(self, n):
        a, b = 1, 1
        for _ in range(n - 1):
            a, b = b, (a + b) % 1_000_000_007
        return b
''', '''class Solution:
    def countRoutes(self, n):
        return (3 ** n // 2 + 1) % 1_000_000_007 if n > 2 else max(n, 1)
'''],
("Recursion with overlapping subproblems: see [DP from recursion](#/lesson/neet-dp/dp-from-recursion).",
 "Look at the **last** move. It advanced the token 1, 2 or 3 squares, so before it the token stood on square n−1, n−2 or n−3. Every way to reach one of those extends to exactly one way to reach n, so ways(n) = ways(n−1) + ways(n−2) + ways(n−3).",
 ["Solve n = 1, 2, 3 by listing the sequences.",
  "Write the recurrence, then notice how many times the plain recursion recomputes ways(n−2).",
  "You only ever need the previous three values: keep three variables and roll them forward."],
 "Direct recursion with three branches takes roughly 1.84ⁿ calls: n = 40 already needs tens of billions.",
 "Keep `(a, b, c) = (ways(i), ways(i−1), ways(i−2))`, starting from `(1, 0, 0)` for i = 0. Each step: `a, b, c = a + b + c, a, b`.\n\nDry run: i=1 → (1,1,0); i=2 → (2,1,1); i=3 → (4,2,1); i=4 → (7,4,2). So ways(4) = 7.",
 "Time O(n), space O(1).",
 "Using the two-term Fibonacci recurrence. Wrong base cases: ways(0) must be 1, and negative positions count as 0. Forgetting the modulus only matters in languages with fixed-size integers, but apply it anyway to keep numbers small.",
 "Allow an arbitrary set of move lengths, or mark some squares as forbidden. The version with moves of 1 or 2 is [Climbing Stairs](#/problem/climbing-stairs).")),

P("grid-robot-path", "Warehouse Robot Path", "Medium", "Recursion & DP", "findPath",
"""
A warehouse floor is a grid where `0` is free and `1` is a shelf. A robot starts in the top-left cell and must reach the bottom-right cell. It can only move **down** (`"D"`) or **right** (`"R"`) and cannot enter a shelf.

Return the route as a string of moves. If several routes exist, return the one that comes **first alphabetically** (so prefer `D` over `R` whenever both lead to the goal). If no route exists, return `"NONE"`. For a 1 × 1 grid the route is the empty string.

**Constraints:** `1 <= rows, cols <= 150`; the start and goal cells are free.

**Example 1:** `[[0,0,0],[1,0,1],[0,0,0]]` → `"RDDR"`

**Example 2:** `[[0,1],[1,0]]` → `"NONE"`
""",
'''class Solution:
    def findPath(self, grid: List[List[int]]) -> str:
        n, m = len(grid), len(grid[0])
        ok = [[False] * (m + 1) for _ in range(n + 1)]
        for r in range(n - 1, -1, -1):
            for c in range(m - 1, -1, -1):
                if grid[r][c] == 0:
                    ok[r][c] = (r == n - 1 and c == m - 1) or ok[r + 1][c] or ok[r][c + 1]
        if not ok[0][0]:
            return "NONE"
        r = c = 0
        moves = []
        while (r, c) != (n - 1, m - 1):
            if ok[r + 1][c]:
                moves.append("D")
                r += 1
            else:
                moves.append("R")
                c += 1
        return "".join(moves)
''',
[[[[0, 0, 0], [1, 0, 1], [0, 0, 0]]], [[[0, 1], [1, 0]]], [[[0]]], [[[0, 0]]], [[[0], [0]]], [[[0, 0], [0, 0]]],
 [[[0, 0, 0], [0, 1, 0], [0, 0, 0]]], [[[0, 0, 0], [0, 0, 1], [1, 0, 0]]], [[[0, 0, 1], [0, 0, 0], [1, 1, 0]]],
 [[[0, 1, 0], [0, 1, 0], [0, 0, 0]]], [[[0, 0, 0, 0], [1, 1, 1, 0], [0, 0, 0, 0]]], [_maze(150, 150, 0.12)], [_maze(150, 150, 0.3)],
 [[[0] * 150 for _ in range(150)]], [_maze(40, 40, 0.2)], [_maze(30, 60, 0.15)]],
['''class Solution:
    def findPath(self, grid):
        n, m = len(grid), len(grid[0])
        r = c = 0
        moves = []
        while (r, c) != (n - 1, m - 1):
            if r + 1 < n and grid[r + 1][c] == 0:
                moves.append("D")
                r += 1
            elif c + 1 < m and grid[r][c + 1] == 0:
                moves.append("R")
                c += 1
            else:
                return "NONE"
        return "".join(moves)
'''],
("Grid dynamic programming: see [DP on grids](#/lesson/neet-dp/dp-grids).",
 "A greedy walk that steps into any free neighbour can wander into a dead end. First answer a simpler question for every cell, \"can the goal be reached from here?\", working backwards from the goal. With that table the walk never makes a wrong turn.",
 ["Define ok(r, c) = the goal is reachable from cell (r, c). What is ok for the goal itself? For a shelf?",
  "ok(r, c) depends only on the cell below and the cell to the right, so fill the table from the bottom-right corner.",
  "Then walk from the start: go down if ok(below) is true, otherwise go right."],
 "Plain recursion that tries down then right and backtracks: correct but exponential, about 2^(rows+cols) paths, because the same dead-end cells are explored again and again. Adding a set of failed cells (memoisation) fixes it.",
 "Fill `ok` bottom-up with one row and one column of padding (all False). If `ok[0][0]` is False return NONE. Otherwise build the string greedily.\n\nDry run example 1: ok is True along the middle column and the bottom-right, False at (1,0) and (1,2). From (0,0): below is a shelf → R; from (0,1): below is ok → D, D; then R. Result `RDDR`.",
 "Time O(rows × cols), space O(rows × cols).",
 "Greedy without the table (wrong solution) gets trapped in example 1's cousin where going down first leads to a dead end. Deep recursion on a 150 × 150 grid can exceed Python's recursion limit; the bottom-up table avoids recursion entirely.",
 "Count the routes instead ([Unique Paths II](#/problem/unique-paths-ii)) or allow four directions, which needs breadth-first search rather than DP.")),

P("fixed-point-index", "Fixed Point", "Easy", "Recursion & DP", "fixedPoint",
"""
An array `arr` holds **distinct integers in increasing order**. A *fixed point* is an index `i` with `arr[i] == i`.

Return the smallest fixed point, or `-1` if there is none. A linear scan is too slow to earn full marks: use the sorted order.

**Constraints:** `0 <= len(arr) <= 10^4` (think about `10^9`); values fit in 64 bits.

**Example 1:** `[-8, -3, 0, 3, 4, 9]` → `3`

**Example 2:** `[1, 2, 3]` → `-1`
""",
'''class Solution:
    def fixedPoint(self, arr: List[int]) -> int:
        lo, hi = 0, len(arr)
        while lo < hi:
            mid = (lo + hi) // 2
            if arr[mid] >= mid:
                hi = mid
            else:
                lo = mid + 1
        return lo if lo < len(arr) and arr[lo] == lo else -1
''',
[[[-8, -3, 0, 3, 4, 9]], [[1, 2, 3]], [[]], [[0]], [[5]], [[-1]], [[-1, 1]], [[0, 1, 2, 3]], [[-5, -4, -3, 3]], [[-2, 0, 2, 4, 6]],
 [list(range(-5000, 0)) + [5000] + list(range(5002, 9000))], [list(range(10, 9000))], [list(range(-9000, -10))],
 [[-3, -2, 2, 3, 4, 10]]],
['''class Solution:
    def fixedPoint(self, arr):
        lo, hi = 0, len(arr) - 1
        while lo <= hi:
            mid = (lo + hi) // 2
            if arr[mid] == mid:
                return mid
            if arr[mid] > mid:
                hi = mid - 1
            else:
                lo = mid + 1
        return -1
'''],
("Binary search and its invariants: see [Binary search done right](#/lesson/neet-window-stack/binary-search-right).",
 "Because the integers are distinct and increasing, each step to the right raises the value by at least 1, the same amount the index rises. So the difference `arr[i] − i` never decreases. You are searching a sorted sequence of differences for the first 0.",
 ["If `arr[mid] < mid`, could a fixed point be on the left? Each step left lowers the value by at least 1 and the index by exactly 1.",
  "So the predicate `arr[i] >= i` is False, …, False, True, …, True. Binary search for the first True.",
  "Check at the end that the position found really satisfies `arr[i] == i`."],
 "Scan every index: O(n). Acceptable only as the starting point.",
 "Search the half-open range `[lo, hi)` for the first index with `arr[i] >= i`.\n\nDry run `[-8,-3,0,3,4,9]`: lo 0, hi 6, mid 3: 3 ≥ 3 → hi 3. mid 1: −3 < 1 → lo 2. mid 2: 0 < 2 → lo 3. Stop: arr[3] = 3 → answer 3 (index 4 is also a fixed point but is not the smallest).",
 "Time O(log n), space O(1).",
 "Returning the first match found by a classic binary search gives *a* fixed point, not the smallest (the wrong solution returns 4 on the first example). The argument needs distinct values: with duplicates, `arr[i] − i` can go down and both halves may need searching.",
 "Solve the version with duplicates by recursing into both sides but skipping ahead: on the left, search only up to `min(mid − 1, arr[mid])`.")),

P("tower-moves", "Tower Transfer", "Medium", "Recursion & DP", "towerMoves",
"""
Three pegs are numbered `0`, `1`, `2`. Peg 0 holds `n` discs of different sizes, largest at the bottom. Move the whole pile to peg 2 following the usual rules: move one disc at a time, only the top disc of a peg, and never place a disc on a smaller one.

Return the shortest sequence of moves as a list of pairs `[from_peg, to_peg]`.

**Constraints:** `0 <= n <= 12`.

**Example 1:** `n = 1` → `[[0, 2]]`

**Example 2:** `n = 2` → `[[0, 1], [0, 2], [1, 2]]`
""",
'''class Solution:
    def towerMoves(self, n: int) -> List[List[int]]:
        moves = []

        def shift(count, src, dst, spare):
            if count == 0:
                return
            shift(count - 1, src, spare, dst)
            moves.append([src, dst])
            shift(count - 1, spare, dst, src)
        shift(n, 0, 2, 1)
        return moves
''',
[[1], [2], [0], [3], [4], [5], [6], [7], [8], [10], [11], [12]],
['''class Solution:
    def towerMoves(self, n):
        moves = []

        def shift(count, src, dst, spare):
            if count == 0:
                return
            shift(count - 1, src, dst, spare)
            moves.append([src, dst])
            shift(count - 1, spare, dst, src)
        shift(n, 0, 2, 1)
        return moves
''', '''class Solution:
    def towerMoves(self, n):
        return [[0, 2]] * n
'''],
("Recursion and trusting the recursive call: see [Designing recursive algorithms](#/lesson/dsa-foundations/recursion-design).",
 "The largest disc can only move when all the others sit together on the spare peg. So: move the n−1 smaller discs out of the way (a smaller copy of the same problem), move the big disc, move the n−1 discs on top of it (the same problem again).",
 ["Solve n = 1 and n = 2 by hand.",
  "For n = 3, what must the pegs look like at the moment the largest disc moves?",
  "shift(count, src, dst, spare) = shift(count−1, src, spare, dst); record [src, dst]; shift(count−1, spare, dst, src)."],
 "Breadth-first search over all 3ⁿ arrangements of discs finds the shortest sequence without insight: about half a million states for n = 12, workable but far more code.",
 "The helper appends moves to a shared list. The base case `count == 0` does nothing.\n\nDry run n = 2: shift(1, 0, 1, 2) → [0,1]; then [0,2]; shift(1, 1, 2, 0) → [1,2].",
 "Exactly 2ⁿ − 1 moves, so time and output size O(2ⁿ); recursion depth n.",
 "Swapping `dst` and `spare` in the first recursive call. Forgetting that the roles of the pegs change at each level.",
 "Prove that 2ⁿ − 1 is optimal (the recurrence T(n) = 2T(n−1) + 1). Write an iterative version using three explicit stacks, and validate a sequence of moves supplied by someone else.")),

P("letter-orders", "Distinct Letter Orders", "Medium", "Recursion & DP", "distinctOrders",
"""
Given a string of lower-case letters that **may contain repeated letters**, return every distinct string that can be formed by re-ordering all of its letters, in alphabetical order.

**Constraints:** `0 <= len(s) <= 8`.

**Example 1:** `"aab"` → `["aab", "aba", "baa"]`

**Example 2:** `"zz"` → `["zz"]`
""",
'''class Solution:
    def distinctOrders(self, s: str) -> List[str]:
        counts = collections.Counter(s)
        letters = sorted(counts)
        out, current = [], []

        def build():
            if len(current) == len(s):
                out.append("".join(current))
                return
            for ch in letters:
                if counts[ch]:
                    counts[ch] -= 1
                    current.append(ch)
                    build()
                    current.pop()
                    counts[ch] += 1
        build()
        return out
''',
[["aab"], ["zz"], [""], ["a"], ["ba"], ["abc"], ["aabb"], ["cba"], ["aaaaaaaa"], ["aaaabbbb"], ["abcdefg"], ["gfedcba"],
 ["aabbccd"], ["mississi"]],
['''class Solution:
    def distinctOrders(self, s):
        return sorted("".join(p) for p in itertools.permutations(s))
''', '''class Solution:
    def distinctOrders(self, s):
        return sorted(set(s[i:] + s[:i] for i in range(len(s)))) if s else [""]
'''],
("Backtracking: choose, explore, undo. See [The backtracking template](#/lesson/neet-heap-graphs/backtracking-template).",
 "Duplicates appear when two *equal* letters swap roles. Avoid that at the source: at each position choose a **letter value** (not a letter position), and a value may be chosen only while copies of it remain. Each distinct string is then built exactly once.",
 ["With all-different letters there are n! orders. Why does `aab` have only 3 and not 6?",
  "Count how many of each letter you have.",
  "At every position loop over the distinct letters in alphabetical order; use one copy, recurse, give it back."],
 "Generate all n! permutations and remove duplicates with a set. For `aaaaaaaa` that builds 40,320 strings to keep one.",
 "Counter of letters; `build()` appends the finished string when the length is reached; otherwise tries each available letter.\n\nDry run `aab` (a:2, b:1): a → a → b gives `aab`; a → b → a gives `aba`; b → a → a gives `baa`. Alphabetical order comes for free because the letters are tried in sorted order.",
 "Time O(n × number of results); the number of results is n! / (c₁! c₂! …). Space O(n) besides the output.",
 "Returning duplicates from a plain permutation generator. Forgetting to restore the count after the recursive call. The empty string has exactly one ordering: `[\"\"]`.",
 "Return only the count (a multinomial coefficient), or the k-th ordering without generating the others. Compare [Permutations II](#/problem/permutations-ii).")),

P("crate-tower", "Tallest Crate Tower", "Hard", "Recursion & DP", "tallestTower",
"""
A warehouse has crates given as `[width, depth, height]`. Crates cannot be rotated. Crate A may be placed directly on crate B only if A is **strictly smaller than B in all three measurements**.

Return the greatest total height of a tower that can be built from some of the crates (each crate used at most once). An empty warehouse gives 0.

**Constraints:** `0 <= number of crates <= 600`; measurements in `[1, 10^6]`.

**Example:** `[[4,4,3],[2,2,1],[3,5,2],[5,5,5]]` → `9` (bottom to top: `[5,5,5]`, `[4,4,3]`, `[2,2,1]`)
""",
'''class Solution:
    def tallestTower(self, crates: List[List[int]]) -> int:
        crates = sorted(crates, reverse=True)
        best = [0] * len(crates)
        for i, (w, d, h) in enumerate(crates):
            top = 0
            for j in range(i):
                bw, bd, bh = crates[j]
                if bw > w and bd > d and bh > h and best[j] > top:
                    top = best[j]
            best[i] = top + h
        return max(best, default=0)
''',
[[[[4, 4, 3], [2, 2, 1], [3, 5, 2], [5, 5, 5]]], [[]], [[[1, 1, 1]]], [[[2, 2, 2], [2, 2, 2]]], [[[3, 3, 3], [2, 2, 3]]],
 [[[5, 1, 9], [4, 2, 8], [3, 3, 7]]], [[[1, 1, 1], [2, 2, 2], [3, 3, 3], [4, 4, 4]]], [[[4, 4, 1], [3, 3, 100], [2, 2, 2]]],
 [[[10, 10, 10], [9, 9, 1], [8, 8, 8], [9, 9, 9]]], [[[i, i, 1] for i in range(1, 601)]],
 [[[R.randint(1, 60), R.randint(1, 60), R.randint(1, 60)] for _ in range(600)]],
 [[[R.randint(1, 10 ** 6), R.randint(1, 10 ** 6), R.randint(1, 10 ** 6)] for _ in range(500)]],
 [[[5, 5, 2], [4, 6, 9], [3, 3, 1]]]],
['''class Solution:
    def tallestTower(self, crates):
        crates = sorted(crates, reverse=True)
        total, last = 0, None
        for w, d, h in crates:
            if last is None or (w < last[0] and d < last[1] and h < last[2]):
                total += h
                last = (w, d, h)
        return total
''', '''class Solution:
    def tallestTower(self, crates):
        crates = sorted(crates, reverse=True)
        best = [0] * len(crates)
        for i, (w, d, h) in enumerate(crates):
            top = 0
            for j in range(i):
                bw, bd, bh = crates[j]
                if bw >= w and bd >= d and bh >= h:
                    top = max(top, best[j])
            best[i] = top + h
        return max(best, default=0)
'''],
("Longest increasing subsequence as a DP over \"the best chain ending here\": see [LIS](#/lesson/neet-dp/dp-lis).",
 "Sort the crates by width, largest first. Then any legal tower read from bottom to top is a subsequence of the sorted list, so the question becomes a longest-chain problem: best[i] = height of the tallest tower whose top crate is crate i.",
 ["A greedy choice (always put the largest remaining crate that fits) can block a much taller crate later.",
  "After sorting by one dimension, which crates could possibly lie beneath crate i?",
  "best[i] = h_i + max(best[j]) over earlier crates j that are strictly larger in all three measurements."],
 "Try every subset or every ordering: 2ⁿ or n! possibilities. Recursion \"tallest tower with this crate at the bottom\" is fine once memoised, and is the same DP.",
 "Sort descending. For each i scan all j < i, keep the best compatible `best[j]`, add own height. Answer: max of `best`.\n\nDry run example: sorted `[5,5,5], [4,4,3], [3,5,2], [2,2,1]`. best = 5; 5+3 = 8; `[3,5,2]` fits only on `[5,5,5]`? depth 5 is not < 5 → no → 2; `[2,2,1]` on `[4,4,3]` → 9. Answer 9.",
 "Time O(n²) after an O(n log n) sort, space O(n).",
 "Allowing equal measurements (`>=`) stacks identical crates on each other. Greedy by sorted order fails on the eighth test, where skipping a short wide crate lets a 100-tall crate in.",
 "Allow rotations (each crate becomes up to six oriented crates). The two-dimensional cousin with an O(n log n) solution is [Russian Doll Envelopes](#/problem/russian-doll-envelopes).")),

P("bool-expr-ways", "Ways to Bracket a Boolean Expression", "Hard", "Recursion & DP", "countWays",
"""
An expression consists of the digits `0` (false) and `1` (true) separated by the operators `&` (AND), `|` (OR) and `^` (XOR), for example `0|1^1&1`. It has no brackets, so its value depends on the order in which the operators are applied.

Count the number of ways to **fully bracket** the expression so that it evaluates to `want` (a boolean). Return the exact count as an integer.

**Constraints:** the expression has between 1 and 31 digits (length up to 61) and is well formed.

**Example 1:** `expr = "1|0&1", want = True` → `2` (both `(1|0)&1` and `1|(0&1)` are true)

**Example 2:** `expr = "1^1&0", want = False` → `1` (only `(1^1)&0` is false)
""",
'''class Solution:
    def countWays(self, expr: str, want: bool) -> int:
        vals = [int(ch) for ch in expr[0::2]]
        ops = expr[1::2]
        n = len(vals)
        true = [[0] * n for _ in range(n)]
        false = [[0] * n for _ in range(n)]
        for i in range(n):
            true[i][i] = vals[i]
            false[i][i] = 1 - vals[i]
        for size in range(2, n + 1):
            for i in range(n - size + 1):
                j = i + size - 1
                t = f = 0
                for k in range(i, j):
                    lt, lf, rt, rf = true[i][k], false[i][k], true[k + 1][j], false[k + 1][j]
                    if ops[k] == "&":
                        t += lt * rt
                        f += lt * rf + lf * rt + lf * rf
                    elif ops[k] == "|":
                        t += lt * rt + lt * rf + lf * rt
                        f += lf * rf
                    else:
                        t += lt * rf + lf * rt
                        f += lt * rt + lf * rf
                true[i][j], false[i][j] = t, f
        return true[0][n - 1] if want else false[0][n - 1]
''',
[["1|0&1", True], ["1^1&0", False], ["0|1^1&1", False], ["0|1^1&1", True], ["0&0&0&1^1|0", True], ["1", True], ["1", False], ["0", False], ["1&1", True], ["1&0", True], ["1|0", True],
 ["1^1", True], ["1^1^1", True], ["1|1|1|1", True], ["0|0|0|0", True], ["^".join("10" * 15 + "1"), True],
 ["&".join("1" * 31), True], ["|".join("01" * 15), False], ["1^0&1|0^1&1|0", False]],
['''class Solution:
    def countWays(self, expr, want):
        vals = [int(ch) for ch in expr[0::2]]
        ops = expr[1::2]

        @functools.lru_cache(None)
        def go(i, j):
            if i == j:
                return frozenset([vals[i]])
            out = set()
            for k in range(i, j):
                for a in go(i, k):
                    for b in go(k + 1, j):
                        out.add(a & b if ops[k] == "&" else a | b if ops[k] == "|" else a ^ b)
            return frozenset(out)
        return 1 if int(want) in go(0, len(vals) - 1) else 0
''', '''class Solution:
    def countWays(self, expr, want):
        return 1 if bool(eval(expr)) == want else 0
'''],
("Interval dynamic programming, where a range is split at every possible point: see [Interval DP](#/lesson/neet-dp/dp-intervals).",
 "Whatever the bracketing, exactly one operator is applied **last**. It splits the expression into a left part and a right part that are bracketed independently. If you know, for each part, how many bracketings give true and how many give false, the truth table of the operator tells you how to combine the four numbers.",
 ["Pick the operator evaluated last. What smaller problems remain?",
  "For each sub-range keep two counts: ways to make it true and ways to make it false.",
  "For AND: true = lt·rt. For OR: false = lf·rf. For XOR: true = lt·rf + lf·rt. The other count is everything else."],
 "Plain recursion over the last operator without a table recomputes each sub-range many times; the number of bracketings is a Catalan number (about 3.8 × 10¹⁵ for 31 digits), so enumeration is out of the question.",
 "Tables `true[i][j]`, `false[i][j]` over digit positions. Fill by increasing range size; for each split point k use operator `ops[k]`.\n\nDry run `1|0&1`, want True: single digits first. Split at `|`: left `1` is true (1 way), right `0&1` is false (1 way) → OR true: 1 way. Split at `&`: left `1|0` true (1 way), right `1` true → AND true: 1 way. Total 2.",
 "Time O(n³) for n digits (about 30,000 inner steps at the limit), space O(n²).",
 "Counting only whether a value is *possible* rather than how many ways. Evaluating with normal precedence gives one bracketing, not all. The counts exceed 64 bits for long inputs: fine in Python, an overflow in Java or C++.",
 "The same \"last operation\" split solves LeetCode's *Different Ways to Add Parentheses* and [Burst Balloons](#/problem/burst-balloons).")),

P("friend-hops", "Friend Hops", "Medium", "System Design & Scalability", "hops",
"""
A social network has `n` members numbered `0 … n-1`. Each entry `[u, v]` of `friendships` says that `u` and `v` are friends (friendship is mutual).

Return the smallest number of friendship links on a chain connecting member `a` to member `b`, or `-1` if they are not connected at all. A member is 0 hops from themselves.

At real scale the network is far too large to explore outward from one side only, so practise searching **from both ends at once**.

**Constraints:** `1 <= n <= 2·10^4`; up to `3·10^4` friendships.

**Example 1:** `n = 5, friendships = [[0,1],[1,2],[2,3]], a = 0, b = 3` → `3`

**Example 2:** same network, `a = 0, b = 4` → `-1`
""",
'''class Solution:
    def hops(self, n: int, friendships: List[List[int]], a: int, b: int) -> int:
        if a == b:
            return 0
        adj = [[] for _ in range(n)]
        for u, v in friendships:
            adj[u].append(v)
            adj[v].append(u)
        dist_a, dist_b = {a: 0}, {b: 0}
        front_a, front_b = [a], [b]
        while front_a and front_b:
            if len(front_a) > len(front_b):
                front_a, front_b, dist_a, dist_b = front_b, front_a, dist_b, dist_a
            best = None
            nxt = []
            for u in front_a:
                for v in adj[u]:
                    if v in dist_b:
                        cand = dist_a[u] + 1 + dist_b[v]
                        if best is None or cand < best:
                            best = cand
                    if v not in dist_a:
                        dist_a[v] = dist_a[u] + 1
                        nxt.append(v)
            if best is not None:
                return best
            front_a = nxt
        return -1
''',
[[5, [[0, 1], [1, 2], [2, 3]], 0, 3], [5, [[0, 1], [1, 2], [2, 3]], 0, 4], [1, [], 0, 0], [2, [[0, 1]], 0, 1], [2, [], 0, 1],
 [4, [[0, 1], [1, 2], [2, 3], [0, 3]], 0, 2], [6, [[0, 1], [0, 2], [1, 3], [2, 3], [3, 4], [4, 5]], 0, 5],
 [7, [[0, 1], [1, 2], [2, 6], [0, 3], [3, 4], [4, 5], [5, 6]], 0, 6], [3, [[0, 1], [0, 1], [1, 2]], 2, 0], [4, [[0, 0], [0, 1]], 1, 0],
 [_people, _links, 3, 4000], [_people, _links, 17, 18], [3000, [[i, i + 1] for i in range(2999)], 0, 2999],
 [3000, [[i, i + 1] for i in range(2999)] + [[0, 2990]], 10, 2995], [3000, [[0, i] for i in range(1, 3000)], 77, 2000]],
['''class Solution:
    def hops(self, n, friendships, a, b):
        adj = [[] for _ in range(n)]
        for u, v in friendships:
            adj[u].append(v)
        dist = {a: 0}
        queue = collections.deque([a])
        while queue:
            u = queue.popleft()
            for v in adj[u]:
                if v not in dist:
                    dist[v] = dist[u] + 1
                    queue.append(v)
        return dist.get(b, -1)
''', '''class Solution:
    def hops(self, n, friendships, a, b):
        adj = [[] for _ in range(n)]
        for u, v in friendships:
            adj[u].append(v)
            adj[v].append(u)
        seen, stack = {a: 0}, [a]
        while stack:
            u = stack.pop()
            for v in adj[u]:
                if v not in seen:
                    seen[v] = seen[u] + 1
                    stack.append(v)
        return seen.get(b, -1)
'''],
("Breadth-first search for shortest paths in unweighted graphs: see [DFS and BFS](#/lesson/neet-heap-graphs/dfs-bfs).",
 "If everyone has about k friends, a search of depth d from one side touches about k^d people. Two searches of depth d/2, one from each person, touch only about 2·k^(d/2): the square root. They are finished when the two explored regions touch.",
 ["Ordinary BFS from `a` is correct; get that working first.",
  "Now keep two distance maps and two frontiers. Always expand the smaller frontier by one whole level.",
  "When an expanded member's neighbour is already in the other map, a chain is found; finish the level and return the smallest total seen."],
 "Depth-first search finds *a* chain but not the shortest one. One-sided BFS is correct with time O(n + m), and is the fallback answer.",
 "Expand level by level. For each `u` in the smaller frontier and each friend `v`: if `v` is known to the other side, candidate = dist(u) + 1 + other(v). New members get a distance and join the next frontier. Return the best candidate at the end of the level.\n\nDry run example 1: frontiers {0} and {3}. Expand 0 → {1}. Expand 3 → {2}. Expand 1: friend 2 is known to the other side with distance 1 → 1 + 1 + 1 = 3.",
 "Worst case O(n + m) like plain BFS, but in a network with branching factor k and distance d it explores about k^(d/2) instead of k^d nodes.",
 "Returning the first meeting found in the middle of a level can be one too long: finish the level and take the minimum. Storing the friendship in one direction only. Using DFS distances.",
 "At real scale the members live on many machines: discuss how to find which machine holds a person, how to batch the lookups for a frontier, and caching. See [Scaling from one server to many](#/lesson/system-design/scale-stateless-to-sharded).")),

P("ring-router", "Ring Router", "Medium", "System Design & Scalability", "RingRouter",
"""
A cache cluster places its servers on a **ring** of positions `0 … size-1`. A key with hash position `k` is stored on the first server found when walking clockwise (increasing positions) from `k`, wrapping from `size-1` back to `0`; a server sitting exactly at `k` takes the key.

Implement class `RingRouter(size)`:

- `addServer(pos)`: place a server at `pos`. Returns `False` if one is already there.
- `removeServer(pos)`: returns `True` if a server was removed.
- `route(k)`: returns the position of the server responsible for `k`, or `-1` if the ring has no servers.

**Constraints:** `1 <= size <= 10^9`; up to `2·10^4` calls; `route` should not scan all servers.

**Example (size 100):** `addServer(20), addServer(70), route(10) → 20, route(20) → 20, route(21) → 70, route(90) → 20, removeServer(20) → True, route(90) → 70`
""",
'''class RingRouter:
    def __init__(self, size: int):
        self.size = size
        self.servers = []

    def addServer(self, pos: int) -> bool:
        i = bisect.bisect_left(self.servers, pos)
        if i < len(self.servers) and self.servers[i] == pos:
            return False
        self.servers.insert(i, pos)
        return True

    def removeServer(self, pos: int) -> bool:
        i = bisect.bisect_left(self.servers, pos)
        if i < len(self.servers) and self.servers[i] == pos:
            self.servers.pop(i)
            return True
        return False

    def route(self, k: int) -> int:
        if not self.servers:
            return -1
        i = bisect.bisect_left(self.servers, k)
        return self.servers[i] if i < len(self.servers) else self.servers[0]
''',
[[["RingRouter", "addServer", "addServer", "route", "route", "route", "route", "removeServer", "route"],
  [[100], [20], [70], [10], [20], [21], [90], [20], [90]]],
 [["RingRouter", "route", "removeServer"], [[10], [3], [3]]],
 [["RingRouter", "addServer", "addServer", "route", "route"], [[10], [5], [5], [5], [6]]],
 [["RingRouter", "addServer", "route", "route", "route"], [[10], [0], [0], [9], [1]]],
 [["RingRouter", "addServer", "addServer", "addServer", "route", "removeServer", "route", "removeServer", "route"],
  [[1000], [999], [0], [500], [501], [999], [501], [0], [501]]],
 [["RingRouter", "addServer", "removeServer", "removeServer", "route"], [[5], [2], [2], [2], [2]]],
 _ops(("RingRouter", [1000]), 4000, [("addServer", lambda: [R.randrange(1000)]), ("removeServer", lambda: [R.randrange(1000)]),
                                     ("route", lambda: [R.randrange(1000)]), ("route", lambda: [R.randrange(1000)])]),
 _ops(("RingRouter", [10 ** 9]), 4000, [("addServer", lambda: [R.randrange(10 ** 9)]), ("route", lambda: [R.randrange(10 ** 9)])]),
 _ops(("RingRouter", [50]), 3000, [("addServer", lambda: [R.randrange(50)]), ("removeServer", lambda: [R.randrange(50)]),
                                   ("route", lambda: [R.randrange(50)])]),
 _ops(("RingRouter", [8]), 2000, [("addServer", lambda: [R.randrange(8)]), ("removeServer", lambda: [R.randrange(8)]),
                                  ("route", lambda: [R.randrange(8)])])],
['''class RingRouter:
    def __init__(self, size):
        self.size = size
        self.servers = []

    def addServer(self, pos):
        if pos in self.servers:
            return False
        self.servers.append(pos)
        self.servers.sort()
        return True

    def removeServer(self, pos):
        if pos in self.servers:
            self.servers.remove(pos)
            return True
        return False

    def route(self, k):
        if not self.servers:
            return -1
        i = bisect.bisect_right(self.servers, k)
        return self.servers[i] if i < len(self.servers) else self.servers[0]
''', '''class RingRouter:
    def __init__(self, size):
        self.size = size
        self.servers = []

    def addServer(self, pos):
        if pos in self.servers:
            return False
        self.servers.append(pos)
        self.servers.sort()
        return True

    def removeServer(self, pos):
        if pos in self.servers:
            self.servers.remove(pos)
            return True
        return False

    def route(self, k):
        if not self.servers:
            return -1
        return self.servers[k % len(self.servers)]
'''],
("Binary search with `bisect`, and the idea of consistent hashing: see [The hash ring](#/lesson/system-design/consistent-hashing-ring).",
 "Keep the server positions sorted. \"First server clockwise from k\" is the first position ≥ k, which binary search finds; if there is none, wrap to the smallest position.",
 ["Why not `server = hash(key) % number_of_servers`? Think about what happens to every key when one server is added.",
  "A sorted list of positions turns the clockwise walk into a lower-bound search.",
  "Handle the wrap-around: if the search runs off the end, the answer is `servers[0]`."],
 "Scan all servers and compute the clockwise distance to each: O(servers) per lookup.",
 "`route(k)`: `i = bisect_left(servers, k)`; return `servers[i]`, or `servers[0]` when `i == len(servers)`.\n\nDry run with servers [20, 70]: route(10) → index 0 → 20. route(21) → index 1 → 70. route(90) → index 2 = len → wrap → 20. After removing 20, route(90) wraps to 70: only the keys that lived on the removed server moved.",
 "`route` O(log s). `addServer`/`removeServer` O(s) because a Python list shifts elements; a balanced tree makes them O(log s).",
 "`bisect_right` skips a server sitting exactly on the key's position. Modulo routing (second wrong solution) reshuffles nearly every key when the cluster changes size.",
 "Add virtual nodes: each physical server appears at many positions to even out the load. See [Virtual nodes](#/lesson/system-design/consistent-hashing-virtual-nodes).")),

P("rate-gate", "Sliding-Window Rate Gate", "Medium", "System Design & Scalability", "RateGate",
"""
An API allows each client at most `limit` requests in any window of `window` seconds. Build the gate for one client.

Implement class `RateGate(limit, window)`:

- `allow(t)`: a request arrives at integer time `t` (seconds). It is **accepted** if fewer than `limit` requests were accepted at times in the interval `(t - window, t]`; then it is recorded and the method returns `True`. Otherwise return `False`, and the rejected request is **not** recorded.
- `load(t)`: returns how many accepted requests lie in `(t - window, t]`.

Times never decrease from one call to the next.

**Constraints:** `1 <= limit <= 10^4`; `1 <= window <= 10^6`; up to `2·10^4` calls.

**Example (limit 2, window 10):** `allow(1) → True, allow(2) → True, allow(3) → False, allow(11) → True` (the request at time 1 has left the window), `allow(11) → False, load(12) → 1`
""",
'''class RateGate:
    def __init__(self, limit: int, window: int):
        self.limit = limit
        self.window = window
        self.times = collections.deque()

    def _expire(self, t):
        while self.times and self.times[0] <= t - self.window:
            self.times.popleft()

    def allow(self, t: int) -> bool:
        self._expire(t)
        if len(self.times) >= self.limit:
            return False
        self.times.append(t)
        return True

    def load(self, t: int) -> int:
        self._expire(t)
        return len(self.times)
''',
[[["RateGate", "allow", "allow", "allow", "allow", "allow", "load"], [[2, 10], [1], [2], [3], [11], [11], [12]]],
 [["RateGate", "load", "allow", "load"], [[1, 1], [0], [0], [0]]],
 [["RateGate", "allow", "allow", "allow", "allow"], [[1, 5], [0], [4], [5], [9]]],
 [["RateGate", "allow", "allow", "allow", "load", "allow"], [[3, 1], [7], [7], [7], [7], [8]]],
 [["RateGate", "allow", "allow", "allow", "allow", "allow"], [[2, 3], [0], [1], [2], [3], [4]]],
 [["RateGate", "allow", "load", "load", "load"], [[5, 10], [100], [109], [110], [111]]],
 (lambda ts: [["RateGate"] + ["allow"] * len(ts), [[5, 20]] + [[t] for t in ts]])(_times),
 (lambda ts: [["RateGate"] + [R.choice(["allow", "allow", "load"]) for _ in ts], [[50, 100]] + [[t] for t in ts]])(_times),
 (lambda ts: [["RateGate"] + ["allow"] * len(ts), [[1, 2]] + [[t] for t in ts]])(_times[:2000]),
 [["RateGate"] + ["allow"] * 3000, [[1000, 10 ** 6]] + [[i] for i in range(3000)]]],
['''class RateGate:
    def __init__(self, limit, window):
        self.limit = limit
        self.window = window
        self.times = collections.deque()

    def allow(self, t):
        while self.times and self.times[0] <= t - self.window:
            self.times.popleft()
        self.times.append(t)
        return len(self.times) <= self.limit

    def load(self, t):
        while self.times and self.times[0] <= t - self.window:
            self.times.popleft()
        return len(self.times)
''', '''class RateGate:
    def __init__(self, limit, window):
        self.limit = limit
        self.window = window
        self.start = None
        self.count = 0

    def allow(self, t):
        if self.start is None or t - self.start >= self.window:
            self.start, self.count = t, 0
        if self.count >= self.limit:
            return False
        self.count += 1
        return True

    def load(self, t):
        if self.start is None or t - self.start >= self.window:
            return 0
        return self.count
'''],
("Queues and sliding windows: see [Rate-limiter algorithms](#/lesson/system-design/rate-limiter-algorithms).",
 "Only accepted requests from the last `window` seconds matter. Because time moves forward, the old ones are always at the front of a queue: drop them, then compare the queue's length with the limit.",
 ["What exactly do you need to remember about the past?",
  "Store the timestamps of accepted requests in a deque, oldest first.",
  "Before every decision remove timestamps `<= t - window`. Record a request only if it is accepted."],
 "Keep every timestamp forever and count those inside the window on each call: O(total requests) per call and unbounded memory.",
 "`_expire(t)` pops from the left while the oldest time is outside `(t − window, t]`. `allow` then checks the size.\n\nDry run (limit 2, window 10): 1, 2 accepted → deque [1,2]. t=3: full → False. t=11: 1 ≤ 11−10 is expired → [2] → accept → [2,11]. t=11 again: full → False. load(12): 2 ≤ 2 expires → 1.",
 "Amortised O(1) per call (each timestamp is added and removed once); memory O(limit).",
 "Recording rejected requests lets a client that keeps hammering lock itself out forever (first wrong solution). A fixed window that resets (second wrong solution) allows twice the limit across a boundary. Off-by-one on the window edge: time `t − window` is outside.",
 "For millions of clients, exact timestamps are too much memory: discuss the sliding-window counter and token bucket, and where the counters live in a distributed setup. See [Distributed rate limiting](#/lesson/system-design/rate-limiter-distributed).")),

P("shard-top-terms", "Top Terms Across Shards", "Medium", "System Design & Scalability", "topTerms",
"""
A search engine keeps its query log on several machines (*shards*). Each shard reports a list of `[term, count]` pairs: how often it saw each term. The same term can appear on several shards, and even more than once in one shard's report.

Return the `k` terms with the highest **total** count across all shards, as `[term, total]` pairs ordered by total descending, breaking ties by term in alphabetical order. If there are fewer than `k` distinct terms, return them all.

**Constraints:** up to `2·10^4` pairs in total; `0 <= k <= 10^4`; counts in `[1, 10^6]`.

**Example:** `shards = [[["cat", 3], ["dog", 2]], [["dog", 2], ["eel", 4]]], k = 2` → `[["dog", 4], ["eel", 4]]`
""",
'''class Solution:
    def topTerms(self, shards: List[List[List]], k: int) -> List[List]:
        totals = collections.defaultdict(int)
        for shard in shards:
            for term, count in shard:
                totals[term] += count
        best = heapq.nsmallest(k, totals.items(), key=lambda item: (-item[1], item[0]))
        return [[term, total] for term, total in best]
''',
[[[[["cat", 3], ["dog", 2]], [["dog", 2], ["eel", 4]]], 2], [[], 3], [[[]], 1], [[[["a", 1]]], 0], [[[["a", 1]]], 5],
 [[[["b", 2], ["a", 2], ["c", 2]]], 2], [[[["x", 1], ["x", 1], ["y", 2]]], 1], [[[["x", 5]], [["y", 5]], [["x", 1]]], 2],
 [[[["m", 1]], [["m", 1]], [["m", 1]], [["n", 2]]], 2],
 [[[[w, R.randint(1, 50)] for w in _words[:500]], [[w, R.randint(1, 50)] for w in _words[500:1000]], [[w, R.randint(1, 50)] for w in _words[1000:]]], 10],
 [[[[w, 1] for w in _words]], 200], [[[["t%d" % i, i % 7 + 1] for i in range(3000)]], 3000],
 [[[["t%d" % i, 10 ** 6] for i in range(2000)], [["t%d" % i, 10 ** 6] for i in range(1000, 3000)]], 1500]],
['''class Solution:
    def topTerms(self, shards, k):
        best = []
        for shard in shards:
            best.extend(sorted(shard, key=lambda p: (-p[1], p[0]))[:k])
        totals = collections.defaultdict(int)
        for term, count in best:
            totals[term] += count
        return [[t, c] for t, c in sorted(totals.items(), key=lambda item: (-item[1], item[0]))[:k]]
''', '''class Solution:
    def topTerms(self, shards, k):
        totals = collections.defaultdict(int)
        for shard in shards:
            for term, count in shard:
                totals[term] += count
        return [[t, c] for t, c in sorted(totals.items(), key=lambda item: -item[1])[:k]]
'''],
("Hash maps for counting and heaps for top-k: see [Heap patterns](#/lesson/neet-heap-graphs/heap-patterns).",
 "A term that is only moderately popular on every shard can be the overall winner, so the per-shard top lists are not enough: you must add up the counts of *all* terms first, then select the top k.",
 ["Why is \"take each shard's top k and merge them\" wrong? Construct a three-shard example.",
  "Sum counts per term in one dictionary.",
  "Select the k best with a heap (or sort) using the key `(-total, term)`."],
 "Sort the full dictionary of totals: O(d log d) for d distinct terms. Perfectly fine here; the heap matters when d is huge and k is small.",
 "Aggregate, then `heapq.nsmallest(k, items, key=(-total, term))`.\n\nDry run example: totals cat 3, dog 4, eel 4. Keys: (−4, dog), (−4, eel), (−3, cat). Top two: dog, eel.",
 "Time O(p + d log k) for p pairs and d distinct terms; space O(d).",
 "Merging local top-k lists (first wrong solution) drops terms that are spread evenly. Forgetting the alphabetical tie-break gives an order that depends on dictionary insertion order.",
 "In the real system the totals do not fit on one machine: partition the terms by hash so that each term is summed on exactly one machine, take a local top k there, and merge those. This is a MapReduce job: see [Hashing, trees and MapReduce](#/lesson/interview-prep/review-hashing-trees-mapreduce).")),

P("merge-into-buffer", "Merge Into the Spare Room", "Easy", "Sorting & Searching", "mergeIn",
"""
Array `a` has room for `m + len(b)` numbers. Its first `m` entries are sorted in non-decreasing order; the remaining entries are placeholders (zeros) to be overwritten. Array `b` is sorted too.

Merge `b` into `a` **in place** so that `a` becomes one sorted array. Return nothing and do not allocate another array.

**Constraints:** `0 <= m, len(b) <= 10^4`.

**Example:** `a = [2, 5, 9, 0, 0], m = 3, b = [1, 6]` → `a = [1, 2, 5, 6, 9]`
""",
'''class Solution:
    def mergeIn(self, a: List[int], m: int, b: List[int]) -> None:
        i, j, k = m - 1, len(b) - 1, m + len(b) - 1
        while j >= 0:
            if i >= 0 and a[i] > b[j]:
                a[k] = a[i]
                i -= 1
            else:
                a[k] = b[j]
                j -= 1
            k -= 1
''',
[[[2, 5, 9, 0, 0], 3, [1, 6]], [[], 0, []], [[1], 1, []], [[0], 0, [1]], [[4, 5, 6, 0, 0, 0], 3, [1, 2, 3]], [[1, 2, 3, 0, 0, 0], 3, [4, 5, 6]],
 [[1, 1, 0, 0], 2, [1, 1]], [[-5, 0, 0], 1, [-7, -6]], [[2, 0], 1, [1]], [[1, 3, 5, 7, 0, 0, 0], 4, [2, 4, 6]],
 [sorted(R.randint(0, 999) for _ in range(6000)) + [0] * 5000, 6000, sorted(R.randint(0, 999) for _ in range(5000))],
 [list(range(0, 8000, 2)) + [0] * 4000, 4000, list(range(1, 8000, 2))], [[0, 0, 0, 0, 0], 2, [0, 0, 1]]],
['''class Solution:
    def mergeIn(self, a, m, b):
        i = j = k = 0
        while i < m and j < len(b):
            if a[i] <= b[j]:
                a[k] = a[i]
                i += 1
            else:
                a[k] = b[j]
                j += 1
            k += 1
        while j < len(b):
            a[k] = b[j]
            j += 1
            k += 1
''', '''class Solution:
    def mergeIn(self, a, m, b):
        i, j, k = m - 1, len(b) - 1, m + len(b) - 1
        while i >= 0 and j >= 0:
            if a[i] > b[j]:
                a[k] = a[i]
                i -= 1
            else:
                a[k] = b[j]
                j -= 1
            k -= 1
'''],
("The merge step of merge sort: see [Merge sort](#/lesson/dsa-foundations/merge-sort).",
 "Merging from the front would overwrite numbers of `a` that have not been read yet. The free space is at the *back*, so fill from the back: the largest remaining number goes into the last free slot.",
 ["Where is the empty space? Which end of the result can you write without destroying data?",
  "Use three indexes: last real element of `a`, last element of `b`, last slot.",
  "When `b` is used up, the rest of `a` is already in place. So the loop only needs `while j >= 0`."],
 "Copy `b` into the tail and call `sort`: O((m+n) log(m+n)). Or merge into a new list: O(m+n) extra memory.",
 "`i = m−1`, `j = len(b)−1`, `k = m+len(b)−1`. While `j >= 0`: write the larger of `a[i]` and `b[j]` at `k` and move that index.\n\nDry run `[2,5,9,_,_]`, `[1,6]`: 9 > 6 → slot 4 = 9; 5 < 6 → slot 3 = 6; 5 > 1 → slot 2 = 5; 2 > 1 → slot 1 = 2; i exhausted → slot 0 = 1.",
 "Time O(m + n), space O(1).",
 "Merging forwards overwrites unread elements. Stopping when `i` runs out leaves elements of `b` uncopied (second wrong solution fails on `a = [0], m = 0, b = [1]`).",
 "Identical to [Merge Sorted Array](#/problem/merge-sorted-array). Discuss merging k sorted files that do not fit in memory: a heap of the k current heads.")),

P("cluster-shuffled-words", "Cluster Shuffled Words", "Easy", "Sorting & Searching", "clusterWords",
"""
Re-order a list of lower-case words so that words made of exactly the same letters (shuffles of one another) end up **next to each other**.

To make the answer unique: order the groups by their *signature* (the word's letters in alphabetical order), and inside a group order the words alphabetically.

**Constraints:** up to `10^4` words, each of length at most 20.

**Example:** `["tea", "bat", "eat", "tab", "ate", "cab"]` → `["cab", "bat", "tab", "ate", "eat", "tea"]` (signatures `abc`, `abt`, `aet`)
""",
'''class Solution:
    def clusterWords(self, words: List[str]) -> List[str]:
        return sorted(words, key=lambda w: ("".join(sorted(w)), w))
''',
[[["tea", "bat", "eat", "tab", "ate", "cab"]], [[]], [["x"]], [["b", "a"]], [["ab", "ba", "ab"]], [["abc", "bca", "xyz", "cab", "zyx"]],
 [["aa", "a", "aaa"]], [["listen", "google", "silent", "enlist", "elgoog"]], [["", "a", ""]], [_words], [_words[::-1][:700]],
 [["".join(R.sample("abcdefghij", 10)) for _ in range(2000)]], [["ba", "ab", "c"]]],
['''class Solution:
    def clusterWords(self, words):
        return sorted(words)
''', '''class Solution:
    def clusterWords(self, words):
        return sorted(words, key=lambda w: "".join(sorted(w)))
'''],
("Sorting with a key function: see [Sorting in Python](#/lesson/python/py-heapq-bisect-sorting).",
 "Two words are shuffles of each other exactly when their sorted letters are equal. Sorting the list by that signature therefore brings each group together; you never have to compare words pairwise.",
 ["What do `tea`, `eat` and `ate` have in common after you sort their letters?",
  "A sort can use any key you compute from the element.",
  "Use the tuple (signature, word) as the key to make the order fully determined."],
 "Compare every pair of words with a letter count: O(n²) comparisons.",
 "One call: `sorted(words, key=lambda w: (\"\".join(sorted(w)), w))`.\n\nDry run: keys (aet, tea), (abt, bat), (aet, eat), (abt, tab), (aet, ate), (abc, cab). Sorted: cab, bat, tab, ate, eat, tea.",
 "O(n · L log L) to build signatures plus O(n log n) comparisons of keys of length L.",
 "Plain alphabetical sorting does not group shuffles (`ate`, `bat`, `eat`). Sorting by signature only is correct for grouping but leaves the order inside a group to the stability of the sort, which the expected output here does not accept.",
 "If the order of groups does not matter, a dictionary from signature to list avoids the n log n sort entirely: see [Group Anagrams](#/problem/group-anagrams).")),

P("sparse-word-search", "Search With Blanks", "Medium", "Sorting & Searching", "findWord",
"""
A dictionary page was stored as a sorted array of distinct words, but many slots are empty strings `""` scattered between them, for example `["", "bee", "", "", "cow", "", "elk"]`. The non-empty words are in alphabetical order.

Return the index of `target` (a non-empty word), or `-1` if it is absent. Aim for binary-search behaviour when blanks are few.

**Constraints:** `0 <= len(words) <= 10^4`.

**Example 1:** `words = ["", "bee", "", "", "cow", "", "elk"], target = "cow"` → `4`

**Example 2:** same array, `target = "dog"` → `-1`
""",
'''class Solution:
    def findWord(self, words: List[str], target: str) -> int:
        lo, hi = 0, len(words) - 1
        while lo <= hi:
            mid = (lo + hi) // 2
            left, right = mid, mid + 1
            probe = -1
            while left >= lo or right <= hi:
                if left >= lo and words[left]:
                    probe = left
                    break
                if right <= hi and words[right]:
                    probe = right
                    break
                left -= 1
                right += 1
            if probe == -1:
                return -1
            if words[probe] == target:
                return probe
            if words[probe] < target:
                lo = probe + 1
            else:
                hi = probe - 1
        return -1
''',
[[["", "bee", "", "", "cow", "", "elk"], "cow"], [["", "bee", "", "", "cow", "", "elk"], "dog"], [[], "a"], [[""], "a"], [["a"], "a"],
 [["", "", ""], "a"], [["a", "", "", "", ""], "a"], [["", "", "", "", "z"], "z"], [["a", "", "c", "", "e"], "e"], [["a", "", "c", "", "e"], "b"],
 [["", "bee", "", "", "cow", "", "elk"], "bee"], [["", "bee", "", "", "cow", "", "elk"], "elk"], [_SP, _SPW[0]], [_SP, _SPW[-1]],
 [_SP, _SPW[700]], [_SP, "zzzz"], [_SP, _SPW[333]]],
['''class Solution:
    def findWord(self, words, target):
        lo, hi = 0, len(words) - 1
        while lo <= hi:
            mid = (lo + hi) // 2
            if words[mid] == target:
                return mid
            if words[mid] < target:
                lo = mid + 1
            else:
                hi = mid - 1
        return -1
'''],
("Binary search: see [Binary search done right](#/lesson/neet-window-stack/binary-search-right).",
 "Binary search needs a real word at the midpoint to decide which half to keep. If the midpoint is blank, slide to the nearest non-blank slot and use that as the pivot instead.",
 ["What goes wrong if the middle element is the empty string? (`\"\" < target` is always true.)",
  "From `mid`, look outward in both directions, one step at a time, for a non-empty word inside the current range.",
  "If the whole range is blank the target is not there."],
 "Linear scan: O(n) regardless of the blanks.",
 "Standard `lo`/`hi` loop. Find `probe`, the non-blank index nearest to `mid` within `[lo, hi]`. Compare `words[probe]` with the target and discard the half on the far side of `probe`.\n\nDry run for `cow`: lo 0, hi 6, mid 3 is blank; step outward: index 4 holds `cow` → found.",
 "O(log n) when blanks are rare; O(n) in the worst case (for example all blanks), which no algorithm can beat because every slot might have to be inspected.",
 "Treating `\"\"` as a normal value sends the search right every time (wrong solution). Searching outward beyond `lo`/`hi` re-examines discarded territory and can loop forever.",
 "Ask what should happen when the target *is* the empty string (here it is excluded). Related: [Search in Rotated Sorted Array](#/problem/search-in-rotated-sorted-array), another search where the midpoint needs interpretation.")),

P("zigzag-heights", "Zigzag Fence", "Medium", "Sorting & Searching", "zigzag",
"""
Fence posts of various heights must be arranged so that the heights alternate **high, low, high, low, …**: every post at an even index is at least as tall as its neighbours, and every post at an odd index is at most as tall as its neighbours.

Return any arrangement of the given heights with this property. (Equal neighbours are fine.)

**Constraints:** `0 <= len(heights) <= 10^4`. A solution without sorting exists.

**Example:** `[4, 8, 2, 6, 7]` → for instance `[8, 2, 6, 4, 7]`
""",
'''class Solution:
    def zigzag(self, heights: List[int]) -> List[int]:
        a = list(heights)
        for i in range(1, len(a)):
            if (i % 2 == 1 and a[i] > a[i - 1]) or (i % 2 == 0 and a[i] < a[i - 1]):
                a[i], a[i - 1] = a[i - 1], a[i]
        return a
''',
[[[4, 8, 2, 6, 7]], [[]], [[4]], [[1, 2]], [[2, 1]], [[1, 2, 3]], [[3, 2, 1]], [[7, 7, 7, 7]], [[1, 2, 3, 4, 5, 6]], [[6, 5, 4, 3, 2, 1]],
 [[R.randint(0, 100) for _ in range(9000)]], [list(range(8000))], [[0, 0, 1, 1, 0, 0, 1]], [[-3, -1, -2]]],
['''class Solution:
    def zigzag(self, heights):
        return sorted(heights, reverse=True)
''', '''class Solution:
    def zigzag(self, heights):
        a = sorted(heights)
        return a[len(a) // 2:] + a[:len(a) // 2]
'''],
("Local swaps and loop invariants; sorting as a baseline: see [Greedy method](#/lesson/neet-greedy-math/greedy-method).",
 "Walk left to right and repair each neighbouring pair that points the wrong way by swapping it. A swap never breaks the pair before it: if position i−1 was supposed to be a high point and receives an even larger value, it is still a high point.",
 ["A sorted array can be fixed by swapping pairs (1,2), (3,4), … Try it on `[1,2,3,4,5]`.",
  "Can you avoid the sort? Look at one pair at a time: at odd `i` you need `a[i] <= a[i-1]`.",
  "If the pair is wrong, swap. Convince yourself the earlier pair stays valid."],
 "Sort descending, then swap every pair starting at index 1: O(n log n).",
 "For i = 1 … n−1: odd i requires `a[i] <= a[i-1]`, even i requires `a[i] >= a[i-1]`; swap when violated.\n\nDry run `[4,8,2,6,7]`: i=1: 8 > 4 → swap → `[8,4,2,6,7]`. i=2: need 2 ≥ 4 → swap → `[8,2,4,6,7]`. i=3: need 6 ≤ 4 → swap → `[8,2,6,4,7]`. i=4: 7 ≥ 4 fine.",
 "Time O(n), space O(1) beyond the copy.",
 "A fully sorted array is not alternating. Rotating the sorted halves does not interleave them. Checking only one neighbour in your own tests: verify both sides of every post.",
 "The strict version (no equal neighbours) is harder and needs the median: LeetCode's *Wiggle Sort II*."),
checker='''def check(args, got, expected):
    heights = args[0]
    if not isinstance(got, list) or sorted(got) != sorted(heights):
        return False
    for i in range(1, len(got)):
        if i % 2 == 1 and got[i] > got[i - 1]:
            return False
        if i % 2 == 0 and got[i] < got[i - 1]:
            return False
    return True
'''),

P("rank-board", "Rank Board", "Medium", "Sorting & Searching", "RankBoard",
"""
Scores arrive one at a time in a live competition. At any moment the organisers may ask how a given score would rank.

Implement class `RankBoard`:

- `record(x)` records the score `x` (duplicates allowed).
- `countAtMost(x)` returns how many recorded scores are **less than or equal to** `x`.

**Constraints:** `0 <= x <= 10^5`; up to `2·10^4` calls. Both operations should be much faster than scanning all recorded scores.

**Example:** `record(5), record(1), record(4), record(4), countAtMost(4) → 3, countAtMost(0) → 0, record(9), countAtMost(100000) → 5`
""",
'''class RankBoard:
    SIZE = 100001

    def __init__(self):
        self.tree = [0] * (self.SIZE + 1)

    def record(self, x: int) -> None:
        i = x + 1
        while i <= self.SIZE:
            self.tree[i] += 1
            i += i & -i

    def countAtMost(self, x: int) -> int:
        i = min(x, self.SIZE - 1) + 1
        total = 0
        while i > 0:
            total += self.tree[i]
            i -= i & -i
        return total
''',
[[["RankBoard", "record", "record", "record", "record", "countAtMost", "countAtMost", "record", "countAtMost"], [[], [5], [1], [4], [4], [4], [0], [9], [100000]]],
 [["RankBoard", "countAtMost"], [[], [50]]],
 [["RankBoard", "record", "countAtMost", "countAtMost"], [[], [0], [0], [1]]],
 [["RankBoard", "record", "record", "record", "countAtMost", "countAtMost"], [[], [7], [7], [7], [6], [7]]],
 [["RankBoard", "record", "record", "countAtMost", "countAtMost", "countAtMost"], [[], [100000], [99999], [99998], [99999], [100000]]],
 [["RankBoard", "record", "countAtMost", "record", "countAtMost"], [[], [3], [2], [2], [2]]],
 _ops(("RankBoard", []), 3300, [("record", lambda: [R.randint(0, 100)]), ("countAtMost", lambda: [R.randint(0, 100)])]),
 _ops(("RankBoard", []), 3300, [("record", lambda: [R.randint(0, 100000)]), ("countAtMost", lambda: [R.randint(0, 100000)])]),
 _ops(("RankBoard", []), 3300, [("record", lambda: [R.randint(0, 100000)]), ("record", lambda: [R.randint(0, 5)]), ("countAtMost", lambda: [R.randint(0, 100000)])]),
 [["RankBoard"] + ["record"] * 3000 + ["countAtMost"] * 100, [[]] + [[i * 7 % 1000] for i in range(3000)] + [[i * 10] for i in range(100)]]],
['''class RankBoard:
    def __init__(self):
        self.seen = []

    def record(self, x):
        self.seen.append(x)

    def countAtMost(self, x):
        return sum(1 for v in self.seen if v < x)
''', '''class RankBoard:
    def __init__(self):
        self.seen = set()

    def record(self, x):
        self.seen.add(x)

    def countAtMost(self, x):
        return sum(1 for v in self.seen if v <= x)
'''],
("Prefix sums; binary search with `bisect`; optionally the binary indexed tree described in [Sorting and searching](#/lesson/interview-prep/sorting-searching).",
 "\"How many values are ≤ x\" is a prefix count over the value axis. You need a structure that supports both *add one at position x* and *sum of positions 0…x* quickly. A sorted list gives O(log n) queries but O(n) inserts; a binary indexed tree gives O(log M) for both.",
 ["A plain list makes `record` O(1) and the query O(n). A sorted list makes the query a binary search. Start there.",
  "Keeping a count per score value turns the query into a prefix sum of counts.",
  "A binary indexed (Fenwick) tree stores partial sums so that both update and prefix sum touch only about log M cells."],
 "Append to a list and count on every query: O(n) per query, O(n²) overall.",
 "The tree is an array where cell `i` covers a block of `i & -i` positions ending at `i`. Update: add 1 at `i`, then jump to `i + (i & -i)`. Query: add cell `i`, jump to `i − (i & -i)`. Positions are shifted by one because index 0 cannot be used.\n\nDry run: record(4) updates cells 5, 6, 8, 16, …. countAtMost(4) reads cell 5 and cell 4 → finds the score.",
 "O(log M) per operation with M = 100,001 possible scores (17 steps); space O(M).",
 "Using `<` instead of `<=`. Storing scores in a set loses duplicates. Forgetting the +1 shift, which makes the update loop spin forever at index 0.",
 "Without a bound on the scores, use a balanced binary search tree whose nodes store the size of their left subtree, or `bisect.insort` on a sorted list. Related: LeetCode's *Count of Smaller Numbers After Self*.")),

P("staircase-grid-search", "Staircase Grid Search", "Medium", "Sorting & Searching", "locate",
"""
A price table is a grid in which every row is sorted in increasing order from left to right **and** every column is sorted in increasing order from top to bottom. All values are distinct.

Return `[row, col]` of `target`, or `[-1, -1]` if it does not occur. Aim for O(rows + cols) steps.

**Constraints:** `0 <= rows, cols <= 300`.

**Example:** `grid = [[1, 4, 9], [2, 7, 12], [6, 8, 15]]`: `target = 7` → `[1, 1]`; `target = 5` → `[-1, -1]`
""",
'''class Solution:
    def locate(self, grid: List[List[int]], target: int) -> List[int]:
        if not grid or not grid[0]:
            return [-1, -1]
        r, c = 0, len(grid[0]) - 1
        while r < len(grid) and c >= 0:
            if grid[r][c] == target:
                return [r, c]
            if grid[r][c] > target:
                c -= 1
            else:
                r += 1
        return [-1, -1]
''',
[[[[1, 4, 9], [2, 7, 12], [6, 8, 15]], 7], [[[1, 4, 9], [2, 7, 12], [6, 8, 15]], 5], [[], 1], [[[]], 1], [[[3]], 3], [[[3]], 4],
 [[[1, 2, 3, 4]], 4], [[[1], [2], [3]], 1], [[[1, 4, 9], [2, 7, 12], [6, 8, 15]], 6], [[[1, 4, 9], [2, 7, 12], [6, 8, 15]], 9],
 [[[1, 4, 9], [2, 7, 12], [6, 8, 15]], 15], [[[1, 4, 9], [2, 7, 12], [6, 8, 15]], 0], [_stair, _stair[59][0]], [_stair, _stair[0][32]],
 [_stair, _stair[31][20]], [_stair, _stair[31][20] + 1], [[[1, 10, 20], [2, 11, 21], [3, 12, 22]], 12]],
['''class Solution:
    def locate(self, grid, target):
        for r, row in enumerate(grid):
            if row and row[0] <= target <= row[-1]:
                i = bisect.bisect_left(row, target)
                return [r, i] if i < len(row) and row[i] == target else [-1, -1]
        return [-1, -1]
'''],
("Sorted order in two directions: see [Binary search on rotated arrays and partitions](#/lesson/neet-window-stack/rotated-and-partitions).",
 "Stand in the top-right corner. Everything to the left is smaller and everything below is larger, so one comparison with the target eliminates either the whole current column or the whole current row.",
 ["From a corner cell with value v: if v is too big, where can the target not be?",
  "The top-left corner is useless (both moves go to larger values). Top-right or bottom-left work.",
  "Move left when the cell is too large, down when it is too small; stop when you leave the grid."],
 "Check every cell: O(rows × cols). Binary search each row: O(rows log cols).",
 "Start at `(0, cols−1)`. Loop: equal → found; larger → `c -= 1`; smaller → `r += 1`.\n\nDry run target 7: 9 > 7 → left to 4; 4 < 7 → down to 7 → found at [1, 1].",
 "At most rows + cols steps, O(1) space.",
 "Assuming the whole grid is sorted row after row (it is not: 2 follows 9). Picking the first row whose range contains the target and searching only it (wrong solution fails for 7 when the first row is `[1, 4, 9]`). Empty grid or empty rows.",
 "Same idea as LeetCode's *Search a 2D Matrix II*. A divide-and-conquer alternative cuts the grid into quadrants around a diagonal element.")),

P("triangle-kind", "Triangle Classifier", "Easy", "Testing", "classify",
"""
A classic function used to teach testing: given three integer side lengths, classify the triangle.

Return:

- `"invalid"` if the lengths cannot form a triangle with positive area (a non-positive side, or one side at least as long as the other two together),
- `"equilateral"` if all three sides are equal,
- `"isosceles"` if exactly two are equal,
- `"scalene"` otherwise.

**Constraints:** each side is an integer in `[-10^18, 10^18]`.

**Example 1:** `(3, 4, 5)` → `"scalene"`

**Example 2:** `(1, 2, 3)` → `"invalid"` (flat: 1 + 2 = 3)
""",
'''class Solution:
    def classify(self, a: int, b: int, c: int) -> str:
        x, y, z = sorted((a, b, c))
        if x <= 0 or x + y <= z:
            return "invalid"
        if x == z:
            return "equilateral"
        if x == y or y == z:
            return "isosceles"
        return "scalene"
''',
[[3, 4, 5], [1, 2, 3], [2, 2, 2], [2, 2, 3], [3, 2, 2], [2, 3, 2], [0, 0, 0], [-1, 5, 5], [1, 1, 2], [5, 1, 1], [1, 5, 1],
 [10 ** 18, 10 ** 18, 10 ** 18], [10 ** 18, 10 ** 18 - 1, 1], [10 ** 18, 10 ** 18 - 1, 2], [7, 10, 5], [1, 1, 1], [2, 2, 4], [0, 4, 4]],
['''class Solution:
    def classify(self, a, b, c):
        if a <= 0 or b <= 0 or c <= 0 or a + b < c or a + c < b or b + c < a:
            return "invalid"
        if a == b == c:
            return "equilateral"
        if a == b or b == c or a == c:
            return "isosceles"
        return "scalene"
''', '''class Solution:
    def classify(self, a, b, c):
        if a + b <= c:
            return "invalid"
        if a == b == c:
            return "equilateral"
        if a == b or b == c:
            return "isosceles"
        return "scalene"
'''],
("Conditionals; equivalence classes and boundary values from [Testing questions](#/lesson/interview-prep/testing-questions).",
 "The code is four `if`s; the skill is thinking of all the inputs that could break it. Sorting the sides first means there is only one triangle inequality to check and only two equality patterns.",
 ["List the classes of input before coding: each output, plus zero, negative, flat, and each *position* of the odd side.",
  "After sorting into x ≤ y ≤ z, the only inequality that can fail is x + y > z.",
  "Check validity first; an invalid triple such as (2, 2, 4) must not be reported as isosceles."],
 "Without sorting you need three inequality checks and three equality checks; missing one permutation is the classic bug.",
 "Sort. Invalid if the smallest is ≤ 0 or `x + y <= z`. Equilateral if `x == z`. Isosceles if `x == y or y == z`.\n\nDry run (5, 1, 1): sorted 1, 1, 5 → 1 + 1 ≤ 5 → invalid. (3, 2, 2): sorted 2, 2, 3 → valid, x == y → isosceles.",
 "O(1).",
 "Using `<` instead of `<=` accepts flat triangles (first wrong solution says (1, 2, 3) is scalene). Checking only one ordering of the inequality or of the equal pair. In languages with fixed-size integers, `x + y` can overflow: compare `x > z - y` instead.",
 "Write the test list for this function as an interviewer would expect: valid of each kind, every permutation of the unequal side, zero, negative, flat, nearly flat, maximum values, and non-integer or missing input if the language allows them.")),

P("boundary-values", "Boundary Value Set", "Easy", "Testing", "boundaryValues",
"""
A form field accepts integers in one or more **valid ranges**, each given as `[lo, hi]` (inclusive). Boundary-value analysis says the most valuable test inputs are the edges of each range and their immediate neighbours.

Return the sorted list of **distinct** test values consisting of, for every range: `lo - 1`, `lo`, `lo + 1`, `hi - 1`, `hi`, `hi + 1`.

**Constraints:** up to `2000` ranges with `lo <= hi`; ranges may touch or overlap.

**Example 1:** `[[1, 10]]` → `[0, 1, 2, 9, 10, 11]`

**Example 2:** `[[5, 5]]` → `[4, 5, 6]`
""",
'''class Solution:
    def boundaryValues(self, ranges: List[List[int]]) -> List[int]:
        values = set()
        for lo, hi in ranges:
            values.update((lo - 1, lo, lo + 1, hi - 1, hi, hi + 1))
        return sorted(values)
''',
[[[[1, 10]]], [[[5, 5]]], [[]], [[[0, 1]]], [[[1, 3], [5, 9]]], [[[1, 3], [4, 6]]], [[[-5, -1], [1, 5]]], [[[10, 20], [1, 3]]],
 [[[0, 100], [50, 60]]], [[[i * 10, i * 10 + 3] for i in range(2000)]], [[[R.randint(0, 500), 600 + R.randint(0, 500)] for _ in range(1500)]],
 [[[7, 8]]], [[[2, 4], [2, 4]]]],
['''class Solution:
    def boundaryValues(self, ranges):
        out = []
        for lo, hi in ranges:
            out += [lo - 1, lo, lo + 1, hi - 1, hi, hi + 1]
        return sorted(out)
''', '''class Solution:
    def boundaryValues(self, ranges):
        values = set()
        for lo, hi in ranges:
            values.update((lo, hi))
        return sorted(values)
'''],
("Sets and sorting; the technique itself is explained in [Partitions and boundaries](#/lesson/thinking/partitions-boundaries).",
 "Bugs cluster at edges because that is where `<` gets confused with `<=`. For each range collect the six values around its two edges; a set removes the repeats that occur when a range is short or ranges are close together.",
 ["How many distinct values does the range [5, 5] produce? And [7, 8]?",
  "Collect into a set, not a list.",
  "Sort once at the end."],
 "Append to a list and remove duplicates by scanning: O(n²).",
 "Loop over ranges, `values.update(...)` with the six numbers, return `sorted(values)`.\n\nDry run `[[5,5]]`: 4, 5, 6, 4, 5, 6 → set {4, 5, 6}.",
 "O(n log n) for the sort, O(n) space.",
 "Returning duplicates. Forgetting the values just *outside* the range, which are the ones that should be rejected.",
 "Extend to floats (use the smallest representable step), dates, and strings (length boundaries). Combine with equivalence partitioning: one value from the middle of each range.")),

P("pairwise-gaps", "Pairwise Coverage Gaps", "Medium", "Testing", "uncoveredPairs",
"""
A product has several configuration parameters; parameter `i` has `levels[i]` possible settings numbered from 0. Testing all combinations is too expensive, so teams aim for **pairwise coverage**: for every two parameters, every combination of their settings should appear together in at least one test.

Each test is a list giving one setting per parameter. Return how many (parameter pair, setting pair) combinations are **not covered** by the given tests.

**Constraints:** `1 <= number of parameters <= 12`; each `levels[i] <= 8`; up to `600` tests.

**Example:** `levels = [2, 2, 2]`, `tests = [[0,0,0],[1,1,1]]` → `6` (each of the three parameter pairs has four setting pairs, and only `(0,0)` and `(1,1)` are covered)
""",
'''class Solution:
    def uncoveredPairs(self, levels: List[int], tests: List[List[int]]) -> int:
        n = len(levels)
        total = sum(levels[i] * levels[j] for i in range(n) for j in range(i + 1, n))
        seen = set()
        for test in tests:
            for i in range(n):
                for j in range(i + 1, n):
                    seen.add((i, j, test[i], test[j]))
        return total - len(seen)
''',
[[[2, 2, 2], [[0, 0, 0], [1, 1, 1]]], [[3], []], [[2, 2], []], [[2, 2], [[0, 0], [0, 1], [1, 0], [1, 1]]], [[2, 2], [[0, 0], [0, 0]]],
 [[2, 2, 2], [[0, 0, 0], [0, 1, 1], [1, 0, 1], [1, 1, 0]]], [[3, 2], [[0, 0], [1, 1], [2, 0]]], [[1, 1, 1], [[0, 0, 0]]],
 [[1, 1, 1], []], [[8] * 12, [[R.randrange(8) for _ in range(12)] for _ in range(600)]],
 [[2, 3, 4, 5], [[R.randrange(2), R.randrange(3), R.randrange(4), R.randrange(5)] for _ in range(30)]],
 [[4, 4, 4, 4, 4], [[i % 4, (i // 4) % 4, (i + i // 4) % 4, (i + 2 * (i // 4)) % 4, (i + 3 * (i // 4)) % 4] for i in range(16)]],
 [[2, 2, 2, 2], [[0, 0, 0, 0]]]],
['''class Solution:
    def uncoveredPairs(self, levels, tests):
        n = len(levels)
        total = sum(levels[i] * levels[j] for i in range(n) for j in range(i + 1, n))
        covered = 0
        for test in tests:
            covered += n * (n - 1) // 2
        return max(0, total - covered)
''', '''class Solution:
    def uncoveredPairs(self, levels, tests):
        total = 1
        for lv in levels:
            total *= lv
        return total - len(set(map(tuple, tests)))
'''],
("Sets of tuples and counting pairs; pairwise testing is introduced in [Decision tables, states and pairwise](#/lesson/thinking/tables-states-pairwise).",
 "Count what must be covered, count what is covered, subtract. A covered item is identified by four numbers: the two parameter indexes and their two settings. Storing those 4-tuples in a set removes repeats automatically.",
 ["How many combinations exist for parameters i and j? `levels[i] * levels[j]`.",
  "One test covers one setting pair for each of the n(n−1)/2 parameter pairs, but several tests may cover the same one.",
  "Put `(i, j, test[i], test[j])` in a set; the answer is total − size of the set."],
 "For every parameter pair and every setting pair, scan all tests looking for a match: O(n² · L² · T).",
 "Compute `total`. For each test and each i < j add the 4-tuple. Return the difference.\n\nDry run example: total = 3 × 4 = 12. Test 000 covers (0,1,0,0), (0,2,0,0), (1,2,0,0); test 111 covers three more. 12 − 6 = 6.",
 "Time O(T · n²), space O(min(T · n², total)).",
 "Assuming every test covers n(n−1)/2 *new* combinations. Confusing pairwise coverage with full combinatorial coverage (the second wrong solution).",
 "Generate a small pairwise test suite greedily: repeatedly add the test that covers the most still-uncovered pairs. The last hand-written test in this problem is an orthogonal array: 16 tests covering all pairs of five 4-level parameters.")),
]

for _p in PROBLEMS:
    if _p["id"] == "ctci-merge-into-buffer":
        _p["inplace_arg"] = 0
