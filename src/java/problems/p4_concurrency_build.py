"""Java track, model problems part 4: enums as state machines, concurrency models, money, imports, Maven."""


def G(prereqs, intuition, hints, brute, approach, complexity, pitfalls, follow_up=None):
    d = dict(prereqs=prereqs, intuition=intuition, hints=hints, brute_force=brute, approach=approach,
             complexity=complexity, pitfalls=pitfalls)
    if follow_up:
        d["follow_up"] = follow_up
    return d


PROBLEMS = [
# ------------------------------------------------------------------ java-enum-state-machine
dict(
    id="java-enum-state-machine",
    title="Enum state machine",
    difficulty="Medium",
    pattern="Java enums",
    entry="run_machine",
    description=r"""
An enum with a transition table is the standard way to model a process such as an order's life cycle.

`transitions` maps each state name to the list of states it may move to (every state appears as a key; a
state with an empty list is **terminal**).

Write `run_machine(transitions, start, events)`. `events` is a list of requested target states, processed
in order from the state `start`:

- if the target is **not a state at all**, the result for that event is `"unknown"` and the state is unchanged
  (in Java this would be `Enum.valueOf` throwing `IllegalArgumentException`);
- if the current state may move to the target, the result is `"ok"` and the state changes;
- otherwise the result is `"rejected"` and the state is unchanged.

Return `[final_state, results, is_terminal]`, where `is_terminal` says whether the final state has no
outgoing transitions.

**Example** with `NEW → [PAID, CANCELLED]`, `PAID → [SHIPPED, CANCELLED]`, `SHIPPED → [DELIVERED]`,
`DELIVERED → []`, `CANCELLED → []`:
`run_machine(t, "NEW", ["PAID", "DELIVERED", "SHIPPED", "REFUNDED"])` → `["SHIPPED", ["ok", "rejected", "ok", "unknown"], False]`
""",
    starter='''def run_machine(transitions, start, events):
    pass
''',
    solution='''def run_machine(transitions, start, events):
    state = start
    results = []
    for target in events:
        if target not in transitions:
            results.append("unknown")
        elif target in transitions[state]:
            results.append("ok")
            state = target
        else:
            results.append("rejected")
    return [state, results, len(transitions[state]) == 0]
''',
    tests=[
        [{"NEW": ["PAID", "CANCELLED"], "PAID": ["SHIPPED", "CANCELLED"], "SHIPPED": ["DELIVERED"], "DELIVERED": [], "CANCELLED": []},
         "NEW", ["PAID", "DELIVERED", "SHIPPED", "REFUNDED"]],
        [{"NEW": ["PAID", "CANCELLED"], "PAID": ["SHIPPED", "CANCELLED"], "SHIPPED": ["DELIVERED"], "DELIVERED": [], "CANCELLED": []},
         "NEW", []],
        [{"NEW": ["PAID", "CANCELLED"], "PAID": ["SHIPPED", "CANCELLED"], "SHIPPED": ["DELIVERED"], "DELIVERED": [], "CANCELLED": []},
         "NEW", ["CANCELLED", "PAID", "NEW"]],
        [{"NEW": ["PAID", "CANCELLED"], "PAID": ["SHIPPED", "CANCELLED"], "SHIPPED": ["DELIVERED"], "DELIVERED": [], "CANCELLED": []},
         "NEW", ["PAID", "SHIPPED", "DELIVERED"]],
        [{"NEW": ["PAID", "CANCELLED"], "PAID": ["SHIPPED", "CANCELLED"], "SHIPPED": ["DELIVERED"], "DELIVERED": [], "CANCELLED": []},
         "DELIVERED", ["NEW"]],
        [{"NEW": ["PAID", "CANCELLED"], "PAID": ["SHIPPED", "CANCELLED"], "SHIPPED": ["DELIVERED"], "DELIVERED": [], "CANCELLED": []},
         "NEW", ["NEW", "new", "PAID"]],
        [{"RED": ["GREEN"], "GREEN": ["AMBER"], "AMBER": ["RED"]}, "RED", ["GREEN", "AMBER", "RED", "GREEN", "RED"]],
        [{"ON": ["OFF", "ON"], "OFF": ["ON"]}, "ON", ["ON", "ON", "OFF", "OFF", "ON"]],
        [{"ONLY": []}, "ONLY", ["ONLY", "OTHER"]],
        [{"A": ["B"], "B": ["C"], "C": []}, "A", ["C", "B", "A", "C", "C"]],
        [{"A": ["B"], "B": ["C"], "C": []}, "B", ["X", "Y", "Z"]],
    ],
    wrong_solutions=[
        '''def run_machine(transitions, start, events):
    state, results = start, []
    for target in events:
        if target in transitions.get(state, []):
            results.append("ok"); state = target
        else:
            results.append("rejected")
    return [state, results, len(transitions[state]) == 0]
''',
        '''def run_machine(transitions, start, events):
    state, results = start, []
    for target in events:
        if target not in transitions:
            results.append("unknown")
        elif target in transitions[state]:
            results.append("ok")
        else:
            results.append("rejected")
        state = target if target in transitions else state
    return [state, results, len(transitions[state]) == 0]
''',
    ],
    guide=G(
        "Lesson *Enums: constants with data and behaviour*: the state machine built from an enum and `EnumSet`.",
        "Keep one current state. For each request there are three possibilities, tested in a fixed order: the "
        "target does not exist; the move is allowed; the move is not allowed.",
        ["Check 'is it a state?' before anything else.", "Only an allowed move changes the current state.",
         "Terminal means the final state's transition list is empty."],
        "A chain of `if (state == NEW && target == PAID) ...` statements grows with every state and is where "
        "forgotten cases hide. A table (map from state to allowed targets) scales and can be printed.",
        r"""**Dry run** of the example from `NEW`: `PAID` allowed → state `PAID`. `DELIVERED` is a state but not
reachable from `PAID` → rejected. `SHIPPED` allowed → state `SHIPPED`. `REFUNDED` is not a state → unknown.
Final `SHIPPED`, which can still move to `DELIVERED`, so not terminal.

```java
enum OrderState {
    NEW, PAID, SHIPPED, DELIVERED, CANCELLED;

    private Set<OrderState> next = EnumSet.noneOf(OrderState.class);

    static {                                     // set up after all constants exist
        NEW.next = EnumSet.of(PAID, CANCELLED);
        PAID.next = EnumSet.of(SHIPPED, CANCELLED);
        SHIPPED.next = EnumSet.of(DELIVERED);
    }

    boolean canMoveTo(OrderState target) { return next.contains(target); }
    boolean isTerminal()                 { return next.isEmpty(); }
}

OrderState state = OrderState.NEW;
OrderState target = OrderState.valueOf("PAID");      // IllegalArgumentException for an unknown name
if (state.canMoveTo(target)) state = target;
```""",
        "Time O(events × out-degree), or O(events) with sets; space O(events) for the results.",
        "- Moving to the target even when the transition is rejected.\n- Reporting an unknown state as rejected.\n"
        "- Allowing a self-transition that the table does not list.",
    ),
),
# ------------------------------------------------------------------ java-interleaving-counter
dict(
    id="java-interleaving-counter",
    title="Race condition: every possible final count",
    difficulty="Hard",
    pattern="Java concurrency",
    entry="possible_totals",
    description=r"""
`counter++` is not atomic. Each increment is two steps on shared memory:

1. **read** the shared counter into a thread-private temporary;
2. **write** `temporary + 1` back to the shared counter.

`threads` threads each perform `increments` increments, with no synchronisation. The scheduler may switch
threads between **any** two steps. Each thread executes its own steps in order.

Write `possible_totals(threads, increments)` returning the **sorted** list of every final counter value
that some interleaving can produce. The counter starts at 0.

Constraints: `1 <= threads <= 3`, `0 <= increments <= 4`, and the total number of steps is at most 16.

**Examples** `possible_totals(1, 3)` → `[3]`; `possible_totals(2, 1)` → `[1, 2]`;
`possible_totals(2, 2)` → `[2, 3, 4]`.
""",
    starter='''def possible_totals(threads, increments):
    pass
''',
    solution='''def possible_totals(threads, increments):
    steps = increments * 2
    seen = set()
    finals = set()
    start = (0, tuple((0, 0) for _ in range(threads)))
    stack = [start]
    while stack:
        state = stack.pop()
        if state in seen:
            continue
        seen.add(state)
        shared, ts = state
        done = True
        for i, (pc, tmp) in enumerate(ts):
            if pc == steps:
                continue
            done = False
            if pc % 2 == 0:
                nxt = (shared, ts[:i] + ((pc + 1, shared),) + ts[i + 1:])
            else:
                nxt = (tmp + 1, ts[:i] + ((pc + 1, 0),) + ts[i + 1:])
            stack.append(nxt)
        if done:
            finals.add(shared)
    return sorted(finals)
''',
    tests=[
        [1, 3],
        [2, 1],
        [2, 2],
        [3, 1],
        [1, 0],
        [3, 0],
        [2, 3],
        [2, 4],
        [3, 2],
        [1, 1],
        [1, 4],
    ],
    wrong_solutions=[
        '''def possible_totals(threads, increments):
    return [threads * increments]
''',
        '''def possible_totals(threads, increments):
    if increments == 0:
        return [0]
    return list(range(increments, threads * increments + 1))
''',
        '''def possible_totals(threads, increments):
    if increments == 0:
        return [0]
    return list(range(1, threads * increments + 1))
''',
    ],
    guide=G(
        "Lesson *Race conditions, synchronization, deadlock and virtual threads*: the lost update.",
        "The program's state is the shared counter plus, for each thread, how far it has got and what it holds "
        "in its temporary. From any state, any unfinished thread may take the next step. Explore every reachable "
        "state and collect the counter values of the finished ones.",
        ["Represent a state as `(shared, ((pc, tmp), ...))` so it can go in a set.",
         "An even `pc` is a read (copy shared into tmp); an odd `pc` is a write (shared = tmp + 1).",
         "Use a visited set: many interleavings lead to the same state, and without it the search explodes."],
        "Enumerate every ordering of the steps (all ways to interleave the threads' step sequences) and simulate "
        "each one. For 2 threads × 4 increments that is 12,870 orderings; for 3 × 2 it is 90,720. The state-space "
        "search visits far fewer states because orderings that reach the same state are merged.",
        r"""**Dry run** `possible_totals(2, 1)`: steps per thread are R then W.

- A.R, A.W, B.R, B.W → A writes 1, B reads 1 and writes 2 → **2**.
- A.R, B.R, A.W, B.W → both read 0, both write 1 → **1** (a lost update).

So `[1, 2]`. For 2 threads × 2 increments the minimum is **2**, not 1 or 2-per-thread: one thread's stale
write can wipe out all but one of the other's increments, and then be overtaken in turn.

```java
class Unsafe { int count; void inc() { count++; } }                 // read, add, write: a race

class Safe {
    private final java.util.concurrent.atomic.AtomicInteger count = new java.util.concurrent.atomic.AtomicInteger();
    void inc() { count.incrementAndGet(); }                         // one atomic step
    int get()  { return count.get(); }
}

class AlsoSafe {
    private int count;
    synchronized void inc() { count++; }                            // mutual exclusion
    synchronized int get()  { return count; }
}
```""",
        "The number of states is at most (max counter + 1) × (steps + 1)^threads × (max tmp + 1)^threads; a few "
        "thousand for the allowed sizes. Time and space are proportional to the states visited.",
        "- Assuming the only outcomes are 'all increments' and 'one thread's worth'.\n"
        "- Treating the increment as a single step.\n- Exploring without memoisation.\n"
        "- Forgetting the zero-increment case, whose only result is 0.",
        "With `synchronized` or `AtomicInteger` the only possible total is `threads × increments`.",
    ),
),
# ------------------------------------------------------------------ java-deadlock-detect
dict(
    id="java-deadlock-detect",
    title="Deadlock risk: lock-order inversion",
    difficulty="Hard",
    pattern="Java concurrency",
    entry="lock_cycle",
    description=r"""
Two threads can deadlock when one takes lock A then B while another takes B then A. Tools detect this risk
from recorded **traces** by building a **lock-order graph**.

`traces` is a list with one entry per thread; each entry is that thread's sequence of
`["lock", name]` and `["unlock", name]` events, in order. Locks are **reentrant**: locking a lock the thread
already holds adds nothing, and you may assume each such extra lock is matched by an extra unlock (keep a
count per lock).

**Graph.** Whenever a thread acquires a lock `B` that it does not already hold, add an edge `A → B` for every
lock `A` it currently holds. Edges from all threads go into one graph.

**Self-inflicted cycles do not count.** An inversion needs two threads. Record, for every edge, the set of
threads that produced it. There is a deadlock risk if the graph has a cycle `L1 → L2 → ... → Lk → L1`
(k ≥ 2) and the **union** of the thread sets of that cycle's edges contains at least two different threads.

Write `lock_cycle(traces)` returning `True` if such a cycle exists, else `False`.

**Example** thread 0: lock pen, lock paper, unlock paper, unlock pen; thread 1: lock paper, lock pen, unlock
pen, unlock paper → `True`.
""",
    starter='''def lock_cycle(traces):
    pass
''',
    solution='''def lock_cycle(traces):
    edges = {}                                   # (a, b) -> set of thread ids
    for tid, trace in enumerate(traces):
        held = {}
        order = []
        for kind, name in trace:
            if kind == "lock":
                if held.get(name, 0) == 0:
                    for a in order:
                        edges.setdefault((a, name), set()).add(tid)
                    order.append(name)
                held[name] = held.get(name, 0) + 1
            else:
                held[name] = held.get(name, 0) - 1
                if held[name] == 0:
                    order.remove(name)
    adj = {}
    for (a, b) in edges:
        adj.setdefault(a, []).append(b)
    nodes = sorted(set(adj) | {b for bs in adj.values() for b in bs})

    # Search for a cycle, carrying the set of threads that contributed an edge along the path.
    # A cycle is risky when at least two different threads appear among its edges.
    def dfs(start, node, threads_seen, visited):
        for nxt in adj.get(node, []):
            u = threads_seen | edges[(node, nxt)]
            if nxt == start:
                if len(u) >= 2:
                    return True
                continue
            if nxt in visited:
                continue
            if dfs(start, nxt, u, visited | {nxt}):
                return True
        return False

    for s in nodes:
        if dfs(s, s, set(), {s}):
            return True
    return False
''',
    tests=[
        [[[["lock", "pen"], ["lock", "paper"], ["unlock", "paper"], ["unlock", "pen"]],
          [["lock", "paper"], ["lock", "pen"], ["unlock", "pen"], ["unlock", "paper"]]]],
        [[[["lock", "pen"], ["lock", "paper"], ["unlock", "paper"], ["unlock", "pen"]],
          [["lock", "pen"], ["lock", "paper"], ["unlock", "paper"], ["unlock", "pen"]]]],
        [[[["lock", "a"], ["lock", "b"], ["unlock", "b"], ["unlock", "a"], ["lock", "b"], ["lock", "a"], ["unlock", "a"], ["unlock", "b"]]]],
        [[]],
        [[[], []]],
        [[[["lock", "a"], ["unlock", "a"], ["lock", "b"], ["unlock", "b"]],
          [["lock", "b"], ["unlock", "b"], ["lock", "a"], ["unlock", "a"]]]],
        [[[["lock", "a"], ["lock", "b"], ["unlock", "b"], ["unlock", "a"]],
          [["lock", "b"], ["lock", "c"], ["unlock", "c"], ["unlock", "b"]],
          [["lock", "c"], ["lock", "a"], ["unlock", "a"], ["unlock", "c"]]]],
        [[[["lock", "a"], ["lock", "b"], ["unlock", "b"], ["unlock", "a"]],
          [["lock", "b"], ["lock", "c"], ["unlock", "c"], ["unlock", "b"]],
          [["lock", "a"], ["lock", "c"], ["unlock", "c"], ["unlock", "a"]]]],
        [[[["lock", "a"], ["lock", "a"], ["lock", "b"], ["unlock", "b"], ["unlock", "a"], ["unlock", "a"]],
          [["lock", "b"], ["lock", "b"], ["unlock", "b"], ["unlock", "b"]]]],
        [[[["lock", "a"], ["lock", "b"], ["lock", "c"], ["unlock", "c"], ["unlock", "b"], ["unlock", "a"]],
          [["lock", "c"], ["lock", "a"], ["unlock", "a"], ["unlock", "c"]]]],
        [[[["lock", "x"], ["lock", "y"], ["unlock", "x"], ["lock", "z"], ["unlock", "z"], ["unlock", "y"]],
          [["lock", "z"], ["lock", "x"], ["unlock", "x"], ["unlock", "z"]]]],
        [[[["lock", "a"], ["lock", "b"], ["unlock", "b"], ["unlock", "a"], ["lock", "b"], ["lock", "a"], ["unlock", "a"], ["unlock", "b"]],
          [["lock", "a"], ["lock", "b"], ["unlock", "b"], ["unlock", "a"]]]],
    ],
    wrong_solutions=[
        '''def lock_cycle(traces):
    edges = set()
    for trace in traces:
        held = []
        for kind, name in trace:
            if kind == "lock":
                if name not in held:
                    for a in held: edges.add((a, name))
                    held.append(name)
            elif name in held:
                held.remove(name)
    return any((b, a) in edges for (a, b) in edges)
''',
        '''def lock_cycle(traces):
    orders = []
    for trace in traces:
        seen = []
        for kind, name in trace:
            if kind == "lock" and name not in seen:
                seen.append(name)
        orders.append(seen)
    for i in range(len(orders)):
        for j in range(i + 1, len(orders)):
            for a in orders[i]:
                for b in orders[i]:
                    if a != b and a in orders[j] and b in orders[j]:
                        if (orders[i].index(a) < orders[i].index(b)) != (orders[j].index(a) < orders[j].index(b)):
                            return True
    return False
''',
    ],
    guide=G(
        "Lesson *Race conditions, synchronization, deadlock and virtual threads*: the four conditions and lock ordering.",
        "A deadlock needs a circular wait. Record, for every thread, 'I took B while holding A' as an arrow "
        "A → B. If the arrows from different threads form a loop, some schedule can make each thread hold one lock "
        "of the loop while waiting for the next.",
        ["Replay each trace keeping the list of locks currently held, with a count per lock for reentrancy.",
         "Add an edge from every held lock to a newly acquired one, remembering which thread produced it.",
         "Search for a cycle, carrying the union of the threads seen on the path's edges; the cycle counts when that union has two or more threads."],
        "Comparing only pairs of locks (is there both A → B and B → A?) misses cycles of three or more locks, such "
        "as the dining philosophers, and wrongly flags a single thread that takes A then B and later B then A.",
        r"""**Dry run** three threads: T0 takes a then b, T1 takes b then c, T2 takes c then a. Edges
`a → b {T0}`, `b → c {T1}`, `c → a {T2}`. Starting at `a`: threads seen `{0}`, then `{0, 1}`, then the edge back to `a` gives `{0, 1, 2}`: more than
one thread took part in the cycle → **True**.
Change T2 to take a then c and the edge becomes `a → c`: no cycle, **False**. That is lock ordering at work.

```java
// Deadlock-prone
void transfer(Account from, Account to, long amount) {
    synchronized (from) { synchronized (to) { from.debit(amount); to.credit(amount); } }
}

// Fixed: always lock in one global order (here by account id)
void transferSafely(Account x, Account y, long amount) {
    Account first = x.id() < y.id() ? x : y;
    Account second = first == x ? y : x;
    synchronized (first) { synchronized (second) { x.debit(amount); y.credit(amount); } }
}
// Diagnose a hang with: jstack <pid>   ("Found one Java-level deadlock")
```""",
        "Building the graph is O(total events × locks held). The cycle search is exponential in the worst case, "
        "which is acceptable for the handful of locks in a trace; real tools use the same graph with smarter searches.",
        "- Checking only two-lock inversions.\n- Flagging a cycle created by one thread alone.\n"
        "- Adding edges for reentrant acquisitions.\n- Using the order locks were first seen instead of what was held at the time.",
    ),
),
# ------------------------------------------------------------------ java-executor-schedule
dict(
    id="java-executor-schedule",
    title="Fixed thread pool in virtual time",
    difficulty="Medium",
    pattern="Java concurrency",
    entry="schedule",
    description=r"""
Simulate `Executors.newFixedThreadPool(workers)` running tasks that are all submitted at time 0, in order.

- Task `i` (0-based) needs `durations[i]` time units.
- Tasks wait in a FIFO queue. Whenever a worker is free and the queue is not empty, the worker takes the
  task at the head. If several workers are free at the same moment, the one with the **lowest id** takes the
  next task (workers are numbered from 1).

Write `schedule(durations, workers)` returning `[assignments, makespan]`:

- `assignments[i]` is `[worker, start, end]` for task `i`;
- `makespan` is the time at which the last task finishes (0 if there are no tasks).

**Example** `schedule([4, 2, 1, 3, 2], 2)` →
`[[[1, 0, 4], [2, 0, 2], [2, 2, 3], [2, 3, 6], [1, 4, 6]], 6]`
""",
    starter='''def schedule(durations, workers):
    pass
''',
    solution='''def schedule(durations, workers):
    import heapq
    free = [(0, w) for w in range(1, workers + 1)]
    heapq.heapify(free)
    out = []
    makespan = 0
    for d in durations:
        t, w = heapq.heappop(free)
        out.append([w, t, t + d])
        makespan = max(makespan, t + d)
        heapq.heappush(free, (t + d, w))
    return [out, makespan]
''',
    tests=[
        [[4, 2, 1, 3, 2], 2],
        [[4, 2, 1, 3, 2], 1],
        [[4, 2, 1, 3, 2], 3],
        [[], 4],
        [[5], 3],
        [[1, 1, 1, 1], 4],
        [[1, 1, 1, 1, 1], 4],
        [[3, 3, 3, 3, 3, 3], 2],
        [[2, 2, 2, 1], 3],
        [[0, 0, 5], 1],
        [[7, 1, 1, 1, 1, 1, 1, 1], 2],
        [[i % 5 + 1 for i in range(40)], 6],
    ],
    wrong_solutions=[
        '''def schedule(durations, workers):
    out, t = [], [0] * workers
    for i, d in enumerate(durations):
        w = i % workers
        out.append([w + 1, t[w], t[w] + d])
        t[w] += d
    return [out, max(t) if durations else 0]
''',
        '''def schedule(durations, workers):
    import heapq
    free = [(0, -w) for w in range(1, workers + 1)]
    heapq.heapify(free)
    out, makespan = [], 0
    for d in durations:
        t, w = heapq.heappop(free)
        out.append([-w, t, t + d])
        makespan = max(makespan, t + d)
        heapq.heappush(free, (t + d, w))
    return [out, makespan]
''',
    ],
    guide=G(
        "Lesson *Threads, Runnable and ExecutorService*: thread pools, queues and the scheduling model.",
        "Each task goes to the worker that becomes free earliest. Keep the workers in a priority queue ordered "
        "by the time they are next free (and by id to break ties), pop one per task and push it back with its "
        "new free time.",
        ["Start with every worker free at time 0.", "A heap of `(free_time, worker_id)` gives both rules at once.",
         "The task's start is the popped free time; its end is start plus duration."],
        "Scan all workers for the smallest free time for every task: O(n × workers). The heap brings it to "
        "O(n log workers).",
        r"""**Dry run** `[4, 2, 1, 3, 2]` with 2 workers. Heap `[(0,1), (0,2)]`.
T0 → worker 1, 0..4. T1 → worker 2, 0..2. T2 → worker 2 (free at 2), 2..3. T3 → worker 2 (free at 3), 3..6.
T4 → worker 1 (free at 4), 4..6. Makespan 6. With one worker it is 12; with three it is 4, which is the
length of the longest task and cannot be beaten.

```java
try (ExecutorService pool = Executors.newFixedThreadPool(2)) {
    List<Future<String>> results = new ArrayList<>();
    for (int d : new int[] {4, 2, 1, 3, 2}) {
        results.add(pool.submit(() -> {
            Thread.sleep(d * 100L);
            return Thread.currentThread().getName();
        }));
    }
    for (Future<String> f : results) System.out.println(f.get());   // which worker ran each task
}                                                                   // close(): shut down and wait
```""",
        "Time O(n log w) for n tasks and w workers, space O(n + w).",
        "- Round-robin assignment, which ignores when workers become free.\n"
        "- Breaking ties toward the highest worker id.\n- Returning a makespan of the last task instead of the latest finish.",
    ),
),
# ------------------------------------------------------------------ java-bounded-buffer
dict(
    id="java-bounded-buffer",
    title="Producer-consumer with a bounded buffer",
    difficulty="Medium",
    pattern="Java concurrency",
    entry="bounded_buffer",
    description=r"""
Simulate an `ArrayBlockingQueue` of a given `capacity` shared by producers and consumers.

`script` is a string of `"P"` and `"C"` characters, processed left to right:

- `"P"`: a producer calls `put` with the next item. Items are numbered 1, 2, 3, ... in the order of the `P`
  characters. If the buffer is full, the producer **blocks**: it waits in a FIFO line of blocked producers.
- `"C"`: a consumer calls `take`. If the buffer is empty, the consumer blocks in a FIFO line of blocked
  consumers.

After each character, let blocked operations complete for as long as possible, repeating until nothing
changes: first, while a producer is blocked and the buffer has room, the first blocked producer puts its
item; then, while a consumer is blocked and the buffer is not empty, the first blocked consumer takes the
head item. Repeat both loops until neither makes progress.

Return `[consumed, buffer, blocked_producers, blocked_consumers]`:

- `consumed`: item numbers in the order they were taken;
- `buffer`: the items left in the buffer, head first;
- the two counts of operations still blocked at the end.

**Example** `bounded_buffer(2, "PPPPCC")` → `[[1, 2], [3, 4], 0, 0]`
(after `PPPP` the buffer is `[1, 2]` with two producers blocked; each `C` frees a slot that a blocked producer fills).
""",
    starter='''def bounded_buffer(capacity, script):
    pass
''',
    solution='''def bounded_buffer(capacity, script):
    from collections import deque
    buf, wait_put = deque(), deque()
    wait_take = 0
    consumed = []
    next_item = 1
    for ch in script:
        if ch == "P":
            wait_put.append(next_item)
            next_item += 1
        else:
            wait_take += 1
        progress = True
        while progress:
            progress = False
            while wait_put and len(buf) < capacity:
                buf.append(wait_put.popleft())
                progress = True
            while wait_take and buf:
                consumed.append(buf.popleft())
                wait_take -= 1
                progress = True
    return [consumed, list(buf), len(wait_put), wait_take]
''',
    tests=[
        [2, "PPPPCC"],
        [2, "PPPP"],
        [2, "CCP"],
        [1, "PCPCPC"],
        [1, "PPPCCC"],
        [3, ""],
        [3, "CCC"],
        [3, "PPP"],
        [2, "CCCPPPPP"],
        [2, "PCCPPPCPC"],
        [1, "CPPPPCC"],
        [4, "PPPPPPCCPPCCCCCC"],
        [2, "PPPPPPPPCCCCCCCC"],
    ],
    wrong_solutions=[
        '''def bounded_buffer(capacity, script):
    buf, consumed, nxt, bp, bc = [], [], 1, 0, 0
    for ch in script:
        if ch == "P":
            if len(buf) < capacity: buf.append(nxt)
            else: bp += 1
            nxt += 1
        else:
            if buf: consumed.append(buf.pop(0))
            else: bc += 1
    return [consumed, buf, bp, bc]
''',
        '''def bounded_buffer(capacity, script):
    from collections import deque
    buf, wait_put, wait_take, consumed, nxt = deque(), deque(), 0, [], 1
    for ch in script:
        if ch == "P":
            wait_put.append(nxt); nxt += 1
        else:
            wait_take += 1
        if wait_put and len(buf) < capacity:
            buf.append(wait_put.popleft())
        if wait_take and buf:
            consumed.append(buf.popleft()); wait_take -= 1
    return [consumed, list(buf), len(wait_put), wait_take]
''',
    ],
    guide=G(
        "Lesson *Concurrency utilities, thread-safety levels and lazy initialisation*: `BlockingQueue` and producer-consumer.",
        "Treat every `put` and `take` as a request that joins a waiting line, then let the lines drain whenever "
        "the buffer allows. A blocked operation is not lost; it finishes later, when another operation makes room "
        "or supplies an item.",
        ["Keep three things: the buffer, the queue of waiting items, and a count of waiting consumers.",
         "After each new request, loop: move waiting items in while there is room; let waiting consumers take while there are items.",
         "Repeat until a full round makes no progress, because a take can unblock a put and the reverse."],
        "Dropping an operation that cannot proceed immediately (instead of making it wait) loses items and "
        "consumers. That is how a non-blocking `offer`/`poll` behaves, not `put`/`take`.",
        r"""**Dry run** `bounded_buffer(2, "PPPPCC")`. After `PP`: buffer `[1, 2]`. After `PP` more: producers
waiting with items 3 and 4. First `C`: takes 1 → buffer `[2]`; room appears, item 3 enters → `[2, 3]`.
Second `C`: takes 2; item 4 enters → `[3, 4]`. Result `[[1, 2], [3, 4], 0, 0]`.

```java
BlockingQueue<Integer> shelf = new ArrayBlockingQueue<>(2);

Thread producer = new Thread(() -> {
    try {
        for (int i = 1; i <= 4; i++) shelf.put(i);      // blocks while the queue is full
    } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
});
Thread consumer = new Thread(() -> {
    try {
        for (int i = 0; i < 2; i++) System.out.println(shelf.take());   // blocks while it is empty
    } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
});
producer.start(); consumer.start();
producer.join(); consumer.join();
System.out.println(shelf);            // [3, 4]
```""",
        "Time O(length of the script): each item enters and leaves the buffer at most once. Space O(length).",
        "- Discarding blocked operations.\n- Draining only one waiting operation per step.\n"
        "- Letting a late consumer overtake one that was already waiting.\n- Numbering items by when they enter the buffer instead of by when `put` was called.",
    ),
),
# ------------------------------------------------------------------ java-money-rounding
dict(
    id="java-money-rounding",
    title="Money: exact arithmetic and HALF_UP rounding",
    difficulty="Medium",
    pattern="Java numbers",
    entry="invoice",
    description=r"""
Never use `double` for money. Compute an invoice exactly, as `BigDecimal` would.

`invoice(lines, vat_percent)`:

- `lines` is a list of `[price, quantity]` where `price` is a **string** with exactly two decimals, such as
  `"19.99"` or `"0.10"` (never negative), and `quantity` is a non-negative integer;
- `vat_percent` is a non-negative integer, such as `20`.

Compute:

1. `subtotal` = sum of `price × quantity` (exact);
2. `vat` = `subtotal × vat_percent / 100`, rounded to 2 decimals with **HALF_UP** (a third decimal digit of
   5 or more rounds away from zero);
3. `total` = `subtotal + vat`.

Return `[subtotal, vat, total]` as strings with exactly two decimals.

**Example** `invoice([["19.99", 1]], 20)` → `["19.99", "4.00", "23.99"]` (the exact VAT is 3.998);
`invoice([["0.10", 3]], 0)` → `["0.30", "0.00", "0.30"]` (with doubles, 0.1 × 3 is 0.30000000000000004).
""",
    starter='''def invoice(lines, vat_percent):
    pass
''',
    solution='''def invoice(lines, vat_percent):
    def to_cents(s):
        whole, frac = s.split(".")
        return int(whole) * 100 + int(frac)

    def fmt(c):
        return "%d.%02d" % (c // 100, c % 100)

    subtotal = sum(to_cents(p) * q for p, q in lines)
    num = subtotal * vat_percent
    vat = (num + 50) // 100
    return [fmt(subtotal), fmt(vat), fmt(subtotal + vat)]
''',
    tests=[
        [[["19.99", 1]], 20],
        [[["0.10", 3]], 0],
        [[], 20],
        [[["0.05", 1]], 10],
        [[["0.04", 1]], 10],
        [[["1.15", 1]], 50],
        [[["2.67", 1], ["0.01", 1]], 25],
        [[["10.00", 3], ["0.33", 3]], 7],
        [[["1.10", 3], ["2.20", 3]], 0],
        [[["0.29", 100]], 0],
        [[["99999999.99", 99]], 21],
        [[["0.25", 1]], 2],
        [[["0.75", 1]], 2],
        [[["1.45", 1]], 10],
    ],
    wrong_solutions=[
        '''def invoice(lines, vat_percent):
    subtotal = sum(float(p) * q for p, q in lines)
    vat = round(subtotal * vat_percent / 100, 2)
    return ["%.2f" % subtotal, "%.2f" % vat, "%.2f" % (subtotal + vat)]
''',
        '''def invoice(lines, vat_percent):
    def to_cents(s):
        whole, frac = s.split(".")
        return int(whole) * 100 + int(frac)
    def fmt(c):
        return "%d.%02d" % (c // 100, c % 100)
    subtotal = sum(to_cents(p) * q for p, q in lines)
    vat = subtotal * vat_percent // 100
    return [fmt(subtotal), fmt(vat), fmt(subtotal + vat)]
''',
        '''def invoice(lines, vat_percent):
    def to_cents(s):
        return int(round(float(s) * 100))
    def fmt(c):
        return "%d.%02d" % (c // 100, c % 100)
    subtotal = sum(to_cents(p) * q for p, q in lines)
    vat = int(round(subtotal * vat_percent / 100))
    return [fmt(subtotal), fmt(vat), fmt(subtotal + vat)]
''',
    ],
    guide=G(
        "Lessons *Primitive types and how numbers are stored* and *Everyday habits: scope, for-each, libraries, money and boxing*.",
        "Work in whole cents. Integers are exact, so the only place a decision is needed is the single division "
        "by 100 for the VAT, and HALF_UP for non-negative numbers is 'add half the divisor, then divide downward'.",
        ["Parse `\"19.99\"` by splitting at the dot: 19 × 100 + 99. Do not go through `float`.",
         "VAT in cents is `subtotal_cents × percent / 100`; compute `(n + 50) // 100` for HALF_UP.",
         "Format with `cents // 100` and `cents % 100` padded to two digits."],
        "Using `float` and `round` is shorter and wrong twice over: decimal fractions are not exact in binary, and "
        "Python's `round` uses banker's rounding (halves go to the even neighbour).",
        r"""**Dry run** `invoice([["1.45", 1]], 10)`: subtotal 145 cents. VAT numerator `145 × 10 = 1450`;
`(1450 + 50) // 100 = 15` cents (exact value 14.5 rounds up). Total 160 → `["1.45", "0.15", "1.60"]`.
With floats, `round(0.145, 2)` gives `0.14`, because 0.145 is stored as 0.14499999...

```java
import java.math.BigDecimal;
import java.math.RoundingMode;

static BigDecimal[] invoice(List<String[]> lines, int vatPercent) {
    BigDecimal subtotal = BigDecimal.ZERO;
    for (String[] line : lines) {
        subtotal = subtotal.add(new BigDecimal(line[0]).multiply(new BigDecimal(line[1])));   // String constructor: exact
    }
    BigDecimal vat = subtotal.multiply(BigDecimal.valueOf(vatPercent))
            .divide(BigDecimal.valueOf(100), 2, RoundingMode.HALF_UP);
    return new BigDecimal[] { subtotal.setScale(2), vat, subtotal.add(vat) };
}
// Never: new BigDecimal(0.1)   -> 0.1000000000000000055511151231257827...
```""",
        "Time O(number of lines), space O(1).",
        "- Parsing prices through `float`.\n- Truncating the VAT instead of rounding.\n"
        "- Banker's rounding (`round`) where HALF_UP was specified.\n- Formatting 5 cents as `0.5` instead of `0.05`.",
        "`RoundingMode.HALF_EVEN` is common in finance because it does not bias totals upward; implement it as a variant.",
    ),
),
# ------------------------------------------------------------------ java-import-resolution
dict(
    id="java-import-resolution",
    title="Resolve a simple class name",
    difficulty="Medium",
    pattern="Java packages",
    entry="resolve_name",
    description=r"""
The compiler turns a simple name such as `List` into a fully qualified name by searching in a fixed order.

`resolve_name(name, current_pkg, single_imports, wildcard_imports, packages)`:

- `packages` maps a package name to the list of class names it contains;
- `current_pkg` is the package of the file being compiled;
- `single_imports` is a list of fully qualified names, e.g. `"java.util.List"` (`import java.util.List;`);
- `wildcard_imports` is a list of package names, e.g. `"java.util"` (`import java.util.*;`).

**Search order** (stop at the first step that succeeds):

1. a **single-type import** whose last component equals `name` → that fully qualified name;
2. a class `name` in the **current package** → `current_pkg + "." + name`;
3. **on-demand imports**: look in `java.lang` (always imported) and in each wildcard package. Collect the
   distinct packages that contain `name`:
   - exactly one → `package + "." + name`;
   - more than one → `"ambiguous"`;
   - none → `"cannot find symbol"`.

A wildcard import does **not** include sub-packages. A wildcard package that does not exist in `packages`
contributes nothing.

**Example** `resolve_name("Date", "com.shop", [], ["java.util", "java.sql"], pk)` → `"ambiguous"` when both
packages contain `Date`.
""",
    starter='''def resolve_name(name, current_pkg, single_imports, wildcard_imports, packages):
    pass
''',
    solution='''def resolve_name(name, current_pkg, single_imports, wildcard_imports, packages):
    for full in single_imports:
        if full.rsplit(".", 1)[-1] == name:
            return full
    if name in packages.get(current_pkg, []):
        return current_pkg + "." + name
    hits = []
    for pkg in ["java.lang"] + list(wildcard_imports):
        if name in packages.get(pkg, []) and pkg not in hits:
            hits.append(pkg)
    if len(hits) == 1:
        return hits[0] + "." + name
    return "ambiguous" if hits else "cannot find symbol"
''',
    tests=[
        ["Date", "com.shop", [], ["java.util", "java.sql"],
         {"java.lang": ["String", "Math", "Object"], "java.util": ["List", "Date", "ArrayList"], "java.sql": ["Date", "Connection"], "com.shop": ["Order", "List"], "java.util.concurrent": ["Future"]}],
        ["Date", "com.shop", ["java.sql.Date"], ["java.util", "java.sql"],
         {"java.lang": ["String", "Math", "Object"], "java.util": ["List", "Date", "ArrayList"], "java.sql": ["Date", "Connection"], "com.shop": ["Order", "List"], "java.util.concurrent": ["Future"]}],
        ["List", "com.shop", [], ["java.util"],
         {"java.lang": ["String", "Math", "Object"], "java.util": ["List", "Date", "ArrayList"], "java.sql": ["Date", "Connection"], "com.shop": ["Order", "List"], "java.util.concurrent": ["Future"]}],
        ["String", "com.shop", [], [],
         {"java.lang": ["String", "Math", "Object"], "java.util": ["List", "Date", "ArrayList"], "java.sql": ["Date", "Connection"], "com.shop": ["Order", "List"], "java.util.concurrent": ["Future"]}],
        ["Future", "com.shop", [], ["java.util"],
         {"java.lang": ["String", "Math", "Object"], "java.util": ["List", "Date", "ArrayList"], "java.sql": ["Date", "Connection"], "com.shop": ["Order", "List"], "java.util.concurrent": ["Future"]}],
        ["Future", "com.shop", [], ["java.util", "java.util.concurrent"],
         {"java.lang": ["String", "Math", "Object"], "java.util": ["List", "Date", "ArrayList"], "java.sql": ["Date", "Connection"], "com.shop": ["Order", "List"], "java.util.concurrent": ["Future"]}],
        ["Order", "com.shop", [], [],
         {"java.lang": ["String", "Math", "Object"], "java.util": ["List", "Date", "ArrayList"], "java.sql": ["Date", "Connection"], "com.shop": ["Order", "List"], "java.util.concurrent": ["Future"]}],
        ["ArrayList", "com.shop", [], ["java.util", "java.util"],
         {"java.lang": ["String", "Math", "Object"], "java.util": ["List", "Date", "ArrayList"], "java.sql": ["Date", "Connection"], "com.shop": ["Order", "List"], "java.util.concurrent": ["Future"]}],
        ["List", "com.shop", ["java.util.List"], [],
         {"java.lang": ["String", "Math", "Object"], "java.util": ["List", "Date", "ArrayList"], "java.sql": ["Date", "Connection"], "com.shop": ["Order", "List"], "java.util.concurrent": ["Future"]}],
        ["Connection", "com.shop", [], ["java.util", "no.such.pkg"],
         {"java.lang": ["String", "Math", "Object"], "java.util": ["List", "Date", "ArrayList"], "java.sql": ["Date", "Connection"], "com.shop": ["Order", "List"], "java.util.concurrent": ["Future"]}],
        ["Object", "app", [], ["lib"], {"java.lang": ["Object"], "lib": ["Object"], "app": []}],
        ["Object", "app", [], ["lib"], {"java.lang": ["Object"], "lib": ["Object"], "app": ["Object"]}],
        ["Math", "java.lang", [], [], {"java.lang": ["Math"]}],
    ],
    wrong_solutions=[
        '''def resolve_name(name, current_pkg, single_imports, wildcard_imports, packages):
    for full in single_imports:
        if full.rsplit(".", 1)[-1] == name:
            return full
    for pkg in ["java.lang"] + list(wildcard_imports) + [current_pkg]:
        if name in packages.get(pkg, []):
            return pkg + "." + name
    return "cannot find symbol"
''',
        '''def resolve_name(name, current_pkg, single_imports, wildcard_imports, packages):
    for full in single_imports:
        if full.rsplit(".", 1)[-1] == name:
            return full
    if name in packages.get(current_pkg, []):
        return current_pkg + "." + name
    hits = []
    for pkg in ["java.lang"] + list(wildcard_imports):
        for p, classes in packages.items():
            if (p == pkg or p.startswith(pkg + ".")) and name in classes and p not in hits:
                hits.append(p)
    if len(hits) == 1:
        return hits[0] + "." + name
    return "ambiguous" if hits else "cannot find symbol"
''',
    ],
    guide=G(
        "Lesson *Packages, imports and the String toolbox*: how the compiler resolves a short name.",
        "Three levels of priority. A specific import beats the current package, which beats wildcard imports. "
        "Only at the last level can two candidates clash, and then the compiler refuses to choose.",
        ["Check single-type imports by comparing the text after the last dot.",
         "Then the current package.", "Then gather hits from `java.lang` plus the wildcard packages, without duplicates, and count them."],
        "Returning the first package that contains the name gets the priority order wrong and never reports ambiguity.",
        r"""**Dry run** name `List`, current package `com.shop` (which has its own `List`), wildcard `java.util`.
No single-type import. The current package contains `List` → `com.shop.List`. The wildcard is never
consulted. Add `import java.util.List;` and the answer becomes `java.util.List`.

**Dry run** name `Object`, wildcard `lib` where `lib.Object` exists: `java.lang.Object` and `lib.Object`
are both on-demand candidates → `"ambiguous"`.

```java
package com.shop;

import java.util.*;
import java.sql.*;
import java.util.Date;                 // single-type import: settles the clash

class Report {
    Date printed;                      // java.util.Date
    java.sql.Date stored;              // the other one, written in full
    List<String> lines;                // com.shop.List if this package declares one, else java.util.List
}
```""",
        "Time O(imports + size of the packages consulted), space O(1).",
        "- Preferring a wildcard import to a class in the current package.\n- Letting a wildcard reach into sub-packages.\n"
        "- Forgetting that `java.lang` is always an on-demand import and can take part in an ambiguity.\n"
        "- Counting the same package twice when it is imported twice.",
    ),
),
# ------------------------------------------------------------------ java-maven-mediation
dict(
    id="java-maven-mediation",
    title="Maven dependency mediation: nearest wins",
    difficulty="Medium",
    pattern="Java build tools",
    entry="mediate",
    description=r"""
A Maven project can request two versions of one library through different paths. Maven keeps exactly one,
chosen by **dependency mediation**:

- the version **nearest** to the project in the dependency tree wins;
- at equal depth, the one **declared first** wins;
- the dependencies of a version that **lost** are not followed.

Write `mediate(root_deps, graph)`:

- `root_deps` is the ordered list of the project's direct dependencies, each `"name:version"`;
- `graph` maps `"name:version"` to the ordered list of that artifact's own dependencies (a missing key means
  no dependencies).

Process the tree **breadth-first**: a queue starts with the root dependencies (depth 1) in order. Take the
head: if its `name` is already chosen, skip it entirely; otherwise choose this version and append its
dependencies to the queue in order.

Return the chosen versions as a list of `"name:version"` strings **sorted by name**.

**Example** `mediate(["A:1.0", "B:1.0"], {"A:1.0": ["X:1.0"], "B:1.0": ["C:1.0"], "C:1.0": ["X:2.0"]})`
→ `["A:1.0", "B:1.0", "C:1.0", "X:1.0"]` (X 1.0 is at depth 2, X 2.0 at depth 3).
""",
    starter='''def mediate(root_deps, graph):
    pass
''',
    solution='''def mediate(root_deps, graph):
    from collections import deque
    chosen = {}
    queue = deque(root_deps)
    while queue:
        coord = queue.popleft()
        name, version = coord.split(":")
        if name in chosen:
            continue
        chosen[name] = version
        queue.extend(graph.get(coord, []))
    return [n + ":" + chosen[n] for n in sorted(chosen)]
''',
    tests=[
        [["A:1.0", "B:1.0"], {"A:1.0": ["X:1.0"], "B:1.0": ["C:1.0"], "C:1.0": ["X:2.0"]}],
        [["B:1.0", "A:1.0"], {"A:1.0": ["X:1.0"], "B:1.0": ["X:2.0"]}],
        [["A:1.0", "B:1.0"], {"A:1.0": ["X:1.0"], "B:1.0": ["X:2.0"]}],
        [["A:1.0", "B:1.0", "X:3.0"], {"A:1.0": ["X:1.0"], "B:1.0": ["X:2.0"]}],
        [[], {}],
        [["A:1.0"], {}],
        [["A:1.0", "A:2.0"], {"A:1.0": ["Y:1"], "A:2.0": ["Z:1"]}],
        [["A:1.0", "B:1.0"], {"A:1.0": ["X:1.0"], "B:1.0": ["C:1.0"], "C:1.0": ["X:2.0", "Y:3.1"], "X:1.0": ["Y:3.0"], "X:2.0": ["W:9"]}],
        [["A:1", "B:1"], {"A:1": ["B:2"], "B:1": ["A:2"], "B:2": ["Q:1"], "A:2": ["R:1"]}],
        [["A:1"], {"A:1": ["B:1"], "B:1": ["C:1"], "C:1": ["A:9", "D:1"]}],
        [["L:1", "M:1"], {"L:1": ["N:1", "O:1"], "M:1": ["O:2", "N:2"], "N:1": ["P:1"], "O:1": ["P:2"], "O:2": ["Z:1"]}],
    ],
    wrong_solutions=[
        '''def mediate(root_deps, graph):
    chosen = {}
    def visit(coord):
        name, version = coord.split(":")
        if name in chosen:
            return
        chosen[name] = version
        for d in graph.get(coord, []):
            visit(d)
    for c in root_deps:
        visit(c)
    return [n + ":" + chosen[n] for n in sorted(chosen)]
''',
        '''def mediate(root_deps, graph):
    from collections import deque
    best = {}
    queue, seen = deque(root_deps), set()
    while queue:
        coord = queue.popleft()
        if coord in seen: continue
        seen.add(coord)
        name, version = coord.split(":")
        if name not in best or [float(x) for x in version.split(".")] > [float(x) for x in best[name].split(".")]:
            best[name] = version
        queue.extend(graph.get(coord, []))
    return [n + ":" + best[n] for n in sorted(best)]
''',
    ],
    guide=G(
        "Lesson *Maven, Gradle and the module system*: transitive dependencies and nearest-wins mediation.",
        "Breadth-first search visits the tree level by level, left to right. The first time a library name comes "
        "off the queue is therefore its nearest, earliest-declared occurrence, which is exactly Maven's rule.",
        ["Use a queue, not recursion: recursion goes deep before wide and measures the wrong thing.",
         "Decide on the **name**: once a name is chosen, later versions of it are ignored.",
         "Only a chosen version's dependencies join the queue."],
        "Depth-first traversal (plain recursion) follows A's entire subtree before looking at B, so a deep "
        "transitive dependency of A can beat a direct dependency declared later. Choosing the highest version is "
        "Gradle's default, not Maven's.",
        r"""**Dry run** roots `[A:1.0, B:1.0]`; `A → X:1.0`; `B → C`; `C → X:2.0, Y:3.1`; `X:1.0 → Y:3.0`;
`X:2.0 → W:9`. Queue: A, B → choose A (queue B, X:1.0) → choose B (X:1.0, C) → choose X 1.0 (C, Y:3.0) →
choose C (Y:3.0, X:2.0, Y:3.1) → choose Y 3.0 → X:2.0 skipped, so W is never considered → Y:3.1 skipped.
Result `["A:1.0", "B:1.0", "C:1.0", "X:1.0", "Y:3.0"]`.

```xml
<!-- Force a version: a direct declaration is at depth 1 and always wins -->
<dependency>
  <groupId>org.example</groupId><artifactId>x</artifactId><version>2.0</version>
</dependency>

<!-- Or pin it for the whole build -->
<dependencyManagement>
  <dependencies>
    <dependency><groupId>org.example</groupId><artifactId>x</artifactId><version>2.0</version></dependency>
  </dependencies>
</dependencyManagement>
```

```java
// Inspect the result on a real project:  mvn dependency:tree -Dverbose
// The equivalent data structure in Java:
record Coordinate(String name, String version) { }
Map<String, String> chosen = new LinkedHashMap<>();
Deque<Coordinate> queue = new ArrayDeque<>(rootDeps);
while (!queue.isEmpty()) {
    Coordinate c = queue.poll();
    if (chosen.putIfAbsent(c.name(), c.version()) == null) {
        queue.addAll(graph.getOrDefault(c, List.of()));
    }
}
```""",
        "Time O(V + E) over the artifacts and dependency edges visited, space O(V).",
        "- Depth-first traversal.\n- Picking the highest version.\n- Following the dependencies of a version that lost.\n"
        "- Keying the decision on `name:version` instead of the name.",
    ),
),
]
