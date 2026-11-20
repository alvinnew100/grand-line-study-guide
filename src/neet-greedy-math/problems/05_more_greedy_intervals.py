import random

_r = random.Random(455)

_greed_big = [_r.randint(1, 10 ** 6) for _ in range(8000)]
_cookie_big = [_r.randint(1, 10 ** 6) for _ in range(8000)]
_boxes_big = [[_r.randint(1, 1000), _r.randint(1, 1000)] for _ in range(1000)]
_costs_big = [[_r.randint(1, 1000), _r.randint(1, 1000)] for _ in range(100)]
_costs_big2 = [[_r.randint(1, 1000), _r.randint(1, 1000)] for _ in range(1000)]


def _queue(n):
    """Build a valid (h, k) list from a random line of people."""
    line = [_r.randint(1, 50) for _ in range(n)]
    out = []
    for i, h in enumerate(line):
        out.append([h, sum(1 for x in line[:i] if x >= h)])
    _r.shuffle(out)
    return out


_queue_big = _queue(600)
_senate_big = "".join(_r.choice("RD") for _ in range(10000))
_wiggle_big = [_r.randint(0, 1000) for _ in range(10000)]
_largest_big = [_r.randint(0, 10 ** 9) for _ in range(100)]
_balloons_big = [[s, s + _r.randint(0, 2000)] for s in (_r.randint(-10 ** 6, 10 ** 6) for _ in range(8000))]


def _disjoint(n):
    out, x = [], 0
    for _ in range(n):
        x += _r.randint(1, 6)
        L = _r.randint(0, 6)
        out.append([x, x + L])
        x += L
    return out


_ila, _ilb = _disjoint(3000), _disjoint(3000)


def _cal_ops(n, span):
    ops, args = ["MyCalendar"], [[]]
    for _ in range(n):
        s = _r.randint(0, span)
        ops.append("book")
        args.append([s, s + _r.randint(1, 30)])
    return [ops, args]


_cal_big = _cal_ops(1000, 5000)
_trips_big = []
for _ in range(1000):
    a = _r.randint(0, 990)
    _trips_big.append([_r.randint(1, 5), a, _r.randint(a + 1, 1000)])

_summary_big = sorted(_r.sample(range(-20000, 20000), 12000))

