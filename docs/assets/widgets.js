/* Interactive lesson widgets: <div class="widget" data-widget="bits|float|cache|bigo"></div> */
window.Widgets = (() => {
  const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

  // ------------------------------------------------ integer bits
  function bits(el) {
    let w = +(el.dataset.width || 8), val = 0n;
    el.innerHTML = `<h4>Integer bit explorer</h4>
      <div class="row"><label>Width <select class="w">${[4, 8, 16, 32].map((x) => `<option ${x === w ? "selected" : ""}>${x}</option>`).join("")}</select></label>
      <label>Decimal <input type="text" class="dec" value="0" inputmode="numeric" style="width:9em"></label>
      <span class="muted" style="font-size:12px">Click bits to flip them.</span></div>
      <div class="bits"></div><div class="kv" style="margin-top:12px"></div>`;
    const bitsEl = el.querySelector(".bits"), kv = el.querySelector(".kv"), dec = el.querySelector(".dec");
    const mask = () => (1n << BigInt(w)) - 1n;
    function draw() {
      val &= mask();
      bitsEl.innerHTML = "";
      for (let i = w - 1; i >= 0; i--) {
        const on = (val >> BigInt(i)) & 1n;
        const b = document.createElement("div");
        b.className = "bit" + (on ? " on" : "") + (i === w - 1 ? " sign" : "") + ((i + 1) % 4 === 0 && i !== w - 1 ? " gap" : "");
        b.textContent = on ? "1" : "0";
        b.title = `bit ${i} (2^${i})`;
        b.onclick = () => { val ^= 1n << BigInt(i); draw(); };
        bitsEl.appendChild(b);
      }
      const unsigned = val;
      const signed = val >> BigInt(w - 1) ? val - (1n << BigInt(w)) : val;
      const hex = "0x" + val.toString(16).toUpperCase().padStart(w / 4, "0");
      kv.innerHTML = `<span>Unsigned (B2U)</span><span>${unsigned}</span><span>Two's complement (B2T)</span><span>${signed}</span>
        <span>Hex</span><span>${hex}</span><span>~x (NOT)</span><span>${(~val) & mask()} / 0x${((~val) & mask()).toString(16).toUpperCase()}</span>
        <span>-x (negate)</span><span>${(-signed) >= -(1n << BigInt(w - 1)) && (-signed) < (1n << BigInt(w - 1)) ? -signed : (1n << BigInt(w - 1)) * -1n + " (overflow: TMin)"}</span>
        <span>Range (signed)</span><span>[${-(1n << BigInt(w - 1))}, ${(1n << BigInt(w - 1)) - 1n}]</span>`;
      if (document.activeElement !== dec) dec.value = String(signed);
    }
    dec.oninput = () => {
      try {
        let v = dec.value.trim();
        let n = v.startsWith("0x") || v.startsWith("0X") ? BigInt(v) : v.startsWith("0b") ? BigInt(v) : BigInt(v || "0");
        val = n & mask();
        draw();
      } catch (_) {}
    };
    el.querySelector(".w").onchange = (e) => { w = +e.target.value; draw(); };
    draw();
  }

  // ------------------------------------------------ IEEE-754 float32
  function float(el) {
    let u = 0x3f800000 >>> 0; // 1.0
    el.innerHTML = `<h4>IEEE-754 single-precision explorer</h4>
      <div class="row"><label>Value <input type="text" class="fv" value="1.0" style="width:12em"></label>
      <span class="muted" style="font-size:12px">Red = sign, amber = exponent (8 bits), blue = fraction (23 bits). Click to flip.</span></div>
      <div class="bits"></div><div class="kv" style="margin-top:12px"></div>`;
    const bitsEl = el.querySelector(".bits"), kv = el.querySelector(".kv"), fv = el.querySelector(".fv");
    const buf = new DataView(new ArrayBuffer(4));
    function draw() {
      buf.setUint32(0, u);
      const f = buf.getFloat32(0);
      bitsEl.innerHTML = "";
      for (let i = 31; i >= 0; i--) {
        const on = (u >>> i) & 1;
        const b = document.createElement("div");
        b.className = "bit" + (on ? " on" : "") + (i === 31 ? " sign" : i >= 23 ? " exp" : "") + (i === 30 || i === 22 ? " gap" : "");
        b.textContent = on;
        b.onclick = () => { u = (u ^ (1 << i)) >>> 0; draw(); };
        bitsEl.appendChild(b);
      }
      const s = u >>> 31, e = (u >>> 23) & 0xff, frac = u & 0x7fffff;
      let kind, formula;
      if (e === 0xff) { kind = frac ? "NaN" : "Infinity"; formula = kind; }
      else if (e === 0) { kind = frac ? "Denormalized" : "Zero"; formula = `(-1)^${s} × 0.${frac.toString(2).padStart(23, "0").replace(/0+$/, "") || "0"}₂ × 2^(1-127)`; }
      else { kind = "Normalized"; formula = `(-1)^${s} × 1.${frac.toString(2).padStart(23, "0").replace(/0+$/, "") || "0"}₂ × 2^(${e}-127 = ${e - 127})`; }
      kv.innerHTML = `<span>Value</span><span>${Object.is(f, -0) ? "-0" : f}</span><span>Kind</span><span>${kind}</span>
        <span>Sign s</span><span>${s}</span><span>Exponent e</span><span>${e} (bias 127 → E = ${e === 0 ? -126 : e - 127})</span>
        <span>Fraction</span><span>0x${frac.toString(16).padStart(6, "0")}</span><span>Formula</span><span>${esc(formula)}</span>
        <span>Hex</span><span>0x${u.toString(16).padStart(8, "0").toUpperCase()}</span>`;
      if (document.activeElement !== fv) fv.value = Object.is(f, -0) ? "-0" : String(f);
    }
    fv.oninput = () => { const x = Number(fv.value); if (!Number.isNaN(x) || fv.value.trim().toLowerCase() === "nan") { buf.setFloat32(0, x); u = buf.getUint32(0); draw(); } };
    draw();
  }

  // ------------------------------------------------ cache simulator
  function cache(el) {
    el.innerHTML = `<h4>Cache simulator</h4>
      <div class="row">
        <label>Sets S <select class="S">${[1, 2, 4, 8, 16].map((x) => `<option ${x === 4 ? "selected" : ""}>${x}</option>`).join("")}</select></label>
        <label>Lines/set E <select class="E">${[1, 2, 4].map((x) => `<option>${x}</option>`).join("")}</select></label>
        <label>Block B <select class="B">${[4, 8, 16, 32].map((x) => `<option ${x === 16 ? "selected" : ""}>${x}</option>`).join("")}</select> bytes</label>
      </div>
      <div class="row"><label style="flex:1">Address trace (decimal or 0x hex, comma/space separated)
        <input type="text" class="tr" value="0, 4, 16, 64, 0, 80, 16, 128, 0" style="width:100%"></label></div>
      <div class="row"><button class="btn sm go" type="button">Simulate (LRU)</button><span class="sum muted"></span></div>
      <div class="cache-grid"></div>`;
    const q = (c) => el.querySelector(c);
    function sim() {
      const S = +q(".S").value, E = +q(".E").value, B = +q(".B").value;
      const s = Math.log2(S), b = Math.log2(B);
      const addrs = q(".tr").value.split(/[\s,]+/).filter(Boolean).map((x) => Number(x));
      const sets = Array.from({ length: S }, () => []);
      let hits = 0, misses = 0, evict = 0;
      const rows = addrs.map((a, t) => {
        const set = (a >> b) & (S - 1), tag = a >> (s + b);
        const lines = sets[set];
        const idx = lines.findIndex((l) => l.tag === tag);
        let res;
        if (idx >= 0) { hits++; res = "hit"; lines[idx].used = t; }
        else {
          misses++; res = "miss";
          if (lines.length < E) lines.push({ tag, used: t });
          else { evict++; res = "miss (evict)"; let lru = 0; lines.forEach((l, i) => { if (l.used < lines[lru].used) lru = i; }); lines[lru] = { tag, used: t }; }
        }
        return `<tr class="${res.startsWith("hit") ? "hit" : "miss"}"><td>${a}</td><td>0x${a.toString(16)}</td><td>${tag}</td><td>${set}</td><td>${a & (B - 1)}</td><td>${res}</td></tr>`;
      });
      q(".sum").textContent = `${hits} hits, ${misses} misses (${evict} evictions) · hit rate ${addrs.length ? ((100 * hits) / addrs.length).toFixed(1) : 0}% · s=${s}, b=${b}`;
      q(".cache-grid").innerHTML = `<table><thead><tr><th>addr</th><th>hex</th><th>tag</th><th>set</th><th>offset</th><th>result</th></tr></thead><tbody>${rows.join("")}</tbody></table>`;
    }
    q(".go").onclick = sim;
    el.querySelectorAll("select").forEach((s) => (s.onchange = sim));
    sim();
  }

  // ------------------------------------------------ Big-O growth plot
  function bigo(el) {
    const fns = [
      ["1", () => 1], ["log n", (n) => Math.log2(n)], ["n", (n) => n], ["n log n", (n) => n * Math.log2(n)],
      ["n²", (n) => n * n], ["n³", (n) => n ** 3], ["2ⁿ", (n) => 2 ** n],
    ];
    const colors = ["#64748b", "#0ea5e9", "#22c55e", "#eab308", "#f97316", "#ef4444", "#a855f7"];
    el.innerHTML = `<h4>Growth rates</h4><div class="row"><label>n up to <input type="range" class="n" min="4" max="64" value="16"></label><span class="nv muted"></span>
      <label class="check"><input type="checkbox" class="log"> log scale</label></div><svg viewBox="0 0 600 280" style="width:100%;height:auto"></svg>
      <div class="row lg" style="font-size:12px"></div>`;
    const svg = el.querySelector("svg"), nIn = el.querySelector(".n"), logIn = el.querySelector(".log");
    el.querySelector(".lg").innerHTML = fns.map((f, i) => `<span><span style="display:inline-block;width:10px;height:10px;border-radius:2px;background:${colors[i]}"></span> ${f[0]}</span>`).join("");
    function draw() {
      const N = +nIn.value, log = logIn.checked;
      el.querySelector(".nv").textContent = `n = ${N}`;
      const W = 600, H = 280, P = 30;
      const ymax = log ? Math.log10(2 ** N) : N * N * 1.2;
      const Y = (v) => { const y = log ? Math.log10(Math.max(v, 1)) : v; return H - P - (Math.min(y, ymax) / ymax) * (H - 2 * P); };
      const X = (n) => P + ((n - 1) / (N - 1)) * (W - 2 * P);
      let paths = fns.map((f, i) => {
        let d = "";
        for (let n = 1; n <= N; n += Math.max(1, (N - 1) / 120)) d += (d ? "L" : "M") + X(n).toFixed(1) + "," + Y(f[1](n)).toFixed(1);
        return `<path d="${d}" fill="none" stroke="${colors[i]}" stroke-width="2.5" stroke-linejoin="round"/>`;
      }).join("");
      svg.innerHTML = `<line x1="${P}" y1="${H - P}" x2="${W - P}" y2="${H - P}" stroke="currentColor" opacity=".3"/><line x1="${P}" y1="${P}" x2="${P}" y2="${H - P}" stroke="currentColor" opacity=".3"/>${paths}
        <text x="${W - P}" y="${H - 8}" text-anchor="end" font-size="12" fill="currentColor" opacity=".6">n</text><text x="8" y="${P - 10}" font-size="12" fill="currentColor" opacity=".6">${log ? "log₁₀ ops" : "ops (clipped)"}</text>`;
    }
    nIn.oninput = draw; logIn.onchange = draw;
    draw();
  }

  const registry = { bits, float, cache, bigo };
  return {
    mount(el) {
      const fn = registry[el.dataset.widget];
      if (fn && !el.dataset.mounted) { el.dataset.mounted = "1"; try { fn(el); } catch (e) { el.textContent = "Widget error: " + e.message; } }
    },
  };
})();
