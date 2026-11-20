# Health checks, logging and observability

Once the service is deployed, two questions dominate its life: *is it healthy right now?* and *why did
that request fail/slow down?* Lubanovic touches these under "Other Service-Level Stuff" (logging;
metrics, monitoring, observability; tracing) and "Troubleshooting" in the production chapter. This lesson
turns them into concrete FastAPI practice: health endpoints, the three pillars of observability, and the
resilience patterns — timeouts, retries, circuit breakers — that keep one failing dependency from taking
everything down.

## Health checks

Orchestrators and load balancers poll HTTP endpoints to decide what to do with each replica. Kubernetes
distinguishes three probes, and the distinction is worth adopting anywhere:

| Probe | Question | On failure |
|---|---|---|
| **Liveness** | Is the process alive and not deadlocked? | **restart** the container |
| **Readiness** | Can it serve traffic *now*? | **remove from load balancing** (no restart) |
| **Startup** | Has slow initialisation finished? | hold off liveness checks |

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

The rules that prevent self-inflicted outages:

- **Liveness must not check dependencies.** If the database blips and liveness fails, the orchestrator
  restarts *every* replica — turning a brief DB hiccup into a full outage and a thundering herd of
  reconnects. Liveness answers only "is this process responsive?".
- **Readiness may check critical dependencies** — with short timeouts — and should fail during startup
  (model still loading) and during graceful shutdown (so the balancer drains you).
- Keep them fast and unauthenticated, but expose little: a boolean per check, not versions and stack
  details.
- A blocked event loop makes the liveness endpoint time out — which is actually a useful signal.

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

## The three pillars

| Pillar | Answers | Shape | Tools |
|---|---|---|---|
| **Logs** | what exactly happened in this request? | discrete events, high detail | stdout → Loki/ELK/CloudWatch |
| **Metrics** | how is the system behaving overall? trends, alerts | numeric time series, cheap | Prometheus + Grafana, Datadog |
| **Traces** | where did the time go across services? | tree of timed spans per request | OpenTelemetry → Jaeger/Tempo |

### Logs

