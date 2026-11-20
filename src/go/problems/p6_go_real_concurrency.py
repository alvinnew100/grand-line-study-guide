"""Real Go problems, part 2 (kind="go"): goroutines, channels, sync, context, and interview classics.

All concurrent problems have deterministic expected results. Timing checks use generous margins, and
every blocking call in the harness is wrapped in `within`, which reports a timeout instead of hanging.
"""


def harness(checks, imports=(), pre=""):
    imps = sorted(set(["fmt"]) | set(imports))
    lines = ["package main", "", "import ("]
    lines += ['\t"%s"' % i for i in imps]
    lines += [
        ")", "",
        "var caseNo int", "",
        "func check(f func() (any, any)) {",
        "\tcaseNo++",
        "\tdefer func() {",
        "\t\tif r := recover(); r != nil {",
        '\t\t\tfmt.Println("CASE", caseNo, "FAIL", "panic:", r)',
        "\t\t}",
        "\t}()",
        "\tgot, want := f()",
        "\tif fmt.Sprint(got) == fmt.Sprint(want) {",
        '\t\tfmt.Println("CASE", caseNo, "OK")',
        "\t} else {",
        '\t\tfmt.Println("CASE", caseNo, "FAIL", "got", got, "want", want)',
        "\t}",
        "}", "",
    ]
    if pre:
        lines += [pre.strip("\n"), ""]
    lines.append("func main() {")
    for c in checks:
        if isinstance(c, str):
            lines.append("\tcheck(func() (any, any) { %s })" % c)
        else:
            lines.append("\tcheck(func() (any, any) { return %s, %s })" % c)
    lines.append("}")
    return "\n".join(lines) + "\n"


def G(prereqs, intuition, hints, brute, approach, complexity, pitfalls):
    return dict(prereqs=prereqs, intuition=intuition, hints=hints, brute_force=brute,
                approach=approach, complexity=complexity, pitfalls=pitfalls)


LOGIN = "\n\n*This problem is compiled and run as real Go on the judge server, so you need to be logged in to run it.*\n"

WITHIN = '''// within runs f and reports a timeout instead of blocking for ever.
func within(f func() any) any {
	ch := make(chan any, 1)
	go func() {
		defer func() {
			if r := recover(); r != nil {
				ch <- fmt.Sprint("panic: ", r)
			}
		}()
		ch <- f()
	}()
	select {
	case v := <-ch:
		return v
	case <-time.After(1500 * time.Millisecond):
		return "timeout: a goroutine is blocked"
	}
}
'''

