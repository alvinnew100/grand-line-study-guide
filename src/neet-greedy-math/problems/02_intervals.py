import random

_r = random.Random(252)


def _disjoint(n, gap=5, maxlen=5):
    out, x = [], 0
    for _ in range(n):
        x += _r.randint(1, gap)
        L = _r.randint(0, maxlen)
        out.append([x, x + L])
        x += L
    return out


def _rand_intervals(n, hi=10 ** 6, maxlen=1000):
    out = []
    for _ in range(n):
        s = _r.randint(0, hi)
        out.append([s, s + _r.randint(1, maxlen)])
    return out


_ins_big = _disjoint(5000)
_ins_new = [_ins_big[1500][0] + 1, _ins_big[3000][1] - 1]
_merge_big = _rand_intervals(6000)
_merge_chain = [[i, i + 1] for i in range(0, 10000, 2)]  # touching? no: [0,1],[2,3] disjoint
_erase_big = _rand_intervals(6000, hi=10 ** 5, maxlen=100)
_meet_big_ok = [[2 * i, 2 * i + 2] for i in range(10000)]
_r.shuffle(_meet_big_ok)
_meet_big_bad = _meet_big_ok[:] + [[7, 9]]
_rooms_big = _rand_intervals(10000, hi=10 ** 5, maxlen=500)
_mi_int = _rand_intervals(5000, hi=10 ** 6, maxlen=5000)
_mi_q = [_r.randint(0, 10 ** 6 + 5000) for _ in range(5000)]

