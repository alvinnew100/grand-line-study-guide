/* Pyodide worker: runs learner code off the main thread. */
importScripts("https://cdn.jsdelivr.net/pyodide/v0.26.4/full/pyodide.js");

let py = null;
let currentId = null;
const loadedTracks = {};
let hashOk = false;

const ready = (async () => {
  py = await loadPyodide();
  const src = await (await fetch("harness.py", { cache: "no-cache" })).text();
  py.FS.writeFile("/home/pyodide/harness.py", src);
  py.runPython("import sys; sys.path.insert(0, '/home/pyodide'); import harness; import warnings; warnings.filterwarnings('ignore', category=FutureWarning); warnings.filterwarnings('ignore', category=DeprecationWarning)");
  py.setStdout({ batched: (s) => postMessage({ id: currentId, type: "stdout", data: s + "\n" }) });
  py.setStderr({ batched: (s) => postMessage({ id: currentId, type: "stderr", data: s + "\n" }) });
  postMessage({ type: "ready" });
})().catch((e) => postMessage({ type: "fatal", data: String(e) }));

async function loadPkgs(code) {
  try {
    if (!hashOk && /hashlib|hmac/.test(code)) {
      // the default hashlib has no OpenSSL-backed functions (pbkdf2_hmac, scrypt)
      await py.loadPackage("hashlib", { messageCallback: () => {} });
      py.runPython("import importlib, hashlib; importlib.reload(hashlib)");
      hashOk = true;
    }
    await py.loadPackagesFromImports(code, { messageCallback: () => {} });
  } catch (e) {
    /* missing packages surface as ImportError when the code runs */
  }
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
      await loadPkgs(code + "\n" + ref);
      py.globals.set("_on_result", (s) => postMessage({ id, type: "progress", data: JSON.parse(s) }));
      const out = py.runPython(`harness.judge_problem(_CODE, ${JSON.stringify(track)}, ${JSON.stringify(pid)}, ${JSON.stringify(mode)}, _LINES, _on_result)`);
      postMessage({ id, type: "done", data: JSON.parse(out) });
    } else if (type === "run") {
      const { code } = e.data;
      await loadPkgs(code);
      const ns = py.globals.get("dict")();
      // Run snippets as a real script: without __name__, classes report their module as "builtins"
      // (which breaks pydantic's from_attributes) and `if __name__ == "__main__":` never runs.
      ns.set("__name__", "__main__");
      let result;
      try {
        result = await py.runPythonAsync(code, { globals: ns, filename: "snippet.py" });
      } finally {
        ns.destroy();
      }
      let repr = null;
      if (result !== undefined && result !== null) {
        try { repr = String(result); } catch (_) {}
        if (result && result.destroy) result.destroy();
      }
      postMessage({ id, type: "done", data: { repr } });
    }
  } catch (err) {
    let msg = String(err && err.message ? err.message : err);
    // keep the end of python tracebacks (most useful part)
    const lines = msg.split("\n").filter((l) => !l.includes("/lib/python3") && !l.includes("_pyodide"));
    postMessage({ id, type: "error", data: lines.slice(-15).join("\n") });
  }
};
