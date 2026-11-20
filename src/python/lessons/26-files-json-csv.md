# Files, pathlib, JSON and CSV

Sooner or later every program reads or writes something: a configuration file, a log, a CSV export, a JSON API payload. Python's tools for this are small and consistent — `open()` for file objects, `pathlib` for paths, `json` and `csv` for the two most common text formats — but they have sharp edges around encodings, newlines, and resource handling. This lesson covers the tools and the edges.

## Opening files

```python
with open("notes.txt", "w", encoding="utf-8") as f:
    f.write("first line\n")
```

`open(path, mode, encoding=...)` returns a **file object**. Always use it in a `with` block so it is closed (and its buffer flushed) even if an exception occurs.

| Mode | Meaning |
|---|---|
| `"r"` | read text (default); `FileNotFoundError` if missing |
| `"w"` | write text; **truncates** an existing file, creates if missing |
| `"a"` | append to the end; creates if missing |
| `"x"` | exclusive create; `FileExistsError` if it already exists |
| `"r+"` | read and write without truncating |
| add `"b"` | binary mode: `"rb"`, `"wb"` — you get/give `bytes`, no decoding |

**Always pass `encoding="utf-8"` in text mode.** Without it, Python uses a platform-dependent default (historically cp1252 on Windows), so a file that works on your Mac produces `UnicodeDecodeError` or mojibake on a colleague's PC. (UTF-8 becomes the default in Python 3.15.)

```python-run
import os, tempfile
path = os.path.join(tempfile.gettempdir(), "study_notes.txt")

with open(path, "w", encoding="utf-8") as f:
    f.write("first line\n")
    f.writelines(["second line\n", "third: héllo\n"])     # no newlines added for you
    print("fourth via print", 42, file=f)

with open(path, encoding="utf-8") as f:
    print(repr(f.read()))               # whole file as one string

with open(path, encoding="utf-8") as f:
    for number, line in enumerate(f, 1):                    # lazy, line by line
        print(number, line.rstrip("\n"))

with open(path, "a", encoding="utf-8") as f:
    f.write("appended\n")
with open(path, encoding="utf-8") as f:
    lines = f.read().splitlines()       # list of lines without newline characters
print(len(lines), lines[-1])

with open(path, "rb") as f:
    print(f.read(20))                   # bytes: note the UTF-8 encoding of é
os.remove(path)
```

### Reading methods

| Call | Returns | Notes |
|---|---|---|
| `f.read()` | the whole file | fine for small files |
| `f.read(n)` | up to `n` characters/bytes | chunked reading |
| `f.readline()` | one line including `\n`; `""` at EOF | |
| `f.readlines()` | list of all lines | loads everything |
| `for line in f` | lines lazily | **preferred** — constant memory |

A file object is an iterator over its lines, so a 50 GB log can be processed with a few kilobytes of memory. Lines keep their trailing `"\n"`; strip it with `line.rstrip("\n")` (or `.strip()` for all whitespace).

Files have a **position**: after `read()` you are at the end, and a second `read()` returns `""`. `f.seek(0)` rewinds; `f.tell()` reports the position.

### Text versus binary

Text mode decodes bytes to `str` using the encoding and translates newlines (`\r\n` → `\n` on reading). Binary mode gives raw `bytes` — use it for images, PDFs, compressed data, or when hashing/copying. `str.encode()` and `bytes.decode()` convert between the two worlds.

### In-memory files

`io.StringIO` and `io.BytesIO` are file-like objects backed by memory — perfect for tests and for APIs that insist on a file:

```python-run
import io
buf = io.StringIO()
buf.write("alpha\nbeta\n")
print("gamma", file=buf)
buf.seek(0)
print([line.strip() for line in buf], repr(buf.getvalue()))
```

## pathlib

`pathlib.Path` represents filesystem paths as objects, replacing most of `os.path`, `glob` and parts of `os`/`shutil` with readable methods. Paths are joined with the `/` operator, which works on every OS.

