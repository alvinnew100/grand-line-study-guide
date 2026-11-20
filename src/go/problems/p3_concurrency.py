"""Go track problems, part 3: channels, select, worker pools, pipelines, WaitGroup, mutexes and the scheduler.

Real goroutines run in an order the programmer does not control. To make the answers checkable,
every problem here fixes one deterministic scheduling rule and says so in the statement.
"""

PROBLEMS = [
# ------------------------------------------------------------------ go-channel-sim
dict(
    id="go-channel-sim",
    title="Channel simulator: rendezvous, buffers and deadlock",
    difficulty="Hard",
    pattern="Go concurrency",
    entry="run_channels",
    description=r"""
A **goroutine** is a function running independently of the others; a **channel** is a typed pipe
that goroutines use to hand values to each other.

- An **unbuffered** channel (capacity 0) has no storage. A send waits until a receiver is ready at
  the same moment, and the value is handed over directly. This meeting is called a *rendezvous*.
- A **buffered** channel of capacity `c` stores up to `c` values. A send waits only when the buffer is
  full; a receive waits only when it is empty.
- After `close(ch)`: receiving first drains any buffered values, then returns the zero value with
  `ok == false` immediately, forever. Sending on a closed channel, or closing twice, **panics**.

Simulate a program. `chans` maps channel names to capacities. `scripts[i]` is the list of operations
of goroutine `i`; **goroutine 0 is `main`**. Operations: `["send", ch, value]`, `["recv", ch]`, `["close", ch]`.

**Scheduling rule.** Repeat *rounds*. In a round, visit the goroutines in index order; each
unfinished goroutine tries its **next** operation once:

- `close ch`: panic if already closed; otherwise mark closed and advance.
- `send ch v`: panic if `ch` is closed. If the buffer has room, store `v` and advance. Otherwise, if
  `ch` is unbuffered and some **other** unfinished goroutine's next operation is `recv` on `ch`
  (choose the lowest index), that goroutine receives `v` and **both** advance. Otherwise it stays blocked.
- `recv ch`: if the buffer has a value, take the oldest and advance. Otherwise, if `ch` is closed,
  receive `[0, false]` and advance. Otherwise, if `ch` is unbuffered and some other unfinished
  goroutine's next operation is `send` on `ch` (lowest index), take its value and both advance.
  Otherwise it stays blocked.

The program ends:

- with `"ok"` as soon as `main` has finished all its operations (checked before the first round and
  after every operation), exactly like a real Go program, which exits when `main` returns;
- with `"panic"` at the moment of a panic;
- with `"deadlock"` when a whole round makes no progress and `main` is not finished.

Return `[status, received, leaked]`: `received[i]` is the list of `[value, ok]` pairs goroutine `i`
received (`ok` is `true` for real values), and `leaked` is the number of goroutines other than
`main` that had not finished when the program ended.

**Example 1:** `run_channels({"c": 0}, [[["recv","c"]], [["send","c",7]]])` → `["ok", [[[7, true]], []], 0]`

**Example 2:** `run_channels({"c": 0}, [[["send","c",1]]])` → `["deadlock", [[]], 0]` (nobody will ever receive)

**Example 3:** `run_channels({"c": 1}, [[["send","c",1], ["close","c"], ["recv","c"], ["recv","c"]]])`
→ `["ok", [[[1, true], [0, false]]], 0]`
""",
    starter='''def run_channels(chans, scripts):
    # return [status, received, leaked]
    pass
''',
    solution='''def run_channels(chans, scripts):
    buf = {c: [] for c in chans}
    closed = set()
    n = len(scripts)
    pc = [0] * n
    received = [[] for _ in range(n)]

    def done(i):
        return pc[i] >= len(scripts[i])

    def result(status):
        return [status, received, sum(1 for i in range(1, n) if not done(i))]

    def partner(i, kind, ch):
        for j in range(n):
            if j != i and not done(j):
                op = scripts[j][pc[j]]
                if op[0] == kind and op[1] == ch:
                    return j
        return None

    if n == 0 or done(0):
        return result("ok")
    while True:
        progress = False
        for i in range(n):
            if done(i):
                continue
            op = scripts[i][pc[i]]
            kind, ch = op[0], op[1]
            if kind == "close":
                if ch in closed:
                    return result("panic")
                closed.add(ch)
                pc[i] += 1
                progress = True
            elif kind == "send":
                if ch in closed:
                    return result("panic")
                if len(buf[ch]) < chans[ch]:
                    buf[ch].append(op[2])
                    pc[i] += 1
                    progress = True
                elif chans[ch] == 0:
                    j = partner(i, "recv", ch)
                    if j is not None:
                        received[j].append([op[2], True])
                        pc[j] += 1
                        pc[i] += 1
                        progress = True
            else:
                if buf[ch]:
                    received[i].append([buf[ch].pop(0), True])
                    pc[i] += 1
                    progress = True
                elif ch in closed:
                    received[i].append([0, False])
                    pc[i] += 1
                    progress = True
                elif chans[ch] == 0:
                    j = partner(i, "send", ch)
                    if j is not None:
                        received[i].append([scripts[j][pc[j]][2], True])
                        pc[j] += 1
                        pc[i] += 1
                        progress = True
            if done(0):
                return result("ok")
        if not progress:
            return result("deadlock")
''',
    tests=[
        [{"c": 0}, [[["recv", "c"]], [["send", "c", 7]]]],
        [{"c": 0}, [[["send", "c", 1]]]],
        [{"c": 1}, [[["send", "c", 1], ["close", "c"], ["recv", "c"], ["recv", "c"]]]],
        [{}, [[]]],
        [{"c": 0}, [[], [["send", "c", 1]]]],
        [{"c": 2}, [[["send", "c", 1], ["send", "c", 2], ["send", "c", 3]]]],
        [{"c": 2}, [[["send", "c", 1], ["send", "c", 2], ["send", "c", 3]], [["recv", "c"]]]],
        [{"c": 0}, [[["recv", "c"], ["recv", "c"], ["recv", "c"]], [["send", "c", 1], ["send", "c", 2]], [["send", "c", 9]]]],
        [{"c": 0, "done": 0}, [[["recv", "done"]], [["send", "c", 5], ["send", "done", 1]], [["recv", "c"]]]],
        [{"c": 0}, [[["close", "c"], ["close", "c"]]]],
        [{"c": 1}, [[["close", "c"], ["send", "c", 1]]]],
        [{"c": 0}, [[["recv", "c"], ["recv", "c"]], [["send", "c", 4], ["close", "c"]]]],
        [{"a": 0, "b": 0}, [[["recv", "a"], ["send", "b", 1]], [["recv", "b"], ["send", "a", 2]]]],
        [{"jobs": 3, "res": 3}, [[["send", "jobs", 1], ["send", "jobs", 2], ["send", "jobs", 3], ["close", "jobs"],
                                  ["recv", "res"], ["recv", "res"], ["recv", "res"]],
                                 [["recv", "jobs"], ["send", "res", 10], ["recv", "jobs"], ["send", "res", 20]],
                                 [["recv", "jobs"], ["send", "res", 30], ["recv", "jobs"]]]],
        [{"c": 0}, [[["recv", "c"]], [["send", "c", 1], ["send", "c", 2]], [["send", "c", 3]], [["recv", "c"], ["recv", "c"], ["recv", "c"]]]],
        [{"c": 0}, [[["send", "c", 1]], [["recv", "c"], ["close", "c"]], [["send", "c", 2]]]],
    ],
    examples=3,
    wrong_solutions=[
        '''def run_channels(chans, scripts):
    buf = {c: [] for c in chans}; closed = set(); n = len(scripts)
    pc = [0] * n; rec = [[] for _ in range(n)]
    done = lambda i: pc[i] >= len(scripts[i])
    res = lambda s: [s, rec, sum(1 for i in range(1, n) if not done(i))]
    if n == 0 or done(0): return res("ok")
    while True:
        progress = False
        for i in range(n):
            if done(i): continue
            op = scripts[i][pc[i]]; kind, ch = op[0], op[1]
            if kind == "close":
                if ch in closed: return res("panic")
                closed.add(ch); pc[i] += 1; progress = True
            elif kind == "send":
                if ch in closed: return res("panic")
                if len(buf[ch]) < max(chans[ch], 1):
                    buf[ch].append(op[2]); pc[i] += 1; progress = True
            else:
                if buf[ch]:
                    rec[i].append([buf[ch].pop(0), True]); pc[i] += 1; progress = True
                elif ch in closed:
                    rec[i].append([0, False]); pc[i] += 1; progress = True
            if done(0): return res("ok")
        if not progress: return res("deadlock")
''',
        '''def run_channels(chans, scripts):
    buf = {c: [] for c in chans}; closed = set(); n = len(scripts)
    pc = [0] * n; rec = [[] for _ in range(n)]
    done = lambda i: pc[i] >= len(scripts[i])
    res = lambda s: [s, rec, sum(1 for i in range(1, n) if not done(i))]
    def partner(i, kind, ch):
        for j in range(n):
            if j != i and not done(j) and scripts[j][pc[j]][0] == kind and scripts[j][pc[j]][1] == ch: return j
    while True:
        progress = False
        for i in range(n):
            if done(i): continue
            op = scripts[i][pc[i]]; kind, ch = op[0], op[1]
            if kind == "close":
                if ch in closed: return res("panic")
                closed.add(ch); pc[i] += 1; progress = True
            elif kind == "send":
                if ch in closed: return res("panic")
                if len(buf[ch]) < chans[ch]:
                    buf[ch].append(op[2]); pc[i] += 1; progress = True
                elif chans[ch] == 0:
                    j = partner(i, "recv", ch)
                    if j is not None:
                        rec[j].append([op[2], True]); pc[j] += 1; pc[i] += 1; progress = True
            else:
                if buf[ch]:
                    rec[i].append([buf[ch].pop(0), True]); pc[i] += 1; progress = True
                elif ch in closed:
                    rec[i].append([0, False]); pc[i] += 1; progress = True
                elif chans[ch] == 0:
                    j = partner(i, "send", ch)
                    if j is not None:
                        rec[i].append([scripts[j][pc[j]][2], True]); pc[j] += 1; pc[i] += 1; progress = True
        if all(done(i) for i in range(n)): return res("ok")
        if not progress: return res("deadlock")
''',
    ],
    guide=dict(
        prereqs="Queues, simulation loops. Lesson: [Goroutines and channels](#/lesson/go/go-goroutines-channels).",
        intuition="Each goroutine is a list with a bookmark. A buffered channel is a queue with a size limit. "
                  "An unbuffered channel is a handshake: neither side may move unless the other side's bookmark "
                  "is on the matching operation, and then both bookmarks move together.",
        hints=[
            "Keep `pc[i]`, the index of goroutine i's next operation, and a list per channel for the buffer.",
            "Write a helper that finds the lowest-index *other* goroutine whose next operation is a given kind on a given channel.",
            "Check 'has main finished?' after every single operation, and 'did anything move?' after every round.",
        ],
        brute_force="Modelling an unbuffered channel as a buffer of size 1 is the usual shortcut. It lets a "
                    "sender continue with nobody listening, so programs that deadlock in Go appear to work.",
        approach=r"""
Round-robin loop with a `progress` flag. Order of checks inside `recv` matters: buffer, then closed, then
rendezvous.

**Dry run** of the handshake test `{"a":0,"b":0}`, main = `[recv a, send b 1]`, g1 = `[recv b, send a 2]`.
Round 1: main wants `recv a`; no goroutine's next op is `send a` (g1 is at `recv b`) → blocked. g1 wants
`recv b`; main's next op is `recv a`, not `send b` → blocked. No progress → `"deadlock"`. Each side waits for
the other to go first: the classic circular wait.

**The same situation in Go:**

```go
package main

import "fmt"

func main() {
	c := make(chan int) // unbuffered

	go func() { c <- 7 }() // blocks until main is ready to receive
	fmt.Println(<-c)       // 7

	d := make(chan int, 1) // buffered
	d <- 1                 // does not block: there is room
	close(d)
	v, ok := <-d
	fmt.Println(v, ok) // 1 true   (buffered value survives close)
	v, ok = <-d
	fmt.Println(v, ok) // 0 false  (closed and drained)

	e := make(chan int)
	e <- 1 // fatal error: all goroutines are asleep - deadlock!
}
```
""",
        complexity="Each round is O(G²) because of the partner search; the number of rounds is at most the "
                   "total number of operations. Fine for test-sized inputs.",
        pitfalls="Waiting for *all* goroutines before declaring success (Go exits when main returns; the rest "
                 "are abandoned, which is what `leaked` counts). Checking rendezvous before the closed flag. "
                 "Letting a goroutine rendezvous with itself.",
        follow_up="Add `select`, or replace the round-robin rule with a search over all interleavings to find "
                  "whether *some* schedule deadlocks.",
    ),
),

# ------------------------------------------------------------------ go-select-sim
dict(
    id="go-select-sim",
    title="select with ready channels",
    difficulty="Medium",
    pattern="Go concurrency",
    entry="run_selects",
    description=r"""
`select` lets one goroutine wait on several channel operations at once:

```go
select {
case v := <-a:      // receive case
case b <- 1:        // send case
default:            // optional: runs when no case is ready
}
```

Rules of the real language: Go looks at all cases; if one or more are **ready** it picks one of them
**at random**; if none is ready it runs `default` when present and otherwise blocks.

To make answers checkable, replace "at random" by a fixed rule: **the k-th `select` statement
executed (counting from 0) picks ready case number `k mod r`**, where `r` is the number of ready
cases, listed in source order.

`chans` maps a channel name to `[capacity, initial_values, closed]`. Statements run in one goroutine:

- `["close", ch]`: closes the channel. Closing a closed channel outputs `"panic"` and stops.
- `["select", cases, has_default]` where a case is `["recv", ch]` or `["send", ch, v]`, and `ch` may be
  `None`, which stands for a **nil channel**.

When is a case ready?

- `recv`: the buffer holds a value, or the channel is closed.
- `send`: the buffer has room, or the channel is closed (the case is chosen and then panics).
- a nil channel is **never** ready, for both send and receive.

Output per select:

- chosen receive: `["recv", ch, value, ok]` (a closed, empty channel gives `0, false`);
- chosen send with room: `["send", ch]` and the value is stored;
- chosen send on a closed channel: `"panic"`, and the program stops;
- nothing ready, with default: `"default"`;
- nothing ready, no default: `"block"`, and the program stops (with a single goroutine this is a deadlock).

Return the list of outputs.

**Example 1:** `run_selects({"a": [1, [5], false]}, [["select", [["recv","a"]], false], ["select", [["recv","a"]], true]])`
→ `[["recv", "a", 5, true], "default"]`

**Example 2:** `run_selects({"a": [1, [], false]}, [["select", [["recv", None], ["send","a",9]], false], ["select", [["recv","a"]], false]])`
→ `[["send", "a"], ["recv", "a", 9, true]]`
""",
    starter='''def run_selects(chans, stmts):
    pass
''',
    solution='''def run_selects(chans, stmts):
    cap = {c: v[0] for c, v in chans.items()}
    buf = {c: list(v[1]) for c, v in chans.items()}
    closed = {c for c, v in chans.items() if v[2]}
    out = []
    k = 0
    for st in stmts:
        if st[0] == "close":
            if st[1] in closed:
                out.append("panic")
                break
            closed.add(st[1])
            continue
        cases, has_default = st[1], st[2]
        ready = []
        for c in cases:
            ch = c[1]
            if ch is None:
                continue
            if c[0] == "recv":
                if buf[ch] or ch in closed:
                    ready.append(c)
            elif ch in closed or len(buf[ch]) < cap[ch]:
                ready.append(c)
        index = k
        k += 1
        if not ready:
            if has_default:
                out.append("default")
                continue
            out.append("block")
            break
        c = ready[index % len(ready)]
        ch = c[1]
        if c[0] == "recv":
            if buf[ch]:
                out.append(["recv", ch, buf[ch].pop(0), True])
            else:
                out.append(["recv", ch, 0, False])
        else:
            if ch in closed:
                out.append("panic")
                break
            buf[ch].append(c[2])
            out.append(["send", ch])
    return out
''',
    tests=[
        [{"a": [1, [5], False]}, [["select", [["recv", "a"]], False], ["select", [["recv", "a"]], True]]],
        [{"a": [1, [], False]}, [["select", [["recv", None], ["send", "a", 9]], False], ["select", [["recv", "a"]], False]]],
        [{}, []],
        [{}, [["select", [], True], ["select", [], False], ["select", [], True]]],
        [{"a": [0, [], False]}, [["select", [["recv", "a"]], False]]],
        [{"a": [0, [], False]}, [["select", [["recv", "a"], ["send", "a", 1]], True], ["close", "a"],
                                 ["select", [["recv", "a"]], True], ["select", [["recv", "a"]], False]]],
        [{"a": [2, [1, 2], False], "b": [2, [10, 20], False]},
         [["select", [["recv", "a"], ["recv", "b"]], False]] * 5],
        [{"a": [2, [1, 2], False], "b": [2, [10, 20], False]},
         [["select", [["recv", "b"], ["recv", "a"]], True]] * 5],
        [{"a": [1, [], True]}, [["select", [["send", "a", 1]], True]]],
        [{"a": [1, [], False]}, [["close", "a"], ["close", "a"], ["select", [["recv", "a"]], True]]],
        [{"a": [1, [7], True]}, [["select", [["recv", "a"]], True], ["select", [["recv", "a"]], True],
                                 ["select", [["recv", "a"]], True]]],
        [{"out": [2, [], False]}, [["select", [["send", "out", i]], True] for i in range(4)]
         + [["select", [["recv", "out"]], True] for _ in range(3)]],
        [{"a": [1, [1], False], "b": [1, [], False], "c": [1, [3], False]},
         [["select", [["recv", "a"], ["send", "b", 2], ["recv", "c"], ["recv", None]], False]] * 4],
        [{"a": [1, [1], False]}, [["select", [["send", None, 1], ["recv", None]], True],
                                  ["select", [["send", None, 1]], False], ["select", [["recv", "a"]], False]]],
        [{"q": [1, [], False], "stop": [0, [], False]},
         [["select", [["recv", "stop"], ["send", "q", 1]], False], ["select", [["recv", "stop"], ["send", "q", 2]], True],
          ["close", "stop"], ["select", [["recv", "stop"], ["send", "q", 3]], False],
          ["select", [["recv", "q"], ["recv", "stop"]], False], ["select", [["recv", "q"], ["recv", "stop"]], False]]],
    ],
    examples=2,
    wrong_solutions=[
        '''def run_selects(chans, stmts):
    cap = {c: v[0] for c, v in chans.items()}; buf = {c: list(v[1]) for c, v in chans.items()}
    closed = {c for c, v in chans.items() if v[2]}; out = []
    for st in stmts:
        if st[0] == "close":
            if st[1] in closed: out.append("panic"); break
            closed.add(st[1]); continue
        ready = []
        for c in st[1]:
            ch = c[1]
            if ch is None: continue
            if c[0] == "recv":
                if buf[ch] or ch in closed: ready.append(c)
            elif ch in closed or len(buf[ch]) < cap[ch]: ready.append(c)
        if not ready:
            if st[2]: out.append("default"); continue
            out.append("block"); break
        c = ready[0]; ch = c[1]
        if c[0] == "recv":
            out.append(["recv", ch, buf[ch].pop(0), True] if buf[ch] else ["recv", ch, 0, False])
        else:
            if ch in closed: out.append("panic"); break
            buf[ch].append(c[2]); out.append(["send", ch])
    return out
''',
        '''def run_selects(chans, stmts):
    cap = {c: v[0] for c, v in chans.items()}; buf = {c: list(v[1]) for c, v in chans.items()}
    closed = {c for c, v in chans.items() if v[2]}; out = []; k = 0
    for st in stmts:
        if st[0] == "close":
            if st[1] in closed: out.append("panic"); break
            closed.add(st[1]); continue
        index = k; k += 1
        if st[2]:
            out.append("default"); continue
        ready = []
        for c in st[1]:
            ch = c[1]
            if ch is None: continue
            if c[0] == "recv":
                if buf[ch] or ch in closed: ready.append(c)
            elif ch in closed or len(buf[ch]) < cap[ch]: ready.append(c)
        if not ready:
            out.append("block"); break
        c = ready[index % len(ready)]; ch = c[1]
        if c[0] == "recv":
            out.append(["recv", ch, buf[ch].pop(0), True] if buf[ch] else ["recv", ch, 0, False])
        else:
            if ch in closed: out.append("panic"); break
            buf[ch].append(c[2]); out.append(["send", ch])
    return out
''',
    ],
    guide=dict(
        prereqs="Lesson: [select and concurrency patterns](#/lesson/go/go-select-patterns).",
        intuition="`select` is a waiter looking at several doors. Step one: which doors are open right now? "
                  "Step two: if some are, walk through one of them (here: by the fixed rule). If none are, take "
                  "the `default` exit if the room has one; otherwise stand and wait.",
        hints=[
            "Compute the list of ready cases first, in source order, skipping nil channels.",
            "`default` matters only when the ready list is empty. It is never 'one of the choices'.",
            "A closed channel is always ready to receive, and 'ready' to send (which then panics).",
        ],
        brute_force="Always taking the first ready case in source order is the most common wrong mental model "
                    "of `select`. Real Go randomises precisely so that programs cannot rely on case order.",
        approach=r"""
Per statement: build `ready`; branch on empty/non-empty; apply the chosen case to the buffers.

**Dry run** of the test with `a=[1,2]`, `b=[10,20]` and five identical `select { <-a; <-b }`:
k=0: both ready, `0 mod 2 = 0` → a gives 1. k=1: `1 mod 2 = 1` → b gives 10. k=2: index 0 → a gives 2.
k=3: only b is ready (r=1), `3 mod 1 = 0` → b gives 20. k=4: nothing ready, no default → `"block"`.

**The same construct in Go:**

```go
package main

import (
	"fmt"
	"time"
)

func main() {
	data := make(chan int, 1)
	var disabled chan int // nil channel: its case can never be chosen

	select {
	case v := <-data:
		fmt.Println("got", v)
	case <-disabled:
		fmt.Println("never printed")
	default:
		fmt.Println("nothing ready") // printed: data is empty
	}

	data <- 42
	select {
	case v := <-data:
		fmt.Println("got", v) // got 42
	case <-time.After(time.Second):
		fmt.Println("timed out")
	}
}
```
""",
        complexity="O(total number of cases).",
        pitfalls="Choosing `default` when a case is ready. Treating a nil channel as closed (nil blocks "
                 "forever; closed is always ready). Forgetting that the counter `k` advances for every select, "
                 "including those that take `default`.",
    ),
),

# ------------------------------------------------------------------ go-worker-pool
dict(
    id="go-worker-pool",
    title="Worker pool schedule",
    difficulty="Medium",
    pattern="Go concurrency",
    entry="schedule",
    description=r"""
A **worker pool** is a fixed number of goroutines that all read jobs from one shared channel. It
limits how much work runs at the same time.

`n` workers are numbered `0..n-1`. `jobs` is a list of `[arrival, duration]`, sorted by arrival
time. Jobs are handed out in that order (first come, first served) through an unbuffered channel:

- When a job reaches the front of the queue, if one or more workers are **idle at the job's arrival
  time** (their previous job ended at or before `arrival`), the idle worker with the **lowest number**
  takes it and starts at `arrival`.
- Otherwise the job waits for the worker that becomes free **earliest** (lowest number on ties) and
  starts the moment that worker is free.

Return `[assignments, makespan]`: `assignments[i] = [worker, start, end]` for job `i`, and
`makespan` is the time the last job ends (0 when there are no jobs).

**Example 1:** `schedule(2, [[0, 5], [0, 3], [1, 2]])` → `[[[0, 0, 5], [1, 0, 3], [1, 3, 5]], 5]`

**Example 2:** `schedule(2, [[0, 2], [10, 1]])` → `[[[0, 0, 2], [0, 10, 11]], 11]` (both idle at time 10: lowest number wins)
""",
    starter='''def schedule(n, jobs):
    pass
''',
    solution='''def schedule(n, jobs):
    free = [0] * n
    out = []
    for arrival, duration in jobs:
        worker = None
        for w in range(n):
            if free[w] <= arrival:
                worker = w
                break
        if worker is not None:
            start = arrival
        else:
            worker = min(range(n), key=lambda w: (free[w], w))
            start = free[worker]
        free[worker] = start + duration
        out.append([worker, start, start + duration])
    return [out, max((a[2] for a in out), default=0)]
''',
    tests=[
        [2, [[0, 5], [0, 3], [1, 2]]],
        [2, [[0, 2], [10, 1]]],
        [3, []],
        [1, [[0, 4], [1, 4], [2, 4]]],
        [4, [[0, 1], [0, 1], [0, 1]]],
        [2, [[0, 3], [0, 9], [5, 1], [5, 1]]],
        [3, [[0, 10], [1, 2], [2, 2], [3, 2], [4, 2], [5, 2]]],
        [2, [[0, 4], [0, 4], [1, 1], [1, 1], [1, 1]]],
        [3, [[5, 0], [5, 0], [5, 3], [5, 3]]],
        [2, [[0, 7], [3, 1], [3, 1], [20, 5], [21, 5], [22, 5]]],
        [5, [[i, 7] for i in range(30)]],
        [3, [[0, 6], [0, 2], [0, 2], [2, 1], [2, 1], [3, 5], [100, 1]]],
    ],
    examples=2,
    wrong_solutions=[
        '''def schedule(n, jobs):
    import heapq
    heap = [(0, w) for w in range(n)]
    out = []
    for a, d in jobs:
        f, w = heapq.heappop(heap)
        s = max(a, f)
        out.append([w, s, s + d])
        heapq.heappush(heap, (s + d, w))
    return [out, max((x[2] for x in out), default=0)]
''',
        '''def schedule(n, jobs):
    out = []
    for i, (a, d) in enumerate(jobs):
        out.append([i % n, a, a + d])
    return [out, max((x[2] for x in out), default=0)]
''',
    ],
    guide=dict(
        prereqs="Lists; optionally heaps. Lesson: [select and concurrency patterns](#/lesson/go/go-select-patterns).",
        intuition="Keep one number per worker: the time it becomes free. For each job, either somebody is "
                  "already free (pick the lowest number) or everybody is busy (pick whoever finishes first).",
        hints=[
            "An array `free[w]` is enough state.",
            "Check for idle workers *at the arrival time* before looking for the earliest finisher.",
            "A plain min-heap keyed by `(free_time, worker)` picks the worker that has been idle longest, not "
            "the lowest-numbered idle one. They differ.",
        ],
        brute_force="Stepping a clock one tick at a time and moving jobs when a worker is idle is correct but "
                    "its cost depends on the durations. Jumping directly from event to event is better.",
        approach=r"""
For each job scan the workers (O(n)); assign, update `free`.

**Dry run** of example 2: job `[0,2]`: all idle, worker 0, ends at 2. Job `[10,1]`: at time 10 both are idle
(`free = [2, 0]`), lowest number is worker 0 → `[0, 10, 11]`. A min-heap on free time would pick worker 1
(free since 0), which is the wrong answer for this rule.

**An idiomatic worker pool in Go:**

```go
package main

import (
	"fmt"
	"sync"
	"time"
)

func main() {
	jobs := make(chan int)
	results := make(chan string)
	var wg sync.WaitGroup

	for w := 0; w < 2; w++ { // two workers
		wg.Add(1)
		go func(id int) {
			defer wg.Done()
			for j := range jobs { // ends when jobs is closed and drained
				time.Sleep(time.Duration(j) * 10 * time.Millisecond)
				results <- fmt.Sprintf("worker %d finished job of size %d", id, j)
			}
		}(w)
	}

	go func() {
		for _, size := range []int{5, 3, 2} {
			jobs <- size
		}
		close(jobs)
		wg.Wait()
		close(results)
	}()

	for r := range results {
		fmt.Println(r)
	}
}
```

Which worker takes which job is up to the Go scheduler; this problem's fixed rule exists only so that
answers can be checked.
""",
        complexity="O(jobs × n) with the scan. With two heaps (idle workers by number, busy workers by finish "
                   "time) it becomes O(jobs × log n).",
        pitfalls="Round-robin assignment. A single heap on free time. Forgetting that a worker whose job ends "
                 "exactly at the arrival time counts as idle. Zero-duration jobs.",
    ),
),

# ------------------------------------------------------------------ go-pipeline-backpressure
dict(
    id="go-pipeline-backpressure",
    title="Pipeline with backpressure",
    difficulty="Hard",
    pattern="Go concurrency",
    entry="pipeline",
    description=r"""
A **pipeline** is a row of stages. Each stage is one goroutine that receives an item from the
channel on its left, works on it, and sends it to the channel on its right. When a later stage is
slow, the channel between them fills up and the earlier stage is forced to wait. That automatic
slowing-down is called **backpressure**.

There are `m` stages. Stage `i` needs `times[i]` time units per item and handles one item at a time,
in order. `caps[i]` (for `i = 0..m-2`) is the buffer capacity of the channel between stage `i` and
stage `i+1`. All `n_items` items are waiting in front of stage 0 at time 0; whatever leaves the
last stage is consumed immediately.

Life of item `k` at stage `i`:

1. It **starts** when it has arrived from stage `i-1` *and* stage `i` has handed off item `k-1`:
   `start[i][k] = max(depart[i-1][k], depart[i][k-1])` (missing terms count as 0).
2. It is **finished** at `fin = start[i][k] + times[i]`.
3. It **departs** (the send completes and the stage is free again):
   - last stage: `depart = fin`;
   - channel capacity `c >= 1`: there must be a free slot. A slot is held by an item from the moment
     it departs stage `i` until stage `i+1` starts it. So `depart[i][k] = max(fin, start[i+1][k-c])`,
     or `fin` when `k < c`;
   - capacity `0` (unbuffered): the hand-off happens when stage `i+1` is free:
     `depart[i][k] = max(fin, depart[i+1][k-1])`, or `fin` when `k = 0`.

The time a stage spends between `fin` and `depart` is time **blocked** by backpressure.

Return `[completion_times, blocked]`: the departure time of every item from the last stage, and for
each stage the total blocked time over all items.

**Example 1:** `pipeline(3, [1, 3], [0])` → `[[4, 7, 10], [4, 0]]` (stage 0 is blocked for 0 + 2 + 2 time units)

**Example 2:** `pipeline(3, [1, 3], [5])` → `[[4, 7, 10], [0, 0]]` (same throughput, but stage 0 is never blocked)
""",
    starter='''def pipeline(n_items, times, caps):
    # return [completion_times, blocked_per_stage]
    pass
''',
    solution='''def pipeline(n_items, times, caps):
    m = len(times)
    start = [[0] * n_items for _ in range(m)]
    depart = [[0] * n_items for _ in range(m)]
    blocked = [0] * m
    for k in range(n_items):
        for i in range(m):
            arrive = depart[i - 1][k] if i > 0 else 0
            prev = depart[i][k - 1] if k > 0 else 0
            s = max(arrive, prev)
            fin = s + times[i]
            start[i][k] = s
            if i == m - 1:
                d = fin
            else:
                c = caps[i]
                if c == 0:
                    d = max(fin, depart[i + 1][k - 1]) if k > 0 else fin
                elif k - c >= 0:
                    d = max(fin, start[i + 1][k - c])
                else:
                    d = fin
            depart[i][k] = d
            blocked[i] += d - fin
    return [depart[m - 1] if m else [], blocked]
''',
    tests=[
        [3, [1, 3], [0]],
        [3, [1, 3], [5]],
        [0, [2, 2], [1]],
        [4, [5], []],
        [5, [1, 1, 1], [0, 0]],
        [5, [3, 1], [0]],
        [6, [1, 4], [1]],
        [6, [1, 4], [2]],
        [6, [1, 2, 6], [1, 1]],
        [6, [1, 2, 6], [0, 3]],
        [8, [2, 5, 1, 4], [1, 0, 2]],
        [1, [7, 7, 7], [0, 0]],
        [10, [0, 3], [2]],
        [200, [1, 2, 3, 2, 1], [3, 0, 1, 5]],
    ],
    examples=2,
    wrong_solutions=[
        '''def pipeline(n_items, times, caps):
    m = len(times)
    done = [[0] * n_items for _ in range(m)]
    for k in range(n_items):
        for i in range(m):
            a = done[i - 1][k] if i > 0 else 0
            p = done[i][k - 1] if k > 0 else 0
            done[i][k] = max(a, p) + times[i]
    return [done[m - 1] if m else [], [0] * m]
''',
        '''def pipeline(n_items, times, caps):
    m = len(times)
    start = [[0] * n_items for _ in range(m)]
    depart = [[0] * n_items for _ in range(m)]
    blocked = [0] * m
    for k in range(n_items):
        for i in range(m):
            arrive = depart[i - 1][k] if i > 0 else 0
            prev = depart[i][k - 1] if k > 0 else 0
            s = max(arrive, prev); fin = s + times[i]; start[i][k] = s
            if i == m - 1: d = fin
            else:
                c = max(caps[i], 1)
                d = max(fin, start[i + 1][k - c]) if k - c >= 0 else fin
            depart[i][k] = d; blocked[i] += d - fin
    return [depart[m - 1] if m else [], blocked]
''',
    ],
    guide=dict(
        prereqs="Dynamic programming over a 2-D table. Lesson: "
                "[select and concurrency patterns](#/lesson/go/go-select-patterns).",
        intuition="Think of a car wash with several stations and a few parking spots between them. A car that "
                  "is finished at station 1 cannot leave until a spot ahead is free, and while it sits there, "
                  "station 1 cannot take the next car. Every number you need is 'the latest of the things I am "
                  "waiting for'.",
        hints=[
            "Fill two tables, `start[i][k]` and `depart[i][k]`, with items in the outer loop and stages in the inner loop.",
            "With that loop order, everything the formulas refer to (earlier item, or same item at the earlier "
            "stage) has already been computed.",
            "A slot frees when the *next stage starts* the item that was `c` positions earlier.",
        ],
        brute_force="A tick-by-tick simulation with explicit queues gives the same numbers in O(total time × "
                    "stages). The recurrence gets there in O(items × stages) regardless of how long stages take.",
        approach=r"""
Nested loops, one `max` per rule.

**Dry run** of example 1 (`times=[1,3]`, unbuffered). Item 0: stage 0 runs 0→1 and departs at 1; stage 1 runs
1→4. Item 1: stage 0 runs 1→2, but stage 1 is busy until 4, so it departs at 4 (blocked 2); stage 1 runs
4→7. Item 2: stage 0 runs 4→5, departs at 7 (blocked 2); stage 1 runs 7→10. Completions `[4,7,10]`, blocked `[4,0]`.

A bigger buffer (example 2) removes the blocking of stage 0 but does **not** make items finish earlier: the
slowest stage sets the throughput. Buffers smooth bursts; they do not fix a bottleneck.

**A pipeline in Go:**

```go
package main

import "fmt"

func generate(n int) <-chan int {
	out := make(chan int) // unbuffered: the generator feels backpressure at once
	go func() {
		defer close(out)
		for i := 1; i <= n; i++ {
			out <- i
		}
	}()
	return out
}

func square(in <-chan int) <-chan int {
	out := make(chan int, 2) // small buffer between stages
	go func() {
		defer close(out)
		for v := range in {
			out <- v * v // blocks here when the next stage is slow
		}
	}()
	return out
}

func main() {
	for v := range square(generate(4)) {
		fmt.Println(v) // 1 4 9 16
	}
}
```
""",
        complexity="O(n_items × stages) time and space.",
        pitfalls="Ignoring blocking altogether (the first wrong solution: correct completion times for the "
                 "last stage, wrong blocked totals). Treating an unbuffered channel as a buffer of one. "
                 "Using `depart` of the next stage where `start` is required for buffered channels.",
    ),
),

# ------------------------------------------------------------------ go-waitgroup-validate
dict(
    id="go-waitgroup-validate",
    title="WaitGroup counter checker",
    difficulty="Easy",
    pattern="Go concurrency",
    entry="waitgroup",
    description=r"""
`sync.WaitGroup` lets one goroutine wait for a group of others. It is a counter with three methods:

- `Add(n)` adds `n` to the counter (normally called before starting `n` goroutines);
- `Done()` subtracts 1 (called by each goroutine when it finishes);
- `Wait()` blocks until the counter is 0.

If the counter ever goes **below zero** the program panics with `sync: negative WaitGroup counter`.
If someone waits and the counter never returns to 0, that goroutine is stuck forever.

You get the events in the order they happened: `["add", n]` (`n` may be negative), `["done"]`, `["wait"]`.
Process them in order:

- `add`/`done` change the counter. If it becomes negative, return `["panic", index_of_event, waits_so_far]`.
- `wait` when the counter is 0 returns at once: record `"immediate"`.
- `wait` when the counter is positive blocks: record it as pending. When a later event brings the
  counter to 0, every pending wait is released; its record becomes the **index of that event**.
- A pending wait that is never released stays recorded as `"never"`.

At the end return `[status, counter, waits]` where `status` is `"deadlock"` if any wait is `"never"`,
else `"ok"`, and `waits` holds one record per `wait` event in order.

**Example 1:** `[["add", 2], ["wait"], ["done"], ["done"]]` → `["ok", 0, [3]]`

**Example 2:** `[["add", 1], ["done"], ["done"]]` → `["panic", 2, []]`

**Example 3:** `[["add", 2], ["done"], ["wait"]]` → `["deadlock", 1, ["never"]]`
""",
    starter='''def waitgroup(events):
    pass
''',
    solution='''def waitgroup(events):
    counter = 0
    waits = []
    pending = []
    for i, e in enumerate(events):
        if e[0] == "wait":
            if counter == 0:
                waits.append("immediate")
            else:
                pending.append(len(waits))
                waits.append("never")
            continue
        counter += e[1] if e[0] == "add" else -1
        if counter < 0:
            return ["panic", i, waits]
        if counter == 0:
            for w in pending:
                waits[w] = i
            pending = []
    return ["deadlock" if pending else "ok", counter, waits]
''',
    tests=[
        [[["add", 2], ["wait"], ["done"], ["done"]]],
        [[["add", 1], ["done"], ["done"]]],
        [[["add", 2], ["done"], ["wait"]]],
        [[]],
        [[["wait"], ["wait"]]],
        [[["done"]]],
        [[["add", 3], ["add", -3], ["wait"]]],
        [[["add", 1], ["wait"], ["add", 1], ["done"], ["wait"], ["done"], ["wait"]]],
        [[["add", 2], ["wait"], ["add", -5]]],
        [[["add", 1], ["wait"], ["done"], ["add", 1], ["wait"]]],
        [[["add", 0], ["wait"], ["add", 2], ["done"]]],
        [[["add", 50]] + [["done"]] * 49 + [["wait"], ["done"], ["wait"]]],
        [[["add", 1], ["wait"], ["wait"], ["add", -1], ["add", -1]]],
    ],
    examples=3,
    wrong_solutions=[
        '''def waitgroup(events):
    counter = 0; waits = []
    for i, e in enumerate(events):
        if e[0] == "wait":
            waits.append("immediate" if counter == 0 else "never")
            continue
        counter += e[1] if e[0] == "add" else -1
        if counter < 0:
            return ["panic", i, waits]
    return ["deadlock" if "never" in waits else "ok", counter, waits]
''',
        '''def waitgroup(events):
    counter = 0; waits = []; pending = []
    for i, e in enumerate(events):
        if e[0] == "wait":
            if counter == 0: waits.append("immediate")
            else: pending.append(len(waits)); waits.append("never")
            continue
        counter += e[1] if e[0] == "add" else -1
        if counter <= 0:
            for w in pending: waits[w] = i
            pending = []
        counter = max(counter, 0)
    return ["deadlock" if pending else "ok", counter, waits]
''',
    ],
    guide=dict(
        prereqs="Lesson: [WaitGroup, Mutex, Once, atomics and errgroup](#/lesson/go/go-sync-primitives).",
        intuition="A WaitGroup is a tally of 'jobs still running'. Waiting means 'tell me when the tally hits "
                  "zero'. The two classic bugs are a tally that goes negative (too many `Done`) and one that "
                  "never reaches zero (a missing `Done`).",
        hints=[
            "Keep the counter and a list of positions of waits that are still blocked.",
            "Check for a negative counter before checking for zero.",
            "When the counter reaches zero, release *all* pending waits with the same event index.",
        ],
        brute_force="Direct simulation is already optimal.",
        approach=r"""
Single pass.

**Dry run** of example 1: `add 2` → 2. `wait` → pending (record 0 is `"never"` for now). `done` → 1. `done` → 0 at
event index 3 → the record becomes 3. Result `["ok", 0, [3]]`.

**Correct use in Go:**

```go
package main

import (
	"fmt"
	"sync"
)

func main() {
	var wg sync.WaitGroup
	results := make([]int, 3)

	for i := range results {
		wg.Add(1) // in the parent, BEFORE the go statement
		go func() {
			defer wg.Done() // always runs, even if the work panics
			results[i] = i * i
		}()
	}

	wg.Wait() // blocks until all three called Done
	fmt.Println(results) // [0 1 4]
}
```

Calling `wg.Add(1)` *inside* the goroutine is a race: `Wait` may run before any `Add` and return immediately.
Since Go 1.25 `wg.Go(func() { ... })` does the Add/Done pair for you.
""",
        complexity="O(number of events).",
        pitfalls="Releasing waiters when the counter is negative. Forgetting that several waiters can be "
                 "pending. Reporting `ok` when a wait is still blocked at the end.",
    ),
),

# ------------------------------------------------------------------ go-mutex-timeline
dict(
    id="go-mutex-timeline",
    title="Mutex and RWMutex contention timeline",
    difficulty="Medium",
    pattern="Go concurrency",
    entry="lock_timeline",
    description=r"""
A **mutex** (mutual exclusion lock) lets only one goroutine at a time into a protected section of
code. Go's `sync.RWMutex` is a refinement: any number of **readers** may hold it together, but a
**writer** needs it alone.

Each request is `[arrival, hold, mode]`: the goroutine asks for the lock at time `arrival`, keeps it
for `hold` time units once granted, and `mode` is `"r"` (read lock, `RLock`) or `"w"` (write lock, `Lock`).

Use this deterministic, fair model:

- Requests are served in order of arrival (ties: lower index in the input first). **No overtaking**:
  a request is never granted before a request that is ahead of it in that order. (This models the fact
  that in Go a waiting writer blocks readers that arrive later, so writers do not starve.)
- A **reader** is granted at the earliest time that is: at or after its arrival, not before the grant
  time of the request ahead of it, and not before every **writer** ahead of it has released.
- A **writer** is granted at the earliest time that is: at or after its arrival, not before the grant
  time of the request ahead of it, and not before **every** request ahead of it has released.

Return `[timeline, total_wait]`: `timeline[i] = [grant, release]` for request `i` (input order), and
`total_wait` is the sum of `grant - arrival`.

**Example 1:** `lock_timeline([[0, 5, "w"], [1, 2, "w"]])` → `[[[0, 5], [5, 7]], 4]`

**Example 2:** `lock_timeline([[0, 5, "r"], [1, 2, "r"]])` → `[[[0, 5], [1, 3]], 0]` (readers share)

**Example 3:** `lock_timeline([[0, 5, "r"], [1, 2, "w"], [2, 1, "r"]])` → `[[[0, 5], [5, 7], [7, 8]], 9]`
(the late reader queues behind the waiting writer)
""",
    starter='''def lock_timeline(requests):
    pass
''',
    solution='''def lock_timeline(requests):
    order = sorted(range(len(requests)), key=lambda i: (requests[i][0], i))
    res = [None] * len(requests)
    prev_grant = 0
    last_writer_release = 0
    max_release = 0
    for i in order:
        arrival, hold, mode = requests[i]
        barrier = last_writer_release if mode == "r" else max_release
        grant = max(arrival, prev_grant, barrier)
        release = grant + hold
        res[i] = [grant, release]
        prev_grant = grant
        max_release = max(max_release, release)
        if mode == "w":
            last_writer_release = max(last_writer_release, release)
    return [res, sum(res[i][0] - requests[i][0] for i in range(len(requests)))]
''',
    tests=[
        [[[0, 5, "w"], [1, 2, "w"]]],
        [[[0, 5, "r"], [1, 2, "r"]]],
        [[[0, 5, "r"], [1, 2, "w"], [2, 1, "r"]]],
        [[]],
        [[[3, 4, "w"]]],
        [[[5, 1, "w"], [0, 2, "w"], [0, 2, "w"]]],
        [[[0, 10, "r"], [0, 10, "r"], [0, 10, "r"], [1, 1, "w"]]],
        [[[0, 1, "w"], [0, 3, "r"], [0, 3, "r"], [0, 1, "w"], [0, 2, "r"]]],
        [[[0, 2, "r"], [10, 2, "w"], [20, 2, "r"]]],
        [[[0, 4, "r"], [1, 10, "r"], [2, 1, "w"], [3, 1, "r"], [3, 1, "w"]]],
        [[[0, 0, "w"], [0, 0, "w"], [0, 0, "r"]]],
        [[[i, 3, "w"] for i in range(50)]],
        [[[i, 3, "r"] for i in range(50)] + [[10, 1, "w"]]],
    ],
    examples=3,
    wrong_solutions=[
        '''def lock_timeline(requests):
    order = sorted(range(len(requests)), key=lambda i: (requests[i][0], i))
    res = [None] * len(requests); free = 0
    for i in order:
        a, h, mode = requests[i]
        g = max(a, free); free = g + h
        res[i] = [g, free]
    return [res, sum(res[i][0] - requests[i][0] for i in range(len(requests)))]
''',
        '''def lock_timeline(requests):
    res = [None] * len(requests); pg = 0; lw = 0; mr = 0
    for i in range(len(requests)):
        a, h, mode = requests[i]
        g = max(a, pg, lw if mode == "r" else mr)
        res[i] = [g, g + h]; pg = g; mr = max(mr, g + h)
        if mode == "w": lw = max(lw, g + h)
    return [res, sum(res[i][0] - requests[i][0] for i in range(len(requests)))]
''',
    ],
    guide=dict(
        prereqs="Sorting with a key. Lesson: [WaitGroup, Mutex, Once, atomics and errgroup](#/lesson/go/go-sync-primitives).",
        intuition="Imagine a single queue at a door. Readers may walk in together; a writer needs the room "
                  "empty. Because nobody jumps the queue, each person only needs three facts: when they "
                  "arrived, when the person in front got in, and when the people in front who conflict with "
                  "them leave.",
        hints=[
            "Sort indexes by `(arrival, index)` but write answers back in input order.",
            "Carry three running values: previous grant time, latest writer release, latest release of anyone.",
            "Readers wait for writers only; writers wait for everybody.",
        ],
        brute_force="A time-stepped simulation with an explicit queue and a set of holders works and is "
                    "easier to trust; it costs O(total time). The three running maxima give O(n log n).",
        approach=r"""
Sort, then one pass with `grant = max(arrival, prev_grant, barrier)`.

**Dry run** of example 3: reader A `[0,5]` → granted 0, releases 5. Writer B arrives 1: must wait for every
release ahead (5) → granted 5, releases 7. Reader C arrives 2: no overtaking (B's grant is 5) and must wait
for writer B's release (7) → granted 7, releases 8. Waits: 0 + 4 + 5 = 9. Without the no-overtaking rule C
would have joined A at time 2; a steady stream of such readers would starve B forever.

**Mutexes in Go:**

```go
package main

import (
	"fmt"
	"sync"
)

type Cache struct {
	mu   sync.RWMutex
	data map[string]string
}

func (c *Cache) Get(k string) (string, bool) {
	c.mu.RLock() // many readers may be here together
	defer c.mu.RUnlock()
	v, ok := c.data[k]
	return v, ok
}

func (c *Cache) Set(k, v string) {
	c.mu.Lock() // exclusive
	defer c.mu.Unlock()
	c.data[k] = v
}

func main() {
	c := &Cache{data: map[string]string{}}
	c.Set("lang", "go")
	fmt.Println(c.Get("lang")) // go true
}
```
""",
        complexity="O(n log n) for the sort, O(n) for the pass.",
        pitfalls="Letting readers overtake a waiting writer. Treating everything as an exclusive lock. "
                 "Processing in input order when the input is not sorted by arrival.",
    ),
),

# ------------------------------------------------------------------ go-gmp-scheduler
dict(
    id="go-gmp-scheduler",
    title="G-M-P scheduler with work stealing",
    difficulty="Hard",
    pattern="Go runtime",
    entry="gmp",
    description=r"""
The Go runtime runs many goroutines on few operating-system threads. Its scheduler is described by
three letters:

- **G**: a goroutine (a piece of work);
- **M**: a machine, meaning an operating-system thread that executes code;
- **P**: a processor, a scheduling slot that owns a **local run queue** of goroutines. An M must hold
  a P to run Go code, so the number of Ps is the number of goroutines that can run at the same instant.

There is also one **global run queue** shared by all Ps. A P with nothing to do **steals** work from
another P. Simulate a simplified scheduler in rounds.

Input: `local[p]` is P number `p`'s local queue, a list of `[gid, work]`; `global_q` has the same
shape; `quantum` is how much work a goroutine does in one round; `global_every` is a fairness
period (see rule 1).

In round `r` (starting at 1) each P, **in index order**, picks one goroutine:

1. If `r` is a multiple of `global_every` and the global queue is not empty, take the **front of the
   global queue** (this stops goroutines there from starving).
2. Otherwise, if its local queue is not empty, take the front of the local queue.
3. Otherwise, if the global queue is not empty, take its front.
4. Otherwise **steal**: choose the P with the longest local queue at this moment (lowest index on
   ties). If that queue is empty, stay idle this round. Otherwise remove the first `ceil(len / 2)`
   goroutines from the front of the victim's queue; run the first of them and append the others to
   your own local queue in the same order.

After every P has picked, all picked goroutines run: `work -= quantum`. A goroutine whose work is
now `<= 0` is finished in round `r`. An unfinished one is appended to the **back of the local queue
of the P that ran it** (processed in P index order).

Rounds repeat until all queues are empty. Return `[trace, finished]`: `trace[r-1]` lists, per P, the
`gid` it ran in round `r` (`None` if idle), and `finished` is the list of `[gid, round]` sorted by `gid`.

**Example:** `gmp([[[1, 2], [2, 1]], []], [], 1, 61)`

Round 1: P0 takes G1. P1 is empty, global is empty, so it steals from P0 (queue `[G2]`, takes `ceil(1/2) = 1`)
and runs G2. G1 has 1 unit left and goes back to P0; G2 is finished. Round 2: P0 runs G1; P1 is idle.

→ `[[[1, 2], [1, None]], [[1, 2], [2, 1]]]`
""",
    starter='''def gmp(local, global_q, quantum, global_every):
    # return [trace, finished]
    pass
''',
    solution='''def gmp(local, global_q, quantum, global_every):
    local = [[list(g) for g in q] for q in local]
    glob = [list(g) for g in global_q]
    n = len(local)
    trace = []
    finished = {}
    rnd = 0
    while n and (glob or any(local)):
        rnd += 1
        running = []
        for p in range(n):
            g = None
            if rnd % global_every == 0 and glob:
                g = glob.pop(0)
            elif local[p]:
                g = local[p].pop(0)
            elif glob:
                g = glob.pop(0)
            else:
                victim = max(range(n), key=lambda v: (len(local[v]), -v))
                if local[victim]:
                    k = (len(local[victim]) + 1) // 2
                    stolen = local[victim][:k]
                    local[victim] = local[victim][k:]
                    g = stolen[0]
                    local[p].extend(stolen[1:])
            running.append(g)
        row = []
        for p, g in enumerate(running):
            if g is None:
                row.append(None)
                continue
            row.append(g[0])
            g[1] -= quantum
            if g[1] <= 0:
                finished[g[0]] = rnd
            else:
                local[p].append(g)
        trace.append(row)
    return [trace, [[gid, r] for gid, r in sorted(finished.items())]]
''',
    tests=[
        [[[[1, 2], [2, 1]], []], [], 1, 61],
        [[[], []], [], 1, 61],
        [[[[1, 1]]], [], 1, 61],
        [[[[1, 5]]], [], 2, 61],
        [[[], []], [[1, 1], [2, 1], [3, 1]], 1, 61],
        [[[[1, 3], [2, 3], [3, 3], [4, 3]], [], []], [], 1, 61],
        [[[[1, 4]], [[2, 4]]], [[9, 1]], 1, 2],
        [[[[1, 4]], [[2, 4]]], [[9, 1]], 1, 61],
        [[[[1, 2], [2, 2], [3, 2], [4, 2], [5, 2]], [[6, 1]], []], [[7, 3], [8, 1]], 2, 3],
        [[[[1, 10]], [], [], []], [], 3, 61],
        [[[[1, 1], [2, 1], [3, 1]], [[4, 1], [5, 1], [6, 1]]], [], 1, 1],
        [[[[i, (i % 4) + 1] for i in range(1, 9)], [], [[20, 6]], []], [[30, 2], [31, 2]], 1, 4],
        [[[[1, 3], [2, 3]], [[3, 3], [4, 3]]], [[5, 3], [6, 3]], 1, 1],
    ],
    examples=1,
    wrong_solutions=[
        '''def gmp(local, global_q, quantum, global_every):
    local = [[list(g) for g in q] for q in local]; glob = [list(g) for g in global_q]
    n = len(local); trace = []; fin = {}; r = 0
    while n and (glob or any(local)):
        r += 1; running = []
        for p in range(n):
            g = None
            if r % global_every == 0 and glob: g = glob.pop(0)
            elif local[p]: g = local[p].pop(0)
            elif glob: g = glob.pop(0)
            running.append(g)
        row = []
        for p, g in enumerate(running):
            if g is None: row.append(None); continue
            row.append(g[0]); g[1] -= quantum
            if g[1] <= 0: fin[g[0]] = r
            else: local[p].append(g)
        trace.append(row)
    return [trace, [[a, b] for a, b in sorted(fin.items())]]
''',
        '''def gmp(local, global_q, quantum, global_every):
    local = [[list(g) for g in q] for q in local]; glob = [list(g) for g in global_q]
    n = len(local); trace = []; fin = {}; r = 0
    while n and (glob or any(local)):
        r += 1; running = []
        for p in range(n):
            g = None
            if local[p]: g = local[p].pop(0)
            elif glob: g = glob.pop(0)
            else:
                v = max(range(n), key=lambda x: (len(local[x]), -x))
                if local[v]:
                    k = (len(local[v]) + 1) // 2
                    st = local[v][:k]; local[v] = local[v][k:]
                    g = st[0]; local[p].extend(st[1:])
            running.append(g)
        row = []
        for p, g in enumerate(running):
            if g is None: row.append(None); continue
            row.append(g[0]); g[1] -= quantum
            if g[1] <= 0: fin[g[0]] = r
            else: local[p].append(g)
        trace.append(row)
    return [trace, [[a, b] for a, b in sorted(fin.items())]]
''',
        '''def gmp(local, global_q, quantum, global_every):
    local = [[list(g) for g in q] for q in local]; glob = [list(g) for g in global_q]
    n = len(local); trace = []; fin = {}; r = 0
    while n and (glob or any(local)):
        r += 1; running = []
        for p in range(n):
            g = None
            if r % global_every == 0 and glob: g = glob.pop(0)
            elif local[p]: g = local[p].pop(0)
            elif glob: g = glob.pop(0)
            else:
                v = max(range(n), key=lambda x: (len(local[x]), -x))
                if local[v]:
                    g = local[v].pop()
            running.append(g)
        row = []
        for p, g in enumerate(running):
            if g is None: row.append(None); continue
            row.append(g[0]); g[1] -= quantum
            if g[1] <= 0: fin[g[0]] = r
            else: local[p].append(g)
        trace.append(row)
    return [trace, [[a, b] for a, b in sorted(fin.items())]]
''',
    ],
    guide=dict(
        prereqs="Queues and simulation. Lesson: "
                "[Runtime questions: scheduler, escape analysis and GC](#/lesson/go/go-interview-runtime).",
        intuition="Each P is a cashier with their own line. A cashier with an empty line first looks at the "
                  "shared overflow line, and if that is empty too, walks over to the busiest colleague and "
                  "takes half of their line. Every so often every cashier serves the overflow line first so "
                  "nobody there waits forever.",
        hints=[
            "Copy the input lists; you will mutate them.",
            "Split a round into two phases: everybody picks (sequentially, P0 first), then everybody runs. "
            "Re-queue unfinished goroutines only in the second phase.",
            "For stealing: `k = (len + 1) // 2`, take `victim[:k]`, run the first, keep the rest.",
        ],
        brute_force="A single shared queue for all Ps (no local queues, no stealing) is the simplest "
                    "scheduler. It is also how Go worked before version 1.1, and it scaled badly because every "
                    "pick needed a global lock.",
        approach=r"""
Loop while any queue is non-empty; implement the four pick rules in order; then the run phase.

**Dry run** of the test `local=[[G1:4],[G2:4]]`, `global=[G9:1]`, quantum 1, `global_every=2`.
Round 1: P0 runs G1, P1 runs G2 (both from local queues); G9 keeps waiting. Round 2 is a multiple of 2:
P0 takes G9 from the global queue first; P1 finds the global queue empty and runs G2. With
`global_every=61` instead, G9 would wait until both local goroutines finished, which is the starvation
that rule 1 prevents (the real runtime checks the global queue every 61st scheduling tick).

**Watching the real scheduler from Go:**

```go
package main

import (
	"fmt"
	"runtime"
	"sync"
)

func main() {
	fmt.Println("Ps:", runtime.GOMAXPROCS(0)) // number of Ps (defaults to the CPU count)

	var wg sync.WaitGroup
	for i := 0; i < 8; i++ {
		wg.Add(1)
		go func() { // each go statement creates a G, queued on the current P
			defer wg.Done()
			sum := 0
			for j := 0; j < 1_000_000; j++ {
				sum += j
			}
		}()
	}
	wg.Wait()
	fmt.Println("goroutines now:", runtime.NumGoroutine()) // 1
}
```

```text
$ GODEBUG=schedtrace=1000 ./prog     # prints one scheduler summary line per second
```
""",
        complexity="O(rounds × P) picks plus the stealing slices; rounds ≤ total work / quantum.",
        pitfalls="Re-queueing a goroutine before all Ps have picked (it could be stolen and run twice in one "
                 "round). Stealing from the back or stealing only one. Ignoring the periodic global-queue "
                 "check. Rounding the stolen half down, which steals nothing from a queue of length 1.",
        follow_up="The real runtime adds `runnext` (a one-slot fast lane per P), the network poller, sysmon "
                  "preemption every 10 ms, and hands a P to another M when a goroutine blocks in a system call.",
    ),
),
]
