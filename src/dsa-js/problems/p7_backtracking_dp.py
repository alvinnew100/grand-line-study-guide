"""DSA in JavaScript: Backtracking and Dynamic Programming problems."""
import random


def G(prereqs, intuition, hints, brute_force, approach, complexity, pitfalls, follow_up=""):
    return dict(prereqs=prereqs, intuition=intuition, hints=hints, brute_force=brute_force,
                approach=approach, complexity=complexity, pitfalls=pitfalls, follow_up=follow_up)


r = random.Random(71)
LONG_A = "".join(r.choice("abcde") for _ in range(900))
LONG_B = "".join(r.choice("abcde") for _ in range(800))
EDIT_A = "".join(r.choice("abcdefgh") for _ in range(450))
EDIT_B = "".join(r.choice("abcdefgh") for _ in range(400))
HOUSES = [r.randint(0, 400) for _ in range(5000)]

PROBLEMS = [
dict(
    id="js-subsets", title="Subsets", difficulty="Medium", pattern="Backtracking",
    leetcode="https://leetcode.com/problems/subsets/",
    neetcode="https://neetcode.io/problems/subsets",
    kind="js", entry="subsets", compare="unordered_nested",
    description=r"""
Given an array `nums` of **distinct** integers, return every subset (the power set), including the empty subset
and `nums` itself. Subsets and the values inside them may be in any order, but no subset may appear twice.

- `1 <= nums.length <= 10`

**Example 1:** `[1, 2, 3]` → `[[], [1], [2], [1, 2], [3], [1, 3], [2, 3], [1, 2, 3]]`

**Example 2:** `[7]` → `[[], [7]]`
""",
    starter="function subsets(nums) {\n  const result = [];\n  // your code\n  return result;\n}\n",
    solution=r'''function subsets(nums) {
  const result = [], path = [];
  function backtrack(i) {
    if (i === nums.length) {
      result.push([...path]);        // COPY: path keeps changing afterwards
      return;
    }
    path.push(nums[i]);              // choice 1: take nums[i]
    backtrack(i + 1);
    path.pop();                      // undo
    backtrack(i + 1);                // choice 2: skip nums[i]
  }
  backtrack(0);
  return result;
}
''',
    tests=[[[1, 2, 3]], [[7]], [[0]], [[1, 2]], [[-1, 5, 3]], [[4, 1, 0, -2]], [list(range(1, 9))], [[9, -9, 3, 0, 1, 2, 5, 8, 7, 6]]],
    examples=2,
    wrong_solutions=[
        "function subsets(nums) {\n  const res = [], path = [];\n  (function bt(i) { if (i === nums.length) { res.push(path); return; } path.push(nums[i]); bt(i + 1); path.pop(); bt(i + 1); })(0);\n  return res;\n}\n",
        "function subsets(nums) {\n  const res = [[]];\n  for (const x of nums) res.push([x]);\n  res.push([...nums]);\n  return res;\n}\n",
    ],
    guide=G(
        prereqs="The lesson *Recursion depth limits and backtracking*: one shared `path` array, push / recurse / pop.",
        intuition="Each element is either in the subset or not. Walk the elements in order and branch twice at each one. The leaves of this decision tree are exactly the 2^n subsets.",
        hints=[
            "At index `i`, you have two choices for `nums[i]`.",
            "Use one shared `path` array and undo each `push` with a `pop`.",
            "When you reach the end, push a **copy** of `path`.",
        ],
        brute_force="Iterative doubling is equally fast: start with `[[]]` and for each `x` append `x` to a copy of every existing subset. Bitmasks also work: subset `mask` contains `nums[i]` when `(mask >> i) & 1`.",
        approach="1. `backtrack(i)`: at the end, record `[...path]`.\n2. Otherwise push `nums[i]`, recurse, pop, recurse again.\n3. Call `backtrack(0)`.",
        complexity="Time O(n * 2^n) (2^n subsets, each copied in O(n)). Space O(n) recursion besides the output.",
        pitfalls="- `result.push(path)` stores the **same** array object every time; after all the pops you get a list of empty arrays. Copy with `[...path]` or `path.slice()`.\n- Recursion depth is only n here, so the call stack is never a concern.",
        follow_up="Subsets II has duplicates: sort first and skip an equal value at the same depth when its twin was skipped.",
    ),
),
dict(
    id="js-combination-sum", title="Combination Sum", difficulty="Medium", pattern="Backtracking",
    leetcode="https://leetcode.com/problems/combination-sum/",
    neetcode="https://neetcode.io/problems/combination-target-sum",
    kind="js", entry="combinationSum", compare="unordered_nested",
    description=r"""
Given an array of **distinct** positive integers `candidates` and a positive `target`, return every unique
combination of candidates that adds up to `target`. The same number may be used any number of times. Two
combinations are the same if they use the same numbers the same number of times; order does not matter.

- `1 <= candidates.length <= 30`, `2 <= candidates[i] <= 40`, `1 <= target <= 40`

**Example 1:** `candidates = [2, 5, 6, 9], target = 9` → `[[2, 2, 5], [9]]`

**Example 2:** `candidates = [3, 4, 5], target = 16` → `[[3, 3, 3, 3, 4], [3, 3, 5, 5], [3, 4, 4, 5], [4, 4, 4, 4]]`
""",
    starter="function combinationSum(candidates, target) {\n  const result = [];\n  // your code\n  return result;\n}\n",
    solution=r'''function combinationSum(candidates, target) {
  const nums = [...candidates].sort((a, b) => a - b);
  const result = [], path = [];
  function backtrack(start, remaining) {
    if (remaining === 0) { result.push([...path]); return; }
    for (let i = start; i < nums.length; i++) {
      if (nums[i] > remaining) break;      // sorted: every later number is too big as well
      path.push(nums[i]);
      backtrack(i, remaining - nums[i]);   // i, not i + 1: the number may be reused
      path.pop();
    }
  }
  backtrack(0, target);
  return result;
}
''',
    tests=[[[2, 5, 6, 9], 9], [[3, 4, 5], 16], [[2, 3, 6, 7], 7], [[2, 3, 5], 8], [[2], 1], [[7], 7], [[10, 1, 2, 7, 6, 5], 8],
           [[8, 7, 4, 3], 11], [[2, 3, 4, 5, 6, 7, 8], 25], [list(range(2, 32)), 40]],
    examples=2,
    wrong_solutions=[
        "function combinationSum(c, t) {\n  const res = [], path = [];\n  (function bt(s, rem) { if (rem === 0) { res.push(path); return; } for (let i = s; i < c.length; i++) if (c[i] <= rem) { path.push(c[i]); bt(i, rem - c[i]); path.pop(); } })(0, t);\n  return res;\n}\n",
        "function combinationSum(c, t) {\n  const res = [], path = [];\n  (function bt(s, rem) { if (rem === 0) { res.push([...path]); return; } for (let i = s; i < c.length; i++) if (c[i] <= rem) { path.push(c[i]); bt(i + 1, rem - c[i]); path.pop(); } })(0, t);\n  return res;\n}\n",
    ],
    guide=G(
        prereqs="Backtracking with a `start` index (lesson *Recursion depth limits and backtracking*).",
        intuition="Build combinations in non-decreasing index order: after choosing `nums[i]`, only allow choices at index `i` or later. That rules out generating `[2, 3]` and `[3, 2]` as two different answers, while `i` (not `i + 1`) allows reuse.",
        hints=[
            "How do you avoid producing the same combination in two orders?",
            "Pass a `start` index; loop `i` from `start`.",
            "Recurse with `i` to allow reuse; sort first so you can `break` once a number is too big.",
        ],
        brute_force="Looping over all candidates at every level (no `start`) finds each multiset once per ordering; deduplicating afterwards with a `Set` of sorted strings works but explores far more branches.",
        approach="1. Sort a copy numerically.\n2. `backtrack(start, remaining)`: zero → record copy.\n3. For `i` from `start`: if `nums[i] > remaining` break; push, recurse `(i, remaining - nums[i])`, pop.",
        complexity="Exponential in target / min(candidate); the pruning keeps it small for target <= 40.",
        pitfalls="- Recursing with `i + 1` forbids reuse (that is Combination Sum II's rule).\n- Without the `start` index you return permutations of the same combination.\n- Forgetting to copy `path` when recording.",
        follow_up="Combination Sum II (each number once, input has duplicates): sort, recurse with `i + 1`, and skip `nums[i] === nums[i - 1]` when `i > start`.",
    ),
),
dict(
    id="js-permute", title="Permutations", difficulty="Medium", pattern="Backtracking",
    leetcode="https://leetcode.com/problems/permutations/",
    neetcode="https://neetcode.io/problems/permutations",
    kind="js", entry="permute", compare="unordered",
    description=r"""
Given an array `nums` of **distinct** integers, return all possible orderings (permutations) of its elements.
The list of permutations may be in any order, but each permutation must list its values in its own order.

- `1 <= nums.length <= 7`

**Example 1:** `[1, 2, 3]` → `[[1,2,3],[1,3,2],[2,1,3],[2,3,1],[3,1,2],[3,2,1]]`

**Example 2:** `[0, 1]` → `[[0, 1], [1, 0]]`
""",
    starter="function permute(nums) {\n  const result = [];\n  // your code\n  return result;\n}\n",
    solution=r'''function permute(nums) {
  const result = [], path = [];
  const used = new Array(nums.length).fill(false);
  function backtrack() {
    if (path.length === nums.length) { result.push([...path]); return; }
    for (let i = 0; i < nums.length; i++) {
      if (used[i]) continue;
      used[i] = true;
      path.push(nums[i]);
      backtrack();
      path.pop();
      used[i] = false;
    }
  }
  backtrack();
  return result;
}
''',
    tests=[[[1, 2, 3]], [[0, 1]], [[1]], [[-1, 5]], [[3, 1, 2]], [[1, 2, 3, 4]], [[5, -4, 0, 9, 2]], [[1, 2, 3, 4, 5, 6, 7]]],
    examples=2,
    wrong_solutions=[
        "function permute(nums) {\n  const res = [];\n  for (let i = 0; i < nums.length; i++) res.push([...nums.slice(i), ...nums.slice(0, i)]);\n  return res;\n}\n",
        "function permute(nums) {\n  const res = [], path = [];\n  (function bt() { if (path.length === nums.length) { res.push([...path]); return; } for (const x of nums) { path.push(x); bt(); path.pop(); } })();\n  return res;\n}\n",
    ],
    guide=G(
        prereqs="Backtracking with a `used` array (lesson *Recursion depth limits and backtracking*).",
        intuition="Fill positions one at a time. For the next position you may pick any element not already used. A boolean `used` array tells you which ones are still free; undo the mark when you backtrack.",
        hints=[
            "How many choices are there for the first position? For the second?",
            "Keep `used[i]` so an element is not placed twice.",
            "Record a copy once `path.length === nums.length`.",
        ],
        brute_force="Rotations give only n of the n! orderings. Generating all n^n sequences and filtering out ones with repeats works but wastes most of the effort.",
        approach="1. `used` all false, empty `path`.\n2. `backtrack()`: full → record copy; otherwise for each unused `i`: mark, push, recurse, pop, unmark.",
        complexity="Time O(n * n!), space O(n) besides the output.",
        pitfalls="- Forgetting `used` lets an element appear twice.\n- Forgetting to reset `used[i] = false` after the recursive call loses later permutations.\n- Recording `path` itself instead of a copy.",
        follow_up="Permutations II (duplicates): sort and skip `nums[i] === nums[i - 1]` when `!used[i - 1]`. Next Permutation produces them in lexicographic order without recursion.",
    ),
),
dict(
    id="js-word-search", title="Word Search", difficulty="Medium", pattern="Backtracking",
    leetcode="https://leetcode.com/problems/word-search/",
    neetcode="https://neetcode.io/problems/search-for-word",
    kind="js", entry="exist",
    description=r"""
`board` is a 2-D grid of single-character strings. Return `true` if `word` can be spelled by a path of cells
where consecutive letters are horizontally or vertically adjacent and no cell is used more than once.

- `1 <= rows, cols <= 6`, `1 <= word.length <= 15`, upper and lower case letters

**Example 1:** `board = [["A","B","C","D"],["S","A","A","T"],["A","C","A","E"]], word = "CAT"` → `true`

**Example 2:** same board, `word = "BAT"` → `false`
""",
    starter="function exist(board, word) {\n  // your code\n}\n",
    solution=r'''function exist(board, word) {
  const rows = board.length, cols = board[0].length;
  function dfs(r, c, i) {
    if (i === word.length) return true;
    if (r < 0 || c < 0 || r >= rows || c >= cols || board[r][c] !== word[i]) return false;
    const saved = board[r][c];
    board[r][c] = "#";                       // mark as used on this path
    const found = dfs(r + 1, c, i + 1) || dfs(r - 1, c, i + 1) || dfs(r, c + 1, i + 1) || dfs(r, c - 1, i + 1);
    board[r][c] = saved;                     // undo for other paths
    return found;
  }
  for (let r = 0; r < rows; r++)
    for (let c = 0; c < cols; c++)
      if (dfs(r, c, 0)) return true;
  return false;
}
''',
    tests=[[[["A", "B", "C", "D"], ["S", "A", "A", "T"], ["A", "C", "A", "E"]], "CAT"],
           [[["A", "B", "C", "D"], ["S", "A", "A", "T"], ["A", "C", "A", "E"]], "BAT"],
           [[["A", "B", "C", "E"], ["S", "F", "C", "S"], ["A", "D", "E", "E"]], "ABCCED"],
           [[["A", "B", "C", "E"], ["S", "F", "C", "S"], ["A", "D", "E", "E"]], "SEE"],
           [[["A", "B", "C", "E"], ["S", "F", "C", "S"], ["A", "D", "E", "E"]], "ABCB"],
           [[["a"]], "a"], [[["a"]], "b"], [[["a", "a"]], "aaa"], [[["a", "b"], ["c", "d"]], "abdc"], [[["a", "b"], ["c", "d"]], "abcd"],
           [[["C", "A", "A"], ["A", "A", "A"], ["B", "C", "D"]], "AAB"],
           [[["A"] * 6 for _ in range(6)], "AAAAAAAAAAAAAAB"], [[["A"] * 6 for _ in range(5)] + [["A"] * 5 + ["B"]], "AAAAAAAAAAAAAAB"]],
    examples=2,
    wrong_solutions=[
        "function exist(board, word) {\n  const s = board.flat().join('');\n  return [...word].every(ch => s.includes(ch));\n}\n",
        "function exist(board, word) {\n  const R = board.length, C = board[0].length;\n  function dfs(r, c, i) {\n    if (i === word.length) return true;\n    if (r < 0 || c < 0 || r >= R || c >= C || board[r][c] !== word[i]) return false;\n    board[r][c] = '#';\n    return dfs(r + 1, c, i + 1) || dfs(r - 1, c, i + 1) || dfs(r, c + 1, i + 1) || dfs(r, c - 1, i + 1);\n  }\n  for (let r = 0; r < R; r++) for (let c = 0; c < C; c++) if (dfs(r, c, 0)) return true;\n  return false;\n}\n",
    ],
    guide=G(
        prereqs="Grid DFS and backtracking: mark, recurse, unmark (lesson *Recursion depth limits and backtracking*).",
        intuition="Try every cell as a starting point. From a matching cell, extend the path to a neighbour that matches the next letter, temporarily marking the current cell so the path cannot reuse it. When a branch fails, restore the cell and try the next neighbour.",
        hints=[
            "Write `dfs(r, c, i)`: can `word[i..]` be spelled starting at cell `(r, c)`?",
            "Mark the cell (for example with `\"#\"`) before recursing and restore it afterwards.",
            "Check bounds and the letter at the top of `dfs`, so callers stay simple.",
        ],
        brute_force="Checking that each letter merely appears in the board ignores adjacency. Without marking, a path can step back onto a cell it already used (`\"aaa\"` on a two-cell board), and marking without restoring breaks later starting points.",
        approach="1. For every cell, call `dfs(r, c, 0)`.\n2. `dfs`: success when `i === word.length`; fail on bounds or mismatch.\n3. Save the letter, write `\"#\"`, try four neighbours with `||` (short-circuits on success), restore, return.",
        complexity="Time O(R * C * 3^L): after the first step each cell has at most 3 unvisited neighbours. Space O(L) recursion.",
        pitfalls="- Forgetting to restore the cell breaks later starting points.\n- `board` is mutated during the search and restored; if the interviewer forbids mutation, use a separate `visited` grid.\n- Recursion depth is at most the word length (15), so the call stack is safe.",
        follow_up="Pruning: if the board lacks enough copies of some letter, return false immediately; search from the rarer end of the word. Word Search II combines this with a trie.",
    ),
),
dict(
    id="js-climbing-stairs", title="Climbing Stairs", difficulty="Easy", pattern="1-D DP",
    leetcode="https://leetcode.com/problems/climbing-stairs/",
    neetcode="https://neetcode.io/problems/climbing-stairs",
    kind="js", entry="climbStairs",
    description=r"""
A staircase has `n` steps. Each move climbs either 1 or 2 steps. In how many different sequences of moves can you
reach the top exactly?

- `1 <= n <= 45` (the answer fits comfortably below `Number.MAX_SAFE_INTEGER`)

**Example 1:** `n = 2` → `2` (1+1, 2)

**Example 2:** `n = 3` → `3` (1+1+1, 1+2, 2+1)
""",
    starter="function climbStairs(n) {\n  // your code\n}\n",
    solution=r'''function climbStairs(n) {
  let prev = 1, cur = 1;        // ways to reach step 0 and step 1
  for (let i = 2; i <= n; i++) {
    [prev, cur] = [cur, prev + cur];
  }
  return cur;
}
''',
    tests=[[2], [3], [1], [4], [5], [10], [20], [30], [44], [45]],
    examples=2,
    wrong_solutions=[
        "function climbStairs(n) {\n  return n;\n}\n",
        "function climbStairs(n) {\n  let a = 1, b = 2;\n  for (let i = 3; i < n; i++) [a, b] = [b, a + b];\n  return n === 1 ? 1 : b;\n}\n",
    ],
    guide=G(
        prereqs="The lesson *Memoisation and DP tables in JavaScript*: from recursion to a rolling pair of variables.",
        intuition="The last move to step `n` was either a 1-step from `n - 1` or a 2-step from `n - 2`. So `ways(n) = ways(n - 1) + ways(n - 2)`: the Fibonacci numbers.",
        hints=[
            "How could the very last move have looked?",
            "Write the recurrence, then notice it only needs the previous two values.",
            "Destructuring `[prev, cur] = [cur, prev + cur]` updates both at once.",
        ],
        brute_force="Plain recursion `ways(n - 1) + ways(n - 2)` makes about 1.8 * 10^9 calls for n = 45 (exponential). Memoising it with a `Map` or array makes it O(n).",
        approach="1. `prev = 1` (step 0), `cur = 1` (step 1).\n2. For i = 2..n: `[prev, cur] = [cur, prev + cur]`.\n3. Return `cur`.",
        complexity="Time O(n), space O(1).",
        pitfalls="- Off-by-one in the loop bounds is the usual bug: test n = 1, 2, 3.\n- For much larger n the values exceed 2^53 and lose precision; switch to `BigInt` (`1n`, `prev + cur` stays exact).",
        follow_up="Min Cost Climbing Stairs adds costs: `dp[i] = cost[i] + Math.min(dp[i - 1], dp[i - 2])`.",
    ),
),
dict(
    id="js-house-robber", title="House Robber", difficulty="Medium", pattern="1-D DP",
    leetcode="https://leetcode.com/problems/house-robber/",
    neetcode="https://neetcode.io/problems/house-robber",
    kind="js", entry="rob",
    description=r"""
Houses stand in a row; `nums[i]` is the money in house `i`. You may not take money from two **adjacent** houses.
Return the most money you can collect.

- `1 <= nums.length <= 100` on LeetCode (tests here go up to 5000), `0 <= nums[i] <= 400`

**Example 1:** `[2, 9, 8, 3, 6]` → `16` (2 + 8 + 6)

**Example 2:** `[1, 1, 3, 3]` → `4`
""",
    starter="function rob(nums) {\n  // your code\n}\n",
    solution=r'''function rob(nums) {
  let skip = 0, take = 0;        // best total if the previous house was skipped / taken
  for (const x of nums) {
    [skip, take] = [Math.max(skip, take), skip + x];
  }
  return Math.max(skip, take);
}
''',
    tests=[[[2, 9, 8, 3, 6]], [[1, 1, 3, 3]], [[5]], [[1, 2]], [[2, 1]], [[1, 2, 3, 1]], [[2, 7, 9, 3, 1]], [[0, 0, 0]],
           [[2, 1, 1, 2]], [[400, 0, 0, 400]], [HOUSES]],
    examples=2,
    wrong_solutions=[
        "function rob(nums) {\n  let even = 0, odd = 0;\n  nums.forEach((x, i) => { if (i % 2) odd += x; else even += x; });\n  return Math.max(even, odd);\n}\n",
        "function rob(nums) {\n  let a = 0, b = 0;\n  for (const x of nums) [a, b] = [b, a + x];\n  return b;\n}\n",
    ],
    guide=G(
        prereqs="1-D DP with two rolling variables (lesson *Memoisation and DP tables in JavaScript*).",
        intuition="At each house you either take it (then the previous house must have been skipped) or skip it (then the previous house may be either). Two running totals capture both possibilities.",
        hints=[
            "Taking alternating houses fails on `[2, 1, 1, 2]`. Why?",
            "`best(i) = Math.max(best(i - 1), best(i - 2) + nums[i])`.",
            "Keep only the last two values, or the `skip` / `take` pair.",
        ],
        brute_force="Try every subset of non-adjacent houses recursively: O(2^n). Memoising `best(i)` turns it into O(n).",
        approach="1. `skip = 0`, `take = 0`.\n2. For each `x`: `newSkip = max(skip, take)`, `newTake = skip + x`.\n3. Answer `max(skip, take)`.\n\n**Dry run** `[2,9,8,3,6]`: (0,2) → (2,9) → (9,10) → (10,12) → (12,16) → 16.",
        complexity="Time O(n), space O(1).",
        pitfalls="- Updating `skip` before computing `take` with the old `skip`: use destructuring or a temporary.\n- Returning only `take` misses answers that skip the last house.",
        follow_up="House Robber II puts the houses in a circle: run this twice, excluding the first or the last house.",
    ),
),
dict(
    id="js-coin-change", title="Coin Change", difficulty="Medium", pattern="1-D DP",
    leetcode="https://leetcode.com/problems/coin-change/",
    neetcode="https://neetcode.io/problems/coin-change",
    kind="js", entry="coinChange",
    description=r"""
Given coin denominations `coins` (unlimited supply of each) and an `amount`, return the fewest coins that add up
to exactly `amount`, or `-1` if it cannot be done. `amount = 0` needs 0 coins.

- `1 <= coins.length <= 12`, `1 <= coins[i] <= 2^31 - 1`, `0 <= amount <= 10^4`

**Example 1:** `coins = [1, 5, 10], amount = 12` → `3` (10 + 1 + 1)

**Example 2:** `coins = [2], amount = 3` → `-1`
""",
    starter="function coinChange(coins, amount) {\n  // your code\n}\n",
    solution=r'''function coinChange(coins, amount) {
  const dp = new Array(amount + 1).fill(Infinity);   // dp[a] = fewest coins for amount a
  dp[0] = 0;
  for (let a = 1; a <= amount; a++) {
    for (const c of coins) {
      if (c <= a && dp[a - c] + 1 < dp[a]) dp[a] = dp[a - c] + 1;
    }
  }
  return dp[amount] === Infinity ? -1 : dp[amount];
}
''',
    tests=[[[1, 5, 10], 12], [[2], 3], [[1], 0], [[1, 2, 5], 11], [[2, 5, 10, 1], 27], [[186, 419, 83, 408], 6249], [[1, 3, 4], 6],
           [[7], 14], [[2147483647], 2], [[3, 7], 5], [[1, 7, 10], 14], [[5, 7, 11, 13, 17], 10000]],
    examples=2,
    wrong_solutions=[
        "function coinChange(coins, amount) {\n  const cs = [...coins].sort((a, b) => b - a);\n  let n = 0;\n  for (const c of cs) { n += Math.floor(amount / c); amount %= c; }\n  return amount === 0 ? n : -1;\n}\n",
        "function coinChange(coins, amount) {\n  const dp = new Array(amount + 1).fill(0);\n  for (let a = 1; a <= amount; a++) { let best = Infinity; for (const c of coins) if (c <= a) best = Math.min(best, dp[a - c] + 1); dp[a] = best; }\n  return dp[amount];\n}\n",
    ],
    guide=G(
        prereqs="Bottom-up DP tables with `new Array(n).fill(Infinity)` (lesson *Memoisation and DP tables in JavaScript*).",
        intuition="The best way to pay `a` ends with some coin `c`; what remains is paying `a - c` as cheaply as possible. So `dp[a] = 1 + min over coins of dp[a - c]`, built from small amounts upward.",
        hints=[
            "Greedy (largest coin first) fails for `[1, 3, 4]` and amount 6. Try it.",
            "Define `dp[a]` = fewest coins for amount `a`; `dp[0] = 0`.",
            "Use `Infinity` for \"impossible\"; `Infinity + 1` is still `Infinity`, so no special cases are needed.",
        ],
        brute_force="Recursion over every coin choice without memoisation is exponential; with a memo `Map` it becomes the same O(amount * coins) as the table.",
        approach="1. `dp = Array(amount + 1).fill(Infinity)`, `dp[0] = 0`.\n2. For `a` from 1 to `amount`, for each coin `c <= a`: `dp[a] = Math.min(dp[a], dp[a - c] + 1)`.\n3. Return `dp[amount]` or -1.",
        complexity="Time O(amount * coins), space O(amount).",
        pitfalls="- Greedy is not correct for arbitrary coin systems.\n- Leaving unreachable amounts at `Infinity` and returning it: the answer must be -1.\n- Huge coins (2^31 - 1) are fine: `c <= a` skips them.",
        follow_up="Coin Change II counts combinations instead: loop coins in the outer loop to avoid counting orderings twice.",
    ),
),
dict(
    id="js-word-break", title="Word Break", difficulty="Medium", pattern="1-D DP",
    leetcode="https://leetcode.com/problems/word-break/",
    neetcode="https://neetcode.io/problems/word-break",
    kind="js", entry="wordBreak",
    description=r"""
Given a string `s` and a list of dictionary words `wordDict`, return `true` if `s` can be split into a sequence of
one or more dictionary words (words may be reused).

- `1 <= s.length <= 300`, `1 <= wordDict.length <= 1000`, `1 <= word length <= 20`, lowercase letters

**Example 1:** `s = "neetcode", wordDict = ["neet", "code"]` → `true`

**Example 2:** `s = "catsandog", wordDict = ["cats", "dog", "sand", "and", "cat"]` → `false`
""",
    starter="function wordBreak(s, wordDict) {\n  // your code\n}\n",
    solution=r'''function wordBreak(s, wordDict) {
  const words = new Set(wordDict);
  let maxLen = 0;
  for (const w of wordDict) maxLen = Math.max(maxLen, w.length);
  const dp = new Array(s.length + 1).fill(false);   // dp[i]: s.slice(0, i) can be split
  dp[0] = true;
  for (let i = 1; i <= s.length; i++) {
    for (let j = Math.max(0, i - maxLen); j < i; j++) {
      if (dp[j] && words.has(s.slice(j, i))) { dp[i] = true; break; }
    }
  }
  return dp[s.length];
}
''',
    tests=[["neetcode", ["neet", "code"]], ["catsandog", ["cats", "dog", "sand", "and", "cat"]], ["applepenapple", ["apple", "pen"]],
           ["a", ["a"]], ["a", ["b"]], ["aaaaaaa", ["aaaa", "aaa"]], ["cars", ["car", "ca", "rs"]], ["goalspecial", ["go", "goal", "goals", "special"]],
           ["bb", ["a", "b", "bbb", "bbbb"]], ["a" * 150 + "b", ["a", "aa", "aaa", "aaaa", "aaaaa", "aaaaaa"]],
           ["a" * 300, ["a" * k for k in range(1, 11)]]],
    examples=2,
    wrong_solutions=[
        "function wordBreak(s, wordDict) {\n  let rest = s;\n  for (const w of [...wordDict].sort((a, b) => b.length - a.length)) rest = rest.split(w).join('');\n  return rest.length === 0;\n}\n",
        "function wordBreak(s, wordDict) {\n  let i = 0;\n  outer: while (i < s.length) { for (const w of wordDict) if (s.startsWith(w, i)) { i += w.length; continue outer; } return false; }\n  return true;\n}\n",
    ],
    guide=G(
        prereqs="Boolean DP arrays, `Set` lookups and `slice` (lesson *Memoisation and DP tables in JavaScript*).",
        intuition="A prefix of length `i` is breakable if some shorter breakable prefix of length `j` is followed by a dictionary word `s.slice(j, i)`. Fill this for i = 1..n.",
        hints=[
            "Greedily taking the first matching word fails on `\"cars\"` with `[\"car\", \"ca\", \"rs\"]`.",
            "`dp[i]` = can the first `i` characters be split? `dp[0] = true`.",
            "Only look back at most `maxLen` characters; use a `Set` for O(1) word checks.",
        ],
        brute_force="Recursively try every dictionary word as the next piece: exponential on inputs like `\"aaaa...ab\"`. Memoising the start index fixes it.",
        approach="1. `words = new Set(wordDict)`, compute `maxLen`.\n2. `dp[0] = true`; for each `i`, check `j` from `i - maxLen` to `i - 1`: if `dp[j]` and `words.has(s.slice(j, i))` then `dp[i] = true`.\n3. Return `dp[n]`.",
        complexity="Time O(n * maxLen * maxLen) (each slice costs up to maxLen). Space O(n).",
        pitfalls="- Greedy matching commits to the wrong word.\n- `wordDict.includes` is O(dictionary) per check; convert to a `Set`.\n- Removing words with `split/join` changes which characters become adjacent.",
        follow_up="Word Break II returns all sentences: memoise the list of splits per start index.",
    ),
),
dict(
    id="js-unique-paths", title="Unique Paths", difficulty="Medium", pattern="2-D DP",
    leetcode="https://leetcode.com/problems/unique-paths/",
    neetcode="https://neetcode.io/problems/count-paths",
    kind="js", entry="uniquePaths",
    description=r"""
A robot starts in the top-left cell of an `m x n` grid and wants to reach the bottom-right cell. It can only move
**right** or **down** one cell at a time. How many different paths are there?

- `1 <= m, n <= 100`; the answer is at most `2 * 10^9`

**Example 1:** `m = 3, n = 6` → `21`

**Example 2:** `m = 3, n = 2` → `3`
""",
    starter="function uniquePaths(m, n) {\n  // your code\n}\n",
    solution=r'''function uniquePaths(m, n) {
  const row = new Array(n).fill(1);       // first row: one way to reach each cell
  for (let r = 1; r < m; r++) {
    for (let c = 1; c < n; c++) {
      row[c] += row[c - 1];               // from above (old row[c]) + from the left
    }
  }
  return row[n - 1];
}
''',
    tests=[[3, 6], [3, 2], [1, 1], [1, 10], [10, 1], [2, 2], [3, 7], [7, 3], [10, 10], [23, 12], [17, 17], [100, 2]],
    examples=2,
    wrong_solutions=[
        "function uniquePaths(m, n) {\n  return m * n - 1;\n}\n",
        "function uniquePaths(m, n) {\n  const row = new Array(n).fill(1);\n  for (let r = 1; r < m; r++) for (let c = 1; c < n; c++) row[c] = row[c - 1] + 1;\n  return row[n - 1];\n}\n",
    ],
    guide=G(
        prereqs="2-D DP and rolling one row (lesson *Memoisation and DP tables in JavaScript*).",
        intuition="Every cell can only be entered from above or from the left, so the number of paths to it is the sum of those two counts. The first row and column have exactly one path each.",
        hints=[
            "How many ways are there to reach a cell in the top row?",
            "`paths[r][c] = paths[r - 1][c] + paths[r][c - 1]`.",
            "One row is enough: before the update `row[c]` still holds the value from the row above.",
        ],
        brute_force="Recursing from the target to the start without memoisation explores every path individually: exponential.",
        approach="1. `row = new Array(n).fill(1)`.\n2. For each later row, for `c` from 1: `row[c] += row[c - 1]`.\n3. Return `row[n - 1]`.\n\nMath version: the robot makes `m - 1` downs and `n - 1` rights, so the answer is C(m + n - 2, m - 1).",
        complexity="Time O(m * n), space O(n).",
        pitfalls="- `Array(m).fill(Array(n).fill(0))` shares one inner array between all rows; use `Array.from({ length: m }, () => new Array(n).fill(0))` for a full 2-D table.\n- Computing the binomial with factorials overflows `Number` precision quickly (20! is above 2^53). Multiply and divide step by step, or use `BigInt`.",
        follow_up="Unique Paths II adds obstacles: set blocked cells to 0 and run the same recurrence.",
    ),
),
dict(
    id="js-longest-common-subsequence", title="Longest Common Subsequence", difficulty="Medium", pattern="2-D DP",
    leetcode="https://leetcode.com/problems/longest-common-subsequence/",
    neetcode="https://neetcode.io/problems/longest-common-subsequence",
    kind="js", entry="longestCommonSubsequence",
    description=r"""
A **subsequence** keeps some characters of a string in their original order, possibly with gaps (`"ace"` is a
subsequence of `"abcde"`). Return the length of the longest subsequence that two strings `text1` and `text2`
have in common (0 if none).

- `1 <= text1.length, text2.length <= 1000`, lowercase letters

**Example 1:** `"cat", "crabt"` → `3`

**Example 2:** `"abcd", "efgh"` → `0`
""",
    starter="function longestCommonSubsequence(text1, text2) {\n  // your code\n}\n",
    solution=r'''function longestCommonSubsequence(text1, text2) {
  const m = text1.length, n = text2.length;
  let prev = new Int32Array(n + 1), cur = new Int32Array(n + 1);   // zero-filled rows
  for (let i = 1; i <= m; i++) {
    for (let j = 1; j <= n; j++) {
      cur[j] = text1[i - 1] === text2[j - 1]
        ? prev[j - 1] + 1
        : Math.max(prev[j], cur[j - 1]);
    }
    [prev, cur] = [cur, prev];            // reuse the old row as the next scratch row
  }
  return prev[n];
}
''',
    tests=[["cat", "crabt"], ["abcd", "efgh"], ["abcde", "ace"], ["abc", "abc"], ["a", "a"], ["a", "b"], ["bl", "yby"],
           ["ezupkr", "ubmrapg"], ["oxcpqrsvwf", "shmtulqrypy"], ["aaaa", "aa"], [LONG_A, LONG_B]],
    examples=2,
    wrong_solutions=[
        "function longestCommonSubsequence(a, b) {\n  const s = new Set(b);\n  let n = 0;\n  for (const c of a) if (s.has(c)) n++;\n  return n;\n}\n",
        "function longestCommonSubsequence(a, b) {\n  let best = 0;\n  for (let i = 0; i < a.length; i++) for (let j = 0; j < b.length; j++) { let k = 0; while (i + k < a.length && j + k < b.length && a[i + k] === b[j + k]) k++; best = Math.max(best, k); }\n  return best;\n}\n",
    ],
    guide=G(
        prereqs="2-D string DP and typed arrays (lesson *Memoisation and DP tables in JavaScript*).",
        intuition="Compare prefixes. If the last characters match, they can end a common subsequence: `1 + LCS` of both shorter prefixes. If not, one of them is useless at the end: take the better of dropping either one.",
        hints=[
            "Let `dp[i][j]` be the LCS of the first `i` characters of `text1` and the first `j` of `text2`.",
            "Match: `dp[i-1][j-1] + 1`. No match: `Math.max(dp[i-1][j], dp[i][j-1])`.",
            "Only the previous row is needed; `Int32Array` rows start filled with zeros.",
        ],
        brute_force="Enumerate all 2^m subsequences of `text1` and test each against `text2`: hopeless for length 1000. Plain recursion on `(i, j)` without a memo is also exponential.",
        approach="1. Two rows `prev` and `cur` of length `n + 1`.\n2. For each `i`, fill `cur[j]` with the recurrence; swap rows.\n3. Return `prev[n]` after the last swap.",
        complexity="Time O(m * n) = 10^6 steps, space O(n).",
        pitfalls="- Longest common **substring** (no gaps) is a different problem with a different recurrence.\n- Off-by-one between the table index `i` and the string index `i - 1`.\n- A full `Array.from` 1001 x 1001 table works too, but the two-row typed-array version is faster and lighter.",
        follow_up="Edit Distance and Shortest Common Supersequence fill the same table shape.",
    ),
),
dict(
    id="js-edit-distance", title="Edit Distance", difficulty="Medium", pattern="2-D DP",
    leetcode="https://leetcode.com/problems/edit-distance/",
    neetcode="https://neetcode.io/problems/edit-distance",
    kind="js", entry="minDistance",
    description=r"""
Return the minimum number of single-character operations needed to turn `word1` into `word2`. The allowed
operations are: insert a character, delete a character, and replace a character.

- `0 <= word1.length, word2.length <= 500`, lowercase letters

**Example 1:** `"monkeys", "money"` → `2` (delete `k`, delete `s`)

**Example 2:** `"neatcdee", "neetcode"` → `3`
""",
    starter="function minDistance(word1, word2) {\n  // your code\n}\n",
    solution=r'''function minDistance(word1, word2) {
  const m = word1.length, n = word2.length;
  let prev = Array.from({ length: n + 1 }, (_, j) => j);   // "" -> word2 prefix: j inserts
  for (let i = 1; i <= m; i++) {
    const cur = new Array(n + 1);
    cur[0] = i;                                             // word1 prefix -> "": i deletes
    for (let j = 1; j <= n; j++) {
      if (word1[i - 1] === word2[j - 1]) cur[j] = prev[j - 1];
      else cur[j] = 1 + Math.min(prev[j],        // delete
                                 cur[j - 1],     // insert
                                 prev[j - 1]);   // replace
    }
    prev = cur;
  }
  return prev[n];
}
''',
    tests=[["monkeys", "money"], ["neatcdee", "neetcode"], ["", ""], ["", "abc"], ["abc", ""], ["horse", "ros"],
           ["intention", "execution"], ["a", "a"], ["ab", "ba"], ["kitten", "sitting"], ["abcdef", "azced"], [EDIT_A, EDIT_B]],
    examples=2,
    wrong_solutions=[
        "function minDistance(a, b) {\n  let d = Math.abs(a.length - b.length);\n  for (let i = 0; i < Math.min(a.length, b.length); i++) if (a[i] !== b[i]) d++;\n  return d;\n}\n",
        "function minDistance(a, b) {\n  const m = a.length, n = b.length;\n  let prev = Array.from({ length: n + 1 }, (_, j) => j);\n  for (let i = 1; i <= m; i++) {\n    const cur = [i];\n    for (let j = 1; j <= n; j++) cur[j] = a[i - 1] === b[j - 1] ? prev[j - 1] : 1 + Math.min(prev[j], cur[j - 1]);\n    prev = cur;\n  }\n  return prev[n];\n}\n",
    ],
    guide=G(
        prereqs="The LCS table shape (*Longest Common Subsequence*) and base rows built with `Array.from({ length }, (_, j) => j)`.",
        intuition="Look at the last characters of the two prefixes. If they match, no operation is needed for them. Otherwise the last operation was a delete, an insert or a replace, each costing 1 plus the distance of a smaller pair of prefixes.",
        hints=[
            "What is the distance between `\"\"` and a word of length j?",
            "`dp[i][j]` = distance between the first i chars of word1 and the first j of word2.",
            "Mismatch: `1 + Math.min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1])`.",
        ],
        brute_force="Recursion over the three operations without memoisation is exponential (3^(m+n) branches).",
        approach="1. `prev[j] = j`.\n2. For each `i`: `cur[0] = i`; fill `cur[j]` with the match / three-way minimum.\n3. Return `prev[n]`.\n\n**Dry run** `\"ab\"` → `\"ba\"`: no shared position, but one delete and one insert (or two replaces) give 2.",
        complexity="Time O(m * n), space O(n).",
        pitfalls="- Forgetting the replace option (only insert/delete) gives the wrong answer for `\"ab\"`/`\"ba\"`-style inputs.\n- Wrong base cases: row 0 is `j` inserts and column 0 is `i` deletes.\n- Comparing position by position (Hamming distance) ignores shifts.",
        follow_up="Return the actual operations by keeping the full table and walking back from `dp[m][n]`.",
    ),
),
]
