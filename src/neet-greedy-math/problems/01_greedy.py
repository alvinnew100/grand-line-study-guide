import random

_r = random.Random(150)

# ---------- large-input generators (deterministic) ----------
_big_sub = [_r.randint(-10000, 10000) for _ in range(20000)]
_big_neg = [_r.randint(-10000, -1) for _ in range(5000)]

_jump_ok = [_r.randint(1, 5) for _ in range(20000)]
_jump_trap = [3] * 9000 + [2, 1, 0, 0] + [4] * 9000

_jump2_big = [_r.randint(1, 50) for _ in range(20000)]
_jump2_ones = [1] * 10000

_gas_big = [_r.randint(0, 10000) for _ in range(8000)]
_cost_big = [_r.randint(0, 10000) for _ in range(8000)]
_cost_big[0] = 0
_gas_big[0] = sum(_cost_big) - sum(_gas_big[1:]) + 5  # make total feasible


def _hand_big(ok):
    hand = []
    for _ in range(2000):
        s = _r.randint(0, 10 ** 9 - 10)
        hand.extend(range(s, s + 5))
    _r.shuffle(hand)
    if not ok:
        hand[0] += 1
    return hand


_hand_true = _hand_big(True)
_hand_false = _hand_big(False)

_trip_big = [[_r.randint(1, 1000), _r.randint(1, 1000), _r.randint(1, 1000)] for _ in range(8000)]
_trip_big_t = [700, 800, 900]
_trip_big.append([700, 1, 1])
_trip_big.append([1, 800, 1])
_trip_big.append([1, 1, 900])

_part_big = "".join(chr(97 + i) * 300 + chr(97 + i) for i in range(26)) * 1
_part_rand = "".join(_r.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(5000))

_paren_big_ok = "(" * 5000 + "*" * 5000
_paren_big_bad = "(" * 5001 + "*" * 4999 + ")" * 0
_paren_mix = "".join(_r.choice("(*)") for _ in range(10000))

_bills_big = ([5] * 3 + [10, 20]) * 3000
_bills_big_bad = [5, 5, 10] * 2000 + [20, 20, 20, 20]

_ratings_big = [_r.randint(0, 20000) for _ in range(20000)]
_ratings_mountain = list(range(10000)) + list(range(10000, -1, -1))

_people_big = [_r.randint(1, 30000) for _ in range(20000)]

