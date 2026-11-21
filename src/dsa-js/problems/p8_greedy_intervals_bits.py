"""DSA in JavaScript: Greedy, Intervals and Bit Manipulation problems."""
import random


def G(prereqs, intuition, hints, brute_force, approach, complexity, pitfalls, follow_up=""):
    return dict(prereqs=prereqs, intuition=intuition, hints=hints, brute_force=brute_force,
                approach=approach, complexity=complexity, pitfalls=pitfalls, follow_up=follow_up)


r = random.Random(89)
KADANE = [r.randint(-1000, 1000) for _ in range(20000)]
JUMPS_OK = [r.randint(1, 3) for _ in range(20000)]
JUMPS_BAD = [r.randint(1, 3) for _ in range(5000)] + [0, 0, 0, 0] + [1] * 100


def random_intervals(n, seed, span=100000, maxlen=200):
    rr = random.Random(seed)
    out = []
    for _ in range(n):
        s = rr.randint(0, span)
        out.append([s, s + rr.randint(0, maxlen)])
    return out


def sorted_disjoint(n, seed):
    rr = random.Random(seed)
    out, cur = [], 0
    for _ in range(n):
        s = cur + rr.randint(1, 20)
        e = s + rr.randint(0, 20)
        out.append([s, e]); cur = e
    return out


def gas_case(n, seed):
    rr = random.Random(seed)
    gas = [rr.randint(0, 100) for _ in range(n)]
    cost = [rr.randint(0, 100) for _ in range(n)]
    diff = sum(gas) - sum(cost)
    if diff < 0:
        gas[0] += -diff          # make a full loop possible
    return [gas, cost]


