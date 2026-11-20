"""Build the study guide data from src/ into docs/data/.

Usage:
  python tools/build.py              # build every track
  python tools/build.py --track dsa  # build/validate one track only

For each track src/<track>/track.py defines TRACK (see AUTHORING.md).
Problems live in src/<track>/problems/*.py, each defining PROBLEMS = [dict(...), ...].
Lessons are Markdown files in src/<track>/lessons/.

Expected outputs are never hand-written: the reference `solution` is run on every
test's args with the same harness the browser uses, so tests are always consistent.
"""
import argparse
import importlib.util
import json
import re
import shutil
import sqlite3
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
OUT = ROOT / "docs" / "data"
sys.path.insert(0, str(ROOT / "docs" / "assets" / "judge"))
import harness  # noqa: E402

REQUIRED_PROBLEM = ["id", "title", "difficulty", "description", "starter", "solution", "tests"]
DIFFS = {"Easy", "Medium", "Hard"}
errors = []


def err(msg):
    errors.append(msg)
    print("  ERROR:", msg)


def fix_json_backslashes(s):
    """Make LaTeX-in-JSON forgiving: '\\frac' written as '\frac' would become a form feed.
    Keep only real JSON escapes; double every other backslash. Mirrors fixJson() in app.js."""
    out, i, n = [], 0, len(s)
    while i < n:
        c = s[i]
        if c != "\\":
            out.append(c)
            i += 1
            continue
        nxt = s[i + 1] if i + 1 < n else ""
        after = s[i + 2] if i + 2 < n else ""
        if nxt == "\\":
            out.append("\\\\")
            i += 2
        elif nxt in '"/':
            out.append("\\" + nxt)
            i += 2
        elif nxt == "u" and re.fullmatch(r"[0-9a-fA-F]{4}", s[i + 2:i + 6] or ""):
            out.append(s[i:i + 6])
            i += 6
        elif nxt in "bfnrt" and not after.isalpha():
            out.append("\\" + nxt)
            i += 2
        else:
            out.append("\\\\")
            i += 1
    return "".join(out)


