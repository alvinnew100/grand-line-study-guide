"""Linux CLI problems, set 3: the classic text filters, rebuilt in Python."""

PROBLEMS = [
# ------------------------------------------------------------------ wc
dict(
    id="cli-mini-wc",
    title="A Mini wc",
    difficulty="Easy",
    pattern="Text Processing",
    entry="wc",
    description=r"""
`wc` prints three numbers for its input: lines, words and bytes. Reproduce them.

Given a string `text`, return `[lines, words, bytes]` where

* **lines** is the number of newline characters (`\n`) — so a final line without a trailing newline
  is *not* counted, exactly like the real tool;
* **words** is the number of maximal runs of non-whitespace characters;
* **bytes** is the size of the text when encoded as UTF-8 (not the number of characters).

**Example 1:** `"hello world\n"` → `[1, 2, 12]`

**Example 2:** `"no newline"` → `[0, 2, 10]`

**Example 3:** `"héllo\n"` → `[1, 1, 7]` (the `é` occupies two bytes)
""",
    starter='''def wc(text: str) -> List[int]:
    pass
''',
    solution='''def wc(text):
    return [text.count("\\n"), len(text.split()), len(text.encode("utf-8"))]
''',
    tests=[
        ["hello world\n"], ["no newline"], ["héllo\n"], [""], ["\n\n\n"],
        ["  spaced   out\twords \n"], ["one\ntwo\nthree"], ["a b\nc d\n"],
        ["日本語 text\n"], ["   \n \t \n"], ["x"], ["tab\tseparated\tfields\nrow\ttwo\n"],
    ],
    examples=3,
    wrong_solutions=[
        '''def wc(text):
    return [len(text.splitlines()), len(text.split()), len(text.encode("utf-8"))]
''',
        '''def wc(text):
    return [text.count("\\n"), len(text.split()), len(text)]
''',
        '''def wc(text):
    return [text.count("\\n"), len(text.split(" ")), len(text.encode("utf-8"))]
''',
    ],
    guide=dict(
        prereqs="The redirection lesson (where `wc` first appears) and the text-processing lessons. Python strings versus bytes.",
        intuition="Each of the three counts answers a slightly different question than people expect. A *line* is something terminated by a newline, so `wc -l` is really counting newline characters. A *word* is anything between whitespace. And the last number is storage, measured in bytes, which only equals the character count for plain ASCII.",
        hints=[
            "Count `\\n` characters rather than splitting into lines.",
            "`str.split()` with no argument splits on any whitespace run and ignores leading and trailing whitespace.",
            "Encode to UTF-8 before measuring length.",
        ],
        brute_force="Walk the text character by character with a flag 'am I inside a word?', incrementing the word count on every transition from whitespace to non-whitespace and the line count on every newline. This is what the C implementation does and it is already O(n); the built-ins just hide the loop.",
        approach="""1. `lines = text.count('\\n')`.
2. `words = len(text.split())`.
3. `bytes = len(text.encode('utf-8'))`.

**Dry run, `"one\\ntwo\\nthree"`:** two newline characters → 2 lines (the unterminated `three` is not a full line), three words, 13 bytes. Result `[2, 3, 13]`.""",
        complexity="Time O(n), space O(n) for the temporary list of words and the encoded copy.",
        pitfalls="""* `splitlines()` counts the unterminated last line, giving one more than `wc -l`.
* `split(' ')` produces empty strings for consecutive spaces and does not split on tabs or newlines.
* `len(text)` counts code points; `wc -c` counts bytes (use `wc -m` for characters).""",
        follow_up="Add the `-L` statistic: the length of the longest line.",
    ),
),
# ------------------------------------------------------------------ sort | uniq -c | sort -rn
dict(
    id="cli-top-k-lines",
    title="sort | uniq -c | sort -rn | head",
    difficulty="Easy",
    pattern="Pipelines",
    entry="top_k",
    description=r"""
The most famous one-liner on Unix answers "what are the most common values?":

```bash
sort access.txt | uniq -c | sort -rn | head -n 3
```

Implement the whole pipeline. Given a list of `lines` and an integer `k`, return the `k` most frequent
distinct lines as `[count, line]` pairs, highest count first. Break ties by the line itself in
ascending order. If there are fewer than `k` distinct lines, return them all.

**Example 1:** `lines = ["GET", "POST", "GET", "PUT", "GET", "POST"], k = 2` → `[[3, "GET"], [2, "POST"]]`

**Example 2:** `lines = ["b", "a"], k = 5` → `[[1, "a"], [1, "b"]]`
""",
    starter='''def top_k(lines: List[str], k: int) -> List[list]:
    pass
''',
    solution='''def top_k(lines, k):
    counts = {}
    for line in lines:
        counts[line] = counts.get(line, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return [[c, line] for line, c in ranked[:k]]
''',
    tests=[
        [["GET", "POST", "GET", "PUT", "GET", "POST"], 2],
        [["b", "a"], 5],
        [[], 3],
        [["x"], 1],
        [["a", "b", "a", "b", "a", "b"], 1],
        [["404", "200", "200", "500", "404", "200", "301"], 3],
        [["z", "y", "x", "z", "y", "x"], 3],
        [["a", "b", "a", "c", "a", "b"], 0],
        [["a", "b", "a", "b", "c", "a", "a"], 2],
        [["10.0.0.%d" % (i % 7) for i in range(500)] + ["10.0.0.3"] * 5, 4],
        [["same"] * 50, 2],
        [["a", "A", "a", "A", "b"], 2],
    ],
    examples=2,
    wrong_solutions=[
        '''def top_k(lines, k):
    out = []
    for line in lines:
        if out and out[-1][1] == line:
            out[-1][0] += 1
        else:
            out.append([1, line])
    out.sort(key=lambda p: (-p[0], p[1]))
    return out[:k]
''',
        '''def top_k(lines, k):
    counts = {}
    for line in lines:
        counts[line] = counts.get(line, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: kv[1], reverse=True)
    return [[c, line] for line, c in ranked[:k]]
''',
    ],
    guide=dict(
        prereqs="The pipelines lesson and the `sort`/`uniq` section of the text-processing lesson. Dictionaries and sorting with a key.",
        intuition="`uniq` only merges **adjacent** duplicates, which is why the pipeline sorts first: sorting pushes equal lines next to each other so one pass can count each run. The second sort then orders the runs by their count. In a language with hash maps you can skip the first sort and count directly, but the two-stage shape — group, then rank — is the same.",
        hints=[
            "Count occurrences with a dictionary.",
            "Sort the `(line, count)` pairs by a tuple key: negative count first, then the line.",
            "Slice the first `k` and reshape into `[count, line]`.",
        ],
        brute_force="For every distinct line, scan the whole list to count it: O(d × n) for d distinct values. Or mimic the pipeline literally — sort all n lines, O(n log n) — then count runs. Both work; the hash map avoids sorting the full input.",
        approach="""1. Build `counts`.
2. `sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))`.
3. Return the first `k` as `[count, line]`.

**Dry run, example 1:** counts `{GET: 3, POST: 2, PUT: 1}`. Sorted by `(-count, line)`: GET, POST, PUT. Take two → `[[3, "GET"], [2, "POST"]]`.""",
        complexity="Time O(n + d log d) for n lines and d distinct values; space O(d).",
        pitfalls="""* Counting only adjacent runs without sorting first — the classic `uniq` mistake.
* Sorting by count alone leaves ties in arbitrary (insertion) order.
* `k = 0` and an empty input must return an empty list.""",
        follow_up="When d is huge and k is small, a heap (`heapq.nsmallest(k, ...)`) ranks in O(d log k). On the real command line, `sort -k1,1nr -k2` gives a deterministic tie order.",
    ),
),
# ------------------------------------------------------------------ cut
dict(
    id="cli-cut-fields",
    title="cut -d -f",
    difficulty="Medium",
    pattern="Text Processing",
    entry="cut_fields",
    description=r"""
`cut -d: -f1,3 /etc/passwd` slices columns out of delimited text. Implement field mode.

`cut_fields(lines, delim, spec)` returns the transformed lines.

* `delim` is a single character. Fields are numbered from **1**.
* `spec` is a comma-separated list of items: `N` (one field), `N-M` (inclusive range), `N-` (from N
  to the end) or `-M` (from the first to M).
* Selected fields are printed **in their original order**, each at most once, joined by `delim` —
  the order in which you list them does not matter (`3,1` behaves like `1,3`).
* Field numbers past the end of a line select nothing.
* A line that does **not contain the delimiter at all** is passed through unchanged, whatever the
  spec says (this is the default behaviour of the real tool).

**Example 1:** `lines = ["root:x:0:0:/root"], delim = ":", spec = "1,3"` → `["root:0"]`

**Example 2:** `lines = ["a,b,c,d,e"], delim = ",", spec = "2-4"` → `["b,c,d"]`

**Example 3:** `lines = ["no delimiter here"], delim = ",", spec = "2"` → `["no delimiter here"]`
""",
    starter='''def cut_fields(lines: List[str], delim: str, spec: str) -> List[str]:
    pass
''',
    solution='''def cut_fields(lines, delim, spec):
    ranges = []
    for item in spec.split(","):
        if "-" in item:
            lo, hi = item.split("-")
            ranges.append((int(lo) if lo else 1, int(hi) if hi else None))
        else:
            ranges.append((int(item), int(item)))

    def wanted(n):
        return any(lo <= n and (hi is None or n <= hi) for lo, hi in ranges)

    out = []
    for line in lines:
        if delim not in line:
            out.append(line)
            continue
        fields = line.split(delim)
        out.append(delim.join(f for i, f in enumerate(fields, 1) if wanted(i)))
    return out
''',
    tests=[
        [["root:x:0:0:/root"], ":", "1,3"],
        [["a,b,c,d,e"], ",", "2-4"],
        [["no delimiter here"], ",", "2"],
        [["a,b,c,d,e"], ",", "3,1"],
        [["a,b,c,d,e"], ",", "4-"],
        [["a,b,c,d,e"], ",", "-2"],
        [["a,b,c"], ",", "2,2,1-2"],
        [["a,b,c"], ",", "5"],
        [["a,,c,", ",x"], ",", "1,2,4"],
        [[], ",", "1"],
        [["k=v", "plain", "a=b=c"], "=", "2-"],
        [["one two  three"], " ", "1,3"],
        [["u1\t10\tok", "u2\t20\tfail"], "\t", "1,3"],
        [["a:b:c:d"], ":", "1,3-"],
    ],
    examples=3,
    wrong_solutions=[
        '''def cut_fields(lines, delim, spec):
    out = []
    for line in lines:
        if delim not in line:
            out.append(line)
            continue
        f = line.split(delim)
        picked = []
        for item in spec.split(","):
            if "-" in item:
                lo, hi = item.split("-")
                lo = int(lo) if lo else 1
                hi = int(hi) if hi else len(f)
            else:
                lo = hi = int(item)
            picked.extend(f[lo - 1:hi])
        out.append(delim.join(picked))
    return out
''',
        '''def cut_fields(lines, delim, spec):
    ranges = []
    for item in spec.split(","):
        if "-" in item:
            lo, hi = item.split("-")
            ranges.append((int(lo) if lo else 1, int(hi) if hi else 10 ** 9))
        else:
            ranges.append((int(item), int(item)))
    out = []
    for line in lines:
        fields = line.split(delim)
        out.append(delim.join(f for i, f in enumerate(fields, 1)
                              if any(lo <= i <= hi for lo, hi in ranges)))
    return out
''',
    ],
    guide=dict(
        prereqs="The text-processing lesson (`cut`). `str.split` with an explicit separator.",
        intuition="`cut` is a *filter on field numbers*, not a re-arranger. It walks the fields of a line from left to right and asks of each one: is your number in the selected set? That mental model explains two surprises at once: listing `3,1` cannot swap columns, and listing a field twice cannot duplicate it.",
        hints=[
            "Parse the spec once into `(low, high)` pairs; use `None` (or infinity) for an open end.",
            "Split each line on the exact delimiter — not on whitespace — so empty fields are preserved.",
            "Handle the no-delimiter case before splitting.",
        ],
        brute_force="For each line and each item of the spec, slice the list of fields and append the slice to the output. It is short, but it emits fields in spec order and repeats overlapping ones, which is not what `cut` does. Fixing it means collecting a set of indices anyway.",
        approach="""1. Turn the spec into ranges: `N` → `(N, N)`, `N-M` → `(N, M)`, `N-` → `(N, None)`, `-M` → `(1, M)`.
2. For each line: if the delimiter is absent, emit the line untouched.
3. Otherwise split, keep the fields whose 1-based index lies in any range, and join with the delimiter.

**Dry run, `"a,b,c,d,e"` with `3,1`:** ranges `(3,3)` and `(1,1)`. Walk fields: 1 `a` keep, 2 `b` drop, 3 `c` keep, 4 and 5 drop → `a,c`.""",
        complexity="Time O(total characters × number of ranges), space O(longest line).",
        pitfalls="""* Using `split()` without an argument collapses repeated delimiters; `cut` treats `a,,c` as three fields with an empty middle one. This is also why `cut -d' '` struggles with columns aligned by several spaces.
* Printing nothing for delimiter-less lines; the real tool echoes them unless `-s` is given.
* Emitting fields in spec order.""",
        follow_up="Implement `-s` (suppress lines without the delimiter), `--complement`, and character mode `-c`. To reorder columns for real, reach for `awk`.",
    ),
),
# ------------------------------------------------------------------ tr
dict(
    id="cli-tr-translate",
    title="tr: Translate or Delete Characters",
    difficulty="Medium",
    pattern="Text Processing",
    entry="tr",
    description=r"""
`tr` rewrites a stream one character at a time. Implement its two main modes.

`tr(text, set1, set2, delete)`:

* Sets are written as literal characters and ranges: `a-z` means every character from `a` to `z`.
  A `-` at the very start or end of a set is a literal dash.
* **Translate** (`delete` is `False`): each character found in `set1` is replaced by the character
  at the same position in `set2`. If `set2` is shorter, it is padded by repeating its **last**
  character. If a character occurs more than once in `set1`, the **last** occurrence decides.
* **Delete** (`delete` is `True`): every character in `set1` is removed; `set2` is ignored.

All other characters pass through untouched. In translate mode `set2` is never empty.

**Example 1:** `tr("hello", "a-z", "A-Z", False)` → `"HELLO"`

**Example 2:** `tr("2026-11-20", "0-9", "", True)` → `"--"`

**Example 3:** `tr("hello", "el", "x", False)` → `"hxxxo"`
""",
    starter='''def tr(text: str, set1: str, set2: str, delete: bool) -> str:
    pass
''',
    solution='''def tr(text, set1, set2, delete):
    def expand(spec):
        out, i = [], 0
        while i < len(spec):
            if i + 2 < len(spec) and spec[i + 1] == "-":
                out.extend(chr(c) for c in range(ord(spec[i]), ord(spec[i + 2]) + 1))
                i += 3
            else:
                out.append(spec[i])
                i += 1
        return out

    src = expand(set1)
    if delete:
        drop = set(src)
        return "".join(ch for ch in text if ch not in drop)
    dst = expand(set2)
    if len(dst) < len(src):
        dst += [dst[-1]] * (len(src) - len(dst))
    table = {}
    for a, b in zip(src, dst):
        table[a] = b
    return "".join(table.get(ch, ch) for ch in text)
''',
    tests=[
        ["hello", "a-z", "A-Z", False],
        ["2026-11-20", "0-9", "", True],
        ["hello", "el", "x", False],
        ["hello world", "lo", "01", False],
        ["a-b-c", "-", "_", False],
        ["Hello, World!", "a-zA-Z", "", True],
        ["abc", "a-c", "A", False],
        ["aabb", "aa", "xy", False],
        ["", "a", "b", False],
        ["tab\tand space", " \t", "_", False],
        ["hello", "a-y", "b-z", False],
        ["Mississippi", "sp", "", True],
        ["x-ray", "a-", "A_", False],
        ["HAL", "A-Y", "B-Z", False],
        ["unchanged", "0-9", "#", False],
    ],
    examples=3,
    wrong_solutions=[
        '''def tr(text, set1, set2, delete):
    def expand(spec):
        out, i = [], 0
        while i < len(spec):
            if i + 2 < len(spec) and spec[i + 1] == "-":
                out.extend(chr(c) for c in range(ord(spec[i]), ord(spec[i + 2]) + 1))
                i += 3
            else:
                out.append(spec[i])
                i += 1
        return out
    src = expand(set1)
    if delete:
        return "".join(ch for ch in text if ch not in src)
    dst = expand(set2)
    dst += [dst[-1]] * max(0, len(src) - len(dst))
    for a, b in zip(src, dst):
        text = text.replace(a, b)
    return text
''',
        '''def tr(text, set1, set2, delete):
    def expand(spec):
        out, i = [], 0
        while i < len(spec):
            if i + 2 < len(spec) and spec[i + 1] == "-":
                out.extend(chr(c) for c in range(ord(spec[i]), ord(spec[i + 2]) + 1))
                i += 3
            else:
                out.append(spec[i])
                i += 1
        return out
    src = expand(set1)
    if delete:
        return "".join(ch for ch in text if ch not in src)
    table = dict(zip(src, expand(set2)))
    return "".join(table.get(ch, ch) for ch in text)
''',
    ],
    guide=dict(
        prereqs="The text-processing lesson (`tr`). Dictionaries; `ord` and `chr`.",
        intuition="`tr` has no notion of words or lines; it owns a lookup table from character to character and pushes every input character through it exactly once. Building that table is the whole job: expand both sets into explicit lists, pad the second, pair them up. Because each character is looked up once, a replacement can never be 'replaced again' — the property that makes `tr a-y b-z` a clean shift rather than a cascade.",
        hints=[
            "Write `expand(spec)` that turns `a-e` into `['a','b','c','d','e']` and leaves a leading or trailing dash alone.",
            "Pad the second list with its final element until the lengths match.",
            "Build a dict by iterating the pairs in order, so later duplicates overwrite earlier ones; translate with `table.get(ch, ch)`.",
        ],
        brute_force="Apply `text.replace(a, b)` for each pair in turn. Each replace scans the whole text (O(n × |set|)) and, worse, later replacements see the output of earlier ones: with `a-y` → `b-z` every letter ends up as `z`.",
        approach="""1. Expand `set1`. If deleting, filter the text against that set and return.
2. Expand `set2` and pad it.
3. `table[a] = b` for each aligned pair.
4. Map every character of the text through the table.

**Dry run, `tr("hello", "el", "x", False)`:** `src = [e, l]`, `dst = [x]` padded to `[x, x]`. Table `{e: x, l: x}`. `h e l l o` → `h x x x o`.""",
        complexity="Time O(|text| + |sets|), space O(|sets|).",
        pitfalls="""* Sequential replaces cascade.
* Truncating instead of padding when `set2` is short (`zip` stops early).
* Reading `a-` as a range — a dash at the edge is literal.
* `tr` works on characters, not strings: `tr 'cat' 'dog'` maps c→d, a→o, t→g everywhere.""",
        follow_up="Add `-s` (squeeze runs of the same output character into one) and `-c` (complement of set1), plus classes such as `[:upper:]`.",
    ),
),
# ------------------------------------------------------------------ grep
dict(
    id="cli-mini-grep",
    title="grep with -i -v -n -c",
    difficulty="Medium",
    pattern="Regular Expressions",
    entry="grep",
    description=r"""
Implement the heart of `grep`: print the lines in which a regular expression matches **somewhere**.

`grep(lines, pattern, flags)`:

* `pattern` is a regular expression (the tests only use syntax shared by `grep -E` and Python's
  `re`: literals, `.`, `*`, `+`, `?`, `[...]`, `^`, `$`, `|`, `( )`).
* `flags` is a string containing any of these letters, in any order:
  * `i` — ignore case;
  * `v` — invert: select lines that do **not** match;
  * `n` — prefix each output line with its 1-based line number and a colon;
  * `c` — instead of lines, output a single element: the count of selected lines, as a string.
    (`c` wins over `n`.)

Return the list of output lines.

**Example 1:** `lines = ["error: disk", "ok", "Error: net"], pattern = "error", flags = ""` → `["error: disk"]`

**Example 2:** same lines, `flags = "in"` → `["1:error: disk", "3:Error: net"]`

**Example 3:** same lines, `flags = "vc"` → `["2"]`
""",
    starter='''def grep(lines: List[str], pattern: str, flags: str) -> List[str]:
    pass
''',
    solution='''import re

def grep(lines, pattern, flags):
    rx = re.compile(pattern, re.IGNORECASE if "i" in flags else 0)
    invert = "v" in flags
    picked = [(i, line) for i, line in enumerate(lines, 1)
              if (rx.search(line) is not None) != invert]
    if "c" in flags:
        return [str(len(picked))]
    if "n" in flags:
        return ["%d:%s" % (i, line) for i, line in picked]
    return [line for _, line in picked]
''',
    tests=[
        [["error: disk", "ok", "Error: net"], "error", ""],
        [["error: disk", "ok", "Error: net"], "error", "in"],
        [["error: disk", "ok", "Error: net"], "error", "vc"],
        [["alpha", "beta", "gamma"], "^b", ""],
        [["alpha", "beta", "gamma"], "a$", "n"],
        [["alpha", "beta", "gamma"], "mm|ph", ""],
        [["x1", "x22", "y333", ""], "[0-9][0-9]", "n"],
        [["", "  ", "text"], "^$", "c"],
        [["", "  ", "text"], "^$", "vn"],
        [[], "anything", "c"],
        [[], "anything", ""],
        [["Warn", "WARN", "warn", "info"], "warn", "ic"],
        [["Warn", "WARN", "warn", "info"], "warn", "iv"],
        [["a.b", "axb", "ab"], "a.b", ""],
        [["a.b", "axb", "ab"], "a\\.b", "n"],
        [["GET /api 200", "GET /img 404", "POST /api 500"], "(4|5)[0-9][0-9]$", "nc"],
        [["colour", "color", "colr"], "colou?r", ""],
    ],
    examples=3,
    wrong_solutions=[
        '''import re

def grep(lines, pattern, flags):
    rx = re.compile(pattern, re.IGNORECASE if "i" in flags else 0)
    invert = "v" in flags
    picked = [(i, line) for i, line in enumerate(lines, 1)
              if (rx.match(line) is not None) != invert]
    if "c" in flags:
        return [str(len(picked))]
    if "n" in flags:
        return ["%d:%s" % (i, line) for i, line in picked]
    return [line for _, line in picked]
''',
        '''import re

def grep(lines, pattern, flags):
    rx = re.compile(pattern, re.IGNORECASE if "i" in flags else 0)
    hits = [(i, line) for i, line in enumerate(lines, 1) if rx.search(line)]
    if "c" in flags:
        return [str(len(hits))]
    if "v" in flags:
        hits = [(i, line) for i, line in enumerate(lines, 1) if not rx.search(line)]
    if "n" in flags:
        return ["%d:%s" % (i, line) for i, line in hits]
    return [line for _, line in hits]
''',
        '''import re

def grep(lines, pattern, flags):
    rx = re.compile(pattern, re.IGNORECASE if "i" in flags else 0)
    invert = "v" in flags
    picked = [line for line in lines if (rx.search(line) is not None) != invert]
    if "c" in flags:
        return [str(len(picked))]
    if "n" in flags:
        return ["%d:%s" % (i, line) for i, line in enumerate(picked, 1)]
    return picked
''',
    ],
    guide=dict(
        prereqs="The regular-expressions lesson. Python's `re.search` versus `re.match`.",
        intuition="`grep` is a line filter with one question per line: does the pattern match anywhere in it? Every option is a small adjustment around that question — compare case-insensitively, flip the answer, remember the line number, or count instead of print. Structuring the code as *select, then format* keeps the options from interfering with one another.",
        hints=[
            "Compile the pattern once, adding `re.IGNORECASE` when `i` is present.",
            "Selection rule: `matched != invert`. Keep the original line number with each selected line.",
            "Formatting comes last: count beats numbering.",
        ],
        brute_force="Without a regex engine you could test literal substrings with `in`, which is what `grep -F` does, but that cannot express anchors, classes or alternation. Recompiling the pattern for every line also works and is merely wasteful.",
        approach="""1. `rx = re.compile(pattern, flags)`.
2. Enumerate lines from 1; keep `(number, line)` where `bool(rx.search(line)) != invert`.
3. `c` → `[str(count)]`; `n` → `"N:line"`; otherwise the bare lines.

**Dry run, example 3 (`vc`):** matches for `error` (case-sensitive): line 1 yes, line 2 no, line 3 no (`Error` has a capital). Inverted selection keeps lines 2 and 3 → count `2`.""",
        complexity="Time O(total characters) for typical patterns; space O(selected lines).",
        pitfalls="""* `re.match` anchors at the start; `grep` searches the whole line.
* With `-v`, the count is of the *non-matching* lines.
* Line numbers refer to the input, not to the position among the selected lines.
* `.` is a metacharacter: `a.b` also matches `axb`.""",
        follow_up="Add `-w` (whole-word match), `-o` (print only the matched part), `-l` across multiple files, and context lines `-A`/`-B`.",
    ),
),
]
