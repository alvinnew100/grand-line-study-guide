PROBLEMS = [
dict(
    id="api-idempotency-store",
    title="Idempotency-Key Store",
    difficulty="Medium",
    pattern="Reliability",
    kind="class",
    entry="IdempotencyStore",
    description=r"""
Payment and order APIs accept an `Idempotency-Key` header so a client can safely retry a `POST` after a
timeout: the server performs the action once and **replays** the stored response for retries. Implement
the bookkeeping.

`IdempotencyStore(ttl)`:

- `begin(key, body_hash, now)` returns a string:
  - `"new"` — key unseen (or its record expired: `now - created >= ttl`). Record it as *in progress*
    with this `body_hash` and `created = now`.
  - `"conflict"` — key exists with a **different** `body_hash` (client reused a key for another request → 422).
  - `"in_progress"` — same body, but the first request has not completed yet (→ 409, try later).
  - `"replay:" + response` — same body and a stored response exists.
- `complete(key, response, now)` stores `response` (a string) for an in-progress key and returns `True`;
  returns `False` if the key is unknown or expired.
- `fail(key, now)` deletes the record (the action failed and may be retried as new); returns `True` if a
  record was removed.

**Example:** `["IdempotencyStore","begin","begin","complete","begin","begin"]`,
`[[60],["k1","h1",0],["k1","h1",1],["k1","201 order#7",2],["k1","h1",3],["k1","h2",4]]`
→ `[None,"new","in_progress",True,"replay:201 order#7","conflict"]`
""",
    starter='''class IdempotencyStore:
    def __init__(self, ttl: int):
        pass

    def begin(self, key: str, body_hash: str, now: int) -> str:
        pass

    def complete(self, key: str, response: str, now: int) -> bool:
        pass

    def fail(self, key: str, now: int) -> bool:
        pass
''',
    solution='''class IdempotencyStore:
    def __init__(self, ttl):
        self.ttl = ttl
        self.rec = {}  # key -> [body_hash, created, response or None]

    def _live(self, key, now):
        r = self.rec.get(key)
        if r is None:
            return None
        if now - r[1] >= self.ttl:
            del self.rec[key]
            return None
        return r

    def begin(self, key, body_hash, now):
        r = self._live(key, now)
        if r is None:
            self.rec[key] = [body_hash, now, None]
            return "new"
        if r[0] != body_hash:
            return "conflict"
        if r[2] is None:
            return "in_progress"
        return "replay:" + r[2]

    def complete(self, key, response, now):
        r = self._live(key, now)
        if r is None:
            return False
        r[2] = response
        return True

    def fail(self, key, now):
        r = self._live(key, now)
        if r is None:
            return False
        del self.rec[key]
        return True
''',
    tests=[
        [["IdempotencyStore", "begin", "begin", "complete", "begin", "begin"], [[60], ["k1", "h1", 0], ["k1", "h1", 1], ["k1", "201 order#7", 2], ["k1", "h1", 3], ["k1", "h2", 4]]],
        [["IdempotencyStore", "begin", "complete", "begin"], [[10], ["a", "x", 0], ["a", "ok", 1], ["a", "x", 10]]],
        [["IdempotencyStore", "begin", "complete", "begin"], [[10], ["a", "x", 0], ["a", "ok", 1], ["a", "x", 9]]],
        [["IdempotencyStore", "complete", "fail"], [[10], ["ghost", "r", 0], ["ghost", 0]]],
        [["IdempotencyStore", "begin", "fail", "begin", "complete", "begin"], [[10], ["a", "x", 0], ["a", 1], ["a", "y", 2], ["a", "200", 3], ["a", "y", 4]]],
        [["IdempotencyStore", "begin", "begin", "begin"], [[5], ["a", "x", 0], ["b", "x", 0], ["a", "x", 0]]],
        [["IdempotencyStore", "begin", "complete"], [[5], ["a", "x", 0], ["a", "r", 5]]],
        [["IdempotencyStore", "begin", "begin"], [[5], ["a", "x", 0], ["a", "y", 7]]],
        [["IdempotencyStore", "begin", "complete", "complete", "begin"], [[100], ["a", "x", 0], ["a", "first", 1], ["a", "second", 2], ["a", "x", 3]]],
        [["IdempotencyStore", "begin", "fail", "fail"], [[100], ["a", "x", 0], ["a", 1], ["a", 2]]],
        [["IdempotencyStore"] + ["begin", "complete"] * 50 + ["begin"] * 3,
         [[1000]] + [a for i in range(50) for a in ([f"k{i}", "h", i], [f"k{i}", f"r{i}", i])] + [["k7", "h", 60], ["k7", "z", 60], ["k99", "h", 60]]],
    ],
    wrong_solutions=[
        '''class IdempotencyStore:
    def __init__(self, ttl): self.rec = {}
    def begin(self, key, h, now):
        r = self.rec.get(key)
        if r is None: self.rec[key] = [h, None]; return "new"
        if r[0] != h: return "conflict"
        return "in_progress" if r[1] is None else "replay:" + r[1]
    def complete(self, key, resp, now):
        if key not in self.rec: return False
        self.rec[key][1] = resp; return True
    def fail(self, key, now):
        return self.rec.pop(key, None) is not None
''',
        '''class IdempotencyStore:
    def __init__(self, ttl): self.ttl = ttl; self.rec = {}
    def begin(self, key, h, now):
        r = self.rec.get(key)
        if r is None or now - r[1] >= self.ttl: self.rec[key] = [h, now, None]; return "new"
        if r[2] is None: return "in_progress"
        return "replay:" + r[2]
    def complete(self, key, resp, now):
        r = self.rec.get(key)
        if r is None or now - r[1] >= self.ttl: return False
        r[2] = resp; return True
    def fail(self, key, now):
        return self.rec.pop(key, None) is not None
''',
    ],
    guide=dict(
        prereqs="Idempotent methods (lesson *REST design and JSON*); caching with TTL.",
        intuition="Idempotency keys turn an unsafe `POST` into something a client may retry. The store is a tiny "
                  "state machine per key: *absent → in progress → completed*, plus a fingerprint of the body so a "
                  "reused key with a different request is caught instead of silently replayed.",
        hints=["Store `[body_hash, created, response]` per key.",
               "Write one helper that returns the record or `None` if missing/expired (and deletes expired ones).",
               "Check body hash before progress state: a mismatched body is always a conflict."],
        brute_force="Not applicable; correctness of the state transitions is the whole challenge.",
        approach="`begin`: no live record → create, `new`; hash differs → `conflict`; response missing → "
                 "`in_progress`; else replay. `complete`/`fail` operate on live records only.",
        complexity="O(1) per operation.",
        pitfalls="- Replaying a response for a different body.\n- Forgetting the TTL boundary (`>=`).\n"
                 "- Not allowing a retry after a failed attempt (`fail` must delete).",
        follow_up="In production the `begin` step must be atomic across workers — e.g. Redis `SET key value NX EX ttl` "
                  "or a unique constraint in the database.",
    ),
),
dict(
    id="api-sse-parse",
    title="Parse a Server-Sent Events Stream",
    difficulty="Medium",
    pattern="Streaming",
    entry="parseSSE",
    description=r"""
LLM APIs stream tokens as **Server-Sent Events**: UTF-8 text where each event is a block of `field: value`
lines terminated by a blank line. Write the client-side parser.

`parseSSE(stream)` returns a list of events, each `{"event": name, "data": text, "id": last_id}`.

Rules (a simplified version of the WHATWG spec):

- Split into lines on `\r\n`, `\n` or `\r`.
- A line starting with `:` is a comment — ignore it.
- Otherwise split on the **first** `:` into field and value; if there is no colon, the whole line is the
  field and the value is `""`. If the value starts with a single space, remove that one space.
- `data` → append value to the data buffer (lines are joined with `\n`). `event` → set the event type.
  `id` → set the last event id (ignore the field if the value contains `"\x00"`). Other fields (e.g. `retry`) are ignored.
- A **blank line** dispatches: if the data buffer is empty, nothing is emitted; otherwise emit an event
  with type (default `"message"`), the joined data, and the current last id (`None` if never set).
  Then reset the data buffer and event type — but **the last id persists** across events.
- Text after the final blank line (an incomplete event) is discarded.

**Example:** `"data: hel\ndata: lo\n\nevent: done\ndata: [DONE]\n\n"` →
`[{"event":"message","data":"hel\nlo","id":None}, {"event":"done","data":"[DONE]","id":None}]`
""",
    starter='''def parseSSE(stream: str) -> list[dict]:
    pass
''',
    solution='''import re

def parseSSE(stream):
    events, data, etype, last_id = [], [], "", None
    lines = re.split(r"\\r\\n|\\n|\\r", stream)
    # the final element is text after the last line break (incomplete line) -> drop it
    for line in lines[:-1]:
        if line == "":
            if data:
                events.append({"event": etype or "message", "data": "\\n".join(data), "id": last_id})
            data, etype = [], ""
            continue
        if line.startswith(":"):
            continue
        field, sep, value = line.partition(":")
        if sep and value.startswith(" "):
            value = value[1:]
        if field == "data":
            data.append(value)
        elif field == "event":
            etype = value
        elif field == "id":
            if "\\x00" not in value:
                last_id = value
    return events
''',
    tests=[
        ["data: hel\ndata: lo\n\nevent: done\ndata: [DONE]\n\n"],
        [""],
        ["data: a\n\n"],
        ["data: a"],
        ["data: a\n\ndata: incomplete\n"],
        [": keep-alive\n\n: ping\ndata: x\n\n"],
        ["id: 1\ndata: first\n\ndata: second\n\nid: 3\ndata: third\n\n"],
        ["data:no-space\ndata:  two-spaces\n\n"],
        ["data\n\n"],
        ["data\ndata\n\n"],
        ["event: token\n\ndata: after\n\n"],
        ["retry: 3000\ndata: r\n\n"],
        ["data: a\r\ndata: b\r\n\r\ndata: c\rdata: d\r\r"],
        ["data: {\"token\": \"Hi\"}\n\ndata: {\"token\": \" there\"}\n\ndata: [DONE]\n\n"],
        ["id: bad\x00id\ndata: z\n\nid\ndata: y\n\n"],
        ["".join(f"event: t\nid: {i}\ndata: tok{i}\n\n" for i in range(300))],
    ],
    wrong_solutions=[
        '''def parseSSE(stream):
    out = []
    for block in stream.split("\\n\\n"):
        if not block.strip(): continue
        ev, data = "message", []
        for line in block.split("\\n"):
            if line.startswith("data:"): data.append(line[5:].strip())
            elif line.startswith("event:"): ev = line[6:].strip()
        if data: out.append({"event": ev, "data": "\\n".join(data), "id": None})
    return out
''',
        '''import re
def parseSSE(stream):
    events, data, et, lid = [], [], "", None
    for line in re.split(r"\\r\\n|\\n|\\r", stream)[:-1]:
        if line == "":
            if data: events.append({"event": et or "message", "data": "\\n".join(data), "id": lid})
            data, et, lid = [], "", None
            continue
        if line.startswith(":"): continue
        f, s, v = line.partition(":")
        if s and v.startswith(" "): v = v[1:]
        if f == "data": data.append(v)
        elif f == "event": et = v
        elif f == "id" and "\\x00" not in v: lid = v
    return events
''',
    ],
    guide=dict(
        prereqs="Streaming responses and SSE (lesson *WebSockets, streaming and Server-Sent Events*).",
        intuition="SSE is a line protocol with a tiny state machine: accumulate fields until a blank line, then "
                  "emit. The subtle parts are exactly the ones naive `split('\\n\\n')` parsers get wrong: comments "
                  "(used as keep-alive pings), the single optional space, multi-line data, and the sticky `id`.",
        hints=["`re.split(r'\\r\\n|\\n|\\r', s)` handles all three line endings; the last element is an unfinished line.",
               "`line.partition(':')` splits on the first colon only — JSON data contains colons.",
               "Remove exactly one leading space, not all whitespace.",
               "Reset data and event type after a blank line, but keep the last id."],
        brute_force="Splitting on `\\n\\n` and stripping values works for well-behaved servers and fails on CRLF, "
                    "leading-space and id edge cases.",
        approach="Iterate complete lines; blank → dispatch if data; `:` prefix → skip; else partition, strip one space, "
                 "update state. Dry run `data\\ndata\\n\\n`: two empty data lines → data `\"\\n\"` → one event.",
        complexity="O(len(stream)).",
        pitfalls="- `.strip()` on values destroys meaningful spaces (LLM tokens often begin with a space!).\n"
                 "- Emitting an event when only `event:` was set.\n- Resetting `id` per event.",
        follow_up="Browsers expose this as `new EventSource(url)` and auto-reconnect, sending `Last-Event-ID` so the "
                  "server can resume. `EventSource` only supports GET; LLM clients usually POST and parse with fetch.",
    ),
),
dict(
    id="api-retry-backoff",
    title="Retry with Exponential Backoff",
    difficulty="Medium",
    pattern="Reliability",
    entry="retrySchedule",
    description=r"""
A resilient HTTP client retries transient failures with exponentially growing waits, honours the
server's `Retry-After`, and gives up eventually. Simulate it.

`retrySchedule(responses, base, factor, max_delay, max_retries)`:

- `responses[i]` is what attempt `i` receives: either an int status (e.g. `503`) or a string
  `"429:7"` meaning status 429 with `Retry-After: 7` seconds.
- After attempt `i` (0-based) gets a response:
  - status `< 400` → success, stop;
  - status not in `{408, 429, 500, 502, 503, 504}` → non-retryable, stop;
  - retryable but `i == max_retries` (retries exhausted) or no more responses → stop;
  - otherwise wait `delay = min(max_delay, base * factor ** i)`; if a `Retry-After` value is present use
    `min(max_delay, max(delay, retry_after))`. Then make attempt `i + 1`.
- Return `[final_status, delays]` where `delays` lists every wait in order (floats are fine; they are
  compared with tolerance).

**Example:** `retrySchedule([503, 503, 200], 0.5, 2, 10, 5)` → `[200, [0.5, 1.0]]`

**Example:** `retrySchedule(["429:7", 200], 1, 2, 30, 3)` → `[200, [7]]`
""",
    starter='''def retrySchedule(responses: list, base: float, factor: float, max_delay: float, max_retries: int) -> list:
    pass
''',
    solution='''RETRYABLE = {408, 429, 500, 502, 503, 504}

def retrySchedule(responses, base, factor, max_delay, max_retries):
    delays = []
    status = None
    for i, r in enumerate(responses):
        retry_after = None
        if isinstance(r, str):
            s, _, ra = r.partition(":")
            status = int(s)
            if ra:
                retry_after = float(ra)
        else:
            status = r
        if status < 400 or status not in RETRYABLE:
            break
        if i == max_retries or i == len(responses) - 1:
            break
        d = min(max_delay, base * factor ** i)
        if retry_after is not None:
            d = min(max_delay, max(d, retry_after))
        delays.append(d)
    return [status, delays]
''',
    compare="float",
    tests=[
        [[503, 503, 200], 0.5, 2, 10, 5],
        [["429:7", 200], 1, 2, 30, 3],
        [[200], 1, 2, 30, 3],
        [[404, 200], 1, 2, 30, 3],
        [[500, 500, 500, 500, 500, 500], 1, 2, 30, 3],
        [[503, 503, 503, 503, 503, 503, 503, 200], 1, 2, 10, 10],
        [["429:100", 200], 1, 2, 30, 3],
        [["429:0", 200], 4, 2, 30, 3],
        [[502, 504, 408, 201], 0.1, 3, 60, 5],
        [[503], 1, 2, 30, 0],
        [[503, 200], 1, 2, 30, 0],
        [[301], 1, 2, 30, 3],
        [[503, "503:2", 422, 200], 1, 2, 30, 5],
        [["429", 200], 1, 2, 30, 3],
    ],
    wrong_solutions=[
        '''def retrySchedule(responses, base, factor, max_delay, max_retries):
    delays = []
    for i, r in enumerate(responses):
        s = int(str(r).split(":")[0])
        if s < 400: return [s, delays]
        if i == max_retries or i == len(responses) - 1: return [s, delays]
        delays.append(min(max_delay, base * factor ** i))
    return [s, delays]
''',
        '''def retrySchedule(responses, base, factor, max_delay, max_retries):
    delays = []
    for i, r in enumerate(responses):
        s, _, ra = str(r).partition(":")
        s = int(s)
        if s < 400 or s not in {408, 429, 500, 502, 503, 504}: return [s, delays]
        if i == max_retries or i == len(responses) - 1: return [s, delays]
        delays.append(float(ra) if ra else base * factor ** i)
    return [s, delays]
''',
    ],
    guide=dict(
        prereqs="Status codes and retryability (problem *Classify an HTTP Status Code*); lesson *Health checks, logging and observability*.",
        intuition="Exponential backoff spreads retries out so a struggling server can recover; the cap stops waits "
                  "from exploding; `Retry-After` is the server telling you exactly how long to back off — respect it "
                  "but never wait *less* than your own schedule, and never more than your cap.",
        hints=["Parse each response into `(status, retry_after or None)` first.",
               "Decide 'stop' before computing a delay — no wait is recorded after the final attempt.",
               "Delay for attempt `i` is `base * factor ** i`, capped."],
        brute_force="Already linear; the challenge is the stop conditions.",
        approach="Loop attempts; classify; stop on success / non-retryable / exhausted; else append the delay. "
                 "Dry run `[503, '503:2', 422, 200]`, base 1, factor 2: wait 1; attempt 1 → delay 2 vs retry-after 2 → 2; "
                 "attempt 2 → 422 stop → `[422, [1, 2]]`.",
        complexity="O(len(responses)).",
        pitfalls="- Retrying 4xx errors like 404/422 (they will never succeed).\n- Recording a delay after the last attempt.\n"
                 "- Letting `Retry-After` exceed your cap (a hostile or buggy server could stall you forever).",
        follow_up="Production clients add **jitter** (`random.uniform(0, delay)`) so thousands of clients don't retry "
                  "in lock-step, and only retry non-idempotent requests that carry an idempotency key.",
    ),
),
dict(
    id="api-micro-batcher",
    title="Dynamic Micro-Batching for Inference",
    difficulty="Medium",
    pattern="ML Serving",
    entry="formBatches",
    description=r"""
GPUs are far more efficient on batches than on single inputs, so model servers collect concurrent
requests into **micro-batches**: dispatch when the batch is full **or** when the oldest request has
waited `max_wait`, whichever comes first.

`formBatches(arrivals, max_batch, max_wait)`: `arrivals` are non-decreasing request arrival times
(request `i` arrives at `arrivals[i]`).

- When a request arrives and no batch is open, it opens a batch at `t0 = its arrival` with
  `deadline = t0 + max_wait`.
- A later request joins the open batch if its arrival is `<= deadline`. If the join makes the batch reach
  `max_batch`, the batch is dispatched **at that request's arrival time**.
- If the next request arrives **after** the deadline (or there are no more requests), the open batch is
  dispatched at `deadline`.

Return a list of `[dispatch_time, [request indices]]` in dispatch order.

**Example:** `formBatches([0, 1, 2, 10, 11], 3, 5)` → `[[2, [0, 1, 2]], [15, [3, 4]]]`

Constraints: `max_batch >= 1`, `max_wait >= 0`, up to 20,000 requests.
""",
    starter='''def formBatches(arrivals: list[float], max_batch: int, max_wait: float) -> list:
    pass
''',
    solution='''def formBatches(arrivals, max_batch, max_wait):
    out, cur, deadline = [], [], None
    for i, t in enumerate(arrivals):
        if cur and t > deadline:
            out.append([deadline, cur])
            cur = []
        if not cur:
            deadline = t + max_wait
        cur.append(i)
        if len(cur) == max_batch:
            out.append([t, cur])
            cur = []
    if cur:
        out.append([deadline, cur])
    return out
''',
    tests=[
        [[0, 1, 2, 10, 11], 3, 5],
        [[], 4, 10],
        [[7], 4, 10],
        [[0, 0, 0, 0, 0], 2, 10],
        [[0, 5, 6], 8, 5],
        [[0, 1, 2, 3], 1, 100],
        [[0, 3, 3, 9, 12, 12, 12, 30], 3, 4],
        [[0, 10, 20, 30], 5, 0],
        [[0, 0, 1, 1], 10, 0],
        [[0.0, 0.004, 0.009, 0.0101, 0.02], 4, 0.01],
        [[i // 3 for i in range(20000)], 32, 2],
    ],
    wrong_solutions=[
        '''def formBatches(arrivals, max_batch, max_wait):
    out = []
    for s in range(0, len(arrivals), max_batch):
        idx = list(range(s, min(s + max_batch, len(arrivals))))
        out.append([arrivals[idx[-1]], idx])
    return out
''',
        '''def formBatches(arrivals, max_batch, max_wait):
    out, cur, dl = [], [], None
    for i, t in enumerate(arrivals):
        if cur and t >= dl:
            out.append([dl, cur]); cur = []
        if not cur: dl = t + max_wait
        cur.append(i)
        if len(cur) == max_batch:
            out.append([t, cur]); cur = []
    if cur: out.append([dl, cur])
    return out
''',
    ],
    guide=dict(
        prereqs="Batching for model serving (lesson *Serving an ML model with FastAPI*).",
        intuition="Micro-batching trades a little latency (at most `max_wait`) for a lot of throughput. The "
                  "simulation is a single pass: keep the open batch and its deadline; each arrival either closes the "
                  "old batch (deadline passed) or joins it; a full batch flushes immediately.",
        hints=["Check 'did the deadline pass?' *before* adding the new request.",
               "The deadline is fixed by the first request of the batch.",
               "Don't forget to flush the last open batch at its deadline."],
        brute_force="Chunking into fixed groups of `max_batch` ignores time completely and makes early requests "
                    "wait arbitrarily long under light load.",
        approach="Dry run `[0,1,2,10,11], 3, 5`: open at 0 (deadline 5), 1 joins, 2 joins → full → dispatch at 2. "
                 "10 opens (deadline 15), 11 joins; end → dispatch at 15.",
        complexity="O(n).",
        pitfalls="- `>` vs `>=`: a request arriving exactly at the deadline still joins.\n"
                 "- Dispatch time for a full batch is the arrival time of the request that filled it.\n"
                 "- `max_wait = 0` still batches simultaneous arrivals.",
        follow_up="Real servers (Triton, Ray Serve, TorchServe) implement this with an asyncio queue: a background "
                  "task awaits the first item, then `asyncio.wait_for` the rest until the deadline. LLM servers go "
                  "further with *continuous batching* at the token level (vLLM).",
    ),
),
]
