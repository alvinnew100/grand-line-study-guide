"""spring-track helper: sanity checks for lessons (not part of the build)."""
import glob, io, json, os, re, sys, contextlib, importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(HERE)
run_code = "--run" in sys.argv


def all_ids():
    lessons, problems = set(), set()
    for tp in glob.glob(os.path.join(SRC, "*", "track.py")):
        text = open(tp, encoding="utf-8").read()
        track = os.path.basename(os.path.dirname(tp))
        for m in re.finditer(r'"([a-z0-9-]+)"', text):
            lessons.add((track, m.group(1)))
        for pf in glob.glob(os.path.join(os.path.dirname(tp), "problems", "*.py")):
            problems.update(re.findall(r'id="([^"]+)"', open(pf, encoding="utf-8").read()))
    return lessons, problems


lessons, problems = all_ids()
spring_track = open(os.path.join(HERE, "track.py"), encoding="utf-8").read()
bad = 0
for f in sorted(glob.glob(os.path.join(HERE, "lessons", "*.md"))):
    text = open(f, encoding="utf-8").read()
    name = os.path.basename(f)
    notes = []
    words = len(text.split())
    if words < 2400:
        notes.append(f"only {words} words")
    prose = re.sub(r"```.*?```", "", text, flags=re.S)
    prose = re.sub(r"`[^`\n]+`", "", prose)
    for w in ("simply", "obviously", "just", "as you know"):
        hits = re.findall(r"\b%s\b" % w, prose, flags=re.I)
        if hits:
            notes.append(f"banned word '{w}' x{len(hits)}")
    for need in ("**Before this lesson:**", "## In plain words", "## Glossary", "> **Source:**", "```quiz", "## Summary",
                 "## Pitfalls", "## Cheat sheet", "```mermaid", "[!INTERVIEW]"):
        if need not in text:
            notes.append(f"missing {need}")
    for q in re.findall(r"```quiz\s*\n(.*?)```", text, re.S):
        try:
            qs = json.loads(q)
            if not 6 <= len(qs) <= 8:
                notes.append(f"quiz has {len(qs)} questions")
            for item in qs:
                if not (0 <= item["answer"] < len(item["options"])) or "explain" not in item:
                    notes.append("quiz item bad")
        except Exception as e:  # noqa: BLE001
            notes.append(f"quiz json: {e}")
    for track, lid in re.findall(r"\(#/lesson/([a-z0-9-]+)/([a-z0-9-]+)\)", text):
        if (track, lid) not in lessons and not (track == "spring" and ('"%s"' % lid) in spring_track):
            notes.append(f"dead lesson link {track}/{lid}")
    for pid in re.findall(r"\(#/problem/([a-z0-9-]+)\)", text):
        if pid not in problems:
            notes.append(f"dead problem link {pid}")
    if re.search(r"(?<!\\)\$", prose):
        notes.append("bare $ in prose")
    if run_code:
        for i, code in enumerate(re.findall(r"```python-run\s*\n(.*?)```", text, re.S)):
            buf = io.StringIO()
            try:
                with contextlib.redirect_stdout(buf):
                    import ast, asyncio, inspect
                    co = compile(code, f"{name}#{i}", "exec", flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
                    r = eval(co, {"__name__": "__main__"})
                    if inspect.iscoroutine(r):
                        asyncio.run(r)
            except Exception as e:  # noqa: BLE001
                notes.append(f"python-run #{i} failed: {type(e).__name__}: {e}")
    if notes:
        bad += 1
        print(name, "->", "; ".join(notes))
print("lessons with notes:", bad)
