"""Author helper: run every ```python-run block in this track's lessons and report failures.

  python src/web-security/websec-runblocks.py [-v]
"""
import contextlib
import glob
import io
import os
import re
import sys
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
verbose = "-v" in sys.argv
bad = 0
total = 0
for path in sorted(glob.glob(os.path.join(HERE, "lessons", "*.md"))):
    text = open(path, encoding="utf-8").read()
    for index, block in enumerate(re.findall(r"```python-run\s*\n(.*?)```", text, re.S), start=1):
        total += 1
        out = io.StringIO()
        try:
            with contextlib.redirect_stdout(out):
                exec(compile(block, f"{os.path.basename(path)}#{index}", "exec"), {"__name__": "__main__"})
        except Exception:
            bad += 1
            print(f"FAIL {os.path.basename(path)} block {index}\n{traceback.format_exc()}")
            continue
        if verbose:
            print(f"--- {os.path.basename(path)} block {index}\n{out.getvalue()}")
print(f"{total} blocks, {bad} failed")
