# End-to-end project: a production model service

This capstone assembles the whole track into one coherent service: a **sentiment-analysis API** with
single and batch prediction, a streaming "explain" endpoint, API-key auth, rate limiting, caching,
versioned routes, health checks, tests and a Docker image. Every file is short, and every choice has been
motivated in an earlier lesson — the point here is to see how the pieces fit, in the layered structure
from Lubanovic's book (web → service → data/model, with shared schemas).

## Requirements

- `POST /v1/predict` — classify one or many texts; return label, score and model version.
- `POST /v1/explain/stream` — stream a token-by-token explanation over SSE.
- `GET /v1/model` — model metadata. `GET /healthz`, `GET /readyz` — probes.
- API key in `X-API-Key`; per-key rate limit; predictions cached by `(model_version, text)`.
- The model loads once at startup; inference never blocks the event loop.
- Config from the environment; structured logs with request IDs; tests without the real model.

## Layout

```text
sentiment-service/
├── app/
│   ├── main.py              # app factory, lifespan, middleware, routers, exception handlers
│   ├── config.py            # Settings (pydantic-settings)
│   ├── schemas.py           # Pydantic request/response models      (the book's "model" package)
│   ├── errors.py            # domain exceptions
│   ├── deps.py              # dependencies: settings, auth, rate limit, service
│   ├── web/                 # routers                               (web layer)
│   │   ├── health.py
│   │   └── v1.py
│   ├── service/             # business logic                        (service layer)
│   │   └── sentiment.py
│   └── ml/                  # model loading and inference           (data layer for a model)
│       ├── model.py
│       └── batcher.py
├── tests/
│   ├── conftest.py
│   └── test_api.py
├── requirements.txt
├── Dockerfile
└── .env.example
```

## Configuration — `app/config.py`

```python
from functools import lru_cache
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="APP_", extra="ignore",
                                      protected_namespaces=())
    environment: str = "dev"
    api_keys: list[SecretStr] = []                 # APP_API_KEYS='["k1","k2"]'
    model_uri: str = "models/sentiment.joblib"
    model_version: str = "2025-01-15"
    max_batch_size: int = Field(32, ge=1, le=256)
    max_wait_ms: int = Field(5, ge=0, le=100)
    rate_limit_per_minute: int = Field(120, ge=1)
    cache_ttl_seconds: int = Field(300, ge=0)
    cors_origins: list[str] = []

@lru_cache
def get_settings() -> Settings:
    return Settings()
```

## Schemas — `app/schemas.py`

```python
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

class PredictRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    texts: list[str] = Field(min_length=1, max_length=64)

    @field_validator("texts")
    @classmethod
    def check_texts(cls, v: list[str]) -> list[str]:
        cleaned = [t.strip() for t in v]
        if any(not t or len(t) > 5_000 for t in cleaned):
            raise ValueError("each text must be 1-5000 characters")
        return cleaned

class Prediction(BaseModel):
    label: Literal["positive", "negative", "neutral"]
    score: float = Field(ge=0, le=1)
    cached: bool = False

class PredictResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    predictions: list[Prediction]
    model_version: str

class ModelInfo(BaseModel):
    name: str
    version: str
    labels: list[str]
```

## The model wrapper — `app/ml/model.py`

The "data layer" for an ML service is the model itself. Wrap it behind a small interface so the rest of
the app (and the tests) never touch framework-specific objects:

```python
from typing import Protocol

class SentimentModel(Protocol):
    name: str
    version: str
    labels: list[str]
    def predict_batch(self, texts: list[str]) -> list[tuple[str, float]]: ...

class SklearnSentimentModel:
    name = "sentiment"
    labels = ["negative", "neutral", "positive"]

    def __init__(self, uri: str, version: str):
        import joblib
        self._pipeline = joblib.load(uri)            # tokenizer/vectoriser + classifier in ONE artefact
        self.version = version

    def predict_batch(self, texts: list[str]) -> list[tuple[str, float]]:
        proba = self._pipeline.predict_proba(texts)                   # vectorised, releases the GIL
        idx = proba.argmax(axis=1)
        return [(self.labels[i], float(p[i])) for i, p in zip(idx, proba)]
```