PROBLEMS = [
# ------------------------------------------------------------------ parallel map
dict(
    id="go-real-parallel-map", title="Run work in goroutines, keep the order", difficulty="Medium", pattern="Go concurrency", kind="go", cases=8,
    description=r"""
Write `func ParallelMap(xs []int, f func(int) int) []int`.

It must call `f` once for every element of `xs`, **each call in its own goroutine**, wait for all of them with a
`sync.WaitGroup`, and return the results **in the same order as the input** (`out[i] == f(xs[i])`).

The tests use a slow `f` and check that the whole call finishes much faster than running the calls one after another.

**Example:** `ParallelMap([]int{1, 2, 3}, square)` → `[1 4 9]`
""" + LOGIN,
    starter='package main\n\n// ParallelMap applies f to every element concurrently and keeps the input order.\nfunc ParallelMap(xs []int, f func(int) int) []int {\n\t// your code\n\treturn nil\n}\n',
    solution='package main\n\nimport "sync"\n\n// ParallelMap applies f to every element concurrently and keeps the input order.\nfunc ParallelMap(xs []int, f func(int) int) []int {\n\tout := make([]int, len(xs))\n\tvar wg sync.WaitGroup\n\tfor i, x := range xs {\n\t\twg.Add(1)\n\t\tgo func(i, x int) {\n\t\t\tdefer wg.Done()\n\t\t\tout[i] = f(x) // each goroutine writes its own element\n\t\t}(i, x)\n\t}\n\twg.Wait()\n\treturn out\n}\n',
    wrong_solutions=[
        'package main\n\nfunc ParallelMap(xs []int, f func(int) int) []int {\n\tout := make([]int, len(xs))\n\tfor i, x := range xs {\n\t\tout[i] = f(x)\n\t}\n\treturn out\n}\n',
        'package main\n\nimport "sync"\n\nfunc ParallelMap(xs []int, f func(int) int) []int {\n\tout := make([]int, 0, len(xs))\n\tvar wg sync.WaitGroup\n\tvar mu sync.Mutex\n\tfor _, x := range xs {\n\t\twg.Add(1)\n\t\tgo func(x int) {\n\t\t\tdefer wg.Done()\n\t\t\tv := f(x)\n\t\t\tmu.Lock()\n\t\t\tout = append(out, v)\n\t\t\tmu.Unlock()\n\t\t}(x)\n\t}\n\twg.Wait()\n\treturn out\n}\n',
    ],
    harness=harness([
        "return within(func() any { return ParallelMap([]int{1, 2, 3}, func(n int) int { return n * n }) }), []int{1, 4, 9}",
        "return within(func() any { return len(ParallelMap(nil, func(n int) int { return n })) }), 0",
        "return within(func() any { return ParallelMap([]int{7}, func(n int) int { return n + 1 }) }), []int{8}",
        "return within(func() any { return ParallelMap([]int{1, 2, 3, 4, 5, 6}, slowSquare) }), []int{1, 4, 9, 16, 25, 36}",
        "return within(func() any { start := time.Now(); ParallelMap([]int{1, 2, 3, 4, 5, 6}, slowSquare); return time.Since(start) < 200*time.Millisecond }), true",
        "return within(func() any { var calls atomic.Int64; ParallelMap(make([]int, 50), func(n int) int { calls.Add(1); return n }); return calls.Load() }), 50",
        "return within(func() any { in := []int{3, 2, 1}; ParallelMap(in, slowSquare); return in }), []int{3, 2, 1}",
        "return within(func() any { out := ParallelMap([]int{6, 1, 6, 1}, slowSquare); return out }), []int{36, 1, 36, 1}",
    ], imports=["time", "sync/atomic"], pre=WITHIN + '''
// slowSquare sleeps longer for SMALLER inputs, so results finish in reverse order.
func slowSquare(n int) int {
	time.Sleep(time.Duration(7-n) * 15 * time.Millisecond)
	return n * n
}'''),
    guide=G(
        "[Goroutines and channels](#/lesson/go/go-goroutines-channels), [WaitGroup, Mutex, Once, atomics and errgroup](#/lesson/go/go-sync-primitives).",
        "Allocate the result slice first with the right length. Give each goroutine its index; it writes only `out[i]`. Different elements of a slice are different variables, so no lock is needed, and the order is fixed by the index, not by who finishes first.",
        ["`out := make([]int, len(xs))`.", "`wg.Add(1)` before each `go`, `defer wg.Done()` inside.", "Pass `i` and `x` to the goroutine as arguments and store `out[i] = f(x)`; call `wg.Wait()` before returning."],
        "A plain loop calling `f` gives the right answer and takes the sum of all durations. Appending results as goroutines finish is concurrent but returns them in completion order.",
        "**Dry run:** inputs `[1 2 3]` → three goroutines. Whatever order they finish in, goroutine 0 writes `out[0]`, goroutine 1 writes `out[1]`, goroutine 2 writes `out[2]` → `[1 4 9]`.\n\n"
        "```go\nout := make([]int, len(xs))\nvar wg sync.WaitGroup\nfor i, x := range xs {\n\twg.Add(1)\n\tgo func(i, x int) {\n\t\tdefer wg.Done()\n\t\tout[i] = f(x)\n\t}(i, x)\n}\nwg.Wait()\nreturn out\n```",
        "Wall-clock time is about the slowest single call; total work is O(n). Space O(n).",
        "Returning before `wg.Wait()`. `wg.Add` inside the goroutine. Appending to a shared slice (a data race without a mutex, and the wrong order with one).",
    ),
),
# ------------------------------------------------------------------ safe counter
dict(
    id="go-real-safe-counter", title="A counter that is safe for goroutines", difficulty="Medium", pattern="Go concurrency", kind="go", cases=8,
    description=r"""
Define a type `SafeCounter` with methods:

- `Inc()` adds 1;
- `Add(n int)` adds `n`;
- `Value() int` returns the current total.

Many goroutines will call these methods at the same time, so protect the number with a `sync.Mutex` stored in the
struct. The zero value (`var c SafeCounter`) must be ready to use.
""" + LOGIN,
    starter='package main\n\nimport "sync"\n\n// SafeCounter is a counter that may be used from many goroutines.\ntype SafeCounter struct {\n\tmu sync.Mutex // protects n\n\tn  int\n}\n\n// Inc adds one.\nfunc (c *SafeCounter) Inc() {\n\t// your code\n}\n\n// add Add and Value\n',
    solution='package main\n\nimport "sync"\n\n// SafeCounter is a counter that may be used from many goroutines.\ntype SafeCounter struct {\n\tmu sync.Mutex // protects n\n\tn  int\n}\n\n// Inc adds one.\nfunc (c *SafeCounter) Inc() { c.Add(1) }\n\n// Add adds n.\nfunc (c *SafeCounter) Add(n int) {\n\tc.mu.Lock()\n\tdefer c.mu.Unlock()\n\tc.n += n\n}\n\n// Value returns the current total.\nfunc (c *SafeCounter) Value() int {\n\tc.mu.Lock()\n\tdefer c.mu.Unlock()\n\treturn c.n\n}\n',
    wrong_solutions=[
        'package main\n\nimport "sync"\n\ntype SafeCounter struct {\n\tmu *sync.Mutex\n\tn  int\n}\n\nfunc (c SafeCounter) Inc()       { c.n++ }\nfunc (c SafeCounter) Add(n int)  { c.n += n }\nfunc (c SafeCounter) Value() int { return c.n }\n',
        'package main\n\nimport "sync"\n\ntype SafeCounter struct {\n\tmu sync.Mutex\n\tn  int\n}\n\nfunc (c *SafeCounter) Inc() {\n\tc.mu.Lock()\n\tdefer c.mu.Unlock()\n\tc.n++\n}\n\nfunc (c *SafeCounter) Add(n int) {\n\tc.mu.Lock()\n\tdefer c.mu.Unlock()\n\tc.n++\n}\n\nfunc (c *SafeCounter) Value() int {\n\tc.mu.Lock()\n\tdefer c.mu.Unlock()\n\treturn c.n\n}\n',
    ],
    harness=harness([
        "var c SafeCounter; return c.Value(), 0",
        "var c SafeCounter; c.Inc(); c.Inc(); return c.Value(), 2",
        "var c SafeCounter; c.Add(5); c.Add(-2); return c.Value(), 3",
        "return within(func() any { var c SafeCounter; hammer(&c, 50, 200); return c.Value() }), 10000",
        "return within(func() any { var c SafeCounter; var wg sync.WaitGroup; for i := 1; i <= 100; i++ { wg.Add(1); go func(i int) { defer wg.Done(); c.Add(i) }(i) }; wg.Wait(); return c.Value() }), 5050",
        "var a, b SafeCounter; a.Inc(); b.Add(10); return fmt.Sprint(a.Value(), b.Value()), \"1 10\"",
        "return within(func() any { var c SafeCounter; hammer(&c, 8, 1000); c.Add(-8000); return c.Value() }), 0",
        "return within(func() any { var c SafeCounter; done := make(chan bool); go func() { for i := 0; i < 500; i++ { _ = c.Value() }; done <- true }(); hammer(&c, 4, 500); <-done; return c.Value() }), 2000",
    ], imports=["sync", "time"], pre=WITHIN + '''
func hammer(c *SafeCounter, goroutines, perGoroutine int) {
	var wg sync.WaitGroup
	for g := 0; g < goroutines; g++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for i := 0; i < perGoroutine; i++ {
				c.Inc()
			}
		}()
	}
	wg.Wait()
}'''),
    guide=G(
        "[WaitGroup, Mutex, Once, atomics and errgroup](#/lesson/go/go-sync-primitives).",
        "`n++` is read, add, write. If two goroutines interleave those steps an update is lost. A mutex lets only one goroutine at a time run the read-modify-write.",
        ["Keep the mutex in the struct, next to the field it protects.", "Every method locks, defers the unlock, then touches `c.n`; that includes `Value`.", "Use pointer receivers. A value receiver would copy the struct and lock a copy of the mutex."],
        "An unprotected `int` passes single-goroutine tests and loses updates under concurrency; the race detector (`go test -race`) reports it.",
        "**Dry run:** 50 goroutines × 200 `Inc` calls. Each call holds the lock for the whole `c.n += 1`, so no two overlap: the total is exactly 10000.\n\n"
        "```go\nfunc (c *SafeCounter) Add(n int) {\n\tc.mu.Lock()\n\tdefer c.mu.Unlock()\n\tc.n += n\n}\n\nfunc (c *SafeCounter) Value() int {\n\tc.mu.Lock()\n\tdefer c.mu.Unlock()\n\treturn c.n\n}\n```\n\n"
        "For a single number, `atomic.Int64` with `Add` and `Load` is an equally valid solution.",
        "O(1) per call.",
        "Value receivers (nothing is ever counted). Locking writes and not reads. Calling a locking method from another method while holding the lock: Go's mutex is not re-entrant and would deadlock.",
    ),
),
# ------------------------------------------------------------------ worker pool
dict(
    id="go-real-worker-pool", title="Worker pool with a concurrency limit", difficulty="Hard", pattern="Go concurrency", kind="go", cases=9,
    description=r"""
Write `func ProcessAll(jobs []int, workers int, f func(int) int) []int`.

- Start exactly `workers` goroutines (assume `workers >= 1`). They take jobs from a shared channel.
- Each job `jobs[i]` is processed by calling `f` once; the result goes to position `i` of the returned slice.
- **At no moment may more than `workers` calls of `f` be running.** The tests measure this.
- Return when every job is done.

**Example:** `ProcessAll([]int{1, 2, 3, 4}, 2, double)` → `[2 4 6 8]`, with at most two calls of `double` in progress at once.
""" + LOGIN,
    starter='package main\n\n// ProcessAll runs f on every job using a fixed number of worker goroutines.\nfunc ProcessAll(jobs []int, workers int, f func(int) int) []int {\n\t// your code\n\treturn nil\n}\n',
    solution='package main\n\nimport "sync"\n\n// ProcessAll runs f on every job using a fixed number of worker goroutines.\nfunc ProcessAll(jobs []int, workers int, f func(int) int) []int {\n\tout := make([]int, len(jobs))\n\tindexes := make(chan int)\n\n\tvar wg sync.WaitGroup\n\tfor w := 0; w < workers; w++ {\n\t\twg.Add(1)\n\t\tgo func() {\n\t\t\tdefer wg.Done()\n\t\t\tfor i := range indexes { // ends when indexes is closed\n\t\t\t\tout[i] = f(jobs[i])\n\t\t\t}\n\t\t}()\n\t}\n\n\tfor i := range jobs {\n\t\tindexes <- i\n\t}\n\tclose(indexes)\n\twg.Wait()\n\treturn out\n}\n',
    wrong_solutions=[
        'package main\n\nimport "sync"\n\nfunc ProcessAll(jobs []int, workers int, f func(int) int) []int {\n\tout := make([]int, len(jobs))\n\tvar wg sync.WaitGroup\n\tfor i := range jobs {\n\t\twg.Add(1)\n\t\tgo func(i int) {\n\t\t\tdefer wg.Done()\n\t\t\tout[i] = f(jobs[i])\n\t\t}(i)\n\t}\n\twg.Wait()\n\treturn out\n}\n',
        'package main\n\nfunc ProcessAll(jobs []int, workers int, f func(int) int) []int {\n\tout := make([]int, len(jobs))\n\tfor i := range jobs {\n\t\tout[i] = f(jobs[i])\n\t}\n\treturn out\n}\n',
    ],
    harness=harness([
        "return within(func() any { return ProcessAll([]int{1, 2, 3, 4}, 2, func(n int) int { return n * 2 }) }), []int{2, 4, 6, 8}",
        "return within(func() any { return len(ProcessAll(nil, 3, func(n int) int { return n })) }), 0",
        "return within(func() any { return ProcessAll([]int{5}, 4, func(n int) int { return n + 1 }) }), []int{6}",
        "return within(func() any { var m meter; out := ProcessAll([]int{1, 2, 3, 4, 5, 6, 7, 8, 9}, 3, m.slow); return fmt.Sprint(out, m.peak() <= 3) }), \"[10 20 30 40 50 60 70 80 90] true\"",
        "return within(func() any { var m meter; ProcessAll(make([]int, 12), 3, m.slow); return m.peak() >= 2 }), true",
        "return within(func() any { var m meter; ProcessAll(make([]int, 6), 1, m.slow); return m.peak() }), 1",
        "return within(func() any { var m meter; ProcessAll(make([]int, 2), 8, m.slow); return m.peak() <= 2 }), true",
        "return within(func() any { var m meter; ProcessAll(make([]int, 40), 4, m.slow); return m.calls.Load() }), 40",
        "return within(func() any { var m meter; start := time.Now(); ProcessAll(make([]int, 20), 10, m.slow); return time.Since(start) < 200*time.Millisecond }), true",
    ], imports=["sync/atomic", "time"], pre=WITHIN + '''
// meter records how many calls of slow run at the same time.
type meter struct {
	cur, max, calls atomic.Int64
}

func (m *meter) slow(n int) int {
	c := m.cur.Add(1)
	for {
		old := m.max.Load()
		if c <= old || m.max.CompareAndSwap(old, c) {
			break
		}
	}
	m.calls.Add(1)
	time.Sleep(15 * time.Millisecond)
	m.cur.Add(-1)
	return n * 10
}

func (m *meter) peak() int64 { return m.max.Load() }'''),
    guide=G(
        "[select and concurrency patterns](#/lesson/go/go-select-patterns) (worker pool, fan-out), [WaitGroup, Mutex, Once, atomics and errgroup](#/lesson/go/go-sync-primitives).",
        "The number of goroutines that receive from the jobs channel is the concurrency limit. Send **indexes** through the channel so each worker knows where to store its result.",
        ["Start `workers` goroutines, each doing `for i := range indexes { out[i] = f(jobs[i]) }`.", "The producer sends every index and then **closes** the channel so the workers' loops end.", "Wait for the workers with a WaitGroup before returning `out`."],
        "One goroutine per job is simple and breaks the limit: 10,000 jobs would start 10,000 simultaneous calls. A plain loop respects the limit and uses no concurrency at all.",
        "**Dry run:** 4 jobs, 2 workers. Index 0 goes to one worker, index 1 to the other. Index 2 is sent only when a worker is free again (the unbuffered send blocks until then). At most two calls of `f` ever overlap. After `close`, both workers leave their loops and `wg.Wait()` returns.\n\n"
        "```go\nout := make([]int, len(jobs))\nindexes := make(chan int)\nvar wg sync.WaitGroup\nfor w := 0; w < workers; w++ {\n\twg.Add(1)\n\tgo func() {\n\t\tdefer wg.Done()\n\t\tfor i := range indexes {\n\t\t\tout[i] = f(jobs[i])\n\t\t}\n\t}()\n}\nfor i := range jobs {\n\tindexes <- i\n}\nclose(indexes)\nwg.Wait()\nreturn out\n```",
        "Wall-clock time about `len(jobs) / workers` call durations; O(n) space.",
        "Forgetting `close(indexes)`: the workers wait for ever and `wg.Wait()` deadlocks. Collecting results from a channel in completion order. Starting a goroutine per job. Closing the channel from a worker.",
    ),
),
# ------------------------------------------------------------------ pipeline
dict(
    id="go-real-pipeline", title="A three-stage channel pipeline", difficulty="Medium", pattern="Go concurrency", kind="go", cases=8,
    description=r"""
Write three functions that form a pipeline:

```go
func Generate(nums ...int) <-chan int      // sends each number, then closes the channel
func Square(in <-chan int) <-chan int      // sends n*n for every n received, then closes
func Collect(in <-chan int) []int          // receives until the channel is closed
```

`Generate` and `Square` each start one goroutine and return their output channel immediately.
Every stage must **close** its output when it is finished, otherwise the next stage waits for ever.

**Example:** `Collect(Square(Generate(1, 2, 3)))` → `[1 4 9]`
""" + LOGIN,
    starter='package main\n\n// Generate sends nums on a channel and closes it.\nfunc Generate(nums ...int) <-chan int {\n\tout := make(chan int)\n\t// your code\n\treturn out\n}\n\n// Square sends the square of every value received from in.\nfunc Square(in <-chan int) <-chan int {\n\tout := make(chan int)\n\t// your code\n\treturn out\n}\n\n// Collect gathers every value from in into a slice.\nfunc Collect(in <-chan int) []int {\n\t// your code\n\treturn nil\n}\n',
    solution='package main\n\n// Generate sends nums on a channel and closes it.\nfunc Generate(nums ...int) <-chan int {\n\tout := make(chan int)\n\tgo func() {\n\t\tdefer close(out)\n\t\tfor _, n := range nums {\n\t\t\tout <- n\n\t\t}\n\t}()\n\treturn out\n}\n\n// Square sends the square of every value received from in.\nfunc Square(in <-chan int) <-chan int {\n\tout := make(chan int)\n\tgo func() {\n\t\tdefer close(out)\n\t\tfor n := range in {\n\t\t\tout <- n * n\n\t\t}\n\t}()\n\treturn out\n}\n\n// Collect gathers every value from in into a slice.\nfunc Collect(in <-chan int) []int {\n\tout := []int{}\n\tfor n := range in {\n\t\tout = append(out, n)\n\t}\n\treturn out\n}\n',
    wrong_solutions=[
        'package main\n\nfunc Generate(nums ...int) <-chan int {\n\tout := make(chan int)\n\tgo func() {\n\t\tfor _, n := range nums {\n\t\t\tout <- n\n\t\t}\n\t}()\n\treturn out\n}\n\nfunc Square(in <-chan int) <-chan int {\n\tout := make(chan int)\n\tgo func() {\n\t\tdefer close(out)\n\t\tfor n := range in {\n\t\t\tout <- n * n\n\t\t}\n\t}()\n\treturn out\n}\n\nfunc Collect(in <-chan int) []int {\n\tout := []int{}\n\tfor n := range in {\n\t\tout = append(out, n)\n\t}\n\treturn out\n}\n',
        'package main\n\nfunc Generate(nums ...int) <-chan int {\n\tout := make(chan int)\n\tgo func() {\n\t\tdefer close(out)\n\t\tfor _, n := range nums {\n\t\t\tout <- n\n\t\t}\n\t}()\n\treturn out\n}\n\nfunc Square(in <-chan int) <-chan int {\n\tout := make(chan int)\n\tgo func() {\n\t\tdefer close(out)\n\t\tfor n := range in {\n\t\t\tout <- n + n\n\t\t}\n\t}()\n\treturn out\n}\n\nfunc Collect(in <-chan int) []int {\n\tout := []int{}\n\tfor n := range in {\n\t\tout = append(out, n)\n\t}\n\treturn out\n}\n',
    ],
    harness=harness([
        "return within(func() any { return Collect(Square(Generate(1, 2, 3))) }), []int{1, 4, 9}",
        "return within(func() any { return Collect(Generate(5, 6, 7)) }), []int{5, 6, 7}",
        "return within(func() any { return len(Collect(Generate())) }), 0",
        "return within(func() any { return len(Collect(Square(Generate()))) }), 0",
        "return within(func() any { return Collect(Square(Square(Generate(2, 3)))) }), []int{16, 81}",
        "return within(func() any { ch := Generate(9); <-ch; _, open := <-ch; return open }), false",
        "return within(func() any { ch := Square(Generate(-4)); v := <-ch; _, open := <-ch; return fmt.Sprint(v, open) }), \"16 false\"",
        "return within(func() any { nums := make([]int, 500); for i := range nums { nums[i] = i }; out := Collect(Square(Generate(nums...))); return fmt.Sprint(len(out), out[499]) }), \"500 249001\"",
    ], imports=["time"], pre=WITHIN),
    guide=G(
        "[select and concurrency patterns](#/lesson/go/go-select-patterns): the pipeline pattern; closing and `range` from [Goroutines and channels](#/lesson/go/go-goroutines-channels).",
        "Every stage has the same shape: make an output channel, start a goroutine that writes to it and closes it when done, return the channel at once. Closing travels down the line and ends each `range` loop in turn.",
        ["Inside the goroutine, `defer close(out)` as the first statement.", "`Square` ranges over `in`; that loop ends when the previous stage closes its channel.", "`Collect` is a plain `for n := range in` with `append`; it needs no goroutine."],
        "Doing all the work in one loop over a slice is simpler for this toy task. The pipeline form pays off when stages are slow, independent or infinite.",
        "**Dry run:** `Generate(1,2,3)` sends 1 → `Square` receives 1, sends 1 → `Collect` appends 1; and so on. After 3, `Generate` closes; `Square`'s loop ends and it closes; `Collect`'s loop ends and it returns `[1 4 9]`.\n\n"
        "```go\nfunc Square(in <-chan int) <-chan int {\n\tout := make(chan int)\n\tgo func() {\n\t\tdefer close(out)\n\t\tfor n := range in {\n\t\t\tout <- n * n\n\t\t}\n\t}()\n\treturn out\n}\n```",
        "O(n) values pass through each stage; with unbuffered channels at most one value is in flight per stage.",
        "A missing `close` makes the downstream `range` block for ever (the tests report a timeout). Sending in the calling goroutine before returning the channel deadlocks, since nobody is receiving yet. Closing the *input* channel from a receiver.",
    ),
),
# ------------------------------------------------------------------ merge / fan-in
dict(
    id="go-real-merge", title="Fan-in: merge channels into one", difficulty="Hard", pattern="Go concurrency", kind="go", cases=8,
    description=r"""
Write `func Merge(chans ...<-chan int) <-chan int`.

The returned channel must deliver **every value** received from **every** input channel (in any order), and it
must be **closed** once all input channels have been closed and drained. With no input channels, the returned
channel is closed straight away.

Because several goroutines send to the same output channel, none of them may close it alone: wait for all of
them with a `sync.WaitGroup`, then close once.
""" + LOGIN,
    starter='package main\n\n// Merge forwards the values of all input channels to one output channel.\nfunc Merge(chans ...<-chan int) <-chan int {\n\tout := make(chan int)\n\t// your code\n\treturn out\n}\n',
    solution='package main\n\nimport "sync"\n\n// Merge forwards the values of all input channels to one output channel.\nfunc Merge(chans ...<-chan int) <-chan int {\n\tout := make(chan int)\n\tvar wg sync.WaitGroup\n\tfor _, ch := range chans {\n\t\twg.Add(1)\n\t\tgo func(ch <-chan int) {\n\t\t\tdefer wg.Done()\n\t\t\tfor v := range ch {\n\t\t\t\tout <- v\n\t\t\t}\n\t\t}(ch)\n\t}\n\tgo func() {\n\t\twg.Wait()\n\t\tclose(out)\n\t}()\n\treturn out\n}\n',
    wrong_solutions=[
        'package main\n\nfunc Merge(chans ...<-chan int) <-chan int {\n\tout := make(chan int)\n\tgo func() {\n\t\tdefer close(out)\n\t\tif len(chans) == 0 {\n\t\t\treturn\n\t\t}\n\t\tfor v := range chans[0] {\n\t\t\tout <- v\n\t\t}\n\t}()\n\treturn out\n}\n',
        'package main\n\nfunc Merge(chans ...<-chan int) <-chan int {\n\tout := make(chan int)\n\tfor _, ch := range chans {\n\t\tgo func(ch <-chan int) {\n\t\t\tfor v := range ch {\n\t\t\t\tout <- v\n\t\t\t}\n\t\t}(ch)\n\t}\n\treturn out\n}\n',
    ],
    harness=harness([
        "return within(func() any { return drain(Merge(src(1, 2), src(3))) }), []int{1, 2, 3}",
        "return within(func() any { return len(drain(Merge())) }), 0",
        "return within(func() any { return drain(Merge(src(5, 4, 3))) }), []int{3, 4, 5}",
        "return within(func() any { return drain(Merge(src(), src(7), src())) }), []int{7}",
        "return within(func() any { return drain(Merge(src(1, 1), src(1), src(2, 1))) }), []int{1, 1, 1, 1, 2}",
        "return within(func() any { var ins []<-chan int; for i := 0; i < 20; i++ { ins = append(ins, src(i, i+100)) }; return len(drain(Merge(ins...))) }), 40",
        "return within(func() any { out := Merge(src(9)); <-out; _, open := <-out; return open }), false",
        "return within(func() any { slow := make(chan int); go func() { time.Sleep(30 * time.Millisecond); slow <- 8; close(slow) }(); return drain(Merge(src(1, 2, 3), slow)) }), []int{1, 2, 3, 8}",
    ], imports=["sort", "time"], pre=WITHIN + '''
// src returns a channel that delivers vals and is then closed.
func src(vals ...int) <-chan int {
	ch := make(chan int)
	go func() {
		defer close(ch)
		for _, v := range vals {
			ch <- v
		}
	}()
	return ch
}

// drain reads a channel until it is closed and returns the values sorted.
func drain(ch <-chan int) []int {
	out := []int{}
	for v := range ch {
		out = append(out, v)
	}
	sort.Ints(out)
	return out
}'''),
    guide=G(
        "[select and concurrency patterns](#/lesson/go/go-select-patterns): fan-in and the closer goroutine.",
        "One forwarding goroutine per input copies values to the shared output. A separate goroutine waits for all forwarders and closes the output exactly once.",
        ["For each input: `wg.Add(1)`, then a goroutine that ranges over that input and sends to `out`.", "Pass the channel to the goroutine as an argument.", "`go func() { wg.Wait(); close(out) }()`; do not call `wg.Wait()` in `Merge` itself, or it would block before returning the channel."],
        "Reading the inputs one after another delivers everything only if earlier inputs finish; a slow or endless first channel starves the rest.",
        "**Dry run:** `Merge(src(1,2), src(3))` → two forwarders. They send 1, 2 and 3 in some interleaving. When both inputs are closed both forwarders call `Done`; the closer's `Wait` returns and it closes `out`; the consumer's `range` ends.\n\n"
        "```go\nout := make(chan int)\nvar wg sync.WaitGroup\nfor _, ch := range chans {\n\twg.Add(1)\n\tgo func(ch <-chan int) {\n\t\tdefer wg.Done()\n\t\tfor v := range ch {\n\t\t\tout <- v\n\t\t}\n\t}(ch)\n}\ngo func() {\n\twg.Wait()\n\tclose(out)\n}()\nreturn out\n```",
        "O(total values); one goroutine per input plus one closer.",
        "Never closing the output (consumers block: the tests report a timeout). Closing from each forwarder (panic: close of closed channel, or send on closed channel). Waiting inside `Merge` before returning (deadlock: nobody is receiving yet).",
    ),
),
# ------------------------------------------------------------------ context wait
dict(
    id="go-real-context-wait", title="Wait, unless the context says stop", difficulty="Medium", pattern="Go context", kind="go", cases=8,
    description=r"""
Write `func WaitOrCancel(ctx context.Context, d time.Duration) error`.

It waits for the duration `d` and then returns `nil`. If `ctx` is cancelled or its deadline passes **before**
`d` has elapsed, it returns **immediately** with `ctx.Err()` (that is, `context.Canceled` or
`context.DeadlineExceeded`).

This is the shape of every well-behaved blocking operation in Go: a `select` between the work and `ctx.Done()`.
""" + LOGIN,
    starter='package main\n\nimport (\n\t"context"\n\t"time"\n)\n\n// WaitOrCancel waits for d, or returns early with ctx.Err() if ctx ends first.\nfunc WaitOrCancel(ctx context.Context, d time.Duration) error {\n\t// your code\n\ttime.Sleep(d)\n\treturn nil\n}\n',
    solution='package main\n\nimport (\n\t"context"\n\t"time"\n)\n\n// WaitOrCancel waits for d, or returns early with ctx.Err() if ctx ends first.\nfunc WaitOrCancel(ctx context.Context, d time.Duration) error {\n\ttimer := time.NewTimer(d)\n\tdefer timer.Stop()\n\tselect {\n\tcase <-timer.C:\n\t\treturn nil\n\tcase <-ctx.Done():\n\t\treturn ctx.Err()\n\t}\n}\n',
    wrong_solutions=[
        'package main\n\nimport (\n\t"context"\n\t"time"\n)\n\nfunc WaitOrCancel(ctx context.Context, d time.Duration) error {\n\ttime.Sleep(d)\n\treturn ctx.Err()\n}\n',
        'package main\n\nimport (\n\t"context"\n\t"time"\n)\n\nfunc WaitOrCancel(ctx context.Context, d time.Duration) error {\n\tselect {\n\tcase <-time.After(d):\n\t\treturn nil\n\tcase <-ctx.Done():\n\t\treturn context.Canceled\n\t}\n}\n',
    ],
    harness=harness([
        "return within(func() any { return WaitOrCancel(context.Background(), 10*time.Millisecond) == nil }), true",
        "return within(func() any { start := time.Now(); WaitOrCancel(context.Background(), 40*time.Millisecond); return time.Since(start) >= 35*time.Millisecond }), true",
        "return within(func() any { ctx, cancel := context.WithCancel(context.Background()); cancel(); return errors.Is(WaitOrCancel(ctx, time.Second), context.Canceled) }), true",
        "return within(func() any { ctx, cancel := context.WithCancel(context.Background()); cancel(); start := time.Now(); WaitOrCancel(ctx, time.Second); return time.Since(start) < 300*time.Millisecond }), true",
        "return within(func() any { ctx, cancel := context.WithTimeout(context.Background(), 20*time.Millisecond); defer cancel(); return errors.Is(WaitOrCancel(ctx, time.Second), context.DeadlineExceeded) }), true",
        "return within(func() any { ctx, cancel := context.WithTimeout(context.Background(), time.Second); defer cancel(); return WaitOrCancel(ctx, 10*time.Millisecond) == nil }), true",
        "return within(func() any { ctx, cancel := context.WithCancel(context.Background()); time.AfterFunc(30*time.Millisecond, cancel); start := time.Now(); err := WaitOrCancel(ctx, time.Second); return fmt.Sprint(errors.Is(err, context.Canceled), time.Since(start) < 400*time.Millisecond) }), \"true true\"",
        "return within(func() any { parent, cancel := context.WithCancel(context.Background()); child, cancelChild := context.WithTimeout(parent, time.Second); defer cancelChild(); cancel(); return errors.Is(WaitOrCancel(child, time.Second), context.Canceled) }), true",
    ], imports=["context", "errors", "time"], pre=WITHIN),
    guide=G(
        "[Context: cancellation and its tree](#/lesson/go/go-context-cancel), [Deadlines, timeouts and context values](#/lesson/go/go-context-deadlines-values), `select` from [select and concurrency patterns](#/lesson/go/go-select-patterns).",
        "Two things can happen first: the time is up, or the context is done. `select` waits for whichever comes first.",
        ["`time.After(d)` or a `time.Timer` gives a channel that fires after `d`.", "`ctx.Done()` is a channel that is closed on cancellation or deadline.", "Return `ctx.Err()`, which already says which of the two reasons applied."],
        "`time.Sleep(d)` followed by `return ctx.Err()` returns the right error far too late: the caller asked to stop and waited the full duration anyway.",
        "**Dry run:** the context is cancelled after 30 ms and `d` is one second. The `select` is blocked on both channels; at 30 ms `ctx.Done()` becomes ready; the function returns `context.Canceled` at once.\n\n"
        "```go\nfunc WaitOrCancel(ctx context.Context, d time.Duration) error {\n\ttimer := time.NewTimer(d)\n\tdefer timer.Stop()\n\tselect {\n\tcase <-timer.C:\n\t\treturn nil\n\tcase <-ctx.Done():\n\t\treturn ctx.Err()\n\t}\n}\n```\n\n"
        "The explicit timer with `Stop` releases the timer as soon as the function returns early.",
        "O(1); it blocks for at most `d`.",
        "Sleeping instead of selecting. Returning a hard-coded `context.Canceled` when the cause was a deadline. Checking `ctx.Err()` only once at the start.",
    ),
),
# ------------------------------------------------------------------ valid parentheses
dict(
    id="go-real-valid-parens", title="Valid brackets (interview classic)", difficulty="Easy", pattern="Go interview", kind="go", cases=10,
    description=r"""
Write `func IsValid(s string) bool`. The string contains only the characters `( ) [ ] { }`.

It is valid when every opening bracket is closed by the same kind of bracket and in the correct order.
The empty string is valid.

**Examples:** `"()[]{}"` → `true`, `"([{}])"` → `true`, `"(]"` → `false`, `"(("` → `false`.
""" + LOGIN,
    starter="package main\n\n// IsValid reports whether the brackets in s are balanced.\nfunc IsValid(s string) bool {\n\t// your code\n\treturn false\n}\n",
    solution="package main\n\n// IsValid reports whether the brackets in s are balanced.\nfunc IsValid(s string) bool {\n\tpairs := map[rune]rune{')': '(', ']': '[', '}': '{'}\n\tvar stack []rune\n\tfor _, r := range s {\n\t\topen, isClosing := pairs[r]\n\t\tif !isClosing {\n\t\t\tstack = append(stack, r)\n\t\t\tcontinue\n\t\t}\n\t\tif len(stack) == 0 || stack[len(stack)-1] != open {\n\t\t\treturn false\n\t\t}\n\t\tstack = stack[:len(stack)-1]\n\t}\n\treturn len(stack) == 0\n}\n",
    wrong_solutions=[
        "package main\n\nimport \"strings\"\n\nfunc IsValid(s string) bool {\n\treturn strings.Count(s, \"(\") == strings.Count(s, \")\") &&\n\t\tstrings.Count(s, \"[\") == strings.Count(s, \"]\") &&\n\t\tstrings.Count(s, \"{\") == strings.Count(s, \"}\")\n}\n",
        "package main\n\nfunc IsValid(s string) bool {\n\tpairs := map[rune]rune{')': '(', ']': '[', '}': '{'}\n\tvar stack []rune\n\tfor _, r := range s {\n\t\topen, isClosing := pairs[r]\n\t\tif !isClosing {\n\t\t\tstack = append(stack, r)\n\t\t\tcontinue\n\t\t}\n\t\tif len(stack) == 0 || stack[len(stack)-1] != open {\n\t\t\treturn false\n\t\t}\n\t\tstack = stack[:len(stack)-1]\n\t}\n\treturn true\n}\n",
    ],
    harness=harness([
        ('IsValid("()")', "true"), ('IsValid("()[]{}")', "true"), ('IsValid("([{}])")', "true"), ('IsValid("")', "true"),
        ('IsValid("(]")', "false"), ('IsValid("([)]")', "false"), ('IsValid("((")', "false"), ('IsValid(")")', "false"),
        ('IsValid("{[]}()")', "true"), ('IsValid(strings.Repeat("(", 5000) + strings.Repeat(")", 5000))', "true"),
    ], imports=["strings"]),
    guide=G(
        "Slices used as a stack ([Arrays and slices](#/lesson/go/go-arrays-slices)), maps, `range` over a string.",
        "The most recently opened bracket must be the first one closed: last in, first out. That is a stack.",
        ["Push opening brackets with `append`.", "For a closing bracket, the top of the stack must be its partner; otherwise return false.", "At the end the stack must be empty."],
        "Counting each kind of bracket accepts `([)]` and `)(`: counts ignore order.",
        "**Dry run:** `([)]` → push `(`, push `[`; `)` expects `(` but the top is `[` → false.\n\n"
        "```go\npairs := map[rune]rune{')': '(', ']': '[', '}': '{'}\nvar stack []rune\nfor _, r := range s {\n\topen, isClosing := pairs[r]\n\tif !isClosing {\n\t\tstack = append(stack, r)\n\t\tcontinue\n\t}\n\tif len(stack) == 0 || stack[len(stack)-1] != open {\n\t\treturn false\n\t}\n\tstack = stack[:len(stack)-1]\n}\nreturn len(stack) == 0\n```",
        "O(n) time, O(n) space.",
        "Popping from an empty stack (index out of range). Forgetting the final emptiness check, which accepts `((`.",
    ),
),
# ------------------------------------------------------------------ reverse linked list
dict(
    id="go-real-reverse-list", title="Reverse a linked list with pointers", difficulty="Medium", pattern="Go interview", kind="go", cases=8,
    description=r"""
A singly linked list is made of nodes, each pointing to the next; the last node's `Next` is `nil`:

```go
type Node struct {
    Val  int
    Next *Node
}
```

Keep that type in your file and write `func Reverse(head *Node) *Node`, which reverses the list **in place**
(re-pointing the existing nodes, not creating new ones) and returns the new head. An empty list (`nil`) stays `nil`.

**Example:** `1 → 2 → 3` becomes `3 → 2 → 1`.
""" + LOGIN,
    starter="package main\n\n// Node is an element of a singly linked list.\ntype Node struct {\n\tVal  int\n\tNext *Node\n}\n\n// Reverse reverses the list and returns its new head.\nfunc Reverse(head *Node) *Node {\n\t// your code\n\treturn head\n}\n",
    solution="package main\n\n// Node is an element of a singly linked list.\ntype Node struct {\n\tVal  int\n\tNext *Node\n}\n\n// Reverse reverses the list and returns its new head.\nfunc Reverse(head *Node) *Node {\n\tvar prev *Node\n\tfor cur := head; cur != nil; {\n\t\tnext := cur.Next\n\t\tcur.Next = prev\n\t\tprev, cur = cur, next\n\t}\n\treturn prev\n}\n",
    wrong_solutions=[
        "package main\n\ntype Node struct {\n\tVal  int\n\tNext *Node\n}\n\nfunc Reverse(head *Node) *Node {\n\tvar prev *Node\n\tfor cur := head; cur != nil; cur = cur.Next {\n\t\tcur.Next = prev\n\t\tprev = cur\n\t}\n\treturn prev\n}\n",
        "package main\n\ntype Node struct {\n\tVal  int\n\tNext *Node\n}\n\nfunc Reverse(head *Node) *Node {\n\tvar out *Node\n\tfor cur := head; cur != nil; cur = cur.Next {\n\t\tout = &Node{Val: cur.Val, Next: out}\n\t}\n\treturn out\n}\n",
    ],
    harness=harness([
        ("values(Reverse(build(1, 2, 3)))", "[]int{3, 2, 1}"), ("Reverse(nil) == nil", "true"), ("values(Reverse(build(7)))", "[]int{7}"),
        ("values(Reverse(build(1, 2)))", "[]int{2, 1}"), ("values(Reverse(Reverse(build(4, 5, 6, 7))))", "[]int{4, 5, 6, 7}"),
        "head := build(1, 2, 3); first := head; r := Reverse(head); return fmt.Sprint(first.Next == nil, r.Val), \"true 3\"",
        "head := build(1, 2, 3); last := head.Next.Next; return Reverse(head) == last, true",
        "vals := make([]int, 1000); for i := range vals { vals[i] = i }; return values(Reverse(build(vals...)))[0], 999",
    ], pre='''func build(vals ...int) *Node {
	var head, tail *Node
	for _, v := range vals {
		n := &Node{Val: v}
		if head == nil {
			head, tail = n, n
		} else {
			tail.Next = n
			tail = n
		}
	}
	return head
}

func values(head *Node) []int {
	out := []int{}
	for n, steps := head, 0; n != nil && steps < 100000; n, steps = n.Next, steps+1 {
		out = append(out, n.Val)
	}
	return out
}'''),
    guide=G(
        "[Pointers, nil and mutability](#/lesson/go/go-pointers-basics).",
        "Walk the list once and turn every arrow around. Before you overwrite a node's `Next`, save where it pointed, or the rest of the list is lost.",
        ["Keep three pointers: `prev` (starts nil), `cur` and `next`.", "In each step: `next = cur.Next`, `cur.Next = prev`, then move `prev` and `cur` forward.", "When `cur` is nil, `prev` is the new head."],
        "Copying the values into a slice, reversing it and writing them back needs O(n) extra memory and does not practise pointer manipulation.",
        "**Dry run** for `1 → 2 → 3`: prev=nil, cur=1. Step 1: next=2, `1.Next=nil`, prev=1, cur=2. Step 2: next=3, `2.Next=1`, prev=2, cur=3. Step 3: next=nil, `3.Next=2`, prev=3, cur=nil. Return 3: `3 → 2 → 1`.\n\n"
        "```go\nvar prev *Node\nfor cur := head; cur != nil; {\n\tnext := cur.Next\n\tcur.Next = prev\n\tprev, cur = cur, next\n}\nreturn prev\n```",
        "O(n) time, O(1) extra space.",
        "Advancing with `cur = cur.Next` after overwriting `cur.Next`: the walk goes backwards and stops after one node. Building new nodes instead of re-linking. Returning `head`, which is now the tail.",
    ),
),
# ------------------------------------------------------------------ group anagrams
dict(
    id="go-real-group-anagrams", title="Group anagrams (maps and sorting)", difficulty="Medium", pattern="Go interview", kind="go", cases=8,
    description=r"""
Two words are anagrams when one can be formed by rearranging the letters of the other (`"listen"` and `"silent"`).

Write `func GroupAnagrams(words []string) [][]string` that puts anagrams into the same group. To make the output
deterministic:

- inside each group, sort the words alphabetically;
- sort the groups by their first word.

Words contain lower-case letters `a`–`z` only. The input must not be modified. No words gives an empty result.

**Example:** `["eat", "tea", "tan", "ate", "nat", "bat"]` → `[[ate eat tea] [bat] [nat tan]]`
""" + LOGIN,
    starter="package main\n\n// GroupAnagrams groups words that are anagrams of each other.\nfunc GroupAnagrams(words []string) [][]string {\n\t// your code\n\treturn nil\n}\n",
    solution='package main\n\nimport "sort"\n\n// GroupAnagrams groups words that are anagrams of each other.\nfunc GroupAnagrams(words []string) [][]string {\n\tgroups := make(map[[26]int][]string)\n\tfor _, w := range words {\n\t\tvar key [26]int // letter counts: an array is comparable, so it can be a map key\n\t\tfor i := 0; i < len(w); i++ {\n\t\t\tkey[w[i]-\'a\']++\n\t\t}\n\t\tgroups[key] = append(groups[key], w)\n\t}\n\tout := make([][]string, 0, len(groups))\n\tfor _, g := range groups {\n\t\tsort.Strings(g)\n\t\tout = append(out, g)\n\t}\n\tsort.Slice(out, func(i, j int) bool { return out[i][0] < out[j][0] })\n\treturn out\n}\n',
    wrong_solutions=[
        'package main\n\nimport "sort"\n\nfunc GroupAnagrams(words []string) [][]string {\n\tgroups := make(map[int][]string)\n\tfor _, w := range words {\n\t\tsum := 0\n\t\tfor i := 0; i < len(w); i++ {\n\t\t\tsum += int(w[i])\n\t\t}\n\t\tgroups[sum] = append(groups[sum], w)\n\t}\n\tout := make([][]string, 0, len(groups))\n\tfor _, g := range groups {\n\t\tsort.Strings(g)\n\t\tout = append(out, g)\n\t}\n\tsort.Slice(out, func(i, j int) bool { return out[i][0] < out[j][0] })\n\treturn out\n}\n',
        'package main\n\nfunc GroupAnagrams(words []string) [][]string {\n\tgroups := make(map[[26]int][]string)\n\tvar order [][26]int\n\tfor _, w := range words {\n\t\tvar key [26]int\n\t\tfor i := 0; i < len(w); i++ {\n\t\t\tkey[w[i]-\'a\']++\n\t\t}\n\t\tif _, ok := groups[key]; !ok {\n\t\t\torder = append(order, key)\n\t\t}\n\t\tgroups[key] = append(groups[key], w)\n\t}\n\tout := [][]string{}\n\tfor _, k := range order {\n\t\tout = append(out, groups[k])\n\t}\n\treturn out\n}\n',
    ],
    harness=harness([
        ('GroupAnagrams([]string{"eat", "tea", "tan", "ate", "nat", "bat"})', '[][]string{{"ate", "eat", "tea"}, {"bat"}, {"nat", "tan"}}'),
        ("len(GroupAnagrams(nil))", "0"), ('GroupAnagrams([]string{"a"})', '[][]string{{"a"}}'),
        ('GroupAnagrams([]string{"ab", "ba", "ab"})', '[][]string{{"ab", "ab", "ba"}}'),
        ('GroupAnagrams([]string{"ad", "bc"})', '[][]string{{"ad"}, {"bc"}}'),
        ('GroupAnagrams([]string{"", "b", ""})', '[][]string{{"", ""}, {"b"}}'),
        ('GroupAnagrams([]string{"listen", "silent", "enlist", "google", "gogole", "cat"})', '[][]string{{"cat"}, {"enlist", "listen", "silent"}, {"gogole", "google"}}'),
        'in := []string{"tea", "eat"}; _ = GroupAnagrams(in); return in, []string{"tea", "eat"}',
    ]),
    guide=G(
        "[Maps and structs](#/lesson/go/go-maps-structs) (arrays as map keys), sorting with `sort` or `slices`.",
        "Anagrams have the same letters with the same counts. Compute a 'signature' that is identical for all anagrams and use it as a map key.",
        ["A `[26]int` of letter counts is a signature, and arrays are comparable, so it can be a map key directly.", "`groups[key] = append(groups[key], w)` works even for the first word, because a missing key yields a nil slice.", "Sort each group, then sort the groups by first word; map iteration order is random."],
        "Comparing every word with every other by sorting both: O(n² · k log k).",
        "**Dry run:** `eat`, `tea`, `ate` all give counts a=1, e=1, t=1 → same key → one group, sorted `[ate eat tea]`. `ad` and `bc` have the same character sum (197) but different counts, so they are different groups.\n\n"
        "```go\ngroups := make(map[[26]int][]string)\nfor _, w := range words {\n\tvar key [26]int\n\tfor i := 0; i < len(w); i++ {\n\t\tkey[w[i]-'a']++\n\t}\n\tgroups[key] = append(groups[key], w)\n}\n```\n\n"
        "An alternative key is the word with its letters sorted, as a string.",
        "O(n · k) to build the groups for n words of length k, plus sorting the output.",
        "A signature that collides, such as the sum of character codes. Returning groups in map order (changes from run to run). Sorting the caller's slice.",
    ),
),
# ------------------------------------------------------------------ binary search
dict(
    id="go-real-binary-search", title="Binary search", difficulty="Easy", pattern="Go interview", kind="go", cases=10,
    description=r"""
Write `func Search(xs []int, target int) int`.

`xs` is sorted in increasing order with no duplicates. Return the index of `target`, or `-1` if it is not present.
Use binary search: repeatedly halve the range that could contain the target.

**Examples:** `Search([]int{1, 3, 5, 7, 9}, 7)` → `3`; `Search([]int{1, 3, 5, 7, 9}, 4)` → `-1`.
""" + LOGIN,
    starter="package main\n\n// Search returns the index of target in the sorted slice xs, or -1.\nfunc Search(xs []int, target int) int {\n\t// your code\n\treturn -1\n}\n",
    solution="package main\n\n// Search returns the index of target in the sorted slice xs, or -1.\nfunc Search(xs []int, target int) int {\n\tlo, hi := 0, len(xs)-1\n\tfor lo <= hi {\n\t\tmid := lo + (hi-lo)/2\n\t\tswitch {\n\t\tcase xs[mid] == target:\n\t\t\treturn mid\n\t\tcase xs[mid] < target:\n\t\t\tlo = mid + 1\n\t\tdefault:\n\t\t\thi = mid - 1\n\t\t}\n\t}\n\treturn -1\n}\n",
    wrong_solutions=[
        "package main\n\nfunc Search(xs []int, target int) int {\n\tlo, hi := 0, len(xs)-1\n\tfor lo < hi {\n\t\tmid := lo + (hi-lo)/2\n\t\tswitch {\n\t\tcase xs[mid] == target:\n\t\t\treturn mid\n\t\tcase xs[mid] < target:\n\t\t\tlo = mid + 1\n\t\tdefault:\n\t\t\thi = mid - 1\n\t\t}\n\t}\n\treturn -1\n}\n",
        "package main\n\nfunc Search(xs []int, target int) int {\n\tfor i, x := range xs {\n\t\tif x >= target {\n\t\t\treturn i\n\t\t}\n\t}\n\treturn -1\n}\n",
    ],
    harness=harness([
        ("Search([]int{1, 3, 5, 7, 9}, 7)", "3"), ("Search([]int{1, 3, 5, 7, 9}, 4)", "-1"), ("Search(nil, 1)", "-1"),
        ("Search([]int{5}, 5)", "0"), ("Search([]int{5}, 6)", "-1"), ("Search([]int{1, 3, 5, 7, 9}, 1)", "0"),
        ("Search([]int{1, 3, 5, 7, 9}, 9)", "4"), ("Search([]int{2, 4}, 4)", "1"), ("Search([]int{-9, -3, 0, 8}, -10)", "-1"),
        "xs := make([]int, 100000); for i := range xs { xs[i] = i * 2 }; return fmt.Sprint(Search(xs, 199998), Search(xs, 77777)), \"99999 -1\"",
    ]),
    guide=G(
        "Loops and slices: [for, switch and goto](#/lesson/go/go-for-switch), [Arrays and slices](#/lesson/go/go-arrays-slices).",
        "Because the slice is sorted, comparing the middle element with the target tells you which half can be thrown away. Each step halves the search range.",
        ["Keep an inclusive range `[lo, hi]`, starting at `0` and `len(xs)-1`.", "Loop while `lo <= hi`; compute `mid := lo + (hi-lo)/2`.", "Move `lo` to `mid+1` or `hi` to `mid-1`; never to `mid` itself."],
        "A linear scan is O(n). For a million elements binary search needs about 20 comparisons.",
        "**Dry run:** `[1 3 5 7 9]`, target 7: lo=0, hi=4, mid=2 (5 < 7) → lo=3; mid=3 (7) → return 3. Target 4: mid=2 (5 > 4) → hi=1; mid=0 (1 < 4) → lo=1; mid=1 (3 < 4) → lo=2 > hi → -1.\n\n"
        "```go\nlo, hi := 0, len(xs)-1\nfor lo <= hi {\n\tmid := lo + (hi-lo)/2\n\tswitch {\n\tcase xs[mid] == target:\n\t\treturn mid\n\tcase xs[mid] < target:\n\t\tlo = mid + 1\n\tdefault:\n\t\thi = mid - 1\n\t}\n}\nreturn -1\n```\n\n"
        "In real code, use `slices.BinarySearch(xs, target)` from the standard library.",
        "O(log n) time, O(1) space.",
        "`lo < hi` misses the last remaining element. `mid = (lo + hi) / 2` can overflow for huge indexes in fixed-width integers. Setting `lo = mid` loops for ever.",
    ),
),
# ------------------------------------------------------------------ two sum
dict(
    id="go-real-two-sum", title="Two Sum with a map", difficulty="Easy", pattern="Go interview", kind="go", cases=9,
    description=r"""
Write `func TwoSum(nums []int, target int) []int`.

Return the indexes `[i, j]` with `i < j` of the two **different positions** whose values add up to `target`.
If several pairs exist, return the one whose second index `j` is smallest. If there is no such pair, return `nil`.

**Examples:** `TwoSum([]int{2, 7, 11, 15}, 9)` → `[0 1]`; `TwoSum([]int{3, 3}, 6)` → `[0 1]`; `TwoSum([]int{1, 2}, 7)` → `[]` (nil).
""" + LOGIN,
    starter="package main\n\n// TwoSum returns the indexes of two values that add up to target.\nfunc TwoSum(nums []int, target int) []int {\n\t// your code\n\treturn nil\n}\n",
    solution="package main\n\n// TwoSum returns the indexes of two values that add up to target.\nfunc TwoSum(nums []int, target int) []int {\n\tseen := make(map[int]int, len(nums)) // value -> index where it was first seen\n\tfor j, x := range nums {\n\t\tif i, ok := seen[target-x]; ok {\n\t\t\treturn []int{i, j}\n\t\t}\n\t\tif _, dup := seen[x]; !dup {\n\t\t\tseen[x] = j\n\t\t}\n\t}\n\treturn nil\n}\n",
    wrong_solutions=[
        "package main\n\nfunc TwoSum(nums []int, target int) []int {\n\tseen := make(map[int]int, len(nums))\n\tfor j, x := range nums {\n\t\tseen[x] = j\n\t}\n\tfor i, x := range nums {\n\t\tif j, ok := seen[target-x]; ok {\n\t\t\treturn []int{i, j}\n\t\t}\n\t}\n\treturn nil\n}\n",
        "package main\n\nfunc TwoSum(nums []int, target int) []int {\n\tseen := make(map[int]int, len(nums))\n\tfor j, x := range nums {\n\t\tif _, ok := seen[target-x]; ok {\n\t\t\treturn []int{target - x, x}\n\t\t}\n\t\tseen[x] = j\n\t}\n\treturn nil\n}\n",
    ],
    harness=harness([
        ("TwoSum([]int{2, 7, 11, 15}, 9)", "[]int{0, 1}"), ("TwoSum([]int{3, 2, 4}, 6)", "[]int{1, 2}"), ("TwoSum([]int{3, 3}, 6)", "[]int{0, 1}"),
        ("len(TwoSum([]int{1, 2}, 7))", "0"), ("len(TwoSum(nil, 0))", "0"), ("len(TwoSum([]int{5}, 10))", "0"),
        ("TwoSum([]int{-3, 4, 3, 90}, 0)", "[]int{0, 2}"), ("TwoSum([]int{0, 4, 3, 0}, 0)", "[]int{0, 3}"),
        "nums := make([]int, 50000); for i := range nums { nums[i] = i }; return TwoSum(nums, 99997), []int{49998, 49999}",
    ]),
    guide=G(
        "[Maps and structs](#/lesson/go/go-maps-structs): comma-ok lookup.",
        "For each value `x` you need to know whether `target - x` appeared earlier. A map from value to index answers that in constant time.",
        ["Walk the slice once with `for j, x := range nums`.", "Look up `target - x` **before** storing `x`, so an element is never paired with itself.", "Use `i, ok := seen[...]`; index 0 is a valid answer, so do not test for zero."],
        "Two nested loops over all pairs: O(n²). With 50,000 elements that is over a billion comparisons.",
        "**Dry run:** `[3 2 4]`, target 6. j=0: need 3, not seen; store 3→0. j=1: need 4, not seen; store 2→1. j=2: need 2, seen at 1 → `[1 2]`.\n\n"
        "```go\nseen := make(map[int]int, len(nums))\nfor j, x := range nums {\n\tif i, ok := seen[target-x]; ok {\n\t\treturn []int{i, j}\n\t}\n\tif _, dup := seen[x]; !dup {\n\t\tseen[x] = j\n\t}\n}\nreturn nil\n```",
        "O(n) time and space.",
        "Filling the map first and then searching lets an element pair with itself (`[3 2 4]` with target 6 would return `[0 0]`). Returning the values instead of the indexes. Testing `seen[k] != 0` instead of using comma-ok.",
    ),
),
]
