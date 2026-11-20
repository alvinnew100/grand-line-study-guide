import random as _random

_r = _random.Random(37)


def _bank(n, m, slack):
    alloc = [[_r.randint(0, 3) for _ in range(m)] for _ in range(n)]
    need = [[_r.randint(0, 4) for _ in range(m)] for _ in range(n)]
    maxi = [[a + d for a, d in zip(alloc[i], need[i])] for i in range(n)]
    avail = [_r.randint(0, slack) for _ in range(m)]
    return [avail, alloc, maxi]


def _chain(n):
    # process i holds resource i and wants resource i+1; the last one wants nothing
    return [list(range(n)), [i + 1 for i in range(n - 1)] + [-1]]


def _rw(n):
    t, out = 0, []
    for _ in range(n):
        t += _r.randint(0, 3)
        out.append([t, "W" if _r.random() < 0.3 else "R", _r.randint(1, 6)])
    return out


_BANK_CHECK = '''def check(args, got, expected):
    available, allocation, maximum = args
    n = len(allocation)
    if not expected:
        return got == []
    if not isinstance(got, list) or sorted(got) != list(range(n)):
        return False
    work = list(available)
    for i in got:
        for j in range(len(work)):
            if maximum[i][j] - allocation[i][j] > work[j]:
                return False
        for j in range(len(work)):
            work[j] += allocation[i][j]
    return True
'''

