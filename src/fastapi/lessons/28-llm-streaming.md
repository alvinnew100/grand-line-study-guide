# Streaming LLM output and versioned endpoints

Large language models changed what "serving a model" feels like. A classifier answers in 20 ms; an LLM may
take 20 *seconds* to finish — but it produces its answer one token at a time, and users are happy as long
as text starts flowing quickly. That makes **streaming** the core serving pattern. Models also change
constantly, so **versioning** — of the API and of the model behind it — is the second theme of this
lesson.

## Latency for generative models

Two numbers replace "request latency":

- **TTFT — time to first token**: how long until the user sees *something*. Dominated by queueing and
  prompt processing.
- **TPS — tokens per second** (or inter-token latency): how fast the text flows afterwards.

$$\text{total time} \approx \text{TTFT} + \frac{\text{output tokens}}{\text{TPS}}$$

A 500-token answer at 50 tokens/s takes 10 s in total. Without streaming, the user stares at a spinner
for 10 s; with streaming they start reading after ~0.5 s. Same compute, completely different product.
Streaming also lets users **cancel** bad answers early, saving compute.

## An SSE token-streaming endpoint

Typically your FastAPI service sits between clients and a model backend (an inference server such as vLLM
or TGI, or a hosted model API). The work is I/O-bound — exactly what async is for.

```python
import json
from collections.abc import AsyncIterator
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

router = APIRouter(prefix="/v1", tags=["chat"])

class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str = Field(min_length=1, max_length=32_000)

class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(min_length=1, max_length=100)
    max_tokens: int = Field(512, ge=1, le=4096)            # ALWAYS cap output length
    temperature: float = Field(0.7, ge=0, le=2)
    stream: bool = True

def sse(data: dict | str, event: str | None = None) -> str:
    payload = data if isinstance(data, str) else json.dumps(data, ensure_ascii=False)
    head = f"event: {event}\n" if event else ""
    return f"{head}data: {payload}\n\n"

@router.post("/chat")
async def chat(req: ChatRequest, request: Request, user: CurrentUser, llm: LLMDep):
    await enforce_token_budget(user, req)                  # fail BEFORE streaming starts -> real 4xx

    async def event_stream() -> AsyncIterator[str]:
        usage = {"completion_tokens": 0}
        try:
            async for token in llm.stream(req.messages, max_tokens=req.max_tokens,
                                          temperature=req.temperature):
                usage["completion_tokens"] += 1
                yield sse({"text": token}, event="token")
            yield sse({"usage": usage, "finish_reason": "stop"}, event="done")
        except asyncio.CancelledError:
            raise                                          # client disconnected: let cancellation propagate
        except Exception:
            logger.exception("generation failed")
            yield sse({"message": "generation failed"}, event="error")   # status is already 200
        finally:
            await record_usage(user, usage)                # runs on completion, error AND disconnect

    return StreamingResponse(event_stream(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
```

(With recent FastAPI you can instead declare `response_class=EventSourceResponse` and `yield
ServerSentEvent(...)` objects directly from the endpoint — see the streaming lesson. The mechanics below
are identical.)

Design decisions embedded in that code:

1. **Validate and authorise before the first byte.** Once streaming starts the status is `200`; anything
   you can reject (bad input, no quota, unknown model) should be rejected *before* returning the
   response, as a proper 4xx.
2. **In-band errors.** After headers are sent, failures become an `error` event, and the stream ends.
   Clients must treat "stream ended without a `done` event" as failure.
3. **An explicit terminator** (`done` event, or OpenAI-style `data: [DONE]`) distinguishes completion from
   a dropped connection.
4. **Cancellation propagates.** When the client disconnects, Starlette cancels the generator; because
   `llm.stream` is being awaited inside it, the upstream request is cancelled too and the GPU stops
   generating. Never swallow `CancelledError`.
5. **`finally` for accounting.** Usage metering and cleanup must run on every exit path.
6. **`max_tokens` is capped** by the schema: output length is the main cost and latency driver.

