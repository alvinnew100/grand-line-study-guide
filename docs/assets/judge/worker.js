/* Pyodide worker: runs learner code off the main thread. */
importScripts("https://cdn.jsdelivr.net/pyodide/v0.26.4/full/pyodide.js");

let py = null;
let currentId = null;
const loadedTracks = {};
let hashOk = false;

// Pure-Python wheels installed from PyPI with micropip on first use (lessons only, never the judge).
// Versions are pinned and checked against Pyodide 0.26.4 (Python 3.12, pydantic 2.7.0, pydantic-core 2.18.1,
// matplotlib 3.5.2, pandas 2.2.0); keep AUTHORING.md in step when changing them.
const PIP = {
  seaborn: ["seaborn==0.13.2"],
  plotly: ["plotly==6.0.1", "narwhals==1.31.0"],
  fastapi: ["ssl", "fastapi==0.115.6", "starlette==0.41.3", "httpx==0.28.1", "httpcore==1.0.7", "anyio==4.7.0", "sniffio==1.3.1", "h11==0.14.0"],
};
const pipDone = {};
let mplReady = false;

// Lesson-only helpers (figures, Plotly capture, FastAPI without threads). Kept out of harness.py so the
// judge never imports matplotlib or FastAPI.
const SKY_PY = String.raw`
import base64, io, json, sys, time

PLOTLY = []
_PARK = object()


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

def _drive(coro):
    """Run an ASGI coroutine to completion synchronously (works while it never waits on real I/O)."""
    try:
        while True:
            got = coro.send(None)
            if got is not None:
                try:
                    coro.close()
                except RuntimeError:
                    pass  # a task group inside the app refuses to stop early; report the real cause below
                raise RuntimeError(
                    "This request waited on real async I/O (asyncio.sleep, streaming, a background "
                    "task or @app.middleware), which the in-browser TestClient cannot do without threads. "
                    "Use the request panel, or 'await' an httpx.AsyncClient (see the lesson notes).")
    except StopIteration as stop:
        return stop.value


class _Park:
    def __await__(self):
        yield _PARK


def _scope(request, root_path=""):
    url = request.url
    port = url.port or (443 if url.scheme == "https" else 80)
    return {
        "type": "http", "asgi": {"version": "3.0"}, "http_version": "1.1",
        "method": request.method, "scheme": url.scheme,
        "path": url.path, "raw_path": url.raw_path.split(b"?")[0], "query_string": url.query,
        "root_path": root_path, "headers": [(k.lower(), v) for k, v in request.headers.raw],
        "server": (url.host, port), "client": ("testclient", 50000), "extensions": {},
    }


def asgi_setup():
    import anyio.to_thread
    import httpx

    async def run_sync(func, *args, abandon_on_cancel=False, cancellable=None, limiter=None):
        # Pyodide has no threads: run sync endpoints and dependencies inline.
        return func(*args)

    anyio.to_thread.run_sync = run_sync

    class SyncASGITransport(httpx.BaseTransport):
        def __init__(self, app, raise_server_exceptions=True, root_path=""):
            self.app, self.raise_server_exceptions, self.root_path = app, raise_server_exceptions, root_path

        def handle_request(self, request):
            body = request.read()
            pending = [{"type": "http.request", "body": body, "more_body": False}]
            state = {"status": None, "headers": [], "parts": []}

            async def receive():
                if pending:
                    return pending.pop()
                return {"type": "http.disconnect"}

            async def send(message):
                if message["type"] == "http.response.start":
                    state["status"], state["headers"] = message["status"], message.get("headers", [])
                elif message["type"] == "http.response.body":
                    state["parts"].append(message.get("body", b""))

            try:
                _drive(self.app(_scope(request, self.root_path), receive, send))
            except Exception:
                if self.raise_server_exceptions:
                    raise
                if state["status"] is None:
                    state["status"], state["parts"] = 500, [b"Internal Server Error"]
            return httpx.Response(state["status"], headers=state["headers"],
                                  content=b"".join(state["parts"]), request=request)

    class TestClient(httpx.Client):
        """Drop-in for fastapi.testclient.TestClient that needs no threads (Pyodide)."""
        __test__ = False

        def __init__(self, app, base_url="http://testserver", raise_server_exceptions=True,
                     root_path="", cookies=None, headers=None, follow_redirects=True, **_):
            self.app = app
            self._lifespan = None
            super().__init__(transport=SyncASGITransport(app, raise_server_exceptions, root_path),
                             base_url=base_url, headers=headers, cookies=cookies,
                             follow_redirects=follow_redirects)

        def __enter__(self):
            inbox = [{"type": "lifespan.startup"}]
            sent = []

            async def receive():
                while not inbox:
                    await _Park()
                return inbox.pop(0)

            async def send(message):
                sent.append(message["type"])

            coro = self.app({"type": "lifespan", "asgi": {"version": "3.0"}, "state": {}}, receive, send)
            self._lifespan = (coro, inbox)
            self._step(coro)
            if "lifespan.startup.failed" in sent:
                raise RuntimeError("Application startup failed")
            return self

        @staticmethod
        def _step(coro):
            try:
                while True:
                    got = coro.send(None)
                    if got is _PARK:
                        return
                    if got is not None:
                        raise RuntimeError("Lifespan code waited on real async I/O, which needs the event loop.")
            except StopIteration:
                pass

        def __exit__(self, *exc):
            if self._lifespan:
                coro, inbox = self._lifespan
                inbox.append({"type": "lifespan.shutdown"})
                self._step(coro)
                self._lifespan = None
            self.close()

    import starlette.testclient
    import fastapi.testclient
    starlette.testclient.TestClient = TestClient
    fastapi.testclient.TestClient = TestClient


def app_info(app):
    """Routes of a FastAPI app, with an example JSON body built from the OpenAPI schema."""
    try:
        spec = app.openapi()
    except Exception:
        spec = {"paths": {}}
    comps = spec.get("components", {}).get("schemas", {})

    def example(schema, depth=0):
        if depth > 4 or not isinstance(schema, dict):
            return None
        if "$ref" in schema:
            return example(comps.get(schema["$ref"].split("/")[-1], {}), depth + 1)
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
            return {k: example(v, depth + 1) for k, v in props.items() if k in required or depth <= 1}
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
            body = None
            content = (op.get("requestBody") or {}).get("content", {})
            if "application/json" in content:
                body = json.dumps(example(content["application/json"].get("schema", {})), indent=2)
            routes.append({"method": method.upper(), "path": path, "body": body, "summary": op.get("summary", "")})
    return json.dumps(routes)


async def app_request(app, method, path, body, headers_json):
    import httpx, traceback
    headers = json.loads(headers_json or "{}")
    content = body.encode() if body else None
    if content and not any(k.lower() == "content-type" for k in headers):
        headers["content-type"] = "application/json"
    transport = httpx.ASGITransport(app=app)
    t0 = time.perf_counter()
    try:
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            r = await client.request(method, path, content=content, headers=headers)
    except Exception as exc:
        # an unhandled exception in the app: a real server answers 500 and logs the traceback
        # (here only the learner's own frames, not the framework's)
        frames = [f for f in traceback.extract_tb(exc.__traceback__) if f.filename == "snippet.py"]
        print("Traceback (most recent call last):\n" + "".join(traceback.format_list(frames))
              + "".join(traceback.format_exception_only(exc)), end="", file=sys.stderr)
        return json.dumps({"status": 500, "reason": "Internal Server Error", "ms": round((time.perf_counter() - t0) * 1000, 1),
                           "headers": [["content-type", "text/plain; charset=utf-8"]], "body": "Internal Server Error",
                           "json": False, "error": "".join(traceback.format_exception_only(exc)).strip()})
    ms = (time.perf_counter() - t0) * 1000
    try:
        data = r.json()
        text = json.dumps(data, indent=2, ensure_ascii=False)
        is_json = True
    except Exception:
        text, is_json = r.text, False
    return json.dumps({"status": r.status_code, "reason": r.reason_phrase, "ms": round(ms, 1),
                       "headers": list(r.headers.items()), "body": text[:200000], "json": is_json})
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
    if (name === "fastapi") py.runPython("import _sky; _sky.asgi_setup()");
    if (name === "plotly") py.runPython("import _sky; _sky.plotly_hook()");
    pipDone[name] = true;
  } catch (e) {
    const msg = String(e && e.message ? e.message : e).trim().split("\n").slice(-2).join("\n");
    postMessage({ id, type: "stderr", data: `Could not install ${name} (are you offline?): ${msg}\n` });
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
    if (lessons && (imports(code, "fastapi") || imports(code, "starlette") || imports(code, "httpx")))
      await pip("fastapi", id, "Installing FastAPI (first use downloads about 4 MB)…");
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
      while (apps.size >= 8) { const [k, v] = apps.entries().next().value; v.destroy(); apps.delete(k); }
      apps.set(keepAs, ns);
      kept = true;
    }
  } finally {
    flushFigures(id);
    if (!kept) ns.destroy();
  }
  return repr;
}

onmessage = async (e) => {
  await ready;
  const { id, type } = e.data;
  currentId = id;
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
    } else if (type === "app-run") {
      // fastapi-run: run the block, keep its namespace so the request panel can call `app` later
      const { code, key } = e.data;
      if (!imports(code, "fastapi")) await loadPkgs("import fastapi", id, true);
      const repr = await runSnippet(id, code, key);
      const sky = py.pyimport("_sky"), app = apps.get(key).get("app");
      const routes = JSON.parse(sky.app_info(app));
      app.destroy(); sky.destroy();
      postMessage({ id, type: "done", data: { repr, routes } });
    } else if (type === "app-request") {
      const { key, method, path, body, headers } = e.data;
      const ns = apps.get(key);
      if (!ns) { postMessage({ id, type: "error", data: "NOAPP" }); return; }
      const sky = py.pyimport("_sky"), app = ns.get("app");
      try {
        const out = await sky.app_request(app, method, path, body || "", JSON.stringify(headers || {}));
        postMessage({ id, type: "done", data: JSON.parse(out) });
      } finally {
        app.destroy(); sky.destroy();
        flushFigures(id);
      }
    }
  } catch (err) {
    let msg = String(err && err.message ? err.message : err);
    // keep the end of python tracebacks (most useful part)
    const lines = msg.split("\n").filter((l) => !l.includes("/lib/python3") && !l.includes("_pyodide") && !l.includes("/home/pyodide/_sky.py"));
    postMessage({ id, type: "error", data: lines.slice(-15).join("\n") });
  }
};