PROBLEMS = [
dict(
    id="js-maximum-subarray", title="Maximum Subarray", difficulty="Medium", pattern="Greedy",
    leetcode="https://leetcode.com/problems/maximum-subarray/",
    neetcode="https://neetcode.io/problems/maximum-subarray",
    kind="js", entry="maxSubArray",
    description=r"""
Given an integer array `nums`, return the largest sum of a non-empty **contiguous** subarray.

- `1 <= nums.length <= 10^5`, `-10^4 <= nums[i] <= 10^4`

**Example 1:** `[2, -3, 4, -2, 2, 1, -1, 4]` → `8` (`[4, -2, 2, 1, -1, 4]`)

**Example 2:** `[-1]` → `-1`
""",
    starter="function maxSubArray(nums) {\n  // your code\n}\n",
    solution=r'''function maxSubArray(nums) {
  let best = nums[0], cur = 0;
  for (const x of nums) {
    cur = Math.max(x, cur + x);     // extend the current run or start fresh at x
    best = Math.max(best, cur);
  }
  return best;
}
''',
    tests=[[[2, -3, 4, -2, 2, 1, -1, 4]], [[-1]], [[-2, 1, -3, 4, -1, 2, 1, -5, 4]], [[1]], [[5, 4, -1, 7, 8]], [[-3, -2, -5]],
           [[0, 0, 0]], [[-1, 0, -2]], [[8, -19, 5, -4, 20]], [[10000] * 10], [KADANE]],
    examples=2,
    wrong_solutions=[
        "function maxSubArray(nums) {\n  let best = 0, cur = 0;\n  for (const x of nums) { cur = Math.max(0, cur + x); best = Math.max(best, cur); }\n  return best;\n}\n",
        "function maxSubArray(nums) {\n  return nums.reduce((a, b) => a + b, 0);\n}\n",
    ],
    guide=G(
        prereqs="Running totals and `Math.max`; the greedy lesson *Pattern map III*.",
        intuition="Walk left to right with the best sum of a run that **ends here**. If the run so far is negative, it can only hurt whatever comes next, so drop it and start fresh at the current element (Kadane's algorithm).",
        hints=[
            "What is the best subarray that ends exactly at index i?",
            "It is either `nums[i]` alone or `nums[i]` added to the best run ending at `i - 1`.",
            "Start `best` at `nums[0]`, not 0, so all-negative arrays work.",
        ],
        brute_force="Try every start and extend to every end with a running sum: O(n^2). Divide and conquer gives O(n log n).",
        approach="1. `best = nums[0]`, `cur = 0`.\n2. For each `x`: `cur = Math.max(x, cur + x)`; `best = Math.max(best, cur)`.\n\n**Dry run** `[2,-3,4,-2,2,1,-1,4]`: cur 2, -1, 4, 2, 4, 5, 4, 8 → best 8.",
        complexity="Time O(n), space O(1).",
        pitfalls="- Starting `best` at 0 returns 0 for `[-3, -2, -5]`; the subarray must be non-empty.\n- Summing everything is the answer only when no prefix or suffix is negative.",
        follow_up="Maximum Product Subarray tracks both the largest and smallest product ending here, because a negative factor swaps them.",
    ),
),
dict(
    id="js-jump-game", title="Jump Game", difficulty="Medium", pattern="Greedy",
    leetcode="https://leetcode.com/problems/jump-game/",
    neetcode="https://neetcode.io/problems/jump-game",
    kind="js", entry="canJump",
    description=r"""
You start at index 0 of `nums`. From index `i` you may jump forward by any distance from 1 up to `nums[i]`.
Return `true` if you can reach the last index.

- `1 <= nums.length <= 10^4` on LeetCode (tests here go higher), `0 <= nums[i] <= 1000`

**Example 1:** `[1, 2, 0, 1, 0]` → `true`

**Example 2:** `[1, 2, 1, 0, 1]` → `false`
""",
    starter="function canJump(nums) {\n  // your code\n}\n",
    solution=r'''function canJump(nums) {
  let reach = 0;                         // farthest index reachable so far
  for (let i = 0; i < nums.length; i++) {
    if (i > reach) return false;         // stuck before i
    reach = Math.max(reach, i + nums[i]);
    if (reach >= nums.length - 1) return true;
  }
  return true;
}
''',
    tests=[[[1, 2, 0, 1, 0]], [[1, 2, 1, 0, 1]], [[0]], [[2, 3, 1, 1, 4]], [[3, 2, 1, 0, 4]], [[2, 0, 0]], [[0, 1]], [[1, 0, 1, 0]],
           [[5, 0, 0, 0, 0, 0]], [[1, 1, 1, 1]], [[2, 3, 0, 1, 4]], [[3, 0, 8, 2, 0, 0, 1]], [JUMPS_OK], [JUMPS_BAD]],
    examples=2,
    wrong_solutions=[
        "function canJump(nums) {\n  return !nums.slice(0, -1).includes(0);\n}\n",
        "function canJump(nums) {\n  let i = 0;\n  while (i < nums.length - 1) { if (nums[i] === 0) return false; i += nums[i]; }\n  return true;\n}\n",
    ],
    guide=G(
        prereqs="Greedy scans with a running maximum (lesson *Pattern map III*).",
        intuition="You never need to know **how** you reach a position, only the farthest index reachable so far. Scan left to right: if the current index is beyond that reach, you are stuck; otherwise extend the reach with `i + nums[i]`.",
        hints=[
            "Track one number: the farthest reachable index.",
            "If `i > reach`, can you ever stand on index `i`?",
            "You can stop early as soon as `reach` covers the last index.",
        ],
        brute_force="DP marking `good[i]` from right to left, checking all jump lengths: O(n * max jump). Always jumping the maximum distance is wrong: a shorter jump may land on a better springboard.",
        approach="1. `reach = 0`.\n2. For each `i`: if `i > reach` return false; `reach = Math.max(reach, i + nums[i])`; return true once `reach >= n - 1`.\n\n**Dry run** `[1,2,1,0,1]`: reach 1, 3, 3, 3; at i = 4 > 3 → false.",
        complexity="Time O(n), space O(1).",
        pitfalls="- A zero is not always fatal (`[2, 0, 0]` is reachable); only a zero you cannot jump over is.\n- Always taking the longest jump can skip the only useful springboard.",
        follow_up="Jump Game II asks for the minimum number of jumps: a BFS by layers of reach in O(n).",
    ),
),
dict(
    id="js-gas-station", title="Gas Station", difficulty="Medium", pattern="Greedy",
    leetcode="https://leetcode.com/problems/gas-station/",
    neetcode="https://neetcode.io/problems/gas-station",
    kind="js", entry="canCompleteCircuit",
    description=r"""
`n` gas stations stand on a circular road. Station `i` gives `gas[i]` units of fuel, and driving from station `i` to
station `i + 1` (wrapping around) uses `cost[i]` units. You start with an empty tank at a station of your choice.
Return the index of the station from which you can drive around the whole circle once, or `-1` if impossible.
If a solution exists it is unique.

**Example 1:** `gas = [1, 2, 3, 4], cost = [2, 2, 4, 1]` → `3`

**Example 2:** `gas = [1, 2, 3], cost = [2, 3, 2]` → `-1`
""",
    starter="function canCompleteCircuit(gas, cost) {\n  // your code\n}\n",
    solution=r'''function canCompleteCircuit(gas, cost) {
  let total = 0, tank = 0, start = 0;
  for (let i = 0; i < gas.length; i++) {
    const d = gas[i] - cost[i];
    total += d;
    tank += d;
    if (tank < 0) {          // cannot get past i from start: no station in start..i works
      start = i + 1;
      tank = 0;
    }
  }
  return total < 0 ? -1 : start;
}
''',
    tests=[[[1, 2, 3, 4], [2, 2, 4, 1]], [[1, 2, 3], [2, 3, 2]], [[1, 2, 3, 4, 5], [3, 4, 5, 1, 2]], [[2, 3, 4], [3, 4, 3]],
           [[5], [4]], [[4], [5]], [[0, 0, 5], [1, 1, 1]], [[3, 1, 1], [1, 2, 2]], [[5, 1, 2, 3, 4], [4, 4, 1, 5, 1]],
           gas_case(30, 1), gas_case(20000, 2)],
    examples=2,
    wrong_solutions=[
        "function canCompleteCircuit(gas, cost) {\n  const s = gas.reduce((a, b) => a + b, 0) - cost.reduce((a, b) => a + b, 0);\n  return s < 0 ? -1 : 0;\n}\n",
        "function canCompleteCircuit(gas, cost) {\n  let best = 0;\n  for (let i = 1; i < gas.length; i++) if (gas[i] - cost[i] > gas[best] - cost[best]) best = i;\n  return gas.reduce((a, b) => a + b, 0) < cost.reduce((a, b) => a + b, 0) ? -1 : best;\n}\n",
    ],
    guide=G(
        prereqs="Running sums and the greedy exchange argument (lesson *Pattern map III*).",
        intuition="If total gas is less than total cost, no start works. Otherwise, drive from a candidate start; the moment the tank goes negative at station `i`, every station between the start and `i` also fails (each would arrive at `i` with even less fuel), so jump the candidate to `i + 1`.",
        hints=[
            "When is the trip impossible from every start?",
            "If you run dry at `i` starting from `s`, could any station in `s..i` be the answer?",
            "One pass: `total`, `tank`, `start`.",
        ],
        brute_force="Simulate a full loop from every start: O(n^2).",
        approach="1. For each `i`, add `gas[i] - cost[i]` to `total` and `tank`.\n2. If `tank < 0`, set `start = i + 1`, `tank = 0`.\n3. Return `-1` if `total < 0`, else `start`.",
        complexity="Time O(n), space O(1).",
        pitfalls="- Picking the station with the largest surplus is a guess, not a proof.\n- `start` can become `n` only when `total < 0`, which you report as -1 anyway.",
        follow_up="The same \"reset on negative\" idea is Kadane's algorithm in disguise.",
    ),
),
dict(
    id="js-merge-intervals", title="Merge Intervals", difficulty="Medium", pattern="Intervals",
    leetcode="https://leetcode.com/problems/merge-intervals/",
    neetcode="https://neetcode.io/problems/merge-intervals",
    kind="js", entry="merge",
    description=r"""
`intervals[i] = [start, end]`. Merge every group of overlapping intervals (intervals that touch, like `[1, 4]`
and `[4, 5]`, also overlap) and return the merged intervals sorted by start.

- `1 <= intervals.length <= 10^4`, `0 <= start <= end <= 10^5`

**Example 1:** `[[1, 3], [1, 5], [6, 7]]` → `[[1, 5], [6, 7]]`

**Example 2:** `[[1, 2], [2, 3]]` → `[[1, 3]]`
""",
    starter="function merge(intervals) {\n  // your code\n}\n",
    solution=r'''function merge(intervals) {
  const sorted = [...intervals].sort((a, b) => a[0] - b[0]);   // numeric, by start
  const out = [];
  for (const [s, e] of sorted) {
    const last = out[out.length - 1];
    if (last && s <= last[1]) last[1] = Math.max(last[1], e);  // overlap: extend
    else out.push([s, e]);
  }
  return out;
}
''',
    tests=[[[[1, 3], [1, 5], [6, 7]]], [[[1, 2], [2, 3]]], [[[1, 3], [2, 6], [8, 10], [15, 18]]], [[[1, 4], [4, 5]]], [[[5, 5]]],
           [[[1, 4], [0, 4]]], [[[1, 4], [2, 3]]], [[[9, 10], [100, 200], [10, 20], [3, 4]]], [[[2, 3], [4, 5], [6, 7], [8, 9], [1, 10]]],
           [[[0, 0], [1, 1], [0, 1]]], [random_intervals(400, 1)], [random_intervals(8000, 2, 10**5, 30)]],
    examples=2,
    wrong_solutions=[
        "function merge(intervals) {\n  const s = [...intervals].sort(), out = [];\n  for (const [a, b] of s) { const l = out[out.length - 1]; if (l && a <= l[1]) l[1] = Math.max(l[1], b); else out.push([a, b]); }\n  return out;\n}\n",
        "function merge(intervals) {\n  const s = [...intervals].sort((x, y) => x[0] - y[0]), out = [];\n  for (const [a, b] of s) { const l = out[out.length - 1]; if (l && a < l[1]) l[1] = b; else out.push([a, b]); }\n  return out;\n}\n",
    ],
    guide=G(
        prereqs="Sorting arrays of arrays with a comparator (lesson *Numbers and sorting without surprises*); the interval lessons.",
        intuition="After sorting by start, overlapping intervals sit next to each other. Sweep once: either the next interval overlaps the last merged one (extend its end) or it starts a new block.",
        hints=[
            "Sort by start with `(a, b) => a[0] - b[0]`.",
            "Compare each interval's start with the end of the last merged interval.",
            "When merging, the new end is the **maximum** of both ends.",
        ],
        brute_force="Repeatedly scan all pairs and merge any overlapping pair until nothing changes: O(n^2) or worse.",
        approach="1. Sort a copy by start.\n2. For each `[s, e]`: if `out` is non-empty and `s <= last[1]`, set `last[1] = Math.max(last[1], e)`; else push.\n3. Return `out`.",
        complexity="Time O(n log n) for the sort, space O(n).",
        pitfalls="- `intervals.sort()` with no comparator converts each pair to a string like `\"10,20\"` and sorts lexicographically: `[10, 20]` lands before `[9, 10]`.\n- `last[1] = e` (instead of the max) shrinks an interval that contains the next one (`[1,4]`, `[2,3]`).\n- Use `<=` so touching intervals merge.",
        follow_up="Insert Interval does the same sweep on already-sorted input in O(n).",
    ),
),
dict(
    id="js-insert-interval", title="Insert Interval", difficulty="Medium", pattern="Intervals",
    leetcode="https://leetcode.com/problems/insert-interval/",
    neetcode="https://neetcode.io/problems/insert-new-interval",
    kind="js", entry="insert",
    description=r"""
`intervals` is a list of non-overlapping intervals sorted by start. Insert `newInterval`, merging wherever it
overlaps (touching counts as overlapping), and return the resulting sorted, non-overlapping list.

**Example 1:** `intervals = [[1, 3], [4, 6]], newInterval = [2, 5]` → `[[1, 6]]`

**Example 2:** `intervals = [[1, 2], [3, 5], [9, 10]], newInterval = [6, 7]` → `[[1, 2], [3, 5], [6, 7], [9, 10]]`
""",
    starter="function insert(intervals, newInterval) {\n  // your code\n}\n",
    solution=r'''function insert(intervals, newInterval) {
  const out = [];
  let [s, e] = newInterval;
  let i = 0;
  while (i < intervals.length && intervals[i][1] < s) out.push(intervals[i++]);   // entirely before
  while (i < intervals.length && intervals[i][0] <= e) {                         // overlapping
    s = Math.min(s, intervals[i][0]);
    e = Math.max(e, intervals[i][1]);
    i++;
  }
  out.push([s, e]);
  while (i < intervals.length) out.push(intervals[i++]);                         // entirely after
  return out;
}
''',
    tests=[[[[1, 3], [4, 6]], [2, 5]], [[[1, 2], [3, 5], [9, 10]], [6, 7]], [[], [5, 7]], [[[1, 5]], [2, 3]], [[[1, 5]], [6, 8]],
           [[[3, 5]], [1, 2]], [[[1, 2], [3, 5], [6, 7], [8, 10], [12, 16]], [4, 8]], [[[1, 5]], [5, 7]], [[[2, 5], [6, 7]], [0, 10]],
           [[[1, 2], [5, 6]], [3, 4]], [sorted_disjoint(3000, 1), [5000, 9000]]],
    examples=2,
    wrong_solutions=[
        "function insert(intervals, nw) {\n  return [...intervals, nw].sort((a, b) => a[0] - b[0]);\n}\n",
        "function insert(intervals, nw) {\n  const out = []; let [s, e] = nw, i = 0;\n  while (i < intervals.length && intervals[i][1] < s) out.push(intervals[i++]);\n  while (i < intervals.length && intervals[i][0] < e) { s = Math.min(s, intervals[i][0]); e = Math.max(e, intervals[i][1]); i++; }\n  out.push([s, e]);\n  while (i < intervals.length) out.push(intervals[i++]);\n  return out;\n}\n",
    ],
    guide=G(
        prereqs="*Merge Intervals* and two-phase scans with an index (lesson *Pattern map III*).",
        intuition="Because the list is already sorted and disjoint, it splits into three runs: intervals that end before the new one starts, intervals that overlap it, and intervals that start after it ends. Copy the first run, fold the middle run into one interval, copy the last run.",
        hints=[
            "Which intervals can be copied unchanged at the front?",
            "While `intervals[i][0] <= e`, the interval overlaps: widen `[s, e]`.",
            "Push the merged interval, then the rest.",
        ],
        brute_force="Append and run the full Merge Intervals algorithm: O(n log n). Correct, but it ignores that the input is sorted.",
        approach="1. Copy intervals with `end < s`.\n2. Merge intervals with `start <= e` into `[s, e]`.\n3. Push `[s, e]`, then copy the rest.",
        complexity="Time O(n), space O(n) for the output.",
        pitfalls="- `<` instead of `<=` in the overlap test fails to merge touching intervals (`[1,5]` and `[5,7]`).\n- Forgetting the case where the new interval goes at the very end or into an empty list.",
        follow_up="With many insertions, keep intervals in a balanced tree keyed by start.",
    ),
),
dict(
    id="js-non-overlapping-intervals", title="Non-overlapping Intervals", difficulty="Medium", pattern="Intervals",
    leetcode="https://leetcode.com/problems/non-overlapping-intervals/",
    neetcode="https://neetcode.io/problems/non-overlapping-intervals",
    kind="js", entry="eraseOverlapIntervals",
    description=r"""
Return the minimum number of intervals you must remove so that the rest do not overlap. Here intervals that only
touch at a point, like `[1, 2]` and `[2, 3]`, do **not** overlap.

- `1 <= intervals.length <= 10^5`, `-5 * 10^4 <= start < end <= 5 * 10^4`

**Example 1:** `[[1, 2], [2, 4], [1, 4]]` → `1`

**Example 2:** `[[1, 2], [2, 4]]` → `0`
""",
    starter="function eraseOverlapIntervals(intervals) {\n  // your code\n}\n",
    solution=r'''function eraseOverlapIntervals(intervals) {
  const sorted = [...intervals].sort((a, b) => a[1] - b[1]);   // by END
  let removed = 0, lastEnd = -Infinity;
  for (const [s, e] of sorted) {
    if (s >= lastEnd) lastEnd = e;     // keep it: it ends earliest among compatible ones
    else removed++;                    // overlaps the kept interval: remove it
  }
  return removed;
}
''',
    tests=[[[[1, 2], [2, 4], [1, 4]]], [[[1, 2], [2, 4]]], [[[1, 2], [2, 3], [3, 4], [1, 3]]], [[[1, 2], [1, 2], [1, 2]]], [[[0, 1]]],
           [[[1, 100], [11, 22], [1, 11], [2, 12]]], [[[-5, -1], [-3, 2], [0, 4], [3, 6]]], [[[1, 10], [2, 3], [4, 5], [6, 7]]],
           [[[-50000, 50000], [0, 1]]], [[[s, s + r.randint(1, 50)] for s in r.sample(range(-50000, 49900), 3000)]]],
    examples=2,
    wrong_solutions=[
        "function eraseOverlapIntervals(intervals) {\n  const s = [...intervals].sort((a, b) => a[0] - b[0]);\n  let removed = 0, lastEnd = -Infinity;\n  for (const [a, b] of s) { if (a >= lastEnd) lastEnd = b; else removed++; }\n  return removed;\n}\n",
        "function eraseOverlapIntervals(intervals) {\n  const s = [...intervals].sort((a, b) => a[1] - b[1]);\n  let removed = 0, lastEnd = -Infinity;\n  for (const [a, b] of s) { if (a > lastEnd) lastEnd = b; else removed++; }\n  return removed;\n}\n",
    ],
    guide=G(
        prereqs="Interval scheduling and the greedy exchange argument (lesson *Pattern map III*).",
        intuition="Removing as few as possible means keeping as many as possible. To keep the most, always keep the compatible interval that **ends earliest**: it leaves the most room for everything after it.",
        hints=[
            "Flip the question: what is the largest set of non-overlapping intervals?",
            "Sort by end time, not start time.",
            "Keep an interval when `start >= lastEnd`; otherwise count it as removed.",
        ],
        brute_force="Try every subset to keep: O(2^n). Sorting by start and keeping greedily fails on `[[1,100],[11,22],[1,11],[2,12]]`.",
        approach="1. Sort a copy by end.\n2. `lastEnd = -Infinity`; for each `[s, e]`: if `s >= lastEnd` keep (update `lastEnd`), else `removed++`.\n3. Return `removed`.",
        complexity="Time O(n log n), space O(n) for the copy.",
        pitfalls="- `>` instead of `>=` treats touching intervals as overlapping.\n- Sorting by start without the \"keep the smaller end\" fix gives too many removals.\n- `-Infinity` as the starting `lastEnd` is safe for negative coordinates; `0` is not.",
        follow_up="Minimum Number of Arrows to Burst Balloons is the same greedy where touching does count as overlapping.",
    ),
),
dict(
    id="js-number-of-1-bits", title="Number of 1 Bits", difficulty="Easy", pattern="Bit Manipulation",
    leetcode="https://leetcode.com/problems/number-of-1-bits/",
    neetcode="https://neetcode.io/problems/number-of-one-bits",
    kind="js", entry="hammingWeight",
    description=r"""
`n` is a 32-bit **unsigned** integer given as an ordinary JavaScript number between `0` and `2^32 - 1`
(`4294967295`). Return how many of its 32 bits are `1`.

**Example 1:** `11` (binary `1011`) → `3`

**Example 2:** `4294967293` (binary `11111111111111111111111111111101`) → `31`

Careful: JavaScript bitwise operators work on **signed** 32-bit values, so numbers at or above `2^31` behave like
negative numbers inside `&`, `|` and `>>`.
""",
    starter="function hammingWeight(n) {\n  // your code\n}\n",
    solution=r'''function hammingWeight(n) {
  let count = 0;
  while (n !== 0) {
    n &= n - 1;        // clears the lowest set bit (works on the signed 32-bit view too)
    count++;
  }
  return count;
}
''',
    tests=[[11], [4294967293], [0], [1], [128], [2147483648], [2147483647], [4294967295], [2863311530], [65535], [1 << 20], [123456789]],
    examples=2,
    wrong_solutions=[
        "function hammingWeight(n) {\n  let c = 0;\n  while (n > 0) { c += n & 1; n >>= 1; }\n  return c;\n}\n",
        "function hammingWeight(n) {\n  let c = 0;\n  for (let i = 0; i < 31; i++) c += (n >>> i) & 1;\n  return c;\n}\n",
    ],
    guide=G(
        prereqs="The lesson *Pattern map III*: JavaScript's 32-bit bitwise operators, `>>` versus `>>>`, and `n & (n - 1)`.",
        intuition="`n & (n - 1)` switches off exactly the lowest 1 bit. Repeat until nothing is left and count the steps: one step per set bit.",
        hints=[
            "What does subtracting 1 do to the lowest set bit and the zeros below it?",
            "`n &= n - 1` until `n === 0`.",
            "If you shift instead, use `>>>` (unsigned) so the loop ends for numbers at or above 2^31.",
        ],
        brute_force="Check all 32 positions: `(n >>> i) & 1` for `i` from 0 to 31. Also O(1), just 32 steps every time. `n.toString(2)` and counting `\"1\"` characters works for non-negative numbers too.",
        approach="1. `count = 0`.\n2. While `n !== 0`: `n &= n - 1`; `count++`.\n\nFor `n >= 2^31`, the first `&` turns `n` into a negative 32-bit value, but the bit pattern is the same and the loop still clears one bit per step until 0.",
        complexity="O(number of set bits) <= 32 steps; O(1) space.",
        pitfalls="- `n >>= 1` is an arithmetic shift: for `2147483648` it produces a negative number and `while (n > 0)` stops immediately (or, with `!== 0`, never stops because the sign bit is copied in).\n- Looping over only 31 bits misses the top bit.",
        follow_up="Counting Bits computes the counts for every number 0..n in O(n) total.",
    ),
),
dict(
    id="js-counting-bits", title="Counting Bits", difficulty="Easy", pattern="Bit Manipulation",
    leetcode="https://leetcode.com/problems/counting-bits/",
    neetcode="https://neetcode.io/problems/counting-bits",
    kind="js", entry="countBits",
    description=r"""
Given `n`, return an array `ans` of length `n + 1` where `ans[i]` is the number of `1` bits in the binary form of
`i`. Aim for O(n) overall.

- `0 <= n <= 10^5`

**Example 1:** `n = 4` → `[0, 1, 1, 2, 1]`

**Example 2:** `n = 0` → `[0]`
""",
    starter="function countBits(n) {\n  // your code\n}\n",
    solution=r'''function countBits(n) {
  const ans = new Array(n + 1).fill(0);
  for (let i = 1; i <= n; i++) {
    ans[i] = ans[i >> 1] + (i & 1);   // drop the last bit, then add it back if it was 1
  }
  return ans;
}
''',
    tests=[[4], [0], [1], [2], [5], [8], [16], [31], [100], [20000]],
    examples=2,
    wrong_solutions=[
        "function countBits(n) {\n  const a = [];\n  for (let i = 0; i <= n; i++) a.push(i % 2);\n  return a;\n}\n",
        "function countBits(n) {\n  const a = new Array(n + 1).fill(0);\n  for (let i = 1; i <= n; i++) a[i] = a[i - 1] + 1;\n  return a;\n}\n",
    ],
    guide=G(
        prereqs="Bit shifts and DP over earlier answers (lesson *Pattern map III*).",
        intuition="`i >> 1` is `i` with its last bit removed, and it is smaller than `i`, so its answer is already known. Add 1 if the removed bit `i & 1` was set.",
        hints=[
            "How does the binary form of `i` relate to that of `i >> 1`?",
            "`ans[i] = ans[i >> 1] + (i & 1)`.",
            "Alternative: `ans[i] = ans[i & (i - 1)] + 1`.",
        ],
        brute_force="Run *Number of 1 Bits* on each `i`: O(n log n), fine but not the intended O(n).",
        approach="1. `ans = new Array(n + 1).fill(0)`.\n2. For `i` from 1 to `n`: `ans[i] = ans[i >> 1] + (i & 1)`.",
        complexity="Time O(n), space O(n) for the output.",
        pitfalls="- `new Array(n + 1)` without `fill(0)` contains holes; reading `ans[0]` then gives `undefined` and the sums become `NaN`.\n- `i % 2` alone is only the last bit.",
        follow_up="`Number.prototype.toString(2)` and a regex count also work but allocate a string per number.",
    ),
),
dict(
    id="js-reverse-bits", title="Reverse Bits", difficulty="Easy", pattern="Bit Manipulation",
    leetcode="https://leetcode.com/problems/reverse-bits/",
    neetcode="https://neetcode.io/problems/reverse-bits",
    kind="js", entry="reverseBits",
    description=r"""
`n` is a 32-bit unsigned integer given as a JavaScript number in `0 .. 2^32 - 1`. Reverse the order of its 32 bits
(bit 0 swaps with bit 31, bit 1 with bit 30, and so on) and return the result as an **unsigned** value, again in
`0 .. 2^32 - 1`.

**Example 1:** `43261596` (`00000010100101000001111010011100`) → `964176192` (`00111001011110000010100101000000`)

**Example 2:** `1` → `2147483648`
""",
    starter="function reverseBits(n) {\n  // your code\n}\n",
    solution=r'''function reverseBits(n) {
  let res = 0;
  for (let i = 0; i < 32; i++) {
    res = (res << 1) | (n & 1);   // append n's lowest bit to res
    n >>>= 1;                     // unsigned shift: no sign bit copied in
  }
  return res >>> 0;               // reinterpret the 32 bits as unsigned
}
''',
    tests=[[43261596], [1], [0], [4294967293], [4294967295], [2147483648], [2], [3], [65535], [2863311530], [123456789], [305419896]],
    examples=2,
    wrong_solutions=[
        "function reverseBits(n) {\n  let res = 0;\n  for (let i = 0; i < 32; i++) { res = (res << 1) | (n & 1); n >>>= 1; }\n  return res;\n}\n",
        "function reverseBits(n) {\n  return parseInt(n.toString(2).split('').reverse().join(''), 2);\n}\n",
    ],
    guide=G(
        prereqs="Left shift, `&`, `|`, and `>>> 0` to read a 32-bit pattern as unsigned (lesson *Pattern map III*).",
        intuition="Peel bits off the right end of `n` one at a time and push each onto the right end of `res`. After 32 steps the first bit peeled has travelled to the top.",
        hints=[
            "`n & 1` reads the lowest bit; `n >>>= 1` drops it.",
            "`res = (res << 1) | bit` appends a bit.",
            "In JavaScript, `res << 1` produces a **signed** 32-bit number. How do you turn it back into unsigned?",
        ],
        brute_force="Convert to a binary string, pad to 32 characters with `padStart(32, \"0\")`, reverse, and `parseInt(..., 2)`. Correct if you remember the padding; forgetting it reverses only the significant bits.",
        approach="1. `res = 0`.\n2. 32 times: `res = (res << 1) | (n & 1)`; `n >>>= 1`.\n3. Return `res >>> 0`.\n\n**Dry run** `n = 1`: the first step puts 1 in `res`; 31 more left shifts move it to bit 31, giving a negative signed value `-2147483648`; `>>> 0` turns it into `2147483648`.",
        complexity="O(32) = O(1) time and space.",
        pitfalls="- Returning `res` without `>>> 0` gives negative answers whenever bit 31 is set.\n- Using `>>` on `n` copies the sign bit for inputs at or above 2^31; it does not matter here because only 32 bits are read, but `>>>` states the intent.\n- `toString(2)` drops leading zeros, so the reversed string is too short.",
        follow_up="If called many times, reverse byte by byte with a 256-entry lookup table.",
    ),
),
dict(
    id="js-sum-of-two-integers", title="Sum of Two Integers", difficulty="Medium", pattern="Bit Manipulation",
    leetcode="https://leetcode.com/problems/sum-of-two-integers/",
    neetcode="https://neetcode.io/problems/sum-of-two-integers",
    kind="js", entry="getSum",
    description=r"""
Return `a + b` **without** using the operators `+` or `-`.

- `-1000 <= a, b <= 1000`

**Example 1:** `a = 1, b = 1` → `2`

**Example 2:** `a = 4, b = 7` → `11`

JavaScript's bitwise operators treat numbers as 32-bit two's-complement integers, which is exactly what makes
negative numbers work here.
""",
    starter="function getSum(a, b) {\n  // no + or - allowed\n}\n",
    solution=r'''function getSum(a, b) {
  while (b !== 0) {
    const carry = (a & b) << 1;   // positions where both have a 1 carry into the next bit
    a = a ^ b;                    // sum without carries
    b = carry;
  }
  return a;
}
''',
    tests=[[1, 1], [4, 7], [0, 0], [-1, 1], [-5, -7], [1000, -1000], [-1000, -1000], [999, 1], [-1, -1], [123, -456], [0, -3], [512, 512]],
    examples=2,
    wrong_solutions=[
        "function getSum(a, b) {\n  return a ^ b;\n}\n",
        "function getSum(a, b) {\n  return a | b;\n}\n",
    ],
    guide=G(
        prereqs="XOR, AND, left shift, and two's complement (lesson *Pattern map III*).",
        intuition="Binary addition per bit: XOR gives the sum bit ignoring carries, and AND shifted left gives the carries. Add those two numbers the same way, repeating until there is no carry left.",
        hints=[
            "What is `1 ^ 1`? What is `1 & 1`?",
            "`a ^ b` = sum without carry; `(a & b) << 1` = carry.",
            "Loop until the carry is 0. In JavaScript the 32-bit operators handle negatives for you.",
        ],
        brute_force="Loops like incrementing `a` by one `b` times still need `+` or `-`; the bit method is the intended answer.",
        approach="1. While `b !== 0`: `carry = (a & b) << 1`; `a = a ^ b`; `b = carry`.\n2. Return `a`.\n\n**Dry run** 4 + 7: `100 ^ 111 = 011`, carry `100 << 1 = 1000`; `0011 ^ 1000 = 1011` (11), carry 0.",
        complexity="At most 32 iterations: O(1).",
        pitfalls="- In Python the same loop runs forever on negatives (unbounded integers need a mask). JavaScript truncates every bitwise result to 32 bits, so the carry eventually shifts out.\n- Inputs beyond the 32-bit range would be silently truncated by the operators.",
        follow_up="Subtract with `getSum(a, getSum(~b, 1))`, since `-b` is `~b + 1` in two's complement.",
    ),
),
dict(
    id="js-missing-number", title="Missing Number", difficulty="Easy", pattern="Bit Manipulation",
    leetcode="https://leetcode.com/problems/missing-number/",
    neetcode="https://neetcode.io/problems/missing-number",
    kind="js", entry="missingNumber",
    description=r"""
`nums` contains `n` distinct numbers taken from `0, 1, ..., n`, so exactly one number of that range is missing.
Return it, using O(1) extra space.

**Example 1:** `[1, 2, 3]` → `0`

**Example 2:** `[0, 2]` → `1`
""",
    starter="function missingNumber(nums) {\n  // your code\n}\n",
    solution=r'''function missingNumber(nums) {
  let x = nums.length;                 // start with n, the index that has no slot
  for (let i = 0; i < nums.length; i++) {
    x ^= i ^ nums[i];                  // pairs cancel: only the missing value survives
  }
  return x;
}
''',
    tests=[[[1, 2, 3]], [[0, 2]], [[0]], [[1]], [[3, 0, 1]], [[9, 6, 4, 2, 3, 5, 7, 0, 1]], [[0, 1, 2, 3]], [[2, 1]],
           [r.sample(range(10001), 10000)], [list(range(1, 5001))]],
    examples=2,
    wrong_solutions=[
        "function missingNumber(nums) {\n  const s = [...nums].sort();\n  for (let i = 0; i < s.length; i++) if (s[i] !== i) return i;\n  return s.length;\n}\n",
        "function missingNumber(nums) {\n  let x = 0;\n  for (let i = 0; i < nums.length; i++) x ^= i ^ nums[i];\n  return x;\n}\n",
    ],
    guide=G(
        prereqs="XOR properties `x ^ x = 0` and `x ^ 0 = x` (lesson *Pattern map III*).",
        intuition="XOR every index 0..n with every value in the array. Every number that is present appears twice (once as an index, once as a value) and cancels; the missing number appears only once and survives.",
        hints=[
            "What is `x ^ x`? And the order of XOR operations?",
            "The indices run 0..n-1; remember to include `n` itself.",
            "Alternatively: `n * (n + 1) / 2 - sum(nums)`.",
        ],
        brute_force="Sort numerically and find the first index where `nums[i] !== i`: O(n log n). Or put everything in a `Set`: O(n) space.",
        approach="1. `x = n`.\n2. For each `i`: `x ^= i ^ nums[i]`.\n3. Return `x`.\n\n**Dry run** `[0, 2]`: x = 2; i=0: 2^0^0 = 2; i=1: 2^1^2 = 1 → 1.",
        complexity="Time O(n), space O(1).",
        pitfalls="- Default `sort()` puts `10` before `2`, so the sorted scan finds the wrong gap once numbers reach two digits.\n- Forgetting to include `n` in the XOR fails when the missing number is `n`.\n- The sum formula is safe here (n <= 10^4), but in general large sums need care with `Number.MAX_SAFE_INTEGER`.",
        follow_up="Find the Duplicate Number and First Missing Positive use the array indices themselves as the hash.",
    ),
),
]