`app/ml/batcher.py` is the `MicroBatcher` from the serving lesson, calling
`await run_in_threadpool(model.predict_batch, texts)` so inference runs in a worker thread.

## Service layer — `app/service/sentiment.py`

No HTTP here — just rules: cache lookup, batching, assembling results.

```python
import hashlib

class SentimentService:
    def __init__(self, model, batcher, cache, ttl: int):
        self.model, self.batcher, self.cache, self.ttl = model, batcher, cache, ttl

    def _key(self, text: str) -> str:
        digest = hashlib.sha256(text.encode()).hexdigest()
        return f"pred:{self.model.version}:{digest}"       # model version in the key!

    async def predict(self, texts: list[str]) -> list[Prediction]:
        results: list[Prediction | None] = [None] * len(texts)
        misses: list[int] = []
        for i, text in enumerate(texts):
            hit = await self.cache.get(self._key(text))
            if hit is not None:
                results[i] = Prediction.model_validate_json(hit).model_copy(update={"cached": True})
            else:
                misses.append(i)
        if misses:
            outputs = await asyncio.gather(*(self.batcher.submit(texts[i]) for i in misses))
            for i, (label, score) in zip(misses, outputs):
                pred = Prediction(label=label, score=score)
                results[i] = pred
                await self.cache.set(self._key(texts[i]), pred.model_dump_json(), ex=self.ttl)
        return results
```

## Dependencies — `app/deps.py`

```python
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def require_api_key(key: Annotated[str | None, Depends(api_key_header)],
                    settings: Annotated[Settings, Depends(get_settings)]) -> str:
    valid = key is not None and any(
        secrets.compare_digest(key, k.get_secret_value()) for k in settings.api_keys)
    if not valid:
        raise HTTPException(status_code=401, detail="Invalid or missing API key",
                            headers={"WWW-Authenticate": "ApiKey"})
    return hashlib.sha256(key.encode()).hexdigest()[:12]         # an ID safe to log / use as limiter key

async def rate_limit(request: Request, client_id: Annotated[str, Depends(require_api_key)],
                     settings: Annotated[Settings, Depends(get_settings)]) -> None:
    allowed, retry_after = await request.app.state.limiter.allow(client_id)
    if not allowed:
        raise HTTPException(status_code=429, detail="Rate limit exceeded",
                            headers={"Retry-After": str(retry_after)})

def get_service(request: Request) -> SentimentService:
    service = getattr(request.app.state, "service", None)
    if service is None:
        raise HTTPException(status_code=503, detail="Model not ready")
    return service

ServiceDep = Annotated[SentimentService, Depends(get_service)]
```

## Web layer — `app/web/v1.py`

```python
router = APIRouter(prefix="/v1", tags=["v1"], dependencies=[Depends(rate_limit)])   # auth + limit on all

@router.post("/predict", response_model=PredictResponse)
async def predict(req: PredictRequest, service: ServiceDep) -> PredictResponse:
    try:
        async with asyncio.timeout(5):
            preds = await service.predict(req.texts)
    except asyncio.QueueFull:
        raise HTTPException(503, "Server busy", headers={"Retry-After": "1"})
    except TimeoutError:
        raise HTTPException(504, "Inference timed out")
    return PredictResponse(predictions=preds, model_version=service.model.version)

@router.get("/model", response_model=ModelInfo)
async def model_info(service: ServiceDep) -> ModelInfo:
    m = service.model
    return ModelInfo(name=m.name, version=m.version, labels=m.labels)

@router.post("/explain/stream")
async def explain_stream(req: ExplainRequest, service: ServiceDep):
    async def events():
        try:
            async for token in service.explain(req.text):
                yield f"event: token\ndata: {json.dumps({'text': token})}\n\n"
            yield f"event: done\ndata: {json.dumps({'model_version': service.model.version})}\n\n"
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("explain failed")
            yield 'event: error\ndata: {"message": "generation failed"}\n\n'
    return StreamingResponse(events(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
```

`app/web/health.py` holds `/healthz` (always 200) and `/readyz` (503 until `app.state.service` exists) —
outside the authenticated router.

