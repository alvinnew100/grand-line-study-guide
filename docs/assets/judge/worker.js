/* Pyodide worker: runs learner code off the main thread. */
importScripts("https://cdn.jsdelivr.net/pyodide/v0.26.4/full/pyodide.js");

let py = null;
let currentId = null;
const loadedTracks = {};
let hashOk = false;

// Pure-Python wheels installed from PyPI on first use (lessons only, never the judge).
// Versions are pinned and checked against Pyodide 0.26.4 (Python 3.12, pydantic 2.7.0, pydantic-core 2.18.1,
// matplotlib 3.5.2, pandas 2.2.0); keep AUTHORING.md in step when changing them.
const PIP = {
  seaborn: ["seaborn==0.13.2"],
  plotly: ["plotly==6.0.1", "narwhals==1.31.0"],
};
// FastAPI's wheels: [file, path on files.pythonhosted.org, sha256]. To bump one, take url and digest
// from https://pypi.org/pypi/<name>/<version>/json.
const WHEELS = [
  ["fastapi-0.115.6-py3-none-any.whl", "52/b3/7e4df40e585df024fac2f80d1a2d579c854ac37109675db2b0cc22c0bb9e", "e9240b29e36fa8f4bb7290316988e90c381e5092e0cbe84e7818cc3713bcf305"],
  ["starlette-0.41.3-py3-none-any.whl", "96/00/2b325970b3060c7cecebab6d295afe763365822b1306a12eeab198f74323", "44cedb2b7c77a9de33a8b74b2b90e9f50d11fcf25d8270ea525ad71a25374ff7"],
  ["httpx-0.28.1-py3-none-any.whl", "2a/39/e50c7c3a983047577ee07d2a9e53faf5a69493943ec3f6a384bdc792deb2", "d909fcccc110f8c7faf814ca82a9a4d816bc5a6dbfea25d6591d6985b8ba59ad"],
  ["httpcore-1.0.7-py3-none-any.whl", "87/f5/72347bc88306acb359581ac4d52f23c0ef445b57157adedb9aee0cd689d2", "a3fff8f43dc260d5bd363d9f9cf1830fa3a458b332856f34282de498ed420edd"],
  ["anyio-4.7.0-py3-none-any.whl", "a0/7a/4daaf3b6c08ad7ceffea4634ec206faeff697526421c20f07628c7372156", "ea60c3723ab42ba6fff7e8ccb0488c898ec538ff4df1f1d5e642c3601d07e352"],
  ["sniffio-1.3.1-py3-none-any.whl", "e9/44/75a9c9421471a6c4805dbf2356f7c181a29c1879239abab1ea2cc8f38b40", "2f6da418d1f1e0fddd844478f41680e794e6051915791a034ff65e5f100525a2"],
  ["h11-0.14.0-py3-none-any.whl", "95/04/ff642e65ad6b90db43e668d70ffb6736436c7ce41fcc549f4e9472234127", "e3fe4ac4b851c468cc8363d500db52c2ead036020723024a109d37346efaa761"],
  ["python_multipart-0.0.20-py3-none-any.whl", "45/58/38b5afbc1a800eeea951b9285d3912613f2603bdf897a4ab0f4bd7f405fc", "8a62d3a8335e06589fe01f2a3e178cdcc632f3fbe0d492ad9ee0ec35aab1f104"],
];
const pipDone = {};
let mplReady = false;

