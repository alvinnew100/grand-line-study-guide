import random

_R = random.Random(777)

PROBLEMS = [
# ---------------------------------------------------------------------------------------------
dict(
    id="subsets",
    title="Subsets",
    difficulty="Medium",
    pattern="Backtracking",
    leetcode="https://leetcode.com/problems/subsets/",
    neetcode="https://neetcode.io/problems/subsets",
    entry="subsets",
    compare="unordered_nested",
    description=r"""
Given a list of **distinct** integers `nums`, return every possible subset (the *power set*),
including the empty set and `nums` itself. No subset may appear twice. The subsets, and the
numbers inside each subset, may be listed in any order.

**Constraints:** `1 <= len(nums) <= 10`, `-10 <= nums[i] <= 10`, all values distinct.

**Example 1:** `nums = [1,2,3]` → `[[],[1],[2],[1,2],[3],[1,3],[2,3],[1,2,3]]`

**Example 2:** `nums = [0]` → `[[],[0]]`
""",
    starter='''class Solution:
    def subsets(self, nums: List[int]) -> List[List[int]]:
        pass
''',
    solution='''class Solution:
    def subsets(self, nums):
        res, path = [], []

        def dfs(i):
            if i == len(nums):
                res.append(path[:])
                return
            path.append(nums[i])      # include nums[i]
            dfs(i + 1)
            path.pop()                # exclude nums[i]
            dfs(i + 1)

        dfs(0)
        return res
''',
    tests=[
        [[1, 2, 3]],
        [[0]],
        [[5, -3]],
        [[1, 2]],
        [[4, 1, 0, -1]],
        [[-10, 10, 0, 3, 7]],
        [list(range(1, 8))],
        [[9, -9, 8, -8, 7, -7, 6, -6, 5, -5]],
        [list(range(10))],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def subsets(self, nums):
        res, path = [], []
        def dfs(i):
            if i == len(nums):
                res.append(path)
                return
            path.append(nums[i]); dfs(i + 1); path.pop(); dfs(i + 1)
        dfs(0)
        return res
''',
        '''class Solution:
    def subsets(self, nums):
        res = [[]]
        for x in nums:
            res.append([x])
        res.append(list(nums))
        return res
''',
    ],
    guide=dict(
        prereqs="Recursion; the include/exclude state-space tree (lesson *The backtracking template*).",
        intuition=r"""
Each element is either **in** or **out** of a subset, so there are $2^n$ subsets. A recursive
function walks the elements left to right and branches twice at each one — the result is a full
binary tree of depth `n` whose `2^n` leaves are exactly the subsets.
""",
        hints=[
            "How many choices do you have for each individual element?",
            "Write dfs(i): decide about nums[i], recurse on i + 1. Where does a finished subset get recorded?",
            "Append nums[i] to path, recurse, pop, recurse again. At i == n, append a COPY of path to the answer.",
        ],
        brute_force="Iterate a bitmask `m` from 0 to 2ⁿ−1 and include `nums[j]` when bit `j` is set. Same O(n·2ⁿ) complexity — this is a perfectly good alternative, not a slow one.",
        approach=r"""
**Include/exclude recursion**

```
dfs(0, [])
├─ take 1 → dfs(1,[1])
│   ├─ take 2 → dfs(2,[1,2]) → [1,2,3], [1,2]
│   └─ skip 2 → dfs(2,[1])   → [1,3],   [1]
└─ skip 1 → dfs(1,[])
    ├─ take 2 → [2,3], [2]
    └─ skip 2 → [3], []
```

Alternative **"for-loop" form** (records every node, not just leaves):
`dfs(start)`: record `path[:]`; for `j` in `start..n-1`: push `nums[j]`, `dfs(j+1)`, pop. It
generates subsets in "lexicographic by index" order and generalises directly to *Subsets II* and *Combination Sum*.

**Iterative form:** start with `[[]]`; for each `x`, extend with `[s + [x] for s in res]`.
""",
        complexity="O(n · 2ⁿ) time — 2ⁿ subsets, each copied in O(n). O(n) recursion depth plus the output.",
        pitfalls=r"""
- Appending `path` instead of `path[:]` — every entry aliases the same list, which ends up empty.
- Forgetting the empty subset.
- Mutating `path` without undoing the change (missing `pop`).
""",
        follow_up="*Subsets II* adds duplicates; *Combination Sum* adds a target; *Letter Case Permutation* is the same include/flip tree.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="combination-sum",
    title="Combination Sum",
    difficulty="Medium",
    pattern="Backtracking",
    leetcode="https://leetcode.com/problems/combination-sum/",
    neetcode="https://neetcode.io/problems/combination-target-sum",
    entry="combinationSum",
    compare="unordered_nested",
    description=r"""
You are given a list of **distinct** positive integers `candidates` and a positive `target`.
Return every distinct combination of candidates that adds up to `target`. Each candidate may be
used **any number of times**. Two combinations are the same if they use each number the same number
of times (so `[2,2,3]` and `[3,2,2]` count once). Output order does not matter.

**Constraints:** `1 <= len(candidates) <= 30`, `2 <= candidates[i] <= 40`, values distinct, `1 <= target <= 40`.

**Example 1:** `candidates = [2,3,6,7], target = 7` → `[[2,2,3],[7]]`

**Example 2:** `candidates = [2,3,5], target = 8` → `[[2,2,2,2],[2,3,3],[3,5]]`

**Example 3:** `candidates = [2], target = 1` → `[]`
""",
    starter='''class Solution:
    def combinationSum(self, candidates: List[int], target: int) -> List[List[int]]:
        pass
''',
    solution='''class Solution:
    def combinationSum(self, candidates, target):
        cand = sorted(candidates)
        res, path = [], []

        def dfs(start, remain):
            if remain == 0:
                res.append(path[:])
                return
            for j in range(start, len(cand)):
                if cand[j] > remain:
                    break                  # sorted: nothing later fits either
                path.append(cand[j])
                dfs(j, remain - cand[j])   # j, not j+1: reuse allowed
                path.pop()

        dfs(0, target)
        return res
''',
    tests=[
        [[2, 3, 6, 7], 7],
        [[2, 3, 5], 8],
        [[2], 1],
        [[7, 3, 2], 18],
        [[8, 7, 4, 3], 11],
        [[2], 40],
        [[40], 40],
        [[5, 10], 3],
        [[3, 4, 5], 20],
        [list(range(2, 12)), 25],
        [[2, 3, 5, 7, 11, 13], 30],
    ],
    examples=3,
    wrong_solutions=[
        '''class Solution:
    def combinationSum(self, candidates, target):
        res = []
        def dfs(path, remain):
            if remain == 0:
                res.append(path[:]); return
            if remain < 0: return
            for c in candidates:
                path.append(c); dfs(path, remain - c); path.pop()
        dfs([], target)
        return res
''',
        '''class Solution:
    def combinationSum(self, candidates, target):
        res = []
        def dfs(start, path, remain):
            if remain == 0:
                res.append(path[:]); return
            if remain < 0: return
            for j in range(start, len(candidates)):
                path.append(candidates[j]); dfs(j + 1, path, remain - candidates[j]); path.pop()
        dfs(0, [], target)
        return res
''',
    ],
    guide=dict(
        prereqs="The backtracking template with a `start` index (lesson *The backtracking template*); pruning on sorted input.",
        intuition=r"""
To avoid counting `[2,2,3]` and `[2,3,2]` separately, build each combination in **non-decreasing
index order**: once you move past candidate `j`, never pick it again. Allowing reuse just means the
recursive call starts at `j` instead of `j + 1`. Sorting lets you stop the loop as soon as a candidate exceeds what's left.
""",
        hints=[
            "Why does trying every candidate at every level produce duplicate combinations?",
            "Pass a start index so each level only picks candidates at or after the previous pick.",
            "for j in range(start, n): if cand[j] > remain: break; push, dfs(j, remain − cand[j]), pop. Record when remain == 0.",
        ],
        brute_force="Recurse over all sequences (any candidate at any level) and deduplicate by sorting each result into a set of tuples. Exponentially more work and memory than necessary.",
        approach=r"""
`dfs(start, remain)`:
- `remain == 0` → record a copy of `path`.
- otherwise for `j` from `start`: if `cand[j] > remain` break (sorted); else choose, `dfs(j, remain - cand[j])`, un-choose.

**Dry run** `[2,3,6,7], target 7` (sorted):

```
dfs(0,7)
├─2 → dfs(0,5)
│   ├─2 → dfs(0,3)
│   │   ├─2 → dfs(0,1): 2>1 break
│   │   └─3 → dfs(1,0) ✔ [2,2,3]
│   └─3 → dfs(1,2): 3>2 break
├─3 → dfs(1,4) ─3→ dfs(1,1): break
├─6 → dfs(2,1): break
└─7 → dfs(3,0) ✔ [7]
```
""",
        complexity="Exponential: with smallest candidate m the depth is ≤ T/m and branching ≤ n, giving O(n^(T/m)) as a loose bound; output-sensitive in practice. Space O(T/m) recursion depth.",
        pitfalls=r"""
- Looping over all candidates at each level (duplicates in different orders — wrong solution #1).
- Recursing with `j + 1` (forbids reuse — wrong solution #2).
- Forgetting to sort before using `break` for pruning (then you must use `continue`).
""",
        follow_up="*Combination Sum II* (each used once, duplicates in input), *Combination Sum III* (k numbers from 1–9), *Combination Sum IV* (order matters → DP counting).",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="combination-sum-ii",
    title="Combination Sum II",
    difficulty="Medium",
    pattern="Backtracking",
    leetcode="https://leetcode.com/problems/combination-sum-ii/",
    neetcode="https://neetcode.io/problems/combination-target-sum-ii",
    entry="combinationSum2",
    compare="unordered_nested",
    description=r"""
Given a list `candidates` that **may contain repeated numbers** and a `target`, return every unique
combination whose sum equals `target`, where each **position** of `candidates` can be used at most once.
The answer must not contain the same combination twice (as a multiset). Any order is accepted.

**Constraints:** `1 <= len(candidates) <= 100`, `1 <= candidates[i] <= 50`, `1 <= target <= 30`.

**Example 1:** `candidates = [10,1,2,7,6,1,5], target = 8` → `[[1,1,6],[1,2,5],[1,7],[2,6]]`

**Example 2:** `candidates = [2,5,2,1,2], target = 5` → `[[1,2,2],[5]]`
""",
    starter='''class Solution:
    def combinationSum2(self, candidates: List[int], target: int) -> List[List[int]]:
        pass
''',
    solution='''class Solution:
    def combinationSum2(self, candidates, target):
        cand = sorted(candidates)
        res, path = [], []

        def dfs(start, remain):
            if remain == 0:
                res.append(path[:])
                return
            for j in range(start, len(cand)):
                if j > start and cand[j] == cand[j - 1]:
                    continue               # same value already tried at this depth
                if cand[j] > remain:
                    break
                path.append(cand[j])
                dfs(j + 1, remain - cand[j])
                path.pop()

        dfs(0, target)
        return res
''',
    tests=[
        [[10, 1, 2, 7, 6, 1, 5], 8],
        [[2, 5, 2, 1, 2], 5],
        [[1], 1],
        [[2], 1],
        [[1, 1, 1, 1, 1], 3],
        [[3, 1, 3, 5, 1, 1], 8],
        [[4, 4, 2, 1, 4, 2, 2, 1, 3], 6],
        [[50, 50, 50], 30],
        [[1] * 15, 8],
        [[_R.randint(1, 10) for _ in range(20)], 15],
        [list(range(1, 31)), 30],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def combinationSum2(self, candidates, target):
        cand = sorted(candidates)
        res = []
        def dfs(start, path, remain):
            if remain == 0:
                res.append(path[:]); return
            for j in range(start, len(cand)):
                if cand[j] > remain: break
                path.append(cand[j]); dfs(j + 1, path, remain - cand[j]); path.pop()
        dfs(0, [], target)
        return res
''',
        '''class Solution:
    def combinationSum2(self, candidates, target):
        cand = sorted(set(candidates))
        res = []
        def dfs(start, path, remain):
            if remain == 0:
                res.append(path[:]); return
            for j in range(start, len(cand)):
                if cand[j] > remain: break
                path.append(cand[j]); dfs(j + 1, path, remain - cand[j]); path.pop()
        dfs(0, [], target)
        return res
''',
    ],
    guide=dict(
        prereqs="*Combination Sum*; the 'skip equal siblings' duplicate rule (lesson *Duplicates, pruning and constraint search*).",
        intuition=r"""
Sort first so equal values are adjacent. Duplicated *results* arise only when, at the **same depth**
of the tree, you start a branch with a value you have already started a branch with. So inside the
loop skip `cand[j]` if `j > start` and it equals `cand[j-1]`. Going *deeper* with an equal value is
fine — that's how `[1,1,6]` is produced.
""",
        hints=[
            "What changes from Combination Sum: each index once (so recurse with j + 1), and the input has repeats.",
            "Sort. Where exactly do duplicate combinations come from — choosing the same value as a sibling, or as a child?",
            "In the loop: if j > start and cand[j] == cand[j−1]: continue. Also break when cand[j] > remain.",
        ],
        brute_force="Generate all 2ⁿ subsets, keep those summing to target, deduplicate via a set of sorted tuples. Hopeless for n = 100 (`[1]*100` alone has 2¹⁰⁰ subsets).",
        approach=r"""
Sorted `[1,1,2,5,6,7,10]`, target 8:

```
dfs(0,8)
├─1(j0) → dfs(1,7)
│   ├─1(j1) → dfs(2,6) ─ 2→dfs(3,4) ✗ ... 6 → ✔ [1,1,6]
│   ├─2 → dfs(3,5) ─ 5 → ✔ [1,2,5]
│   ├─5 → ✗   6 → ✗
│   └─7 → ✔ [1,7]
├─1(j1)  SKIPPED: same value as sibling j0
├─2 → dfs(3,6) ─ 6 → ✔ [2,6]
...
```

Rule of thumb: **skip duplicates across siblings, allow them along a path.**
""",
        complexity="O(2ⁿ · n) worst case, but the skip rule plus the sorted `break` make it output-sensitive. Space O(n) depth.",
        pitfalls=r"""
- Writing `if j > 0` instead of `if j > start` — that forbids `[1,1,6]`.
- Deduplicating the input with `set` (loses legitimate repeats — wrong solution #2).
- Forgetting to sort; the adjacency trick needs equal values to be neighbours.
""",
        follow_up="The same sibling-skip rule solves *Subsets II* and *Permutations II*.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="permutations",
    title="Permutations",
    difficulty="Medium",
    pattern="Backtracking",
    leetcode="https://leetcode.com/problems/permutations/",
    neetcode="https://neetcode.io/problems/permutations",
    entry="permute",
    compare="unordered",
    description=r"""
Given a list of **distinct** integers, return every ordering (permutation) of them. The list of
permutations may be in any order, but each permutation is of course an ordered list.

**Constraints:** `1 <= len(nums) <= 6` (tests go up to 7), `-10 <= nums[i] <= 10`, all distinct.

**Example 1:** `nums = [1,2,3]` → `[[1,2,3],[1,3,2],[2,1,3],[2,3,1],[3,1,2],[3,2,1]]`

**Example 2:** `nums = [0,1]` → `[[0,1],[1,0]]`
""",
    starter='''class Solution:
    def permute(self, nums: List[int]) -> List[List[int]]:
        pass
''',
    solution='''class Solution:
    def permute(self, nums):
        res, path = [], []
        used = [False] * len(nums)

        def dfs():
            if len(path) == len(nums):
                res.append(path[:])
                return
            for i, x in enumerate(nums):
                if not used[i]:
                    used[i] = True
                    path.append(x)
                    dfs()
                    path.pop()
                    used[i] = False

        dfs()
        return res
''',
    tests=[
        [[1, 2, 3]],
        [[0, 1]],
        [[1]],
        [[-1, 5]],
        [[3, 1, 2, 0]],
        [[-10, 10, 0, 5, -5]],
        [[6, 5, 4, 3, 2, 1]],
        [[1, 2, 3, 4, 5, 6, 7]],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def permute(self, nums):
        res = []
        def dfs(path):
            if len(path) == len(nums):
                res.append(path[:]); return
            for x in nums:
                if path and x == path[-1]: continue
                path.append(x); dfs(path); path.pop()
        dfs([])
        return res
''',
        '''class Solution:
    def permute(self, nums):
        return [nums[i:] + nums[:i] for i in range(len(nums))]
''',
    ],
    guide=dict(
        prereqs="Backtracking template; a `used` array (lesson *The backtracking template*).",
        intuition=r"""
A permutation is built position by position. At each position you may place **any element not yet
placed**. Track which ones are used with a boolean array, and undo the mark when you backtrack.
The tree has `n` choices at depth 0, `n-1` at depth 1, ... → `n!` leaves.
""",
        hints=[
            "Unlike subsets, order matters — at every step all unused elements are candidates, not just later ones.",
            "Keep a used[] array (or a set). Recurse until the path has n elements.",
            "for i in range(n): if not used[i]: mark, append, recurse, pop, unmark.",
        ],
        brute_force="`itertools.permutations(nums)` does it in one line — know it exists, but interviewers want the recursion. Generating all nⁿ sequences and filtering ones with repeats is wasteful.",
        approach=r"""
```
[]
├─1 → [1] ─2→[1,2]─3→[1,2,3]
│        └3→[1,3]─2→[1,3,2]
├─2 → [2] ─1→[2,1,3]  ─3→[2,3,1]
└─3 → [3] ─1→[3,1,2]  ─2→[3,2,1]
```

Swap-based alternative: `dfs(i)`: if `i == n` record `nums[:]`; for `j` in `i..n-1`: swap `nums[i], nums[j]`, `dfs(i+1)`, swap back. It uses no extra `used` array.
""",
        complexity="O(n · n!) time (n! permutations, each copied in O(n)); O(n) extra space besides output.",
        pitfalls=r"""
- Not tracking used elements — checking only that you don't repeat the *previous* element still allows `[1,2,1]` (wrong solution #1).
- Forgetting to un-mark `used[i]` after the recursive call.
- Appending `path` instead of a copy.
""",
        follow_up="*Permutations II* (duplicates: sort, and skip `nums[i]` if it equals `nums[i-1]` and `nums[i-1]` is not currently used). *Next Permutation* generates them one at a time in lexicographic order.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="subsets-ii",
    title="Subsets II",
    difficulty="Medium",
    pattern="Backtracking",
    leetcode="https://leetcode.com/problems/subsets-ii/",
    neetcode="https://neetcode.io/problems/subsets-ii",
    entry="subsetsWithDup",
    compare="unordered_nested",
    description=r"""
Given a list of integers `nums` that **may contain duplicates**, return all distinct subsets.
Two subsets are the same if they contain the same values with the same multiplicities
(`[1,2]` from different positions counts once). Any order is accepted.

**Constraints:** `1 <= len(nums) <= 10`, `-10 <= nums[i] <= 10`.

**Example 1:** `nums = [1,2,2]` → `[[],[1],[1,2],[1,2,2],[2],[2,2]]`

**Example 2:** `nums = [0]` → `[[],[0]]`
""",
    starter='''class Solution:
    def subsetsWithDup(self, nums: List[int]) -> List[List[int]]:
        pass
''',
    solution='''class Solution:
    def subsetsWithDup(self, nums):
        nums = sorted(nums)
        res, path = [], []

        def dfs(start):
            res.append(path[:])
            for j in range(start, len(nums)):
                if j > start and nums[j] == nums[j - 1]:
                    continue
                path.append(nums[j])
                dfs(j + 1)
                path.pop()

        dfs(0)
        return res
''',
    tests=[
        [[1, 2, 2]],
        [[0]],
        [[2, 2]],
        [[4, 4, 4, 1, 4]],
        [[1, 2, 3]],
        [[3, 1, 3, 1]],
        [[-1, 1, 2, 2, -1, 0]],
        [[5] * 10],
        [[1, 1, 2, 2, 3, 3, 4, 4, 5, 5]],
        [list(range(10))],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def subsetsWithDup(self, nums):
        res, path = [], []
        def dfs(i):
            if i == len(nums):
                res.append(path[:]); return
            path.append(nums[i]); dfs(i + 1); path.pop(); dfs(i + 1)
        dfs(0)
        return res
''',
        '''class Solution:
    def subsetsWithDup(self, nums):
        nums = sorted(set(nums))
        res = [[]]
        for x in nums:
            res += [s + [x] for s in res]
        return res
''',
    ],
    guide=dict(
        prereqs="*Subsets* (for-loop form); the sibling-skip rule from *Combination Sum II*.",
        intuition=r"""
Sort, then use the "record every node" version of the subsets recursion. Two siblings that start
with the same value would generate identical sub-trees, so skip a value equal to its left neighbour
**at the same level** (`j > start`).

Equivalent view: for a value that appears `c` times you choose how many copies to take (0..c) — a
different count gives a different subset, a different *choice of positions* does not.
""",
        hints=[
            "Run plain Subsets on [1,2,2]. Which outputs repeat, and in which branches do they appear?",
            "Sort so duplicates are adjacent; the repetition comes from starting two sibling branches with the same value.",
            "Record path at every call; loop j from start; continue if j > start and nums[j] == nums[j−1].",
        ],
        brute_force="Generate all 2ⁿ subsets, sort each, insert tuples into a set. O(n · 2ⁿ log n) — acceptable for n ≤ 10, but the skip rule is the expected answer.",
        approach=r"""
Sorted `[1,2,2]`:

```
dfs(0) records []
├─1 → dfs(1) records [1]
│     ├─2(j1) → [1,2] → ─2(j2)→ [1,2,2]
│     └─2(j2) SKIP (same as sibling j1)
├─2(j1) → [2] → ─2(j2)→ [2,2]
└─2(j2) SKIP
```
Result: `[], [1], [1,2], [1,2,2], [2], [2,2]`.
""",
        complexity="O(n · 2ⁿ) worst case (all distinct). Space O(n) recursion.",
        pitfalls=r"""
- Skipping with `j > 0` instead of `j > start` (loses `[2,2]`).
- Forgetting to sort.
- Collapsing duplicates with `set(nums)` (loses `[2,2]` — wrong solution #2).
""",
        follow_up="Count-based generation: build `Counter(nums)`, and for each distinct value loop over how many copies to take.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="word-search",
    title="Word Search",
    difficulty="Medium",
    pattern="Backtracking",
    leetcode="https://leetcode.com/problems/word-search/",
    neetcode="https://neetcode.io/problems/search-for-word",
    entry="exist",
    description=r"""
Given an `m × n` grid of letters `board` and a string `word`, decide whether `word` can be spelled
by a path of cells where consecutive cells are **horizontally or vertically adjacent**, and no cell
is used more than once in the path. Return `True` or `False`.

**Constraints:** `1 <= m, n <= 6`, `1 <= len(word) <= 15`, letters are upper/lower-case English.

**Example 1:**
```
board = [["A","B","C","E"],
         ["S","F","C","S"],
         ["A","D","E","E"]]
word = "ABCCED"  -> True
word = "SEE"     -> True
word = "ABCB"    -> False   (would need to reuse the B)
```
""",
    starter='''class Solution:
    def exist(self, board: List[List[str]], word: str) -> bool:
        pass
''',
    solution='''from collections import Counter

class Solution:
    def exist(self, board, word):
        R, C = len(board), len(board[0])
        have = Counter(ch for row in board for ch in row)
        need = Counter(word)
        if any(have[ch] < k for ch, k in need.items()):
            return False
        if have[word[0]] > have[word[-1]]:
            word = word[::-1]          # start from the rarer end

        def dfs(r, c, i):
            if i == len(word):
                return True
            if r < 0 or c < 0 or r == R or c == C or board[r][c] != word[i]:
                return False
            tmp, board[r][c] = board[r][c], "#"
            found = (dfs(r + 1, c, i + 1) or dfs(r - 1, c, i + 1)
                     or dfs(r, c + 1, i + 1) or dfs(r, c - 1, i + 1))
            board[r][c] = tmp
            return found

        return any(dfs(r, c, 0) for r in range(R) for c in range(C))
''',
    tests=[
        [[["A", "B", "C", "E"], ["S", "F", "C", "S"], ["A", "D", "E", "E"]], "ABCCED"],
        [[["A", "B", "C", "E"], ["S", "F", "C", "S"], ["A", "D", "E", "E"]], "SEE"],
        [[["A", "B", "C", "E"], ["S", "F", "C", "S"], ["A", "D", "E", "E"]], "ABCB"],
        [[["a"]], "a"],
        [[["a"]], "b"],
        [[["a", "b"]], "ba"],
        [[["a", "b"], ["c", "d"]], "abdc"],
        [[["a", "b"], ["c", "d"]], "abcd"],
        [[["a", "a"]], "aaa"],
        [[["C", "A", "A"], ["A", "A", "A"], ["B", "C", "D"]], "AAB"],
        [[["A"] * 3 for _ in range(3)], "AAAAAAB"],
        [[["A", "A", "A", "B"], ["A", "A", "A", "A"]], "BAAAAAAA"],
        [[["A", "A", "A", "B"], ["A", "A", "A", "A"]], "BAAAAAAAA"],
        [[["A", "B", "C", "E"], ["S", "F", "E", "S"], ["A", "D", "E", "E"]], "ABCESEEEFS"],
        [[list("abcdef"), list("ghijkl"), list("mnopqr"), list("stuvwx"), list("yzABCD"), list("EFGHIJ")], "abcdeflkjihg"],
    ],
    examples=3,
    wrong_solutions=[
        '''class Solution:
    def exist(self, board, word):
        R, C = len(board), len(board[0])
        def dfs(r, c, i):
            if i == len(word): return True
            if r < 0 or c < 0 or r == R or c == C or board[r][c] != word[i]: return False
            return dfs(r+1,c,i+1) or dfs(r-1,c,i+1) or dfs(r,c+1,i+1) or dfs(r,c-1,i+1)
        return any(dfs(r, c, 0) for r in range(R) for c in range(C))
''',
        '''class Solution:
    def exist(self, board, word):
        from collections import Counter
        have = Counter(ch for row in board for ch in row)
        return all(have[ch] >= k for ch, k in Counter(word).items())
''',
    ],
    guide=dict(
        prereqs="Grid DFS (lesson *DFS and BFS on grids*); backtracking with an undo step.",
        intuition=r"""
Try every cell as a starting point and walk the word letter by letter with DFS. The twist compared
to flood fill is that "visited" is **per path**, not global: a cell used by a failed path may be
needed by another path. So mark the cell on the way down and **unmark it on the way back** — that's backtracking.
""",
        hints=[
            "Write dfs(r, c, i): can word[i:] be spelled starting at cell (r, c)?",
            "How do you stop a path from reusing a cell, while still letting a different path use it later?",
            "Temporarily overwrite board[r][c] with '#', recurse in four directions, then restore it. Prune when the letter doesn't match.",
        ],
        brute_force="Enumerate all simple paths of length `len(word)` from every cell and compare strings — the same exponential tree, but without pruning on the first mismatch.",
        approach=r"""
1. Optional pruning: if the board lacks enough copies of some letter, return `False`. If the first letter of `word` is more common than the last, search for the reversed word (fewer starting points survive).
2. `dfs(r, c, i)`: out of bounds or `board[r][c] != word[i]` → `False`; `i == len(word)` → `True`.
3. Mark, recurse into four neighbours with `i+1`, restore, return.

**Dry run** `"ABCB"`: start at (0,0) A → (0,1) B → (0,2) C → neighbours of C: (0,1) is `#` (in use), (1,2) is C, (0,3) is E → no B available → backtrack → `False` from every start.
""",
        complexity="O(m · n · 3^L) time: from each start, each step has at most 3 new directions (you can't go back). O(L) recursion depth.",
        pitfalls=r"""
- Global `visited` that is never cleared (fails when two paths overlap).
- Not restoring the cell (wrong answers on later starting cells).
- Allowing reuse (wrong solution #1 accepts `"aaa"` on a 1×2 board).
- Checking `i == len(word)` *after* the bounds check means a match ending at the grid edge is lost — order the checks as shown.
""",
        follow_up="*Word Search II* finds many words at once — build a Trie of the words and walk it during the DFS.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="palindrome-partitioning",
    title="Palindrome Partitioning",
    difficulty="Medium",
    pattern="Backtracking",
    leetcode="https://leetcode.com/problems/palindrome-partitioning/",
    neetcode="https://neetcode.io/problems/palindrome-partitioning",
    entry="partition",
    compare="unordered",
    description=r"""
Cut a string `s` into consecutive pieces so that **every piece is a palindrome** (reads the same
both ways). Return every possible way to do it; each way is a list of pieces in left-to-right order.
The list of ways may be in any order.

**Constraints:** `1 <= len(s) <= 16`, lowercase letters only.

**Example 1:** `s = "aab"` → `[["a","a","b"],["aa","b"]]`

**Example 2:** `s = "a"` → `[["a"]]`
""",
    starter='''class Solution:
    def partition(self, s: str) -> List[List[str]]:
        pass
''',
    solution='''class Solution:
    def partition(self, s):
        n = len(s)
        # pal[i][j] is True when s[i..j] is a palindrome
        pal = [[False] * n for _ in range(n)]
        for i in range(n - 1, -1, -1):
            for j in range(i, n):
                pal[i][j] = s[i] == s[j] and (j - i < 2 or pal[i + 1][j - 1])
        res, path = [], []

        def dfs(i):
            if i == n:
                res.append(path[:])
                return
            for j in range(i, n):
                if pal[i][j]:
                    path.append(s[i:j + 1])
                    dfs(j + 1)
                    path.pop()

        dfs(0)
        return res
''',
    tests=[
        ["aab"],
        ["a"],
        ["ab"],
        ["aba"],
        ["racecar"],
        ["abcba"],
        ["aaaa"],
        ["abbab"],
        ["efe"],
        ["abcdefghijklmnop"],
        ["aaaaaaaaaa"],
        ["ababababab"],
        ["cdd"],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def partition(self, s):
        res = []
        def dfs(i, path):
            if i == len(s):
                res.append(path[:]); return
            for j in range(i + 1, len(s)):
                t = s[i:j]
                if t == t[::-1]:
                    path.append(t); dfs(j, path); path.pop()
        dfs(0, [])
        return res
''',
        '''class Solution:
    def partition(self, s):
        return [list(s)]
''',
    ],
    guide=dict(
        prereqs="Backtracking over cut positions; optional DP table for palindromic substrings.",
        intuition=r"""
Decide the **first piece**: it is `s[0..j]` for some `j` where that prefix is a palindrome. Then
recursively partition the rest `s[j+1..]`. Each root-to-leaf path in this tree is one valid partition.
Precomputing which substrings are palindromes turns each check into O(1).
""",
        hints=[
            "Think about the first piece of a partition. What are your options for it?",
            "dfs(i) partitions the suffix starting at i: try every end j ≥ i where s[i..j] is a palindrome.",
            "Precompute pal[i][j] = s[i]==s[j] and (j−i<2 or pal[i+1][j−1]); then backtrack with path.append(s[i:j+1]).",
        ],
        brute_force="There are 2ⁿ⁻¹ ways to cut a string; enumerate them all with a bitmask and keep those where every piece is a palindrome: O(n · 2ⁿ).",
        approach=r"""
`dfs(i)`: if `i == n` record the path. Else for each `j` in `i..n-1` with `pal[i][j]`: push `s[i:j+1]`, `dfs(j+1)`, pop.

**Dry run** `"aab"`:

```
dfs(0)
├─"a"  → dfs(1)
│        ├─"a" → dfs(2) ─"b"→ ✔ [a,a,b]
│        └─"ab" ✗ not a palindrome
├─"aa" → dfs(2) ─"b"→ ✔ [aa,b]
└─"aab" ✗
```
""",
        complexity="O(n · 2ⁿ) time worst case (all-equal string: every cut works), O(n²) for the palindrome table. Space O(n²) + recursion O(n).",
        pitfalls=r"""
- Off-by-one in the end index: a loop `range(i + 1, len(s))` over exclusive ends never takes the final character as a piece (wrong solution #1). Use `range(i + 1, len(s) + 1)` for exclusive ends.
- Forgetting the single-character pieces — they are always palindromes.
- Rechecking palindromes with slicing everywhere is fine for n ≤ 16 but the DP table is cleaner.
""",
        follow_up="*Palindrome Partitioning II* asks only for the minimum number of cuts — a 1-D DP over the same table, O(n²).",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="letter-combinations-of-a-phone-number",
    title="Letter Combinations of a Phone Number",
    difficulty="Medium",
    pattern="Backtracking",
    leetcode="https://leetcode.com/problems/letter-combinations-of-a-phone-number/",
    neetcode="https://neetcode.io/problems/combinations-of-a-phone-number",
    entry="letterCombinations",
    compare="unordered",
    description=r"""
On an old phone keypad each digit 2–9 stands for several letters:

| 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
|---|---|---|---|---|---|---|---|
| abc | def | ghi | jkl | mno | pqrs | tuv | wxyz |

Given a string of digits from `2`–`9`, return every string you could type by choosing one letter
for each digit, in order. Return the strings in any order. An empty input produces an empty list.

**Constraints:** `0 <= len(digits) <= 4`.

**Example 1:** `digits = "23"` → `["ad","ae","af","bd","be","bf","cd","ce","cf"]`

**Example 2:** `digits = ""` → `[]`

**Example 3:** `digits = "2"` → `["a","b","c"]`
""",
    starter='''class Solution:
    def letterCombinations(self, digits: str) -> List[str]:
        pass
''',
    solution='''class Solution:
    def letterCombinations(self, digits):
        if not digits:
            return []
        keys = {"2": "abc", "3": "def", "4": "ghi", "5": "jkl",
                "6": "mno", "7": "pqrs", "8": "tuv", "9": "wxyz"}
        res, path = [], []

        def dfs(i):
            if i == len(digits):
                res.append("".join(path))
                return
            for ch in keys[digits[i]]:
                path.append(ch)
                dfs(i + 1)
                path.pop()

        dfs(0)
        return res
''',
    tests=[
        ["23"], [""], ["2"], ["7"], ["9"], ["79"], ["22"], ["234"], ["777"], ["2345"], ["7979"], ["9999"], ["8"],
    ],
    examples=3,
    wrong_solutions=[
        '''class Solution:
    def letterCombinations(self, digits):
        res = [""]
        keys = {"2": "abc", "3": "def", "4": "ghi", "5": "jkl", "6": "mno", "7": "pqr", "8": "tuv", "9": "wxy"}
        for d in digits:
            res = [p + c for p in res for c in keys[d]]
        return res
''',
        '''class Solution:
    def letterCombinations(self, digits):
        keys = {"2": "abc", "3": "def", "4": "ghi", "5": "jkl", "6": "mno", "7": "pqrs", "8": "tuv", "9": "wxyz"}
        res = [""]
        for d in digits:
            res = [p + c for p in res for c in keys[d]]
        return res
''',
    ],
    guide=dict(
        prereqs="Backtracking template (lesson *The backtracking template*); Cartesian products.",
        intuition=r"""
This is a **Cartesian product**: one choice per digit, independent of the other choices. The
state-space tree has depth `len(digits)` and the branching factor at each level is the number of
letters on that key (3 or 4).
""",
        hints=[
            "How many letters does each digit offer, and does a choice for one digit restrict any other?",
            "Write dfs(i) that picks a letter for digits[i] and recurses on i + 1.",
            "Base case i == len(digits): join the path. Don't forget digits == '' must return [] (not [''])."
        ],
        brute_force="Nested loops work only for a fixed length. The iterative product `res = [p + c for p in res for c in keys[d]]` is equally optimal — just remember the empty case.",
        approach=r"""
```
"23"
├─a ─ d e f → ad ae af
├─b ─ d e f → bd be bf
└─c ─ d e f → cd ce cf
```
`dfs(i)`: if `i == len(digits)` record `''.join(path)`; else for each letter of `keys[digits[i]]` push, recurse, pop.
""",
        complexity="O(4ⁿ · n) time (up to 4 letters per digit, building each string costs n); O(n) recursion depth.",
        pitfalls=r"""
- Returning `[""]` for empty input (wrong solution #2).
- Typos in the keypad map — 7 and 9 have **four** letters.
- Concatenating strings in the recursion (`path + ch`) is fine; just be consistent.
""",
        follow_up="`itertools.product(*(keys[d] for d in digits))` is the library one-liner. Related: *Generate Parentheses* (choices constrained by counts).",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="n-queens",
    title="N-Queens",
    difficulty="Hard",
    pattern="Backtracking",
    leetcode="https://leetcode.com/problems/n-queens/",
    neetcode="https://neetcode.io/problems/n-queens",
    entry="solveNQueens",
    compare="unordered",
    description=r"""
Place `n` chess queens on an `n × n` board so that no two attack each other — no two share a row,
a column, or a diagonal. Return **all** distinct placements. Draw each placement as a list of `n`
strings, one per row, using `'Q'` for a queen and `'.'` for an empty square. The solutions may be
listed in any order.

**Constraints:** `1 <= n <= 9`.

**Example 1:** `n = 4` →
```
[[".Q..",     ["..Q.",
  "...Q",      "Q...",
  "Q...",      "...Q",
  "..Q."],     ".Q.."]]
```

**Example 2:** `n = 1` → `[["Q"]]`
""",
    starter='''class Solution:
    def solveNQueens(self, n: int) -> List[List[str]]:
        pass
''',
    solution='''class Solution:
    def solveNQueens(self, n):
        cols, diag, anti = set(), set(), set()
        place = [0] * n            # place[r] = column of the queen in row r
        res = []

        def dfs(r):
            if r == n:
                res.append(["." * c + "Q" + "." * (n - c - 1) for c in place])
                return
            for c in range(n):
                if c in cols or (r - c) in diag or (r + c) in anti:
                    continue
                cols.add(c); diag.add(r - c); anti.add(r + c)
                place[r] = c
                dfs(r + 1)
                cols.remove(c); diag.remove(r - c); anti.remove(r + c)

        dfs(0)
        return res
''',
    tests=[[4], [1], [2], [3], [5], [6], [7], [8], [9]],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def solveNQueens(self, n):
        cols = set(); diag = set(); place = [0] * n; res = []
        def dfs(r):
            if r == n:
                res.append(["." * c + "Q" + "." * (n - c - 1) for c in place]); return
            for c in range(n):
                if c in cols or (r - c) in diag: continue
                cols.add(c); diag.add(r - c); place[r] = c; dfs(r + 1); cols.remove(c); diag.remove(r - c)
        dfs(0)
        return res
''',
        '''class Solution:
    def solveNQueens(self, n):
        cols, diag, anti = set(), set(), set()
        place = [0] * n; res = []
        def dfs(r):
            if r == n:
                res.append(["." * c + "Q" + "." * (n - c - 1) for c in place]); return
            for c in range(n):
                if c in cols or (r + c) in diag or (r + c) in anti: continue
                cols.add(c); diag.add(r + c); anti.add(r + c); place[r] = c
                dfs(r + 1)
                cols.discard(c); diag.discard(r + c); anti.discard(r + c)
        dfs(0)
        return res
''',
    ],
    guide=dict(
        prereqs="Backtracking with constraint sets (lesson *Duplicates, pruning and constraint search*).",
        intuition=r"""
Exactly one queen goes in each row, so recurse **row by row** and choose a column. A column is safe if
no earlier queen uses that column, that "\" diagonal, or that "/" diagonal. Cells on the same "\"
diagonal share `r - c`; cells on the same "/" diagonal share `r + c`. Three sets make every safety check O(1).
""",
        hints=[
            "Since no two queens share a row, what does each level of your recursion decide?",
            "How can you identify a diagonal with a single number? Look at r − c and r + c along a diagonal.",
            "Keep sets cols, r−c, r+c. For each column in the current row: skip if any set contains it; otherwise add, recurse, remove.",
        ],
        brute_force="Choose n of the n² cells (C(n², n) placements) and test each — astronomically many. Placing one per row and testing all nⁿ assignments at the end is better but still far slower than pruning as you go.",
        approach=r"""
`dfs(r)`: if `r == n`, render `place` into strings. Otherwise for each `c`: if safe, add to the three sets, set `place[r] = c`, `dfs(r+1)`, remove.

**Dry run** `n = 4` (row: tried columns):
- r0 c0 → r1: c0 col ✗, c1 diag ✗, c2 ok → r2: all blocked → back; r1 c3 → r2 c1 → r3 all blocked → back ... r0 c0 fails entirely.
- r0 c1 → r1 c3 → r2 c0 → r3 c2 ✔ `.Q.. / ...Q / Q... / ..Q.`
- r0 c2 → r1 c0 → r2 c3 → r3 c1 ✔
- r0 c3 → fails.

Solution counts: n = 1..9 → 1, 0, 0, 2, 10, 4, 40, 92, 352.
""",
        complexity="O(n!) roughly — row r has at most n − r safe columns; plus O(n²) to render each solution. Space O(n) for the sets and recursion.",
        pitfalls=r"""
- Checking columns and only one diagonal direction (wrong solution #1), or using the same key for both diagonals (wrong solution #2).
- Building board strings eagerly at each step — render only at the leaf.
- Remember `n = 2` and `n = 3` have no solutions: return `[]`.
""",
        follow_up="*N-Queens II* asks only for the count — the same search, or a bitmask version where `cols`, `diag`, `anti` are integers and the free columns are `~(cols | diag | anti) & ((1 << n) - 1)`.",
    ),
),
]
