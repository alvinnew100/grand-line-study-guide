"""DSA in JavaScript: Rotate Image, Valid Sudoku, Trapping Rain Water, Merge k Sorted Lists."""
import random


def G(prereqs, intuition, hints, brute_force, approach, complexity, pitfalls, follow_up=""):
    return dict(prereqs=prereqs, intuition=intuition, hints=hints, brute_force=brute_force,
                approach=approach, complexity=complexity, pitfalls=pitfalls, follow_up=follow_up)


rng = random.Random(97)

LIST_HELPERS = r'''
// --- provided: ListNode and helpers (do not change) ---
class ListNode {
  constructor(val = 0, next = null) {
    this.val = val;
    this.next = next;
  }
}
function buildList(values) {            // [1, 2, 3] -> 1 -> 2 -> 3
  const dummy = new ListNode();
  let tail = dummy;
  for (const v of values) { tail.next = new ListNode(v); tail = tail.next; }
  return dummy.next;
}
function listToArray(head) {            // 1 -> 2 -> 3 -> [1, 2, 3]
  const out = [];
  for (let n = head; n && out.length < 100000; n = n.next) out.push(n.val);
  return out;
}
'''

CONVENTION = r"""

**How the tests talk to your code.** Lists are written as arrays: `[1, 2, 3]` means `1 -> 2 -> 3`, and `[]` is the
empty list (`null`). The provided `ListNode` class, `buildList` and `listToArray` helpers and the small driver at
the bottom convert between the two, so your function receives and returns real `ListNode` objects. Do not edit
the provided part.
"""

MK_DRIVER = "\nfunction runMergeK(lists) {\n  return listToArray(mergeKLists(lists.map(buildList)));\n}\n"
ROT_DRIVER = "\n// --- driver used by the tests (provided, do not change) ---\nfunction runRotate(matrix) {\n  rotate(matrix);      // your function must change `matrix` itself\n  return matrix;       // the tests then read the matrix back\n}\n"


def mk(body):
    return body + LIST_HELPERS + MK_DRIVER


def rot(body):
    return body + ROT_DRIVER


def square(n):
    return [[rng.randint(-1000, 1000) for _ in range(n)] for _ in range(n)]


def sorted_list(n):
    return sorted(rng.randint(-10000, 10000) for _ in range(n))