### The upstream side

Consuming a streaming backend with `httpx` (one shared `AsyncClient` created in the lifespan):

```python
async def stream(self, messages, **params) -> AsyncIterator[str]:
    async with self.http.stream("POST", f"{self.base_url}/v1/chat/completions",
                                json={"messages": messages, "stream": True, **params},
                                timeout=httpx.Timeout(connect=2, read=60, write=10, pool=2)) as r:
        r.raise_for_status()
        async for line in r.aiter_lines():
            if not line.startswith("data: "):
                continue                                   # skip comments / keep-alives / blanks
            data = line[len("data: "):]
            if data == "[DONE]":
                return
            delta = json.loads(data)["choices"][0]["delta"].get("content")
            if delta:
                yield delta
```

Leaving the `async with` block — normally or through cancellation — closes the upstream connection,
which is what stops generation.

### End-to-end simulation

Everything above, runnable: a fake model, the SSE endpoint logic, a client that disconnects mid-stream,
and proof that generation stops.

```python-run
import asyncio, json, time

generated = 0

async def fake_llm(prompt, max_tokens):
    """Stands in for the model backend: ~30 ms to first token, then ~10 ms per token."""
    global generated
    words = ("FastAPI streams tokens with server sent events so users see text immediately "
             "instead of waiting for the full answer").split()
    await asyncio.sleep(0.03)
    for w in words[:max_tokens]:
        generated += 1
        yield w + " "
        await asyncio.sleep(0.01)

def sse(data, event=None):
    return (f"event: {event}\n" if event else "") + f"data: {json.dumps(data)}\n\n"

async def chat_endpoint(prompt, max_tokens=64):
    n = 0
    try:
        async for tok in fake_llm(prompt, max_tokens):
            n += 1
            yield sse({"text": tok}, "token")
        yield sse({"finish_reason": "stop", "completion_tokens": n}, "done")
    finally:
        print(f"   [server] stream closed after {n} tokens (usage recorded)")

async def client(read_limit=None):
    t0, ttft, text, events = time.perf_counter(), None, "", 0
    stream = chat_endpoint("explain streaming")
    async for frame in stream:
        lines = dict(l.split(": ", 1) for l in frame.strip().split("\n"))
        if lines.get("event") == "token":
            ttft = ttft or time.perf_counter() - t0
            text += json.loads(lines["data"])["text"]
            events += 1
            if read_limit and events >= read_limit:
                await stream.aclose()            # client disconnects -> generator is closed
                break
    total = time.perf_counter() - t0
    return ttft, total, events, text

ttft, total, n, text = await client()
print(f"full stream : TTFT {ttft*1000:.0f} ms, total {total*1000:.0f} ms, {n} tokens, "
      f"{n / (total - ttft):.0f} tok/s")
print("             ", text.strip())
before = generated
ttft, total, n, text = await client(read_limit=5)
print(f"disconnected: read {n} tokens; model generated only {generated - before} more "
      f"(not the full answer) -> compute saved")
```

### LLM-specific protections

- **Rate limit by tokens, not just requests**: budgets per user/tenant per minute and per day; count
  prompt + completion tokens (token bucket where `cost` = tokens).
- **Concurrency limits**: a semaphore per backend; streams are long-lived, so a small number of slow
  clients can occupy all slots — set a maximum stream duration and idle timeouts.
- **Backpressure**: if the client reads slowly, `yield` naturally blocks at the socket; don't buffer whole
  answers in memory "to be safe".
- **Prompt and output handling**: treat model output as untrusted (escape before rendering HTML; never
  `eval`; validate tool-call arguments with Pydantic); log prompts carefully — they contain user data.
- **Structured output**: when you need JSON from the model, validate it with a Pydantic model
  (`model_validate_json`) and retry or repair on failure.
- **Observability**: record TTFT, tokens/s, prompt/completion tokens, finish reason, model version and
  cost per request.

