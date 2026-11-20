import random

_R = random.Random(4242)


def _kth_stream_test(k, init, adds):
    ops = ["KthLargest"] + ["add"] * len(adds)
    args = [[k, init]] + [[v] for v in adds]
    return [ops, args]


def _twitter_ops(rng, n_ops, users):
    ops, args = ["Twitter"], [[]]
    tid = 1
    for _ in range(n_ops):
        r = rng.random()
        u = rng.randint(1, users)
        if r < 0.40:
            ops.append("postTweet"); args.append([u, tid]); tid += 1
        elif r < 0.65:
            ops.append("getNewsFeed"); args.append([u])
        elif r < 0.85:
            v = rng.randint(1, users)
            ops.append("follow"); args.append([u, v])
        else:
            v = rng.randint(1, users)
            ops.append("unfollow"); args.append([u, v])
    return [ops, args]


def _median_ops(rng, n, lo, hi):
    ops, args = ["MedianFinder"], [[]]
    for _ in range(n):
        ops.append("addNum"); args.append([rng.randint(lo, hi)])
        if rng.random() < 0.5:
            ops.append("findMedian"); args.append([])
    ops.append("findMedian"); args.append([])
    return [ops, args]


_KCLOSEST_CHECK = '''
def check(args, got, expected):
    points, k = args
    if not isinstance(got, list) or len(got) != k:
        return False
    pool = {}
    for p in points:
        pool[tuple(p)] = pool.get(tuple(p), 0) + 1
    for p in got:
        if not isinstance(p, list) or len(p) != 2:
            return False
        t = tuple(p)
        if pool.get(t, 0) == 0:
            return False
        pool[t] -= 1
    d = lambda p: p[0] * p[0] + p[1] * p[1]
    return sorted(map(d, got)) == sorted(map(d, expected))
'''

