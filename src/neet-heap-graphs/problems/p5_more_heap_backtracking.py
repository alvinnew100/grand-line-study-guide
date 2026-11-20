import random

_R = random.Random(2025)


def _words(rng, n, vocab):
    pool = ["".join(rng.choice("abcde") for _ in range(rng.randint(1, 4))) for _ in range(vocab)]
    return [rng.choice(pool) for _ in range(n)]


def _tasks(rng, n, tmax, pmax):
    return [[[rng.randint(1, tmax), rng.randint(1, pmax)] for _ in range(n)]]


def _seat_ops(rng, n, steps):
    ops, args, taken = ["SeatManager"], [[n]], set()
    for _ in range(steps):
        if taken and (len(taken) == n or rng.random() < 0.4):
            s = rng.choice(sorted(taken))
            taken.discard(s)
            ops.append("unreserve"); args.append([s])
        else:
            taken.add(min(set(range(1, n + 1)) - taken))
            ops.append("reserve"); args.append([])
    return [ops, args]


def _sudoku(rng, holes):
    base = [[(3 * (r % 3) + r // 3 + c) % 9 + 1 for c in range(9)] for r in range(9)]
    digits = list(range(1, 10))
    rng.shuffle(digits)
    rows = [b * 3 + r for b in rng.sample(range(3), 3) for r in rng.sample(range(3), 3)]
    cols = [b * 3 + c for b in rng.sample(range(3), 3) for c in rng.sample(range(3), 3)]
    grid = [[str(digits[base[r][c] - 1]) for c in cols] for r in rows]
    cells = [(r, c) for r in range(9) for c in range(9)]
    for r, c in rng.sample(cells, holes):
        grid[r][c] = "."
    return [grid]


_REORG_CHECK = '''
def check(args, got, expected):
    s = args[0]
    if expected == "":
        return got == ""
    if not isinstance(got, str) or sorted(got) != sorted(s):
        return False
    return all(got[i] != got[i + 1] for i in range(len(got) - 1))
'''

_SUDOKU_CHECK = '''
def check(args, got, expected):
    given = args[0]
    if not isinstance(got, list) or len(got) != 9:
        return False
    want = set("123456789")
    for r in range(9):
        if not isinstance(got[r], list) or len(got[r]) != 9:
            return False
        for c in range(9):
            if given[r][c] != "." and got[r][c] != given[r][c]:
                return False
    for i in range(9):
        if set(got[i]) != want or {got[r][i] for r in range(9)} != want:
            return False
        br, bc = 3 * (i // 3), 3 * (i % 3)
        if {got[br + a][bc + b] for a in range(3) for b in range(3)} != want:
            return False
    return True
'''

PROBLEMS = [
# ---------------------------------------------------------------------------------------------
dict(
    id="top-k-frequent-words",
    title="Top K Frequent Words",
    difficulty="Medium",
    pattern="Heap / Priority Queue",
    leetcode="https://leetcode.com/problems/top-k-frequent-words/",
    entry="topKFrequent",
    description=r"""
Given a list of lowercase `words` and an integer `k`, return the `k` words that occur most often.

Order the answer from **most frequent to least frequent**. When two words occur the same number of
times, the one that comes **first alphabetically** goes first.

**Constraints:** `1 <= len(words) <= 500` (tests go to 10^4), `1 <= k <=` number of distinct words.

**Example 1:** `words = ["i","love","leetcode","i","love","coding"], k = 2` → `["i","love"]`
(both appear twice; `"i"` is alphabetically first)

**Example 2:** `words = ["the","day","is","sunny","the","the","the","sunny","is","is"], k = 4` → `["the","is","sunny","day"]`
""",
    starter='''class Solution:
    def topKFrequent(self, words: List[str], k: int) -> List[str]:
        pass
''',
    solution='''import heapq
from collections import Counter

class Solution:
    def topKFrequent(self, words, k):
        count = Counter(words)
        heap = [(-c, w) for w, c in count.items()]   # most frequent first, then alphabetical
        heapq.heapify(heap)
        return [heapq.heappop(heap)[1] for _ in range(k)]
''',
    tests=[
        [["i", "love", "leetcode", "i", "love", "coding"], 2],
        [["the", "day", "is", "sunny", "the", "the", "the", "sunny", "is", "is"], 4],
        [["a"], 1],
        [["b", "a"], 2],
        [["b", "a", "c"], 1],
        [["aaa", "aa", "a"], 2],
        [["x", "y", "x", "y", "z"], 3],
        [["i", "love", "leetcode", "i", "love", "coding"], 3],
        [["zz", "zz", "ab", "ab", "ab", "c"], 2],
        [_words(_R, 500, 30), 10],
        [_words(_R, 10000, 200), 50],
        [_words(_R, 3000, 400), 150],
    ],
    examples=2,
    wrong_solutions=[
        '''from collections import Counter
class Solution:
    def topKFrequent(self, words, k):
        return [w for w, _ in Counter(words).most_common(k)]
''',
        '''from collections import Counter
class Solution:
    def topKFrequent(self, words, k):
        c = Counter(words)
        return sorted(c, key=lambda w: (c[w], w), reverse=True)[:k]
''',
    ],
    guide=dict(
        prereqs="Hash-map counting; heaps of tuples (lesson *Binary heaps and Python's heapq*); top-k pattern (lesson *Heap patterns*).",
        intuition=r"""
Count the words, then rank them by a **two-part key**: higher count first, and for equal counts the
alphabetically smaller word first. Python compares tuples left to right, so the key `(-count, word)`
expresses exactly that in a min-heap: the smallest tuple has the largest count and, on ties, the
smallest word.
""",
        hints=[
            "First reduce the problem: how many times does each distinct word appear?",
            "You need an ordering with a tie-breaker. What single tuple sorts 'big count first, then small word first'?",
            "Build (-count, word) tuples, heapify, pop k times. (Or sort the distinct words by that key and slice.)",
        ],
        brute_force="For each of the k answers, scan all distinct words for the best remaining one: O(k·d) for d distinct words. Sorting all distinct words by `(-count, word)` is O(d log d) and perfectly acceptable.",
        approach=r"""
1. `count = Counter(words)`.
2. `heap = [(-c, w) ...]`, `heapify` in O(d).
3. Pop `k` times; each pop returns the next-best word.

**Dry run** Example 1: counts i:2, love:2, leetcode:1, coding:1. Tuples: (-2,"i"), (-2,"love"), (-1,"leetcode"), (-1,"coding"). Pops: (-2,"i") then (-2,"love") → `["i","love"]`.

**O(n log k) variant:** keep a size-k heap of the *worst* kept word on top. That needs the reversed ordering (small count first, then alphabetically *larger* word first), which requires a small wrapper class with a custom `__lt__`, because you can't negate a string.
""",
        complexity="O(n) to count + O(d) heapify + O(k log d) pops. Space O(d).",
        pitfalls=r"""
- `Counter.most_common(k)` breaks ties by first appearance, not alphabetically (wrong solution #1).
- Sorting by `(count, word)` with `reverse=True` reverses the alphabetical tie-break too (wrong solution #2).
- Returning the words in heap-internal order instead of popping them.
""",
        follow_up="*Top K Frequent Elements* (any order allowed) can be solved in O(n) with bucket sort by frequency. *Sort Characters By Frequency* is the same counting-then-ranking idea.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="reorganize-string",
    title="Reorganize String",
    difficulty="Medium",
    pattern="Heap / Priority Queue",
    leetcode="https://leetcode.com/problems/reorganize-string/",
    neetcode="https://neetcode.io/problems/reorganize-string",
    entry="reorganizeString",
    checker=_REORG_CHECK,
    description=r"""
Rearrange the letters of a lowercase string `s` so that **no two neighbouring characters are the
same**. Return any such arrangement, or the empty string `""` if none exists.

The judge accepts every valid arrangement: it checks that you used exactly the letters of `s` and
that no two adjacent letters are equal.

**Constraints:** `1 <= len(s) <= 500` (tests go to 10^4).

**Example 1:** `s = "aab"` → `"aba"`

**Example 2:** `s = "aaab"` → `""` (three `a`s cannot be separated by one `b`)
""",
    starter='''class Solution:
    def reorganizeString(self, s: str) -> str:
        pass
''',
    solution='''import heapq
from collections import Counter

class Solution:
    def reorganizeString(self, s):
        heap = [(-c, ch) for ch, c in Counter(s).items()]
        heapq.heapify(heap)
        if -heap[0][0] > (len(s) + 1) // 2:
            return ""
        out = []
        held = None                     # the letter used last turn, waiting one turn
        while heap:
            c, ch = heapq.heappop(heap)
            out.append(ch)
            if held:
                heapq.heappush(heap, held)
            held = (c + 1, ch) if c + 1 < 0 else None
        return "".join(out)
''',
    tests=[
        ["aab"], ["aaab"], ["a"], ["aa"], ["ab"], ["aabb"], ["aaabc"], ["aaabbb"], ["vvvlo"],
        ["aabbb"], ["zzzzyyyxxw"], ["aaaabc"],
        ["".join(_R.choice("abc") for _ in range(500))],
        ["a" * 5000 + "b" * 2500 + "c" * 2499],
        ["a" * 5001 + "b" * 2500 + "c" * 2499],
        ["a" * 5002 + "b" * 2500 + "c" * 2498],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def reorganizeString(self, s):
        t = sorted(s); n = len(t); out = [""] * n; i = 0
        for ch in t:
            out[i] = ch; i += 2
            if i >= n: i = 1
        return "".join(out)
''',
        '''import heapq
from collections import Counter
class Solution:
    def reorganizeString(self, s):
        heap = [(-c, ch) for ch, c in Counter(s).items()]
        heapq.heapify(heap)
        if -heap[0][0] > len(s) // 2: return ""
        out = []; held = None
        while heap:
            c, ch = heapq.heappop(heap); out.append(ch)
            if held: heapq.heappush(heap, held)
            held = (c + 1, ch) if c + 1 < 0 else None
        return "".join(out)
''',
    ],
    guide=dict(
        prereqs="Max-heap via negation; the 'hold one item back for a turn' scheduling idea (lesson *Heap patterns*, Task Scheduler).",
        intuition=r"""
The most frequent letter is the hardest to place: it needs a different letter between every two of
its copies. So at each position write the letter with the **most copies remaining** — except you may
not reuse the letter you wrote in the previous position. Keep that letter out of the heap for one
turn. It is Task Scheduler with a cooldown of 1.

An arrangement exists exactly when the largest count is at most `(n + 1) // 2` (the number of
even positions 0, 2, 4, ...).
""",
        hints=[
            "Which letter is most likely to end up next to itself? What limits how many copies of it can fit?",
            "Greedy: always place the letter with the most remaining copies that differs from the previous letter.",
            "Max-heap of (-count, letter). Pop, append, and push back the letter you popped on the PREVIOUS turn (if it still has copies).",
        ],
        brute_force="Try all permutations of the letters and test each: O(n!·n). Hopeless beyond about 10 letters.",
        approach=r"""
1. Count letters; if the largest count exceeds `(n + 1) // 2` return `""`.
2. Max-heap of `(-count, letter)`; `held = None`.
3. Loop: pop the most frequent available letter, append it; push `held` back; set `held` to the letter you popped (with one fewer copy) if copies remain.

**Dry run** `"aaabc"` (a:3, b:1, c:1): pop a → "a", held a2. Pop b → "ab", push a2, held none (b used up). Pop a → "aba", held a1. Pop c → "abac", push a1. Pop a → "abaca".

**No-heap alternative:** fill positions 0, 2, 4, ... starting with the most frequent letter, then wrap to 1, 3, 5, ...
""",
        complexity="O(n log 26) = O(n) time; O(26) heap plus the output.",
        pitfalls=r"""
- Filling even-then-odd positions in **alphabetical** order instead of starting with the most frequent letter (wrong solution #1 breaks on `"aabbb"`).
- Using `len(s) // 2` as the limit — odd lengths allow one extra copy (wrong solution #2 rejects `"aab"`).
- Pushing the just-used letter straight back, which lets it be chosen twice in a row.
""",
        follow_up="*Rearrange String k Distance Apart* generalises the hold-back queue to length k. *Task Scheduler* allows idle slots instead of failing.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="single-threaded-cpu",
    title="Single-Threaded CPU",
    difficulty="Medium",
    pattern="Heap / Priority Queue",
    leetcode="https://leetcode.com/problems/single-threaded-cpu/",
    neetcode="https://neetcode.io/problems/single-threaded-cpu",
    entry="getOrder",
    description=r"""
You have `n` tasks numbered `0..n-1`. `tasks[i] = [enqueueTime, processingTime]` means task `i`
becomes available at `enqueueTime` and needs `processingTime` units of CPU.

The CPU runs one task at a time and never interrupts a task:

- when it is free and tasks are available, it starts the available task with the **shortest
  processing time**; ties go to the **smaller index**;
- when it is free and nothing is available, it waits until the next task arrives;
- it can start a new task the instant the previous one finishes.

Return the order in which the tasks are processed.

**Constraints:** `1 <= n <= 10^5` (tests go to 2000), `1 <= enqueueTime, processingTime <= 10^9`.

**Example 1:** `tasks = [[1,2],[2,4],[3,2],[4,1]]` → `[0,2,3,1]`

**Example 2:** `tasks = [[7,10],[7,12],[7,5],[7,4],[7,2]]` → `[4,3,2,0,1]`
""",
    starter='''class Solution:
    def getOrder(self, tasks: List[List[int]]) -> List[int]:
        pass
''',
    solution='''import heapq

class Solution:
    def getOrder(self, tasks):
        order = sorted(range(len(tasks)), key=lambda i: tasks[i][0])   # by arrival time
        heap, res = [], []
        time, j, n = 0, 0, len(tasks)
        while len(res) < n:
            if not heap and time < tasks[order[j]][0]:
                time = tasks[order[j]][0]              # idle: jump to the next arrival
            while j < n and tasks[order[j]][0] <= time:
                i = order[j]
                heapq.heappush(heap, (tasks[i][1], i))
                j += 1
            dur, i = heapq.heappop(heap)
            time += dur
            res.append(i)
        return res
''',
    tests=[
        [[[1, 2], [2, 4], [3, 2], [4, 1]]],
        [[[7, 10], [7, 12], [7, 5], [7, 4], [7, 2]]],
        [[[5, 1]]],
        [[[1, 1], [100, 1], [50, 1]]],
        [[[1, 10], [2, 1], [3, 1], [4, 1]]],
        [[[2, 3], [1, 3], [1, 3]]],
        [[[1000000000, 1000000000], [1, 1]]],
        [[[5, 2], [5, 2], [5, 2], [1, 100]]],
        [[[1, 3], [2, 2], [4, 2], [4, 1], [100, 5], [100, 5]]],
        _tasks(_R, 50, 30, 10),
        _tasks(_R, 2000, 5000, 20),
        _tasks(_R, 2000, 10**9, 10**9),
        _tasks(_R, 1500, 5, 3),
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def getOrder(self, tasks):
        return sorted(range(len(tasks)), key=lambda i: (tasks[i][1], i))
''',
        '''class Solution:
    def getOrder(self, tasks):
        return sorted(range(len(tasks)), key=lambda i: (tasks[i][0], tasks[i][1], i))
''',
    ],
    guide=dict(
        prereqs="Scheduling with a heap of ready items and a sorted list of future arrivals (lesson *Heap patterns*, pattern 4).",
        intuition=r"""
Simulate the CPU. Two collections are involved: tasks that have **not arrived yet** (sorted by
arrival time, consumed with a pointer) and tasks that are **available now** (a min-heap keyed on
`(processingTime, index)`, which encodes the tie-break). Each step: admit everything that has arrived
by the current time, pop the best task, advance the clock by its duration.
""",
        hints=[
            "At the moment the CPU becomes free, which tasks may it choose from, and by what rule?",
            "Sort task indices by enqueue time. Keep a min-heap of (processingTime, index) for tasks whose enqueue time <= current time.",
            "If the heap is empty and tasks remain, jump the clock to the next arrival instead of ticking one unit at a time.",
        ],
        brute_force="Each time the CPU is free, scan all unfinished tasks for the best available one: O(n²).",
        approach=r"""
1. `order` = indices sorted by enqueue time; `time = 0`, pointer `j = 0`.
2. While not all tasks are done: if the heap is empty and the next task is in the future, set `time` to its arrival. Push all tasks with `enqueue <= time`. Pop `(dur, i)`, append `i`, `time += dur`.

**Dry run** Example 1: time jumps to 1, push task 0. Run 0 → time 3; push tasks 1 (4) and 2 (2). Run 2 → time 5; push task 3 (1). Run 3 → time 6. Run 1. Order `[0,2,3,1]`.
""",
        complexity="O(n log n) for the sort and for n pushes/pops. Space O(n).",
        pitfalls=r"""
- Sorting by processing time alone ignores arrival times (wrong solution #1).
- Running tasks in arrival order ignores the shortest-job rule (wrong solution #2).
- Advancing the clock one unit at a time — times go up to 10⁹.
- Losing the original indices when sorting; sort indices, not the task list.
""",
        follow_up="*Process Tasks Using Servers* uses two heaps (free servers, busy servers). *Meeting Rooms II* keeps a heap of end times.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="ipo",
    title="IPO",
    difficulty="Hard",
    pattern="Heap / Priority Queue",
    leetcode="https://leetcode.com/problems/ipo/",
    neetcode="https://neetcode.io/problems/ipo",
    entry="findMaximizedCapital",
    description=r"""
A company starts with capital `w` and may complete **at most `k`** distinct projects, one after
another. Project `i` can be started only if the current capital is at least `capital[i]`; finishing
it adds the pure profit `profits[i]` to the capital (the starting capital is not spent).

Return the largest capital the company can have after at most `k` projects.

**Constraints:** `1 <= k <= 10^5`, `0 <= w <= 10^9`, `1 <= n <= 10^5` (tests go to 10^4),
`0 <= profits[i] <= 10^4`, `0 <= capital[i] <= 10^9`.

**Example 1:** `k = 2, w = 0, profits = [1,2,3], capital = [0,1,1]` → `4`
(only project 0 is affordable; capital becomes 1; then project 2 gives 3)

**Example 2:** `k = 3, w = 0, profits = [1,2,3], capital = [0,1,2]` → `6`
""",
    starter='''class Solution:
    def findMaximizedCapital(self, k: int, w: int, profits: List[int], capital: List[int]) -> int:
        pass
''',
    solution='''import heapq

class Solution:
    def findMaximizedCapital(self, k, w, profits, capital):
        projects = sorted(zip(capital, profits))     # cheapest requirement first
        heap = []                                    # max-heap of affordable profits
        j, n = 0, len(projects)
        for _ in range(k):
            while j < n and projects[j][0] <= w:
                heapq.heappush(heap, -projects[j][1])
                j += 1
            if not heap:
                break
            w -= heapq.heappop(heap)                 # subtracting a negative adds the profit
        return w
''',
    tests=[
        [2, 0, [1, 2, 3], [0, 1, 1]],
        [3, 0, [1, 2, 3], [0, 1, 2]],
        [1, 0, [5], [1]],
        [1, 2, [1, 2, 3], [1, 1, 2]],
        [10, 0, [1, 2, 3], [0, 1, 2]],
        [2, 1, [5, 4, 3], [5, 5, 5]],
        [3, 0, [0, 0, 0], [0, 0, 0]],
        [2, 0, [1, 10, 100], [0, 1, 11]],
        [1, 5, [3, 9, 4], [6, 5, 1]],
        [100000, 1000000000, [10000, 10000], [0, 1000000000]],
        [50, 3, [_R.randint(0, 100) for _ in range(300)], [_R.randint(0, 400) for _ in range(300)]],
        [5000, 0, [_R.randint(0, 10000) for _ in range(10000)], [_R.randint(0, 10**6) for _ in range(10000)]],
        [20, 100, [_R.randint(0, 10000) for _ in range(10000)], [_R.randint(0, 10**9) for _ in range(10000)]],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def findMaximizedCapital(self, k, w, profits, capital):
        return w + sum(sorted(profits, reverse=True)[:k])
''',
        '''class Solution:
    def findMaximizedCapital(self, k, w, profits, capital):
        for c, p in sorted(zip(capital, profits))[:k]:
            if c <= w: w += p
        return w
''',
    ],
    guide=dict(
        prereqs="Greedy choice with a max-heap; sorting plus a pointer to admit items as they become available (lesson *Heap patterns*).",
        intuition=r"""
Capital never decreases, so a project that is affordable now stays affordable forever. That makes
the greedy choice safe: among everything you can afford **right now**, take the most profitable —
it gives the biggest capital for the next round, which can only unlock more projects. Sort projects
by required capital so "newly affordable" projects can be added with a moving pointer, and keep
their profits in a max-heap.
""",
        hints=[
            "After finishing a project, can any previously affordable project become unaffordable?",
            "Of all projects you can currently afford, which one should you do next, and why can that never hurt?",
            "Sort by capital. Each round: push profits of all projects with capital <= w into a max-heap, then pop the largest and add it to w.",
        ],
        brute_force="Each round scan all remaining projects for the most profitable affordable one: O(k·n).",
        approach=r"""
1. Sort `(capital, profit)` pairs by capital; pointer `j = 0`.
2. Repeat up to `k` times: push the profit of every project with `capital <= w`; if the heap is empty, stop; otherwise `w += largest profit`.

**Dry run** Example 1 (`k=2, w=0`): affordable: project 0 (profit 1) → w = 1. Now projects 1 and 2 are affordable (profits 2, 3) → take 3 → w = 4.
""",
        complexity="O(n log n) to sort + O((n + k) log n) heap work (the loop stops early when nothing is affordable). Space O(n).",
        pitfalls=r"""
- Ignoring the capital requirement and taking the k largest profits (wrong solution #1).
- Doing the cheapest projects first regardless of profit (wrong solution #2).
- Not breaking when the heap is empty — with `k = 10⁵` and nothing affordable you would loop needlessly (or pop from an empty heap).
- Subtracting the required capital: profits are *pure*, the capital is not spent.
""",
        follow_up="The same 'sort by threshold, heap by value' skeleton solves *Maximum Performance of a Team* and *Minimum Number of Refueling Stops*.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="seat-reservation-manager",
    title="Seat Reservation Manager",
    difficulty="Medium",
    pattern="Heap / Priority Queue",
    leetcode="https://leetcode.com/problems/seat-reservation-manager/",
    neetcode="https://neetcode.io/problems/seat-reservation-manager",
    kind="class",
    entry="SeatManager",
    description=r"""
Design a manager for `n` seats numbered `1..n`, all free at the start.

- `SeatManager(n)` — create the manager.
- `reserve()` — reserve the **lowest-numbered free seat** and return its number.
- `unreserve(seatNumber)` — free the given seat again.

Every `reserve` call is guaranteed to have a free seat, and `unreserve` is only called on a seat
that is currently reserved.

**Constraints:** `1 <= n <= 10^5`, at most `10^5` calls.

**Example**

```
SeatManager(5)
reserve()    -> 1
reserve()    -> 2
unreserve(2)
reserve()    -> 2
reserve()    -> 3
reserve()    -> 4
reserve()    -> 5
unreserve(5)
```
""",
    starter='''class SeatManager:

    def __init__(self, n: int):
        pass

    def reserve(self) -> int:
        pass

    def unreserve(self, seatNumber: int) -> None:
        pass
''',
    solution='''import heapq

class SeatManager:
    def __init__(self, n):
        self.next_fresh = 1        # smallest seat that has never been handed out
        self.returned = []         # min-heap of seats that were given back

    def reserve(self):
        if self.returned:
            return heapq.heappop(self.returned)   # always smaller than next_fresh
        seat = self.next_fresh
        self.next_fresh += 1
        return seat

    def unreserve(self, seatNumber):
        heapq.heappush(self.returned, seatNumber)
''',
    tests=[
        [["SeatManager", "reserve", "reserve", "unreserve", "reserve", "reserve", "reserve", "reserve", "unreserve"],
         [[5], [], [], [2], [], [], [], [], [5]]],
        [["SeatManager", "reserve"], [[1]]],
        [["SeatManager", "reserve", "unreserve", "reserve"], [[1], [], [1], []]],
        [["SeatManager", "reserve", "reserve", "reserve", "unreserve", "unreserve", "reserve", "reserve", "reserve"],
         [[4], [], [], [], [3], [1], [], [], []]],
        [["SeatManager", "reserve", "reserve", "reserve", "unreserve", "unreserve", "reserve", "reserve"],
         [[3], [], [], [], [1], [3], [], []]],
        [["SeatManager", "reserve", "reserve", "unreserve", "unreserve", "reserve", "reserve", "reserve"],
         [[10], [], [], [1], [2], [], [], []]],
        _seat_ops(random.Random(1), 3, 30),
        _seat_ops(random.Random(2), 10, 200),
        _seat_ops(random.Random(3), 50, 2000),
        _seat_ops(random.Random(4), 1000, 5000),
        _seat_ops(random.Random(5), 100000, 3000),
    ],
    examples=1,
    wrong_solutions=[
        '''class SeatManager:
    def __init__(self, n):
        self.nxt = 1; self.back = []
    def reserve(self):
        if self.back: return self.back.pop()
        self.nxt += 1
        return self.nxt - 1
    def unreserve(self, seatNumber):
        self.back.append(seatNumber)
''',
        '''class SeatManager:
    def __init__(self, n):
        self.nxt = 1
    def reserve(self):
        self.nxt += 1
        return self.nxt - 1
    def unreserve(self, seatNumber):
        self.nxt = min(self.nxt, seatNumber)
''',
    ],
    guide=dict(
        prereqs="Min-heap basics (lesson *Binary heaps and Python's heapq*).",
        intuition=r"""
"Give me the smallest free seat, and seats can come back" is the priority-queue contract word for
word. A min-heap of free seats answers `reserve` in O(log n). A small refinement avoids putting all
`n` seats into the heap at the start: remember the smallest seat that has *never* been used, and keep
only **returned** seats in the heap. A returned seat is always smaller than the never-used marker, so
check the heap first.
""",
        hints=[
            "Which data structure returns the minimum quickly while items are added back?",
            "Put free seat numbers in a min-heap: reserve pops, unreserve pushes.",
            "Optimisation: keep a counter for untouched seats and a heap only for returned ones; prefer the heap when it is non-empty.",
        ],
        brute_force="Keep a boolean array and scan from seat 1 for the first free one: O(n) per `reserve`.",
        approach=r"""
- `reserve`: if the heap of returned seats is non-empty, pop its minimum; otherwise hand out `next_fresh` and increment it.
- `unreserve(x)`: push `x`.

**Dry run** (example): reserve → 1, reserve → 2, unreserve(2) → heap [2], reserve → 2 (from heap), then 3, 4, 5 from the counter.

Simplest version: `heap = list(range(1, n + 1))` (already a valid heap), pop/push directly — O(n) setup.
""",
        complexity="reserve / unreserve O(log m) where m is the number of returned seats; constructor O(1). Space O(m).",
        pitfalls=r"""
- Handing back the **most recently** returned seat (a stack) instead of the smallest (wrong solution #1).
- Tracking only one "smallest free" number loses information when several seats are returned (wrong solution #2).
- Forgetting that returned seats are always smaller than the fresh counter — check the heap first.
""",
        follow_up="*Smallest Number in Infinite Set* is the same design with an extra set to prevent duplicate pushes. *Exam Room* asks for the seat farthest from others instead.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="combinations",
    title="Combinations",
    difficulty="Medium",
    pattern="Backtracking",
    leetcode="https://leetcode.com/problems/combinations/",
    neetcode="https://neetcode.io/problems/combinations",
    entry="combine",
    compare="unordered_nested",
    description=r"""
Given two integers `n` and `k`, return every way to choose `k` **different** numbers from
`1, 2, ..., n`. The order inside a choice does not matter (`[1,2]` and `[2,1]` are the same choice,
list it once), and the choices may be returned in any order.

**Constraints:** `1 <= k <= n <= 20` (tests keep the output small).

**Example 1:** `n = 4, k = 2` → `[[1,2],[1,3],[1,4],[2,3],[2,4],[3,4]]`

**Example 2:** `n = 1, k = 1` → `[[1]]`
""",
    starter='''class Solution:
    def combine(self, n: int, k: int) -> List[List[int]]:
        pass
''',
    solution='''class Solution:
    def combine(self, n, k):
        res, path = [], []

        def dfs(start):
            if len(path) == k:
                res.append(path[:])
                return
            need = k - len(path)
            for x in range(start, n - need + 2):   # leave enough numbers to finish
                path.append(x)
                dfs(x + 1)
                path.pop()

        dfs(1)
        return res
''',
    tests=[[4, 2], [1, 1], [3, 3], [3, 1], [5, 3], [5, 5], [6, 2], [7, 4], [10, 2], [10, 5], [12, 3], [20, 1], [20, 19], [14, 7]],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def combine(self, n, k):
        res, path = [], []
        def dfs():
            if len(path) == k:
                res.append(path[:]); return
            for x in range(1, n + 1):
                if x not in path:
                    path.append(x); dfs(); path.pop()
        if n > 8: return []
        dfs()
        return res
''',
        '''class Solution:
    def combine(self, n, k):
        res, path = [], []
        def dfs(start):
            if len(path) == k:
                res.append(path[:]); return
            for x in range(start, n):
                path.append(x); dfs(x + 1); path.pop()
        dfs(1)
        return res
''',
    ],
    guide=dict(
        prereqs="The backtracking template with a `start` value (lesson *The backtracking template and state-space trees*).",
        intuition=r"""
Build each choice in **increasing order**: after picking `x`, only numbers larger than `x` may
follow. That way every set of `k` numbers is produced exactly once (in its sorted order) and never in
a shuffled order. Stop a branch as soon as it has `k` numbers.
""",
        hints=[
            "How do you avoid producing both [1,2] and [2,1]?",
            "Write dfs(start): try each x from start to n, then recurse with x + 1.",
            "Record a copy of the path when its length is k. Optional pruning: stop the loop when fewer than (k − len(path)) numbers remain.",
        ],
        brute_force="Generate all 2ⁿ subsets and keep those of size k, or generate all ordered arrangements and deduplicate. Both do far more work than the C(n, k) answers require.",
        approach=r"""
`dfs(start)`: if `len(path) == k`, record. Otherwise for `x` in `start..n`: append, `dfs(x + 1)`, pop.

**Dry run** `n = 4, k = 2`: 1 → (2) (3) (4) gives [1,2] [1,3] [1,4]; 2 → [2,3] [2,4]; 3 → [3,4]; 4 → no number left to pair with.

**Pruning:** if you still need `need` numbers, the largest useful starting value is `n − need + 1`; beyond that the branch cannot finish. This removes all dead branches (the tree then has only useful nodes).
""",
        complexity="O(k · C(n, k)) time — C(n, k) answers, each copied in O(k). Recursion depth k.",
        pitfalls=r"""
- Looping from 1 every time (produces every ordering — wrong solution #1).
- Off-by-one upper bound: `range(start, n)` never uses the number `n` (wrong solution #2).
- Appending `path` without copying.
""",
        follow_up="*Combination Sum III* adds a target sum; *Subsets* is the union over all k. `itertools.combinations(range(1, n + 1), k)` is the library version.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="permutations-ii",
    title="Permutations II",
    difficulty="Medium",
    pattern="Backtracking",
    leetcode="https://leetcode.com/problems/permutations-ii/",
    neetcode="https://neetcode.io/problems/permutations-ii",
    entry="permuteUnique",
    compare="unordered",
    description=r"""
Given a list of numbers that **may contain duplicates**, return all the *distinct* orderings of the
list. Each distinct ordering must appear exactly once; the orderings can be returned in any order.

**Constraints:** `1 <= len(nums) <= 8`, `-10 <= nums[i] <= 10`.

**Example 1:** `nums = [1,1,2]` → `[[1,1,2],[1,2,1],[2,1,1]]`

**Example 2:** `nums = [1,2,3]` → all six orderings
""",
    starter='''class Solution:
    def permuteUnique(self, nums: List[int]) -> List[List[int]]:
        pass
''',
    solution='''from collections import Counter

class Solution:
    def permuteUnique(self, nums):
        count = Counter(nums)
        n = len(nums)
        res, path = [], []

        def dfs():
            if len(path) == n:
                res.append(path[:])
                return
            for x in count:                # each DISTINCT value once per position
                if count[x] > 0:
                    count[x] -= 1
                    path.append(x)
                    dfs()
                    path.pop()
                    count[x] += 1

        dfs()
        return res
''',
    tests=[
        [[1, 1, 2]], [[1, 2, 3]], [[1]], [[2, 2]], [[2, 2, 2, 2]], [[1, 1, 2, 2]], [[3, 3, 0, 3]],
        [[-1, 2, -1, 2, 1]], [[0, 1, 0, 0, 9]], [[1, 1, 1, 2, 2, 3]], [[1, 2, 3, 4, 5, 6]], [[5, 5, 5, 5, 6, 6, 7, 7]],
    ],
    examples=2,
    wrong_solutions=[
        '''import itertools
class Solution:
    def permuteUnique(self, nums):
        return [list(p) for p in itertools.permutations(nums)]
''',
        '''import itertools
class Solution:
    def permuteUnique(self, nums):
        return [list(p) for p in itertools.permutations(sorted(set(nums)))]
''',
    ],
    guide=dict(
        prereqs="*Permutations*; handling duplicates (lesson *Duplicates, pruning and constraint search*).",
        intuition=r"""
Plain permutation code treats two equal numbers as different items and so outputs the same ordering
several times. The cure is to decide, at each position, **which distinct value** goes there — not
which index. Keep a counter of how many copies of each value are still unused; loop over the distinct
values; use one copy; recurse; give it back.
""",
        hints=[
            "Run ordinary permutation code on [1,1,2]. Why does [1,1,2] appear twice?",
            "At a given position, placing the first 1 or the second 1 gives the same result. Choose by value, not by index.",
            "Counter of remaining copies: for each key with count > 0: decrement, append, recurse, pop, increment.",
        ],
        brute_force="Generate all n! orderings and deduplicate with a set of tuples: O(n · n!) work even when only a handful are distinct.",
        approach=r"""
`dfs()`: if the path has `n` items, record it. Otherwise loop over the distinct values in the counter that still have copies.

**Dry run** `[1,1,2]` (counter 1:2, 2:1): position 0 → 1 (1:1 left) → position 1 → 1 → 2 gives `[1,1,2]`; position 1 → 2 → 1 gives `[1,2,1]`. Position 0 → 2 → 1 → 1 gives `[2,1,1]`. Three results, no repeats.

**Sorting alternative:** sort, use a `used` array, and skip `nums[i]` when `i > 0`, `nums[i] == nums[i-1]` and `used[i-1]` is `False`.
""",
        complexity="O(n · P) where P = n! / (c₁! · c₂! · ...) is the number of distinct orderings. Recursion depth n.",
        pitfalls=r"""
- Not handling duplicates at all (wrong solution #1).
- Removing duplicates from the input (wrong solution #2) — every copy must still be placed.
- In the sorting variant, writing `used[i-1]` instead of `not used[i-1]` still works but prunes less; mixing up the index conditions loses answers.
""",
        follow_up="Counting distinct permutations needs no search: the multinomial formula above. Related: *Subsets II*, *Combination Sum II*.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="restore-ip-addresses",
    title="Restore IP Addresses",
    difficulty="Medium",
    pattern="Backtracking",
    leetcode="https://leetcode.com/problems/restore-ip-addresses/",
    entry="restoreIpAddresses",
    compare="unordered",
    description=r"""
An IPv4 address is written as four whole numbers separated by dots, such as `192.168.1.1`. Each
number must be between `0` and `255` and must **not have leading zeros** (`0` is fine, `01` and `00`
are not).

Given a string `s` containing only digits, return every valid IP address that can be formed by
inserting exactly three dots into `s` — without reordering or dropping any digit. Any order is accepted.

**Constraints:** `1 <= len(s) <= 20`.

**Example 1:** `s = "25525511135"` → `["255.255.11.135","255.255.111.35"]`

**Example 2:** `s = "0000"` → `["0.0.0.0"]`

**Example 3:** `s = "101023"` → `["1.0.10.23","1.0.102.3","10.1.0.23","10.10.2.3","101.0.2.3"]`
""",
    starter='''class Solution:
    def restoreIpAddresses(self, s: str) -> List[str]:
        pass
''',
    solution='''class Solution:
    def restoreIpAddresses(self, s):
        res, parts = [], []

        def dfs(i):
            left = 4 - len(parts)                      # parts still to place
            if len(s) - i < left or len(s) - i > 3 * left:
                return                                 # too few or too many digits remain
            if left == 0:
                res.append(".".join(parts))
                return
            for size in (1, 2, 3):
                piece = s[i:i + size]
                if len(piece) < size:
                    break
                if (size > 1 and piece[0] == "0") or int(piece) > 255:
                    break
                parts.append(piece)
                dfs(i + size)
                parts.pop()

        dfs(0)
        return res
''',
    tests=[
        ["25525511135"], ["0000"], ["101023"], ["1"], ["123"], ["1111"], ["010010"], ["255255255255"],
        ["256256256256"], ["00000"], ["172162541"], ["1000"], ["19216811"], ["12345678901234567890"], ["99999"],
    ],
    examples=3,
    wrong_solutions=[
        '''class Solution:
    def restoreIpAddresses(self, s):
        res = []; n = len(s)
        for a in range(1, 4):
            for b in range(1, 4):
                for c in range(1, 4):
                    d = n - a - b - c
                    if 1 <= d <= 3:
                        p = [s[:a], s[a:a+b], s[a+b:a+b+c], s[a+b+c:]]
                        if all(int(x) <= 255 for x in p): res.append(".".join(p))
        return res
''',
        '''class Solution:
    def restoreIpAddresses(self, s):
        res = []; n = len(s)
        for a in range(1, 4):
            for b in range(1, 4):
                for c in range(1, 4):
                    d = n - a - b - c
                    if 1 <= d <= 3:
                        p = [s[:a], s[a:a+b], s[a+b:a+b+c], s[a+b+c:]]
                        if all(str(int(x)) == x for x in p): res.append(".".join(p))
        return res
''',
    ],
    guide=dict(
        prereqs="Partitioning by backtracking (lesson *The backtracking template*, shape 5 — where to cut next).",
        intuition=r"""
You are cutting the string into exactly four pieces. Decide the pieces left to right: the next piece
is the next 1, 2 or 3 digits, provided it is a legal number. After four pieces, the whole string must
be used up. Two cheap checks prune almost everything: a piece starting with `0` must be exactly `"0"`,
and the remaining digits must be able to fill the remaining pieces (between 1 and 3 digits each).
""",
        hints=[
            "How long can one part of an IP address be? How many parts are there?",
            "dfs(i): the next part is s[i:i+1], s[i:i+2] or s[i:i+3]. What makes a part invalid?",
            "Reject leading zeros and values above 255; record when 4 parts have been chosen and i == len(s).",
        ],
        brute_force="Three nested loops over the lengths (1–3) of the first three parts; the fourth is what remains. Only 27 combinations — a completely valid solution; the recursion generalises it.",
        approach=r"""
`dfs(i)` with a list `parts`: if four parts are placed and `i == len(s)`, join with dots. Otherwise try sizes 1–3.

**Dry run** `"0000"`: first part must be `"0"` (`"00"` has a leading zero) → same for the other three → `0.0.0.0`.

`"101023"`: `1` → `0` → `10` → `23` ✔; `1` → `0` → `102` → `3` ✔; `10` → `1` → `0` → `23` ✔; `10` → `10` → `2` → `3` ✔; `101` → `0` → `2` → `3` ✔.
""",
        complexity="At most 3⁴ = 81 leaves regardless of input length, so O(1) search plus O(n) per string built.",
        pitfalls=r"""
- Accepting leading zeros such as `01` (wrong solution #1).
- Forgetting the 255 limit (wrong solution #2).
- Using fewer or more than four parts, or leaving digits unused.
- Converting with `int` and back loses leading zeros — keep the original substring in the answer.
""",
        follow_up="*Validate IP Address* checks one given string (including IPv6). The same cut-and-validate recursion solves *Palindrome Partitioning* and *Word Break II*.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="word-break-ii",
    title="Word Break II",
    difficulty="Hard",
    pattern="Backtracking",
    leetcode="https://leetcode.com/problems/word-break-ii/",
    neetcode="https://neetcode.io/problems/word-break-ii",
    entry="wordBreak",
    compare="unordered",
    description=r"""
Given a string `s` and a list of distinct dictionary words `wordDict`, insert spaces into `s` so
that **every piece is a dictionary word**. Return all the sentences you can make this way, in any
order. A dictionary word may be used any number of times.

**Constraints:** `1 <= len(s) <= 20`, `1 <= len(wordDict) <= 1000`, words have 1–10 lowercase letters.

**Example 1:** `s = "catsanddog", wordDict = ["cat","cats","and","sand","dog"]` → `["cats and dog","cat sand dog"]`

**Example 2:** `s = "pineapplepenapple", wordDict = ["apple","pen","applepen","pine","pineapple"]`
→ `["pine apple pen apple","pineapple pen apple","pine applepen apple"]`

**Example 3:** `s = "catsandog", wordDict = ["cats","dog","sand","and","cat"]` → `[]`
""",
    starter='''class Solution:
    def wordBreak(self, s: str, wordDict: List[str]) -> List[str]:
        pass
''',
    solution='''from functools import lru_cache

class Solution:
    def wordBreak(self, s, wordDict):
        words = set(wordDict)
        longest = max(map(len, words))
        n = len(s)

        @lru_cache(maxsize=None)
        def sentences(i):
            """all ways to break the suffix s[i:]"""
            if i == n:
                return [""]
            out = []
            for j in range(i + 1, min(n, i + longest) + 1):
                w = s[i:j]
                if w in words:
                    for rest in sentences(j):
                        out.append(w if not rest else w + " " + rest)
            return out

        return sentences(0)
''',
    tests=[
        ["catsanddog", ["cat", "cats", "and", "sand", "dog"]],
        ["pineapplepenapple", ["apple", "pen", "applepen", "pine", "pineapple"]],
        ["catsandog", ["cats", "dog", "sand", "and", "cat"]],
        ["a", ["a"]],
        ["a", ["b"]],
        ["aaaa", ["a", "aa"]],
        ["leetcode", ["leet", "code"]],
        ["abcd", ["a", "abc", "b", "cd"]],
        ["aaaaaaaaaaaa", ["a", "aa", "aaa"]],
        ["aaaaaaaaaaaaaaaaaaab", ["a", "aa", "aaa", "aaaa", "aaaaa"]],
        ["bb", ["a", "b", "bbb", "bbbb"]],
        ["thequickbrownfox", ["the", "quick", "brown", "fox", "thequick", "brownfox", "qu", "ick"]],
    ],
    examples=3,
    wrong_solutions=[
        '''class Solution:
    def wordBreak(self, s, wordDict):
        words = set(wordDict); out = []; i = 0
        while i < len(s):
            for j in range(len(s), i, -1):
                if s[i:j] in words:
                    out.append(s[i:j]); i = j; break
            else:
                return []
        return [" ".join(out)]
''',
        '''class Solution:
    def wordBreak(self, s, wordDict):
        res = []
        def dfs(i, path):
            if i == len(s):
                res.append(" ".join(path)); return
            for w in wordDict:
                if s.startswith(w, i) and w not in path:
                    dfs(i + len(w), path + [w])
        dfs(0, [])
        return res
''',
    ],
    guide=dict(
        prereqs="Partition backtracking (lesson *The backtracking template*); memoisation; why a doomed search must be pruned (lesson *Duplicates, pruning and constraint search*).",
        intuition=r"""
Choose the **first word**: any dictionary word that is a prefix of the remaining text. Then solve
the same problem for what is left. The set of sentences for a suffix `s[i:]` depends only on `i`, so
cache it — that is what stops inputs like `"aaaa...ab"` (many ways to start, none of which can
finish) from exploding: the failing suffixes are computed once and remembered as "no sentences".
""",
        hints=[
            "What are the options for the first word of a sentence?",
            "Define sentences(i) = all ways to break s[i:]. How does it use sentences(j) for j > i?",
            "Memoise sentences(i). For each j with s[i:j] in the dictionary, prepend that word to every sentence in sentences(j). sentences(len(s)) is one empty sentence.",
        ],
        brute_force="Try all 2ⁿ⁻¹ ways to cut the string and keep the cuts where every piece is a word — O(2ⁿ · n). Fine for n ≤ 20 in principle, but un-memoised recursion can still repeat hopeless work.",
        approach=r"""
1. Put the words in a set; note the longest word length to bound the loop.
2. `sentences(i)`: if `i == n` return `[""]`. For each end `j`: if `s[i:j]` is a word, combine it with each sentence of `sentences(j)`.
3. Answer: `sentences(0)`.

**Dry run** `"catsanddog"`: at 0, `cat` → at 3 `sand` → at 7 `dog` → end ✔ "cat sand dog". At 0, `cats` → at 4 `and` → at 7 `dog` ✔ "cats and dog" (the result for index 7 is reused from the cache).
""",
        complexity="The output can be exponential (2ⁿ⁻¹ sentences for `\"aaa...\"` with dictionary `a, aa, ...`), so O(n · 2ⁿ) worst case. With memoisation, suffixes with no solution cost only O(n · L) once each.",
        pitfalls=r"""
- Greedy longest-match (wrong solution #1) finds at most one sentence and can dead-end.
- Forbidding a word from being reused (wrong solution #2).
- Returning `[""]` instead of `[]` when no sentence exists — the empty sentence is only the base case for the *end* of the string.
- No memoisation: exponential time on inputs that have no answer at all.
""",
        follow_up="*Word Break* (I) only asks whether a split exists — a 1-D DP. A trie over the dictionary speeds up the prefix tests when words are long.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="matchsticks-to-square",
    title="Matchsticks to Square",
    difficulty="Medium",
    pattern="Backtracking",
    leetcode="https://leetcode.com/problems/matchsticks-to-square/",
    neetcode="https://neetcode.io/problems/matchsticks-to-square",
    entry="makesquare",
    description=r"""
You are given the lengths of some matchsticks. Using **every** matchstick exactly once, and without
breaking any, decide whether they can be laid end to end to form the four sides of a square.
Return `True` or `False`.

**Constraints:** `1 <= len(matchsticks) <= 15`, `1 <= matchsticks[i] <= 10^8`.

**Example 1:** `[1,1,2,2,2]` → `True` (sides: 2, 2, 2, 1+1)

**Example 2:** `[3,3,3,3,4]` → `False` (the total 16 gives side 4, but the 3s cannot be completed to 4)
""",
    starter='''class Solution:
    def makesquare(self, matchsticks: List[int]) -> bool:
        pass
''',
    solution='''class Solution:
    def makesquare(self, matchsticks):
        total = sum(matchsticks)
        if len(matchsticks) < 4 or total % 4:
            return False
        side = total // 4
        sticks = sorted(matchsticks, reverse=True)     # big sticks first: fail early
        if sticks[0] > side:
            return False
        sides = [0, 0, 0, 0]

        def dfs(i):
            if i == len(sticks):
                return True                            # all placed; sums are forced to be equal
            tried = set()
            for j in range(4):
                if sides[j] + sticks[i] <= side and sides[j] not in tried:
                    tried.add(sides[j])                # sides with equal length are interchangeable
                    sides[j] += sticks[i]
                    if dfs(i + 1):
                        return True
                    sides[j] -= sticks[i]
            return False

        return dfs(0)
''',
    tests=[
        [[1, 1, 2, 2, 2]],
        [[3, 3, 3, 3, 4]],
        [[5, 5, 5, 5]],
        [[1, 2, 3]],
        [[1, 1, 1, 1, 1]],
        [[2, 2, 2, 2, 2, 2]],
        [[4, 5, 5, 5, 8, 3, 9, 6, 8, 7]],
        [[7, 8, 8, 9, 9, 5, 3, 9, 9, 5]],
        [[7, 4, 7, 3, 9, 8, 2, 8, 5, 7]],
        [[100000000, 100000000, 100000000, 100000000]],
        [[5, 5, 5, 5, 4, 4, 4, 4, 3, 3, 3, 3]],
        [[1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 6]],
        [[10, 6, 5, 5, 5, 3, 3, 3, 2, 2, 2, 2]],
        [[12, 12, 12, 16, 20, 24, 28, 32, 36, 40, 44, 48, 52, 56, 60]],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def makesquare(self, matchsticks):
        return len(matchsticks) >= 4 and sum(matchsticks) % 4 == 0 and max(matchsticks) <= sum(matchsticks) // 4
''',
        '''class Solution:
    def makesquare(self, matchsticks):
        total = sum(matchsticks)
        if total % 4: return False
        side = total // 4; sides = [0] * 4
        for x in sorted(matchsticks, reverse=True):
            for j in range(4):
                if sides[j] + x <= side:
                    sides[j] += x; break
            else:
                return False
        return True
''',
    ],
    guide=dict(
        prereqs="Backtracking with pruning and symmetry breaking (lesson *Duplicates, pruning and constraint search*).",
        intuition=r"""
The side length is forced: `total / 4`. The task is then to deal every stick into one of four
"buckets" so that no bucket exceeds the side length — if all sticks are placed, each bucket must hold
exactly one side. Each stick has four options, so the raw tree has 4ⁿ leaves; three prunings make it
fast: place **long sticks first** (they fail soonest), never overfill a bucket, and never try two
buckets that currently hold the **same** length (they are interchangeable).
""",
        hints=[
            "What must the side length be? Which quick checks rule out a square immediately?",
            "Assign sticks one at a time to one of four sides, undoing the assignment when it leads nowhere.",
            "Sort descending. Skip a side if adding the stick exceeds the target, or if you already tried a side with the same current length for this stick.",
        ],
        brute_force="Try all 4ⁿ assignments of sticks to sides and test each: 4¹⁵ ≈ 10⁹ — too slow without pruning.",
        approach=r"""
1. Reject if fewer than 4 sticks, total not divisible by 4, or the longest stick exceeds the side.
2. Sort descending; `sides = [0,0,0,0]`.
3. `dfs(i)`: place stick `i` on each side that still has room (skipping sides whose length was already tried); recurse; undo.

**Dry run** `[2,2,2,1,1]`, side 2: the three 2s each fill a side of their own (a full side has no room, so the next 2 moves on); the first 1 goes on the fourth side, and so does the second. All sticks placed → `True`.

For `[4,3,3,3,3]` (side 4): the 4 fills one side; three 3s take the other three sides; the last 3 fits nowhere. Undoing does not help, because every other arrangement is the same up to renaming sides → `False`.
""",
        complexity="O(4ⁿ) worst case, far less with the prunings; recursion depth n. A bitmask DP alternative runs in O(n · 2ⁿ).",
        pitfalls=r"""
- Checking only the arithmetic conditions (wrong solution #1 accepts `[3,3,3,3,4]`).
- Greedy first-fit without backtracking (wrong solution #2 fails `[4,5,5,5,8,3,9,6,8,7]`).
- Forgetting to undo `sides[j] += stick` on failure.
- Sorting ascending — small sticks first makes failures appear very deep in the tree.
""",
        follow_up="*Partition to K Equal Sum Subsets* is the same problem with k buckets. *Fair Distribution of Cookies* minimises the largest bucket instead.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="sudoku-solver",
    title="Sudoku Solver",
    difficulty="Hard",
    pattern="Backtracking",
    leetcode="https://leetcode.com/problems/sudoku-solver/",
    entry="solveSudoku",
    inplace_arg=0,
    checker=_SUDOKU_CHECK,
    description=r"""
Fill in a partially completed 9 × 9 Sudoku grid **in place**. The grid is a list of 9 rows; each cell
is a string: a digit `"1"`–`"9"` or `"."` for an empty cell.

A finished grid must have each digit 1–9 exactly once in every **row**, every **column**, and every
one of the nine **3 × 3 boxes**. The given digits must stay where they are. Every test puzzle has at
least one solution; if a puzzle has several, any valid completion is accepted. Return nothing.

**Example** (first three rows shown)

```
5 3 . | . 7 . | . . .        5 3 4 | 6 7 8 | 9 1 2
6 . . | 1 9 5 | . . .  --->  6 7 2 | 1 9 5 | 3 4 8
. 9 8 | . . . | . 6 .        1 9 8 | 3 4 2 | 5 6 7
```
""",
    starter='''class Solution:
    def solveSudoku(self, board: List[List[str]]) -> None:
        """
        Do not return anything, modify board in-place instead.
        """
        pass
''',
    solution='''class Solution:
    def solveSudoku(self, board):
        rows = [set() for _ in range(9)]
        cols = [set() for _ in range(9)]
        boxes = [set() for _ in range(9)]
        empty = []
        for r in range(9):
            for c in range(9):
                d = board[r][c]
                if d == ".":
                    empty.append((r, c))
                else:
                    rows[r].add(d); cols[c].add(d); boxes[(r // 3) * 3 + c // 3].add(d)
        digits = "123456789"

        def options(r, c):
            used = rows[r] | cols[c] | boxes[(r // 3) * 3 + c // 3]
            return [d for d in digits if d not in used]

        def dfs():
            if not empty:
                return True
            # most constrained cell first
            k = min(range(len(empty)), key=lambda i: len(options(*empty[i])))
            empty[k], empty[-1] = empty[-1], empty[k]
            r, c = empty.pop()
            b = (r // 3) * 3 + c // 3
            for d in options(r, c):
                board[r][c] = d
                rows[r].add(d); cols[c].add(d); boxes[b].add(d)
                if dfs():
                    return True
                rows[r].remove(d); cols[c].remove(d); boxes[b].remove(d)
            board[r][c] = "."
            empty.append((r, c))
            return False

        dfs()
''',
    tests=[
        [[["5", "3", ".", ".", "7", ".", ".", ".", "."], ["6", ".", ".", "1", "9", "5", ".", ".", "."],
          [".", "9", "8", ".", ".", ".", ".", "6", "."], ["8", ".", ".", ".", "6", ".", ".", ".", "3"],
          ["4", ".", ".", "8", ".", "3", ".", ".", "1"], ["7", ".", ".", ".", "2", ".", ".", ".", "6"],
          [".", "6", ".", ".", ".", ".", "2", "8", "."], [".", ".", ".", "4", "1", "9", ".", ".", "5"],
          [".", ".", ".", ".", "8", ".", ".", "7", "9"]]],
        _sudoku(random.Random(81), 0),
        _sudoku(random.Random(82), 1),
        _sudoku(random.Random(83), 10),
        _sudoku(random.Random(84), 25),
        _sudoku(random.Random(85), 35),
        _sudoku(random.Random(86), 40),
        _sudoku(random.Random(87), 45),
        _sudoku(random.Random(88), 48),
        _sudoku(random.Random(89), 50),
        _sudoku(random.Random(90), 52),
    ],
    examples=1,
    wrong_solutions=[
        '''class Solution:
    def solveSudoku(self, board):
        for r in range(9):
            for c in range(9):
                if board[r][c] == ".":
                    used = set(board[r]) | {board[i][c] for i in range(9)}
                    br, bc = 3 * (r // 3), 3 * (c // 3)
                    used |= {board[br + a][bc + b] for a in range(3) for b in range(3)}
                    for d in "123456789":
                        if d not in used:
                            board[r][c] = d; break
''',
        '''class Solution:
    def solveSudoku(self, board):
        for r in range(9):
            missing = [d for d in "123456789" if d not in board[r]]
            for c in range(9):
                if board[r][c] == ".": board[r][c] = missing.pop()
''',
    ],
    guide=dict(
        prereqs="Constraint search with sets for O(1) validity checks (lesson *Duplicates, pruning and constraint search*, N-Queens section).",
        intuition=r"""
Sudoku is N-Queens with more rules. Pick an empty cell, try each digit that does not already appear
in its row, column or box, and recurse on the rest of the grid; if no digit leads to a full grid,
erase the cell and report failure to the caller, which then tries its next digit. Keeping a set of
used digits per row, column and box makes "is this digit allowed here?" a constant-time question.
Choosing the empty cell with the **fewest legal digits** first keeps the tree narrow.
""",
        hints=[
            "What is one 'decision' in this puzzle, and what makes a decision legal?",
            "Keep 27 sets (9 rows, 9 columns, 9 boxes). Box index of (r, c) is (r // 3) * 3 + c // 3.",
            "dfs(): pick an empty cell; for each allowed digit: place, update sets, recurse, and undo if the recursion fails. Return True when no empty cells remain.",
        ],
        brute_force="Fill every empty cell with every digit (9^(empty cells) grids) and validate at the end. Even 20 empty cells would be about 10¹⁹ grids.",
        approach=r"""
1. Scan the grid once: record used digits per row/column/box and collect the empty cells.
2. `dfs()`: no empty cell → solved. Otherwise take the empty cell with the fewest options; for each option place it, recurse, undo on failure.
3. Because the function returns `True` as soon as the grid is complete, the board is left in its solved state.

**Dry run** (example, cell (0,2)): row 0 has {5,3,7}, column 2 has {8}, box 0 has {5,3,6,9,8} → options {1,2,4}. Try 1 ... eventually a contradiction appears further on, the recursion unwinds, 2 is tried, then 4, which leads to the full solution.
""",
        complexity="Exponential in the number of empty cells in the worst case; with the fewest-options heuristic, ordinary puzzles need only a few hundred to a few thousand placements. Space O(81).",
        pitfalls=r"""
- Greedy filling without undo (wrong solution #1) paints itself into a corner.
- Satisfying only the row rule (wrong solution #2).
- Forgetting to restore the cell to `"."` and the three sets when a digit fails.
- Continuing to search (and undoing a finished grid) after a solution is found — propagate `True` upward.
- Mixing integers and strings: cells are strings.
""",
        follow_up="*Valid Sudoku* only checks the three rules on a partial grid. Faster solvers use bitmasks and constraint propagation (naked singles) or Knuth's Dancing Links.",
    ),
),
]