// Lesson-only helpers (figures, Plotly capture, FastAPI without threads). Kept out of harness.py so the
// judge never imports matplotlib or FastAPI.
const SKY_PY = String.raw`
import base64, io, json, sys, time

PLOTLY = []


def mpl_flush(limit=8):
    """PNG (base64) of every open matplotlib figure, then close them all to free memory."""
    plt = sys.modules.get("matplotlib.pyplot")
    if plt is None:
        return []
    out = []
    try:
        for num in plt.get_fignums()[:limit]:
            fig = plt.figure(num)
            buf = io.BytesIO()
            fig.savefig(buf, format="png", dpi=144, bbox_inches="tight")
            w, h = fig.get_size_inches() * 100
            out.append({"png": base64.b64encode(buf.getvalue()).decode("ascii"), "w": round(float(w)), "h": round(float(h))})
            buf.close()
    finally:
        plt.close("all")
    return out


def plotly_flush():
    out = PLOTLY[:4]
    PLOTLY.clear()
    return out


def plotly_hook():
    import plotly.io as pio
    import plotly.basedatatypes as bd

    def show(fig, *args, **kwargs):
        PLOTLY.append(pio.to_json(fig, validate=False))

    pio.show = show
    bd.BaseFigure.show = lambda self, *a, **k: show(self)


def finish(value):
    """Decide what to print for the last expression: capture Plotly figures, hide matplotlib object reprs."""
    if value is None:
        return None
    if hasattr(value, "to_plotly_json") and type(value).__module__.startswith("plotly"):
        PLOTLY.append(value.to_json())
        return None
    if isinstance(value, str):
        return value
    probe = value[0] if isinstance(value, (list, tuple)) and value else value
    if type(probe).__module__.startswith(("matplotlib", "seaborn")):
        return None
    return repr(value)


# ---------------------------------------------------------------- FastAPI without threads
#
# Two ways to drive an ASGI app here, both on one thread:
# - the sync TestClient runs it on VirtualLoop, a private event loop that never waits (sleeps finish
#   at once), so client.get(...) and "with client.websocket_connect(...)" work from plain code;
# - the request panel awaits it on Pyodide's own loop (real time) and reports every ASGI send
#   as it happens, so streamed chunks and WebSocket messages show up live.

import asyncio
import asyncio.events as _events
import codecs
import traceback


class _Stuck(RuntimeError):
    pass


class _NoWaitSelector:
    def __init__(self, loop):
        self.loop = loop

    def select(self, timeout):
        if timeout is None:  # nothing ready and no timer: every task waits for something that never comes
            raise _Stuck()
        self.loop._now += max(0.0, timeout)
        return []


class VirtualLoop(asyncio.BaseEventLoop):
    """An asyncio loop with a virtual clock: when every task waits on a timer it jumps to that timer."""

    def __init__(self):
        super().__init__()
        self._now = 0.0
        self._selector = _NoWaitSelector(self)

    def time(self):
        return self._now

    def _process_events(self, event_list):
        pass

    def _write_to_self(self):
        pass


_VLOOP = None


def vloop():
    global _VLOOP
    if _VLOOP is None or _VLOOP.is_closed():
        _VLOOP = VirtualLoop()
    return _VLOOP


def vrun(awaitable):
    """Run an awaitable to completion on the virtual loop from sync code, even inside a running loop."""
    loop = vloop()
    if loop.is_running():
        raise RuntimeError("TestClient was called from inside the app it is testing.")
    fut = asyncio.ensure_future(awaitable, loop=loop)
    outer = _events._get_running_loop()
    _events._set_running_loop(None)
    try:
        return loop.run_until_complete(fut)
    except _Stuck:
        fut.cancel()
        try:
            loop.run_until_complete(fut)
        except BaseException:
            pass
        raise
    finally:
        _events._set_running_loop(outer)


def _scope(request, root_path="", state=None, kind="http"):
    url = request.url
    secure = url.scheme in ("https", "wss")
    port = url.port or (443 if secure else 80)
    scope = {
        "type": kind, "asgi": {"version": "3.0"}, "http_version": "1.1", "scheme": url.scheme,
        "path": url.path, "raw_path": url.raw_path.split(b"?")[0], "query_string": url.query,
        "root_path": root_path, "headers": [(k.lower(), v) for k, v in request.headers.raw],
        "server": (url.host, port), "client": ("testclient", 50000), "state": dict(state or {}),
    }
    if kind == "http":
        scope["method"] = request.method
        scope["extensions"] = {"http.response.debug": {}}
    else:
        proto = request.headers.get("sec-websocket-protocol")
        scope["subprotocols"] = [p.strip() for p in proto.split(",")] if proto else []
        scope["extensions"] = {"websocket.http.response": {}}
    return scope


async def _asgi_http(app, scope, body, on_start, on_body, done):
    """One HTTP exchange. receive() hands over the body, then blocks until the response is complete
    (StreamingResponse and middleware listen for a disconnect while they stream)."""
    first = [True]

    async def receive():
        if first[0]:
            first[0] = False
            return {"type": "http.request", "body": body, "more_body": False}
        await done.wait()
        return {"type": "http.disconnect"}

    async def send(message):
        kind = message["type"]
        if done.is_set() and kind.startswith("http.response"):
            raise OSError("client disconnected")
        if kind == "http.response.start":
            on_start(message)
        elif kind == "http.response.body":
            more = message.get("more_body", False)
            on_body(message.get("body", b""), more)
            if not more:
                done.set()

    try:
        await app(scope, receive, send)
    finally:
        done.set()


class _Channel:
    """The app side of a long-lived ASGI connection (lifespan, WebSocket) run on the virtual loop."""

    def __init__(self, app, scope, what):
        self.inbox = asyncio.Queue()
        self.outbox = []
        self.what = what
        self.flag = asyncio.Event()

        async def receive():
            return await self.inbox.get()

        async def send(message):
            self.outbox.append(message)
            self.flag.set()

        self.task = vloop().create_task(app(scope, receive, send))
        self.task.add_done_callback(lambda _t: self.flag.set())

    def push(self, message):
        self.inbox.put_nowait(message)

    def error(self):
        t = self.task
        return t.exception() if t.done() and not t.cancelled() else None

    def pull(self, call):
        """Next message the app sent; runs the loop until there is one."""
        while not self.outbox:
            if self.task.done():
                if self.error() is not None:
                    raise self.error()
                raise RuntimeError(f"{call}: the {self.what} handler has finished and sent nothing more.")
            self.flag.clear()
            try:
                vrun(self.flag.wait())
            except _Stuck:
                raise RuntimeError(f"{call} would wait forever: the {self.what} handler is itself waiting "
                                   "(for a message from the client?) and has nothing to send.") from None
        return self.outbox.pop(0)

    def finish(self):
        """Let the app run to the end (cancel it if it would wait forever); return its exception."""
        if not self.task.done():
            try:
                vrun(asyncio.wait({self.task}))
            except _Stuck:
                self.task.cancel()
                try:
                    vrun(asyncio.wait({self.task}))
                except BaseException:
                    pass
        return self.error()


def asgi_setup():
    import anyio.to_thread
    import httpx
    import starlette.testclient as st
    from starlette.websockets import WebSocketDisconnect

    async def run_sync(func, *args, abandon_on_cancel=False, cancellable=None, limiter=None):
        # Pyodide has no threads: run sync endpoints and dependencies inline.
        return func(*args)

    anyio.to_thread.run_sync = run_sync

    class SyncASGITransport(httpx.BaseTransport):
        def __init__(self, app, raise_server_exceptions=True, root_path="", app_state=None):
            self.app, self.raise_server_exceptions, self.root_path = app, raise_server_exceptions, root_path
            self.app_state = app_state if app_state is not None else {}

        def handle_request(self, request):
            body = request.read()
            state = {"status": None, "headers": [], "parts": []}

            def on_start(message):
                state["status"], state["headers"] = message["status"], message.get("headers", [])

            def on_body(chunk, more):
                state["parts"].append(chunk)

            async def exchange():
                await _asgi_http(self.app, _scope(request, self.root_path, self.app_state), body,
                                 on_start, on_body, asyncio.Event())

            try:
                vrun(exchange())
            except _Stuck:
                raise RuntimeError(f"{request.method} {request.url.path} never finished: the app waits for "
                                   "something that cannot happen.") from None
            except Exception:
                if self.raise_server_exceptions:
                    raise
                if state["status"] is None:
                    state["status"], state["parts"] = 500, [b"Internal Server Error"]
            return httpx.Response(state["status"], headers=state["headers"],
                                  content=b"".join(state["parts"]), request=request)

    class WebSocketTestSession(st.WebSocketTestSession):
        """starlette's session API (send_text, receive_json, ...) on the virtual loop instead of a thread."""

        def __init__(self, app, scope):
            self.app, self.scope = app, scope
            self.accepted_subprotocol = None
            self.extra_headers = None
            self._ch = None

        def __enter__(self):
            self._ch = _Channel(self.app, self.scope, "WebSocket")
            self.send({"type": "websocket.connect"})
            try:
                message = self.receive()
                self._raise_on_close(message)
            except BaseException:
                self._ch.finish()
                raise
            self.accepted_subprotocol = message.get("subprotocol", None)
            self.extra_headers = message.get("headers", None)
            return self

        def __exit__(self, *exc):
            try:
                self.close(1000)
            finally:
                err = self._ch.finish()
            if err is not None and not isinstance(err, WebSocketDisconnect):
                raise err

        def send(self, message):
            self._ch.push(message)

        def receive(self):
            return self._ch.pull("receive()")

    class TestClient(httpx.Client):
        """Drop-in for fastapi.testclient.TestClient that needs no threads (Pyodide)."""
        __test__ = False

        def __init__(self, app, base_url="http://testserver", raise_server_exceptions=True,
                     root_path="", cookies=None, headers=None, follow_redirects=True, **_):
            self.app = app
            self.app_state = {}
            self._lifespan = None
            super().__init__(transport=SyncASGITransport(app, raise_server_exceptions, root_path, self.app_state),
                             base_url=base_url, headers=headers, cookies=cookies,
                             follow_redirects=follow_redirects)

        def websocket_connect(self, url, subprotocols=None, **kwargs):
            from urllib.parse import urljoin
            headers = dict(kwargs.get("headers") or {})
            headers.setdefault("connection", "upgrade")
            headers.setdefault("sec-websocket-key", "testserver==")
            headers.setdefault("sec-websocket-version", "13")
            if subprotocols is not None:
                headers.setdefault("sec-websocket-protocol", ", ".join(subprotocols))
            request = self.build_request("GET", urljoin("ws://testserver", url), headers=headers,
                                         params=kwargs.get("params"), cookies=kwargs.get("cookies"))
            transport = self._transport
            return WebSocketTestSession(self.app, _scope(request, transport.root_path, self.app_state, "websocket"))

        def __enter__(self):
            ch = _Channel(self.app, {"type": "lifespan", "asgi": {"version": "3.0"}, "state": self.app_state},
                          "lifespan")
            ch.push({"type": "lifespan.startup"})
            message = ch.pull("Application startup")
            if message["type"] == "lifespan.startup.failed":
                err = ch.finish()
                raise err or RuntimeError(message.get("message") or "Application startup failed")
            self._lifespan = ch
            return self

        def __exit__(self, *exc):
            ch, self._lifespan = self._lifespan, None
            if ch is not None:
                ch.push({"type": "lifespan.shutdown"})
                try:
                    message = ch.pull("Application shutdown")
                    if message["type"] == "lifespan.shutdown.failed":
                        raise ch.finish() or RuntimeError(message.get("message") or "Application shutdown failed")
                finally:
                    ch.finish()
            self.close()

    st.TestClient = TestClient
    st.WebSocketTestSession = WebSocketTestSession
    import fastapi.testclient
    fastapi.testclient.TestClient = TestClient


def _form_example(schema, comps, example):
    """Form fields of a multipart / urlencoded body, from its OpenAPI schema."""
    if "$ref" in schema:
        schema = comps.get(schema["$ref"].split("/")[-1], {})
    fields = []
    for name, prop in (schema.get("properties") or {}).items():
        options = [prop] + [s for s in prop.get("anyOf", []) if s.get("type") != "null"]
        is_file = any(o.get("format") == "binary" or (o.get("items") or {}).get("format") == "binary"
                      for o in options)
        many = any(o.get("type") == "array" for o in options)
        value = None if is_file else example(prop)
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        fields.append({"name": name, "file": is_file, "many": many,
                       "value": "" if value is None else str(value).lower() if isinstance(value, bool) else str(value)})
    return fields


def app_info(app):
    """Routes of a FastAPI app, with an example body built from the OpenAPI schema, plus WebSocket routes."""
    try:
        spec = app.openapi()
    except Exception:
        spec = {"paths": {}}
    comps = spec.get("components", {}).get("schemas", {})

    def example(schema, depth=0):
        if depth > 6 or not isinstance(schema, dict):
            return None
        if "$ref" in schema:  # following a reference does not nest the value any deeper
            return example(comps.get(schema["$ref"].split("/")[-1], {}), depth)
        for key in ("example", "default"):
            if schema.get(key) is not None:
                return schema[key]
        if schema.get("examples"):
            return schema["examples"][0]
        for key in ("anyOf", "oneOf", "allOf"):
            if schema.get(key):
                options = [s for s in schema[key] if s.get("type") != "null"] or schema[key]
                return example(options[0], depth + 1)
        if "enum" in schema:
            return schema["enum"][0]
        kind = schema.get("type")
        if kind == "object" or "properties" in schema:
            props = schema.get("properties", {})
            required = schema.get("required", list(props))
            return {k: example(v, depth + 1) for k, v in props.items() if k in required or depth == 0}
        if kind == "array":
            item = example(schema.get("items", {}), depth + 1)
            return [] if item is None else [item]
        if kind in ("integer", "number"):
            low = schema.get("minimum", schema.get("exclusiveMinimum", -1) + 1)
            high = schema.get("maximum", schema.get("exclusiveMaximum", low + 2) - 1)
            value = max(low, min(1, high))
            return int(value) if kind == "integer" else float(value)
        if kind == "string":
            text = "string".ljust(schema.get("minLength", 0), "s")
            return text[:schema.get("maxLength", len(text))]
        return {"boolean": True}.get(kind)

    routes = []
    for path, ops in spec.get("paths", {}).items():
        for method, op in ops.items():
            route = {"method": method.upper(), "path": path, "body": None, "summary": op.get("summary", "")}
            content = (op.get("requestBody") or {}).get("content", {})
            if "application/json" in content:
                route["body"] = json.dumps(example(content["application/json"].get("schema", {})), indent=2)
            for ctype, mode in (("multipart/form-data", "file"), ("application/x-www-form-urlencoded", "form")):
                if ctype in content:
                    fields = _form_example(content[ctype].get("schema", {}), comps, example)
                    if mode == "file" and not any(f["file"] for f in fields):
                        mode = "form"
                    route["form"] = {"mode": mode, "fields": fields}
            routes.append(route)
    for r in getattr(app, "routes", []):
        if "WebSocket" in type(r).__name__ and getattr(r, "path", None):
            routes.append({"method": "WS", "path": r.path, "body": None, "summary": getattr(r, "name", "") or ""})
    return json.dumps(routes)


def _snippet_traceback(exc):
    """The learner's own frames only, as a real server would log them."""
    frames = [f for f in traceback.extract_tb(exc.__traceback__) if f.filename == "snippet.py"]
    print("Traceback (most recent call last):\n" + "".join(traceback.format_list(frames))
          + "".join(traceback.format_exception_only(exc)), end="", file=sys.stderr)
    return "".join(traceback.format_exception_only(exc)).strip()


_TEXTUAL = ("text/", "json", "xml", "javascript", "x-www-form-urlencoded", "event-stream", "ndjson", "yaml", "csv")
_LIVE = {}      # block key -> (task, done event) of the request being streamed
_SOCKETS = {}   # block key -> _PanelSocket


def _build_request(spec, files):
    import httpx
    headers = spec.get("headers") or {}
    url = "http://testserver" + spec["path"]
    mode = spec.get("mode", "json")
    if spec["method"] == "GET" or mode == "json":
        body = (spec.get("body") or "").encode()
        if body and not any(k.lower() == "content-type" for k in headers):
            headers["content-type"] = "application/json"
        return httpx.Request(spec["method"], url, headers=headers, content=body or None)
    data = {}
    for name, value in spec.get("fields") or []:
        if name:
            data.setdefault(name, []).append(value)
    data = {k: v[0] if len(v) == 1 else v for k, v in data.items()}
    if mode == "file":
        uploads = [(f.field or "file", (f.name, f.data.to_bytes(), f.type or "application/octet-stream"))
                   for f in files]
        if not uploads:  # multipart with text fields only (shows FastAPI's "field required" for the file)
            from httpx._multipart import MultipartStream
            stream = MultipartStream(data=data, files={})
            headers = {**stream.get_headers(), **headers}
            return httpx.Request(spec["method"], url, headers=headers, content=b"".join(stream))
        return httpx.Request(spec["method"], url, headers=headers, data=data, files=uploads)
    return httpx.Request(spec["method"], url, headers=headers, data=data)


async def app_request(key, app, spec_json, files, emit):
    """Send one request from the panel. Reports {"type": "head"} and, for streamed bodies, one
    {"type": "chunk"} per ASGI body message as it is sent; returns the whole response."""
    import base64, http
    spec = json.loads(spec_json)
    try:
        request = _build_request(spec, files)
        body = request.read()
    except Exception as exc:
        return json.dumps({"bad": "".join(traceback.format_exception_only(exc)).strip()})
    t0 = time.perf_counter()
    ms = lambda: round((time.perf_counter() - t0) * 1000, 1)
    head = {"status": None, "headers": []}
    parts, live = [], {"streaming": False, "chunks": 0, "bytes": 0, "stopped": False}
    decoder = codecs.getincrementaldecoder("utf-8")("replace")
    done = asyncio.Event()

    def ctype():
        return next((v for k, v in head["headers"] if k.lower() == "content-type"), "")

    def on_start(message):
        head["status"] = message["status"]
        head["headers"] = [(k.decode("latin-1"), v.decode("latin-1")) for k, v in message.get("headers", [])]
        emit(json.dumps({"type": "head", "status": head["status"], "headers": head["headers"], "ms": ms()}))

    def on_body(chunk, more):
        parts.append(chunk)
        live["bytes"] += len(chunk)
        if more:
            live["streaming"] = True
        if live["streaming"] and chunk:
            live["chunks"] += 1
            textual = any(t in ctype() for t in _TEXTUAL)
            emit(json.dumps({"type": "chunk", "ms": ms(), "n": len(chunk),
                             "text": decoder.decode(chunk) if textual else None}))
            if live["chunks"] >= 2000 or live["bytes"] > 2_000_000:
                live["stopped"] = "limit"
                stop(key)

    _LIVE[key] = (asyncio.current_task(), done)
    error = None
    try:
        await _asgi_http(app, _scope(request), body, on_start, on_body, done)
    except asyncio.CancelledError:
        live["stopped"] = live["stopped"] or "user"
    except Exception as exc:
        # an unhandled exception in the app: a real server answers 500 and logs the traceback
        error = _snippet_traceback(exc)
        if head["status"] is None:
            head["status"], head["headers"], parts = 500, [["content-type", "text/plain; charset=utf-8"]], [b"Internal Server Error"]
    finally:
        if _LIVE.get(key, (None,))[0] is asyncio.current_task():
            del _LIVE[key]
    if head["status"] is None:
        head["status"] = 500
    raw = b"".join(parts)
    out = {"status": head["status"], "ms": ms(), "headers": head["headers"], "json": False,
           "streamed": live["chunks"] > 1, "chunks": live["chunks"], "bytes": len(raw), "stopped": live["stopped"]}
    try:
        out["reason"] = http.HTTPStatus(head["status"]).phrase
    except ValueError:
        out["reason"] = ""
    kind = ctype()
    if kind.startswith("image/") and len(raw) < 3_000_000:
        out["image"] = f"data:{kind.split(';')[0]};base64," + base64.b64encode(raw).decode("ascii")
        out["body"] = ""
    elif raw and not any(t in kind for t in _TEXTUAL) and b"\x00" in raw[:2048]:
        out["body"] = f"({len(raw):,} bytes of binary data, {kind or 'no content-type'})"
    else:
        text = raw.decode("utf-8", "replace")
        try:
            if live["chunks"] > 1:  # a real stream: keep it as sent (one chunk = middleware re-streaming JSON)
                raise ValueError
            out["body"], out["json"] = json.dumps(json.loads(text), indent=2, ensure_ascii=False), True
        except ValueError:
            out["body"] = text
        out["body"] = out["body"][:200000]
    if error:
        out["error"] = error
    return json.dumps(out)


def stop(key):
    """Stop the request this block is streaming (like closing the browser tab)."""
    entry = _LIVE.pop(key, None)
    if entry:
        task, done = entry
        done.set()
        task.cancel()


class _PanelSocket:
    def __init__(self, app, scope, emit):
        self.app, self.scope, self.emit = app, scope, emit
        self.inbox = asyncio.Queue()
        self.state = "connecting"
        self.client_closed = False
        self.task = None

    def say(self, **event):
        self.emit(json.dumps(event))

    async def run(self):
        from starlette.websockets import WebSocketDisconnect

        async def receive():
            message = await self.inbox.get()
            self.emit(None)  # route the handler's prints to this socket's block
            return message

        async def send(message):
            kind = message["type"]
            if self.client_closed and kind in ("websocket.send", "websocket.close"):
                raise OSError("the client has disconnected")
            if kind == "websocket.accept":
                self.state = "open"
                self.say(type="open", subprotocol=message.get("subprotocol"))
            elif kind == "websocket.send":
                data = message.get("bytes")
                if data is not None:
                    self.say(type="recv", text=None, bytes=len(data), preview=data[:64].hex(" "))
                else:
                    self.say(type="recv", text=message.get("text", ""))
            elif kind == "websocket.close":
                self.state = "closed"
                self.say(type="close", code=message.get("code", 1000), reason=message.get("reason") or "", by="server")
            elif kind == "websocket.http.response.start":
                self.state = "closed"
                self.say(type="denied", status=message["status"])

        self.task = asyncio.current_task()
        self.inbox.put_nowait({"type": "websocket.connect"})
        error = None
        try:
            await self.app(self.scope, receive, send)
        except (WebSocketDisconnect, asyncio.CancelledError):
            pass
        except Exception as exc:
            error = _snippet_traceback(exc)
        if self.state == "connecting":   # the handler returned (or failed) before accept: the handshake is refused
            self.say(type="denied", status=500 if error else 403)
        elif self.state == "open" and not self.client_closed:
            self.say(type="close", code=1011 if error else 1000, by="server",
                     reason="the handler raised an exception" if error else "the handler returned")
        return json.dumps({"error": error})


async def ws_open(key, app, path, headers_json, emit):
    import httpx
    ws_close(key)
    headers = json.loads(headers_json or "{}")
    for k, v in (("connection", "upgrade"), ("upgrade", "websocket"), ("sec-websocket-key", "testserver=="),
                 ("sec-websocket-version", "13")):
        headers.setdefault(k, v)
    request = httpx.Request("GET", "ws://testserver" + path, headers=headers)
    sock = _PanelSocket(app, _scope(request, kind="websocket"), emit)
    _SOCKETS[key] = sock
    try:
        return await sock.run()
    finally:
        if _SOCKETS.get(key) is sock:
            del _SOCKETS[key]


def ws_send(key, text):
    sock = _SOCKETS.get(key)
    if sock is None or sock.state != "open":
        return False
    sock.inbox.put_nowait({"type": "websocket.receive", "text": text})
    return True


def ws_close(key, code=1000):
    sock = _SOCKETS.pop(key, None)
    if sock is None:
        return False
    sock.client_closed = True
    sock.inbox.put_nowait({"type": "websocket.disconnect", "code": code})
    if sock.task is not None:  # a handler that never reads again is stopped after a second
        asyncio.get_event_loop().call_later(1.0, lambda: sock.task.done() or sock.task.cancel())
    return True
`;

