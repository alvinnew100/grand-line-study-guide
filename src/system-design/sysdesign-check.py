"""Author helper for the system-design track (not part of the site build).

  python src/system-design/sysdesign-check.py            # check every lesson
  python src/system-design/sysdesign-check.py 10 11      # only files starting with 10-, 11-

For each lesson: word count, banned beginner-hostile words, python-run blocks executed,
quiz size, mermaid count and required section headings.
"""
import contextlib, glob, io, json, os, re, sys, traceback

HERE = os.path.dirname(os.path.abspath(__file__))
BANNED = re.compile(r"\b(simply|obviously|just|as you know)\b", re.I)
MIN_WORDS = 2600


def main():
    only = sys.argv[1:]
    bad = 0
    for f in sorted(glob.glob(os.path.join(HERE, "lessons", "*.md"))):
        name = os.path.basename(f)
        if only and not any(name.startswith(o + "-") for o in only):
            continue
        text = open(f, encoding="utf-8").read()
        words = len(text.split())
        notes = []
        if words < MIN_WORDS:
            notes.append(f"only {words} words")
        prose = re.sub(r"```.*?```", "", text, flags=re.S)
        hits = sorted({m.group(0).lower() for m in BANNED.finditer(prose)})
        if hits:
            lines = [i + 1 for i, l in enumerate(text.splitlines()) if BANNED.search(l)]
            notes.append(f"banned words {hits} at lines {lines[:12]}")
        for sec in ("Before this lesson", "In plain words", "Summary", "Glossary", "**Source:**"):
            if sec not in text:
                notes.append(f"missing '{sec}'")
        quizzes = re.findall(r"```quiz\s*\n(.*?)```", text, re.S)
        nq = 0
        for q in quizzes:
            try:
                items = json.loads(q)
                nq += len(items)
                for it in items:
                    assert 0 <= it["answer"] < len(it["options"]) and it.get("explain")
            except Exception as e:  # noqa: BLE001
                notes.append(f"quiz error {e}")
        if not 6 <= nq <= 8:
            notes.append(f"{nq} quiz questions")
        nm = len(re.findall(r"```mermaid", text))
        if nm < 2:
            notes.append(f"{nm} mermaid diagrams")
        runs = re.findall(r"```python-run\s*\n(.*?)```", text, re.S)
        if not runs and not name.startswith(("43", "44", "45")):
            notes.append("no python-run block")
        for i, code in enumerate(runs):
            buf = io.StringIO()
            try:
                with contextlib.redirect_stdout(buf):
                    exec(compile(code, f"{name}#run{i}", "exec"), {"__name__": "__main__"})
            except Exception:  # noqa: BLE001
                notes.append(f"python-run #{i} failed: {traceback.format_exc().splitlines()[-1]}")
        if text.count("```") % 2:
            notes.append("unbalanced code fences")
        flag = "!!" if notes else "ok"
        bad += bool(notes)
        print(f"{flag} {name:48s} {words:5d}w  runs={len(runs)} mermaid={nm} quiz={nq}  " + "; ".join(notes))
    print(f"{bad} lesson(s) with notes")


if __name__ == "__main__":
    main()
