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
      try { await rpc("sg_save", { ...creds(), p_data: { ...clean(S()), _stats: computeStats() } }, keepalive); S()._dirty = false; store.save(); last = new Date(); }
      catch (e) { if (/Session expired/.test(e.message)) setSess(null); throw e; }
      finally { busy = false; }
    }
    async function pull() {
      if (!sess) return false;
      let remote;
      try { remote = (await rpc("sg_load", creds())) || {}; } catch (e) { if (/Session expired/.test(e.message)) setSess(null); throw e; }
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
      user: () => (sess ? sess.u : null), last: () => last, pull, push, board: () => rpc("sg_leaderboard", {}),
      async judge(language, files, stdin) {
        if (!sess) throw new Error("LOGIN");
        const r = await fetch("https://xupqehazxffimjdvdgbh.supabase.co/functions/v1/judge", { method: "POST", headers: { apikey: KEY, "Content-Type": "application/json" },
          body: JSON.stringify({ username: sess.u, token: sess.t, language, files, stdin: stdin || "" }) });
        const j = await r.json().catch(() => null);
        if (r.status === 401) throw new Error("LOGIN");
        if (!r.ok || !j) throw new Error((j && j.error) || `Judge error (${r.status})`);
        return j;
      },
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
    let html = `<a class="side-track ${!activeTrack ? "active" : ""}" href="#/"><span class="ico">🏰</span><span class="lbl">Home</span></a>
      <a class="side-track" href="#/roadmap"><span class="ico">🗺️</span><span class="lbl">Roadmap</span></a>
      <a class="side-track ${activeTrack === "#plan" ? "active" : ""}" href="#/plan"><span class="ico">📅</span><span class="lbl">Study plan</span></a>
      <a class="side-track ${activeTrack === "#mock" ? "active" : ""}" href="#/mock"><span class="ico">🎤</span><span class="lbl">Mock interviews</span></a>
      <a class="side-track" href="#/scoreboard"><span class="ico">🏆</span><span class="lbl">Scoreboard</span></a>
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
    if (lang === "js-run") { pending[id] = { type: "js", code }; return `<div class="runnable" id="${id}"></div>`; }
    if (lang === "html-run") { pending[id] = { type: "html", code }; return `<div class="runnable" id="${id}"></div>`; }
    if (lang === "fastapi-run") { pending[id] = { type: "api", code, info: infoStr }; return `<div class="runnable" id="${id}"></div>`; }
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
        else if (b.type === "js") WebKit.mountJs(el, b.code, makeEditor);
        else if (b.type === "html") WebKit.mountHtml(el, b.code, makeEditor);
        else if (b.type === "api") mountApi(el, b.code, b.info);
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
      renderInline($(".qq", q), quizText(`${i + 1}. ${it.q}`));
      const opts = $(".qopts", q);
      const reveal = (chosen) => {
        $$(".qopt", opts).forEach((b, j) => {
          b.disabled = true;
          if (j === it.answer) b.classList.add("right");
          else if (j === chosen) b.classList.add("wrong");
        });
        if (!$(".qexp", q)) {
          const ex = h(`<div class="qexp"></div>`);
          renderInline(ex, (chosen === it.answer ? "✅ **Correct.** " : "❌ **Not quite.** ") + quizText(it.explain));
          q.appendChild(ex);
        }
      };
      it.options.forEach((o, j) => {
        const b = h(`<button class="qopt" type="button"></button>`);
        renderInline(b, quizText(o));
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
  // Quiz strings are plain text with inline markdown, never HTML: show < and > literally outside
  // code spans, so List<Integer>, <Esc> or git restore <file> are not swallowed as unknown tags.
  function quizText(md) {
    return String(md || "").split(/(`[^`\n]+`)/g)
      .map((part, i) => (i % 2 ? part : part.replace(/</g, "&lt;").replace(/>/g, "&gt;"))).join("");
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
      worker = new Worker("assets/judge/worker.js?v=8");
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
        let timer = null;
        const arm = (ms) => {
          clearTimeout(timer);
          timer = setTimeout(() => {
            handlers.delete(id);
            restart();
            reject(Object.assign(new Error("Time Limit Exceeded"), { tle: true }));
          }, ms);
        };
        arm(timeoutMs);
        handlers.set(id, (d) => {
          // package downloads ask for a longer limit; ms 0 restores the normal one
          if (d.type === "timer") arm(d.ms || timeoutMs);
          else if (d.type === "done") { clearTimeout(timer); handlers.delete(id); resolve(d.data); }
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
      appRun: (code, key, onEvent, t = 30000) => call({ type: "app-run", code, key }, onEvent, t),
      appRequest: (key, req, onEvent, t = 15000) => call({ type: "app-request", key, ...req }, onEvent, t),
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
      value, mode: mode === "sql" ? "text/x-sqlite" : mode === "java" ? "text/x-java" : mode === "go" ? "text/x-go" : mode === "js" ? "javascript" : mode === "html" ? "htmlmixed" : { name: "python", version: 3 },
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

  // Output of one Python run: text in `out`, matplotlib PNGs and Plotly frames in `figs`.
  function pyOutput(out, figs) {
    figs.innerHTML = "";
    out.textContent = Py.isReady() ? "" : "Starting Python (first run downloads ~10 MB)…\n";
    let first = true, nFig = 0;
    const span = (s, cls) => { const sp = document.createElement("span"); if (cls) sp.className = cls; sp.textContent = s; out.appendChild(sp); };
    const write = (s, cls) => { if (first) { out.textContent = ""; first = false; } span(s, cls); };
    const onEvent = (d) => {
      if (d.type === "stdout" || d.type === "stderr") write(d.data, d.type === "stderr" ? "err" : "");
      else if (d.type === "status") { if (first) out.textContent = ""; span(d.data + "\n", "note"); }
      else if (d.type === "image") {
        const n = ++nFig;
        const img = h(`<figure class="run-fig"><img alt="Figure ${n} drawn by the code above" width="${d.data.w}" height="${d.data.h}" decoding="async"></figure>`);
        img.firstElementChild.src = "data:image/png;base64," + d.data.png;
        // wide multi-panel figures scroll sideways on phones instead of shrinking to unreadable
        if (d.data.w > 760) { img.firstElementChild.style.minWidth = "520px"; img.tabIndex = 0; }
        figs.appendChild(img);
      } else if (d.type === "plotly") figs.appendChild(WebKit.plotlyFrame(d.data, ++nFig));
    };
    const end = () => {
      if (!first) return;
      if (figs.childElementCount) out.textContent = "";
      else write("(no output)");
    };
    return { write, onEvent, end };
  }

  // ```fastapi-run: the block defines a FastAPI `app`; a request panel calls it in-process (no network).
  function mountApi(el, code, info) {
    const opt = (k) => (info.match(new RegExp(`\\b${k}=(\\S+)`)) || [])[1];
    const key = el.id;
    el.innerHTML = `<div class="runnable-bar"><span class="lang">FastAPI</span>
      <button class="reset" type="button">Reset</button><button class="run" type="button">▶ Run</button></div><div class="cm"></div>
      <pre class="runnable-out"></pre><div class="runnable-figs"></div>
      <form class="api" novalidate>
        <div class="api-head"><span class="api-title">Try a request</span><span class="api-hint">Send runs the code above first if it changed.</span></div>
        <div class="api-routes" role="group" aria-label="Routes in this app" hidden></div>
        <div class="api-row">
          <select class="api-method" aria-label="HTTP method">${["GET", "POST", "PUT", "PATCH", "DELETE"].map((m) => `<option>${m}</option>`).join("")}</select>
          <input class="api-path" type="text" aria-label="Path and query string" autocomplete="off" autocapitalize="off" spellcheck="false">
          <button class="api-send" type="submit">Send</button>
        </div>
        <label class="api-field api-body-wrap"><span>JSON body</span><textarea class="api-body" rows="5" spellcheck="false" autocapitalize="off"></textarea></label>
        <details class="api-more"><summary>Request headers</summary>
          <label class="api-field"><span>One per line, as <code>Name: value</code></span><textarea class="api-headers" rows="2" spellcheck="false" autocapitalize="off" placeholder="X-Token: secret"></textarea></label></details>
        <div class="api-resp" aria-live="polite"></div>
      </form>`;
    const original = code.replace(/\n$/, "");
    const out = $(".runnable-out", el), figs = $(".runnable-figs", el), runBtn = $(".run", el), sendBtn = $(".api-send", el);
    const method = $(".api-method", el), path = $(".api-path", el), body = $(".api-body", el), hdrs = $(".api-headers", el);
    const resp = $(".api-resp", el), routesBox = $(".api-routes", el), bodyWrap = $(".api-body-wrap", el);
    method.value = (opt("method") || "GET").toUpperCase();
    path.value = opt("path") || "/";
    let lastRun = null, routes = [], autoBody = "";
    const syncBody = () => { bodyWrap.hidden = method.value === "GET"; };
    method.onchange = syncBody; syncBody();
    const cm = makeEditor($(".cm", el), original, "python", { auto: true, keys: { "Ctrl-Enter": () => run(), "Cmd-Enter": () => run() } });
    $(".reset", el).onclick = () => cm.setValue(original);
    const busy = (on, label) => {
      runBtn.disabled = sendBtn.disabled = on;
      runBtn.textContent = on && label === "run" ? "Running…" : "▶ Run";
      sendBtn.textContent = on && label === "send" ? "Sending…" : "Send";
    };
    const pick = (r, focus) => {
      method.value = r.method; path.value = r.path; syncBody();
      if (r.body && (!body.value.trim() || body.value === autoBody)) body.value = autoBody = r.body;
      if (!focus) return;
      path.focus();
      const m = r.path.match(/\{[^}]+\}/);   // select the first {param} so it can be typed over
      if (m) path.setSelectionRange(m.index, m.index + m[0].length);
    };
    // the route a concrete request goes to, e.g. POST /items/7 -> POST /items/{item_id}
    const routeFor = (m, p) => routes.find((r) => r.method === m &&
      new RegExp("^" + r.path.replace(/[.*+?^$()|[\]\\]/g, "\\$&").replace(/\{[^}]+\}/g, "[^/]+") + "$").test(p.split("?")[0]));
    function showRoutes() {
      routesBox.innerHTML = "";
      routes.filter((r) => !/^\/(docs|redoc|openapi\.json)/.test(r.path)).forEach((r) => {
        const b = h(`<button type="button" class="api-route"><b>${esc(r.method)}</b> ${esc(r.path)}</button>`);
        if (r.summary) b.title = r.summary;
        b.onclick = () => pick(r, true);
        routesBox.appendChild(b);
      });
      routesBox.hidden = !routesBox.childElementCount;
    }
    async function run() {
      busy(true, "run");
      const src = cm.getValue(), o = pyOutput(out, figs);
      let ok = false;
      try {
        const r = await Py.appRun(src, key, o.onEvent, 30000);
        if (r.repr && r.repr !== "None") o.write(r.repr + "\n");
        routes = r.routes || []; showRoutes(); lastRun = src; ok = true;
        if (!opt("path") && path.value === "/" && routes.length && !routes.some((x) => x.path === "/")) pick(routes[0]);
        else if (!body.value.trim()) { const r0 = routeFor(method.value, path.value); if (r0 && r0.body) body.value = autoBody = r0.body; }
      } catch (e) { o.write((e.tle ? "⏱ Stopped after 30 s.\n" : "") + e.message, "err"); lastRun = null; }
      o.end();
      if (ok && out.textContent === "(no output)") out.textContent = "";
      busy(false);
      return ok;
    }
    function render(req, r) {
      const cls = r.status >= 500 ? "s5" : r.status >= 400 ? "s4" : r.status >= 300 ? "s3" : "s2";
      resp.innerHTML = `<div class="api-line"><span class="api-req">${esc(req.method)} ${esc(req.path)}</span>
        <span class="api-status ${cls}">${r.status} ${esc(r.reason || "")}</span><span class="api-ms">${r.ms} ms</span></div>
        <details class="api-hdrs"><summary>Response headers (${r.headers.length})</summary><pre>${esc(r.headers.map(([k, v]) => `${k}: ${v}`).join("\n"))}</pre></details>
        <pre class="api-json">${r.body === "" ? '<span class="muted">(empty body)</span>' : esc(r.body)}</pre>
        ${r.error ? `<div class="api-err">${esc(r.error)}</div>` : ""}`;
    }
    async function send(ev) {
      if (ev) ev.preventDefault();
      if (cm.getValue() !== lastRun && !(await run())) { resp.innerHTML = `<div class="api-err">Fix the error in the code above, then send again.</div>`; return; }
      let p = path.value.trim() || "/";
      if (!p.startsWith("/")) p = "/" + p;
      const headers = {};
      hdrs.value.split("\n").forEach((line) => { const i = line.indexOf(":"); if (i > 0) headers[line.slice(0, i).trim()] = line.slice(i + 1).trim(); });
      const req = { method: method.value, path: p, body: method.value === "GET" ? "" : body.value.trim(), headers };
      busy(true, "send");
      resp.innerHTML = `<div class="meta">Sending…</div>`;
      try {
        let r;
        const log = (d) => { if (d.type === "stdout" || d.type === "stderr") { const sp = document.createElement("span"); if (d.type === "stderr") sp.className = "err"; sp.textContent = d.data; out.appendChild(sp); } };
        try { r = await Py.appRequest(key, req, log); }
        catch (e) {
          if (e.message !== "NOAPP") throw e;
          busy(false); if (!(await run())) return; busy(true, "send");   // Python restarted since the last run
          r = await Py.appRequest(key, req, log);
        }
        render(req, r);
      } catch (e) { resp.innerHTML = `<div class="api-err">${esc(e.tle ? "⏱ The request took longer than 15 s." : e.message)}</div>`; }
      busy(false);
    }
    $("form.api", el).onsubmit = send;
    runBtn.onclick = run;
  }

  function mountRunnable(el, code, lang, dataset) {
    el.innerHTML = `<div class="runnable-bar"><span class="lang">${lang === "sql" ? "SQL" + (dataset ? " · " + esc(dataset) : "") : "Python"}</span>
      <button class="reset" type="button">Reset</button><button class="run" type="button">▶ Run</button></div><div class="cm"></div>`;
    const out = h(lang === "sql" ? `<div class="sql-result" hidden></div>` : `<pre class="runnable-out"></pre>`);
    el.appendChild(out);
    const figs = lang === "sql" ? null : el.appendChild(h(`<div class="runnable-figs"></div>`));
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
        const o = pyOutput(out, figs);
        try {
          const r = await Py.run(cm.getValue(), o.onEvent);
          if (r && r.repr && r.repr !== "None") o.write(r.repr + "\n");
        } catch (e) { o.write((e.tle ? "⏱ Stopped after 30 s.\n" : "") + e.message, "err"); }
        o.end();
      }
      btn.disabled = false;
      btn.textContent = "▶ Run";
    }
    btn.onclick = go;
  }


  // ---------------------------------------------------------------- Ghibli stills & quotes
  const TRACK_FILM = { csapp: "laputa", python: "baron", "dsa-foundations": "mimi", "neet-arrays": "majo", "neet-window-stack": "howl",
    "neet-linked-trees": "totoro", "neet-heap-graphs": "mononoke", "neet-dp": "chihiro", "neet-greedy-math": "porco", sql: "kokurikozaka",
    databases: "nausicaa", ml: "kazetachinu", fastapi: "ponyo", mlops: "karigurashi", "ai-eng": "kimitachi", "llm-practice": "kaguyahime", os: "ged", "linux-cli": "yamada", vim: "marnie", cicd: "umi", thinking: "omoide", "html-css": "tanuki", javascript: "red-turtle", git: "aya", networking: "ghiblies", "web-security": "onyourmark", docker: "umi", redis: "baron", mongodb: "nausicaa", nodejs: "howl", react: "totoro", firebase: "ponyo", graphql: "kaguyahime", django: "majo", nginx: "porco", "js-testing": "mimi", typescript: "kazetachinu", go: "laputa", java: "chihiro", spring: "totoro", aws: "nausicaa", kubernetes: "ponyo", terraform: "mononoke", "system-design": "laputa", microservices: "howl", "interview-prep": "mimi" };
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
    const lw = Ghibli.works.laputa;
    const hero = lw && lw.files.includes("laputa036") ? { w: lw, src: "assets/ghibli/laputa/laputa036.webp" } : Ghibli.still("laputa", "hero");
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
    const cont = s.last ? `<a class="btn primary" href="${esc(s.last.href)}">Continue: ${esc(s.last.title)}</a>` : (nextTrack() ? `<a class="btn primary" href="#/track/${nextTrack()}">Start: ${esc(DATA.tracks[nextTrack()].title)}</a>` : `<a class="btn primary" href="#/roadmap">Open the roadmap</a>`);
    setPage(`<div class="page">
      <section class="hero2" ${hero ? `style="background-image:url('${hero.src}')"` : ""}>
        <div class="hero2-in">
          <p class="hero2-kicker">Big Tech interview prep · a Studio Ghibli themed, fan-made study guide</p>
          <h1>Build your castle in the sky, one lesson a day.</h1>
          <p>Everything top tech companies interview on: algorithms with a live judge, systems, operating systems, Linux, SQL and databases, CI/CD, machine learning, MLOps, AI engineering and open-ended engineering questions.</p>
          <div class="hero2-cta">${cont}<a class="btn glass" href="#/roadmap">Roadmap</a><button class="btn glass" id="rndBtn" type="button">Random problem</button></div>
        </div>
        ${hero ? `<div class="hero2-credit">${Ghibli.credit(hero.w)}</div>` : ""}
      </section>
      ${homePlanHTML()}
      <div class="dash">
        <div class="card dash-ring">
          <svg viewBox="0 0 120 120" width="120" height="120" aria-hidden="true"><circle cx="60" cy="60" r="52" fill="none" stroke="var(--surface-2)" stroke-width="10"/>
            <circle cx="60" cy="60" r="52" fill="none" stroke="var(--accent)" stroke-width="10" stroke-linecap="round" stroke-dasharray="${(C * frac).toFixed(1)} ${C.toFixed(1)}" transform="rotate(-90 60 60)"/>
            <text x="60" y="58" text-anchor="middle" font-size="24" font-weight="800" fill="currentColor">${solved}</text><text x="60" y="76" text-anchor="middle" font-size="11" fill="currentColor" opacity=".6">of ${nProb} solved</text></svg>
          <div class="dash-diff">${["Easy", "Medium", "Hard"].map((d) => `<div><span class="diff ${d}">${d}</span><b>${diff[d][0]}/${diff[d][1]}</b></div>`).join("")}
            <div><span class="muted">Lessons read</span><b>${read}/${totals.lessons}</b></div>
            <div><a href="#/scoreboard">${levelOf(computeStats().points).name}</a><b>${computeStats().points} pts</b></div></div>
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
    const hp = $("#homePlan");
    if (hp) wirePlanChecks(hp, () => { const p = S().plan, st = p && planStatus(p, buildPlan(p)), el = $("#homePlanSt"); if (st && el) { el.textContent = st.label; el.className = "pl-badge " + st.cls; } });
    const rb = $("#rndBtn");
    if (rb) rb.onclick = () => { const p = randomUnsolved(); if (p) location.hash = `#/problem/${p}`; };
  }

  // ---------------------------------------------------------------- scoreboard
  const LEVELS = [[0, "Seedling"], [100, "Sprout"], [300, "Wanderer"], [700, "Navigator"], [1500, "Pilot"], [3000, "Sky Captain"], [6000, "Castle Keeper"]];
  const levelOf = (pts) => { let i = 0; LEVELS.forEach((l, k) => { if (pts >= l[0]) i = k; }); return { name: LEVELS[i][1], n: i + 1, next: LEVELS[i + 1] ? LEVELS[i + 1][0] : null }; };
  function computeStats() {
    const s = S(), PTS = { Easy: 10, Medium: 20, Hard: 40 }, tracks = {};
    let points = 0, problems = 0;
    Object.keys(s.solved || {}).forEach((pid) => {
      const loc = DATA.problemTrack[pid];
      if (!loc) return;
      const m = DATA.tracks[loc.track].problemIndex[pid];
      points += PTS[m.difficulty] || 10; problems++; tracks[loc.track] = (tracks[loc.track] || 0) + 1;
    });
    const lessons = Object.keys(s.lessons || {}).filter((k) => DATA.tracks[k.split("/")[0]]).length;
    points += lessons * 5;
    return { points, problems, lessons, streak: streaks().best, tracks };
  }
  async function viewScoreboard() {
    renderSidebar(null);
    const me = computeStats(), lv = levelOf(me.points), u = Cloud.user();
    const rows = DATA.index.map((ti) => {
      const t = DATA.tracks[ti.id];
      if (!t) return "";
      const p = trackProgress(t);
      return `<a class="lesson-row" href="#/track/${t.id}"><span class="st">${esc(t.icon || "")}</span><span style="flex:1;min-width:0">${esc(t.title)}<span class="bar" style="display:block;margin-top:4px"><i style="width:${p.pct}%"></i></span></span><span class="mins">${me.tracks[t.id] || 0}/${ti.problems} problems · ${p.pct}%</span></a>`;
    }).join("");
    setPage(`<div class="page narrow"><div class="crumbs"><a href="#/">Home</a></div><h1 class="page-title">Scoreboard</h1>
      <p class="muted">Points count across every track: 10 for an Easy problem, 20 for Medium, 40 for Hard, and 5 for each lesson you complete.</p>
      <div class="card"><div class="streak-row" style="flex-wrap:wrap"><div><b>${me.points}</b><span>points</span></div><div><b>${esc(lv.name)}</b><span>level ${lv.n}${lv.next ? " · next at " + lv.next : " · top level"}</span></div><div><b>${me.problems}</b><span>problems solved</span></div><div><b>${me.lessons}</b><span>lessons done</span></div><div><b>${me.streak}</b><span>best streak</span></div></div>
        ${lv.next ? `<div class="bar" style="margin-top:12px"><i style="width:${Math.min(100, Math.round((100 * me.points) / lv.next))}%"></i></div>` : ""}</div>
      <div class="section-h"><h2>Leaderboard</h2></div>
      ${u ? "" : `<p class="muted">Create an account in ⚙ to appear here. Usernames on the leaderboard are public.</p>`}
      <div class="table-wrap" id="lb"><div class="loading">Loading…</div></div>
      <div class="section-h"><h2>Your progress by track</h2></div><div class="table-wrap" style="padding:8px">${rows}</div></div>`);
    if (u) await Cloud.push().catch(() => {});
    const lb = $("#lb");
    try {
      const list = (await Cloud.board()) || [];
      if (!lb) return;
      lb.innerHTML = list.length ? `<table class="ptable"><thead><tr><th>#</th><th>Player</th><th>Level</th><th>Points</th><th class="pat">Problems</th><th class="pat">Lessons</th><th class="pat">Best streak</th></tr></thead><tbody>${list.map((r, i) => {
        const st = r.stats || {}, pts = +st.points || 0;
        return `<tr class="${r.username === u ? "me" : ""}"><td>${i < 3 ? ["🥇", "🥈", "🥉"][i] : i + 1}</td><td><b>${esc(r.username)}</b>${r.username === u ? " (you)" : ""}</td><td>${esc(levelOf(pts).name)}</td><td><b>${pts}</b></td><td class="pat">${+st.problems || 0}</td><td class="pat">${+st.lessons || 0}</td><td class="pat">${+st.streak || 0}</td></tr>`;
      }).join("")}</tbody></table>` : `<div class="loading">No players yet. Be the first.</div>`;
    } catch (e) {
      if (lb) lb.innerHTML = `<div class="loading">The leaderboard is not available yet.</div>`;
    }
  }

  // ---------------------------------------------------------------- roadmap (recommended study flow)
  const PATH = [
    { title: "Start here", why: "The tools every later stage assumes. Python is also the most requested language in Singapore tech postings.",
      tracks: [["python", "Python Mastery"], ["linux-cli", "The Linux Command Line"], ["git", "Git"], ["vim", "Practical Vim"]] },
    { title: "Interview coding", why: "Every junior posting asks for data structures and algorithms, and the coding round tests them. Keep a few problems going every day from here on.",
      tracks: [["dsa-foundations", "DSA Foundations"], ["neet-arrays", "Arrays, Hashing & Two Pointers"], ["neet-window-stack", "Sliding Window, Stack & Binary Search"],
        ["neet-linked-trees", "Linked Lists, Trees & Tries"], ["neet-heap-graphs", "Heaps, Backtracking & Graphs"], ["neet-dp", "Dynamic Programming"], ["neet-greedy-math", "Greedy, Intervals, Math & Bits"], ["dsa-js", "DSA in JavaScript"],
        ["interview-prep", "Cracking the Coding Interview"], ["behavioural", "Behavioural Interviews"]] },
    { title: "SQL and data stores", why: "SQL is the second most requested skill in Singapore postings and has its own interview round.",
      tracks: [["sql", "SQL"], ["databases", "Databases & Data-Intensive Systems"], ["redis", "Redis"], ["mongodb", "MongoDB"]] },
    { title: "A backend language and framework", why: "Postings ask for one strong backend language. Java with Spring and Go lead in Singapore; Python and Node.js follow. Learn one stack well, then skim the others.",
      tracks: [["java", "Java"], ["spring", "Spring Boot"], ["go", "Go"], ["fastapi", "FastAPI & Backend"], ["javascript", "JavaScript"], ["typescript", "TypeScript"],
        ["nodejs", "Node.js"], ["graphql", "GraphQL & API Design"], ["django", "Django"]] },
    { title: "Cloud and DevOps", why: "AWS, containers and automation show up in a large and rising share of postings.",
      tracks: [["docker", "Docker & Containers"], ["kubernetes", "Kubernetes"], ["aws", "AWS"], ["terraform", "Terraform"], ["cicd", "CI/CD"], ["jira", "Jira & Agile Delivery"], ["nginx", "NGINX"]] },
    { title: "System design and architecture", why: "The design round, and the open-ended questions around it.",
      tracks: [["networking", "Computer Networking"], ["system-design", "System Design Interview"], ["microservices", "Microservices"], ["web-security", "Web Application Security"], ["thinking", "Open-Ended Engineering Questions"]] },
    { title: "How computers work", why: "The fundamentals behind 'what happens when' questions.",
      tracks: [["csapp", "Computer Systems"], ["os", "Operating Systems"]] },
    { title: "Machine learning and AI", why: "For ML and AI engineer roles: Python, models, LLMs, retrieval and deployment.",
      tracks: [["statistics", "Practical Statistics"], ["ml", "Machine Learning"], ["deep-learning", "Deep Learning with PyTorch"], ["mlops", "MLOps"], ["ai-eng", "AI Engineering"], ["llm-practice", "LLMs Hands-On"]] },
    { title: "Front end", why: "For full-stack roles: pages, React and testing.",
      tracks: [["html-css", "HTML & CSS"], ["react", "React with Firebase"], ["js-testing", "JavaScript Testing"]] },
  ];
  const ROLES = [
    ["Backend engineer", ["python", "git", "behavioural", "linux-cli", "dsa-foundations", "neet-arrays", "sql", "java", "spring", "docker", "aws", "system-design", "jira"]],
    ["Full-stack engineer", ["python", "git", "behavioural", "dsa-foundations", "neet-arrays", "dsa-js", "sql", "javascript", "typescript", "react", "nodejs", "docker", "system-design", "jira"]],
    ["AI / ML engineer", ["python", "git", "behavioural", "dsa-foundations", "neet-arrays", "sql", "statistics", "ml", "deep-learning", "ai-eng", "llm-practice", "fastapi", "docker", "mlops"]],
  ];
  function nextTrack() {
    for (const st of PATH) for (const [id] of st.tracks) { const t = DATA.tracks[id]; if (t && trackProgress(t).pct < 100) return id; }
    return null;
  }
  function viewRoadmap() {
    renderSidebar(null);
    const next = nextTrack();
    let n = 0;
    const stages = PATH.map((st, i) => {
      const cards = st.tracks.map(([id, name]) => {
        n++;
        const t = DATA.tracks[id];
        if (!t) return `<div class="rstep soon"><span class="rn-n">${n}</span><span class="rn-t">${esc(name)}</span><span class="rn-m">Being written</span></div>`;
        const p = trackProgress(t);
        return `<a class="rstep ${p.pct === 100 ? "done" : p.pct ? "started" : ""} ${id === next ? "next" : ""}" href="#/track/${id}">
          <span class="rn-n">${p.pct === 100 ? "✓" : n}</span><span class="rn-t">${esc(t.icon || "")} ${esc(t.title)}</span>
          <span class="bar"><i style="width:${p.pct}%"></i></span><span class="rn-m">${id === next ? "Next up · " : ""}${p.done}/${p.total} done · ${p.pct}%</span></a>`;
      }).join("");
      return `<section class="stage"><h2><span class="stage-n">Stage ${i + 1}</span> ${esc(st.title)}</h2><p class="muted">${esc(st.why)}</p><div class="stage-grid">${cards}</div></section>`;
    }).join("");
    setPage(`<div class="page"><div class="crumbs"><a href="#/">Home</a></div><h1 class="page-title">Roadmap</h1>
      <p class="muted">Follow the stages top to bottom and the numbered tracks left to right. Every stage is asked about in real job descriptions, so none is filler. Start with Stage 1, keep Stage 2 problems going every day, and choose the order of the later stages by the jobs you are applying for.</p>
      <div class="card" style="margin-top:14px"><h3 style="margin:0">Short on time? The first tracks to finish for each role</h3>
        ${ROLES.map(([role, ids]) => `<p style="margin:6px 0 0"><b>${role}:</b> ${ids.map((id) => (DATA.tracks[id] ? `<a href="#/track/${id}">${esc(DATA.tracks[id].title)}</a>` : `<span class="muted">${esc(id)} (being written)</span>`)).join(" → ")}</p>`).join("")}
        <p class="muted" style="font-size:12px;margin:8px 0 0">Ordered from a survey of Singapore job postings in late 2026. The full path below covers everything.</p></div>
      ${stages}${Ghibli.figure("laputa", "roadmap", "wide")}</div>`);
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
    const items = [{ t: "Home", s: "", href: "#/" }, { t: "Roadmap", s: "", href: "#/roadmap" }, { t: "Study plan", s: "Plan", href: "#/plan" }, { t: "Mock interviews", s: "Practice", href: "#/mock" }, { t: "Mock history", s: "Practice", href: "#/mock/history" }, { t: "All problems", s: "", href: "#/problems" }, { t: "Gallery", s: "", href: "#/gallery" }, { t: "Credits", s: "", href: "#/credits" }];
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
    if (/```(python-run|py-run|fastapi-run)/.test(md)) setTimeout(() => Py.warm(), 1500);
  }

  // ---------------------------------------------------------------- problem workspace
  async function viewProblem(pid) {
    const p = await getProblem(pid);
    if (!p) return viewNotFound();
    const t = DATA.tracks[p._loc.track];
    const mod = t.modules.find((m) => m.id === p._loc.module);
    renderSidebar(t.id);
    const isSql = p.kind === "sql", isJs = p.kind === "js", isWeb = p.kind === "web", isSrv = p.kind === "java" || p.kind === "go";
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
            <span class="lang">${isSql ? "SQLite" : isJs ? "JavaScript" : isWeb ? "HTML · CSS" : isSrv ? (p.kind === "java" ? "Java 21" : "Go 1.23") : "Python 3"}</span>
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
            renderMarkdown("```" + (isSql ? "sql" : isJs ? "javascript" : isWeb ? "html" : isSrv ? p.kind : "python") + "\n" + p.solution.trim() + "\n```", $(".prose", sol));
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
    const cm = makeEditor($("#editorHost"), saved || p.starter, isSql ? "sql" : isJs ? "js" : isWeb ? "html" : isSrv ? p.kind : "python", {
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
      if (isWeb) { cbody.innerHTML = `<p class="muted" style="margin-top:0"><b>Run</b> shows a live preview of your page. <b>Submit</b> checks it against these requirements:</p><ul class="checks">${(p.checks || []).map((c) => `<li>${esc(c.name)}</li>`).join("")}</ul>`; return; }
      if (isSrv) { cbody.innerHTML = `<p class="muted" style="margin-top:0">${p.kind === "java" ? "Java" : "Go"} runs on the judge server, so you need to be logged in (open ⚙). <b>Run</b> and <b>Submit</b> both compile your code and run all ${p.cases || ""} tests; expect a result in two or three seconds.</p>`; return; }
      if (isJs) { cbody.innerHTML = `<p class="muted" style="margin-top:0"><b>Run</b> checks the example tests; <b>Submit</b> runs all ${p.tests.length} tests. Use <code>console.log</code> to debug; its output appears with the result.</p>`; return; }
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
      if (isJs) return runJs(code, submit);
      if (isWeb) return runWeb(code, submit);
      if (isSrv) return runServer(code);
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

    async function runServer(code) {
      setBusy(true, "Sending to the judge server…");
      try {
        const java = p.kind === "java", NL = String.fromCharCode(10);
        const files = java ? [{ name: "Main.java", content: p.harness }, { name: "Solution.java", content: code }]
          : [{ name: "main.go", content: p.harness }, { name: "solution.go", content: code }];
        let r;
        try { r = await Cloud.judge(p.kind, files, ""); }
        catch (e) {
          lastCases = [];
          lastResultHTML = e.message === "LOGIN"
            ? `<p class="verdict warn">Log in to run ${java ? "Java" : "Go"}</p><p class="muted">Java and Go run on the judge server, which needs an account. Open ⚙ to create one or log in, then run again.</p>`
            : `<p class="verdict bad">Judge unavailable</p><div class="io err">${esc(e.message)}</div>`;
          showConsole("result"); cbody.innerHTML = lastResultHTML; return;
        }
        const cases = [], other = [];
        (r.stdout || "").split(NL).forEach((ln) => {
          const m = ln.match(/^CASE ([0-9]+) (OK|FAIL) ?(.*)$/);
          if (m) cases.push({ i: +m[1], ok: m[2] === "OK", msg: m[3] }); else if (ln.trim()) other.push(ln);
        });
        const passed = cases.filter((c) => c.ok).length, total = p.cases || cases.length;
        let verdict, cls = "bad";
        if (r.compile_error) verdict = "Compile Error";
        else if (r.timed_out) { verdict = "Time Limit Exceeded"; cls = "warn"; }
        else if (total > 0 && passed === total && cases.length === total && r.code === 0) { verdict = "Accepted"; cls = "ok"; }
        else if (r.code !== 0 && cases.length < total) verdict = "Runtime Error";
        else verdict = "Wrong Answer";
        record(true, verdict, passed, total);
        lastCases = [];
        lastResultHTML = `<p class="verdict ${cls}">${verdict}</p><p class="muted" style="margin:0 0 8px">${passed} / ${total} tests passed · ${r.ms} ms on the server${cls === "ok" ? " · 🎉 marked as solved" : ""}</p>
          ${cases.length ? `<ul class="checks">${cases.map((c) => `<li class="${c.ok ? "ok" : "bad"}">${c.ok ? "✓" : "✗"} Test ${c.i}${c.msg ? ` <span class="muted">${esc(c.msg)}</span>` : ""}</li>`).join("")}</ul>` : ""}
          ${r.stderr ? `<div class="io-label">${r.compile_error ? "Compiler output" : "Errors"}</div><div class="io err">${esc(r.stderr)}</div>` : ""}
          ${other.length ? `<div class="io-label">Your output</div><div class="io">${esc(other.join(NL))}</div>` : ""}${cls === "ok" ? nextSteps() : ""}`;
        showConsole("result"); cbody.innerHTML = lastResultHTML;
      } finally { setBusy(false); }
    }
    async function runJs(code, submit) {
      const tests = submit ? p.tests : p.tests.slice(0, p.examples || 3);
      setBusy(true, `Running ${tests.length} tests…`);
      try {
        const r = await WebKit.runJs(code, p.entry, tests);
        if (r.fatal) {
          record(submit, r.tle ? "Time Limit Exceeded" : "Runtime Error", 0, tests.length);
          lastCases = []; lastResultHTML = `<p class="verdict ${r.tle ? "warn" : "bad"}">${r.tle ? "Time Limit Exceeded" : "Error"}</p><div class="io err">${esc(r.fatal)}</div>`;
        } else {
          const cases = r.results.map((c, i) => {
            let ok = false;
            if (!c.error) { try { ok = WebKit.eq(JSON.parse(c.got_s), tests[i].expected, p.compare || "exact", p.tolerance || 1e-6); } catch (_) {} }
            return { ...c, ok, args_s: tests[i].args.map(fmt).join(", "), exp_s: fmt(tests[i].expected), stdout: "" };
          });
          const passed = cases.filter((c) => c.ok).length, all = passed === cases.length;
          const verdict = all ? (submit ? "Accepted" : "All examples passed") : cases.some((c) => c.error) ? "Runtime Error" : "Wrong Answer";
          record(submit, verdict, passed, cases.length);
          lastCases = cases.filter((c, i) => i < (p.examples || 3) || !c.ok).slice(0, 12);
          lastResultHTML = `<p class="verdict ${all ? "ok" : "bad"}">${verdict}</p><p class="muted" style="margin:0">${passed} / ${cases.length} tests passed${submit && all ? " · 🎉 marked as solved" : ""}</p>
            <div class="case-tabs">${lastCases.map((c, i) => `<button class="${c.ok ? "ok" : "bad"}" data-i="${i}">${c.ok ? "✓" : "✗"} Case ${c.i + 1}</button>`).join("")}</div><div id="caseDetail"></div>
            ${r.logs && r.logs.length ? `<div class="io-label">Console</div><div class="io">${esc(r.logs.slice(0, 200).join(String.fromCharCode(10)))}</div>` : ""}${submit && all ? nextSteps() : ""}`;
        }
        showConsole("result"); cbody.innerHTML = lastResultHTML; wireCaseTabs();
      } finally { setBusy(false); }
    }
    async function runWeb(code, submit) {
      setBusy(true, "Rendering…");
      try {
        let html = "";
        if (submit) {
          const out = await WebKit.runWeb(code, p.checks || []);
          const passed = out.filter((c) => c.ok).length, ok = passed === out.length;
          record(true, ok ? "Accepted" : "Wrong Answer", passed, out.length);
          html = `<p class="verdict ${ok ? "ok" : "bad"}">${ok ? "Accepted" : "Not there yet"}</p><p class="muted" style="margin:0 0 8px">${passed} / ${out.length} requirements met${ok ? " · 🎉 marked as solved" : ""}</p>
            <ul class="checks">${out.map((c) => `<li class="${c.ok ? "ok" : "bad"}">${c.ok ? "✓" : "✗"} ${esc(c.name)}${c.error ? ` <span class="muted">(${esc(c.error)})</span>` : ""}</li>`).join("")}</ul>${ok ? nextSteps() : ""}`;
        }
        lastCases = []; lastResultHTML = html + `<div class="io-label">Preview</div><div id="webPrev" class="web-host"></div>`;
        showConsole("result"); cbody.innerHTML = lastResultHTML; WebKit.preview($("#webPrev"), code);
      } finally { setBusy(false); }
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
    if (isSql) Sql.warm(); else if (!isJs && !isWeb && !isSrv) Py.warm();
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

  // ---------------------------------------------------------------- study plan (#/plan)
  // State: s.plan = { start, end, hours, tracks, ex, genAt, marks, first, replans } (or null).
  // The schedule itself is not stored: it is rebuilt from these settings. Items finished before
  // genAt are left out, so ticking things off later never reshuffles the days.
  const PL = { core: [0, 1, 2, 5], dsaStage: 1, review: 0.12, studyDays: 6, revisit: 15, cost: { Easy: 20, Medium: 35, Hard: 50 }, mock: { coding: 60, design: 60, behavioural: 20 } };
  const MOCK_NAME = { coding: "Coding mock", design: "System design mock", behavioural: "Behavioural mock" };
  const KIND_LABEL = { lesson: "Read", problem: "Practise", revisit: "Revisit", review: "Review", mock: "Mock" };
  const pDate = (k) => { const [y, m, d] = String(k).split("-").map(Number); return new Date(y, m - 1, d); };
  const validDay = (k) => /^\d{4}-\d{2}-\d{2}$/.test(k || "") && !isNaN(pDate(k));
  const addDays = (k, n) => { const d = pDate(k); d.setDate(d.getDate() + n); return dayKey(d); };
  const daysBetween = (a, b) => Math.round((pDate(b) - pDate(a)) / 864e5);
  const yearIf = (k, o) => (Math.abs(pDate(k) - new Date()) > 300 * 864e5 ? { ...o, year: "numeric" } : o);  // show the year when it is not obvious
  const fmtDay = (k, o = { weekday: "short", day: "numeric", month: "short" }) => pDate(k).toLocaleDateString(undefined, yearIf(k, o));
  const fmtShort = (k) => fmtDay(k, { day: "numeric", month: "short" });
  const fmtMin = (m) => { m = Math.round(m); return m < 60 ? `${m} min` : `${Math.floor(m / 60)} h${m % 60 ? " " + (m % 60) + " min" : ""}`; };
  const fmtH = (m) => (m < 60 ? `${Math.round(m)} min` : `${(m / 60).toFixed(m < 6000 ? 1 : 0).replace(/\.0$/, "")} h`);
  const sumMin = (a) => a.reduce((x, i) => x + i.min, 0);
  const lessonCost = (l) => Math.max(5, Math.round(((l.words || 0) / 180) * 1.3));
  const dsaTracks = () => PATH[PL.dsaStage].tracks.map((x) => x[0]);
  const probMeta = (pid) => { const loc = DATA.problemTrack[pid]; return loc && DATA.tracks[loc.track] ? DATA.tracks[loc.track].problemIndex[pid] : null; };
  const coreTracks = () => PL.core.flatMap((i) => PATH[i].tracks.map((x) => x[0])).filter((id) => DATA.tracks[id] && id !== "dsa-js"); // dsa-js repeats the pattern problems in JS: opt-in only

  // Depth "essentials" (default for new plans): neet-* lessons + Easy/Medium problems; python and
  // dsa-foundations lessons + the first problem of each module; every other track its interview,
  // essentials or playbook lessons + the first lesson of each module + about a third of its problems,
  // Easy and Medium first. Depth "all" takes everything (plans saved without a depth used that).
  // Streams: "read" (other tracks and the CTCI hiring/behavioural chapters), "theory" (DSA Foundations)
  // and "pat" (pattern practice: neet-* in NeetCode roadmap order, then CTCI's coding chapters).
  // Tier "A" items are kept before any "B" item when time is short: interview lessons, CTCI's hiring
  // and behavioural chapters, and each pattern's first lesson with its first two Easy/Medium problems.
  const ESS_RE = /interview|essentials|playbook/i;
  const DIFF_RANK = { Easy: 0, Medium: 1, Hard: 2 };
  const DEPTH_NAME = { essentials: "Interview essentials", all: "Everything" };
  function trackItems(id, ex, genAt, marks, depth) {
    const t = DATA.tracks[id], s = S(), out = [];
    let skipped = 0;
    if (!t) return { out, skipped };
    const isD = dsaTracks().includes(id), mk = marks || {}, ess = depth !== "all";
    const neet = /^neet-/.test(id), firstOnly = id === "python" || id === "dsa-foundations", ctci = id === "interview-prep";
    const before = (v) => !!v && (typeof v !== "number" || v < genAt);
    let quota = null;
    if (ess && !neet && !firstOnly) {
      const all = t.modules.flatMap((m) => m.problems || []).filter((p) => t.problemIndex[p]);
      quota = new Set(all.map((p, i) => ({ p, i, r: DIFF_RANK[t.problemIndex[p].difficulty] ?? 1 })).sort((a, b) => a.r - b.r || a.i - b.i)
        .slice(0, Math.ceil(all.length / 3)).map((x) => x.p));
    }
    t.modules.forEach((m) => {
      const probs = (m.problems || []).filter((p) => t.problemIndex[p]);
      // Behavioural rounds are in every interview loop, so that whole track is interview material.
      const soft = (ctci && !probs.length) || id === "behavioural";
      const stream = !isD || soft ? "read" : id === "dsa-foundations" ? "theory" : "pat";
      (m.lessons || []).forEach((l, li) => {
        const key = `${id}/${l.id}`, star = soft || ESS_RE.test(`${l.id} ${l.title}`);
        if (ess && !neet && !firstOnly && li > 0 && !star) return;
        if (before(s.lessons[key])) { skipped++; return; }
        out.push({ c: "L:" + key, k: "lesson", track: id, stream, tier: star || (neet && li === 0) ? "A" : "B", href: `#/lesson/${id}/${l.id}`, title: l.title, sub: t.title, min: lessonCost(l) });
      });
      if (!isD && !ex) return;
      let em = 0;
      probs.forEach((pid, pi) => {
        const x = t.problemIndex[pid];
        if (ess && ((neet && x.difficulty === "Hard") || (firstOnly && pi > 0) || (quota && !quota.has(pid)))) return;
        const core = neet && x.difficulty !== "Hard" && em++ < 2;
        if (before(s.solved[pid]) || before(mk["P:" + pid])) { skipped++; return; }
        out.push({ c: "P:" + pid, k: "problem", track: id, stream, tier: core ? "A" : "B", href: `#/problem/${pid}`, title: x.title, sub: `${x.difficulty} · ${t.title}`, pat: isD ? x.pattern || t.title : null, min: PL.cost[x.difficulty] || 35 });
      });
    });
    return { out, skipped };
  }

  function buildPlan(cfg) {
    const nDays = Math.max(1, daysBetween(cfg.start, cfg.end) + 1);
    const B = (cfg.hours * 60) / PL.studyDays;
    const nRev = nDays >= 10 ? Math.max(2, Math.round(nDays * PL.review)) : 0;
    const days = [];
    for (let i = 0; i < nDays; i++) days.push({ i, key: addDays(cfg.start, i), w: Math.floor(i / 7) + 1, rest: i % 7 === 6, review: i >= nDays - nRev, items: [] });
    const wkEnd = (w) => { const e = addDays(cfg.start, w * 7 - 1); return e > cfg.end ? cfg.end : e; };
    const mockItem = (kind, d) => ({ c: `M:${kind}:${d.key}`, k: "mock", kind, href: "#/mock", title: MOCK_NAME[kind] + " interview",
      sub: kind === "behavioural" ? "5 questions, 2 minutes each" : "45 minutes, then score yourself", min: PL.mock[kind], ws: addDays(cfg.start, (d.w - 1) * 7), we: wkEnd(d.w) });
    // weekly mocks: coding from week 3; from week 5 a second one alternating system design and behavioural
    days.forEach((d) => {
      if (d.rest || d.review || d.w < 3) return;
      if (d.i % 7 === 5) d.items.push(mockItem("coding", d));
      if (d.i % 7 === 2 && d.w >= 5) d.items.push(mockItem(d.w % 2 ? "design" : "behavioural", d));
    });
    const revDays = days.filter((d) => d.review && !d.rest);
    if (revDays.length) {
      const n = revDays.length, put = (j, k) => revDays[j].items.push(mockItem(k, revDays[j]));
      put(0, "coding");
      if (n >= 2) put(Math.floor(n / 2), "design");
      if (n >= 3) put(n - 1, "behavioural");
    }
    // three streams, each in roadmap order: other tracks (45% of the time), DSA theory (25%) and
    // pattern practice (30%); a stream that needs less hands its time to the others
    const W = { read: 0.45, theory: 0.25, pat: 0.3 }, streams = { read: [], theory: [], pat: [] }, per = {};
    const depth = cfg.depth || "all";
    let skipped = 0;
    PATH.forEach((st) => st.tracks.forEach(([id]) => {
      if (!cfg.tracks.includes(id) || !DATA.tracks[id] || per[id]) return;
      const r = trackItems(id, cfg.ex, cfg.genAt, cfg.marks, depth);
      skipped += r.skipped;
      per[id] = { id, title: DATA.tracks[id].title, total: r.out.length, kept: 0, min: sumMin(r.out), keptMin: 0 };
      r.out.forEach((it) => streams[it.stream].push(it));
    }));
    const study = days.filter((d) => !d.rest && !d.review);
    const avail = study.map((d) => Math.max(0, B - sumMin(d.items)));
    const availTot = avail.reduce((a, x) => a + x, 0);
    const need = {};
    Object.keys(W).forEach((k) => (need[k] = sumMin(streams[k])));
    const alloc = (C) => {
      const cap = { read: 0, theory: 0, pat: 0 };
      let open = Object.keys(W).filter((k) => need[k] > 0), left = C;
      while (open.length) {
        const ws = open.reduce((a, k) => a + W[k], 0), small = open.filter((k) => need[k] <= (left * W[k]) / ws);
        if (!small.length) { open.forEach((k) => (cap[k] = (left * W[k]) / ws)); break; }
        small.forEach((k) => { cap[k] = need[k]; left -= need[k]; });
        open = open.filter((k) => !small.includes(k));
      }
      return cap;
    };
    const prefix = (arr, cap) => { const out = []; let c = 0; for (const it of arr) { if (c + it.min > cap + 0.01) break; c += it.min; out.push(it); } return out; };
    const keep = (arr, cap) => {
      const A = arr.filter((x) => x.tier === "A"), sA = sumMin(A);
      const set = new Set(sA <= cap ? A.concat(prefix(arr.filter((x) => x.tier !== "A"), cap - sA)) : prefix(A, cap));
      return arr.filter((x) => set.has(x));
    };
    const patterns = (arr) => new Set(arr.filter((x) => x.pat).map((x) => x.pat)).size;
    let revisitMin = 0, kept = { read: [], theory: [], pat: [] };
    for (let pass = 0; pass < 3; pass++) {
      const cap = alloc(Math.max(0, availTot - revisitMin));
      Object.keys(W).forEach((k) => (kept[k] = keep(streams[k], cap[k])));
      revisitMin = patterns(kept.theory.concat(kept.pat)) * PL.revisit;
    }
    const kr = kept.read, all = kept.read.concat(kept.theory, kept.pat);
    // spread each stream evenly over the study days, in proportion to each day's free time
    const cum = []; let acc = 0;
    avail.forEach((a) => cum.push((acc += a)));
    const place = (arr) => {
      const tot = sumMin(arr);
      let c = 0, j = 0;
      arr.forEach((it) => {
        const pos = tot ? ((c + it.min / 2) / tot) * acc : 0;
        c += it.min;
        while (j < study.length - 1 && cum[j] < pos) j++;
        study[j].items.push({ ...it });
      });
    };
    place(kept.read); place(kept.theory); place(kept.pat);
    // spaced repetition: revisit each pattern about three days after first practising it
    const seen = new Set(), firstOf = [];
    study.forEach((d) => d.items.forEach((it) => {
      if (!it.pat || seen.has(it.pat)) return;
      seen.add(it.pat); firstOf.push(it);
      const tgt = days.find((x) => x.i >= d.i + 3 && !x.rest && !x.review);
      if (tgt) tgt.items.push({ c: "R:" + it.c.slice(2), k: "revisit", href: it.href, title: `Revisit ${it.pat}`, sub: `Re-solve “${it.title}” from a blank editor`, min: PL.revisit });
    }));
    // final review window: rotate through practised patterns and the tracks read
    const topics = [], keptTracks = [...new Set(kr.map((x) => x.track))];
    for (let i = 0; i < Math.max(firstOf.length, keptTracks.length); i++) {
      if (firstOf[i]) topics.push({ href: firstOf[i].href, title: `Review ${firstOf[i].pat}`, sub: `Re-solve “${firstOf[i].title}” and one more ${firstOf[i].pat} problem` });
      if (keptTracks[i]) topics.push({ href: `#/track/${keptTracks[i]}`, title: `Review ${DATA.tracks[keptTracks[i]].title}`, sub: "Skim your notes and retake two lesson quizzes" });
    }
    if (!topics.length) topics.push({ href: "#/roadmap", title: "Review your weakest topics", sub: "Re-read notes and retake quizzes" });
    let ti = 0;
    revDays.forEach((d) => {
      let free = B - sumMin(d.items), n = 0;
      while (free >= 20 && n < 4) { const tp = topics[ti++ % topics.length]; d.items.push({ ...tp, c: `V:${d.key}:${n}`, k: "review", min: 30 }); free -= 30; n++; }
    });
    const rank = { revisit: 0, review: 1, lesson: 2, problem: 3, mock: 4 };
    days.forEach((d) => d.items.sort((a, b) => rank[a.k] - rank[b.k] + (a.k === "problem" && b.k === "problem" ? (a.pat ? 1 : 0) - (b.pat ? 1 : 0) : 0)));
    all.forEach((it) => { per[it.track].kept++; per[it.track].keptMin += it.min; });
    const trimmed = Object.values(per).filter((p) => p.kept < p.total);
    return { days, B, per, trimmed, fits: !trimmed.length, need: need.read + need.theory + need.pat, room: availTot - revisitMin, kept: sumMin(all), skipped, depth };
  }
  // smallest number of weeks (from cfg.start) or hours a week that fits everything; null if none within the cap
  function planFitSearch(cfg, field) {
    const tryIt = (v) => buildPlan(field === "weeks" ? { ...cfg, end: addDays(cfg.start, v * 7 - 1) } : { ...cfg, hours: v }).fits;
    let lo = 1, hi = field === "weeks" ? 156 : 80;
    if (!tryIt(hi)) return null;
    while (lo < hi) { const mid = (lo + hi) >> 1; if (tryIt(mid)) hi = mid; else lo = mid + 1; }
    return lo;
  }

  function mockDoneIn(kind, ws, we) {
    return ((S().mocks || {}).history || []).some((m) => { const k = dayKey(new Date(m.at)); return m.kind === kind && k >= ws && k <= we; });
  }
  function itemAuto(it) {
    if (it.k === "problem") return !!S().solved[it.c.slice(2)];
    if (it.k === "mock") return mockDoneIn(it.kind, it.ws, it.we);
    return false;
  }
  function itemDone(it, plan) {
    if (it.k === "lesson") return !!S().lessons[it.c.slice(2)];
    return itemAuto(it) || !!((plan && plan.marks) || {})[it.c];
  }
  function planStatus(plan, b) {
    const today = dayKey();
    let all = 0, done = 0, due = 0, dueMin = 0, ahead = 0;
    b.days.forEach((d) => d.items.forEach((it) => {
      all++;
      if (itemDone(it, plan)) { done++; if (d.key > today) ahead++; }
      else if (d.key < today) { due++; dueMin += it.min; }
    }));
    let label = "On track", cls = "ok";
    if (today < plan.start) { label = `Starts ${fmtDay(plan.start)}`; cls = ""; }
    else if (today > plan.end) { label = due ? `Ended with ${due} tasks open` : "Plan complete"; cls = due ? "warn" : "ok"; }
    else if (due) { label = `Behind by ${due} task${due > 1 ? "s" : ""}`; cls = "warn"; }
    else if (ahead) label = "Ahead of schedule";
    return { all, done, due, dueMin, ahead, label, cls, pct: all ? Math.round((100 * done) / all) : 0 };
  }
  function planToggle(code, on) {
    store.set((s) => {
      const p = s.plan;
      if (!p) return;
      p.marks = p.marks || {};
      if (code.startsWith("L:")) { const k = code.slice(2); if (on) { if (!s.lessons[k]) { s.lessons[k] = Date.now(); bump(s); } } else delete s.lessons[k]; }
      else if (on) p.marks[code] = Date.now();
      else delete p.marks[code];
    });
  }
  function planItemHTML(it, plan) {
    const done = itemDone(it, plan), auto = itemAuto(it);
    const why = auto ? (it.k === "mock" ? "Done: you saved a mock of this kind this week" : "Solved in the judge") : "";
    return `<li class="pl-it ${done ? "done" : ""}"><input type="checkbox" data-c="${esc(it.c)}" ${done ? "checked" : ""} ${auto ? "disabled" : ""} aria-label="${esc(`${KIND_LABEL[it.k]}: ${it.title}`)}"${why ? ` title="${esc(why)}"` : ""}>
      <span class="pl-k k-${it.k}">${KIND_LABEL[it.k]}</span><span class="pl-t"><a href="${esc(it.href)}">${esc(it.title)}</a><span class="muted">${esc(it.sub || "")}</span></span><span class="mins">${it.min} min</span></li>`;
  }
  function wirePlanChecks(root, after) {
    root.addEventListener("change", (e) => {
      const cb = e.target.closest("input[data-c]");
      if (!cb) return;
      planToggle(cb.dataset.c, cb.checked);
      $$(`input[data-c="${CSS.escape(cb.dataset.c)}"]`).forEach((x) => { x.checked = cb.checked; const li = x.closest(".pl-it"); if (li) li.classList.toggle("done", cb.checked); });
      if (after) after();
    });
  }
  function planDayHTML(d, plan, today) {
    const isT = d.key === today;
    return `<div class="pl-day ${isT ? "today" : ""} ${d.key < today ? "past" : ""}" ${isT ? 'id="plTodayRow"' : ""}>
      <h3 class="pl-dh"><span>${fmtDay(d.key)}</span>${isT ? `<span class="pl-badge ok">Today</span>` : ""}${d.review && !d.rest ? `<span class="pill">Review</span>` : ""}${d.items.length ? `<span class="mins">${fmtMin(sumMin(d.items))}</span>` : ""}</h3>
      ${d.items.length ? `<ul class="pl-items">${d.items.map((it) => planItemHTML(it, plan)).join("")}</ul>` : `<p class="muted pl-rest">${d.rest ? "Rest day, or catch up on anything left from this week." : "Nothing scheduled."}</p>`}</div>`;
  }
  function planICS(b) {
    const e = (s) => String(s).replace(/\\/g, "\\\\").replace(/;/g, "\\;").replace(/,/g, "\\,").replace(/\r?\n/g, "\\n");
    const fold = (line) => { const cps = Array.from(line), out = []; for (let i = 0; i < cps.length; i += 60) out.push(cps.slice(i, i + 60).join("")); return out.join("\r\n "); };
    const stamp = new Date().toISOString().replace(/[-:]/g, "").replace(/\.\d+/, "");
    const L = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Sky Castle//Study plan//EN", "CALSCALE:GREGORIAN", "X-WR-CALNAME:Sky Castle study plan"];
    b.days.forEach((d) => {
      if (!d.items.length) return;
      const k = d.key.replace(/-/g, "");
      L.push("BEGIN:VEVENT", `UID:sky-castle-plan-${k}@sky-castle`, `DTSTAMP:${stamp}`, `DTSTART;VALUE=DATE:${k}`, `DTEND;VALUE=DATE:${addDays(d.key, 1).replace(/-/g, "")}`,
        `SUMMARY:${e(`Study: ${d.items.length} task${d.items.length > 1 ? "s" : ""} (${fmtMin(sumMin(d.items))})`)}`,
        `DESCRIPTION:${e(d.items.map((it) => `- ${KIND_LABEL[it.k]}: ${it.title} (${it.min} min)`).join("\n"))}`, "TRANSP:TRANSPARENT", "END:VEVENT");
    });
    L.push("END:VCALENDAR");
    return L.map(fold).join("\r\n") + "\r\n";
  }

  function viewPlan(sub, msg) {
    renderSidebar("#plan");
    const plan = S().plan;
    if (!plan || sub === "edit") return viewPlanForm(plan);
    const b = buildPlan(plan), today = dayKey();
    const weeks = Math.ceil(b.days.length / 7);
    const tday = b.days.find((d) => d.key === today);
    const curW = tday ? tday.w : today < plan.start ? 1 : weeks;
    let wk = "";
    for (let w = 1; w <= weeks; w++) {
      const ds = b.days.filter((d) => d.w === w), items = ds.flatMap((d) => d.items);
      wk += `<details class="module pl-week" ${w === curW ? "open" : ""}><summary><span class="num">${w}</span><span class="t"><b>Week ${w} · ${fmtShort(ds[0].key)} – ${fmtShort(ds[ds.length - 1].key)}</b>
        <span>${fmtH(sumMin(items))} planned${ds.some((d) => d.review) ? " · review and mocks" : ""} · <span data-wk="${w}"></span></span></span><span class="chev" aria-hidden="true">▸</span></summary>
        <div class="module-body">${ds.map((d) => planDayHTML(d, plan, today)).join("")}</div></details>`;
    }
    const nT = plan.tracks.filter((id) => DATA.tracks[id]).length;
    let trim;
    if (b.fits) trim = `<p class="pl-fit">Everything you selected${b.depth === "essentials" ? " (interview essentials)" : ""} fits: about ${fmtH(b.need)} of material in about ${fmtH(b.room)} of study time${b.skipped ? `, leaving out ${b.skipped} items you had already finished` : ""}.</p>`;
    else {
      const wN = planFitSearch(plan, "weeks"), hN = planFitSearch(plan, "hours");
      // A short plan never holds every track, so this is a quiet, collapsed note at the end of the
      // page, not a warning: the plan already contains the most interview-relevant work.
      const later = b.trimmed.map((p) => `<li><b>${esc(p.title)}</b> <span class="muted">${p.total - p.kept} more task${p.total - p.kept === 1 ? "" : "s"} for later (about ${fmtH(p.min - p.keptMin)})</span></li>`).join("");
      trim = `<details class="card pl-later"><summary>This plan covers the interview essentials that fit your time. More material is waiting for later: show what</summary>
        <p>Your tracks hold about <b>${fmtH(b.need)}</b> of material and this plan has about <b>${fmtH(b.room)}</b> of study time, so it starts with what interviews test most: coding patterns, DSA, the behavioural chapters and each track's interview lessons. Everything else stays on the site for after the plan, or for a longer plan.</p>
        <ul class="pl-trim-list">${later}</ul>
        <p>To include all of it: ${wN ? `about <b>${wN} weeks</b> at ${plan.hours} h a week` : "more than three years at this pace"}${hN ? `, or about <b>${hN} h a week</b> until ${fmtDay(plan.end)}` : ""}.</p>
        <div class="dlg-row">${wN && wN * 7 > b.days.length ? `<button class="btn sm" type="button" id="plExtend">Move end date to ${fmtDay(addDays(plan.start, wN * 7 - 1))}</button>` : ""}<a class="btn sm" href="#/plan/edit">Change hours or tracks</a></div></details>`;
    }
    const todayList = tday ? (tday.items.length ? `<ul class="pl-items">${tday.items.map((it) => planItemHTML(it, plan)).join("")}</ul>` : `<p class="muted pl-rest">${tday.rest ? "Rest day. Catch up on anything left from this week, or take the day off." : "Nothing scheduled today."}</p>`)
      : `<p class="muted pl-rest">${today < plan.start ? `Your plan starts on ${fmtDay(plan.start)}.` : "This plan has ended."}</p>`;
    setPage(`<div class="page narrow" id="plRoot"><div class="crumbs"><a href="#/">Home</a></div>
      <div class="pl-head"><div><h1 class="page-title">Study plan</h1><p class="muted" style="margin:0">${fmtDay(plan.start)} to ${fmtDay(plan.end)} · ${weeks} weeks · ${plan.hours} h a week · ${DEPTH_NAME[b.depth]} · ${nT} track${nT === 1 ? "" : "s"}${plan.replans ? ` · re-planned ${plan.replans}×` : ""}</p></div>
        <div class="pl-actions"><a class="btn sm" href="#/plan/edit">Edit settings</a><button class="btn sm" type="button" id="plIcs">Export to calendar (.ics)</button><button class="btn sm danger" type="button" id="plDel">Delete plan</button></div></div>
      <p id="plMsg" class="pl-msg" role="status" tabindex="-1">${esc(msg || "")}</p>
      <section class="card pl-status" id="plStatus" aria-label="Plan status"></section>
      <section class="card pl-today" aria-labelledby="plTodayH"><h2 id="plTodayH">Today${tday ? ` · ${fmtDay(today)}` : ""}</h2>${todayList}</section>
      <div class="section-h"><h2>Week by week</h2>${tday ? `<button class="btn sm" type="button" id="plJump">Jump to today</button>` : ""}</div>
      ${wk}
      ${trim}
      <p class="muted pl-note">How times are estimated: a lesson takes its word count at 180 words a minute plus 30% for demos and the quiz; an Easy problem 20 minutes, Medium 35, Hard 50. ${plan.hours} h a week is spread over six study days; every seventh day is a rest or catch-up day. DSA theory (about 25% of the time) and pattern practice (30%, in NeetCode roadmap order with a lesson before each pattern's problems) run alongside the other tracks, each pattern comes back for a revisit about three days after you first practise it, and the last ${Math.round(PL.review * 100)}% of the plan is review and mock interviews.</p></div>`);
    const drawStatus = () => {
      const st = planStatus(plan, b), el = $("#plStatus");
      if (!el) return;
      const canRe = today >= plan.start && today <= plan.end && today !== plan.start;
      el.innerHTML = `<div class="pl-st-row"><div class="streak-row"><div><b>${st.done}/${st.all}</b><span>tasks done</span></div><div><b>${st.pct}%</b><span>complete</span></div><div><b>${Math.max(0, daysBetween(today, plan.end) + 1)}</b><span>days left</span></div></div><span class="pl-badge ${st.cls}">${esc(st.label)}</span></div>
        <div class="bar"><i style="width:${st.pct}%"></i></div>
        ${st.due ? `<p>${st.due} task${st.due > 1 ? "s" : ""} from earlier days ${st.due > 1 ? "are" : "is"} unfinished (about ${fmtH(st.dueMin)}). Re-plan to spread the unfinished work over the days left before ${fmtDay(plan.end)}, or use a rest day to catch up.</p>` : ""}
        ${today > plan.end ? `<p>The end date has passed, so a re-plan cannot keep it. Choose a new date in <a href="#/plan/edit">Edit settings</a>.</p>` : ""}
        <div class="dlg-row"><button class="btn sm ${st.due ? "primary" : ""}" type="button" id="plRe" ${canRe ? "" : "disabled"} title="${canRe ? "Reschedule everything unfinished from today, keeping the end date" : "Available once the plan has started and before it ends"}">Re-plan from today</button><a class="btn sm" href="#/mock">Mock interviews</a></div>`;
      $("#plRe").onclick = () => {
        store.set((s) => { s.plan.start = today; s.plan.genAt = Date.now(); s.plan.replans = (s.plan.replans || 0) + 1; });
        const nb = buildPlan(S().plan);
        viewPlan(null, nb.fits ? `Re-planned: unfinished work now runs from today to ${fmtDay(plan.end)}.` : `Re-planned from today. Some unfinished work no longer fits before ${fmtDay(plan.end)} and moved to "for later" at the end of the page; move the end date to keep it.`);
        const m = $("#plMsg"); if (m) m.focus();
      };
      for (let w = 1; w <= weeks; w++) {
        const its = b.days.filter((d) => d.w === w).flatMap((d) => d.items), sp = $(`[data-wk="${w}"]`);
        if (sp) sp.textContent = `${its.filter((it) => itemDone(it, plan)).length}/${its.length} done`;
      }
    };
    drawStatus();
    wirePlanChecks($("#plRoot"), drawStatus);
    $("#plDel").onclick = () => { if (confirm("Delete this study plan? Your lesson and problem progress is kept.")) { store.set((s) => (s.plan = null)); viewPlan(); } };
    $("#plIcs").onclick = () => {
      const a = document.createElement("a");
      a.href = URL.createObjectURL(new Blob([planICS(b)], { type: "text/calendar" }));
      a.download = `sky-castle-plan-${plan.start}.ics`;
      a.click();
      setTimeout(() => URL.revokeObjectURL(a.href), 1000);
    };
    const ex = $("#plExtend");
    if (ex) ex.onclick = () => { const wN = planFitSearch(plan, "weeks"); store.set((s) => (s.plan.end = addDays(s.plan.start, wN * 7 - 1))); viewPlan(null, `End date moved to ${fmtDay(S().plan.end)}.`); };
    const jb = $("#plJump");
    if (jb) jb.onclick = () => { const r = $("#plTodayRow"); if (r) { r.closest("details").open = true; r.scrollIntoView({ block: "center" }); const c = $("input, a", r); if (c) c.focus({ preventScroll: true }); } };
  }

  function viewPlanForm(plan) {
    const today = dayKey();
    const start = plan && plan.start > today ? plan.start : today;
    const nDays = plan ? daysBetween(plan.start, plan.end) + 1 : 84;
    const wks = Math.round(nDays / 7), std = [8, 12, 16, 24].includes(wks) && nDays % 7 === 0;
    const mode = !plan || std ? "weeks" : "date";
    const sel = new Set(plan ? plan.tracks : coreTracks()), ex = plan ? plan.ex !== false : true, depth = plan ? plan.depth || "all" : "essentials";
    const endDefault = plan && plan.end > addDays(start, 6) ? plan.end : addDays(start, 83);
    const stages = PATH.map((st, i) => {
      const ids = st.tracks.filter(([id]) => DATA.tracks[id]);
      if (!ids.length) return "";
      return `<fieldset class="pl-stage"><legend><label class="check"><input type="checkbox" data-stage="${i}"> <b>Stage ${i + 1}: ${esc(st.title)}</b></label></legend>
        <div class="pl-tracks">${ids.map(([id]) => `<label class="check"><input type="checkbox" name="plTrack" value="${id}" data-st="${i}" ${sel.has(id) ? "checked" : ""}> <span>${esc(DATA.tracks[id].icon || "")} ${esc(DATA.tracks[id].title)} <span class="muted" data-est="${id}"></span></span></label>`).join("")}</div></fieldset>`;
    }).join("");
    const seg = (name, vals, cur, fmtv) => `<div class="seg">${vals.map((v) => `<label><input type="radio" name="${name}" value="${v}" ${v === cur ? "checked" : ""}><span>${fmtv(v)}</span></label>`).join("")}</div>`;
    setPage(`<div class="page narrow"><div class="crumbs"><a href="#/">Home</a>${plan ? ` / <a href="#/plan">Study plan</a>` : ""}</div>
      <h1 class="page-title">${plan ? "Edit your study plan" : "Make a study plan"}</h1>
      <p class="muted">Tell the planner when you start, how long you have and how many hours a week you can give. It lays the roadmap out day by day: one reading item and some coding practice most days, revisits a few days after each new pattern, weekly mock interviews from week 3 and a review stretch at the end.${plan ? " Saving rebuilds the schedule from the start date; work you have finished is kept and left out." : ""}</p>
      <form id="plForm" class="pl-form" novalidate>
        <section class="card"><h2>When</h2>
          <label class="fld"><span>Start date</span><input type="date" id="plStart" value="${start}" required></label>
          <fieldset class="fld-set"><legend>How long</legend>
            <label class="check"><input type="radio" name="plMode" value="weeks" ${mode === "weeks" ? "checked" : ""}> A fixed length</label>
            ${seg("plWeeks", [8, 12, 16, 24], std ? wks : 12, (v) => `${v} weeks`)}
            <label class="check"><input type="radio" name="plMode" value="date" ${mode === "date" ? "checked" : ""}> Until my interview date</label>
            <label class="fld fld-inline"><span>Interview date</span><input type="date" id="plEnd" value="${endDefault}"></label>
          </fieldset>
          <fieldset class="fld-set"><legend>Hours a week</legend>${seg("plHours", [5, 10, 15, 20, 30], plan && [5, 10, 15, 20, 30].includes(plan.hours) ? plan.hours : 10, (v) => `${v} h`)}</fieldset>
        </section>
        <section class="card"><h2>What to study</h2>
          <fieldset class="fld-set"><legend>Depth</legend>${seg("plDepth", ["essentials", "all"], depth, (v) => DEPTH_NAME[v])}
            <p class="muted" style="margin:0;font-size:13.5px">Interview essentials: pattern tracks' lessons with their Easy and Medium problems; Python and DSA Foundations lessons with one problem per module; for every other track its interview and essentials lessons, the first lesson of each module and about a third of its problems. Everything: every lesson and problem.</p></fieldset>
          <p class="muted" style="margin:0">Tracks are scheduled in roadmap order (ordered by Singapore job demand). The core preset is Stages 1, 2, 3 and 6. Hours shown are what is left in each track at the chosen depth.</p>
          <div class="chips" style="margin:6px 0 0"><button type="button" class="chip" data-preset="core">Core stages</button><button type="button" class="chip" data-preset="all">All stages</button><button type="button" class="chip" data-preset="none">Clear</button></div>
          ${stages}
          <label class="check"><input type="checkbox" id="plEx" ${ex ? "checked" : ""}> Include each track's practice exercises, not only its lessons (coding-interview tracks always include their problems)</label>
        </section>
        <section class="card pl-preview" aria-labelledby="plPrevH"><h2 id="plPrevH">Preview</h2><div id="plPreview" aria-live="polite"></div></section>
        <p id="plErr" class="acct-bad" role="alert"></p>
        <div class="dlg-row"><button class="btn primary" type="submit">${plan ? "Save and rebuild plan" : "Generate my plan"}</button>${plan ? `<a class="btn" href="#/plan">Cancel</a>` : ""}</div>
      </form></div>`);
    const form = $("#plForm");
    const syncStages = () => $$("[data-stage]", form).forEach((sc) => {
      const boxes = $$(`[data-st="${sc.dataset.stage}"]`, form), on = boxes.filter((x) => x.checked).length;
      sc.checked = on === boxes.length; sc.indeterminate = on > 0 && on < boxes.length;
    });
    const read = () => {
      const st = $("#plStart").value, mode = (form.plMode.value || "weeks");
      const end = mode === "weeks" ? (validDay(st) ? addDays(st, +form.plWeeks.value * 7 - 1) : "") : $("#plEnd").value;
      return { start: st, end, hours: +form.plHours.value || 10, depth: form.plDepth.value === "all" ? "all" : "essentials", tracks: $$("[name=plTrack]:checked", form).map((x) => x.value), ex: $("#plEx").checked, genAt: Date.now(), marks: (plan && plan.marks) || {} };
    };
    const check = (c) => {
      if (!validDay(c.start)) return "Choose a start date.";
      if (!validDay(c.end)) return "Choose your interview date.";
      if (daysBetween(c.start, c.end) < 6) return "The interview date must be at least a week after the start date.";
      if (daysBetween(c.start, c.end) > 731) return "Keep the plan under two years.";
      if (!c.tracks.length) return "Tick at least one track.";
      return "";
    };
    const draw = () => {
      syncStages();
      const c = read(), bad = check(c);
      $("#plEnd").disabled = form.plMode.value !== "date";
      $$("[name=plWeeks]", form).forEach((x) => (x.disabled = form.plMode.value !== "weeks"));
      $$("[data-est]", form).forEach((el) => { const m = sumMin(trackItems(el.dataset.est, c.ex, Date.now(), c.marks, c.depth).out); el.textContent = m ? `· ~${fmtH(m)}` : "· done"; });
      const pv = $("#plPreview");
      if (bad) { pv.innerHTML = `<p class="muted" style="margin:0">${esc(bad)}</p>`; return; }
      const b = buildPlan(c), n = Math.ceil(b.days.length / 7);
      const pct = b.need ? Math.round((100 * b.kept) / b.need) : 100;
      pv.innerHTML = `<p style="margin:0 0 6px">${fmtDay(c.start)} to ${fmtDay(c.end)} · ${n} weeks · ${DEPTH_NAME[c.depth]} · about <b>${fmtH(b.room)}</b> of study time for <b>${fmtH(b.need)}</b> of material.</p>
        ${b.fits ? `<p class="pl-fit" style="margin:0">Everything you selected fits.</p>` : `<p class="pl-fit" style="margin:0">Covers about ${pct}% of these tracks, starting with what interviews test most. The rest stays available for later; more weeks or hours include more.</p>`}`;
    };
    const redraw = debounce(draw, 120);
    form.addEventListener("input", redraw);
    form.addEventListener("change", (e) => {
      if (e.target.dataset.stage !== undefined) $$(`[data-st="${e.target.dataset.stage}"]`, form).forEach((x) => (x.checked = e.target.checked));
      if (e.target.name === "plWeeks") form.plMode.value = "weeks";
      redraw();
    });
    $("#plEnd").addEventListener("focus", () => (form.plMode.value = "date"));
    $$("[data-preset]", form).forEach((bt) => (bt.onclick = () => {
      const want = bt.dataset.preset === "core" ? new Set(coreTracks()) : bt.dataset.preset === "all" ? null : new Set();
      $$("[name=plTrack]", form).forEach((x) => (x.checked = want ? want.has(x.value) : true));
      draw();
    }));
    form.onsubmit = (e) => {
      e.preventDefault();
      const c = read(), bad = check(c);
      $("#plErr").textContent = bad;
      if (bad) return;
      store.set((s) => (s.plan = { ...c, first: (plan && plan.first) || c.start, replans: 0 }));
      if (location.hash === "#/plan") viewPlan(); else location.hash = "#/plan";
    };
    draw();
  }

  function homePlanHTML() {
    const plan = S().plan;
    if (!plan) return `<div class="card pl-home"><div><h2>Plan your prep</h2><p>Pick your interview date and weekly hours. You get a day-by-day schedule that follows the roadmap, with coding practice, spaced revisits and mock interviews built in.</p></div>
      <div class="pl-home-cta"><a class="btn primary" href="#/plan">Make a study plan</a><a class="btn" href="#/mock">Try a mock interview</a></div></div>`;
    const b = buildPlan(plan), st = planStatus(plan, b), today = dayKey(), d = b.days.find((x) => x.key === today);
    const body = !d ? `<p class="muted">${today < plan.start ? `Your plan starts on ${fmtDay(plan.start)}.` : "Your plan has ended. Set a new date to keep going."}</p>`
      : d.items.length ? `<ul class="pl-items">${d.items.slice(0, 6).map((it) => planItemHTML(it, plan)).join("")}</ul>${d.items.length > 6 ? `<p class="muted" style="margin:0;font-size:13px">and ${d.items.length - 6} more on the plan page</p>` : ""}`
      : `<p class="muted">Rest day: catch up on anything left from this week, or take the day off.</p>`;
    return `<section class="card pl-home today" id="homePlan" aria-labelledby="homePlanH"><div class="pl-home-h"><h2 id="homePlanH">Today's plan</h2><span class="pl-badge ${st.cls}" id="homePlanSt">${esc(st.label)}</span></div>${body}
      <div class="pl-home-cta"><a class="btn sm" href="#/plan">Open the full plan</a><a class="btn sm" href="#/mock">Mock interviews</a></div></section>`;
  }

  // ---------------------------------------------------------------- mock interviews (#/mock)
  // State: s.mocks = { active: {...} | null, history: [{ kind, at, end, scores, notes, ... }] }
  const MOCK_MIN = 45;
  const SCALE = ["", "Missed", "Partly", "Solid", "Strong"];
  const SD_STEPS = [["req", "Requirements", "Functional and non-functional requirements, users and scope", 5], ["est", "Estimates", "Traffic, storage and bandwidth, roughly", 5],
    ["api", "API", "The main calls, with their inputs and outputs", 5], ["data", "Data model", "Entities, keys, and which store holds them and why", 5],
    ["hld", "High-level design", "Boxes and arrows for the main read and write flows", 10], ["deep", "Deep dive", "One or two components in depth", 10],
    ["trade", "Bottlenecks and trade-offs", "Single points of failure, hot spots, and what you would change at ten times the load", 5]];
  const RUBRIC = {
    coding: [["ps", "Problem solving", "Clarified the problem, found a working approach, then improved it"], ["cq", "Code quality", "Correct, readable code with clear names and structure"],
      ["comm", "Communication", "Thought aloud, explained trade-offs and complexity, used hints well"], ["test", "Testing", "Traced examples and edge cases, found and fixed bugs"]],
    design: SD_STEPS.map(([k, t, d]) => [k, t, d]),
  };
  const SD_PROMPTS = [
    ["Design a rate limiter that protects a public API used by millions of clients.", "rate-limiter"],
    ["Design a consistent-hashing layer that spreads keys over a cache cluster that grows and shrinks.", "consistent-hashing"],
    ["Design a distributed key-value store where each request can choose between speed and consistency.", "key-value-store"],
    ["Design a service that hands out unique, roughly time-ordered 64-bit IDs from several data centres.", "unique-id"],
    ["Design a link shortener that creates 100 million short links a day and redirects quickly.", "url-shortener"],
    ["Design a polite web crawler that fetches a billion pages a month.", "web-crawler"],
    ["Design a notification service that sends push, SMS and email reliably and without duplicates.", "notification-system"],
    ["Design the home feed of a social app with hundreds of millions of users.", "news-feed"],
    ["Design a chat service with one-to-one and group conversations and online status.", "chat-system"],
    ["Design the autocomplete suggestions under a search box on a busy site.", "search-autocomplete"],
    ["Design a video platform: uploads, transcoding and smooth playback worldwide.", "video-platform"],
    ["Design a file storage service that keeps files in sync across a user's devices.", "file-storage-sync"],
    ["Design ride-hailing dispatch that matches riders with nearby drivers in real time.", "more-designs", "ride-hailing"],
    ["Design a payment system that never charges a customer twice.", "more-designs", "payment-system"],
    ["Design a concert ticket-booking system that never sells the same seat twice.", "more-designs", "ticket-booking"],
    ["Design a metrics and monitoring system with dashboards and alerts.", "more-designs", "metrics-and-job-scheduler"],
  ];
  const BQ = [
    ["Conflict", "Tell me about a time you disagreed with a teammate about a technical decision. How was it settled?"],
    ["Conflict", "Describe working with someone whose way of working was very different from yours."],
    ["Failure", "Tell me about a project that did not go to plan. What did you learn from it?"],
    ["Failure", "Describe a mistake you made that affected other people, and what you did next."],
    ["Ownership", "Tell me about a time you picked up work outside your role because it needed doing."],
    ["Ownership", "Describe a problem you noticed and fixed without anyone asking you to."],
    ["Influence", "Tell me about a time you persuaded people to try your idea without having authority over them."],
    ["Teamwork", "Describe a time you helped a teammate get unstuck or learn something."],
    ["Ambiguity", "Tell me about a time the requirements were unclear. How did you move forward?"],
    ["Ambiguity", "Describe a decision you had to make with incomplete information."],
    ["Prioritisation", "Tell me about a time you had more work than time. How did you decide what to drop?"],
    ["Prioritisation", "Describe a tight deadline you met, or missed, and what you did about it."],
    ["Customer focus", "Tell me about a time you went out of your way for a user or customer."],
    ["Learning", "Tell me about a time you had to learn a new technology or domain quickly."],
    ["Technical depth", "What is the hardest technical problem you have solved? Walk me through it."],
    ["Feedback", "Tell me about critical feedback you received and what you changed because of it."],
    ["Motivation", "Why do you want this role, and why at this company?"],
    ["Impact", "Tell me about the piece of work you are proudest of. What difference did it make?"],
  ];
  const STAR = [["Situation", "Set the scene in a sentence or two: where, when, who."], ["Task", "What were you responsible for, and what was at stake?"],
    ["Action", "What did you do, step by step? Say “I”, not “we”."], ["Result", "What happened? Give a number if you can, then what you learned."]];
  const AREA_HELP = { coding: { ps: "interview-prep/optimisation-techniques", cq: "interview-prep/good-code-and-recovery", comm: "interview-prep/seven-step-method", test: "interview-prep/seven-step-method" },
    design: { req: "system-design/framework-four-steps", est: "system-design/estimation-worked", api: "system-design/bb-apis-observability", data: "system-design/bb-databases-replication-partitioning", hld: "system-design/framework-four-steps", deep: "system-design/framework-dos-donts", trade: "system-design/bb-cap-queues-idempotency" },
    behavioural: "behavioural/star-in-depth" };
  const lessonLink = (path) => { if (!path) return ""; const [tid, lid] = path.split("/"), t = DATA.tracks[tid]; const l = t && flatLessons(t).find((x) => x.id === lid); return l ? `<a href="#/lesson/${tid}/${lid}">${esc(l.title)}</a>` : ""; };
  const clock = (ms) => { const t = Math.max(0, Math.ceil(ms / 1000)); return `${Math.floor(t / 60)}:${String(t % 60).padStart(2, "0")}`; };
  const mocksOf = () => S().mocks || { active: null, history: [] };
  const avgScore = (m) => { const v = Object.values(m.scores || {}); return v.length ? v.reduce((a, x) => a + x, 0) / v.length : 0; };
  const shuffle = (a) => { a = a.slice(); for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; } return a; };

  function pickCodingMock() {
    const s = S(), codable = (x) => x && (!x.kind || x.kind === "function" || x.kind === "class" || x.kind === "js");
    const studied = (id) => { const t = DATA.tracks[id]; return !!t && t.modules.some((m) => (m.lessons || []).some((l) => s.lessons[`${id}/${l.id}`]) || (m.problems || []).some((p) => s.solved[p] || s.tried[p])); };
    const collect = (ids) => ids.flatMap((id) => { const t = DATA.tracks[id]; return t ? t.modules.flatMap((m) => m.problems || []).filter((p) => codable(t.problemIndex[p])).map((p) => ({ pid: p, d: t.problemIndex[p].difficulty })) : []; });
    let note = "", pool = collect(dsaTracks().filter(studied));
    if (!pool.length) pool = collect(Object.keys(DATA.tracks).filter(studied));
    if (!pool.length) { pool = collect(dsaTracks().slice(0, 2)); note = "You have not started a coding track yet, so these come from the first coding tracks on the roadmap."; }
    const rnd = (a) => a[Math.floor(Math.random() * a.length)];
    const pick = (tiers, excl) => {
      for (const fresh of [true, false]) for (const ds of tiers) {
        const c = pool.filter((x) => ds.includes(x.d) && x.pid !== excl && (!fresh || !s.solved[x.pid]));
        if (c.length) return rnd(c).pid;
      }
      return null;
    };
    const warm = pick([["Easy"], ["Medium"]]), main = pick([["Medium", "Hard"]], warm) || pick([["Easy"]], warm);
    return { probs: [warm, main].filter(Boolean), note };
  }
  function mockStart(kind) {
    const a = { kind, at: Date.now(), phase: "run" };
    if (kind === "coding") { const r = pickCodingMock(); a.probs = r.probs; a.note = r.note; a.dur = MOCK_MIN; }
    else if (kind === "design") { a.p = Math.floor(Math.random() * SD_PROMPTS.length); a.dur = MOCK_MIN; a.checks = {}; }
    else { a.qs = shuffle(BQ.map((q, i) => i)).reduce((acc, i) => (acc.length < 5 && !acc.some((j) => BQ[j][0] === BQ[i][0]) ? acc.concat(i) : acc), []); a.qi = 0; a.qAt = null; }
    store.set((s) => { s.mocks = s.mocks || { history: [] }; s.mocks.active = a; });
    viewMock();
    mockTick();
  }
  function mockSet(fn) { store.set((s) => { if (s.mocks && s.mocks.active) fn(s.mocks.active, s); }); }

  let announceEl = null;
  const said = {};
  function announce(msg) {
    if (!announceEl) { announceEl = h(`<div class="sr-only" aria-live="assertive"></div>`); document.body.appendChild(announceEl); }
    announceEl.textContent = msg;
  }
  function mockTick() {
    const a = mocksOf().active, timed = a && a.phase === "run" && a.dur;
    let pill = $("#mockPill");
    if (!timed) { if (pill) pill.remove(); }
    else {
      if (!pill) { pill = h(`<a id="mockPill" class="mock-pill" href="#/mock"></a>`); $(".top-actions").prepend(pill); }
      const ms = a.at + a.dur * 60000 - Date.now();
      pill.textContent = ms > 0 ? `⏱ ${clock(ms)}` : "⏱ Time's up";
      pill.classList.toggle("soon", ms > 0 && ms <= 300000);
      pill.classList.toggle("late", ms <= 0);
      const lbl = `${MOCK_NAME[a.kind]}: ${ms > 0 ? clock(ms) + " left" : "time is up"}. Open the mock page.`;
      if (pill.title !== lbl) { pill.title = lbl; pill.setAttribute("aria-label", lbl); }
      if (ms <= 300000 && ms > 0 && !said[a.at + "5"]) { said[a.at + "5"] = 1; announce("Five minutes left in your mock interview."); }
      if (ms <= 0 && !said[a.at + "0"]) { said[a.at + "0"] = 1; announce("Time is up. Finish and score your mock interview."); }
    }
    $$("[data-until]").forEach((el) => {
      const ms = +el.dataset.until - Date.now();
      el.textContent = clock(ms);
      el.classList.toggle("late", ms <= 0);
      el.classList.toggle("soon", ms > 0 && ms <= +(el.dataset.soon || 300000));
      if (ms <= 0 && el.dataset.over && !el.dataset.done) { el.dataset.done = 1; const o = document.getElementById(el.dataset.over); if (o) o.hidden = false; }
    });
  }
  setInterval(mockTick, 1000);

  function viewMock(sub) {
    renderSidebar("#mock");
    if (sub === "history") return viewMockHistory();
    const a = mocksOf().active;
    if (a) return a.phase === "review" ? viewMockReview(a) : viewMockRun(a);
    const hist = mocksOf().history || [];
    const card = (kind, ico, title, desc, meta) => `<article class="card mk-card"><div class="card-top"><div class="card-ico" aria-hidden="true">${ico}</div><h2>${title}</h2></div><p>${desc}</p>
      <div class="card-meta"><span>${meta}</span>${hist.filter((m) => m.kind === kind).length ? `<span>${hist.filter((m) => m.kind === kind).length} done</span>` : ""}</div>
      <button class="btn primary" type="button" data-start="${kind}">Start ${title.toLowerCase()}</button></article>`;
    setPage(`<div class="page narrow"><div class="crumbs"><a href="#/">Home</a></div><h1 class="page-title">Mock interviews</h1>
      <p class="muted">Practise under a clock, then score yourself honestly against the rubric an interviewer would use. Scores are saved, so you can see which areas need work.${S().plan ? ` Your <a href="#/plan">study plan</a> schedules one most weeks.` : ""}</p>
      <div class="mk-grid">
        ${card("coding", "⌨️", "Coding mock", "Two problems from the tracks you have studied, unsolved ones first: a warm-up, then a harder one. The clock follows you onto the problem pages.", "45 minutes")}
        ${card("design", "🏗️", "System design mock", "A random design prompt from the system-design case studies, with a step checklist to pace yourself and links to the lessons afterwards.", "45 minutes")}
        ${card("behavioural", "🗣️", "Behavioural mock", "Five questions on different themes. Answer each out loud in STAR form within two minutes, then rate each answer.", "About 15 minutes")}
      </div>
      <div class="section-h"><h2>Recent mocks</h2>${hist.length ? `<a href="#/mock/history">Full history and weak spots</a>` : ""}</div>
      ${hist.length ? `<div class="table-wrap">${mockTable(hist.slice(-5).reverse(), true)}</div>` : `<p class="muted">No mocks yet. Your scores will appear here.</p>`}</div>`);
    $$("[data-start]").forEach((b) => (b.onclick = () => mockStart(b.dataset.start)));
  }
  function mockHead(a, title) {
    return `<div class="crumbs"><a href="#/">Home</a> / <a href="#/mock">Mock interviews</a></div><h1 class="page-title">${title}</h1>`;
  }
  function viewMockRun(a) {
    const until = a.dur ? a.at + a.dur * 60000 : 0, late = until && Date.now() >= until;
    const clockCard = a.dur ? `<div class="card mk-clock-card"><div class="mk-clock" role="timer" aria-label="Time left" data-until="${until}" data-over="mkOver">${clock(until - Date.now())}</div>
      <p class="muted" style="margin:0">The clock keeps running if you open a problem or reload the page; it also shows in the top bar.</p><p id="mkOver" class="pl-warn" ${late ? "" : "hidden"} style="margin:0">Time is up. Stop where you are and score yourself.</p></div>` : "";
    const actions = `<div class="dlg-row"><button class="btn primary" type="button" id="mkFinish">Finish and score yourself</button><button class="btn danger" type="button" id="mkAbandon">Abandon mock</button></div>`;
    if (a.kind === "coding") {
      const s = S();
      setPage(`<div class="page narrow">${mockHead(a, "Coding mock")}${clockCard}
        ${a.note ? `<p class="muted">${esc(a.note)}</p>` : ""}
        <ol class="mk-probs">${(a.probs || []).map((pid, i) => { const x = probMeta(pid); return x ? `<li class="card"><span class="pill">${i ? "Main problem · about 30 min" : "Warm-up · about 15 min"}</span>
          <a class="mk-pt" href="#/problem/${esc(pid)}">${esc(x.title)}</a><span><span class="diff ${esc(x.difficulty)}">${esc(x.difficulty)}</span>${s.solved[pid] && s.solved[pid] >= a.at ? ` <span class="pill" style="color:var(--ok)">✓ Solved during this mock</span>` : ""}</span></li>` : ""; }).join("")}</ol>
        <section class="card"><h2>How to run it</h2><ul class="mk-list"><li>Spend the first two or three minutes restating the problem and asking about inputs, sizes and edge cases.</li>
          <li>Say the brute force first, then improve it, and state the time and space complexity before you code.</li><li>Talk while you type, as if an interviewer is listening. Recording yourself helps.</li>
          <li>Trace an example and one edge case by hand before you press Submit. Leave the Guide tab closed.</li></ul></section>${actions}</div>`);
    } else if (a.kind === "design") {
      const [q] = SD_PROMPTS[a.p] || SD_PROMPTS[0];
      setPage(`<div class="page narrow">${mockHead(a, "System design mock")}${clockCard}
        <section class="card mk-prompt"><span class="tcard-group">Your prompt</span><h2>${esc(q)}</h2><p class="muted" style="margin:0">Use paper or a whiteboard tool and talk out loud. Tick each step as you cover it; the minutes are a guide.</p></section>
        <section class="card"><h2>Checklist</h2><ul class="mk-check">${SD_STEPS.map(([k, t, d, m]) => `<li><label class="check"><input type="checkbox" data-step="${k}" ${a.checks && a.checks[k] ? "checked" : ""}> <span><b>${t}</b> <span class="muted">· ~${m} min · ${d}</span></span></label></li>`).join("")}</ul></section>${actions}</div>`);
      $$("[data-step]").forEach((cb) => (cb.onchange = () => mockSet((x) => { x.checks = x.checks || {}; x.checks[cb.dataset.step] = cb.checked; })));
    } else {
      const qi = a.qi || 0, [tag, q] = BQ[a.qs[qi]] || BQ[0], last = qi >= a.qs.length - 1;
      const qUntil = a.qAt ? a.qAt + 120000 : 0;
      setPage(`<div class="page narrow">${mockHead(a, "Behavioural mock")}
        <p class="muted">Question ${qi + 1} of ${a.qs.length}. Read it, take a few seconds to pick a story, then start the two-minute clock and answer out loud.</p>
        <div class="bar" style="margin-bottom:14px"><i style="width:${(100 * qi) / a.qs.length}%"></i></div>
        <section class="card mk-prompt"><span class="tcard-group">${esc(tag)}</span><h2>${esc(q)}</h2>
          ${a.qAt ? `<div class="mk-clock sm" role="timer" aria-label="Answer time left" data-until="${qUntil}" data-soon="30000" data-over="mkOver">${clock(qUntil - Date.now())}</div><p id="mkOver" class="pl-warn" ${Date.now() >= qUntil ? "" : "hidden"} style="margin:0">Two minutes are up. Wrap up with the result.</p>` : ""}
          <div class="dlg-row">${a.qAt ? `<button class="btn primary" type="button" id="mkNext">${last ? "Finish and rate my answers" : "Next question"}</button>` : `<button class="btn primary" type="button" id="mkGo">Start my 2-minute answer</button>`}</div></section>
        <section class="card"><h2>STAR, briefly</h2><dl class="mk-star">${STAR.map(([k, d]) => `<dt>${k}</dt><dd>${d}</dd>`).join("")}</dl>
          <p class="muted" style="margin:0;font-size:14px">More in ${lessonLink("behavioural/story-bank") || lessonLink("interview-prep/story-grid-star") || "the interview-prep track"}${lessonLink("behavioural/follow-up-probes") ? ` and ${lessonLink("behavioural/follow-up-probes")}` : lessonLink("interview-prep/classic-behavioural-questions") ? ` and ${lessonLink("interview-prep/classic-behavioural-questions")}` : ""}.</p></section>
        <div class="dlg-row"><button class="btn danger" type="button" id="mkAbandon">Abandon mock</button></div></div>`);
      const go = $("#mkGo"), nx = $("#mkNext");
      if (go) go.onclick = () => { mockSet((x) => (x.qAt = Date.now())); viewMock(); mockTick(); const b = $("#mkNext"); if (b) b.focus(); };
      if (nx) nx.onclick = () => { mockSet((x) => { if (last) { x.phase = "review"; x.end = Date.now(); } else { x.qi = qi + 1; x.qAt = null; } }); viewMock(); const b = $("#mkGo") || $("#mkReview input"); if (b) b.focus(); };
    }
    const fin = $("#mkFinish");
    if (fin) fin.onclick = () => { mockSet((x) => { x.phase = "review"; x.end = Date.now(); }); mockTick(); viewMock(); const f = $("#mkReview input"); if (f) f.focus(); };
    $("#mkAbandon").onclick = () => { if (confirm("Abandon this mock? Nothing is saved to your history.")) { store.set((s) => (s.mocks.active = null)); mockTick(); viewMock(); } };
    mockTick();
  }
  function viewMockReview(a) {
    const s = S();
    let areas, pre = {}, intro = "";
    if (a.kind === "behavioural") areas = a.qs.map((i) => [BQ[i][0], BQ[i][0], BQ[i][1]]);
    else areas = RUBRIC[a.kind];
    if (a.kind === "design") SD_STEPS.forEach(([k]) => { if (!(a.checks || {})[k]) pre[k] = 1; });
    if (a.kind === "coding") intro = `<ul class="mk-list">${(a.probs || []).map((pid) => { const x = probMeta(pid); return x ? `<li><a href="#/problem/${esc(pid)}">${esc(x.title)}</a> <span class="diff ${esc(x.difficulty)}">${esc(x.difficulty)}</span>${x.pattern ? ` <span class="muted">· ${esc(x.pattern)}</span>` : ""} · ${s.solved[pid] && s.solved[pid] >= a.at ? `<b style="color:var(--ok)">solved during the mock</b>` : "not solved during the mock"}</li>` : ""; }).join("")}</ul>`;
    if (a.kind === "design") {
      const [q, mod, lid] = SD_PROMPTS[a.p] || SD_PROMPTS[0], t = DATA.tracks["system-design"], m = t && t.modules.find((x) => x.id === mod);
      const ls = m ? m.lessons.filter((l) => !lid || l.id === lid) : [];
      intro = `<p><b>Prompt:</b> ${esc(q)}</p>${ls.length ? `<p>Compare your design with ${ls.map((l) => `<a href="#/lesson/system-design/${esc(l.id)}">${esc(l.title)}</a>`).join(" and ")}.</p>` : ""}${Object.keys(pre).length ? `<p class="muted">Steps you did not tick start at 1; change them if you did cover them.</p>` : ""}`;
    }
    const mins = Math.max(1, Math.round(((a.end || Date.now()) - a.at) / 60000));
    setPage(`<div class="page narrow">${mockHead(a, `Score your ${MOCK_NAME[a.kind].toLowerCase()}`)}
      <p class="muted">You took ${mins} minute${mins > 1 ? "s" : ""}. Rate each area from 1 to 4 as an interviewer would: 1 missed, 2 partly, 3 solid, 4 strong.</p>${intro}
      <form id="mkReview" class="card mk-review" novalidate>
        ${areas.map(([k, t, d]) => `<fieldset class="rub"><legend><b>${esc(t)}</b><span class="muted">${esc(d)}</span></legend><div class="seg">${[1, 2, 3, 4].map((v) => `<label><input type="radio" name="r-${esc(k)}" value="${v}" ${pre[k] === v ? "checked" : ""} required><span>${v} · ${SCALE[v]}</span></label>`).join("")}</div></fieldset>`).join("")}
        <label class="fld"><span>Notes for next time</span><textarea id="mkNotes" class="notes-area" maxlength="2000" placeholder="What went well, where you got stuck, what to practise next…"></textarea></label>
        <p id="mkErr" class="acct-bad" role="alert"></p>
        <div class="dlg-row"><button class="btn primary" type="submit">Save to history</button><button class="btn danger" type="button" id="mkAbandon">Discard</button></div></form></div>`);
    $("#mkReview").onsubmit = (e) => {
      e.preventDefault();
      const scores = {};
      let missing = 0;
      areas.forEach(([k]) => { const r = $(`#mkReview [name="r-${CSS.escape(k)}"]:checked`); if (r) scores[k] = +r.value; else missing++; });
      if (missing) { $("#mkErr").textContent = `Rate every area (${missing} still blank).`; return; }
      const notes = $("#mkNotes").value.slice(0, 2000);
      store.set((st) => {
        const x = st.mocks.active;
        if (!x) return;
        const e2 = { kind: x.kind, at: x.at, end: x.end || Date.now(), scores, notes };
        if (x.probs) { e2.probs = x.probs; e2.solved = x.probs.filter((p) => st.solved[p] && st.solved[p] >= x.at); }
        if (x.p != null) e2.p = x.p;
        if (x.qs) e2.qs = x.qs;
        st.mocks.history = (st.mocks.history || []).concat(e2).slice(-60);
        st.mocks.active = null;
      });
      location.hash = "#/mock/history";
    };
    $("#mkAbandon").onclick = () => { if (confirm("Discard this mock without saving?")) { store.set((st) => (st.mocks.active = null)); viewMock(); } };
  }
  function mockDetail(m) {
    if (m.kind === "coding") return (m.probs || []).map((p) => { const x = probMeta(p); return x ? `<a href="#/problem/${esc(p)}">${esc(x.title)}</a>${(m.solved || []).includes(p) ? " ✓" : ""}` : ""; }).filter(Boolean).join(", ");
    if (m.kind === "design") return esc((SD_PROMPTS[m.p] || [""])[0]);
    return `${(m.qs || []).length} questions`;
  }
  function mockTable(list, short) {
    return `<table class="ptable mk-table"><thead><tr><th>Date</th><th>Type</th><th class="pat">Details</th><th>Score</th>${short ? "" : `<th>Notes</th>`}</tr></thead><tbody>${list.map((m) => `<tr>
      <td>${new Date(m.at).toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" })}</td><td>${MOCK_NAME[m.kind] || esc(m.kind)}</td><td class="pat">${mockDetail(m)}</td>
      <td><b>${avgScore(m).toFixed(1)}</b><span class="muted">/4</span></td>${short ? "" : `<td class="mk-notes">${m.notes ? esc(m.notes) : `<span class="muted">none</span>`}</td>`}</tr>`).join("")}</tbody></table>`;
  }
  function mockChart(hist) {
    const W = 640, H = 220, L = 30, Rp = 14, T = 12, Bp = 30, n = hist.length;
    const x = (i) => (n === 1 ? (L + W - Rp) / 2 : L + (i * (W - L - Rp)) / (n - 1)), y = (v) => T + ((4 - v) / 3) * (H - T - Bp);
    const col = { coding: "var(--accent)", design: "var(--accent-2)", behavioural: "var(--warn)" };
    let g = [1, 2, 3, 4].map((v) => `<line x1="${L}" x2="${W - Rp}" y1="${y(v)}" y2="${y(v)}" stroke="var(--border)" stroke-width="1"/><text x="${L - 8}" y="${y(v) + 4}" text-anchor="end" font-size="11" fill="var(--muted)">${v}</text>`).join("");
    Object.keys(col).forEach((k) => {
      const pts = hist.map((m, i) => [i, m]).filter(([, m]) => m.kind === k);
      if (pts.length > 1) g += `<polyline fill="none" stroke="${col[k]}" stroke-width="2" points="${pts.map(([i, m]) => `${x(i).toFixed(1)},${y(avgScore(m)).toFixed(1)}`).join(" ")}"/>`;
      g += pts.map(([i, m]) => `<circle cx="${x(i).toFixed(1)}" cy="${y(avgScore(m)).toFixed(1)}" r="4.5" fill="${col[k]}" stroke="var(--surface)" stroke-width="2"><title>${MOCK_NAME[k]}, ${new Date(m.at).toLocaleDateString()}: ${avgScore(m).toFixed(1)} of 4</title></circle>`).join("");
    });
    const d0 = new Date(hist[0].at).toLocaleDateString(undefined, { day: "numeric", month: "short" }), d1 = new Date(hist[n - 1].at).toLocaleDateString(undefined, { day: "numeric", month: "short" });
    g += `<text x="${L}" y="${H - 8}" font-size="11" fill="var(--muted)">${d0}</text>${n > 1 ? `<text x="${W - Rp}" y="${H - 8}" text-anchor="end" font-size="11" fill="var(--muted)">${d1}</text>` : ""}`;
    const kinds = Object.keys(col).filter((k) => hist.some((m) => m.kind === k));
    return `<figure class="mk-chart"><svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Average self-score per mock, from 1 to 4, oldest on the left. ${n} mocks; the table below lists every score.">${g}</svg>
      <figcaption class="mk-legend">${kinds.map((k) => `<span><i style="background:${col[k]}"></i>${MOCK_NAME[k]}</span>`).join("")}</figcaption></figure>`;
  }
  function viewMockHistory() {
    const hist = (mocksOf().history || []).slice().sort((a, b) => a.at - b.at);
    if (!hist.length) {
      setPage(`<div class="page narrow"><div class="crumbs"><a href="#/">Home</a> / <a href="#/mock">Mock interviews</a></div><h1 class="page-title">Mock history</h1><p>No mocks saved yet. <a href="#/mock">Run your first mock</a> and your scores will build up here.</p></div>`);
      return;
    }
    const agg = {};
    hist.forEach((m) => {
      const labels = m.kind === "behavioural" ? null : Object.fromEntries((RUBRIC[m.kind] || []).map(([k, t]) => [k, t]));
      Object.entries(m.scores || {}).forEach(([k, v]) => {
        const id = m.kind + ":" + k;
        (agg[id] = agg[id] || { kind: m.kind, key: k, label: labels ? labels[k] || k : k, sum: 0, n: 0 });
        agg[id].sum += v; agg[id].n++;
      });
    });
    const areas = Object.values(agg).map((a) => ({ ...a, avg: a.sum / a.n })).sort((a, b) => a.avg - b.avg);
    const weak = new Set(areas.filter((a) => a.avg < 3.5).slice(0, Math.min(3, Math.max(1, Math.floor(areas.length / 3)))).map((a) => a.kind + ":" + a.key));
    const byKind = ["coding", "design", "behavioural"].filter((k) => areas.some((a) => a.kind === k)).map((k) => {
      const rows = areas.filter((a) => a.kind === k).map((a) => {
        const isW = weak.has(a.kind + ":" + a.key), help = k === "behavioural" ? AREA_HELP.behavioural : (AREA_HELP[k] || {})[a.key];
        return `<li class="mk-area ${isW ? "weak" : ""}"><span class="mk-al">${esc(a.label)}${isW ? ` <span class="pl-badge warn">Focus</span>` : ""}</span><span class="bar"><i style="width:${(a.avg / 4) * 100}%"></i></span><span class="mk-av">${a.avg.toFixed(1)} <span class="muted">(${a.n})</span></span>${isW && lessonLink(help) ? `<span class="mk-help">Brush up: ${lessonLink(help)}</span>` : ""}</li>`;
      }).join("");
      const ms = hist.filter((m) => m.kind === k);
      return `<section class="card"><h3>${MOCK_NAME[k]} <span class="muted" style="font-weight:400;font-size:14px">· ${ms.length} done · average ${(ms.reduce((a, m) => a + avgScore(m), 0) / ms.length).toFixed(1)}/4</span></h3><ul class="mk-areas">${rows}</ul></section>`;
    }).join("");
    const weakList = areas.filter((a) => weak.has(a.kind + ":" + a.key));
    setPage(`<div class="page narrow"><div class="crumbs"><a href="#/">Home</a> / <a href="#/mock">Mock interviews</a></div><h1 class="page-title">Mock history</h1>
      <p class="muted">${hist.length} mock${hist.length > 1 ? "s" : ""} saved. Scores are your own 1-to-4 ratings, averaged per mock.</p>
      ${weakList.length ? `<p class="pl-warn">Weakest areas so far: ${weakList.map((a) => `<b>${esc(a.label)}</b> (${MOCK_NAME[a.kind].toLowerCase()}, ${a.avg.toFixed(1)})`).join(", ")}.</p>` : `<p class="pl-fit">No weak areas: every area averages 3.5 or more.</p>`}
      <section class="card"><h2>Scores over time</h2>${mockChart(hist)}</section>
      <div class="section-h"><h2>Rubric areas</h2></div><div class="mk-kinds">${byKind}</div>
      <div class="section-h"><h2>Every mock</h2><a class="btn sm" href="#/mock">Start another</a></div>
      <div class="table-wrap">${mockTable(hist.slice().reverse(), false)}</div></div>`);
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
      else if (parts[0] === "scoreboard") await viewScoreboard();
      else if (parts[0] === "roadmap") viewRoadmap();
      else if (parts[0] === "plan") viewPlan(parts[1]);
      else if (parts[0] === "mock") viewMock(parts[1]);
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
         <p class="acct-warn"><b>Read this first.</b> Choose a simple username and a <b>new password you have never used anywhere else</b>. Accounts exist only to save study progress, and this site may be shared by several people, so do not use a real password. There is no password reset. Your username is shown on the public scoreboard, so do not use your real name.</p>
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
  window.__sg = { Py, Sql, DATA, getProblem, Cloud }; // debugging hook used by the self-test
  Promise.all([loadAll(), Ghibli.load(), Cloud.pull().catch(() => {})]).then(() => { mockTick(); return route(); }).catch((e) => {
    main.innerHTML = `<div class="page narrow"><h1 class="page-title">Could not load content</h1><p class="muted">${esc(e.message)}</p><p>If you opened the file directly, serve the <code>docs/</code> folder over HTTP (e.g. <code>python -m http.server</code>).</p></div>`;
  });
})();