const ready = (async () => {
  py = await loadPyodide();
  const src = await (await fetch("harness.py", { cache: "no-cache" })).text();
  py.FS.writeFile("/home/pyodide/harness.py", src);
  py.FS.writeFile("/home/pyodide/_sky.py", SKY_PY);
  py.runPython("import os; os.environ['MPLBACKEND'] = 'Agg'");
  py.runPython("import sys; sys.path.insert(0, '/home/pyodide'); import harness; import warnings; warnings.filterwarnings('ignore', category=FutureWarning); warnings.filterwarnings('ignore', category=DeprecationWarning); warnings.filterwarnings('ignore', message='.*(non-GUI backend|non-interactive).*')");
  py.setStdout({ batched: (s) => postMessage({ id: currentId, type: "stdout", data: s + "\n" }) });
  py.setStderr({ batched: (s) => postMessage({ id: currentId, type: "stderr", data: s + "\n" }) });
  postMessage({ type: "ready" });
})().catch((e) => postMessage({ type: "fatal", data: String(e) }));

const imports = (code, name) => new RegExp(`^\\s*(?:import|from)\\s+${name}\\b`, "m").test(code);

async function pip(name, id, note) {
  if (pipDone[name]) return;
  if (note) postMessage({ id, type: "status", data: note });
  postMessage({ id, type: "timer", ms: 180000 }); // downloads do not count towards the run time limit
  try {
    await py.loadPackage("micropip", { messageCallback: () => {} });
    await py.runPythonAsync(`import micropip\nawait micropip.install(${JSON.stringify(PIP[name])})`);
    if (name === "plotly") py.runPython("import _sky; _sky.plotly_hook()");
    pipDone[name] = true;
  } catch (e) {
    const msg = String(e && e.message ? e.message : e).trim().split("\n").slice(-2).join("\n");
    postMessage({ id, type: "stderr", data: `Could not install ${name} (are you offline?): ${msg}\n` });
    throw e;
  }
}

