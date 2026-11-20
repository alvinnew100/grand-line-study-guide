/* JavaScript and HTML/CSS runtimes for lessons and problems (the browser runs these natively). */
window.WebKit = (() => {
  const WORKER_SRC = `
    const fmt = (v) => { if (typeof v === "string") return v; try { const s = JSON.stringify(v); return s === undefined ? String(v) : s; } catch (e) { return String(v); } };
    onmessage = (e) => {
      const { code, entry, tests } = e.data, logs = [], con = {};
      ["log", "info", "warn", "error", "debug"].forEach((k) => (con[k] = (...a) => logs.push(a.map(fmt).join(" "))));
      con.table = (v) => logs.push(fmt(v));
      try {
        if (!entry) { const r = new Function("console", code)(con); postMessage({ logs, value: r === undefined ? null : fmt(r) }); return; }
        const fn = new Function("console", code + "\\n;return (typeof " + entry + " !== 'undefined') ? " + entry + " : null;")(con);
        if (typeof fn !== "function" ) throw new Error("Define a function (or class) named " + entry);
        const results = tests.map((t, i) => {
          const t0 = performance.now(); let got = null, error = null;
          try { got = fn(...JSON.parse(JSON.stringify(t.args))); if (got === undefined) got = null; }
          catch (err) { error = String(err && err.stack ? err.stack.split("\\n").slice(0, 3).join("\\n") : err); }
          let got_s = null;
          if (!error) { try { got_s = JSON.stringify(got); } catch (err) { error = "Result is not JSON-serialisable: " + err; } }
          return { i, got_s, error, ms: +(performance.now() - t0).toFixed(2) };
        });
        postMessage({ results, logs });
      } catch (err) { postMessage({ fatal: String(err), logs }); }
    };`;
  let workerUrl = null;

  function runJs(code, entry, tests, timeoutMs = 8000) {
    if (!workerUrl) workerUrl = URL.createObjectURL(new Blob([WORKER_SRC], { type: "text/javascript" }));
    return new Promise((resolve) => {
      const w = new Worker(workerUrl);
      const timer = setTimeout(() => { w.terminate(); resolve({ fatal: "Time Limit Exceeded: stopped after " + timeoutMs / 1000 + " s (infinite loop?)", logs: [], tle: true }); }, timeoutMs);
      w.onmessage = (e) => { clearTimeout(timer); w.terminate(); resolve(e.data); };
      w.onerror = (e) => { clearTimeout(timer); w.terminate(); resolve({ fatal: e.message || "Script error", logs: [] }); };
      w.postMessage({ code, entry: entry || null, tests: tests || [] });
    });
  }

  // ---- comparison (mirrors harness.compare: exact | unordered | unordered_nested | float)
  const canon = (v) => (Array.isArray(v) ? "[" + v.map(canon).join(",") + "]"
    : v && typeof v === "object" ? "{" + Object.keys(v).sort().map((k) => JSON.stringify(k) + ":" + canon(v[k])).join(",") + "}" : JSON.stringify(v));
  function floatEq(a, b, tol) {
    if (typeof a === "number" && typeof b === "number") return Math.abs(a - b) <= tol * Math.max(1, Math.abs(a), Math.abs(b));
    if (Array.isArray(a) && Array.isArray(b)) return a.length === b.length && a.every((x, i) => floatEq(x, b[i], tol));
    if (a && b && typeof a === "object" && typeof b === "object") { const ka = Object.keys(a).sort(), kb = Object.keys(b).sort(); return canon(ka) === canon(kb) && ka.every((k) => floatEq(a[k], b[k], tol)); }
    return canon(a) === canon(b);
  }
  function eq(got, exp, mode, tol = 1e-6) {
    if (mode === "float") return floatEq(got, exp, tol);
    if (mode === "unordered" && Array.isArray(got) && Array.isArray(exp)) return canon(got.map(canon).sort()) === canon(exp.map(canon).sort());
    if (mode === "unordered_nested" && Array.isArray(got) && Array.isArray(exp)) {
      const c = (l) => l.map((x) => (Array.isArray(x) ? canon(x.map(canon).sort()) : canon(x))).sort();
      return canon(c(got)) === canon(c(exp));
    }
    return canon(got) === canon(exp);
  }

  // ---- HTML/CSS: render in a sandboxed iframe and evaluate checks inside it
  let seq = 0;
  function frameDoc(code, checks, id) {
    const probe = checks ? "<scr" + "ipt>window.addEventListener('load',function(){var cs=" + JSON.stringify(checks).replace(/</g, "\\u003c") +
      ";var out=cs.map(function(c){try{return{name:c.name,ok:!!(new Function('return ('+c.test+')')())}}catch(e){return{name:c.name,ok:false,error:String(e)}}});parent.postMessage({__web:" +
      JSON.stringify(id) + ",out:out},'*')});</scr" + "ipt>" : "";
    return code + probe;
  }
  function runWeb(code, checks, timeoutMs = 6000) {
    return new Promise((resolve) => {
      const id = "w" + ++seq, f = document.createElement("iframe");
      f.setAttribute("sandbox", "allow-scripts");
      f.style.cssText = "position:fixed;left:-9999px;top:0;width:1024px;height:768px;visibility:hidden";
      const done = (out) => { clearTimeout(timer); window.removeEventListener("message", onMsg); f.remove(); resolve(out); };
      const onMsg = (e) => { if (e.data && e.data.__web === id) done(e.data.out); };
      const timer = setTimeout(() => done(checks.map((c) => ({ name: c.name, ok: false, error: "The page did not finish loading" }))), timeoutMs);
      window.addEventListener("message", onMsg);
      f.srcdoc = frameDoc(code, checks, id);
      document.body.appendChild(f);
    });
  }
  function preview(host, code) {
    host.innerHTML = "";
    const f = document.createElement("iframe");
    f.setAttribute("sandbox", "allow-scripts allow-forms allow-modals");
    f.className = "web-preview";
    f.srcdoc = code;
    host.appendChild(f);
    return f;
  }

  // ---- lesson blocks
  function bar(label) {
    return `<div class="runnable-bar"><span class="lang">${label}</span><button class="reset" type="button">Reset</button><button class="run" type="button">▶ Run</button></div><div class="cm"></div>`;
  }
  function mountJs(el, code, makeEditor) {
    el.innerHTML = bar("JavaScript") + `<pre class="runnable-out"></pre>`;
    const original = code.replace(/\n$/, ""), out = el.querySelector(".runnable-out"), btn = el.querySelector(".run");
    const go = async () => {
      btn.disabled = true; out.textContent = "";
      const r = await runJs(cm.getValue(), null, []);
      (r.logs || []).forEach((l) => { const s = document.createElement("span"); s.textContent = l + "\n"; out.appendChild(s); });
      if (r.fatal) { const s = document.createElement("span"); s.className = "err"; s.textContent = r.fatal; out.appendChild(s); }
      else if (r.value && r.value !== "null") { const s = document.createElement("span"); s.textContent = r.value + "\n"; out.appendChild(s); }
      if (!out.textContent) out.textContent = "(no output)";
      btn.disabled = false;
    };
    const cm = makeEditor(el.querySelector(".cm"), original, "js", { auto: true, keys: { "Ctrl-Enter": go, "Cmd-Enter": go } });
    el.querySelector(".reset").onclick = () => cm.setValue(original);
    btn.onclick = go;
  }
  function mountHtml(el, code, makeEditor) {
    el.innerHTML = bar("HTML · CSS · JS") + `<div class="web-host"></div>`;
    const original = code.replace(/\n$/, ""), host = el.querySelector(".web-host");
    const go = () => preview(host, cm.getValue());
    const cm = makeEditor(el.querySelector(".cm"), original, "html", { auto: true, keys: { "Ctrl-Enter": go, "Cmd-Enter": go } });
    el.querySelector(".reset").onclick = () => { cm.setValue(original); go(); };
    el.querySelector(".run").onclick = go;
    go();
  }
  return { runJs, runWeb, eq, preview, mountJs, mountHtml };
})();
