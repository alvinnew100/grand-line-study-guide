# Root-cause analysis from evidence: logs, graphs, stack traces, bisecting and five whys

> **Before this lesson:** read [Hypothesis-driven triage](#/lesson/thinking/hypothesis-triage). That lesson is about deciding *what to look at*. This one is about *reading what you find* — the raw material an interviewer may put in front of you.

## In plain words

A detective at a scene does not start with a theory. They start with what is there: a broken window, mud on the carpet, a clock stopped at 9:40. Each item of evidence rules some stories out and makes others more likely, and the detective keeps going until only one story fits everything.

Some interviews hand you evidence instead of a vague complaint: a page of **logs** (lines of text a program writes as it works), a **graph** of some measurement over time, or a **stack trace** (the report a program prints when it crashes). The question is "what happened?" You are being tested on careful reading and on not jumping to the first story that fits one clue. At work, this is everyday: most bugs are solved by someone reading an error message properly.

**Root-cause analysis**, shortened to RCA, means going beyond "what broke" to "why was it possible for this to break, and why did nothing stop it?"

## Tool 1 — Reading a stack trace

When a program hits an error it cannot handle, it prints where it was. A program runs functions that call other functions; the list of "who called whom" at the moment of the crash is the **call stack**, and the printout is the stack trace.

Start with the smallest possible example.

```python-run
def average(values):
    return sum(values) / len(values)      # line 2

def report(scores):
    return "Average: " + str(average(scores))   # line 5

try:
    print(report([]))                      # line 8
except Exception:
    import traceback
    traceback.print_exc()
```

Run it. The output ends with something like:

```text
Traceback (most recent call last):
  File "...", line 8, in <module>
    print(report([]))
  File "...", line 5, in report
    return "Average: " + str(average(scores))
  File "...", line 2, in average
    return sum(values) / len(values)
ZeroDivisionError: division by zero
```

How to read it, in order:

1. **Read the last line first.** It names the **exception** (the kind of error) and a message: `ZeroDivisionError: division by zero`. That is *what* went wrong.
2. **Read upward from the bottom.** In Python the last frame listed is where the error happened: `average`, line 2. (Java and JavaScript print the other way round, with the failing frame at the top. The first thing to learn about any language's traces is which end is which.)
3. **Find the first line that is your own code.** Real traces are full of library and framework lines. The interesting frame is usually the deepest one in code your team wrote.
4. **Ask what value made that line fail.** Division by zero means `len(values)` was 0, so `values` was empty.
5. **Walk up to find where the bad value came from.** `average` did what it was told. `report` passed it an empty list. Who gave `report` an empty list?

Step 5 is the difference between a patch and a fix. The crash is in `average`; the *cause* may be three calls higher, where a filter removed every score. Adding `if not values: return 0` silences the crash and may hide a real problem — a report of "average: 0" for a class whose scores failed to load.

Some trace patterns and what they usually mean:

| Message | Usually means |
|---|---|
| `NullPointerException`, `NoneType has no attribute`, `undefined is not a function` | Something expected to exist was missing: a lookup returned nothing |
| `KeyError`, `IndexError`, `ArrayIndexOutOfBounds` | Asked for an item that is not there: empty list, off-by-one, unexpected key |
| `TimeoutError`, `Connection refused`, `Connection reset` | Another service or the network did not answer |
| `OutOfMemoryError`, `Killed` | The process used more memory than allowed |
| `StackOverflowError`, `RecursionError` | A function kept calling itself with no end |
| `"Caused by:"` chains | One error wrapped another; the **last** "Caused by" is the original |

## Tool 2 — Reading logs

A log line normally has a **timestamp**, a **severity level** (DEBUG, INFO, WARN, ERROR), the component, and a message. Many systems add a **request ID** — a label attached to everything done for one user request, so its lines can be collected from several services.

Here is a small extract an interviewer might show:

```text
10:01:58 INFO  api      req=a1 GET /cart user=17 200 45ms
10:02:00 INFO  deploy   version 2.4.1 started on api-3
10:02:03 WARN  api-3    req=b7 pool wait 800ms
10:02:04 INFO  api      req=b8 GET /cart user=22 200 51ms
10:02:05 ERROR api-3    req=b7 POST /checkout user=31 500 db timeout after 5000ms
10:02:05 WARN  api-3    req=c2 pool wait 2100ms
10:02:06 ERROR api-3    req=c2 POST /checkout user=40 500 db timeout after 5000ms
10:02:07 INFO  api-1    req=c5 POST /checkout user=41 200 310ms
10:02:09 ERROR api-3    req=c9 POST /checkout user=52 500 no connections available
```

A method for any log:

1. **Find the first error, not the loudest.** The first ERROR is at 10:02:05. But two seconds earlier there is a WARN — "pool wait 800ms" — and three seconds before that, a deploy. The earliest unusual line is the best clue; later errors are often consequences.
2. **Look at what immediately precedes it.** A deploy of version 2.4.1 on `api-3` at 10:02:00.
3. **Group the errors by something.** Every error is on `api-3`. A checkout on `api-1` at 10:02:07 succeeded. So the fault is specific to one machine — the one with the new version.
4. **Follow one request ID.** `b7`: waited 800 ms for the pool, then timed out talking to the database after 5 seconds.
5. **Notice what is absent.** No errors on `GET /cart`. No errors on other machines. No database error saying the database itself is down.

Vocabulary: a **connection pool** is a fixed set of open connections to a database that requests borrow and return, because opening a new one each time is slow. "No connections available" means all are in use and none came back.

**The story that fits all the evidence:** version 2.4.1 on `api-3` is borrowing database connections during checkout and not returning them (a *leak*). The pool empties; requests wait, then time out. Machines still on the old version are unaffected. **Next checks:** the count of connections in use on `api-3` against other machines; the code change in 2.4.1 around checkout. **Mitigation:** halt the rollout and roll `api-3` back.

Notice the wrong stories that single clues suggest: "db timeout" alone says "the database is slow" — contradicted by `api-1` succeeding against the same database.

> [!INTERVIEW]
> Say what the evidence **excludes** as well as what it suggests: "the database itself is probably healthy, because another server reached it in 310 ms at the same moment." Interviewers plant such a line to see whether you use it.

## Tool 3 — Reading graphs

A graph question usually shows a metric over time and asks what happened. Read it in a fixed order.

1. **Axes and units.** What is measured, per what, over how long? A y-axis that does not start at zero can make a 2 % wobble look like a cliff.
2. **Shape.** Each shape hints at a family of cause.

| Shape | Typical causes |
|---|---|
| **Step** — sudden jump to a new level that stays | A deploy, a configuration change, a failed component |
| **Spike** — up and back | A burst of traffic, a short outage, a retry storm, a scheduled job |
| **Ramp** — steady climb | A leak, a queue falling behind, data growth |
| **Sawtooth** — climb, drop, climb | Memory growing until a restart or garbage collection; a cache filling and being cleared |
| **Periodic** — repeats daily or hourly | Human rhythms, scheduled jobs |
| **Flat line at a round number** | A limit being hit: pool size, quota, rate limit |
| **Drop to zero** | The thing stopped — or the *measurement* stopped |

3. **Timing.** What else happened at that minute? Overlay deploys, configuration changes and incidents.
4. **Other metrics at the same time.** Errors up while traffic is flat suggests a fault; errors and traffic up together suggests overload; traffic *down* with errors flat may mean users cannot even reach you.
5. **Breakdowns.** Split by version, region, endpoint, customer. A step that exists in only one slice localises the cause.

The last row of the table catches many people. A graph of "orders per minute" falling to zero might mean no orders — or that the component that counts orders has crashed while orders continue. Always ask whether a second, independent signal agrees.

## Tool 4 — Bisecting

**Bisection** finds *which change* broke something when there are many candidates. It is the number-guessing game: "I'm thinking of a number between 1 and 100" is solved in seven guesses by always halving the range.

Suppose a test passed at commit 1 and fails at commit 64. (A **commit** is one saved change in the history of the code.) Test commit 32. If it fails, the culprit is in 2–32; if it passes, in 33–64. Repeat. Sixty-four commits need six tests, since $2^6 = 64$; a thousand need ten.

```python-run
def first_bad(n, is_bad):
    lo, hi = 1, n                # lo is known good-or-unknown, hi is known bad
    steps = 0
    while lo < hi:
        mid = (lo + hi) // 2
        steps += 1
        if is_bad(mid):
            hi = mid             # culprit is mid or earlier
        else:
            lo = mid + 1         # culprit is after mid
    return lo, steps

culprit = 45
print(first_bad(64, lambda c: c >= culprit))     # (45, 6)
print(first_bad(1000, lambda c: c >= 733))       # (733, 10)
```

The function keeps a range that must contain the first bad commit and halves it each loop. The tool `git bisect` automates this on a real repository.

Conditions for bisecting to work: the failure must be **reproducible** (a test that fails only sometimes will mislead it — run it several times per step), and there must be a clear good point and bad point. The same halving idea works beyond commits: half the configuration, half the input file, half the plugins.

## Tool 5 — Five whys

Finding the faulty line answers "what broke". The **five whys** technique asks "why?" repeatedly to reach causes that are worth fixing. Five is a habit, not a law; stop when you reach something you can change that would prevent a whole class of failures.

Continuing the connection-leak example:

1. *Why did checkout fail?* Requests could not get a database connection.
2. *Why?* Version 2.4.1 did not return connections when a payment was declined.
3. *Why?* An early `return` was added before the line that releases the connection.
4. *Why was that not caught?* No test covers the declined-payment path, and the pool has no leak warning.
5. *Why did it reach customers?* The rollout had no automatic check on error rate after the first machine.

Now there are fixes at several depths: repair the line (necessary, shallow); release connections with a construct that cannot be skipped; add the missing test; add a leak alert; add a gate to the rollout. The deeper fixes prevent other bugs you have not met yet.

Three cautions:

- **There is rarely a single root cause.** Real incidents need several things to go wrong together. Write "contributing causes".
- **Never stop at a person.** "Because Sam forgot" is not a cause you can fix. Ask why the system allowed forgetting to matter. This is the *blameless* principle from the Google SRE book: people act reasonably given what they knew, so fix the system around them.
- **Do not stop at the first plausible why.** "The database timed out" was a symptom two levels above the cause.

## Putting it together: a worked exercise

**Prompt.** "Here is what we know. At 14:00 the share of successful payments fell from 98 % to 91 % and stayed there. No deploy of the payments service that day. Overall traffic is normal. What do you do, and what might you find?" Attempt before opening.

<details><summary>Model answer</summary>

**Read the shape.** A *step* to a new stable level: something changed at 14:00 and stayed changed. Not a spike (burst), not a ramp (leak).

**What it excludes.** Traffic is normal, so not overload. A fall of 7 points rather than to zero means most payments work — the failure is in a *subset*.

**Break it down.** Split success rate by card type, bank, country, device, app version, payment provider and amount. I'm looking for one slice that went from 98 % to near zero while the rest stayed flat; a 7-point overall drop is what a complete failure of a 7 % slice looks like.

**What changed, if not our deploy?** A configuration or flag change; a deploy of a *different* service that payments calls; a certificate that expired at 14:00 (round times are suspicious); a change on the provider's side; a new app version released to stores.

**Suppose the breakdown shows:** all failures are one card network through one provider, and logs for those requests show `error=invalid_merchant_config`. First error at 14:00:03; no warnings before. Then the provider's status page or our own configuration history is the next check. Say we find that a configuration push at 14:00 from another team rotated a credential for that network.

**Mitigate.** Revert the configuration, or route that card network through the backup provider.

**Five whys.** Payments failed → credential invalid → rotated without updating the dependent setting → the two settings live in different places with no link → configuration changes do not go through the staged rollout and checks that code does. Actions: validate configuration before applying; roll configuration out gradually like code; alert on payment success *per card network*; add the dependency to the rotation runbook.

**What I'd say to the interviewer.** "A step change with normal traffic and a partial drop says a subset broke because of a change. I'd find the subset by slicing and the change by timeline, mitigate by reverting or rerouting, then ask why configuration can change without the safeguards code has."

</details>

## Common mistakes

- Reading the top of a trace and stopping, or reading only the bottom when the language prints the other way.
- Fixing where it crashed instead of where the bad value came from.
- Building a story on one log line and ignoring a line that contradicts it.
- Treating things that happened at the same time as cause and effect without a mechanism.
- Believing a graph without checking its axes, or that the measurement itself is alive.
- Ending the analysis at a person.

## Summary

- Stack trace: read the error line, find the failing frame in your own code, ask what value broke it, then trace that value upward.
- Logs: earliest anomaly first; group errors by machine, version or endpoint; follow one request ID; note what is absent.
- Graphs: axes, shape, timing, companion metrics, breakdowns. Steps suggest changes; ramps suggest leaks; flat tops suggest limits.
- Bisect when there are many candidate changes: halve the range each test.
- Five whys turns one bug into several preventive fixes; there are usually several contributing causes, and none of them is a person.

## Glossary

| Term | Meaning |
|---|---|
| Root-cause analysis (RCA) | Working out why a failure was possible, not only what failed |
| Log | Text lines a program writes describing what it is doing |
| Stack trace | A printout of the chain of function calls at the moment of an error |
| Exception | An error signalled by a program at run time |
| Frame | One entry in a stack trace: one function call |
| Request ID | A label attached to all work done for one request |
| Connection pool | A reusable set of open connections to a database |
| Leak | A resource that is taken and never given back |
| Commit | One saved change in a code history |
| Bisection | Finding a culprit by repeatedly halving the range of candidates |
| Five whys | Asking "why?" repeatedly to reach fixable underlying causes |
| Contributing cause | One of several conditions that together allowed a failure |

## Check yourself

```quiz
[
  {"q": "In a Python stack trace, where is the line on which the error occurred?",
   "options": ["The first frame listed", "The last frame listed, directly above the error message", "It is not shown", "Always in the middle"],
   "answer": 1,
   "explain": "Python prints the most recent call last, so the failing frame sits at the bottom, above the exception line."},
  {"q": "A function crashes with division by zero because it received an empty list. What is the better fix?",
   "options": ["Return 0 for empty lists and move on", "Find out why the caller passed an empty list, and decide what should happen in that case", "Catch every exception and ignore it", "Delete the function"],
   "answer": 1,
   "explain": "The crash site is where the problem surfaced; the cause is where the unexpected value was produced."},
  {"q": "Errors appear only on the one server running the new version, while another server reaches the database quickly. What does this exclude?",
   "options": ["A bug in the new version", "The database being generally slow or down", "A connection leak", "A bad deploy"],
   "answer": 1,
   "explain": "A healthy response from the same database at the same time shows the database is not the common fault."},
  {"q": "A metric jumps at 14:00 to a new level and stays there. Which cause family fits best?",
   "options": ["A memory leak", "A change such as a deploy, configuration push or failed component", "Normal daily rhythm", "Random noise"],
   "answer": 1,
   "explain": "A step is the signature of something switching from one state to another; leaks produce ramps."},
  {"q": "A test passed at commit 1 and fails at commit 512. How many tests does bisection need at most?",
   "options": ["9", "64", "256", "512"],
   "answer": 0,
   "explain": "Each test halves the range; 2^9 = 512, so nine halvings isolate the first bad commit."},
  {"q": "Which is an acceptable final answer in a five-whys chain?",
   "options": ["Because the engineer was careless", "Because configuration changes bypass the checks and staged rollout that code changes get", "Because it broke", "Because computers are unreliable"],
   "answer": 1,
   "explain": "A useful cause is a property of the system that can be changed; blaming a person fixes nothing."},
  {"q": "A graph of orders per minute falls to exactly zero. What should you check before concluding there are no orders?",
   "options": ["Nothing", "Whether the measurement itself is still working, using an independent signal", "The colour of the graph", "Yesterday's weather"],
   "answer": 1,
   "explain": "A dead counter looks identical to a dead business; confirm with a second source."}
]
```

> **Source:** Google SRE Book, "Effective Troubleshooting" (https://sre.google/sre-book/effective-troubleshooting/), "Postmortem Culture: Learning from Failure" (https://sre.google/sre-book/postmortem-culture/) and "Monitoring Distributed Systems" (https://sre.google/sre-book/monitoring-distributed-systems/); Git documentation, `git bisect` (https://git-scm.com/docs/git-bisect). Examples, log extracts and wording are original.
