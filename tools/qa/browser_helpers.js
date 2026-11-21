// Browser QA helpers for the Sky Castle study guide.
//
// Paste this whole file into the DevTools console (or a javascript_tool call) on a page of the
// local preview (python -m http.server 8765 --directory docs). These checks only read data and run
// code; they record no progress. Still, prefer http://127.0.0.1:8765 or a private window: on the
// owner's machine http://localhost:8765 is signed in to their account, and opening lessons there
// moves the home page's "Continue" pointer.
//
//   await __loadMermaid();                 // needed once before __mermaidAll on a fresh page
//   await __selftest('python')             // every problem: reference passes, starter fails
//   await __lessonDemos(['python'])        // every python-run / js-run demo runs (html-run: count only)
//   await __sqlDemos('sql')                // every sql-run demo returns a result (some fail on purpose)
//   await __mermaidAll(['python'])         // every mermaid block parses
//   await __mermaid('python')              // render pass: diagrams draw, quiz present, no KaTeX error
//   __fullSweep(); ... later: __sweepReport()   // all tracks: problems + demos + sql demos
//
// Keep the browser tab in front while these run: background tabs throttle timers and skip layout,
// which makes web problems' layout checks fail falsely. html-run demos are interaction-tested with
// Playwright instead (tools/qa/html_demo_monkey.js).

window.__loadMermaid = async () => {
  if (window.mermaid) return 'already loaded';
  await new Promise((res, rej) => {
    const s = document.createElement('script');
    s.src = 'https://cdn.jsdelivr.net/npm/mermaid@10.9.1/dist/mermaid.min.js';
    s.onload = res; s.onerror = rej; document.head.appendChild(s);
  });
  window.mermaid.initialize({ startOnLoad: false });
  return 'loaded';
};

window.__selftest = async (tid) => {
  const { Py, Sql } = window.__sg;
  const all = await (await fetch('data/problems/' + tid + '.json', { cache: 'no-store' })).json();
  const out = { tid, n: 0, ok: 0, server: 0, fails: [] };
  const jsPass = (r, p) => !r.fatal && r.results.every((x, i) => !x.error && WebKit.eq(JSON.parse(x.got_s), p.tests[i].expected, p.compare || 'exact', p.tolerance || 1e-6));
  for (const [pid, p] of Object.entries(all)) {
    out.n++;
    try {
      if (p.kind === 'java' || p.kind === 'go') { out.server++; out.ok++; continue; }   // judged on the server at build time
      if (p.kind === 'js') {
        const r = await WebKit.runJs(p.solution, p.entry, p.tests);
        if (!jsPass(r, p)) out.fails.push(pid + ': solution fails ' + String(r.fatal || '').slice(0, 120));
        else if (jsPass(await WebKit.runJs(p.starter, p.entry, p.tests), p)) out.fails.push(pid + ': starter already passes');
        else out.ok++;
      } else if (p.kind === 'web') {
        const r = await WebKit.runWeb(p.solution, p.checks); const s = await WebKit.runWeb(p.starter, p.checks);
        if (!r.every((x) => x.ok)) out.fails.push(pid + ': solution fails ' + JSON.stringify(r.filter((x) => !x.ok)[0]).slice(0, 160));
        else if (s.every((x) => x.ok)) out.fails.push(pid + ': starter already passes'); else out.ok++;
      } else if (p.kind === 'sql') {
        const a = await Sql.run(p.solution, p.dataset); if (a.res) out.ok++;
      } else {
        const r = await Py.judge(p.solution, tid, pid, 'submit', [], null, 60000);
        if (r.passed !== r.total || !r.total) { out.fails.push(pid + ': solution ' + r.passed + '/' + r.total + ' ' + (r.error || '').slice(-120)); continue; }
        let s = null; try { s = await Py.judge(p.starter, tid, pid, 'submit', [], null, 60000); } catch (e) { s = { passed: 0, total: 1 }; }
        if (s.total && s.passed === s.total) out.fails.push(pid + ': starter already passes'); else out.ok++;
      }
    } catch (e) { out.fails.push(pid + ': EXC ' + String(e.message || e).slice(-160)); }
  }
  return out;
};