PROBLEMS = [
# ================================================================== GREEDY
dict(
    id="assign-cookies",
    title="Assign Cookies",
    difficulty="Easy",
    pattern="Greedy + sorting",
    leetcode="https://leetcode.com/problems/assign-cookies/",
    entry="findContentChildren",
    description=r"""
Each child `i` has a *greed factor* `g[i]`: the smallest cookie size that will satisfy them. Each
cookie `j` has a size `s[j]`. A child gets at most one cookie, a cookie goes to at most one child,
and child `i` is content only if their cookie has size `>= g[i]`. Return the largest number of
children you can make content.

**Constraints**
- `1 <= len(g) <= 3·10^4`, `0 <= len(s) <= 3·10^4`, values between `1` and `2^31 - 1`

**Example 1:** `g = [1,2,3], s = [1,1]` → `1` (only the child with greed 1 can be satisfied).

**Example 2:** `g = [1,2], s = [1,2,3]` → `2`.
""",
    starter='''class Solution:
    def findContentChildren(self, g: List[int], s: List[int]) -> int:
        pass
''',
    solution='''class Solution:
    def findContentChildren(self, g, s):
        g, s = sorted(g), sorted(s)
        child = 0
        for cookie in s:                      # smallest cookie first
            if child < len(g) and cookie >= g[child]:
                child += 1                    # it satisfies the least greedy unsatisfied child
        return child
''',
    tests=[
        [[1, 2, 3], [1, 1]],
        [[1, 2], [1, 2, 3]],
        [[5], []],
        [[1], [1]],
        [[2], [1]],
        [[10, 9, 8, 7], [5, 6, 7, 8]],
        [[1, 1, 1], [1]],
        [[3, 1, 2], [2, 2, 2]],
        [[1, 2, 3], [3]],
        [[7, 8, 9, 10], [5, 6, 7, 8]],
        [[2147483647], [2147483647]],
        [_greed_big, _cookie_big],
        [[1] * 5000, [1] * 3000],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def findContentChildren(self, g, s):
        return sum(1 for a, b in zip(sorted(g), sorted(s)) if b >= a)
''',
        '''class Solution:
    def findContentChildren(self, g, s):
        return min(len(g), len(s))
''',
    ],
    guide=dict(
        prereqs="Sorting; two pointers. Lesson *When greedy works*.",
        intuition=r"""
Small cookies are the least useful, and children with small greed are the easiest to please. Hand
out cookies from smallest to largest; each cookie goes to the least greedy child still waiting, if it
is big enough for them. If it is too small for that child it is too small for everyone left, so it is
thrown away.
""",
        hints=[
            "Sort both lists.",
            "Which child is the easiest to satisfy? Which cookie should you try first?",
            "Two pointers: advance the cookie pointer every step, the child pointer only on a match.",
        ],
        brute_force="For each child, scan all unused cookies for the smallest that fits: O(n·m).",
        approach=r"""
Sort `g` and `s`. Walk the cookies in increasing size keeping an index `child`. If
`cookie >= g[child]`, that child is content: `child += 1`. The answer is `child`.

**Dry run** `g=[1,2,3]`, `s=[1,1]`: cookie 1 ≥ g[0]=1 → child=1; cookie 1 < g[1]=2 → wasted. Answer **1**.

**Exchange argument.** If an optimal plan gives the smallest usable cookie to a greedier child,
swap it with whatever the least greedy child got: both are still satisfied (the bigger cookie is at
least as large), so nothing is lost.
""",
        complexity="Time **O(n log n + m log m)** for the two sorts; the scan is linear. Space O(n + m) for the sorted copies.",
        pitfalls="Pairing the i-th child with the i-th cookie (`zip`) is wrong — a cookie that fails one child must be skipped without skipping the child. Remember `s` may be empty.",
        follow_up="*Boats to Save People*, *Maximum Matching of Players With Trainers* (same problem), *Advantage Shuffle*.",
    ),
),
dict(
    id="maximum-units-on-a-truck",
    title="Maximum Units on a Truck",
    difficulty="Easy",
    pattern="Greedy + sorting",
    leetcode="https://leetcode.com/problems/maximum-units-on-a-truck/",
    entry="maximumUnits",
    description=r"""
`boxTypes[i] = [count, unitsPerBox]` says there are `count` boxes of type `i`, each holding
`unitsPerBox` units. The truck can carry at most `truckSize` **boxes** (any types). Return the
maximum total number of units it can carry.

**Constraints**
- `1 <= len(boxTypes) <= 1000`, `1 <= count, unitsPerBox <= 1000`, `1 <= truckSize <= 10^6`

**Example 1:** `boxTypes = [[1,3],[2,2],[3,1]], truckSize = 4` → `8` (1·3 + 2·2 + 1·1).

**Example 2:** `boxTypes = [[5,10],[2,5],[4,7],[3,9]], truckSize = 10` → `91`.
""",
    starter='''class Solution:
    def maximumUnits(self, boxTypes: List[List[int]], truckSize: int) -> int:
        pass
''',
    solution='''class Solution:
    def maximumUnits(self, boxTypes, truckSize):
        total = 0
        for count, units in sorted(boxTypes, key=lambda b: -b[1]):   # richest boxes first
            take = min(count, truckSize)
            total += take * units
            truckSize -= take
            if truckSize == 0:
                break
        return total
''',
    tests=[
        [[[1, 3], [2, 2], [3, 1]], 4],
        [[[5, 10], [2, 5], [4, 7], [3, 9]], 10],
        [[[1, 1]], 1],
        [[[3, 5]], 10],
        [[[10, 1], [1, 10]], 1],
        [[[2, 2], [2, 2]], 3],
        [[[1000, 1000]], 999],
        [[[1, 3], [5, 5], [2, 5], [4, 2], [4, 1], [3, 1], [2, 2], [1, 3], [2, 5], [3, 2]], 35],
        [[[2, 1], [4, 4], [3, 1], [4, 1], [2, 4], [3, 4], [1, 3], [4, 3], [5, 3], [5, 3]], 13],
        [[[5, 1], [1, 9]], 3],
        [_boxes_big, 100000],
        [_boxes_big, 10 ** 6],
        [_boxes_big, 7],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def maximumUnits(self, boxTypes, truckSize):
        total = 0
        for count, units in sorted(boxTypes, reverse=True):     # sorts by count, not by units
            take = min(count, truckSize)
            total += take * units
            truckSize -= take
        return total
''',
        '''class Solution:
    def maximumUnits(self, boxTypes, truckSize):
        total = 0
        for count, units in sorted(boxTypes, key=lambda b: -b[1]):
            if count <= truckSize:                               # never takes part of a type
                total += count * units
                truckSize -= count
        return total
''',
    ],
    guide=dict(
        prereqs="Sorting with a key function. Lesson *When greedy works* (fractional knapsack).",
        intuition="Every box takes exactly one slot on the truck, so a slot is best spent on the box with the most units. Fill the truck with the richest boxes first. This is the *fractional knapsack*: boxes of a type can be taken one at a time, so there is never awkward leftover space.",
        hints=[
            "All boxes cost the same (one slot). What should you compare?",
            "Sort the types by units per box, largest first.",
            "Take min(count, remaining) boxes of each type until the truck is full.",
        ],
        brute_force="Expand every box into a list of its unit value, sort that list and sum the top `truckSize` — correct but up to 10⁶ elements.",
        approach=r"""
**Dry run** `[[1,3],[2,2],[3,1]]`, size 4: take 1 box of 3 units (3), 2 boxes of 2 (4), then 1 of the
3 boxes with 1 unit (1). Total **8**.

Why greedy is safe: swapping any loaded box for an unloaded box with more units can only raise the
total, so an optimal load never leaves a richer box behind.
""",
        complexity="Time **O(n log n)**, space O(n). (Counting sort over the 1000 possible unit values gives O(n + 1000).)",
        pitfalls="Sorting by box count instead of units per box; skipping a type because it does not fit entirely (you may take part of it).",
        follow_up="0/1 knapsack, where items have different sizes, needs dynamic programming — compare with the lesson's counterexample.",
    ),
),
dict(
    id="two-city-scheduling",
    title="Two City Scheduling",
    difficulty="Medium",
    pattern="Greedy + sorting by difference",
    leetcode="https://leetcode.com/problems/two-city-scheduling/",
    entry="twoCitySchedCost",
    description=r"""
A company interviews `2n` people. `costs[i] = [aCost, bCost]` is the price of flying person `i` to
city A or to city B. Exactly `n` people must go to each city. Return the minimum total cost.

**Constraints**
- `2 <= len(costs) <= 100` (always even; tests here go to 1000), `1 <= aCost, bCost <= 1000`

**Example 1:** `costs = [[10,20],[30,200],[400,50],[30,20]]` → `110`
(persons 0 and 1 to A: 10 + 30; persons 2 and 3 to B: 50 + 20).

**Example 2:** `costs = [[1,2],[1,2]]` → `3`.
""",
    starter='''class Solution:
    def twoCitySchedCost(self, costs: List[List[int]]) -> int:
        pass
''',
    solution='''class Solution:
    def twoCitySchedCost(self, costs):
        costs = sorted(costs, key=lambda c: c[0] - c[1])   # biggest saving by choosing A first
        n = len(costs) // 2
        return sum(c[0] for c in costs[:n]) + sum(c[1] for c in costs[n:])
''',
    tests=[
        [[[10, 20], [30, 200], [400, 50], [30, 20]]],
        [[[1, 2], [1, 2]]],
        [[[259, 770], [448, 54], [926, 667], [184, 139], [840, 118], [577, 469]]],
        [[[515, 563], [451, 713], [537, 709], [343, 819], [855, 779], [457, 60], [650, 359], [631, 42]]],
        [[[5, 5], [5, 5]]],
        [[[1, 1000], [1, 1000]]],
        [[[1000, 1], [1000, 1]]],
        [[[10, 20], [10, 20], [10, 20], [10, 20]]],
        [[[1, 100], [100, 1]]],
        [[[3, 1], [2, 1], [1, 3], [1, 2]]],
        [[[70, 311], [74, 927], [732, 711], [126, 583], [857, 118], [97, 928], [975, 843], [175, 221]]],
        [_costs_big],
        [_costs_big2],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def twoCitySchedCost(self, costs):
        return sum(min(a, b) for a, b in costs)          # ignores the n / n split
''',
        '''class Solution:
    def twoCitySchedCost(self, costs):
        costs = sorted(costs)                             # sorts by cost of A only
        n = len(costs) // 2
        return sum(c[0] for c in costs[:n]) + sum(c[1] for c in costs[n:])
''',
    ],
    guide=dict(
        prereqs="Sorting by a computed key. Exchange arguments (lesson *When greedy works*).",
        intuition=r"""
Pretend everyone flies to B first: cost `sum(bCost)`. Now you must move exactly `n` people to A.
Moving person `i` changes the bill by `aCost − bCost` (negative means a saving). To minimise the
total, move the `n` people with the **smallest** `aCost − bCost`. What matters is not how cheap a
city is for a person, but how much *difference* the choice makes.
""",
        hints=[
            "Send everyone to B, then decide who to switch to A.",
            "What does switching person i change in the total?",
            "Sort by aCost - bCost; first half to A, second half to B.",
        ],
        brute_force="Try every way to choose n of the 2n people for city A: C(2n, n) subsets — about 10²⁹ for 2n = 100. A DP over (person, seats left in A) is O(n²).",
        approach=r"""
**Dry run** `[[10,20],[30,200],[400,50],[30,20]]`: differences `−10, −170, 350, 10`. Sorted:
`[30,200] (−170)`, `[10,20] (−10)`, `[30,20] (10)`, `[400,50] (350)`. First two → A: 30 + 10; last two →
B: 20 + 50. Total **110**.

**Exchange argument.** If person `p` is in A and `q` in B but `diff(p) > diff(q)`, swapping them
changes the cost by `diff(q) − diff(p) < 0`. So in an optimal plan the A group has the n smallest
differences.
""",
        complexity="Time **O(n log n)**, space O(n).",
        pitfalls="Taking each person's cheaper city ignores the equal-split rule. Sorting by one city's cost alone is not enough.",
        follow_up="With three cities or unequal quotas the same 'regret' idea leads to min-cost flow / DP.",
    ),
),
dict(
    id="queue-reconstruction-by-height",
    title="Queue Reconstruction by Height",
    difficulty="Medium",
    pattern="Greedy + sorting + insertion",
    leetcode="https://leetcode.com/problems/queue-reconstruction-by-height/",
    entry="reconstructQueue",
    checker=r'''
def check(args, got, expected):
    people = args[0]
    if not isinstance(got, list) or len(got) != len(people):
        return False
    try:
        if sorted(map(list, got)) != sorted(map(list, people)):
            return False
        for i, (h, k) in enumerate(got):
            if sum(1 for x in got[:i] if x[0] >= h) != k:
                return False
    except Exception:
        return False
    return True
''',
    description=r"""
People stand in a queue. Each person is described by `[h, k]`: their height `h`, and `k`, the number
of people **in front of them** whose height is **greater than or equal to** `h`. You are given these
pairs in scrambled order. Rebuild and return the queue. (A valid queue is guaranteed to exist; the
judge verifies your answer against the definition.)

**Constraints**
- `1 <= len(people) <= 2000`, `0 <= h <= 10^6`, `0 <= k < len(people)`

**Example 1:** `[[7,0],[4,4],[7,1],[5,0],[6,1],[5,2]]` → `[[5,0],[7,0],[5,2],[6,1],[4,4],[7,1]]`.

**Example 2:** `[[6,0],[5,0],[4,0],[3,2],[2,2],[1,4]]` → `[[4,0],[5,0],[2,2],[3,2],[1,4],[6,0]]`.
""",
    starter='''class Solution:
    def reconstructQueue(self, people: List[List[int]]) -> List[List[int]]:
        pass
''',
    solution='''class Solution:
    def reconstructQueue(self, people):
        # tallest first; among equal heights, smaller k first
        people = sorted(people, key=lambda p: (-p[0], p[1]))
        queue = []
        for p in people:
            queue.insert(p[1], p)     # exactly k taller-or-equal people are already placed
        return queue
''',
    tests=[
        [[[7, 0], [4, 4], [7, 1], [5, 0], [6, 1], [5, 2]]],
        [[[6, 0], [5, 0], [4, 0], [3, 2], [2, 2], [1, 4]]],
        [[[1, 0]]],
        [[[2, 0], [1, 1]]],
        [[[1, 0], [2, 0]]],
        [[[5, 0], [5, 1], [5, 2]]],
        [[[9, 0], [7, 0], [1, 9], [3, 0], [2, 7], [5, 3], [6, 0], [3, 4], [6, 2], [5, 2]]],
        [[[2, 4], [3, 4], [9, 0], [0, 6], [7, 1], [6, 0], [7, 3], [2, 5], [1, 1], [8, 0]]],
        [[[3, 0], [3, 1], [1, 2], [2, 2]]],
        [[[0, 0], [0, 1], [0, 2], [0, 3]]],
        [_queue(40)],
        [_queue_big],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def reconstructQueue(self, people):
        return sorted(people, key=lambda p: (p[1], p[0]))
''',
        '''class Solution:
    def reconstructQueue(self, people):
        people = sorted(people, key=lambda p: (-p[0], -p[1]))   # wrong tie-break
        queue = []
        for p in people:
            queue.insert(min(p[1], len(queue)), p)
        return queue
''',
    ],
    guide=dict(
        prereqs="Sorting by a tuple key; `list.insert`. The 'forced move at the extremes' pattern from *Greedy patterns*.",
        intuition=r"""
Short people are invisible to tall people: inserting a shorter person anywhere never changes a taller
person's count. So place people from **tallest to shortest**. When it is someone's turn, everyone
already placed is at least as tall, so the person's `k` is exactly the index where they must be
inserted. Later (shorter) arrivals will not disturb that.
""",
        hints=[
            "Whose k value is unaffected by everybody else's position?",
            "Process people from tallest to shortest. What does k mean at the moment you insert someone?",
            "Sort by (-h, k) and insert each person at index k.",
        ],
        brute_force="Try all permutations and check each against the definition: O(n!·n²).",
        approach=r"""
**Dry run** (example 1). Sorted: `[7,0] [7,1] [6,1] [5,0] [5,2] [4,4]`.

| insert | queue |
|---|---|
| [7,0] at 0 | [7,0] |
| [7,1] at 1 | [7,0] [7,1] |
| [6,1] at 1 | [7,0] [6,1] [7,1] |
| [5,0] at 0 | [5,0] [7,0] [6,1] [7,1] |
| [5,2] at 2 | [5,0] [7,0] [5,2] [6,1] [7,1] |
| [4,4] at 4 | [5,0] [7,0] [5,2] [6,1] [4,4] [7,1] |

Equal heights: the one with smaller `k` stands further forward, so it must be inserted first.
""",
        complexity="Time **O(n²)** — n insertions into a list, each O(n). Space O(n). (A Fenwick tree or segment tree brings it to O(n log n).)",
        pitfalls="Tie-break for equal heights must be ascending `k`. Sorting shortest-first requires a different (harder) 'k-th empty slot' method.",
        follow_up="O(n log n) with a binary indexed tree: process shortest first and place each person in the k-th still-empty slot.",
    ),
),
dict(
    id="dota2-senate",
    title="Dota2 Senate",
    difficulty="Medium",
    pattern="Greedy + queue simulation",
    leetcode="https://leetcode.com/problems/dota2-senate/",
    entry="predictPartyVictory",
    description=r"""
Senators belong to party `R` (Radiant) or `D` (Dire); `senate` lists them in speaking order. Voting
goes round after round in that order. On their turn a senator who still has rights may **ban** one
other senator (who loses all rights for good). A senator who has been banned is skipped. When every
senator who can still act belongs to one party, that party wins. Everyone plays optimally. Return
`"Radiant"` or `"Dire"`.

**Constraints**
- `1 <= len(senate) <= 10^4`

**Example 1:** `"RD"` → `"Radiant"` (R bans D before D can act).

**Example 2:** `"RDD"` → `"Dire"` (R bans the first D; the second D bans R).
""",
    starter='''class Solution:
    def predictPartyVictory(self, senate: str) -> str:
        pass
''',
    solution='''class Solution:
    def predictPartyVictory(self, senate):
        n = len(senate)
        r = collections.deque(i for i, c in enumerate(senate) if c == "R")
        d = collections.deque(i for i, c in enumerate(senate) if c == "D")
        while r and d:
            i, j = r.popleft(), d.popleft()
            if i < j:
                r.append(i + n)      # R speaks first, bans that D, and queues for the next round
            else:
                d.append(j + n)
        return "Radiant" if r else "Dire"
''',
    tests=[
        ["RD"], ["RDD"], ["R"], ["D"], ["DR"], ["DDRRR"], ["RRDDD"], ["DRRDRDRDRDDRDRDR"],
        ["RDRDRDDRDR"], ["DDDDRRDDDRDRDRRDDRDDDRDRRRRDRRRRRDRDDRDDRRDDRRRDDRRRDDDDRRRRRRRDDRRRDDRDDDRRRDRDDRDDDRRDRRDRRRDRDRDR"],
        ["RRR" + "D" * 4], ["D" * 5000 + "R" * 5000], [_senate_big], ["RD" * 5000],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def predictPartyVictory(self, senate):
        return "Radiant" if senate.count("R") >= senate.count("D") else "Dire"
''',
        '''class Solution:
    def predictPartyVictory(self, senate):
        return "Radiant" if senate[0] == "R" else "Dire"
''',
    ],
    guide=dict(
        prereqs="Queues (`collections.deque`). Greedy choice: remove the most dangerous opponent.",
        intuition=r"""
When it is your turn, which opponent should you ban? The one who would otherwise act **soonest** —
they are the first who could ban one of your own. Banning anyone later lets an earlier opponent
strike first. So each acting senator bans the next opposing senator in speaking order.

Keep two queues of positions, one per party. Compare the fronts: the smaller index speaks first, bans
the other, and re-enters the line for the next round (index + n keeps the order right).
""",
        hints=[
            "Counting letters is not enough — order matters ('DRR' vs 'RRD').",
            "Whom should an acting senator ban to protect their party best?",
            "Two queues of indices; pop both fronts, the smaller one survives and is re-appended with index + n.",
        ],
        brute_force="Simulate round after round on a list, scanning forward for the next opponent to ban: O(n²).",
        approach=r"""
**Dry run** `"RDD"`: R = [0], D = [1, 2]. Fronts 0 vs 1 → R wins, R = [3], D = [2]. Fronts 3 vs 2 → D
wins, D = [5], R = []. **Dire**.

Each comparison removes one senator permanently, so there are at most n − 1 steps.
""",
        complexity="Time **O(n)**, space O(n).",
        pitfalls="Majority does not decide it: `\"DRRDRDRDRDDRDRDR\"` has equal counts. Re-appending with the same index (instead of index + n) breaks the round order.",
        follow_up="The same two-queue idea solves many 'who survives' simulations (*Josephus*-style problems).",
    ),
),
dict(
    id="wiggle-subsequence",
    title="Wiggle Subsequence",
    difficulty="Medium",
    pattern="Greedy (peaks and valleys)",
    leetcode="https://leetcode.com/problems/wiggle-subsequence/",
    entry="wiggleMaxLength",
    description=r"""
A sequence *wiggles* if the differences between consecutive elements strictly alternate between
positive and negative (a sequence of one element, or of two different elements, counts). A
**subsequence** is obtained by deleting any elements without reordering. Return the length of the
longest wiggle subsequence of `nums`.

**Constraints**
- `1 <= len(nums) <= 1000` (tests go to 10^4), `0 <= nums[i] <= 1000`

**Example 1:** `[1,7,4,9,2,5]` → `6` (already wiggles: +6, −3, +5, −7, +3).

**Example 2:** `[1,17,5,10,13,15,10,5,16,8]` → `7`. `[1,2,3,4,5]` → `2`.
""",
    starter='''class Solution:
    def wiggleMaxLength(self, nums: List[int]) -> int:
        pass
''',
    solution='''class Solution:
    def wiggleMaxLength(self, nums):
        up = down = 1          # best wiggle length ending with a rise / with a fall
        for i in range(1, len(nums)):
            if nums[i] > nums[i - 1]:
                up = down + 1
            elif nums[i] < nums[i - 1]:
                down = up + 1
        return max(up, down)
''',
    tests=[
        [[1, 7, 4, 9, 2, 5]],
        [[1, 17, 5, 10, 13, 15, 10, 5, 16, 8]],
        [[1, 2, 3, 4, 5]],
        [[5]],
        [[3, 3]],
        [[3, 3, 3, 2, 5]],
        [[1, 2]],
        [[5, 4, 3, 2, 1]],
        [[0, 0, 0, 0]],
        [[1, 1, 2, 2, 1, 1, 2, 2]],
        [[2, 1, 4, 5, 6, 3, 3, 4, 8, 4]],
        [_wiggle_big],
        [list(range(5000)) + list(range(5000, 0, -1))],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def wiggleMaxLength(self, nums):
        count = 1
        for i in range(1, len(nums)):
            if nums[i] != nums[i - 1]:
                count += 1                       # counts every change, not direction changes
        return count
''',
        '''class Solution:
    def wiggleMaxLength(self, nums):
        if len(nums) < 2: return len(nums)
        count, prev = 1, 0
        for i in range(1, len(nums)):
            diff = nums[i] - nums[i - 1]
            if diff * prev < 0 or prev == 0:     # counts flat steps as turns
                count += 1
            prev = diff
        return count
''',
    ],
    guide=dict(
        prereqs="Kadane-style running state (lesson *Greedy patterns*).",
        intuition=r"""
Draw the numbers as a mountain range. Along one long climb only the bottom and the top matter:
keeping the highest point of a climb gives the next descent the most room. So the answer is the number
of **turning points** (peaks and valleys) plus the endpoints. Equivalently keep two numbers: `up`, the
longest wiggle so far that ends on a rise, and `down`, the longest that ends on a fall. A rise can
only extend a sequence that ended on a fall, and vice versa.
""",
        hints=[
            "On a strictly increasing run, how many elements can you keep?",
            "Count direction changes, ignoring flat steps.",
            "up = down + 1 on a rise, down = up + 1 on a fall; answer max(up, down).",
        ],
        brute_force="DP over pairs: for each i and each earlier j, extend the best opposite-direction sequence — O(n²).",
        approach=r"""
**Dry run** `[1,17,5,10,13,15,10,5,16,8]`:

| step | move | up | down |
|---|---|---|---|
| 1→17 | rise | 2 | 1 |
| 17→5 | fall | 2 | 3 |
| 5→10 | rise | 4 | 3 |
| 10→13, 13→15 | rise | 4 | 3 |
| 15→10 | fall | 4 | 5 |
| 10→5 | fall | 4 | 5 |
| 5→16 | rise | 6 | 5 |
| 16→8 | fall | 6 | **7** |
""",
        complexity="Time **O(n)**, space **O(1)**.",
        pitfalls="Equal neighbours are neither a rise nor a fall — skip them. Counting every unequal pair overcounts long climbs.",
        follow_up="*Wiggle Sort* (rearrange in place), *Longest Turbulent Subarray* (contiguous version).",
    ),
),
dict(
    id="largest-number",
    title="Largest Number",
    difficulty="Medium",
    pattern="Greedy + custom sort",
    leetcode="https://leetcode.com/problems/largest-number/",
    neetcode="https://neetcode.io/problems/largest-number",
    entry="largestNumber",
    description=r"""
Arrange the non-negative integers in `nums` side by side so that the digits read as the largest
possible number, and return it as a **string** (it may be far too big for a fixed-width integer).
The result must not have extra leading zeros: if every number is 0, return `"0"`.

**Constraints**
- `1 <= len(nums) <= 100`, `0 <= nums[i] <= 10^9`

**Example 1:** `[10, 2]` → `"210"`.

**Example 2:** `[3, 30, 34, 5, 9]` → `"9534330"`.
""",
    starter='''class Solution:
    def largestNumber(self, nums: List[int]) -> str:
        pass
''',
    solution='''class Solution:
    def largestNumber(self, nums):
        strs = [str(x) for x in nums]
        # a should come before b when the concatenation a+b is larger than b+a
        strs.sort(key=functools.cmp_to_key(lambda a, b: -1 if a + b > b + a else (1 if a + b < b + a else 0)))
        out = "".join(strs)
        return "0" if out[0] == "0" else out
''',
    tests=[
        [[10, 2]],
        [[3, 30, 34, 5, 9]],
        [[0, 0]],
        [[0]],
        [[1]],
        [[432, 43243]],
        [[121, 12]],
        [[12, 121]],
        [[34323, 3432]],
        [[9, 99, 999, 0]],
        [[111311, 1113]],
        [[1000000000, 1000000000]],
        [[8308, 8308, 830]],
        [_largest_big],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def largestNumber(self, nums):
        return "".join(sorted(map(str, nums), reverse=True))       # plain string order
''',
        '''class Solution:
    def largestNumber(self, nums):
        strs = sorted(map(str, nums), key=functools.cmp_to_key(lambda a, b: -1 if a + b > b + a else 1))
        return "".join(strs)                                        # "00" instead of "0"
''',
    ],
    guide=dict(
        prereqs="Sorting with a comparison function (`functools.cmp_to_key`). Exchange arguments.",
        intuition=r"""
For two numbers the decision is easy: put `a` before `b` if the string `a+b` is bigger than `b+a`
(same length, so string comparison equals numeric comparison). The surprising fact is that this
pairwise rule is a consistent ordering, so sorting the whole list by it gives the best arrangement —
if any neighbouring pair were in the "wrong" order, swapping them would make the number larger.
""",
        hints=[
            "Compare 3 and 30: which goes first, and how do you know?",
            "For strings a and b compare a+b with b+a.",
            "Sort with that comparator, join, and handle the all-zeros case.",
        ],
        brute_force="Try all permutations and keep the largest concatenation: O(n!).",
        approach=r"""
**Dry run** `[3, 30, 34, 5, 9]`: `9` vs `5`: "95" > "59" → 9 first. `34` vs `3`: "343" > "334" → 34
before 3. `3` vs `30`: "330" > "303" → 3 before 30. Order: 9, 5, 34, 3, 30 → **"9534330"**.

Plain descending string sort fails on `3` vs `30` ("30" > "3" alphabetically, giving "303").
""",
        complexity="Time **O(n log n · L)** where L is the digit length (each comparison builds two short strings); space O(n·L).",
        pitfalls="All zeros must give `\"0\"`, not `\"000\"`. Sorting numerically or lexicographically is wrong.",
        follow_up="Smallest number by the mirrored rule (watch leading zeros). Proving transitivity of the comparator is a classic exercise.",
    ),
),
# ================================================================== INTERVALS
dict(
    id="minimum-number-of-arrows-to-burst-balloons",
    title="Minimum Number of Arrows to Burst Balloons",
    difficulty="Medium",
    pattern="Intervals / greedy by end",
    leetcode="https://leetcode.com/problems/minimum-number-of-arrows-to-burst-balloons/",
    entry="findMinArrowShots",
    description=r"""
Balloons are taped to a wall; balloon `i` covers the horizontal range `points[i] = [xstart, xend]`
(both ends included). An arrow shot straight up at position `x` bursts every balloon with
`xstart <= x <= xend`. Return the minimum number of arrows needed to burst them all.

**Constraints**
- `1 <= len(points) <= 10^5`, `-2^31 <= xstart <= xend <= 2^31 - 1`

**Example 1:** `[[10,16],[2,8],[1,6],[7,12]]` → `2` (shoot at x = 6 and x = 11).

**Example 2:** `[[1,2],[3,4],[5,6],[7,8]]` → `4`. `[[1,2],[2,3],[3,4],[4,5]]` → `2`.
""",
    starter='''class Solution:
    def findMinArrowShots(self, points: List[List[int]]) -> int:
        pass
''',
    solution='''class Solution:
    def findMinArrowShots(self, points):
        arrows = 0
        last = None                      # x position of the most recent arrow
        for s, e in sorted(points, key=lambda p: p[1]):
            if last is None or s > last: # this balloon is not hit by the last arrow
                arrows += 1
                last = e                 # shoot as far right as this balloon allows
        return arrows
''',
    tests=[
        [[[10, 16], [2, 8], [1, 6], [7, 12]]],
        [[[1, 2], [3, 4], [5, 6], [7, 8]]],
        [[[1, 2], [2, 3], [3, 4], [4, 5]]],
        [[[1, 2]]],
        [[[2, 3], [2, 3]]],
        [[[-2147483648, 2147483647]]],
        [[[-2147483646, -2147483645], [2147483646, 2147483647]]],
        [[[1, 10], [2, 3], [4, 5], [6, 7]]],
        [[[3, 9], [7, 12], [3, 8], [6, 8], [9, 10], [2, 9], [0, 9], [3, 9], [0, 6], [2, 8]]],
        [[[0, 0], [0, 0], [1, 1]]],
        [[[9, 12], [1, 10], [4, 11], [8, 12], [3, 9], [6, 9], [6, 7]]],
        [_balloons_big],
        [[[i, i + 1] for i in range(0, 20000, 2)]],
    ],
    examples=3,
    wrong_solutions=[
        '''class Solution:
    def findMinArrowShots(self, points):
        arrows, last = 0, None
        for s, e in sorted(points, key=lambda p: p[1]):
            if last is None or s >= last:        # touching balloons need separate arrows (wrong)
                arrows += 1; last = e
        return arrows
''',
        '''class Solution:
    def findMinArrowShots(self, points):
        arrows, last = 0, None
        for s, e in sorted(points):              # sorted by start, never shrinks the window
            if last is None or s > last:
                arrows += 1; last = e
        return arrows
''',
    ],
    guide=dict(
        prereqs="*Non-overlapping Intervals*; lesson *Interval fundamentals* (sort by end).",
        intuition=r"""
Look at the balloon that **ends first**. Some arrow must hit it, and the best place for that arrow
is its right edge: moving the arrow right can only make it reach more of the other balloons (all of
which end later). Shoot there, discard every balloon the arrow hits, repeat.
""",
        hints=[
            "Sort by the right end.",
            "Where is the best position for the arrow that bursts the first-ending balloon?",
            "Count a new arrow whenever a balloon starts strictly after the last arrow's position.",
        ],
        brute_force="Try every subset of candidate positions (the balloon end points): exponential.",
        approach=r"""
**Dry run** `[[10,16],[2,8],[1,6],[7,12]]` sorted by end: `[1,6] [2,8] [7,12] [10,16]`.
Arrow at 6 (hits `[1,6]`, `[2,8]`); `[7,12]` starts after 6 → arrow at 12 (also hits `[10,16]`). **2**.

This is exactly interval scheduling: the number of arrows equals the maximum number of pairwise
non-overlapping balloons — except that here touching balloons **do** overlap (closed ranges), hence
`s > last` rather than `s >= last`.
""",
        complexity="Time **O(n log n)**, space O(n).",
        pitfalls="Closed ranges: `[1,2]` and `[2,3]` share an arrow. If you sort by start instead, you must track `last = min(last, e)`.",
        follow_up="*Non-overlapping Intervals*, *Video Stitching*, *Minimum Number of Taps to Open to Water a Garden*.",
    ),
),
dict(
    id="interval-list-intersections",
    title="Interval List Intersections",
    difficulty="Medium",
    pattern="Intervals / two pointers",
    leetcode="https://leetcode.com/problems/interval-list-intersections/",
    entry="intervalIntersection",
    description=r"""
`firstList` and `secondList` are each a list of closed intervals that is sorted and pairwise
disjoint. Return every interval that is common to both lists (the intersection of the two sets of
points), in sorted order. A single shared point such as `[5,5]` counts.

**Constraints**
- `0 <= len(firstList), len(secondList) <= 1000` (tests go to 3000), `0 <= start <= end <= 10^9`

**Example 1:** `firstList = [[0,2],[5,10],[13,23],[24,25]]`,
`secondList = [[1,5],[8,12],[15,24],[25,26]]` → `[[1,2],[5,5],[8,10],[15,23],[24,24],[25,25]]`.

**Example 2:** `firstList = [[1,3],[5,9]], secondList = []` → `[]`.
""",
    starter='''class Solution:
    def intervalIntersection(self, firstList: List[List[int]], secondList: List[List[int]]) -> List[List[int]]:
        pass
''',
    solution='''class Solution:
    def intervalIntersection(self, firstList, secondList):
        i = j = 0
        out = []
        while i < len(firstList) and j < len(secondList):
            lo = max(firstList[i][0], secondList[j][0])
            hi = min(firstList[i][1], secondList[j][1])
            if lo <= hi:
                out.append([lo, hi])
            if firstList[i][1] < secondList[j][1]:   # whichever ends first is finished
                i += 1
            else:
                j += 1
        return out
''',
    tests=[
        [[[0, 2], [5, 10], [13, 23], [24, 25]], [[1, 5], [8, 12], [15, 24], [25, 26]]],
        [[[1, 3], [5, 9]], []],
        [[], [[4, 8]]],
        [[[1, 7]], [[3, 10]]],
        [[[1, 2]], [[3, 4]]],
        [[[1, 2]], [[2, 3]]],
        [[[0, 100]], [[1, 2], [5, 6], [50, 200]]],
        [[[3, 5], [9, 20]], [[4, 5], [7, 10], [11, 12], [14, 15], [16, 20]]],
        [[[5, 10]], [[5, 10]]],
        [[[1, 1], [3, 3]], [[1, 3]]],
        [[[0, 5], [12, 14], [15, 18]], [[11, 15], [18, 19]]],
        [_ila, _ilb],
        [_ila, [[0, 10 ** 9]]],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def intervalIntersection(self, firstList, secondList):
        i = j = 0
        out = []
        while i < len(firstList) and j < len(secondList):
            lo = max(firstList[i][0], secondList[j][0]); hi = min(firstList[i][1], secondList[j][1])
            if lo < hi:                                     # drops single-point overlaps
                out.append([lo, hi])
            if firstList[i][1] < secondList[j][1]: i += 1
            else: j += 1
        return out
''',
        '''class Solution:
    def intervalIntersection(self, firstList, secondList):
        out = []
        for a, b in zip(firstList, secondList):            # only pairs equal indices
            lo, hi = max(a[0], b[0]), min(a[1], b[1])
            if lo <= hi: out.append([lo, hi])
        return out
''',
    ],
    guide=dict(
        prereqs="The overlap test `max(starts) <= min(ends)`; two pointers. Lesson *Interval fundamentals* §7.",
        intuition="Hold one interval from each list. Their intersection (if any) is `[max of starts, min of ends]`. Then throw away the interval that **ends first** — nothing later in the other list can still touch it, because the other list's later intervals start even further right.",
        hints=[
            "How do you compute the intersection of two closed intervals?",
            "After comparing A[i] and B[j], which of the two can never intersect anything else?",
            "Advance the pointer whose interval has the smaller end.",
        ],
        brute_force="Compare every pair: O(n·m).",
        approach=r"""
**Dry run** (example 1): `[0,2]∩[1,5] = [1,2]`, advance A (2 < 5). `[5,10]∩[1,5] = [5,5]`, advance B.
`[5,10]∩[8,12] = [8,10]`, advance A. `[13,23]∩[8,12]` empty, advance B. `[13,23]∩[15,24] = [15,23]`,
advance A. `[24,25]∩[15,24] = [24,24]`, advance B. `[24,25]∩[25,26] = [25,25]`. Done.
""",
        complexity="Time **O(n + m)**, space O(1) besides the output.",
        pitfalls="Use `<=` so that single-point intersections are kept. Do not advance both pointers at once.",
        follow_up="*Employee Free Time* (merge everyone's intervals, report gaps), *Merge Two Sorted Lists* (same pointer dance).",
    ),
),
dict(
    id="my-calendar-i",
    title="My Calendar I",
    difficulty="Medium",
    pattern="Intervals / sorted list + binary search",
    leetcode="https://leetcode.com/problems/my-calendar-i/",
    kind="class",
    entry="MyCalendar",
    description=r"""
Design a calendar that refuses double bookings.

- `MyCalendar()` creates an empty calendar.
- `book(startTime, endTime)` tries to add the half-open event `[startTime, endTime)`. If it does not
  overlap any event already stored, store it and return `True`; otherwise return `False` and store
  nothing. Events that merely touch (`[10,20)` then `[20,30)`) do not overlap.

**Constraints**
- `0 <= startTime < endTime <= 10^9`; at most 1000 calls.

**Example:**
```
ops  = ["MyCalendar","book","book","book"]
args = [[],[10,20],[15,25],[20,30]]
out  = [null,true,false,true]
```
""",
    starter='''class MyCalendar:

    def __init__(self):
        pass

    def book(self, startTime: int, endTime: int) -> bool:
        pass
''',
    solution='''class MyCalendar:
    def __init__(self):
        self.starts = []      # sorted start times
        self.ends = []        # ends[i] belongs to starts[i]

    def book(self, startTime, endTime):
        i = bisect.bisect_right(self.starts, startTime)   # events before index i start at or before startTime
        if i > 0 and self.ends[i - 1] > startTime:        # previous event still running
            return False
        if i < len(self.starts) and self.starts[i] < endTime:   # next event starts too early
            return False
        self.starts.insert(i, startTime)
        self.ends.insert(i, endTime)
        return True
''',
    tests=[
        [["MyCalendar", "book", "book", "book"], [[], [10, 20], [15, 25], [20, 30]]],
        [["MyCalendar", "book"], [[], [0, 1]]],
        [["MyCalendar", "book", "book"], [[], [5, 10], [5, 10]]],
        [["MyCalendar", "book", "book", "book"], [[], [10, 20], [0, 10], [20, 30]]],
        [["MyCalendar", "book", "book", "book", "book"], [[], [10, 20], [5, 11], [19, 25], [12, 13]]],
        [["MyCalendar", "book", "book", "book"], [[], [10, 20], [0, 100], [30, 40]]],
        [["MyCalendar", "book", "book", "book", "book"], [[], [10, 20], [30, 40], [20, 30], [15, 35]]],
        [["MyCalendar", "book", "book", "book"], [[], [0, 1000000000], [1, 2], [999999999, 1000000000]]],
        [["MyCalendar", "book", "book", "book", "book", "book"], [[], [47, 50], [33, 41], [39, 45], [33, 42], [25, 32]]],
        [["MyCalendar", "book", "book", "book", "book"], [[], [20, 30], [10, 20], [30, 40], [29, 31]]],
        [["MyCalendar", "book", "book", "book"], [[], [1, 5], [2, 3], [5, 6]]],
        _cal_big,
        _cal_ops(1000, 10 ** 9),
    ],
    examples=1,
    wrong_solutions=[
        '''class MyCalendar:
    def __init__(self):
        self.ev = []
    def book(self, startTime, endTime):
        for s, e in self.ev:
            if s <= endTime and startTime <= e:       # treats touching events as a clash
                return False
        self.ev.append((startTime, endTime))
        return True
''',
        '''class MyCalendar:
    def __init__(self):
        self.ev = []
    def book(self, startTime, endTime):
        for s, e in self.ev:
            if s <= startTime < e:                    # only checks the new start
                return False
        self.ev.append((startTime, endTime))
        return True
''',
    ],
    guide=dict(
        prereqs="Half-open overlap test; binary search with `bisect`. Lesson *Interval fundamentals*.",
        intuition=r"""
Two half-open events overlap exactly when `s1 < e2 and s2 < e1`. The simplest solution checks the new
event against every stored one (O(n) per booking). If the stored events are kept **sorted**, the new
event can only clash with its two would-be neighbours: the event just before it (does that one end
after I start?) and the event just after it (does it start before I end?).
""",
        hints=[
            "Write the overlap test for half-open intervals.",
            "A linear scan over stored events passes; can sorted order narrow the candidates?",
            "Binary search the insertion point; check only the previous event's end and the next event's start.",
        ],
        brute_force="Keep a plain list; for each `book`, compare with every stored event: O(n) per call, O(n²) overall — fine for 1000 calls.",
        approach=r"""
**Dry run**: book(10,20) → stored. book(15,25): insertion index 1; previous event ends at 20 > 15 →
**False**. book(20,30): index 1; previous ends at 20, not > 20; no next → **True**.
""",
        complexity="Binary search is O(log n); `list.insert` is O(n) in the worst case, so O(n) per call here. A balanced tree (`sortedcontainers.SortedList`) gives O(log n).",
        pitfalls="Using `<=` rejects back-to-back events. Checking only whether the new start falls inside an old event misses the case where the new event swallows an old one.",
        follow_up="*My Calendar II* (allow double but not triple booking), *My Calendar III* (maximum overlap — sweep line / difference map).",
    ),
),
dict(
    id="car-pooling",
    title="Car Pooling",
    difficulty="Medium",
    pattern="Intervals / sweep line (difference array)",
    leetcode="https://leetcode.com/problems/car-pooling/",
    entry="carPooling",
    description=r"""
A car with `capacity` empty seats drives east only. `trips[i] = [numPassengers, from, to]` means
that group boards at kilometre `from` and leaves at kilometre `to`. Return `True` if every trip can
be served without ever having more than `capacity` passengers in the car. Passengers leaving at a
kilometre free their seats before others board there.

**Constraints**
- `1 <= len(trips) <= 1000`, `1 <= numPassengers <= 100`, `0 <= from < to <= 1000`, `1 <= capacity <= 10^5`

**Example 1:** `trips = [[2,1,5],[3,3,7]], capacity = 4` → `False`.

**Example 2:** `trips = [[2,1,5],[3,3,7]], capacity = 5` → `True`.
""",
    starter='''class Solution:
    def carPooling(self, trips: List[List[int]], capacity: int) -> bool:
        pass
''',
    solution='''class Solution:
    def carPooling(self, trips, capacity):
        change = [0] * 1001               # change[x] = net passengers boarding at kilometre x
        for people, start, end in trips:
            change[start] += people
            change[end] -= people
        load = 0
        for delta in change:
            load += delta
            if load > capacity:
                return False
        return True
''',
    tests=[
        [[[2, 1, 5], [3, 3, 7]], 4],
        [[[2, 1, 5], [3, 3, 7]], 5],
        [[[2, 1, 5], [3, 5, 7]], 3],
        [[[3, 2, 7], [3, 7, 9], [8, 3, 9]], 11],
        [[[1, 0, 1000]], 1],
        [[[5, 0, 1]], 4],
        [[[9, 0, 1], [3, 3, 7]], 4],
        [[[2, 2, 6], [2, 4, 7], [8, 6, 7]], 11],
        [[[7, 5, 6], [6, 7, 8], [10, 1, 6]], 16],
        [[[3, 5, 9], [4, 2, 5], [3, 4, 6], [9, 1, 4], [5, 6, 8], [5, 4, 6]], 14],
        [[[100, 0, 1000]] * 1000, 100000],
        [[[100, 0, 1000]] * 1000 + [[1, 500, 501]], 100000],
        [_trips_big, 1200],
        [_trips_big, 1700],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def carPooling(self, trips, capacity):
        return sum(t[0] for t in trips) <= capacity
''',
        '''class Solution:
    def carPooling(self, trips, capacity):
        change = [0] * 1002
        for people, start, end in trips:
            change[start] += people
            change[end + 1] -= people          # keeps passengers one kilometre too long
        load = 0
        for d in change:
            load += d
            if load > capacity: return False
        return True
''',
    ],
    guide=dict(
        prereqs="Lesson *Sweep lines and heaps* (events and difference arrays).",
        intuition="The number of passengers only changes at pick-up and drop-off points. Record `+people` at each `from` and `−people` at each `to`, then walk the road from kilometre 0 adding up the changes: the running total is the current load. This is *Meeting Rooms II* with weights.",
        hints=[
            "When does the number of passengers change?",
            "Store the change at each kilometre: +p at from, -p at to.",
            "Prefix-sum the changes and compare with capacity at every kilometre.",
        ],
        brute_force="For every kilometre 0..1000, sum the passengers of all trips covering it: O(1000·n).",
        approach=r"""
**Dry run** `[[2,1,5],[3,3,7]]`, capacity 4: change[1]=+2, change[3]=+3, change[5]=−2, change[7]=−3.
Load: km1 → 2, km3 → 5 > 4 → **False**.

With large coordinates, sort the events `(position, delta)` instead (drop-offs before pick-ups on
ties, which tuple order gives for free because `−p < +p`), or use a min-heap of end positions.
""",
        complexity="Time **O(n + R)** with R = 1001 road positions; space O(R).",
        pitfalls="Passengers leave **at** `to` — subtract at `to`, not `to + 1`. Summing all passengers ignores that trips may not overlap.",
        follow_up="*Corporate Flight Bookings*, *Range Addition*, *My Calendar III* — all difference arrays.",
    ),
),
dict(
    id="summary-ranges",
    title="Summary Ranges",
    difficulty="Easy",
    pattern="Intervals / run grouping",
    leetcode="https://leetcode.com/problems/summary-ranges/",
    entry="summaryRanges",
    description=r"""
`nums` is a sorted list of **distinct** integers. Compress it into the shortest list of ranges that
covers exactly those numbers: a run of consecutive values `a, a+1, …, b` becomes the string
`"a->b"`, and a number standing alone becomes `"a"`. Return the strings in order.

**Constraints**
- `0 <= len(nums) <= 20` on LeetCode (tests here are larger), values fit in 32 bits.

**Example 1:** `[0,1,2,4,5,7]` → `["0->2","4->5","7"]`.

**Example 2:** `[0,2,3,4,6,8,9]` → `["0","2->4","6","8->9"]`.
""",
    starter='''class Solution:
    def summaryRanges(self, nums: List[int]) -> List[str]:
        pass
''',
    solution='''class Solution:
    def summaryRanges(self, nums):
        out = []
        i, n = 0, len(nums)
        while i < n:
            start = nums[i]
            while i + 1 < n and nums[i + 1] == nums[i] + 1:   # extend the run
                i += 1
            out.append(str(start) if nums[i] == start else f"{start}->{nums[i]}")
            i += 1
        return out
''',
    tests=[
        [[0, 1, 2, 4, 5, 7]],
        [[0, 2, 3, 4, 6, 8, 9]],
        [[]],
        [[5]],
        [[-1]],
        [[1, 3, 5, 7]],
        [[1, 2, 3, 4, 5]],
        [[-3, -2, -1, 1, 2]],
        [[-2147483648, -2147483647, 2147483647]],
        [[0, 1]],
        [[-5, -3, -2, 0]],
        [_summary_big],
        [list(range(-5000, 5000))],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def summaryRanges(self, nums):
        out, i, n = [], 0, len(nums)
        while i < n:
            start = nums[i]
            while i + 1 < n and nums[i + 1] == nums[i] + 1:
                i += 1
            out.append(f"{start}->{nums[i]}")              # "7->7" for single numbers
            i += 1
        return out
''',
        '''class Solution:
    def summaryRanges(self, nums):
        if not nums: return []
        out, start = [], nums[0]
        for i in range(1, len(nums)):
            if nums[i] != nums[i - 1] + 1:
                out.append(str(start) if start == nums[i - 1] else f"{start}->{nums[i - 1]}")
                start = nums[i]
        return out                                          # forgets the final run
''',
    ],
    guide=dict(
        prereqs="Loops with two indices. Related to merging intervals: each number is the interval [x, x].",
        intuition="Scan left to right. Remember where the current run started; keep walking while the next number is exactly one more. When the run stops, write it down — as a single number if it never grew, otherwise as `start->end`.",
        hints=[
            "What condition says the next number continues the current run?",
            "Use an inner loop that advances while nums[i+1] == nums[i] + 1.",
            "Format differently when the run has length one. Do not forget the last run.",
        ],
        brute_force="There is nothing slower that is natural here; the one-pass scan is the baseline.",
        approach=r"""
**Dry run** `[0,1,2,4,5,7]`: start 0, extend to 2 → `"0->2"`; start 4, extend to 5 → `"4->5"`;
start 7, cannot extend → `"7"`.
""",
        complexity="Time **O(n)**, space O(1) besides the output.",
        pitfalls="Emitting `\"7->7\"`; losing the last run when the loop ends; empty input.",
        follow_up="*Missing Ranges* (report the gaps instead), *Data Stream as Disjoint Intervals*.",
    ),
),
]