PROBLEMS = [
# ---------------------------------------------------------------------------------------------
dict(
    id="kth-largest-element-in-a-stream",
    title="Kth Largest Element in a Stream",
    difficulty="Easy",
    pattern="Heap / Priority Queue",
    leetcode="https://leetcode.com/problems/kth-largest-element-in-a-stream/",
    neetcode="https://neetcode.io/problems/kth-largest-integer-in-a-stream",
    kind="class",
    entry="KthLargest",
    description=r"""
Build a class that watches a stream of integers and can always report the **k-th largest** value
seen so far (k-th largest in sorted order, so duplicates count separately — in `[5, 5, 3]` the
2nd largest is `5`).

- `KthLargest(k, nums)` — set up the tracker with the integer `k` and an initial list `nums`.
- `add(val)` — append `val` to the stream and return the k-th largest element of everything seen.

**Constraints**

- `1 <= k <= 10^4`, `0 <= len(nums) <= 10^4`
- `-10^4 <= nums[i], val <= 10^4`
- At most `10^4` calls to `add`; whenever `add` is called, the stream holds at least `k` numbers
  (so `nums` may start with only `k - 1` elements).

**Example**

```
KthLargest(3, [4, 5, 8, 2])
add(3)  -> 4     stream 2 3 4 5 8 : 3rd largest is 4
add(5)  -> 5     stream 2 3 4 5 5 8
add(10) -> 5
add(9)  -> 8
add(4)  -> 8
```
""",
    starter='''class KthLargest:

    def __init__(self, k: int, nums: List[int]):
        pass

    def add(self, val: int) -> int:
        pass
''',
    solution='''import heapq

class KthLargest:
    def __init__(self, k, nums):
        self.k = k
        self.h = list(nums)
        heapq.heapify(self.h)
        while len(self.h) > k:
            heapq.heappop(self.h)

    def add(self, val):
        if len(self.h) < self.k:
            heapq.heappush(self.h, val)
        elif val > self.h[0]:
            heapq.heapreplace(self.h, val)
        return self.h[0]
''',
    tests=[
        _kth_stream_test(3, [4, 5, 8, 2], [3, 5, 10, 9, 4]),
        _kth_stream_test(1, [], [-3, -2, -4, 0, 4]),
        _kth_stream_test(2, [0], [-1, 1, -2, -4, 3]),
        _kth_stream_test(4, [7, 7, 7, 7, 8, 3], [2, 10, 9, 9]),
        _kth_stream_test(1, [5], [5, 5, 1, 6]),
        _kth_stream_test(3, [1, 2], [3, 3, 3, 0, 100]),
        _kth_stream_test(2, [-10000, 10000], [0, -10000, 10000, 10000]),
        _kth_stream_test(5, [], [1, 2, 3, 4, 5, 6, 7, 8]),
        _kth_stream_test(10, [_R.randint(-10**4, 10**4) for _ in range(10**4)],
                         [_R.randint(-10**4, 10**4) for _ in range(3000)]),
        _kth_stream_test(2500, [_R.randint(-10**4, 10**4) for _ in range(5000)],
                         [_R.randint(-10**4, 10**4) for _ in range(3000)]),
        _kth_stream_test(1, [_R.randint(-50, 50) for _ in range(200)], [_R.randint(-60, 60) for _ in range(200)]),
    ],
    examples=2,
    wrong_solutions=[
        '''import heapq
class KthLargest:
    def __init__(self, k, nums):
        self.k = k
        self.h = list(nums)
        heapq.heapify(self.h)
    def add(self, val):
        heapq.heappush(self.h, val)
        return self.h[0]
''',
        '''class KthLargest:
    def __init__(self, k, nums):
        self.k = k
        self.s = set(nums)
    def add(self, val):
        self.s.add(val)
        return sorted(self.s, reverse=True)[self.k - 1]
''',
    ],
    guide=dict(
        prereqs="Binary heaps and `heapq` (lesson *Binary heaps and Python's heapq*); the top-k pattern (lesson *Heap patterns*).",
        intuition=r"""
You never need the whole stream sorted — only its top `k` values. Keep exactly those `k` values in a
**min-heap**. The smallest of the top `k` *is* the k-th largest overall, and a min-heap keeps
that element at index 0. A new value either beats the heap's minimum (it joins the top `k`, and the
old minimum is evicted) or it doesn't (it can never matter again, because the k-th largest only goes up).
""",
        hints=[
            "Which values from the stream can ever be the answer again? Can you throw the rest away?",
            "Store only the k largest values. Which of them is the answer, and which data structure gives you that one in O(1)?",
            "Use a min-heap of size k: push the new value, and if the size exceeds k pop the minimum. The answer is heap[0].",
        ],
        brute_force=r"""
Append every value to a list and sort it (descending) on each `add`, returning index `k-1`. That is
$O(n \log n)$ per call. Keeping the list sorted with `bisect.insort` gets lookup to O(1) but insertion
is still O(n) because of shifting.
""",
        approach=r"""
1. In the constructor, heapify `nums` (O(n)) and pop until only `k` elements remain.
2. In `add(val)`:
   - if the heap holds fewer than `k` values, push `val`;
   - otherwise, if `val > heap[0]`, replace the root with `val` (`heapreplace` pops then pushes in one sift);
   - return `heap[0]`.

**Dry run** with `k = 3, nums = [4, 5, 8, 2]`: after trimming, heap = `{4, 5, 8}` (root 4).

| add | action | heap (min first) | return |
|---|---|---|---|
| 3 | 3 ≤ 4, ignore | 4 5 8 | 4 |
| 5 | 5 > 4, replace | 5 5 8 | 5 |
| 10 | 10 > 5, replace | 5 8 10 | 5 |
| 9 | 9 > 5, replace | 8 9 10 | 8 |
| 4 | ignore | 8 9 10 | 8 |
""",
        complexity="Constructor O(n + (n−k) log n) — heapify is linear, each trimming pop is O(log n). Each `add` is O(log k). Space O(k).",
        pitfalls=r"""
- Using a **max-heap** of everything: then the k-th largest is buried and you must pop k times.
- Forgetting the case where `nums` starts with fewer than `k` values — you must push unconditionally until the heap is full.
- Deduplicating values (using a set): the k-th largest counts duplicates.
- Comparing with `>=` vs `>` doesn't change correctness here, but `>` avoids pointless work.
""",
        follow_up="What if you also had to support removing a value from the stream? (Look up *lazy deletion* in a heap, or use a balanced BST / `SortedList`.) Related: *Kth Largest Element in an Array*, *Top K Frequent Elements*.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="last-stone-weight",
    title="Last Stone Weight",
    difficulty="Easy",
    pattern="Heap / Priority Queue",
    leetcode="https://leetcode.com/problems/last-stone-weight/",
    neetcode="https://neetcode.io/problems/last-stone-weight",
    entry="lastStoneWeight",
    description=r"""
You have a pile of stones with positive integer weights. Repeatedly take the **two heaviest**
stones, with weights `x <= y`, and smash them together:

- if `x == y`, both are destroyed;
- otherwise the lighter one is destroyed and the heavier becomes a stone of weight `y - x`.

Continue until at most one stone is left. Return its weight, or `0` if no stones remain.

**Constraints:** `1 <= len(stones) <= 30` in the original problem (tests here go up to 10^4), `1 <= stones[i] <= 1000`.

**Example 1:** `stones = [2,7,4,1,8,1]` → `1`
(8 and 7 → 1; then 4 and 2 → 2; then 2 and 1 → 1; then 1 and 1 → 0; one stone of weight 1 is left.)

**Example 2:** `stones = [1]` → `1`
""",
    starter='''class Solution:
    def lastStoneWeight(self, stones: List[int]) -> int:
        pass
''',
    solution='''import heapq

class Solution:
    def lastStoneWeight(self, stones):
        h = [-s for s in stones]
        heapq.heapify(h)
        while len(h) > 1:
            y = -heapq.heappop(h)
            x = -heapq.heappop(h)
            if y != x:
                heapq.heappush(h, -(y - x))
        return -h[0] if h else 0
''',
    tests=[
        [[2, 7, 4, 1, 8, 1]],
        [[1]],
        [[3, 3]],
        [[10, 4]],
        [[2, 2, 2]],
        [[1, 3]],
        [[9, 3, 2, 10]],
        [[1000] * 30],
        [[1000] * 29 + [1]],
        [[31, 26, 33, 21, 40]],
        [[_R.randint(1, 1000) for _ in range(30)]],
        [[_R.randint(1, 1000) for _ in range(10000)]],
        [[_R.randint(1, 1000) for _ in range(9999)]],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def lastStoneWeight(self, stones):
        s = sorted(stones)
        while len(s) > 1:
            y = s.pop(); x = s.pop()
            if y != x:
                s.append(y - x)
        return s[0] if s else 0
''',
        '''import heapq
class Solution:
    def lastStoneWeight(self, stones):
        h = list(stones)
        heapq.heapify(h)
        while len(h) > 1:
            x = heapq.heappop(h); y = heapq.heappop(h)
            if y != x:
                heapq.heappush(h, y - x)
        return h[0] if h else 0
''',
    ],
    guide=dict(
        prereqs="Binary heaps; the negation trick for max-heaps with `heapq` (lesson *Binary heaps and Python's heapq*).",
        intuition=r"""
Every round needs "the two largest right now", and the result of the round may be put back. A
structure that repeatedly hands you the maximum while accepting new inserts is exactly a
**max-priority queue**. Python's `heapq` is a min-heap, so store negated weights.
""",
        hints=[
            "Which two stones are needed each round? What data structure returns the maximum quickly and also accepts insertions?",
            "heapq only gives the minimum. How can you turn a min-heap into a max-heap for numbers?",
            "Push -w for every stone. Pop twice, push back -(y - x) if non-zero, and stop when one or zero items remain.",
        ],
        brute_force=r"""
Sort the list each round and take the last two: O(n log n) per round and up to n rounds → $O(n^2 \log n)$.
Sorting once and then appending the difference **without re-sorting** is a common bug (see pitfalls).
""",
        approach=r"""
1. `h = [-s for s in stones]`; `heapify(h)` (O(n)).
2. While at least two stones: pop `y` (heaviest) and `x`; if they differ push `-(y - x)`.
3. Return `-h[0]` or `0`.

**Dry run** `[2,7,4,1,8,1]`: max-heap holds 8 7 4 2 1 1.
8,7 → push 1 → {4,2,1,1,1}. 4,2 → push 2 → {2,1,1,1}. 2,1 → push 1 → {1,1,1}. 1,1 → nothing → {1}. Answer 1.
""",
        complexity="Each round removes at least one stone, so at most n−1 rounds of O(log n) → O(n log n) time, O(n) space (O(1) extra if you negate in place).",
        pitfalls=r"""
- Forgetting to negate when pushing the difference back (mixing signs breaks the heap).
- Sorting once then `append`ing the difference: the new stone is not in its sorted position.
- Returning `h[0]` without negating, or crashing on an empty heap — return `0` when nothing is left.
""",
        follow_up="Last Stone Weight II asks for the minimum possible final weight when you may choose any pair — that is a subset-sum DP, not a heap problem.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="k-closest-points-to-origin",
    title="K Closest Points to Origin",
    difficulty="Medium",
    pattern="Heap / Priority Queue",
    leetcode="https://leetcode.com/problems/k-closest-points-to-origin/",
    neetcode="https://neetcode.io/problems/k-closest-points-to-origin",
    entry="kClosest",
    checker=_KCLOSEST_CHECK,
    description=r"""
Given a list of points `points[i] = [x, y]` in the plane and an integer `k`, return the `k`
points nearest to the origin `(0, 0)` using ordinary Euclidean distance $\sqrt{x^2 + y^2}$.

You may return them **in any order**. If several points tie at the boundary distance, any valid
choice is accepted (the judge checks that your answer has the same multiset of distances as an
optimal answer and that every point really comes from the input).

**Constraints:** `1 <= k <= len(points) <= 10^4`, `-10^4 <= x, y <= 10^4`.

**Example 1:** `points = [[1,3],[-2,2]], k = 1` → `[[-2,2]]` (distance² 8 beats 10).

**Example 2:** `points = [[3,3],[5,-1],[-2,4]], k = 2` → `[[3,3],[-2,4]]` (any order).
""",
    starter='''class Solution:
    def kClosest(self, points: List[List[int]], k: int) -> List[List[int]]:
        pass
''',
    solution='''import heapq

class Solution:
    def kClosest(self, points, k):
        heap = []  # max-heap by distance via negation, size <= k
        for x, y in points:
            d = -(x * x + y * y)
            if len(heap) < k:
                heapq.heappush(heap, (d, x, y))
            elif d > heap[0][0]:
                heapq.heapreplace(heap, (d, x, y))
        return [[x, y] for _, x, y in heap]
''',
    tests=[
        [[[1, 3], [-2, 2]], 1],
        [[[3, 3], [5, -1], [-2, 4]], 2],
        [[[0, 0]], 1],
        [[[1, 1], [1, 1], [2, 2]], 2],
        [[[1, 0], [0, 1], [-1, 0], [0, -1], [5, 5]], 4],
        [[[2, 2], [1, 1], [3, 3]], 3],
        [[[-5, 4], [-6, -5], [4, 6]], 2],
        [[[10000, 10000], [-10000, -10000], [0, 1]], 1],
        [[[1, 2], [2, 1], [0, 3], [3, 0]], 2],
        [[[_R.randint(-10**4, 10**4), _R.randint(-10**4, 10**4)] for _ in range(10**4)], 50],
        [[[_R.randint(-100, 100), _R.randint(-100, 100)] for _ in range(5000)], 2500],
        [[[_R.randint(-10, 10), _R.randint(-10, 10)] for _ in range(300)], 299],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def kClosest(self, points, k):
        return sorted(points, key=lambda p: abs(p[0]) + abs(p[1]))[:k]
''',
        '''import heapq
class Solution:
    def kClosest(self, points, k):
        heap = []
        for x, y in points:
            heapq.heappush(heap, (x * x + y * y, x, y))
            if len(heap) > k:
                heapq.heappop(heap)
        return [[x, y] for _, x, y in heap]
''',
    ],
    guide=dict(
        prereqs="Top-k with a bounded heap (lesson *Heap patterns*); the max-heap negation trick.",
        intuition=r"""
"k smallest of n" is the mirror image of "k largest": keep a **max-heap of size k** holding the best
candidates so far. Its root is the *worst* of the current best k, which is exactly the one a better
newcomer should evict. Compare squared distances — the square root is monotonic, so it never changes the order.
""",
        hints=[
            "You don't need the actual distance; what quantity orders points the same way without floating point?",
            "If you keep the k best points seen so far, which one should be thrown out when a closer point arrives?",
            "Keep a heap of (-dist², x, y) of size k. If a new point's -dist² is greater than the root's, heapreplace.",
        ],
        brute_force="Sort all points by $x^2+y^2$ and slice the first k: O(n log n) time, O(n) space. Perfectly acceptable in an interview as a first answer.",
        approach=r"""
1. For each point compute `d = x*x + y*y` and push `(-d, x, y)`.
2. While the heap has fewer than `k` entries, just push. Otherwise, if `-d > heap[0][0]` (i.e. the new point is closer than the farthest kept point), `heapreplace`.
3. Return the points left in the heap.

**Dry run** `[[3,3],[5,-1],[-2,4]], k=2`: push (−18) and (−26). Root is −26 (farthest, 26). Next (−20): −20 > −26, replace → heap holds 18 and 20 → `[[3,3],[-2,4]]`.

*Alternative:* **Quickselect** partitions around a pivot by distance in average O(n) time, worst O(n²).
""",
        complexity="O(n log k) time, O(k) extra space. Quickselect: O(n) average.",
        pitfalls=r"""
- Using a **min-heap** of size k and popping the smallest — that throws away the closest points (wrong solution #2).
- Using Manhattan distance or `abs`.
- Using `math.sqrt` then comparing floats — works, but slower and unnecessary.
- Pushing tuples `(d, [x, y])` — on ties Python compares the lists, which is fine here but crashes when the payload is not comparable; prefer `(d, x, y)` or add an index tiebreaker.
""",
        follow_up="If points arrive as a stream, the bounded max-heap is the right tool. If k is close to n, keep a heap of the n−k *farthest* instead. Related: *Kth Largest Element in an Array*.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="kth-largest-element-in-an-array",
    title="Kth Largest Element in an Array",
    difficulty="Medium",
    pattern="Heap / Priority Queue",
    leetcode="https://leetcode.com/problems/kth-largest-element-in-an-array/",
    neetcode="https://neetcode.io/problems/kth-largest-element-in-an-array",
    entry="findKthLargest",
    description=r"""
Given an integer array `nums` and an integer `k`, return the value that would sit at position `k`
if the array were sorted from largest to smallest (1-indexed). Duplicates count: the 2nd largest of
`[3, 3, 1]` is `3`.

Try to beat full sorting.

**Constraints:** `1 <= k <= len(nums) <= 10^5` (judge tests go up to 2·10^4), `-10^4 <= nums[i] <= 10^4`.

**Example 1:** `nums = [3,2,1,5,6,4], k = 2` → `5`

**Example 2:** `nums = [3,2,3,1,2,4,5,5,6], k = 4` → `4`
""",
    starter='''class Solution:
    def findKthLargest(self, nums: List[int], k: int) -> int:
        pass
''',
    solution='''import heapq

class Solution:
    def findKthLargest(self, nums, k):
        heap = nums[:k]
        heapq.heapify(heap)
        for x in nums[k:]:
            if x > heap[0]:
                heapq.heapreplace(heap, x)
        return heap[0]
''',
    tests=[
        [[3, 2, 1, 5, 6, 4], 2],
        [[3, 2, 3, 1, 2, 4, 5, 5, 6], 4],
        [[1], 1],
        [[2, 1], 2],
        [[7, 7, 7, 7], 3],
        [[-1, -2, -3, -4], 1],
        [[-1, -2, -3, -4], 4],
        [[5, 2, 4, 1, 3, 6, 0], 7],
        [list(range(20000)), 1],
        [list(range(10000, 0, -1)), 5000],
        [[1] * 10000 + [2] * 10000, 10001],
        [[_R.randint(-10**4, 10**4) for _ in range(20000)], 777],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def findKthLargest(self, nums, k):
        return sorted(set(nums), reverse=True)[k - 1]
''',
        '''class Solution:
    def findKthLargest(self, nums, k):
        return sorted(nums)[k - 1]
''',
    ],
    guide=dict(
        prereqs="Bounded min-heap for top-k; optionally quickselect (partitioning from quicksort).",
        intuition=r"""
Same idea as the stream version: a min-heap of size `k` holds the k largest values seen so far and
its root is the answer. Since all data is available up front, you can also use **quickselect**:
partition around a pivot and recurse into only the side that contains the target index.
""",
        hints=[
            "Sorting works in O(n log n). Can you avoid ordering the elements you'll never report?",
            "Maintain the k largest values in a structure whose minimum is cheap to read and replace.",
            "heapify the first k values, then for each remaining x, if x > heap[0] do heapreplace. Return heap[0].",
        ],
        brute_force="`sorted(nums)[-k]` — O(n log n) time. Fine for a first pass; mention it, then improve.",
        approach=r"""
**Heap approach**

1. `heap = nums[:k]`, `heapify(heap)` — O(k).
2. For every other `x`: if `x > heap[0]`, `heapreplace(heap, x)`.
3. Return `heap[0]`.

Dry run `[3,2,1,5,6,4], k=2`: heap {2,3}. 1: skip. 5 > 2 → {3,5}. 6 > 3 → {5,6}. 4 < 5 skip. Answer 5.

**Quickselect approach** (average O(n)): choose a random pivot, three-way partition into `> pivot`, `== pivot`, `< pivot`. If `k <= len(greater)` recurse into greater; else if `k <= len(greater)+len(equal)` return pivot; else recurse into less with `k` reduced. The three-way split is essential for arrays full of duplicates.
""",
        complexity="Heap: O(n log k) time, O(k) space. Quickselect: O(n) expected, O(n²) worst, O(1)–O(n) space depending on implementation.",
        pitfalls=r"""
- De-duplicating with `set` (k-th largest counts repeated values).
- Off-by-one: `sorted(nums)[k-1]` is the k-th **smallest**.
- Two-way quickselect on `[1]*50000 + [2]*50000` degenerates to quadratic time; use a three-way partition or random pivots.
""",
        follow_up="`heapq.nlargest(k, nums)[-1]` is a one-liner using the same idea. Related: *K Closest Points*, *Top K Frequent Elements*, *Find Median from Data Stream*.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="task-scheduler",
    title="Task Scheduler",
    difficulty="Medium",
    pattern="Heap / Priority Queue",
    leetcode="https://leetcode.com/problems/task-scheduler/",
    neetcode="https://neetcode.io/problems/task-scheduling",
    entry="leastInterval",
    description=r"""
A CPU must run a batch of tasks, each labelled by an uppercase letter. Every task takes one time unit.
In each unit the CPU either runs one task or sits **idle**. After running a task with some label,
the CPU must wait at least `n` units before running another task with the **same** label (other labels may run in between).

Tasks may be done in any order. Return the minimum number of time units needed to finish all of them.

**Constraints:** `1 <= len(tasks) <= 10^4`, each task is `'A'`–`'Z'`, `0 <= n <= 100`.

**Example 1:** `tasks = ["A","A","A","B","B","B"], n = 2` → `8`
(`A B idle A B idle A B`)

**Example 2:** `tasks = ["A","C","A","B","D","B"], n = 1` → `6` (no idling needed)

**Example 3:** `tasks = ["A","A","A","B","B","B"], n = 3` → `10`
""",
    starter='''class Solution:
    def leastInterval(self, tasks: List[str], n: int) -> int:
        pass
''',
    solution='''import heapq
from collections import Counter, deque

class Solution:
    def leastInterval(self, tasks, n):
        heap = [-c for c in Counter(tasks).values()]
        heapq.heapify(heap)
        cooling = deque()  # (time it becomes available, negative remaining count)
        time = 0
        while heap or cooling:
            time += 1
            if heap:
                c = heapq.heappop(heap) + 1
                if c:
                    cooling.append((time + n, c))
            else:
                time = cooling[0][0]  # jump over idle time
            if cooling and cooling[0][0] == time:
                heapq.heappush(heap, cooling.popleft()[1])
        return time
''',
    tests=[
        [["A", "A", "A", "B", "B", "B"], 2],
        [["A", "C", "A", "B", "D", "B"], 1],
        [["A", "A", "A", "B", "B", "B"], 3],
        [["A"], 5],
        [["A", "A", "A", "A"], 0],
        [["A", "A", "A", "A"], 3],
        [["A", "A", "A", "A", "A", "A", "B", "C", "D", "E", "F", "G"], 2],
        [["A", "B", "C", "D", "E", "A", "B", "C", "D", "E"], 4],
        [list("AAABBBCCCDDE"), 2],
        [list("AAAABBBBCCCC"), 1],
        [[chr(65 + _R.randint(0, 25)) for _ in range(10000)], 100],
        [[chr(65 + _R.randint(0, 3)) for _ in range(10000)], 7],
        [["Z"] * 10000, 100],
    ],
    examples=3,
    wrong_solutions=[
        '''from collections import Counter
class Solution:
    def leastInterval(self, tasks, n):
        m = max(Counter(tasks).values())
        return (m - 1) * (n + 1) + 1
''',
        '''class Solution:
    def leastInterval(self, tasks, n):
        return len(tasks)
''',
    ],
    guide=dict(
        prereqs="Max-heap via negation; a queue for items that are temporarily unavailable (lesson *Heap patterns*, scheduling section).",
        intuition=r"""
Greedy: at every time step, run the available task with the **most remaining copies**. The most
frequent task is the bottleneck — if you postpone it, its copies bunch up at the end and force idle
time. A max-heap gives the most frequent available label; a FIFO queue holds labels that are cooling
down, each tagged with the time it becomes available again.

There is also a closed form. Let `maxf` be the highest frequency and `cnt` the number of labels with
that frequency. Lay out `maxf - 1` "frames" of length `n + 1` followed by a final partial frame of `cnt`
tasks: the answer is `max(len(tasks), (maxf - 1) * (n + 1) + cnt)`.
""",
        hints=[
            "Which task is the most dangerous to postpone? Think about the task that appears most often.",
            "Simulate time: a max-heap of remaining counts for ready tasks, and a queue of (ready_time, count) for tasks cooling down.",
            "Or count: (maxFreq − 1) full frames of size n+1, plus the number of tasks tied for maxFreq; the answer can never be below len(tasks).",
        ],
        brute_force="Try every ordering of tasks and simulate — factorial time. Even a naive simulation that scans all 26 labels each time step is fine (O(26 · answer)), and is a good stepping stone to the heap.",
        approach=r"""
**Heap + cooldown queue simulation**

1. Count frequencies; push negated counts into a max-heap.
2. Each tick `time += 1`. If the heap is non-empty, pop the largest count, decrement it, and if copies remain enqueue `(time + n, count)`.
3. If the heap is empty but the queue isn't, the CPU idles — jump `time` straight to the front item's ready time.
4. If the front of the queue becomes ready at `time`, move it back to the heap.

**Dry run** `AAABBB, n = 2` (a task run at tick t returns to the heap after tick t + 2):

| tick | heap before | run | cooling queue after |
|---|---|---|---|
| 1 | A3 B3 | A | (A2, ready after 3) |
| 2 | B3 | B | (A2, 3) (B2, 4) |
| 3 | – | idle | A2 returns to heap |
| 4 | A2 | A | B2 returns; (A1, 6) |
| 5 | B2 | B | (A1, 6) (B1, 7) |
| 6 | – | idle | A1 returns |
| 7 | A1 | A | B1 returns |
| 8 | B1 | B | done |

**Formula:** maxf = 3, cnt = 2 → (3 − 1)·3 + 2 = 8, and max(6, 8) = 8.
""",
        complexity="Simulation: O(T log 26) = O(T) where T is the answer (≤ len·(n+1)); jumping over idle stretches keeps it O(len(tasks) log 26). Formula: O(len(tasks)) time, O(1) space (26 counters).",
        pitfalls=r"""
- Forgetting that the answer is at least `len(tasks)`: with many distinct labels no idling is needed and the frame formula undercounts (e.g. `AABBCCDD`, `n = 1`: frames give 6, the truth is 8).
- Forgetting the `cnt` term — several labels can share the maximum frequency.
- Off-by-one on the ready time: a task run at time `t` may run again at `t + n + 1`, i.e. it is re-admitted *after* tick `t + n`.
""",
        follow_up="If the order of tasks were fixed (LeetCode 2365 *Task Scheduler II*), you'd use a hash map of last-run times instead. Related: *Reorganize String* (n = 1, return an arrangement).",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="design-twitter",
    title="Design Twitter",
    difficulty="Medium",
    pattern="Heap / Priority Queue",
    leetcode="https://leetcode.com/problems/design-twitter/",
    neetcode="https://neetcode.io/problems/design-twitter-feed",
    kind="class",
    entry="Twitter",
    description=r"""
Design a tiny social network.

- `Twitter()` — create an empty network.
- `postTweet(userId, tweetId)` — user `userId` publishes a tweet with the unique id `tweetId`.
- `getNewsFeed(userId)` — return the ids of the **10 most recent** tweets that were posted either by
  the user or by someone they currently follow, ordered **newest first** (fewer than 10 if there aren't enough).
- `follow(followerId, followeeId)` — the follower starts following the followee (no effect if already following).
- `unfollow(followerId, followeeId)` — stop following (no effect if not following).

"Recent" means order of posting calls, not tweet id. A user always sees their own tweets; a user
following themselves (or unfollowing themselves) changes nothing.

**Constraints:** `1 <= userId <= 500`, tweet ids are unique, at most `3 * 10^4` calls overall.

**Example**

```
postTweet(1, 5)
getNewsFeed(1)   -> [5]
follow(1, 2)
postTweet(2, 6)
getNewsFeed(1)   -> [6, 5]
unfollow(1, 2)
getNewsFeed(1)   -> [5]
```
""",
    starter='''class Twitter:

    def __init__(self):
        pass

    def postTweet(self, userId: int, tweetId: int) -> None:
        pass

    def getNewsFeed(self, userId: int) -> List[int]:
        pass

    def follow(self, followerId: int, followeeId: int) -> None:
        pass

    def unfollow(self, followerId: int, followeeId: int) -> None:
        pass
''',
    solution='''import heapq
from collections import defaultdict

class Twitter:
    def __init__(self):
        self.time = 0
        self.tweets = defaultdict(list)     # user -> [(time, tweetId)] in posting order
        self.following = defaultdict(set)

    def postTweet(self, userId, tweetId):
        self.time += 1
        self.tweets[userId].append((self.time, tweetId))

    def getNewsFeed(self, userId):
        users = self.following[userId] | {userId}
        heap = []
        for u in users:
            if self.tweets[u]:
                i = len(self.tweets[u]) - 1
                t, tid = self.tweets[u][i]
                heap.append((-t, tid, u, i))
        heapq.heapify(heap)
        feed = []
        while heap and len(feed) < 10:
            _, tid, u, i = heapq.heappop(heap)
            feed.append(tid)
            if i > 0:
                t, nid = self.tweets[u][i - 1]
                heapq.heappush(heap, (-t, nid, u, i - 1))
        return feed

    def follow(self, followerId, followeeId):
        if followerId != followeeId:
            self.following[followerId].add(followeeId)

    def unfollow(self, followerId, followeeId):
        self.following[followerId].discard(followeeId)
''',
    tests=[
        [["Twitter", "postTweet", "getNewsFeed", "follow", "postTweet", "getNewsFeed", "unfollow", "getNewsFeed"],
         [[], [1, 5], [1], [1, 2], [2, 6], [1], [1, 2], [1]]],
        [["Twitter", "getNewsFeed"], [[], [7]]],
        [["Twitter", "postTweet", "postTweet", "postTweet", "postTweet", "postTweet", "postTweet", "postTweet",
          "postTweet", "postTweet", "postTweet", "postTweet", "postTweet", "getNewsFeed"],
         [[], [1, 5], [1, 3], [1, 101], [1, 13], [1, 10], [1, 2], [1, 94], [1, 505], [1, 333], [1, 22], [1, 11], [1, 205], [1]]],
        [["Twitter", "postTweet", "follow", "follow", "getNewsFeed", "unfollow", "getNewsFeed"],
         [[], [1, 1], [1, 1], [2, 1], [2], [1, 1], [1]]],
        [["Twitter", "postTweet", "postTweet", "unfollow", "follow", "getNewsFeed", "follow", "getNewsFeed"],
         [[], [2, 5], [1, 3], [1, 2], [1, 2], [1], [1, 2], [1]]],
        [["Twitter", "follow", "postTweet", "postTweet", "postTweet", "getNewsFeed", "getNewsFeed"],
         [[], [3, 4], [4, 100], [3, 1], [4, 50], [3], [4]]],
        _twitter_ops(random.Random(1), 60, 3),
        _twitter_ops(random.Random(2), 300, 5),
        _twitter_ops(random.Random(3), 1500, 20),
        _twitter_ops(random.Random(4), 2000, 8),
        _twitter_ops(random.Random(5), 1500, 100),
    ],
    examples=1,
    wrong_solutions=[
        '''from collections import defaultdict
class Twitter:
    def __init__(self):
        self.tweets = defaultdict(list)
        self.following = defaultdict(set)
    def postTweet(self, userId, tweetId):
        self.tweets[userId].append(tweetId)
    def getNewsFeed(self, userId):
        ids = list(self.tweets[userId])
        for f in self.following[userId]:
            ids += self.tweets[f]
        return sorted(ids, reverse=True)[:10]
    def follow(self, a, b):
        self.following[a].add(b)
    def unfollow(self, a, b):
        self.following[a].discard(b)
''',
        '''from collections import defaultdict
class Twitter:
    def __init__(self):
        self.t = 0
        self.tweets = defaultdict(list)
        self.following = defaultdict(set)
    def postTweet(self, userId, tweetId):
        self.t += 1
        self.tweets[userId].append((self.t, tweetId))
    def getNewsFeed(self, userId):
        ids = list(self.tweets[userId])
        for f in self.following[userId]:
            ids += self.tweets[f]
        return [x for _, x in sorted(ids, reverse=True)[:10]]
    def follow(self, a, b):
        self.following[a].add(b)
    def unfollow(self, a, b):
        self.following[a].discard(b)
''',
    ],
    guide=dict(
        prereqs="Hash maps of sets; merging k sorted lists with a heap (lesson *Heap patterns*).",
        intuition=r"""
Each user's tweets, stored in posting order, form a list sorted by time. A news feed is the **first
10 items of a k-way merge** of the lists belonging to the user and their followees. Put the newest
tweet of each list into a max-heap (keyed on timestamp); pop the newest overall, then push the next
older tweet from the same list. Stop after 10 pops — you never touch older tweets.
""",
        hints=[
            "Tweet ids are not timestamps. What extra piece of state lets you know which tweet is more recent?",
            "Each user's tweets are already sorted by time. Getting the 10 newest across several sorted lists is a classic heap problem.",
            "Seed a heap with (−time, tweetId, user, index) for the last tweet of each relevant user; pop, record, push that user's index−1; repeat ≤ 10 times.",
        ],
        brute_force="Gather every tweet of the user and their followees, sort by time, take 10: O(T log T) per feed request where T is the number of relevant tweets. Correct, but grows with history.",
        approach=r"""
State: a global counter `time`, `tweets[user] = [(time, id), ...]`, and `following[user] = set()`.

`getNewsFeed(u)`:
1. `users = following[u] | {u}`.
2. For each user with tweets, push `(-time_of_last, id, user, last_index)`.
3. Pop up to 10 times; after popping `(.., user, i)` push that user's tweet at `i-1` if it exists.

Dry run with the example: after `postTweet(1,5)` (t=1), `follow(1,2)`, `postTweet(2,6)` (t=2): heap seeds (−2,6) from user 2 and (−1,5) from user 1 → pops 6 then 5 → `[6, 5]`.

`follow` ignores self-follows; `unfollow` uses `discard` so unfollowing a stranger is harmless.
""",
        complexity="post/follow/unfollow O(1). getNewsFeed O(F + 10 log F) where F is the number of followees (heapify is linear). Space O(users + tweets + follow edges).",
        pitfalls=r"""
- Sorting by **tweet id** instead of posting time (wrong solution #1).
- Letting self-follow produce duplicate tweets in the feed, or letting `unfollow(u, u)` hide your own tweets — always add `u` separately.
- Using `remove` on a set for unfollow → `KeyError` when not following.
- Pushing all tweets of all followees into the heap — correct but loses the k-way-merge advantage.
""",
        follow_up="At real scale this is the *fan-out on write vs. fan-out on read* trade-off: precompute feeds when celebrities aren't involved, merge on read when they are. Related: *Merge K Sorted Lists*.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="find-median-from-data-stream",
    title="Find Median from Data Stream",
    difficulty="Hard",
    pattern="Heap / Priority Queue",
    leetcode="https://leetcode.com/problems/find-median-from-data-stream/",
    neetcode="https://neetcode.io/problems/find-median-in-a-data-stream",
    kind="class",
    entry="MedianFinder",
    compare="float",
    tolerance=1e-5,
    description=r"""
The **median** of a sorted list is its middle value, or the average of the two middle values when
the length is even (median of `[2,3,4]` is `3`, of `[2,3]` is `2.5`).

Implement a class that receives numbers one at a time and can report the median at any moment.

- `MedianFinder()` — start with no numbers.
- `addNum(num)` — add an integer to the collection.
- `findMedian()` — return the median of everything added so far (as a float; answers within `1e-5` are accepted).

**Constraints:** `-10^5 <= num <= 10^5`; `findMedian` is only called after at least one `addNum`;
up to `5 * 10^4` calls.

**Example**

```
addNum(1); addNum(2)
findMedian() -> 1.5
addNum(3)
findMedian() -> 2.0
```
""",
    starter='''class MedianFinder:

    def __init__(self):
        pass

    def addNum(self, num: int) -> None:
        pass

    def findMedian(self) -> float:
        pass
''',
    solution='''import heapq

class MedianFinder:
    def __init__(self):
        self.lo = []  # max-heap (negated) of the smaller half
        self.hi = []  # min-heap of the larger half

    def addNum(self, num):
        heapq.heappush(self.lo, -num)
        heapq.heappush(self.hi, -heapq.heappop(self.lo))
        if len(self.hi) > len(self.lo):
            heapq.heappush(self.lo, -heapq.heappop(self.hi))

    def findMedian(self):
        if len(self.lo) > len(self.hi):
            return float(-self.lo[0])
        return (-self.lo[0] + self.hi[0]) / 2.0
''',
    tests=[
        [["MedianFinder", "addNum", "addNum", "findMedian", "addNum", "findMedian"], [[], [1], [2], [], [3], []]],
        [["MedianFinder", "addNum", "findMedian"], [[], [-7], []]],
        [["MedianFinder", "addNum", "addNum", "findMedian"], [[], [5], [5], []]],
        [["MedianFinder", "addNum", "findMedian", "addNum", "findMedian", "addNum", "findMedian", "addNum", "findMedian", "addNum", "findMedian"],
         [[], [6], [], [10], [], [2], [], [6], [], [5], []]],
        [["MedianFinder", "addNum", "addNum", "addNum", "addNum", "findMedian"], [[], [-1], [-2], [-3], [-4], []]],
        [["MedianFinder", "addNum", "addNum", "addNum", "findMedian", "addNum", "findMedian"], [[], [100000], [-100000], [0], [], [1], []]],
        [["MedianFinder"] + ["addNum", "findMedian"] * 10, [[]] + sum([[[i], []] for i in range(10, 0, -1)], [])],
        _median_ops(random.Random(11), 50, -10, 10),
        _median_ops(random.Random(12), 500, -100000, 100000),
        _median_ops(random.Random(13), 4000, -100000, 100000),
        _median_ops(random.Random(14), 4000, 0, 5),
    ],
    examples=1,
    wrong_solutions=[
        '''class MedianFinder:
    def __init__(self):
        self.a = []
    def addNum(self, num):
        self.a.append(num)
    def findMedian(self):
        return float(self.a[len(self.a) // 2])
''',
        '''import heapq
class MedianFinder:
    def __init__(self):
        self.lo = []; self.hi = []
    def addNum(self, num):
        if len(self.lo) <= len(self.hi):
            heapq.heappush(self.lo, -num)
        else:
            heapq.heappush(self.hi, num)
    def findMedian(self):
        if len(self.lo) > len(self.hi):
            return float(-self.lo[0])
        return (-self.lo[0] + self.hi[0]) / 2.0
''',
    ],
    guide=dict(
        prereqs="Two-heap pattern (lesson *Heap patterns*); max-heap via negation.",
        intuition=r"""
Split the numbers into a **lower half** and an **upper half**. If you can see the largest of the
lower half and the smallest of the upper half instantly, the median is one of those (or their
average). That's a **max-heap** for the lower half and a **min-heap** for the upper half, kept
balanced so `len(lo) == len(hi)` or `len(lo) == len(hi) + 1`.
""",
        hints=[
            "The median only depends on the one or two values in the middle. What if you kept the 'left half' and 'right half' separately?",
            "You need the max of the left half and the min of the right half fast — two different heaps.",
            "Push into lo, move lo's max to hi (this guarantees ordering), then if hi became bigger, move hi's min back to lo.",
        ],
        brute_force="Keep a list and sort on every `findMedian` → O(n log n) per query. `bisect.insort` makes queries O(1) but inserts O(n) due to shifting.",
        approach=r"""
Invariants: every element of `lo` ≤ every element of `hi`; `len(lo) - len(hi)` is 0 or 1.

`addNum(x)`:
1. push `x` into `lo` (as `-x`);
2. pop the max of `lo` and push it into `hi` — this routes `x` to the correct side even if it was large;
3. if `len(hi) > len(lo)`, move `hi`'s min back to `lo`.

`findMedian`: if `lo` is bigger, return its max; else average the two tops.

**Dry run** 6, 10, 2, 6, 5:

| add | lo (max-heap) | hi (min-heap) | median |
|---|---|---|---|
| 6 | 6 | – | 6 |
| 10 | 6 | 10 | 8 |
| 2 | 2 6 | 10 | 6 |
| 6 | 2 6 | 6 10 | 6 |
| 5 | 2 5 6 | 6 10 | 6 |
""",
        complexity="addNum O(log n) (a constant number of pushes/pops), findMedian O(1). Space O(n).",
        pitfalls=r"""
- Balancing only by size without enforcing the ordering invariant (wrong solution #2) — a large number can sit in the lower half.
- Forgetting to negate when moving values between heaps.
- Integer division for the even case — return `/ 2` (float) not `// 2`.
""",
        follow_up="If all numbers are in [0, 100], use a 101-bucket counting array. If 99% are in that range, buckets plus two overflow counters. For a *sliding-window* median, add lazy deletion (LeetCode 480).",
    ),
),
]