def load_py(path, var):
    spec = importlib.util.spec_from_file_location(f"m_{path.stem}_{abs(hash(str(path)))}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return getattr(mod, var)


def sql_rows(schema_sql, query):
    con = sqlite3.connect(":memory:")
    con.executescript(schema_sql)
    cur = con.execute(query)
    cols = [d[0] for d in cur.description] if cur.description else []
    rows = [list(r) for r in cur.fetchall()]
    con.close()
    return cols, rows


def build_sql_problem(p, track_dir):
    ds = p.get("dataset")
    ds_path = track_dir / "datasets" / f"{ds}.sql"
    if not ds_path.exists():
        err(f"{p['id']}: dataset {ds_path} missing")
        return None
    try:
        cols, rows = sql_rows(ds_path.read_text(encoding="utf-8"), p["solution"])
    except Exception as e:  # noqa: BLE001
        err(f"{p['id']}: reference SQL failed: {e}")
        return None
    if not rows:
        print(f"  warn: {p['id']} reference query returns 0 rows")
    return {
        **{k: v for k, v in p.items() if k not in ("tests",)},
        "kind": "sql",
        "expected": {"columns": cols, "rows": rows},
        "ordered": p.get("ordered", False),
    }


def build_code_problem(p):
    spec = {
        k: p.get(k)
        for k in ("kind", "entry", "arg_types", "return_type", "compare", "tolerance", "inplace_arg", "checker")
        if p.get(k) is not None
    }
    spec.setdefault("kind", "function")
    if "entry" not in spec:
        err(f"{p['id']}: missing entry")
        return None
    tests = []
    t0 = time.perf_counter()
    for i, args in enumerate(p["tests"]):
        args = list(args)
        got, out, e, ms = harness.execute(p["solution"], spec, args)
        if e:
            err(f"{p['id']}: reference solution failed on test {i}: {e.splitlines()[-1]}")
            return None
        tests.append({"args": args, "expected": got, "ref_ms": round(ms, 3)})
    # starter must at least compile and expose the entry
    try:
        compile(p["starter"], "starter.py", "exec")
    except SyntaxError as e:
        err(f"{p['id']}: starter has a syntax error: {e}")
    if p["starter"].strip() == p["solution"].strip():
        err(f"{p['id']}: starter equals solution")
    # optional wrong answers must FAIL at least one test (guards weak test suites)
    for j, bad in enumerate(p.get("wrong_solutions", [])):
        res = harness.run_tests(bad, spec, [{"args": t["args"], "expected": t["expected"]} for t in tests])
        if res["passed"] == res["total"]:
            err(f"{p['id']}: wrong_solutions[{j}] passes all tests - add stronger tests")
    elapsed = time.perf_counter() - t0
    if elapsed > 5:
        print(f"  warn: {p['id']} reference took {elapsed:.1f}s over all tests (browser will be slower)")
    examples = p.get("examples", min(3, len(tests)))
    out = {k: v for k, v in p.items() if k not in ("tests", "wrong_solutions")}
    out.update(spec=spec, tests=tests, examples=examples)
    size = len(json.dumps(tests))
    if size > 400_000:
        err(f"{p['id']}: tests JSON is {size // 1000} KB; keep under 400 KB")
    return out


def build_track(track_dir):
    tid = track_dir.name
    print(f"[{tid}]")
    track = load_py(track_dir / "track.py", "TRACK")
    if track.get("id") != tid:
        err(f"{tid}: TRACK['id'] must equal folder name")
    problems = {}
    pdir = track_dir / "problems"
    for f in sorted(pdir.glob("*.py")) if pdir.exists() else []:
        try:
            plist = load_py(f, "PROBLEMS")
        except Exception as e:  # noqa: BLE001
            err(f"{f.name}: failed to import: {e}")
            continue
        for p in plist:
            missing = [k for k in REQUIRED_PROBLEM if k not in p and not (k == "tests" and p.get("kind") == "sql")]
            if missing:
                err(f"{f.name}:{p.get('id')}: missing {missing}")
                continue
            if p["difficulty"] not in DIFFS:
                err(f"{p['id']}: difficulty must be one of {DIFFS}")
            if p["id"] in problems:
                err(f"{p['id']}: duplicate problem id")
            built = build_sql_problem(p, track_dir) if p.get("kind") == "sql" else build_code_problem(p)
            if built:
                built["track"] = tid
                problems[p["id"]] = built
    # lessons
    ldir = track_dir / "lessons"
    out_lessons = OUT / "lessons" / tid
    out_lessons.mkdir(parents=True, exist_ok=True)
    for old in out_lessons.glob("*.md"):  # OneDrive can lock dirs; delete files, keep dir
        try:
            old.unlink()
        except OSError:
            pass
    referenced = set()
    words = 0
    for m in track["modules"]:
        for les in m.get("lessons", []):
            f = ldir / les["file"]
            if not f.exists():
                err(f"{tid}/{m['id']}: lesson file {les['file']} missing")
                continue
            text = f.read_text(encoding="utf-8")
            words += len(text.split())
            les["words"] = len(text.split())
            for q in re.findall(r"```quiz\s*\n(.*?)```", text, re.S):
                try:
                    qs = json.loads(fix_json_backslashes(q))
                    for item in qs if isinstance(qs, list) else [qs]:
                        assert "q" in item and "options" in item and "answer" in item
                except Exception as e:  # noqa: BLE001
                    err(f"{les['file']}: bad quiz block ({e})")
            shutil.copy(f, out_lessons / les["file"])
        for pid in m.get("problems", []):
            referenced.add(pid)
            if pid not in problems:
                err(f"{tid}/{m['id']}: problem '{pid}' listed but not defined")
    for pid in problems:
        if pid not in referenced:
            err(f"{tid}: problem '{pid}' defined but not listed in any module")
    # datasets for SQL
    ds_dir = track_dir / "datasets"
    if ds_dir.exists():
        od = OUT / "datasets"
        od.mkdir(parents=True, exist_ok=True)
        for f in ds_dir.glob("*.sql"):
            try:
                sql_rows(f.read_text(encoding="utf-8"), "select 1")
            except Exception as e:  # noqa: BLE001
                err(f"dataset {f.name} failed to load: {e}")
            shutil.copy(f, od / f.name)
    meta = {
        **track,
        "problemIndex": {
            pid: {k: p.get(k) for k in ("title", "difficulty", "pattern", "leetcode", "neetcode", "kind")}
            for pid, p in problems.items()
        },
        "words": words,
    }
    (OUT / "tracks").mkdir(parents=True, exist_ok=True)
    (OUT / "problems").mkdir(parents=True, exist_ok=True)
    (OUT / "tracks" / f"{tid}.json").write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")
    (OUT / "problems" / f"{tid}.json").write_text(json.dumps(problems, ensure_ascii=False), encoding="utf-8")
    print(f"  {len(track['modules'])} modules, {sum(len(m.get('lessons', [])) for m in track['modules'])} lessons, "
          f"{len(problems)} problems, {words} words")
    return meta


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--track")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    dirs = sorted(d for d in SRC.iterdir() if (d / "track.py").exists())
    if a.track:
        dirs = [d for d in dirs if d.name == a.track]
        if not dirs:
            sys.exit(f"no track {a.track}")
    for d in dirs:
        try:
            build_track(d)
        except Exception as e:  # noqa: BLE001
            err(f"{d.name}: {type(e).__name__}: {e}")
    # global index (always from all tracks present on disk)
    order = load_py(SRC / "order.py", "ORDER") if (SRC / "order.py").exists() else []
    metas = []
    for f in (OUT / "tracks").glob("*.json"):
        m = json.loads(f.read_text(encoding="utf-8"))
        metas.append({k: m.get(k) for k in ("id", "title", "icon", "blurb", "color", "sources", "words")} | {
            "modules": len(m["modules"]),
            "lessons": sum(len(x.get("lessons", [])) for x in m["modules"]),
            "problems": len(m["problemIndex"]),
        })
    metas.sort(key=lambda m: order.index(m["id"]) if m["id"] in order else 99)
    (OUT / "index.json").write_text(json.dumps(metas, ensure_ascii=False, indent=1), encoding="utf-8")
    # cache-bust static assets so returning visitors get the new app/css
    idx = ROOT / "docs" / "index.html"
    if idx.exists():
        ver = time.strftime("%Y%m%d%H%M%S")
        html = idx.read_text(encoding="utf-8")
        html = re.sub(r"(assets/(?:app|widgets)\.js|assets/style\.css)(\?v=\w+)?", rf"\g<1>?v={ver}", html)
        idx.write_text(html, encoding="utf-8")
    if errors:
        print(f"\n{len(errors)} error(s).")
        sys.exit(1)
    print("\nOK")


if __name__ == "__main__":
    main()
