"""Turn the downloaded originals (../ghibli-stills) into web-sized WebP files and a manifest.
Output: docs/assets/ghibli/<work>/<name>.webp (1024w), .../t/<name>.webp (420w), manifest.json"""
import html, json, re, urllib.request
from pathlib import Path
from PIL import Image
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT.parent / "ghibli-stills"
OUT = ROOT / "docs" / "assets" / "ghibli"
req = urllib.request.Request("https://www.ghibli.jp/works/", headers={"User-Agent": "Mozilla/5.0"})
index = urllib.request.urlopen(req, timeout=60).read().decode("utf-8", "ignore")
meta = {}
for block in index.split('itemtype="http://schema.org/Movie"')[1:]:
    m = re.search(r"works/([a-z0-9-]+)/", block)
    if not m: continue
    wid = m.group(1)
    g = lambda pat: (re.search(pat, block, re.S) or [None, ""])[1]
    meta[wid] = dict(
        id=wid, title=html.unescape(g(r'<p class="mb15">([^<]+)</p>')).strip(),
        title_ja=html.unescape(g(r'itemprop="name">([^<]+)</span>')).strip(),
        year=g(r"（(\d{4})）"), copyright="© " + html.unescape(g(r"&copy;\s*([^<]+)</p>")).strip(),
        url=f"https://www.ghibli.jp/works/{wid}/")
works = []
for wid, m in meta.items():
    files = []
    d = SRC / wid
    for f in sorted(d.glob("*.jpg")) if d.exists() else []:
        o = OUT / wid / f"{f.stem}.webp"; t = OUT / wid / "t" / f"{f.stem}.webp"
        try:
            if not (o.exists() and t.exists()):
                im = Image.open(f).convert("RGB")
                t.parent.mkdir(parents=True, exist_ok=True)
                a = im.copy(); a.thumbnail((1024, 1024)); a.save(o, "WEBP", quality=70, method=5)
                b = im.copy(); b.thumbnail((420, 420)); b.save(t, "WEBP", quality=62, method=5)
            files.append(f.stem)
        except Exception as e:
            print("skip", f, e)
    m["files"] = files
    works.append(m)
works.sort(key=lambda w: w["year"])
(OUT / "manifest.json").write_text(json.dumps({
    "source": "https://www.ghibli.jp/works/",
    "terms": "Studio Ghibli publishes these stills for free use 'within the bounds of common sense' (常識の範囲でご自由にお使いください).",
    "works": works}, ensure_ascii=False), encoding="utf-8")
print(len(works), "works,", sum(len(w["files"]) for w in works), "stills")
