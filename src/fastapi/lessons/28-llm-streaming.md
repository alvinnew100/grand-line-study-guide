# Streaming LLM output and versioned endpoints

> **Before this lesson:** you should know `StreamingResponse`, the SSE format and how a client
> disconnect cancels a stream ([lesson 24](#/lesson/fastapi/websockets-streaming)), how a model is
> loaded and served ([lesson 27](#/lesson/fastapi/serving-models)), `APIRouter` and
> `include_router` ([lesson 14](#/lesson/fastapi/routers)), token-bucket rate limiting
> ([lesson 20](#/lesson/fastapi/authz-cors)), and `asyncio.CancelledError`
> ([lesson 12](#/lesson/fastapi/async-fundamentals)).

## In plain words

A **large language model** (LLM) is a model trained on huge amounts of text that continues a piece
of text: given a question, it writes an answer. It does so one **token** at a time, where a token is
a word or a piece of a word. Each new token depends on all the ones before it, so the answer cannot be
produced all at once; it grows, token by token, over several seconds.

That changes what "serving a model" feels like. A classifier answers in 20 milliseconds. An LLM may
need 20 *seconds* to finish a long answer, but it can show the first words almost immediately. Think
of two restaurants. In the first, nothing arrives until every course is ready, and you sit in front of
an empty table for forty minutes. In the second, the bread comes at once, then the starter, then the
main course. The total time is the same; the experience is completely different. Streaming is the
second restaurant, and it is the core serving pattern for LLMs.

The second half of the lesson is about **versioning**. Models are retrained, prompts are edited,
response formats grow new fields. Clients that were built against last year's API must keep working,
and when an answer looks wrong you must be able to say which model and which prompt produced it.

Why this matters for a job: "Design an endpoint that streams LLM responses" and "How would you roll
out a new model safely?" are standard questions for anyone building AI products, and the details here
(validate before the first byte, propagate cancellation, sticky canaries) are what separate a good
answer from a vague one.

## Latency for generative models

Two numbers replace the single "request latency" of ordinary endpoints:

- **TTFT, time to first token**: how long until the user sees *something*. It is dominated by waiting
  in the server's queue and by processing the prompt.
- **TPS, tokens per second** (or its inverse, the *inter-token latency*): how fast the text flows
  after that.

$$\text{total time} \approx \text{TTFT} + \frac{\text{output tokens}}{\text{TPS}}$$

The formula in code, for a model that needs half a second to start and then produces 50 tokens a
second:

```python-run
def total_time(ttft_s, tokens_per_s, output_tokens):
    """Time until the whole answer has arrived."""
    return ttft_s + output_tokens / tokens_per_s

TTFT, TPS = 0.5, 50                       # half a second to start, then 50 tokens per second
for n in (20, 200, 500, 2000):
    print(f"{n:5} tokens | no streaming: blank screen for {total_time(TTFT, TPS, n):5.1f} s"
          f" | streaming: text appears after {TTFT} s, finishes at {total_time(TTFT, TPS, n):5.1f} s")
```

`total_time` is the formula above. The loop prints four answer lengths. A 500-token answer finishes
after 10.5 seconds either way; without streaming the user stares at a spinner for all 10.5 of them,
with streaming they start reading after half a second. For 2,000 tokens the gap is 40 seconds of
nothing versus half a second. Same computation, a different product. Streaming also lets users
**cancel** an answer that is going in the wrong direction, which saves the computation for the rest
of it.

## An SSE token-streaming endpoint

Usually your FastAPI service does not run the LLM itself. It sits between the clients and a **model
backend**: an inference server such as vLLM or TGI running on GPUs, or a hosted model API. Your
service checks who is calling, validates the request, applies limits, forwards the request, and relays
the tokens back. That work is waiting on the network, I/O-bound, which is exactly what async is for.

```python
import asyncio, json
from collections.abc import AsyncIterator
from typing import Literal
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

Reading it from the top:

- `ChatMessage` is one turn of a conversation. The `role` says who wrote it: `system` (instructions
  from the application, such as "you are a helpful assistant for a bank"), `user` (the person) or
  `assistant` (earlier replies of the model). The content is limited to 32,000 characters.
- `ChatRequest` holds up to 100 messages and the generation settings. `max_tokens` caps the answer's
  length; it defaults to 512 and can never exceed 4,096. `temperature` controls randomness: 0 makes
  the model pick the most likely token every time, higher values make it more varied.
- `sse(...)` formats one Server-Sent Event, as in lesson 24. `ensure_ascii=False` keeps characters
  such as `é` readable instead of escaping them.
- The endpoint first calls `enforce_token_budget(user, req)`, a function of your own that raises an
  `HTTPException` (for example `429`) if the user has used up their allowance. This happens *before*
  any streaming, so the client gets a real error status.
- `event_stream()` is the async generator that produces the body. For each token arriving from
  `llm.stream(...)` it counts the token and yields a `token` event. When the model is finished it
  yields a `done` event with the usage numbers.
- `except asyncio.CancelledError: raise` lets a cancellation (the client went away) pass straight
  through. `except Exception` catches real failures and turns them into an `error` event.
- `finally:` runs on every way out (normal end, error or disconnect) and records how many tokens were
  used, for billing and limits.
- The `StreamingResponse` marks the body as an event stream and switches off caching and proxy
  buffering.

(With recent FastAPI you can instead declare `response_class=EventSourceResponse` and `yield
ServerSentEvent(...)` objects directly from the endpoint, as lesson 24 showed. The design below is
identical either way.)

The design decisions in that code:

1. **Validate and authorise before the first byte.** Once streaming starts, the status is `200`.
   Anything you can reject (bad input, no quota left, an unknown model) should be rejected *before*
   returning the response, as a proper `4xx`. Pydantic validation and dependencies such as
   `CurrentUser` already run before the endpoint body, which helps.
2. **In-band errors.** After the headers are sent, a failure can only be reported as an `error` event,
   after which the stream ends. Clients must treat "the stream ended without a `done` event" as a
   failure.
3. **An explicit terminator** (a `done` event, or the OpenAI-style `data: [DONE]`) is how a client
   tells a complete answer from a dropped connection; a stream has no `Content-Length` to compare
   against.
4. **Cancellation propagates.** When the client disconnects, Starlette cancels the generator.
   Because `llm.stream(...)` is being awaited inside it, the cancellation reaches the upstream request
   too, the connection to the model backend closes, and the GPU stops generating. Never swallow
   `CancelledError`: catching it and carrying on would keep the model generating for nobody.
5. **`finally` for accounting.** Usage metering and clean-up must run on every exit path.
6. **`max_tokens` is capped** by the schema. Output length is the main driver of both cost and
   latency.

The same endpoint with its outside pieces replaced by stand-ins runs in your browser: `fake_llm`
plays the model, a fixed `BUDGET` plays the token budget, and the user and model dependencies are
left out.

```fastapi-run method=POST path=/v1/chat
import asyncio, json
from typing import Literal
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field

app = FastAPI()
BUDGET = 40                                  # tokens this user may still spend

class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str = Field(min_length=1, max_length=32_000)

class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(min_length=1, max_length=100)
    max_tokens: int = Field(16, ge=1, le=4096)

async def fake_llm(messages, max_tokens):
    words = ("Streaming lets people start reading while the model "
             "is still writing the rest").split()
    for word in words[:max_tokens]:
        await asyncio.sleep(0.15)                    # one token every 150 ms
        yield word + " "

def sse(data, event=None):
    return (f"event: {event}\n" if event else "") + f"data: {json.dumps(data)}\n\n"

@app.post("/v1/chat")
async def chat(req: ChatRequest):
    if req.max_tokens > BUDGET:              # fail BEFORE streaming starts -> real 4xx
        raise HTTPException(429, f"max_tokens is over your budget of {BUDGET}")

    async def event_stream():
        n = 0
        try:
            async for token in fake_llm(req.messages, req.max_tokens):
                n += 1
                yield sse({"text": token}, event="token")
            yield sse({"completion_tokens": n, "finish_reason": "stop"}, event="done")
        finally:
            print(f"[server] stream closed after {n} tokens (usage recorded)")

    return StreamingResponse(event_stream(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

client = TestClient(app)
body = {"messages": [{"role": "user", "content": "Why stream?"}], "max_tokens": 5}
with client.stream("POST", "/v1/chat", json=body) as r:
    kinds = [line for line in r.iter_lines() if line.startswith("event:")]
print(r.status_code, kinds)
print(client.post("/v1/chat", json={**body, "max_tokens": 100}).status_code)
```

The test at the bottom asks for 5 tokens. The server's `finally` line comes first ("stream closed
after 5 tokens"), then the status `200` and the event types in order: five `event: token` lines and
one `event: done`. Asking for 100 tokens is over the budget, so that request is refused with `429`
before a single byte of stream is sent.

Now press Send in the panel. The request body was filled in from the `ChatRequest` schema, with
`max_tokens` at its default of 16. Each event appears as the app yields it, 150 ms apart: 13 `token`
events (the sentence has only 13 words) and a final `done` event reporting `"completion_tokens": 13`.
Then:

- Send again and press **Stop** after a few tokens. The panel hangs up, as a closed browser tab
  would; Starlette cancels the generator, and the output above the panel shows the `finally` line
  with the number of tokens actually produced. Nothing is generated for nobody.
- Set `max_tokens` to 50 in the body and send: `429` with the reason in the JSON, and no stream at
  all, because the check runs before the response starts.

### The upstream side

Most model backends, hosted or self-run, offer an OpenAI-compatible HTTP API that itself streams SSE.
Reading it with `httpx`, using one shared `AsyncClient` created in the lifespan:

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

- `self.http.stream("POST", ...)` sends the request and gives back the response *before* the body has
  arrived, so it can be read piece by piece. `"stream": True` asks the backend to stream.
- The timeout allows 60 seconds between pieces of data (`read`), because generation can pause; the
  other limits stay short (lesson 26).
- `r.raise_for_status()` turns an error status from the backend into an exception, which happens
  before your own stream has started, so your endpoint can still answer with a proper error.
- `async for line in r.aiter_lines()` reads the body line by line as it arrives. Lines that are not
  `data:` lines (comments, blank separators) are skipped, `[DONE]` ends the loop, and every other
  line is JSON whose `choices[0].delta.content` holds the next piece of text.
- `yield delta` passes each piece on to the endpoint's generator.

Leaving the `async with` block, normally or through cancellation, closes the connection to the
backend, and closing that connection is what stops the generation.

### End-to-end simulation

Everything above, runnable: a fake model, the endpoint logic, a client that disconnects part-way, and
proof that generation stops.

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

The parts:

- `fake_llm` plays the backend: it waits about 30 ms (the TTFT), then yields one word every 10 ms.
  The global `generated` counts how many tokens the "GPU" actually produced.
- `chat_endpoint` is the server logic: a `token` event per word, a `done` event at the end, and a
  `finally` block that reports how many tokens were sent.
- `client(read_limit)` reads the stream, splits each event into its fields, measures the TTFT, and
  rebuilds the text. With a `read_limit` it stops after that many tokens and calls
  `stream.aclose()`, which is what happens on the server side when a browser tab is closed: the
  generator is closed at its current `yield`.

The first run reads everything: it prints the server's `finally` line ("stream closed after 19
tokens"), then a TTFT of a few tens of milliseconds, a total of roughly a third of a second, 19
tokens, a rate of a few dozen tokens per second (the exact timings vary), and the full sentence. The
second run disconnects after 5 tokens. The server's `finally` still runs ("closed after 5 tokens"),
and the counter shows the model generated only 5 more tokens, not 19: closing the stream stopped
the generation upstream. In a real service those are GPU-seconds, and money, saved.

### LLM-specific protections

- **Rate-limit by tokens, not only by requests.** One request may cost a hundred times more than
  another. Give each user or tenant a budget per minute and per day, counting prompt tokens plus
  completion tokens: a token bucket (lesson 20) where each request's cost is its number of tokens. A
  common approach reserves `max_tokens` before streaming and refunds what was not used afterwards;
  the problem *LLM Token Budget with Reservations* builds exactly that.
- **Concurrency limits.** Use a semaphore per backend. Streams are long-lived, so a handful of slow
  clients can occupy every slot; set a maximum stream duration and idle timeouts.
- **Backpressure.** If a client reads slowly, `yield` naturally waits at the network socket. Do not
  collect whole answers in memory "to be safe".
- **Treat prompts and outputs with care.** Model output is untrusted text: escape it before
  rendering it as HTML, never pass it to `eval`, and validate the arguments of any tool call the
  model requests with Pydantic. Users can also write prompts designed to make the model ignore its
  instructions, which is called **prompt injection**, so never let model output alone authorise an
  action. Prompts contain user data, so log them carefully.
- **Structured output.** When you need JSON from the model, validate it with a Pydantic model
  (`model_validate_json`) and retry or repair on failure.
- **Observability** (lesson 26): record TTFT, tokens per second, prompt and completion tokens, the
  **finish reason** (why generation stopped: the model finished, `max_tokens` was reached, or an
  error), the model version and the cost per request.

## Versioning

Two different things change over time, and they are versioned separately:

| | API version | Model version |
|---|---|---|
| What changes | the request and response *schema*, their meaning | weights, prompts, preprocessing |
| Who cares | client developers (breaking changes) | product and quality owners (behaviour changes) |
| Typical identifier | `/v1`, `/v2` in the path | `2025-01-15`, `sentiment-3.2.0`, a registry hash |
| Rollout | long deprecation windows | canary, shadow, A/B, instant rollback |

A **breaking change** is one that makes existing clients fail: removing or renaming a field,
changing a type, changing what a value means. Adding an optional field is not breaking. To
**deprecate** something is to announce that it will be removed, while it still works.

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

- Each version lives in its own module with its own router and its own prefix, so the two
  `/predict` endpoints become `/v1/predict` and `/v2/predict`.
- Each has its own request and response schemas (`...V1`, `...V2`); that is where the breaking change
  lives.
- `include_router(v1.router, deprecated=True)` keeps serving v1 but marks all its routes as deprecated
  in the OpenAPI documentation, where they appear crossed out.

Keep the versions thin: both should call the same service layer (lesson 15), with only the schemas
and small adapters differing. Deprecate in steps: `deprecated=True`, `Deprecation` and `Sunset`
response headers (the latter announces the date the version will stop working), a dashboard of
traffic per version, and removal only when that traffic reaches zero.

### Model versions

Let clients pin a model version or take the default, and always report which one was used:

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

- `ModelRegistry` holds every loaded model by version string, plus which one is the default.
- `get(version)` uses the requested version or, if none was given, the default. An unknown version
  raises the domain exception `Missing` (lesson 15), which an exception handler turns into `404`.
- The endpoint takes an optional `version` query parameter. `pattern=r"^[\w.\-]+$"` allows only
  letters, digits, underscores, dots and hyphens, so nothing strange reaches the registry or the
  logs.
- The response always includes `model_version`.

Ways to roll out a new model:

- **Shadow**: the new model receives a copy of live traffic; its outputs are logged and compared, but
  never returned to users.
- **Canary**: send a small percentage of traffic to the new version, watch the metrics, and increase
  the percentage step by step. (Named after the canaries miners once carried to detect gas early.)
- **A/B test**: split users into groups to compare business outcomes, such as clicks or purchases.
- **Blue/green**: run the new version alongside the old, switch all traffic at once, and keep the old
  one on standby for instant rollback.

Canary routing should be **sticky**: the same user should get the same model every time, otherwise
they see inconsistent behaviour and the comparison between versions is blurred. That calls for hashing,
not a random choice per request:

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

- `pick_model` hashes the user ID with SHA-256, turns the hex digest into a big integer, and takes it
  modulo 100 to get a **bucket** between 0 and 99. A good hash spreads users evenly over the
  buckets.
- Users whose bucket is below `canary_percent` get the canary; everyone else gets the stable version.
- `Counter` counts how many of 10,000 users land on each model for four percentages.

The output shows 0% sending everyone to stable, 5% sending about 500 users (504 exactly) to the
canary, 25% about 2,500, and 100% everyone. The set built from five calls for `user-42` contains a
single value: the assignment never changes. And when the percentage is raised from 5 to 25, zero
users flip back from canary to stable: raising the threshold only adds buckets, so a ramp-up moves
users in one direction only. Random assignment would have none of these properties.

For LLM applications the "model version" also includes the **prompt template** (the fixed
instructions wrapped around the user's input) and the decoding parameters such as temperature. A
one-line edit to a prompt can change behaviour as much as new weights. Keep prompts in version
control, record the prompt version with every response, and test changes against a fixed set of
example questions with known good answers (a **regression set**) before rolling them out.

> [!INTERVIEW]
> "Design an endpoint that streams LLM responses." — `POST /v1/chat` with a validated request (bounded
> messages, capped `max_tokens`); authenticate, check token budget and reject problems *before* streaming.
> Return `text/event-stream`: an async generator relays tokens from the backend as SSE events, ends with
> an explicit `done` event, reports failures as in-band `error` events, and uses `try/finally` for usage
> accounting. Client disconnects cancel the generator and therefore the upstream call. Disable proxy
> buffering, send keep-alives, bound concurrent streams, measure TTFT and tokens/s, and include the
> model/prompt version in the final event.

## Pitfalls

- Starting the stream, then discovering the user is over quota (the client already has a `200`).
- Swallowing `CancelledError`, so abandoned generations keep burning GPU time.
- No output cap; no per-token rate limits.
- Collecting the full answer on the server before sending it ("fake streaming").
- Holding a database session or transaction open for the whole stream.
- Changing prompts or models in place with no version identifier in responses or logs.
- Random (non-sticky) canary assignment: users see inconsistent behaviour and metrics blur.

## Summary

- For generative models, optimise TTFT and tokens per second; streaming transforms perceived latency
  and makes cancellation possible.
- SSE endpoint: validate first, stream tokens, end with an explicit terminator, report errors
  in-band, account in `finally`, and let cancellation propagate upstream.
- Protect with token-based limits, capped output and bounded concurrent streams.
- Version the API (routers, deprecation) and the model and prompt (registry, pinned or default)
  separately; roll out with shadow, canary or A/B using sticky hashing; always return the version
  used.

## Glossary

- **LLM (large language model)** — a model that generates text, one token at a time.
- **Token** — a word or piece of a word, the unit an LLM reads and writes.
- **TTFT (time to first token)** — how long until the first piece of the answer arrives.
- **TPS (tokens per second)** — how fast the answer flows after that.
- **Model backend / inference server** — the service that runs the LLM, such as vLLM or a hosted API.
- **Role (system / user / assistant)** — who wrote a message in a chat conversation.
- **`max_tokens` / temperature** — the cap on answer length / how random token choices are.
- **Terminator** — the final event (`done` or `[DONE]`) marking a complete answer.
- **Finish reason** — why generation stopped: done, length limit or error.
- **Prompt injection** — input crafted to make a model ignore its instructions.
- **Breaking change** — a change that makes existing clients fail.
- **Deprecate / `Sunset` header** — announce future removal / the header giving the removal date.
- **Model registry** — the store of model versions and which one is the default.
- **Shadow / canary / A/B / blue-green** — ways of exposing a new version gradually or safely.
- **Sticky assignment / bucket** — a user always gets the same variant / the hash-derived number
  (0–99) that decides which.
- **Prompt template** — the fixed instructions wrapped around the user's input.
- **Regression set** — fixed examples with known good answers, used to test changes.

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
   "explain": "Versioned routers let old clients keep working during a deprecation window."},
  {"q": "A model starts answering after 0.5 s and then produces 50 tokens per second. Roughly when does a 500-token answer finish?", "options": ["0.5 s", "10.5 s", "25 s", "500 s"], "answer": 1,
   "explain": "Total time is about TTFT + tokens / TPS = 0.5 + 500/50 = 10.5 seconds; streaming changes when text first appears, not when it ends."}
]
```

> **Source:** Lubanovic, *FastAPI*, ch. 14 "Databases, Data Science, and a Little AI" (Data Science and AI), ch. 15 "Files" (StreamingResponse), ch. 8 "Web Layer" (RESTful API Design); https://fastapi.tiangolo.com/tutorial/server-sent-events/, /advanced/custom-response/, /tutorial/bigger-applications/, /tutorial/path-operation-configuration/
