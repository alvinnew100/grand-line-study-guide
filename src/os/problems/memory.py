import random as _random

_r = _random.Random(23)


def _refs(n, pages):
    return [_r.randrange(pages) for _ in range(n)]


def _local_refs(n, pages, spread=3):
    out, cur = [], 0
    for _ in range(n):
        if _r.random() < 0.1:
            cur = _r.randrange(pages)
        out.append((cur + _r.randrange(spread)) % pages)
    return out


_BELADY = [1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5]
_CLASSIC = [7, 0, 1, 2, 0, 3, 0, 4, 2, 3, 0, 3, 2, 1, 2, 0, 1, 7, 0, 1]

_FIFO_WRONG_AS_LRU = '''from collections import OrderedDict

def {name}(refs, frames):
    if frames == 0:
        return len(refs)
    mem, faults = OrderedDict(), 0
    for p in refs:
        if p in mem:
            mem.move_to_end(p)
            continue
        faults += 1
        if len(mem) == frames:
            mem.popitem(last=False)
        mem[p] = True
    return faults
'''

_FIFO_SRC = '''from collections import deque

def {name}(refs, frames):
    if frames == 0:
        return len(refs)
    mem, order, faults = set(), deque(), 0
    for p in refs:
        if p in mem:
            continue
        faults += 1
        if len(mem) == frames:
            mem.discard(order.popleft())
        mem.add(p)
        order.append(p)
    return faults
'''