Covered in the errors/middleware lesson: structured JSON, one event per line, to **stdout** (the platform
collects it — don't manage log files in containers), with a **request ID** on every line, and no secrets
or personal data. Add the trace ID too so you can jump from a log line to its trace. Configure Uvicorn's
loggers (`uvicorn.error`, `uvicorn.access`) to use the same format, or replace the access log with your
own middleware log line carrying method, path template, status, duration and user/tenant.

### Metrics

Start with the **RED** method for request-driven services — **R**ate, **E**rrors, **D**uration — per
endpoint; for resources use **USE** (utilisation, saturation, errors). The four "golden signals" (latency,
traffic, errors, saturation) say the same thing.

Metric types (Prometheus vocabulary):

- **Counter** — only goes up: `http_requests_total{method,route,status}`.
- **Gauge** — goes up and down: in-flight requests, queue depth, DB pool in use.
- **Histogram** — bucketed observations: request duration → percentiles.

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

Two classic mistakes: **high-cardinality labels** (raw paths with IDs, user IDs, request IDs — each
distinct value creates a new time series and will sink your metrics store), and **averages**. Average
latency hides the experience of your unluckiest users; watch percentiles:

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

That last line is why tail latency matters: fan-out multiplies the odds of hitting the tail.

For ML services add domain metrics: inference latency (separately from total latency), batch sizes, queue
wait, tokens per second, prediction/confidence distributions, input feature statistics (for drift), model
version as a label, GPU utilisation and memory.

### Traces

A **trace** follows one request through every service; each unit of work is a **span** with start time,
duration, attributes and a parent. **OpenTelemetry** is the vendor-neutral standard, and auto-
instrumentation gets you far:

```python
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

FastAPIInstrumentor.instrument_app(app)              # a span per request
HTTPXClientInstrumentor().instrument()               # spans + context propagation on outbound calls
SQLAlchemyInstrumentor().instrument(engine=engine)   # a span per query
```

Context travels between services in the W3C `traceparent` header, so the gateway, your API, the feature
store and the model server all appear in one waterfall. Add manual spans around the interesting parts
(`with tracer.start_as_current_span("model.predict"):`). Traces answer "which hop is slow?" in seconds —
the question metrics can only hint at.

### SLOs and alerting

Define **service-level objectives** on user-visible behaviour — "99.9% of requests succeed", "p95 latency
under 300 ms" — and alert on *symptoms* (error rate, latency, burn rate of the error budget), not on
every cause (CPU at 80% isn't a problem by itself). Alerts must be actionable; noisy alerts get ignored.

## Resilience: surviving your dependencies

Every network call can be slow, fail, or hang. The book's troubleshooting advice starts from asking what
kind of problem you have; the following patterns stop a dependency's problem from becoming yours.

**Timeouts — always.** A missing timeout is an outage waiting to happen: requests pile up holding
connections until the service suffocates.

```python
client = httpx.AsyncClient(timeout=httpx.Timeout(connect=2.0, read=10.0, write=5.0, pool=2.0))
```

**Retries — carefully.** Only for transient failures (connection errors, 502/503/504, 429) and only for
idempotent operations (or with an idempotency key). Use **exponential backoff with jitter** and a cap,
honour `Retry-After`, and bound total attempts — naive retries multiply load on a struggling service
(a *retry storm*).

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

The problem *Retry with Exponential Backoff* builds the decision logic (which statuses, when to stop,
`Retry-After`).

**Circuit breaker.** After repeated failures, stop calling the dependency for a while and fail fast (or
serve a fallback); periodically let one probe through to see whether it recovered:

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

**Also**: bulkheads (separate pools/semaphores per dependency so one can't exhaust everything), load
shedding (fast 503/429 when saturated), graceful degradation (serve cached or default results), and
**deadline propagation** (pass the remaining time budget downstream so nobody works on a request the
client already gave up on).

## Troubleshooting checklist

When latency or errors spike:

1. Which endpoint, which status codes, since when? (metrics) Was there a deploy? (correlate)
2. Is it all replicas or one? All users or one tenant?
3. Where is the time spent? (traces: app, DB, upstream, queue wait)
4. Saturation: CPU, memory (OOM kills?), DB pool exhausted, thread pool full, event loop blocked?
5. Find example failing requests by request ID (logs) and read the traceback.
6. Mitigate first (roll back, scale out, shed load), root-cause second.

> [!INTERVIEW]
> "What's the difference between liveness and readiness probes, and what should each check?" — Liveness
> asks "should this process be restarted?" and must be a cheap in-process check with no dependencies,
> otherwise a database outage restarts every replica. Readiness asks "should this replica receive
> traffic?" and may verify that initialisation finished (model loaded, pools up) and critical dependencies
> respond; failing it just removes the replica from load balancing. During startup and graceful shutdown
> readiness is false while liveness stays true.

## Pitfalls

- Liveness probes that query the database.
- Metrics labelled with raw URLs/user IDs (cardinality explosion).
- Alerting on averages; no percentiles.
- HTTP clients without timeouts; unbounded retries without backoff/jitter; retrying non-idempotent
  POSTs.
- Logs to local files inside containers; logs without correlation IDs.
- Observability added only after the first incident.

## Summary

- Liveness (restart?) vs readiness (route traffic?) vs startup — keep liveness dependency-free.
- Logs = events, metrics = aggregates (RED: rate, errors, duration; percentiles not averages), traces =
  per-request timing across services (OpenTelemetry, `traceparent`).
- Resilience: timeouts everywhere, bounded retries with exponential backoff + jitter for idempotent calls,
  circuit breakers, bulkheads, load shedding.

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
   "explain": "POST isn't idempotent: the first attempt may have succeeded. An idempotency key makes it safe."}
]
```

> **Source:** Lubanovic, *FastAPI*, ch. 9 "Service Layer" (Logging; Metrics, Monitoring, Observability; Tracing) and ch. 13 "Production" (Troubleshooting: Kinds of Problems, Logging, Metrics); https://fastapi.tiangolo.com/deployment/concepts/; Kubernetes docs "Liveness, Readiness and Startup Probes"; OpenTelemetry Python docs; Google SRE Book, "Monitoring Distributed Systems"