// FastAPI: the pure-Python wheels come straight from PyPI's file host, all in parallel and checked
// against their sha256 (no micropip, no index lookups); pydantic & co. come from the Pyodide CDN at
// the same time. Started in the background when a lesson has a fastapi-run block (see "preload").
const FASTAPI_DEPS = ["pydantic", "ssl", "typing-extensions", "idna", "certifi"];
const B64 = (hex) => btoa(String.fromCharCode(...hex.match(/../g).map((x) => parseInt(x, 16))));
let fastapiP = null;
function installFastapi(id) {
  if (!fastapiP) {
    fastapiP = (async () => {
      const t0 = performance.now();
      const deps = py.loadPackage(FASTAPI_DEPS, { messageCallback: () => {} });
      const wheels = await Promise.all(WHEELS.map(async ([file, path, sha]) => {
        const r = await fetch(`https://files.pythonhosted.org/packages/${path}/${file}`, { integrity: "sha256-" + B64(sha) });
        if (!r.ok) throw new Error(`${file}: HTTP ${r.status}`);
        return r.arrayBuffer();
      }));
      await deps;
      const site = py.runPython("import sysconfig; sysconfig.get_paths()['purelib']");
      wheels.forEach((buf) => py.unpackArchive(buf, "wheel", { extractDir: site }));
      py.runPython("import importlib; importlib.invalidate_caches(); import _sky; _sky.asgi_setup()");
      fastapiMs = Math.round(performance.now() - t0);
    })().catch((e) => { fastapiP = null; throw e; });
  }
  return fastapiP;
}
let fastapiMs = 0;

