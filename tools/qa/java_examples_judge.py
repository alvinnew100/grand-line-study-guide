"""Run every Java example in the java track that is followed by its stated output, on the judge server.

A pair is a java fence containing `static void main`, followed directly by a text fence. The example is
compiled as <ClassName>.java with a Main.java wrapper that calls ClassName.main, and stdout is compared
with the text block (trailing spaces ignored). Uses tools/build.py's judge_remote and its cache.
Usage (from study-guide/): python <this file> [lesson-filename-substring ...]
"""
import json
import pathlib
import re
import sys

sys.path.insert(0, "tools")
import build  # noqa: E402

BT = chr(96) * 3
NOFENCE = r"((?:(?!" + BT + r")[\s\S])*?)"  # block body that never crosses a fence
PAIR = re.compile(BT + r"java\r?\n" + NOFENCE + BT + r"[ \t]*\r?\n\s*" + BT + r"text\r?\n" + NOFENCE + BT)
only = sys.argv[1:]
results = {"ok": 0, "mismatch": [], "error": []}

for p in sorted(pathlib.Path("src/java/lessons").glob("*.md")):
    if only and not any(o in p.name for o in only):
        continue
    for idx, (code, expected) in enumerate(PAIR.findall(p.read_text(encoding="utf-8")), 1):
        if "static void main" not in code:
            continue
        m = re.search(r"public\s+(?:final\s+)?class\s+(\w+)", code) or re.search(r"\bclass\s+(\w+)", code)
        if not m or re.search(r"^\s*package\s", code, re.M):
            results["error"].append((p.name, idx, "no class name or has package"))
            continue
        name = m.group(1)
        files = [{"name": name + ".java", "content": code}]
        if name != "Main":
            files.append({"name": "Main.java", "content":
                          "public class Main { public static void main(String[] a) throws Exception { "
                          + name + ".main(a); } }"})
        try:
            res = build.judge_remote("java", files)
        except Exception as e:  # noqa: BLE001
            results["error"].append((p.name, idx, "judge call failed: " + str(e)[:150]))
            continue
        if res is None:
            sys.exit("no .judge-credentials")
        if res.get("compile_error"):
            results["error"].append((p.name, idx, "COMPILE: " + res.get("stderr", "")[:400]))
            continue
        got = [ln.rstrip() for ln in res.get("stdout", "").rstrip().splitlines()]
        want = [ln.rstrip() for ln in expected.rstrip().splitlines()]
        if got == want:
            results["ok"] += 1
        else:
            results["mismatch"].append({"lesson": p.name, "block": idx, "class": name, "exit": res.get("code"),
                                        "want": want[:12], "got": got[:12], "stderr": res.get("stderr", "")[:300]})

print("OK:", results["ok"], "| mismatches:", len(results["mismatch"]), "| errors:", len(results["error"]))
for e in results["error"]:
    print("ERROR", e)
for mm in results["mismatch"]:
    print("MISMATCH", json.dumps(mm, ensure_ascii=False))