PROBLEMS = [
# ------------------------------------------------------------------ Insert Interval
dict(
    id="insert-interval",
    title="Insert Interval",
    difficulty="Medium",
    pattern="Intervals",
    leetcode="https://leetcode.com/problems/insert-interval/",
    neetcode="https://neetcode.io/problems/insert-new-interval",
    entry="insert",
    description=r"""
You are given `intervals`, a list of **non-overlapping** closed intervals `[start, end]` already
sorted by `start`, and one more interval `newInterval`. Insert `newInterval` and merge anything it
overlaps, so that the result is still sorted and non-overlapping. Return the new list.
Intervals that share an endpoint (e.g. `[1,3]` and `[3,5]`) overlap and must be merged.

**Constraints**
- `0 <= len(intervals) <= 10^4`, `0 <= start <= end <= 10^5`

**Example 1:** `intervals = [[1,3],[6,9]], newInterval = [2,5]` → `[[1,5],[6,9]]`.

**Example 2:** `intervals = [[1,2],[3,5],[6,7],[8,10],[12,16]], newInterval = [4,8]`
→ `[[1,2],[3,10],[12,16]]`.
""",
    starter='''class Solution:
    def insert(self, intervals: List[List[int]], newInterval: List[int]) -> List[List[int]]:
        pass
''',
    solution='''class Solution:
    def insert(self, intervals, newInterval):
        out = []
        s, e = newInterval
        i, n = 0, len(intervals)
        while i < n and intervals[i][1] < s:          # entirely to the left
            out.append(intervals[i]); i += 1
        while i < n and intervals[i][0] <= e:         # overlaps: absorb
            s = min(s, intervals[i][0])
            e = max(e, intervals[i][1])
            i += 1
        out.append([s, e])
        out.extend(intervals[i:])                     # entirely to the right
        return out
''',
    tests=[
        [[[1, 3], [6, 9]], [2, 5]],
        [[[1, 2], [3, 5], [6, 7], [8, 10], [12, 16]], [4, 8]],
        [[], [5, 7]],
        [[[1, 5]], [2, 3]],
        [[[1, 5]], [6, 8]],
        [[[3, 5]], [0, 1]],
        [[[1, 5]], [0, 0]],
        [[[1, 3], [5, 7]], [3, 5]],
        [[[1, 2], [4, 5]], [0, 10]],
        [[[1, 2], [5, 6]], [3, 4]],
        [[[0, 0], [2, 2]], [1, 1]],
        [_ins_big, _ins_new],
        [_ins_big, [10 ** 7, 10 ** 7 + 1]],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def insert(self, intervals, newInterval):
        out = []
        s, e = newInterval
        i, n = 0, len(intervals)
        while i < n and intervals[i][1] < s:
            out.append(intervals[i]); i += 1
        while i < n and intervals[i][0] < e:          # misses touching endpoints
            s = min(s, intervals[i][0]); e = max(e, intervals[i][1]); i += 1
        out.append([s, e])
        return out + intervals[i:]
''',
        '''class Solution:
    def insert(self, intervals, newInterval):
        return sorted(intervals + [newInterval])
''',
    ],
    guide=dict(
        prereqs="The overlap test for two intervals (lesson *Interval fundamentals*).",
        intuition=r"""
Because the input is already sorted and disjoint, the existing intervals fall into exactly three
consecutive groups relative to `newInterval = [s, e]`: those that end **before** `s` (untouched,
left), those that **overlap** `[s, e]` (to be swallowed into one big interval), and those that start
**after** `e` (untouched, right). One left-to-right pass handles each group in turn.
""",
        hints=[
            "Which existing intervals cannot possibly touch newInterval?",
            "Copy everything with end < s; then absorb everything with start <= e by widening [s, e].",
            "After absorbing, append [s, e] and then the rest unchanged.",
        ],
        brute_force="Append `newInterval`, sort, then run the *merge intervals* routine: **O(n log n)**. Correct, but it ignores the sortedness you were given.",
        approach=r"""
**Dry run** `[[1,2],[3,5],[6,7],[8,10],[12,16]]`, new `[4,8]`:
1. Left group: `[1,2]` (2 < 4). Stop at `[3,5]` (5 ≥ 4).
2. Absorb `[3,5]` → `[3,8]`; `[6,7]` → `[3,8]`; `[8,10]` (8 ≤ 8) → `[3,10]`; `[12,16]` has 12 > 10, stop.
3. Output `[[1,2],[3,10],[12,16]]`.
""",
        complexity="Time **O(n)**, space O(n) for the output (O(1) extra). Binary search can find the boundaries in O(log n), but building the output is still O(n).",
        pitfalls=r"""
- Using `<` instead of `<=` in the overlap condition fails to merge touching intervals like `[1,3]+[3,5]`.
- Forgetting the empty-input case, or forgetting to append the remaining right-side intervals.
- Mutating `newInterval` / input lists in place can surprise callers; build a new list.
""",
        follow_up="*Merge Intervals* (unsorted input), *Range Module* (many inserts/removals — balanced tree or sorted list).",
    ),
),
# ------------------------------------------------------------------ Merge Intervals
dict(
    id="merge-intervals",
    title="Merge Intervals",
    difficulty="Medium",
    pattern="Intervals / sorting",
    leetcode="https://leetcode.com/problems/merge-intervals/",
    neetcode="https://neetcode.io/problems/merge-intervals",
    entry="merge",
    compare="unordered",
    description=r"""
Given a list of closed intervals `[start, end]` in arbitrary order, merge every group of
overlapping intervals (sharing a single point counts as overlapping) and return the resulting
non-overlapping intervals. Any order of the output list is accepted.

**Constraints**
- `1 <= len(intervals) <= 10^4`, `0 <= start <= end <= 10^4` (tests here use bigger values)

**Example 1:** `[[1,3],[2,6],[8,10],[15,18]]` → `[[1,6],[8,10],[15,18]]`.

**Example 2:** `[[1,4],[4,5]]` → `[[1,5]]`.
""",
    starter='''class Solution:
    def merge(self, intervals: List[List[int]]) -> List[List[int]]:
        pass
''',
    solution='''class Solution:
    def merge(self, intervals):
        intervals = sorted(intervals, key=lambda iv: iv[0])
        out = [list(intervals[0])]
        for s, e in intervals[1:]:
            if s <= out[-1][1]:                 # overlaps the last merged block
                out[-1][1] = max(out[-1][1], e)
            else:
                out.append([s, e])
        return out
''',
    tests=[
        [[[1, 3], [2, 6], [8, 10], [15, 18]]],
        [[[1, 4], [4, 5]]],
        [[[1, 4]]],
        [[[1, 4], [2, 3]]],
        [[[1, 4], [0, 0]]],
        [[[4, 7], [1, 4]]],
        [[[1, 10], [2, 3], [4, 5], [6, 7]]],
        [[[2, 3], [4, 5], [6, 7], [8, 9], [1, 10]]],
        [[[0, 0], [0, 0]]],
        [[[5, 5], [1, 2], [3, 4]]],
        [_merge_big],
        [_merge_chain],
        [[[i, i + 1] for i in range(6000)]],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def merge(self, intervals):
        intervals = sorted(intervals)
        out = [list(intervals[0])]
        for s, e in intervals[1:]:
            if s <= out[-1][1]:
                out[-1][1] = e                 # forgets max(): contained intervals shrink it
            else:
                out.append([s, e])
        return out
''',
        '''class Solution:
    def merge(self, intervals):
        out = [list(intervals[0])]             # forgets to sort
        for s, e in intervals[1:]:
            if s <= out[-1][1]:
                out[-1][1] = max(out[-1][1], e)
            else:
                out.append([s, e])
        return out
''',
    ],
    guide=dict(
        prereqs="Sorting with a key; the overlap test.",
        intuition=r"""
Once intervals are sorted by start, any interval that overlaps the current merged block must come
**right after** it — nothing further down the list can start earlier. So you only ever compare an
interval with the *last* block in the output: either it overlaps (extend the block's end) or it
starts a new block.
""",
        hints=[
            "Sort by start time.",
            "Compare each interval only with the last merged interval.",
            "If start <= last_end, set last_end = max(last_end, end); else append.",
        ],
        brute_force="Repeatedly scan all pairs, merging any overlapping pair until nothing changes — O(n²) per pass, O(n³) worst case. Or union-find over overlapping pairs: O(n²).",
        approach=r"""
**Dry run** `[[1,3],[2,6],[8,10],[15,18]]` (already sorted):
- out = `[[1,3]]`
- `[2,6]`: 2 ≤ 3 → `[1,6]`
- `[8,10]`: 8 > 6 → append
- `[15,18]`: append → `[[1,6],[8,10],[15,18]]`.

**Correctness sketch.** Invariant: `out` holds the merged result of the first k sorted intervals,
and its last block has the largest end so far. A new interval with `s > last_end` cannot overlap any
block (all earlier blocks end even sooner), so it starts a fresh block.
""",
        complexity="Time **O(n log n)** (sorting dominates), space **O(n)** for the sorted copy/output.",
        pitfalls=r"""
- `out[-1][1] = e` instead of `max(...)`: `[1,10]` followed by `[2,3]` would shrink to `[1,3]`.
- Forgetting to sort.
- Strict `<` misses touching intervals such as `[1,4],[4,5]`.
""",
        follow_up="*Insert Interval*, *Interval List Intersections* (two pointers), *Employee Free Time* (merge then report gaps).",
    ),
),
# ------------------------------------------------------------------ Non-overlapping
dict(
    id="non-overlapping-intervals",
    title="Non-overlapping Intervals",
    difficulty="Medium",
    pattern="Intervals / greedy by end",
    leetcode="https://leetcode.com/problems/non-overlapping-intervals/",
    neetcode="https://neetcode.io/problems/non-overlapping-intervals",
    entry="eraseOverlapIntervals",
    description=r"""
Given intervals `[start, end]`, return the minimum number of intervals you must delete so that the
remaining ones do not overlap. Here intervals that merely **touch** (like `[1,2]` and `[2,3]`) do
*not* overlap.

**Constraints**
- `1 <= len(intervals) <= 10^5`, `-5·10^4 <= start < end <= 5·10^4`

**Example 1:** `[[1,2],[2,3],[3,4],[1,3]]` → `1` (drop `[1,3]`).

**Example 2:** `[[1,2],[1,2],[1,2]]` → `2`.
""",
    starter='''class Solution:
    def eraseOverlapIntervals(self, intervals: List[List[int]]) -> int:
        pass
''',
    solution='''class Solution:
    def eraseOverlapIntervals(self, intervals):
        intervals = sorted(intervals, key=lambda iv: iv[1])   # earliest finish first
        kept = 0
        last_end = float("-inf")
        for s, e in intervals:
            if s >= last_end:          # compatible: keep it
                kept += 1
                last_end = e
        return len(intervals) - kept
''',
    tests=[
        [[[1, 2], [2, 3], [3, 4], [1, 3]]],
        [[[1, 2], [1, 2], [1, 2]]],
        [[[1, 2], [2, 3]]],
        [[[1, 100], [11, 22], [1, 11], [2, 12]]],
        [[[0, 2], [1, 3], [2, 4], [3, 5], [4, 6]]],
        [[[1, 2]]],
        [[[-5, -1], [-3, 2], [0, 1]]],
        [[[1, 10], [2, 3], [3, 4], [4, 5]]],
        [[[-50000, 50000], [0, 1]]],
        [[[0, 1], [3, 4], [1, 2]]],
        [_erase_big],
        [[[i, i + 2] for i in range(8000)]],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def eraseOverlapIntervals(self, intervals):
        intervals = sorted(intervals)              # sorts by START and keeps first: wrong greedy
        kept, last_end = 0, float("-inf")
        for s, e in intervals:
            if s >= last_end:
                kept += 1; last_end = e
        return len(intervals) - kept
''',
        '''class Solution:
    def eraseOverlapIntervals(self, intervals):
        intervals = sorted(intervals, key=lambda iv: iv[1])
        kept, last_end = 0, float("-inf")
        for s, e in intervals:
            if s > last_end:                       # treats touching as overlapping
                kept += 1; last_end = e
        return len(intervals) - kept
''',
    ],
    guide=dict(
        prereqs="Lesson *When greedy works* — this is the classic **interval scheduling** problem.",
        intuition=r"""
Removing the fewest intervals = **keeping the most** mutually compatible ones. The classic greedy:
sort by **end** time and keep every interval that starts at or after the end of the last kept one.
Finishing as early as possible leaves the most room for everything after.
""",
        hints=[
            "Flip the question: what is the maximum number of intervals you can keep?",
            "Which interval should be the first one you keep? Think about end times.",
            "Sort by end; keep an interval when start >= last kept end; answer = n - kept.",
        ],
        brute_force="Try every subset and check compatibility — O(2ⁿ·n). A DP over intervals sorted by start with binary search is O(n log n) but more complex.",
        approach=r"""
**Dry run** `[[1,2],[2,3],[3,4],[1,3]]` sorted by end → `[1,2],[2,3],[1,3],[3,4]`:
- `[1,2]` keep (last_end = 2)
- `[2,3]` 2 ≥ 2 keep (3)
- `[1,3]` 1 < 3 skip
- `[3,4]` keep. kept = 3, answer 4 − 3 = **1**.

**Exchange argument.** Let `g` be the interval with the earliest end and `O` an optimal set. If
`g ∉ O`, replace the first interval of `O` with `g`: `g` ends no later, so it still does not overlap
the rest. Same size, now contains `g`. Recurse on what remains to the right of `g`.

Equivalent variant: sort by start, and on overlap delete the one with the **larger end**
(`last_end = min(last_end, e)`).
""",
        complexity="Time **O(n log n)**, space O(n) (sorted copy).",
        pitfalls=r"""
- Sorting by start and greedily keeping the first one: `[[1,100],[11,22],[1,11],[2,12]]` fails.
- Treating touching intervals as overlapping (`>` vs `>=`).
- Shortest-interval-first is another wrong greedy (see lesson counterexamples).
""",
        follow_up="*Minimum Number of Arrows to Burst Balloons* (same greedy; touching counts as overlap there). Weighted version (*Maximum Profit in Job Scheduling*) needs DP.",
    ),
),
# ------------------------------------------------------------------ Meeting Rooms
dict(
    id="meeting-rooms",
    title="Meeting Rooms",
    difficulty="Easy",
    pattern="Intervals / sorting",
    leetcode="https://leetcode.com/problems/meeting-rooms/",
    neetcode="https://neetcode.io/problems/meeting-schedule",
    entry="canAttendMeetings",
    description=r"""
Each meeting is a half-open time range `[start, end)` given as `[start, end]`. Can one person attend
**all** of them? A meeting ending at time `t` and another starting at `t` do not conflict.

(LeetCode/NeetCode pass interval objects; here each meeting is a two-element list.)

**Constraints**
- `0 <= len(intervals) <= 10^4`, `0 <= start < end <= 10^6`

**Example 1:** `[[0,30],[5,10],[15,20]]` → `False`.

**Example 2:** `[[7,10],[2,4]]` → `True`.
""",
    starter='''class Solution:
    def canAttendMeetings(self, intervals: List[List[int]]) -> bool:
        pass
''',
    solution='''class Solution:
    def canAttendMeetings(self, intervals):
        intervals = sorted(intervals)
        for i in range(1, len(intervals)):
            if intervals[i][0] < intervals[i - 1][1]:   # starts before previous ends
                return False
        return True
''',
    tests=[
        [[[0, 30], [5, 10], [15, 20]]],
        [[[7, 10], [2, 4]]],
        [[]],
        [[[1, 5]]],
        [[[1, 5], [5, 10]]],
        [[[5, 10], [1, 6]]],
        [[[1, 2], [3, 4], [2, 3]]],
        [[[1, 10], [2, 3]]],
        [[[0, 1], [0, 1]]],
        [[[10, 20], [0, 5], [5, 10], [19, 30]]],
        [_meet_big_ok],
        [_meet_big_bad],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def canAttendMeetings(self, intervals):
        for i in range(1, len(intervals)):                 # forgets to sort
            if intervals[i][0] < intervals[i - 1][1]:
                return False
        return True
''',
        '''class Solution:
    def canAttendMeetings(self, intervals):
        intervals = sorted(intervals)
        for i in range(1, len(intervals)):
            if intervals[i][0] <= intervals[i - 1][1]:     # back-to-back counted as clash
                return False
        return True
''',
    ],
    guide=dict(
        prereqs="Sorting; the overlap test for half-open intervals.",
        intuition="After sorting by start, a clash can only happen between **neighbours**: if meeting i starts before meeting i−1 ends, you cannot attend both. If no neighbouring pair clashes, no pair does.",
        hints=[
            "Comparing every pair is O(n²). Can sorting reduce the comparisons?",
            "After sorting by start, which pairs do you actually need to check?",
            "Return False if intervals[i][0] < intervals[i-1][1] for any i.",
        ],
        brute_force="Check all pairs `(i, j)` for overlap (`a.start < b.end and b.start < a.end`): **O(n²)**.",
        approach=r"""
Sort, then scan adjacent pairs.

**Dry run** `[[0,30],[5,10],[15,20]]`: sorted the same; `5 < 30` → **False**.

Why neighbours suffice: if `j > i+1` overlaps `i`, then `start[i+1] ≤ start[j] < end[i]`, so `i+1`
already overlaps `i`.
""",
        complexity="Time **O(n log n)**, space O(n) (sorted copy).",
        pitfalls="Using `<=` makes back-to-back meetings clash. Empty input → `True`.",
        follow_up="*Meeting Rooms II* — how many rooms are needed when you cannot attend all?",
    ),
),
# ------------------------------------------------------------------ Meeting Rooms II
dict(
    id="meeting-rooms-ii",
    title="Meeting Rooms II",
    difficulty="Medium",
    pattern="Intervals / heap / sweep line",
    leetcode="https://leetcode.com/problems/meeting-rooms-ii/",
    neetcode="https://neetcode.io/problems/meeting-schedule-ii",
    entry="minMeetingRooms",
    description=r"""
Meetings are half-open ranges `[start, end)` given as two-element lists. Return the minimum number of
conference rooms needed so that every meeting can be held. A room freed at time `t` can host a
meeting that starts at `t`.

**Constraints**
- `0 <= len(intervals) <= 10^4`, `0 <= start < end <= 10^6`

**Example 1:** `[[0,30],[5,10],[15,20]]` → `2`.

**Example 2:** `[[7,10],[2,4]]` → `1`.
""",
    starter='''class Solution:
    def minMeetingRooms(self, intervals: List[List[int]]) -> int:
        pass
''',
    solution='''class Solution:
    def minMeetingRooms(self, intervals):
        intervals = sorted(intervals)
        ends = []                        # min-heap of end times of rooms in use
        for s, e in intervals:
            if ends and ends[0] <= s:    # earliest-ending room is free again
                heapq.heapreplace(ends, e)
            else:
                heapq.heappush(ends, e)
        return len(ends)
''',
    tests=[
        [[[0, 30], [5, 10], [15, 20]]],
        [[[7, 10], [2, 4]]],
        [[]],
        [[[1, 5]]],
        [[[1, 5], [5, 10]]],
        [[[1, 10], [2, 9], [3, 8], [4, 7]]],
        [[[1, 5], [8, 9], [8, 9]]],
        [[[9, 10], [4, 9], [4, 17]]],
        [[[2, 11], [6, 16], [11, 16]]],
        [[[1, 2], [1, 2], [1, 2], [2, 3]]],
        [_rooms_big],
        [_meet_big_ok],
        [[[i, 10 ** 6] for i in range(5000)]],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def minMeetingRooms(self, intervals):
        intervals = sorted(intervals)
        rooms = 1 if intervals else 0
        for i in range(1, len(intervals)):           # only counts adjacent clashes
            if intervals[i][0] < intervals[i - 1][1]:
                rooms += 1
        return rooms
''',
        '''class Solution:
    def minMeetingRooms(self, intervals):
        intervals = sorted(intervals)
        ends = []
        for s, e in intervals:
            if ends and ends[0] < s:                 # strict: misses reuse at the same instant
                heapq.heapreplace(ends, e)
            else:
                heapq.heappush(ends, e)
        return len(ends)
''',
    ],
    guide=dict(
        prereqs="Heaps (`heapq`), sorting. Lesson *Sweep lines and heaps*.",
        intuition=r"""
The answer is the **maximum number of meetings in progress at the same instant**. Two ways to
measure it:

- **Heap of end times.** Process meetings by start time. The heap holds the end time of every room
  in use; its minimum is the room that frees up first. If it is free by the time the new meeting
  starts, reuse it (pop + push), else open a new room (push). The heap size at the end is the answer.
- **Sweep line.** Sort all starts and all ends separately; walk through time, +1 at a start, −1 at an
  end (ends first on ties) and track the peak.
""",
        hints=[
            "The answer equals the peak number of simultaneous meetings.",
            "Sort by start. When a new meeting starts, which existing room is the best candidate to reuse?",
            "Min-heap of end times: if heap[0] <= start, replace it; otherwise push. Return len(heap).",
        ],
        brute_force="For every time point (or every meeting start), count meetings covering it: **O(n²)**.",
        approach=r"""
**Dry run** `[[0,30],[5,10],[15,20]]`:
- `[0,30]`: heap `[30]`
- `[5,10]`: 30 > 5 → push → `[10,30]`
- `[15,20]`: 10 ≤ 15 → replace → `[20,30]`. Size **2**.

**Two-pointer sweep** (no heap):
```
starts = sorted(s for s, e in iv); ends = sorted(e for s, e in iv)
rooms = best = j = 0
for s in starts:
    while ends[j] <= s: j += 1; rooms -= 1
    rooms += 1; best = max(best, rooms)
```
""",
        complexity="Time **O(n log n)**, space **O(n)**.",
        pitfalls=r"""
- Counting adjacent overlaps undercounts or overcounts (see `[[1,10],[2,3],[4,5]]`-style inputs).
- Tie handling: an end at `t` must free the room before a start at `t` (`<=`).
- Forgetting the empty list.
""",
        follow_up="*Car Pooling*, *My Calendar II/III* (difference array / sweep), *Meeting Rooms III* (which room gets each meeting — two heaps).",
    ),
),
# ------------------------------------------------------------------ Minimum Interval per query
dict(
    id="minimum-interval-to-include-each-query",
    title="Minimum Interval to Include Each Query",
    difficulty="Hard",
    pattern="Intervals / offline queries + heap",
    leetcode="https://leetcode.com/problems/minimum-interval-to-include-each-query/",
    neetcode="https://neetcode.io/problems/minimum-interval-including-query",
    entry="minInterval",
    description=r"""
You have closed intervals `[left, right]`; the **size** of one is `right - left + 1` (the number of
integers it covers). For each value `q` in `queries`, find the smallest size among intervals with
`left <= q <= right`, or `-1` if no interval contains `q`. Return the answers in the order of
`queries`.

**Constraints**
- `1 <= len(intervals), len(queries) <= 10^5`, `1 <= left <= right <= 10^7`, `1 <= q <= 10^7`

**Example 1:** `intervals = [[1,4],[2,4],[3,6],[4,4]], queries = [2,3,4,5]` → `[3,3,1,4]`.

**Example 2:** `intervals = [[2,3],[2,5],[1,8],[20,25]], queries = [2,19,5,22]` → `[2,-1,4,6]`.
""",
    starter='''class Solution:
    def minInterval(self, intervals: List[List[int]], queries: List[int]) -> List[int]:
        pass
''',
    solution='''class Solution:
    def minInterval(self, intervals, queries):
        intervals = sorted(intervals)
        heap = []                 # (size, right) of intervals that started at or before q
        ans = {}
        i = 0
        for q in sorted(set(queries)):
            while i < len(intervals) and intervals[i][0] <= q:
                l, r = intervals[i]
                heapq.heappush(heap, (r - l + 1, r))
                i += 1
            while heap and heap[0][1] < q:     # smallest one has already ended: discard
                heapq.heappop(heap)
            ans[q] = heap[0][0] if heap else -1
        return [ans[q] for q in queries]
''',
    tests=[
        [[[1, 4], [2, 4], [3, 6], [4, 4]], [2, 3, 4, 5]],
        [[[2, 3], [2, 5], [1, 8], [20, 25]], [2, 19, 5, 22]],
        [[[1, 1]], [1, 2]],
        [[[5, 10]], [1, 5, 10, 11]],
        [[[1, 10], [3, 4]], [3, 5, 4, 3]],
        [[[1, 3], [1, 3], [2, 2]], [2, 2, 1]],
        [[[1, 10000000]], [10000000, 1]],
        [[[4, 5], [5, 8], [1, 9], [8, 10], [1, 6]], [7, 9, 3, 9, 3]],
        [[[2, 7], [3, 4]], [1, 8, 3]],
        [_mi_int, _mi_q],
        [[[i, 10 ** 7 - i] for i in range(1, 5001)], list(range(1, 10 ** 7, 2000))],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def minInterval(self, intervals, queries):
        intervals = sorted(intervals)
        heap, ans, i = [], {}, 0
        for q in sorted(set(queries)):
            while i < len(intervals) and intervals[i][0] <= q:
                l, r = intervals[i]
                heapq.heappush(heap, (r - l, r))      # size off by one
                i += 1
            while heap and heap[0][1] < q:
                heapq.heappop(heap)
            ans[q] = heap[0][0] if heap else -1
        return [ans[q] for q in queries]
''',
        '''class Solution:
    def minInterval(self, intervals, queries):
        out = []
        for q in queries:
            best = -1
            for l, r in intervals:
                if l <= q <= r:
                    best = r - l + 1                  # takes the LAST, not the smallest
            out.append(best)
        return out
''',
    ],
    guide=dict(
        prereqs="*Meeting Rooms II* (heap of active intervals), sorting queries offline, lazy deletion in heaps.",
        intuition=r"""
Answer the queries **offline** in increasing order. Sweep a pointer through intervals sorted by
`left`: by the time you reach query `q`, every interval with `left ≤ q` has been pushed into a
min-heap keyed by size. Some of those have already ended (`right < q`); because later queries are
even larger, an ended interval is useless forever, so it can be popped **lazily** — only when it
sits at the top. The top of the cleaned heap is the smallest interval containing `q`.
""",
        hints=[
            "Answering queries in sorted order lets you add intervals incrementally.",
            "Keep a min-heap of (size, right) for intervals whose left <= q.",
            "Pop from the top while top.right < q; then the top's size is the answer. Map answers back to the original query order.",
        ],
        brute_force="For each query, scan all intervals: **O(n·q)** — 10¹⁰ operations at the limits.",
        approach=r"""
**Dry run** intervals `[[1,4],[2,4],[3,6],[4,4]]` (sorted), queries sorted `[2,3,4,5]`:
- q=2: push `[1,4]` (4,4), `[2,4]` (3,4). Top (3,4) contains 2 → **3**.
- q=3: push `[3,6]` (4,6). Top (3,4) → **3**.
- q=4: push `[4,4]` (1,4). Top (1,4) → **1**.
- q=5: top (1,4) ends at 4 < 5 → pop; (3,4) pop; (4,4) pop; top (4,6) → **4**.

Use a dict (or sort query indices) to restore the original order; duplicates in `queries` are fine.
""",
        complexity="Time **O((n + q) log n + q log q)**, space **O(n + q)**. Each interval is pushed and popped at most once.",
        pitfalls=r"""
- Size is `right − left + 1`, not `right − left`.
- Returning answers in sorted-query order instead of the input order.
- Popping only intervals with `right < q` — an interval that is not the top may be stale, which is fine (lazy deletion).
""",
        follow_up="Online version: segment tree over coordinates with \"min size\" range-assign, or sort intervals by size and use a DSU to fill each query point once.",
    ),
),
]