async function loadFastapi(id) {
  if (!fastapiMs) {
    postMessage({ id, type: "status", data: `Installing FastAPI (first use only): ${WHEELS.length} wheels from PyPI (0.5 MB) and Pydantic + ssl from the Pyodide CDN (2.7 MB)…` });
    postMessage({ id, type: "timer", ms: 180000 }); // downloads do not count towards the run time limit
  }
  try {
    await installFastapi(id);
  } catch (e) {
    const msg = String(e && e.message ? e.message : e).trim().split("\n").slice(-2).join("\n");
    postMessage({ id, type: "stderr", data: `Could not install FastAPI (are you offline?): ${msg}\n` });
    throw e;
  }
}

async function loadPkgs(code, id, lessons) {
  try {
    if (!hashOk && /hashlib|hmac/.test(code)) {
      // the default hashlib has no OpenSSL-backed functions (pbkdf2_hmac, scrypt)
      await py.loadPackage("hashlib", { messageCallback: () => {} });
      py.runPython("import importlib, hashlib; importlib.reload(hashlib)");
      hashOk = true;
    }
    const mpl = lessons && (imports(code, "matplotlib") || imports(code, "seaborn"));
    const plotly = lessons && imports(code, "plotly");
    if ((mpl && !mplReady) || (plotly && !pipDone.plotly)) {
      postMessage({ id, type: "status", data: "Loading plotting library…" });
      postMessage({ id, type: "timer", ms: 180000 });
    }
    if (lessons && imports(code, "seaborn")) {
      await py.loadPackage(["matplotlib", "pandas"], { messageCallback: () => {} });
      await pip("seaborn", id);
    }
    if (plotly) {
      // Plotly Express builds a data frame even from plain lists
      await py.loadPackage(/plotly\.express/.test(code) ? ["numpy", "pandas"] : ["numpy"], { messageCallback: () => {} });
      await pip("plotly", id);
    }
    if (lessons && ["fastapi", "starlette", "httpx", "python_multipart", "multipart"].some((m) => imports(code, m)))
      await loadFastapi(id);
    await py.loadPackagesFromImports(code, { messageCallback: () => {} });
    if (mpl) mplReady = true;
  } catch (e) {
    /* missing packages surface as ImportError when the code runs */
  } finally {
    postMessage({ id, type: "timer", ms: 0 }); // restart the normal run time limit
  }
}