window.__lessonDemos = async (tracks) => {
  const { Py } = window.__sg; const out = { n: 0, html: 0, fails: [] };
  for (const tid of tracks) {
    const t = await (await fetch('data/tracks/' + tid + '.json', { cache: 'no-store' })).json();
    for (const m of t.modules) for (const l of m.lessons) {
      const md = await (await fetch('data/lessons/' + tid + '/' + l.file, { cache: 'no-store' })).text();
      let cur = null, kind = null; const idx = { py: 0, js: 0, html: 0 };
      for (const ln of md.split(/\r?\n/)) {
        if (cur === null) { const mm = ln.match(/^\s*```(python-run|py-run|js-run|html-run)\s*$/); if (mm) { cur = []; kind = mm[1] === 'js-run' ? 'js' : mm[1] === 'html-run' ? 'html' : 'py'; } }
        else if (/^\s*```\s*$/.test(ln)) {
          idx[kind]++; const code = cur.join('\n'); cur = null; let err = null;
          if (kind === 'html') { out.html++; continue; }
          out.n++;
          if (kind === 'py') { try { await Py.run(code, null, 30000); } catch (e) { err = (e.tle ? 'TLE ' : '') + e.message.slice(-260); } }
          else { const r = await WebKit.runJs(code, null, []); if (r.fatal) err = r.fatal.slice(0, 260); }
          if (err) out.fails.push({ tid, file: l.file, kind, idx: idx[kind], err });
        } else cur.push(ln);
      }
    }
  }
  return out;
};

window.__sqlDemos = async (tid) => {
  const { Sql } = window.__sg;
  const t = await (await fetch('data/tracks/' + tid + '.json', { cache: 'no-store' })).json();
  const out = { n: 0, fails: [] };
  for (const m of t.modules) for (const l of m.lessons) {
    const md = await (await fetch('data/lessons/' + tid + '/' + l.file, { cache: 'no-store' })).text();
    let cur = null, ds = null, idx = 0;
    for (const ln of md.split(/\r?\n/)) {
      if (cur === null) { const mm = ln.match(/^\s*```sql-run(.*)$/); if (mm) { cur = []; ds = (mm[1].match(/dataset=([\w-]+)/) || [])[1]; } }
      else if (/^\s*```\s*$/.test(ln)) {
        idx++; out.n++;
        try { const r = await Sql.run(cur.join('\n'), ds); if (!r.res) out.fails.push({ file: l.file, idx, err: 'no result' }); }
        catch (e) { out.fails.push({ file: l.file, idx, err: String(e.message || e).slice(0, 200) }); }
        cur = null;
      } else cur.push(ln);
    }
  }
  return out;
};

window.__mermaidAll = async (tracks) => {
  const out = { blocks: 0, lessons: 0, fails: [] };
  for (const tid of tracks) {
    let t;
    try { t = await (await fetch('data/tracks/' + tid + '.json', { cache: 'no-store' })).json(); } catch (e) { out.fails.push({ tid, err: 'no track json' }); continue; }
    for (const m of t.modules) for (const l of m.lessons) {
      out.lessons++;
      const md = await (await fetch('data/lessons/' + tid + '/' + l.file, { cache: 'no-store' })).text();
      let cur = null, idx = 0;
      for (const ln of md.split(/\r?\n/)) {
        if (cur === null) { if (/^\s*```mermaid\s*$/.test(ln)) cur = []; }
        else if (/^\s*```\s*$/.test(ln)) {
          idx++; out.blocks++; const code = cur.join('\n'); cur = null;
          try { await window.mermaid.parse(code); } catch (e) { out.fails.push({ tid, file: l.file, idx, err: String(e.message || e).split('\n').slice(0, 4).join(' | ').slice(0, 220) }); }
        } else cur.push(ln);
      }
    }
  }
  return out;
};

// Render pass: navigates to every lesson (so it moves the "Continue" pointer on a signed-in origin).
window.__mermaid = async (tid, filter) => {
  const t = await (await fetch('data/tracks/' + tid + '.json', { cache: 'no-store' })).json();
  const out = [];
  for (const m of t.modules) for (const l of m.lessons) {
    if (filter && !filter.test(l.file)) continue;
    location.hash = '#/lesson/' + tid + '/' + l.id;
    let wraps = [], ok = 0;
    for (let i = 0; i < 24; i++) {
      await new Promise((r) => setTimeout(r, 250));
      wraps = [...document.querySelectorAll('.mermaid-wrap')];
      ok = wraps.filter((w) => w.querySelector('svg') && !/syntax error|parse error/i.test(w.textContent)).length;
      if (wraps.length && ok === wraps.length) break;
    }
    const quiz = document.querySelectorAll('.quiz').length;
    const katexErr = document.querySelectorAll('.katex-error').length;
    if (ok !== wraps.length || !quiz || katexErr) out.push({ file: l.file, mermaid: ok + '/' + wraps.length, quiz, katexErr, bad: wraps.filter((w) => !w.querySelector('svg') || /syntax error|parse error/i.test(w.textContent)).map((w) => w.textContent.slice(0, 120)) });
  }
  return { checked: true, problems: out };
};

// Whole-site sweep (about 10 minutes for 50 tracks with the tab in front). Poll __sweepReport().
window.__fullSweep = async () => {
  const ids = (await (await fetch('data/index.json', { cache: 'no-store' })).json()).map((t) => t.id);
  window.__FULL = { start: Date.now(), done: [], res: {} };
  (async () => {
    for (const tid of ids) {
      const R = window.__FULL.res[tid] = {};
      try { R.p = await window.__selftest(tid); R.d = await window.__lessonDemos([tid]); R.s = await window.__sqlDemos(tid); } catch (e) { R.crash = String(e); }
      window.__FULL.done.push(tid);
    }
    window.__FULL.end = Date.now();
  })();
  return 'started ' + ids.length + ' tracks';
};

window.__sweepReport = () => {
  const F = window.__FULL; if (!F) return 'not started';
  const bad = {}; const tot = { problems: 0, ok: 0, server: 0, demos: 0, sqlDemos: 0 };
  for (const [k, v] of Object.entries(F.res)) {
    if (v.p) { tot.problems += v.p.n; tot.ok += v.p.ok; tot.server += v.p.server; }
    if (v.d) tot.demos += v.d.n; if (v.s) tot.sqlDemos += v.s.n;
    const f = {};
    if (v.crash) f.crash = v.crash;
    if (v.p && v.p.fails.length) f.problems = v.p.fails;
    if (v.d && v.d.fails.length) f.demos = v.d.fails;
    if (v.s && v.s.fails.length && k !== 'sql') f.sql = v.s.fails;   // the sql track's 13 failing demos are intentional
    if (Object.keys(f).length) bad[k] = f;
  }
  return { done: F.done.length, finished: !!F.end, minutes: (((F.end || Date.now()) - F.start) / 60000).toFixed(1), totals: tot, failures: bad };
};

'Sky Castle QA helpers loaded';