## Wiring — `app/main.py`

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    model = await run_in_threadpool(SklearnSentimentModel, settings.model_uri, settings.model_version)
    await run_in_threadpool(model.predict_batch, ["warm up"])
    batcher = MicroBatcher(model.predict_batch, settings.max_batch_size, settings.max_wait_ms / 1000)
    batch_task = asyncio.create_task(batcher.run())
    redis_client = redis.from_url(settings.redis_url, decode_responses=True)
    app.state.limiter = RedisRateLimiter(redis_client, settings.rate_limit_per_minute)
    app.state.service = SentimentService(model, batcher, redis_client, settings.cache_ttl_seconds)
    logger.info("model loaded", extra={"model_version": model.version})
    yield                                              # ---- serving ----
    app.state.service = None                           # readiness -> 503 while draining
    batch_task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await batch_task
    await redis_client.aclose()

def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Sentiment Service", version="1.0.0", lifespan=lifespan,
                  openapi_url=None if settings.environment == "prod" else "/openapi.json")
    app.add_middleware(RequestContextMiddleware)       # request ID + JSON access log + metrics
    app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins,
                       allow_methods=["GET", "POST"], allow_headers=["X-API-Key", "Content-Type"])
    app.include_router(health.router)
    app.include_router(v1.router)

    @app.exception_handler(ModelError)
    async def model_error_handler(request, exc):
        return JSONResponse(status_code=503, content={"detail": "Model unavailable"})
    return app

app = create_app()
```

## Run the core logic

The framework glue aside, the heart of the service is plain Python. This cell runs the schemas, a fake
model, the micro-batcher, the cache-aware service and a rate limiter together — the same objects the
tests use:

```python-run
import asyncio, hashlib, time
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

# ---------- schemas ----------
class PredictRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    texts: list[str] = Field(min_length=1, max_length=64)
    @field_validator("texts")
    @classmethod
    def check_texts(cls, v):
        cleaned = [t.strip() for t in v]
        if any(not t or len(t) > 5000 for t in cleaned):
            raise ValueError("each text must be 1-5000 characters")
        return cleaned

class Prediction(BaseModel):
    label: Literal["positive", "negative", "neutral"]
    score: float = Field(ge=0, le=1)
    cached: bool = False

# ---------- fake model (what tests inject) ----------
class FakeModel:
    name, version, labels = "sentiment", "test-1", ["negative", "neutral", "positive"]
    calls = 0
    def predict_batch(self, texts):
        FakeModel.calls += 1
        out = []
        for t in texts:
            pos = sum(w in t.lower() for w in ("love", "great", "good"))
            neg = sum(w in t.lower() for w in ("hate", "awful", "bad"))
            out.append(("positive", 0.9) if pos > neg else ("negative", 0.9) if neg > pos else ("neutral", 0.6))
        return out

# ---------- micro-batcher ----------
class MicroBatcher:
    def __init__(self, fn, max_batch=8, max_wait=0.005):
        self.fn, self.max_batch, self.max_wait, self.q = fn, max_batch, max_wait, asyncio.Queue(100)
    async def submit(self, item):
        fut = asyncio.get_running_loop().create_future()
        self.q.put_nowait((item, fut))
        return await fut
    async def run(self):
        while True:
            batch = [await self.q.get()]
            deadline = time.monotonic() + self.max_wait
            while len(batch) < self.max_batch and (left := deadline - time.monotonic()) > 0:
                try: batch.append(await asyncio.wait_for(self.q.get(), left))
                except asyncio.TimeoutError: break
            for (_, fut), out in zip(batch, self.fn([i for i, _ in batch])):
                fut.set_result(out)

# ---------- cache + service ----------
class DictCache:
    def __init__(self): self.d = {}
    async def get(self, k): return self.d.get(k)
    async def set(self, k, v, ex): self.d[k] = v

class SentimentService:
    def __init__(self, model, batcher, cache): self.model, self.batcher, self.cache = model, batcher, cache
    def _key(self, t): return f"pred:{self.model.version}:{hashlib.sha256(t.encode()).hexdigest()}"
    async def predict(self, texts):
        results, misses = [None] * len(texts), []
        for i, t in enumerate(texts):
            hit = await self.cache.get(self._key(t))
            if hit: results[i] = Prediction.model_validate_json(hit).model_copy(update={"cached": True})
            else: misses.append(i)
        outs = await asyncio.gather(*(self.batcher.submit(texts[i]) for i in misses))
        for i, (label, score) in zip(misses, outs):
            results[i] = Prediction(label=label, score=score)
            await self.cache.set(self._key(texts[i]), results[i].model_dump_json(), ex=300)
        return results