PROBLEMS = [
dict(
    id="os-bankers-safe-sequence",
    title="Banker's Algorithm: Find a Safe Sequence",
    difficulty="Medium",
    pattern="Deadlocks",
    entry="safe_sequence",
    checker=_BANK_CHECK,
    description=r"""
A system has `m` resource types and `n` processes.

- `available[j]` — free instances of resource `j` right now
- `allocation[i][j]` — instances of `j` currently held by process `i`
- `maximum[i][j]` — the most instances of `j` process `i` may ever hold (its declared claim)

The state is **safe** if the processes can be ordered so that each one, in turn, can obtain its whole
remaining need (`maximum − allocation`) from what is available plus everything released by the
processes before it, then finish and release its allocation.

Return **any** safe sequence as a list of process indices, or `[]` if the state is unsafe.
(Any valid ordering is accepted.)

**Example:** `available = [3, 3, 2]`,
`allocation = [[0,1,0],[2,0,0],[3,0,2],[2,1,1],[0,0,2]]`,
`maximum = [[7,5,3],[3,2,2],[9,0,2],[2,2,2],[4,3,3]]` → e.g. `[1, 3, 4, 0, 2]`

**Constraints:** `1 ≤ n ≤ 200`, `1 ≤ m ≤ 20`, `allocation[i][j] ≤ maximum[i][j]`.
""",
    starter='''def safe_sequence(available, allocation, maximum):
    pass
''',
    solution='''def safe_sequence(available, allocation, maximum):
    n = len(allocation)
    work = list(available)
    need = [[mx - al for mx, al in zip(maximum[i], allocation[i])] for i in range(n)]
    done = [False] * n
    seq = []
    progress = True
    while progress:
        progress = False
        for i in range(n):
            if not done[i] and all(x <= w for x, w in zip(need[i], work)):
                work = [w + a for w, a in zip(work, allocation[i])]
                done[i] = True
                seq.append(i)
                progress = True
    return seq if len(seq) == n else []
''',
    tests=[
        [[3, 3, 2], [[0, 1, 0], [2, 0, 0], [3, 0, 2], [2, 1, 1], [0, 0, 2]], [[7, 5, 3], [3, 2, 2], [9, 0, 2], [2, 2, 2], [4, 3, 3]]],
        [[0, 0], [[1, 0], [0, 1]], [[1, 1], [1, 1]]],
        [[1], [[0]], [[1]]],
        [[0], [[0]], [[1]]],
        [[0, 0, 0], [[1, 2, 3]], [[1, 2, 3]]],
        [[1, 0], [[1, 0], [0, 1]], [[1, 1], [1, 1]]],
        [[2, 3, 0], [[0, 1, 0], [3, 0, 2], [3, 0, 2], [2, 1, 1], [0, 0, 2]], [[7, 5, 3], [3, 2, 2], [9, 0, 2], [2, 2, 2], [4, 3, 3]]],
        [[1, 5, 2, 0], [[0, 0, 1, 2], [1, 0, 0, 0], [1, 3, 5, 4], [0, 6, 3, 2], [0, 0, 1, 4]], [[0, 0, 1, 2], [1, 7, 5, 0], [2, 3, 5, 6], [0, 6, 5, 2], [0, 6, 5, 6]]],
        [[0, 1], [[2, 0], [0, 0], [1, 1]], [[3, 1], [1, 1], [1, 2]]],
        [[1], [[1], [1], [1], [1]], [[5], [4], [3], [2]]],
        [[1], [[1], [1], [1], [1]], [[5], [4], [4], [4]]],
        _bank(8, 3, 4),
        _bank(8, 3, 1),
        _bank(40, 5, 5),
        _bank(150, 6, 2),
    ],
    examples=2,
    wrong_solutions=[
        '''def safe_sequence(available, allocation, maximum):
    return list(range(len(allocation)))
''',
        '''def safe_sequence(available, allocation, maximum):
    n = len(allocation)
    work = list(available)
    done = [False] * n
    seq = []
    progress = True
    while progress:
        progress = False
        for i in range(n):
            if not done[i] and all(mx - al <= w for mx, al, w in zip(maximum[i], allocation[i], work)):
                done[i] = True
                seq.append(i)
                progress = True
    return seq if len(seq) == n else []
''',
        '''def safe_sequence(available, allocation, maximum):
    n = len(allocation)
    work = list(available)
    seq = []
    for i in range(n):
        if all(mx - al <= w for mx, al, w in zip(maximum[i], allocation[i], work)):
            work = [w + a for w, a in zip(work, allocation[i])]
            seq.append(i)
    return seq if len(seq) == n else []
''',
    ],
    guide=dict(
        prereqs="The deadlock-avoidance lesson: safe and unsafe states, the Need matrix. Basic list comprehension skills.",
        intuition="Imagine a cautious banker with limited cash. A customer is 'serviceable' if the banker could hand over *everything* the customer might still ask for. Service that customer in your head, collect their whole loan back, and the vault only grows — so greedily picking any serviceable process never hurts.",
        hints=[
            "Compute `need[i][j] = maximum[i][j] - allocation[i][j]` first.",
            "Keep a `work` vector, starting as `available`. Find any unfinished process whose need fits componentwise inside `work`.",
            "When a process 'finishes', add its *allocation* (not its need) to `work`. Repeat until no process can be added; safe iff all are done.",
        ],
        brute_force="Try all n! orderings and test each one. Correct, and a fine oracle for n ≤ 8, but the greedy search is polynomial because the order in which serviceable processes are picked cannot turn a safe state into a stuck one.",
        approach="""**Dry run** on the first example. Need = `[[7,4,3],[1,2,2],[6,0,0],[0,1,1],[4,3,1]]`, work = `[3,3,2]`.
P0 needs 7 of resource 0 → no. P1 `[1,2,2] ≤ [3,3,2]` → finish, work `[5,3,2]`.
P2 needs 6 → no. P3 `[0,1,1]` fits → work `[7,4,3]`. P4 fits → `[7,4,5]`.
Second pass: P0 fits → `[7,5,5]`; P2 fits → `[10,5,7]`. Sequence `[1,3,4,0,2]`.""",
        complexity="At most n passes over n processes, each comparing m numbers: O(n²·m) time, O(n·m) space.",
        pitfalls="Releasing `need` instead of `allocation`, or releasing nothing (second wrong solution). Making a single pass in index order (third wrong solution) — a process skipped early may become serviceable later. Comparing only the sum of needs rather than each resource type.",
        follow_up="To decide whether to *grant* a request, pretend to grant it (move units from available to allocation), run this check, and roll back if the result is unsafe.",
    ),
),
dict(
    id="os-deadlock-detection",
    title="Deadlock Detection on a Resource Graph",
    difficulty="Medium",
    pattern="Deadlocks",
    entry="deadlocked",
    description=r"""
Every resource has a single instance.

- `holds[r]` is the process currently holding resource `r`, or `-1` if it is free.
- `wants[p]` is the one resource process `p` is blocked waiting for, or `-1` if `p` is not waiting.

A process waiting for a free resource is not stuck (the resource will simply be granted). A process is
**deadlocked** if it can never run again: it is part of a circular wait, or it is waiting — directly or
through a chain of other waiting processes — for a process that is part of one.

Return the sorted list of deadlocked processes.

**Example:** `holds = [0, 1, 2], wants = [1, 0, 0, -1]` → `[0, 1, 2]`
(P0 and P1 wait for each other; P2 holds R2 and waits for R0, held by P0, so it is stuck behind the cycle; P3 is fine).

**Constraints:** up to `10^5` processes and resources. A process may wait for a resource it holds itself (a self-deadlock).
""",
    starter='''def deadlocked(holds, wants):
    pass
''',
    solution='''def deadlocked(holds, wants):
    n = len(wants)
    state = [0] * n          # 0 unknown, 1 on current path, 2 fine, 3 deadlocked
    for s in range(n):
        if state[s]:
            continue
        path, p = [], s
        while p != -1 and state[p] == 0:
            state[p] = 1
            path.append(p)
            r = wants[p]
            p = -1 if r == -1 else holds[r]
        if p == -1:
            verdict = 2
        elif state[p] == 1:
            verdict = 3
        else:
            verdict = state[p]
        for q in path:
            state[q] = verdict
    return [p for p in range(n) if state[p] == 3]
''',
    tests=[
        [[0, 1, 2], [1, 0, 0, -1]],
        [[0, 1], [1, -1]],
        [[], []],
        [[-1], [0]],
        [[0], [0]],
        [[0, 1, 2], [1, 2, 0]],
        [[1, 0, -1], [0, 1, 2]],
        [[0, 1, 2, 3], [1, 2, 3, -1, 0, 3]],
        [[0, 0, 1], [2, 0, -1]],
        [[2, 2, 0, 1], [3, 2, 0, -1, -1]],
        _chain(2000),
        [list(range(3000)), [(i + 1) % 3000 for i in range(3000)]],
        [list(range(2500)) + [-1], [1, 0] + [i - 1 for i in range(2, 2499)] + [2500]],
    ],
    examples=2,
    wrong_solutions=[
        '''def deadlocked(holds, wants):
    n = len(wants)
    out = []
    for s in range(n):
        p, steps = s, 0
        while steps <= n:
            r = wants[p]
            if r == -1 or holds[r] == -1:
                break
            p = holds[r]
            steps += 1
            if p == s:
                out.append(s)
                break
    return out
''',
        '''def deadlocked(holds, wants):
    return [p for p, r in enumerate(wants) if r != -1 and holds[r] != -1]
''',
    ],
    guide=dict(
        prereqs="Resource-allocation graphs and the four deadlock conditions (deadlock lesson). Cycle detection in a functional graph.",
        intuition="Collapse the resource graph into a *wait-for* graph: P → Q when P waits for something Q holds. Each process has at most one outgoing edge, so following edges from any process traces a single path that either ends (someone runnable — the whole chain will eventually drain) or loops (everyone on the path is stuck forever).",
        hints=[
            "Define `next(p)`: `-1` if `p` wants nothing or wants a free resource, else `holds[wants[p]]`.",
            "Walk from each unvisited process, marking nodes 'on the current path'. Stop when you hit `-1`, a node on the current path, or a node already classified.",
            "Whatever verdict the stopping point has, the entire path inherits it. Hitting your own path means a new cycle was found.",
        ],
        brute_force="From every process follow the chain for up to n steps; if it has not terminated by then, it must be looping, so the start is deadlocked. O(n²) in the worst case (one long chain), but obviously correct.",
        approach="""Three-colour walk with path labelling.

**Dry run** `holds=[0,1,2]`, `wants=[1,0,0,-1]`: start P0 → wants R1 held by P1 → P1 wants R0 held by P0, which is on the current path → cycle: P0, P1 deadlocked. Start P2 → wants R0 held by P0, already 'deadlocked' → P2 inherits it. P3 wants nothing → fine. Answer `[0,1,2]`.""",
        complexity="Every process is put on a path exactly once: O(n) time, O(n) space.",
        pitfalls="Reporting only the processes *on* the cycle and missing those queued behind it (first wrong solution). Treating every blocked process as deadlocked (second wrong solution) — blocking is normal; only unresolvable waiting is deadlock. Forgetting the self-wait case.",
        follow_up="With several instances per resource a cycle is necessary but not sufficient; you then need the matrix-based detection algorithm from the lesson, which is the banker's safety check run on current requests instead of maximum claims.",
    ),
),
dict(
    id="os-dining-philosophers",
    title="Dining Philosophers: Replay a Schedule",
    difficulty="Medium",
    pattern="Synchronisation",
    entry="dining",
    description=r"""
`n ≥ 2` philosophers sit round a table; fork `i` lies between philosopher `i` and philosopher `i-1`,
so philosopher `p` uses forks `p` and `(p + 1) % n`.

Each philosopher picks up a **first** fork and then a **second** fork:

- if `ordered` is `False`: first = fork `p`, second = fork `(p + 1) % n`;
- if `ordered` is `True` (resource ordering): first = the lower-numbered of the two, second = the higher.

`schedule` is the sequence in which the philosophers get a turn. On its turn, philosopher `p` does exactly one thing:

- holding no fork → takes the first fork if it is free (otherwise nothing happens);
- holding one fork → takes the second fork if it is free (otherwise nothing happens);
- holding both → eats, then puts both forks down (one meal).

Return `[meals, deadlock]` where `meals[p]` counts philosopher `p`'s meals and `deadlock` is `True`
when, after the schedule, **every** philosopher holds exactly one fork.

**Example:** `n = 3, schedule = [0, 1, 2, 0, 1, 2], ordered = False` → `[[0, 0, 0], True]`

**Constraints:** `2 ≤ n ≤ 1000`, `len(schedule) ≤ 10^5`.
""",
    starter='''def dining(n, schedule, ordered):
    pass
''',
    solution='''def dining(n, schedule, ordered):
    owner = [-1] * n
    held = [0] * n
    meals = [0] * n
    for p in schedule:
        first, second = p, (p + 1) % n
        if ordered and first > second:
            first, second = second, first
        if held[p] == 0:
            if owner[first] == -1:
                owner[first] = p
                held[p] = 1
        elif held[p] == 1:
            if owner[second] == -1:
                owner[second] = p
                held[p] = 2
        else:
            owner[first] = owner[second] = -1
            held[p] = 0
            meals[p] += 1
    return [meals, all(h == 1 for h in held)]
''',
    tests=[
        [3, [0, 1, 2, 0, 1, 2], False],
        [3, [0, 1, 2, 0, 1, 2], True],
        [2, [], False],
        [2, [0, 0, 0], False],
        [2, [0, 1, 0, 1], False],
        [2, [0, 1, 0, 1, 0, 1, 0, 1], True],
        [5, [0, 0, 0, 2, 2, 2, 4, 4, 4], False],
        [5, [0, 1, 2, 3, 4] * 4, False],
        [5, [0, 1, 2, 3, 4] * 4, True],
        [4, [3, 3, 3, 0, 0, 0, 3, 0], True],
        [4, [0, 1, 0, 1, 0, 2, 3, 1, 1, 2, 2], False],
        [50, [_r.randrange(50) for _ in range(4000)], False],
        [50, [_r.randrange(50) for _ in range(4000)], True],
        [1000, list(range(1000)) * 3, False],
    ],
    examples=2,
    wrong_solutions=[
        '''def dining(n, schedule, ordered):
    owner = [-1] * n
    held = [0] * n
    meals = [0] * n
    for p in schedule:
        first, second = p, (p + 1) % n
        if held[p] == 0:
            if owner[first] == -1:
                owner[first] = p
                held[p] = 1
        elif held[p] == 1:
            if owner[second] == -1:
                owner[second] = p
                held[p] = 2
        else:
            owner[first] = owner[second] = -1
            held[p] = 0
            meals[p] += 1
    return [meals, all(h == 1 for h in held)]
''',
        '''def dining(n, schedule, ordered):
    owner = [-1] * n
    held = [0] * n
    meals = [0] * n
    for p in schedule:
        first, second = p, (p + 1) % n
        if ordered and first > second:
            first, second = second, first
        if held[p] == 0:
            if owner[first] == -1:
                owner[first] = p
                held[p] = 1
        elif held[p] == 1:
            owner[second] = p
            held[p] = 2
        else:
            owner[first] = owner[second] = -1
            held[p] = 0
            meals[p] += 1
    return [meals, all(h == 1 for h in held)]
''',
    ],
    guide=dict(
        prereqs="The classic-IPC lesson (dining philosophers), the circular-wait condition, and resource ordering as a prevention technique.",
        intuition="Threads are just interleavings. Fix the interleaving as data and a concurrency puzzle becomes an ordinary state machine: each philosopher is in state 0, 1 or 2 (forks held) and each turn advances that machine by at most one step.",
        hints=[
            "Track `owner[fork]` and `held[p]`.",
            "Compute `(first, second)` at the top of each turn; with `ordered` swap them when `first > second` — that only ever happens for the last philosopher.",
            "Deadlock here is simply `all(h == 1 for h in held)`: n forks, n holders, each waiting for a neighbour.",
        ],
        brute_force="There is no asymptotically worse sensible approach — the simulation is the specification. A real-thread version would be *non-deterministic*, which is exactly why we replay a schedule instead.",
        approach="""**Dry run**, n=3, unordered, schedule `0 1 2 0 1 2`: P0 takes fork 0, P1 takes fork 1, P2 takes fork 2. Second round: P0 wants fork 1 (held by P1), P1 wants fork 2, P2 wants fork 0 — nobody moves. Everyone holds one fork → deadlock.

Ordered: P2's forks are {2, 0}, so its first fork is 0, already taken by P0 → P2 holds nothing. Then P0 wants fork 1 (held), P1 takes fork 2 and can eat on its next turn. No circular wait can form.""",
        complexity="O(len(schedule)) time, O(n) space.",
        pitfalls="Ignoring the `ordered` flag (first wrong solution). Letting a philosopher grab a fork that is already owned (second wrong solution) — the mutual-exclusion violation the whole problem is about. Counting a meal when the second fork is picked up rather than on the following turn.",
        follow_up="Other cures: allow at most n−1 philosophers to reach for forks at once (a counting semaphore), or pick up both forks atomically inside a monitor.",
    ),
),
dict(
    id="os-readers-writers",
    title="Readers–Writers Lock Simulation",
    difficulty="Hard",
    pattern="Synchronisation",
    entry="readers_writers",
    description=r"""
Simulate a readers–writers lock. `requests[i] = [arrival, kind, duration]` with `kind` `"R"` or `"W"`.
Any number of readers may hold the lock together; a writer needs it exclusively. A request that starts
at time `s` holds the lock during `[s, s + duration)`.

At every instant where something arrives or finishes, do in order: (1) release finished holders,
(2) add new arrivals to the waiting list (by arrival, then index), (3) admit according to `prefer`:

- `"readers"`: if no writer is active, **all** waiting readers start (even if writers are waiting).
  Then, if nobody holds the lock, the earliest waiting writer starts.
- `"writers"`: if any writer is waiting, readers are held back; the earliest waiting writer starts as
  soon as nobody holds the lock. If no writer is waiting and none is active, all waiting readers start.

Return the list of start times indexed by request.

**Example:** `requests = [[0,"R",4],[1,"W",2],[2,"R",4]]`
- `prefer = "readers"` → `[0, 6, 2]` (the second reader slips in; the writer waits until 6)
- `prefer = "writers"` → `[0, 4, 6]`

**Constraints:** up to 2000 requests, `duration ≥ 1`.
""",
    starter='''def readers_writers(requests, prefer):
    pass
''',
    solution='''def readers_writers(requests, prefer):
    n = len(requests)
    order = sorted(range(n), key=lambda i: (requests[i][0], i))
    start = [0] * n
    waiting, reader_ends = [], []
    writer_end = None
    k = 0
    if n == 0:
        return start
    t = requests[order[0]][0]
    while True:
        reader_ends = [e for e in reader_ends if e > t]
        if writer_end is not None and writer_end <= t:
            writer_end = None
        while k < n and requests[order[k]][0] <= t:
            waiting.append(order[k])
            k += 1
        if writer_end is None:
            writers = [i for i in waiting if requests[i][1] == "W"]
            if prefer == "writers" and writers:
                if not reader_ends:
                    i = writers[0]
                    start[i] = t
                    writer_end = t + requests[i][2]
                    waiting.remove(i)
            else:
                for i in waiting:
                    if requests[i][1] == "R":
                        start[i] = t
                        reader_ends.append(t + requests[i][2])
                waiting = writers
                if waiting and not reader_ends:
                    i = waiting.pop(0)
                    start[i] = t
                    writer_end = t + requests[i][2]
        cands = []
        if k < n:
            cands.append(requests[order[k]][0])
        if waiting:
            if writer_end is not None:
                cands.append(writer_end)
            if reader_ends:
                cands.append(min(reader_ends))
        if not cands:
            break
        t = min(cands)
    return start
''',
    tests=[
        [[[0, "R", 4], [1, "W", 2], [2, "R", 4]], "readers"],
        [[[0, "R", 4], [1, "W", 2], [2, "R", 4]], "writers"],
        [[], "readers"],
        [[[5, "W", 3]], "writers"],
        [[[0, "W", 3], [0, "W", 2], [0, "R", 1]], "readers"],
        [[[0, "W", 3], [0, "W", 2], [0, "R", 1]], "writers"],
        [[[0, "R", 2], [0, "R", 5], [0, "R", 1]], "writers"],
        [[[0, "R", 3], [1, "W", 1], [2, "R", 3], [4, "R", 3], [6, "R", 3]], "readers"],
        [[[0, "R", 3], [1, "W", 1], [2, "R", 3], [4, "R", 3], [6, "R", 3]], "writers"],
        [[[0, "W", 5], [1, "R", 1], [2, "W", 1], [3, "R", 1]], "readers"],
        [[[0, "W", 5], [1, "R", 1], [2, "W", 1], [3, "R", 1]], "writers"],
        [[[3, "R", 2], [0, "W", 3], [10, "W", 1]], "readers"],
        [_rw(40), "readers"],
        [_rw(40), "writers"],
        [_rw(600), "writers"],
    ],
    examples=2,
    wrong_solutions=[
        '''def readers_writers(requests, prefer):
    order = sorted(range(len(requests)), key=lambda i: (requests[i][0], i))
    start = [0] * len(requests)
    t = 0
    for i in order:
        t = max(t, requests[i][0])
        start[i] = t
        t += requests[i][2]
    return start
''',
        '''def readers_writers(requests, prefer):
    n = len(requests)
    order = sorted(range(n), key=lambda i: (requests[i][0], i))
    start = [0] * n
    waiting, reader_ends = [], []
    writer_end = None
    k = 0
    if n == 0:
        return start
    t = requests[order[0]][0]
    while True:
        reader_ends = [e for e in reader_ends if e > t]
        if writer_end is not None and writer_end <= t:
            writer_end = None
        while k < n and requests[order[k]][0] <= t:
            waiting.append(order[k])
            k += 1
        if writer_end is None:
            writers = [i for i in waiting if requests[i][1] == "W"]
            for i in waiting:
                if requests[i][1] == "R":
                    start[i] = t
                    reader_ends.append(t + requests[i][2])
            waiting = writers
            if waiting and not reader_ends:
                i = waiting.pop(0)
                start[i] = t
                writer_end = t + requests[i][2]
        cands = []
        if k < n:
            cands.append(requests[order[k]][0])
        if waiting:
            if writer_end is not None:
                cands.append(writer_end)
            if reader_ends:
                cands.append(min(reader_ends))
        if not cands:
            break
        t = min(cands)
    return start
''',
    ],
    guide=dict(
        prereqs="The readers–writers problem from the classic-IPC lesson; event-driven simulation as used in the SRTF problem.",
        intuition="The lock has only three interesting states: free, held by k readers, held by one writer. Policy matters at exactly one point — when both a reader and a writer are waiting and the lock could admit readers. 'Readers first' maximises concurrency and can starve writers; 'writers first' keeps data fresh and can starve readers.",
        hints=[
            "Keep `reader_ends` (finish times of active readers), `writer_end` (or None) and a `waiting` list in arrival order.",
            "Write one `admit` step that is called at every event time after releasing finished holders and enqueuing arrivals.",
            "The next event time is the minimum of the next arrival and — only if someone is waiting — the earliest finish among current holders.",
        ],
        brute_force="Advance time one unit at a time and run the same release / enqueue / admit steps on every tick. Easier to reason about and a good cross-check, at O(total time) cost.",
        approach="""**Dry run** `[[0,R,4],[1,W,2],[2,R,4]]`.
*Readers preference*: t=0 R0 starts (ends 4). t=1 W1 waits. t=2 R2 arrives; no writer active → starts (ends 6). t=4 R0 leaves; a reader is still active. t=6 lock free → W1 starts. Result `[0,6,2]`.
*Writers preference*: t=2 R2 arrives but a writer is waiting → held back. t=4 lock free → W1 starts (ends 6). t=6 R2 starts. Result `[0,4,6]`.""",
        complexity="O(E · n) with E events for this straightforward version (the waiting list is rescanned at each event); heaps and separate reader/writer queues bring it to O(n log n).",
        pitfalls="Serialising everything as if it were a plain mutex (first wrong solution). Ignoring the policy flag (second wrong solution). Letting a writer start while readers are still inside. Advancing time to a holder's finish when nobody is waiting, which is harmless but can loop forever if you never break.",
        follow_up="Design a *fair* policy: a single FIFO queue where a batch of consecutive readers enters together. Neither side can starve.",
    ),
),
dict(
    id="os-semaphore-trace",
    title="Evaluate a Semaphore Trace",
    difficulty="Easy",
    pattern="Synchronisation",
    entry="sem_trace",
    description=r"""
A counting semaphore starts with value `initial ≥ 0` and has a FIFO queue of blocked processes.
`ops` is a list of `[pid, op]` pairs executed in order, where `op` is `"P"` (down / wait) or `"V"` (up / signal).

- `P`: if the value is positive, decrement it; otherwise the caller blocks and joins the queue.
- `V`: if the queue is non-empty, wake the process at its head (the value stays unchanged — the
  woken process consumes the signal); otherwise increment the value.
- An operation issued by a process that is currently blocked is **ignored** (a blocked process cannot run).

Return `[value, blocked, woken]`: the final value, the pids still blocked in queue order, and the pids
that were woken, in wake-up order.

**Example:** `initial = 1, ops = [[1,"P"],[2,"P"],[3,"P"],[1,"V"],[2,"V"]]` → `[0, [], [2, 3]]`

**Constraints:** up to `10^5` operations.
""",
    starter='''def sem_trace(initial, ops):
    pass
''',
    solution='''from collections import deque

def sem_trace(initial, ops):
    value = initial
    queue, blocked, woken = deque(), set(), []
    for pid, op in ops:
        if pid in blocked:
            continue
        if op == "P":
            if value > 0:
                value -= 1
            else:
                queue.append(pid)
                blocked.add(pid)
        else:
            if queue:
                w = queue.popleft()
                blocked.discard(w)
                woken.append(w)
            else:
                value += 1
    return [value, list(queue), woken]
''',
    tests=[
        [1, [[1, "P"], [2, "P"], [3, "P"], [1, "V"], [2, "V"]]],
        [0, [[1, "P"], [2, "V"], [1, "P"]]],
        [3, []],
        [0, [[1, "V"], [1, "V"], [2, "P"]]],
        [0, [[1, "P"], [1, "V"], [1, "P"], [2, "V"]]],
        [2, [[1, "P"], [2, "P"], [3, "P"], [4, "P"], [5, "V"], [3, "V"], [3, "P"]]],
        [0, [[7, "P"], [8, "P"], [9, "P"]]],
        [1, [[1, "P"], [1, "P"], [2, "V"], [1, "V"]]],
        [0, [[1, "P"], [2, "P"], [3, "V"], [1, "P"], [3, "V"], [3, "V"]]],
        [5, [[i % 9, "P"] for i in range(40)] + [[100, "V"]] * 3],
        [2, [[_r.randrange(12), _r.choice("PPV")] for _ in range(500)]],
        [0, [[_r.randrange(300), _r.choice("PV")] for _ in range(15000)]],
    ],
    examples=2,
    wrong_solutions=[
        '''def sem_trace(initial, ops):
    value = initial
    queue, blocked, woken = [], set(), []
    for pid, op in ops:
        if pid in blocked:
            continue
        if op == "P":
            if value > 0:
                value -= 1
            else:
                queue.append(pid)
                blocked.add(pid)
        else:
            value += 1
            if queue:
                w = queue.pop(0)
                blocked.discard(w)
                woken.append(w)
    return [value, queue, woken]
''',
        '''def sem_trace(initial, ops):
    value = initial
    queue, woken = [], []
    for pid, op in ops:
        if op == "P":
            if value > 0:
                value -= 1
            else:
                queue.append(pid)
        else:
            if queue:
                woken.append(queue.pop(0))
            else:
                value += 1
    return [value, queue, woken]
''',
    ],
    guide=dict(
        prereqs="Semaphores (down/up, also written P/V or wait/signal) from the IPC lesson; queues.",
        intuition="A semaphore is a counter of 'permits' plus a waiting room. `P` takes a permit or sits down to wait; `V` hands a permit directly to the first waiter if there is one, and only otherwise returns it to the counter. Value and queue are never both non-zero.",
        hints=[
            "Maintain the integer value, a FIFO queue, and a set of blocked pids for fast membership tests.",
            "On `V` with waiters, do **not** increment: the permit is passed straight to the woken process.",
            "Skip any operation whose pid is in the blocked set.",
        ],
        brute_force="A plain list with `pop(0)` and `pid in list` checks is O(n) per operation — O(n²) for a long trace with many blocked processes. A deque and a set fix both.",
        approach="""**Dry run** `initial=1`: P by 1 → value 0. P by 2 → blocks, queue [2]. P by 3 → blocks, queue [2,3]. V by 1 → wakes 2, queue [3], value still 0. V by 2 (now runnable) → wakes 3. Result `[0, [], [2,3]]`.""",
        complexity="O(len(ops)) time, O(number of blocked processes) space.",
        pitfalls="Incrementing on every `V` (first wrong solution) lets a later `P` steal a permit that was already given away. Executing operations of blocked processes (second wrong solution). Using a stack instead of a queue, which starves early waiters.",
        follow_up="Some textbooks let the value go negative, with `-value` equal to the number of waiters. Rewrite the function in that convention and show both give the same wake-up order.",
    ),
),
]
