# Health checks, logging and observability

> **Before this lesson:** you should know middleware and structured logging with request IDs
> ([lesson 21](#/lesson/fastapi/errors-middleware)), how replicas, orchestrators and graceful
> shutdown work ([lesson 25](#/lesson/fastapi/deploy-docker)), timeouts in async code
> ([lesson 12](#/lesson/fastapi/async-fundamentals)), and which HTTP methods are idempotent
> ([lesson 2](#/lesson/fastapi/rest-json)). In Python you need classes, dictionaries and the `with`
> statement.

## In plain words

Once a service is deployed, two questions dominate its life. *Is it healthy right now?* And when
something goes wrong: *why did that request fail, or why is everything slow?* You cannot attach a
debugger to a program serving ten thousand users on twenty machines. You can only look at the signals
it gives off. **Observability** is the ability to understand what is happening inside a system from
the outside, using those signals.

Think of driving a car. The **warning lights** tell you at a glance whether something needs attention
(health checks). The **gauges** show speed, fuel and temperature as numbers changing over time
(metrics). The **trip log** records each event in detail: "14:02, refuelled, 40 litres" (logs). A
**route replay** shows exactly where on the journey you were stuck in traffic and for how long
(traces). And the car has **fuses**, so that one shorted circuit cannot burn out the whole electrical
system (resilience patterns such as the circuit breaker, which is named after the electrical part in
your home).

Lubanovic touches these topics in two places: "Other Service-Level Stuff" in the service-layer chapter
(logging; metrics, monitoring and observability; tracing) and "Troubleshooting" in the production
chapter. This lesson turns them into concrete FastAPI practice.

Why this matters for a job: whoever builds a service usually also runs it, including being woken at
night when it breaks (being **on call**). Interviewers ask about liveness versus readiness probes, why
p99 latency matters more than the average, and how to retry safely. Those answers are all here.

## Health checks

An orchestrator such as Kubernetes, and most load balancers, regularly send small HTTP requests to
each copy of your app to decide what to do with it. Each such check is called a **probe**. Kubernetes
distinguishes three, and the distinction is worth adopting anywhere:

| Probe | Question | On failure |
|---|---|---|
| **Liveness** | Is the process alive and not stuck? | **restart** the container |
| **Readiness** | Can it serve traffic *right now*? | **stop sending it requests** (no restart) |
| **Startup** | Has slow initialisation finished? | hold off the liveness checks until it has |

In FastAPI, probes are ordinary endpoints:

```python
from fastapi import APIRouter, Request, Response, status

router = APIRouter(tags=["health"], include_in_schema=False)

@router.get("/healthz")                      # liveness: cheap, no dependencies
async def liveness():
    return {"status": "ok"}

@router.get("/readyz")                       # readiness: am I able to do my job?
async def readiness(request: Request, response: Response):
    checks = {
        "model_loaded": getattr(request.app.state, "model", None) is not None,
        "database": await ping_db(request.app.state.engine, timeout=1.0),
    }
    if not all(checks.values()):
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return {"status": "ok" if all(checks.values()) else "unavailable", "checks": checks}
```

Line by line:

- `APIRouter(tags=["health"], include_in_schema=False)` groups the probes in a router and hides them
  from the OpenAPI documentation, since clients have no use for them.
- `/healthz` (the `z` is a long-standing naming habit that avoids clashing with real routes) returns
  `{"status": "ok"}` and does nothing else. If the process can answer at all, it is alive.
- `/readyz` builds a dictionary of checks. `getattr(request.app.state, "model", None)` looks for a
  model stored on the app during startup and gives `None` if it is not there yet. `ping_db(...)`
  stands for a function that runs a trivial query such as `SELECT 1` with a one-second limit.
- `all(checks.values())` is true only if every check passed. If not, the endpoint sets the status to
  `503 Service Unavailable` through the injected `Response` object, which tells the balancer "not
  now".

The rules that prevent self-inflicted outages:

- **Liveness must not check dependencies.** Suppose liveness queried the database and the database
  had a 30-second hiccup. Every replica would fail liveness at once, and the orchestrator would
  restart *all* of them, turning a brief database blip into a full outage. Worse, all the fresh
  processes then reconnect at the same moment (a **thundering herd**). Liveness answers only "is this
  process responsive?".
- **Readiness may check critical dependencies**, with short timeouts. It should also fail during
  startup (model still loading) and during graceful shutdown, so that the balancer stops sending new
  requests while the replica drains.
- Keep probes fast and unauthenticated, but reveal little: a true/false per check, not version
  numbers and error details.
- If the event loop is blocked, the liveness endpoint stops answering and times out. That is a useful
  signal: a process stuck in that way genuinely needs restarting.

The decision an orchestrator makes, as a small function:

```python-run
def orchestrator_action(live, ready):
    if not live:  return "RESTART container"
    if not ready: return "remove from load balancer (keep running)"
    return "route traffic"

scenarios = {
    "starting: model still loading": (True, False),
    "normal operation":              (True, True),
    "database unreachable":          (True, False),   # readiness fails, liveness must NOT
    "event loop deadlocked":         (False, False),
    "draining during shutdown":      (True, False),
}
for name, (live, ready) in scenarios.items():
    print(f"{name:32} -> {orchestrator_action(live, ready)}")
```

`orchestrator_action` checks liveness first, then readiness. The dictionary maps five situations to
a pair `(live, ready)`, and the loop prints the action for each. Only one situation, the deadlocked
event loop, leads to a restart. The database outage, the slow startup and the shutdown all lead to
"remove from load balancer (keep running)": the process is fine and will be useful again shortly.
**Deadlocked** means stuck forever, typically two pieces of code each waiting for the other.

## The three pillars

Observability is usually described as three kinds of signal, the "three pillars":

| Pillar | Answers | Shape | Tools |
|---|---|---|---|
| **Logs** | what exactly happened in this request? | individual events, high detail | stdout → Loki, ELK, CloudWatch |
| **Metrics** | how is the system behaving overall? trends, alerts | numbers over time, cheap | Prometheus + Grafana, Datadog |
| **Traces** | where did the time go, across services? | a tree of timed steps per request | OpenTelemetry → Jaeger, Tempo |

### Logs

A **log** is a record of an event, written as the program runs. Lesson 21 built the practice in
detail: **structured** logs (each line is a JSON object with named fields rather than free text), one
event per line, written to **stdout** (the process's standard output, which the platform collects
for you; do not manage log files inside containers), with a **request ID** on every line so that all
lines of one request can be found together, and never any secrets or personal data.

Two additions for this lesson. Put the **trace ID** (below) on each log line as well, so that you can
jump from a suspicious log line to the full trace of its request. And configure Uvicorn's own loggers
(`uvicorn.error` and `uvicorn.access`) to use the same format, or replace the access log with one line
of your own per request from middleware, carrying the method, the route template, the status, the
duration and the user or tenant. The book points out that the default access log records the time,
method and URL of each call, but nothing from the body or headers, so on its own it cannot tell you
*why* a request failed.

### Metrics

A **metric** is a number measured repeatedly over time: requests per second, error count, memory in
use. Each measurement stream is a **time series**. Metrics are cheap to store and fast to query,
which makes them the right tool for dashboards and alerts. The common pairing, which the book also
names, is **Prometheus** to collect metrics and **Grafana** to draw them. Prometheus works by
**scraping**: every few seconds it requests `/metrics` from each replica and stores the numbers it
finds.

What to measure? For a service that handles requests, start with the **RED** method, per endpoint:
**R**ate (requests per second), **E**rrors (failed requests per second) and **D**uration (how long
they take). For resources such as a database pool or a queue use **USE**: **U**tilisation (how busy),
**S**aturation (how much work is waiting) and **E**rrors. Google's four "golden signals" (latency,
traffic, errors, saturation) say the same thing.

Prometheus has three main metric types:

- **Counter**: only ever goes up, such as `http_requests_total`. Rates come from how fast it rises.
- **Gauge**: goes up and down, such as requests in progress, queue depth, database connections in
  use.
- **Histogram**: counts observations into **buckets** by size, such as "how many requests took at
  most 50 ms, at most 100 ms, ...". Percentiles are estimated from the buckets.

Each series can carry **labels**, key-value pairs such as `route="/items/{item_id}"` or
`status="404"`, that let you slice the numbers. Here is a small metrics store written from scratch,
printing the plain-text format that Prometheus scrapes:

```python-run
import bisect
from collections import defaultdict

BUCKETS = [0.05, 0.1, 0.25, 0.5, 1.0, float("inf")]      # upper bounds in seconds

class Metrics:
    def __init__(self):
        self.requests = defaultdict(int)                       # (method, route, status) -> count
        self.hist = defaultdict(lambda: [0] * len(BUCKETS))     # route -> count per bucket

    def observe(self, method, route, status, seconds):
        self.requests[(method, route, status)] += 1             # a counter: only ever goes up
        self.hist[route][bisect.bisect_left(BUCKETS, seconds)] += 1

    def exposition(self):
        """The plain-text format Prometheus scrapes from /metrics."""
        out = []
        for (m, r, s), n in sorted(self.requests.items()):
            out.append(f'http_requests_total{{method="{m}",route="{r}",status="{s}"}} {n}')
        for r, counts in self.hist.items():
            running = 0
            for bound, c in zip(BUCKETS, counts):
                running += c                                    # buckets are cumulative: le = "at most"
                le = "+Inf" if bound == float("inf") else bound
                out.append(f'http_request_duration_seconds_bucket{{route="{r}",le="{le}"}} {running}')
        return "\n".join(out)

m = Metrics()
for seconds, status in [(0.03, 200), (0.04, 200), (0.08, 200), (0.3, 200), (0.04, 404), (2.0, 500)]:
    m.observe("GET", "/items/{item_id}", status, seconds)
print(m.exposition())

raw, template = set(), set()
for item_id in range(1000):
    raw.add(("GET", f"/items/{item_id}", 200))
    template.add(("GET", "/items/{item_id}", 200))
print(f"\nseries if labelled by raw path: {len(raw)}   by route template: {len(template)}")
```

- `BUCKETS` lists the bucket upper bounds; the last, infinity, catches everything.
- `observe` adds one to the counter for this combination of labels, and one to the histogram bucket
  the duration falls into. `bisect.bisect_left(BUCKETS, seconds)` finds the first bound that is at
  least `seconds`; 0.08 lands in the `0.1` bucket.
- `exposition` prints each counter, then each bucket *cumulatively*: the line with `le="0.1"` counts
  every request that took **at most** 0.1 s, including the faster ones. `le` stands for "less than or
  equal".

Six requests were observed. The output shows three counter lines (4 successes, 1 not-found, 1 server
error) and six bucket lines reading 3, 4, 4, 5, 5, 6: three requests within 50 ms, four within
100 ms, five within half a second, and all six within infinity (the 2-second one). The problem
*Latency Histogram and Quantile Estimate* goes one step further and estimates a percentile from such
bucket counts, the way Prometheus does.

The last two lines of the demo illustrate the most common metrics mistake. Labelling by the raw path
creates a **separate time series for every distinct value**, here 1,000 of them for 1,000 item ids,
while the route template creates one. The number of distinct label combinations is called
**cardinality**. User IDs, request IDs and raw URLs have unbounded cardinality and will eventually
overwhelm the metrics database. Always label with the route *template*.

The real library does the same with less code:

```python
from prometheus_client import Counter, Histogram, make_asgi_app

REQUESTS = Counter("http_requests_total", "Requests", ["method", "route", "status"])
LATENCY = Histogram("http_request_duration_seconds", "Latency", ["route"],
                    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5))

@app.middleware("http")
async def metrics_middleware(request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    route = request.scope.get("route")
    path = route.path if route else "unmatched"       # the TEMPLATE (/items/{id}), not the raw URL
    REQUESTS.labels(request.method, path, response.status_code).inc()
    LATENCY.labels(path).observe(time.perf_counter() - start)
    return response

app.mount("/metrics", make_asgi_app())                # scraped by Prometheus
```

- `Counter(...)` and `Histogram(...)` declare the metrics, their help text and their label names.
- The middleware (lesson 21) notes the start time, lets the request run with `call_next`, then reads
  the matched route from `request.scope`. `route.path` is the template such as `/items/{item_id}`;
  requests that matched no route are grouped under `"unmatched"`.
- `.labels(...).inc()` adds one to the counter; `.observe(seconds)` records a duration.
- `make_asgi_app()` creates a small ASGI app serving the text format, mounted at `/metrics`.

### Averages hide the pain: percentiles

The **mean** (average) latency is the most natural number to watch and one of the least useful. A
**percentile** answers a better question: the **p95** is the latency that 95% of requests beat, the
**p99** the one that 99% beat. The slow end of the distribution is called the **tail**, and its
latency **tail latency**.

```python-run
import random, statistics

random.seed(7)
# 98% of requests are fast, 2% hit a slow path (cold cache, lock wait, GC pause...)
latencies = [random.gauss(40, 8) for _ in range(980)] + [random.gauss(1800, 300) for _ in range(20)]

def pct(data, p):
    s = sorted(data)
    return s[min(len(s) - 1, int(p / 100 * len(s)))]

print(f"mean  : {statistics.mean(latencies):7.1f} ms   <- looks fine-ish")
print(f"p50   : {pct(latencies, 50):7.1f} ms")
print(f"p95   : {pct(latencies, 95):7.1f} ms")
print(f"p99   : {pct(latencies, 99):7.1f} ms   <- 1 in 100 requests waits this long")

# A page that makes 20 backend calls is slow if ANY of them is slow:
p_slow_page = 1 - 0.98 ** 20
print(f"chance a 20-call page hits the slow path: {p_slow_page:.0%}")
```

- `random.gauss(40, 8)` draws a number from a bell curve centred on 40 with a spread of 8. The code
  makes 980 fast requests around 40 ms and 20 slow ones around 1,800 ms, and fixes the random seed so
  the numbers are the same every run.
- `pct` sorts the values and picks the one at the requested position.

The mean comes out near 75 ms, a figure no real request experienced: fast requests took about 40 ms
and slow ones nearly two seconds. The p50 and p95 are both in the 40s and 50s, and the p99 jumps to
about 1,800 ms. The last line shows why that matters. If loading a page needs 20 backend calls and
each has a 2% chance of being slow, the chance that *at least one* is slow is 1 − 0.98²⁰, about 33%.
A tail that touches one request in fifty touches one *page* in three. This is why services set goals
on p95 or p99, never on the mean.

For ML services add domain metrics: inference latency (separately from total latency), batch sizes,
time spent waiting in queues, tokens per second, the distribution of predictions and confidence
scores, statistics of the input features (to spot **drift**, when live inputs stop resembling the
training data), the model version as a label, and GPU utilisation and memory.

### Traces

A **trace** follows one request through every service it touches. Each unit of work inside it is a
**span**: a name, a start time, a duration, some attributes, and the ID of its **parent span**. The
spans of one request form a tree, usually drawn as a "waterfall". The book describes tracing as
measuring not only the total time of a call but the time of each intermediate step, so the weak link
can be found.

For spans in different services to join one trace, each outgoing call must carry the trace ID and
the caller's span ID. Passing them along is called **context propagation**, and the W3C standard
header for it is `traceparent`. This demo builds spans with a fake clock and prints the waterfall:

```python-run
import contextvars, secrets
from contextlib import contextmanager

clock = 0.0                                   # a fake clock in milliseconds, so timings are stable
def work(ms):
    global clock
    clock += ms

current = contextvars.ContextVar("current_span", default=None)
finished = []

@contextmanager
def span(name):
    parent = current.get()
    s = {"name": name,
         "trace_id": parent["trace_id"] if parent else secrets.token_hex(16),
         "span_id": secrets.token_hex(8),
         "depth": parent["depth"] + 1 if parent else 0,
         "start": clock}
    token = current.set(s)
    try:
        yield s
    finally:
        s["end"] = clock
        current.reset(token)
        finished.append(s)

with span("POST /v1/predict"):
    work(2)
    with span("check API key"):
        work(1)
    with span("redis GET"):
        work(3)
    with span("model.predict"):
        work(5)
        with span("HTTP POST feature-store") as call:
            print("outgoing header  traceparent:", f"00-{call['trace_id']}-{call['span_id']}-01")
            work(40)
        work(25)
    with span("postgres INSERT"):
        work(6)
    work(1)

for s in sorted(finished, key=lambda s: s["start"]):
    bar = " " * int(s["start"] / 2) + "#" * max(1, round((s["end"] - s["start"]) / 2))
    print(f"{'  ' * s['depth'] + s['name']:28} {s['end'] - s['start']:4.0f} ms |{bar}")
```

- `clock` and `work(ms)` replace real time so the durations are exact.
- `current` is a **context variable**: a value that each async task sees separately, which is how
  real tracing libraries know the "current span" even with many requests interleaved on one event
  loop.
- `span(name)` is a context manager (usable with `with`). On entry it creates a span that inherits
  the parent's trace ID (or makes a new one for the first span), gets its own random span ID, and
  becomes the current span. On exit it records the end time and restores the parent.
- The `with` blocks describe one request: a key check, a cache read, a model call that itself calls
  a feature store over HTTP, and a database insert.
- Inside the HTTP call the demo prints the `traceparent` header that would be sent: version `00`, the
  32-hex-digit trace ID, the 16-hex-digit span ID, and flags `01` meaning "sampled".

The waterfall shows the whole request took 83 ms, and that `model.predict` took 70 of them, 40 of
which were spent waiting for the feature store. Nothing else matters much. Metrics could have told you
"the predict endpoint is slow"; the trace tells you *which hop* is slow, in seconds. The IDs differ on
every run because they are random.

**OpenTelemetry** is the vendor-neutral standard for traces (and increasingly metrics and logs), and
its automatic instrumentation gets you far with three lines:

```python
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

FastAPIInstrumentor.instrument_app(app)              # a span per request
HTTPXClientInstrumentor().instrument()               # spans + context propagation on outbound calls
SQLAlchemyInstrumentor().instrument(engine=engine)   # a span per query
```

Each line patches one library to create spans automatically: one per incoming request, one per
outgoing HTTP call (adding the `traceparent` header for you), one per database query. Add your own
spans around the interesting parts with `with tracer.start_as_current_span("model.predict"):`. The
spans are sent to a tracing backend such as Jaeger or Tempo, which draws the waterfall.

### SLOs and alerting

A **service-level indicator** (SLI) is a measurement of what users experience, such as "fraction of
requests that succeed" or "p95 latency". A **service-level objective** (SLO) is a target for it:
"99.9% of requests succeed over 30 days", "p95 latency under 300 ms". The gap between the target and
perfection is the **error budget**: 99.9% over 30 days allows 0.1% of failures, which is about 43
minutes of complete outage (30 × 24 × 60 × 0.001 = 43.2). The **burn rate** is how fast you are
spending that budget.

Alert on *symptoms* that users feel (error rate, latency, a fast burn rate), not on every possible
cause: CPU at 80% is not a problem in itself if users are served well. Every alert must be
actionable; an alert that fires often and needs no action teaches people to ignore alerts.

## Resilience: surviving your dependencies

Your service depends on others: the database, a payment provider, a model server. Every network call
can be slow, fail, or hang forever. A **transient** failure is one that would likely succeed if
tried again a moment later, such as a dropped connection or a `503`. The patterns below stop a
dependency's problem from becoming yours.

**Timeouts, always.** A call with no time limit is an outage waiting to happen: when the dependency
hangs, requests pile up, each holding a connection and memory, until your service suffocates too.

```python
client = httpx.AsyncClient(timeout=httpx.Timeout(connect=2.0, read=10.0, write=5.0, pool=2.0))
```

The four numbers limit, in seconds, establishing the connection (`connect`), waiting for response
data (`read`), sending the request (`write`) and waiting for a free connection from the client's own
pool (`pool`).

**Retries, carefully.** Retry only transient failures (connection errors, `502`, `503`, `504`,
`429`) and only **idempotent** operations, those that are safe to repeat (lesson 2), or requests that
carry an idempotency key. Wait longer after each failure, which is **exponential backoff**: 0.5 s,
1 s, 2 s, 4 s. Add **jitter**, a random element in each wait, cap the wait, honour the server's
`Retry-After` header, and bound the total number of attempts. Naive retries multiply the load on a
service that is already struggling, a vicious circle called a **retry storm**.

```python-run
import random

def backoff_schedule(base=0.5, factor=2, max_delay=30, retries=6, jitter=True, seed=1):
    rng = random.Random(seed)
    out = []
    for attempt in range(retries):
        delay = min(max_delay, base * factor ** attempt)
        out.append(round(rng.uniform(0, delay), 2) if jitter else delay)   # "full jitter"
    return out

print("no jitter :", backoff_schedule(jitter=False))
print("jitter    :", backoff_schedule())
print("why jitter: without it, 10,000 clients that failed together all retry at exactly 0.5s, 1s, 2s...")
```

`backoff_schedule` computes the wait before each retry: `base * factor ** attempt` doubles each time
(0.5, 1, 2, 4, 8, 16) and `min(max_delay, ...)` caps it. With jitter on, each wait is instead a random
number between zero and that value (`rng.uniform(0, delay)`), a strategy called *full jitter*. The
first line prints the neat doubling sequence; the second prints six smaller, irregular numbers that
grow in the same general way. Imagine a database restart that makes 10,000 clients fail at the same
instant: without jitter they all return at exactly 0.5 s and knock it over again; with jitter their
retries are spread out. The problem *Retry with Exponential Backoff* builds the decision logic
(which statuses to retry, when to stop, how to honour `Retry-After`).

**Circuit breaker.** After repeated failures, stop calling the dependency for a while and fail
immediately (or serve a fallback), which saves your threads and gives the dependency room to recover.
Now and then, let one trial call through to see whether it has recovered. The breaker has three
states: **closed** (normal, calls pass through), **open** (calls are refused at once) and
**half-open** (one trial call is allowed).

```python-run
class CircuitBreaker:
    def __init__(self, threshold=3, reset_after=10):
        self.threshold, self.reset_after = threshold, reset_after
        self.failures, self.opened_at, self.state = 0, None, "closed"

    def call(self, fn, now):
        if self.state == "open":
            if now - self.opened_at < self.reset_after:
                return "fail fast (circuit open)"
            self.state = "half-open"                    # allow one trial call
        try:
            result = fn()
        except Exception:
            self.failures += 1
            if self.state == "half-open" or self.failures >= self.threshold:
                self.state, self.opened_at = "open", now
            return f"error (failures={self.failures}, state={self.state})"
        self.failures, self.state = 0, "closed"
        return result

healthy = False
def upstream():
    if not healthy: raise TimeoutError
    return "200 OK"

cb = CircuitBreaker()
for t in range(0, 8):
    print(f"t={t:>2}", cb.call(upstream, t))
healthy = True
for t in (12, 13, 14):
    print(f"t={t:>2}", cb.call(upstream, t))
```

- The breaker counts consecutive `failures`. After `threshold` (3) failures it moves to `open` and
  remembers when (`opened_at`).
- While open, `call` returns "fail fast" without calling the dependency at all, until `reset_after`
  (10) time units have passed.
- After that it becomes `half-open` and lets one call through. A failure reopens the circuit at once;
  a success resets the count and closes it.
- The time `now` is passed in as an argument rather than read from a clock, which makes the behaviour
  easy to test. This is called **injecting the clock**.

Reading the output: at t = 0, 1 and 2 the upstream fails and the breaker counts 1, 2, 3 failures; at
the third it opens. From t = 3 to 7 every call fails fast without touching the upstream. Then the
upstream recovers. At t = 12, ten units after opening, the breaker goes half-open, the trial call
succeeds, and `200 OK` is returned; t = 13 and 14 pass normally. The problem *Circuit Breaker with an
Injected Clock* asks you to build a breaker with exact boundary rules and a `state` query.

**Also worth knowing**: **bulkheads** (separate pools or semaphores per dependency, so one slow
dependency cannot use up every connection; named after the watertight walls in a ship), **load
shedding** (answering `503` or `429` quickly when saturated instead of queueing work you cannot
finish), **graceful degradation** (serving a cached or simpler answer instead of an error), and
**deadline propagation** (passing the remaining time budget to downstream calls, so nobody keeps
working on a request the client has already given up on).

## Troubleshooting checklist

The book's troubleshooting advice is to start from where and when the problem shows up and work
downward, and to look first at the status code: a `422` usually means Pydantic rejected the input, a
`401` or `403` points at credentials, and a `500` often means something behind your service failed.
It also recommends reproducing a failing request with the same input, and putting real details
(the input values and the specific error) into the exceptions you raise. At production scale, when
latency or errors jump:

1. Which endpoint, which status codes, since when? (metrics) Was there a deploy shortly before?
2. Is it every replica or one? Every user or one tenant?
3. Where is the time going? (traces: your code, the database, another service, queue waiting)
4. Saturation: CPU, memory (are processes being killed for running out of memory?), database pool
   exhausted, thread pool full, event loop blocked?
5. Find example failing requests by request ID (logs) and read the traceback.
6. Mitigate first (roll back, add replicas, shed load), find the root cause second.

> [!INTERVIEW]
> "What's the difference between liveness and readiness probes, and what should each check?" — Liveness
> asks "should this process be restarted?" and must be a cheap in-process check with no dependencies,
> otherwise a database outage restarts every replica. Readiness asks "should this replica receive
> traffic?" and may verify that initialisation finished (model loaded, pools up) and critical dependencies
> respond; failing it only removes the replica from load balancing. During startup and graceful shutdown
> readiness is false while liveness stays true.

## Pitfalls

- Liveness probes that query the database.
- Metrics labelled with raw URLs or user IDs (a cardinality explosion).
- Alerting on averages; no percentiles.
- HTTP clients without timeouts; unbounded retries without backoff and jitter; retrying
  non-idempotent `POST` requests.
- Logs written to files inside containers; logs without request or trace IDs.
- Observability added only after the first incident.

## Summary

- Liveness (restart?) versus readiness (send traffic?) versus startup; keep liveness free of
  dependencies.
- Logs are events, metrics are numbers over time (RED: rate, errors, duration; percentiles, not
  averages; low-cardinality labels), traces are per-request timing across services (OpenTelemetry,
  `traceparent`).
- Set SLOs on what users feel and alert on symptoms.
- Resilience: timeouts everywhere, bounded retries with exponential backoff and jitter for
  idempotent calls, circuit breakers, bulkheads, load shedding.

## Glossary

- **Observability** — understanding a system's internal state from the signals it emits.
- **Probe (liveness / readiness / startup)** — a periodic health request deciding restart / routing /
  when to begin the other checks.
- **Thundering herd** — many clients or processes acting at the same instant and overloading a
  resource.
- **Log / structured log** — a recorded event / one written as JSON with named fields.
- **stdout** — a process's standard output stream, collected by the platform.
- **Metric / time series** — a number measured repeatedly / the stream of its values over time.
- **Scraping** — Prometheus fetching `/metrics` from each replica on a schedule.
- **Counter / gauge / histogram** — a value that only rises / one that rises and falls / counts of
  observations in size buckets.
- **Label / cardinality** — a key-value tag on a series / the number of distinct label combinations.
- **RED / USE / golden signals** — checklists of what to measure for requests / resources / both.
- **Percentile (p50, p95, p99) / tail latency** — the value a given share of requests beat / the
  latency of the slowest requests.
- **Trace / span / parent span** — one request's journey / one timed step in it / the step that
  contains it.
- **Context propagation / `traceparent`** — passing trace IDs along with calls / the standard header
  for it.
- **OpenTelemetry** — the vendor-neutral standard and libraries for traces, metrics and logs.
- **SLI / SLO / error budget / burn rate** — a user-facing measurement / its target / the failures the
  target allows / how fast they are being used.
- **Transient failure** — one that would likely succeed if retried shortly.
- **Exponential backoff / jitter / retry storm** — waits that double / randomness in the waits /
  retries overloading a struggling service.
- **Circuit breaker (closed / open / half-open)** — a guard that stops calls to a failing dependency
  and later tests it.
- **Bulkhead / load shedding / graceful degradation / deadline propagation** — isolated pools per
  dependency / refusing work when saturated / a reduced answer instead of an error / passing the
  remaining time budget on.
- **Injected clock** — passing the current time in as an argument so time-based logic is testable.

```quiz
[
  {"q": "Your liveness probe runs 'SELECT 1' against the database. The DB has a 30-second blip. What happens?", "options": ["Nothing", "The orchestrator restarts all replicas, turning a blip into an outage", "Traffic is drained gracefully", "Only one replica restarts"], "answer": 1,
   "explain": "Liveness failures trigger restarts. Dependency checks belong in readiness, which only removes replicas from rotation."},
  {"q": "Which label would cause a metrics cardinality explosion?", "options": ["HTTP method", "Status code", "Route template like /items/{id}", "The raw request path including IDs"], "answer": 3,
   "explain": "Every distinct label value is a separate time series; raw paths and user IDs are unbounded."},
  {"q": "Why monitor p99 latency rather than the mean?", "options": ["p99 is easier to compute", "Means hide tail latency; fan-out makes many user requests hit the slow tail", "The mean is always higher", "Prometheus can't compute means"], "answer": 1,
   "explain": "A small fraction of very slow requests barely moves the mean yet dominates user experience when a page needs many calls."},
  {"q": "What does jitter add to exponential backoff?", "options": ["Longer waits", "Randomisation so many clients don't retry in synchronised waves", "Encryption", "Idempotency"], "answer": 1,
   "explain": "Without jitter, clients that failed together retry together, re-overloading the recovering service."},
  {"q": "What does a circuit breaker do in the 'open' state?", "options": ["Retries forever", "Fails fast without calling the dependency until a reset timeout, then probes with a trial call", "Doubles the timeout", "Restarts the service"], "answer": 1,
   "explain": "Failing fast protects both the caller's resources and the struggling dependency; half-open tests recovery."},
  {"q": "Which header propagates trace context between services under the W3C standard?", "options": ["X-Request-ID", "traceparent", "Authorization", "ETag"], "answer": 1,
   "explain": "traceparent carries the trace id and parent span id so spans from different services join one trace."},
  {"q": "Which request is unsafe to retry automatically after a timeout?", "options": ["GET /items/1", "PUT /items/1 with a full body", "POST /payments without an idempotency key", "DELETE /items/1"], "answer": 2,
   "explain": "POST isn't idempotent: the first attempt may have succeeded. An idempotency key makes it safe."},
  {"q": "A histogram bucket line reads le=\"0.1\" with value 4. What does that mean?", "options": ["4 requests took exactly 0.1 s", "4 requests took at most 0.1 s, including the faster ones", "4 requests took more than 0.1 s", "The average was 0.1 s over 4 requests"], "answer": 1,
   "explain": "Prometheus histogram buckets are cumulative: le means 'less than or equal to'."}
]
```

> **Source:** Lubanovic, *FastAPI*, ch. 9 "Service Layer" (Logging; Metrics, Monitoring, Observability; Tracing) and ch. 13 "Production" (Troubleshooting: Kinds of Problems, Logging, Metrics); https://fastapi.tiangolo.com/deployment/concepts/; Kubernetes docs "Liveness, Readiness and Startup Probes"; OpenTelemetry Python docs; W3C Trace Context; Google SRE Book, "Monitoring Distributed Systems"