// Send matplotlib PNGs and Plotly figures produced by the last run, then free them.
function flushFigures(id) {
  const sky = py.pyimport("_sky");
  try {
    const pImgs = sky.mpl_flush(), pPlots = sky.plotly_flush();
    const imgs = pImgs.toJs({ dict_converter: Object.fromEntries }), plots = pPlots.toJs();
    pImgs.destroy(); pPlots.destroy();
    imgs.forEach((im) => postMessage({ id, type: "image", data: im }));
    plots.forEach((p) => postMessage({ id, type: "plotly", data: p }));
  } catch (_) {
    /* a broken figure must not hide the run's real output */
  } finally {
    sky.destroy();
  }
}

const apps = new Map(); // fastapi-run block key -> namespace that holds `app`

async function runSnippet(id, code, keepAs) {
  await loadPkgs(code, id, true);
  py.runPython("import _sky");
  const ns = py.globals.get("dict")();
  // Run snippets as a real script: without __name__, classes report their module as "builtins"
  // (which breaks pydantic's from_attributes) and `if __name__ == "__main__":` never runs.
  ns.set("__name__", "__main__");
  let repr = null;
  let kept = false;
  try {
    const result = await py.runPythonAsync(code, { globals: ns, filename: "snippet.py" });
    const sky = py.pyimport("_sky");
    try { repr = sky.finish(result); } catch (_) { repr = null; }
    sky.destroy();
    if (result && result.destroy) result.destroy();
    if (keepAs) {
      if (!ns.has("app")) throw new Error("NameError: a fastapi-run block must define a FastAPI instance named `app`.");
      const old = apps.get(keepAs);
      if (old) old.destroy();
      apps.delete(keepAs);
      while (apps.size >= 8) { const [k, v] = apps.entries().next().value; hangUp(k); v.destroy(); apps.delete(k); }
      apps.set(keepAs, ns);
      kept = true;
    }
  } finally {
    flushFigures(id);
    if (!kept) ns.destroy();
  }
  return repr;
}

