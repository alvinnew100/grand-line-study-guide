"""Check that external links with #fragments in lessons point at an anchor that exists on the page.

Fetches each distinct page once (polite: one request at a time, 0.3 s apart) and looks for
id="frag" / name="frag" (also URL-decoded). Writes anchor_results.json to the temp folder.
Usage (from study-guide/): python -I anchor_check.py
"""
import collections
import html
import json
import pathlib
import re
import sys
import time
import urllib.parse
import urllib.request

import tempfile
OUT = pathlib.Path(tempfile.gettempdir()) / "anchor_results.json"
link = re.compile(r"""(https?://[^\s)>"'`\]]+#[A-Za-z0-9_.:%~-]+)""")
pages = collections.defaultdict(set)   # url without fragment -> fragments
where = collections.defaultdict(list)  # full url -> lesson files
for p in sorted(pathlib.Path("src").glob("*/lessons/*.md")):
    for u in link.findall(p.read_text(encoding="utf-8")):
        u = u.rstrip(".,;:")
        base, frag = u.split("#", 1)
        host = urllib.parse.urlsplit(base).hostname or ""
        if host.endswith("example") or host.endswith("example.com") or host in ("localhost", "127.0.0.1"):
            continue  # placeholder URLs in teaching examples
        if not frag or frag.startswith(":~:") or frag.startswith("/"):
            continue  # text fragments and SPA routes are not element anchors
        pages[base].add(frag)
        where[u].append(f"{p.parent.parent.name}/{p.name}")
print(len(pages), "pages,", sum(len(v) for v in pages.values()), "anchors", file=sys.stderr)

res = {"ok": [], "missing": [], "fetch_error": []}
for i, (base, frags) in enumerate(sorted(pages.items())):
    try:
        req = urllib.request.Request(base, headers={"User-Agent": "Mozilla/5.0 (link checker)"})
        with urllib.request.urlopen(req, timeout=25) as r:
            body = r.read().decode("utf-8", "replace")
    except Exception as e:  # noqa: BLE001
        for f in frags:
            res["fetch_error"].append({"url": base + "#" + f, "err": str(e)[:120], "in": where[base + "#" + f]})
        continue
    ids = set(re.findall(r"""\b(?:id|name)\s*=\s*["']([^"']+)["']""", body))
    ids |= {html.unescape(x) for x in ids}
    low = {x.lower() for x in ids}
    for f in frags:
        cands = {f, urllib.parse.unquote(f)}
        hit = bool(cands & ids) or any(c.lower() in low for c in cands)
        (res["ok"] if hit else res["missing"]).append({"url": base + "#" + f, "in": where[base + "#" + f]})
    time.sleep(0.3)
    if i % 50 == 0:
        print(i, "pages done", file=sys.stderr)
OUT.write_text(json.dumps(res, indent=1), encoding="utf-8")
print("ok", len(res["ok"]), "missing", len(res["missing"]), "fetch_error", len(res["fetch_error"]))
