"""graphql-track helper: run every js-run / python-run block in the lessons and report failures and word counts.

  python src/graphql/graphql_track_check.py [file-substring]
"""
import glob, json, os, re, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
BANNED = re.compile(r"\b(simply|obviously|as you know)\b", re.I)
flt = sys.argv[1] if len(sys.argv) > 1 else ""
bad = 0
for f in sorted(glob.glob(os.path.join(HERE, "lessons", "*.md"))):
    if flt not in f:
        continue
    text = open(f, encoding="utf-8").read()
    name = os.path.basename(f)
    words = len(text.split())
    notes = []
    for i, code in enumerate(re.findall(r"```js-run\s*\n(.*?)```", text, re.S)):
        with tempfile.NamedTemporaryFile("w", suffix=".mjs", delete=False, encoding="utf-8") as t:
            t.write(code)
        r = subprocess.run(["node", t.name], capture_output=True, text=True, encoding="utf-8", timeout=30)
        os.unlink(t.name)
        if r.returncode != 0:
            notes.append("js-run #%d FAILED: %s" % (i, r.stderr.strip().splitlines()[-1] if r.stderr.strip() else "?"))
        elif not r.stdout.strip():
            notes.append("js-run #%d printed nothing" % i)
    for i, code in enumerate(re.findall(r"```python-run\s*\n(.*?)```", text, re.S)):
        r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, encoding="utf-8", timeout=30)
        if r.returncode != 0:
            notes.append("python-run #%d FAILED: %s" % (i, r.stderr.strip().splitlines()[-1]))
    for q in re.findall(r"```quiz\s*\n(.*?)```", text, re.S):
        try:
            qs = json.loads(q)
            if not 6 <= len(qs) <= 8:
                notes.append("quiz has %d questions" % len(qs))
            for item in qs:
                if not (0 <= item["answer"] < len(item["options"])) or not item.get("explain"):
                    notes.append("quiz item bad: " + item["q"][:40])
        except Exception as e:  # noqa: BLE001
            notes.append("quiz JSON: %s" % e)
    if "```quiz" not in text:
        notes.append("no quiz")
    if words < 2400:
        notes.append("only %d words" % words)
    prose = re.sub(r"```.*?```", "", text, flags=re.S)
    m = BANNED.findall(prose)
    if m:
        notes.append("banned words: %s" % sorted(set(x.lower() for x in m)))
    if re.search(r"\bjust\b", prose):
        notes.append("contains 'just' x%d" % len(re.findall(r"\bjust\b", prose)))
    for need in ("Before this lesson", "## In plain words", "## Glossary", "> **Source:**", "[!INTERVIEW]", "[!TIP]", "[!WARNING]", "```mermaid"):
        if need not in text:
            notes.append("missing " + need)
    bad += bool(notes)
    print("%-48s %5d words  %s" % (name, words, "; ".join(notes) or "ok"))
sys.exit(1 if bad else 0)
