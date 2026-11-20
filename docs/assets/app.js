/* Grand Line Study Guide — single-page app (no build step). */
(() => {
  "use strict";

  // ---------------------------------------------------------------- utils
  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const h = (html) => { const t = document.createElement("template"); t.innerHTML = html.trim(); return t.content.firstElementChild; };
  const fmt = (v) => { try { return JSON.stringify(v); } catch (_) { return String(v); } };
  const cache = new Map();
  async function getJSON(url) {
    if (!cache.has(url)) cache.set(url, fetch(url, { cache: "no-cache" }).then((r) => { if (!r.ok) throw new Error(`${r.status} ${url}`); return r.json(); }));
    return cache.get(url);
  }
  async function getText(url) {
    const k = "t:" + url;
    if (!cache.has(k)) cache.set(k, fetch(url, { cache: "no-cache" }).then((r) => { if (!r.ok) throw new Error(`${r.status} ${url}`); return r.text(); }));
    return cache.get(k);
  }
  const trunc = (s, n = 1500) => (s && s.length > n ? s.slice(0, n) + ` … (${s.length.toLocaleString()} chars)` : s);
  const debounce = (fn, ms) => { let t; return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); }; };

  // ---------------------------------------------------------------- storage
  const KEY = "glsg:v1";
  const store = (() => {
    let s = { lessons: {}, solved: {}, tried: {}, quiz: {}, code: {}, notes: {}, last: null, opts: {} };
    try { Object.assign(s, JSON.parse(localStorage.getItem(KEY) || "{}")); } catch (_) {}
    const save = debounce(() => { try { localStorage.setItem(KEY, JSON.stringify(s)); } catch (_) {} }, 250);
    return { get: () => s, save, set(fn) { fn(s); s._dirty = true; save(); cloudTouch(); }, replace(n) { s = Object.assign({ lessons: {}, solved: {}, tried: {}, quiz: {}, code: {}, notes: {}, opts: {} }, n); save(); } };
  })();
  let cloudTouch = () => {};
  const S = () => store.get();

  // ---------------------------------------------------------------- optional account (progress sync)
  const Cloud = (() => {
    const BASE = "https://xupqehazxffimjdvdgbh.supabase.co/rest/v1/rpc/";
    const KEY = "sb_publishable_r5G_XYJgL6BTRmahCPFniQ__Pr9qr0Y";
    const SKEY = "glsg:acct";
    let sess = null, timer = null, last = null, busy = false;
    try { sess = JSON.parse(localStorage.getItem(SKEY) || "null"); } catch (_) {}
    async function rpc(fn, body, keepalive) {
      const r = await fetch(BASE + fn, { method: "POST", keepalive: !!keepalive, headers: { apikey: KEY, "Content-Type": "application/json" }, body: JSON.stringify(body) });
      const j = await r.json().catch(() => null);
      if (!r.ok) throw new Error((j && j.message) || `Sync failed (${r.status})`);
      return j;
    }
    const creds = () => ({ p_username: sess.u, p_token: sess.t });
    function setSess(v) { sess = v; try { v ? localStorage.setItem(SKEY, JSON.stringify(v)) : localStorage.setItem(SKEY, "null"); } catch (_) {} }
    const clean = (o) => { const c = { ...o }; c._dirty = undefined; return c; };
    function merge(local, remote) {
      // union of both devices; on a conflict the local (unsynced) value wins
      const out = { ...remote, ...local };
      ["lessons", "solved", "quiz", "notes", "code", "tried", "opts"].forEach((k) => (out[k] = { ...(remote[k] || {}), ...(local[k] || {}) }));
      const a = { ...(remote.activity || {}) };
      Object.entries(local.activity || {}).forEach(([d, n]) => (a[d] = Math.max(a[d] || 0, n)));
      out.activity = a;
      return out;
    }
    async function push(keepalive) {
      if (!sess || busy) return;
      busy = true;
      try { await rpc("sg_save", { ...creds(), p_data: clean(S()) }, keepalive); S()._dirty = false; store.save(); last = new Date(); }
      catch (e) { if (/Session expired/.test(e.message)) setSess(null); throw e; }
      finally { busy = false; }
    }
    async function pull() {
      if (!sess) return false;
      const remote = (await rpc("sg_load", creds())) || {};
      const local = S(), dirty = local._dirty || !Object.keys(remote).length;
      store.replace(clean(dirty ? merge(local, remote) : merge(remote, local)));  // not dirty: the account copy wins
      last = new Date();
      if (dirty) await push();
      return true;
    }
    async function enter(fn, u, p) {
      u = (u || "").trim().toLowerCase();
      if (!/^[a-z0-9_]{3,20}$/.test(u)) throw new Error("Username must be 3-20 characters using a-z, 0-9 or _");
      if ((p || "").length < 6) throw new Error("Password must be at least 6 characters");
      const t = await rpc(fn, { p_username: u, p_password: p });
      setSess({ u, t });
      S()._dirty = true;   // first login on this device: keep what is here and add the account's data
      await pull();
    }
    cloudTouch = () => { if (!sess) return; clearTimeout(timer); timer = setTimeout(() => push().catch(() => {}), 4000); };
    document.addEventListener("visibilitychange", () => { if (document.hidden && sess && S()._dirty) push(true).catch(() => {}); });
    return {
      user: () => (sess ? sess.u : null), last: () => last, pull, push,
      register: (u, p) => enter("sg_register", u, p), login: (u, p) => enter("sg_login", u, p),
      async logout() { if (sess) { try { await push(); await rpc("sg_logout", creds()); } catch (_) {} } setSess(null); },
    };
  })();

  // ---------------------------------------------------------------- theme
  const root = document.documentElement;
  function applyTheme(t) { if (t) root.dataset.theme = t; else delete root.dataset.theme; }
  const isDark = () => root.dataset.theme ? root.dataset.theme === "dark" : matchMedia("(prefers-color-scheme: dark)").matches;
  try { applyTheme(localStorage.getItem("glsg:theme")); } catch (_) {}
  $("#themeBtn").onclick = () => {
    const next = isDark() ? "light" : "dark";
    applyTheme(next);
    try { localStorage.setItem("glsg:theme", next); } catch (_) {}
    route();
  };

  // ---------------------------------------------------------------- data
  const DATA = { index: [], tracks: {}, problemTrack: {} };
  async function loadAll() {
    DATA.index = await getJSON("data/index.json");
    const metas = await Promise.all(DATA.index.map((t) => getJSON(`data/tracks/${t.id}.json`).catch(() => null)));
    metas.forEach((m) => {
      if (!m) return;
      DATA.tracks[m.id] = m;
      m.modules.forEach((mod) => (mod.problems || []).forEach((pid) => (DATA.problemTrack[pid] = { track: m.id, module: mod.id })));
    });
  }
  async function getProblem(pid) {
    const loc = DATA.problemTrack[pid];
    if (!loc) return null;
    const all = await getJSON(`data/problems/${loc.track}.json`);
    return all[pid] ? { ...all[pid], _loc: loc } : null;
  }
  function trackProgress(t) {
    const s = S();
    let total = 0, done = 0;
    t.modules.forEach((m) => {
      (m.lessons || []).forEach((l) => { total++; if (s.lessons[`${t.id}/${l.id}`]) done++; });
      (m.problems || []).forEach((p) => { total++; if (s.solved[p]) done++; });
    });
    return { total, done, pct: total ? Math.round((100 * done) / total) : 0 };
  }

  // ---------------------------------------------------------------- sidebar
  const sidebar = $("#sidebar"), scrim = $("#scrim");
  const closeMenu = () => { sidebar.classList.remove("open"); scrim.classList.remove("show"); };
  $("#menuBtn").onclick = () => { sidebar.classList.toggle("open"); scrim.classList.toggle("show", sidebar.classList.contains("open")); };
  scrim.onclick = closeMenu;
  function renderSidebar(activeTrack, activeLesson) {
    let html = `<a class="side-track ${!activeTrack ? "active" : ""}" href="#/"><span class="ico">🍃</span><span class="lbl">Home</span></a>
      <a class="side-track" href="#/roadmap"><span class="ico">🗺️</span><span class="lbl">Roadmap</span></a>
      <a class="side-track" href="#/problems"><span class="ico">🧩</span><span class="lbl">All problems</span></a>
      <a class="side-track" href="#/gallery"><span class="ico">🖼️</span><span class="lbl">Gallery</span></a>`;
    let group = null;
    DATA.index.forEach((ti) => {
      const t = DATA.tracks[ti.id];
      if (!t) return;
      if (t.group !== group) { group = t.group; html += `<div class="side-group">${esc(group || "Tracks")}</div>`; }
      const p = trackProgress(t);
      html += `<a class="side-track ${activeTrack === t.id ? "active" : ""}" href="#/track/${t.id}"><span class="ico">${esc(t.icon || "📘")}</span><span class="lbl">${esc(t.title)}</span><span class="pct">${p.pct}%</span></a>`;
      if (activeTrack === t.id) {
        html += `<div class="side-sub">`;
        t.modules.forEach((m) => (m.lessons || []).forEach((l) => {
          const done = S().lessons[`${t.id}/${l.id}`];
          html += `<a class="${activeLesson === l.id ? "active" : ""} ${done ? "done" : ""}" href="#/lesson/${t.id}/${l.id}">${esc(l.title)}</a>`;
        }));
        html += `</div>`;
      }
    });
    sidebar.innerHTML = html;
    const act = $(".side-sub a.active", sidebar);
    if (act) act.scrollIntoView({ block: "nearest" });
  }

  // ---------------------------------------------------------------- markdown
  const CALLOUTS = { NOTE: "Note", TIP: "Tip", WARNING: "Warning", INTERVIEW: "Interview" , IMPORTANT: "Important", CAUTION: "Warning"};
  function protectMath(md) {
    const store = [];
    const parts = md.split(/(```[\s\S]*?```|~~~[\s\S]*?~~~|`[^`\n]+`)/g);
    for (let i = 0; i < parts.length; i += 2) {
      let p = parts[i];
      p = p.replace(/\\\$/g, "@@DOLLAR@@");
      p = p.replace(/\$\$([\s\S]+?)\$\$/g, (_, m) => { store.push({ tex: m, display: true }); return `@@MATH${store.length - 1}@@`; });
      p = p.replace(/\$([^\s$](?:[^$\n]*?[^\s$])?)\$/g, (_, m) => { store.push({ tex: m, display: false }); return `@@MATH${store.length - 1}@@`; });
      parts[i] = p;
    }
    return { md: parts.join(""), store };
  }
  function restoreMath(html, store) {
    return html
      .replace(/@@MATH(\d+)@@/g, (_, i) => {
        const m = store[+i];
        try { return katex.renderToString(decodeEntities(m.tex), { displayMode: m.display, throwOnError: false }); }
        catch (_) { return esc(m.tex); }
      })
      .replace(/@@DOLLAR@@/g, "$");
  }
  const decodeEntities = (s) => { const t = document.createElement("textarea"); t.innerHTML = s; return t.value; };

  const renderer = new marked.Renderer();
  let blockSeq = 0;
  const pending = {};
  renderer.code = function (code, info) {
    // marked v12 passes (code, infostring, escaped)
    if (typeof code === "object") { info = code.lang; code = code.text; }
    const infoStr = (info || "").trim();
    const lang = infoStr.split(/\s+/)[0];
    const id = `blk${++blockSeq}`;
    if (lang === "quiz") { pending[id] = { type: "quiz", code }; return `<div class="quiz" id="${id}"></div>`; }
    if (lang === "mermaid") { pending[id] = { type: "mermaid", code }; return `<div class="mermaid-wrap" id="${id}"></div>`; }
    if (lang === "python-run" || lang === "py-run") { pending[id] = { type: "py", code }; return `<div class="runnable" id="${id}"></div>`; }
    if (lang === "sql-run") {
      const ds = (infoStr.match(/dataset=([\w-]+)/) || [])[1];
      pending[id] = { type: "sql", code, dataset: ds };
      return `<div class="runnable" id="${id}"></div>`;
    }
    let hl;
    try { hl = lang && hljs.getLanguage(lang) ? hljs.highlight(code, { language: lang }).value : hljs.highlightAuto(code).value; }
    catch (_) { hl = esc(code); }
    return `<pre><code class="hljs language-${esc(lang)}">${hl}</code></pre>`;
  };
  renderer.heading = function (text, level, raw) {
    if (typeof text === "object") { level = text.depth; raw = text.text; text = this.parser.parseInline(text.tokens); }
    const slug = String(raw).toLowerCase().replace(/<[^>]+>/g, "").replace(/[^\w]+/g, "-").replace(/^-|-$/g, "");
    return `<h${level} id="${slug}">${text}</h${level}>`;
  };
  marked.setOptions({ renderer, gfm: true, breaks: false });

  function renderMarkdown(md, container, ctx = {}) {
    const { md: safe, store: math } = protectMath(md || "");
    container.innerHTML = restoreMath(marked.parse(safe), math);
    // callouts
    $$("blockquote", container).forEach((bq) => {
      const first = bq.firstElementChild;
      if (!first) return;
      const m = first.innerHTML.match(/^\s*\[!(\w+)\]\s*/);
      if (!m) return;
      const kind = m[1].toUpperCase();
      first.innerHTML = first.innerHTML.slice(m[0].length);
      bq.classList.add("callout", (CALLOUTS[kind] || "Note").toLowerCase());
      bq.insertBefore(h(`<span class="callout-title">${CALLOUTS[kind] || kind}</span>`), first);
    });
    $$("a[href^='http']", container).forEach((a) => { a.target = "_blank"; a.rel = "noopener"; });
    // special blocks
    Object.keys(pending).forEach((id) => {
      const el = container.querySelector("#" + id);
      if (!el) return;
      const b = pending[id];
      delete pending[id];
      try {
        if (b.type === "quiz") mountQuiz(el, b.code, ctx);
        else if (b.type === "mermaid") mountMermaid(el, b.code);
        else if (b.type === "py") mountRunnable(el, b.code, "python");
        else if (b.type === "sql") mountRunnable(el, b.code, "sql", b.dataset);
      } catch (e) {
        el.innerHTML = `<pre class="io err">${esc(e.message)}</pre>`;
      }
    });
    $$(".widget[data-widget]", container).forEach((el) => window.Widgets && window.Widgets.mount(el));
  }

  // ---------------------------------------------------------------- mermaid (lazy)
  let mermaidP = null;
  function loadScript(src) {
    return new Promise((res, rej) => { const s = document.createElement("script"); s.src = src; s.onload = res; s.onerror = rej; document.head.appendChild(s); });
  }
  let mermaidSeq = 0;
  async function mountMermaid(el, code) {
    el.textContent = "Rendering diagram…";
    if (!mermaidP) mermaidP = loadScript("https://cdn.jsdelivr.net/npm/mermaid@10.9.1/dist/mermaid.min.js");
    await mermaidP;
    window.mermaid.initialize({ startOnLoad: false, theme: isDark() ? "dark" : "default", securityLevel: "strict", fontFamily: "Inter, sans-serif" });
    try {
      const { svg } = await window.mermaid.render(`mmd${++mermaidSeq}`, code);
      el.innerHTML = svg;
    } catch (e) {
      el.innerHTML = `<pre class="io">${esc(code)}</pre>`;
    }
  }

  // ---------------------------------------------------------------- quizzes
  function mountQuiz(el, json, ctx) {
    let items = JSON.parse(fixJson(json));
    if (!Array.isArray(items)) items = [items];
    const qkey = `${ctx.key || "q"}#${el.id}`;
    const saved = S().quiz[qkey] || {};
    el.innerHTML = `<div class="quiz-h"><b>✦ Check yourself</b><span class="quiz-score"></span></div>`;
    const score = $(".quiz-score", el);
    const upd = () => {
      const s = S().quiz[qkey] || {};
      const answered = Object.keys(s).length;
      const right = items.filter((it, i) => s[i] === it.answer).length;
      score.textContent = answered ? `${right}/${items.length} correct` : `${items.length} questions`;
    };
    items.forEach((it, i) => {
      const q = h(`<div class="qitem"><div class="qq"></div><div class="qopts"></div></div>`);
      renderInline($(".qq", q), `${i + 1}. ${it.q}`);
      const opts = $(".qopts", q);
      const reveal = (chosen) => {
        $$(".qopt", opts).forEach((b, j) => {
          b.disabled = true;
          if (j === it.answer) b.classList.add("right");
          else if (j === chosen) b.classList.add("wrong");
        });
        if (!$(".qexp", q)) {
          const ex = h(`<div class="qexp"></div>`);
          renderInline(ex, (chosen === it.answer ? "✅ **Correct.** " : "❌ **Not quite.** ") + (it.explain || ""));
          q.appendChild(ex);
        }
      };
      it.options.forEach((o, j) => {
        const b = h(`<button class="qopt" type="button"></button>`);
        renderInline(b, o);
        b.onclick = () => { store.set((s) => { (s.quiz[qkey] = s.quiz[qkey] || {})[i] = j; }); reveal(j); upd(); };
        opts.appendChild(b);
      });
      if (saved[i] !== undefined) reveal(saved[i]);
      el.appendChild(q);
    });
    const reset = h(`<button class="btn sm" type="button" style="margin-top:8px">Retry quiz</button>`);
    reset.onclick = () => { store.set((s) => delete s.quiz[qkey]); mountQuiz(el, json, ctx); };
    el.appendChild(reset);
    upd();
  }
  function fixJson(s) {
    // mirror of fix_json_backslashes() in tools/build.py: tolerate LaTeX commands inside JSON strings
    let out = "";
    for (let i = 0; i < s.length; i++) {
      const c = s[i];
      if (c !== "\\") { out += c; continue; }
      const nx = s[i + 1] || "", af = s[i + 2] || "";
      if (nx === "\\") { out += "\\\\"; i++; }
      else if (nx === '"' || nx === "/") { out += "\\" + nx; i++; }
      else if (nx === "u" && /^[0-9a-fA-F]{4}$/.test(s.slice(i + 2, i + 6))) { out += s.slice(i, i + 6); i += 5; }
      else if ("bfnrt".includes(nx) && nx && !/[A-Za-z]/.test(af)) { out += "\\" + nx; i++; }
      else out += "\\\\";
    }
    return out;
  }
  function renderInline(el, md) {
    const { md: safe, store: math } = protectMath(md || "");
    el.innerHTML = restoreMath(marked.parseInline(safe), math);
  }

  // ---------------------------------------------------------------- python runtime
  const Py = (() => {
    let worker = null, ready = null, seq = 0;
    const handlers = new Map();
    function start() {
      worker = new Worker("assets/judge/worker.js?v=5");
      ready = new Promise((res, rej) => {
        const onmsg = (e) => {
          if (e.data.type === "ready") res();
          else if (e.data.type === "fatal") rej(new Error(e.data.data));
        };
        worker.addEventListener("message", onmsg);
      });
      worker.addEventListener("message", (e) => {
        const hd = handlers.get(e.data.id);
        if (hd) hd(e.data);
      });
      worker.onerror = (e) => console.error("worker error", e);
    }
    function ensure() { if (!worker) start(); return ready; }
    function restart() { if (worker) worker.terminate(); worker = null; handlers.clear(); start(); }
    async function call(msg, onEvent, timeoutMs) {
      await ensure();
      const id = ++seq;
      return new Promise((resolve, reject) => {
        const timer = setTimeout(() => {
          handlers.delete(id);
          restart();
          reject(Object.assign(new Error("Time Limit Exceeded"), { tle: true }));
        }, timeoutMs);
        handlers.set(id, (d) => {
          if (d.type === "done") { clearTimeout(timer); handlers.delete(id); resolve(d.data); }
          else if (d.type === "error") { clearTimeout(timer); handlers.delete(id); reject(new Error(d.data)); }
          else onEvent && onEvent(d);
        });
        worker.postMessage({ ...msg, id });
      });
    }
    return {
      warm: () => ensure().catch(() => {}),
      isReady: () => !!worker,
      run: (code, onEvent, t = 30000) => call({ type: "run", code }, onEvent, t),
      judge: (code, track, pid, mode, lines, onEvent, t = 20000) => call({ type: "judge", code, track, pid, mode, lines }, onEvent, t),
    };
  })();

  // ---------------------------------------------------------------- SQL runtime
  const Sql = (() => {
    let SQLp = null;
    const dsCache = {};
    async function lib() {
      if (!SQLp) SQLp = loadScript("https://cdnjs.cloudflare.com/ajax/libs/sql.js/1.10.3/sql-wasm.min.js")
        .then(() => window.initSqlJs({ locateFile: (f) => `https://cdnjs.cloudflare.com/ajax/libs/sql.js/1.10.3/${f}` }));
      return SQLp;
    }
    async function db(dataset) {
      const SQL = await lib();
      const d = new SQL.Database();
      if (dataset) {
        if (!dsCache[dataset]) dsCache[dataset] = getText(`data/datasets/${dataset}.sql`);
        d.exec(await dsCache[dataset]);
      }
      return d;
    }
    async function run(query, dataset) {
      const d = await db(dataset);
      try {
        const t0 = performance.now();
        const res = d.exec(query);
        return { res, ms: performance.now() - t0 };
      } finally { d.close(); }
    }
    function table(r) {
      if (!r) return `<div class="meta">Query ran. No rows returned.</div>`;
      const rows = r.values.slice(0, 500);
      return `<table><thead><tr>${r.columns.map((c) => `<th>${esc(c)}</th>`).join("")}</tr></thead><tbody>${rows
        .map((row) => `<tr>${row.map((v) => `<td>${v === null ? '<span class="muted">NULL</span>' : esc(v)}</td>`).join("")}</tr>`)
        .join("")}</tbody></table><div class="meta">${r.values.length} row(s)${r.values.length > 500 ? " (showing 500)" : ""}</div>`;
    }
    return { run, table, warm: () => lib().catch(() => {}) };
  })();

  // ---------------------------------------------------------------- editors
  function cmTheme(wrapper) { wrapper.classList.toggle("cm-dark", true); }
  function makeEditor(host, value, mode, opts = {}) {
    const o = S().opts || {};
    const cm = CodeMirror(host, {
      value, mode: mode === "sql" ? "text/x-sqlite" : { name: "python", version: 3 },
      lineNumbers: opts.lineNumbers !== false, indentUnit: 4, tabSize: 4, indentWithTabs: false,
      matchBrackets: true, autoCloseBrackets: true, lineWrapping: !!o.wrap || !!opts.wrap,
      keyMap: o.vim ? "vim" : "default", viewportMargin: opts.auto ? Infinity : 10,
      extraKeys: {
        Tab: (c) => (c.somethingSelected() ? c.indentSelection("add") : c.replaceSelection("    ", "end")),
        "Shift-Tab": (c) => c.indentSelection("subtract"),
        "Ctrl-/": "toggleComment", "Cmd-/": "toggleComment",
        ...(opts.keys || {}),
      },
    });
    cmTheme(host);
    return cm;
  }

  function mountRunnable(el, code, lang, dataset) {
    el.innerHTML = `<div class="runnable-bar"><span class="lang">${lang === "sql" ? "SQL" + (dataset ? " · " + esc(dataset) : "") : "Python"}</span>
      <button class="reset" type="button">Reset</button><button class="run" type="button">▶ Run</button></div><div class="cm"></div>`;
    const out = h(lang === "sql" ? `<div class="sql-result" hidden></div>` : `<pre class="runnable-out"></pre>`);
    el.appendChild(out);
    const original = code.replace(/\n$/, "");
    const cm = makeEditor($(".cm", el), original, lang, { auto: true, keys: { "Ctrl-Enter": () => go(), "Cmd-Enter": () => go() } });
    const btn = $(".run", el);
    $(".reset", el).onclick = () => cm.setValue(original);
    async function go() {
      btn.disabled = true;
      btn.textContent = "Running…";
      if (lang === "sql") {
        out.hidden = false;
        out.innerHTML = `<div class="meta">Running…</div>`;
        try {
          const { res, ms } = await Sql.run(cm.getValue(), dataset);
          out.innerHTML = (res.length ? res.map(Sql.table).join("") : Sql.table(null)).replace(/<\/div>$/, ` · ${ms.toFixed(1)} ms</div>`);
        } catch (e) { out.innerHTML = `<div class="meta" style="color:var(--bad)">${esc(e.message)}</div>`; }
      } else {
        out.textContent = Py.isReady() ? "" : "Starting Python (first run downloads ~10 MB)…\n";
        let first = true;
        const write = (s, cls) => {
          if (first) { out.textContent = ""; first = false; }
          const span = document.createElement("span"); if (cls) span.className = cls; span.textContent = s; out.appendChild(span);
        };
        try {
          const r = await Py.run(cm.getValue(), (d) => write(d.data, d.type === "stderr" ? "err" : ""));
          if (r && r.repr && r.repr !== "None") write(r.repr + "\n");
          if (first) write("(no output)");
        } catch (e) { write((e.tle ? "⏱ Stopped after 30 s.\n" : "") + e.message, "err"); }
      }
      btn.disabled = false;
      btn.textContent = "▶ Run";
    }
    btn.onclick = go;
  }


  // ---------------------------------------------------------------- Ghibli stills & quotes
  const TRACK_FILM = { csapp: "laputa", python: "baron", "dsa-foundations": "mimi", "neet-arrays": "majo", "neet-window-stack": "howl",
    "neet-linked-trees": "totoro", "neet-heap-graphs": "mononoke", "neet-dp": "chihiro", "neet-greedy-math": "porco", sql: "kokurikozaka",
    databases: "nausicaa", ml: "kazetachinu", fastapi: "ponyo", mlops: "karigurashi", "ai-eng": "kimitachi", "llm-practice": "kaguyahime", os: "ged", "linux-cli": "yamada", vim: "marnie" };
  const Ghibli = {
    works: {}, list: [], quotes: [], note: "", terms: "",
    async load() {
      try {
        const m = await getJSON("assets/ghibli/manifest.json");
        this.list = m.works; this.terms = m.terms;
        m.works.forEach((w) => (this.works[w.id] = w));
        const q = await getJSON("assets/ghibli/quotes.json");
        this.quotes = q.quotes; this.note = q.note;
      } catch (_) {}
    },
    hash(str) { let x = 2166136261; for (let i = 0; i < str.length; i++) { x ^= str.charCodeAt(i); x = Math.imul(x, 16777619); } return x >>> 0; },
    still(workId, seed) {
      let w = this.works[workId];
      if (!w || !w.files.length) {
        const ok = this.list.filter((x) => x.files.length);
        if (!ok.length) return null;
        w = ok[this.hash("w" + seed) % ok.length];
      }
      const f = w.files[this.hash(String(seed)) % w.files.length];
      return { w, f, src: `assets/ghibli/${w.id}/${f}.webp`, thumb: `assets/ghibli/${w.id}/t/${f}.webp` };
    },
    credit(w) { return `<a href="${esc(w.url)}" target="_blank" rel="noopener">${esc(w.title)} (${esc(w.year)})</a> · ${esc(w.copyright)} · official still, ghibli.jp`; },
    figure(workId, seed, cls = "") {
      const st = this.still(workId, seed);
      if (!st) return "";
      return `<figure class="still ${cls}"><img loading="lazy" src="${st.src}" alt="Still from ${esc(st.w.title)}" width="1024" height="554"><figcaption>${this.credit(st.w)}</figcaption></figure>`;
    },
    quoteHTML(seed) {
      if (!this.quotes.length) return "";
      const q = this.quotes[this.hash("q" + seed) % this.quotes.length];
      const w = this.works[q.work];
      const ref = w ? `<a href="${esc(w.url)}" target="_blank" rel="noopener"><cite>${esc(w.title)}</cite> (${esc(w.year)})</a>` : "";
      return `<blockquote class="gq"><p>“${esc(q.q)}”</p><footer>— ${esc(q.by)}${ref ? ", " + ref : ""}</footer></blockquote>`;
    },
  };
  const dayKey = (d = new Date()) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
  const bump = (s) => { const k = dayKey(); (s.activity = s.activity || {})[k] = (s.activity[k] || 0) + 1; };
  function streaks() {
    const a = S().activity || {};
    let cur = 0, best = 0, run = 0;
    const d = new Date();
    if (!a[dayKey(d)]) d.setDate(d.getDate() - 1);
    while (a[dayKey(d)]) { cur++; d.setDate(d.getDate() - 1); }
    let prev = null;
    Object.keys(a).sort().forEach((k) => { const t = new Date(k + "T00:00:00"); run = prev && Math.round((t - prev) / 864e5) === 1 ? run + 1 : 1; best = Math.max(best, run); prev = t; });
    return { cur, best: Math.max(best, cur) };
  }
  function calendarHTML() {
    const a = S().activity || {}, now = new Date(), y = now.getFullYear(), m = now.getMonth();
    const first = new Date(y, m, 1).getDay(), days = new Date(y, m + 1, 0).getDate();
    let cells = "SMTWTFS".split("").map((c) => `<span class="cal-h">${c}</span>`).join("") + "<span></span>".repeat(first);
    for (let d = 1; d <= days; d++) {
      const n = a[dayKey(new Date(y, m, d))] || 0;
      cells += `<span class="cal-d ${n ? "l" + Math.min(3, n) : ""} ${d === now.getDate() ? "today" : ""}" title="${n} item(s)">${d}</span>`;
    }
    return `<div class="cal-title">${now.toLocaleString(undefined, { month: "long", year: "numeric" })}</div><div class="cal">${cells}</div>`;
  }
  function difficultyStats() {
    const s = S(), out = { Easy: [0, 0], Medium: [0, 0], Hard: [0, 0] };
    Object.keys(DATA.problemTrack).forEach((pid) => {
      const m = DATA.tracks[DATA.problemTrack[pid].track].problemIndex[pid];
      if (!m || !out[m.difficulty]) return;
      out[m.difficulty][1]++; if (s.solved[pid]) out[m.difficulty][0]++;
    });
    return out;
  }
  function randomUnsolved() {
    const s = S(), pool = Object.keys(DATA.problemTrack).filter((p) => !s.solved[p]);
    return pool.length ? pool[Math.floor(Math.random() * pool.length)] : null;
  }

  // ---------------------------------------------------------------- views
  const main = $("#main");
  function setPage(html, opts = {}) {
    document.body.classList.toggle("workspace", !!opts.workspace);
    document.body.classList.toggle("wide", !!opts.workspace);
    const rbar = $("#readbar"); if (rbar) rbar.remove();
    main.innerHTML = html;
    if (!opts.keepScroll) window.scrollTo(0, 0);
    closeMenu();
  }

  function viewHome() {
    renderSidebar(null);
    const s = S();
    const totals = DATA.index.reduce((a, t) => ({ lessons: a.lessons + (t.lessons || 0), problems: a.problems + (t.problems || 0), words: a.words + (t.words || 0) }), { lessons: 0, problems: 0, words: 0 });
    const solved = Object.keys(s.solved).filter((p) => DATA.problemTrack[p]).length, read = Object.keys(s.lessons).length;
    const hero = Ghibli.still(null, "hero" + dayKey());
    const diff = difficultyStats(), st = streaks();
    const nProb = Object.keys(DATA.problemTrack).length;
    const C = 2 * Math.PI * 52, frac = nProb ? solved / nProb : 0;
    const groupNames = [];
    let buf = "";
    DATA.index.forEach((ti) => {
      const t = DATA.tracks[ti.id];
      if (!t) return;
      const g = t.group || "Other";
      if (!groupNames.includes(g)) groupNames.push(g);
      const p = trackProgress(t), im = Ghibli.still(TRACK_FILM[t.id], "card" + t.id);
      buf += `<a class="card tcard" data-group="${esc(g)}" href="#/track/${t.id}" style="--card-accent:${esc(t.color || "#3f6b4f")}">
        ${im ? `<div class="tcard-img"><img loading="lazy" src="${im.thumb}" alt="Still from ${esc(im.w.title)}"><span class="tcard-film">${esc(im.w.title)}</span></div>` : ""}
        <div class="tcard-body"><span class="tcard-group">${esc(g)}</span><div class="card-top"><div class="card-ico">${esc(t.icon || "📘")}</div><h3>${esc(t.title)}</h3></div>
        <p>${esc(t.blurb || "")}</p>
        <div class="bar"><i style="width:${p.pct}%"></i></div>
        <div class="card-meta"><span>${ti.lessons} lessons</span><span>${ti.problems} problems</span><span>${p.pct}% done</span></div></div></a>`;
    });
    const groups = `<div class="section-h"><h2>Tracks</h2></div>
      <div class="chips" id="grpChips"><button class="chip on" data-g="">All ${DATA.index.length}</button>${groupNames.map((g) => `<button class="chip" data-g="${esc(g)}">${esc(g)}</button>`).join("")}</div>
      <div class="grid" id="trackGrid">${buf}</div>`;
    const cont = s.last ? `<a class="btn primary" href="${esc(s.last.href)}">Continue: ${esc(s.last.title)}</a>` : `<a class="btn primary" href="#/roadmap">Start with the roadmap</a>`;
    setPage(`<div class="page">
      <section class="hero2" ${hero ? `style="background-image:url('${hero.src}')"` : ""}>
        <div class="hero2-in">
          <p class="hero2-kicker">A Studio Ghibli themed, fan-made study guide</p>
          <h1>Study a little every day. The wind will carry you.</h1>
          <p>Computer systems, Python, algorithms with a live judge, SQL and databases, machine learning, FastAPI, MLOps and AI engineering.</p>
          <div class="hero2-cta">${cont}<a class="btn glass" href="#/roadmap">Roadmap</a><button class="btn glass" id="rndBtn" type="button">Random problem</button></div>
        </div>
        ${hero ? `<div class="hero2-credit">${Ghibli.credit(hero.w)}</div>` : ""}
      </section>
      <div class="dash">
        <div class="card dash-ring">
          <svg viewBox="0 0 120 120" width="120" height="120" aria-hidden="true"><circle cx="60" cy="60" r="52" fill="none" stroke="var(--surface-2)" stroke-width="10"/>
            <circle cx="60" cy="60" r="52" fill="none" stroke="var(--accent)" stroke-width="10" stroke-linecap="round" stroke-dasharray="${(C * frac).toFixed(1)} ${C.toFixed(1)}" transform="rotate(-90 60 60)"/>
            <text x="60" y="58" text-anchor="middle" font-size="24" font-weight="800" fill="currentColor">${solved}</text><text x="60" y="76" text-anchor="middle" font-size="11" fill="currentColor" opacity=".6">of ${nProb} solved</text></svg>
          <div class="dash-diff">${["Easy", "Medium", "Hard"].map((d) => `<div><span class="diff ${d}">${d}</span><b>${diff[d][0]}/${diff[d][1]}</b></div>`).join("")}
            <div><span class="muted">Lessons read</span><b>${read}/${totals.lessons}</b></div></div>
        </div>
        <div class="card dash-streak">
          <div class="streak-row"><div><b>${st.cur}</b><span>day streak</span></div><div><b>${st.best}</b><span>best streak</span></div><div><b>${Object.keys(s.activity || {}).length}</b><span>active days</span></div></div>
          ${calendarHTML()}
          <p class="muted" style="font-size:12px;margin:8px 0 0">Finish a lesson or solve a problem to light up today.</p>
        </div>
        <div class="card dash-quote">${Ghibli.quoteHTML("day" + dayKey())}<a class="muted" style="font-size:12px" href="#/credits">Image and quote credits</a></div>
      </div>
      ${groups}
      <div class="footer">Fan-made study site, not affiliated with Studio Ghibli. Stills are the official free images from <a href="https://www.ghibli.jp/works/" target="_blank" rel="noopener">ghibli.jp</a>. <a href="#/gallery">Gallery</a> · <a href="#/credits">Credits</a><br>${totals.lessons} lessons · ${totals.problems} problems · ${Math.round(totals.words / 1000)}k words · progress is stored in this browser</div>
    </div>`);
    $$("#grpChips .chip").forEach((c) => (c.onclick = () => {
      $$("#grpChips .chip").forEach((x) => x.classList.toggle("on", x === c));
      $$("#trackGrid .tcard").forEach((el) => (el.hidden = !!c.dataset.g && el.dataset.group !== c.dataset.g));
    }));
    const rb = $("#rndBtn");
    if (rb) rb.onclick = () => { const p = randomUnsolved(); if (p) location.hash = `#/problem/${p}`; };
  }

  // ---------------------------------------------------------------- roadmap
  const ROADMAP = {
    pos: { csapp: [0, 0], python: [2, 0], sql: [4, 0], "dsa-foundations": [1, 1], fastapi: [2, 1], ml: [3, 1], databases: [4, 1],
      "neet-arrays": [1, 2], mlops: [3, 2], "ai-eng": [4, 2], "neet-window-stack": [0, 3], "neet-linked-trees": [1, 3], "llm-practice": [4, 3],
      "neet-greedy-math": [0, 4], "neet-heap-graphs": [1, 4], "neet-dp": [2, 4], os: [0, 1], "linux-cli": [2, 2], vim: [2, 3] },
    edges: [["csapp", "os"], ["linux-cli", "vim"], ["python", "dsa-foundations"], ["python", "fastapi"], ["python", "ml"], ["sql", "databases"], ["dsa-foundations", "neet-arrays"],
      ["neet-arrays", "neet-window-stack"], ["neet-arrays", "neet-linked-trees"], ["neet-window-stack", "neet-greedy-math"],
      ["neet-linked-trees", "neet-heap-graphs"], ["neet-linked-trees", "neet-dp"], ["ml", "mlops"], ["fastapi", "mlops"], ["databases", "mlops"],
      ["ml", "ai-eng"], ["ai-eng", "llm-practice"]],
  };
  function viewRoadmap() {
    renderSidebar(null);
    const CW = 218, RH = 128, NW = 196, NH = 76, PAD = 16;
    const xy = (id) => { const [c, r] = ROADMAP.pos[id]; return [PAD + c * CW, PAD + r * RH]; };
    const ids = Object.keys(ROADMAP.pos).filter((id) => DATA.tracks[id]);
    const W = PAD * 2 + 4 * CW + NW, H = PAD * 2 + 4 * RH + NH;
    const lines = ROADMAP.edges.filter(([a, b]) => DATA.tracks[a] && DATA.tracks[b]).map(([a, b]) => {
      const [ax, ay] = xy(a), [bx, by] = xy(b);
      const x1 = ax + NW / 2, y1 = ay + NH, x2 = bx + NW / 2, y2 = by, my = (y1 + y2) / 2;
      const done = trackProgress(DATA.tracks[a]).pct === 100;
      return `<path d="M${x1},${y1} C${x1},${my} ${x2},${my} ${x2},${y2}" class="${done ? "done" : ""}"/>`;
    }).join("");
    const nodes = ids.map((id) => {
      const t = DATA.tracks[id], [x, y] = xy(id), p = trackProgress(t);
      return `<a class="rnode ${p.pct === 100 ? "done" : p.pct ? "started" : ""}" href="#/track/${id}" style="left:${x}px;top:${y}px;width:${NW}px;height:${NH}px">
        <span class="rn-t"><span>${esc(t.icon || "")}</span>${esc(t.title)}</span><span class="bar"><i style="width:${p.pct}%"></i></span><span class="rn-m">${p.done}/${p.total} · ${p.pct}%</span></a>`;
    }).join("");
    setPage(`<div class="page"><div class="crumbs"><a href="#/">Home</a></div><h1 class="page-title">Roadmap</h1>
      <p class="muted">Arrows point from a track to the ones that build on it. Start at the top; anything with no arrow into it needs no prerequisites.</p>
      <div class="roadmap-scroll"><div class="roadmap" style="width:${W}px;height:${H}px"><svg width="${W}" height="${H}">${lines}</svg>${nodes}</div></div>
      ${Ghibli.figure("laputa", "roadmap", "wide")}</div>`);
  }

  // ---------------------------------------------------------------- gallery & credits
  function viewGallery(wid) {
    renderSidebar(null);
    const w = wid && Ghibli.works[wid];
    if (w) {
      setPage(`<div class="page"><div class="crumbs"><a href="#/">Home</a> / <a href="#/gallery">Gallery</a></div>
        <h1 class="page-title">${esc(w.title)} <small class="muted">(${esc(w.year)})</small></h1><p class="muted">${esc(w.title_ja)} · ${esc(w.copyright)} · <a href="${esc(w.url)}" target="_blank" rel="noopener">source page on ghibli.jp</a></p>
        <div class="gal">${w.files.map((f) => `<a href="assets/ghibli/${w.id}/${f}.webp" target="_blank" rel="noopener"><img loading="lazy" src="assets/ghibli/${w.id}/t/${f}.webp" alt="Still from ${esc(w.title)}"></a>`).join("")}</div></div>`);
      return;
    }
    const withStills = Ghibli.list.filter((x) => x.files.length);
    const total = withStills.reduce((a, x) => a + x.files.length, 0);
    setPage(`<div class="page"><div class="crumbs"><a href="#/">Home</a></div><h1 class="page-title">Gallery</h1>
      <p class="muted">${total} official stills from ${withStills.length} films, published by Studio Ghibli at <a href="https://www.ghibli.jp/works/" target="_blank" rel="noopener">ghibli.jp/works</a>. <a href="#/credits">Credits and terms</a>.</p>
      <div class="grid">${withStills.map((x) => `<a class="card tcard" href="#/gallery/${x.id}"><div class="tcard-img"><img loading="lazy" src="assets/ghibli/${x.id}/t/${x.files[0]}.webp" alt="Still from ${esc(x.title)}"></div>
        <div class="tcard-body"><h3>${esc(x.title)}</h3><p>${esc(x.title_ja)} · ${esc(x.year)} · ${x.files.length} stills</p></div></a>`).join("")}</div></div>`);
  }
  function viewCredits() {
    renderSidebar(null);
    setPage(`<div class="page narrow"><div class="crumbs"><a href="#/">Home</a></div><h1 class="page-title">Credits</h1>
      <div class="prose">
      <p>This is a personal, fan-made study site. It is not affiliated with or endorsed by Studio Ghibli.</p>
      <h2>Images</h2>
      <p>Every film still on this site is an official image published by Studio Ghibli at <a href="https://www.ghibli.jp/works/" target="_blank" rel="noopener">https://www.ghibli.jp/works/</a>. ${esc(Ghibli.terms)} The images here are resized copies of those files; each one is captioned with its film and copyright line where it appears.</p>
      <table><thead><tr><th>Film</th><th>Year</th><th>Copyright</th><th>Source</th></tr></thead><tbody>${Ghibli.list.filter((x) => x.files.length).map((x) => `<tr><td><a href="#/gallery/${x.id}">${esc(x.title)}</a><br><span class="muted">${esc(x.title_ja)}</span></td><td>${esc(x.year)}</td><td>${esc(x.copyright)}</td><td><a href="${esc(x.url)}" target="_blank" rel="noopener">ghibli.jp</a></td></tr>`).join("")}</tbody></table>
      <h2>Quotes</h2>
      <p>${esc(Ghibli.note)}</p>
      <table><thead><tr><th>Quote</th><th>Speaker</th><th>Film</th></tr></thead><tbody>${Ghibli.quotes.map((q) => { const w = Ghibli.works[q.work]; return `<tr><td>“${esc(q.q)}”</td><td>${esc(q.by)}</td><td>${w ? `<a href="${esc(w.url)}" target="_blank" rel="noopener">${esc(w.title)} (${esc(w.year)})</a>` : esc(q.work)}</td></tr>`; }).join("")}</tbody></table>
      <h2>Study content</h2>
      <p>Lessons are original summaries that cite their source books and documentation at the end of each lesson. Problem statements are written for this site; links go to the original problems on LeetCode and NeetCode.</p>
      <ul>${DATA.index.map((ti) => { const t = DATA.tracks[ti.id]; return t && t.sources && t.sources.length ? `<li><b>${esc(t.title)}:</b> ${t.sources.map(esc).join("; ")}</li>` : ""; }).join("")}</ul>
      <h2>Inspiration and tools</h2>
      <p>The problem selection and ordering of the pattern tracks follow the public NeetCode 150 list, and the roadmap, progress ring and streak calendar were inspired by neetcode.io. The code-and-judge layout follows the convention popularised by LeetCode. All code, text and designs here were written for this site.</p>
      <p>Built with Pyodide, sql.js, CodeMirror, marked, highlight.js, KaTeX and Mermaid (open-source libraries under their own licences), and the Nunito, Zen Maru Gothic and JetBrains Mono fonts.</p>
      </div></div>`);
  }

  // ---------------------------------------------------------------- command palette (Ctrl/Cmd+K)
  function openPalette() {
    let dlg = $("#pal");
    if (!dlg) {
      dlg = h(`<dialog id="pal" class="dlg pal"><input id="palIn" type="search" placeholder="Jump to a track, lesson or problem…" autocomplete="off"><div id="palList"></div><p class="muted pal-hint">↑ ↓ to move · Enter to open · Esc to close</p></dialog>`);
      document.body.appendChild(dlg);
    }
    const items = [{ t: "Home", s: "", href: "#/" }, { t: "Roadmap", s: "", href: "#/roadmap" }, { t: "All problems", s: "", href: "#/problems" }, { t: "Gallery", s: "", href: "#/gallery" }, { t: "Credits", s: "", href: "#/credits" }];
    DATA.index.forEach((ti) => {
      const t = DATA.tracks[ti.id];
      if (!t) return;
      items.push({ t: t.title, s: "Track", href: `#/track/${t.id}` });
      t.modules.forEach((m) => {
        (m.lessons || []).forEach((l) => items.push({ t: l.title, s: `Lesson · ${t.title}`, href: `#/lesson/${t.id}/${l.id}` }));
        (m.problems || []).forEach((pid) => { const x = t.problemIndex[pid]; if (x) items.push({ t: x.title, s: `Problem · ${x.difficulty}`, href: `#/problem/${pid}` }); });
      });
    });
    const inp = $("#palIn"), list = $("#palList");
    let sel = 0, shown = [];
    const draw = () => {
      const q = inp.value.toLowerCase().trim();
      shown = (q ? items.filter((i) => (i.t + " " + i.s).toLowerCase().includes(q)) : items).slice(0, 12);
      sel = Math.min(sel, Math.max(0, shown.length - 1));
      list.innerHTML = shown.map((i, n) => `<a class="pal-i ${n === sel ? "on" : ""}" href="${i.href}"><b>${esc(i.t)}</b><span>${esc(i.s)}</span></a>`).join("") || `<p class="muted" style="padding:8px">Nothing found.</p>`;
    };
    inp.value = ""; sel = 0; draw();
    inp.oninput = () => { sel = 0; draw(); };
    inp.onkeydown = (e) => {
      if (e.key === "ArrowDown") { sel = Math.min(sel + 1, shown.length - 1); draw(); e.preventDefault(); }
      else if (e.key === "ArrowUp") { sel = Math.max(sel - 1, 0); draw(); e.preventDefault(); }
      else if (e.key === "Enter" && shown[sel]) { location.hash = shown[sel].href; dlg.close(); e.preventDefault(); }
    };
    list.onclick = (e) => { if (e.target.closest("a")) dlg.close(); };
    dlg.onclick = (e) => { if (e.target === dlg) dlg.close(); };
    dlg.showModal();
  }
  document.addEventListener("keydown", (e) => { if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") { e.preventDefault(); openPalette(); } });
  window.addEventListener("scroll", () => { const b = $("#readbar"); if (b) { const d = document.documentElement; b.style.width = Math.min(100, (100 * d.scrollTop) / Math.max(1, d.scrollHeight - d.clientHeight)) + "%"; } }, { passive: true });

  function lessonMinutes(l) { return Math.max(3, Math.round((l.words || 0) / 220)); }

  function viewTrack(tid) {
    const t = DATA.tracks[tid];
    if (!t) return viewNotFound();
    renderSidebar(tid);
    const s = S();
    const p = trackProgress(t);
    const mods = t.modules.map((m, i) => {
      const lessons = (m.lessons || []).map((l) => {
        const done = s.lessons[`${tid}/${l.id}`];
        return `<a class="lesson-row ${done ? "done" : ""}" href="#/lesson/${tid}/${l.id}"><span class="st">${done ? "✓" : "○"}</span><span>${esc(l.title)}</span><span class="mins">${lessonMinutes(l)} min</span></a>`;
      }).join("");
      const probs = (m.problems || []).length ? `<div class="subhead">Practice</div><div class="table-wrap" style="border:0">${problemTable(m.problems, t)}</div>` : "";
      const mdone = (m.lessons || []).every((l) => s.lessons[`${tid}/${l.id}`]) && (m.problems || []).every((x) => s.solved[x]);
      return `<details class="module" ${i === 0 || !mdone ? "open" : ""}>
        <summary><span class="num">${mdone ? "✓" : i + 1}</span><span class="t"><b>${esc(m.title)}</b><span>${esc(m.summary || "")}</span></span><span class="chev">▸</span></summary>
        <div class="module-body">${lessons ? `<div class="subhead">Lessons</div>${lessons}` : ""}${probs}</div></details>`;
    }).join("");
    setPage(`<div class="page narrow" style="--card-accent:${esc(t.color || "#d1412b")}">
      <div class="crumbs"><a href="#/">Home</a> / <span>${esc(t.group || "")}</span></div>
      ${Ghibli.figure(TRACK_FILM[tid], "track" + tid, "banner")}
      <div class="track-head"><div class="card-ico">${esc(t.icon || "📘")}</div><div>
        <h1 class="page-title">${esc(t.title)}</h1><p class="muted" style="margin:0 0 8px">${esc(t.blurb || "")}</p>
        ${t.sources && t.sources.length ? `<div class="sources">Sources: ${t.sources.map(esc).join(" · ")}</div>` : ""}
      </div></div>
      <div class="bar" style="margin:8px 0 6px"><i style="width:${p.pct}%"></i></div>
      <p class="muted" style="font-size:13px;margin:0 0 20px">${p.done} of ${p.total} items complete</p>
      ${mods}
    </div>`);
  }

  function problemTable(pids, trackOrNull, showTrack) {
    const s = S();
    const rows = pids.map((pid) => {
      const loc = DATA.problemTrack[pid];
      const t = trackOrNull || (loc && DATA.tracks[loc.track]);
      const meta = t && t.problemIndex[pid];
      if (!meta) return "";
      const st = s.solved[pid] ? `<span class="status-dot solved" title="Solved">✓</span>` : s.tried[pid] ? `<span class="status-dot tried" title="Attempted">◐</span>` : `<span class="status-dot muted">·</span>`;
      const links = [meta.leetcode ? `<a class="ext" href="${esc(meta.leetcode)}" target="_blank" rel="noopener">LC</a>` : "", meta.neetcode ? `<a class="ext" href="${esc(meta.neetcode)}" target="_blank" rel="noopener">NC</a>` : ""].join("");
      return `<tr><td class="st">${st}</td><td><a href="#/problem/${esc(pid)}">${esc(meta.title)}</a></td><td><span class="diff ${esc(meta.difficulty)}">${esc(meta.difficulty)}</span></td>
        ${showTrack ? `<td class="trk">${esc(t.title)}</td>` : `<td class="pat">${esc(meta.pattern || (meta.kind === "sql" ? "SQL" : ""))}</td>`}<td class="links">${links}</td></tr>`;
    }).join("");
    return `<table class="ptable"><thead><tr><th></th><th>Problem</th><th>Difficulty</th><th class="${showTrack ? "trk" : "pat"}">${showTrack ? "Track" : "Pattern"}</th><th class="links"></th></tr></thead><tbody>${rows}</tbody></table>`;
  }

  function viewProblems(q) {
    renderSidebar(null);
    const all = Object.keys(DATA.problemTrack);
    setPage(`<div class="page">
      <div class="crumbs"><a href="#/">Home</a></div>
      <h1 class="page-title">All problems</h1>
      <p class="muted">${all.length} problems across every track. Solved problems are saved in this browser.</p>
      <div class="filters">
        <input id="fq" type="search" placeholder="Filter by title or pattern…" value="${esc(q || "")}">
        <select id="ft"><option value="">All tracks</option>${DATA.index.filter((t) => t.problems).map((t) => `<option value="${t.id}">${esc(t.title)}</option>`).join("")}</select>
        <select id="fd"><option value="">Any difficulty</option><option>Easy</option><option>Medium</option><option>Hard</option></select>
        <select id="fs"><option value="">Any status</option><option value="todo">Unsolved</option><option value="solved">Solved</option><option value="tried">Attempted</option></select>
      </div>
      <div class="table-wrap" id="ptab"></div></div>`);
    const draw = () => {
      const fq = $("#fq").value.toLowerCase(), ft = $("#ft").value, fd = $("#fd").value, fs = $("#fs").value;
      const s = S();
      const list = all.filter((pid) => {
        const loc = DATA.problemTrack[pid];
        const m = DATA.tracks[loc.track].problemIndex[pid];
        if (ft && loc.track !== ft) return false;
        if (fd && m.difficulty !== fd) return false;
        if (fs === "solved" && !s.solved[pid]) return false;
        if (fs === "todo" && s.solved[pid]) return false;
        if (fs === "tried" && !(s.tried[pid] && !s.solved[pid])) return false;
        if (fq && !(`${m.title} ${m.pattern || ""} ${pid}`.toLowerCase().includes(fq))) return false;
        return true;
      });
      $("#ptab").innerHTML = list.length ? problemTable(list, null, true) : `<div class="loading">No problems match.</div>`;
    };
    $$(".filters input, .filters select").forEach((e) => (e.oninput = draw));
    draw();
  }

  function flatLessons(t) {
    const out = [];
    t.modules.forEach((m) => (m.lessons || []).forEach((l) => out.push({ ...l, module: m })));
    return out;
  }

  async function viewLesson(tid, lid) {
    const t = DATA.tracks[tid];
    if (!t) return viewNotFound();
    const flat = flatLessons(t);
    const idx = flat.findIndex((l) => l.id === lid);
    if (idx < 0) return viewNotFound();
    const l = flat[idx];
    renderSidebar(tid, lid);
    setPage(`<div class="page"><div class="crumbs"><a href="#/">Home</a> / <a href="#/track/${tid}">${esc(t.title)}</a> / <span>${esc(l.module.title)}</span></div>
      <div class="lesson-layout"><article class="prose" id="lessonBody"><div class="loading">Loading lesson…</div></article><nav class="toc" id="toc"></nav></div></div>`);
    let md;
    try { md = await getText(`data/lessons/${tid}/${l.file}`); }
    catch (e) { $("#lessonBody").innerHTML = `<p>Could not load lesson: ${esc(e.message)}</p>`; return; }
    const body = $("#lessonBody");
    if (!body) return;
    if (!/^\s*#\s/.test(md)) md = `# ${l.title}\n\n` + md;
    renderMarkdown(md, body, { key: `${tid}/${lid}` });
    const h1 = $("h1", body), fig = Ghibli.figure(TRACK_FILM[tid], `${tid}/${lid}`, "banner");
    if (fig && h1) h1.insertAdjacentHTML("afterend", fig);
    if (!$("#readbar")) document.body.appendChild(h(`<div id="readbar"></div>`));
    store.set((s) => (s.last = { href: location.hash, title: l.title, sub: t.title }));
    // TOC
    const heads = $$("h2, h3", body);
    $("#toc").innerHTML = heads.length ? `<b>On this page</b>` + heads.map((x) => `<a class="${x.tagName.toLowerCase()}" href="#${x.id}" data-id="${x.id}">${esc(x.textContent)}</a>`).join("") : "";
    $$("#toc a").forEach((a) => (a.onclick = (e) => { e.preventDefault(); const el = document.getElementById(a.dataset.id); if (el) window.scrollTo({ top: el.getBoundingClientRect().top + scrollY - 70, behavior: "smooth" }); }));
    if ("IntersectionObserver" in window && heads.length) {
      const io = new IntersectionObserver((ents) => {
        ents.forEach((en) => { if (en.isIntersecting) { $$("#toc a").forEach((a) => a.classList.toggle("active", a.dataset.id === en.target.id)); } });
      }, { rootMargin: "-80px 0px -70% 0px" });
      heads.forEach((x) => io.observe(x));
    }
    // module problems + footer
    const mod = l.module;
    const isLastInModule = mod.lessons[mod.lessons.length - 1].id === lid;
    const prev = flat[idx - 1], next = flat[idx + 1];
    const key = `${tid}/${lid}`;
    const foot = h(`<div>
      ${isLastInModule && (mod.problems || []).length ? `<h2 id="practice">Practice: ${esc(mod.title)}</h2><p>Put the lesson to work. Each problem has hints and a full walkthrough in its Guide tab.</p><div class="table-wrap">${problemTable(mod.problems, t)}</div>` : ""}
      ${Ghibli.quoteHTML(key)}
      <div class="lesson-foot">
        <button class="btn ${S().lessons[key] ? "ok" : "primary"}" id="doneBtn">${S().lessons[key] ? "✓ Completed" : "Mark lesson complete"}</button>
        <div class="navs">${prev ? `<a class="btn" href="#/lesson/${tid}/${prev.id}">← ${esc(prev.title)}</a>` : ""}${next ? `<a class="btn" href="#/lesson/${tid}/${next.id}">${esc(next.title)} →</a>` : `<a class="btn" href="#/track/${tid}">Back to track</a>`}</div>
      </div></div>`);
    body.appendChild(foot);
    $("#doneBtn").onclick = () => {
      const on = !S().lessons[key];
      store.set((s) => { if (on) { s.lessons[key] = Date.now(); bump(s); } else delete s.lessons[key]; });
      if (on && next) location.hash = `#/lesson/${tid}/${next.id}`;
      else viewLesson(tid, lid);
    };
    if (/```python-run|```py-run/.test(md)) setTimeout(() => Py.warm(), 1500);
  }

  // ---------------------------------------------------------------- problem workspace
  async function viewProblem(pid) {
    const p = await getProblem(pid);
    if (!p) return viewNotFound();
    const t = DATA.tracks[p._loc.track];
    const mod = t.modules.find((m) => m.id === p._loc.module);
    renderSidebar(t.id);
    const isSql = p.kind === "sql";
    const saved = S().code[pid];
    store.set((s) => (s.last = { href: location.hash, title: p.title, sub: `${t.title} · ${p.difficulty}` }));
    const plist = mod.problems, pi = plist.indexOf(pid);
    const prevP = plist[pi - 1], nextP = plist[pi + 1];
    setPage(`<div class="ws">
      <div class="ws-tabs-mobile" role="tablist"><button data-p="left" class="on">Problem</button><button data-p="editor">Code</button><button data-p="console">Result</button></div>
      <div class="ws-body">
        <section class="pane left on">
          <div class="pane-tabs"><button data-t="desc" class="on">Description</button><button data-t="guide">Guide</button><button data-t="notes">Notes</button><button data-t="subs">Submissions</button></div>
          <div class="pane-scroll" id="leftBody"></div>
        </section>
        <section class="pane editor">
          <div class="editor-bar">
            <a class="btn sm" href="#/track/${t.id}" title="Back to track">←</a>
            <span class="lang">${isSql ? "SQLite" : "Python 3"}</span>
            ${prevP ? `<a class="btn sm" href="#/problem/${prevP}" title="Previous problem">‹</a>` : ""}${nextP ? `<a class="btn sm" href="#/problem/${nextP}" title="Next problem">›</a>` : ""}
            <span class="sp"></span>
            <button class="btn sm" id="resetCodeBtn" title="Reset to starter code">Reset</button>
            <button class="btn sm" id="runBtn" title="Run examples (Ctrl+Enter)">▶ Run</button>
            <button class="btn sm ok" id="submitBtn" title="Submit all tests (Ctrl+Shift+Enter)">Submit</button>
          </div>
          <div class="editor-host" id="editorHost"></div>
          <div class="editor-actions-mobile"><button class="btn" id="runBtnM">▶ Run</button><button class="btn ok" id="submitBtnM">Submit</button></div>
        </section>
        <section class="pane console">
          <div class="pane-tabs"><button data-c="cases" class="on">Testcases</button><button data-c="result">Result</button></div>
          <div class="console-body" id="consoleBody"></div>
        </section>
      </div></div>`, { workspace: true });

    // mobile pane switching
    const showPane = (name) => {
      $$(".ws-tabs-mobile button").forEach((b) => b.classList.toggle("on", b.dataset.p === name));
      $$(".pane").forEach((pn) => pn.classList.toggle("on", pn.classList.contains(name)));
      if (name === "editor") setTimeout(() => cm.refresh(), 0);
    };
    $$(".ws-tabs-mobile button").forEach((b) => (b.onclick = () => showPane(b.dataset.p)));

    // left tabs
    const leftBody = $("#leftBody");
    const tabs = {
      desc: () => {
        leftBody.innerHTML = `<h1 class="p-title">${esc(p.title)}</h1>
          <div class="p-meta"><span class="diff ${esc(p.difficulty)}">${esc(p.difficulty)}</span>${p.pattern ? `<span class="pill">${esc(p.pattern)}</span>` : ""}
          ${S().solved[pid] ? `<span class="pill" style="color:var(--ok)">✓ Solved</span>` : ""}
          ${p.leetcode ? `<a class="ext" href="${esc(p.leetcode)}" target="_blank" rel="noopener">LeetCode ↗</a>` : ""}${p.neetcode ? `<a class="ext" href="${esc(p.neetcode)}" target="_blank" rel="noopener">NeetCode ↗</a>` : ""}</div>
          <div class="prose" id="descBody"></div>`;
        let md = p.description || "";
        if (!isSql && p.tests && p.examples) {
          md += "\n\n### Examples from the judge\n\n" + p.tests.slice(0, p.examples).map((tc, i) => `**Example ${i + 1}**\n\n\`\`\`text\nInput:  ${trunc(argsLabel(tc.args), 300)}\nOutput: ${trunc(fmt(tc.expected), 300)}\n\`\`\``).join("\n\n");
        }
        if (p.guide && p.guide.prereqs) md += `\n\n> [!TIP]\n> **Before you start:** ${p.guide.prereqs.replace(/\n/g, "\n> ")}`;
        renderMarkdown(md, $("#descBody"));
      },
      guide: () => {
        const g = p.guide || {};
        const secs = [
          ["prereqs", "📚 Prerequisites", true], ["intuition", "💡 Intuition", false],
          ...(g.hints || []).map((x, i) => [null, `🧭 Hint ${i + 1}`, false, x]),
          ["brute_force", "🐢 Brute force", false], ["approach", "🚀 Optimal approach (walkthrough)", false],
          ["complexity", "⏱ Complexity", false], ["pitfalls", "⚠️ Pitfalls & edge cases", false], ["follow_up", "🔭 Follow-ups", false],
        ];
        leftBody.innerHTML = `<p class="muted" style="margin-top:0">Reveal one step at a time. Try the problem again after each hint.</p>`;
        secs.forEach(([k, title, open, val]) => {
          const content = val !== undefined ? val : g[k];
          if (!content) return;
          const d = h(`<details class="guide-sec" ${open ? "open" : ""}><summary>${title}</summary><div class="prose"></div></details>`);
          d.addEventListener("toggle", () => { if (d.open && !d._r) { d._r = 1; renderMarkdown(content, $(".prose", d)); } });
          if (open) { d._r = 1; renderMarkdown(content, $(".prose", d)); }
          leftBody.appendChild(d);
        });
        const sol = h(`<details class="guide-sec"><summary>🏴‍☠️ Reference solution</summary><div class="prose"></div></details>`);
        sol.addEventListener("toggle", () => {
          if (sol.open && !sol._r) {
            sol._r = 1;
            renderMarkdown("```" + (isSql ? "sql" : "python") + "\n" + p.solution.trim() + "\n```", $(".prose", sol));
            const b = h(`<button class="btn sm" style="margin:0 0 12px">Load into editor</button>`);
            b.onclick = () => { if (confirm("Replace your code with the reference solution?")) { cm.setValue(p.solution.trim() + "\n"); showPane("editor"); } };
            $(".prose", sol).appendChild(b);
          }
        });
        leftBody.appendChild(sol);
      },
      notes: () => {
        leftBody.innerHTML = `<p class="muted" style="margin-top:0">Your private notes for this problem (saved in this browser).</p><textarea class="notes-area" id="notesArea" placeholder="Key insight, mistakes you made, complexity…"></textarea>`;
        const ta = $("#notesArea");
        ta.value = S().notes[pid] || "";
        ta.oninput = () => store.set((s) => (s.notes[pid] = ta.value));
      },
      subs: () => {
        const subs = (S().tried[pid] && S().tried[pid].subs) || [];
        leftBody.innerHTML = subs.length ? `<table class="ptable"><thead><tr><th>When</th><th>Verdict</th><th>Passed</th></tr></thead><tbody>${subs.slice().reverse().map((x) => `<tr><td>${new Date(x.at).toLocaleString()}</td><td style="color:${x.ok ? "var(--ok)" : "var(--bad)"}">${esc(x.verdict)}</td><td>${x.passed}/${x.total}</td></tr>`).join("")}</tbody></table>` : `<p class="muted">No submissions yet.</p>`;
      },
    };
    $$(".pane.left .pane-tabs button").forEach((b) => (b.onclick = () => { $$(".pane.left .pane-tabs button").forEach((x) => x.classList.toggle("on", x === b)); tabs[b.dataset.t](); leftBody.scrollTop = 0; }));
    tabs.desc();

    // editor
    const cm = makeEditor($("#editorHost"), saved || p.starter, isSql ? "sql" : "python", {
      keys: { "Ctrl-Enter": () => run(false), "Cmd-Enter": () => run(false), "Shift-Ctrl-Enter": () => run(true), "Shift-Cmd-Enter": () => run(true) },
    });
    cm.on("change", debounce(() => store.set((s) => (s.code[pid] = cm.getValue())), 400));
    $("#resetCodeBtn").onclick = () => { if (confirm("Reset to the starter code? Your current code will be lost.")) cm.setValue(p.starter); };

    // console
    const cbody = $("#consoleBody");
    let customText = null;
    const ctabs = $$(".pane.console .pane-tabs button");
    const showConsole = (name) => ctabs.forEach((b) => b.classList.toggle("on", b.dataset.c === name));
    function drawCases() {
      showConsole("cases");
      if (isSql) {
        cbody.innerHTML = `<p class="muted" style="margin-top:0">Your query runs against the <code>${esc(p.dataset)}</code> dataset. <b>Run</b> shows your result; <b>Submit</b> compares it with the expected result${p.ordered ? " (row order matters)" : " (row order ignored)"}.</p><div id="schemaBox"></div>`;
        return;
      }
      const ex = p.tests.slice(0, p.examples || 3);
      if (customText === null) customText = ex.map((tc) => fmt(tc.args)).join("\n");
      cbody.innerHTML = `<p class="muted" style="margin-top:0">Each line is one test: a JSON list of the arguments. <b>Run</b> checks these lines; <b>Submit</b> runs all ${p.tests.length} tests, hidden ones included.${p.kind === "class" ? " Design problems take [operations, arguments]." : ""}</p>
        <textarea class="io" id="customIn" spellcheck="false" rows="${Math.min(8, ex.length + 1)}"></textarea>`;
      const ta = $("#customIn");
      ta.value = customText;
      ta.oninput = () => (customText = ta.value);
    }
    ctabs.forEach((b) => (b.onclick = () => (b.dataset.c === "cases" ? drawCases() : (lastResultHTML ? (showConsole("result"), (cbody.innerHTML = lastResultHTML), wireCaseTabs()) : null))));
    drawCases();
    let lastResultHTML = "";
    let lastCases = [];

    function argsLabel(args) {
    const s = Array.isArray(args) ? args.map(fmt).join(", ") : fmt(args);
    return s.length > 1500 ? s.slice(0, 1500) + ` … (${s.length.toLocaleString()} chars, truncated)` : s;
  }

    function wireCaseTabs() {
      const holder = $("#caseDetail");
      if (!holder) return;
      const btns = $$(".case-tabs button", cbody);
      const show = (i) => {
        btns.forEach((b) => b.classList.toggle("on", +b.dataset.i === i));
        const c = lastCases[i];
        holder.innerHTML = `<div class="io-label">Input</div><div class="io">${esc(c.args_s)}</div>
          ${c.error ? `<div class="io-label">Error</div><div class="io err">${esc(c.error)}</div>` : `<div class="io-label">Your output</div><div class="io">${esc(c.got_s)}</div>`}
          ${c.exp_s != null ? `<div class="io-label">Expected</div><div class="io">${esc(c.exp_s)}</div>` : ""}
          ${c.stdout ? `<div class="io-label">Stdout</div><div class="io">${esc(c.stdout)}</div>` : ""}
          ${c.ms !== undefined ? `<div class="io-label">Runtime</div><div class="muted" style="font-size:13px">${c.ms} ms</div>` : ""}`;
      };
      btns.forEach((b) => (b.onclick = () => show(+b.dataset.i)));
      const firstBad = lastCases.findIndex((c) => !c.ok);
      show(firstBad >= 0 ? firstBad : 0);
    }

    function setBusy(on, label) {
      ["#runBtn", "#submitBtn", "#runBtnM", "#submitBtnM"].forEach((s) => { const b = $(s); if (b) b.disabled = on; });
      if (on) { showConsole("result"); cbody.innerHTML = `<div class="progress-line"></div><p class="muted">${esc(label)}</p>`; }
    }

    function record(submit, verdict, passed, total) {
      store.set((s) => {
        const tr = (s.tried[pid] = s.tried[pid] || { subs: [] });
        if (submit) {
          tr.subs.push({ at: Date.now(), verdict, passed, total, ok: verdict === "Accepted" });
          if (tr.subs.length > 30) tr.subs.shift();
          if (verdict === "Accepted") { if (!s.solved[pid]) bump(s); s.solved[pid] = Date.now(); }
        }
      });
    }

    async function run(submit) {
      const code = cm.getValue();
      store.set((s) => (s.code[pid] = code));
      if (window.innerWidth < 900) showPane("console");
      if (isSql) return runSql(code, submit);
      const lines = submit ? [] : (customText ?? "").split("\n").map((x) => x.trim()).filter(Boolean);
      const total = submit ? p.tests.length : lines.length;
      setBusy(true, Py.isReady() ? `Running ${total} test${total > 1 ? "s" : ""}…` : "Starting Python in your browser (first run downloads ~10 MB)…");
      let done = 0;
      try {
        // Tests are loaded and compared inside Python (lossless for big ints and floats).
        const res = await Py.judge(code, t.id, pid, submit ? "submit" : "run", lines, (d) => {
          if (d.type === "progress") { done++; const pl = $(".muted", cbody); if (pl) pl.textContent = `Running… ${done}/${total}`; }
        }, submit ? 25000 : 20000);
        if (res.invalid) {
          lastCases = []; lastResultHTML = `<p class="verdict bad">Invalid test input</p><div class="io err">${esc(res.invalid)}</div>`;
          showConsole("result"); cbody.innerHTML = lastResultHTML; return;
        }
        const cases = res.results.map((c) => {
          // Per-test time limit: 40x the reference (native CPython) runtime, at least 1 s.
          const limit = c.ref_ms != null ? Math.max(1000, c.ref_ms * 40) : Infinity;
          if (c.ok && c.ms > limit) { c.ok = false; c.slow = true; c.error = `Time Limit Exceeded: ${c.ms.toFixed(0)} ms (limit ${limit.toFixed(0)} ms). Your answer is correct but too slow; look for a better time complexity.`; }
          return c;
        });
        res.passed = cases.filter((c) => c.ok).length;
        const hasErr = cases.find((c) => c.error && !c.slow) || cases.find((c) => c.error);
        const ms = cases.reduce((a, c) => a + (c.ms || 0), 0);
        let verdict, cls;
        if (res.passed === res.total) { verdict = submit ? "Accepted" : "All examples passed"; cls = "ok"; }
        else if (cases.some((c) => c.slow) && !cases.some((c) => !c.ok && !c.slow)) { verdict = "Time Limit Exceeded"; cls = "warn"; }
        else if (hasErr && !hasErr.slow) { verdict = /SyntaxError|IndentationError/.test(hasErr.error) ? "Compile Error" : "Runtime Error"; cls = "bad"; }
        else { verdict = "Wrong Answer"; cls = "bad"; }
        record(submit, verdict, res.passed, res.total);
        // On submit show at most: the failing case (like LeetCode) + all examples
        lastCases = submit && res.passed !== res.total ? cases.filter((c, i) => i < (p.examples || 3) || !c.ok).slice(0, 12) : cases.slice(0, submit ? Math.min(cases.length, 12) : cases.length);
        lastResultHTML = `<p class="verdict ${cls}">${verdict}</p>
          <p class="muted" style="margin:0">${res.passed} / ${res.total} tests passed · ${ms.toFixed(1)} ms total${submit && res.passed === res.total ? " · 🎉 marked as solved" : ""}</p>
          ${submit && res.passed !== res.total ? `<p class="muted" style="font-size:13px">Showing the examples and the first failing hidden tests.</p>` : ""}
          <div class="case-tabs">${lastCases.map((c, i) => `<button class="${c.ok ? "ok" : "bad"}" data-i="${i}">${c.ok ? "✓" : "✗"} Case ${c.i + 1}</button>`).join("")}</div>
          <div id="caseDetail"></div>
          ${submit && res.passed === res.total ? nextSteps() : ""}`;
        showConsole("result");
        cbody.innerHTML = lastResultHTML;
        wireCaseTabs();
      } catch (e) {
        const tle = e.tle;
        record(submit, tle ? "Time Limit Exceeded" : "Runtime Error", done, total);
        lastResultHTML = `<p class="verdict ${tle ? "warn" : "bad"}">${tle ? "Time Limit Exceeded" : "Error"}</p>
          <p class="muted">${tle ? `Your code ran too long (passed ${done} of ${total} before stopping). Look for a more efficient algorithm or an infinite loop.` : ""}</p>${tle ? "" : `<div class="io err">${esc(e.message)}</div>`}`;
        lastCases = [];
        showConsole("result");
        cbody.innerHTML = lastResultHTML;
      } finally { setBusy(false); }
    }

    function nextSteps() {
      return Ghibli.quoteHTML("ok" + pid) + `<div style="margin-top:14px;display:flex;gap:8px;flex-wrap:wrap">${nextP ? `<a class="btn primary sm" href="#/problem/${nextP}">Next problem →</a>` : `<a class="btn primary sm" href="#/track/${t.id}">Back to track</a>`}<button class="btn sm" onclick="document.querySelector('[data-t=guide]').click()">Compare with the walkthrough</button></div>`;
    }

    async function runSql(code, submit) {
      setBusy(true, "Running query…");
      try {
        const { res, ms } = await Sql.run(code, p.dataset);
        const r = res[res.length - 1];
        const got = r ? { columns: r.columns, rows: r.values } : { columns: [], rows: [] };
        let html = "";
        if (submit) {
          const ok = sqlEqual(got, p.expected, p.ordered);
          const verdict = ok ? "Accepted" : "Wrong Answer";
          record(true, verdict, ok ? 1 : 0, 1);
          html += `<p class="verdict ${ok ? "ok" : "bad"}">${verdict}</p><p class="muted" style="margin:0 0 8px">${got.rows.length} row(s) returned · expected ${p.expected.rows.length} · ${ms.toFixed(1)} ms${ok ? " · 🎉 marked as solved" : ""}</p>`;
          if (!ok) html += `<p class="muted" style="font-size:13px">${sqlDiffHint(got, p.expected, p.ordered)}</p>`;
        } else html += `<p class="muted" style="margin:0 0 8px">${got.rows.length} row(s) · ${ms.toFixed(1)} ms</p>`;
        html += `<div class="io-label">Your result</div><div class="sql-result">${Sql.table(r)}</div>`;
        if (submit) html += `<div class="io-label">Expected</div><div class="sql-result">${Sql.table({ columns: p.expected.columns, values: p.expected.rows })}</div>`;
        if (submit && sqlEqual(got, p.expected, p.ordered)) html += nextSteps();
        lastResultHTML = html; lastCases = [];
        showConsole("result"); cbody.innerHTML = html;
      } catch (e) {
        lastResultHTML = `<p class="verdict bad">SQL Error</p><div class="io err">${esc(e.message)}</div>`;
        showConsole("result"); cbody.innerHTML = lastResultHTML;
      } finally { setBusy(false); }
    }

    $("#runBtn").onclick = () => run(false);
    $("#submitBtn").onclick = () => run(true);
    $("#runBtnM").onclick = () => run(false);
    $("#submitBtnM").onclick = () => run(true);
    if (isSql) Sql.warm(); else Py.warm();
    if (isSql) {
      // show dataset schema under testcases
      getText(`data/datasets/${p.dataset}.sql`).then((sql) => {
        const box = $("#schemaBox");
        if (!box) return;
        const creates = sql.match(/CREATE TABLE[\s\S]*?\);/gi) || [];
        box.innerHTML = `<div class="io-label">Schema</div><pre class="io">${esc(creates.join("\n\n"))}</pre>`;
      }).catch(() => {});
    }
  }

  function normVal(v) { if (typeof v === "number") return Math.round(v * 1e6) / 1e6; return v; }
  function sqlEqual(got, exp, ordered) {
    if (got.columns.length !== exp.columns.length) return false;
    if (got.rows.length !== exp.rows.length) return false;
    const a = got.rows.map((r) => JSON.stringify(r.map(normVal)));
    const b = exp.rows.map((r) => JSON.stringify(r.map(normVal)));
    if (!ordered) { a.sort(); b.sort(); }
    return a.every((x, i) => x === b[i]);
  }
  function sqlDiffHint(got, exp, ordered) {
    if (got.columns.length !== exp.columns.length) return `Expected ${exp.columns.length} column(s) (${exp.columns.map(esc).join(", ")}), got ${got.columns.length}.`;
    if (got.rows.length !== exp.rows.length) return `Row count differs: check your filters, joins (duplicates?) and GROUP BY.`;
    if (ordered) {
      const a = got.rows.map((r) => JSON.stringify(r.map(normVal))).sort(), b = exp.rows.map((r) => JSON.stringify(r.map(normVal))).sort();
      if (a.every((x, i) => x === b[i])) return "Right rows, wrong order: check ORDER BY.";
    }
    return "Same shape but some values differ: check calculations, rounding and NULL handling.";
  }

  // ---------------------------------------------------------------- search
  function viewSearch(q) {
    renderSidebar(null);
    const ql = q.toLowerCase().trim();
    const res = [];
    DATA.index.forEach((ti) => {
      const t = DATA.tracks[ti.id];
      if (!t) return;
      t.modules.forEach((m) => {
        (m.lessons || []).forEach((l) => {
          const hay = `${l.title} ${m.title} ${t.title}`.toLowerCase();
          if (hay.includes(ql)) res.push({ href: `#/lesson/${t.id}/${l.id}`, title: l.title, sub: `${t.title} · ${m.title}`, kind: "Lesson", score: l.title.toLowerCase().includes(ql) ? 2 : 1 });
        });
        (m.problems || []).forEach((pid) => {
          const meta = t.problemIndex[pid];
          if (!meta) return;
          const hay = `${meta.title} ${meta.pattern || ""} ${pid}`.toLowerCase();
          if (hay.includes(ql)) res.push({ href: `#/problem/${pid}`, title: meta.title, sub: `${t.title} · ${meta.difficulty}${meta.pattern ? " · " + meta.pattern : ""}`, kind: "Problem", score: meta.title.toLowerCase().includes(ql) ? 2 : 1 });
        });
      });
    });
    res.sort((a, b) => b.score - a.score);
    setPage(`<div class="page narrow"><div class="crumbs"><a href="#/">Home</a></div><h1 class="page-title">Search: “${esc(q)}”</h1>
      <p class="muted">${res.length} result(s)</p>
      <div class="table-wrap">${res.length ? res.slice(0, 200).map((r) => `<a class="lesson-row" href="${r.href}"><span class="pill">${r.kind}</span><span><b>${esc(r.title)}</b><br><span class="muted" style="font-size:13px">${esc(r.sub)}</span></span></a>`).join("") : `<div class="loading">Nothing found. Try a broader word.</div>`}</div></div>`);
  }

  function viewNotFound() {
    renderSidebar(null);
    setPage(`<div class="page narrow"><h1 class="page-title">Lost at sea</h1><p>That page doesn't exist (yet). <a href="#/">Back to the home port</a>.</p></div>`);
  }

  // ---------------------------------------------------------------- router
  async function route() {
    const hash = location.hash.replace(/^#\/?/, "");
    const [path, query] = hash.split("?");
    const parts = path.split("/").filter(Boolean).map(decodeURIComponent);
    try {
      if (!parts.length) viewHome();
      else if (parts[0] === "track") viewTrack(parts[1]);
      else if (parts[0] === "lesson") await viewLesson(parts[1], parts[2]);
      else if (parts[0] === "problem") await viewProblem(parts[1]);
      else if (parts[0] === "problems") viewProblems(new URLSearchParams(query || "").get("q"));
      else if (parts[0] === "roadmap") viewRoadmap();
      else if (parts[0] === "gallery") viewGallery(parts[1]);
      else if (parts[0] === "credits") viewCredits();
      else if (parts[0] === "search") viewSearch(new URLSearchParams(query || "").get("q") || "");
      else viewNotFound();
    } catch (e) {
      console.error(e);
      setPage(`<div class="page narrow"><h1 class="page-title">Something went wrong</h1><pre class="io err">${esc(e.stack || e.message)}</pre></div>`);
    }
  }
  window.addEventListener("hashchange", route);

  $("#searchForm").onsubmit = (e) => {
    e.preventDefault();
    const q = $("#searchInput").value.trim();
    if (q) location.hash = `#/search?q=${encodeURIComponent(q)}`;
    $("#searchInput").blur();
  };

  // ---------------------------------------------------------------- settings
  const dlg = $("#settingsDlg");
  function drawAcct(msg, bad) {
    const box = $("#acct");
    if (!box) return;
    const u = Cloud.user();
    box.innerHTML = u
      ? `<h3>Account</h3><p>Signed in as <b>${esc(u)}</b>. Progress syncs automatically${Cloud.last() ? " · last synced " + Cloud.last().toLocaleTimeString() : ""}.</p>
         <div class="dlg-row"><button type="button" class="btn" id="acSync">Sync now</button><button type="button" class="btn" id="acOut">Log out</button></div>`
      : `<h3>Save progress across devices (optional)</h3>
         <p class="acct-warn"><b>Read this first.</b> Choose a simple username and a <b>new password you have never used anywhere else</b>. Accounts exist only to save study progress, and this site may be shared by several people, so do not use a real password. There is no password reset.</p>
         <div class="acct-form"><input id="acU" placeholder="username (a-z, 0-9, _)" autocomplete="username" maxlength="20" autocapitalize="none" spellcheck="false">
         <input id="acP" type="password" placeholder="new password (6+ characters)" autocomplete="new-password" maxlength="72"></div>
         <div class="dlg-row"><button type="button" class="btn primary" id="acReg">Create account</button><button type="button" class="btn" id="acIn">Log in</button></div>`;
    box.insertAdjacentHTML("beforeend", `<p id="acMsg" class="${bad ? "acct-bad" : "muted"}" style="font-size:13px;min-height:1.2em">${esc(msg || "")}</p>`);
    const drawMsg = (m) => { const el = $("#acMsg"); if (el) { el.className = "muted"; el.textContent = m; } };
    const act = (fn, working, done) => async () => {
      drawMsg(working);
      try { await fn(); drawAcct(done); route(); } catch (e) { drawAcct(e.message, true); }
    };
    if (u) {
      $("#acSync").onclick = act(async () => { await Cloud.pull(); await Cloud.push(); }, "Syncing…", "Synced.");
      $("#acOut").onclick = act(() => Cloud.logout(), "Logging out…", "Logged out. Your progress stays in this browser.");
    } else {
      const vals = () => [$("#acU").value, $("#acP").value];
      $("#acReg").onclick = () => { const [a, b] = vals(); act(() => Cloud.register(a, b), "Creating account…", "Account created. Progress will sync from now on.")(); };
      $("#acIn").onclick = () => { const [a, b] = vals(); act(() => Cloud.login(a, b), "Logging in…", "Logged in and synced.")(); };
    }
  }
  $("#settingsBtn").onclick = () => { drawAcct(); $("#optVim").checked = !!S().opts.vim; $("#optWrap").checked = !!S().opts.wrap; dlg.showModal(); };
  $("#optVim").onchange = (e) => store.set((s) => (s.opts.vim = e.target.checked));
  $("#optWrap").onchange = (e) => store.set((s) => (s.opts.wrap = e.target.checked));
  $("#exportBtn").onclick = () => {
    const blob = new Blob([JSON.stringify(S(), null, 1)], { type: "application/json" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `grand-line-progress-${new Date().toISOString().slice(0, 10)}.json`;
    a.click();
    setTimeout(() => URL.revokeObjectURL(a.href), 1000);
  };
  $("#importFile").onchange = async (e) => {
    const f = e.target.files[0];
    if (!f) return;
    try { store.replace(JSON.parse(await f.text())); alert("Progress imported."); dlg.close(); route(); }
    catch (err) { alert("Could not import: " + err.message); }
  };
  $("#resetBtn").onclick = () => { if (confirm("Erase ALL progress, code and notes in this browser?")) { store.replace({}); dlg.close(); route(); } };

  // ---------------------------------------------------------------- boot
  window.__sg = { Py, Sql, DATA, getProblem }; // debugging hook used by the self-test
  Promise.all([loadAll(), Ghibli.load(), Cloud.pull().catch(() => {})]).then(route).catch((e) => {
    main.innerHTML = `<div class="page narrow"><h1 class="page-title">Could not load content</h1><p class="muted">${esc(e.message)}</p><p>If you opened the file directly, serve the <code>docs/</code> folder over HTTP (e.g. <code>python -m http.server</code>).</p></div>`;
  });
})();
