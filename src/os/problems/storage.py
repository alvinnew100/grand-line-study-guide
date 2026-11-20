import random as _random

_r = _random.Random(53)


def _reqs(n, top=199):
    return [_r.randint(0, top) for _ in range(n)]


def _stripe(disks, size, missing):
    data = [[_r.randrange(256) for _ in range(size)] for _ in range(disks - 1)]
    parity = [0] * size
    for blk in data:
        parity = [a ^ b for a, b in zip(parity, blk)]
    stripe = data + [parity]
    if missing is not None:
        stripe[missing] = None
    return stripe


_CLASSIC_Q = [98, 183, 37, 122, 14, 124, 65, 67]

PROBLEMS = [
dict(
    id="os-disk-fcfs",
    title="Disk Scheduling: FCFS Head Movement",
    difficulty="Easy",
    pattern="Disk Scheduling",
    entry="disk_fcfs",
    description=r"""
A disk arm starts at cylinder `head`. Pending requests are served strictly in the order given.
Return the total number of cylinders the arm travels.

**Example:** `head = 53, requests = [98, 183, 37, 122, 14, 124, 65, 67]` → `640`

**Constraints:** `0 ≤ len(requests) ≤ 10^5`, cylinders are non-negative integers.
""",
    starter='''def disk_fcfs(head, requests):
    pass
''',
    solution='''def disk_fcfs(head, requests):
    total = 0
    for c in requests:
        total += abs(c - head)
        head = c
    return total
''',
    tests=[
        [53, _CLASSIC_Q],
        [0, [10, 5, 20]],
        [50, []],
        [50, [50]],
        [10, [10, 10, 10]],
        [100, [0, 200, 0, 200]],
        [7, [3]],
        [0, [1, 2, 3, 4, 5]],
        [199, [0]],
        [100, _reqs(50)],
        [0, _reqs(50000, 10**6)],
    ],
    examples=2,
    wrong_solutions=[
        '''def disk_fcfs(head, requests):
    return sum(abs(c - head) for c in requests)
''',
        '''def disk_fcfs(head, requests):
    if not requests:
        return 0
    return max(max(requests), head) - min(min(requests), head)
''',
    ],
    guide=dict(
        prereqs="The disk lesson: cylinders, seek time, why arm movement dominates on rotating disks.",
        intuition="Seek distance is just the absolute difference between consecutive positions. FCFS does no reordering, so the answer is the length of the path head → r₀ → r₁ → …",
        hints=[
            "Walk the list keeping the current arm position.",
            "Add `abs(next - current)` and then move.",
            "The empty list costs nothing.",
        ],
        brute_force="Move the arm one cylinder at a time towards each target, counting steps. O(total distance) instead of O(n).",
        approach="""Accumulate absolute differences.

**Dry run** head 53: 53→98 (45), →183 (85), →37 (146), →122 (85), →14 (108), →124 (110), →65 (59), →67 (2). Sum 640.""",
        complexity="O(n) time, O(1) space.",
        pitfalls="Measuring every request from the *original* head position (first wrong solution). Assuming the answer is the span between the extremes (second wrong solution) — that is only a lower bound.",
        follow_up="Use this as the baseline when you implement SSTF, SCAN, C-SCAN and LOOK in the next problems.",
    ),
),
dict(
    id="os-disk-sstf",
    title="Disk Scheduling: Shortest Seek Time First",
    difficulty="Medium",
    pattern="Disk Scheduling",
    entry="disk_sstf",
    description=r"""
With **SSTF**, the arm always serves the pending request closest to its current position. When two
pending requests are equally close, serve the one on the **lower-numbered** cylinder.

Return the total head movement, starting from cylinder `head`.

**Example:** `head = 53, requests = [98, 183, 37, 122, 14, 124, 65, 67]` → `236`
(order 65, 67, 37, 14, 98, 122, 124, 183).

**Constraints:** `0 ≤ len(requests) ≤ 2·10^4`; duplicates allowed.
""",
    starter='''def disk_sstf(head, requests):
    pass
''',
    solution='''import bisect

def disk_sstf(head, requests):
    pending = sorted(requests)
    total = 0
    while pending:
        i = bisect.bisect_left(pending, head)
        if i == 0:
            j = 0
        elif i == len(pending):
            j = i - 1
        else:
            j = i - 1 if head - pending[i - 1] <= pending[i] - head else i
        total += abs(pending[j] - head)
        head = pending.pop(j)
    return total
''',
    tests=[
        [53, _CLASSIC_Q],
        [50, [40, 60]],
        [50, []],
        [50, [50, 50]],
        [0, [5, 1, 9]],
        [100, [90, 110, 80, 130]],
        [10, [12, 8, 14, 6, 16]],
        [100, [99, 102, 97, 200]],
        [5, [0, 10, 11]],
        [199, [0, 100, 198]],
        [100, _reqs(60)],
        [5000, _reqs(8000, 10000)],
    ],
    examples=2,
    wrong_solutions=[
        '''def disk_sstf(head, requests):
    total = 0
    for c in sorted(requests, key=lambda c: abs(c - head)):
        total += abs(c - head)
        head = c
    return total
''',
        '''import bisect

def disk_sstf(head, requests):
    pending = sorted(requests)
    total = 0
    while pending:
        i = bisect.bisect_left(pending, head)
        if i == 0:
            j = 0
        elif i == len(pending):
            j = i - 1
        else:
            j = i - 1 if head - pending[i - 1] < pending[i] - head else i
        total += abs(pending[j] - head)
        head = pending.pop(j)
    return total
''',
    ],
    guide=dict(
        prereqs="FCFS disk scheduling, binary search (`bisect`), greedy algorithms.",
        intuition="SSTF is 'shortest job first' for the disk arm: do the cheapest thing next. In a sorted list of pending cylinders the nearest one is always an immediate neighbour of the head position, so you never need to look further than two candidates.",
        hints=[
            "The nearest request must be re-evaluated after every move — sorting once by distance from the *initial* head is wrong.",
            "Sort the cylinders. `bisect_left` gives the insertion point; the candidates are the elements just left and just right of it.",
            "Use `<=` when comparing left distance to right distance so that ties go to the lower cylinder.",
        ],
        brute_force="Each round, scan all pending requests for the minimum `(distance, cylinder)` and remove it: O(n²). Easy to trust; use it to validate the bisect version.",
        approach="""**Dry run** head 53, sorted `[14,37,65,67,98,122,124,183]`: neighbours 37 (16 away) and 65 (12) → 65. Then 37 (28) vs 67 (2) → 67. Then 37 (30) vs 98 (31) → 37. Then 14, then 98, 122, 124, 183. Movement 12+2+30+23+84+24+2+59 = 236.""",
        complexity="O(n log n) for sorting plus n binary searches; `list.pop` in the middle is O(n), so O(n²) worst case in pure Python — a balanced tree or two-pointer expansion gives true O(n log n).",
        pitfalls="Sorting once by initial distance (first wrong solution). Breaking ties upward (second wrong solution). Forgetting that SSTF can **starve** far-away requests when new ones keep arriving near the arm.",
        follow_up="Because the pending set is static here, the arm's visited range only ever grows outward: implement it with two pointers expanding from the head position and no deletions.",
    ),
),
dict(
    id="os-disk-scan",
    title="Disk Scheduling: SCAN (Elevator to the Edge)",
    difficulty="Medium",
    pattern="Disk Scheduling",
    entry="disk_scan",
    description=r"""
In this version of **SCAN** the arm sweeps in its current direction serving every request it passes.

- If no pending request lies on the other side of the starting position, the arm stops at the last request in its direction.
- Otherwise it continues **all the way to the edge** of the disk (cylinder `max_cyl` when moving `"up"`,
  cylinder `0` when moving `"down"`), reverses, and serves the remaining requests, stopping at the last one.

Requests on the starting cylinder cost nothing. Return the total head movement.

**Example:** `head = 53, requests = [98, 183, 37, 122, 14, 124, 65, 67], max_cyl = 199, direction = "down"`
→ `236` (53 → 0 is 53 cylinders, then 0 → 183 is 183).

**Constraints:** `0 ≤ head, requests[i] ≤ max_cyl`, `len(requests) ≤ 10^5`.
""",
    starter='''def disk_scan(head, requests, max_cyl, direction):
    pass
''',
    solution='''def disk_scan(head, requests, max_cyl, direction):
    below = [c for c in requests if c < head]
    above = [c for c in requests if c > head]
    if direction == "up":
        if not below:
            return max(above) - head if above else 0
        return (max_cyl - head) + (max_cyl - min(below))
    if not above:
        return head - min(below) if below else 0
    return head + max(above)
''',
    tests=[
        [53, _CLASSIC_Q, 199, "down"],
        [53, _CLASSIC_Q, 199, "up"],
        [50, [], 199, "up"],
        [50, [50, 50], 199, "down"],
        [50, [60, 70], 199, "up"],
        [50, [60, 70], 199, "down"],
        [50, [10, 20], 199, "down"],
        [50, [10, 20], 199, "up"],
        [0, [5, 9], 9, "down"],
        [9, [0, 4], 9, "up"],
        [100, [100, 150, 199], 199, "up"],
        [100, _reqs(80), 199, "up"],
        [100, _reqs(80), 199, "down"],
        [5000, _reqs(50000, 9999), 9999, "up"],
    ],
    examples=2,
    wrong_solutions=[
        '''def disk_scan(head, requests, max_cyl, direction):
    below = [c for c in requests if c < head]
    above = [c for c in requests if c > head]
    if direction == "up":
        if not below:
            return max(above) - head if above else 0
        if not above:
            return head - min(below)
        return (max(above) - head) + (max(above) - min(below))
    if not above:
        return head - min(below) if below else 0
    if not below:
        return max(above) - head
    return (head - min(below)) + (max(above) - min(below))
''',
        '''def disk_scan(head, requests, max_cyl, direction):
    if not requests:
        return 0
    if direction == "up":
        return (max_cyl - head) + (max_cyl - min(requests))
    return head + max(requests)
''',
    ],
    guide=dict(
        prereqs="FCFS and SSTF disk scheduling. The lift analogy from the disk lesson.",
        intuition="A sweep visits every cylinder between its endpoints, so you never need to simulate individual requests: the total is determined by where the arm turns round and where it finally stops. Only three numbers matter — the head, the edge, and the farthest request on the far side.",
        hints=[
            "Split the requests into those below the head and those above it; requests *at* the head are free.",
            "Moving up with nothing below: the arm just goes to the highest request.",
            "Moving up with something below: it travels `max_cyl - head` to the edge, then `max_cyl - min(below)` back down.",
        ],
        brute_force="Sort the requests, build the explicit visiting order (upward part, edge, downward part) and sum absolute differences as in FCFS. O(n log n) and a good cross-check for the closed form.",
        approach="""**Dry run** head 53 moving down, queue `98 183 37 122 14 124 65 67`, max 199: above = {98,183,122,124,65,67} is non-empty, so the arm goes to cylinder 0 (53) and then up to the largest request 183 (183). Total 236.
Moving up instead: `(199 − 53) + (199 − 14) = 146 + 185 = 331`.""",
        complexity="O(n) time (one pass for min/max), O(n) or O(1) space depending on whether you build the two lists.",
        pitfalls="Reversing at the last request instead of the edge — that is LOOK (first wrong solution). Going to the edge even when nothing is waiting behind (second wrong solution; the statement says the arm stops). Counting requests at the head position as movement.",
        follow_up="SCAN favours the middle cylinders, which are passed twice per round trip. C-SCAN (next problem) evens out the waiting time.",
    ),
),
dict(
    id="os-disk-cscan",
    title="Disk Scheduling: C-SCAN",
    difficulty="Medium",
    pattern="Disk Scheduling",
    entry="disk_cscan",
    description=r"""
**Circular SCAN** serves requests only while moving **upwards**.

- Starting at `head`, the arm moves up serving every request at or above its position.
- If requests below the starting position remain, the arm continues to the top edge `max_cyl`,
  flies back to cylinder `0` without serving anything (that return trip **counts** as `max_cyl` cylinders
  of movement), and then moves up again to the largest of the remaining requests.
- If nothing lies below the starting position, the arm simply stops at the highest request.

Return the total head movement.

**Example:** `head = 53, requests = [98, 183, 37, 122, 14, 124, 65, 67], max_cyl = 199` → `382`
(146 up to the edge, 199 for the return, 37 up to the last request).

**Constraints:** `0 ≤ head, requests[i] ≤ max_cyl`, `len(requests) ≤ 10^5`.
""",
    starter='''def disk_cscan(head, requests, max_cyl):
    pass
''',
    solution='''def disk_cscan(head, requests, max_cyl):
    below = [c for c in requests if c < head]
    above = [c for c in requests if c > head]
    if not below:
        return max(above) - head if above else 0
    return (max_cyl - head) + max_cyl + max(below)
''',
    tests=[
        [53, _CLASSIC_Q, 199],
        [50, [60, 70], 199],
        [50, [], 199],
        [50, [50], 199],
        [50, [10, 20], 199],
        [0, [5, 9], 9],
        [9, [0, 4], 9],
        [199, [0], 199],
        [100, [99], 199],
        [10, [0, 0, 5, 10], 20],
        [100, _reqs(80), 199],
        [5000, _reqs(50000, 9999), 9999],
    ],
    examples=2,
    wrong_solutions=[
        '''def disk_cscan(head, requests, max_cyl):
    below = [c for c in requests if c < head]
    above = [c for c in requests if c > head]
    if not below:
        return max(above) - head if above else 0
    return (max_cyl - head) + (max_cyl - min(below))
''',
        '''def disk_cscan(head, requests, max_cyl):
    below = [c for c in requests if c < head]
    above = [c for c in requests if c > head]
    if not below:
        return max(above) - head if above else 0
    return (max_cyl - head) + max(below)
''',
    ],
    guide=dict(
        prereqs="SCAN disk scheduling (previous problem).",
        intuition="Treat the cylinders as a ring: after the top edge comes cylinder 0. The arm keeps travelling the same way round the ring, so a request never waits for more than one full lap — unlike SCAN, where a request just behind the arm waits for almost two sweeps.",
        hints=[
            "Again only the extremes matter: split into below and above the head.",
            "If nothing is below, there is no wrap-around at all.",
            "With a wrap: up to the edge, the full-width return, then up to the **largest** of the below-requests (it is served last on the second pass).",
        ],
        brute_force="Sort, build the visiting order `above ascending → max_cyl → 0 → below ascending` and add up the absolute differences.",
        approach="""**Dry run** head 53, max 199: below = {37, 14}. Up to the edge: 199 − 53 = 146. Return: 199. Up to max(below) = 37. Total 382.""",
        complexity="O(n) time.",
        pitfalls="Using `min(below)` as in SCAN's formula (first wrong solution) — on the second pass the arm moves upward, so it ends at the *largest* low request. Forgetting to count the return seek (second wrong solution); some textbooks exclude it, so always check the convention you are asked for.",
        follow_up="C-LOOK jumps from the highest request straight to the lowest one instead of visiting both edges. Write its closed form.",
    ),
),
dict(
    id="os-disk-look",
    title="Disk Scheduling: LOOK Service Order",
    difficulty="Medium",
    pattern="Disk Scheduling",
    entry="disk_look",
    description=r"""
**LOOK** is the elevator algorithm that reverses at the last request rather than at the disk edge.

Starting at cylinder `head` and moving in `direction` (`"up"` or `"down"`):

1. requests located exactly at `head` are served first;
2. then every request ahead of the arm, in the order the arm reaches them;
3. then the arm reverses and serves the rest.

Duplicate requests are all served when the arm reaches that cylinder. Return the order in which the
cylinders are served (a list with the same length as `requests`).

**Example:** `head = 53, requests = [98, 183, 37, 122, 14, 124, 65, 67], direction = "up"`
→ `[65, 67, 98, 122, 124, 183, 37, 14]`

**Constraints:** `len(requests) ≤ 10^5`.
""",
    starter='''def disk_look(head, requests, direction):
    pass
''',
    solution='''def disk_look(head, requests, direction):
    here = [c for c in requests if c == head]
    up = sorted(c for c in requests if c > head)
    down = sorted((c for c in requests if c < head), reverse=True)
    return here + (up + down if direction == "up" else down + up)
''',
    tests=[
        [53, _CLASSIC_Q, "up"],
        [53, _CLASSIC_Q, "down"],
        [10, [], "up"],
        [10, [10], "down"],
        [10, [12, 10, 8, 10], "up"],
        [0, [3, 1, 2], "down"],
        [9, [3, 1, 2], "up"],
        [5, [7, 7, 3, 3, 9], "down"],
        [5, [7, 7, 3, 3, 9], "up"],
        [100, [100, 99, 101], "down"],
        [100, _reqs(80), "up"],
        [5000, _reqs(12000, 9999), "down"],
    ],
    examples=2,
    wrong_solutions=[
        '''def disk_look(head, requests, direction):
    here = [c for c in requests if c == head]
    up = sorted(c for c in requests if c > head)
    down = sorted(c for c in requests if c < head)
    return here + (up + down if direction == "up" else down + up)
''',
        '''def disk_look(head, requests, direction):
    return sorted(requests, key=lambda c: (abs(c - head), c))
''',
    ],
    guide=dict(
        prereqs="SCAN and C-SCAN, sorting with `reverse=True`.",
        intuition="An elevator serves floors in one direction in increasing distance, then turns round and does the same the other way. So the answer is two sorted runs glued together: ascending for the upward leg, descending for the downward leg.",
        hints=[
            "Partition the requests into three groups: at the head, above, below.",
            "Above must be ascending; below must be **descending** — in both directions of travel that is the order the arm meets them.",
            "Concatenate according to the starting direction.",
        ],
        brute_force="Simulate the arm cylinder by cylinder, emitting requests as it passes them and reversing when nothing remains ahead. O(range of cylinders) rather than O(n log n).",
        approach="""**Dry run** head 53, up: above sorted `[65,67,98,122,124,183]`; below descending `[37,14]`. Order: 65, 67, 98, 122, 124, 183, 37, 14. Movement would be (183−53) + (183−14) = 299, versus 331 for SCAN to the edge.""",
        complexity="O(n log n) time for the two sorts, O(n) space.",
        pitfalls="Leaving the lower group ascending (first wrong solution) — the arm would have to jump to the far end first, which is C-LOOK, not LOOK. Ordering by distance from the start (second wrong solution) is a zig-zag no real arm would perform.",
        follow_up="Compute the total movement from the order and compare LOOK, SCAN, C-SCAN, SSTF and FCFS on the same queue. On SSDs none of this matters: there is no arm, so Linux uses a no-op style scheduler.",
    ),
),
dict(
    id="os-inode-max-file-size",
    title="Maximum File Size of an Inode",
    difficulty="Easy",
    pattern="File Systems",
    entry="max_file_size",
    description=r"""
A UNIX-style inode contains `direct` direct block pointers, plus `single` single-indirect, `double`
double-indirect and `triple` triple-indirect pointers. Blocks are `block_size` bytes and a block
pointer occupies `ptr_size` bytes, so one indirect block holds `block_size // ptr_size` pointers.

Return the largest file size in **bytes** that the pointer structure can address.

**Example:** `block_size = 1024, ptr_size = 4, direct = 10, single = 1, double = 1, triple = 0`
→ pointers per block = 256 → `(10 + 256 + 256²) × 1024 = 67,383,296`

**Constraints:** `block_size` and `ptr_size` are powers of two with `ptr_size ≤ block_size`; counts are `≥ 0`.
""",
    starter='''def max_file_size(block_size, ptr_size, direct, single, double, triple):
    pass
''',
    solution='''def max_file_size(block_size, ptr_size, direct, single, double, triple):
    n = block_size // ptr_size
    blocks = direct + single * n + double * n ** 2 + triple * n ** 3
    return blocks * block_size
''',
    tests=[
        [1024, 4, 10, 1, 1, 0],
        [4096, 4, 12, 1, 1, 1],
        [512, 2, 0, 0, 0, 0],
        [512, 4, 7, 0, 0, 0],
        [4096, 8, 12, 1, 1, 1],
        [1024, 4, 0, 1, 0, 0],
        [1024, 4, 0, 0, 0, 1],
        [8, 8, 3, 2, 2, 2],
        [2048, 4, 12, 2, 0, 1],
        [8192, 8, 10, 1, 2, 0],
        [65536, 8, 12, 1, 1, 1],
    ],
    examples=2,
    wrong_solutions=[
        '''def max_file_size(block_size, ptr_size, direct, single, double, triple):
    n = block_size // ptr_size
    return (direct + single * n + double * n * 2 + triple * n * 3) * block_size
''',
        '''def max_file_size(block_size, ptr_size, direct, single, double, triple):
    n = block_size
    return (direct + single * n + double * n ** 2 + triple * n ** 3) * block_size
''',
        '''def max_file_size(block_size, ptr_size, direct, single, double, triple):
    n = block_size // ptr_size
    return direct + single * n + double * n ** 2 + triple * n ** 3
''',
    ],
    guide=dict(
        prereqs="The file-system implementation lesson: inodes, direct and indirect blocks.",
        intuition="Count data blocks, then multiply by the block size. Each level of indirection multiplies reach by the fan-out `n = block_size / ptr_size`: a single-indirect pointer reaches `n` blocks, a double `n²`, a triple `n³`.",
        hints=[
            "First compute how many pointers fit in one block.",
            "A double-indirect pointer leads to a block of `n` pointers, each leading to a block of `n` data pointers.",
            "Sum the reachable data blocks over all pointer kinds and convert to bytes at the very end.",
        ],
        brute_force="Recursively 'walk' the tree and count leaves. Pointless for a triple-indirect tree with a billion leaves; the closed form is the only sensible approach.",
        approach="""`blocks = direct + single·n + double·n² + triple·n³`, answer `blocks × block_size`.

**Dry run** 4 KB blocks, 4-byte pointers: n = 1024. Blocks = 12 + 1024 + 1,048,576 + 1,073,741,824 = 1,074,791,436 → about 4.4 × 10¹² bytes (≈ 4 TiB).""",
        complexity="O(1).",
        pitfalls="Multiplying by the level number instead of raising to a power (first wrong solution). Using the block size as the fan-out (second). Returning blocks instead of bytes (third). In real systems the limit may be lower still because the file-size field or the block-pointer width (e.g. 32 bits) caps it first.",
        follow_up="How many disk reads are needed to fetch byte 5,000,000 of a file if only the inode is cached? See the next problem.",
    ),
),
dict(
    id="os-inode-block-lookup",
    title="Inode Block Lookup Path",
    difficulty="Medium",
    pattern="File Systems",
    entry="block_path",
    description=r"""
An inode has `direct` direct pointers followed by one single-indirect, one double-indirect and one
triple-indirect pointer. Every indirect block holds `n` pointers.

Given a file's **logical block number** `block_no` (0-based), return the path used to find it:

- `[0, i]` — direct pointer `i`
- `[1, i]` — entry `i` of the single-indirect block
- `[2, i, j]` — entry `i` of the double-indirect block, then entry `j` of that block
- `[3, i, j, k]` — the analogous three indices under the triple-indirect pointer
- `[]` — the block number is beyond what the inode can address

**Example:** `block_no = 300, direct = 12, n = 256` → `[2, 0, 32]`
(blocks 0–11 are direct, 12–267 single-indirect; 300 − 268 = 32 → first second-level block, slot 32).

**Constraints:** `0 ≤ block_no < 2^62`, `0 ≤ direct ≤ 64`, `1 ≤ n ≤ 2^16`.
""",
    starter='''def block_path(block_no, direct, n):
    pass
''',
    solution='''def block_path(block_no, direct, n):
    if block_no < direct:
        return [0, block_no]
    b = block_no - direct
    if b < n:
        return [1, b]
    b -= n
    if b < n * n:
        return [2, b // n, b % n]
    b -= n * n
    if b < n ** 3:
        return [3, b // (n * n), (b // n) % n, b % n]
    return []
''',
    tests=[
        [300, 12, 256],
        [5, 12, 256],
        [0, 12, 1024],
        [11, 12, 1024],
        [12, 12, 1024],
        [1035, 12, 1024],
        [1036, 12, 1024],
        [12 + 1024 + 1024 * 1024 - 1, 12, 1024],
        [12 + 1024 + 1024 * 1024, 12, 1024],
        [12 + 1024 + 1024 ** 2 + 1024 ** 3 - 1, 12, 1024],
        [12 + 1024 + 1024 ** 2 + 1024 ** 3, 12, 1024],
        [0, 0, 2],
        [13, 0, 2],
        [14, 0, 2],
        [10, 3, 1],
        [123456789, 10, 300],
    ],
    examples=2,
    wrong_solutions=[
        '''def block_path(block_no, direct, n):
    if block_no < direct:
        return [0, block_no]
    b = block_no
    if b < n:
        return [1, b]
    if b < n * n:
        return [2, b // n, b % n]
    if b < n ** 3:
        return [3, b // (n * n), (b // n) % n, b % n]
    return []
''',
        '''def block_path(block_no, direct, n):
    if block_no <= direct:
        return [0, block_no]
    b = block_no - direct
    if b <= n:
        return [1, b]
    b -= n
    if b <= n * n:
        return [2, b // n, b % n]
    b -= n * n
    if b <= n ** 3:
        return [3, b // (n * n), (b // n) % n, b % n]
    return []
''',
    ],
    guide=dict(
        prereqs="Inode structure (previous problem), integer division and remainder as 'digit extraction'.",
        intuition="The inode lays its regions end to end: direct, then single, double, triple. Subtract the sizes of the regions you skip; what is left is an index *inside* the region, and writing that index in base `n` gives the slot to follow at each level.",
        hints=[
            "Handle the regions in order, subtracting each region's capacity before testing the next.",
            "Inside the double-indirect region the remaining index `b` splits as `(b // n, b % n)`.",
            "Inside the triple region the three digits are `b // n²`, `(b // n) % n`, `b % n`.",
        ],
        brute_force="Enumerate logical blocks from 0, advancing a multi-level odometer until you reach `block_no`. O(block_no) — unusable for a block number near 10⁹.",
        approach="""**Dry run** `block_no = 1036`, 12 direct, n = 1024: not direct; b = 1024; not `< 1024`, so subtract → b = 0 → `[2, 0, 0]`, the very first block reached through the double-indirect pointer.

For `[3, i, j, k]` each lookup costs four block reads beyond the inode: three pointer blocks plus the data block.""",
        complexity="O(1) time and space.",
        pitfalls="Not subtracting earlier regions (first wrong solution). Off-by-one boundaries with `<=` (second wrong solution) — the block at index `direct` is the first single-indirect one. Forgetting the 'too large' case.",
        follow_up="Extent-based file systems (ext4, NTFS, XFS) replace this pointer tree with (start, length) runs. What does the lookup become?",
    ),
),
dict(
    id="os-fat-chain",
    title="Follow a FAT Chain",
    difficulty="Easy",
    pattern="File Systems",
    entry="fat_chain",
    description=r"""
In a FAT file system the table `fat` has one entry per disk block: `fat[b]` is the number of the next
block of the same file, or `-1` if `b` is the file's last block.

Given the table and a file's first block `start` (or `-1` for an empty file), return the list of the
file's blocks in order.

A damaged table may contain an entry pointing outside the table or a chain that loops back on itself.
In either case return `None`.

**Example:** `fat = [-1, -1, 10, 11, 7, -1, 3, 2, -1, -1, 12, 14, -1, -1, -1], start = 4`
→ `[4, 7, 2, 10, 12]`

**Constraints:** `len(fat) ≤ 10^6`.
""",
    starter='''def fat_chain(fat, start):
    pass
''',
    solution='''def fat_chain(fat, start):
    chain, seen = [], set()
    b = start
    while b != -1:
        if b < 0 or b >= len(fat) or b in seen:
            return None
        seen.add(b)
        chain.append(b)
        b = fat[b]
    return chain
''',
    tests=[
        [[-1, -1, 10, 11, 7, -1, 3, 2, -1, -1, 12, 14, -1, -1, -1], 4],
        [[-1, -1, 10, 11, 7, -1, 3, 2, -1, -1, 12, 14, -1, -1, -1], 6],
        [[1, 2, -1], -1],
        [[-1], 0],
        [[], -1],
        [[], 0],
        [[1, 0], 0],
        [[0], 0],
        [[1, 2, 5], 0],
        [[1, -7, -1], 0],
        [[2, -1, 1], 0],
        [[3, -1, 1, 2, 4], 4],
        [list(range(1, 15000)) + [-1], 0],
        [list(range(1, 15000)) + [7000], 5],
    ],
    examples=2,
    wrong_solutions=[
        '''def fat_chain(fat, start):
    chain = []
    b = start
    while b != -1 and len(chain) <= len(fat):
        if b < 0 or b >= len(fat):
            return None
        chain.append(b)
        b = fat[b]
    return chain
''',
        '''def fat_chain(fat, start):
    chain, seen = [], set()
    b = start
    while b != -1:
        if b in seen:
            return None
        seen.add(b)
        chain.append(b)
        b = fat[b % len(fat)] if fat else -1
    return chain
''',
    ],
    guide=dict(
        prereqs="Linked-list allocation with an in-memory table (file-system implementation lesson).",
        intuition="The FAT is a linked list whose 'next' pointers have been pulled out of the data blocks into one array. Reading a file's block list is therefore a pointer chase through that array — plus the paranoia any on-disk structure deserves.",
        hints=[
            "Loop: append the current block, then jump to `fat[current]`, until you read `-1`.",
            "Before using a block number as an index, check it is within `0 .. len(fat) - 1`.",
            "A loop in the chain would run forever; remember visited blocks in a set.",
        ],
        brute_force="Detect loops by comparing against every block already in the list (`b in chain`): O(length²). A set makes it O(length).",
        approach="""**Dry run** start 4: `fat[4] = 7`, `fat[7] = 2`, `fat[2] = 10`, `fat[10] = 12`, `fat[12] = -1` → `[4,7,2,10,12]`.
Corrupt case `fat = [1, 0]`, start 0: visit 0, then 1, then 0 again → already seen → `None`.""",
        complexity="O(length of chain) time and space.",
        pitfalls="No cycle check (infinite loop) or a check that silently returns a truncated list instead of signalling corruption (first wrong solution). Wrapping bad indices instead of rejecting them (second). Treating `start = -1` as an error — it is a legitimate empty file.",
        follow_up="Random access to block k of a file costs k steps in the chain, but all in RAM. The price is the table itself: one entry per disk block must stay in memory, which is why FAT does not scale to huge volumes.",
    ),
),
dict(
    id="os-raid-parity",
    title="RAID Parity and Reconstruction",
    difficulty="Easy",
    pattern="Storage",
    entry="raid_recover",
    description=r"""
A RAID level 4/5 stripe consists of data blocks plus one parity block, where the parity is the
bytewise XOR of all the data blocks. Each block is a list of byte values (0–255) of equal length.

`stripe` is a list of blocks.

- If exactly one entry is `None`, that drive has failed: return the reconstructed block (it may be a
  data block or the parity block — the computation is the same).
- If no entry is `None`, the list holds only data blocks: return their parity block.

**Example:** `stripe = [[1, 2, 3], None, [7, 7, 7]]` → `[6, 5, 4]`

**Constraints:** 1 to 64 blocks, block length up to 4096, at most one `None`. A stripe consisting only of `None` reconstructs to an empty block `[]`.
""",
    starter='''def raid_recover(stripe):
    pass
''',
    solution='''def raid_recover(stripe):
    blocks = [b for b in stripe if b is not None]
    if not blocks:
        return []
    out = [0] * len(blocks[0])
    for b in blocks:
        for i, v in enumerate(b):
            out[i] ^= v
    return out
''',
    tests=[
        [[[1, 2, 3], None, [7, 7, 7]]],
        [[[1, 2, 3], [4, 5, 6]]],
        [[None]],
        [[[9, 9]]],
        [[[0, 255], None]],
        [[[5], [5], None]],
        [[[1], [2], [4], [8]]],
        [[[], None, []]],
        [[None, [170, 85], [255, 0], [15, 240]]],
        [_stripe(5, 16, 2)],
        [_stripe(5, 16, 4)],
        [_stripe(8, 64, None)],
        [_stripe(16, 4096, 0)],
    ],
    examples=2,
    wrong_solutions=[
        '''def raid_recover(stripe):
    blocks = [b for b in stripe if b is not None]
    if not blocks:
        return []
    out = [0] * len(blocks[0])
    for b in blocks:
        for i, v in enumerate(b):
            out[i] = (out[i] + v) % 256
    return out
''',
        '''def raid_recover(stripe):
    blocks = [b for b in stripe if b is not None]
    if not blocks:
        return []
    out = [0] * len(blocks[0])
    for b in blocks:
        for i, v in enumerate(b):
            out[i] |= v
    return out
''',
    ],
    guide=dict(
        prereqs="XOR and its properties; RAID levels (disk lesson).",
        intuition="XOR is its own inverse: `a ^ b ^ b = a`. If `P = D0 ^ D1 ^ D2`, then XOR-ing P with any two of the data blocks cancels them and leaves the third. So 'compute parity' and 'rebuild a missing block' are the *same* operation: XOR everything you still have.",
        hints=[
            "Ignore the `None` entry and combine the others.",
            "Work column by column: byte `i` of the result is the XOR of byte `i` of every surviving block.",
            "Start the accumulator at 0, the identity for XOR.",
        ],
        brute_force="For each byte position try all 256 candidate values and keep the one that makes the XOR of the whole column zero. It works because exactly one value fits — and shows why parity can repair one loss but not two.",
        approach="""**Dry run** `[[1,2,3], None, [7,7,7]]`: column 0: 1 ^ 7 = 6; column 1: 2 ^ 7 = 5; column 2: 3 ^ 7 = 4 → `[6,5,4]`. Check: `[1,2,3] ^ [6,5,4] = [7,7,7]`, consistent whichever of the three is called 'parity'.""",
        complexity="O(blocks × block length) time, O(block length) space.",
        pitfalls="Using addition modulo 256 (first wrong solution) — rebuilding would then need subtraction, and the parity/data symmetry is lost. Using OR (second), which destroys information. Forgetting that single parity survives only one failure; a second failure, or an unreadable sector found during the rebuild, loses data, which motivates RAID 6.",
        follow_up="A small write need not read the whole stripe: `new_parity = old_parity ^ old_data ^ new_data`. Implement that update and verify it against a full recomputation.",
    ),
),
dict(
    id="os-free-bitmap",
    title="Free-space Bitmap: Find a Run of Free Blocks",
    difficulty="Medium",
    pattern="File Systems",
    entry="find_free_run",
    description=r"""
A file system tracks free blocks with a bitmap stored as a list of bytes. Block `i` is described by
bit `i % 8` of byte `i // 8`, counting from the **least significant** bit; a `1` bit means *in use*.

Return the number of the first block that starts a run of at least `n` consecutive free blocks, or
`-1` if there is no such run. The disk has exactly `8 * len(bitmap)` blocks.

**Example:** `bitmap = [0b00001111, 0b11111000], n = 5` → `4`
(blocks 0–3 used, 4–10 free, 11–15 used).

**Constraints:** `len(bitmap) ≤ 10^5`, `1 ≤ n ≤ 10^6`.
""",
    starter='''def find_free_run(bitmap, n):
    pass
''',
    solution='''def find_free_run(bitmap, n):
    run = 0
    for byte_no, byte in enumerate(bitmap):
        if byte == 0 and run + 8 < n:
            run += 8
            continue
        for bit in range(8):
            if byte >> bit & 1:
                run = 0
            else:
                run += 1
                if run == n:
                    return byte_no * 8 + bit - n + 1
    return -1
''',
    tests=[
        [[0b00001111, 0b11111000], 5],
        [[0b00001111, 0b11111000], 7],
        [[0b00001111, 0b11111000], 8],
        [[], 1],
        [[255], 1],
        [[0], 8],
        [[0], 9],
        [[0b11111110], 1],
        [[0b01111111], 1],
        [[0b10000000, 0b00000001], 8],
        [[0b00000001, 0, 0, 0b10000000], 30],
        [[0b00000001, 0, 0, 0b10000000], 31],
        [[0b10101010] * 50 + [0b00111100, 0b11111100], 4],
        [[_r.choice([0, 0, 255, 1, 128, 16]) for _ in range(5000)], 40],
        [[255] * 20000 + [0] * 20000, 159999],
    ],
    examples=2,
    wrong_solutions=[
        '''def find_free_run(bitmap, n):
    run = 0
    for byte_no, byte in enumerate(bitmap):
        for bit in range(8):
            if byte >> (7 - bit) & 1:
                run = 0
            else:
                run += 1
                if run == n:
                    return byte_no * 8 + bit - n + 1
    return -1
''',
        '''def find_free_run(bitmap, n):
    for byte_no, byte in enumerate(bitmap):
        run = 0
        for bit in range(8):
            if byte >> bit & 1:
                run = 0
            else:
                run += 1
                if run == n:
                    return byte_no * 8 + bit - n + 1
    return -1
''',
    ],
    guide=dict(
        prereqs="Bit operations; free-space management with bitmaps versus free lists (memory and file-system lessons).",
        intuition="Flatten the bytes into one long row of bits and look for the first stretch of `n` zeros. A single counter of 'zeros seen since the last one' is all the state required; the bit ordering inside a byte is the only real trap.",
        hints=[
            "Bit `k` of a byte is `(byte >> k) & 1`.",
            "Keep `run`; reset it on a used block, increment on a free one, and return as soon as it reaches `n`.",
            "The run started at `current_block - n + 1`. Runs may cross byte boundaries, so never reset between bytes.",
        ],
        brute_force="For every starting block test the next `n` bits: O(blocks × n). Fine for tiny disks, quadratic for large runs.",
        approach="""**Dry run** bytes `00001111`, `11111000`, n = 5: blocks 0–3 used (run 0). Blocks 4, 5, 6, 7 free → run 4. Block 8 is bit 0 of the second byte = 0 → run 5 → start = 8 − 5 + 1 = 4.

Optional speed-up used in the reference: a byte equal to 0 adds 8 to the run at once when that cannot yet complete it.""",
        complexity="O(number of blocks) time, O(1) space.",
        pitfalls="Reading bits most-significant first (first wrong solution). Resetting the counter at each byte (second) — contiguous runs spanning bytes are then missed. Returning the *end* of the run.",
        follow_up="Real allocators scan a word at a time (find-first-zero instructions) and keep per-group free counts so that full regions are skipped entirely — the idea behind ext2/ext4 block groups.",
    ),
),
dict(
    id="os-unix-permissions",
    title="UNIX Permission Check",
    difficulty="Easy",
    pattern="Protection",
    entry="can_access",
    description=r"""
Decide whether a process may access a file under the classic UNIX nine-bit permission model.

- `mode` — the permission bits as an integer (e.g. `0o640` = `rw-r-----`)
- `owner`, `group` — the file's owner uid and group gid
- `uid`, `gids` — the process's effective uid and the list of groups it belongs to
- `want` — a non-empty string made of the letters `r`, `w`, `x`: **all** listed rights are required

Rules:

1. Exactly **one** class applies: if `uid == owner` use the owner bits; otherwise if `group` is in
   `gids` use the group bits; otherwise use the "other" bits. There is no fall-through to a more generous class.
2. The superuser (`uid == 0`) may always read and write; it may execute only if at least one of the three execute bits is set.

Return `True` or `False`.

**Example:** `mode = 0o640, owner = 1000, group = 50, uid = 1001, gids = [50], want = "r"` → `True`;
with `want = "rw"` → `False`.
""",
    starter='''def can_access(mode, owner, group, uid, gids, want):
    pass
''',
    solution='''def can_access(mode, owner, group, uid, gids, want):
    bit = {"r": 4, "w": 2, "x": 1}
    if uid == 0:
        return "x" not in want or bool(mode & 0o111)
    if uid == owner:
        perms = (mode >> 6) & 7
    elif group in gids:
        perms = (mode >> 3) & 7
    else:
        perms = mode & 7
    return all(perms & bit[c] for c in want)
''',
    tests=[
        [0o640, 1000, 50, 1001, [50], "r"],
        [0o640, 1000, 50, 1001, [50], "rw"],
        [0o640, 1000, 50, 1000, [50], "rw"],
        [0o640, 1000, 50, 1002, [7], "r"],
        [0o077, 1000, 50, 1000, [50], "r"],
        [0o707, 1000, 50, 1001, [50], "x"],
        [0o000, 1000, 50, 0, [0], "rw"],
        [0o600, 1000, 50, 0, [0], "x"],
        [0o601, 1000, 50, 0, [0], "rwx"],
        [0o755, 1000, 50, 1234, [], "rx"],
        [0o755, 1000, 50, 1234, [], "w"],
        [0o4755, 0, 0, 1234, [5], "x"],
        [0o570, 1000, 50, 1001, [3, 50, 9], "rwx"],
        [0o570, 1000, 50, 1000, [50], "w"],
    ],
    examples=2,
    wrong_solutions=[
        '''def can_access(mode, owner, group, uid, gids, want):
    bit = {"r": 4, "w": 2, "x": 1}
    if uid == 0:
        return "x" not in want or bool(mode & 0o111)
    perms = mode & 7
    if uid == owner:
        perms |= (mode >> 6) & 7
    if group in gids:
        perms |= (mode >> 3) & 7
    return all(perms & bit[c] for c in want)
''',
        '''def can_access(mode, owner, group, uid, gids, want):
    bit = {"r": 4, "w": 2, "x": 1}
    if uid == 0:
        return True
    if uid == owner:
        perms = (mode >> 6) & 7
    elif group in gids:
        perms = (mode >> 3) & 7
    else:
        perms = mode & 7
    return all(perms & bit[c] for c in want)
''',
        '''def can_access(mode, owner, group, uid, gids, want):
    bit = {"r": 4, "w": 2, "x": 1}
    if uid == 0:
        return "x" not in want or bool(mode & 0o111)
    if uid == owner:
        perms = (mode >> 6) & 7
    elif group in gids:
        perms = (mode >> 3) & 7
    else:
        perms = mode & 7
    return any(perms & bit[c] for c in want)
''',
    ],
    guide=dict(
        prereqs="Octal notation, bit masks, the protection-domain discussion in the security and Linux lessons.",
        intuition="The mode is three 3-bit groups — owner, group, other. The kernel first decides *who you are relative to the file* and then looks at only that group. The surprising consequence: an owner can be locked out of a file everyone else can read.",
        hints=[
            "Extract a class with a shift and a mask: owner `(mode >> 6) & 7`, group `(mode >> 3) & 7`, other `mode & 7`.",
            "Use `if / elif / else` to choose the class, so that exactly one applies.",
            "Handle uid 0 first; note the special treatment of execute.",
        ],
        brute_force="Render the mode as the string `rwxr-x---` and index into it. Perfectly valid and arguably clearer; the bit version is what the kernel does.",
        approach="""**Dry run** `0o640`, owner 1000, group 50. Process uid 1001 in group 50 → group class → bits `100` → read only. `"r"` → True; `"rw"` → False.
`0o077` with the owner asking for `r`: owner class is `000` → False, even though group and other have everything.""",
        complexity="O(len(want)) time, O(1) space.",
        pitfalls="OR-ing the classes together (first wrong solution). Letting root execute a file with no execute bit at all (second). Requiring *any* rather than *all* requested rights (third). Masking: bits above the low nine (setuid, setgid, sticky) must not disturb the result.",
        follow_up="Real systems layer more on top: access control lists, capabilities such as `CAP_DAC_OVERRIDE` instead of an all-powerful uid 0, and mandatory access control (SELinux, AppArmor).",
    ),
),
]
