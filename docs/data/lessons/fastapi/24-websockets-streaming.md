# WebSockets, streaming and Server-Sent Events

Classic HTTP is request → complete response. Three techniques break that mould, and all three matter for
modern APIs — especially LLM applications where users expect to watch the answer appear token by token:

| Technique | Direction | Transport | Typical use |
|---|---|---|---|
| **StreamingResponse** | server → client, one response | chunked HTTP body | large downloads, NDJSON feeds |
| **Server-Sent Events (SSE)** | server → client, event stream | `text/event-stream` over HTTP | notifications, progress, **LLM token streaming** |
| **WebSocket** | bidirectional, persistent | upgraded TCP connection (`ws://`, `wss://`) | chat, collaboration, games, live control |

All three depend on ASGI's message-based design (lesson 3): the app can keep sending `http.response.body`
chunks or WebSocket frames for as long as the connection lives.

## StreamingResponse

Return a `StreamingResponse` wrapping any iterator or async iterator of `str`/`bytes`:

```python
import asyncio, json
from fastapi import FastAPI
from fastapi.responses import StreamingResponse

app = FastAPI()

async def ndjson_feed():
    for i in range(5):
        yield json.dumps({"seq": i}) + "\n"       # newline-delimited JSON
        await asyncio.sleep(0.5)

@app.get("/feed")
async def feed():
    return StreamingResponse(ndjson_feed(), media_type="application/x-ndjson")
```

No `Content-Length` is sent; HTTP/1.1 uses chunked transfer encoding. Consequences:

- The **status code and headers go out before the first chunk**. If something fails mid-stream you can't
  switch to a 500 — signal errors *in-band* (a final error event) and validate everything you can before
  starting to stream.
- An async generator runs on the event loop — no blocking calls inside. A sync generator is iterated in
  the thread pool.
- When the client disconnects, Starlette cancels the generator (`CancelledError`/`GeneratorExit` at the
  `yield`). Use `try/finally` to release resources — and to **stop paying for LLM tokens nobody is
  reading**.

## Server-Sent Events

SSE is a tiny text protocol on top of a streaming response with `Content-Type: text/event-stream`. Each
event is a block of `field: value` lines ended by a blank line:

```text
event: token
id: 7
data: {"text": " world"}

: this is a comment, often used as a keep-alive ping

data: [DONE]

```

Fields: `data` (payload; repeated `data:` lines are joined with `\n`), `event` (type, default
`message`), `id` (the browser remembers it and sends `Last-Event-ID` when reconnecting), `retry`
(reconnect delay in ms). In the browser, `new EventSource(url)` parses the stream and **reconnects
automatically**. Why SSE is the default for LLM streaming: it's plain HTTP (works through proxies, load
balancers, auth middleware, HTTP/2), one-directional (which is all token streaming needs), and trivial to
consume.

### SSE in FastAPI

Recent FastAPI versions (0.135+) ship first-class support — yield from the endpoint and declare
`EventSourceResponse`:

```python
from collections.abc import AsyncIterable
from fastapi import FastAPI
from fastapi.sse import EventSourceResponse, ServerSentEvent

app = FastAPI()

@app.get("/items/stream", response_class=EventSourceResponse)
async def stream_items() -> AsyncIterable[Item]:
    for item in items:
        yield item                           # serialised to JSON in the data: field

@app.get("/chat/stream", response_class=EventSourceResponse)
async def chat_stream(prompt: str) -> AsyncIterable[ServerSentEvent]:
    i = 0
    async for token in llm.generate(prompt):
        i += 1
        yield ServerSentEvent(data={"text": token}, event="token", id=str(i))
    yield ServerSentEvent(raw_data="[DONE]")        # raw_data: sent without JSON encoding
```

`ServerSentEvent` carries `data` (JSON-encoded), `raw_data` (verbatim string), `event`, `id`, `retry`,
`comment`. FastAPI sets `Cache-Control: no-cache` and `X-Accel-Buffering: no` (stops nginx buffering the
stream) and sends a keep-alive ping comment when the stream is idle for ~15 seconds so proxies don't drop
the connection.

On older versions (or for full control) you format the frames yourself — it's just text:

```python
def sse(data: str, event: str | None = None, id: str | None = None) -> str:
    lines = []
    if event: lines.append(f"event: {event}")
    if id:    lines.append(f"id: {id}")
    lines += [f"data: {line}" for line in data.split("\n")]     # multi-line data = several data: lines
    return "\n".join(lines) + "\n\n"

@app.post("/v1/chat")
async def chat(req: ChatRequest):
    async def gen():
        try:
            async for token in llm.generate(req.prompt):
                yield sse(json.dumps({"text": token}), event="token")
            yield sse("[DONE]")
        except Exception:
            logger.exception("generation failed")
            yield sse(json.dumps({"message": "generation failed"}), event="error")   # in-band error
    return StreamingResponse(gen(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
```

(`EventSource` in browsers only does `GET`; LLM APIs commonly use `POST` + SSE and clients read the
stream with `fetch`. Both are fine.)

Produce and consume a stream end to end:

