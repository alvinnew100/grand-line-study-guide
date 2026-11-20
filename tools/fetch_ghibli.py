"""Download the official stills Studio Ghibli publishes at https://www.ghibli.jp/works/
into <Prepare>/ghibli-stills/<work>/ (originals, not committed)."""
import re, time, sys, urllib.request
from pathlib import Path
OUT = Path(__file__).resolve().parents[2] / "ghibli-stills"
UA = {"User-Agent": "Mozilla/5.0 (study-guide personal download)"}
def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read()
index = get("https://www.ghibli.jp/works/").decode("utf-8", "ignore")
works = sorted(set(re.findall(r"works/([a-z0-9-]+)/\"", index)))
total = 0
for w in works:
    try:
        page = get(f"https://www.ghibli.jp/works/{w}/").decode("utf-8", "ignore")
    except Exception as e:
        print(w, "page failed", e, flush=True); continue
    imgs = sorted(set(u for u in re.findall(r"https://www\.ghibli\.jp/gallery/[A-Za-z0-9_-]+\.jpg", page) if "thumb-" not in u))
    d = OUT / w; d.mkdir(parents=True, exist_ok=True)
    for u in imgs:
        f = d / u.rsplit("/", 1)[1]
        if f.exists() and f.stat().st_size > 10000: total += 1; continue
        try:
            f.write_bytes(get(u)); total += 1; time.sleep(0.15)
        except Exception as e:
            print("fail", u, e, flush=True)
    print(w, len(imgs), flush=True)
print("TOTAL", total)
