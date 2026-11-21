"""nodejs-track helper: checks lessons (word count, required sections, quiz size) and runs every js-run block in Node
with browser-worker-like restrictions (no require/process/setImmediate/Buffer).

  python src/nodejs/nodejs-check.py            # summary of all lessons
  python src/nodejs/nodejs-check.py 04         # also print the output of each js-run block of lesson 04
"""
import json, re, subprocess, sys, glob, os

HERE = os.path.dirname(os.path.abspath(__file__))
RUNNER = r"""
const codes = JSON.parse(require('fs').readFileSync(0, 'utf8'));
const AsyncFn = Object.getPrototypeOf(async function () {}).constructor;
const fmt = (v) => { if (typeof v === 'string') return v; try { const s = JSON.stringify(v); return s === undefined ? String(v) : s; } catch (e) { return String(v); } };
(async () => {
  const out = [];
  for (const code of codes) {
    const logs = []; const con = {}; let last = Date.now(); const started = Date.now();
    ['log', 'info', 'warn', 'error', 'debug', 'table'].forEach((k) => (con[k] = (...a) => { last = Date.now(); logs.push(a.map(fmt).join(' ')); }));
    let error = null;
    const onRej = (e) => { error = 'unhandled rejection: ' + e; };
    process.on('unhandledRejection', onRej);
    try { await new AsyncFn('console', 'require', 'process', 'setImmediate', 'Buffer', 'module', 'exports', code)(con); }
    catch (e) { error = String(e); }
    await new Promise((res) => { const tick = () => (Date.now() - last > 300 || Date.now() - started > 3000) ? res() : setTimeout(tick, 50); tick(); });
    process.off('unhandledRejection', onRej);
    out.push({ logs, error, ms: Date.now() - started });
  }
  console.log(JSON.stringify(out));
  process.exit(0);
})();
"""

show = sys.argv[1] if len(sys.argv) > 1 else None
bad = 0
for f in sorted(glob.glob(os.path.join(HERE, "lessons", "*.md"))):
    name = os.path.basename(f)
    text = open(f, encoding="utf-8").read()
    words = len(text.split())
    problems = []
    if words < 2400:
        problems.append(f"only {words} words")
    for needle in ["## In plain words", "Before this lesson", "## Glossary", "```quiz", "> **Source:**", "```mermaid", "[!INTERVIEW]", "[!TIP]", "[!WARNING]", "## Summary", "## Cheat sheet", "## Pitfalls"]:
        if needle not in text:
            problems.append("missing " + needle)
    for q in re.findall(r"```quiz\s*\n(.*?)```", text, re.S):
        try:
            n = len(json.loads(q))
            if not 6 <= n <= 8:
                problems.append(f"quiz has {n} questions")
            for item in json.loads(q):
                if not (0 <= item["answer"] < len(item["options"])) or "explain" not in item:
                    problems.append("quiz item broken: " + item["q"][:30])
        except Exception as e:
            problems.append(f"quiz JSON: {e}")
    for w in re.findall(r"\b(simply|obviously|just|as you know)\b", re.sub(r"```.*?```", "", text, flags=re.S), re.I):
        problems.append("banned word: " + w)
    codes = re.findall(r"```js-run\s*\n(.*?)```", text, re.S)
    res = json.loads(subprocess.run(["node", "-e", RUNNER], input=json.dumps(codes), capture_output=True, text=True, encoding="utf-8", timeout=300).stdout or "[]")
    if len(res) != len(codes):
        problems.append("runner crashed")
    for i, r in enumerate(res):
        if r["error"]:
            problems.append(f"js-run #{i + 1}: {r['error'][:160]}")
        elif not r["logs"]:
            problems.append(f"js-run #{i + 1}: no output")
        elif r["ms"] > 2600:
            problems.append(f"js-run #{i + 1}: too slow ({r['ms']} ms)")
        if show and name.startswith(show):
            print(f"--- {name} js-run #{i + 1}\n" + "\n".join(r["logs"]) + (f"\nERROR {r['error']}" if r["error"] else ""))
    bad += bool(problems)
    print(f"{name}: {words} words, {len(codes)} js-run" + ("" if not problems else "\n   " + "\n   ".join(problems)))
print(f"{bad} lesson(s) with problems")
