"""Author helper for the aws track: prints lessons below the 2,600-word target and missing files.

  python src/aws/aws-track-check.py
"""
import glob, importlib.util, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("t", os.path.join(HERE, "track.py"))
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
defined = set()
for f in glob.glob(os.path.join(HERE, "problems", "*.py")):
    defined.update(re.findall(r'^\s*id="([a-z0-9-]+)"', open(f, encoding="utf-8").read(), flags=re.M))
for m in getattr(mod, "ALL_MODULES", mod.TRACK["modules"]):
    for les in m["lessons"]:
        p = os.path.join(HERE, "lessons", les["file"])
        if not os.path.exists(p):
            print("  MISSING", les["file"])
            continue
        n = len(open(p, encoding="utf-8").read().split())
        if n < 2600:
            print(f"  SHORT {n:5d}  {les['file']}")
    for p in m["problems"]:
        if p not in defined:
            print("  MISSING PROBLEM", p)