PROBLEMS = [
dict(
    id="os-fifo-page-faults",
    title="Page Faults under FIFO Replacement",
    difficulty="Easy",
    pattern="Page Replacement",
    entry="fifo_faults",
    description=r"""
A process touches pages in the order given by `refs`. Physical memory has `frames` page frames, all
initially empty. On a reference to a page that is not loaded, a **page fault** occurs; if no frame is
free, the page that has been in memory **longest** (first in, first out) is evicted.

Return the number of page faults.

**Example:** `refs = [1, 2, 3, 1, 4, 2], frames = 3` → `4`
(faults on 1, 2, 3; hit on 1; fault on 4 evicts page 1; hit on 2).

**Constraints:** `0 ≤ len(refs) ≤ 10^5`, `0 ≤ frames ≤ 10^4`. With zero frames every reference faults.
""",
    starter='''def fifo_faults(refs, frames):
    pass
''',
    solution=_FIFO_SRC.format(name="fifo_faults"),
    tests=[
        [[1, 2, 3, 1, 4, 2], 3],
        [_BELADY, 3],
        [_BELADY, 4],
        [[], 3],
        [[5, 5, 5, 5], 1],
        [[1, 2, 1, 2, 1, 2], 1],
        [[1, 2, 3], 0],
        [[1, 2, 3, 4], 10],
        [_CLASSIC, 3],
        [[1, 2, 3, 1, 4, 1, 5, 1, 2], 3],
        [_refs(200, 12), 5],
        [_local_refs(5000, 60), 8],
        [_refs(60000, 500), 100],
    ],
    examples=2,
    wrong_solutions=[
        _FIFO_WRONG_AS_LRU.format(name="fifo_faults"),
        '''def fifo_faults(refs, frames):
    return len(set(refs))
''',
    ],
    guide=dict(
        prereqs="Paging and page faults (memory lessons), `set` and `collections.deque`.",
        intuition="FIFO only cares about *load order*. A hit changes nothing at all — that is exactly what makes it different from LRU, and exactly why it can evict a heavily used page.",
        hints=[
            "You need two views of memory: fast membership (a set) and age order (a queue).",
            "On a hit do nothing. On a fault with full memory, pop the queue's left end and remove that page from the set.",
            "Handle `frames == 0` up front: every reference is a fault and there is nothing to evict.",
        ],
        brute_force="Keep the loaded pages in a plain list: `p in list` is O(frames) and `pop(0)` is O(frames), giving O(n·frames). Correct, but too slow for 60,000 references and hundreds of frames.",
        approach="""1. `mem = set()`, `order = deque()`, `faults = 0`.
2. For each page: if in `mem`, continue. Otherwise count a fault; if `len(mem) == frames`, evict `order.popleft()`; add the page to both structures.

**Dry run** `[1,2,3,1,4,2]`, 3 frames: load 1, 2, 3 (3 faults, queue 1→2→3). 1 hits, queue unchanged. 4 faults, evicts 1 (queue 2→3→4). 2 hits. Total 4.""",
        complexity="O(n) time with O(1) work per reference; O(frames) space.",
        pitfalls="Moving a page to the back of the queue on a hit (that is LRU). Returning the count of distinct pages, which ignores re-faults after eviction. Crashing on zero frames.",
        follow_up="Run the reference string `1 2 3 4 1 2 5 1 2 3 4 5` with 3 and then 4 frames. More memory gives *more* faults — Belady's anomaly, impossible for stack algorithms such as LRU.",
    ),
),
dict(
    id="os-lru-page-faults",
    title="Page Faults under LRU Replacement",
    difficulty="Easy",
    pattern="Page Replacement",
    entry="lru_faults",
    description=r"""
Same setting as FIFO paging, but on a fault with no free frame the victim is the page whose **most
recent use lies furthest in the past** (least recently used).

Given the reference string `refs` and the number of frames, return the number of page faults.

**Example:** `refs = [1, 2, 3, 1, 4, 2], frames = 3` → `5`
(4 evicts page 2, the least recently used, so the final reference to 2 faults again).

**Constraints:** `0 ≤ len(refs) ≤ 10^5`, `0 ≤ frames ≤ 10^4`.
""",
    starter='''def lru_faults(refs, frames):
    pass
''',
    solution=_FIFO_WRONG_AS_LRU.format(name="lru_faults"),
    tests=[
        [[1, 2, 3, 1, 4, 2], 3],
        [_BELADY, 3],
        [_BELADY, 4],
        [[], 2],
        [[9], 1],
        [[1, 2, 3], 0],
        [[1, 1, 2, 2, 1, 1], 1],
        [_CLASSIC, 3],
        [_CLASSIC, 4],
        [[1, 2, 3, 1, 4, 1, 5, 1, 2], 3],
        [_refs(300, 10), 4],
        [_local_refs(5000, 60), 8],
        [_refs(60000, 500), 100],
    ],
    examples=2,
    wrong_solutions=[
        _FIFO_SRC.format(name="lru_faults"),
        '''def lru_faults(refs, frames):
    if frames == 0:
        return len(refs)
    count, mem, faults = {}, set(), 0
    for p in refs:
        count[p] = count.get(p, 0) + 1
        if p in mem:
            continue
        faults += 1
        if len(mem) == frames:
            mem.discard(min(mem, key=lambda q: (count[q], q)))
        mem.add(p)
    return faults
''',
    ],
    guide=dict(
        prereqs="FIFO page replacement, `collections.OrderedDict` (or a dict of last-use times).",
        intuition="The recent past is the best cheap predictor of the near future: a page untouched for a long time probably belongs to a phase the program has left. Keep pages ordered by last use; the stale end is the victim.",
        hints=[
            "Start from FIFO and ask: what must change on a *hit*?",
            "An `OrderedDict` keeps insertion order; `move_to_end(page)` refreshes a page in O(1).",
            "Evict with `popitem(last=False)` — the entry that has gone longest without being refreshed.",
        ],
        brute_force="Store `last_used[page] = index` and on each eviction scan all loaded pages for the smallest value: O(frames) per fault, O(n·frames) worst case. Simple and worth writing first.",
        approach="""1. `mem = OrderedDict()`.
2. Hit → `mem.move_to_end(p)`. Miss → fault; if full, `mem.popitem(last=False)`; then `mem[p] = True`.

**Dry run** `[1,2,3,1,4,2]`, 3 frames: after 1,2,3 the order is 1,2,3 (3 faults). Hit on 1 → 2,3,1. 4 faults and evicts 2 → 3,1,4. 2 faults and evicts 3. Total 5.""",
        complexity="O(n) time, O(frames) space.",
        pitfalls="Confusing LRU with LFU (least *frequently* used) — the second wrong solution does exactly that. Forgetting to refresh on a hit turns the code into FIFO.",
        follow_up="True LRU needs work on *every* memory reference, which hardware cannot afford; that is why real kernels approximate it with reference bits (clock, aging).",
    ),
),
dict(
    id="os-optimal-page-faults",
    title="Page Faults under the Optimal (Belady) Policy",
    difficulty="Medium",
    pattern="Page Replacement",
    entry="optimal_faults",
    description=r"""
The optimal replacement policy looks into the future: on a fault with no free frame it evicts the
loaded page whose **next use is furthest away** (or that is never used again). It cannot be built in a
real system, but it gives the lower bound every practical algorithm is measured against.

Return the number of page faults for `refs` with `frames` frames.

**Example:** `refs = [1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5], frames = 3` → `7`

**Constraints:** `0 ≤ len(refs) ≤ 10^5`, `0 ≤ frames ≤ 10^4`. Aim for better than O(n · frames).
""",
    starter='''def optimal_faults(refs, frames):
    pass
''',
    solution='''import heapq

def optimal_faults(refs, frames):
    if frames == 0:
        return len(refs)
    n = len(refs)
    INF = n + 1
    nxt, seen = [INF] * n, {}
    for i in range(n - 1, -1, -1):
        nxt[i] = seen.get(refs[i], INF)
        seen[refs[i]] = i
    cur, heap, faults = {}, [], 0
    for i, p in enumerate(refs):
        if p not in cur:
            faults += 1
            if len(cur) == frames:
                while True:
                    d, q = heapq.heappop(heap)
                    if cur.get(q) == -d:
                        del cur[q]
                        break
        cur[p] = nxt[i]
        heapq.heappush(heap, (-nxt[i], p))
    return faults
''',
    tests=[
        [_BELADY, 3],
        [[1, 2, 3, 1, 4, 2], 3],
        [_BELADY, 4],
        [[], 1],
        [[4, 4, 4], 1],
        [[1, 2, 3], 0],
        [[1, 2, 3, 4, 5], 2],
        [_CLASSIC, 3],
        [_CLASSIC, 4],
        [[1, 2, 3, 4, 1, 2, 3, 4], 3],
        [_refs(300, 10), 4],
        [_local_refs(4000, 50), 6],
        [_refs(50000, 400), 120],
    ],
    examples=2,
    wrong_solutions=[
        _FIFO_WRONG_AS_LRU.format(name="optimal_faults"),
        _FIFO_SRC.format(name="optimal_faults"),
    ],
    guide=dict(
        prereqs="FIFO and LRU fault counting, heaps, precomputing 'next occurrence' arrays with a right-to-left scan.",
        intuition="If you must throw something away, throw away what you will need last. An exchange argument shows no other choice can produce fewer faults: swapping any other victim for the farthest-future one never makes things worse.",
        hints=[
            "For every position `i` precompute `nxt[i]`, the index of the next reference to the same page (or infinity). One backward pass with a dict does it.",
            "Each loaded page has a current 'next use'. The victim is the page with the largest one — a max-heap.",
            "When a page is hit its next use changes. Push the new value and let stale heap entries be discarded lazily when popped.",
        ],
        brute_force="On each fault, for every loaded page scan forward through `refs` to find its next use. O(n · frames · n) in the worst case; fine for classroom-sized strings, hopeless for 50,000 references.",
        approach="""1. Backward pass → `nxt`.
2. `cur[page]` = its next-use index. Heap of `(-next_use, page)`.
3. For each reference: if absent, fault; if full, pop until the entry matches `cur` (not stale), delete that page. Then set `cur[p] = nxt[i]` and push.

**Dry run** `[1,2,3,4,1,2,5,...]`, 3 frames: after 1,2,3 the next uses are 4,5,9. Page 4 faults → evict 3 (next use 9 is farthest). 1 and 2 hit. 5 faults: next uses are 1→7, 2→8, 4→10 → evict 4. Continuing gives 7 faults in total.""",
        complexity="O(n log n) time (each reference pushes once; each entry is popped at most once), O(n) space.",
        pitfalls="Treating 'never used again' as distance 0 instead of infinity. Forgetting to update a page's next use on a hit. Using stale heap entries. Believing this can be implemented in an OS — it needs the future.",
        follow_up="Compare the three counts on the same string: optimal ≤ LRU always, and LRU's fault count never rises when frames are added (it is a *stack algorithm*).",
    ),
),
dict(
    id="os-clock-page-faults",
    title="Clock (Second Chance) Replacement",
    difficulty="Medium",
    pattern="Page Replacement",
    entry="clock_replace",
    description=r"""
Simulate the **clock** page replacement algorithm.

Memory is a circular array of `frames` slots, all empty, and a hand that starts at slot 0. Every loaded
page has a reference bit `R`.

- **Hit:** set the page's `R` to 1. The hand does not move.
- **Fault:** look at the slot under the hand. While it holds a page with `R = 1`, clear the bit and
  advance the hand (wrapping around). When the hand rests on an empty slot or a page with `R = 0`,
  put the new page there (evicting the old occupant, if any), set its `R` to 1 and advance the hand one slot.

Return `[faults, slots]` where `slots` is the final content of the frames in slot order, using `-1` for
an empty slot.

**Example:** `refs = [1, 2, 3, 1, 4], frames = 3` → `[4, [4, 2, 3]]`
(when 4 arrives all three bits are 1; the hand clears them in one full circle and replaces page 1 at slot 0).

**Constraints:** `0 ≤ len(refs) ≤ 10^5`, `1 ≤ frames ≤ 10^4`, page numbers are non-negative.
""",
    starter='''def clock_replace(refs, frames):
    pass
''',
    solution='''def clock_replace(refs, frames):
    slots = [-1] * frames
    rbit = [0] * frames
    where = {}
    hand = faults = 0
    for p in refs:
        if p in where:
            rbit[where[p]] = 1
            continue
        faults += 1
        while slots[hand] != -1 and rbit[hand]:
            rbit[hand] = 0
            hand = (hand + 1) % frames
        if slots[hand] != -1:
            del where[slots[hand]]
        slots[hand] = p
        rbit[hand] = 1
        where[p] = hand
        hand = (hand + 1) % frames
    return [faults, slots]
''',
    tests=[
        [[1, 2, 3, 1, 4], 3],
        [[1, 2, 3, 4, 1, 5], 3],
        [[], 2],
        [[7, 7, 7], 1],
        [[1, 2, 1, 2], 1],
        [[1, 2], 4],
        [[1, 2, 3, 4, 2, 5, 2, 6], 3],
        [_CLASSIC, 3],
        [_BELADY, 4],
        [[1, 2, 3, 2, 4, 2, 5, 2, 6, 2, 7], 3],
        [_refs(300, 9), 4],
        [_local_refs(5000, 40), 7],
        [_refs(50000, 300), 64],
    ],
    examples=2,
    wrong_solutions=[
        '''from collections import deque

def clock_replace(refs, frames):
    slots = [-1] * frames
    where = {}
    hand = faults = 0
    for p in refs:
        if p in where:
            continue
        faults += 1
        if slots[hand] != -1:
            del where[slots[hand]]
        slots[hand] = p
        where[p] = hand
        hand = (hand + 1) % frames
    return [faults, slots]
''',
        '''def clock_replace(refs, frames):
    slots = [-1] * frames
    rbit = [0] * frames
    where = {}
    hand = faults = 0
    for p in refs:
        if p in where:
            rbit[where[p]] = 1
            continue
        faults += 1
        while slots[hand] != -1 and rbit[hand]:
            rbit[hand] = 0
            hand = (hand + 1) % frames
        if slots[hand] != -1:
            del where[slots[hand]]
        slots[hand] = p
        rbit[hand] = 0
        where[p] = hand
        hand = (hand + 1) % frames
    return [faults, slots]
''',
    ],
    guide=dict(
        prereqs="FIFO replacement, the hardware-maintained referenced bit, modular arithmetic for circular arrays.",
        intuition="Clock is FIFO with mercy. The hand visits pages in load order, but a page that has been used since the hand last passed gets its bit cleared and one more lap of life. Only pages that stay untouched for a whole revolution are evicted.",
        hints=[
            "Keep three things: `slots` (page per frame), `rbit` (per frame) and a dict from page to slot for O(1) hits.",
            "The fault loop is: while the slot under the hand is occupied *and* its bit is 1, clear and step.",
            "The sweep always terminates: after at most one full circle every bit is 0.",
        ],
        brute_force="Implement second chance literally as a queue: pop the oldest page; if its bit is set, clear it and append it to the tail; repeat. Same victims, but each move shuffles list elements, whereas the circular array just moves an index.",
        approach="""1. On a hit set the bit; nothing else.
2. On a fault sweep the hand as described, replace, set bit, advance.

**Dry run** `[1,2,3,1,4]`, 3 frames: 1, 2, 3 fill slots 0–2 with R=1; hand is back at 0. Hit on 1. Fault on 4: slot 0 R=1 → clear, slot 1 → clear, slot 2 → clear, back at slot 0 with R=0 → replace page 1. Slots `[4,2,3]`, hand at 1, faults 4.""",
        complexity="Amortised O(1) per reference in practice; a single fault can sweep O(frames) slots, so the worst case is O(n · frames). Space O(frames).",
        pitfalls="Moving the hand on a hit. Loading the new page with R=0 (it would be evicted immediately by the next sweep — second wrong solution). Forgetting to delete the evicted page from the lookup dict. Not advancing the hand after placement.",
        follow_up="Add a modified bit and prefer clean pages (the enhanced clock used by many kernels), or add a second hand a fixed distance behind the first.",
    ),
),
dict(
    id="os-aging-page-replacement",
    title="Aging Counters and Victim Selection",
    difficulty="Medium",
    pattern="Page Replacement",
    entry="aging",
    description=r"""
The **aging** algorithm approximates LRU in software. Every page in memory has a `bits`-bit counter,
initially 0. At each clock tick, for every page:

1. shift its counter right by one bit,
2. put the page's referenced bit (1 if the page was touched during that tick, else 0) into the leftmost position.

`ticks[t]` lists the pages referenced during tick `t` (possibly with repeats). Pages are numbered
`0 .. pages-1` and all of them stay in memory.

Return `[counters, victim]`: the final counter of each page, and the page that would be evicted now —
the one with the smallest counter (lowest page number on ties).

**Example:** `ticks = [[0, 2], [0], [1]], pages = 3, bits = 4` → `[[6, 8, 2], 2]`
(page 0: `1000 → 1100 → 0110`; page 1: `0000 → 0000 → 1000`; page 2: `1000 → 0100 → 0010`).

**Constraints:** `1 ≤ pages ≤ 2000`, `1 ≤ bits ≤ 32`, `0 ≤ len(ticks) ≤ 2000`.
""",
    starter='''def aging(ticks, pages, bits):
    pass
''',
    solution='''def aging(ticks, pages, bits):
    counters = [0] * pages
    top = 1 << (bits - 1)
    for tick in ticks:
        touched = set(tick)
        for p in range(pages):
            counters[p] >>= 1
            if p in touched:
                counters[p] |= top
    victim = min(range(pages), key=lambda p: (counters[p], p))
    return [counters, victim]
''',
    tests=[
        [[[0, 2], [0], [1]], 3, 4],
        [[[0], [1], [2], [3]], 4, 8],
        [[], 3, 8],
        [[[0, 0, 0]], 1, 1],
        [[[1], [1], [1], [0]], 2, 2],
        [[[0, 1], [], [], []], 2, 3],
        [[[2], [], [2], [], [0, 1]], 3, 8],
        [[[0], [0], [0], [0], [1]], 3, 4],
        [[[0, 1, 2]] * 40, 4, 32],
        [[[1, 2], [0, 2], [0, 1], [2]], 3, 8],
        [[_refs(5, 12) for _ in range(30)], 12, 8],
        [[_refs(40, 300) for _ in range(200)], 300, 16],
    ],
    examples=2,
    wrong_solutions=[
        '''def aging(ticks, pages, bits):
    counters = [0] * pages
    mask = (1 << bits) - 1
    for tick in ticks:
        touched = set(tick)
        for p in range(pages):
            counters[p] = (counters[p] << 1) & mask
            if p in touched:
                counters[p] |= 1
    victim = min(range(pages), key=lambda p: (counters[p], p))
    return [counters, victim]
''',
        '''def aging(ticks, pages, bits):
    counters = [0] * pages
    top = 1 << (bits - 1)
    for tick in ticks:
        for p in tick:
            counters[p] = (counters[p] >> 1) | top
    victim = min(range(pages), key=lambda p: (counters[p], p))
    return [counters, victim]
''',
    ],
    guide=dict(
        prereqs="Bit shifts and masks, the referenced bit, why exact LRU is too expensive (page replacement lesson).",
        intuition="Read a counter as a history string, newest tick on the left. Comparing counters as integers compares histories lexicographically: a page touched in the latest tick beats every page that was not, no matter how busy the others were long ago.",
        hints=[
            "Every page ages every tick — including the ones that were not referenced.",
            "The new bit goes in at position `bits - 1`: `counter = (counter >> 1) | (R << (bits - 1))`.",
            "Convert each tick's list to a set first so duplicate references inside one tick count once.",
        ],
        brute_force="Store each page's history as a list of 0/1 values, prepend the new bit each tick, truncate to `bits`, and convert to an integer at the end. Same answer with far more allocation.",
        approach="""1. `counters = [0] * pages`, `top = 1 << (bits - 1)`.
2. For each tick: build the touched set; shift every counter right; OR in `top` for touched pages.
3. Victim = argmin of `(counter, page)`.

**Dry run** from the example with 4 bits: tick 0 touches 0 and 2 → `[8,0,8]`. Tick 1 touches 0 → `[12,0,4]`. Tick 2 touches 1 → `[6,8,2]`. Smallest is page 2.""",
        complexity="O(ticks × pages + total references) time, O(pages) space.",
        pitfalls="Shifting left and inserting at the right (first wrong solution) — that makes *old* references the most significant. Ageing only the referenced pages (second wrong solution), so idle pages never decay. Counting a page twice in one tick.",
        follow_up="Aging differs from true LRU in two ways: it cannot order two references inside one tick, and its memory is only `bits` ticks long. Construct inputs where each limitation picks a different victim from LRU.",
    ),
),
dict(
    id="os-working-set-size",
    title="Working Set Size over Time",
    difficulty="Medium",
    pattern="Page Replacement",
    entry="working_set_sizes",
    description=r"""
The **working set** $w(k, t)$ of a process is the set of distinct pages among its most recent `k`
memory references at time `t`.

Given a reference string `refs` and a window `k ≥ 1`, return a list `out` with `out[t]` = the number
of distinct pages among `refs[max(0, t-k+1) .. t]` (the current reference is included).

**Example:** `refs = [1, 2, 1, 3, 3, 3, 4], k = 3` → `[1, 2, 2, 3, 2, 1, 2]`

**Constraints:** `0 ≤ len(refs) ≤ 2·10^5`, `1 ≤ k ≤ 2·10^5`. An O(n·k) solution is too slow.
""",
    starter='''def working_set_sizes(refs, k):
    pass
''',
    solution='''def working_set_sizes(refs, k):
    count, out = {}, []
    for t, p in enumerate(refs):
        count[p] = count.get(p, 0) + 1
        if t >= k:
            old = refs[t - k]
            count[old] -= 1
            if count[old] == 0:
                del count[old]
        out.append(len(count))
    return out
''',
    tests=[
        [[1, 2, 1, 3, 3, 3, 4], 3],
        [[5, 5, 5, 5], 2],
        [[], 4],
        [[8], 1],
        [[1, 2, 3, 4, 5], 1],
        [[1, 2, 3, 4, 5], 100],
        [[1, 2, 1, 2, 1, 2], 2],
        [[1, 2, 3, 1, 2, 3, 4, 4, 4, 4], 4],
        [[3, 3, 1, 3, 3, 1, 2], 3],
        [_refs(200, 6), 5],
        [_local_refs(3000, 80, 4), 50],
        [_refs(20000, 1000), 3000],
    ],
    examples=2,
    wrong_solutions=[
        '''def working_set_sizes(refs, k):
    count, out = {}, []
    for t, p in enumerate(refs):
        count[p] = count.get(p, 0) + 1
        if t > k:
            old = refs[t - k - 1]
            count[old] -= 1
            if count[old] == 0:
                del count[old]
        out.append(len(count))
    return out
''',
        '''def working_set_sizes(refs, k):
    seen, out = set(), []
    for p in refs:
        seen.add(p)
        out.append(len(seen))
    return out
''',
    ],
    guide=dict(
        prereqs="Sliding-window technique with a frequency map; locality of reference and the working-set model (memory lessons).",
        intuition="As the window slides by one position, exactly one reference enters and at most one leaves. Track how many times each page occurs inside the window; the number of keys with a non-zero count is the working set size.",
        hints=[
            "Recomputing `len(set(window))` every step costs O(k) each time. What changes between consecutive windows?",
            "Use a dict of counts. Add the new page; if the window is now longer than `k`, decrement the page falling off the left edge.",
            "Delete a key when its count reaches zero so that `len(count)` is the answer.",
        ],
        brute_force="`[len(set(refs[max(0,t-k+1):t+1])) for t in range(n)]` — clear and correct, O(n·k). Use it to test the fast version on random inputs.",
        approach="""1. For index `t`: `count[refs[t]] += 1`.
2. If `t >= k`: the element `refs[t-k]` leaves; decrement and delete at zero.
3. Append `len(count)`.

**Dry run** `[1,2,1,3,3,3,4]`, k=3: windows are [1], [1,2], [1,2,1], [2,1,3], [1,3,3], [3,3,3], [3,3,4] → sizes 1,2,2,3,2,1,2.""",
        complexity="O(n) time, O(min(k, distinct pages)) space.",
        pitfalls="Off-by-one on the window edge (the first wrong solution keeps k+1 references). Decrementing without deleting, then counting keys with zero counts. Returning the cumulative number of distinct pages.",
        follow_up="Real kernels define the window in *virtual time* (CPU time used by the process) and approximate it with a referenced bit plus a time-of-last-use field — the WSClock algorithm.",
    ),
),
dict(
    id="os-two-level-translation",
    title="Two-level Page Table Translation",
    difficulty="Medium",
    pattern="Virtual Memory",
    entry="translate",
    description=r"""
Translate a virtual address with a **two-level page table**.

A virtual address is split, from most to least significant bits, into:

`| directory index | table index (pt_bits bits) | offset (offset_bits bits) |`

- `page_dir` is a list. `page_dir[d]` is either `None` (no second-level table) or a list — the second-level table.
- An entry `table[t]` is either `None` (page not present) or the physical **frame number**.
- An index beyond the end of a list also counts as "not mapped".

Return the physical address `frame * 2**offset_bits + offset`, or `-1` if the translation faults.

**Example:** `vaddr = 0x1234, page_dir = [None, [None, None, 7]], offset_bits = 8, pt_bits = 4`
→ offset `0x34`, table index `2`, directory index `1`, frame 7 → `7*256 + 0x34 = 1844`.

**Constraints:** `0 ≤ vaddr < 2^48`, `1 ≤ offset_bits ≤ 16`, `1 ≤ pt_bits ≤ 12`.
""",
    starter='''def translate(vaddr, page_dir, offset_bits, pt_bits):
    pass
''',
    solution='''def translate(vaddr, page_dir, offset_bits, pt_bits):
    offset = vaddr & ((1 << offset_bits) - 1)
    t = (vaddr >> offset_bits) & ((1 << pt_bits) - 1)
    d = vaddr >> (offset_bits + pt_bits)
    if d >= len(page_dir) or page_dir[d] is None:
        return -1
    table = page_dir[d]
    if t >= len(table) or table[t] is None:
        return -1
    return (table[t] << offset_bits) | offset
''',
    tests=[
        [0x1234, [None, [None, None, 7]], 8, 4],
        [0x0000, [[0]], 12, 10],
        [0x00403004, [None, [None, None, None, 9]], 12, 10],
        [5, [], 4, 4],
        [0x1234, [None, None], 8, 4],
        [0x1234, [None, [None, None, None]], 8, 4],
        [0x1934, [None, [None, None, 7]], 8, 4],
        [0xFF, [[3, 0]], 4, 1],
        [0x1F, [[3, 0]], 4, 1],
        [0x2FFF, [[1, 2, 3, 4], None, [5, 6, 7, 8]], 12, 2],
        [0x8ABC, [[1, 2, 3, 4], None, [5, 6, 7, 8]], 12, 2],
        [0x7FFF, [[1, 2, 3, 4], [None, None, None, 0]], 12, 2],
        [(3 << 21) | (17 << 12) | 0xABC, [None, None, None, [None] * 17 + [1000000]], 12, 9],
    ],
    examples=2,
    wrong_solutions=[
        '''def translate(vaddr, page_dir, offset_bits, pt_bits):
    offset = vaddr & ((1 << offset_bits) - 1)
    t = (vaddr >> offset_bits) & ((1 << pt_bits) - 1)
    d = vaddr >> (offset_bits + pt_bits)
    if d >= len(page_dir) or not page_dir[d]:
        return -1
    table = page_dir[d]
    if t >= len(table) or not table[t]:
        return -1
    return (table[t] << offset_bits) | offset
''',
        '''def translate(vaddr, page_dir, offset_bits, pt_bits):
    offset = vaddr & ((1 << offset_bits) - 1)
    d = (vaddr >> offset_bits) & ((1 << pt_bits) - 1)
    t = vaddr >> (offset_bits + pt_bits)
    if d >= len(page_dir) or page_dir[d] is None:
        return -1
    table = page_dir[d]
    if t >= len(table) or table[t] is None:
        return -1
    return (table[t] << offset_bits) | offset
''',
    ],
    guide=dict(
        prereqs="Binary and hexadecimal, shifts and masks, the paging lesson (virtual page number, offset, frame number, multilevel tables).",
        intuition="Paging never changes the offset — it only swaps the page number for a frame number. A two-level table simply performs that swap in two hops, so that unused regions of the address space cost one `None` in the directory instead of a whole table.",
        hints=[
            "Peel fields off from the right: mask the low `offset_bits`, shift, mask the next `pt_bits`, shift; what remains is the directory index.",
            "Check each level for 'index out of range' and for `None` before descending.",
            "Frame number 0 is a perfectly valid frame. Test with `is None`, not truthiness.",
        ],
        brute_force="Convert the address to a binary string, pad it, and slice out the fields by character positions. It works, and is a reasonable way to check the bit-twiddling version, but it is slow and breaks easily on padding.",
        approach="""1. `offset = v & (2^o - 1)`; `t = (v >> o) & (2^p - 1)`; `d = v >> (o + p)`.
2. Fault if `d` is out of range or `page_dir[d] is None`; fault if `t` is out of range or the entry is `None`.
3. Answer `(frame << o) | offset`.

**Dry run** `0x1234`, o=8, p=4: offset `0x34`; `0x12 & 0xF = 2`; `0x12 >> 4 = 1`. `page_dir[1][2] = 7` → `0x734 = 1844`.""",
        complexity="O(1) time and space — which is the point: translation cost depends on the number of levels, not on the size of the address space.",
        pitfalls="Treating frame 0 as 'not present' (first wrong solution). Swapping the two index fields (second wrong solution). Adding instead of OR-ing is fine here, but multiplying the frame by the page *count* rather than the page *size* is a classic slip.",
        follow_up="x86-64 uses four levels of 9 bits each over a 12-bit offset (48-bit addresses), and five levels on newer CPUs. Generalise the function to a list of field widths.",
    ),
),
dict(
    id="os-tlb-simulation",
    title="TLB Hit/Miss Simulation",
    difficulty="Easy",
    pattern="Virtual Memory",
    entry="tlb_sim",
    description=r"""
A translation lookaside buffer caches recent page-number → frame translations. Simulate a fully
associative TLB with `tlb_size` entries and **LRU** replacement.

For each virtual address in `addresses`, its virtual page number is `address // page_size`. If the
page number is in the TLB it is a hit (and becomes the most recently used entry); otherwise it is a
miss and the page number is inserted, evicting the least recently used entry if the TLB is full.

Return `[hits, misses]`.

**Example:** `addresses = [0, 4, 4096, 8, 8192, 4100], page_size = 4096, tlb_size = 2` → `[2, 4]`
(page sequence `0 0 1 0 2 1`: miss, hit, miss, hit, miss — evicting page 1 — and then page 1 misses again, evicting page 0).

**Constraints:** `0 ≤ len(addresses) ≤ 10^5`, `page_size ≥ 1`, `0 ≤ tlb_size ≤ 4096`.
""",
    starter='''def tlb_sim(addresses, page_size, tlb_size):
    pass
''',
    solution='''from collections import OrderedDict

def tlb_sim(addresses, page_size, tlb_size):
    tlb = OrderedDict()
    hits = misses = 0
    for a in addresses:
        vpn = a // page_size
        if vpn in tlb:
            hits += 1
            tlb.move_to_end(vpn)
        else:
            misses += 1
            if tlb_size == 0:
                continue
            if len(tlb) == tlb_size:
                tlb.popitem(last=False)
            tlb[vpn] = True
    return [hits, misses]
''',
    tests=[
        [[0, 4, 4096, 8, 8192, 4100], 4096, 2],
        [[0, 1, 2, 3, 4, 5, 6, 7], 4, 1],
        [[], 4096, 8],
        [[100, 200, 300], 4096, 0],
        [[5], 1, 1],
        [[0, 4096, 0, 8192, 0, 4096], 4096, 2],
        [[0, 100, 200, 300, 400, 0, 100], 100, 3],
        [[4095, 4096, 4097, 8191, 8192], 4096, 4],
        [[10, 20, 10, 30, 10, 40, 20], 10, 2],
        [[i * 64 for i in range(1000)], 4096, 4],
        [[_r.randrange(1 << 20) for _ in range(5000)], 4096, 16],
        [[_r.randrange(1 << 24) for _ in range(20000)], 4096, 64],
    ],
    examples=2,
    wrong_solutions=[
        '''from collections import deque

def tlb_sim(addresses, page_size, tlb_size):
    tlb, order = set(), deque()
    hits = misses = 0
    for a in addresses:
        vpn = a // page_size
        if vpn in tlb:
            hits += 1
        else:
            misses += 1
            if tlb_size == 0:
                continue
            if len(tlb) == tlb_size:
                tlb.discard(order.popleft())
            tlb.add(vpn)
            order.append(vpn)
    return [hits, misses]
''',
        '''from collections import OrderedDict

def tlb_sim(addresses, page_size, tlb_size):
    tlb = OrderedDict()
    hits = misses = 0
    for a in addresses:
        vpn = a
        if vpn in tlb:
            hits += 1
            tlb.move_to_end(vpn)
        else:
            misses += 1
            if tlb_size == 0:
                continue
            if len(tlb) == tlb_size:
                tlb.popitem(last=False)
            tlb[vpn] = True
    return [hits, misses]
''',
    ],
    guide=dict(
        prereqs="LRU page-fault counting (same data structure), the role of the TLB in address translation.",
        intuition="The TLB does not care about bytes, only about pages: thousands of accesses inside one page are one entry. So first reduce each address to its page number, then run an ordinary LRU cache simulation.",
        hints=[
            "Compute `vpn = address // page_size` before anything else.",
            "An `OrderedDict` gives O(1) lookup, refresh (`move_to_end`) and eviction (`popitem(last=False)`).",
            "A zero-entry TLB can never hit; make sure you do not try to evict from an empty structure.",
        ],
        brute_force="Keep the entries in a list ordered by recency: on a hit remove and append; on a miss pop index 0 when full. O(tlb_size) per access — acceptable for 64 entries, but the OrderedDict is cleaner.",
        approach="""For each address: page number; hit → count and refresh; miss → count, evict oldest if full, insert.

**Dry run** pages `0 0 1 0 2 1`, 2 entries: miss(0); hit; miss(1) → {0,1}; hit(0) → order 1,0; miss(2) evicts 1 → {0,2}; miss(1) evicts 0. Result `[2, 4]`.""",
        complexity="O(n) time, O(tlb_size) space.",
        pitfalls="Caching raw addresses rather than page numbers (second wrong solution). Using FIFO eviction (first wrong solution). Dividing by the number of offset *bits* instead of the page size.",
        follow_up="Compute the effective access time: with hit ratio h, TLB lookup time e, and memory access time m, a one-level table costs `h(e+m) + (1-h)(e+2m)`.",
    ),
),
dict(
    id="os-first-fit",
    title="First-fit Memory Allocation",
    difficulty="Easy",
    pattern="Memory Allocation",
    entry="first_fit",
    description=r"""
Free memory is described by `holes`, the sizes of the free regions in address order. Requests arrive
one at a time. With **first fit**, each request is carved from the *first* hole (lowest index) that is
large enough; the hole shrinks by the request size (a hole of size 0 stays in the list and is simply useless).

Return a list giving, for each request, the index of the hole used, or `-1` if no hole can satisfy it.

**Example:** `holes = [100, 500, 200, 300, 600], requests = [212, 417, 112, 426]` → `[1, 4, 1, -1]`

**Constraints:** up to 2000 holes and 2000 requests, sizes are positive integers.
""",
    starter='''def first_fit(holes, requests):
    pass
''',
    solution='''def first_fit(holes, requests):
    free = list(holes)
    out = []
    for r in requests:
        for i, h in enumerate(free):
            if h >= r:
                free[i] -= r
                out.append(i)
                break
        else:
            out.append(-1)
    return out
''',
    tests=[
        [[100, 500, 200, 300, 600], [212, 417, 112, 426]],
        [[10, 20, 30], [30, 20, 10]],
        [[], [5]],
        [[50], []],
        [[8], [8, 1]],
        [[5, 5, 5], [6]],
        [[10, 10], [4, 4, 4, 4, 4]],
        [[300, 100, 200], [100, 100, 100, 100, 200]],
        [[7, 3, 9], [3, 7, 9, 1]],
        [[_r.randint(1, 500) for _ in range(40)], [_r.randint(1, 300) for _ in range(120)]],
        [[1000] * 500, [333] * 1600],
    ],
    examples=2,
    wrong_solutions=[
        '''def first_fit(holes, requests):
    free = list(holes)
    out = []
    for r in requests:
        best = -1
        for i, h in enumerate(free):
            if h >= r and (best == -1 or h < free[best]):
                best = i
        if best != -1:
            free[best] -= r
        out.append(best)
    return out
''',
        '''def first_fit(holes, requests):
    out = []
    for r in requests:
        for i, h in enumerate(holes):
            if h >= r:
                out.append(i)
                break
        else:
            out.append(-1)
    return out
''',
    ],
    guide=dict(
        prereqs="The memory lesson on free-list management (first fit, next fit, best fit, worst fit).",
        intuition="First fit is the laziest possible search: walk the free list from the start and stop at the first region that works. Its virtue is speed; its cost is a clutter of small leftovers near the front of memory.",
        hints=[
            "Copy the hole list so you can shrink holes without mutating the caller's data.",
            "Python's `for ... else` runs the `else` branch only when the loop did not `break` — ideal for 'nothing fitted'.",
            "A hole exactly equal to the request is usable; compare with `>=`.",
        ],
        brute_force="The direct double loop *is* the algorithm: O(holes) per request. There is nothing slower worth writing.",
        approach="""For each request scan holes left to right; at the first `free[i] >= r` subtract and record `i`; otherwise record `-1`.

**Dry run** holes `[100,500,200,300,600]`: 212 → hole 1 (288 left). 417 → holes 0–3 too small (100, 288, 200, 300), hole 4 fits (183 left). 112 → hole 1 (176 left). 426 → nothing ≥ 426 → -1.""",
        complexity="O(R · H) time, O(H) extra space.",
        pitfalls="Forgetting to shrink the hole (second wrong solution). Picking the tightest hole (that is best fit — first wrong solution). Note the last request fails although 100+176+200+300+183 = 959 bytes are free in total: that is **external fragmentation**.",
        follow_up="Implement *next fit*, which resumes the search where the previous one stopped, and compare how the holes end up distributed.",
    ),
),
dict(
    id="os-best-fit",
    title="Best-fit Memory Allocation",
    difficulty="Easy",
    pattern="Memory Allocation",
    entry="best_fit",
    description=r"""
Same model as first fit: `holes` are free-region sizes in address order and each request shrinks the
hole it is carved from. With **best fit** the allocator picks the **smallest hole that is still large
enough**; if several holes tie, it uses the one with the lowest index.

Return the list of hole indices used (or `-1` for requests that cannot be satisfied).

**Example:** `holes = [100, 500, 200, 300, 600], requests = [212, 417, 112, 426]` → `[3, 1, 2, 4]`

**Constraints:** up to 2000 holes and 2000 requests, positive sizes.
""",
    starter='''def best_fit(holes, requests):
    pass
''',
    solution='''def best_fit(holes, requests):
    free = list(holes)
    out = []
    for r in requests:
        best = -1
        for i, h in enumerate(free):
            if h >= r and (best == -1 or h < free[best]):
                best = i
        if best != -1:
            free[best] -= r
        out.append(best)
    return out
''',
    tests=[
        [[100, 500, 200, 300, 600], [212, 417, 112, 426]],
        [[10, 20, 30], [10, 10, 10]],
        [[], [1]],
        [[9], []],
        [[5, 5, 5], [5, 5, 5, 5]],
        [[50, 20, 20], [20, 20, 20]],
        [[8, 16, 8], [9, 8, 7, 1, 8]],
        [[300, 100, 200], [100, 100, 100, 100, 200]],
        [[4, 4], [5]],
        [[_r.randint(1, 500) for _ in range(40)], [_r.randint(1, 300) for _ in range(120)]],
        [[1000 + i for i in range(500)], [333] * 1500],
    ],
    examples=2,
    wrong_solutions=[
        '''def best_fit(holes, requests):
    free = list(holes)
    out = []
    for r in requests:
        for i, h in enumerate(free):
            if h >= r:
                free[i] -= r
                out.append(i)
                break
        else:
            out.append(-1)
    return out
''',
        '''def best_fit(holes, requests):
    free = list(holes)
    out = []
    for r in requests:
        best = -1
        for i, h in enumerate(free):
            if h >= r and (best == -1 or h <= free[best]):
                best = i
        if best != -1:
            free[best] -= r
        out.append(best)
    return out
''',
    ],
    guide=dict(
        prereqs="First-fit allocation (previous problem).",
        intuition="Best fit tries to preserve large holes for large future requests by always spending the tightest region. The side effect is a litter of tiny slivers too small for anyone, which is why it is not automatically better than first fit.",
        hints=[
            "You must look at every hole for each request — there is no early exit.",
            "Track the index of the best candidate so far; replace it only when the new hole is strictly smaller.",
            "Strict `<` (not `<=`) is what implements 'lowest index on ties'.",
        ],
        brute_force="Sort candidate holes by size for every request (O(H log H) each). A single linear scan for the minimum does the same in O(H).",
        approach="""For each request: scan all holes, remember the smallest one with `size >= r`, subtract, record.

**Dry run** `[100,500,200,300,600]`: 212 → candidates 500, 300, 600 → hole 3 (88 left). 417 → 500 or 600 → hole 1 (83 left). 112 → 200 or 600 → hole 2 (88 left). 426 → hole 4 (174 left). Every request succeeds here, where first fit failed the last one.""",
        complexity="O(R · H) time, O(H) space. A balanced tree keyed by size would give O(log H) per request.",
        pitfalls="Breaking at the first fit. Using `<=` and so preferring the *highest* index on ties. Assuming best fit always wastes less memory — simulations show it often leaves more unusable fragments than first fit.",
        follow_up="Try *worst fit* (always the largest hole) and count failed requests for the same random workload under all three policies.",
    ),
),
dict(
    id="os-buddy-allocator",
    title="Buddy System Allocator",
    difficulty="Hard",
    pattern="Memory Allocation",
    entry="buddy",
    description=r"""
Implement a **binary buddy allocator** managing `total` units of memory (`total` is a power of two).
The smallest block is 1 unit.

`ops` is a list of operations:

- `["alloc", size]` — round `size` up to the next power of two `b`. Find the smallest free block of
  size `≥ b` (lowest address among blocks of that size). Split it in halves repeatedly — always keeping
  the **lower** half and freeing the upper half — until it has size `b`. Return its start address, or
  `-1` if no free block is large enough.
- `["free", addr]` — release the allocated block that starts at `addr`. While the freed block's
  buddy (the other half of the block they were split from) is also completely free, merge the two.
  Return the size of the resulting free block. If `addr` is not the start of an allocated block, return `-1`.

Return the list of results.

**Example:** `total = 16, ops = [["alloc",3],["alloc",2],["free",0],["alloc",8],["free",4],["free",8]]`
→ `[0, 4, 4, 8, 8, 16]`

**Constraints:** `1 ≤ total ≤ 2^20`, `1 ≤ size`, up to 20,000 operations.
""",
    starter='''def buddy(total, ops):
    pass
''',
    solution='''def buddy(total, ops):
    free = {}
    size = 1
    while size <= total:
        free[size] = set()
        size *= 2
    free[total].add(0)
    used, out = {}, []
    for op, x in ops:
        if op == "alloc":
            need = 1
            while need < x:
                need *= 2
            size = need
            while size <= total and not free[size]:
                size *= 2
            if size > total:
                out.append(-1)
                continue
            addr = min(free[size])
            free[size].discard(addr)
            while size > need:
                size //= 2
                free[size].add(addr + size)
            used[addr] = need
            out.append(addr)
        else:
            if x not in used:
                out.append(-1)
                continue
            size, addr = used.pop(x), x
            while size < total and (addr ^ size) in free[size]:
                free[size].discard(addr ^ size)
                addr = min(addr, addr ^ size)
                size *= 2
            free[size].add(addr)
            out.append(size)
    return out
''',
    tests=[
        [16, [["alloc", 3], ["alloc", 2], ["free", 0], ["alloc", 8], ["free", 4], ["free", 8]]],
        [8, [["alloc", 8], ["alloc", 1], ["free", 0], ["alloc", 1]]],
        [1, [["alloc", 1], ["alloc", 1], ["free", 0], ["alloc", 1]]],
        [16, []],
        [16, [["free", 0], ["alloc", 17], ["alloc", 16], ["free", 4]]],
        [8, [["alloc", 1]] * 9],
        [8, [["alloc", 1], ["alloc", 1], ["alloc", 1], ["alloc", 1], ["free", 1], ["free", 2], ["free", 0], ["free", 3]]],
        [32, [["alloc", 5], ["alloc", 9], ["alloc", 5], ["free", 0], ["free", 8], ["free", 16]]],
        [16, [["alloc", 4], ["alloc", 4], ["alloc", 4], ["free", 4], ["alloc", 2], ["alloc", 2], ["alloc", 4], ["alloc", 1]]],
        [64, [["alloc", 20], ["alloc", 10], ["free", 0], ["alloc", 16], ["alloc", 16], ["free", 32], ["alloc", 1], ["free", 32]]],
        [16, [["alloc", 2], ["alloc", 2], ["free", 0], ["free", 0], ["free", 2]]],
        [1024, [["alloc", _r.randint(1, 60)] for _ in range(60)] + [["free", a] for a in range(0, 1024, 8)] + [["alloc", 1024]]],
        [1 << 16, [["alloc", 1]] * 3000 + [["free", a] for a in range(2999, -1, -1)] + [["alloc", 1 << 16]]],
    ],
    examples=1,
    wrong_solutions=[
        '''def buddy(total, ops):
    free = {}
    size = 1
    while size <= total:
        free[size] = set()
        size *= 2
    free[total].add(0)
    used, out = {}, []
    for op, x in ops:
        if op == "alloc":
            need = 1
            while need < x:
                need *= 2
            size = need
            while size <= total and not free[size]:
                size *= 2
            if size > total:
                out.append(-1)
                continue
            addr = min(free[size])
            free[size].discard(addr)
            while size > need:
                size //= 2
                free[size].add(addr + size)
            used[addr] = need
            out.append(addr)
        else:
            if x not in used:
                out.append(-1)
                continue
            size = used.pop(x)
            free[size].add(x)
            out.append(size)
    return out
''',
        '''def buddy(total, ops):
    free = {}
    size = 1
    while size <= total:
        free[size] = set()
        size *= 2
    free[total].add(0)
    used, out = {}, []
    for op, x in ops:
        if op == "alloc":
            need = 1
            while need < x:
                need *= 2
            size = need
            while size <= total and not free[size]:
                size *= 2
            if size > total:
                out.append(-1)
                continue
            addr = min(free[size])
            free[size].discard(addr)
            while size > need:
                size //= 2
                free[size].add(addr + size)
            used[addr] = need
            out.append(addr)
        else:
            if x not in used:
                out.append(-1)
                continue
            size, addr = used.pop(x), x
            while size < total and (addr + size) in free[size]:
                free[size].discard(addr + size)
                size *= 2
            free[size].add(addr)
            out.append(size)
    return out
''',
    ],
    guide=dict(
        prereqs="Powers of two and XOR, free lists, internal vs external fragmentation. The Linux case-study lesson describes where the kernel uses this allocator.",
        intuition="Restricting block sizes to powers of two makes two hard things trivial. Splitting is halving. And the partner a block may merge with is fixed by arithmetic: for a block of size `s` at address `a`, the buddy lives at `a XOR s`. No searching of neighbours is ever needed.",
        hints=[
            "Keep one set of free addresses per block size (`free[1]`, `free[2]`, `free[4]`, …) and a dict `used[addr] = size`.",
            "Allocation: round up, climb to the first size with a free block, take the lowest address, then split down, adding each upper half to its free set.",
            "Freeing: loop while `addr ^ size` is in `free[size]` — remove the buddy, keep the lower address, double the size.",
        ],
        brute_force="Model memory as an array of `total` cells and search for aligned free runs on each allocation, re-scanning to merge on free. O(total) per operation and the alignment rules are easy to violate.",
        approach="""**Dry run**, total 16. `alloc 3` → need 4; only a 16 is free → split into 8+8 (upper 8 at address 8 freed), then 4+4 (address 4 freed) → return 0. `alloc 2` → need 2; smallest free block ≥ 2 is the 4 at address 4 → split, free `[6,8)`, return 4. `free 0` → size 4, buddy `0^4 = 4` is not in `free[4]` (it was split) → stays 4. `alloc 8` → block at 8. `free 4` → size 2, buddy 6 is free → merge to (4, size 4); buddy `4^4 = 0` is free → merge to (0, size 8); buddy 8 is allocated → stop, return 8. `free 8` → merges with 0 → 16.""",
        complexity="Each operation walks at most log₂(total) levels. Finding the lowest address with `min` on a set is linear in that set; use a heap or sorted structure per level for strict O(log) bounds.",
        pitfalls="Computing the buddy as `addr + size` (second wrong solution) — only right for the lower half. Never coalescing (first wrong solution), which fragments memory permanently. Merging with a buddy that is only *partly* free: checking membership in `free[size]` at the same size is what prevents that.",
        follow_up="Measure internal fragmentation: a request for 33 units consumes 64. Slab allocators sit on top of the buddy system to serve small fixed-size objects without that waste.",
    ),
),
]