// Stop whatever a block's panel has open (a streamed response, a WebSocket).
function hangUp(key) {
  if (!fastapiMs) return;
  const sky = py.pyimport("_sky");
  try { sky.stop(key); sky.ws_close(key); } finally { sky.destroy(); }
}

// Call fn(app, sky) with the `app` a fastapi-run block defined; "NOAPP" when Python restarted since.
async function withApp(id, key, fn) {
  const ns = apps.get(key);
  if (!ns) { postMessage({ id, type: "error", data: "NOAPP" }); return; }
  const sky = py.pyimport("_sky"), app = ns.get("app");
  try {
    return await fn(app, sky);
  } finally {
    app.destroy(); sky.destroy();
  }
}

onmessage = async (e) => {
  await ready;
  const { id, type } = e.data;
  if (id != null) currentId = id; // fire-and-forget messages (preload, app-stop) keep the current owner
  try {
    if (type === "judge") {
      const { code, track, pid, mode, lines } = e.data;
      if (!loadedTracks[track]) {
        const txt = await (await fetch(`../../data/problems/${track}.json`, { cache: "no-cache" })).text();
        py.globals.set("_T", txt);
        py.runPython(`harness.load_track(${JSON.stringify(track)}, _T)`);
        loadedTracks[track] = true;
      }
      py.globals.set("_CODE", code);
      py.globals.set("_LINES", JSON.stringify(lines || []));
      const ref = py.runPython(`harness._TRACKS[${JSON.stringify(track)}][${JSON.stringify(pid)}]["solution"]`);
      await loadPkgs(code + "\n" + ref, id, false);
      py.globals.set("_on_result", (s) => postMessage({ id, type: "progress", data: JSON.parse(s) }));
      const out = py.runPython(`harness.judge_problem(_CODE, ${JSON.stringify(track)}, ${JSON.stringify(pid)}, ${JSON.stringify(mode)}, _LINES, _on_result)`);
      postMessage({ id, type: "done", data: JSON.parse(out) });
    } else if (type === "run") {
      const repr = await runSnippet(id, e.data.code, null);
      postMessage({ id, type: "done", data: { repr } });
    } else if (type === "preload") {
      // a lesson with fastapi-run blocks is open: install and import FastAPI while the learner reads
      if (e.data.what === "fastapi" && !fastapiP) {
        await installFastapi(null);
        py.runPython("import fastapi, fastapi.testclient, fastapi.responses, starlette.websockets, python_multipart");
      }
    } else if (type === "app-run") {
      // fastapi-run: run the block, keep its namespace so the request panel can call `app` later
      const { code, key } = e.data;
      if (!imports(code, "fastapi")) await loadPkgs("import fastapi", id, true);
      hangUp(key);
      const repr = await runSnippet(id, code, key);
      const sky = py.pyimport("_sky"), app = apps.get(key).get("app");
      const routes = JSON.parse(sky.app_info(app));
      app.destroy(); sky.destroy();
      postMessage({ id, type: "done", data: { repr, routes } });
    } else if (type === "app-request") {
      const { key, spec, files } = e.data;
      const emit = (s) => {
        currentId = id; // prints between chunks belong to this request
        const d = JSON.parse(s);
        postMessage({ id, type: "live", data: d });
        if (d.type === "chunk") postMessage({ id, type: "timer", ms: 15000 }); // a live stream may run on
      };
      await withApp(id, key, async (app, sky) => {
        try {
          const out = await sky.app_request(key, app, JSON.stringify(spec), files || [], emit);
          postMessage({ id, type: "done", data: JSON.parse(out) });
        } finally {
          flushFigures(id);
        }
      });
    } else if (type === "app-stop") {
      hangUp(e.data.key);
    } else if (type === "ws-open") {
      const { key, path, headers } = e.data;
      const emit = (s) => {
        currentId = id; // prints from the handler belong to this socket's block
        if (s == null) return;
        const d = JSON.parse(s);
        postMessage({ id, type: "ws", data: d });
        if (d.type === "open") postMessage({ id, type: "timer", ms: -1 }); // open sockets have no time limit
      };
      await withApp(id, key, async (app, sky) => {
        const out = await sky.ws_open(key, app, path, JSON.stringify(headers || {}), emit);
        postMessage({ id, type: "done", data: JSON.parse(out) });
      });
    } else if (type === "ws-send" || type === "ws-close") {
      const sky = py.pyimport("_sky");
      try {
        const ok = type === "ws-send" ? sky.ws_send(e.data.key, e.data.text) : sky.ws_close(e.data.key);
        postMessage({ id, type: "done", data: { ok } });
      } finally { sky.destroy(); }
    }
  } catch (err) {
    let msg = String(err && err.message ? err.message : err);
    // keep the end of python tracebacks (most useful part)
    const lines = msg.split("\n").filter((l) => !l.includes("/lib/python3") && !l.includes("_pyodide") && !l.includes("/home/pyodide/_sky.py"));
    postMessage({ id, type: "error", data: lines.slice(-15).join("\n") });
  }
};
