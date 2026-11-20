# REST and gRPC serving with FastAPI

## Why FastAPI is the default for Python model APIs

FastAPI combines three things that matter for model serving: **type-hint-driven validation** through
pydantic (bad requests are rejected with a clear 422 before they reach the model), **automatic OpenAPI
docs** (`/docs`), and **ASGI async** performance via Starlette and Uvicorn. Lubanovic's *FastAPI* book
describes it as built on exactly these pillars: Starlette for the web parts, pydantic for the data parts.

## A production-shaped prediction service

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

Things to notice:

1. **Load the model once** in the `lifespan` handler, not per request; warm it up.
2. **Separate liveness and readiness** endpoints (Kubernetes uses them differently — lesson 22).
3. **Validation at the boundary**: ranges, enums, `extra="forbid"`, batch-size cap. The model never sees
   garbage; the client gets a precise 422 error.
4. **Batch endpoint** (`instances: [...]`): vectorised prediction is far cheaper than N single calls.
5. **Response includes the model version** — indispensable for debugging and for joining feedback later.
6. **Metrics** exposed at `/metrics` for Prometheus (module 10).

### `async def` vs `def` — the trap

Lubanovic (ch. 4, 13) explains that async shines when the server spends its time *waiting* on I/O. Model
inference is **CPU-bound** (or GPU-bound): it does not yield to the event loop.

- Calling a blocking `model.predict` directly inside `async def` **blocks the event loop**: every other
  request (including health checks!) stalls until it finishes.
- A plain `def` endpoint is run by FastAPI in a **threadpool**, so the loop stays responsive.
- Or keep `async def` and offload with `run_in_threadpool` / `asyncio.to_thread`, as above.
- NumPy, scikit-learn, PyTorch and ONNX Runtime release the GIL in their native code, so threads do give
  real parallelism for inference — within the limits of CPU cores.
- Use `async` clients (`httpx.AsyncClient`, async Redis) for I/O such as feature-store lookups.

```python-run
# Why blocking the event loop is catastrophic: simulate 20 concurrent requests.
import asyncio, time

def blocking_predict(ms=50):
    time.sleep(ms / 1000)            # stands in for CPU-bound inference
    return 1

async def handler_blocking():
    return blocking_predict()        # blocks the whole loop

async def handler_threadpool():
    return await asyncio.to_thread(blocking_predict)

async def bench(handler, n=20):
    t0 = time.perf_counter()
    await asyncio.gather(*[handler() for _ in range(n)])
    return time.perf_counter() - t0

async def main():
    a = await bench(handler_blocking)
    b = await bench(handler_threadpool)
    print(f"blocking inside async def: {a*1000:.0f} ms for 20 requests (serialised)")
    print(f"offloaded to threadpool : {b*1000:.0f} ms for 20 requests")
try:
    asyncio.run(main())
except RuntimeError:                 # already inside an event loop (e.g. in the browser)
    print("Run locally to see timings: blocking ~1000 ms vs threadpool ~100 ms")
```

### Running it: workers and processes

