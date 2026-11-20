import random

_r = random.Random(48)


def _mat(n, m, lo=-1000, hi=1000):
    return [[_r.randint(lo, hi) for _ in range(m)] for _ in range(n)]


def _zero_mat(n, m, zeros):
    a = [[_r.randint(1, 9) for _ in range(m)] for _ in range(n)]
    for _ in range(zeros):
        a[_r.randrange(n)][_r.randrange(m)] = 0
    return a


def _digits(k):
    return str(_r.randint(1, 9)) + "".join(str(_r.randint(0, 9)) for _ in range(k - 1))


def _ds_ops(n):
    ops, args = ["DetectSquares"], [[]]
    for _ in range(n):
        p = [_r.randint(0, 12), _r.randint(0, 12)]
        if _r.random() < 0.6:
            ops.append("add")
        else:
            ops.append("count")
        args.append([p])
    return [ops, args]


_ds_big = _ds_ops(3000)

_gcd_big = [_r.choice([2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]) * 6 for _ in range(10000)]
_gcd_big2 = [720720 // _r.choice([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 16]) for _ in range(10000)]

PROBLEMS = [
# ------------------------------------------------------------------ Rotate Image
dict(
    id="rotate-image",
    title="Rotate Image",
    difficulty="Medium",
    pattern="Matrix",
    leetcode="https://leetcode.com/problems/rotate-image/",
    neetcode="https://neetcode.io/problems/rotate-matrix",
    entry="rotate",
    inplace_arg=0,
    description=r"""
`matrix` is an `n × n` grid. Rotate it **90° clockwise in place**: modify the given list of lists and
return nothing. (Building a fresh matrix and returning it does not count — the judge inspects the
argument you were given.)

**Constraints**
- `1 <= n <= 20` on LeetCode (tests here go to 200), `-1000 <= matrix[i][j] <= 1000`

**Example 1:** `[[1,2,3],[4,5,6],[7,8,9]]` → becomes `[[7,4,1],[8,5,2],[9,6,3]]`.

**Example 2:** `[[1,2],[3,4]]` → becomes `[[3,1],[4,2]]`.
""",
    starter='''class Solution:
    def rotate(self, matrix: List[List[int]]) -> None:
        """Do not return anything, modify matrix in-place instead."""
        pass
''',
    solution='''class Solution:
    def rotate(self, matrix):
        n = len(matrix)
        for i in range(n):                    # 1) transpose across the main diagonal
            for j in range(i + 1, n):
                matrix[i][j], matrix[j][i] = matrix[j][i], matrix[i][j]
        for row in matrix:                    # 2) mirror each row left <-> right
            row.reverse()
''',
    tests=[
        [[[1, 2, 3], [4, 5, 6], [7, 8, 9]]],
        [[[1, 2], [3, 4]]],
        [[[1]]],
        [[[5, 1, 9, 11], [2, 4, 8, 10], [13, 3, 6, 7], [15, 14, 12, 16]]],
        [[[0, 0], [0, 1]]],
        [[[i * 5 + j for j in range(5)] for i in range(5)]],
        [[[-1, -2, -3], [-4, -5, -6], [-7, -8, -9]]],
        [_mat(6, 6)],
        [_mat(7, 7)],
        [_mat(100, 100)],
        [_mat(151, 151, 0, 9)],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def rotate(self, matrix):
        n = len(matrix)
        for i in range(n):
            for j in range(i + 1, n):
                matrix[i][j], matrix[j][i] = matrix[j][i], matrix[i][j]
''',
        '''class Solution:
    def rotate(self, matrix):
        matrix = [list(r) for r in zip(*matrix[::-1])]   # rebinds the local name only
''',
        '''class Solution:
    def rotate(self, matrix):
        matrix.reverse()                                  # counter-clockwise by mistake
        n = len(matrix)
        for i in range(n):
            for j in range(i + 1, n):
                matrix[i][j], matrix[j][i] = matrix[j][i], matrix[i][j]
        for row in matrix: row.reverse()
        matrix.reverse()
''',
    ],
    guide=dict(
        prereqs="2-D indexing; the lesson *Matrix manipulation*.",
        intuition=r"""
A clockwise quarter turn sends cell `(r, c)` to `(c, n-1-r)`. That map is the composition of two easy
in-place operations: **transpose** (`(r,c) → (c,r)`) and then **reverse every row**
(`(c,r) → (c, n-1-r)`). Each is a sequence of swaps, so no extra matrix is needed.
""",
        hints=[
            "Write down where (r, c) goes after a clockwise rotation.",
            "Can that mapping be split into two simpler reflections?",
            "Transpose (swap matrix[i][j] with matrix[j][i] for j > i), then reverse each row.",
        ],
        brute_force="Allocate `out[c][n-1-r] = matrix[r][c]` and copy back — O(n²) time but O(n²) extra space, which violates the in-place requirement.",
        approach=r"""
**Dry run** `[[1,2,3],[4,5,6],[7,8,9]]`:
- transpose → `[[1,4,7],[2,5,8],[3,6,9]]`
- reverse rows → `[[7,4,1],[8,5,2],[9,6,3]]` ✔

**Alternative — rotate four cells at a time.** For each layer `L` and offset `k`, cycle
`top → right → bottom → left`:
```
tmp = m[L][L+k]
m[L][L+k]         = m[n-1-L-k][L]
m[n-1-L-k][L]     = m[n-1-L][n-1-L-k]
m[n-1-L][n-1-L-k] = m[L+k][n-1-L]
m[L+k][n-1-L]     = tmp
```
""",
        complexity="Time **O(n²)** (every cell touched a constant number of times), space **O(1)**.",
        pitfalls=r"""
- Transposing with `j` from `0` swaps each pair twice — net no-op. Start `j` at `i + 1`.
- `matrix = ...` rebinds the local name; the caller's matrix is unchanged. Use `matrix[:] = ...` if you
  must build a new one (still O(n²) extra space though).
- Counter-clockwise = transpose then reverse **columns** (or reverse rows first, then transpose).
""",
        follow_up="Rotate by 180° (reverse rows and reverse each row). Rotate an `m × n` (non-square) matrix — must allocate a new one.",
    ),
),
# ------------------------------------------------------------------ Spiral Matrix
dict(
    id="spiral-matrix",
    title="Spiral Matrix",
    difficulty="Medium",
    pattern="Matrix / simulation",
    leetcode="https://leetcode.com/problems/spiral-matrix/",
    neetcode="https://neetcode.io/problems/spiral-matrix",
    entry="spiralOrder",
    description=r"""
Return every element of the `m × n` grid `matrix` in **clockwise spiral order**: across the top row,
down the right column, back along the bottom row, up the left column, then repeat on the inner
rectangle.

**Constraints**
- `1 <= m, n <= 10` on LeetCode (tests here are bigger), `-100 <= matrix[i][j] <= 100`

**Example 1:** `[[1,2,3],[4,5,6],[7,8,9]]` → `[1,2,3,6,9,8,7,4,5]`.

**Example 2:** `[[1,2,3,4],[5,6,7,8],[9,10,11,12]]` → `[1,2,3,4,8,12,11,10,9,5,6,7]`.
""",
    starter='''class Solution:
    def spiralOrder(self, matrix: List[List[int]]) -> List[int]:
        pass
''',
    solution='''class Solution:
    def spiralOrder(self, matrix):
        out = []
        top, bottom = 0, len(matrix) - 1
        left, right = 0, len(matrix[0]) - 1
        while top <= bottom and left <= right:
            for c in range(left, right + 1):
                out.append(matrix[top][c])
            top += 1
            for r in range(top, bottom + 1):
                out.append(matrix[r][right])
            right -= 1
            if top <= bottom:                         # a bottom row still exists
                for c in range(right, left - 1, -1):
                    out.append(matrix[bottom][c])
                bottom -= 1
            if left <= right:                         # a left column still exists
                for r in range(bottom, top - 1, -1):
                    out.append(matrix[r][left])
                left += 1
        return out
''',
    tests=[
        [[[1, 2, 3], [4, 5, 6], [7, 8, 9]]],
        [[[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12]]],
        [[[7]]],
        [[[1, 2, 3, 4]]],
        [[[1], [2], [3], [4]]],
        [[[1, 2], [3, 4]]],
        [[[1, 2], [3, 4], [5, 6]]],
        [[[1, 2, 3], [4, 5, 6]]],
        [[[i * 4 + j for j in range(4)] for i in range(4)]],
        [[[i * 3 + j for j in range(3)] for i in range(7)]],
        [_mat(60, 90, -100, 100)],
        [_mat(101, 3, -100, 100)],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def spiralOrder(self, matrix):
        out = []
        top, bottom, left, right = 0, len(matrix) - 1, 0, len(matrix[0]) - 1
        while top <= bottom and left <= right:
            for c in range(left, right + 1): out.append(matrix[top][c])
            top += 1
            for r in range(top, bottom + 1): out.append(matrix[r][right])
            right -= 1
            for c in range(right, left - 1, -1): out.append(matrix[bottom][c])   # no guard
            bottom -= 1
            for r in range(bottom, top - 1, -1): out.append(matrix[r][left])
            left += 1
        return out
''',
        '''class Solution:
    def spiralOrder(self, matrix):
        return [x for row in matrix for x in row]
''',
    ],
    guide=dict(
        prereqs="Loops with shrinking bounds. Lesson *Matrix manipulation*.",
        intuition=r"""
Keep four walls — `top`, `bottom`, `left`, `right`. Walk along the top wall and push it down; walk the
right wall and push it left; walk the bottom wall (if it still exists) and push it up; walk the left
wall (if it still exists) and push it right. Repeat until the walls cross.
""",
        hints=[
            "Maintain four boundaries and shrink one after traversing it.",
            "After the top row and right column, the remaining rectangle might be empty — check before the bottom and left passes.",
            "Loop while top <= bottom and left <= right.",
        ],
        brute_force="Direction-vector simulation with a `visited` grid: turn right when the next cell is out of bounds or visited. Also O(mn), but O(mn) extra space.",
        approach=r"""
**Dry run** 3×4 example:
- top row `1 2 3 4` → top=1
- right col `8 12` → right=2
- bottom row (top 1 ≤ bottom 2) `11 10 9` → bottom=1
- left col (left 0 ≤ right 2) `5` → left=1
- next loop: top row `6 7` → top=2 > bottom=1, right col empty, guards skip the rest.
Result `[1,2,3,4,8,12,11,10,9,5,6,7]`.
""",
        complexity="Time **O(m·n)**, space **O(1)** extra besides the output.",
        pitfalls=r"""
- Without the two guards a single remaining row or column is emitted twice (try a 3×1 or 1×3 grid).
- Off-by-one in reversed ranges: `range(right, left - 1, -1)`.
""",
        follow_up="*Spiral Matrix II* (fill 1..n² in spiral order), *Spiral Matrix III* (walk outward from a start cell).",
    ),
),
# ------------------------------------------------------------------ Set Matrix Zeroes
dict(
    id="set-matrix-zeroes",
    title="Set Matrix Zeroes",
    difficulty="Medium",
    pattern="Matrix / in-place markers",
    leetcode="https://leetcode.com/problems/set-matrix-zeroes/",
    neetcode="https://neetcode.io/problems/set-zeroes-in-matrix",
    entry="setZeroes",
    inplace_arg=0,
    description=r"""
For every cell of the `m × n` grid `matrix` that is `0` **in the original grid**, set its entire row
and entire column to `0`. Modify `matrix` in place and return nothing. Aim for `O(1)` extra space.

**Constraints**
- `1 <= m, n <= 200`, values fit in a 32-bit signed int.

**Example 1:** `[[1,1,1],[1,0,1],[1,1,1]]` → `[[1,0,1],[0,0,0],[1,0,1]]`.

**Example 2:** `[[0,1,2,0],[3,4,5,2],[1,3,1,5]]` → `[[0,0,0,0],[0,4,5,0],[0,3,1,0]]`.
""",
    starter='''class Solution:
    def setZeroes(self, matrix: List[List[int]]) -> None:
        """Do not return anything, modify matrix in-place instead."""
        pass
''',
    solution='''class Solution:
    def setZeroes(self, matrix):
        m, n = len(matrix), len(matrix[0])
        first_row_zero = any(matrix[0][c] == 0 for c in range(n))
        first_col_zero = any(matrix[r][0] == 0 for r in range(m))
        # use row 0 / column 0 as marker arrays for the rest of the grid
        for r in range(1, m):
            for c in range(1, n):
                if matrix[r][c] == 0:
                    matrix[r][0] = 0
                    matrix[0][c] = 0
        for r in range(1, m):
            for c in range(1, n):
                if matrix[r][0] == 0 or matrix[0][c] == 0:
                    matrix[r][c] = 0
        if first_row_zero:
            for c in range(n):
                matrix[0][c] = 0
        if first_col_zero:
            for r in range(m):
                matrix[r][0] = 0
''',
    tests=[
        [[[1, 1, 1], [1, 0, 1], [1, 1, 1]]],
        [[[0, 1, 2, 0], [3, 4, 5, 2], [1, 3, 1, 5]]],
        [[[0]]],
        [[[5]]],
        [[[1, 0]]],
        [[[1], [0], [3]]],
        [[[1, 2, 3], [4, 5, 6]]],
        [[[1, 2, 3, 4], [5, 0, 7, 8], [0, 10, 11, 12], [13, 14, 15, 0]]],
        [[[1, 0, 3]]],
        [[[-1], [2], [3]]],
        [_zero_mat(100, 100, 12)],
        [_zero_mat(120, 80, 3)],
        [_zero_mat(90, 90, 0)],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def setZeroes(self, matrix):
        m, n = len(matrix), len(matrix[0])
        for r in range(m):                      # zeroes while scanning: cascades
            for c in range(n):
                if matrix[r][c] == 0:
                    for k in range(n): matrix[r][k] = 0
                    for k in range(m): matrix[k][c] = 0
''',
        '''class Solution:
    def setZeroes(self, matrix):
        m, n = len(matrix), len(matrix[0])
        for r in range(m):
            for c in range(n):
                if matrix[r][c] == 0:
                    matrix[r][0] = 0; matrix[0][c] = 0
        for r in range(m):                      # markers in row/col 0 not protected
            for c in range(n):
                if matrix[r][0] == 0 or matrix[0][c] == 0:
                    matrix[r][c] = 0
''',
    ],
    guide=dict(
        prereqs="Lesson *Matrix manipulation* (using the matrix itself as scratch space).",
        intuition=r"""
You need to remember *which rows* and *which columns* contained a zero, then zero them out afterwards.
Two boolean arrays (size m and n) do it in O(m+n) space. To get O(1), store those flags **inside the
matrix**: row 0 records which columns must be zeroed, column 0 records which rows must be. The only
casualty is the information about row 0 and column 0 themselves, so save that in two booleans first.
""",
        hints=[
            "Why does zeroing immediately while scanning go wrong?",
            "First solve it with two sets: zero_rows and zero_cols.",
            "Reuse row 0 and column 0 as those sets; remember separately whether row 0 / column 0 had a zero.",
        ],
        brute_force="Copy the matrix and read zeros from the copy while writing the original — O(mn) extra space. Or the two-set version: O(m+n) extra.",
        approach=r"""
1. `first_row_zero`, `first_col_zero` = does row 0 / column 0 contain a zero?
2. For inner cells `r,c ≥ 1`: if zero, mark `matrix[r][0] = matrix[0][c] = 0`.
3. For inner cells: zero them if their row marker or column marker is zero.
4. Finally zero row 0 and/or column 0 if the booleans say so.

**Dry run** `[[0,1,2,0],[3,4,5,2],[1,3,1,5]]`: `first_row_zero = True` (two zeros in row 0),
`first_col_zero = True` (`matrix[0][0] = 0`). Step 2 finds no zeros among the inner cells. Step 3: the
original zero at `matrix[0][3]` now acts as a column marker, so `matrix[1][3]` and `matrix[2][3]`
become 0. Step 4 zeroes row 0 and column 0 → `[[0,0,0,0],[0,4,5,0],[0,3,1,0]]`.
""",
        complexity="Time **O(m·n)**, space **O(1)**.",
        pitfalls=r"""
- Zeroing on the fly turns new zeros into new triggers — everything collapses to 0.
- Processing row 0 / column 0 before the inner cells destroys the markers.
- `matrix[0][0]` is ambiguous (row 0 or column 0?) — that is why two separate booleans are used.
""",
        follow_up="*Game of Life* uses the same \"encode extra state in the cell\" trick (store old and new state in two bits).",
    ),
),
# ------------------------------------------------------------------ Happy Number
dict(
    id="happy-number",
    title="Happy Number",
    difficulty="Easy",
    pattern="Math / cycle detection",
    leetcode="https://leetcode.com/problems/happy-number/",
    neetcode="https://neetcode.io/problems/non-cyclical-number",
    entry="isHappy",
    description=r"""
Start from a positive integer `n` and repeatedly replace it by the **sum of the squares of its
decimal digits**. If this process eventually reaches `1`, `n` is *happy*; otherwise it loops
forever in a cycle that never contains `1`. Return whether `n` is happy.

**Constraints**
- `1 <= n <= 2^31 - 1`

**Example 1:** `n = 19` → `True` (1²+9²=82 → 68 → 100 → 1).

**Example 2:** `n = 2` → `False`.
""",
    starter='''class Solution:
    def isHappy(self, n: int) -> bool:
        pass
''',
    solution='''class Solution:
    def isHappy(self, n):
        def step(x):
            s = 0
            while x:
                x, d = divmod(x, 10)
                s += d * d
            return s
        slow, fast = n, step(n)          # Floyd's tortoise and hare
        while fast != 1 and slow != fast:
            slow = step(slow)
            fast = step(step(fast))
        return fast == 1
''',
    tests=[
        [19], [2], [1], [7], [4], [10], [100], [1111111], [116], [2147483647], [3], [97], [1000000000],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def isHappy(self, n):
        for _ in range(3):                 # gives up after a fixed number of steps
            n = sum(int(d) ** 2 for d in str(n))
        return n == 1
''',
        '''class Solution:
    def isHappy(self, n):
        seen = set()
        while n != 1 and n not in seen:
            seen.add(n)
            n = sum(int(d) for d in str(n)) ** 2      # squares the sum, not each digit
        return n == 1
''',
    ],
    guide=dict(
        prereqs="Digit extraction with `divmod(x, 10)`; cycle detection (hash set or Floyd).",
        intuition=r"""
The sequence is completely determined by the current value, so it either hits 1 or eventually
**repeats** a value — and once it repeats it is stuck in a loop. It cannot grow forever: a number with
`d` digits maps to at most `81·d`, which is smaller than the number itself once `d ≥ 4`, so values
quickly fall below 1000 (for 32-bit input, the first step is already ≤ 81·10 = 810). Detecting the
loop is the whole problem.
""",
        hints=[
            "Why can't the sequence grow without bound?",
            "If a value repeats, the sequence cycles. How do you detect a repeat?",
            "Use a set of seen values — or Floyd's slow/fast pointers for O(1) space.",
        ],
        brute_force="Iterate a fixed large number of times and hope — wrong in principle. The set-based solution is the honest baseline: O(log n) per step, small number of steps.",
        approach=r"""
**Set version**: `while n != 1 and n not in seen: seen.add(n); n = step(n)`; return `n == 1`.

**Floyd**: `slow` moves one step, `fast` two. If there is a cycle they meet; if 1 is reached first,
`fast` hits 1 (and 1 → 1 is itself a fixed point).

**Dry run** `n = 2`: 2 → 4 → 16 → 37 → 58 → 89 → 145 → 42 → 20 → **4** (repeat) → not happy. In fact
every unhappy number falls into this exact 8-cycle.
""",
        complexity="Each step is O(number of digits) = O(log n); the number of steps is bounded by a small constant after the first, so **O(log n)** time; O(1) space with Floyd.",
        pitfalls=r"""
- Squaring the *sum* of digits instead of summing the *squares*.
- Hard-coding an iteration cap.
""",
        follow_up="Same cycle-detection idea: *Linked List Cycle*, *Find the Duplicate Number* (Floyd on an implicit function graph).",
    ),
),
# ------------------------------------------------------------------ Plus One
dict(
    id="plus-one",
    title="Plus One",
    difficulty="Easy",
    pattern="Math / digit arithmetic",
    leetcode="https://leetcode.com/problems/plus-one/",
    neetcode="https://neetcode.io/problems/plus-one",
    entry="plusOne",
    description=r"""
A non-negative integer is stored as a list of its decimal digits `digits`, most significant first,
with no leading zeros (except the number 0 itself, `[0]`). Add one and return the resulting digit list.

**Constraints**
- `1 <= len(digits) <= 100` (tests here go to 10^4), `0 <= digits[i] <= 9`

**Example 1:** `[1,2,3]` → `[1,2,4]`.

**Example 2:** `[9,9]` → `[1,0,0]`.
""",
    starter='''class Solution:
    def plusOne(self, digits: List[int]) -> List[int]:
        pass
''',
    solution='''class Solution:
    def plusOne(self, digits):
        digits = digits[:]
        for i in range(len(digits) - 1, -1, -1):
            if digits[i] < 9:
                digits[i] += 1          # no carry beyond this point
                return digits
            digits[i] = 0               # 9 + 1 = 10: write 0, carry 1
        return [1] + digits             # all nines
''',
    tests=[
        [[1, 2, 3]], [[9, 9]], [[0]], [[9]], [[4, 3, 2, 1]], [[1, 9, 9]], [[8, 9, 9, 9]],
        [[1, 0, 0, 0]], [[9, 8, 9]], [[2, 9]],
        [[9] * 10000], [[1] + [0] * 9999], [[_r.randint(0, 9) for _ in range(5000)] + [9, 9, 9]],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def plusOne(self, digits):
        digits = digits[:]
        digits[-1] += 1
        return digits
''',
        '''class Solution:
    def plusOne(self, digits):
        digits = digits[:]
        for i in range(len(digits) - 1, -1, -1):
            if digits[i] < 9:
                digits[i] += 1
                return digits
            digits[i] = 0
        return digits                   # forgets the new leading 1
''',
    ],
    guide=dict(
        prereqs="Grade-school addition with carries (lesson *Interview number theory*).",
        intuition="Adding one only changes the trailing run of 9s (they become 0s) and the digit just before it (incremented). If *every* digit is 9, the answer is 1 followed by zeros.",
        hints=[
            "Start from the last digit.",
            "A digit below 9 absorbs the carry and you can stop immediately.",
            "If the loop finishes, all digits were 9: prepend a 1.",
        ],
        brute_force="`int(''.join(map(str, digits))) + 1` and convert back. Works in Python (arbitrary precision) but defeats the purpose and is O(n²)-ish for huge numbers due to base conversion.",
        approach=r"""
**Dry run** `[1,9,9]`: i=2 → 9 → 0; i=1 → 9 → 0; i=0 → 1 < 9 → 2 → `[2,0,0]`.
`[9,9]`: both become 0, loop ends → `[1,0,0]`.
""",
        complexity="Time **O(n)** worst case (all 9s), O(1) amortised on random input. Space O(1) extra (O(n) only when a new digit is prepended).",
        pitfalls="Forgetting the all-nines case. Mutating the caller's list may be unexpected; copy if in doubt.",
        follow_up="*Add Binary*, *Add Strings*, *Add Two Numbers* (linked lists), *Multiply Strings*.",
    ),
),
# ------------------------------------------------------------------ Pow(x, n)
dict(
    id="powx-n",
    title="Pow(x, n)",
    difficulty="Medium",
    pattern="Math / fast exponentiation",
    leetcode="https://leetcode.com/problems/powx-n/",
    neetcode="https://neetcode.io/problems/pow-x-n",
    entry="myPow",
    compare="float",
    tolerance=1e-5,
    description=r"""
Compute `x` raised to the integer power `n` **without** using `**`, `pow` or `math.pow`. `n` may be
negative (then the answer is `1 / x^|n|`) and as large as `2^31 - 1` in magnitude, so a loop that
multiplies `n` times is far too slow.

**Constraints**
- `-100.0 < x < 100.0`, `-2^31 <= n <= 2^31 - 1`
- either `x != 0` or `n > 0`; the true answer lies in `[-10^4, 10^4]`.
- Answers are compared with a relative/absolute tolerance of `1e-5`.

**Example 1:** `x = 2.0, n = 10` → `1024.0`.

**Example 2:** `x = 2.0, n = -2` → `0.25`.
""",
    starter='''class Solution:
    def myPow(self, x: float, n: int) -> float:
        pass
''',
    solution='''class Solution:
    def myPow(self, x, n):
        if n < 0:
            x, n = 1 / x, -n
        result = 1.0
        while n:
            if n & 1:            # this bit of the exponent is set
                result *= x
            x *= x               # x, x^2, x^4, x^8, ...
            n >>= 1
        return result
''',
    tests=[
        [2.0, 10],
        [2.0, -2],
        [2.1, 3],
        [1.0, 2147483647],
        [-1.0, -2147483648],
        [-1.0, 2147483647],
        [0.5, 2147483647],
        [2.0, -2147483648],
        [5.5, 0],
        [0.0, 5],
        [-2.0, 3],
        [1.0000001, 10000000],
        [-3.0, -3],
        [99.0, 2],
        [0.99999, 1000000],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def myPow(self, x, n):
        result = 1.0
        while n > 0:             # ignores negative exponents
            if n & 1: result *= x
            x *= x; n >>= 1
        return result
''',
        '''class Solution:
    def myPow(self, x, n):
        if n < 0:
            x, n = 1 / x, -n
        result = 1.0
        while n:
            if n & 1: result *= x
            x *= x; n >>= 1
        return abs(result)       # loses the sign for odd powers of negatives
''',
    ],
    guide=dict(
        prereqs="Binary representation of integers; recursion. Lesson *Interview number theory* (fast exponentiation).",
        intuition=r"""
`x^n` with `n` even is `(x^(n/2))²` — one recursive call and one multiplication instead of `n/2`
multiplications. With `n` odd, peel off one factor `x`. That halves the exponent each step, giving
`O(log n)` multiplications. Iteratively: look at the binary digits of `n`; the powers
`x, x², x⁴, x⁸, …` are produced by repeated squaring, and you multiply in exactly those whose bit is 1.
""",
        hints=[
            "Handle negative n by inverting x.",
            "x^n = (x^(n//2))^2, times one extra x when n is odd.",
            "Iterative: while n: if n & 1: res *= x; x *= x; n >>= 1.",
        ],
        brute_force="Multiply `|n|` times: **O(|n|)** — about 2·10⁹ multiplications for the extreme cases.",
        approach=r"""
**Dry run** `x = 3, n = 13` (binary `1101`):

| n (binary) | bit | result | x |
|---|---|---|---|
| 1101 | 1 | 3 | 9 |
| 110 | 0 | 3 | 81 |
| 11 | 1 | 243 | 6561 |
| 1 | 1 | 1594323 | … |

`3^13 = 3^8 · 3^4 · 3^1 = 1594323` ✔

**Recursive version** (Goodrich, Code Fragment 4.12 does the same):
```
def power(x, n):
    if n == 0: return 1.0
    half = power(x, n // 2)
    return half * half * (x if n % 2 else 1)
```
""",
        complexity="Time **O(log |n|)**, space O(1) iterative (O(log n) recursion depth).",
        pitfalls=r"""
- In C/Java, `-n` overflows for `n = -2^31`; Python ints are unbounded so this is a non-issue here —
  but mention it in interviews.
- Calling `power(x, n//2)` **twice** per level makes it O(n) again.
- Python's `//` floors toward −∞ (`-3 // 2 == -2`), so normalise negative n first.
""",
        follow_up="Modular exponentiation `pow(a, b, m)` (same loop, reduce mod m each multiply) — the basis of RSA and of *Super Pow*. Matrix fast power computes Fibonacci in O(log n).",
    ),
),
# ------------------------------------------------------------------ Multiply Strings
dict(
    id="multiply-strings",
    title="Multiply Strings",
    difficulty="Medium",
    pattern="Math / digit arithmetic",
    leetcode="https://leetcode.com/problems/multiply-strings/",
    neetcode="https://neetcode.io/problems/multiply-strings",
    entry="multiply",
    description=r"""
`num1` and `num2` are non-negative integers written as decimal strings (no leading zeros unless the
number is `"0"`). Return their product, also as a decimal string. Do it with grade-school digit
arithmetic — **don't** convert the whole strings to integers (in Python that would be trivially
`str(int(a)*int(b))`; the judge can't stop you, but an interviewer will).

**Constraints**
- `1 <= len(num1), len(num2) <= 200`

**Example 1:** `num1 = "2", num2 = "3"` → `"6"`.

**Example 2:** `num1 = "123", num2 = "456"` → `"56088"`.
""",
    starter='''class Solution:
    def multiply(self, num1: str, num2: str) -> str:
        pass
''',
    solution='''class Solution:
    def multiply(self, num1, num2):
        if num1 == "0" or num2 == "0":
            return "0"
        m, n = len(num1), len(num2)
        res = [0] * (m + n)               # product has at most m + n digits
        for i in range(m - 1, -1, -1):
            a = ord(num1[i]) - 48
            for j in range(n - 1, -1, -1):
                b = ord(num2[j]) - 48
                total = res[i + j + 1] + a * b     # digit i*j lands at position i+j+1
                res[i + j + 1] = total % 10
                res[i + j] += total // 10
        k = 0
        while k < len(res) - 1 and res[k] == 0:    # strip leading zeros
            k += 1
        return "".join(map(str, res[k:]))
''',
    tests=[
        ["2", "3"],
        ["123", "456"],
        ["0", "52"],
        ["9", "9"],
        ["1", "1"],
        ["99", "99"],
        ["999", "0"],
        ["10", "10"],
        ["1", "123456789"],
        ["123456789", "987654321"],
        [_digits(200), _digits(200)],
        ["9" * 200, "9" * 200],
        [_digits(150), "1" + "0" * 50],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def multiply(self, num1, num2):
        m, n = len(num1), len(num2)
        res = [0] * (m + n)
        for i in range(m - 1, -1, -1):
            for j in range(n - 1, -1, -1):
                t = res[i + j + 1] + int(num1[i]) * int(num2[j])
                res[i + j + 1] = t % 10
                res[i + j] += t // 10
        return "".join(map(str, res))           # keeps leading zeros
''',
        '''class Solution:
    def multiply(self, num1, num2):
        out = 0
        for i, d in enumerate(reversed(num1)):
            out += int(d) * int(num2[-1]) * 10 ** i   # only uses the last digit of num2
        return str(out)
''',
    ],
    guide=dict(
        prereqs="Long multiplication by hand; place value. Lesson *Interview number theory*.",
        intuition=r"""
In long multiplication, digit `num1[i]` times digit `num2[j]` contributes to the column for
`10^((m-1-i) + (n-1-j))`. Indexing an `m+n`-slot result array from the left, that column is slot
`i + j + 1`, and its carry goes to slot `i + j`. Accumulate all `m·n` partial products into those slots
and propagate carries as you go.
""",
        hints=[
            "How many digits can the product of an m-digit and an n-digit number have?",
            "Where does the product of num1[i] and num2[j] land in a length-(m+n) array?",
            "Process from the right; res[i+j+1] gets total % 10, res[i+j] gets the carry. Strip leading zeros.",
        ],
        brute_force="Multiply `num1` by each digit of `num2` to get a shifted string, then add all `n` strings with *Add Strings* — also O(m·n) but with lots of string copying.",
        approach=r"""
**Dry run** `"12" × "34"` (m=n=2, res has 4 slots):
- i=1 (2), j=1 (4): 8 → res `[0,0,0,8]`
- i=1, j=0 (3): 6 + res[2]=0 → res `[0,0,6,8]`
- i=0 (1), j=1: 4 + res[2]=6 = 10 → res[2]=0, res[1]+=1 → `[0,1,0,8]`
- i=0, j=0: 3 + res[1]=1 = 4 → `[0,4,0,8]`
Strip → `"408"` ✔ (12·34 = 408).
""",
        complexity="Time **O(m·n)**, space **O(m+n)**.",
        pitfalls=r"""
- Leading zeros: `"0"×"52"` must be `"0"`, not `"00"`; strip but keep at least one digit.
- Adding the carry into `res[i+j]` without later normalising — it is fixed when that slot is next
  used as `i+j+1`, except for slot 0 which never overflows (product fits in m+n digits).
""",
        follow_up="Karatsuba multiplication is O(n^1.585); CPython uses it for big ints. *Add Strings*, *Plus One*.",
    ),
),
# ------------------------------------------------------------------ Detect Squares
dict(
    id="detect-squares",
    title="Detect Squares",
    difficulty="Medium",
    pattern="Math & geometry / hash map",
    leetcode="https://leetcode.com/problems/detect-squares/",
    neetcode="https://neetcode.io/problems/count-squares",
    kind="class",
    entry="DetectSquares",
    description=r"""
Design a structure over points on a 2-D integer grid:

- `DetectSquares()` — starts empty.
- `add(point)` — inserts `point = [x, y]`. The same point may be added many times; each copy counts
  separately.
- `count(point)` — the query point `[qx, qy]` is **not** stored. Return the number of ways to choose
  three stored points that, together with the query point, are the corners of an
  **axis-aligned square with positive area**.

**Constraints**
- `0 <= x, y <= 1000`; at most 3000 calls in total.

**Example:**
```
ops  = ["DetectSquares","add",[3,10],"add",[11,2],"add",[3,2],"count",[11,10],"count",[14,8],"add",[11,2],"count",[11,10]]
out  = [null, null, null, null, 1, 0, null, 2]
```
After adding `[11,2]` a second time there are two different squares (they differ in which copy of
`[11,2]` is used).
""",
    starter='''class DetectSquares:

    def __init__(self):
        pass

    def add(self, point: List[int]) -> None:
        pass

    def count(self, point: List[int]) -> int:
        pass
''',
    solution='''class DetectSquares:
    def __init__(self):
        self.cnt = collections.Counter()      # (x, y) -> multiplicity
        self.pts = []                         # distinct points, for iteration

    def add(self, point):
        p = tuple(point)
        if self.cnt[p] == 0:
            self.pts.append(p)
        self.cnt[p] += 1

    def count(self, point):
        qx, qy = point
        total = 0
        for x, y in self.pts:
            # (x, y) is the corner diagonally opposite the query
            if abs(x - qx) != abs(y - qy) or x == qx:
                continue
            total += self.cnt[(x, y)] * self.cnt[(x, qy)] * self.cnt[(qx, y)]
        return total
''',
    tests=[
        [["DetectSquares", "add", "add", "add", "count", "count", "add", "count"],
         [[], [[3, 10]], [[11, 2]], [[3, 2]], [[11, 10]], [[14, 8]], [[11, 2]], [[11, 10]]]],
        [["DetectSquares", "count"], [[], [[1, 1]]]],
        [["DetectSquares", "add", "add", "add", "count"], [[], [[0, 0]], [[0, 1]], [[1, 0]], [[1, 1]]]],
        [["DetectSquares", "add", "add", "add", "add", "add", "add", "count"],
         [[], [[0, 0]], [[0, 2]], [[2, 0]], [[0, -0]], [[2, 2]], [[2, 0]], [[0, 2]]]],
        [["DetectSquares", "add", "add", "add", "count", "count", "count"],
         [[], [[1, 1]], [[1, 1]], [[1, 1]], [[1, 1]], [[2, 2]], [[0, 0]]]],
        [["DetectSquares", "add", "add", "add", "count"], [[], [[0, 0]], [[0, 2]], [[2, 0]], [[2, 2]]]],
        [["DetectSquares", "add", "add", "add", "count"], [[], [[5, 5]], [[5, 7]], [[3, 5]], [[3, 7]]]],
        [["DetectSquares", "add", "add", "add", "count"], [[], [[0, 0]], [[0, 3]], [[2, 0]], [[2, 3]]]],
        [["DetectSquares", "add", "add", "add", "add", "add", "add", "add", "add", "count"],
         [[], [[1, 1]], [[1, 2]], [[2, 1]], [[1, 0]], [[0, 1]], [[0, 0]], [[2, 2]], [[2, 0]], [[1, 1]]]],
        [["DetectSquares", "add", "add", "add", "count"], [[], [[1000, 1000]], [[0, 1000]], [[1000, 0]], [[0, 0]]]],
        _ds_big,
    ],
    examples=1,
    wrong_solutions=[
        '''class DetectSquares:
    def __init__(self):
        self.cnt = collections.Counter()
    def add(self, point):
        self.cnt[tuple(point)] += 1
    def count(self, point):
        qx, qy = point
        total = 0
        for (x, y) in list(self.cnt):
            if x - qx == y - qy and x != qx:       # only one diagonal direction
                total += self.cnt[(x, y)] * self.cnt[(x, qy)] * self.cnt[(qx, y)]
        return total
''',
        '''class DetectSquares:
    def __init__(self):
        self.s = set()
    def add(self, point):
        self.s.add(tuple(point))                    # ignores duplicates
    def count(self, point):
        qx, qy = point
        return sum(1 for (x, y) in self.s
                   if abs(x - qx) == abs(y - qy) and x != qx and (x, qy) in self.s and (qx, y) in self.s)
''',
    ],
    guide=dict(
        prereqs="Hash maps with tuple keys; counting with multiplicity. Lesson *Matrix manipulation* (coordinate geometry section).",
        intuition=r"""
An axis-aligned square through the query `(qx, qy)` is pinned down by the corner **diagonally
opposite** it, `(x, y)`: it must satisfy `|x − qx| = |y − qy| ≠ 0`. The two remaining corners are then
forced: `(x, qy)` and `(qx, y)`. So iterate over stored points as diagonal candidates and multiply the
multiplicities of the three corners.
""",
        hints=[
            "Given the query and one more corner, how many squares are determined?",
            "Choose the diagonal corner: |x - qx| == |y - qy| and the side is non-zero.",
            "Multiply counts of (x, y), (x, qy) and (qx, y); keep a Counter of points.",
        ],
        brute_force="Try every triple of stored points — O(n³) per query.",
        approach=r"""
`add`: increment `cnt[(x,y)]`, and remember each distinct point once in a list.
`count`: for each distinct `(x, y)` with `abs(x-qx) == abs(y-qy)` and `x != qx`, add
`cnt[x,y] * cnt[x,qy] * cnt[qx,y]`.

**Dry run** (example, last query `(11,10)`, after `[11,2]` added twice):
diagonal candidate `(3,2)`: |3−11| = 8 = |2−10| ✔ → `cnt(3,2)·cnt(3,10)·cnt(11,2) = 1·1·2 = 2`.
""",
        complexity="`add` **O(1)**; `count` **O(P)** where P = number of distinct points (or O(1000) if you iterate over the points sharing the query's x-coordinate and try both directions). Space O(P).",
        pitfalls=r"""
- Checking only one diagonal direction (`x−qx == y−qy`) misses half the squares.
- Zero-area "squares" when the candidate equals the query point (`x == qx`).
- Duplicates multiply — use counts, not a set.
""",
        follow_up="Count squares that need not be axis-aligned (use any pair as a side and rotate by 90°), *Minimum Area Rectangle*.",
    ),
),
# ------------------------------------------------------------------ Count Primes (extra)
dict(
    id="count-primes",
    title="Count Primes",
    difficulty="Medium",
    pattern="Math / sieve of Eratosthenes",
    leetcode="https://leetcode.com/problems/count-primes/",
    entry="countPrimes",
    description=r"""
Return how many prime numbers are **strictly less than** `n`.

**Constraints**
- `0 <= n <= 5·10^6` (tests here stay at or below `2·10^6` to keep the browser snappy)

**Example 1:** `n = 10` → `4` (2, 3, 5, 7).

**Example 2:** `n = 2` → `0`.
""",
    starter='''class Solution:
    def countPrimes(self, n: int) -> int:
        pass
''',
    solution='''class Solution:
    def countPrimes(self, n):
        if n < 3:
            return 0
        is_p = bytearray([1]) * n
        is_p[0] = is_p[1] = 0
        i = 2
        while i * i < n:
            if is_p[i]:
                # cross off i*i, i*i + i, ... (smaller multiples were crossed by smaller primes)
                is_p[i * i:n:i] = bytes(len(range(i * i, n, i)))
            i += 1
        return sum(is_p)
''',
    tests=[[10], [0], [1], [2], [3], [4], [5], [100], [499979], [1000], [10007], [1000000], [2000000]],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def countPrimes(self, n):
        if n < 3: return 0
        is_p = [True] * (n + 1)                 # counts primes <= n
        is_p[0] = is_p[1] = False
        i = 2
        while i * i <= n:
            if is_p[i]:
                for k in range(i * i, n + 1, i): is_p[k] = False
            i += 1
        return sum(is_p)
''',
        '''class Solution:
    def countPrimes(self, n):
        return sum(1 for k in range(2, n) if k == 2 or k % 2)   # "odd numbers are prime"
''',
    ],
    guide=dict(
        prereqs="Lesson *Interview number theory* (primes and the sieve).",
        intuition=r"""
Instead of testing each number for primality, **cross off composites**. Every composite `c < n` has a
prime factor `p ≤ √c`, so it gets crossed off when you process `p`. And when processing prime `p` you
can start at `p²`, because smaller multiples `k·p` with `k < p` were already crossed off by `k`'s
smallest prime factor.
""",
        hints=[
            "Trial division of every number up to √k is O(n√n). Can you reuse work across numbers?",
            "Mark multiples of each prime as composite.",
            "Only primes p with p*p < n need processing; start crossing at p*p.",
        ],
        brute_force="For each `k < n`, test divisibility by `2..√k`: **O(n√n)** ≈ 2.8·10⁹ steps for 2·10⁶ — too slow in Python.",
        approach=r"""
**Dry run** `n = 30`: start all as prime; p=2 crosses 4,6,…,28; p=3 crosses 9,15,21,27 (already 12, 18…);
p=5 crosses 25; 6² = 36 ≥ 30 so stop. Survivors: 2,3,5,7,11,13,17,19,23,29 → **10**.

Python tip: slice assignment `is_p[p*p::p] = bytes(k)` crosses off a whole progression in C speed,
which is 20–50× faster than an explicit loop.
""",
        complexity="Time **O(n log log n)**, space **O(n)**.",
        pitfalls=r"""
- Off by one: primes **strictly less than** `n`.
- Starting the inner loop at `2p` is correct but slower; starting at `p²` requires the outer bound `p*p < n`.
- Using a Python `list` of bools for n = 5·10⁶ is memory-hungry; `bytearray` is compact.
""",
        follow_up="Linear sieve (each composite crossed once), segmented sieve for ranges, smallest-prime-factor sieve for fast factorisation.",
    ),
),
# ------------------------------------------------------------------ GCD/LCM warm-up (own problem)
dict(
    id="math-gcd",
    title="GCD and LCM of an Array",
    difficulty="Easy",
    pattern="Math / Euclid's algorithm",
    entry="gcdAndLcm",
    description=r"""
*Warm-up (original problem).* Given a non-empty list of positive integers `nums`, return
`[g, l]` where `g` is the **greatest common divisor** of all the numbers and `l` is their **least
common multiple**. Implement gcd yourself with Euclid's algorithm — no `math.gcd` / `math.lcm`.

**Constraints**
- `1 <= len(nums) <= 10^4`, `1 <= nums[i] <= 10^9`
- The LCM of each test is guaranteed to be below `2^53`.

**Example 1:** `nums = [12, 18, 30]` → `[6, 180]`.

**Example 2:** `nums = [7]` → `[7, 7]`.
""",
    starter='''class Solution:
    def gcdAndLcm(self, nums: List[int]) -> List[int]:
        pass
''',
    solution='''class Solution:
    def gcdAndLcm(self, nums):
        def gcd(a, b):
            while b:
                a, b = b, a % b
            return a
        g = l = nums[0]
        for x in nums[1:]:
            g = gcd(g, x)
            l = l // gcd(l, x) * x        # divide first to keep numbers small
        return [g, l]
''',
    tests=[
        [[12, 18, 30]],
        [[7]],
        [[1, 1, 1]],
        [[2, 3]],
        [[4, 6]],
        [[17, 34, 51]],
        [[1000000000, 999999999]],
        [[6, 10, 15]],
        [[8, 8, 8, 8]],
        [[2, 4, 8, 16, 32]],
        [[13, 1]],
        [_gcd_big],
        [_gcd_big2],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def gcdAndLcm(self, nums):
        g, p = nums[0], 1
        for x in nums:
            a, b = g, x
            while b: a, b = b, a % b
            g = a
            p *= x
        return [g, p]                     # product is not the LCM
''',
        '''class Solution:
    def gcdAndLcm(self, nums):
        def gcd(a, b):
            while b: a, b = b, a % b
            return a
        g = gcd(nums[0], nums[-1])        # only looks at two of the numbers
        l = nums[0]
        for x in nums[1:]:
            l = l // gcd(l, x) * x
        return [g, l]
''',
    ],
    guide=dict(
        prereqs="Integer division and remainder. Lesson *Interview number theory* (gcd section).",
        intuition=r"""
Euclid: any common divisor of `a` and `b` also divides `a mod b` (since `a mod b = a − q·b`), and
vice versa, so `gcd(a, b) = gcd(b, a mod b)`. The second argument shrinks fast (at least halving every
two steps), so it reaches 0 in `O(log min(a,b))` steps, at which point the first argument is the gcd.
For lcm, use `lcm(a, b) = a·b / gcd(a, b)`. Both operations are associative, so fold them across the
array.
""",
        hints=[
            "gcd(a, b) = gcd(b, a % b), and gcd(a, 0) = a.",
            "lcm(a, b) = a // gcd(a, b) * b.",
            "Fold left: g = gcd(g, x), l = lcm(l, x).",
        ],
        brute_force="Try every candidate divisor from `min(nums)` downward — O(min · n). For lcm, step through multiples of the max — potentially astronomically many.",
        approach=r"""
**Dry run** `gcd(30, 18)`: (30,18) → (18,12) → (12,6) → (6,0) → **6**.
Array `[12,18,30]`: g: gcd(12,18)=6, gcd(6,30)=6. l: lcm(12,18)=12/6·18=36, lcm(36,30)=36/6·30=180.
""",
        complexity="Time **O(n · log V)** where V is the largest value (big-int lcm arithmetic aside). Space O(1).",
        pitfalls=r"""
- Computing `a*b // gcd` multiplies first — fine in Python, but in fixed-width languages it overflows; divide first.
- The product of the numbers is a multiple but usually not the *least* one.
- `gcd(0, x) = x` — matters if you ever start the fold with 0.
""",
        follow_up="Extended Euclid finds `x, y` with `ax + by = gcd(a,b)` (modular inverses). LeetCode: *Find Greatest Common Divisor of Array*, *GCD of Strings*, *X of a Kind in a Deck of Cards*.",
    ),
),
]