```python-run
from pathlib import Path
import tempfile

p = Path("project") / "data" / "sales.2026.csv"
print(p, "|", p.name, p.stem, p.suffix, p.suffixes, p.parent, p.parts)
print(p.with_suffix(".json").name, p.with_name("costs.csv"), p.is_absolute())

root = Path(tempfile.mkdtemp())
(root / "logs" / "2026").mkdir(parents=True, exist_ok=True)
(root / "logs" / "2026" / "jan.log").write_text("ok\nerror: disk\n", encoding="utf-8")
(root / "logs" / "2026" / "feb.log").write_text("ok\n", encoding="utf-8")
(root / "readme.md").write_text("# hi\n", encoding="utf-8")

print(sorted(x.name for x in root.iterdir()))                      # direct children
print(sorted(str(x.relative_to(root)) for x in root.rglob("*.log")))   # recursive glob
log = root / "logs" / "2026" / "jan.log"
print(log.exists(), log.is_file(), log.parent.is_dir(), log.stat().st_size, "bytes")
print(log.read_text(encoding="utf-8").splitlines())

with log.open("a", encoding="utf-8") as f:                          # Path.open works like open()
    f.write("recovered\n")
log.rename(log.with_name("january.log"))
print(sorted(x.name for x in (root / "logs" / "2026").glob("*")))

import shutil
shutil.rmtree(root)                                                 # delete the whole tree
print(root.exists())
```

| Task | pathlib |
|---|---|
| current dir / home | `Path.cwd()`, `Path.home()` |
| this file's folder | `Path(__file__).resolve().parent` |
| join | `base / "sub" / "file.txt"` |
| exists / type | `p.exists()`, `p.is_file()`, `p.is_dir()` |
| read / write whole file | `p.read_text(encoding=...)`, `p.write_text(...)`, `p.read_bytes()`, `p.write_bytes()` |
| list / search | `p.iterdir()`, `p.glob("*.py")`, `p.rglob("*.py")` |
| create dirs | `p.mkdir(parents=True, exist_ok=True)` |
| delete | `p.unlink(missing_ok=True)`, `p.rmdir()` (empty), `shutil.rmtree(p)` |
| copy / move | `shutil.copy2(src, dst)`, `shutil.move(src, dst)`, `p.rename(new)` |

> [!TIP]
> Build paths relative to the code, not the current working directory: `DATA = Path(__file__).resolve().parent / "data"`. Scripts then work no matter where they're launched from.

`tempfile.TemporaryDirectory()` and `NamedTemporaryFile()` create scratch space that cleans itself up; pytest offers the `tmp_path` fixture for the same purpose.

## JSON

JSON is the lingua franca of web APIs. The `json` module maps between JSON text and Python objects:

| JSON | Python |
|---|---|
| object | `dict` (keys always `str`) |
| array | `list` |
| string | `str` |
| number | `int` or `float` |
| `true` / `false` | `True` / `False` |
| `null` | `None` |

Four functions — remember "**s** for string":

- `json.dumps(obj)` → JSON **s**tring; `json.loads(text)` → Python object.
- `json.dump(obj, file)` / `json.load(file)` → the same, with file objects.

```python-run
import json

order = {"id": 17, "items": [{"sku": "A1", "qty": 2}], "paid": True, "note": None, "total": 12.5, "café": "ü"}
text = json.dumps(order)
print(text)
print(json.dumps(order, indent=2, sort_keys=True, ensure_ascii=False))
back = json.loads(text)
print(back == order, type(back["items"]), back["note"])

# round-trip caveats
print(json.loads(json.dumps({1: "int key", (2): "x"})))      # keys become strings
print(json.loads(json.dumps((1, 2))))                        # tuples become lists
try:
    json.loads("{'single': 'quotes'}")                       # JSON requires double quotes
except json.JSONDecodeError as e:
    print("JSONDecodeError:", e)
```

### Types JSON doesn't know

`datetime`, `Decimal`, `set`, `bytes`, dataclasses and custom classes raise `TypeError: Object of type ... is not JSON serializable`. Supply a `default` function for encoding and, if needed, an `object_hook` for decoding:

```python-run
import json
from dataclasses import dataclass, asdict, is_dataclass
from datetime import datetime, date
from decimal import Decimal

@dataclass
class Order:
    id: int
    placed: datetime
    total: Decimal
    tags: set

def encode(obj):
    if is_dataclass(obj):
        return asdict(obj)
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return str(obj)                 # keep exactness; float would lose it
    if isinstance(obj, set):
        return sorted(obj)
    raise TypeError(f"cannot serialise {type(obj).__name__}")

o = Order(1, datetime(2026, 1, 2, 10, 30), Decimal("19.99"), {"gift", "rush"})
text = json.dumps(o, default=encode)
print(text)

def decode(d):
    if "placed" in d:
        d["placed"] = datetime.fromisoformat(d["placed"])
        d["total"] = Decimal(d["total"])
    return d
print(json.loads(text, object_hook=decode))
```

