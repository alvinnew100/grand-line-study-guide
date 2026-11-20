"""Practical Vim problems, part 1: motions and text objects modelled in pure Python.

Every problem works on ONE line of ASCII text with 0-based columns. Text-object problems return
half-open ranges [start, end) so that an empty selection is representable.
"""

PROBLEMS = [
# ------------------------------------------------------------------ vim-word-forward
dict(
    id="vim-word-forward",
    title="Where does `w` land?",
    difficulty="Easy",
    pattern="Vim motions",
    entry="wordForward",
    description=r"""
Model Vim's `w` motion (jump to the start of the next *word*) on a single line.

Characters fall into three classes:

| class | characters |
|---|---|
| blank | space and tab |
| keyword | `A-Z`, `a-z`, `0-9`, `_` |
| punctuation | every other character |

A **word** is a maximal run of keyword characters *or* a maximal run of punctuation characters.
So `foo.bar()` contains four words: `foo`, `.`, `bar`, `()`.

One press of `w` from column `col`:

1. if the cursor is on a non-blank, skip to the end of the run it is in;
2. skip any blanks;
3. land on the first character of the next word.

This model has only one line: if there is no next word, the cursor moves to the **last character of the
line** (index `len(line) - 1`). On an empty line the answer is always `0`.

Write `wordForward(line, col, count)` returning the column after pressing `w` `count` times
(`count >= 1`, `0 <= col < len(line)` unless the line is empty).

**Example:** `line = "total += price*qty"`, `col = 0`, `count = 1` → `6` (the `+`)

**Example:** same line, `col = 0`, `count = 3` → `14` (the `*`)
""",
    starter='''def wordForward(line: str, col: int, count: int) -> int:
    pass
''',
    solution='''def wordForward(line, col, count):
    def cls(ch):
        if ch in " \\t":
            return 0
        if ch.isalnum() or ch == "_":
            return 1
        return 2
    n = len(line)
    if n == 0:
        return 0
    for _ in range(count):
        i = col
        c = cls(line[i])
        if c != 0:
            while i < n and cls(line[i]) == c:
                i += 1
        while i < n and cls(line[i]) == 0:
            i += 1
        if i >= n:
            return n - 1
        col = i
    return col
''',
    tests=[
        ["total += price*qty", 0, 1],
        ["total += price*qty", 0, 3],
        ["total += price*qty", 0, 4],
        ["foo.bar()", 0, 1],
        ["foo.bar()", 0, 3],
        ["foo.bar()", 4, 1],
        ["", 0, 3],
        ["x", 0, 2],
        ["   lead", 0, 1],
        ["a  b  c", 3, 1],
        ["a  b  c", 0, 9],
        ["trail   ", 0, 1],
        ["if (x_1 >= 10) {", 0, 5],
        ["snake_case_name next", 3, 1],
        ["a\tb", 0, 1],
        ["!!!abc!!!", 1, 2],
    ],
    examples=2,
    wrong_solutions=[
        '''def wordForward(line, col, count):
    n = len(line)
    if n == 0:
        return 0
    for _ in range(count):
        i = col
        while i < n and line[i] not in " \\t":
            i += 1
        while i < n and line[i] in " \\t":
            i += 1
        if i >= n:
            return n - 1
        col = i
    return col
''',
        '''def wordForward(line, col, count):
    def cls(ch):
        if ch in " \\t":
            return 0
        if ch.isalnum() or ch == "_":
            return 1
        return 2
    n = len(line)
    for _ in range(count):
        i = col
        if i < n:
            c = cls(line[i])
            if c != 0:
                while i < n and cls(line[i]) == c:
                    i += 1
        while i < n and cls(line[i]) == 0:
            i += 1
        col = i
    return col
''',
    ],
    guide=dict(
        prereqs="The *Motions* lesson (word-wise movement). String indexing and `while` loops.",
        intuition="`w` does not look for spaces; it looks for a **change of character class**. Classify every "
                  "character as blank, keyword or punctuation, then walk right: leave the run you are standing in, "
                  "cross any blanks, and stop on the first non-blank you meet.",
        hints=[
            "Write a helper `cls(ch)` that returns 0, 1 or 2. Everything else is two `while` loops.",
            "The first loop only runs when the cursor starts on a non-blank; starting on a blank you just skip blanks.",
            "If the index runs off the end of the line there was no next word: return `len(line) - 1` immediately.",
        ],
        brute_force="Split the line into tokens with a regular expression such as `\\w+|[^\\w\\s]+`, record each "
                    "token's start column, and pick the first start greater than `col`, `count` times. It works "
                    "but hides the class-change idea and is easy to get wrong for blanks.",
        approach="Repeat `count` times: read the class at `col`; if it is non-blank advance while the class stays the "
                 "same; then advance while the class is blank; if you fell off the end return the last column, "
                 "otherwise that index is the new `col`.\n\n"
                 "**Dry run** on `foo.bar()` from 0 with count 3: class at 0 is keyword, skip `foo` → index 3 (`.`), "
                 "no blanks, col = 3. Class punctuation, skip `.` → 4 (`b`), col = 4. Class keyword, skip `bar` → 7 "
                 "(`(`), col = 7. Answer 7.",
        complexity="Time O(count + n) in practice (each press only moves right; once the end is reached we return), "
                   "space O(1).",
        pitfalls="- Treating `foo.bar` as one word: that is `W`, not `w`.\n- Returning `len(line)` instead of "
                 "`len(line) - 1` when no word follows; the Normal-mode cursor can never sit past the last character.\n"
                 "- Forgetting the empty line.\n- An underscore is a keyword character, so `snake_case` is one word.",
        follow_up="Add `W`, `b` and `e` (next problem), then a multi-line version where `w` wraps to the next line.",
    ),
),
# ------------------------------------------------------------------ vim-word-motions
dict(
    id="vim-word-motions",
    title="Replay a string of w / b / e / W / B / E",
    difficulty="Medium",
    pattern="Vim motions",
    entry="wordMotions",
    description=r"""
Extend the word model to all six word motions and replay a sequence of them on one line.

Character classes for the lowercase motions are **blank** (space, tab), **keyword** (`A-Za-z0-9_`) and
**punctuation** (anything else). For the uppercase motions there are only two classes: blank and non-blank, so
a WORD is any run of non-blank characters.

| key | rule (single-line model) |
|---|---|
| `w` / `W` | leave the current run if on a non-blank, skip blanks, land on the first character of the next run. No next run → last character of the line. |
| `e` / `E` | step one character right, skip blanks, then go to the **last** character of the run you are in. Nothing but blanks (or nothing) to the right → last character of the line. |
| `b` / `B` | step one character left, skip blanks leftwards, then go to the **first** character of the run you are in. Nothing but blanks (or nothing) to the left → column 0. |

On an empty line every motion leaves the cursor at column 0.

Write `wordMotions(line, col, keys)` where `keys` contains only the characters `wbeWBE`; return the final column.

**Example:** `line = "user.name = input()"`, `col = 0`, `keys = "e"` → `3`

**Example:** same line, `col = 0`, `keys = "WW"` → `12`

**Example:** same line, `col = 12`, `keys = "bb"` → `5`
""",
    starter='''def wordMotions(line: str, col: int, keys: str) -> int:
    pass
''',
    solution='''def wordMotions(line, col, keys):
    n = len(line)
    if n == 0:
        return 0

    def cls(i, big):
        ch = line[i]
        if ch in " \\t":
            return 0
        if big:
            return 1
        return 1 if (ch.isalnum() or ch == "_") else 2

    for k in keys:
        big = k.isupper()
        m = k.lower()
        i = col
        if m == "w":
            t = cls(i, big)
            if t:
                while i < n and cls(i, big) == t:
                    i += 1
            while i < n and cls(i, big) == 0:
                i += 1
            col = i if i < n else n - 1
        elif m == "e":
            i += 1
            while i < n and cls(i, big) == 0:
                i += 1
            if i >= n:
                col = n - 1
            else:
                t = cls(i, big)
                while i + 1 < n and cls(i + 1, big) == t:
                    i += 1
                col = i
        else:
            i -= 1
            while i >= 0 and cls(i, big) == 0:
                i -= 1
            if i < 0:
                col = 0
            else:
                t = cls(i, big)
                while i - 1 >= 0 and cls(i - 1, big) == t:
                    i -= 1
                col = i
    return col
''',
    tests=[
        ["user.name = input()", 0, "e"],
        ["user.name = input()", 0, "WW"],
        ["user.name = input()", 12, "bb"],
        ["user.name = input()", 0, "wwww"],
        ["user.name = input()", 18, "B"],
        ["user.name = input()", 18, "b"],
        ["user.name = input()", 0, "E"],
        ["user.name = input()", 3, "e"],
        ["", 0, "wbeWBE"],
        ["z", 0, "ebw"],
        ["  padded  ", 9, "b"],
        ["  padded  ", 2, "b"],
        ["  padded  ", 7, "e"],
        ["a-b-c d", 0, "eee"],
        ["a-b-c d", 6, "BbbB"],
        ["k8s_pod-name: web-01", 0, "wEbWe"],
    ],
    examples=3,
    wrong_solutions=[
        '''def wordMotions(line, col, keys):
    n = len(line)
    if n == 0:
        return 0
    def cls(i, big):
        ch = line[i]
        if ch in " \\t":
            return 0
        if big:
            return 1
        return 1 if (ch.isalnum() or ch == "_") else 2
    for k in keys:
        big = k.isupper()
        m = k.lower()
        i = col
        if m == "w":
            t = cls(i, big)
            if t:
                while i < n and cls(i, big) == t:
                    i += 1
            while i < n and cls(i, big) == 0:
                i += 1
            col = i if i < n else n - 1
        elif m == "e":
            while i < n and cls(i, big) == 0:
                i += 1
            if i >= n:
                col = n - 1
            else:
                t = cls(i, big)
                while i + 1 < n and cls(i + 1, big) == t:
                    i += 1
                col = i
        else:
            while i >= 0 and cls(i, big) == 0:
                i -= 1
            if i < 0:
                col = 0
            else:
                t = cls(i, big)
                while i - 1 >= 0 and cls(i - 1, big) == t:
                    i -= 1
                col = i
    return col
''',
        '''def wordMotions(line, col, keys):
    n = len(line)
    if n == 0:
        return 0
    def cls(i, big):
        return 0 if line[i] in " \\t" else 1
    for k in keys:
        m = k.lower()
        i = col
        if m == "w":
            while i < n and cls(i, 1):
                i += 1
            while i < n and not cls(i, 1):
                i += 1
            col = i if i < n else n - 1
        elif m == "e":
            i += 1
            while i < n and not cls(i, 1):
                i += 1
            if i >= n:
                col = n - 1
            else:
                while i + 1 < n and cls(i + 1, 1):
                    i += 1
                col = i
        else:
            i -= 1
            while i >= 0 and not cls(i, 1):
                i -= 1
            if i < 0:
                col = 0
            else:
                while i - 1 >= 0 and cls(i - 1, 1):
                    i -= 1
                col = i
    return col
''',
    ],
    guide=dict(
        prereqs="`vim-word-forward`. The difference between a word and a WORD from the *Motions* lesson.",
        intuition="All six motions are the same three steps in a different order: *get off where you are*, *cross the "
                  "blanks*, *slide to an edge of the run*. `e` and `b` must move at least one character first, "
                  "otherwise pressing `e` at the end of a word would never go anywhere.",
        hints=[
            "Make the classifier take a flag: with the flag set, every non-blank is class 1.",
            "`e`: `i += 1`, skip blanks to the right, then extend right while the next character has the same class.",
            "`b` is the mirror image of `e`: `i -= 1`, skip blanks to the left, extend left while the previous character has the same class.",
        ],
        brute_force="Tokenise the line into runs with their start and end columns (once for words, once for WORDs) "
                    "and for each key scan the token list for the first start greater than the cursor (`w`), first "
                    "end greater than the cursor (`e`) or last start smaller than the cursor (`b`). O(keys × tokens).",
        approach="Loop over the keys. Decide `big = key.isupper()`. Apply the rule for the lower-cased key using the "
                 "class function.\n\n**Dry run** `user.name = input()` from 12 with `bb`: first `b`: step to 11 "
                 "(blank), skip blanks left to 10 (`=`), run `=` starts at 10 → col 10. Second `b`: step to 9 (blank), "
                 "skip to 8 (`e`), slide left through `name` to 5 → col 5.",
        complexity="O(len(keys) × n) worst case, O(1) extra space.",
        pitfalls="- Forgetting the mandatory first step for `e`/`b`: the cursor then gets stuck on a word edge.\n"
                 "- Using the three-class classifier for the uppercase motions.\n- `e` on trailing blanks and `b` on "
                 "leading blanks have no target: clamp to the last column or column 0.\n- Off-by-one when sliding to "
                 "the edge: test the *neighbour's* class, not the current one.",
        follow_up="Add `ge`/`gE` (backward to end of word) and counts such as `3w`.",
    ),
),
# ------------------------------------------------------------------ vim-line-anchors
dict(
    id="vim-line-anchors",
    title="Line anchors: 0, ^, $ and g_",
    difficulty="Easy",
    pattern="Vim motions",
    entry="lineAnchor",
    description=r"""
Four Normal-mode motions jump to a fixed place on the current line, regardless of where the cursor was:

| key | lands on |
|---|---|
| `0` | column 0 |
| `^` | the first non-blank character; on a line made only of blanks, the **last** character |
| `$` | the last character |
| `g_` | the last non-blank character; on a line made only of blanks, column 0 |

Blanks are spaces and tabs. On an empty line all four return `0`.

Write `lineAnchor(line, key)` returning the 0-based column.

**Example:** `line = "    return x  "`, `key = "^"` → `4`

**Example:** same line, `key = "g_"` → `11`; `key = "$"` → `13`
""",
    starter='''def lineAnchor(line: str, key: str) -> int:
    pass
''',
    solution='''def lineAnchor(line, key):
    n = len(line)
    if n == 0 or key == "0":
        return 0
    if key == "$":
        return n - 1
    if key == "^":
        for i, ch in enumerate(line):
            if ch not in " \\t":
                return i
        return n - 1
    for i in range(n - 1, -1, -1):
        if line[i] not in " \\t":
            return i
    return 0
''',
    tests=[
        ["    return x  ", "^"],
        ["    return x  ", "g_"],
        ["    return x  ", "$"],
        ["    return x  ", "0"],
        ["", "^"],
        ["", "$"],
        ["", "g_"],
        ["     ", "^"],
        ["     ", "g_"],
        ["     ", "$"],
        ["x", "^"],
        ["x", "g_"],
        ["\t\tindented", "^"],
        ["no_indent", "^"],
        ["tail\t", "g_"],
    ],
    examples=2,
    wrong_solutions=[
        '''def lineAnchor(line, key):
    if key == "0":
        return 0
    if key == "$":
        return max(len(line) - 1, 0)
    if key == "^":
        return len(line) - len(line.lstrip())
    return max(len(line.rstrip()) - 1, 0)
''',
        '''def lineAnchor(line, key):
    n = len(line)
    if n == 0 or key == "0":
        return 0
    if key == "$":
        return n
    if key == "^":
        for i, ch in enumerate(line):
            if ch != " ":
                return i
        return n - 1
    for i in range(n - 1, -1, -1):
        if line[i] != " ":
            return i
    return 0
''',
    ],
    guide=dict(
        prereqs="The *Motions* lesson. Basic string scanning.",
        intuition="These are absolute motions: the starting column is irrelevant. The only thinking required is what "
                  "happens when the thing being looked for (a non-blank) does not exist.",
        hints=[
            "Handle the empty line first; then `0` and `$` are one-liners.",
            "`^` scans from the left for the first character that is not a space or tab.",
            "When the whole line is blank, `^` ends on the last column but `g_` ends on column 0. They are not symmetric.",
        ],
        brute_force="There is nothing slower than a linear scan here; the naive approach is the right one.",
        approach="Branch on the key. For `^` scan left to right, for `g_` scan right to left, each with a fallback.\n\n"
                 "**Dry run** on `····return x··` (dots are spaces, length 14): `^` finds `r` at 4; `g_` scans back from "
                 "13, 12 (blanks) to 11 (`x`); `$` is 13.",
        complexity="O(n) time, O(1) space.",
        pitfalls="- `len(line) - len(line.lstrip())` gives `len(line)` on an all-blank line, which is past the end.\n"
                 "- `$` is `len - 1`, not `len`: in Normal mode the cursor sits *on* a character.\n- Tabs are blanks too.",
        follow_up="As operator targets these behave differently: `d$` includes the last character, while `d0` and `d^` "
                  "exclude the character under the cursor. Try modelling that.",
    ),
),
# ------------------------------------------------------------------ vim-find-char
dict(
    id="vim-find-char",
    title="f, t, F, T and their repeats ; and ,",
    difficulty="Medium",
    pattern="Vim motions",
    entry="findChar",
    description=r"""
Simulate Vim's character-search motions on one line. `keys` is a string made of these commands:

| command | meaning |
|---|---|
| `f{c}` | move **onto** the nearest `c` strictly right of the cursor |
| `F{c}` | move **onto** the nearest `c` strictly left of the cursor |
| `t{c}` | find the nearest `c` strictly right of the cursor and stop **one column before** it |
| `T{c}` | find the nearest `c` strictly left of the cursor and stop **one column after** it |
| `;` | repeat the most recent `f/F/t/T` in the same direction |
| `,` | repeat it in the opposite direction (`f`↔`F`, `t`↔`T`) |

Rules:

- The character after `f`, `F`, `t` or `T` is always taken literally, even if it is `;`, `,` or a letter such as `f`.
- If the target is not found the cursor does not move (the command is still remembered for `;` and `,`).
- `;` and `,` never change which search is remembered. Before any search has been made they do nothing.
- **Repeat rule for t/T:** when a `t`-style search is run through `;` or `,`, the character directly next to the
  cursor in the search direction is skipped, so that the repeat makes progress instead of finding the same
  occurrence again. A freshly typed `t{c}` or `T{c}` does *not* skip: if the neighbour is `c`, the cursor stays put.

Write `findChar(line, col, keys)` returning the final column.

**Example:** `line = "a, b, c, d"`, `col = 0`, `keys = "f,;"` → `4`

**Example:** same line, `col = 0`, `keys = "t,;;"` → `6`

**Example:** same line, `col = 9`, `keys = "F,,"` → `7` (`F,` goes to 7, then `,` searches right for a comma: none, so stay)
""",
    starter='''def findChar(line: str, col: int, keys: str) -> int:
    pass
''',
    solution='''def findChar(line, col, keys):
    def run(kind, ch, col, repeat):
        till = kind in "tT"
        skip = 1 if (till and repeat) else 0
        if kind in "ft":
            idx = line.find(ch, col + 1 + skip)
            if idx < 0:
                return col
            return idx - 1 if till else idx
        idx = line.rfind(ch, 0, max(col - skip, 0))
        if idx < 0:
            return col
        return idx + 1 if till else idx

    flip = {"f": "F", "F": "f", "t": "T", "T": "t"}
    last = None
    i = 0
    while i < len(keys):
        k = keys[i]
        if k in "fFtT" and i + 1 < len(keys):
            last = (k, keys[i + 1])
            col = run(k, keys[i + 1], col, False)
            i += 2
            continue
        if last is not None:
            if k == ";":
                col = run(last[0], last[1], col, True)
            elif k == ",":
                col = run(flip[last[0]], last[1], col, True)
        i += 1
    return col
''',
    tests=[
        ["a, b, c, d", 0, "f,;"],
        ["a, b, c, d", 0, "t,;;"],
        ["a, b, c, d", 9, "F,,"],
        ["a, b, c, d", 0, ";,"],
        ["a, b, c, d", 0, "fz;"],
        ["a, b, c, d", 0, "f,;;;;"],
        ["a, b, c, d", 0, "f,;;,"],
        ["a, b, c, d", 9, "T,;"],
        ["a, b, c, d", 0, "t,t,"],
        ["key=value;other=1", 0, "f;"],
        ["key=value;other=1", 0, "f=;,"],
        ["x,,y", 0, "t,;"],
        ["x,,y", 3, "T,;"],
        ["fff", 0, "ff;"],
        ["", 0, "fa;"],
        ["path/to/some/file.txt", 20, "F/;,"],
        ["path/to/some/file.txt", 0, "t/;,"],
        ["a, b, c, d", 0, "f,;,;;"],
    ],
    examples=3,
    wrong_solutions=[
        '''def findChar(line, col, keys):
    def run(kind, ch, col, repeat):
        till = kind in "tT"
        if kind in "ft":
            idx = line.find(ch, col + 1)
            if idx < 0:
                return col
            return idx - 1 if till else idx
        idx = line.rfind(ch, 0, max(col, 0))
        if idx < 0:
            return col
        return idx + 1 if till else idx
    flip = {"f": "F", "F": "f", "t": "T", "T": "t"}
    last = None
    i = 0
    while i < len(keys):
        k = keys[i]
        if k in "fFtT" and i + 1 < len(keys):
            last = (k, keys[i + 1])
            col = run(k, keys[i + 1], col, False)
            i += 2
            continue
        if last is not None:
            if k == ";":
                col = run(last[0], last[1], col, True)
            elif k == ",":
                col = run(flip[last[0]], last[1], col, True)
        i += 1
    return col
''',
        '''def findChar(line, col, keys):
    def run(kind, ch, col, repeat):
        till = kind in "tT"
        skip = 1 if (till and repeat) else 0
        if kind in "ft":
            idx = line.find(ch, col + 1 + skip)
            if idx < 0:
                return col
            return idx - 1 if till else idx
        idx = line.rfind(ch, 0, max(col - skip, 0))
        if idx < 0:
            return col
        return idx + 1 if till else idx
    flip = {"f": "F", "F": "f", "t": "T", "T": "t"}
    last = None
    i = 0
    while i < len(keys):
        k = keys[i]
        if k == ";" and last:
            col = run(last[0], last[1], col, True)
        elif k == "," and last:
            last = (flip[last[0]], last[1])
            col = run(last[0], last[1], col, True)
        elif k in "fFtT" and i + 1 < len(keys):
            last = (k, keys[i + 1])
            col = run(k, keys[i + 1], col, False)
            i += 1
        i += 1
    return col
''',
    ],
    guide=dict(
        prereqs="The *Motions* lesson (find by character). `str.find` / `str.rfind` with start and end bounds.",
        intuition="There are really two commands (search right, search left) and one modifier (stop on the target or "
                  "next to it). `;` and `,` replay a remembered pair *(kind, char)*; `,` flips the direction for one "
                  "replay only. The single subtle rule is the skip that keeps a repeated `t` from getting stuck.",
        hints=[
            "Parse two characters at a time for `f/F/t/T`, one at a time for `;` and `,`.",
            "Write one helper `run(kind, ch, col, repeat)`; `,` just calls it with the flipped kind.",
            "For a repeated `t`, start searching at `col + 2`; for a repeated `T`, search the slice `[0, col - 1)`.",
        ],
        brute_force="Scan character by character with explicit loops instead of `find`/`rfind`. Same complexity, more "
                    "places for an off-by-one.",
        approach="Keep `last = (kind, char)`. For each command compute the search window, look for the character, and "
                 "convert the hit to a landing column (`idx`, `idx - 1` or `idx + 1`).\n\n"
                 "**Dry run** `a, b, c, d` from 0 with `t,;;`: `t,` finds the comma at 1, lands on 0. `;` repeats with "
                 "the skip: search from column 2, comma at 4, land on 3. `;` again: search from 5, comma at 7, land on 6.",
        complexity="O(len(keys) × n) time, O(1) space.",
        pitfalls="- Treating `;` after `f` as a command: in `f;` the semicolon is the target.\n- Letting `,` overwrite "
                 "the remembered direction; after `f,` then `,` then `;`, the `;` still searches right.\n- A repeated "
                 "`t` without the skip finds the same occurrence forever.\n- `rfind(ch, 0, end)` with a negative `end` "
                 "counts from the right; clamp it to 0.",
        follow_up="Add counts (`2f,`) and use the result as an operator target: `dt,` deletes up to but not including "
                  "the comma, `df,` includes it.",
    ),
),
# ------------------------------------------------------------------ vim-text-object-word
dict(
    id="vim-text-object-word",
    title="Resolve iw and aw",
    difficulty="Medium",
    pattern="Vim text objects",
    entry="wordObject",
    description=r"""
Text objects select a region *around the cursor*, wherever in the region the cursor happens to be.
Resolve the two word objects on a single line and return the selection as a half-open range `[start, end)`.

Character classes: **blank** (space, tab), **keyword** (`A-Za-z0-9_`), **punctuation** (everything else).
A *run* is a maximal stretch of characters of one class.

**`iw` (inner word)** selects the run under the cursor, whatever its class. On a run of blanks, `iw`
selects those blanks.

**`aw` (a word)**:

- cursor on a non-blank run: the run **plus the blanks that follow it**. If no blanks follow (the run is
  followed by another non-blank run or by the end of the line), take the blanks **before** it instead. If
  there are none on either side, just the run.
- cursor on a blank run: the blanks **plus the non-blank run that follows**. If nothing follows, just the blanks.

An empty line yields `[0, 0]`.

Write `wordObject(line, col, obj)` with `obj` equal to `"iw"` or `"aw"`.

**Example:** `line = "let total = 0"`, `col = 6`, `obj = "iw"` → `[4, 9]`

**Example:** same line, `col = 6`, `obj = "aw"` → `[4, 10]` (deleting it leaves `let = 0`)

**Example:** `line = "drop the last"`, `col = 10`, `obj = "aw"` → `[8, 13]` (no blanks after, so take the one before)
""",
    starter='''def wordObject(line: str, col: int, obj: str) -> List[int]:
    pass
''',
    solution='''def wordObject(line, col, obj):
    n = len(line)
    if n == 0:
        return [0, 0]

    def cls(i):
        ch = line[i]
        if ch in " \\t":
            return 0
        return 1 if (ch.isalnum() or ch == "_") else 2

    def run(i):
        c = cls(i)
        s = i
        while s > 0 and cls(s - 1) == c:
            s -= 1
        e = i + 1
        while e < n and cls(e) == c:
            e += 1
        return s, e

    s, e = run(col)
    if obj == "iw":
        return [s, e]
    if cls(col) == 0:
        if e < n:
            _, e2 = run(e)
            return [s, e2]
        return [s, e]
    if e < n and cls(e) == 0:
        _, e2 = run(e)
        return [s, e2]
    if s > 0 and cls(s - 1) == 0:
        s2, _ = run(s - 1)
        return [s2, e]
    return [s, e]
''',
    tests=[
        ["let total = 0", 6, "iw"],
        ["let total = 0", 6, "aw"],
        ["drop the last", 10, "aw"],
        ["drop the last", 10, "iw"],
        ["", 0, "aw"],
        ["solo", 2, "aw"],
        ["solo", 0, "iw"],
        ["a   b", 2, "iw"],
        ["a   b", 2, "aw"],
        ["end   ", 4, "aw"],
        ["end   ", 1, "aw"],
        ["obj.method(arg)", 5, "iw"],
        ["obj.method(arg)", 5, "aw"],
        ["obj.method(arg)", 3, "iw"],
        ["x = obj.attr", 9, "aw"],
        ["  lead", 3, "aw"],
        ["tab\tsep\tcols", 5, "aw"],
    ],
    examples=3,
    wrong_solutions=[
        '''def wordObject(line, col, obj):
    n = len(line)
    if n == 0:
        return [0, 0]
    def cls(i):
        ch = line[i]
        if ch in " \\t":
            return 0
        return 1 if (ch.isalnum() or ch == "_") else 2
    def run(i):
        c = cls(i)
        s = i
        while s > 0 and cls(s - 1) == c:
            s -= 1
        e = i + 1
        while e < n and cls(e) == c:
            e += 1
        return s, e
    s, e = run(col)
    if obj == "iw":
        return [s, e]
    if e < n and cls(e) == 0:
        _, e2 = run(e)
        return [s, e2]
    return [s, e]
''',
        '''def wordObject(line, col, obj):
    n = len(line)
    if n == 0:
        return [0, 0]
    s = col
    while s > 0 and (line[s - 1] in " \\t") == (line[col] in " \\t"):
        s -= 1
    e = col + 1
    while e < n and (line[e] in " \\t") == (line[col] in " \\t"):
        e += 1
    if obj == "iw":
        return [s, e]
    while e < n and line[e] in " \\t":
        e += 1
    return [s, e]
''',
    ],
    guide=dict(
        prereqs="The *Text objects* lesson. `vim-word-forward` for the character classes.",
        intuition="Find the run under the cursor by growing left and right while the class stays the same: that is "
                  "`iw`. `aw` exists so that deleting a word leaves tidy spacing, so it grabs one neighbouring stretch "
                  "of blanks, preferring the trailing one.",
        hints=[
            "Write `run(i)` returning the half-open bounds of the run containing index `i`; you will call it up to twice.",
            "For `aw` on a non-blank: check `line[e]` first (trailing blanks), then `line[s-1]` (leading blanks).",
            "For `aw` on blanks, the second call is `run(e)` to swallow the following word.",
        ],
        brute_force="Tokenise the whole line into runs, find the one containing the cursor, and look at its neighbours "
                    "in the token list. O(n) as well, but builds a list you do not need.",
        approach="Compute `(s, e) = run(col)`. Return it for `iw`. For `aw` extend by exactly one neighbouring run "
                 "according to the rules.\n\n**Dry run** `drop the last`, col 10, `aw`: run is `last` = [9, 13). "
                 "`e == n`, so no trailing blanks. `line[8]` is a blank; its run is [8, 9). Result [8, 13).",
        complexity="O(n) time, O(1) space.",
        pitfalls="- Returning an inclusive end: the range is half-open.\n- Taking both leading *and* trailing blanks; "
                 "`aw` takes one side only.\n- Forgetting that punctuation forms its own run: in `obj.method`, `iw` on "
                 "the dot is just the dot.\n- `aw` at the end of a line must fall back to the leading blanks, otherwise "
                 "`daw` on the last word would leave trailing whitespace.",
        follow_up="Implement `iW`/`aW`, and `daw` followed by `.` to delete several words in a row.",
    ),
),
# ------------------------------------------------------------------ vim-text-object-quote
dict(
    id="vim-text-object-quote",
    title="Resolve i\" and a\"",
    difficulty="Medium",
    pattern="Vim text objects",
    entry="quoteObject",
    description=r"""
Resolve the quote text objects on one line. `obj` is `i"`, `a"`, `i'` or `a'`; the second character is the quote
character `q`. There are no escaped quotes in this model. Return a half-open range `[start, end)`, or `[-1, -1]`
when no quoted string can be found.

**Step 1: find the pair of quotes** (`open`, `close` are their columns):

- If the character under the cursor is `q`: count the `q` characters from the start of the line up to and
  including the cursor. An **odd** count means the cursor is on an opening quote; `close` is the next `q` to the
  right. An **even** count means it is on a closing quote; `open` is the previous `q` to the left.
- Otherwise, if there is a `q` somewhere left of the cursor: `open` is the nearest one on the left and `close`
  the nearest one on the right.
- Otherwise (no `q` to the left): look ahead. `open` is the first `q` right of the cursor and `close` the next
  `q` after that. This is what lets `ci"` work from the start of a line.
- If the needed partner does not exist, return `[-1, -1]`.

**Step 2: choose the range**

- `i` → `[open + 1, close)` (may be empty)
- `a` → both quotes, **plus the blanks (spaces/tabs) immediately after the closing quote**; if there are none,
  plus the blanks immediately before the opening quote.

**Example:** `line = 'msg = "hi there" + name'`, `col = 9`, `obj = 'i"'` → `[7, 15]`

**Example:** same line, `col = 0`, `obj = 'a"'` → `[6, 17]` (looked ahead; trailing space included)

**Example:** `line = "no quotes here"`, `col = 3`, `obj = 'i"'` → `[-1, -1]`
""",
    starter='''def quoteObject(line: str, col: int, obj: str) -> List[int]:
    pass
''',
    solution='''def quoteObject(line, col, obj):
    kind, q = obj[0], obj[1]
    n = len(line)
    if n == 0:
        return [-1, -1]
    if line[col] == q:
        if line.count(q, 0, col + 1) % 2 == 1:
            o = col
            c = line.find(q, col + 1)
        else:
            c = col
            o = line.rfind(q, 0, col)
    else:
        o = line.rfind(q, 0, col)
        if o >= 0:
            c = line.find(q, col + 1)
        else:
            o = line.find(q, col + 1)
            c = line.find(q, o + 1) if o >= 0 else -1
    if o < 0 or c < 0:
        return [-1, -1]
    if kind == "i":
        return [o + 1, c]
    s, e = o, c + 1
    if e < n and line[e] in " \\t":
        while e < n and line[e] in " \\t":
            e += 1
    else:
        while s > 0 and line[s - 1] in " \\t":
            s -= 1
    return [s, e]
''',
    tests=[
        ['msg = "hi there" + name', 9, 'i"'],
        ['msg = "hi there" + name', 0, 'a"'],
        ["no quotes here", 3, 'i"'],
        ['msg = "hi there" + name', 6, 'i"'],
        ['msg = "hi there" + name', 15, 'i"'],
        ['msg = "hi there" + name', 18, 'i"'],
        ['print("a", "b")', 9, 'i"'],
        ['print("a", "b")', 6, 'a"'],
        ['print("a", "b")', 12, 'a"'],
        ['x = ""', 4, 'i"'],
        ['x = ""', 5, 'a"'],
        ["it's fine", 0, "i'"],
        ["d = {'k': 'v'}", 0, "a'"],
        ["d = {'k': 'v'}", 11, "i'"],
        ['"only one', 3, 'i"'],
        ["", 0, 'i"'],
        ['say "hi"', 6, 'a"'],
        ['mixed "it\'s" ok', 9, 'i"'],
    ],
    examples=3,
    wrong_solutions=[
        '''def quoteObject(line, col, obj):
    kind, q = obj[0], obj[1]
    o = line.rfind(q, 0, col + 1)
    c = line.find(q, col + 1)
    if o < 0 or c < 0:
        return [-1, -1]
    if kind == "i":
        return [o + 1, c]
    return [o, c + 1]
''',
        '''def quoteObject(line, col, obj):
    kind, q = obj[0], obj[1]
    n = len(line)
    idx = [i for i, ch in enumerate(line) if ch == q]
    for a, b in zip(idx[0::2], idx[1::2]):
        if col <= b:
            if kind == "i":
                return [a + 1, b]
            e = b + 1
            while e < n and line[e] in " \\t":
                e += 1
            return [a, e]
    return [-1, -1]
''',
    ],
    guide=dict(
        prereqs="The *Text objects* lesson (delimited objects). `str.find`, `str.rfind`, `str.count` with bounds.",
        intuition="Quotes are harder than brackets because the opening and closing characters are identical. Vim "
                  "resolves the ambiguity with a parity count when the cursor is *on* a quote, and with nearest "
                  "neighbours otherwise. The look-ahead case is a convenience so you do not have to move onto the "
                  "string first.",
        hints=[
            "Split into the two cases *cursor on q* and *cursor not on q* before writing any search.",
            "`line.count(q, 0, col + 1) % 2` tells you opening versus closing.",
            "For `a`: extend right over blanks; only if you did not move, extend left over blanks.",
        ],
        brute_force="Pair the quotes two by two from the start of the line and return the first pair that ends at or "
                    "after the cursor. That matches Vim in the common cases but gives a different answer when the "
                    "cursor sits *between* two strings, where this model uses the nearest quote on each side.",
        approach="Find `open`/`close` using the three-way rule, bail out with `[-1, -1]` if either is missing, then "
                 "build the range.\n\n**Dry run** `msg = \"hi there\" + name`, col 0, `a\"`: cursor is not on a quote and "
                 "nothing lies to its left, so look ahead: open = 6, close = 15. Range starts as [6, 16); column 16 is "
                 "a space, extend to 17. Result [6, 17).",
        complexity="O(n) time, O(1) space.",
        pitfalls="- Pairing quotes from the start of the line in every case.\n- Forgetting the look-ahead when the "
                 "cursor is before the first quote.\n- `a\"` takes trailing blanks *or* leading blanks, never both.\n"
                 "- An empty string `\"\"` gives an empty inner range, not a failure.",
        follow_up="Support backslash-escaped quotes (Vim honours the `quoteescape` option), and the backtick object.",
    ),
),
# ------------------------------------------------------------------ vim-text-object-bracket
dict(
    id="vim-text-object-bracket",
    title="Resolve i( a( i[ a[ i{ a{",
    difficulty="Medium",
    pattern="Vim text objects",
    entry="bracketObject",
    description=r"""
Resolve bracket text objects on one line. `obj` is two characters: `i` or `a`, followed by one of

| second character | pair |
|---|---|
| `(` `)` or `b` | `( )` |
| `[` or `]` | `[ ]` |
| `{` `}` or `B` | `{ }` |

Only the chosen pair type matters; other bracket types are ordinary characters.

**Finding the pair.** The object is the innermost pair that *encloses* the cursor, where a cursor sitting on
either bracket of a pair counts as enclosed by that pair:

- cursor on an opening bracket → that is `open`;
- cursor on a closing bracket → `open` is its matching opener (scan left, tracking nesting depth);
- otherwise scan left from the cursor for the first *unmatched* opener.

Then `close` is the bracket matching `open` (scan right, tracking depth). If either scan fails, return `[-1, -1]`.
Unlike the quote objects, bracket objects in this model never look ahead.

**Range** (half-open): `i` → `[open + 1, close)`, `a` → `[open, close + 1)`.

Write `bracketObject(line, col, obj)`.

**Example:** `line = "run(a, f(b), c)"`, `col = 5`, `obj = "i("` → `[4, 14]`

**Example:** same line, `col = 9`, `obj = "a)"` → `[8, 11]`

**Example:** same line, `col = 1`, `obj = "ib"` → `[-1, -1]`
""",
    starter='''def bracketObject(line: str, col: int, obj: str) -> List[int]:
    pass
''',
    solution='''def bracketObject(line, col, obj):
    pairs = {"(": "()", ")": "()", "b": "()", "[": "[]", "]": "[]",
             "{": "{}", "}": "{}", "B": "{}"}
    op, cl = pairs[obj[1]]
    n = len(line)
    if n == 0:
        return [-1, -1]
    o = -1
    if line[col] == op:
        o = col
    else:
        depth = 0
        i = col - 1
        while i >= 0:
            if line[i] == cl:
                depth += 1
            elif line[i] == op:
                if depth == 0:
                    o = i
                    break
                depth -= 1
            i -= 1
    if o < 0:
        return [-1, -1]
    depth = 0
    c = -1
    for i in range(o + 1, n):
        if line[i] == op:
            depth += 1
        elif line[i] == cl:
            if depth == 0:
                c = i
                break
            depth -= 1
    if c < 0:
        return [-1, -1]
    return [o + 1, c] if obj[0] == "i" else [o, c + 1]
''',
    tests=[
        ["run(a, f(b), c)", 5, "i("],
        ["run(a, f(b), c)", 9, "a)"],
        ["run(a, f(b), c)", 1, "ib"],
        ["run(a, f(b), c)", 3, "i("],
        ["run(a, f(b), c)", 14, "a("],
        ["run(a, f(b), c)", 8, "ib"],
        ["run(a, f(b), c)", 10, "i("],
        ["run(a, f(b), c)", 12, "ab"],
        ["xs[i][j] = {k: [1, 2]}", 3, "i["],
        ["xs[i][j] = {k: [1, 2]}", 17, "i["],
        ["xs[i][j] = {k: [1, 2]}", 13, "aB"],
        ["xs[i][j] = {k: [1, 2]}", 17, "i{"],
        ["f()", 1, "i("],
        ["f()", 2, "a("],
        ["(open only", 4, "i("],
        ["close only)", 4, "i)"],
        ["", 0, "i("],
        ["((()))", 2, "a("],
        ["((()))", 4, "i)"],
        ["a(b]c)d", 3, "i("],
    ],
    examples=3,
    wrong_solutions=[
        '''def bracketObject(line, col, obj):
    pairs = {"(": "()", ")": "()", "b": "()", "[": "[]", "]": "[]",
             "{": "{}", "}": "{}", "B": "{}"}
    op, cl = pairs[obj[1]]
    o = line.rfind(op, 0, col + 1)
    c = line.find(cl, col)
    if o < 0 or c < 0:
        return [-1, -1]
    return [o + 1, c] if obj[0] == "i" else [o, c + 1]
''',
        '''def bracketObject(line, col, obj):
    pairs = {"(": "()", ")": "()", "b": "()", "[": "[]", "]": "[]",
             "{": "{}", "}": "{}", "B": "{}"}
    op, cl = pairs[obj[1]]
    n = len(line)
    o = -1
    depth = 0
    i = col - 1
    while i >= 0:
        if line[i] == cl:
            depth += 1
        elif line[i] == op:
            if depth == 0:
                o = i
                break
            depth -= 1
        i -= 1
    if o < 0:
        return [-1, -1]
    depth = 0
    for i in range(o + 1, n):
        if line[i] == op:
            depth += 1
        elif line[i] == cl:
            if depth == 0:
                return [o + 1, i] if obj[0] == "i" else [o, i + 1]
            depth -= 1
    return [-1, -1]
''',
    ],
    guide=dict(
        prereqs="The *Text objects* lesson. Bracket matching with a depth counter (the classic valid-parentheses idea).",
        intuition="Walk left counting closers you pass; an opener cancels one pending closer, and the first opener "
                  "seen with nothing pending is the one that encloses the cursor. From there walk right with the "
                  "mirror-image counter to find its partner.",
        hints=[
            "Map the second character of `obj` to an `(open, close)` pair first; `b` and `B` are aliases.",
            "Special-case the cursor sitting on the opener. A cursor on the closer needs no special case if your left scan starts at `col - 1`.",
            "The right scan must start at `open + 1`, not at the cursor, or nested pairs between them will be miscounted.",
        ],
        brute_force="Precompute all matching pairs with a stack in one pass, then choose the pair with the largest "
                    "`open` satisfying `open <= col <= close`. O(n) time and O(n) space; perfectly acceptable.",
        approach="Left scan for `open`, right scan for `close`, then slice.\n\n**Dry run** `run(a, f(b), c)`, col 5, "
                 "`i(`: `line[5]` is a comma. Scan left: 4 `a`, 3 `(` with depth 0 → open = 3. Scan right from 4: `(` at "
                 "8 → depth 1, `)` at 10 → depth 0, `)` at 14 with depth 0 → close = 14. Inner range [4, 14).",
        complexity="O(n) time, O(1) space.",
        pitfalls="- `rfind`/`find` for the nearest brackets ignores nesting and breaks on `f(g(x), y)`.\n- Forgetting "
                 "that the cursor may be on the opener itself.\n- Counting other bracket types: `a(b]c)` is fine for `i(`."
                 "\n- Empty pairs `()` produce an empty inner range.",
        follow_up="Add the `<`/`>` pair and multi-line buffers; then compare with `%`, which jumps between the same partners.",
    ),
),
# ------------------------------------------------------------------ vim-text-object-tag
dict(
    id="vim-text-object-tag",
    title="Resolve it and at",
    difficulty="Hard",
    pattern="Vim text objects",
    entry="tagObject",
    description=r"""
Resolve the tag text objects on one line of markup.

**Input guarantees.** The line contains opening tags `<name>` or `<name attributes>` and closing tags `</name>`,
where `name` matches `[A-Za-z][A-Za-z0-9-]*`. There are no self-closing tags, no comments, and `<` / `>` appear
only as tag delimiters. Tags are properly nested and every opening tag has its closing tag.

An **element** runs from the `<` of its opening tag to the `>` of its closing tag. The object refers to the
**innermost element that contains the cursor column** (a cursor anywhere on the opening or closing tag is inside
that element).

Return a half-open range `[start, end)`:

- `it` → the content between the opening tag's `>` and the closing tag's `<` (may be empty);
- `at` → the whole element, both tags included.

If the cursor is not inside any element, return `[-1, -1]`.

Write `tagObject(line, col, obj)`.

**Example:** `line = '<li><a href="/x">Docs</a> now</li>'`, `col = 18`, `obj = "it"` → `[17, 21]` (`Docs`)

**Example:** same line, `col = 27`, `obj = "it"` → `[4, 29]`

**Example:** same line, `col = 5`, `obj = "at"` → `[4, 25]`
""",
    starter='''def tagObject(line: str, col: int, obj: str) -> List[int]:
    pass
''',
    solution='''import re

def tagObject(line, col, obj):
    stack = []
    best = None
    for m in re.finditer(r"<(/?)([A-Za-z][A-Za-z0-9-]*)[^>]*>", line):
        if not m.group(1):
            stack.append((m.start(), m.end()))
        elif stack:
            os_, oe = stack.pop()
            cs, ce = m.start(), m.end()
            if os_ <= col < ce:
                if best is None or os_ > best[0]:
                    best = (os_, oe, cs, ce)
    if best is None:
        return [-1, -1]
    os_, oe, cs, ce = best
    return [oe, cs] if obj == "it" else [os_, ce]
''',
    tests=[
        ['<li><a href="/x">Docs</a> now</li>', 18, "it"],
        ['<li><a href="/x">Docs</a> now</li>', 27, "it"],
        ['<li><a href="/x">Docs</a> now</li>', 5, "at"],
        ['<li><a href="/x">Docs</a> now</li>', 0, "it"],
        ['<li><a href="/x">Docs</a> now</li>', 33, "at"],
        ['<li><a href="/x">Docs</a> now</li>', 22, "it"],
        ["plain text", 3, "it"],
        ["a <b>bold</b> z", 0, "at"],
        ["a <b>bold</b> z", 14, "it"],
        ["a <b>bold</b> z", 2, "it"],
        ["<p></p>", 3, "it"],
        ["<p></p>", 3, "at"],
        ["<div><div>x</div><div>y</div></div>", 22, "it"],
        ["<div><div>x</div><div>y</div></div>", 17, "at"],
        ["<div><div>x</div><div>y</div></div>", 30, "it"],
        ["<my-tag><i>a</i><i>b</i></my-tag>", 16, "at"],
        ["", 0, "it"],
    ],
    examples=3,
    wrong_solutions=[
        '''import re

def tagObject(line, col, obj):
    o = line.rfind(">", 0, col + 1)
    c = line.find("</", col)
    if o < 0 or c < 0:
        return [-1, -1]
    if obj == "it":
        return [o + 1, c]
    s = line.rfind("<", 0, o)
    e = line.find(">", c)
    return [s, e + 1]
''',
        '''import re

def tagObject(line, col, obj):
    stack = []
    best = None
    for m in re.finditer(r"<(/?)([A-Za-z][A-Za-z0-9-]*)[^>]*>", line):
        if not m.group(1):
            stack.append((m.start(), m.end()))
        elif stack:
            os_, oe = stack.pop()
            cs, ce = m.start(), m.end()
            if os_ <= col < ce:
                best = (os_, oe, cs, ce)
    if best is None:
        return [-1, -1]
    os_, oe, cs, ce = best
    return [oe, cs] if obj == "it" else [os_, ce]
''',
    ],
    guide=dict(
        prereqs="`vim-text-object-bracket`. Stacks for matching nested delimiters. `re.finditer`.",
        intuition="Tags are brackets with names. Scan the tags left to right, pushing openers and popping on closers: "
                  "every pop yields one complete element. Among the elements whose span covers the cursor, the "
                  "innermost is the one that starts furthest to the right.",
        hints=[
            "One regular expression can find both kinds of tag; a captured `/` tells them apart.",
            "Store `(start_of_open_tag, end_of_open_tag)` on the stack so both `it` and `at` can be answered later.",
            "Containment test: `open_start <= col < close_end`. Keep the candidate with the largest `open_start`.",
        ],
        brute_force="For every opening tag, search forward for its partner by counting same-name openers and closers, "
                    "and keep the tightest element that contains the cursor. O(t²) for t tags.",
        approach="Stack pass over the tags; on each closer, pop, test containment and update the best candidate.\n\n"
                 "**Dry run** `<li><a href=\"/x\">Docs</a> now</li>`, col 27: `<li>` pushed (0, 4); `<a …>` pushed "
                 "(4, 17); `</a>` at [21, 25) pops the anchor, 4 <= 27 < 25 is false; `</li>` at [29, 34) pops the "
                 "list item, 0 <= 27 < 34 holds → best. `it` = [4, 29).",
        complexity="O(n) time, O(depth) space.",
        pitfalls="- Using the nearest `>` on the left and `</` on the right ignores nesting and siblings.\n- Because "
                 "closers arrive innermost-first for nested elements, simply keeping the *last* containing element "
                 "returns the outermost one.\n- A cursor on the closing tag belongs to that element.\n- An empty "
                 "element gives an empty `it` range, not a failure.",
        follow_up="In real Vim, repeating `it` in Visual mode expands to the parent element. Model that with a `count` "
                  "argument that climbs `count - 1` levels.",
    ),
),
]