# ---------- "web layer" ----------
async def predict_endpoint(body, service):
    try:
        req = PredictRequest.model_validate(body)
    except ValidationError as e:
        return 422, [{"loc": ["body", *err["loc"]], "type": err["type"]} for err in e.errors()]
    preds = await service.predict(req.texts)
    return 200, {"predictions": [p.model_dump() for p in preds], "model_version": service.model.version}

model = FakeModel()
batcher = MicroBatcher(model.predict_batch)
task = asyncio.create_task(batcher.run())
service = SentimentService(model, batcher, DictCache())

print(await predict_endpoint({"texts": ["I love this", "awful, I hate it", "it is a phone"]}, service))
print("model calls so far:", FakeModel.calls, "(3 texts, 1 batch)")
print(await predict_endpoint({"texts": ["I love this"]}, service))
print("model calls after repeat:", FakeModel.calls, "(served from cache)")
print(await predict_endpoint({"texts": [], "extra": 1}, service))
print(await predict_endpoint({"texts": ["   "]}, service))
task.cancel()
```

## Tests — `tests/`

```python
# conftest.py
@pytest.fixture
def client():
    app = create_app()
    fake_service = SentimentService(FakeModel(), ImmediateBatcher(FakeModel()), DictCache(), ttl=60)
    app.dependency_overrides[get_service] = lambda: fake_service
    app.dependency_overrides[require_api_key] = lambda: "test-client"
    app.dependency_overrides[rate_limit] = lambda: None
    with TestClient(app) as c:        # (a test lifespan/settings avoids loading the real model)
        yield c
    app.dependency_overrides.clear()

# test_api.py
def test_predict_happy_path(client):
    r = client.post("/v1/predict", json={"texts": ["I love it", "I hate it"]})
    assert r.status_code == 200
    body = r.json()
    assert [p["label"] for p in body["predictions"]] == ["positive", "negative"]
    assert body["model_version"] == "test-1"

@pytest.mark.parametrize("payload", [{}, {"texts": []}, {"texts": ["ok"], "oops": 1},
                                     {"texts": ["x" * 5001]}, {"texts": ["a"] * 65}])
def test_predict_validation(client, payload):
    assert client.post("/v1/predict", json=payload).status_code == 422

def test_auth_required():
    app = create_app()
    app.dependency_overrides[get_service] = lambda: fake_service
    r = TestClient(app).post("/v1/predict", json={"texts": ["hi"]})
    assert r.status_code == 401

def test_stream_ends_with_done(client):
    with client.stream("POST", "/v1/explain/stream", json={"text": "I love it"}) as r:
        events = [l for l in r.iter_lines() if l.startswith("event:")]
    assert events[-1] == "event: done"
