"""Check lesson wording against the source books (8-word sequence overlap).

  python tools/overlap.py                # all tracks
  python tools/overlap.py --track csapp  # one track; exit 1 if any lesson is over the limit

A lesson should share almost no 8-word sequences with a book: anything above 2% means
sentences were copied or only lightly edited and must be rewritten in original wording.
Set BOOKS_DIR to the folder holding the extracted book .txt files.
"""
import argparse, glob, os, re, sys
# Book texts (pdftotext output) live beside the repo in Prepare/books-text (not committed).
BOOKS = os.environ.get("BOOKS_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "books-text"))
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
N, LIMIT = 8, 0.02
tok = lambda t: re.findall(r"[a-z0-9']+", t.lower())


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--track"); a = ap.parse_args()
    grams = set()
    for f in glob.glob(os.path.join(BOOKS, "*.txt")):
        w = tok(open(f, encoding="utf-8", errors="ignore").read())
        grams.update(hash(tuple(w[i:i + N])) for i in range(len(w) - N + 1))
    if not grams:
        sys.exit("no book texts found in " + BOOKS)
    bad = 0
    for f in sorted(glob.glob(os.path.join(ROOT, "src", a.track or "*", "lessons", "*.md"))):
        md = re.sub(r"```.*?```", "", open(f, encoding="utf-8").read(), flags=re.S)
        w = tok(md)
        if len(w) < 200:
            continue
        g = [hash(tuple(w[i:i + N])) for i in range(len(w) - N + 1)]
        frac = sum(x in grams for x in g) / len(g)
        if frac > LIMIT:
            bad += 1
            print(f"{frac * 100:5.1f}%  {os.path.relpath(f, ROOT)}")
    print(f"{bad} lesson(s) over {LIMIT * 100:.0f}%")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
