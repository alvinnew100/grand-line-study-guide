# REST and gRPC serving with FastAPI

> **Before this lesson:** read [Serving patterns: batch, online and streaming](#/lesson/mlops/serving-patterns)
> for what an online model service is and why latency matters, and
> [Python packaging, Makefiles and pre-commit](#/lesson/mlops/packaging-tooling) for the
> `src/churn/` project layout used in the examples. You should be able to read a Python class and a
> function with type hints.

## In plain words

An online model service is a program that waits for questions over the network and answers them.
The rules for how those questions and answers are shaped form an **API** (application programming
interface): which address to call, which fields to send, what comes back, and what an error looks
like. This lesson builds such a service in Python with **FastAPI**, the most popular framework for
the job, and then looks at **gRPC**, a faster alternative used between internal services.

An everyday picture: the service is a restaurant counter with a printed order form. The form lists
exactly which boxes must be filled and what is allowed in each ("size: small, medium or large").
A clerk checks every form before it reaches the kitchen and hands back an unreadable one with a
note saying which box is wrong. The kitchen (the model) only ever sees clean orders. FastAPI is the
clerk and the form; the model is the kitchen.

Why this matters for a job: nearly every ML engineer ends up writing or reviewing a prediction
endpoint, and interviewers love to ask why an `async def` endpoint became slow, how health checks
differ, and how a service should behave when it is overloaded. Those are the questions this lesson
answers.

## Words you need first

- **HTTP** is the protocol of the web. A request names a **method** (`GET` to fetch, `POST` to send
  data), a **path** such as `/predict`, optional **headers** (labelled metadata such as
  `x-request-id`) and a **body**. The response carries a **status code**: 200 means success, 4xx
  means the caller did something wrong, 5xx means the server failed.
- **REST** is the most common style for HTTP APIs: resources at paths, standard methods, and bodies
  written in **JSON** (JavaScript Object Notation, text such as `{"plan": "pro", "tenure": 12}`).
- An **endpoint** is one method plus path that the service answers, such as `POST /predict`.
- A **schema** is a precise description of the shape of data: field names, types and allowed values.
  **Validation** means checking incoming data against the schema before using it.

## Why FastAPI is the default for Python model APIs

FastAPI brings three things that matter for model serving:

1. **Validation driven by type hints.** You describe the request as a Python class using
   **pydantic**, a library that turns type hints into checks. A bad request is rejected with status
   **422 Unprocessable Entity** and a message naming the bad field, before the model sees it.
2. **Automatic documentation.** From the same classes FastAPI generates an **OpenAPI** description
   (a standard, machine-readable API description) and serves an interactive page at `/docs`.
3. **Asynchronous performance.** FastAPI is an **ASGI** application (Asynchronous Server Gateway
   Interface, the standard way async Python web apps talk to servers), built on the Starlette
   toolkit and usually run by the Uvicorn server. Lubanovic's *FastAPI* book describes the framework
   as resting on two pillars: Starlette for the web side and pydantic for the data side.

## A production-shaped prediction service

We build it in two files. The first declares the shapes of requests and responses.

```python
# src/churn/serve/schemas.py
from typing import Literal
from pydantic import BaseModel, Field, ConfigDict

class CustomerFeatures(BaseModel):
    model_config = ConfigDict(extra="forbid")            # unknown fields -> 422 (catches client typos)
    tenure_months: int = Field(ge=0, le=600)
    monthly_charges: float = Field(gt=0, lt=10_000)
    plan: Literal["basic", "pro", "premium"]
    support_tickets_30d: int = Field(0, ge=0)

class PredictRequest(BaseModel):
    instances: list[CustomerFeatures] = Field(min_length=1, max_length=256)

class Prediction(BaseModel):
    churn_probability: float
    label: bool

class PredictResponse(BaseModel):
    model_version: str
    predictions: list[Prediction]
```

Line by line:

- `class CustomerFeatures(BaseModel)` declares one customer's inputs. Inheriting from pydantic's
  `BaseModel` is what turns the type hints into checks.
- `extra="forbid"` rejects any field that is not declared. If a client sends `tenure_month`
  (missing the `s`), the request fails loudly instead of the real field silently taking a default.
- `tenure_months: int = Field(ge=0, le=600)` must be a whole number between 0 and 600 (`ge` means
  greater than or equal, `le` less than or equal).
- `monthly_charges: float = Field(gt=0, lt=10_000)` must be strictly between 0 and 10,000.
- `plan: Literal["basic", "pro", "premium"]` allows only those three strings. A list of allowed
  values like this is often called an **enum**.
- `support_tickets_30d: int = Field(0, ge=0)` is optional: the first argument, `0`, is the default.
- `PredictRequest` wraps a list of customers called `instances`, at least 1 and at most 256 of them.
  Accepting a list lets one call score many customers.
- `Prediction` and `PredictResponse` describe what comes back, including the model version.

If a client sends `{"instances": [{"tenure_months": -3, "monthly_charges": 50, "plan": "gold"}]}`,
FastAPI answers 422 with two errors: `tenure_months` must be at least 0, and `plan` must be one of
the three allowed values. The model code never runs.

The second file is the service itself.

```python
# src/churn/serve/app.py
import logging, time, uuid
from contextlib import asynccontextmanager

import mlflow
import pandas as pd
from fastapi import FastAPI, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from prometheus_client import Counter, Histogram, make_asgi_app

from .schemas import PredictRequest, PredictResponse, Prediction
from .settings import settings

log = logging.getLogger("churn")
REQS = Counter("predict_requests_total", "Prediction requests", ["status", "model_version"])
LAT = Histogram("predict_latency_seconds", "Prediction latency",
                buckets=[.005, .01, .025, .05, .1, .25, .5, 1, 2.5])
state: dict = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- startup: load once, warm up ---
    model = mlflow.pyfunc.load_model(settings.model_uri)
    state["model"] = model
    state["version"] = model.metadata.run_id[:8]
    model.predict(pd.DataFrame([{"tenure_months": 1, "monthly_charges": 10.0, "plan": "basic",
                                 "support_tickets_30d": 0}]))
    state["ready"] = True
    yield
    # --- shutdown ---
    state.clear()

app = FastAPI(title="Churn API", version="1.4.0", lifespan=lifespan)
app.mount("/metrics", make_asgi_app())                   # Prometheus scrape endpoint

@app.middleware("http")
async def request_id(request: Request, call_next):
    rid = request.headers.get("x-request-id", str(uuid.uuid4()))
    response = await call_next(request)
    response.headers["x-request-id"] = rid
    return response

@app.get("/healthz")            # liveness: is the process alive?
def healthz():
    return {"status": "ok"}

@app.get("/readyz")             # readiness: can it serve traffic?
def readyz():
    if not state.get("ready"):
        raise HTTPException(503, "model not loaded")
    return {"status": "ready", "model_version": state["version"]}

@app.post("/predict", response_model=PredictResponse)
async def predict(req: PredictRequest):
    t0 = time.perf_counter()
    df = pd.DataFrame([i.model_dump() for i in req.instances])
    try:
        # the model is CPU-bound and blocking: run it off the event loop
        proba = await run_in_threadpool(state["model"].predict, df)
    except Exception:
        REQS.labels("error", state["version"]).inc()
        log.exception("inference failed")
        raise HTTPException(500, "inference failed")
    LAT.observe(time.perf_counter() - t0)
    REQS.labels("ok", state["version"]).inc()
    return PredictResponse(
        model_version=state["version"],
        predictions=[Prediction(churn_probability=float(p), label=bool(p >= settings.threshold)) for p in proba],
    )
```

Walking through it from top to bottom:

- `REQS` and `LAT` are **metrics** from the Prometheus client library (lesson 27). A **counter**
  only goes up (here: number of requests, split by status and model version). A **histogram**
  counts observations into **buckets**, ranges such as "under 5 ms" and "under 10 ms", from which
  percentiles can be estimated later.
- `lifespan` runs once when the server starts (the part before `yield`) and once when it stops (the
  part after). It loads the model from the registry, keeps it in the `state` dictionary, and makes
  one throw-away prediction to **warm up** the model so the first real user does not pay one-off
  setup costs. Only then does it set `ready`.
- `app.mount("/metrics", ...)` adds the page that Prometheus reads, or **scrapes**, every few
  seconds.
- A **middleware** is a function that runs around every request. This one reads the caller's
  `x-request-id` header, or invents a **UUID** (a random, practically unique identifier), and copies
  it into the response so a request can be followed through logs.
- `/healthz` answers "is the process alive?"; `/readyz` answers "can it serve traffic right now?",
  returning **503 Service Unavailable** while the model is still loading.
- `/predict` turns the validated instances into a pandas DataFrame, runs the model, records the
  latency and the outcome, and builds the response. `model_dump()` converts a pydantic object back
  into a plain dictionary.

Things to notice:

1. **Load the model once** in the `lifespan` handler, not per request; warm it up.
2. **Separate liveness and readiness** endpoints. Kubernetes uses them for different decisions:
   restart the container versus stop sending it traffic (lesson 22).
3. **Validation at the boundary**: ranges, enums, `extra="forbid"`, a cap on batch size. The model
   never sees garbage; the client gets a precise 422 error.
4. **Batch endpoint** (`instances: [...]`): one **vectorised** call that predicts many rows at once
   is far cheaper than N separate calls.
5. **The response includes the model version**, which you need for debugging and later for joining
   predictions with the true outcomes.
6. **Metrics** are exposed at `/metrics` for Prometheus (module 10).

### `async def` vs `def`: the trap

To understand this trap you need three ideas.

- An **event loop** is a single thread that juggles many requests by switching between them
  whenever one is *waiting* (for a database, a network call, a file). A function written with
  `async def` is a **coroutine**: it can pause at each `await` and let the loop serve someone else.
- Work that mostly waits is **I/O-bound** (I/O means input/output). Work that keeps the processor
  busy calculating is **CPU-bound** (or GPU-bound). Model inference is CPU- or GPU-bound: it never
  pauses at an `await`, so it never hands control back to the loop.
- A **threadpool** is a small set of extra threads that can run blocking functions while the event
  loop carries on.

Lubanovic (ch. 4 and 13) stresses that async pays off when a server spends its time *waiting*. The
consequences for model serving:

- Calling a blocking `model.predict` directly inside `async def` **blocks the event loop**: every
  other request, including health checks, stalls until it finishes.
- A plain `def` endpoint is run by FastAPI in its threadpool, so the loop stays responsive.
- You can also keep `async def` and offload the call with `run_in_threadpool` or
  `asyncio.to_thread`, as the service above does.
- Python has a **GIL** (global interpreter lock) that lets only one thread run Python code at a
  time. NumPy, scikit-learn, PyTorch and ONNX Runtime release it inside their compiled code, so
  threads do give real parallel inference, up to the number of CPU cores.
- Use `async` clients (`httpx.AsyncClient`, async Redis) for I/O such as feature-store lookups.

The demo below simulates what happens when 20 requests, each needing 50 ms of computation, arrive
at the same moment together with one health check. It is a timing model rather than a real server,
because the browser that runs these demos has no threads.

```python-run
# Simulate 20 requests arriving together, each needing 50 ms of CPU, plus one health check.
REQUESTS, WORK_MS, CORES = 20, 50, 4

def blocking_in_event_loop():
    # the loop runs one handler at a time and cannot switch while predict() computes
    finish = [WORK_MS * (i + 1) for i in range(REQUESTS)]
    health_check = finish[-1]          # the health check waits behind all 20 predictions
    return finish, health_check

def offloaded_to_threadpool():
    # the loop hands each predict() to a worker thread and stays free; compiled code
    # releases the GIL, so up to CORES predictions run at the same time
    finish = [WORK_MS * (i // CORES + 1) for i in range(REQUESTS)]
    health_check = 1                   # answered by the free loop almost at once
    return finish, health_check

for name, fn in [("blocking inside async def", blocking_in_event_loop),
                 ("offloaded to threadpool", offloaded_to_threadpool)]:
    finish, hc = fn()
    print(f"{name:26s} last done {max(finish):5d} ms, mean {sum(finish) / len(finish):6.1f} ms, "
          f"health check at {hc:4d} ms")
```

In the blocking version, request `i` finishes at `50 * (i + 1)` ms because each must wait for every
earlier one. In the offloaded version, four run at a time, so request `i` finishes in round
`i // 4 + 1` (`//` is whole-number division). The output:

```text
blocking inside async def  last done  1000 ms, mean  525.0 ms, health check at 1000 ms
offloaded to threadpool    last done   250 ms, mean  150.0 ms, health check at    1 ms
```

The health-check column is the dangerous one. A real orchestrator that waits a second for
`/healthz` and gets no answer concludes that the container is dead and restarts it, in the middle
of a traffic spike. Run on a real machine with real threads, the same experiment with
`time.sleep` standing in for inference takes about 1,000 ms when blocking and about 100 ms when
offloaded.

### Running it: workers and processes

```bash
uvicorn churn.serve.app:app --host 0.0.0.0 --port 8000 --workers 4
# or Gunicorn supervising Uvicorn workers (process management, graceful restarts):
gunicorn churn.serve.app:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

`churn.serve.app:app` means "the object called `app` in the module `churn.serve.app`". `--host
0.0.0.0` accepts connections from other machines, not only from the same one, and `--port 8000`
picks the port. `--workers 4` starts four separate **processes** (independent running programs,
each with its own memory). **Gunicorn** is an older, battle-tested process manager that restarts a
crashed worker and restarts workers gracefully during a release.

Each worker is a separate process with **its own copy of the model in memory**: four workers times a
3 GB model is 12 GB. On Kubernetes the usual pattern is **one worker per container**, scaling by
adding containers (the orchestrator then acts as process manager). For GPU models it is one process
per GPU plus a batching layer (lesson 21). As Lubanovic notes, something in front of the servers
must also keep them running, forward requests to them and handle HTTPS. That is the job of a
**reverse proxy** or **load balancer** (a component that spreads incoming requests over several
servers); on Kubernetes an **ingress** plays this role.

## Reliability patterns

A service that calls other services will meet slow and failing dependencies. Six habits keep that
from turning into an outage.

- **Timeouts everywhere**: on the client, on the server, and on every call to another service. A
  request without a timeout can hold memory and a connection forever.
- **Retries with exponential backoff and jitter**: wait 0.1 s, then 0.2 s, then 0.4 s and so on
  before each retry (**exponential backoff**), with a random amount taken off each wait
  (**jitter**). Retry only operations that are safe to repeat, and only errors that are likely
  temporary: connection reset, **429 Too Many Requests**, 503. You will build the schedule in the
  problem `mlops-backoff-schedule`.
- **Load shedding**: when the server is already full, answer 429 or 503 at once instead of accepting
  work it cannot finish in time.
- **Circuit breakers**: after repeated failures from a dependency, stop calling it for a while and
  serve a fallback; then try again carefully. (A problem in this module builds one.)
- **Graceful shutdown**: when the platform asks the process to stop (it sends a signal called
  **SIGTERM**), stop accepting new requests and finish the ones in progress.
- **Idempotency keys** for requests that change something: the client attaches a unique key, and
  the server ignores a second request with the same key, so a retry never applies a change twice.

```python-run
import random
random.seed(0)
def backoff(base=0.1, factor=2, cap=5.0, attempts=6):
    for i in range(attempts):
        raw = min(cap, base * factor ** i)
        yield raw, random.uniform(0, raw)                 # (no jitter, full jitter)
print("attempt  plain   full-jitter")
for i, (plain, jit) in enumerate(backoff()):
    print(f"{i:7d}  {plain:5.2f}s  {jit:5.2f}s")
print("Jitter spreads retries so thousands of clients do not hammer the server in sync.")
```

`backoff` is a **generator**: each `yield` hands back one value and pauses until the loop asks for
the next. For attempt `i` the plain wait is `base * factor ** i` (0.1, 0.2, 0.4, ...), capped at 5
seconds. **Full jitter** picks a random wait between zero and that plain value. The output:

```text
attempt  plain   full-jitter
      0   0.10s   0.08s
      1   0.20s   0.15s
      2   0.40s   0.17s
      3   0.80s   0.21s
      4   1.60s   0.82s
      5   3.20s   1.30s
```

Why bother with randomness? Imagine 10,000 clients whose calls failed at the same instant during a
brief outage. With plain backoff they all retry at exactly 0.1 s, then all at 0.3 s, and each
synchronised wave knocks the recovering server over again. This is called a **thundering herd**.
Jitter smears the retries out over time.

## Testing the API

FastAPI's `TestClient` (built on the httpx library) calls the app inside the test process, with no
real server or network. Lubanovic's testing chapter builds layers of unit, integration and full
tests with **pytest**, Python's standard test runner.

```python
# tests/test_api.py
from fastapi.testclient import TestClient
from churn.serve.app import app

def test_predict_ok():
    with TestClient(app) as client:                       # context manager runs lifespan startup/shutdown
        r = client.post("/predict", json={"instances": [
            {"tenure_months": 12, "monthly_charges": 59.9, "plan": "pro", "support_tickets_30d": 1}]})
        assert r.status_code == 200
        body = r.json()
        assert 0.0 <= body["predictions"][0]["churn_probability"] <= 1.0

def test_rejects_bad_plan():
    with TestClient(app) as client:
        r = client.post("/predict", json={"instances": [
            {"tenure_months": 12, "monthly_charges": 59.9, "plan": "gold"}]})
        assert r.status_code == 422
```

The first test sends a valid customer and checks for 200 and a probability between 0 and 1. The
second sends the invalid plan `"gold"` and checks for 422. Using `with TestClient(app)` matters:
it runs the lifespan startup, so the model is really loaded during the test.

Before going to production, **load-test**: fire increasing volumes of realistic requests with a
tool such as Locust, k6 or `hey`, and find the throughput at which p95 or p99 latency breaks your
SLO (the latency target from lesson 19).

## gRPC

REST with JSON is universal and easy for humans to read, but JSON is slow to parse and bulky for
large lists of numbers. **gRPC** (an open-source remote-procedure-call framework from Google) makes
calling another service look like calling a local function. It runs over **HTTP/2**, a newer
version of HTTP that carries many requests at once over one connection, and encodes messages with
**Protocol Buffers** (Protobuf), a compact binary format whose schema must be written first:

```protobuf
// churn.proto
syntax = "proto3";
package churn.v1;

service ChurnService {
  rpc Predict (PredictRequest) returns (PredictResponse);
  rpc PredictStream (stream Features) returns (stream Prediction);   // bidirectional streaming
}
message Features {
  int32 tenure_months = 1;
  double monthly_charges = 2;
  string plan = 3;
  int32 support_tickets_30d = 4;
}
message PredictRequest  { repeated Features instances = 1; }
message Prediction      { double churn_probability = 1; bool label = 2; }
message PredictResponse { string model_version = 1; repeated Prediction predictions = 2; }
```

Reading the file: `service` lists the callable functions; `rpc Predict` takes a `PredictRequest`
and returns a `PredictResponse`. `PredictStream` uses `stream` on both sides, so client and server
can each send a sequence of messages over one call. A `message` is a record type; `repeated` means
a list. The number after each field (`= 1`, `= 2`) is its **field number**, the identifier written
on the wire in place of the field's name.

```bash
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. churn.proto
```

This command **generates** Python code from the schema: classes for each message and a base class
for the server, so both sides are guaranteed to agree on the format.

| | REST + JSON | gRPC + Protobuf |
|---|---|---|
| Transport | HTTP/1.1 (or 2) | HTTP/2: multiplexed streams, header compression |
| Payload | text, self-describing | compact binary, schema required |
| Contract | OpenAPI (optional) | `.proto` (mandatory), generated clients/servers |
| Streaming | SSE / WebSocket add-ons | first-class client, server and bidirectional streaming |
| Browser support | native | needs gRPC-Web proxy |
| Debuggability | curl-friendly | needs tooling (grpcurl) |
| Best for | public APIs, simplicity | internal service-to-service, high throughput, large tensors |

**Multiplexed** means many requests share one connection at the same time. A **tensor** in the last
row is a multi-dimensional array of numbers, the native data type of deep learning.

Field numbers make **schema evolution** safe: you can add new fields and old and new programs keep
understanding each other, as long as a number is never reused for a different meaning (Kleppmann,
*DDIA* ch. 4). Model servers such as Triton and TF Serving offer both REST and gRPC, and KServe's
Open Inference Protocol defines both. A common architecture uses REST at the edge, where outside
clients call in, and gRPC between internal services and model servers.

> [!INTERVIEW]
> "Should a model endpoint be `async def`?" — Only if the work inside awaits I/O. CPU/GPU inference blocks
> the event loop; use a sync `def` endpoint (threadpool) or offload explicitly, and scale with
> processes/replicas. Add: load the model once at startup, validate with pydantic, expose
> liveness/readiness, return the model version, set timeouts, and batch requests.

## Designing the prediction API contract

The request and response schema is a **contract**: other teams write code against it, so changing
it later is expensive. Decide these points on purpose:

- **Raw inputs or pre-computed features?** Prefer accepting *raw, business-level* fields
  (`tenure_months`, `plan`) and computing derived features inside the service with the shared
  feature code. Clients that compute features themselves will compute them differently, which is
  training/serving skew (lesson 9).
- **Entity ID or full payload?** With an online feature store, the client can send only
  `customer_id` and the service looks the features up: smaller requests and consistent features,
  but one more dependency that can fail. Many APIs accept both: IDs for stored features plus
  request-time context.
- **Batch shape.** `{"instances": [...]}` with a documented maximum, and results returned in the
  same order. Decide whether one bad instance fails the whole request (simple) or produces a
  per-item error (flexible).
- **What comes back.** The score *and* the decision threshold used, the model version and a
  request ID. Avoid returning only a yes/no label: consumers will want the probability later.
- **Versioning.** Put a version in the path (`/v1/predict`). Additive changes, such as a new
  optional field, stay in v1; changes that would break existing clients get `/v2` and a
  **deprecation period**, an announced window during which both versions work.
- **Errors.** Use status codes consistently and a machine-readable error body.

| Status | Meaning for a prediction API |
|---|---|
| 200 | prediction returned |
| 400 / 422 | malformed or invalid input (client must fix; do not retry) |
| 401 / 403 | missing or insufficient credentials |
| 404 | unknown model or entity |
| 413 | payload/batch too large |
| 429 | rate limited or shedding load (retry with backoff; honour `Retry-After`) |
| 500 | bug or inference failure |
| 503 | not ready or dependency down (retry with backoff) |
| 504 | timed out upstream |

A consistent error body can be produced with a custom exception and a handler:

```python
from fastapi import Request
from fastapi.responses import JSONResponse

class PredictionError(Exception):
    def __init__(self, code: str, message: str, status: int = 500):
        self.code, self.message, self.status = code, message, status

@app.exception_handler(PredictionError)
async def prediction_error_handler(request: Request, exc: PredictionError):
    return JSONResponse(status_code=exc.status,
                        content={"error": {"code": exc.code, "message": exc.message,
                                           "request_id": request.headers.get("x-request-id")}})
```

Anywhere in the code you can now `raise PredictionError("unknown_customer", "no features", 404)`,
and the handler turns it into a JSON body with a stable `code` that client programs can test for,
a human-readable `message`, and the request ID for tracing.

## Timeouts, deadlines and load shedding in code

```python
import asyncio
from fastapi import HTTPException

MAX_IN_FLIGHT = 64
_slots = asyncio.Semaphore(MAX_IN_FLIGHT)

@app.post("/v1/predict", response_model=PredictResponse)
async def predict(req: PredictRequest):
    if _slots.locked():                                   # all slots busy: shed instead of queueing forever
        raise HTTPException(429, "server busy", headers={"Retry-After": "1"})
    async with _slots:
        try:
            feats = await asyncio.wait_for(feature_store.get(req.customer_ids), timeout=0.05)
        except asyncio.TimeoutError:
            feats = default_features(req.customer_ids)    # degrade: defaults the model was trained with
            FALLBACKS.labels("feature_timeout").inc()
        try:
            proba = await asyncio.wait_for(run_in_threadpool(model.predict, feats), timeout=0.5)
        except asyncio.TimeoutError:
            raise HTTPException(504, "inference timed out")
    return build_response(proba)
```

A **semaphore** is a counter of free slots: `async with _slots` takes one and gives it back at the
end, and `_slots.locked()` is true when all 64 are taken. In that case the request is turned away
at once with 429 and a `Retry-After` header telling the client when to try again.
`asyncio.wait_for(..., timeout=0.05)` gives the feature-store lookup 50 ms; if it is late, the code
falls back to default feature values and counts the fallback. Inference gets 500 ms before the
service answers **504 Gateway Timeout**.

Why turn work away? A server that accepts more than it can finish makes *every* request slow until
they all time out. The useful output, called **goodput** (requests answered successfully *within*
their deadline), drops to zero even though the machine is working flat out. Rejecting the excess
quickly keeps the accepted requests within the SLO. The simulation shows the effect.

```python-run
# Goodput with and without load shedding when demand exceeds capacity.
def simulate(arrival_rps, capacity_rps, timeout_s, shed, seconds=60):
    queue, served_in_time, rejected = 0.0, 0.0, 0.0
    for _ in range(seconds):
        queue += arrival_rps
        if shed:                                  # bound the queue to what can be served before the timeout
            limit = capacity_rps * timeout_s
            if queue > limit:
                rejected += queue - limit; queue = limit
        wait = queue / capacity_rps               # time for a newly queued request to be served
        done = min(queue, capacity_rps)
        if wait <= timeout_s:
            served_in_time += done
        queue -= done
    return served_in_time / seconds, rejected / seconds

for arrival in (80, 100, 130, 200):
    g0, _ = simulate(arrival, 100, 1.0, shed=False)
    g1, r1 = simulate(arrival, 100, 1.0, shed=True)
    print(f"arrivals {arrival:3d} rps, capacity 100: goodput without shedding {g0:5.1f} rps | with shedding {g1:5.1f} rps (rejecting {r1:4.1f} rps fast)")
```

Each loop turn is one second. New requests join the queue; with shedding on, the queue is cut down
to what can be served before the 1-second timeout. `wait` is how long the newest request would wait;
if that is within the timeout, the requests served this second count as goodput. The output:

```text
arrivals  80 rps, capacity 100: goodput without shedding  80.0 rps | with shedding  80.0 rps (rejecting  0.0 rps fast)
arrivals 100 rps, capacity 100: goodput without shedding 100.0 rps | with shedding 100.0 rps (rejecting  0.0 rps fast)
arrivals 130 rps, capacity 100: goodput without shedding   0.0 rps | with shedding 100.0 rps (rejecting 30.0 rps fast)
arrivals 200 rps, capacity 100: goodput without shedding   0.0 rps | with shedding 100.0 rps (rejecting 100.0 rps fast)
```

Past capacity, the queue of the server without shedding grows until every answer arrives too late
to be useful. The server that sheds keeps delivering its full 100 requests per second on time and
tells the rest to come back later.

## Authentication, limits and other production middleware

A model endpoint is an API like any other, so Lubanovic's chapters on the web layer and on
authentication apply directly:

- **Authenticate** callers, proving who they are, with API keys or **OAuth2** tokens (often
  **JWTs**, JSON Web Tokens, signed tokens that carry the caller's identity). This is usually
  enforced at the gateway or ingress.
- **Authorise** by scope: decide which models this particular client may call.
- **Rate-limit** per client, so one caller cannot use up the capacity of everyone.
- Cap the request body size.
- Enable **CORS** (cross-origin resource sharing, the browser rule about which web sites may call
  your API) only where a browser calls you directly.
- Never log raw credentials, or full payloads that contain personal data.

## gRPC server sketch

```python
# server.py - generated modules churn_pb2 / churn_pb2_grpc come from protoc
import grpc
from concurrent import futures
import churn_pb2, churn_pb2_grpc

class ChurnService(churn_pb2_grpc.ChurnServiceServicer):
    def __init__(self, model, version): self.model, self.version = model, version
    def Predict(self, request, context):
        if len(request.instances) > 256:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "batch too large")
        rows = [[i.tenure_months, i.monthly_charges, i.support_tickets_30d] for i in request.instances]
        probs = self.model.predict(rows)
        return churn_pb2.PredictResponse(
            model_version=self.version,
            predictions=[churn_pb2.Prediction(churn_probability=float(p), label=p >= 0.5) for p in probs])

def serve(model, version):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=8),
                         options=[("grpc.max_receive_message_length", 16 * 1024 * 1024)])
    churn_pb2_grpc.add_ChurnServiceServicer_to_server(ChurnService(model, version), server)
    server.add_insecure_port("[::]:50051")
    server.start(); server.wait_for_termination()
