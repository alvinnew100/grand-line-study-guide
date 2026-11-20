/* Pyodide worker: runs learner code off the main thread. */
importScripts("https://cdn.jsdelivr.net/pyodide/v0.26.4/full/pyodide.js");

let py = null;
let currentId = null;

const ready = (async () => {
  py = await loadPyodide();
  const src = await (await fetch("harness.py")).text();
  py.FS.writeFile("/home/pyodide/harness.py", src);
  py.runPython("import sys; sys.path.insert(0, '/home/pyodide'); import harness");
  py.setStdout({ batched: (s) => postMessage({ id: currentId, type: "stdout", data: s + "\n" }) });
  py.setStderr({ batched: (s) => postMessage({ id: currentId, type: "stderr", data: s + "\n" }) });
  postMessage({ type: "ready" });
})().catch((e) => postMessage({ type: "fatal", data: String(e) }));

async function loadPkgs(code) {
  try {
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
      const { code, spec, tests } = e.data;
      await loadPkgs(code);
      py.globals.set("_CODE", code);
      py.globals.set("_SPEC", JSON.stringify(spec));
      py.globals.set("_TESTS", JSON.stringify(tests));
      py.globals.set("_on_result", (s) => postMessage({ id, type: "progress", data: JSON.parse(s) }));
      const out = py.runPython("harness.run_tests_json(_CODE, _SPEC, _TESTS, _on_result)");
      postMessage({ id, type: "done", data: JSON.parse(out) });
    } else if (type === "run") {
      const { code } = e.data;
      await loadPkgs(code);
      const ns = py.globals.get("dict")();
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