```python-run
import asyncio, json

def sse(data, event=None, id=None):
    lines = ([f"event: {event}"] if event else []) + ([f"id: {id}"] if id else [])
    lines += [f"data: {line}" for line in data.split("\n")]
    return "\n".join(lines) + "\n\n"

async def fake_llm(prompt):
    for tok in ["Fast", "API", " streams", " tokens", " nicely", "."]:
        await asyncio.sleep(0.05)            # model "thinking"
        yield tok

async def endpoint(prompt):
    i = 0
    async for tok in fake_llm(prompt):
        i += 1
        yield sse(json.dumps({"text": tok}), event="token", id=str(i))
    yield ": keep-alive comment\n\n"
    yield sse("[DONE]")

def parse(stream):                           # minimal client-side parser
    for block in stream.split("\n\n"):
        fields = {}
        for line in block.split("\n"):
            if not line or line.startswith(":"):
                continue
            k, _, v = line.partition(":")
            fields[k] = fields.get(k, "") + ("\n" if k in fields else "") + v.removeprefix(" ")
        if "data" in fields:
            yield fields

wire, text = "", ""
async for chunk in endpoint("hi"):
    wire += chunk
    for ev in parse(chunk):
        if ev["data"] != "[DONE]":
            text += json.loads(ev["data"])["text"]
            print(f"  [{ev.get('event')}#{ev.get('id')}] so far: {text!r}")
print("raw wire format (first 2 events):")
print(wire.split("\n\n", 2)[0] + "\n\n" + wire.split("\n\n", 2)[1])
```

The problem *Parse a Server-Sent Events Stream* has you write the spec-accurate parser (CRLF, comments,
the single optional space, sticky ids).

### Streaming in production

- **Buffering proxies** defeat streaming: nginx needs `proxy_buffering off` (or the `X-Accel-Buffering:
  no` header); disable gzip for event streams; some CDNs need configuration.
- **Timeouts**: idle-connection timeouts on load balancers (often 60 s) kill quiet streams — send
  keep-alive comments.
- **Resume**: give events `id`s and honour `Last-Event-ID` to continue after a reconnect.
- **Connections are long-lived**: each open stream holds a socket and a little memory; with async this
  scales to thousands per worker, but release DB sessions *before* streaming.
- **Cancellation**: detect disconnects (`await request.is_disconnected()` or the generator being
  cancelled) and cancel upstream generation.
- **Deploys**: graceful shutdown must let in-flight streams finish or end them cleanly.

## WebSockets

A WebSocket starts as an HTTP `GET` with `Upgrade: websocket`; the server answers `101 Switching
Protocols` and both sides then exchange **frames** (text or binary) freely until someone closes.

```python
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI()

@app.websocket("/ws")
async def echo(websocket: WebSocket):
    await websocket.accept()                     # complete the handshake
    try:
        while True:
            text = await websocket.receive_text()        # also receive_json / receive_bytes
            await websocket.send_text(f"echo: {text}")   # also send_json / send_bytes
    except WebSocketDisconnect:
        pass                                     # client went away: clean up here
```

WebSocket routes accept path/query parameters, headers, cookies and `Depends` like HTTP routes — but
you can't raise `HTTPException`; raise `WebSocketException(code=status.WS_1008_POLICY_VIOLATION)` or call
`await websocket.close(code=...)`.

**Authentication** needs care: browsers can't set an `Authorization` header on a WebSocket. Options:
send a token in the first message after connecting; use a cookie (then check the `Origin` header — CORS
does not apply to WebSockets, so cross-site WebSocket hijacking is a real risk); or a short-lived ticket in
the query string.

### Broadcasting and the multi-worker problem

A chat room needs to send one client's message to everyone:

```python
class ConnectionManager:
    def __init__(self):
        self.active: set[WebSocket] = set()

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.add(ws)

    def disconnect(self, ws: WebSocket):
        self.active.discard(ws)

    async def broadcast(self, message: str):
        for ws in list(self.active):
            try:
                await ws.send_text(message)
            except Exception:
                self.disconnect(ws)

manager = ConnectionManager()

@app.websocket("/ws/{room}")
async def chat(websocket: WebSocket, room: str):
    await manager.connect(websocket)
    try:
        while True:
            await manager.broadcast(f"{room}: {await websocket.receive_text()}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
```

This in-memory manager works with **one process only**. With several workers or replicas, clients are
connected to different processes that don't share `manager.active`. The fix is a message broker: each
worker subscribes to a Redis Pub/Sub channel (or NATS/Kafka) and relays published messages to its own
local connections.

```python-run
import asyncio

class Hub:
    """In-memory pub/sub: what a single-process ConnectionManager boils down to."""
    def __init__(self): self.subscribers = {}
    def subscribe(self, name):
        q = asyncio.Queue(maxsize=100)           # bounded: slow consumers can't exhaust memory
        self.subscribers[name] = q
        return q
    def publish(self, sender, message):
        for name, q in self.subscribers.items():
            if name != sender:
                try: q.put_nowait(f"{sender}: {message}")
                except asyncio.QueueFull: pass   # drop for slow consumer (or disconnect them)

async def client(name, hub, script, inbox_log):
    q = hub.subscribe(name)
    async def reader():
        while True:
            inbox_log.append((name, await q.get()))
    task = asyncio.create_task(reader())
    for delay, msg in script:
        await asyncio.sleep(delay)
        hub.publish(name, msg)
    await asyncio.sleep(0.05)
    task.cancel()

hub, log = Hub(), []
await asyncio.gather(
    client("ann", hub, [(0.01, "hi all"), (0.03, "anyone here?")], log),
    client("bob", hub, [(0.02, "hey ann")], log),
    client("cy", hub, [], log),
)
for who, msg in log:
    print(f"{who:>3} received <- {msg}")
```

