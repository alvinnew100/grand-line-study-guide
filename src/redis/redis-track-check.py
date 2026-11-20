"""Author helper: run every python-run block of the redis lessons and report word counts.

  python src/redis/redis-track-check.py [substring-of-filename]
"""
import glob, io, os, re, sys, contextlib, json, traceback
here = os.path.dirname(os.path.abspath(__file__))
flt = sys.argv[1] if len(sys.argv) > 1 else ""
bad = 0
for f in sorted(glob.glob(os.path.join(here, "lessons", "*.md"))):
    if flt not in os.path.basename(f):
        continue
    text = open(f, encoding="utf-8").read()
    words = len(text.split())
    blocks = re.findall(r"```python-run\s*\n(.*?)```", text, re.S)
    quiz = re.findall(r"```quiz\s*\n(.*?)```", text, re.S)
    nq = sum(len(json.loads(q)) for q in quiz)
    for q in quiz:
        for item in json.loads(q):
            assert 0 <= item["answer"] < len(item["options"]) and item.get("explain"), item["q"]
    status = []
    for i, b in enumerate(blocks):
        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf):
                exec(compile(b, f"{os.path.basename(f)}#{i}", "exec"), {"__name__": "__main__"})
            status.append("ok" if buf.getvalue().strip() else "NO-OUTPUT")
        except Exception:
            bad += 1
            status.append("FAIL")
            traceback.print_exc()
    flags = []
    if words < 2400: flags.append("SHORT")
    if not 6 <= nq <= 8: flags.append("QUIZ")
    if "```mermaid" not in text: flags.append("no-mermaid")
    if "> **Source:**" not in text: flags.append("NO-SOURCE")
    for c in ("[!INTERVIEW]", "[!TIP]", "[!WARNING]"):
        if c not in text: flags.append("no" + c)
    if "```bash" not in text: flags.append("no-bash")
    for need in ("## In plain words", "Before this lesson", "## Glossary", "## Pitfalls", "cheat sheet", "## Summary"):
        if need not in text: flags.append("MISSING<" + need + ">")
    prose = re.sub(r"```.*?```", "", text, flags=re.S)
    for ln in prose.splitlines():
        for w in re.findall(r"[^a-z](simply|obviously|just|as you know)[^a-z]", " " + ln.lower() + " "):
            flags.append("BANNED:" + w + ":" + ln.strip()[:50])
    if not blocks: flags.append("NO-RUN")
    print(f"{os.path.basename(f):42s} {words:5d}w quiz={nq} run={status} {' '.join(flags)}")
sys.exit(1 if bad else 0)
