import random as _random

_r = _random.Random(11)


def _procs(n, max_arr=20, max_burst=9):
    return [[_r.randint(0, max_arr), _r.randint(1, max_burst)] for _ in range(n)]


def _procs_prio(n):
    return [[_r.randint(0, 15), _r.randint(1, 8), _r.randint(0, 4)] for _ in range(n)]


PROBLEMS = [
dict(
    id="os-fcfs-scheduling",
    title="FCFS Scheduling: Waiting and Turnaround",
    difficulty="Easy",
    pattern="CPU Scheduling",
    entry="fcfs",
    description=r"""
A single CPU runs jobs strictly in order of arrival (first-come, first-served) and never preempts.

`procs[i] = [arrival, burst]` describes job `i` (the index is its id). Jobs that arrive at the same
instant run in increasing id order. If the CPU has nothing to run it sits idle until the next arrival.

Return a list where entry `i` is `[waiting, turnaround]` for job `i`:

- **turnaround** = completion time − arrival time
- **waiting** = turnaround − burst

**Example:** `procs = [[0, 5], [1, 3], [2, 1]]` → `[[0, 5], [4, 7], [6, 7]]`
(job 1 starts at 5 and ends at 8; job 2 runs from 8 to 9).

**Constraints:** `0 ≤ len(procs) ≤ 10^4`, `arrival ≥ 0`, `burst ≥ 1`. The input is *not* guaranteed to be sorted.
""",
    starter='''def fcfs(procs):
    # procs[i] = [arrival, burst]; return [[waiting, turnaround], ...] indexed by job id
    pass
''',
    solution='''def fcfs(procs):
    order = sorted(range(len(procs)), key=lambda i: (procs[i][0], i))
    res = [None] * len(procs)
    clock = 0
    for i in order:
        arrival, burst = procs[i]
        clock = max(clock, arrival) + burst
        res[i] = [clock - arrival - burst, clock - arrival]
    return res
''',
    tests=[
        [[[0, 5], [1, 3], [2, 1]]],
        [[[0, 3], [10, 2]]],
        [[[4, 2], [0, 6], [2, 1]]],
        [[]],
        [[[7, 4]]],
        [[[0, 1], [0, 1], [0, 1]]],
        [[[5, 2], [5, 9], [5, 1], [0, 1]]],
        [[[0, 10], [1, 1], [2, 1], [3, 1]]],
        [[[3, 3], [3, 3], [20, 1], [21, 5], [21, 1]]],
        [_procs(12)],
        [_procs(40, 200, 5)],
        [[[i, 2] for i in range(3000)]],
    ],
    examples=2,
    wrong_solutions=[
        '''def fcfs(procs):
    res = []
    clock = 0
    for arrival, burst in procs:
        clock = max(clock, arrival) + burst
        res.append([clock - arrival - burst, clock - arrival])
    return res
''',
        '''def fcfs(procs):
    order = sorted(range(len(procs)), key=lambda i: (procs[i][0], i))
    res = [None] * len(procs)
    clock = 0
    for i in order:
        arrival, burst = procs[i]
        clock += burst
        res[i] = [clock - arrival - burst, clock - arrival]
    return res
''',
    ],
    guide=dict(
        prereqs="The scheduling lesson: arrival time, burst time, turnaround and waiting time. Sorting with a key.",
        intuition="FCFS is a single queue at a ticket counter. The only state you need is one clock: the moment the CPU next becomes free. Each job starts at the later of *its arrival* and *that clock*.",
        hints=[
            "Process the jobs in arrival order, but remember where each answer belongs: the output is indexed by the original job id.",
            "Keep a variable `clock`. A job starts at `max(clock, arrival)` — the `max` covers idle gaps.",
            "After a job finishes at `clock`, turnaround is `clock - arrival` and waiting is that minus the burst.",
        ],
        brute_force="Advance a clock one time unit at a time, keeping an explicit queue of arrived jobs. It works, but costs O(total time) instead of O(n log n) and adds nothing for a non-preemptive policy.",
        approach="""1. Build a list of job ids sorted by `(arrival, id)`.
2. Walk it with `clock = 0`. For each job: `clock = max(clock, arrival) + burst`.
3. Store `[clock - arrival - burst, clock - arrival]` at the job's original index.

**Dry run** on `[[4,2],[0,6],[2,1]]`: order is job 1, job 2, job 0.
Job 1: clock = max(0,0)+6 = 6 → wait 0, turnaround 6.
Job 2: clock = max(6,2)+1 = 7 → wait 4, turnaround 5.
Job 0: clock = max(7,4)+2 = 9 → wait 3, turnaround 5.
Answer `[[3,5],[0,6],[4,5]]`.""",
        complexity="Time O(n log n) for the sort, O(n) for the sweep. Space O(n) for the order and the result.",
        pitfalls="Forgetting the idle gap (`clock += burst` only) produces negative waiting times. Returning results in arrival order instead of id order. Breaking arrival ties arbitrarily — the statement fixes them by id.",
        follow_up="Compute the average waiting time and observe the *convoy effect*: put one long job first and watch every short job behind it suffer.",
    ),
),
dict(
    id="os-sjf-scheduling",
    title="Shortest Job First (Non-preemptive)",
    difficulty="Medium",
    pattern="CPU Scheduling",
    entry="sjf",
    description=r"""
Simulate **non-preemptive shortest-job-first** on one CPU.

`procs[i] = [arrival, burst]`. Whenever the CPU becomes free, it picks, among the jobs that have
already arrived, the one with the smallest burst. Ties are broken by earlier arrival, then by smaller id.
Once started, a job runs to completion. If nothing has arrived, the CPU idles until the next arrival.

Return `[[waiting, turnaround], ...]` indexed by job id.

**Example:** `procs = [[0, 7], [1, 2], [2, 4], [3, 1]]` → `[[0, 7], [7, 9], [8, 12], [4, 5]]`
(run order: job 0, job 3, job 1, job 2).

**Constraints:** `0 ≤ len(procs) ≤ 10^4`, `burst ≥ 1`.
""",
    starter='''def sjf(procs):
    pass
''',
    solution='''import heapq

def sjf(procs):
    n = len(procs)
    order = sorted(range(n), key=lambda i: (procs[i][0], i))
    res = [None] * n
    ready, clock, k = [], 0, 0
    while k < n or ready:
        if not ready and procs[order[k]][0] > clock:
            clock = procs[order[k]][0]
        while k < n and procs[order[k]][0] <= clock:
            i = order[k]
            heapq.heappush(ready, (procs[i][1], procs[i][0], i))
            k += 1
        burst, arrival, i = heapq.heappop(ready)
        clock += burst
        res[i] = [clock - arrival - burst, clock - arrival]
    return res
''',
    tests=[
        [[[0, 7], [1, 2], [2, 4], [3, 1]]],
        [[[0, 3], [0, 1], [0, 2]]],
        [[]],
        [[[5, 5]]],
        [[[0, 2], [10, 3], [10, 1]]],
        [[[0, 4], [0, 4], [0, 4]]],
        [[[2, 6], [2, 6], [0, 6], [1, 6]]],
        [[[0, 10], [1, 9], [2, 8], [3, 1], [4, 1]]],
        [[[0, 1], [50, 5], [50, 2], [51, 1], [100, 3]]],
        [_procs(15)],
        [_procs(60, 100, 9)],
        [[[0, 5000 - i] for i in range(2000)]],
    ],
    examples=2,
    wrong_solutions=[
        '''def sjf(procs):
    order = sorted(range(len(procs)), key=lambda i: (procs[i][1], procs[i][0], i))
    res = [None] * len(procs)
    clock = 0
    for i in order:
        a, b = procs[i]
        clock = max(clock, a) + b
        res[i] = [clock - a - b, clock - a]
    return res
''',
        '''def sjf(procs):
    order = sorted(range(len(procs)), key=lambda i: (procs[i][0], i))
    res = [None] * len(procs)
    clock = 0
    for i in order:
        a, b = procs[i]
        clock = max(clock, a) + b
        res[i] = [clock - a - b, clock - a]
    return res
''',
    ],
    guide=dict(
        prereqs="FCFS simulation (previous problem), heaps / priority queues, the scheduling lesson's argument that shortest-first minimises mean turnaround.",
        intuition="The decision point is *the moment the CPU becomes free*. Only jobs that already exist can compete, so you need two structures: a list of future arrivals sorted by time, and a min-heap of ready jobs keyed by burst.",
        hints=[
            "Sorting everything by burst is wrong: a short job that has not arrived yet cannot be chosen.",
            "Maintain a pointer into the arrival-sorted list. Each time the clock moves, push every job with `arrival <= clock` into a heap.",
            "Heap key `(burst, arrival, id)` implements all three tie-break levels at once. If the heap is empty, jump the clock to the next arrival.",
        ],
        brute_force="At each decision scan every unfinished job, filter those that have arrived, and take the minimum: O(n) per decision, O(n²) overall. Perfectly fine for small n and a good way to check a heap solution.",
        approach="""1. Sort ids by `(arrival, id)`; set `clock = 0`.
2. Loop while jobs remain: if the heap is empty, jump `clock` to the next arrival. Push all arrived jobs.
3. Pop the smallest `(burst, arrival, id)`, advance the clock by its burst, record the result.

**Dry run** `[[0,7],[1,2],[2,4],[3,1]]`: at t=0 only job 0 is ready → runs to 7. At t=7 the heap holds bursts 2, 4, 1 → job 3 runs 7–8 (wait 4), job 1 runs 8–10 (wait 7), job 2 runs 10–14 (wait 8).""",
        complexity="Time O(n log n): one sort plus one push and one pop per job. Space O(n).",
        pitfalls="Sorting globally by burst (ignores arrivals). Forgetting to idle when the ready set is empty. Pushing arrivals only *before* jumping the clock, which leaves the heap empty and crashes on pop.",
        follow_up="Real systems do not know bursts in advance; they estimate them with exponential averaging of past bursts. Try feeding this simulator estimated bursts instead of true ones.",
    ),
),
dict(
    id="os-srtf-scheduling",
    title="Shortest Remaining Time First (Preemptive)",
    difficulty="Medium",
    pattern="CPU Scheduling",
    entry="srtf",
    description=r"""
Simulate **shortest-remaining-time-first**, the preemptive version of SJF.

`procs[i] = [arrival, burst]`. At every instant the CPU runs the arrived, unfinished job with the least
*remaining* time. Ties: earlier arrival first, then smaller id. Consequently a newly arrived job
preempts the running one only when its burst is **strictly** smaller than the running job's remaining time.

Return `[[waiting, turnaround], ...]` indexed by job id, where waiting = turnaround − burst.

**Example:** `procs = [[0, 8], [1, 4], [2, 2]]` → `[[6, 14], [2, 6], [0, 2]]`
(timeline: job 0 for 0–1, job 1 for 1–2, job 2 for 2–4, job 1 for 4–7, job 0 for 7–14).

**Constraints:** `0 ≤ len(procs) ≤ 10^4`, `burst ≥ 1`, times up to `10^9` (do not step one tick at a time).
""",
    starter='''def srtf(procs):
    pass
''',
    solution='''import heapq

def srtf(procs):
    n = len(procs)
    order = sorted(range(n), key=lambda i: (procs[i][0], i))
    done = [0] * n
    ready, clock, k, finished = [], 0, 0, 0
    while finished < n:
        while k < n and procs[order[k]][0] <= clock:
            i = order[k]
            heapq.heappush(ready, (procs[i][1], procs[i][0], i))
            k += 1
        if not ready:
            clock = procs[order[k]][0]
            continue
        rem, arrival, i = heapq.heappop(ready)
        nxt = procs[order[k]][0] if k < n else float("inf")
        run = min(rem, nxt - clock)
        clock += run
        if rem == run:
            done[i] = clock
            finished += 1
        else:
            heapq.heappush(ready, (rem - run, arrival, i))
    return [[done[i] - a - b, done[i] - a] for i, (a, b) in enumerate(procs)]
''',
    tests=[
        [[[0, 8], [1, 4], [2, 2]]],
        [[[0, 7], [2, 4], [4, 1], [5, 4]]],
        [[]],
        [[[3, 3]]],
        [[[0, 5], [5, 5]]],
        [[[0, 4], [1, 3]]],
        [[[0, 4], [1, 2]]],
        [[[0, 3], [0, 3], [0, 1]]],
        [[[0, 10], [1, 1], [2, 1], [3, 1], [4, 1]]],
        [[[0, 1], [100, 6], [102, 2], [103, 1]]],
        [[[0, 1000000000], [1, 5], [999, 3]]],
        [_procs(14)],
        [_procs(80, 150, 9)],
    ],
    examples=2,
    wrong_solutions=[
        '''import heapq

def srtf(procs):
    n = len(procs)
    order = sorted(range(n), key=lambda i: (procs[i][0], i))
    res = [None] * n
    ready, clock, k = [], 0, 0
    while k < n or ready:
        if not ready and procs[order[k]][0] > clock:
            clock = procs[order[k]][0]
        while k < n and procs[order[k]][0] <= clock:
            i = order[k]
            heapq.heappush(ready, (procs[i][1], procs[i][0], i))
            k += 1
        burst, arrival, i = heapq.heappop(ready)
        clock += burst
        res[i] = [clock - arrival - burst, clock - arrival]
    return res
''',
        '''import heapq

def srtf(procs):
    n = len(procs)
    order = sorted(range(n), key=lambda i: (procs[i][0], i))
    done = [0] * n
    ready, clock, k, finished = [], 0, 0, 0
    while finished < n:
        while k < n and procs[order[k]][0] <= clock:
            i = order[k]
            heapq.heappush(ready, (procs[i][1], -procs[i][0], i))
            k += 1
        if not ready:
            clock = procs[order[k]][0]
            continue
        rem, arrival, i = heapq.heappop(ready)
        nxt = procs[order[k]][0] if k < n else float("inf")
        run = min(rem, nxt - clock)
        clock += run
        if rem == run:
            done[i] = clock
            finished += 1
        else:
            heapq.heappush(ready, (rem - run, arrival, i))
    return [[done[i] - a - b, done[i] - a] for i, (a, b) in enumerate(procs)]
''',
    ],
    guide=dict(
        prereqs="Non-preemptive SJF, heaps, event-driven simulation (jumping between interesting instants instead of ticking).",
        intuition="The schedule can only change at two kinds of instants: a job arrives, or the running job finishes. Between two such events the choice is fixed, so run the current best job until whichever event comes first.",
        hints=[
            "Keep a heap of `(remaining, arrival, id)` for ready jobs and a pointer into the arrival-sorted list.",
            "Pop the best job and let it run for `min(remaining, next_arrival - clock)` time units.",
            "If it did not finish, push it back with its reduced remaining time. The heap then decides whether the newcomer preempts it.",
        ],
        brute_force="Tick one unit at a time, choosing the minimum-remaining job each tick. O(total time × n) — hopeless when a burst is 10⁹, but an excellent oracle for small random tests.",
        approach="""1. Sort ids by arrival. `clock = 0`.
2. Push all jobs with `arrival <= clock`. If none are ready, jump to the next arrival.
3. Pop the minimum; compute `run = min(rem, next_arrival - clock)`; advance the clock.
4. Finished → record completion. Otherwise push back `(rem - run, arrival, id)`.

**Dry run** `[[0,8],[1,4],[2,2]]`: t=0 job 0 runs 1 unit (rem 7). t=1 heap {(7,j0),(4,j1)} → j1 runs 1 unit (rem 3). t=2 heap {(7,j0),(3,j1),(2,j2)} → j2 runs 2, done at 4. j1 runs 3, done at 7. j0 runs 7, done at 14.""",
        complexity="The loop body runs at most 2n times (each iteration either finishes a job or consumes an arrival), so O(n log n) time and O(n) space.",
        pitfalls="Preempting on ties (causes useless context switches and different answers). Ticking unit by unit and timing out. Computing waiting as `start - arrival`, which is wrong once a job can be interrupted — use `turnaround - burst`.",
        follow_up="Count context switches, then add a switch cost and see when SRTF stops beating SJF.",
    ),
),
dict(
    id="os-round-robin",
    title="Round Robin: Build the Gantt Chart",
    difficulty="Medium",
    pattern="CPU Scheduling",
    entry="round_robin",
    description=r"""
Simulate **round-robin** scheduling with time slice `quantum` and return the Gantt chart.

`procs[i] = [arrival, burst]`. The ready queue is FIFO. The job at the head runs for
`min(quantum, remaining)` time units. When its slice ends:

1. every job that arrived **during or exactly at the end of** the slice joins the queue (by arrival, then id),
2. *then* the job that just ran rejoins the tail if it still has work left.

If the queue is empty the CPU idles until the next arrival.

Return a list of slices `[id, start, end]` in execution order. Do **not** merge consecutive slices of the same job.

**Example:** `procs = [[0, 5], [1, 3]], quantum = 2` →
`[[0,0,2],[1,2,4],[0,4,6],[1,6,7],[0,7,8]]`

**Constraints:** `0 ≤ len(procs) ≤ 2000`, `burst ≥ 1`, `quantum ≥ 1`.
""",
    starter='''def round_robin(procs, quantum):
    pass
''',
    solution='''from collections import deque

def round_robin(procs, quantum):
    n = len(procs)
    order = sorted(range(n), key=lambda i: (procs[i][0], i))
    rem = [b for _, b in procs]
    queue, out = deque(), []
    clock = k = 0
    while k < n or queue:
        if not queue:
            clock = max(clock, procs[order[k]][0])
        while k < n and procs[order[k]][0] <= clock:
            queue.append(order[k])
            k += 1
        i = queue.popleft()
        run = min(quantum, rem[i])
        out.append([i, clock, clock + run])
        clock += run
        rem[i] -= run
        while k < n and procs[order[k]][0] <= clock:
            queue.append(order[k])
            k += 1
        if rem[i]:
            queue.append(i)
    return out
''',
    tests=[
        [[[0, 5], [1, 3]], 2],
        [[[0, 4], [0, 4], [0, 4]], 3],
        [[], 4],
        [[[2, 7]], 3],
        [[[0, 2], [2, 2]], 2],
        [[[0, 3], [2, 1], [2, 1]], 2],
        [[[0, 1], [9, 2], [9, 5]], 2],
        [[[0, 10], [1, 1]], 100],
        [[[5, 3], [0, 6], [1, 2]], 1],
        [[[0, 6], [3, 2]], 3],
        [_procs(10), 3],
        [_procs(30, 40, 9), 4],
        [[[0, 50]] * 30, 7],
    ],
    examples=2,
    wrong_solutions=[
        '''from collections import deque

def round_robin(procs, quantum):
    n = len(procs)
    order = sorted(range(n), key=lambda i: (procs[i][0], i))
    rem = [b for _, b in procs]
    queue, out = deque(), []
    clock = k = 0
    while k < n or queue:
        if not queue:
            clock = max(clock, procs[order[k]][0])
        while k < n and procs[order[k]][0] <= clock:
            queue.append(order[k])
            k += 1
        i = queue.popleft()
        run = min(quantum, rem[i])
        out.append([i, clock, clock + run])
        clock += run
        rem[i] -= run
        if rem[i]:
            queue.append(i)
    return out
''',
        '''from collections import deque

def round_robin(procs, quantum):
    queue = deque(sorted(range(len(procs)), key=lambda i: (procs[i][0], i)))
    rem = [b for _, b in procs]
    out, clock = [], 0
    while queue:
        i = queue.popleft()
        clock = max(clock, procs[i][0])
        run = min(quantum, rem[i])
        out.append([i, clock, clock + run])
        clock += run
        rem[i] -= run
        if rem[i]:
            queue.append(i)
    return out
''',
    ],
    guide=dict(
        prereqs="Queues (`collections.deque`), FCFS simulation, the idea of a time quantum.",
        intuition="Round robin is FCFS with a timer. The entire subtlety is the *order of two enqueues* at the end of a slice: newcomers first, the preempted job second. Get that order right and everything else is bookkeeping.",
        hints=[
            "Keep arrivals in a sorted list with a pointer, and the ready jobs in a deque.",
            "After advancing the clock past a slice, admit every job with `arrival <= clock` before deciding what to do with the job that just ran.",
            "If the deque is empty but jobs remain, jump the clock forward to the next arrival instead of looping.",
        ],
        brute_force="Tick one time unit at a time with a per-job counter of how much of the quantum has been used. Correct but O(total burst) steps with fiddly state; the slice-at-a-time version is both shorter and faster.",
        approach="""1. `clock = 0`, pointer `k = 0` into arrival order, empty deque.
2. If the deque is empty, set `clock` to the next arrival. Admit all arrived jobs.
3. Pop the head, run `min(quantum, rem)`, append `[id, clock, clock+run]`, advance the clock.
4. Admit arrivals with `arrival <= clock`, then re-append the job if unfinished.

**Dry run** `[[0,3],[2,1],[2,1]]`, q=2: slice `[0,0,2]`; at t=2 jobs 1 and 2 arrive and enter *before* job 0 → queue [1,2,0]. Slices `[1,2,3]`, `[2,3,4]`, `[0,4,5]`.""",
        complexity="The number of slices is S = Σ⌈burst/quantum⌉. Time O(n log n + S), space O(n + S) for the output.",
        pitfalls="Re-queuing the preempted job before admitting newcomers. Seeding the queue with all jobs regardless of arrival. Merging adjacent slices when the statement says not to. Infinite loop when the queue is empty and you forget to jump the clock.",
        follow_up="Derive waiting times from the chart. Then plot average turnaround against the quantum: very small quanta drown in switches, very large ones degenerate into FCFS.",
    ),
),
dict(
    id="os-priority-scheduling",
    title="Preemptive Priority Scheduling",
    difficulty="Medium",
    pattern="CPU Scheduling",
    entry="priority_schedule",
    description=r"""
Simulate **preemptive priority scheduling**.

`procs[i] = [arrival, burst, priority]`, and a **smaller number means higher priority**. At every instant
the CPU runs the arrived, unfinished job with the best priority; among equals the one that arrived
earlier wins, then the smaller id (so equal-priority jobs are served FCFS, with no time slicing).
A newcomer preempts only if its priority is strictly better.

Return `[[waiting, turnaround], ...]` indexed by job id.

**Example:** `procs = [[0, 5, 2], [1, 2, 0], [2, 3, 2]]` → `[[2, 7], [0, 2], [5, 8]]`
(job 0 runs 0–1, job 1 preempts for 1–3, job 0 resumes 3–7, job 2 runs 7–10).

**Constraints:** `0 ≤ len(procs) ≤ 10^4`, `burst ≥ 1`, times up to `10^9`.
""",
    starter='''def priority_schedule(procs):
    pass
''',
    solution='''import heapq

def priority_schedule(procs):
    n = len(procs)
    order = sorted(range(n), key=lambda i: (procs[i][0], i))
    rem = [p[1] for p in procs]
    done = [0] * n
    ready, clock, k, finished = [], 0, 0, 0
    while finished < n:
        while k < n and procs[order[k]][0] <= clock:
            i = order[k]
            heapq.heappush(ready, (procs[i][2], procs[i][0], i))
            k += 1
        if not ready:
            clock = procs[order[k]][0]
            continue
        prio, arrival, i = ready[0]
        nxt = procs[order[k]][0] if k < n else float("inf")
        run = min(rem[i], nxt - clock)
        clock += run
        rem[i] -= run
        if rem[i] == 0:
            heapq.heappop(ready)
            done[i] = clock
            finished += 1
    return [[done[i] - p[0] - p[1], done[i] - p[0]] for i, p in enumerate(procs)]
''',
    tests=[
        [[[0, 5, 2], [1, 2, 0], [2, 3, 2]]],
        [[[0, 4, 1], [0, 3, 1], [0, 2, 0]]],
        [[]],
        [[[6, 2, 9]]],
        [[[0, 3, 1], [1, 3, 1]]],
        [[[0, 10, 5], [2, 1, 4], [3, 1, 3], [4, 1, 2]]],
        [[[0, 2, 0], [20, 4, 3], [21, 1, 3], [22, 2, 1]]],
        [[[0, 6, 3], [1, 2, 3], [2, 2, 3]]],
        [[[0, 1000000000, 9], [5, 5, 1]]],
        [[[3, 4, 2], [0, 8, 4], [3, 1, 2], [5, 2, 0]]],
        [_procs_prio(12)],
        [_procs_prio(70)],
    ],
    examples=2,
    wrong_solutions=[
        '''import heapq

def priority_schedule(procs):
    n = len(procs)
    order = sorted(range(n), key=lambda i: (procs[i][0], i))
    res = [None] * n
    ready, clock, k = [], 0, 0
    while k < n or ready:
        if not ready and procs[order[k]][0] > clock:
            clock = procs[order[k]][0]
        while k < n and procs[order[k]][0] <= clock:
            i = order[k]
            heapq.heappush(ready, (procs[i][2], procs[i][0], i))
            k += 1
        prio, arrival, i = heapq.heappop(ready)
        clock += procs[i][1]
        res[i] = [clock - arrival - procs[i][1], clock - arrival]
    return res
''',
        '''import heapq

def priority_schedule(procs):
    n = len(procs)
    order = sorted(range(n), key=lambda i: (procs[i][0], i))
    rem = [p[1] for p in procs]
    done = [0] * n
    ready, clock, k, finished = [], 0, 0, 0
    while finished < n:
        while k < n and procs[order[k]][0] <= clock:
            i = order[k]
            heapq.heappush(ready, (-procs[i][2], procs[i][0], i))
            k += 1
        if not ready:
            clock = procs[order[k]][0]
            continue
        prio, arrival, i = ready[0]
        nxt = procs[order[k]][0] if k < n else float("inf")
        run = min(rem[i], nxt - clock)
        clock += run
        rem[i] -= run
        if rem[i] == 0:
            heapq.heappop(ready)
            done[i] = clock
            finished += 1
    return [[done[i] - p[0] - p[1], done[i] - p[0]] for i, p in enumerate(procs)]
''',
    ],
    guide=dict(
        prereqs="SRTF simulation (the structure is identical), heaps with tuple keys.",
        intuition="Replace *remaining time* in SRTF with a fixed priority number. Because the key of a job never changes while it runs, you can leave it at the top of the heap and only pop it when it finishes.",
        hints=[
            "The heap key is `(priority, arrival, id)`; none of these change over time.",
            "Peek at the top, run it until it finishes or until the next arrival, whichever is sooner.",
            "After the next arrival is pushed, simply peek again — if the newcomer is better it is now on top, which *is* the preemption.",
        ],
        brute_force="Unit-time ticking, scanning all jobs each tick for the best arrived one: O(T·n). Useful as a checker on tiny inputs only.",
        approach="""1. Sort ids by arrival; keep `rem[i]`.
2. Admit arrivals up to `clock`; if none ready, jump the clock.
3. Peek the best job; `run = min(rem, next_arrival - clock)`; update clock and rem; pop only when rem hits zero.

**Dry run** `[[0,5,2],[1,2,0],[2,3,2]]`: job 0 runs 0–1 (rem 4). Job 1 (prio 0) arrives, tops the heap, runs 1–2, then job 2 arrives (prio 2, not better), job 1 finishes at 3. Top is job 0 (earlier arrival than job 2) → 3–7. Job 2 → 7–10.""",
        complexity="O(n log n) time — each job is pushed and popped once, and the loop body runs at most 2n times. O(n) space.",
        pitfalls="Reversing the priority convention. Rotating equal-priority jobs (that is priority + round robin, a different policy). Forgetting that a low-priority job may wait forever in a real system — *starvation* — which is why real schedulers add aging.",
        follow_up="Add aging: every T time units a waiting job's priority number drops by one. How does the worst-case wait change?",
    ),
),
dict(
    id="os-mlfq",
    title="Multilevel Feedback Queue",
    difficulty="Hard",
    pattern="CPU Scheduling",
    entry="mlfq",
    description=r"""
Simulate a simplified **multilevel feedback queue** (MLFQ).

There are `len(quanta)` FIFO queues; level 0 is the highest priority and level `L-1` the lowest.
`quanta[l]` is the time slice used at level `l`. `procs[i] = [arrival, burst]`.

Rules:

- A newly arrived job enters level 0.
- The scheduler always takes the head of the highest-priority non-empty queue and runs it for
  `min(quanta[level], remaining)` time units. Slices are **not** interrupted by arrivals (decisions happen only at slice boundaries).
- At the end of a slice, first admit every job with `arrival <= now` to level 0 (by arrival, then id).
  Then, if the job that ran is unfinished, it is demoted to the next lower level (the bottom level
  feeds back into itself, giving round robin there).
- If all queues are empty, the CPU idles until the next arrival.

Return the list of completion times indexed by job id.

**Example:** `procs = [[0, 6], [0, 2]], quanta = [2, 4]` → `[8, 4]`
(job 0 runs 0–2 and is demoted; job 1 runs 2–4 and finishes; job 0 runs 4–8 at level 1).

**Constraints:** `0 ≤ len(procs) ≤ 2000`, `1 ≤ len(quanta) ≤ 8`, all quanta and bursts `≥ 1`.
""",
    starter='''def mlfq(procs, quanta):
    pass
''',
    solution='''from collections import deque

def mlfq(procs, quanta):
    n, levels = len(procs), len(quanta)
    order = sorted(range(n), key=lambda i: (procs[i][0], i))
    rem = [b for _, b in procs]
    done = [0] * n
    queues = [deque() for _ in range(levels)]
    clock = k = 0
    left = n
    while left:
        while k < n and procs[order[k]][0] <= clock:
            queues[0].append(order[k])
            k += 1
        lvl = next((l for l in range(levels) if queues[l]), None)
        if lvl is None:
            clock = procs[order[k]][0]
            continue
        i = queues[lvl].popleft()
        run = min(quanta[lvl], rem[i])
        clock += run
        rem[i] -= run
        while k < n and procs[order[k]][0] <= clock:
            queues[0].append(order[k])
            k += 1
        if rem[i] == 0:
            done[i] = clock
            left -= 1
        else:
            queues[min(lvl + 1, levels - 1)].append(i)
    return done
''',
    tests=[
        [[[0, 6], [0, 2]], [2, 4]],
        [[[0, 10], [3, 1]], [2, 4, 8]],
        [[], [1]],
        [[[4, 3]], [1, 1]],
        [[[0, 5], [0, 5]], [2]],
        [[[0, 3], [2, 3]], [2]],
        [[[0, 20], [1, 2], [2, 2], [3, 2]], [2, 4, 8]],
        [[[0, 1], [30, 9], [31, 1]], [3, 3]],
        [[[0, 7], [0, 7], [0, 7]], [1, 2, 100]],
        [[[0, 9], [1, 9], [20, 1]], [4, 4]],
        [_procs(12), [2, 4, 8]],
        [_procs(40, 60, 9), [1, 2, 3, 4]],
        [_procs(25, 10, 9), [3]],
    ],
    examples=2,
    wrong_solutions=[
        '''from collections import deque

def mlfq(procs, quanta):
    n, levels = len(procs), len(quanta)
    order = sorted(range(n), key=lambda i: (procs[i][0], i))
    rem = [b for _, b in procs]
    done = [0] * n
    queues = [deque() for _ in range(levels)]
    clock = k = 0
    left = n
    while left:
        while k < n and procs[order[k]][0] <= clock:
            queues[0].append(order[k])
            k += 1
        lvl = next((l for l in range(levels) if queues[l]), None)
        if lvl is None:
            clock = procs[order[k]][0]
            continue
        i = queues[lvl].popleft()
        run = min(quanta[lvl], rem[i])
        clock += run
        rem[i] -= run
        while k < n and procs[order[k]][0] <= clock:
            queues[0].append(order[k])
            k += 1
        if rem[i] == 0:
            done[i] = clock
            left -= 1
        else:
            queues[lvl].append(i)
    return done
''',
        '''from collections import deque

def mlfq(procs, quanta):
    n, levels = len(procs), len(quanta)
    order = sorted(range(n), key=lambda i: (procs[i][0], i))
    rem = [b for _, b in procs]
    done = [0] * n
    queues = [deque() for _ in range(levels)]
    clock = k = 0
    left = n
    while left:
        while k < n and procs[order[k]][0] <= clock:
            queues[0].append(order[k])
            k += 1
        lvl = next((l for l in range(levels) if queues[l]), None)
        if lvl is None:
            clock = procs[order[k]][0]
            continue
        i = queues[lvl].popleft()
        run = min(quanta[lvl], rem[i])
        clock += run
        rem[i] -= run
        if rem[i] == 0:
            done[i] = clock
            left -= 1
        else:
            queues[min(lvl + 1, levels - 1)].append(i)
    return done
''',
    ],
    guide=dict(
        prereqs="Round-robin simulation, the scheduling lesson's discussion of multiple queues and why CPU-bound jobs sink.",
        intuition="MLFQ learns a job's nature by watching it. A job that burns a whole slice looks CPU-bound and is pushed down to a level with longer but rarer slices; short interactive jobs finish near the top. The simulation is round robin with an array of queues instead of one.",
        hints=[
            "Use a list of deques. Picking the next job is a scan for the first non-empty level.",
            "Reuse the round-robin skeleton: admit arrivals, run one slice, admit arrivals again, then demote or retire.",
            "The demotion target is `min(level + 1, L - 1)`; the clamp is what makes the last level a round robin.",
        ],
        brute_force="Tick-by-tick simulation with per-job 'slice used so far' counters. It handles the rules but is slower and far easier to get wrong at slice boundaries.",
        approach="""1. Sort ids by arrival; create `L` deques; `clock = 0`.
2. Admit arrivals to level 0. Find the highest non-empty level; if none, jump the clock.
3. Run the head for `min(quanta[level], rem)`. Admit arrivals up to the new clock.
4. Finished → record. Otherwise append to `min(level+1, L-1)`.

**Dry run** `[[0,10],[3,1]]`, quanta `[2,4,8]`: job 0 runs 0–2 → level 1. Level 0 empty, so job 0 runs 2–6 at level 1 (job 1 arrives at 3 but cannot interrupt) → level 2. Job 1 runs 6–7, done. Job 0 runs 7–11, done. Answer `[11, 7]`.""",
        complexity="Each slice costs O(L) to find a queue. With S slices in total: O(n log n + S·L) time, O(n) space.",
        pitfalls="Putting the demoted job back in the same level. Forgetting that the bottom level recycles. Skipping the second 'admit arrivals' step, which lets a demoted job jump ahead in the single-level case. Preempting mid-slice when the statement forbids it.",
        follow_up="Real MLFQs add a periodic *priority boost* that moves everything back to level 0 to prevent starvation and to forgive jobs whose behaviour changed. Add a boost every B time units.",
    ),
),
]