```

`ChurnService` fills in the generated base class: its `Predict` method receives an already-decoded
`request` object and returns a response message. `context.abort` ends the call with an error.
`serve` creates a server with a pool of 8 threads, raises the maximum message size to 16 MB, and
listens on port 50051 (`add_insecure_port` means no TLS, which is acceptable only inside a trusted
network or behind a proxy that adds encryption).

gRPC has its own status codes (`INVALID_ARGUMENT`, `UNAVAILABLE`, `DEADLINE_EXCEEDED`,
`RESOURCE_EXHAUSTED`) and built-in **deadlines** that travel with the call across service hops: if
the original caller's deadline has passed, every downstream service can stop working on the request.
REST only gets this by convention, for example with a custom header.

## Summary

- FastAPI gives validation, documentation and ASGI performance. Structure the service around a
  model loaded once in `lifespan`, typed schemas, health endpoints, metrics and versioned responses.
- Never block the event loop with inference; understand workers versus replicas and the memory each
  process needs.
- Build in timeouts, retries with jittered backoff, load shedding and graceful shutdown.
- Test in-process with `TestClient`; load-test against the SLO.
- gRPC offers compact binary payloads, streaming and strict contracts for internal, high-throughput
  paths.

## Glossary

- **API** - the agreed shape of requests and responses between programs.
- **HTTP method / status code** - the verb of a request (`GET`, `POST`) / the number saying how it
  went (200, 422, 503).
- **REST / JSON** - a common style of HTTP API / the text format its bodies use.
- **Endpoint** - one method plus path that a service answers.
- **Schema / validation** - a description of a data shape / checking data against it.
- **pydantic** - the library FastAPI uses to turn type hints into validation.
- **OpenAPI** - a standard machine-readable description of an HTTP API.
- **ASGI / Uvicorn / Gunicorn** - the async Python server interface / a server that runs ASGI apps
  / a process manager that supervises workers.
- **Event loop / coroutine** - one thread that switches between waiting tasks / a function that can
  pause at `await`.
- **I/O-bound / CPU-bound** - mostly waiting / mostly computing.
- **Threadpool / GIL** - extra threads for blocking work / Python's lock that lets one thread run
  Python code at a time.
- **Middleware** - code that runs around every request.
- **Liveness / readiness** - "the process is alive" / "it can serve traffic now".
- **Exponential backoff / jitter / thundering herd** - growing waits between retries / randomness
  added to them / many clients retrying in lock-step.
- **Load shedding / goodput** - rejecting excess work quickly / requests answered within their
  deadline.
- **Circuit breaker** - stops calling a failing dependency for a while.
- **Idempotency key** - a unique key that makes a retried request harmless.
- **Semaphore** - a counter of free slots that limits concurrent work.
- **gRPC / Protocol Buffers / HTTP/2** - a remote-call framework / its binary, schema-first format /
  the transport carrying many requests on one connection.
- **Field number / schema evolution** - a Protobuf field's wire identifier / changing a schema
  without breaking old programs.
- **Deadline** - the time by which a call must finish, passed along to downstream services.

```quiz
[
  {"q": "Where should the model be loaded in a FastAPI service?",
   "options": ["Inside the /predict handler on each request", "Once at startup (lifespan handler), then reused", "In the Dockerfile CMD", "In the client"],
   "answer": 1, "explain": "Per-request loading adds huge latency and memory churn."},
  {"q": "What happens if you call a blocking 200 ms `model.predict` directly inside an `async def` endpoint?",
   "options": ["Nothing special", "The event loop is blocked, stalling all other requests including health checks", "FastAPI auto-parallelises it", "The request is rejected"],
   "answer": 1, "explain": "Blocking code in a coroutine prevents the loop from serving other tasks."},
  {"q": "What does pydantic's `extra=\"forbid\"` do for a request model?",
   "options": ["Allows any extra fields", "Rejects requests containing unknown fields with a validation error", "Encrypts the payload", "Disables validation"],
   "answer": 1, "explain": "It catches client typos such as a misspelled feature name."},
  {"q": "With 4 Uvicorn workers and a 3 GB model, approximate memory for models is...",
   "options": ["3 GB", "12 GB", "0.75 GB", "Depends only on request rate"],
   "answer": 1, "explain": "Each worker process holds its own copy."},
  {"q": "Why add jitter to exponential backoff?",
   "options": ["To make retries slower", "To desynchronise clients and avoid thundering-herd retry spikes", "To use less memory", "To bypass rate limits"],
   "answer": 1, "explain": "Without jitter, clients that failed together retry together."},
  {"q": "Which is an advantage of gRPC over REST/JSON for internal model serving?",
   "options": ["It is human-readable with curl", "Compact binary payloads, HTTP/2 multiplexing and first-class streaming", "It needs no schema", "It works natively in all browsers"],
   "answer": 1, "explain": "Protobuf over HTTP/2 is efficient; the cost is tooling and browser support."},
  {"q": "What is the difference between /healthz (liveness) and /readyz (readiness)?",
   "options": ["They are identical", "Liveness says the process is alive; readiness says it can serve traffic (e.g. model loaded)", "Readiness restarts the pod", "Liveness checks the database schema"],
   "answer": 1, "explain": "A pod can be alive but not ready while a large model loads."},
  {"q": "Demand is 130 requests per second and capacity is 100. Why does load shedding raise goodput?",
   "options": ["It makes the model faster", "Rejecting the excess quickly keeps the queue short enough that accepted requests finish within their deadline", "It retries every request twice", "It adds more replicas automatically"],
   "answer": 1, "explain": "Without shedding the queue grows until every answer is too late; with it, 100 requests per second still finish on time."}
]
```

> **Source:** Bill Lubanovic, *FastAPI*, ch. 3–5 (FastAPI, async/Starlette, pydantic), ch. 12 (testing), ch. 13 (production: workers, performance, queues); FastAPI documentation (*Lifespan events*, *Concurrency and async/await*, *Testing*); gRPC and Protocol Buffers documentation; Martin Kleppmann, *DDIA*, ch. 4 (Protobuf schema evolution).