In real services, Pydantic models do this conversion and validation for you. Notes: never use `eval` to parse JSON-like text; for one-JSON-object-per-line files (**JSON Lines**), loop over the file and `json.loads` each line; and `pickle` is Python-only and **unsafe on untrusted data** (it can execute code) — prefer JSON for interchange.

## CSV

CSV looks trivial — "just split on commas" — until a field contains a comma, a quote or a newline. The `csv` module handles the quoting rules.

```python-run
import csv, io

text = '''name,age,city,quote
Ana,31,Lisbon,"Hello, world"
Ben,25,"New
York","She said ""hi"""
'''
print("naive split:", text.splitlines()[1].split(","))       # wrong: 5 fields

for row in csv.reader(io.StringIO(text, newline="")):
    print(row)

for row in csv.DictReader(io.StringIO(text, newline="")):    # header row -> dict keys
    print(row["name"], int(row["age"]) + 1, repr(row["city"]))
```

Every value read from a CSV is a **string** — convert types yourself.

Writing:

```python-run
import csv, io

rows = [{"name": "Ana", "score": 91.5, "note": "top, again"}, {"name": "Ben", "score": 78, "note": 'said "ok"'}]
out = io.StringIO(newline="")
writer = csv.DictWriter(out, fieldnames=["name", "score", "note"])
writer.writeheader()
writer.writerows(rows)
print(out.getvalue())

out2 = io.StringIO(newline="")
w = csv.writer(out2, delimiter="\t")                        # TSV
w.writerow(["id", "value"]); w.writerows([[1, "a"], [2, "b"]])
print(repr(out2.getvalue()))
```

With real files, open them with **`newline=""`** (the csv module does its own newline handling; without it you get blank lines between rows on Windows) and an explicit encoding:

```python
with open("people.csv", newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        ...

with open("out.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerows(rows)
```

Files exported from Excel often start with a byte-order mark; read them with `encoding="utf-8-sig"`. For heavy analysis you'd use pandas (`pd.read_csv`), but `csv` is dependency-free and streams row by row.

## Worked example: a small ETL pipeline

Read a CSV, clean and aggregate it, and write a JSON report — streaming, with proper encodings:

```python-run
import csv, json, tempfile
from collections import defaultdict
from pathlib import Path

work = Path(tempfile.mkdtemp())
src, dst = work / "sales.csv", work / "report.json"
src.write_text(
    "region,product,units,price\n"
    "north,cola,10,1.50\n"
    "south,cola,4,1.50\n"
    "north,sake,,9.00\n"            # missing units
    "north,meat,3,12.25\n"
    "south,meat,x,12.25\n",         # bad units
    encoding="utf-8",
)

def read_sales(path):
    with path.open(newline="", encoding="utf-8") as f:
        for line_no, row in enumerate(csv.DictReader(f), start=2):
            try:
                yield row["region"], int(row["units"]) * float(row["price"])
            except ValueError:
                print(f"skipping line {line_no}: {row}")

totals = defaultdict(float)
for region, revenue in read_sales(src):
    totals[region] += revenue

with dst.open("w", encoding="utf-8") as f:
    json.dump({"revenue_by_region": totals, "regions": sorted(totals)}, f, indent=2)
print(dst.read_text(encoding="utf-8"))
```

The generator `read_sales` keeps memory flat and isolates parsing/validation from aggregation.

> [!INTERVIEW]
> Typical questions: "How do you read a huge file?" — iterate line by line (`for line in f`) or in fixed-size chunks; never `read()` it all. "Why `with open(...)`?" — guarantees the file is closed/flushed even on exceptions. "`json.dump` vs `json.dumps`?" — file vs string. "Why not `line.split(',')` for CSV?" — quoted fields may contain commas, quotes and newlines. "Text vs binary mode?" — `str` with decoding and newline translation vs raw `bytes`.

## Persisting program state: load-or-default

Small programs often need to remember something between runs — a user's name, preferences, a high score. The dependable pattern has three parts: **load** what was saved or fall back to defaults, **work** with a plain dictionary in memory, and **save** when something changes. Keeping each part in its own function makes all three testable.

