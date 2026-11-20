"""Go track problems, part 4: context trees, tickers, JSON struct tags, test reports and HTTP middleware."""

PROBLEMS = [
# ------------------------------------------------------------------ go-context-tree
dict(
    id="go-context-tree",
    title="Context cancellation through a tree",
    difficulty="Medium",
    pattern="Go context",
    entry="context_states",
    description=r"""
A `context.Context` carries a cancellation signal through a Go program. Contexts form a **tree**:
every context except the root is derived from a parent, and

> when a context is cancelled, **all contexts derived from it are cancelled too**. Cancellation never
> travels upward to the parent.

A context finishes ("is done") for one of two reasons, visible through `ctx.Err()`:

- `"context canceled"`: its cancel function was called;
- `"context deadline exceeded"`: its deadline passed.

Input:

- `nodes`: a list of `[id, parent_id, deadline]` with parents listed before their children.
  `parent_id` is `None` for a root (like `context.Background()`); `deadline` is an absolute time or
  `None` (a context made with `WithCancel` has no deadline of its own).
- `cancels`: a list of `[id, time]`: the cancel function of that context is called at that time
  (if it is called several times, only the earliest matters).

For each context compute:

- its **effective deadline**: the earliest of its own deadline and its parent's effective deadline
  (`None` if neither exists). This is what `ctx.Deadline()` reports.
- the time it becomes done and why. Candidates are: the parent became done (the child takes the
  parent's time **and the parent's error**), its own cancel call, its own deadline. The earliest
  wins. On equal times the priority is: parent first, then own cancel, then own deadline.
  If there is no candidate, it is never done.

Return, in input order, `[id, done_time, error, effective_deadline]` with `None` for "never"/"none".

**Example:** `nodes = [["root", None, None], ["req", "root", 100], ["db", "req", 150], ["cache", "req", 30]]`,
`cancels = [["req", 60]]`

→ `[["root", None, None, None], ["req", 60, "context canceled", 100], ["db", 60, "context canceled", 100], ["cache", 30, "context deadline exceeded", 30]]`
""",
    starter='''def context_states(nodes, cancels):
    pass
''',
    solution='''def context_states(nodes, cancels):
    first_cancel = {}
    for cid, t in cancels:
        if cid not in first_cancel or t < first_cancel[cid]:
            first_cancel[cid] = t
    state = {}
    out = []
    for cid, parent, deadline in nodes:
        p_done, p_err, p_deadline = state[parent] if parent is not None else (None, None, None)
        if deadline is None:
            eff = p_deadline
        elif p_deadline is None:
            eff = deadline
        else:
            eff = min(deadline, p_deadline)
        candidates = []
        if p_done is not None:
            candidates.append((p_done, 0, p_err))
        if cid in first_cancel:
            candidates.append((first_cancel[cid], 1, "context canceled"))
        if deadline is not None:
            candidates.append((deadline, 2, "context deadline exceeded"))
        if candidates:
            t, _, err = min(candidates)
        else:
            t, err = None, None
        state[cid] = (t, err, eff)
        out.append([cid, t, err, eff])
    return out
''',
    tests=[
        [[["root", None, None], ["req", "root", 100], ["db", "req", 150], ["cache", "req", 30]], [["req", 60]]],
        [[], []],
        [[["bg", None, None]], []],
        [[["bg", None, None], ["a", "bg", None]], [["a", 5], ["a", 2], ["a", 9]]],
        [[["bg", None, None], ["a", "bg", None], ["b", "a", None], ["c", "b", None]], [["b", 7]]],
        [[["bg", None, None], ["a", "bg", 50], ["b", "a", 80], ["c", "b", 20], ["d", "c", None]], []],
        [[["bg", None, None], ["a", "bg", 50], ["b", "a", None]], [["b", 50], ["a", 50]]],
        [[["bg", None, None], ["a", "bg", 50], ["b", "a", 50]], [["b", 50]]],
        [[["bg", None, None], ["a", "bg", 10], ["b", "a", None]], [["b", 99], ["a", 40]]],
        [[["r1", None, None], ["r2", None, 5], ["x", "r1", None], ["y", "r2", None]], [["x", 3]]],
        [[["bg", None, None], ["srv", "bg", None], ["r1", "srv", 30], ["r2", "srv", 60], ["q1", "r1", None],
          ["q2", "r2", 45], ["q3", "r2", None]], [["srv", 50], ["q3", 10], ["q1", 31]]],
        [[["n0", None, None]] + [["n%d" % i, "n%d" % (i - 1), 1000 - i] for i in range(1, 60)], [["n30", 500]]],
    ],
    examples=1,
    wrong_solutions=[
        '''def context_states(nodes, cancels):
    fc = {}
    for cid, t in cancels: fc[cid] = min(t, fc.get(cid, t))
    out = []
    for cid, parent, deadline in nodes:
        c = []
        if cid in fc: c.append((fc[cid], 1, "context canceled"))
        if deadline is not None: c.append((deadline, 2, "context deadline exceeded"))
        t, _, e = min(c) if c else (None, None, None)
        out.append([cid, t, e, deadline])
    return out
''',
        '''def context_states(nodes, cancels):
    fc = {}
    for cid, t in cancels: fc[cid] = min(t, fc.get(cid, t))
    st = {}; out = []
    for cid, parent, deadline in nodes:
        pd, pe, pdl = st[parent] if parent is not None else (None, None, None)
        eff = deadline if pdl is None else pdl if deadline is None else min(deadline, pdl)
        c = []
        if pd is not None: c.append((pd, 2, "context canceled"))
        if cid in fc: c.append((fc[cid], 1, "context canceled"))
        if deadline is not None: c.append((deadline, 0, "context deadline exceeded"))
        t, _, e = min(c) if c else (None, None, None)
        st[cid] = (t, e, eff); out.append([cid, t, e, eff])
    return out
''',
    ],
    guide=dict(
        prereqs="Trees processed parent-before-child. Lessons: [Context: cancellation and its tree](#/lesson/go/go-context-cancel) "
                "and [Deadlines, timeouts and context values](#/lesson/go/go-context-deadlines-values).",
        intuition="A context is a walkie-talkie tuned to its parent's channel. When the parent says 'stop', "
                  "every descendant hears it at the same instant and repeats the same reason. A child may also "
                  "decide to stop earlier on its own, but it can never outlive its parent.",
        hints=[
            "Because parents come first in the list, one pass with a dictionary of finished states is enough.",
            "Collect up to three candidate `(time, priority, error)` tuples and take the minimum.",
            "A child inherits the parent's *error text*, not always `canceled`: a parent that timed out makes "
            "its children report `deadline exceeded`.",
        ],
        brute_force="For each node walk up to the root and combine the ancestors' cancels and deadlines: "
                    "O(depth) per node. The one-pass version reuses the parent's already-computed answer.",
        approach=r"""
One pass; `state[id] = (done_time, error, effective_deadline)`.

**Dry run** of the example. `root`: nothing. `req`: cancel at 60 vs deadline 100 → done 60, canceled; effective
deadline 100. `db`: parent done at 60 (canceled) vs own deadline 150 → 60, canceled; effective deadline
`min(150, 100) = 100`. `cache`: parent 60 vs own deadline 30 → 30, deadline exceeded.

**The same tree in Go:**

```go
package main

import (
	"context"
	"fmt"
	"time"
)

func main() {
	root := context.Background()
	req, cancelReq := context.WithTimeout(root, 100*time.Millisecond)
	defer cancelReq()
	db, cancelDB := context.WithTimeout(req, 150*time.Millisecond) // cannot outlive req
	defer cancelDB()
	cache, cancelCache := context.WithTimeout(req, 30*time.Millisecond)
	defer cancelCache()

	time.AfterFunc(60*time.Millisecond, cancelReq) // cancel the request early

	<-cache.Done()
	fmt.Println("cache:", cache.Err()) // context deadline exceeded
	<-db.Done()
	fmt.Println("db:", db.Err())       // context canceled (inherited from req)
	fmt.Println("root:", root.Err())   // <nil>: cancellation never goes up
}
```
""",
        complexity="O(nodes + cancels).",
        pitfalls="Ignoring the parent. Always reporting `canceled` for inherited cancellation. Forgetting "
                 "that a child's deadline later than the parent's has no effect. Wrong tie-break order.",
    ),
),

# ------------------------------------------------------------------ go-ticker-rate-limiter
dict(
    id="go-ticker-rate-limiter",
    title="Rate limiting with time.Ticker",
    difficulty="Medium",
    pattern="Go standard library",
    entry="ticker_starts",
    description=r"""
A simple way to limit how often something happens in Go is a ticker:

```go
ticker := time.NewTicker(period)
for req := range requests {
    <-ticker.C      // wait for the next tick
    handle(req)
}
```

`time.Ticker` fires at times `period, 2*period, 3*period, ...` and delivers each tick on a channel
with a **buffer of exactly one**. If the buffer is still full when the next tick fires, that tick is
**dropped**. So a slow consumer does not get a burst of saved-up ticks later: at most one is waiting.

One goroutine handles requests one after another. `requests` is a list of `[arrival, service]`,
sorted by arrival; all times are non-negative integers and `period >= 1`.

For each request:

1. it is **ready** at `ready = max(arrival, time the previous request finished)` (0 if there is none);
2. it then takes one tick from the channel. Let `c` be the moment the previous tick was taken
   (0 before the first request). The next tick that can be taken is the first multiple of `period`
   that is **strictly greater than `c`**. The request starts at `start = max(ready, that tick time)`;
3. it finishes at `start + service`.

Return `[starts, dropped]` where `dropped` is the number of ticks that fired at or before the last
start time but were never taken, that is `last_start // period - number_of_requests` (0 for no requests).

**Example 1:** `ticker_starts(10, [[0, 1], [0, 1], [0, 1]])` → `[[10, 20, 30], 0]`

**Example 2:** `ticker_starts(10, [[0, 35], [0, 1], [0, 1]])` → `[[10, 45, 50], 2]`
(while the first request ran, the tick at 20 was buffered and the ticks at 30 and 40 were dropped)
""",
    starter='''def ticker_starts(period, requests):
    pass
''',
    solution='''def ticker_starts(period, requests):
    taken = 0
    free = 0
    starts = []
    for arrival, service in requests:
        ready = max(arrival, free)
        tick = (taken // period + 1) * period
        start = max(ready, tick)
        starts.append(start)
        taken = start
        free = start + service
    dropped = starts[-1] // period - len(starts) if starts else 0
    return [starts, dropped]
''',
    tests=[
        [10, [[0, 1], [0, 1], [0, 1]]],
        [10, [[0, 35], [0, 1], [0, 1]]],
        [10, []],
        [1, [[0, 0], [0, 0], [0, 0]]],
        [5, [[100, 1]]],
        [5, [[3, 0], [4, 0], [5, 0], [6, 0]]],
        [10, [[0, 10], [0, 10], [0, 10]]],
        [10, [[0, 9], [0, 11], [0, 1]]],
        [7, [[0, 3], [50, 3], [51, 3], [52, 30], [53, 1]]],
        [10, [[25, 0], [25, 0]]],
        [10, [[20, 0], [20, 0]]],
        [3, [[i, 1] for i in range(40)]],
        [4, [[0, 13], [1, 2], [2, 9], [40, 0], [40, 0]]],
    ],
    examples=2,
    wrong_solutions=[
        '''def ticker_starts(period, requests):
    starts = []; free = 0
    for i, (a, s) in enumerate(requests):
        st = max(a, free, (i + 1) * period)
        starts.append(st); free = st + s
    return [starts, starts[-1] // period - len(starts) if starts else 0]
''',
        '''def ticker_starts(period, requests):
    starts = []; free = 0; nxt = period
    for a, s in requests:
        st = max(a, free, nxt)
        starts.append(st); free = st + s; nxt += period
    return [starts, starts[-1] // period - len(starts) if starts else 0]
''',
        '''def ticker_starts(period, requests):
    starts = []; free = 0
    for a, s in requests:
        r = max(a, free)
        st = -(-r // period) * period if r > 0 else period
        starts.append(st); free = st + s
    return [starts, starts[-1] // period - len(starts) if starts else 0]
''',
    ],
    guide=dict(
        prereqs="Integer division. Lesson: [io, bufio and time](#/lesson/go/go-io-time).",
        intuition="The ticker is a tap that drips into a cup holding one drop. A fast consumer waits for each "
                  "drop. A slow consumer finds one drop waiting, no matter how many dripped while it was "
                  "away, and the next drop comes at the normal rhythm.",
        hints=[
            "You only need two numbers of state: when the last tick was taken and when the worker is free.",
            "The next usable tick is `(taken // period + 1) * period`.",
            "If the request is ready *after* that tick time, the tick was sitting in the buffer and the "
            "request starts immediately at `ready`.",
        ],
        brute_force="Simulate every tick: at each multiple of `period` set a boolean 'buffer full' (or count "
                    "a drop if it already is), and advance the consumer. Correct, but O(total time / period).",
        approach=r"""
One loop with `start = max(ready, next_tick_after(taken))`.

**Dry run** of example 2 (`period 10`): request 0 ready at 0, next tick 10 → start 10, finish 45. Request 1 ready
at 45; ticks after 10 start at 20, which already fired and is buffered → start 45, finish 46. Request 2 ready
at 46; next tick after 45 is 50 → start 50. Ticks fired up to 50: five (10..50); taken: three; dropped: two.

Notice the consequence: after a slow request, two requests ran only 5 time units apart (45 and 50). A ticker
guarantees an *average* rate, not a minimum gap.

**The same pattern in Go:**

```go
package main

import (
	"fmt"
	"time"
)

func main() {
	ticker := time.NewTicker(100 * time.Millisecond)
	defer ticker.Stop() // release the ticker's resources

	start := time.Now()
	for i := 1; i <= 3; i++ {
		<-ticker.C // at most one tick is ever buffered
		fmt.Printf("request %d at ~%dms\n", i, time.Since(start).Milliseconds()/100*100)
	}
}
```

```text
request 1 at ~100ms
request 2 at ~200ms
request 3 at ~300ms
```

For production rate limiting prefer `golang.org/x/time/rate`, a token bucket with a configurable burst.
""",
        complexity="O(number of requests), O(1) extra space.",
        pitfalls="Assuming request `i` uses tick `i+1` (ignores dropped ticks). Rounding `ready` up to a "
                 "multiple of the period (ignores the buffered tick). Using `>=` instead of 'strictly after "
                 "the last taken tick', which would let one tick serve two requests.",
    ),
),

# ------------------------------------------------------------------ go-json-tags
dict(
    id="go-json-tags",
    title="JSON marshalling rules for struct tags",
    difficulty="Medium",
    pattern="Go standard library",
    entry="marshal",
    description=r"""
`encoding/json` turns a Go struct into JSON text by looking at each field's name and its `json`
**struct tag** (a small annotation string). Reproduce its rules.

A struct is given as a list of fields, in declaration order. Each field is `[go_name, tag, value]`
where `tag` is the text inside `json:"..."` (an empty string means the field has no tag) and `value`
is one of: an integer, a boolean, a string (letters, digits, spaces and simple punctuation only),
`None` (a nil pointer, slice or map), a list (a slice), a dictionary with string keys (a Go map), or
a nested struct written as `{"__struct__": [fields]}`.

Rules, applied per field:

1. **Unexported** fields (Go name starting with a lower-case letter) are skipped, whatever the tag says.
2. A tag that is exactly `-` skips the field.
3. Split the tag at commas. The first part is the JSON key; if it is empty, the key is the Go name.
   (So the tag `-,` produces a key that is literally `-`.) The remaining parts are options.
4. Option `omitempty`: skip the field if its value is "empty": `false`, `0`, `""`, `None`, an empty
   list or an empty map. **A nested struct is never empty.**
5. Option `string`: an integer or boolean value is written inside quotes (`42` → `"42"`).

Output format (compact, exactly as Go prints it): no spaces; struct fields in declaration order;
**map keys sorted** alphabetically; `None` → `null`; booleans → `true`/`false`; strings in double quotes.

Return the JSON text.

**Example 1:** `marshal([["ID", "id", 7], ["Name", "", "Ann"], ["password", "pw", "x"], ["Tmp", "-", 1]])`
→ `{"id":7,"Name":"Ann"}`

**Example 2:** `marshal([["Age", "age,omitempty", 0], ["Tags", "tags,omitempty", []], ["N", "n,string", 5]])`
→ `{"n":"5"}`
""",
    starter='''def marshal(fields):
    pass
''',
    solution='''import json


def marshal(fields):
    def is_struct(v):
        return isinstance(v, dict) and "__struct__" in v

    def empty(v):
        if v is None or v is False:
            return True
        if is_struct(v):
            return False
        if isinstance(v, bool):
            return False
        if isinstance(v, int):
            return v == 0
        return len(v) == 0

    def enc(v):
        if is_struct(v):
            return obj(v["__struct__"])
        if isinstance(v, dict):
            return "{" + ",".join(json.dumps(k) + ":" + enc(v[k]) for k in sorted(v)) + "}"
        if isinstance(v, list):
            return "[" + ",".join(enc(x) for x in v) + "]"
        return json.dumps(v)

    def obj(fs):
        parts = []
        for name, tag, val in fs:
            if not name[:1].isupper():
                continue
            if tag == "-":
                continue
            pieces = tag.split(",")
            key = pieces[0] or name
            opts = pieces[1:]
            if "omitempty" in opts and empty(val):
                continue
            text = enc(val)
            if "string" in opts and isinstance(val, int):
                text = json.dumps(text)
            parts.append(json.dumps(key) + ":" + text)
        return "{" + ",".join(parts) + "}"

    return obj(fields)
''',
    tests=[
        [[["ID", "id", 7], ["Name", "", "Ann"], ["password", "pw", "x"], ["Tmp", "-", 1]]],
        [[["Age", "age,omitempty", 0], ["Tags", "tags,omitempty", []], ["N", "n,string", 5]]],
        [[]],
        [[["hidden", "", 1]]],
        [[["Dash", "-,", 1], ["Empty", ",omitempty", ""], ["Kept", ",omitempty", "v"]]],
        [[["A", "a", None], ["B", "b,omitempty", None], ["C", "c", []], ["D", "d", {}], ["E", "e,omitempty", {}]]],
        [[["OK", "ok,omitempty", False], ["Yes", "yes,omitempty", True], ["Flag", "flag,string", True], ["Zero", "zero,string", 0]]],
        [[["M", "m", {"b": 2, "a": 1, "c": [3, 2, 1]}], ["L", "l", ["x", "y"]]]],
        [[["User", "user", {"__struct__": [["Name", "name", "Bo"], ["secret", "s", 1]]}],
          ["Meta", "meta,omitempty", {"__struct__": []}]]],
        [[["Items", "items", [{"__struct__": [["ID", "id", 1], ["Qty", "qty,omitempty", 0]]},
                              {"__struct__": [["ID", "id", 2], ["Qty", "qty,omitempty", 3]]}]],
          ["Total", "total,string,omitempty", 3]]],
        [[["Name", "name,omitempty", " "], ["Count", "count,omitempty", -1], ["Z", "omitempty", 0]]],
        [[["A", "a,omitempty,string", 0], ["B", "b,omitempty,string", 12], ["C", "c,string", "text"]]],
        [[["Outer", "", {"__struct__": [["Inner", "", {"__struct__": [["Deep", "deep", {"k": None}]]}]]}]]],
    ],
    examples=2,
    wrong_solutions=[
        '''import json
def marshal(fields):
    d = {}
    for name, tag, val in fields:
        if tag == "-": continue
        p = tag.split(",")
        if "omitempty" in p[1:] and not val: continue
        d[p[0] or name] = val
    return json.dumps(d, separators=(",", ":"))
''',
        '''import json
def marshal(fields):
    def is_struct(v): return isinstance(v, dict) and "__struct__" in v
    def enc(v):
        if is_struct(v): return obj(v["__struct__"])
        if isinstance(v, dict): return "{" + ",".join(json.dumps(k) + ":" + enc(v[k]) for k in sorted(v)) + "}"
        if isinstance(v, list): return "[" + ",".join(enc(x) for x in v) + "]"
        return json.dumps(v)
    def obj(fs):
        parts = []
        for name, tag, val in fs:
            if not name[:1].isupper() or tag.startswith("-"): continue
            pieces = tag.split(","); key = pieces[0] or name; opts = pieces[1:]
            if "omitempty" in opts and (val is None or val == 0 or val == "" or val == [] or val == {} or val == {"__struct__": []}):
                continue
            text = enc(val)
            if "string" in opts and isinstance(val, int): text = json.dumps(text)
            parts.append(json.dumps(key) + ":" + text)
        return "{" + ",".join(parts) + "}"
    return obj(fields)
''',
    ],
    guide=dict(
        prereqs="Recursion, string building. Lesson: [encoding/json](#/lesson/go/go-json).",
        intuition="For every field ask three questions in order: may I see it (exported, not `-`)? what is it "
                  "called (tag name or Go name)? should I leave it out (`omitempty` and empty)? Then encode the "
                  "value by its kind, recursing into containers.",
        hints=[
            "Write `enc(value)` for values and `obj(fields)` for structs; they call each other.",
            "Check `bool` before `int` in Python, because `True` is an instance of `int`.",
            "A struct with zero fields still prints `{}` under `omitempty`; only maps and slices can be 'empty'.",
        ],
        brute_force="Building a Python dict and calling `json.dumps` loses three things at once: unexported "
                    "fields, the `string` option and the never-empty rule for structs.",
        approach=r"""
Two mutually recursive functions; build strings with `",".join(...)`.

**Dry run** of example 2: `Age` has `omitempty` and value 0 → skipped. `Tags` has `omitempty` and `[]` → skipped.
`N` has option `string` → `5` becomes `"5"`. Result `{"n":"5"}`.

**The same rules in Go:**

```go
package main

import (
	"encoding/json"
	"fmt"
)

type Address struct {
	City string `json:"city,omitempty"`
}

type User struct {
	ID       int               `json:"id"`
	Name     string            // no tag: key is "Name"
	password string            // unexported: never marshalled
	Age      int               `json:"age,omitempty"`
	Balance  int64             `json:"balance,string"`
	Tmp      int               `json:"-"`
	Addr     Address           `json:"addr,omitempty"` // a struct is never "empty"
	Labels   map[string]string `json:"labels"`
}

func main() {
	u := User{ID: 7, Name: "Ann", password: "x", Balance: 5,
		Labels: map[string]string{"b": "2", "a": "1"}}
	out, _ := json.Marshal(u)
	fmt.Println(string(out))
}
```

```text
{"id":7,"Name":"Ann","balance":"5","addr":{},"labels":{"a":"1","b":"2"}}
```

Since Go 1.24 the option `omitzero` exists for the case `omitempty` cannot handle: it omits a struct whose
fields are all zero (and `time.Time{}`).
""",
        complexity="O(size of the value tree).",
        pitfalls="Marshalling unexported fields. Treating `-,` like `-`. Omitting empty structs. Forgetting to "
                 "sort map keys. Applying `string` to string values.",
    ),
),

# ------------------------------------------------------------------ go-table-test-summary
dict(
    id="go-table-test-summary",
    title="Table-test report in go test -v style",
    difficulty="Medium",
    pattern="Go testing",
    entry="test_report",
    description=r"""
In a Go **table-driven test** one test function loops over a list of cases and runs each as a
**subtest** with `t.Run(name, func(t *testing.T) {...})`. `go test -v` then prints one line per test
and subtest.

You are given the leaf outcomes in execution order as `[test, subtest, outcome]`:

- `test` is the top-level function name, e.g. `"TestAdd"`;
- `subtest` is the name passed to `t.Run`, or `None` when the test function has no subtests
  (such a test appears exactly once);
- `outcome` is `"pass"`, `"fail"` or `"skip"`.

Go's rules to reproduce:

1. **Subtest names are rewritten**: every space becomes an underscore.
2. **Duplicate names** inside the same test get a suffix: the second `x` becomes `x#01`, the third
   `x#02`, and so on (two digits). Compare names after rule 1.
3. A test with subtests is `FAIL` if any subtest failed, otherwise `PASS` (even when every subtest
   was skipped). A test without subtests has its own outcome.
4. The whole run is `FAIL` if any top-level test is `FAIL`, otherwise `PASS`.

Output a list of lines. For each top-level test, in order of first appearance:

- `--- STATUS: TestName`
- then for each of its subtests in order: four spaces, then `--- STATUS: TestName/subtest_name`

with `STATUS` being `PASS`, `FAIL` or `SKIP`. The final line is `FAIL` or `PASS` for the whole run.

**Example:** `[["TestAdd", "zero", "pass"], ["TestAdd", "big numbers", "fail"], ["TestName", None, "skip"]]`

→ `["--- FAIL: TestAdd", "    --- PASS: TestAdd/zero", "    --- FAIL: TestAdd/big_numbers", "--- SKIP: TestName", "FAIL"]`
""",
    starter='''def test_report(results):
    pass
''',
    solution='''def test_report(results):
    order = []
    subs = {}
    own = {}
    counts = {}
    for top, sub, outcome in results:
        if top not in subs:
            order.append(top)
            subs[top] = []
            own[top] = None
            counts[top] = {}
        if sub is None:
            own[top] = outcome
            continue
        name = sub.replace(" ", "_")
        seen = counts[top].get(name, 0)
        counts[top][name] = seen + 1
        if seen:
            name = "%s#%02d" % (name, seen)
        subs[top].append((name, outcome))
    lines = []
    failed = False
    for top in order:
        if subs[top]:
            status = "FAIL" if any(o == "fail" for _, o in subs[top]) else "PASS"
        else:
            status = (own[top] or "pass").upper()
        failed = failed or status == "FAIL"
        lines.append("--- %s: %s" % (status, top))
        for name, o in subs[top]:
            lines.append("    --- %s: %s/%s" % (o.upper(), top, name))
    lines.append("FAIL" if failed else "PASS")
    return lines
''',
    tests=[
        [[["TestAdd", "zero", "pass"], ["TestAdd", "big numbers", "fail"], ["TestName", None, "skip"]]],
        [[]],
        [[["TestOne", None, "pass"]]],
        [[["TestOne", None, "fail"], ["TestTwo", None, "pass"]]],
        [[["TestSkip", "a", "skip"], ["TestSkip", "b", "skip"]]],
        [[["TestDup", "case", "pass"], ["TestDup", "case", "pass"], ["TestDup", "case", "fail"]]],
        [[["TestDup", "a b", "pass"], ["TestDup", "a_b", "pass"], ["TestOther", "a b", "pass"]]],
        [[["TestA", "x", "pass"], ["TestB", "x", "fail"], ["TestA", "y", "pass"], ["TestB", "x", "pass"]]],
        [[["TestParse", "empty input", "pass"], ["TestParse", "only  spaces", "pass"], ["TestParse", "ok", "skip"]]],
        [[["TestT", "c%d" % (i % 3), "fail" if i == 7 else "pass"] for i in range(12)]],
        [[["TestA", None, "skip"], ["TestB", None, "skip"]]],
        [[["TestX", "n", "pass"]] * 11],
    ],
    examples=1,
    wrong_solutions=[
        '''def test_report(results):
    lines = []; failed = False
    for top, sub, outcome in results:
        if sub is None:
            lines.append("--- %s: %s" % (outcome.upper(), top))
        else:
            lines.append("    --- %s: %s/%s" % (outcome.upper(), top, sub.replace(" ", "_")))
        failed = failed or outcome == "fail"
    lines.append("FAIL" if failed else "PASS")
    return lines
''',
        '''def test_report(results):
    order = []; subs = {}; own = {}
    for top, sub, outcome in results:
        if top not in subs:
            order.append(top); subs[top] = []; own[top] = None
        if sub is None: own[top] = outcome
        else: subs[top].append((sub.replace(" ", "_"), outcome))
    lines = []; failed = False
    for top in order:
        if subs[top]:
            st = "FAIL" if any(o == "fail" for _, o in subs[top]) else ("SKIP" if all(o == "skip" for _, o in subs[top]) else "PASS")
        else:
            st = own[top].upper()
        failed = failed or st == "FAIL"
        lines.append("--- %s: %s" % (st, top))
        for name, o in subs[top]:
            lines.append("    --- %s: %s/%s" % (o.upper(), top, name))
    lines.append("FAIL" if failed else "PASS")
    return lines
''',
    ],
    guide=dict(
        prereqs="Dictionaries that preserve insertion order. Lesson: "
                "[Tests, tables, subtests and coverage](#/lesson/go/go-testing-basics).",
        intuition="Group the leaves by parent while remembering the order parents first appeared, tidy each "
                  "subtest name the way Go does, then print parents with a status computed from their children.",
        hints=[
            "Collect first, print second: the parent line comes before its children but depends on all of them.",
            "Keep a per-test counter of how many times each (rewritten) name has been used.",
            "A parent with only skipped children passes.",
        ],
        brute_force="Printing one line per input row as it arrives cannot produce the parent lines or their "
                    "status, and it misses the duplicate-name suffix.",
        approach=r"""
Pass 1 groups and renames; pass 2 prints.

**Dry run:** `TestDup` with subtests `case`, `case`, `case` (pass, pass, fail). Names become `case`, `case#01`,
`case#02`. One failed → parent `FAIL`. Lines: `--- FAIL: TestDup`, `    --- PASS: TestDup/case`,
`    --- PASS: TestDup/case#01`, `    --- FAIL: TestDup/case#02`, `FAIL`.

**A table-driven test in Go:**

```go
package calc

import "testing"

func Add(a, b int) int { return a + b }

func TestAdd(t *testing.T) {
	cases := []struct {
		name       string
		a, b, want int
	}{
		{"zero", 0, 0, 0},
		{"big numbers", 1 << 40, 1, 1<<40 + 1},
		{"negative", -2, -3, -5},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			if got := Add(tc.a, tc.b); got != tc.want {
				t.Errorf("Add(%d, %d) = %d, want %d", tc.a, tc.b, got, tc.want)
			}
		})
	}
}
```

```text
$ go test -v -run 'TestAdd/big_numbers'
=== RUN   TestAdd
=== RUN   TestAdd/big_numbers
--- PASS: TestAdd (0.00s)
    --- PASS: TestAdd/big_numbers (0.00s)
PASS
```

The rewritten name (`big_numbers`) is what you type after `-run` to execute a single case.
""",
        complexity="O(number of results).",
        pitfalls="Forgetting the space-to-underscore rewrite before counting duplicates. Marking an all-skip "
                 "parent as SKIP. Sharing duplicate counters between different top-level tests.",
    ),
),

# ------------------------------------------------------------------ go-middleware-chain
dict(
    id="go-middleware-chain",
    title="HTTP middleware chain order",
    difficulty="Medium",
    pattern="Go backend",
    entry="serve",
    description=r"""
In Go's `net/http`, a **handler** answers a request. A **middleware** is a function that takes a
handler and returns a new handler wrapping it, so it can run code before and after the inner one,
or refuse to call it at all:

```go
func logging(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        log.Println("before")
        next.ServeHTTP(w, r)   // call the wrapped handler
        log.Println("after")
    })
}
```

Wrapping several middlewares produces layers like an onion. Simulate one request passing through.

`middlewares` is a list of `[name, kind, arg]`:

| kind | behaviour |
|---|---|
| `"log"` | records `name:before`, calls the next layer, then records `name:after` (skipped if a panic passes through) |
| `"deferlog"` | records `name:before`, calls the next layer, and records `name:after` **even if a panic passes through** (it uses `defer`) |
| `"auth"` | if the header named `arg` is in `headers`: calls the next layer. Otherwise records `name:deny`, answers status `401` and does **not** call the next layer |
| `"recover"` | calls the next layer; if a panic comes out of it, records `name:recovered` and answers status `500` |

`order` says how the list was wrapped around the handler:

- `"first_outermost"`: the first middleware in the list is the outermost layer (what routers such as chi do with `r.Use(a, b, c)`);
- `"last_outermost"`: the result of the naive loop `for _, m := range list { h = m(h) }`, where the last one ends up outermost.

`handler` is `"ok"` (records `handler`, status `200`) or `"panic"` (records `handler`, then panics).

Return `[events, status]`. If a panic escapes every layer, the status is the string `"crash"`.

**Example 1:** `serve([["L","log",None], ["A","auth","Token"]], "first_outermost", "ok", ["Token"])`
→ `[["L:before", "handler", "L:after"], 200]`

**Example 2:** same middlewares, `headers = []` → `[["L:before", "A:deny", "L:after"], 401]`

**Example 3:** same middlewares with `"last_outermost"` and `headers = []` → `[["A:deny"], 401]`
""",
    starter='''def serve(middlewares, order, handler, headers):
    pass
''',
    solution='''def serve(middlewares, order, handler, headers):
    chain = list(middlewares) if order == "first_outermost" else list(middlewares)[::-1]
    events = []

    class Panic(Exception):
        pass

    def call(i):
        if i == len(chain):
            events.append("handler")
            if handler == "panic":
                raise Panic()
            return 200
        name, kind, arg = chain[i]
        if kind == "log":
            events.append(name + ":before")
            status = call(i + 1)
            events.append(name + ":after")
            return status
        if kind == "deferlog":
            events.append(name + ":before")
            try:
                return call(i + 1)
            finally:
                events.append(name + ":after")
        if kind == "auth":
            if arg not in headers:
                events.append(name + ":deny")
                return 401
            return call(i + 1)
        if kind == "recover":
            try:
                return call(i + 1)
            except Panic:
                events.append(name + ":recovered")
                return 500

    try:
        status = call(0)
    except Panic:
        status = "crash"
    return [events, status]
''',
    tests=[
        [[["L", "log", None], ["A", "auth", "Token"]], "first_outermost", "ok", ["Token"]],
        [[["L", "log", None], ["A", "auth", "Token"]], "first_outermost", "ok", []],
        [[["L", "log", None], ["A", "auth", "Token"]], "last_outermost", "ok", []],
        [[], "first_outermost", "ok", []],
        [[], "last_outermost", "panic", []],
        [[["R", "recover", None], ["L", "log", None], ["D", "deferlog", None]], "first_outermost", "panic", []],
        [[["R", "recover", None], ["L", "log", None], ["D", "deferlog", None]], "last_outermost", "panic", []],
        [[["L1", "log", None], ["L2", "log", None], ["L3", "log", None]], "first_outermost", "ok", []],
        [[["L1", "log", None], ["L2", "log", None], ["L3", "log", None]], "last_outermost", "ok", []],
        [[["D", "deferlog", None], ["L", "log", None]], "first_outermost", "panic", []],
        [[["A", "auth", "X-Key"], ["B", "auth", "X-Admin"], ["L", "log", None]], "first_outermost", "ok", ["X-Key"]],
        [[["A", "auth", "X-Key"], ["B", "auth", "X-Admin"], ["L", "log", None]], "first_outermost", "ok", ["X-Admin", "X-Key"]],
        [[["D", "deferlog", None], ["R", "recover", None], ["A", "auth", "T"], ["L", "log", None]], "first_outermost", "panic", ["T"]],
        [[["D", "deferlog", None], ["R", "recover", None], ["A", "auth", "T"], ["L", "log", None]], "last_outermost", "panic", ["T"]],
        [[["R1", "recover", None], ["R2", "recover", None]], "first_outermost", "panic", []],
    ],
    examples=3,
    wrong_solutions=[
        '''def serve(middlewares, order, handler, headers):
    chain = list(middlewares)
    events = []
    class Panic(Exception): pass
    def call(i):
        if i == len(chain):
            events.append("handler")
            if handler == "panic": raise Panic()
            return 200
        name, kind, arg = chain[i]
        if kind == "log":
            events.append(name + ":before"); s = call(i + 1); events.append(name + ":after"); return s
        if kind == "deferlog":
            events.append(name + ":before")
            try: return call(i + 1)
            finally: events.append(name + ":after")
        if kind == "auth":
            if arg not in headers:
                events.append(name + ":deny"); return 401
            return call(i + 1)
        try: return call(i + 1)
        except Panic:
            events.append(name + ":recovered"); return 500
    try: status = call(0)
    except Panic: status = "crash"
    return [events, status]
''',
        '''def serve(middlewares, order, handler, headers):
    chain = list(middlewares) if order == "first_outermost" else list(middlewares)[::-1]
    events = []
    class Panic(Exception): pass
    def call(i):
        if i == len(chain):
            events.append("handler")
            if handler == "panic": raise Panic()
            return 200
        name, kind, arg = chain[i]
        if kind in ("log", "deferlog"):
            events.append(name + ":before")
            try: return call(i + 1)
            finally: events.append(name + ":after")
        if kind == "auth":
            if arg not in headers:
                events.append(name + ":deny"); return 401
            return call(i + 1)
        try: return call(i + 1)
        except Panic:
            events.append(name + ":recovered"); return 500
    try: status = call(0)
    except Panic: status = "crash"
    return [events, status]
''',
        '''def serve(middlewares, order, handler, headers):
    chain = list(middlewares) if order == "first_outermost" else list(middlewares)[::-1]
    events = []; status = 200
    for name, kind, arg in chain:
        if kind in ("log", "deferlog"): events.append(name + ":before")
        if kind == "auth" and arg not in headers:
            events.append(name + ":deny"); return [events, 401]
    events.append("handler")
    if handler == "panic":
        status = "crash"
        for name, kind, arg in chain[::-1]:
            if kind == "recover":
                events.append(name + ":recovered"); status = 500; break
    for name, kind, arg in chain[::-1]:
        if kind in ("log", "deferlog"): events.append(name + ":after")
    return [events, status]
''',
    ],
    guide=dict(
        prereqs="Recursion and exceptions. Lesson: "
                "[A REST service: routing, handlers and middleware](#/lesson/go/go-rest-service).",
        intuition="Middlewares are the layers of an onion and the handler is the centre. A request travels "
                  "inward through every layer's 'before' code, reaches the centre, and the response travels "
                  "back out through the 'after' code in the opposite order. Any layer can stop the trip early.",
        hints=[
            "Recursion mirrors the nesting: `call(i)` runs layer `i` and calls `call(i + 1)` for the inner layers.",
            "Model a Go panic with a Python exception; `defer` is `finally`, `recover` is `except`.",
            "For `last_outermost`, reverse the list once and reuse the same code.",
        ],
        brute_force="Two flat loops (all the 'before' events, then all the 'after' events in reverse) handle "
                    "the happy path only. Early returns from `auth` and panics caught half-way need real nesting.",
        approach=r"""
Build the chain in outermost-first order, then recurse.

**Dry run:** `[R recover, L log, D deferlog]`, first outermost, handler panics. `R` calls `L`: `L:before`. `L`
calls `D`: `D:before`. Handler: `handler`, panic. Unwinding: `D`'s deferred log runs → `D:after`. `L`'s plain
'after' line is skipped. `R` recovers → `R:recovered`, status 500.
Events: `L:before, D:before, handler, D:after, R:recovered`.

**The same chain in Go:**

```go
package main

import (
	"fmt"
	"net/http"
	"net/http/httptest"
)

type Middleware func(http.Handler) http.Handler

// Chain makes the FIRST middleware the outermost layer.
func Chain(h http.Handler, ms ...Middleware) http.Handler {
	for i := len(ms) - 1; i >= 0; i-- { // wrap from the inside out
		h = ms[i](h)
	}
	return h
}

func Log(name string) Middleware {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			fmt.Println(name + ":before")
			defer fmt.Println(name + ":after")
			next.ServeHTTP(w, r)
		})
	}
}

func Auth(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Header.Get("Token") == "" {
			http.Error(w, "unauthorized", http.StatusUnauthorized)
			return // the inner handler is never called
		}
		next.ServeHTTP(w, r)
	})
}

func main() {
	hello := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) { fmt.Println("handler") })
	h := Chain(hello, Log("L"), Auth)

	rec := httptest.NewRecorder()
	h.ServeHTTP(rec, httptest.NewRequest("GET", "/", nil))
	fmt.Println(rec.Code)
}
```

```text
L:before
L:after
401
```
""",
        complexity="O(number of middlewares) per request.",
        pitfalls="Wrapping in the wrong direction (the naive loop reverses the order you wrote). Putting the "
                 "recover middleware inside the logger, so the logger never sees the 500. Writing 'after' code "
                 "without `defer`, so it is skipped on panic.",
    ),
),
]