## Versioning

Two things version independently:

| | API version | Model version |
|---|---|---|
| What changes | request/response *schema*, semantics | weights, prompts, preprocessing |
| Who cares | client developers (breaking changes) | product/quality owners (behaviour changes) |
| Typical identifier | `/v1`, `/v2` in the path | `2025-01-15`, `sentiment-3.2.0`, a registry hash |
| Rollout | long deprecation windows | canary, shadow, A/B, instant rollback |

### API versions with routers

```python
# app/api/v1/predict.py
router = APIRouter(prefix="/v1", tags=["v1"])

@router.post("/predict", response_model=PredictResponseV1)
def predict_v1(req: PredictRequestV1, models: RegistryDep): ...

# app/api/v2/predict.py - breaking change: batch input, richer output
router = APIRouter(prefix="/v2", tags=["v2"])

@router.post("/predict", response_model=PredictResponseV2)
def predict_v2(req: PredictRequestV2, models: RegistryDep): ...

# main.py
app.include_router(v1.router, deprecated=True)     # still served; greyed out in docs
app.include_router(v2.router)
```

Keep the versions thin: both call the same service layer; only schemas and adapters differ. Deprecate
with `deprecated=True`, `Deprecation`/`Sunset` response headers, usage dashboards per version, and removal
only when traffic reaches zero.

### Model versions

Let clients pin a model or take the default, and always report what was used:

```python
class ModelRegistry:
    def __init__(self):
        self.models: dict[str, Model] = {}
        self.default: str | None = None

    def get(self, version: str | None) -> Model:
        key = version or self.default
        if key not in self.models:
            raise Missing(f"model version {version!r} not available")
        return self.models[key]

@router.post("/v2/models/{name}/predict")
def predict(name: str, req: PredictRequestV2, registry: RegistryDep,
            version: Annotated[str | None, Query(pattern=r"^[\w.\-]+$")] = None):
    model = registry.get(version)
    return PredictResponseV2(predictions=model.predict(req.instances), model_version=model.version)
```

Rollout strategies:

- **Shadow**: the new model receives a copy of live traffic; its outputs are logged, not returned.
- **Canary**: route a small percentage to the new version; watch metrics; ramp up.
- **A/B**: split by user to compare business outcomes.
- **Blue/green**: switch all traffic at once with the old version on standby for instant rollback.

Canary routing should be **sticky** — the same user gets the same model every time — which means hashing,
not random choice:

```python-run
import hashlib
from collections import Counter

def pick_model(user_id: str, canary_percent: int, stable="2025-01-15", canary="2025-03-01"):
    """Deterministic bucketing: a user always lands in the same bucket (0-99)."""
    bucket = int(hashlib.sha256(user_id.encode()).hexdigest(), 16) % 100
    return canary if bucket < canary_percent else stable

users = [f"user-{i}" for i in range(10_000)]
for pct in (0, 5, 25, 100):
    share = Counter(pick_model(u, pct) for u in users)
    print(f"canary {pct:>3}% ->", dict(share))

print("sticky:", {pick_model("user-42", 25) for _ in range(5)})     # one value: always the same
# Ramping 5% -> 25% only moves users from stable to canary, never back:
moved_back = sum(pick_model(u, 5) == "2025-03-01" and pick_model(u, 25) != "2025-03-01" for u in users)
print("users flipped back when ramping up:", moved_back)
```

For LLM applications the "model version" includes the **prompt template** and decoding parameters: a
prompt edit can change behaviour as much as new weights. Version prompts in code, record the prompt
version with each response, and evaluate changes against a regression set before rollout.

> [!INTERVIEW]
> "Design an endpoint that streams LLM responses." — `POST /v1/chat` with a validated request (bounded
> messages, capped `max_tokens`); authenticate, check token budget and reject problems *before* streaming.
> Return `text/event-stream`: an async generator relays tokens from the backend as SSE events, ends with
> an explicit `done` event, reports failures as in-band `error` events, and uses `try/finally` for usage
> accounting. Client disconnects cancel the generator and therefore the upstream call. Disable proxy
> buffering, send keep-alives, bound concurrent streams, measure TTFT and tokens/s, and include the
> model/prompt version in the final event.

