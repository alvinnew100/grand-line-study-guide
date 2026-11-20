"""Author-side checks for the django track (not part of the site build).

  python src/django/django-track-check.py            # structure, links, banned words, word counts
  python src/django/django-track-check.py --run      # also execute every python-run block
"""
import glob, importlib.util, io, contextlib, os, re, sys, traceback

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(HERE)
BANNED = re.compile(r"\b(simply|obviously|just|as you know)\b", re.I)


def load_track(path):
    spec = importlib.util.spec_from_file_location("t" + str(abs(hash(path))), path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.TRACK


def all_lesson_ids():
    ids = {}
    for tp in glob.glob(os.path.join(SRC, "*", "track.py")):
        try:
            t = load_track(tp)
        except Exception:
            continue
        ids[t["id"]] = {l["id"] for m in t["modules"] for l in m.get("lessons", [])}
    return ids


def main():
    run = "--run" in sys.argv
    ids = all_lesson_ids()
    problems = 0
    for f in sorted(glob.glob(os.path.join(HERE, "lessons", "*.md"))):
        name = os.path.basename(f)
        text = open(f, encoding="utf-8").read()
        words = len(text.split())
        issues = []
        if words < 2400:
            issues.append(f"only {words} words")
        for needle in ("## In plain words", "> **Before this lesson:**", "## Glossary", "```quiz", "> **Source:**",
                       "[!INTERVIEW]", "## Summary", "## Cheat sheet", "```mermaid", "## Pitfalls"):
            if needle not in text:
                issues.append(f"missing {needle!r}")
        for track, lesson in re.findall(r"\(#/lesson/([\w-]+)/([\w-]+)\)", text):
            if lesson not in ids.get(track, set()):
                issues.append(f"bad link {track}/{lesson}")
        prose = re.sub(r"```.*?```", "", text, flags=re.S)
        prose = re.sub(r"`[^`\n]*`", "", prose)
        for m in BANNED.finditer(prose):
            line = prose[:m.start()].count("\n")
            ctx = prose[max(0, m.start() - 40):m.end() + 30].replace("\n", " ")
            issues.append(f"banned word {m.group(0)!r}: ...{ctx}...")
        if run:
            for i, code in enumerate(re.findall(r"```python-run\s*\n(.*?)```", text, re.S)):
                buf = io.StringIO()
                try:
                    with contextlib.redirect_stdout(buf):
                        exec(compile(code, f"{name}[{i}]", "exec"), {"__name__": "__main__"})
                except Exception:
                    issues.append(f"python-run block {i} failed: {traceback.format_exc().splitlines()[-1]}")
        if issues:
            problems += 1
            print(name, f"({words} words)")
            for it in issues:
                print("   -", it)
    print(f"{problems} lesson file(s) with issues")


if __name__ == "__main__":
    main()
