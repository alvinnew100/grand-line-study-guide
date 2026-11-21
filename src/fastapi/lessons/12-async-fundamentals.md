# async def, await and the event loop

> **Before this lesson:** you should know that FastAPI runs on an event loop and a thread pool
> ([lesson 3](#/lesson/fastapi/asgi-stack)) and what a generator and `yield` are
> ([lesson 11](#/lesson/fastapi/yield-deps)). No earlier experience with `async` or `await` is
> assumed; both are built up from zero here.

## In plain words

A web server spends most of its time *waiting*: for a database to answer, for another service to
reply, for a file to be read. While one request waits, the processor has nothing to do for that
request. **Async** programming is a way of writing code so that this idle time is used to make
progress on other requests.

An everyday picture: one cook in a kitchen. The cook puts a pot on to boil, and while it heats,
chops vegetables for a second dish, then stirs a third. One person, several dishes moving forward,
because the cook never stands watching the pot. Now imagine the cook *does* stand and stare at the
pot for ten minutes. Every other dish in the kitchen stops. In a server, that staring cook is a
"blocking call" in the wrong place, and it is the most common cause of FastAPI services that are slow
for no visible reason.

In FastAPI the cook is called the **event loop**. This lesson explains what it is, what the keywords
`async` and `await` tell it, and how to answer the question every FastAPI programmer asks: "should
this endpoint be `async def` or `def`?"

Why this matters for a job: that question comes up in almost every FastAPI interview, usually as
"what happens if you call `time.sleep(5)` inside an `async def` endpoint?". You will be able to
answer it, and to demonstrate the answer with code.

## Concurrency is about waiting

Lubanovic's chapter 4 illustrates the idea with housework: you start the washing machine, and while
it runs you wash the dishes. Two words describe ways of getting several things done, and they are
not the same:

- **Concurrency** means making progress on several tasks by switching between them whenever one is
  waiting. One worker, many tasks in progress.
- **Parallelism** means several workers each working at the same instant: more people cleaning, or
  more processor cores computing.

Which one helps depends on what the work is. **I/O-bound** work spends its time waiting for input
and output (network, disk, database). **CPU-bound** work spends its time computing.

| | Concurrency (async) | Parallelism (processes) |
|---|---|---|
| Helps with | I/O-bound work (waiting) | CPU-bound work (computing) |
| Mechanism | one thread switches between tasks at `await` | several processes on several cores |
| Python tool | `asyncio` | `multiprocessing`, multiple Uvicorn workers |

**Threads** sit between the two. A thread is a separate line of execution inside one program, and
the operating system switches between threads on its own schedule, without asking them. In the
standard Python interpreter the **GIL** (global interpreter lock) allows only one thread at a time to
run Python code. Threads therefore help with waiting (the lock is released while a thread waits for
I/O) but not with computation written in Python. Libraries written in compiled languages, such as
NumPy and PyTorch, release the lock during heavy calculation, so threads *do* help there. (Python
3.13 and later also offer an optional build without the GIL.)

## Coroutines and `await`

Writing `async def` in place of `def` defines a **coroutine function**. The first surprise is that
calling it does *not* run it. The call returns a **coroutine object**, a "task ready to be run". The
body runs only when the object is awaited (or scheduled as a task, shown below).

```python-run
import asyncio

async def fetch(name, delay):
    print(f"{name}: start")
    await asyncio.sleep(delay)        # "I'm waiting - loop, run something else"
    print(f"{name}: done")
    return name.upper()

coro = fetch("a", 0.1)
print(type(coro).__name__)            # coroutine - nothing has run yet
print(await coro)                     # now it runs
```

Line by line:

- `async def fetch(name, delay):` defines a coroutine function.
- `await asyncio.sleep(delay)` waits for `delay` seconds *without holding up the program*. It stands
  in for any wait, such as a database query.
- `coro = fetch("a", 0.1)` calls the function. Nothing is printed yet.
- `print(type(coro).__name__)` prints `coroutine`, confirming that we hold an object and no code has
  run.
- `print(await coro)` runs it. Now `a: start` and `a: done` appear, followed by the return value `A`.

`await` does two things at once. It **pauses** the current coroutine until the thing being awaited
has finished. And it **hands control back to the event loop**, so that other tasks can run in the
meantime. The event loop is a small scheduler whose whole job is: "which tasks are ready to
continue? Run each one until its next `await`."

The book reaches this point by way of generators, the functions from lesson 11 that pause at
`yield` and resume later. That is what coroutines are underneath: functions that can be paused and
resumed.

## Running things concurrently

Awaiting coroutines one after another is **sequential**: the second does not start until the first
has finished. To make their waits overlap, hand them to the loop together with `asyncio.gather`:

```python-run
import asyncio, time

async def call_service(name, delay):
    await asyncio.sleep(delay)        # stands in for a DB query or HTTP call
    return f"{name} ok"

t = time.perf_counter()
a = await call_service("users", 0.3)
b = await call_service("orders", 0.3)
c = await call_service("prices", 0.3)
print("sequential:", round(time.perf_counter() - t, 2), "s")

t = time.perf_counter()
a, b, c = await asyncio.gather(call_service("users", 0.3),
                               call_service("orders", 0.3),
                               call_service("prices", 0.3))
print("concurrent:", round(time.perf_counter() - t, 2), "s", [a, b, c])
```

- `call_service` waits for a given time and returns a string. It stands for a database query or a
  call to another service.
- `time.perf_counter()` reads a precise clock; subtracting two readings gives the elapsed time.
- The first block awaits three calls in turn. Each takes 0.3 seconds.
- The second block passes all three to `asyncio.gather`, which starts them all and waits until all
  have finished, returning their results in order.

The output is `sequential: 0.9 s` and then `concurrent: 0.3 s` with the three results (the timings
may differ by a hundredth or so). Three 0.3-second waits take 0.9 seconds one after another but 0.3
seconds when overlapped, and all of it on **one thread**. Nothing ran at the same instant; the waits
overlapped.

In Python 3.11 and later, prefer `async with asyncio.TaskGroup() as tg: tg.create_task(...)`. If one
task fails, the group cancels the others and reports the errors together. This discipline is known
as structured concurrency.

## The cardinal sin: blocking the event loop

The loop can only switch tasks at an `await`. A call that makes the program wait *without* an
`await` is called a **blocking** call: `time.sleep`, `requests.get`, a synchronous database driver,
a large pandas operation, running a machine-learning model. If a coroutine makes such a call,
*nothing else runs* on that loop until it returns. Every other request being handled by that worker
is frozen.

```python-run
import asyncio, time

async def heartbeat():
    for i in range(6):
        print(f"  tick {i} at {time.perf_counter() - T:.2f}s")
        await asyncio.sleep(0.1)

async def well_behaved():
    await asyncio.sleep(0.35)             # yields to the loop while waiting

async def blocker():
    time.sleep(0.35)                      # blocks the whole event loop!

async def offloaded():
    await asyncio.to_thread(time.sleep, 0.35)   # run the blocking call in a worker thread

for fn in (well_behaved, blocker, offloaded):
    print(fn.__name__)
    T = time.perf_counter()
    try:
        await asyncio.gather(heartbeat(), fn())
    except Exception as e:                # (browser runtimes without threads can't run to_thread)
        print("  not supported here:", type(e).__name__)
```

The experiment runs a `heartbeat` coroutine, which prints a tick every 0.1 seconds, alongside three
different companions:

- `well_behaved` waits with `await asyncio.sleep(0.35)`. The ticks appear on time: about 0.0, 0.1,
  0.2, 0.3 and so on.
- `blocker` waits with `time.sleep(0.35)`, the ordinary blocking sleep. Look at the tick times: there
  is a gap of about 0.35 seconds during which no tick could be printed. The loop was stuck inside
  `time.sleep` and could not switch to the heartbeat.
- `offloaded` moves the same blocking call to another thread with `asyncio.to_thread`. Where threads
  are available the ticks stay regular. Some browser runtimes have no threads, in which case this
  part prints `not supported here`.

In a real server, that gap is *every other user's request* standing still.

## How FastAPI runs your functions

This table is the heart of the lesson:

| You write | FastAPI runs it | Blocking calls inside are... |
|---|---|---|
| `async def endpoint()` | directly on the event loop | **catastrophic**: they block all requests on that worker |
| `def endpoint()` | in a **thread pool**, awaited by the loop | fine: only that one thread waits |

A **thread pool** is a fixed set of threads kept ready for jobs. FastAPI hands every plain `def`
endpoint to one of them, so that a blocking call inside it holds up only that thread. The same holds
for dependencies and background tasks. The pool has a default limit of **40** threads (set by AnyIO,
the library FastAPI uses for this), so at most 40 synchronous endpoints run at once in each worker;
further ones wait their turn.

The decision rule, following the FastAPI documentation:

1. If you use libraries that are called with `await` (an async database driver, `httpx.AsyncClient`,
   `aiofiles`, async Redis): use `async def`.
2. If you use blocking libraries (`requests`, `psycopg2`, synchronous SQLAlchemy sessions, most
   machine-learning inference): use plain `def`.
3. If your function does no I/O at all and only computes a small result: `async def` is fine and
   slightly cheaper, because no thread hand-over is needed.
4. If you do not know: use `def`.

```python
@app.get("/sync-db")
def read_users(session: SessionDep):          # sync driver -> def, runs in thread pool
    return session.exec(select(User)).all()

@app.get("/proxy")
async def proxy(http: HttpDep):               # async client -> async def
    r = await http.get("https://api.example.com/data")
    return r.json()

@app.get("/mixed")
async def mixed():
    # must call a blocking function from async code? push it to a thread explicitly
    from fastapi.concurrency import run_in_threadpool
    result = await run_in_threadpool(blocking_function, arg)
    return result
```

Three endpoints, three cases. `read_users` uses a synchronous database session, so it is a plain
`def` and runs in the thread pool. `proxy` uses an async HTTP client, so it is `async def` and awaits
the call. `mixed` is an `async def` that must call a blocking function anyway; it pushes that one
call onto a thread with `run_in_threadpool` and awaits the result.

Lubanovic gives the same guidance in "FastAPI and Async": synchronous and asynchronous path functions
can be mixed freely, and FastAPI arranges matters so that the synchronous ones do not block the
asynchronous ones.

> [!WARNING]
> The worst combination is `async def` with a blocking library. It looks modern and it passes tests
> (which send one request at a time), and then it collapses when many requests arrive together: every
> request waits for the blocking calls of all the requests ahead of it. If the slowest requests
> become dramatically slower under load while the processor is nearly idle, suspect this first.

## CPU-bound work

Neither async nor threads speed up computation written in pure Python, because of the GIL. The
options, in order of preference:

- Use compiled libraries that release the GIL (NumPy, PyTorch, ONNX Runtime) from a **`def`**
  endpoint, or through `run_in_threadpool`.
- Run **several worker processes** (lesson 3), so that each processor core serves requests.
- Hand heavy jobs to a **process pool**
  (`loop.run_in_executor(ProcessPoolExecutor(), fn, x)`) or to a task queue (Celery, RQ, Arq,
  Dramatiq: separate programs that run jobs outside the web server) and answer `202 Accepted`.

## Timeouts and cancellation

Never wait without limit on a network call. A **timeout** is a maximum waiting time.
`asyncio.timeout` (Python 3.11 and later) and `asyncio.wait_for` both stop the awaited operation
when the time is up:

```python-run
import asyncio

async def slow_upstream():
    try:
        await asyncio.sleep(5)
        return "data"
    except asyncio.CancelledError:
        print("upstream call cancelled - cleaning up")
        raise                                   # always re-raise CancelledError

try:
    async with asyncio.timeout(0.2):
        await slow_upstream()
except TimeoutError:
    print("-> respond 504 Gateway Timeout")
```

- `slow_upstream` would take 5 seconds. ("Upstream" means a service that yours depends on.)
- `async with asyncio.timeout(0.2):` allows at most 0.2 seconds for the code inside.
- When time runs out, the loop **cancels** the coroutine: it raises a special exception,
  `asyncio.CancelledError`, inside it at the line where it is waiting. The `except` branch prints a
  message and re-raises.
- Outside, the timeout block turns the cancellation into a `TimeoutError`, and the code prints the
  response it would send.

The output is `upstream call cancelled - cleaning up` and then `-> respond 504 Gateway Timeout`.

FastAPI and Starlette cancel your handler themselves in some situations, for instance when a client
disconnects in the middle of a streamed response. Put clean-up in `try` / `finally`, and never
swallow `CancelledError`: always re-raise it.

## Async pitfalls beyond blocking

- **Forgetting `await`.** `result = fetch()` gives you a coroutine object, not data. Python prints
  the warning "coroutine was never awaited".
- **Fire-and-forget tasks.** `asyncio.create_task(x())` starts a coroutine running in the
  background. If you keep no reference to the returned task, Python's memory clean-up (garbage
  collection) may discard it half-way through. Keep a reference, or use `BackgroundTasks` or a
  `TaskGroup`.
- **Shared state.** Between two `await`s nothing else can run, so plain steps are safe. But every
  `await` is a point at which other tasks may change data you both use. Protect a rule that must
  hold across an `await` with an `asyncio.Lock`.
- **Thread locks in async code.** A `threading.Lock` held across an `await` can freeze the loop.

> [!INTERVIEW]
> "What happens if you call `time.sleep(5)` (or `requests.get`) inside an `async def` endpoint?" — The
> function runs on the event loop's thread, and the blocking call does not hand control back, so the
> loop, and with it every other request on that worker, is frozen for 5 seconds. Fixes: make the
> endpoint a plain `def` (FastAPI runs it in its thread pool), use an async equivalent
> (`await asyncio.sleep`, `httpx.AsyncClient`), or wrap the call in `run_in_threadpool` /
> `asyncio.to_thread`.

## Build an event loop in thirty lines

The loop stops being mysterious once you have written one. Coroutines are functions that can be
resumed. A scheduler keeps a queue of tasks that are ready to run and a list of tasks that are
asleep, and again and again runs one ready task until it next pauses. Below, plain generators play
the part of coroutines, and `yield seconds` plays the part of `await asyncio.sleep(seconds)`. Time is
simulated, so the output is the same on every run:

```python-run
import heapq
from collections import deque

class MiniLoop:
    def __init__(self):
        self.ready, self.sleeping, self.now, self.seq = deque(), [], 0.0, 0

    def create_task(self, gen, name):
        self.ready.append((gen, name))

    def run(self):
        while self.ready or self.sleeping:
            if not self.ready:                               # nothing runnable: jump to next wake-up
                wake, _, gen, name = heapq.heappop(self.sleeping)
                self.now = max(self.now, wake)
                self.ready.append((gen, name))
            gen, name = self.ready.popleft()
            try:
                delay = next(gen)                            # run until the task's next "await"
            except StopIteration:
                print(f"t={self.now:.1f}  {name} finished")
                continue
            self.seq += 1
            heapq.heappush(self.sleeping, (self.now + delay, self.seq, gen, name))

def request(name, db_time, loop):
    print(f"t={loop.now:.1f}  {name} start, querying db")
    yield db_time                                            # await db.execute(...)
    print(f"t={loop.now:.1f}  {name} got rows, calling upstream")
    yield 0.2                                                # await http.get(...)

def blocking_request(name, loop):
    print(f"t={loop.now:.1f}  {name} start, BLOCKING for 1.0s (time.sleep / sync driver)")
    loop.now += 1.0                                          # holds the thread: nobody else can run
    yield 0

loop = MiniLoop()
loop.create_task(request("A", 0.3, loop), "A")
loop.create_task(request("B", 0.1, loop), "B")
loop.run()
print("--- same two requests, plus one that blocks the loop ---")
loop = MiniLoop()
loop.create_task(request("A", 0.3, loop), "A")
loop.create_task(blocking_request("X", loop), "X")
loop.create_task(request("B", 0.1, loop), "B")
loop.run()
```

How the miniature loop works:

- `self.ready` is a queue of tasks that can run now. `self.sleeping` is a heap (a structure that
  always gives back the smallest item first) of tasks ordered by wake-up time. `self.now` is the
  simulated clock.
- `run` repeats until both are empty. If nothing is ready, it jumps the clock forward to the next
  wake-up time and moves that task to the ready queue.
- It takes one ready task and calls `next(gen)`, which runs the generator up to its next `yield`.
  The yielded number is how long the task wants to sleep, so the task is filed under
  `now + delay`. When a generator ends, `StopIteration` is raised and the task is reported finished.
- `request` simulates a handler with two waits. `blocking_request` simulates a handler that holds
  the thread for a full second: it pushes the clock forward itself and gives nobody else a turn.

In the first run, A and B overlap: A starts at 0.0 and B at 0.0; B gets its rows at 0.1, A at 0.3;
B finishes at 0.3 and A at 0.5. Their waits add up to 0.8 seconds, yet both are done by 0.5.

In the second run, request X never hands control back. The clock moves forward a full second while
A sits waiting and B has not even *started*; B's first line is printed at `t=1.0`. That is exactly
what `time.sleep`, `requests.get` or a synchronous database call does inside an `async def`
endpoint.

The real `asyncio` loop adds a way of asking the operating system which network connections have
data ready, plus callbacks, cancellation and error handling. The scheduling idea is the same.

## Measuring the damage

A small experiment puts numbers on the cost: ten "requests", each needing 50 milliseconds of I/O,
handled in two ways.

```python-run
import asyncio, time

async def good_handler():
    await asyncio.sleep(0.05)                 # async driver: yields while waiting

async def bad_handler():
    time.sleep(0.05)                          # sync call inside async def: blocks the loop

async def measure(handler, n=10):
    latencies, t0 = [], time.perf_counter()
    async def one():
        start = time.perf_counter()
        await handler()
        latencies.append(time.perf_counter() - start)
    await asyncio.gather(*(one() for _ in range(n)))
    total = time.perf_counter() - t0
    return total, max(latencies)

for name, handler in (("await asyncio.sleep", good_handler), ("time.sleep in async", bad_handler)):
    total, worst = await measure(handler)
    print(f"{name:22} total {total:.2f}s   throughput {10 / total:5.0f} req/s")
```

`measure` starts ten copies of a handler together with `gather` and times the whole batch. With the
well-behaved handler, the ten waits overlap: the total is about 0.05 seconds, a **throughput**
(requests completed per second) of roughly 200. With the blocking handler, each `time.sleep` holds
the loop, the ten run one after another, the total is about 0.5 seconds, and throughput falls to
about 20.

The same work, and roughly ten times less of it gets done. In a real server the last request in the
line waits for all the others, so the slowest response times grow in step with the number of
simultaneous requests. (Those slowest times are often quoted as *p99 latency*: the response time
that 99% of requests beat.)

## Finding a blocked loop in practice

The pattern of symptoms is distinctive: response times rise with load while processor use stays
low, health checks time out now and then, and *unrelated* endpoints slow down together. Ways to
confirm it:

- **asyncio debug mode.** Start the program with the environment variable `PYTHONASYNCIODEBUG=1`.
  The loop then logs every step of a task that takes longer than 100 milliseconds, naming the
  coroutine: `Executing <Task ...> took 1.203 seconds`.
- **A watchdog task.** A coroutine that sleeps for 100 milliseconds in a loop, and records how late
  it wakes each time, measures the loop's delay directly. Publish that number as a metric.
- **Sampling profilers.** `py-spy dump --pid <pid>` prints what every thread of a running program
  is doing at that instant, without stopping it. If the main thread is inside a network read
  underneath your endpoint, you have found the blocking call.
- **Reading the code.** Inside `async def` functions, look for `requests.`, `time.sleep`, `open(`
  on large files, `subprocess.run`, synchronous database, Redis or cloud clients, heavy `json` or
  pandas work, and model inference.

## Sync-to-async translation table

| Blocking call | Async-friendly replacement |
|---|---|
| `time.sleep(n)` | `await asyncio.sleep(n)` |
| `requests.get(url)` | `await client.get(url)` with a shared `httpx.AsyncClient` |
| `psycopg2` / sync SQLAlchemy session | `asyncpg`, psycopg 3 async, `AsyncSession` — or keep sync and use `def` endpoints |
| `redis.Redis` | `redis.asyncio.Redis` |
| `open(...).read()` on big files | `aiofiles`, or `await run_in_threadpool(...)` |
| `subprocess.run(...)` | `await asyncio.create_subprocess_exec(...)` |
| `boto3` calls | `aioboto3`/`aiobotocore`, or a thread |
| CPU-heavy function | `await run_in_threadpool(fn)` (GIL-releasing native code) or a process pool |
| `threading.Lock` | `asyncio.Lock` |
| `queue.Queue` | `asyncio.Queue` |

When no async library exists for something, wrapping the call in `run_in_threadpool` or
`asyncio.to_thread` is a perfectly respectable answer. It occupies one of the worker's pool threads
for the duration of the call.

## Summary

- Async gives concurrency for I/O-bound work on one thread; parallelism for CPU-bound work needs
  processes.
- `await` pauses the coroutine and lets the loop run other tasks; `gather` and `TaskGroup` make
  waits overlap.
- Never block the loop: no synchronous I/O and no heavy computation inside `async def`.
- FastAPI runs `async def` on the loop and `def` in a 40-thread pool; choose according to the
  libraries you call.
- Use timeouts; clean up in `finally`; re-raise `CancelledError`.

## Glossary

- **Concurrency** — progress on several tasks by switching between them while they wait.
- **Parallelism** — several workers computing at the same instant.
- **I/O-bound / CPU-bound** — limited by waiting on input and output / limited by computing.
- **Coroutine function** — a function defined with `async def`.
- **Coroutine object** — what calling a coroutine function returns; it runs when awaited.
- **`await`** — pause here until the awaited thing finishes, and let the loop run others meanwhile.
- **Event loop** — the scheduler that runs ready tasks until their next `await`.
- **Task** — a coroutine handed to the loop to run concurrently.
- **`asyncio.gather`** — start several coroutines and wait for all of them.
- **Blocking call** — a call that waits without `await`, stopping the whole loop.
- **Thread pool** — a fixed set of threads to which FastAPI gives plain `def` functions.
- **GIL** — the lock that lets only one thread run Python code at a time.
- **Timeout** — a maximum time to wait for an operation.
- **Cancellation** — stopping a coroutine by raising `CancelledError` at its current `await`.
- **Throughput** — requests completed per second.
- **p99 latency** — the response time that 99% of requests are faster than.

```quiz
[
  {"q": "What does calling an 'async def' function without await return?", "options": ["Its result", "A coroutine object that hasn't run yet", "None", "A thread"], "answer": 1,
   "explain": "Coroutine functions return coroutine objects; the body runs only when awaited or scheduled as a task."},
  {"q": "Three independent 1-second I/O calls are awaited with asyncio.gather. Approximate total time?", "options": ["3 s", "1 s", "0.33 s", "Depends on CPU cores"], "answer": 1,
   "explain": "Their waiting overlaps on the single event loop, so the total is about the longest one."},
  {"q": "How does FastAPI execute a plain 'def' endpoint?", "options": ["On the event loop directly", "In a thread pool, so blocking calls don't stall the loop", "In a new process", "It refuses to run it"], "answer": 1,
   "explain": "Sync endpoints and dependencies are run via a thread pool (default limit 40 threads)."},
  {"q": "Your endpoint uses the blocking 'requests' library. Which declaration is correct?", "options": ["async def, calling requests.get directly", "def (sync), so it runs in the thread pool", "async def with time.sleep", "It doesn't matter"], "answer": 1,
   "explain": "Blocking libraries belong in sync endpoints (or behind run_in_threadpool); in async def they freeze the loop."},
  {"q": "Why doesn't asyncio speed up a pure-Python CPU-heavy loop?", "options": ["asyncio is slow", "There is no await point and only one thread runs the loop; CPU work needs parallelism (processes)", "The GIL is disabled", "Uvicorn forbids it"], "answer": 1,
   "explain": "Async helps when tasks wait. CPU-bound work occupies the single loop thread; use processes or GIL-releasing native code."},
  {"q": "What should you do after catching asyncio.CancelledError to clean up?", "options": ["Return None", "Re-raise it", "Call sys.exit", "Retry the operation"], "answer": 1,
   "explain": "Swallowing cancellation breaks timeouts and shutdown; clean up, then re-raise."},
  {"q": "p99 latency is terrible under load but CPU usage is low. Most likely culprit?", "options": ["Too many workers", "Blocking I/O inside async def endpoints", "Pydantic validation", "JSON serialisation"], "answer": 1,
   "explain": "A blocked event loop serialises all requests on a worker while the CPU sits idle waiting on I/O."}
]
```

> **Source:** Lubanovic, *FastAPI*, ch. 4 "Async, Concurrency, and Starlette Tour" (Types of Concurrency, Python Generators, Python async, await, and asyncio, FastAPI and Async, Interlude: Cleaning the Clue House); https://fastapi.tiangolo.com/async/; Python docs, asyncio