```

## Packaging — `Dockerfile`

```dockerfile
FROM python:3.13-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=2
RUN useradd --create-home --uid 10001 app
WORKDIR /code
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY ./app ./app
USER app
EXPOSE 8000
CMD ["fastapi", "run", "app/main.py", "--port", "8000", "--proxy-headers"]
```

One process per container; replicas, TLS, probes (`/healthz`, `/readyz`) and autoscaling belong to the
platform. The model artefact is fetched from the registry/volume named by `APP_MODEL_URI` at startup, so
shipping a new model is a config change plus rolling restart — and a rollback is the reverse.

## Review checklist

Walk a request through and name the lesson behind each step:

1. TLS terminates at the proxy; Uvicorn receives ASGI events (*ASGI stack*, *deployment*).
2. Middleware assigns a request ID, starts the timer (*middleware, logging*).
3. Router matches `/v1/predict`; dependencies authenticate the key and apply the rate limit
   (*routers, dependencies, security*).
4. Pydantic validates the body — 422 on failure (*Pydantic*).
5. The service checks the cache, submits misses to the batcher (*layers, caching, batching*).
6. Inference runs in a thread; the loop stays free (*async*).
7. The response model serialises predictions with the model version (*response models, versioning*).
8. The access log line and metrics are emitted (*observability*).

> [!INTERVIEW]
> "Design a production ML inference API." — Structure the answer along this lesson: (1) contract —
> versioned REST endpoints, strict Pydantic schemas with bounds, model version in responses; (2) lifecycle
> — model loaded once in lifespan, warm-up, readiness gating; (3) execution — inference off the event
> loop, bounded concurrency, dynamic batching, timeouts and load shedding; (4) cross-cutting — auth, rate
> limits (by tokens for LLMs), caching keyed by model version + input hash; (5) operations — Docker image,
> one process per container, replicas behind a load balancer, config via environment, health probes,
> structured logs, RED metrics plus model metrics, tracing; (6) change management — tests with fake
> models via dependency overrides, canary/shadow rollouts, instant rollback.

## Extensions to try

- Add `/v2/predict` returning per-label probabilities; mark v1 deprecated.
- Swap `DictCache` for Redis and the fake limiter for a token bucket in a Lua script.
- Add Prometheus metrics for batch size and queue wait; alert on p95 latency.
- Add a shadow model: run it on a sample of traffic and log disagreement with the primary.
- Persist predictions asynchronously for drift monitoring (background task → queue → warehouse).

## Summary

- The project applies the layered architecture: thin routers, a service with the rules, a model wrapper
  behind a small interface, shared Pydantic schemas.
- Lifespan owns long-lived resources; dependencies provide them (and are overridden in tests).
- Validation, auth, rate limiting, caching, batching, timeouts, streaming, logging and health checks each
  occupy a few lines in a predictable place.

```quiz
[
  {"q": "Why is the model wrapped behind a small interface (predict_batch) instead of used directly in routers?", "options": ["It is faster", "The rest of the app and the tests depend on a narrow contract, so models and frameworks can be swapped or faked", "Pydantic requires it", "To avoid loading the model"], "answer": 1,
   "explain": "This is the layering principle applied to ML: the 'data layer' hides framework details behind a simple API."},
  {"q": "Why does the cache key include the model version?", "options": ["To make keys longer", "So predictions from an old model are never served after a new model is deployed", "Redis requires it", "For authentication"], "answer": 1,
   "explain": "Cached outputs are only valid for the model that produced them; versioned keys invalidate implicitly on rollout."},
  {"q": "The rate-limit and auth dependencies are attached to the v1 router. Why are health endpoints in a separate router?", "options": ["They are slower", "Probes must work without credentials and shouldn't consume rate-limit budget", "FastAPI forbids mixing", "They need WebSockets"], "answer": 1,
   "explain": "Orchestrator probes are unauthenticated and frequent; keeping them outside the protected router avoids false failures."},
  {"q": "During shutdown the lifespan sets app.state.service = None first. What does that achieve?", "options": ["Frees GPU memory instantly", "Readiness starts failing so the load balancer stops sending new traffic while in-flight work drains", "It restarts the worker", "It clears the cache"], "answer": 1,
   "explain": "Failing readiness during draining is how a replica leaves rotation gracefully."},
  {"q": "How do the tests avoid loading the real model?", "options": ["They skip prediction tests", "They override the get_service dependency with a service built on a fake model", "They mock HTTP", "They run in production"], "answer": 1,
   "explain": "dependency_overrides injects fakes at the boundary so API tests are fast and deterministic."},
  {"q": "Shipping a new model version in this design requires:", "options": ["Rewriting the routers", "Changing APP_MODEL_URI/APP_MODEL_VERSION and performing a rolling restart", "A database migration", "Rebuilding the client SDK"], "answer": 1,
   "explain": "The model is configuration, not code: new replicas load the new artefact and readiness gates the rollout; rollback is the same switch reversed."}
]
```

> **Source:** Lubanovic, *FastAPI*, Part III "Making a Website" (ch. 8 "Web Layer", ch. 9 "Service Layer", ch. 10 "Data Layer"), ch. 12 "Testing", ch. 13 "Production", ch. 14 "Databases, Data Science, and a Little AI"; https://fastapi.tiangolo.com/advanced/events/, /tutorial/bigger-applications/, /tutorial/testing/, /deployment/docker/