```python-run
import json, tempfile
from pathlib import Path

DEFAULTS = {"name": None, "theme": "light", "launches": 0}

def load_settings(path):
    """Return saved settings merged over the defaults; never raises for a missing or damaged file."""
    try:
        saved = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        saved = {}
    if not isinstance(saved, dict):
        saved = {}
    return {**DEFAULTS, **saved}

def save_settings(path, settings):
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(settings, indent=2), encoding="utf-8")
    temporary.replace(path)               # swap in the finished file in one step

path = Path(tempfile.mkdtemp()) / "settings.json"
for run in range(3):                      # three 'runs' of the program
    settings = load_settings(path)
    settings["launches"] += 1
    if settings["name"] is None:
        settings["name"] = "Dana"         # would come from input() on the first run
    save_settings(path, settings)
    print(f"run {run + 1}: {settings}")

path.write_text("{ this is not json", encoding="utf-8")
print("after corruption:", load_settings(path))
```

Three details make it robust. Merging the saved values *over* a dictionary of defaults means a file written by an older version of the program, lacking newer keys, still loads. Catching `JSONDecodeError` as well as `FileNotFoundError` covers a half-written or hand-edited file. And writing to a temporary file that is then renamed means a crash in the middle of saving cannot leave a truncated settings file behind. The introductory treatment of reading, writing and JSON is in the "Start here" lesson *Files, errors and tests*.

## Pitfalls recap

- Omitting `encoding="utf-8"` (platform-dependent behaviour).
- `"w"` mode silently truncates existing files.
- Forgetting `newline=""` when opening CSV files.
- Calling `f.read()` twice without `seek(0)`.
- Assuming CSV values are numbers — they're strings.
- JSON keys become strings; tuples become lists; `NaN`/`Infinity` aren't valid strict JSON.
- Building paths with string concatenation and hard-coded `\` or `/`; relative paths depending on the current directory.
- Unpickling untrusted data.

## Summary

Use `with open(..., encoding="utf-8")` and iterate lazily; use `pathlib.Path` for every path operation; use `json` (`dump/load` for files, `dumps/loads` for strings, `default=` for extra types) and `csv` (`reader`/`DictReader`, `writer`/`DictWriter`, `newline=""`) instead of hand-rolled parsing.

```quiz
[
  {"q": "What does opening an existing file with mode 'w' do?", "options": ["Appends to it", "Truncates it to empty before writing", "Raises FileExistsError", "Opens read-only"], "answer": 1,
   "explain": "'w' creates or truncates. Use 'a' to append or 'x' to fail if the file exists."},
  {"q": "Most memory-efficient way to process a 20 GB text file?", "options": ["f.read().splitlines()", "f.readlines()", "for line in f:", "list(f)"], "answer": 2,
   "explain": "Iterating the file object yields one line at a time; the others load everything."},
  {"q": "Which function converts a Python dict to a JSON string?", "options": ["json.dump", "json.dumps", "json.load", "json.loads"], "answer": 1,
   "explain": "dumps = dump to string; dump writes to a file object."},
  {"q": "`json.loads(json.dumps({1: 'a'}))` returns:", "options": ["{1: 'a'}", "{'1': 'a'}", "[[1, 'a']]", "TypeError"], "answer": 1,
   "explain": "JSON object keys are always strings, so the int key is converted and stays a string on the way back."},
  {"q": "Why open CSV files with newline=''?", "options": ["To strip whitespace", "The csv module handles line endings itself; otherwise you may get blank rows or broken embedded newlines", "It is faster", "To enable Unicode"], "answer": 1,
   "explain": "Python's universal-newline translation interferes with the csv module's own handling."},
  {"q": "With pathlib, how do you build 'data/raw/x.csv' portably?", "options": ["'data' + '\\\\raw\\\\x.csv'", "Path('data') / 'raw' / 'x.csv'", "os.join('data','raw','x.csv')", "Path('data', sep='/')"], "answer": 1,
   "explain": "The / operator joins path components using the right separator for the OS."},
  {"q": "What type are the values produced by csv.DictReader?", "options": ["Inferred ints/floats", "Always strings", "bytes", "Depends on the header"], "answer": 1,
   "explain": "The csv module performs no type conversion; convert explicitly."},
  {"q": "Why pass encoding='utf-8' explicitly to open()?", "options": ["It is required syntax", "The default encoding depends on the platform, causing bugs across machines", "It makes files smaller", "It enables binary mode"], "answer": 1,
   "explain": "Relying on the locale default is a classic 'works on my machine' problem."}
]
```

> **Source:** Goodrich, Tamassia & Goldwasser, *Data Structures and Algorithms in Python*, §1.6 (Simple Input and Output: console and files); Python docs, *Tutorial* ch. 7 "Input and Output", *Library Reference* `pathlib`, `json`, `csv`, `io`.
