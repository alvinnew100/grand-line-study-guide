# async def, await and the event loop

"Should this endpoint be `async def` or `def`?" is the most common FastAPI question, and getting it wrong
is the most common cause of mysteriously slow services. To answer it you need a mental model of the
**event loop** — which is simpler than its reputation.

## Concurrency is about waiting

A typical API request spends almost all its time *waiting*: for the database, for another service, for a
disk. Lubanovic's chapter 4 illustrates this with a domestic interlude — cleaning the house: you start the
washing machine, and while it runs you wash dishes; you don't stand watching the washer. That's
**concurrency**: making progress on several tasks by switching whenever one is waiting. **Parallelism**
is different: several workers literally working at the same instant (more people cleaning; more CPU
cores).

| | Concurrency (async) | Parallelism (processes) |
|---|---|---|
| Helps with | I/O-bound work (waiting) | CPU-bound work (computing) |
| Mechanism | one thread switches between tasks at `await` | several processes on several cores |
| Python tool | `asyncio` | `multiprocessing`, multiple Uvicorn workers |

Threads sit in between: the OS switches between them pre-emptively. In CPython the **GIL** (global
interpreter lock) lets only one thread execute Python bytecode at a time, so threads help with blocking I/O
(the GIL is released while waiting) but not with pure-Python CPU work. (Native libraries like NumPy and
PyTorch release the GIL during heavy computation, so threads *do* help there. Python 3.13+ also offers an
optional free-threaded build.)

## Coroutines and `await`

`async def` defines a **coroutine function**. Calling it does *not* run it — it returns a coroutine object.
It runs when awaited or scheduled as a task:

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

`await` does two things: it *suspends* the current coroutine until the awaited thing completes, and it
*hands control back to the event loop* so other tasks can run in the meantime. The loop is a simple
scheduler: "which tasks are ready to continue? run each until its next `await`".

The book builds up to this from generators — a function that can pause at `yield` and resume later — and
that's precisely what coroutines are underneath: resumable functions.

## Running things concurrently

Awaiting coroutines one after another is **sequential**. To overlap their waiting, create tasks or use
`asyncio.gather` / `TaskGroup`:

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

Three 0.3 s waits take ~0.9 s sequentially but ~0.3 s concurrently — on **one thread**. In Python 3.11+,
prefer `async with asyncio.TaskGroup() as tg: tg.create_task(...)`: if one task fails, the others are
cancelled and errors are raised together (structured concurrency).

## The cardinal sin: blocking the event loop

The loop can only switch tasks at an `await`. If a coroutine does something slow **without awaiting** —
`time.sleep`, `requests.get`, a synchronous DB driver, a big pandas operation, model inference — *nothing
else runs* on that loop until it finishes. Every other in-flight request on that worker freezes.

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

Look at the tick timestamps: with `blocker`, the heartbeat stalls for 0.35 s. In a real server that stall
is *every other user's request*. With `asyncio.to_thread` the blocking call runs in a thread and the loop
stays responsive.

## How FastAPI runs your functions

This is the key table:

| You write | FastAPI runs it | Blocking calls inside are... |
|---|---|---|
| `async def endpoint()` | directly on the event loop | **catastrophic** — they block all requests on that worker |
| `def endpoint()` | in a **thread pool** (via AnyIO), awaited by the loop | fine — only that thread waits |

The same applies to dependencies, and to background tasks. The thread pool has a default limit of **40**
threads (AnyIO's default limiter), so at most 40 sync endpoints run at once per worker; the rest queue.

So the decision rule, as the FastAPI docs put it:

1. If you use libraries that you call with `await` (async DB driver, `httpx.AsyncClient`, `aiofiles`,
   async Redis): use `async def`.
2. If you use blocking libraries (`requests`, `psycopg2`, sync SQLAlchemy sessions, most ML inference): use
   plain `def`.
3. If your function doesn't do any I/O (just computes a small result): `async def` is fine and slightly
   cheaper (no thread hop).
4. If you don't know: use `def`.

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

Lubanovic gives the same guidance in "FastAPI and Async": you can freely mix sync and async path functions,
and FastAPI arranges that sync ones don't block the async ones.

> [!WARNING]
> The worst configuration is `async def` + blocking library. It looks modern, passes tests (one request at
> a time), and collapses under concurrency: latency for all requests becomes the *sum* of the blocking
> calls. If p99 latency explodes while CPU is idle, suspect this first.

## CPU-bound work

Neither async nor threads speed up pure-Python computation (GIL). Options, in order of preference:

- Use native libraries that release the GIL (NumPy, PyTorch, ONNX Runtime) from a **`def`** endpoint or
  `run_in_threadpool`.
- Run **multiple worker processes** so each core serves requests.
- Offload heavy jobs to a **process pool** (`loop.run_in_executor(ProcessPoolExecutor(), fn, x)`) or a task
  queue (Celery, RQ, Arq, Dramatiq) and return `202 Accepted`.

## Timeouts and cancellation

Never wait forever on a network call. `asyncio.timeout` (3.11+) or `asyncio.wait_for` cancels the awaited
operation:

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

Cancellation is delivered as `asyncio.CancelledError` raised at the current `await`. FastAPI/Starlette
cancel your handler in some situations (e.g. client disconnects during a streaming response), so cleanup
belongs in `try/finally`, and you should never swallow `CancelledError`.

## Async pitfalls beyond blocking

- **Forgetting `await`**: `result = fetch()` gives you a coroutine object, not data (Python warns
  "coroutine was never awaited").
- **Fire-and-forget tasks**: `asyncio.create_task(x())` without keeping a reference can be garbage
  collected mid-flight; keep references or use `BackgroundTasks`/`TaskGroup`.
- **Shared state**: there are no data races *between* awaits, but any `await` is a point where other
  tasks may change shared state. Use `asyncio.Lock` when an invariant spans an await.
- **Sync locks in async code** (`threading.Lock`) can deadlock the loop.

> [!INTERVIEW]
> "What happens if you call `time.sleep(5)` (or `requests.get`) inside an `async def` endpoint?" — The
> function runs on the event loop thread, and the blocking call doesn't yield control, so the loop — and
> therefore every other request on that worker — is frozen for 5 seconds. Fixes: make the endpoint a plain
> `def` (FastAPI runs it in its thread pool), use an async equivalent (`await asyncio.sleep`,
> `httpx.AsyncClient`), or wrap the call in `run_in_threadpool` / `asyncio.to_thread`.

## Summary

- Async gives concurrency for I/O-bound work on one thread; parallelism for CPU work needs processes.
- `await` suspends the coroutine and lets the loop run other tasks; `gather`/`TaskGroup` overlap waits.
- Never block the loop: no sync I/O or heavy CPU inside `async def`.
- FastAPI runs `async def` on the loop and `def` in a 40-thread pool — choose by the libraries you call.
- Use timeouts; clean up in `finally`; re-raise `CancelledError`.

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