```bash
uvicorn churn.serve.app:app --host 0.0.0.0 --port 8000 --workers 4
# or Gunicorn supervising Uvicorn workers (process management, graceful restarts):
gunicorn churn.serve.app:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

Each worker is a separate process with **its own copy of the model in memory**. Four workers × a 3 GB
model = 12 GB. On Kubernetes the usual pattern is **one worker per container** and scale with replicas
(the orchestrator is your process manager); for GPU models, one process per GPU plus a batching layer
(lesson 21). As Lubanovic notes, something above the servers must also keep them running, reverse-proxy
requests and terminate HTTPS — a load balancer / ingress does this.

## Reliability patterns

- **Timeouts everywhere**: client-side, server-side, and on every downstream call. A request without a
  timeout is a resource leak.
- **Retries with exponential backoff and jitter** — only for idempotent operations and transient errors
  (connection reset, 429, 503). You will build the schedule in `mlops-backoff-schedule`.
- **Load shedding**: when the queue is full, return 429/503 quickly rather than accept work you cannot
  finish in time.
- **Circuit breakers**: stop calling a failing dependency for a while; serve a fallback.
- **Graceful shutdown**: on SIGTERM, stop accepting new requests, finish in-flight ones.
- **Idempotency keys** for non-idempotent POSTs so retries do not double-apply.

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

## Testing the API

FastAPI's `TestClient` (built on httpx) exercises the app in-process — no server needed. Lubanovic's
testing chapter layers unit, integration and full tests with pytest.

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

Load-test before production with Locust, k6 or `hey` to find the throughput at which p95/p99 latency
breaks your SLO.

## gRPC

REST with JSON is universal and human-friendly, but JSON parsing is slow and verbose for large numeric
payloads. **gRPC** uses **HTTP/2** and **Protocol Buffers** (binary, schema-first):

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

```bash
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. churn.proto
```

| | REST + JSON | gRPC + Protobuf |
|---|---|---|
| Transport | HTTP/1.1 (or 2) | HTTP/2: multiplexed streams, header compression |
| Payload | text, self-describing | compact binary, schema required |
| Contract | OpenAPI (optional) | `.proto` (mandatory), generated clients/servers |
| Streaming | SSE / WebSocket add-ons | first-class client, server and bidirectional streaming |
| Browser support | native | needs gRPC-Web proxy |
| Debuggability | curl-friendly | needs tooling (grpcurl) |
| Best for | public APIs, simplicity | internal service-to-service, high throughput, large tensors |

Protobuf field numbers enable **schema evolution**: adding fields is backward and forward compatible as
long as numbers are never reused (DDIA ch. 4). Model servers such as Triton and TF Serving expose both
REST and gRPC; KServe's Open Inference Protocol defines both too. A common architecture: REST at the
edge for clients, gRPC between internal services and model servers.

> [!INTERVIEW]
> "Should a model endpoint be `async def`?" — Only if the work inside awaits I/O. CPU/GPU inference blocks
> the event loop; use a sync `def` endpoint (threadpool) or offload explicitly, and scale with
> processes/replicas. Add: load the model once at startup, validate with pydantic, expose
> liveness/readiness, return the model version, set timeouts, and batch requests.

## Designing the prediction API contract

The request and response schema is a public contract; changing it later is expensive. Decisions to make
deliberately:

- **Raw inputs or pre-computed features?** Prefer accepting *raw, business-level* fields
  (`tenure_months`, `plan`) and computing derived features inside the service with the shared feature
  code. Clients that compute features themselves will compute them differently (skew).
- **Entity ID or full payload?** With an online feature store, the client sends `customer_id` and the
  service looks up features: smaller requests and consistent features, but a runtime dependency. Many
  APIs accept both: IDs for stored features plus request-time context.
- **Batch shape.** `{"instances": [...]}` with a documented maximum; return results in the same order;
  decide whether one bad instance fails the whole request (simple) or yields per-item errors (flexible).
- **What comes back.** Scores *and* the decision threshold used, the model version, and a request ID.
  Avoid returning only a label: consumers will want the probability later.
- **Versioning.** Put a version in the path (`/v1/predict`). Additive changes (new optional field) stay
  in v1; breaking changes get `/v2` and a deprecation period.
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

Why shed load? A server that accepts more work than it can finish makes *every* request slow and then
times them all out — zero goodput. Rejecting the excess quickly keeps the accepted requests within the
SLO.

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

Past capacity, the unshedded server's queue grows until every response is too late to be useful; the
shedding server keeps serving its full capacity within the deadline.

## Authentication, limits and other production middleware

A model endpoint is an API like any other. Lubanovic's chapters on the web layer and on authentication
apply directly: authenticate callers (API keys or OAuth2/JWT, usually enforced at the gateway/ingress),
authorise by scope (which models may this client call?), rate-limit per client, cap request body size,
enable CORS only where a browser calls you directly, and never log raw credentials or full payloads
containing personal data.

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

gRPC has its own status codes (`INVALID_ARGUMENT`, `UNAVAILABLE`, `DEADLINE_EXCEEDED`,
`RESOURCE_EXHAUSTED`) and first-class **deadlines** that propagate across service hops: if the caller's
deadline has passed, downstream services can stop working on the request — a property REST only gets by
convention.

## Summary

- FastAPI gives validation, docs and ASGI performance; structure the service around a lifespan-loaded
  model, typed schemas, health endpoints, metrics and versioned responses.
- Never block the event loop with inference; understand workers vs replicas and memory per process.
- Build in timeouts, retries with jittered backoff, load shedding, graceful shutdown.
- Test with `TestClient`; load-test for the SLO.
- gRPC offers compact binary payloads, streaming and strict contracts for internal high-throughput paths.

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
   "answer": 1, "explain": "A pod can be alive but not ready while a large model loads."}
]
```

> **Source:** Bill Lubanovic, *FastAPI*, ch. 3–5 (FastAPI, async/Starlette, pydantic), ch. 12 (testing), ch. 13 (production: workers, performance, queues); FastAPI documentation (*Lifespan events*, *Concurrency and async/await*, *Testing*); gRPC and Protocol Buffers documentation; Martin Kleppmann, *DDIA*, ch. 4 (Protobuf schema evolution).
