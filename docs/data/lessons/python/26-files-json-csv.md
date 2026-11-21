# Files, pathlib, JSON and CSV

> **Before this lesson:** you should have read and written a first text file as in [Files, errors and tests: programs you can rely on](#/lesson/python/py-start-files-tests). You need strings versus bytes from [Lists, tuples and strings](#/lesson/python/py-sequences), dictionaries from [Dictionaries and sets](#/lesson/python/py-dicts-sets), the `with` statement from [Context managers and contextlib](#/lesson/python/py-context-managers), generators from [Generators and yield from](#/lesson/python/py-generators) and exceptions from [Exceptions](#/lesson/python/py-exceptions).

## In plain words

Everything a program holds in its variables disappears when the program ends. To keep information, or to exchange it with other programs, it has to be written to a **file**: a named piece of data on the disk. Sooner or later every program reads or writes one: a settings file, a log, an export from a spreadsheet, data received from a web service.

Four tools cover nearly all of this work:

- `open()` gives you a **file object**, your handle for reading or writing one file. Think of borrowing a book from a library desk: you ask for it, use it, and hand it back. Handing it back (closing the file) is the step people forget, and the `with` statement does it for you.
- `pathlib` deals with **paths**, the addresses of files and folders, such as `reports/2026/sales.csv`.
- **JSON** is a text format for nested data (lists inside dictionaries inside lists). It is the common language in which web services exchange data.
- **CSV** ("comma-separated values") is a text format for tables: one line per row, commas between the columns. Every spreadsheet program can read and write it.

Why this matters for a job: reading a file, transforming the data and writing a result is the single most common shape of a small work task, and it is a frequent take-home interview exercise. The tools are small and consistent, but they have sharp edges (text encodings, line endings, files left open) that cause real bugs. This lesson covers the tools and the edges.

## Opening files

The basic pattern for working with a file looks like this:

```python
with open("notes.txt", "w", encoding="utf-8") as f:
    f.write("first line\n")
```

`open(path, mode, encoding=...)` returns a file object. The first argument says which file, the second (the **mode**) says what you intend to do with it, and `encoding` says how text is converted to bytes, explained in a moment. Always open files in a `with` block. When the block ends the file is closed, even if an error occurred inside. Closing matters because Python collects written text in memory (a **buffer**) and only puts it on the disk in batches; closing writes out whatever is still waiting, which is called **flushing**.

| Mode | Meaning |
|---|---|
| `"r"` | read text (default); `FileNotFoundError` if missing |
| `"w"` | write text; **truncates** an existing file, creates if missing |
| `"a"` | append to the end; creates if missing |
| `"x"` | exclusive create; `FileExistsError` if it already exists |
| `"r+"` | read and write without truncating |
| add `"b"` | binary mode: `"rb"`, `"wb"` — you get/give `bytes`, no decoding |

A file on disk contains bytes, not characters. An **encoding** is the rule for turning characters into bytes and back, and **UTF-8** is the one that can represent every character and that almost everything uses today. **Always pass `encoding="utf-8"` in text mode.** If you leave it out, Python uses a default that depends on the computer (on Windows, traditionally an older encoding called cp1252). A file that works on your Mac then fails with `UnicodeDecodeError` on a colleague's PC, or shows garbled characters. (UTF-8 becomes the default in Python 3.15.)

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

**Reading this code block by block**

- The first `with` opens the file for writing. `f.write(...)` writes a string exactly as given, so each line break `\n` has to be included. `writelines` writes each string of a list, also without adding line breaks. `print(..., file=f)` prints into the file and does add one.
- The second block reads the whole file into one string with `f.read()`; `repr` makes the `\n` characters visible.
- The third block loops over the file object, which hands out one line at a time. `enumerate(f, 1)` numbers them from 1, and `rstrip("\n")` removes the line break before printing.
- The fourth block opens with mode `"a"` and appends a line; reading again and calling `splitlines()` gives a list of five lines without line breaks.
- The fifth block opens in binary mode (`"rb"`) and reads the first 20 bytes. The result starts with `b'...'` and is raw bytes; nothing is decoded.
- `os.remove(path)` deletes the file.

### Reading methods

| Call | Returns | Notes |
|---|---|---|
| `f.read()` | the whole file | fine for small files |
| `f.read(n)` | up to `n` characters/bytes | chunked reading |
| `f.readline()` | one line including `\n`; `""` at EOF | |
| `f.readlines()` | list of all lines | loads everything |
| `for line in f` | lines lazily | **preferred** — constant memory |

A file object is an iterator over its lines, which is why the `for` loop is preferred: a 50 GB log can be processed with a few kilobytes of memory. Each line keeps its trailing `"\n"`; remove it with `line.rstrip("\n")`, or with `.strip()` to remove all surrounding whitespace.

An open file has a **position**, like a bookmark. After `read()` the position is at the end, so a second `read()` returns the empty string `""`. `f.seek(0)` moves the position back to the start, and `f.tell()` reports where it is.

### Text versus binary

In **text mode** Python decodes the file's bytes into `str` using the encoding, and also tidies up line endings: Windows marks the end of a line with two characters, `\r\n`, which are turned into the single `\n` when reading. In **binary mode** you receive the raw `bytes` untouched. Use binary mode for images, PDFs and compressed data, and when copying a file or computing a checksum of it. `str.encode()` and `bytes.decode()` convert between the two.

### In-memory files

`io.StringIO` and `io.BytesIO` are objects that behave like open files but keep their contents in memory. They are ideal in tests, and for functions that insist on being given a file:

```python-run
import io
buf = io.StringIO()
buf.write("alpha\nbeta\n")
print("gamma", file=buf)
buf.seek(0)
print([line.strip() for line in buf], repr(buf.getvalue()))
```

The buffer is written to in two ways, rewound with `seek(0)`, and read line by line like a file. `getvalue()` returns everything it holds as one string.

## pathlib

A **path** is the address of a file or folder. Paths are often handled as plain strings, which goes wrong easily, not least because Windows separates folders with `\` and everything else with `/`. `pathlib.Path` represents a path as an object with readable methods, and replaces most of the older `os.path` and `glob` functions. Paths are joined with the `/` operator, which produces the right separator on every operating system.

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

**What the demo shows**

- The first two prints take a path apart without touching the disk: `name` is the last part (`sales.2026.csv`), `stem` is the name without its final extension, `suffix` is `.csv`, `suffixes` lists all extensions, `parent` is the folder it is in, and `parts` is a tuple of every component. `with_suffix` and `with_name` return modified copies. `is_absolute()` is `False`: the path is **relative**, meaning it is interpreted starting from the current folder.
- `tempfile.mkdtemp()` creates a real scratch folder. `mkdir(parents=True, exist_ok=True)` creates a folder with all the folders above it and does not complain if it already exists. `write_text` creates a file in one call.
- `iterdir()` lists what is directly inside a folder. `rglob("*.log")` searches the folder and everything below it for names matching a pattern, where `*` stands for any characters.
- `exists()`, `is_file()` and `is_dir()` ask questions about a path; `stat().st_size` is the size in bytes; `read_text` reads a whole file.
- `log.open("a", ...)` works exactly like the built-in `open`. `rename` renames the file.
- `shutil.rmtree(root)` deletes the folder with everything in it, after which `root.exists()` is `False`.

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
> Build paths relative to the code, not relative to the folder the program happens to be started from: `DATA = Path(__file__).resolve().parent / "data"`. (`__file__` is the path of the current source file.) The program then works wherever it is launched from.

`tempfile.TemporaryDirectory()` and `NamedTemporaryFile()` create temporary folders and files that remove themselves; pytest offers a ready-made `tmp_path` for the same purpose in tests.

## JSON

JSON (JavaScript Object Notation) is the text format in which most web services send and receive data; an **API** is the set of requests a service accepts. JSON looks very much like Python's own notation for dictionaries and lists. The `json` module translates between JSON text and Python objects like this:

| JSON | Python |
|---|---|
| object | `dict` (keys always `str`) |
| array | `list` |
| string | `str` |
| number | `int` or `float` |
| `true` / `false` | `True` / `False` |
| `null` | `None` |

Turning objects into text or bytes for storing or sending is called **serialisation**; the reverse is **parsing** (or deserialisation). The module has four functions. To keep them apart, remember "**s** is for string":

- `json.dumps(obj)` returns a JSON **s**tring; `json.loads(text)` takes a string and returns Python objects.
- `json.dump(obj, file)` and `json.load(file)` do the same, writing to or reading from an open file.

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

- `json.dumps(order)` gives one compact line. Note the JSON spellings `true` and `null`, and that non-English letters are written as `\u...` escapes by default.
- `indent=2` spreads the output over indented lines, `sort_keys=True` orders the keys, and `ensure_ascii=False` keeps `é` and `ü` readable.
- `json.loads(text)` rebuilds an equal dictionary.
- The last part shows what does *not* survive a round trip: integer keys come back as strings (`{'1': 'int key', '2': 'x'}`), a tuple comes back as a list, and text with single quotes is not valid JSON and raises `JSONDecodeError`.

### Types JSON doesn't know

JSON has only the six kinds of value in the table above. Dates and times (`datetime`), exact decimals (`Decimal`), sets, bytes, dataclasses and objects of your own classes cause `TypeError: Object of type ... is not JSON serializable`. The remedy is to pass `json.dumps` a function as `default=`; it is called for every object the module does not know and must return something it does know. For reading, an `object_hook` function can convert each dictionary back after it is parsed.

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

`encode` handles four cases: a dataclass becomes a dictionary, a date becomes text in the standard ISO format, a `Decimal` becomes a string (a float would lose exactness), and a set becomes a sorted list. Anything else is refused. The printed JSON shows the result. `decode` then turns the two special fields back into a `datetime` and a `Decimal` on the way in.

In real services, Pydantic models (see the typing module) do this converting and checking for you. Three further notes. Never use `eval` to read JSON-like text, because `eval` runs whatever code the text contains. For files with one JSON object per line (**JSON Lines**), loop over the file and call `json.loads` on each line. And `pickle`, Python's own format for saving objects, is **unsafe on data you do not trust**, because loading a pickle can run code; prefer JSON for exchanging data.

## CSV

CSV looks as if it needs no library: split each line at the commas. That works until a field itself contains a comma, a quotation mark or a line break. CSV solves those cases with quoting rules (a field in double quotes may contain commas and line breaks; a quotation mark inside it is written twice), and the `csv` module implements them.

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

The sample has two data rows with deliberately awkward content. Splitting the first row at commas gives five pieces, because `"Hello, world"` is cut in two: wrong. `csv.reader` returns each row as a correct list of four strings, including Ben's city with a line break inside it and the quotation marks around `hi`. `csv.DictReader` uses the first row as column names and returns each following row as a dictionary, so fields can be read by name.

Every value read from a CSV file is a **string**. Converting to numbers is up to you, as `int(row["age"])` does above.

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

`DictWriter` writes dictionaries as rows in the column order given by `fieldnames`; `writeheader()` writes the title row. In the output, the note containing a comma has been put in quotes automatically, and the quotation marks in the other note have been doubled. The second part writes a tab-separated file by passing `delimiter="\t"`.

With real files, open them with **`newline=""`** and an explicit encoding. The `csv` module manages line endings itself, and without `newline=""` you get a blank line between rows on Windows.

```python
with open("people.csv", newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        ...

with open("out.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerows(rows)
```

Files exported from Excel often begin with an invisible marker called a byte-order mark; read them with `encoding="utf-8-sig"`, which removes it. For heavy analysis you would use the pandas library (`pd.read_csv`), but `csv` needs no installation and processes a file row by row.

## Worked example: a small ETL pipeline

**ETL** stands for extract, transform, load: read data from one place, clean and reshape it, and write it somewhere else. This small pipeline reads a CSV file of sales, skips the rows that are damaged, adds up revenue per region, and writes a JSON report:

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

- The first lines create a scratch folder and a CSV file with five data rows, two of which are bad (an empty `units` field and the letter `x`).
- `read_sales` is a generator. For each row it yields the region and the revenue, `units × price`. Converting a bad value raises `ValueError`, which is caught: the row is reported with its line number and skipped.
- The main loop adds each revenue to its region in a `defaultdict(float)`.
- `json.dump` writes the report file, which is then read back and printed.

The output shows the two skipped lines, then a report with `north` at 51.75 and `south` at 6.0. Because `read_sales` is a generator, only one row is in memory at a time, and the reading-and-checking is kept apart from the adding-up.

> [!INTERVIEW]
> Typical questions: "How do you read a huge file?" Loop over it line by line (`for line in f`) or read fixed-size pieces; never `read()` it whole. "Why `with open(...)`?" It guarantees the file is closed and flushed even when an exception occurs. "`json.dump` or `json.dumps`?" To a file, or to a string. "Why not `line.split(',')` for CSV?" Quoted fields may contain commas, quotation marks and line breaks. "Text mode or binary mode?" `str` with decoding and line-ending translation, or raw `bytes`.

## Persisting program state: load-or-default

Small programs often need to remember something from one run to the next: a user's name, some preferences, a high score. Keeping data beyond the life of the program is called **persistence**. The dependable pattern has three parts: **load** what was saved, or fall back on defaults; **work** with a plain dictionary in memory; **save** when something changes. Putting each part in a function of its own makes all three testable.

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

The loop imitates three runs of a program. The launch counter goes 1, 2, 3 and the name is remembered from the first run on, which shows that the file carries the data from one run to the next. Finally the file is deliberately damaged, and `load_settings` returns the defaults without crashing.

Three details make this robust. First, the saved values are merged *over* a dictionary of defaults, so a file written by an older version of the program, which lacks newer keys, still loads. Second, catching `JSONDecodeError` as well as `FileNotFoundError` covers a half-written or hand-edited file. Third, the new contents are written to a temporary file which is then renamed over the real one; a crash in the middle of saving therefore cannot leave a cut-off settings file behind.

## Pitfalls recap

- Leaving out `encoding="utf-8"`, so that behaviour depends on the machine.
- Mode `"w"` empties an existing file without asking.
- Forgetting `newline=""` when opening CSV files.
- Calling `f.read()` twice without `seek(0)` in between.
- Assuming CSV values are numbers; they are strings.
- JSON keys become strings and tuples become lists; `NaN` and `Infinity` are not valid in strict JSON.
- Building paths by gluing strings together with a hard-coded `\` or `/`, and relative paths that depend on the current folder.
- Loading pickles from sources you do not trust.

## Summary

Use `with open(..., encoding="utf-8")` and loop over the file line by line. Use `pathlib.Path` for everything to do with paths. Use `json` (`dump` / `load` for files, `dumps` / `loads` for strings, `default=` for extra types) and `csv` (`reader` / `DictReader`, `writer` / `DictWriter`, `newline=""`) in preference to parsing by hand.

## Glossary

- **File** - a named piece of data stored on disk.
- **File object** - what `open()` returns: the handle through which a file is read or written.
- **Mode** - the second argument of `open()`: read, write, append, exclusive create; text or binary.
- **Encoding / UTF-8** - the rule for converting characters to bytes / the encoding nearly everything uses.
- **Buffer / flush** - text held in memory before being written / writing it out to the disk.
- **Text mode / binary mode** - reading and writing `str` with decoding / raw `bytes`.
- **Position** - the place in an open file where the next read or write happens.
- **Path** - the address of a file or folder.
- **Absolute / relative path** - starting at the top of the file system / starting from the current folder.
- **`pathlib.Path`** - the object-based way of handling paths.
- **Glob pattern** - a name pattern such as `*.log`, where `*` matches any characters.
- **JSON** - a text format for nested dictionaries, lists, strings, numbers, `true` / `false` and `null`.
- **Serialisation / parsing** - converting objects to text or bytes / converting them back.
- **JSON Lines** - a file with one JSON value per line.
- **CSV** - a text format for tables: one row per line, fields separated by commas, with quoting rules.
- **Delimiter** - the character that separates fields, a comma or a tab.
- **ETL** - extract, transform, load: read data, reshape it, write it elsewhere.
- **Persistence** - keeping data beyond the run of the program.
- **Pickle** - Python's own serialisation format; unsafe to load from untrusted sources.

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
  {"q": "With pathlib, how do you build 'data/raw/x.csv' portably?", "options": ["`'data' + '\\\\raw\\\\x.csv'`", "`Path('data') / 'raw' / 'x.csv'`", "`os.join('data','raw','x.csv')`", "`Path('data', sep='/')`"], "answer": 1,
   "explain": "The / operator joins path components using the right separator for the OS."},
  {"q": "What type are the values produced by csv.DictReader?", "options": ["Inferred ints/floats", "Always strings", "bytes", "Depends on the header"], "answer": 1,
   "explain": "The csv module performs no type conversion; convert explicitly."},
  {"q": "Why pass encoding='utf-8' explicitly to open()?", "options": ["It is required syntax", "The default encoding depends on the platform, causing bugs across machines", "It makes files smaller", "It enables binary mode"], "answer": 1,
   "explain": "Relying on the locale default is a classic 'works on my machine' problem."}
]
```

> **Source:** Goodrich, Tamassia & Goldwasser, *Data Structures and Algorithms in Python*, §1.6 (Simple Input and Output: console and files), restated in original wording with new examples; Python docs, *Tutorial* ch. 7 "Input and Output", *Library Reference* `pathlib`, `json`, `csv`, `io`.