# a valid, completed sudoku and variants
BASE = [[(r * 3 + r // 3 + c) % 9 + 1 for c in range(9)] for r in range(9)]


def board(cells=None, blank=0.0, seed=1):
    r = random.Random(seed)
    b = [[str(v) for v in row] for row in BASE]
    for row in b:
        for i in range(9):
            if r.random() < blank:
                row[i] = "."
    for (i, j), v in (cells or {}).items():
        b[i][j] = v
    return b


EMPTY = [["."] * 9 for _ in range(9)]
CLASSIC = [list(s) for s in [
    "53..7....", "6..195...", ".98....6.", "8...6...3", "4..8.3..1", "7...2...6", ".6....28.", "...419..5", "....8..79"]]
ROW_DUP = [row[:] for row in CLASSIC]; ROW_DUP[0][2] = "5"
COL_DUP = [row[:] for row in CLASSIC]; COL_DUP[8][0] = "5"
BOX_DUP = [row[:] for row in CLASSIC]; BOX_DUP[1][1] = "9"   # 9 already at (2,1)

RAIN_BIG = [rng.randint(0, 10000) for _ in range(20000)]
RAIN_MOUNTAIN = list(range(0, 5000)) + list(range(5000, -1, -1))
RAIN_VALLEY = list(range(5000, -1, -1)) + list(range(0, 5001))

PROBLEMS = [
dict(
    id="js-rotate-image", title="Rotate Image", difficulty="Medium", pattern="Math & Geometry",
    leetcode="https://leetcode.com/problems/rotate-image/",
    neetcode="https://neetcode.io/problems/rotate-matrix",
    kind="js", entry="runRotate",
    description=r"""
You are given an `n x n` matrix (an array of `n` rows, each with `n` numbers). Turn it **90 degrees clockwise**,
changing the matrix **in place**: modify the very same array you were given, and do not build a second matrix.
The function returns nothing; the tests read the matrix after your function finishes.

- `1 <= n <= 20`
- `-1000 <= matrix[i][j] <= 1000`

**Example 1:** `[[1, 2, 3], [4, 5, 6], [7, 8, 9]]` becomes `[[7, 4, 1], [8, 5, 2], [9, 6, 3]]`

**Example 2:** `[[1, 2], [3, 4]]` becomes `[[3, 1], [4, 2]]`

**How the tests talk to your code.** The provided driver `runRotate` calls your `rotate(matrix)` and then returns
the same `matrix` array to be compared. A solution that returns a new matrix without changing the original fails.
""",
    starter="function rotate(matrix) {\n  // change matrix in place; no return value needed\n}\n" + ROT_DRIVER,
    solution=rot(r'''function rotate(matrix) {
  const n = matrix.length;
  // step 1: transpose (mirror across the main diagonal)
  for (let i = 0; i < n; i++) {
    for (let j = i + 1; j < n; j++) {
      [matrix[i][j], matrix[j][i]] = [matrix[j][i], matrix[i][j]];
    }
  }
  // step 2: reverse every row
  for (const row of matrix) row.reverse();
}
'''),
    tests=[[[[1, 2, 3], [4, 5, 6], [7, 8, 9]]], [[[1, 2], [3, 4]]], [[[5]]], [[[-1, 0], [0, 1]]],
           [[[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12], [13, 14, 15, 16]]],
           [[[0, 0, 0], [0, 1, 0], [0, 0, 0]]], [[[7, 7], [7, 7]]],
           [[[5, 1, 9, 11], [2, 4, 8, 10], [13, 3, 6, 7], [15, 14, 12, 16]]],
           [square(5)], [square(7)], [square(20)]],
    examples=2,
    wrong_solutions=[
        rot("function rotate(matrix) {\n  const n = matrix.length;\n  for (let i = 0; i < n; i++)\n    for (let j = i + 1; j < n; j++)\n      [matrix[i][j], matrix[j][i]] = [matrix[j][i], matrix[i][j]];\n}\n"),
        rot("function rotate(matrix) {\n  const n = matrix.length;\n  for (let i = 0; i < n; i++)\n    for (let j = i + 1; j < n; j++)\n      [matrix[i][j], matrix[j][i]] = [matrix[j][i], matrix[i][j]];\n  matrix.reverse();\n}\n"),
        rot("function rotate(matrix) {\n  const n = matrix.length;\n  const out = matrix.map((row, i) => row.map((_, j) => matrix[n - 1 - j][i]));\n  return out;\n}\n"),
    ],
    guide=G(
        prereqs="Nested arrays and swapping two values with destructuring `[a, b] = [b, a]` (lesson *JavaScript for coding interviews*); the matrix example in *Pattern map III*.",
        intuition="A clockwise quarter turn is two simple mirror moves in a row: first mirror the grid across its main diagonal (the transpose, where `matrix[i][j]` swaps with `matrix[j][i]`), then mirror each row left to right. Each mirror can be done with swaps, so no second matrix is needed.",
        hints=[
            "Write the 3 x 3 example on paper and see where the top row `1 2 3` ends up: it becomes the right-hand column.",
            "Try swapping `matrix[i][j]` with `matrix[j][i]` first and look at the result.",
            "After the transpose, what single operation on each row finishes the job?",
        ],
        brute_force="Allocate a new `n x n` matrix and copy: the cell at row `i`, column `j` goes to row `j`, column `n - 1 - i`. That is O(n^2) time but also O(n^2) extra space, and it does not change the original array, so it breaks the in-place rule.",
        approach="1. Transpose: for every `i`, and every `j > i`, swap `matrix[i][j]` and `matrix[j][i]`. Starting `j` at `i + 1` visits each pair once; starting at 0 would swap every pair twice and undo it.\n2. Reverse each row with `row.reverse()`.\n\n**Dry run** `[[1,2],[3,4]]`: transpose swaps the 2 and 3 to give `[[1,3],[2,4]]`; reversing each row gives `[[3,1],[4,2]]`.",
        complexity="Time O(n^2) because every cell is touched a constant number of times; space O(1) extra.",
        pitfalls="- Looping `j` from 0 instead of `i + 1` swaps each pair twice and leaves the matrix unchanged.\n- Transposing and then reversing the **order of rows** (`matrix.reverse()`) gives a counter-clockwise turn.\n- Assigning `matrix = newMatrix` only changes your local variable; the caller still holds the old array.",
        follow_up="Spiral Matrix and Set Matrix Zeroes also work on grids in place. For a counter-clockwise turn, reverse the rows first and then transpose.",
    ),
),
dict(
    id="js-valid-sudoku", title="Valid Sudoku", difficulty="Medium", pattern="Arrays & Hashing",
    leetcode="https://leetcode.com/problems/valid-sudoku/",
    neetcode="https://neetcode.io/problems/valid-sudoku",
    kind="js", entry="isValidSudoku",
    description=r"""
A Sudoku board is a `9 x 9` grid whose cells are either a digit character `"1"` to `"9"` or `"."` for an empty cell.
Decide whether the digits already placed obey the rules, ignoring whether the puzzle can be finished:

- a digit may appear at most once in each **row**,
- at most once in each **column**,
- and at most once in each of the nine `3 x 3` **boxes** (the grid cut into three bands of three columns by three bands of three rows).

Empty cells are never a problem. Return `true` if the board is valid so far, otherwise `false`.

**Example 1:** a board with the digits of a well-known puzzle and no repeats → `true`

**Example 2:** the same board with a second `"5"` in the first row → `false`
""",
    starter="function isValidSudoku(board) {\n  // your code\n}\n",
    solution=r'''function isValidSudoku(board) {
  const rows = Array.from({ length: 9 }, () => new Set());
  const cols = Array.from({ length: 9 }, () => new Set());
  const boxes = Array.from({ length: 9 }, () => new Set());
  for (let r = 0; r < 9; r++) {
    for (let c = 0; c < 9; c++) {
      const d = board[r][c];
      if (d === ".") continue;
      const b = Math.floor(r / 3) * 3 + Math.floor(c / 3);   // which box, numbered 0..8
      if (rows[r].has(d) || cols[c].has(d) || boxes[b].has(d)) return false;
      rows[r].add(d); cols[c].add(d); boxes[b].add(d);
    }
  }
  return true;
}
''',
    tests=[[CLASSIC], [ROW_DUP], [COL_DUP], [BOX_DUP], [EMPTY], [[[str(v) for v in row] for row in BASE]],
           [board({(0, 0): "5", (0, 1): "5"})], [board({(4, 4): "."}, blank=0.5, seed=3)],
           [board(blank=0.7, seed=5)], [board({(0, 8): "1", (8, 0): "1"}, blank=0.9, seed=8)],
           [[["1" if (r, c) in ((0, 0), (8, 8)) else "." for c in range(9)] for r in range(9)]],
           [[["1" if (r, c) in ((0, 0), (2, 2)) else "." for c in range(9)] for r in range(9)]]],
    examples=2,
    wrong_solutions=[
        "function isValidSudoku(board) {\n  for (let r = 0; r < 9; r++) {\n    const seen = new Set();\n    for (const d of board[r]) {\n      if (d === \".\") continue;\n      if (seen.has(d)) return false;\n      seen.add(d);\n    }\n  }\n  return true;\n}\n",
        "function isValidSudoku(board) {\n  for (let r = 0; r < 9; r++) {\n    const row = new Set(), col = new Set();\n    for (let c = 0; c < 9; c++) {\n      const a = board[r][c], b = board[c][r];\n      if (a !== \".\") { if (row.has(a)) return false; row.add(a); }\n      if (b !== \".\") { if (col.has(b)) return false; col.add(b); }\n    }\n  }\n  return true;\n}\n",
        "function isValidSudoku(board) {\n  const seen = new Set();\n  for (let r = 0; r < 9; r++)\n    for (let c = 0; c < 9; c++) {\n      const d = board[r][c];\n      if (seen.has(d + \"r\" + r) || seen.has(d + \"c\" + c) || seen.has(d + \"b\" + Math.floor(r / 3) + Math.floor(c / 3))) return false;\n      seen.add(d + \"r\" + r); seen.add(d + \"c\" + c); seen.add(d + \"b\" + Math.floor(r / 3) + Math.floor(c / 3));\n    }\n  return true;\n}\n",
    ],
    guide=G(
        prereqs="`Set` and `has`/`add` (lesson *JavaScript for coding interviews*); integer division with `Math.floor`.",
        intuition="Checking a rule means asking \"have I already seen this digit in this group?\" A `Set` answers that in one step. Every cell belongs to exactly three groups (its row, its column and its box), so keep nine sets for each kind and check all three while scanning the board once.",
        hints=[
            "You need 27 groups in total: 9 rows, 9 columns and 9 boxes.",
            "The box of cell `(r, c)` can be numbered with `Math.floor(r / 3) * 3 + Math.floor(c / 3)`.",
            "Skip `\".\"` cells; a repeated dot is not a violation.",
        ],
        brute_force="For every filled cell, rescan its row, its column and its box for the same digit: about 81 x 27 comparisons. That is constant time for a fixed 9 x 9 board but clumsy and easy to get wrong.",
        approach="1. Create `rows`, `cols` and `boxes`, each an array of nine empty `Set`s.\n2. For each cell `(r, c)` that is not `\".\"`, compute its box index `b`.\n3. If the digit is already in `rows[r]`, `cols[c]` or `boxes[b]`, return `false`.\n4. Otherwise add it to all three sets.\n5. After the scan return `true`.\n\n**Dry run:** `\"5\"` at `(0, 0)` goes into row 0, column 0, box 0. A second `\"5\"` at `(0, 1)` finds it in row 0 and returns `false` immediately.",
        complexity="Time O(81), which is O(1) for a fixed board (or O(n^2) for an n x n generalisation); space O(81) for the sets.",
        pitfalls="- Writing `Array(9).fill(new Set())` makes all nine entries the **same** set; use `Array.from({ length: 9 }, () => new Set())`.\n- Forgetting the box check: rows and columns alone accept boards with a repeat inside a 3 x 3 box.\n- Treating `\".\"` as a digit makes any board with two empty cells look invalid.\n- Computing the box index with `/` instead of `Math.floor(... / 3)` gives fractions.",
        follow_up="Sudoku Solver adds backtracking on top of exactly this validity check.",
    ),
),
dict(
    id="js-trapping-rain-water", title="Trapping Rain Water", difficulty="Hard", pattern="Two Pointers",
    leetcode="https://leetcode.com/problems/trapping-rain-water/",
    neetcode="https://neetcode.io/problems/trapping-rain-water",
    kind="js", entry="trap",
    description=r"""
You are given an array `height` of non-negative integers. Each number is the height of a bar of width 1, standing
side by side. After rain, water collects in the dips between taller bars. Return the total number of units of
water that stay trapped.

- `0 <= height.length <= 20000`
- `0 <= height[i] <= 10000`

**Example 1:** `[0, 1, 0, 2, 1, 0, 1, 3, 2, 1, 2, 1]` → `6`

**Example 2:** `[4, 2, 0, 3, 2, 5]` → `9`
""",
    starter="function trap(height) {\n  // your code\n}\n",
    solution=r'''function trap(height) {
  let l = 0, r = height.length - 1;
  let leftMax = 0, rightMax = 0, water = 0;
  while (l < r) {
    if (height[l] < height[r]) {            // the left side is the lower wall, so it decides
      leftMax = Math.max(leftMax, height[l]);
      water += leftMax - height[l];
      l++;
    } else {
      rightMax = Math.max(rightMax, height[r]);
      water += rightMax - height[r];
      r--;
    }
  }
  return water;
}
''',
    tests=[[[0, 1, 0, 2, 1, 0, 1, 3, 2, 1, 2, 1]], [[4, 2, 0, 3, 2, 5]], [[]], [[5]], [[3, 3]], [[1, 2, 3, 4, 5]],
           [[5, 4, 3, 2, 1]], [[5, 0, 5]], [[0, 0, 0]], [[2, 0, 2, 0, 2]], [RAIN_BIG], [RAIN_MOUNTAIN], [RAIN_VALLEY]],
    examples=2,
    wrong_solutions=[
        "function trap(height) {\n  let water = 0;\n  for (let i = 1; i < height.length - 1; i++) {\n    water += Math.max(0, Math.min(height[i - 1], height[i + 1]) - height[i]);\n  }\n  return water;\n}\n",
        "function trap(height) {\n  let water = 0;\n  for (let i = 0; i < height.length; i++) {\n    let left = 0;\n    for (let j = 0; j <= i; j++) left = Math.max(left, height[j]);\n    water += left - height[i];\n  }\n  return water;\n}\n",
        "function trap(height) {\n  const n = height.length;\n  let best = 0;\n  for (let i = 0; i < n; i++) for (let j = i + 1; j < n; j++) best = Math.max(best, Math.min(height[i], height[j]) * (j - i - 1));\n  return best;\n}\n",
    ],
    guide=G(
        prereqs="Two pointers moving inward from both ends (lesson *Pattern map I*), as in Container With Most Water.",
        intuition="Water above one bar rises to the lower of the tallest wall on its left and the tallest wall on its right, minus the bar's own height. If you know the left wall is the shorter side, you do not need the exact right maximum: it is at least as tall, so the left maximum alone decides the water there.",
        hints=[
            "For a single bar, how high does the water stand? Think of the tallest bar on each side.",
            "Computing both maxima for every bar works in O(n) time with two helper arrays. Can you drop the arrays?",
            "Move the pointer on the side whose current bar is lower, carrying a running maximum for that side only.",
        ],
        brute_force="For every bar scan left and right for the tallest walls: `min(maxLeft, maxRight) - height[i]`. O(n^2) time and O(1) space. Precomputing prefix and suffix maxima arrays gets O(n) time with O(n) space.",
        approach="1. `l = 0`, `r = n - 1`, `leftMax = rightMax = water = 0`.\n2. While `l < r`: if `height[l] < height[r]`, update `leftMax`, add `leftMax - height[l]` to `water`, move `l` right; otherwise do the mirror image on `r`.\n3. Return `water`.\n\n**Dry run** `[4, 2, 0, 3, 2, 5]`: the left bar 4 is lower than 5, so leftMax = 4; bars 2, 0, 3, 2 add 2 + 4 + 1 + 2 = 9 before the pointers meet.",
        complexity="Time O(n), space O(1).",
        pitfalls="- Looking only at the two **neighbouring** bars instead of the tallest bars on each side.\n- Forgetting that the empty array must return `0` (the loop condition handles it).\n- Computing the area `min * width` as in Container With Most Water: this problem sums water per bar.\n- Adding water before updating the running maximum can produce negative contributions; update the maximum first.",
        follow_up="Trapping Rain Water II does the same on a 2D grid with a min-heap. Container With Most Water uses the same two-pointer shape for a different goal.",
    ),
),
dict(
    id="js-merge-k-sorted-lists", title="Merge k Sorted Lists", difficulty="Hard", pattern="Linked List",
    leetcode="https://leetcode.com/problems/merge-k-sorted-lists/",
    neetcode="https://neetcode.io/problems/merge-k-sorted-linked-lists",
    kind="js", entry="runMergeK",
    description=r"""
You are given an array `lists` of `k` linked lists, each sorted in non-decreasing order. Merge them into a single
sorted linked list and return its head.

- `0 <= k <= 100`, each list has `0..500` nodes, values in `-10000..10000`
- `k = 0` means there are no lists at all, and the answer is the empty list

**Example 1:** `[[1, 4, 5], [1, 3, 4], [2, 6]]` → `[1, 1, 2, 3, 4, 4, 5, 6]`

**Example 2:** `[]` → `[]`
""" + CONVENTION,
    starter="function mergeKLists(lists) {\n  // your code\n}\n" + LIST_HELPERS + MK_DRIVER,
    solution=mk(r'''function mergeTwo(a, b) {
  const dummy = new ListNode();
  let tail = dummy;
  while (a && b) {
    if (a.val <= b.val) { tail.next = a; a = a.next; }
    else { tail.next = b; b = b.next; }
    tail = tail.next;
  }
  tail.next = a || b;
  return dummy.next;
}

function mergeKLists(lists) {
  if (lists.length === 0) return null;
  // merge in pairs, round after round, until one list remains
  while (lists.length > 1) {
    const merged = [];
    for (let i = 0; i < lists.length; i += 2) {
      merged.push(mergeTwo(lists[i], i + 1 < lists.length ? lists[i + 1] : null));
    }
    lists = merged;
  }
  return lists[0];
}
'''),
    tests=[[[[1, 4, 5], [1, 3, 4], [2, 6]]], [[]], [[[]]], [[[], []]], [[[1]]], [[[2], [1]]], [[[1, 2, 3], [4, 5, 6], [7, 8, 9]]],
           [[[7, 8, 9], [4, 5, 6], [1, 2, 3]]], [[[1, 1, 1], [1, 1], [1]]], [[[-5, 0], [], [-10, 10], []]],
           [[sorted_list(rng.randint(0, 500)) for _ in range(100)]], [[sorted_list(500) for _ in range(7)]],
           [[sorted_list(3) for _ in range(31)]]],
    examples=2,
    wrong_solutions=[
        mk("function mergeKLists(lists) {\n  const d = new ListNode(); let t = d;\n  for (const l of lists) for (let n = l; n; n = n.next) { t.next = new ListNode(n.val); t = t.next; }\n  return d.next;\n}\n"),
        mk("function mergeKLists(lists) {\n  if (lists.length === 0) return null;\n  let [a, b] = lists;\n  const d = new ListNode(); let t = d;\n  while (a && b) {\n    if (a.val <= b.val) { t.next = a; a = a.next; } else { t.next = b; b = b.next; }\n    t = t.next;\n  }\n  t.next = a || b;\n  return d.next;\n}\n"),
        mk("function mergeKLists(lists) {\n  const heads = lists.filter(Boolean);\n  if (heads.length === 0) return null;\n  let best = heads[0];\n  for (const h of heads) if (h.val > best.val) best = h;\n  return best;\n}\n"),
    ],
    guide=G(
        prereqs="Merge Two Sorted Lists (this track) and the `ListNode` convention from the lesson *Linked lists and trees with classes*.",
        intuition="Merging two sorted lists is already solved. Merging `k` of them is the same job repeated: pair the lists up, merge each pair, and repeat on the results. Each round halves the number of lists, so only about `log k` rounds are needed and every node is touched once per round.",
        hints=[
            "Reuse your Merge Two Sorted Lists function.",
            "Merging lists one after another into a growing result is slow, because the long result is re-walked every time. Merge in pairs instead.",
            "A min-heap holding the current head of each list also works; JavaScript has no built-in heap, so divide and conquer is shorter to write.",
        ],
        brute_force="Collect every value into an array, sort, and rebuild the list: O(N log N) for N nodes in total, and it ignores the sortedness. Merging into one accumulating list is O(N k) in the worst case.",
        approach="1. If `lists` is empty return `null`.\n2. While more than one list remains, build a new array by merging `lists[0]` with `lists[1]`, `lists[2]` with `lists[3]`, and so on (an odd last list is merged with `null`, which just keeps it).\n3. Return the single remaining list.\n\n**Dry run** three lists A, B, C: round 1 gives `[merge(A, B), C]`; round 2 gives `[merge(merge(A, B), C)]`.",
        complexity="Time O(N log k) for N nodes in total; space O(1) extra besides the array of heads (the merge relinks existing nodes).",
        pitfalls="- `lists` can be empty (`k = 0`) or contain empty lists (`null` heads); handle both.\n- Reading `lists[i + 1]` past the end when the count is odd gives `undefined`, not `null`.\n- Taking only each list's first node and ignoring the rest.\n- Comparing with `<` versus `<=` does not change correctness here, but a stable `<=` keeps equal values in list order.",
        follow_up="Using a min-heap of `(value, list index)` gives the same O(N log k) bound and also streams results one node at a time (see the heap lesson).",
    ),
),
]