## Pitfalls

- Starting the stream, then discovering the user is over quota (the client already has a 200).
- Swallowing `CancelledError`, so abandoned generations keep burning GPU.
- No output cap; no per-token rate limits.
- Buffering the full completion server-side before sending ("fake streaming").
- Holding a DB session/transaction open for the whole stream.
- Changing prompts or models in place with no version identifier in responses or logs.
- Random (non-sticky) canary assignment — users see inconsistent behaviour and metrics blur.

## Summary

- For generative models optimise TTFT and tokens/s; streaming transforms perceived latency and enables
  cancellation.
- SSE endpoint: validate first, stream tokens, explicit terminator, in-band errors, `finally` for
  accounting, cancellation propagated upstream.
- Protect with token-based limits, capped output, bounded concurrent streams.
- Version the API (routers, deprecation) and the model/prompt (registry, pinned or default) separately;
  roll out with shadow/canary/A-B using sticky hashing; always return the version used.

```quiz
[
  {"q": "What does TTFT measure?", "options": ["Total generation time", "Time from request until the first token is received", "Tokens per second", "Time to load the model"], "answer": 1,
   "explain": "Time to first token governs perceived responsiveness; total time also depends on output length and tokens/s."},
  {"q": "Why must quota and validation checks happen before returning the StreamingResponse?", "options": ["Streaming disables dependencies", "Once streaming starts the 200 status and headers are already sent, so you can no longer return a proper 4xx", "Generators can't raise", "SSE forbids errors"], "answer": 1,
   "explain": "Errors after the first byte can only be signalled in-band; reject what you can up front."},
  {"q": "How does a streaming client distinguish a completed answer from a dropped connection?", "options": ["By the status code", "By an explicit terminal event such as 'done' or [DONE]", "It can't", "By Content-Length"], "answer": 1,
   "explain": "Streams have no Content-Length; an explicit terminator marks successful completion."},
  {"q": "What should happen upstream when the client disconnects mid-stream?", "options": ["Finish generating and cache it", "The generator is cancelled and the upstream generation request is closed to stop wasting compute", "Restart the request", "Nothing"], "answer": 1,
   "explain": "Propagating cancellation frees GPU capacity and avoids paying for unread tokens."},
  {"q": "Why rate-limit LLM endpoints by tokens rather than only by requests?", "options": ["Tokens are easier to count", "Cost and load scale with prompt and output tokens; one request can be 100x more expensive than another", "HTTP requires it", "Requests can't be counted when streaming"], "answer": 1,
   "explain": "Request counts ignore size; token budgets track actual resource consumption."},
  {"q": "Why should canary assignment hash the user ID instead of choosing randomly per request?", "options": ["Hashing is faster", "Sticky assignment gives each user consistent behaviour and clean comparisons", "Random numbers are insecure", "Load balancers require it"], "answer": 1,
   "explain": "Deterministic bucketing keeps a user on one version and makes ramp-ups monotonic."},
  {"q": "A breaking change to the response schema is needed. Best approach?", "options": ["Change /v1 in place", "Add /v2 via a new router, keep /v1 running and marked deprecated until traffic migrates", "Return both schemas merged", "Disable docs"], "answer": 1,
   "explain": "Versioned routers let old clients keep working during a deprecation window."}
]
```

> **Source:** Lubanovic, *FastAPI*, ch. 14 "Databases, Data Science, and a Little AI" (Data Science and AI), ch. 15 "Files" (StreamingResponse), ch. 8 "Web Layer" (RESTful API Design); https://fastapi.tiangolo.com/tutorial/server-sent-events/, /advanced/custom-response/, /tutorial/bigger-applications/, /tutorial/path-operation-configuration/