### Choosing

- Server pushes updates, client just listens → **SSE** (simpler, HTTP-native, auto-reconnect).
- Client and server both talk continuously with low latency, or binary frames → **WebSocket**.
- One big payload produced incrementally → **StreamingResponse**.
- Occasional updates, simplicity over latency → plain polling is still legitimate.

> [!INTERVIEW]
> "How do you stream LLM output to a browser, and what breaks in production?" — Expose an endpoint
> returning `text/event-stream`: an async generator forwards model tokens as SSE `data:` events and ends
> with a terminator like `[DONE]`. Things that break: proxies buffering the response (disable buffering,
> no gzip), idle timeouts (send keep-alive comments), errors after headers are sent (emit an in-band error
> event), client disconnects (cancel generation to stop wasting compute), resources held for the stream's
> lifetime (release DB sessions first), and reconnection (event ids + `Last-Event-ID`). WebSockets are
> only needed when the client must also send messages mid-stream.

## Pitfalls

- Blocking calls inside async stream generators (the entire worker stalls for the stream's duration).
- Expecting to change the status code after streaming began.
- Forgetting the blank line that terminates an SSE event; `.strip()`-ing token data (LLM tokens often
  start with a space).
- In-memory WebSocket broadcast with multiple workers.
- No backpressure: unbounded queues per slow client.
- Not handling `WebSocketDisconnect` → noisy errors and leaked connections.

## Summary

- `StreamingResponse` sends a body incrementally; headers/status are committed before the first chunk.
- SSE = `text/event-stream` with `data:`/`event:`/`id:` lines and blank-line delimiters; ideal for
  server-to-client token streaming; FastAPI offers `EventSourceResponse`/`ServerSentEvent`.
- WebSockets give full-duplex frames after an HTTP upgrade; multi-process broadcasting needs a broker.
- Production streaming is about buffering, timeouts, cancellation and backpressure.

```quiz
[
  {"q": "Which Content-Type identifies a Server-Sent Events stream?", "options": ["application/json", "text/event-stream", "multipart/form-data", "application/octet-stream"], "answer": 1,
   "explain": "SSE responses use text/event-stream; browsers' EventSource requires it."},
  {"q": "What terminates a single SSE event?", "options": ["A semicolon", "A blank line", "The string [DONE]", "Closing the connection"], "answer": 1,
   "explain": "Events are blocks of field lines ended by an empty line. [DONE] is just a convention some APIs send as data."},
  {"q": "An exception occurs after a StreamingResponse has sent several chunks. What can the server do?", "options": ["Change the status to 500", "Send an in-band error event and end the stream - status and headers are already sent", "Resend the headers", "Nothing is sent to the client until the generator finishes"], "answer": 1,
   "explain": "HTTP status and headers precede the body; mid-stream failures must be signalled within the stream."},
  {"q": "Why prefer SSE over WebSockets for LLM token streaming?", "options": ["SSE is bidirectional", "It is one-directional plain HTTP: simpler, proxy-friendly, with built-in reconnection", "SSE supports binary frames", "WebSockets can't send text"], "answer": 1,
   "explain": "Token streaming only needs server-to-client; SSE reuses ordinary HTTP infrastructure."},
  {"q": "A WebSocket chat works locally but with 4 workers users miss messages. Why?", "options": ["WebSockets can't scale", "Each worker keeps its own in-memory connection set; broadcasting needs a shared broker like Redis Pub/Sub", "Uvicorn drops frames", "CORS blocks them"], "answer": 1,
   "explain": "Processes don't share memory; a broker fans messages out to every worker's local connections."},
  {"q": "What should a streaming endpoint do when the client disconnects mid-generation?", "options": ["Keep generating to completion", "Stop/cancel the upstream generation and release resources", "Restart the stream", "Return 404"], "answer": 1,
   "explain": "Continuing wastes GPU/compute and money; handle cancellation in try/finally."},
  {"q": "Which HTTP status completes a WebSocket handshake?", "options": ["200 OK", "101 Switching Protocols", "204 No Content", "302 Found"], "answer": 1,
   "explain": "The Upgrade request is answered with 101, after which the connection speaks the WebSocket protocol."}
]
```

> **Source:** Lubanovic, *FastAPI*, ch. 15 "Files" (StreamingResponse) and ch. 4 "Async, Concurrency, and Starlette Tour"; https://fastapi.tiangolo.com/advanced/websockets/, /advanced/custom-response/, /tutorial/server-sent-events/; WHATWG HTML Standard, "Server-sent events"