PROBLEMS = [
# ------------------------------------------------------------------ Kadane
dict(
    id="maximum-subarray",
    title="Maximum Subarray",
    difficulty="Medium",
    pattern="Greedy / Kadane",
    leetcode="https://leetcode.com/problems/maximum-subarray/",
    neetcode="https://neetcode.io/problems/maximum-subarray",
    entry="maxSubArray",
    description=r"""
You are given a non-empty integer array `nums`. A **subarray** is a contiguous, non-empty run of
elements. Return the largest sum that any subarray can have.

**Constraints**
- `1 <= len(nums) <= 10^5`
- `-10^4 <= nums[i] <= 10^4`

**Example 1:** `nums = [-2,1,-3,4,-1,2,1,-5,4]` → `6` (the run `[4,-1,2,1]`).

**Example 2:** `nums = [-3,-7,-1]` → `-1` (the subarray must be non-empty, so with every value
negative the best you can do is the single largest element).
""",
    starter='''class Solution:
    def maxSubArray(self, nums: List[int]) -> int:
        pass
''',
    solution='''class Solution:
    def maxSubArray(self, nums):
        best = cur = nums[0]
        for x in nums[1:]:
            cur = max(x, cur + x)      # extend the running run, or restart at x
            best = max(best, cur)
        return best
''',
    tests=[
        [[-2, 1, -3, 4, -1, 2, 1, -5, 4]],
        [[-3, -7, -1]],
        [[5, 4, -1, 7, 8]],
        [[1]],
        [[-10000]],
        [[0, 0, 0]],
        [[-1, 0, -2]],
        [[8, -19, 5, -4, 20]],
        [[2, -1, 2, -1, 2]],
        [[-2, -1]],
        [_big_sub],
        [_big_neg],
        [[10000] * 10000],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def maxSubArray(self, nums):
        best = cur = 0
        for x in nums:
            cur = max(0, cur + x)
            best = max(best, cur)
        return best
''',
        '''class Solution:
    def maxSubArray(self, nums):
        return sum(x for x in nums if x > 0) or max(nums)
''',
    ],
    guide=dict(
        prereqs="Prefix sums, the idea of a *running* best. See the lesson *When greedy works*.",
        intuition=r"""
Walk left to right keeping `cur` = the best sum of a subarray that **ends at the current index**.
At each new element `x` there are only two choices: glue `x` onto the best run that ended one step
earlier (`cur + x`) or start fresh at `x`. If `cur` has gone negative it can only drag `x` down, so
you throw it away. That local "drop a negative prefix" decision is the greedy step, and the global
answer is the maximum `cur` ever seen.
""",
        hints=[
            "Think about the best subarray that *ends* at index i rather than anywhere.",
            "If the best sum ending at i-1 is negative, is it ever worth extending?",
            "cur = max(x, cur + x); best = max(best, cur). Initialise both with nums[0], not 0.",
        ],
        brute_force=r"""
Try every start `i`, extend `j` from `i` to the end while accumulating a running sum, and track the
maximum. That is **O(n²)** time, O(1) space — about 5·10⁹ steps for `n = 10^5`, far too slow.
(The naive triple loop that re-sums every subarray is O(n³).)
""",
        approach=r"""
**Kadane's algorithm**

1. `best = cur = nums[0]`.
2. For each later `x`: `cur = max(x, cur + x)`, then `best = max(best, cur)`.
3. Return `best`.

**Dry run** on `[-2,1,-3,4,-1,2,1,-5,4]`:

| x | cur (= max(x, cur+x)) | best |
|---|---|---|
| -2 | -2 | -2 |
| 1 | max(1, -1) = 1 | 1 |
| -3 | max(-3, -2) = -2 | 1 |
| 4 | max(4, 2) = 4 | 4 |
| -1 | 3 | 4 |
| 2 | 5 | 5 |
| 1 | 6 | **6** |
| -5 | 1 | 6 |
| 4 | 5 | 6 |

**Why it is correct.** Let `E[i]` be the best sum of a subarray ending exactly at `i`. Any such
subarray is either `[nums[i]]` alone or (a subarray ending at `i-1`) + `nums[i]`, so
`E[i] = max(nums[i], E[i-1] + nums[i])`. The optimum ends *somewhere*, so it equals `max E[i]`.
Kadane is this one-dimensional DP with the table compressed to one variable — which is why it is
often described as both "greedy" and "DP".
""",
        complexity="Time **O(n)** — one pass. Space **O(1)** — two variables.",
        pitfalls=r"""
- Initialising `best = 0` returns 0 for an all-negative array; the subarray must be non-empty.
- Updating `best` *before* `cur` (or forgetting to update it inside the loop) misses the last run.
- Resetting `cur = 0` when it goes negative is fine **only** if `best` was initialised to
  `nums[0]` / `-inf`, and you update `best` before the reset.
""",
        follow_up=r"""
- Return the indices of the best subarray: remember where the current run started whenever you restart.
- Divide-and-conquer O(n log n) version (LeetCode's follow-up): best of left half, right half, and the
  best crossing the middle.
- Related: *Maximum Product Subarray* (track both max and min), *Maximum Sum Circular Subarray*
  (answer = max(kadane, total − min-subarray)).
""",
    ),
),
# ------------------------------------------------------------------ Jump Game
dict(
    id="jump-game",
    title="Jump Game",
    difficulty="Medium",
    pattern="Greedy",
    leetcode="https://leetcode.com/problems/jump-game/",
    neetcode="https://neetcode.io/problems/jump-game",
    entry="canJump",
    description=r"""
You start on index `0` of an array `nums`. The value `nums[i]` is the **maximum** distance you may
jump forward from index `i` (you can also jump any shorter distance, including staying put is not
useful). Decide whether you can land on the last index.

**Constraints**
- `1 <= len(nums) <= 10^4`
- `0 <= nums[i] <= 10^5`

**Example 1:** `nums = [2,3,1,1,4]` → `True` (0 → 1 → 4).

**Example 2:** `nums = [3,2,1,0,4]` → `False` — every route ends up stuck on the `0` at index 3.
""",
    starter='''class Solution:
    def canJump(self, nums: List[int]) -> bool:
        pass
''',
    solution='''class Solution:
    def canJump(self, nums):
        reach = 0
        for i, step in enumerate(nums):
            if i > reach:            # this index can never be reached
                return False
            reach = max(reach, i + step)
        return True
''',
    tests=[
        [[2, 3, 1, 1, 4]],
        [[3, 2, 1, 0, 4]],
        [[0]],
        [[0, 1]],
        [[1, 0]],
        [[2, 0, 0]],
        [[1, 1, 0, 1]],
        [[2, 5, 0, 0]],
        [[1, 2, 0, 0, 1]],
        [[4, 0, 0, 0, 0]],
        [_jump_ok],
        [_jump_trap],
        [[1] * 9999 + [0]],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def canJump(self, nums):
        return 0 not in nums[:-1]
''',
        '''class Solution:
    def canJump(self, nums):
        i = 0
        while i < len(nums) - 1:
            if nums[i] == 0:
                return False
            i += nums[i]          # always take the longest jump
        return True
''',
    ],
    guide=dict(
        prereqs="Arrays; the greedy *frontier* idea from the lesson *Greedy patterns*.",
        intuition=r"""
You do not need to know *which* path to take — only *how far* you could possibly get. Keep `reach`,
the furthest index reachable using any of the indices seen so far. Every index `≤ reach` is
reachable (you could stop there instead), so scan left to right; if you ever stand on an index
beyond `reach`, you are stuck.
""",
        hints=[
            "Is the set of reachable indices always a prefix 0..k of the array? Why?",
            "Track the furthest reachable index while scanning.",
            "If i > reach at any point, return False; otherwise reach = max(reach, i + nums[i]).",
        ],
        brute_force=r"""
DFS/BFS from index 0 trying every jump length — exponential without memo, **O(n·max(nums))** with a
`seen` set or a bottom-up DP `good[i] = any(good[j] for j in i+1..i+nums[i])`. Works, but
`O(n²)` in the worst case.
""",
        approach=r"""
1. `reach = 0`.
2. For each `i`: if `i > reach` → `False`. Else `reach = max(reach, i + nums[i])`.
3. Finishing the loop means the last index was ≤ reach → `True`.

**Dry run** `[3,2,1,0,4]`: i=0 reach=3; i=1 reach=3; i=2 reach=3; i=3 reach=3; i=4 > 3 → **False**.

An equivalent backward greedy: `goal = n-1`; for `i` from `n-2` down to `0`, if
`i + nums[i] >= goal` then `goal = i`. Answer is `goal == 0`.
""",
        complexity="Time **O(n)**, space **O(1)**.",
        pitfalls=r"""
- "Always take the longest jump" is **not** correct: `[2,5,0,0]` — jumping 2 lands on a 0, but
  jumping 1 reaches the 5.
- A single-element array is already at the goal → `True`, even if it is `[0]`.
- Zeros are only fatal if you cannot jump *over* them.
""",
        follow_up="*Jump Game II* (minimum number of jumps), *Jump Game III* (BFS on ±nums[i]), *Jump Game VII* (sliding window).",
    ),
),
# ------------------------------------------------------------------ Jump Game II
dict(
    id="jump-game-ii",
    title="Jump Game II",
    difficulty="Medium",
    pattern="Greedy / implicit BFS",
    leetcode="https://leetcode.com/problems/jump-game-ii/",
    neetcode="https://neetcode.io/problems/jump-game-ii",
    entry="jump",
    description=r"""
Same board as *Jump Game*: from index `i` you may move forward by any distance from `1` to
`nums[i]`. This time the last index is **guaranteed** to be reachable. Return the **fewest** jumps
needed to get from index `0` to index `n-1`.

**Constraints**
- `1 <= len(nums) <= 10^4`
- `0 <= nums[i] <= 1000`, and the last index is reachable.

**Example 1:** `nums = [2,3,1,1,4]` → `2` (0 → 1 → 4).

**Example 2:** `nums = [2,3,0,1,4]` → `2`.
""",
    starter='''class Solution:
    def jump(self, nums: List[int]) -> int:
        pass
''',
    solution='''class Solution:
    def jump(self, nums):
        jumps = 0
        cur_end = 0        # last index reachable with `jumps` jumps
        farthest = 0       # last index reachable with `jumps + 1` jumps
        for i in range(len(nums) - 1):
            farthest = max(farthest, i + nums[i])
            if i == cur_end:          # must jump to go any further
                jumps += 1
                cur_end = farthest
        return jumps
''',
    tests=[
        [[2, 3, 1, 1, 4]],
        [[2, 3, 0, 1, 4]],
        [[0]],
        [[1, 2]],
        [[1, 1, 1, 1]],
        [[5, 1, 1, 1, 1, 1]],
        [[1, 2, 3]],
        [[3, 1, 1, 1, 5, 1, 1, 1, 1]],
        [[2, 1]],
        [[1, 1, 1, 1, 1, 1, 1, 10, 1]],
        [_jump2_big],
        [_jump2_ones],
        [[1000] * 10000],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def jump(self, nums):
        i = jumps = 0
        while i < len(nums) - 1:
            if nums[i] == 0:
                return -1
            i += nums[i]          # always take the biggest jump
            jumps += 1
        return jumps
''',
        '''class Solution:
    def jump(self, nums):
        jumps = cur_end = farthest = 0
        for i in range(len(nums)):          # off by one: also loops on the last index
            farthest = max(farthest, i + nums[i])
            if i == cur_end:
                jumps += 1
                cur_end = farthest
        return jumps
''',
    ],
    guide=dict(
        prereqs="*Jump Game*; breadth-first search levels (BFS) — this is BFS on an implicit graph.",
        intuition=r"""
Think in **layers**. Layer 0 is index 0. Layer 1 is every index reachable in one jump — a contiguous
window `[1, farthest]`. Layer 2 is the window reachable from any index in layer 1, and so on. Because
each layer is a contiguous range, you never need a queue: scan left to right, and whenever you walk
off the end of the current layer you are forced to spend one more jump, and the next layer ends at
the farthest point any index in this layer could reach.
""",
        hints=[
            "Indices reachable with k jumps form a contiguous range. What are its endpoints?",
            "Keep the end of the current range and the farthest index seen while scanning it.",
            "When i reaches cur_end, increment jumps and set cur_end = farthest. Stop before the last index.",
        ],
        brute_force=r"""
DP: `dp[0]=0`, and for each `i` relax `dp[j] = min(dp[j], dp[i]+1)` for `j` in `i+1..i+nums[i]`.
**O(n · max(nums))** ≈ O(n²) time, O(n) space.
""",
        approach=r"""
```
jumps = cur_end = farthest = 0
for i in 0 .. n-2:
    farthest = max(farthest, i + nums[i])
    if i == cur_end: jumps += 1; cur_end = farthest
```

**Dry run** `[2,3,1,1,4]`:
- i=0: farthest=2, i==cur_end(0) → jumps=1, cur_end=2
- i=1: farthest=4
- i=2: farthest=4, i==cur_end(2) → jumps=2, cur_end=4
- loop ends (we do not process i=4). Answer **2**.

**Exchange argument.** Suppose some optimal route's k-th jump lands at index `p`. Our greedy layer
`k` ends at `cur_end ≥ p` (it is the farthest any k-jump route can reach), so anything the optimal
route can do next, the greedy layer can do too. By induction greedy never needs more jumps.
""",
        complexity="Time **O(n)**, space **O(1)**.",
        pitfalls=r"""
- Looping to `n-1` inclusive counts an extra jump when `cur_end` happens to equal `n-1`.
- `[0]` needs **0** jumps.
- "Jump as far as possible" is wrong: `[2,3,1,1,4]` — jumping to index 2 costs 3 jumps total.
""",
        follow_up="Return the actual path (store which index produced `farthest`). *Video Stitching* and *Minimum Number of Taps* are the same layer trick on intervals.",
    ),
),
# ------------------------------------------------------------------ Gas Station
dict(
    id="gas-station",
    title="Gas Station",
    difficulty="Medium",
    pattern="Greedy",
    leetcode="https://leetcode.com/problems/gas-station/",
    neetcode="https://neetcode.io/problems/gas-station",
    entry="canCompleteCircuit",
    checker=r'''
def check(args, got, expected):
    gas, cost = args
    n = len(gas)
    if expected == -1:
        return got == -1
    if not isinstance(got, int) or isinstance(got, bool) or not (0 <= got < n):
        return False
    tank = 0
    for k in range(n):
        i = (got + k) % n
        tank += gas[i] - cost[i]
        if tank < 0:
            return False
    return True
''',
    description=r"""
`n` gas stations sit on a circular road. Station `i` gives you `gas[i]` litres, and driving from
station `i` to station `i+1` (wrapping from `n-1` to `0`) burns `cost[i]` litres. Your car has an
unlimited tank and starts **empty** at a station of your choice.

Return an index from which you can drive all the way around once, clockwise, without the tank going
negative; return `-1` if no start works. (When a start exists it is unique for the official
problem; the judge accepts any valid start.)

**Constraints**
- `1 <= n <= 10^5`, `0 <= gas[i], cost[i] <= 10^4`

**Example 1:** `gas = [1,2,3,4,5], cost = [3,4,5,1,2]` → `3`.

**Example 2:** `gas = [2,3,4], cost = [3,4,3]` → `-1` (total gas 9 < total cost 10).
""",
    starter='''class Solution:
    def canCompleteCircuit(self, gas: List[int], cost: List[int]) -> int:
        pass
''',
    solution='''class Solution:
    def canCompleteCircuit(self, gas, cost):
        if sum(gas) < sum(cost):
            return -1
        start = tank = 0
        for i in range(len(gas)):
            tank += gas[i] - cost[i]
            if tank < 0:          # cannot reach i+1 from `start` (nor from anything in between)
                start = i + 1
                tank = 0
        return start
''',
    tests=[
        [[1, 2, 3, 4, 5], [3, 4, 5, 1, 2]],
        [[2, 3, 4], [3, 4, 3]],
        [[5], [4]],
        [[4], [5]],
        [[0], [0]],
        [[3, 1, 1], [1, 2, 2]],
        [[1, 2], [2, 1]],
        [[5, 1, 2, 3, 4], [4, 4, 1, 5, 1]],
        [[5, 8, 2, 8], [6, 5, 6, 6]],
        [[2, 0, 0, 0], [0, 0, 0, 2]],
        [_gas_big, _cost_big],
        [[1] * 20000, [1] * 19999 + [2]],
        [[0] * 19999 + [20000], [1] * 20000],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def canCompleteCircuit(self, gas, cost):
        if sum(gas) < sum(cost):
            return -1
        return max(range(len(gas)), key=lambda i: gas[i] - cost[i])
''',
        '''class Solution:
    def canCompleteCircuit(self, gas, cost):
        start = tank = 0
        for i in range(len(gas)):
            tank += gas[i] - cost[i]
            if tank < 0:
                start, tank = i + 1, 0
        return start if start < len(gas) else -1   # forgets the total-sum check
''',
    ],
    guide=dict(
        prereqs="Prefix sums; the *restart* style of greedy (same flavour as Kadane).",
        intuition=r"""
Two facts do all the work:

1. If total gas ≥ total cost, *some* start works (pick the station right after the lowest point of the
   running balance — from there the balance never dips below zero).
2. If you start at `s` and first run dry trying to reach `i+1`, then **no** station between `s` and
   `i` can be a valid start either: each of them would arrive at `i` with *less* fuel than you had
   (you reached each of them with a non-negative tank). So jump the candidate to `i+1`.
""",
        hints=[
            "When is the answer definitely -1? Compare two sums.",
            "If you start at s and fail before reaching i+1, can any station in s..i work?",
            "One pass: running tank; on negative, start = i+1 and tank = 0. Return start if totals allow.",
        ],
        brute_force="Simulate the full loop from every start: **O(n²)** time, O(1) space.",
        approach=r"""
```
if sum(gas) < sum(cost): return -1
start = tank = 0
for i: tank += gas[i]-cost[i]; if tank < 0: start, tank = i+1, 0
return start
```

**Dry run** `gas=[1,2,3,4,5]`, `cost=[3,4,5,1,2]` → diffs `[-2,-2,-2,3,3]`:
- i=0 tank=-2 → start=1, tank=0
- i=1 tank=-2 → start=2
- i=2 tank=-2 → start=3
- i=3 tank=3; i=4 tank=6. Totals 15 ≥ 15, so answer **3**.

Why don't we need to check the wrap-around part from `start` back to `start-1`? Because the total
is non-negative and the stretch `[start, n-1]` has a non-negative sum, the remaining prefix
`[0, start-1]` is covered by the surplus — formally, the prefix sum hits its minimum just before
`start`.
""",
        complexity="Time **O(n)**, space **O(1)**.",
        pitfalls=r"""
- Forgetting the global `sum(gas) < sum(cost)` test returns a bogus index.
- Choosing the station with the largest `gas[i]-cost[i]` is a tempting but wrong heuristic.
- Resetting `tank` without moving `start` (or vice versa).
""",
        follow_up="Equivalent formulation: answer is (index of the minimum prefix sum) + 1 mod n. Related: *Maximum Sum Circular Subarray*.",
    ),
),
# ------------------------------------------------------------------ Hand of Straights
dict(
    id="hand-of-straights",
    title="Hand of Straights",
    difficulty="Medium",
    pattern="Greedy + hash map",
    leetcode="https://leetcode.com/problems/hand-of-straights/",
    neetcode="https://neetcode.io/problems/hand-of-straights",
    entry="isNStraightHand",
    description=r"""
Alice holds cards with integer values `hand`. She wants to split **all** of them into groups of
exactly `groupSize` cards where each group is a run of consecutive values (like `4,5,6`). Return
`True` if such a split exists.

**Constraints**
- `1 <= len(hand) <= 10^4`, `0 <= hand[i] <= 10^9`, `1 <= groupSize <= len(hand)`

**Example 1:** `hand = [1,2,3,6,2,3,4,7,8], groupSize = 3` → `True` (`[1,2,3] [2,3,4] [6,7,8]`).

**Example 2:** `hand = [1,2,3,4,5], groupSize = 4` → `False` (5 cards cannot form groups of 4).
""",
    starter='''class Solution:
    def isNStraightHand(self, hand: List[int], groupSize: int) -> bool:
        pass
''',
    solution='''class Solution:
    def isNStraightHand(self, hand, groupSize):
        if len(hand) % groupSize:
            return False
        count = collections.Counter(hand)
        for start in sorted(count):
            k = count[start]
            if k == 0:
                continue
            # the smallest remaining card MUST start k groups
            for v in range(start, start + groupSize):
                if count[v] < k:
                    return False
                count[v] -= k
        return True
''',
    tests=[
        [[1, 2, 3, 6, 2, 3, 4, 7, 8], 3],
        [[1, 2, 3, 4, 5], 4],
        [[1], 1],
        [[5, 5, 5], 1],
        [[1, 2, 3, 4, 5, 6], 2],
        [[1, 1, 2, 2, 3, 3], 3],
        [[1, 2, 4, 5, 6, 7], 3],
        [[1, 1, 2, 3], 2],
        [[8, 10, 12], 3],
        [[0, 0, 1, 1, 2, 2, 2, 3, 4], 3],
        [[3, 2, 1, 2, 3, 4, 3, 4, 5, 9, 10, 11], 3],
        [_hand_true, 5],
        [_hand_false, 5],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def isNStraightHand(self, hand, groupSize):
        return len(hand) % groupSize == 0
''',
        '''class Solution:
    def isNStraightHand(self, hand, groupSize):
        if len(hand) % groupSize:
            return False
        s = sorted(set(hand))
        # only checks that distinct values are consecutive in blocks
        return all(s[i + 1] - s[i] == 1 for i in range(len(s) - 1)) or groupSize == 1
''',
    ],
    guide=dict(
        prereqs="Hash maps / `Counter`, sorting.",
        intuition=r"""
Look at the **smallest** card value still in the hand. Nothing smaller exists, so it cannot sit in
the middle or end of a run — it *must* be the first card of a group. If it appears `k` times, it
starts `k` groups, which consume `k` copies of each of the next `groupSize-1` values. Repeat. Every
step is forced, so if any step fails the answer is `False`.
""",
        hints=[
            "Quick reject: what must be true of len(hand) and groupSize?",
            "Which card can only ever be the *start* of a group?",
            "Count with a Counter, visit values in sorted order, and subtract count[start] from each value in the run.",
        ],
        brute_force="Repeatedly sort, take the minimum, and remove `start..start+g-1` from a list one by one — O(n²) list removals.",
        approach=r"""
1. If `len(hand) % groupSize != 0` → `False`.
2. `count = Counter(hand)`; iterate `start` over `sorted(count)`.
3. If `count[start] = k > 0`, for each `v` in `start..start+g-1` require `count[v] ≥ k` and subtract `k`.

**Dry run** `[1,2,3,6,2,3,4,7,8]`, g=3: counts `{1:1,2:2,3:2,4:1,6:1,7:1,8:1}`.
- start 1 (k=1): take 1,2,3 → `{2:1,3:1,4:1,...}`
- start 2 (k=1): take 2,3,4 → all zero
- 3, 4 skipped (k=0); start 6: take 6,7,8. → **True**.

Processing a whole batch of `k` groups at once keeps it fast even with many duplicates.
""",
        complexity="Time **O(n log n)**: sorting the distinct values dominates; the subtraction work totals O(n) because every card is consumed once per group it belongs to (each inner step removes at least one card, or fails). Space O(n) for the counter.",
        pitfalls=r"""
- Checking only that the distinct values are consecutive ignores multiplicities.
- Using a min-heap and popping the wrong element when duplicates exist — the batch (`k`) approach avoids that.
- `groupSize == 1` is always `True`.
""",
        follow_up="Identical problem: *Divide Array in Sets of K Consecutive Numbers* (LC 1296). Harder cousin: *Split Array into Consecutive Subsequences* (runs of length ≥ 3).",
    ),
),
# ------------------------------------------------------------------ Merge Triplets
dict(
    id="merge-triplets-to-form-target-triplet",
    title="Merge Triplets to Form Target Triplet",
    difficulty="Medium",
    pattern="Greedy",
    leetcode="https://leetcode.com/problems/merge-triplets-to-form-target-triplet/",
    neetcode="https://neetcode.io/problems/merge-triplets-to-form-target",
    entry="mergeTriplets",
    description=r"""
You have a list of `triplets`, each `[a, b, c]`, and a `target = [x, y, z]`. One operation picks two
triplets `i` and `j` and overwrites triplet `j` with the element-wise maximum
`[max(a_i,a_j), max(b_i,b_j), max(c_i,c_j)]`. You may do any number of operations. Return `True`
if `target` can appear as one of the triplets.

**Constraints**
- `1 <= len(triplets) <= 10^5`, all values in `1..1000`.

**Example 1:** `triplets = [[2,5,3],[1,8,4],[1,7,5]], target = [2,7,5]` → `True`
(merge the 1st and 3rd).

**Example 2:** `triplets = [[3,4,5],[4,5,6]], target = [3,2,5]` → `False`.
""",
    starter='''class Solution:
    def mergeTriplets(self, triplets: List[List[int]], target: List[int]) -> bool:
        pass
''',
    solution='''class Solution:
    def mergeTriplets(self, triplets, target):
        x, y, z = target
        got = [False, False, False]
        for a, b, c in triplets:
            if a > x or b > y or c > z:
                continue          # using this triplet would overshoot forever
            got[0] |= a == x
            got[1] |= b == y
            got[2] |= c == z
        return all(got)
''',
    tests=[
        [[[2, 5, 3], [1, 8, 4], [1, 7, 5]], [2, 7, 5]],
        [[[3, 4, 5], [4, 5, 6]], [3, 2, 5]],
        [[[2, 5, 3], [2, 3, 4], [1, 2, 5], [5, 2, 3]], [5, 5, 5]],
        [[[1, 1, 1]], [1, 1, 1]],
        [[[1, 1, 1]], [2, 2, 2]],
        [[[5, 1, 1], [1, 5, 1]], [5, 5, 1]],
        [[[5, 1, 9], [1, 5, 1], [1, 1, 5]], [5, 5, 5]],
        [[[1, 2, 3], [3, 2, 1]], [3, 2, 3]],
        [[[7, 7, 7]], [7, 7, 6]],
        [[[2, 2, 2], [2, 2, 2]], [2, 2, 2]],
        [_trip_big, _trip_big_t],
        [[[1, 1, 1]] * 15000 + [[2, 2, 3]], [2, 2, 2]],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def mergeTriplets(self, triplets, target):
        got = [False] * 3
        for t in triplets:
            for k in range(3):
                if t[k] == target[k]:
                    got[k] = True          # forgets to discard overshooting triplets
        return all(got)
''',
        '''class Solution:
    def mergeTriplets(self, triplets, target):
        return target in triplets
''',
    ],
    guide=dict(
        prereqs="None beyond loops — a nice example of *filter then combine* greedy.",
        intuition=r"""
`max` can only make numbers bigger. So any triplet with **some** coordinate larger than the target's
is poison: merging it in would push that coordinate past the target permanently. Throw those away.
Among the safe triplets, merging *all* of them is harmless (nothing exceeds the target) and gives the
largest possible result; the target is reachable iff each coordinate of the target is hit exactly by
some safe triplet.
""",
        hints=[
            "Can a coordinate ever decrease after a merge?",
            "Discard every triplet that exceeds the target in any position.",
            "Among the rest, check that each of x, y, z is matched by at least one triplet.",
        ],
        brute_force="Try every subset of triplets and take its element-wise max — O(2ⁿ).",
        approach=r"""
Scan once. Skip `[a,b,c]` if `a>x or b>y or c>z`. Otherwise set `found[0] |= a==x`, etc.
Return `all(found)`.

**Dry run** `[[2,5,3],[1,8,4],[1,7,5]]`, target `[2,7,5]`:
- `[2,5,3]` safe → found x.
- `[1,8,4]` 8 > 7 → skip.
- `[1,7,5]` safe → found y, z. → **True**.
""",
        complexity="Time **O(n)**, space **O(1)**.",
        pitfalls=r"""
- Not filtering out overshooting triplets (they would match `x` but ruin `y`).
- Requiring a single triplet to equal the target — merges combine several.
""",
        follow_up="Generalises to k-tuples unchanged. Compare with *Bitwise OR* subset problems where the same \"only safe items\" filter applies.",
    ),
),
# ------------------------------------------------------------------ Partition Labels
dict(
    id="partition-labels",
    title="Partition Labels",
    difficulty="Medium",
    pattern="Greedy / intervals",
    leetcode="https://leetcode.com/problems/partition-labels/",
    neetcode="https://neetcode.io/problems/partition-labels",
    entry="partitionLabels",
    description=r"""
Cut the lowercase string `s` into as **many** contiguous pieces as possible such that every letter
appears in at most one piece. Return the lengths of the pieces in order (they sum to `len(s)`).

**Constraints**
- `1 <= len(s) <= 500` on LeetCode (tests here go larger), lowercase letters only.

**Example 1:** `s = "ababcbacadefegdehijhklij"` → `[9,7,8]`
(`"ababcbaca" | "defegde" | "hijhklij"`).

**Example 2:** `s = "eccbbbbdec"` → `[10]`.
""",
    starter='''class Solution:
    def partitionLabels(self, s: str) -> List[int]:
        pass
''',
    solution='''class Solution:
    def partitionLabels(self, s):
        last = {ch: i for i, ch in enumerate(s)}
        out = []
        start = end = 0
        for i, ch in enumerate(s):
            end = max(end, last[ch])     # this piece must stretch at least this far
            if i == end:                 # nothing inside reaches further: cut here
                out.append(end - start + 1)
                start = i + 1
        return out
''',
    tests=[
        ["ababcbacadefegdehijhklij"],
        ["eccbbbbdec"],
        ["a"],
        ["abc"],
        ["aaaa"],
        ["abca"],
        ["abab"],
        ["caedbdedda"],
        ["qiejxqfnqceocmy"],
        ["abcdefghijklmnopqrstuvwxyz" * 3],
        [_part_big],
        [_part_rand],
        ["".join(chr(97 + i % 26) * 7 for i in range(26)) * 1],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def partitionLabels(self, s):
        out, start = [], 0
        for i in range(1, len(s) + 1):
            if i == len(s) or s[i] != s[i - 1]:
                out.append(i - start)
                start = i
        return out
''',
        '''class Solution:
    def partitionLabels(self, s):
        last = {ch: i for i, ch in enumerate(s)}
        out, start = [], 0
        for i, ch in enumerate(s):
            if i == last[ch]:          # only looks at the current letter, not the running max
                out.append(i - start + 1)
                start = i + 1
        return out
''',
    ],
    guide=dict(
        prereqs="Hash maps; *merging intervals* — each letter defines an interval [first, last].",
        intuition=r"""
Each letter occupies an interval from its first to its last occurrence. A piece that contains a letter
must contain that letter's whole interval. So start a piece, and as you scan, keep pushing its right
edge to the furthest last-occurrence of any letter seen inside it. When the scan index catches up with
that edge, nothing inside the piece reaches further — cut. Cutting at the earliest legal point is the
greedy choice that maximises the number of pieces.
""",
        hints=[
            "Precompute the last index of every letter.",
            "Track the furthest last-index among letters in the current piece.",
            "When i equals that furthest index, close the piece and record its length.",
        ],
        brute_force="For each candidate cut point, verify no letter appears on both sides by scanning — O(n²) (or O(26·n) with prefix counts).",
        approach=r"""
1. `last[ch]` = last index of each character.
2. `start = end = 0`. For each `i`: `end = max(end, last[s[i]])`; if `i == end`, append
   `end-start+1`, `start = i+1`.

**Dry run** `"eccbbbbdec"`: last = `{e:8, c:9, b:6, d:7}`. i=0 end=8; i=1 end=9; … never `i==end` until
i=9 → `[10]`.
""",
        complexity="Time **O(n)**; space **O(1)** extra (26 letters) plus the output.",
        pitfalls=r"""
- Cutting when the *current* letter ends, instead of when the running maximum ends.
- Off-by-one in the length (`end - start + 1`).
""",
        follow_up="Same as *merge intervals* on the 26 letter intervals. Variant: return the pieces themselves.",
    ),
),
# ------------------------------------------------------------------ Valid Parenthesis String
dict(
    id="valid-parenthesis-string",
    title="Valid Parenthesis String",
    difficulty="Medium",
    pattern="Greedy (range of open counts)",
    leetcode="https://leetcode.com/problems/valid-parenthesis-string/",
    neetcode="https://neetcode.io/problems/valid-parenthesis-string",
    entry="checkValidString",
    description=r"""
The string `s` contains only `'('`, `')'` and `'*'`. Each `'*'` is a wildcard that you may read as
`'('`, as `')'`, or as nothing. Return `True` if some choice of wildcards makes `s` a balanced
parenthesis string (every `'('` is closed by a later `')'` and no `')'` is unmatched). The empty
string counts as balanced.

**Constraints**
- `1 <= len(s) <= 100` on LeetCode (tests here go up to 10^4).

**Example 1:** `s = "(*)"` → `True`.

**Example 2:** `s = "(*))"` → `True` (read `*` as `(`). `s = ")*("` → `False`.
""",
    starter='''class Solution:
    def checkValidString(self, s: str) -> bool:
        pass
''',
    solution='''class Solution:
    def checkValidString(self, s):
        lo = hi = 0     # min / max possible number of unmatched '('
        for ch in s:
            if ch == "(":
                lo += 1; hi += 1
            elif ch == ")":
                lo -= 1; hi -= 1
            else:
                lo -= 1; hi += 1
            if hi < 0:          # too many ')' even if every * is '('
                return False
            lo = max(lo, 0)     # a negative count is never a real choice
        return lo == 0
''',
    tests=[
        ["(*)"],
        ["(*))"],
        [")*("],
        ["()"],
        ["*"],
        ["(("],
        ["(*"],
        ["*)"],
        ["**(("],
        ["(((******))"],
        ["(())((())()()(*)(*()(())())())()()((()())((()))(*"],
        [_paren_big_ok],
        [_paren_big_bad],
        [_paren_mix],
        ["(*)" * 3000 + ")"],
    ],
    examples=3,
    wrong_solutions=[
        '''class Solution:
    def checkValidString(self, s):
        return s.count("(") <= s.count(")") + s.count("*") and s.count(")") <= s.count("(") + s.count("*")
''',
        '''class Solution:
    def checkValidString(self, s):
        lo = hi = 0
        for ch in s:
            lo += 1 if ch == "(" else -1
            hi += -1 if ch == ")" else 1
            if hi < 0:
                return False
        return lo <= 0        # never clamps lo, so "*(" style cases slip through
''',
    ],
    guide=dict(
        prereqs="The balance-counter check for ordinary parentheses; *Valid Parentheses*.",
        intuition=r"""
For plain parentheses you track a single balance (open count). With wildcards the balance is no
longer a single number — it is a **range** `[lo, hi]` of possible open counts after each prefix.
`'('` shifts the range up, `')'` shifts it down, `'*'` widens it by one in both directions. If even
`hi` drops below zero, too many `')'` exist. A negative `lo` would correspond to an invalid choice, so
clamp it to 0. At the end, a valid string needs 0 to be in the range, i.e. `lo == 0`.
""",
        hints=[
            "With only ( and ), one counter suffices. What does a * do to that counter?",
            "Track the minimum and maximum possible number of unmatched '('.",
            "Fail if hi < 0; clamp lo at 0; answer is lo == 0.",
        ],
        brute_force=r"""
Try all `3^k` interpretations of the `k` wildcards — exponential. A memoised DP on `(index, balance)`
is **O(n²)** time and space and is a perfectly good interview answer before the greedy.
""",
        approach=r"""
**Dry run** `"(*))"`:

| ch | lo | hi |
|---|---|---|
| ( | 1 | 1 |
| * | 0 | 2 |
| ) | -1→0 | 1 |
| ) | -1→0 | 0 |

`hi` never went negative and `lo == 0` → **True**.

Why clamping is safe: the set of reachable balances is always a contiguous range (wildcards can
take any of three values), so representing it by its endpoints loses nothing; balances below 0 are
illegal and simply removed.

An alternative is **two stacks** (indices of `'('` and of `'*'`): match each `')'` with an open
paren first, else a star; at the end, pair remaining `'('` with stars that come *after* them.
""",
        complexity="Time **O(n)**, space **O(1)** (greedy) — O(n) for the two-stack version.",
        pitfalls=r"""
- Only comparing total counts ignores order: `")*("` has balanced counts but is invalid.
- Forgetting to clamp `lo` makes `"*("`-type strings look valid.
- Returning `lo <= 0` instead of `lo == 0` after clamping is equivalent, but without clamping it is wrong.
""",
        follow_up="*Minimum Add to Make Parentheses Valid*, *Minimum Remove to Make Valid Parentheses*, *Longest Valid Parentheses*.",
    ),
),
# ------------------------------------------------------------------ Lemonade Change (extra)
dict(
    id="lemonade-change",
    title="Lemonade Change",
    difficulty="Easy",
    pattern="Greedy",
    leetcode="https://leetcode.com/problems/lemonade-change/",
    entry="lemonadeChange",
    description=r"""
A lemonade costs `$5`. Customers arrive in the order given by `bills`, each paying with one `$5`,
`$10` or `$20` bill, and each must receive correct change immediately. You start with no money.
Return `True` if you can give everyone correct change.

**Constraints**
- `1 <= len(bills) <= 10^5`, each bill is 5, 10 or 20.

**Example 1:** `bills = [5,5,5,10,20]` → `True`.

**Example 2:** `bills = [5,5,10,10,20]` → `False` (for the `$20` you hold two `$10` but no `$5`).
""",
    starter='''class Solution:
    def lemonadeChange(self, bills: List[int]) -> bool:
        pass
''',
    solution='''class Solution:
    def lemonadeChange(self, bills):
        fives = tens = 0
        for b in bills:
            if b == 5:
                fives += 1
            elif b == 10:
                if not fives:
                    return False
                fives -= 1; tens += 1
            else:
                if tens and fives:          # prefer spending the less flexible $10
                    tens -= 1; fives -= 1
                elif fives >= 3:
                    fives -= 3
                else:
                    return False
        return True
''',
    tests=[
        [[5, 5, 5, 10, 20]],
        [[5, 5, 10, 10, 20]],
        [[5]],
        [[10]],
        [[20]],
        [[5, 10]],
        [[5, 5, 10, 20, 5, 5, 5, 5, 5, 5, 5, 5, 5, 10, 5, 5, 20, 5, 20, 5]],
        [[5, 5, 5, 5, 10, 5, 10, 10, 10, 20]],
        [[5, 10, 5, 20]],
        [[5, 5, 5, 5, 10, 20, 10, 10]],
        [[5, 5, 5, 20, 5, 10]],
        [_bills_big],
        [_bills_big_bad],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def lemonadeChange(self, bills):
        fives = tens = 0
        for b in bills:
            if b == 5:
                fives += 1
            elif b == 10:
                if not fives: return False
                fives -= 1; tens += 1
            else:
                if fives >= 3: fives -= 3          # spends $5s first: wasteful
                elif tens and fives: tens -= 1; fives -= 1
                else: return False
        return True
''',
        '''class Solution:
    def lemonadeChange(self, bills):
        return sum(bills) >= 5 * len(bills) and bills[0] == 5
''',
    ],
    guide=dict(
        prereqs="Counting; the *keep your options open* style of greedy.",
        intuition=r"""
Only `$5` and `$10` bills are ever useful as change (nobody needs change in `$20`s). A `$5` can help
any future customer; a `$10` only helps `$20` payers. So when a `$20` arrives and you can pay with
either `10+5` or `5+5+5`, spend the `$10` — it keeps the more flexible `$5` bills in your drawer.
""",
        hints=[
            "Do you ever need to remember how many $20 bills you hold?",
            "For a $20, which combination of change keeps you more flexible later?",
            "Prefer 10+5; fall back to 5+5+5; otherwise fail.",
        ],
        brute_force="Try every way to make change for each $20 (two options) — exponential branching, though the greedy shows it is unnecessary.",
        approach=r"""
Keep counters `fives`, `tens`. `$5` → `fives += 1`. `$10` → need a five. `$20` → use `10+5` if
possible, else `5+5+5`, else `False`.

**Exchange argument.** Suppose an optimal strategy pays some `$20` with `5+5+5` while a `$10` was
available. Swap: pay `10+5` instead. Compared with the original strategy you now hold
two more `$5` bills and one fewer `$10`. Any later change the `$10` would have provided, two `$5`
bills can provide too, so the swapped strategy never gets stuck where the original did not.
""",
        complexity="Time **O(n)**, space **O(1)**.",
        pitfalls="Spending three `$5`s first when a `$10` is available fails `[5,5,5,5,10,20,10,10]`: the `$20` eats three fives, leaving none for the next `$10`. Also: you never need to track `$20` bills.",
        follow_up="Classic **coin change** greedy only works for *canonical* coin systems (e.g. 1,5,10,25); with coins 1,3,4 and amount 6 greedy gives 4+1+1 instead of 3+3 — see the lesson.",
    ),
),
# ------------------------------------------------------------------ Candy (extra)
dict(
    id="candy",
    title="Candy",
    difficulty="Hard",
    pattern="Greedy (two passes)",
    leetcode="https://leetcode.com/problems/candy/",
    entry="candy",
    description=r"""
Children stand in a line; child `i` has a score `ratings[i]`. Hand out candy so that

- every child gets at least one candy, and
- any child whose score is **strictly higher** than an immediate neighbour gets more candy than
  that neighbour.

Return the minimum total number of candies.

**Constraints**
- `1 <= n <= 2·10^4`, `0 <= ratings[i] <= 2·10^4`

**Example 1:** `ratings = [1,0,2]` → `5` (candies `[2,1,2]`).

**Example 2:** `ratings = [1,2,2]` → `4` (candies `[1,2,1]` — equal neighbours have no constraint).
""",
    starter='''class Solution:
    def candy(self, ratings: List[int]) -> int:
        pass
''',
    solution='''class Solution:
    def candy(self, ratings):
        n = len(ratings)
        c = [1] * n
        for i in range(1, n):                 # satisfy the left-neighbour rule
            if ratings[i] > ratings[i - 1]:
                c[i] = c[i - 1] + 1
        for i in range(n - 2, -1, -1):        # satisfy the right-neighbour rule
            if ratings[i] > ratings[i + 1]:
                c[i] = max(c[i], c[i + 1] + 1)
        return sum(c)
''',
    tests=[
        [[1, 0, 2]],
        [[1, 2, 2]],
        [[5]],
        [[1, 2, 3, 4, 5]],
        [[5, 4, 3, 2, 1]],
        [[3, 3, 3]],
        [[1, 3, 2, 2, 1]],
        [[1, 2, 87, 87, 87, 2, 1]],
        [[1, 3, 4, 5, 2]],
        [[0, 1, 2, 5, 3, 2, 7]],
        [_ratings_big],
        [_ratings_mountain],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def candy(self, ratings):
        n = len(ratings)
        c = [1] * n
        for i in range(1, n):
            if ratings[i] > ratings[i - 1]:
                c[i] = c[i - 1] + 1
        return sum(c)
''',
        '''class Solution:
    def candy(self, ratings):
        n = len(ratings)
        c = [1] * n
        for i in range(1, n):
            if ratings[i] > ratings[i - 1]:
                c[i] = c[i - 1] + 1
        for i in range(n - 2, -1, -1):
            if ratings[i] > ratings[i + 1]:
                c[i] = c[i + 1] + 1          # overwrites instead of taking the max
        return sum(c)
''',
    ],
    guide=dict(
        prereqs="Array passes from both ends (like *Product of Array Except Self*).",
        intuition=r"""
The constraints split into two independent families: "beat your **left** neighbour" and "beat your
**right** neighbour". A left-to-right pass gives the minimum satisfying the first family (each
child gets one more than the left neighbour on an ascent, else 1). A right-to-left pass does the same
for the second family. Taking the **max** of the two at every index satisfies both, and it is minimal
because each child's count is forced to be at least each value separately.
""",
        hints=[
            "Handle the left-neighbour condition alone first. What is the minimum then?",
            "Do the same from the right.",
            "Combine with max at each index and sum.",
        ],
        brute_force="Start everyone at 1 and repeatedly sweep fixing violations until nothing changes — O(n²) worst case (a long descending run fixes one child per sweep).",
        approach=r"""
**Dry run** `[1,3,2,2,1]`:
- left pass: `[1,2,1,1,1]`
- right pass (with max): i=3: 2>1 → max(1,2)=2; i=2: 2>2? no; i=1: 3>2 → max(2,2)=2; i=0: no.
  → `[1,2,1,2,1]`, sum **7**.

There is also an O(1)-space one-pass solution that counts lengths of ascending and descending
slopes, but the two-pass version is the one to present first.
""",
        complexity="Time **O(n)**, space **O(n)**.",
        pitfalls=r"""
- One pass only handles one direction.
- Assigning `c[i] = c[i+1] + 1` in the second pass can *lower* a value set by the first pass (peak cases).
- Equal ratings impose no constraint at all.
""",
        follow_up="O(1)-space slope counting; circular arrangement variant.",
    ),
),
# ------------------------------------------------------------------ Boats (extra)
dict(
    id="boats-to-save-people",
    title="Boats to Save People",
    difficulty="Medium",
    pattern="Greedy + two pointers",
    leetcode="https://leetcode.com/problems/boats-to-save-people/",
    entry="numRescueBoats",
    description=r"""
`people[i]` is the weight of person `i`. Each boat carries **at most two** people whose combined
weight is at most `limit`. Every person weighs at most `limit`. Return the minimum number of boats
needed to carry everyone.

**Constraints**
- `1 <= len(people) <= 5·10^4`, `1 <= people[i] <= limit <= 3·10^4`

**Example 1:** `people = [3,2,2,1], limit = 3` → `3` (`(1,2)`, `(2)`, `(3)`).

**Example 2:** `people = [3,5,3,4], limit = 5` → `4`.
""",
    starter='''class Solution:
    def numRescueBoats(self, people: List[int], limit: int) -> int:
        pass
''',
    solution='''class Solution:
    def numRescueBoats(self, people, limit):
        p = sorted(people)
        i, j = 0, len(p) - 1
        boats = 0
        while i <= j:
            if p[i] + p[j] <= limit:   # the lightest can ride with the heaviest
                i += 1
            j -= 1                     # the heaviest always leaves now
            boats += 1
        return boats
''',
    tests=[
        [[3, 2, 2, 1], 3],
        [[3, 5, 3, 4], 5],
        [[1, 2], 3],
        [[5], 5],
        [[1, 1, 1, 1], 2],
        [[2, 2, 2, 2], 3],
        [[1, 5, 3, 5], 7],
        [[2, 49, 10, 7, 11, 41, 47, 2, 22, 6, 13, 12, 33, 18, 10, 26, 2, 6, 50, 10], 50],
        [[3, 8, 7, 1, 4], 9],
        [[1, 2, 2, 3], 4],
        [_people_big, 30000],
        [[15000] * 20000, 30000],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def numRescueBoats(self, people, limit):
        p = sorted(people)
        boats, i = 0, 0
        while i < len(p):          # pairs adjacent people after sorting
            if i + 1 < len(p) and p[i] + p[i + 1] <= limit:
                i += 2
            else:
                i += 1
            boats += 1
        return boats
''',
        '''class Solution:
    def numRescueBoats(self, people, limit):
        return (len(people) + 1) // 2
''',
    ],
    guide=dict(
        prereqs="Sorting, two pointers.",
        intuition=r"""
Consider the **heaviest** person. They need a boat anyway. The best partner for them is the
**lightest** person: if even the lightest cannot fit, nobody can, so the heaviest rides alone. If the
lightest fits, pairing them is never worse than any other pairing (exchange argument: swap the
lightest into the heaviest's boat and whoever was there into the lightest's old spot — weights only
go down).
""",
        hints=[
            "Sort the weights.",
            "Who is the best possible partner for the heaviest remaining person?",
            "Two pointers: if p[i]+p[j] <= limit move i; always move j; count a boat.",
        ],
        brute_force="Try all perfect matchings / pairings — exponential; or O(n²) by searching for the best partner each time.",
        approach=r"""
Sort, `i=0, j=n-1`. While `i <= j`: if `p[i]+p[j] <= limit`, `i += 1`; then `j -= 1`, `boats += 1`.

**Dry run** `[1,2,2,3]`, limit 3: (1,3)? 4>3 → 3 alone (boats 1); (1,2) fits (2); `[2]` alone (3). **3**.
""",
        complexity="Time **O(n log n)** for sorting (counting sort gives O(n + limit)); space O(n) for the sorted copy.",
        pitfalls=r"""
- Pairing *adjacent* people after sorting is not optimal: `[1,2,3,4]` with limit 5 → adjacent pairing
  gives `(1,2),(3),(4)` = 3 boats, but `(1,4),(2,3)` needs only 2.
- Loop condition must be `i <= j` so the last single person is counted.
""",
        follow_up="With more than two seats per boat the problem becomes bin packing, which is NP-hard — greedy is then only an approximation.",
    ),
),
]
