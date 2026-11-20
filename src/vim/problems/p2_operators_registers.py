"""Practical Vim problems, part 2: operators, keystroke counting, a tiny Normal-mode simulator,
registers and macros. All columns and rows are 0-based."""

DELETE_SOLUTION = '''def applyDelete(line, col, cmd):
    n = len(line)
    if n == 0:
        return ["", 0]

    def cls(i):
        ch = line[i]
        if ch in " \\t":
            return 0
        return 1 if (ch.isalnum() or ch == "_") else 2

    s, e = col, col
    if cmd == "x":
        e = col + 1
    elif cmd == "d$":
        e = n
    elif cmd == "d0":
        s = 0
    elif cmd == "dw":
        i = col
        t = cls(i)
        if t:
            while i < n and cls(i) == t:
                i += 1
        while i < n and cls(i) == 0:
            i += 1
        e = i
    elif cmd == "de":
        i = col + 1
        while i < n and cls(i) == 0:
            i += 1
        if i >= n:
            e = n
        else:
            t = cls(i)
            while i + 1 < n and cls(i + 1) == t:
                i += 1
            e = i + 1
    elif cmd == "db":
        i = col - 1
        while i >= 0 and cls(i) == 0:
            i -= 1
        if i < 0:
            s = 0
        else:
            t = cls(i)
            while i - 1 >= 0 and cls(i - 1) == t:
                i -= 1
            s = i
    else:
        idx = line.find(cmd[2], col + 1)
        if idx < 0:
            return [line, col]
        e = idx if cmd[1] == "t" else idx + 1
    new = line[:s] + line[e:]
    return [new, max(0, min(s, len(new) - 1))]
'''

CHANGE_SOLUTION = '''def applyChange(line, col, cmd, text):
    n = len(line)

    def cls(i):
        ch = line[i]
        if ch in " \\t":
            return 0
        return 1 if (ch.isalnum() or ch == "_") else 2

    def quote(q):
        if n == 0:
            return None
        if line[col] == q:
            if line.count(q, 0, col + 1) % 2 == 1:
                o, c = col, line.find(q, col + 1)
            else:
                o, c = line.rfind(q, 0, col), col
        else:
            o = line.rfind(q, 0, col)
            if o >= 0:
                c = line.find(q, col + 1)
            else:
                o = line.find(q, col + 1)
                c = line.find(q, o + 1) if o >= 0 else -1
        if o < 0 or c < 0:
            return None
        return o + 1, c

    def bracket(op, cl):
        if n == 0:
            return None
        o = -1
        if line[col] == op:
            o = col
        else:
            depth = 0
            for i in range(col - 1, -1, -1):
                if line[i] == cl:
                    depth += 1
                elif line[i] == op:
                    if depth == 0:
                        o = i
                        break
                    depth -= 1
        if o < 0:
            return None
        depth = 0
        for i in range(o + 1, n):
            if line[i] == op:
                depth += 1
            elif line[i] == cl:
                if depth == 0:
                    return o + 1, i
                depth -= 1
        return None

    rng = None
    if cmd == "cc":
        rng = (0, n)
    elif cmd == "C":
        rng = (col, n)
    elif cmd == "s":
        rng = (col, min(col + 1, n))
    elif cmd == "cw":
        if n == 0:
            rng = (0, 0)
        else:
            t = cls(col)
            i = col
            while i < n and cls(i) == t:
                i += 1
            rng = (col, i)
    elif cmd[:2] in ("ct", "cf"):
        idx = line.find(cmd[2], col + 1)
        if idx >= 0:
            rng = (col, idx if cmd[1] == "t" else idx + 1)
    elif cmd[:2] == "ci":
        ch = cmd[2]
        if ch in "\\"'":
            rng = quote(ch)
        else:
            op, cl = {"(": "()", ")": "()", "[": "[]", "]": "[]", "{": "{}", "}": "{}"}[ch]
            rng = bracket(op, cl)
    if rng is None:
        return [line, col]
    s, e = rng
    new = line[:s] + text + line[e:]
    newcol = s + len(text) - 1 if text else s - 1
    return [new, max(newcol, 0)]
'''

GOLF_SOLUTION = '''import re

_NAME = r"(?:Esc|CR|Enter|Return|Tab|BS|Del|Space|lt|Bar|Up|Down|Left|Right|Home|End|F[0-9]{1,2})"
_KEY = re.compile(r"<(?:(?:[CSAM]-)+(?:" + _NAME + r"|.)|" + _NAME + r")>", re.I | re.S)

def golfScore(keys):
    i = 0
    total = 0
    while i < len(keys):
        m = _KEY.match(keys, i) if keys[i] == "<" else None
        i = m.end() if m else i + 1
        total += 1
    return total
'''

DOT_SOLUTION = '''import re

def dotPlan(text, old, new):
    k = len(re.findall(r"(?<![A-Za-z0-9_])" + re.escape(old) + r"(?![A-Za-z0-9_])", text))
    if k == 0:
        return [0, 0, 0]
    dot_total = (len(old) + 6) + (len(new) + 3) + 2 * (k - 1)
    sub_total = len(old) + len(new) + 12
    return [k - 1, dot_total, sub_total]
'''

SIM_SOLUTION = '''def normalSim(lines, keys):
    buf = list(lines)
    row = col = 0
    reg = None

    def clamp(c):
        return max(0, min(c, len(buf[row]) - 1))

    def first_nonblank(s):
        for i, ch in enumerate(s):
            if ch not in " \\t":
                return i
        return 0

    i = 0
    while i < len(keys):
        k = keys[i]
        line = buf[row]
        if k == "h":
            col = clamp(col - 1)
        elif k == "l":
            col = clamp(col + 1)
        elif k == "j":
            if row + 1 < len(buf):
                row += 1
                col = clamp(col)
        elif k == "k":
            if row > 0:
                row -= 1
                col = clamp(col)
        elif k == "0":
            col = 0
        elif k == "$":
            col = clamp(len(line))
        elif k == "x":
            if line:
                reg = (line[col], "c")
                buf[row] = line[:col] + line[col + 1:]
                col = clamp(col)
        elif k == "d":
            i += 1
            reg = (line, "l")
            del buf[row]
            if not buf:
                buf.append("")
            row = min(row, len(buf) - 1)
            col = first_nonblank(buf[row])
        elif k == "y":
            i += 1
            reg = (line, "l")
        elif k in "pP":
            if reg is not None:
                text, kind = reg
                if kind == "l":
                    if k == "p":
                        row += 1
                    buf.insert(row, text)
                    col = first_nonblank(text)
                else:
                    at = col + 1 if (k == "p" and line) else col
                    buf[row] = line[:at] + text + line[at:]
                    col = at + len(text) - 1
        elif k == "J":
            if row + 1 < len(buf):
                nxt = buf[row + 1].lstrip(" \\t")
                sep = " "
                if line == "" or nxt == "" or line[-1] in " \\t" or nxt[0] == ")":
                    sep = ""
                buf[row] = line + sep + nxt
                del buf[row + 1]
                col = clamp(len(line))
        elif k == "r":
            i += 1
            if line:
                buf[row] = line[:col] + keys[i] + line[col + 1:]
        elif k == "~":
            if line:
                buf[row] = line[:col] + line[col].swapcase() + line[col + 1:]
                col = clamp(col + 1)
        i += 1
    return [buf, row, col]
'''

REG_SOLUTION = '''def registerSim(ops, queries):
    reg = {}
    for kind, name, text in ops:
        if name == "_":
            continue
        if name == "":
            if kind == "y":
                reg["0"] = text
            elif "\\n" in text:
                for d in range(9, 1, -1):
                    if str(d - 1) in reg:
                        reg[str(d)] = reg[str(d - 1)]
                reg["1"] = text
            else:
                reg["-"] = text
            reg['"'] = text
        elif name.isupper():
            low = name.lower()
            reg[low] = reg.get(low, "") + text
            reg['"'] = reg[low]
        else:
            reg[name] = text
            reg['"'] = text
    return [reg.get(q, "") for q in queries]
'''

MACRO_SOLUTION = '''def expandMacro(registers, keys):
    out = []
    state = {"last": None}

    def run(s):
        i = 0
        n = len(s)
        while i < n:
            j = i
            if s[j] in "123456789":
                while j < n and s[j].isdigit():
                    j += 1
            if j + 1 < n and s[j] == "@" and (s[j + 1] == "@" or s[j + 1].islower()):
                count = int(s[i:j]) if j > i else 1
                name = s[j + 1]
                if name == "@":
                    name = state["last"]
                i = j + 2
                if name is None:
                    continue
                for _ in range(count):
                    state["last"] = name
                    run(registers.get(name, ""))
                continue
            if j > i:
                out.append(s[i:j])
                i = j
            else:
                out.append(s[i])
                i += 1

    run(keys)
    return "".join(out)
'''

PROBLEMS = [
# ------------------------------------------------------------------ vim-delete-motion
dict(
    id="vim-delete-motion",
    title="Apply d{motion} to a line",
    difficulty="Medium",
    pattern="Vim operators",
    entry="applyDelete",
    description=r"""
An operator acts on the text between the cursor and wherever the motion would take it. Apply one delete
command to a single line and report the new line and the new cursor column.

Character classes are **blank** (space, tab), **keyword** (`A-Za-z0-9_`) and **punctuation** (the rest); a word
is a maximal run of keyword characters or of punctuation characters.

| `cmd` | text removed (columns, `n = len(line)`) |
|---|---|
| `x` | the character under the cursor |
| `d$` | from the cursor to the end of the line, inclusive |
| `d0` | from column 0 up to, but **not** including, the cursor |
| `dw` | from the cursor up to, not including, the start of the next word (leave the current run if on a non-blank, then skip blanks). If there is no next word, everything to the end of the line. |
| `de` | from the cursor through the end of the word found by: step right one character, skip blanks, slide to the last character of that run. If only blanks (or nothing) lie to the right, everything to the end of the line. |
| `db` | from the start of the word found by stepping left one character, skipping blanks leftwards and sliding to the first character of that run (column 0 if there is none) up to, not including, the cursor |
| `dt{c}` | from the cursor up to, not including, the next `c` strictly right of the cursor |
| `df{c}` | the same but including that `c` |

If the target of `dt`/`df` does not exist, nothing changes and the cursor stays where it was.

**Cursor afterwards:** the column where the deleted text started, clamped so that it is still on a character
(`min(start, len(new_line) - 1)`, and never below 0). On an empty line every command returns `["", 0]`.

Write `applyDelete(line, col, cmd)` returning `[new_line, new_col]`.

**Example:** `line = "retry_count = limit + 1"`, `col = 0`, `cmd = "dw"` → `["= limit + 1", 0]`

**Example:** same line, `col = 14`, `cmd = "d$"` → `["retry_count = ", 13]`

**Example:** `line = "open(path, mode)"`, `col = 5`, `cmd = "dt,"` → `["open(, mode)", 5]`
""",
    starter='''def applyDelete(line: str, col: int, cmd: str) -> list:
    pass
''',
    solution=DELETE_SOLUTION,
    tests=[
        ["retry_count = limit + 1", 0, "dw"],
        ["retry_count = limit + 1", 14, "d$"],
        ["open(path, mode)", 5, "dt,"],
        ["open(path, mode)", 5, "df,"],
        ["open(path, mode)", 5, "dt;"],
        ["open(path, mode)", 5, "dw"],
        ["open(path, mode)", 4, "dw"],
        ["retry_count = limit + 1", 22, "dw"],
        ["retry_count = limit + 1", 11, "dw"],
        ["retry_count = limit + 1", 14, "de"],
        ["retry_count = limit + 1", 18, "de"],
        ["retry_count = limit + 1", 14, "db"],
        ["retry_count = limit + 1", 16, "db"],
        ["retry_count = limit + 1", 0, "db"],
        ["retry_count = limit + 1", 6, "d0"],
        ["abc", 2, "x"],
        ["a", 0, "x"],
        ["", 0, "dw"],
        ["tail   ", 0, "dw"],
        ["tail   ", 3, "de"],
        ["x.y.z", 0, "de"],
        ["a,b,c", 0, "df,"],
    ],
    examples=3,
    wrong_solutions=[
        '''def applyDelete(line, col, cmd):
    n = len(line)
    if n == 0:
        return ["", 0]
    s, e = col, col
    if cmd == "x":
        e = col + 1
    elif cmd == "d$":
        e = n
    elif cmd == "d0":
        s = 0
    elif cmd in ("dw", "de"):
        i = col
        while i < n and line[i] != " ":
            i += 1
        if cmd == "dw":
            while i < n and line[i] == " ":
                i += 1
        e = i
    elif cmd == "db":
        i = col - 1
        while i >= 0 and line[i] == " ":
            i -= 1
        while i >= 0 and line[i] != " ":
            i -= 1
        s = i + 1
    else:
        idx = line.find(cmd[2], col + 1)
        if idx < 0:
            return [line, col]
        e = idx if cmd[1] == "t" else idx + 1
    new = line[:s] + line[e:]
    return [new, max(0, min(s, len(new) - 1))]
''',
        DELETE_SOLUTION.replace("return [new, max(0, min(s, len(new) - 1))]", "return [new, s]"),
        DELETE_SOLUTION.replace('e = idx if cmd[1] == "t" else idx + 1', 'e = idx + 1 if cmd[1] == "t" else idx'),
    ],
    guide=dict(
        prereqs="The *Normal mode grammar* lesson (operator + motion), `vim-word-motions` and `vim-find-char`.",
        intuition="Every command reduces to a half-open slice `[s, e)` of the line to cut out. The motion decides one "
                  "end, the cursor is the other. The only real knowledge is which motions are **exclusive** (`w`, `b`, "
                  "`0`, `t`: the destination character survives) and which are **inclusive** (`e`, `$`, `f`: it is "
                  "deleted too).",
        hints=[
            "Start with `s = e = col` and let each command move exactly one of the two ends.",
            "Reuse the word-motion loops, but for `dw` let the index run to `n` instead of clamping to `n - 1`.",
            "Inclusive motions add one to the end index: `de` ends at `i + 1`, `df` at `idx + 1`.",
        ],
        brute_force="Compute the motion's landing column with a motion function, then post-process: add one for "
                    "inclusive motions and special-case `dw` at the end of the line. Equivalent, but the special case "
                    "is easy to forget because the motion function clamps to the last character.",
        approach="Dispatch on `cmd`, compute `[s, e)`, splice, clamp the cursor.\n\n**Dry run** "
                 "`retry_count = limit + 1`, col 14 (`l`), `db`: step to 13 (blank), skip blanks to 12 (`=`), the run "
                 "`=` starts at 12, so `s = 12`, `e = 14`. Result `retry_count limit + 1`, cursor 12.",
        complexity="O(n) time and space (building the new string).",
        pitfalls="- Mixing up inclusive and exclusive: `dt,` keeps the comma, `df,` removes it.\n- `dw` on the last "
                 "word must delete to the end of the line.\n- After `d$` the cursor cannot stay at `col`; that column "
                 "no longer exists.\n- A failed `dt`/`df` is a no-op, not a delete-to-end.",
        follow_up="Add counts (`d2w`, `2dw`, `d3f,`) and notice that `d2w` and `2dw` give the same result.",
    ),
),
# ------------------------------------------------------------------ vim-change-command
dict(
    id="vim-change-command",
    title="Apply a change command and type the replacement",
    difficulty="Hard",
    pattern="Vim operators",
    entry="applyChange",
    description=r"""
A change command deletes a region, enters Insert mode, and whatever is typed before `<Esc>` replaces the region.
Simulate `cmd`, then typing `text`, then `<Esc>`, on a single line.

| `cmd` | region replaced (half-open, `n = len(line)`) |
|---|---|
| `cc` | the whole line `[0, n)` (this model ignores auto-indent) |
| `C` | `[col, n)` |
| `s` | the character under the cursor (nothing on an empty line) |
| `cw` | from the cursor to the end of the **run** it is in (runs are keyword `A-Za-z0-9_`, punctuation, or blank). Note the difference from `dw`: the blanks after a word are **kept**. On a blank, the rest of that run of blanks is replaced. |
| `ct{c}` / `cf{c}` | from the cursor up to (excluding / including) the next `c` strictly to the right |
| `ci"` / `ci'` | the inside of a quoted string, located exactly as in *Resolve i" and a"*: on a quote use the parity of the count of quotes up to the cursor; otherwise nearest quote on each side; with no quote on the left, look ahead to the first pair |
| `ci(` `ci)` `ci[` `ci]` `ci{` `ci}` | the inside of the innermost enclosing pair, located exactly as in *Resolve i( a( …* (cursor on a bracket counts as inside; no look-ahead) |

If the region cannot be found (missing character, quote or bracket), nothing happens: return `[line, col]`.

**Cursor afterwards.** `<Esc>` moves the cursor one column left of the insertion point, so it rests on the last
character typed: `start + len(text) - 1`. If `text` is empty it is `start - 1`. Never below 0.

Write `applyChange(line, col, cmd, text)` returning `[new_line, new_col]`.

**Example:** `line = 'log.info("started")'`, `col = 0`, `cmd = 'ci"'`, `text = "ready"` → `['log.info("ready")', 14]`

**Example:** `line = "timeout = 30  # seconds"`, `col = 0`, `cmd = "cw"`, `text = "deadline"` → `["deadline = 30  # seconds", 7]`

**Example:** `line = "sum(xs[1:], start)"`, `col = 8`, `cmd = "ci("`, `text = ""` → `["sum()", 3]`
""",
    starter='''def applyChange(line: str, col: int, cmd: str, text: str) -> list:
    pass
''',
    solution=CHANGE_SOLUTION,
    tests=[
        ['log.info("started")', 0, 'ci"', "ready"],
        ["timeout = 30  # seconds", 0, "cw", "deadline"],
        ["sum(xs[1:], start)", 8, "ci(", ""],
        ["sum(xs[1:], start)", 8, "ci[", "0"],
        ["sum(xs[1:], start)", 0, "ci(", "x"],
        ["sum(xs[1:], start)", 3, "ci)", "a, b"],
        ["timeout = 30  # seconds", 12, "cw", " "],
        ["timeout = 30  # seconds", 3, "cw", "X"],
        ["timeout = 30  # seconds", 10, "C", "45"],
        ["timeout = 30  # seconds", 10, "cc", "pass"],
        ["timeout = 30  # seconds", 10, "s", "9"],
        ["timeout = 30  # seconds", 0, "ct=", "t "],
        ["timeout = 30  # seconds", 0, "cf=", "t ="],
        ["timeout = 30  # seconds", 0, "ct!", "zzz"],
        ["", 0, "cw", "new"],
        ["", 0, "cc", ""],
        ["", 0, 'ci"', "x"],
        ["a = {'k': [1, 2]}", 12, "ci{", ""],
        ["a = {'k': [1, 2]}", 6, "ci'", "key"],
        ['f("a", "b")', 6, 'ci"', "mid"],
        ["x.y", 1, "cw", "->"],
        ["end", 2, "C", ""],
    ],
    examples=3,
    wrong_solutions=[
        CHANGE_SOLUTION.replace("newcol = s + len(text) - 1 if text else s - 1", "newcol = s + len(text)"),
        CHANGE_SOLUTION.replace("            while i < n and cls(i) == t:\n                i += 1\n            rng = (col, i)",
                                "            while i < n and cls(i) == t:\n                i += 1\n"
                                "            while i < n and cls(i) == 0:\n                i += 1\n            rng = (col, i)"),
        CHANGE_SOLUTION.replace("                o = line.find(q, col + 1)\n                c = line.find(q, o + 1) if o >= 0 else -1",
                                "                c = -1"),
    ],
    guide=dict(
        prereqs="`vim-delete-motion`, `vim-text-object-quote`, `vim-text-object-bracket`, and the *Dot formula* lesson "
                "(why `c` commands make good repeatable changes).",
        intuition="`c` is `d` followed by an insert, with one twist: `cw` stops at the end of the word instead of "
                  "swallowing the following blanks, because you are about to type a replacement word and want the "
                  "spacing to survive. After `<Esc>` the cursor steps back onto the last typed character.",
        hints=[
            "Compute a half-open region for each command; `None` means the command failed.",
            "Copy the quote and bracket resolvers from the text-object problems and return only the *inner* range.",
            "The final column is `start + len(text) - 1`, or `start - 1` for empty text, floored at 0.",
        ],
        brute_force="Handle every command with its own splice and cursor formula. It works, but duplicating the "
                    "splice and the `<Esc>` rule a dozen times invites inconsistent off-by-ones.",
        approach="One dispatcher yields `(s, e)` or `None`; one tail builds `line[:s] + text + line[e:]` and the "
                 "cursor.\n\n**Dry run** `sum(xs[1:], start)`, col 8 (`:`), `ci(`, empty text: scanning left from 7 "
                 "meets `[` (not a paren, ignored) and the `(` at 3 with depth 0, so open = 3; scanning right the "
                 "first `)` at depth 0 is at 17. Region [4, 17). New line `sum()`; cursor = 4 - 1 = 3.",
        complexity="O(n) time and space.",
        pitfalls="- Giving `cw` the range of `dw`: the blank after the word must stay.\n- Leaving the cursor after "
                 "the inserted text: `<Esc>` moves it left by one.\n- Inserting `text` when the region was not found; "
                 "a failed command changes nothing.\n- For `ci(` only parentheses count towards nesting depth.",
        follow_up="Make the function return a closure that replays the same change at another column: that is the dot command.",
    ),
),
# ------------------------------------------------------------------ vim-golf-score
dict(
    id="vim-golf-score",
    title="Count keystrokes (VimGolf scoring)",
    difficulty="Easy",
    pattern="Vim keystroke economy",
    entry="golfScore",
    description=r"""
Editing plans are written in Vim's key notation, where special keys appear in angle brackets. VimGolf-style
scoring charges **one point per key press**, and a chord such as Ctrl-R is one press.

Tokenise `keys` from left to right:

- A **special key** is `<NAME>` where `NAME` is one of `Esc`, `CR`, `Enter`, `Return`, `Tab`, `BS`, `Del`,
  `Space`, `lt`, `Bar`, `Up`, `Down`, `Left`, `Right`, `Home`, `End`, or `F` followed by one or two digits.
  It counts as **1**.
- A **chord** is `<` + one or more modifier prefixes (`C-`, `S-`, `A-`, `M-`) + either a single character or one
  of the names above + `>`; for example `<C-r>`, `<C-S-Tab>`, `<A-CR>`. It counts as **1**.
- Names and modifiers are case-insensitive (`<esc>`, `<c-R>` are fine).
- Anything else is a single ordinary key worth **1**, including a `<` that does not start a valid special key
  (so `<<` is two keys, and `<foo>` is five).

Write `golfScore(keys)` returning the total.

**Example:** `"ciwtotal<Esc>"` → `9` (`c`, `i`, `w`, five letters, `<Esc>`)

**Example:** `":%s/a/b/g<CR>"` → `10`

**Example:** `"A;<Esc>j."` → `5`
""",
    starter='''def golfScore(keys: str) -> int:
    pass
''',
    solution=GOLF_SOLUTION,
    tests=[
        ["ciwtotal<Esc>"],
        [":%s/a/b/g<CR>"],
        ["A;<Esc>j."],
        [""],
        ["<<"],
        ["<foo>"],
        ["i<C-r>0<Esc>"],
        ["<esc><ESC><c-R>"],
        ["<C-S-Tab><A-CR>"],
        ["a<b>c"],
        ["qaI- <Esc>jq3@a"],
        ["<F5><F12><F123>"],
        ["<lt>div<gt>"],
        ["<C-"],
        ["i<Tab><BS><Space><Del><Esc>"],
        ["<C->>"],
    ],
    examples=3,
    wrong_solutions=[
        '''def golfScore(keys):
    return len(keys)
''',
        '''import re

def golfScore(keys):
    return len(re.findall(r"<[^<>]+>|.", keys, re.S))
''',
        '''import re

def golfScore(keys):
    return len(re.findall(r"<(?:Esc|CR|Tab|BS|Del|Space|lt|C-.)>|.", keys, re.S))
''',
    ],
    guide=dict(
        prereqs="The *Dot command* lesson (why keystroke counts are a useful, if crude, measure). Regular expressions "
                "anchored at a position (`pattern.match(s, i)`).",
        intuition="It is a tokeniser with exactly two token shapes: a recognised `<…>` group, or one character. The "
                  "work is in being strict about what counts as a recognised group so that literal `<` characters in "
                  "the keystrokes are not swallowed.",
        hints=[
            "Walk an index through the string; at each `<` try to match a special key *at that position*.",
            "Build the pattern from an alternation of names, an optional run of modifier prefixes, and `re.I`.",
            "If the match fails, consume one character and add one to the score, exactly as for any other key.",
        ],
        brute_force="`len(keys)` overcounts every special key, and the lazy pattern `<[^<>]+>` undercounts whenever "
                    "the text contains an innocent `<…>` such as an HTML tag being typed. Both are tempting and wrong.",
        approach="Compile one regular expression for special keys and chords. Loop: if the current character is `<` "
                 "and the pattern matches here, jump to the end of the match; otherwise advance by one. Add 1 each "
                 "time.\n\n**Dry run** `A;<Esc>j.`: `A` (1), `;` (2), `<Esc>` matches (3), `j` (4), `.` (5).",
        complexity="O(n) time, O(1) space.",
        pitfalls="- Case sensitivity: `<esc>` and `<ESC>` are the same key.\n- Stacked modifiers such as `<C-S-Tab>`.\n"
                 "- `<F123>` is not a function key: it is six ordinary keys.\n- `<C->>` is Ctrl plus the character `>`.",
        follow_up="Weight the score: charge 2 for chords and for upper-case letters (they need a modifier), then "
                  "compare `A` with `$a`.",
    ),
),
# ------------------------------------------------------------------ vim-dot-plan
dict(
    id="vim-dot-plan",
    title="Dot plan versus substitute: who wins?",
    difficulty="Easy",
    pattern="Vim keystroke economy",
    entry="dotPlan",
    description=r"""
You need to rename the identifier `old` to `new` everywhere in `text`. Two plans are on the table.

**Plan A, the dot formula.** Search for the whole word, change the first match, then alternate `n` (next match)
and `.` (repeat the change):

```
/\<old\><CR>   cw new <Esc>   n.   n.   ...
```

**Plan B, one substitute command:**

```
:%s/\<old\>/new/g<CR>
```

Let `k` be the number of **whole-word** occurrences of `old` in `text`: occurrences that are neither preceded
nor followed by a keyword character (`A-Za-z0-9_`). `old` and `new` consist only of keyword characters and
`text` may span several lines. Every key costs 1, and `<CR>` and `<Esc>` are one key each, so

- Plan A costs `(len(old) + 6) + (len(new) + 3) + 2 * (k - 1)`
- Plan B costs `len(old) + len(new) + 12`

Write `dotPlan(text, old, new)` returning `[dots, cost_a, cost_b]`, where `dots = k - 1` is how many times `.` is
pressed. If `k` is 0 return `[0, 0, 0]`: there is nothing to do.

**Example:** `text = "n = 1\nprint(n, n2)"`, `old = "n"`, `new = "count"` → `[1, 17, 18]` (two matches; `n2` and `print` do not count)

**Example:** `text = "id id id id"`, `old = "id"`, `new = "key"` → `[3, 20, 17]`
""",
    starter='''def dotPlan(text: str, old: str, new: str) -> List[int]:
    pass
''',
    solution=DOT_SOLUTION,
    tests=[
        ["n = 1\nprint(n, n2)", "n", "count"],
        ["id id id id", "id", "key"],
        ["nothing here", "x", "y"],
        ["x", "x", "y"],
        ["max_len = len(xs); max_len2 = max_len", "max_len", "limit"],
        ["aaa aa a", "a", "b"],
        ["i=i+i*i", "i", "idx"],
        ["user\nuser_id\nuser.id\n(user)", "user", "account"],
        ["tmp tmp tmp", "tmp", "t"],
        ["Total total TOTAL", "total", "sum"],
        ["x1 x x_1 1x x", "x", "value"],
        ["", "a", "b"],
        ["k" + " k" * 40, "k", "key"],
    ],
    examples=2,
    wrong_solutions=[
        '''def dotPlan(text, old, new):
    k = text.count(old)
    if k == 0:
        return [0, 0, 0]
    return [k - 1, (len(old) + 6) + (len(new) + 3) + 2 * (k - 1), len(old) + len(new) + 12]
''',
        '''def dotPlan(text, old, new):
    k = text.split().count(old)
    if k == 0:
        return [0, 0, 0]
    return [k - 1, (len(old) + 6) + (len(new) + 3) + 2 * (k - 1), len(old) + len(new) + 12]
''',
        '''import re

def dotPlan(text, old, new):
    k = len(re.findall(r"(?<![A-Za-z0-9_])" + re.escape(old) + r"(?![A-Za-z0-9_])", text))
    return [k - 1, (len(old) + 6) + (len(new) + 3) + 2 * (k - 1), len(old) + len(new) + 12]
''',
    ],
    guide=dict(
        prereqs="The *Dot formula* lesson and the *Substitution* lesson. Word boundaries in regular expressions.",
        intuition="Both costs are fixed formulas; the only computation is counting whole-word matches, which is what "
                  "Vim's `\\<` and `\\>` anchors do. Subtract the formulas and the lengths cancel: Plan A wins only when "
                  "`2k + 7 < 12`, that is for one or two matches. The dot formula earns its keep through *control* "
                  "(you can skip a match), not through raw key count on big jobs.",
        hints=[
            "A whole-word match is `old` with no keyword character immediately before or after it.",
            "Use look-arounds: `(?<![A-Za-z0-9_])` and `(?![A-Za-z0-9_])`.",
            "Handle `k == 0` before applying the formulas, otherwise `dots` becomes -1.",
        ],
        brute_force="Scan every index, compare the slice with `old`, and test the neighbours by hand. O(n·m), fine for "
                    "these sizes.",
        approach="Count with one regular expression, then plug into the formulas.\n\n**Dry run** `n = 1\\nprint(n, n2)`"
                 " with `n` → `count`: matches at the first `n` and inside the call; the `n` of `print` is preceded by "
                 "`i`, the `n` of `n2` is followed by `2`. k = 2, dots = 1, A = 7 + 8 + 2 = 17, B = 1 + 5 + 12 = 18.",
        complexity="O(n) time, O(1) extra space.",
        pitfalls="- `text.count(old)` counts substrings such as the `n` in `print`.\n- Splitting on whitespace misses "
                 "`(user)` and `user.id`.\n- The underscore is a keyword character: `user_id` does not contain the word "
                 "`user`.\n- Zero matches.",
        follow_up="Add Plan C: `*` on the first occurrence instead of typing the search (cost 1 instead of "
                  "`len(old) + 6`). When does it beat Plan B?",
    ),
),
# ------------------------------------------------------------------ vim-normal-sim
dict(
    id="vim-normal-sim",
    title="A tiny Normal-mode simulator",
    difficulty="Hard",
    pattern="Vim simulation",
    entry="normalSim",
    description=r"""
Simulate a small subset of Normal mode on a buffer. `lines` is a non-empty list of strings; the cursor starts at
row 0, column 0; there is a single register, initially empty. Return `[lines, row, col]` after running `keys`.

"Clamp" means `col = max(0, min(col, len(current_line) - 1))`. "First non-blank" means the index of the first
character that is not a space or tab, or 0 if there is none.

| key | effect |
|---|---|
| `h` `l` | column − 1 / + 1, clamped |
| `j` `k` | row + 1 / − 1 if that row exists, then clamp the column to the new line |
| `0` `$` | first column / last column of the line |
| `x` | on a non-empty line: delete the character under the cursor into the register (**character-wise**), then clamp |
| `dd` | delete the current line into the register (**line-wise**). A buffer never becomes empty: deleting the only line leaves `[""]`. Row is clamped to the last line; column = first non-blank |
| `yy` | copy the current line into the register (line-wise); cursor unchanged |
| `p` | put after. Line-wise register: insert it as a new line **below**, move to it, column = first non-blank. Character-wise: insert the text right after the cursor character (at column 0 on an empty line); cursor on the last inserted character |
| `P` | put before. Line-wise: insert as a new line **above**; the cursor is on the new line, column = first non-blank. Character-wise: insert at the cursor column; cursor on the last inserted character |
| `J` | join the next line onto this one (no-op on the last line): strip the next line's leading blanks and concatenate with **one space**, except use no separator when the current line is empty, the current line ends in a blank, the stripped next line is empty, or the stripped next line starts with `)`. Cursor column = length of the original current line, clamped |
| `r{c}` | replace the character under the cursor with `c` (nothing on an empty line); cursor unchanged |
| `~` | toggle the case of the character under the cursor, then move one column right (clamped); nothing on an empty line |

`p`/`P` with an empty register do nothing. `keys` contains only the commands above.

**Example:** `lines = ["one", "two"]`, `keys = "ddp"` → `[["two", "one"], 1, 0]` (swap two lines)

**Example:** `lines = ["teh"]`, `keys = "lxp"` → `[["the"], 0, 2]` (swap two characters)

**Example:** `lines = ["foo(", "    a,", "    b", ")"]`, `keys = "JJJ"` → `[["foo( a, b)"], 0, 9]`
""",
    starter='''def normalSim(lines: List[str], keys: str) -> list:
    pass
''',
    solution=SIM_SOLUTION,
    tests=[
        [["one", "two"], "ddp"],
        [["teh"], "lxp"],
        [["foo(", "    a,", "    b", ")"], "JJJ"],
        [["alpha", "beta", "gamma"], "yyjp"],
        [["alpha", "beta", "gamma"], "jyykP"],
        [["only"], "dd"],
        [["only"], "ddp"],
        [["only"], "p"],
        [["abc"], "xxxx"],
        [["abc"], "$xP"],
        [["hello world"], "~~~~~"],
        [["a"], "~~"],
        [["cat"], "rbllrd"],
        [["", "x"], "rzxJ"],
        [["short", "a much longer line"], "j$k"],
        [["key = ", "  value"], "J"],
        [["first", ""], "J"],
        [["a", "b", "c", "d"], "jddjp"],
        [["  indented", "top"], "jddkP"],
        [["ab", "cd"], "lxjp0P"],
        [["x", "y", "z"], "jjddddddp"],
        [["wrap", "(arg)"], "J"],
        [["a", ""], "xjp"],
        [["ab", ""], "xjP"],
    ],
    examples=3,
    wrong_solutions=[
        SIM_SOLUTION.replace('''                    if k == "p":
                        row += 1
                    buf.insert(row, text)''', '''                    row += 1
                    buf.insert(row, text)'''),
        SIM_SOLUTION.replace('at = col + 1 if (k == "p" and line) else col', 'at = col + 1 if k == "p" else col')
                    .replace("col = at + len(text) - 1", "col = at"),
        SIM_SOLUTION.replace('''                if line == "" or nxt == "" or line[-1] in " \\t" or nxt[0] == ")":
                    sep = ""''', '''                if nxt == "":
                    sep = ""'''),
    ],
    guide=dict(
        prereqs="The *Registers* lesson (character-wise versus line-wise text), the *Normal mode grammar* lesson.",
        intuition="The whole simulator is a loop over keys with three pieces of state: the buffer, the cursor, and one "
                  "register that remembers both the text **and how it was captured**. That second fact is why `ddp` "
                  "swaps lines while `xp` swaps characters although both end in the same `p`.",
        hints=[
            "Store the register as a pair `(text, kind)` with kind `'l'` or `'c'`.",
            "Consume two characters for `dd`, `yy` and `r{c}`; everything else is one key.",
            "Write `clamp` and `first_nonblank` helpers first; nearly every command ends with one of them.",
        ],
        brute_force="A long `if` chain operating on the list of strings *is* the natural solution; there is no "
                    "asymptotically different approach. The risk is not speed but subtle cursor rules.",
        approach="Process keys left to right, applying the table.\n\n**Dry run** `[\"teh\"]` with `lxp`: `l` → col 1. "
                 "`x` removes `e`: line `th`, register (`e`, char), col clamped to 1. `p` inserts after column 1 at "
                 "index 2: `the`, cursor on the inserted character, col 2.",
        complexity="O(len(keys) × L) where L is the line length (each edit rebuilds a string), plus O(rows) for line "
                   "insertions and deletions.",
        pitfalls="- Line-wise `P` keeps the same row index (the new line now occupies it); line-wise `p` increments it.\n"
                 "- Character-wise `p` on an empty line inserts at column 0, not 1.\n- `dd` on the last remaining line "
                 "must leave one empty line.\n- `J` strips the *next* line's leading blanks and can decide to insert no "
                 "space at all.\n- After `x` at the end of a line the cursor steps back.",
        follow_up="Add counts (`3dd`, `2p`), `u` for undo using a stack of buffer snapshots, and `.` to repeat the "
                  "last change.",
    ),
),
# ------------------------------------------------------------------ vim-registers
dict(
    id="vim-registers",
    title="Simulate the unnamed, numbered and named registers",
    difficulty="Medium",
    pattern="Vim registers",
    entry="registerSim",
    description=r"""
Model how yanks and deletes flow through Vim's registers. `ops` is a list of `[kind, name, text]`:

- `kind` is `"y"` (yank) or `"d"` (delete or change);
- `name` is the register given with a `"x` prefix, or `""` when the command had no prefix;
- `text` is what was captured. A text **containing a newline** is a multi-line capture.

Rules of this model (they follow Vim's documented behaviour):

1. `name == "_"` (black hole): nothing at all changes.
2. No prefix, **yank**: the text goes to register `0`.
3. No prefix, **delete**, multi-line text: registers `1`…`8` shift down to `2`…`9` (the old `9` is lost) and the
   text goes to `1`.
4. No prefix, **delete**, text without a newline: the text goes to the small-delete register `-`. The numbered
   registers are untouched.
5. Lower-case name `a`–`z`: that register is overwritten. Registers `0`–`9` and `-` are untouched.
6. Upper-case name `A`–`Z`: the text is **appended** to the lower-case register of the same letter (plain
   concatenation).
7. In every case except the black hole, the unnamed register `"` ends up holding what the written register now
   holds (for an append, the whole accumulated text).

Then answer `queries`, a list of register names among `"`, `0`–`9`, `-`, `a`–`z`: return each one's contents,
with `""` for a register that was never set.

**Example:** `ops = [["y","","alpha"], ["d","","x"], ["d","","line\n"]]`, `queries = ['"', "0", "1", "-"]`
→ `["line\n", "alpha", "line\n", "x"]`

**Example:** `ops = [["y","a","one "], ["y","A","two"], ["d","_","junk"]]`, `queries = ["a", '"', "0"]`
→ `["one two", "one two", ""]`
""",
    starter='''def registerSim(ops: List[List[str]], queries: List[str]) -> List[str]:
    pass
''',
    solution=REG_SOLUTION,
    tests=[
        [[["y", "", "alpha"], ["d", "", "x"], ["d", "", "line\n"]], ['"', "0", "1", "-"]],
        [[["y", "a", "one "], ["y", "A", "two"], ["d", "_", "junk"]], ["a", '"', "0"]],
        [[], ['"', "0", "1", "a", "-"]],
        [[["d", "", "L%d\n" % i] for i in range(1, 12)], ["1", "2", "8", "9", '"']],
        [[["d", "", "L1\n"], ["d", "", "L2\n"], ["y", "", "kept"], ["d", "", "L3\n"]], ["0", "1", "2", "3", '"']],
        [[["y", "", "keep"], ["d", "", "word"], ["d", "", "w2"]], ["0", "-", "1", '"']],
        [[["d", "", "a\n"], ["d", "x", "b\n"], ["d", "", "c\n"]], ["1", "2", "3", "x", '"']],
        [[["y", "q", "one"], ["y", "q", "two"]], ["q", '"', "0"]],
        [[["y", "Q", "fresh"]], ["q", '"']],
        [[["y", "", "zero"], ["y", "b", "bee"]], ["0", "b", '"']],
        [[["y", "", "zero"], ["d", "_", "gone\n"], ["d", "_", "g"]], ['"', "0", "1", "-"]],
        [[["d", "c", "tiny"], ["d", "", "t"]], ["c", "-", '"', "1"]],
        [[["y", "a", "x"], ["d", "A", "y\n"], ["y", "A", "z"]], ["a", '"', "1", "0"]],
        [[["d", "", "one\ntwo\n"], ["y", "", "three\n"]], ["1", "0", '"', "2"]],
    ],
    examples=2,
    wrong_solutions=[
        REG_SOLUTION.replace('            elif "\\n" in text:', '            elif True:'),
        REG_SOLUTION.replace('''                for d in range(9, 1, -1):
                    if str(d - 1) in reg:
                        reg[str(d)] = reg[str(d - 1)]
''', '''                for d in range(2, 10):
                    if str(d - 1) in reg:
                        reg[str(d)] = reg[str(d - 1)]
'''),
        REG_SOLUTION.replace('''            reg[name] = text
            reg['"'] = text''', '''            reg[name] = text
            reg['"'] = text
            if kind == "y":
                reg["0"] = text'''),
        REG_SOLUTION.replace('''            reg[low] = reg.get(low, "") + text
            reg['"'] = reg[low]''', '''            reg[low] = reg.get(low, "") + text
            reg['"'] = text'''),
    ],
    guide=dict(
        prereqs="The *Registers* lesson. Dictionaries.",
        intuition="Think of the registers as a small key-value store with routing rules. A command with no prefix is "
                  "routed by *what it did*: yanks to `0`, big deletes into the `1`–`9` queue, small deletes to `-`. A "
                  "command with a prefix goes exactly where you said. The unnamed register is a pointer to whichever "
                  "register was written last.",
        hints=[
            "Use a dict from register name to text; missing keys mean empty.",
            "Shift the numbered registers from 9 down to 2, otherwise you copy one value into all of them.",
            "After every write, set `reg['\"']` to the current content of the register you just wrote.",
        ],
        brute_force="Keep a Python list for registers 1–9 and insert at the front, truncating to nine items. That is "
                    "equally fast and arguably clearer; the dict version just keeps all registers uniform.",
        approach="Loop over the operations, applying the first rule that matches.\n\n**Dry run** of example 1: yank "
                 "`alpha` → `0 = alpha`, `\" = alpha`. Delete `x` (no newline) → `- = x`, `\" = x`. Delete `line\\n` → "
                 "nothing to shift, `1 = line\\n`, `\" = line\\n`. Register `0` still holds `alpha`: that is the yank "
                 "register surviving two deletes.",
        complexity="O(len(ops) + len(queries)) time (the shift is a constant nine steps), O(total text) space.",
        pitfalls="- Sending every delete to register 1; small deletes go to `-`.\n- Shifting upward (2 ← 1, 3 ← 2 …) "
                 "copies register 1 everywhere.\n- A named yank does not touch register 0.\n- After an append, the "
                 "unnamed register holds the whole accumulated text, not just the new piece.\n- The black hole really "
                 "changes nothing, not even the unnamed register.",
        follow_up="Add the read-only registers (`.` last inserted text, `:` last Ex command, `%` file name) and the "
                  "system clipboard registers `+` and `*`.",
    ),
),
# ------------------------------------------------------------------ vim-macro-expand
dict(
    id="vim-macro-expand",
    title="Expand macros with counts",
    difficulty="Medium",
    pattern="Vim macros",
    entry="expandMacro",
    description=r"""
A macro is just a register full of keystrokes; `@a` types the contents of register `a`, and `7@a` does so seven
times. Macros may invoke other macros. Flatten a keystroke string into the keys that are finally executed.

`registers` maps lower-case letters to keystroke strings. Scan `keys` left to right:

- **Count.** A count is a run of digits whose first digit is `1`–`9`. (A `0` that does not continue a count is the
  "go to column 0" motion and is copied like any other key.)
- **Invocation.** An optional count followed by `@` and a lower-case letter `x` runs register `x` that many times
  (once without a count). Each run is itself expanded by these same rules. A register missing from `registers`
  is empty.
- **Repeat.** `@@` (optionally with a count) runs the register that was executed **most recently at that moment**,
  including registers run from inside other macros. If no macro has run yet it produces nothing.
- **Everything else** is copied to the output unchanged, including a count that is not followed by an invocation
  (`3j` stays `3j`).

Inputs are guaranteed not to recurse forever, and `@` is only ever used as described.

Write `expandMacro(registers, keys)` returning the flattened string.

**Example:** `registers = {"a": "A;j"}`, `keys = "3@a"` → `"A;jA;jA;j"`

**Example:** `registers = {"a": "0f,2@bj", "b": "x"}`, `keys = "@a@@"` → `"0f,xxjx"` (the most recently run register is `b`)

**Example:** `registers = {}`, `keys = "10j@q@@dd"` → `"10jdd"`
""",
    starter='''def expandMacro(registers: Dict[str, str], keys: str) -> str:
    pass
''',
    solution=MACRO_SOLUTION,
    tests=[
        [{"a": "A;j"}, "3@a"],
        [{"a": "0f,2@bj", "b": "x"}, "@a@@"],
        [{}, "10j@q@@dd"],
        [{"a": "x"}, "@@@a@@"],
        [{"a": "x"}, "12@a"],
        [{"a": "dw"}, "0@a"],
        [{"a": "dw"}, "20@a0"],
        [{"a": "1@b", "b": "2@c", "c": "~"}, "2@a"],
        [{"a": "ib<Esc>", "b": "@a@a"}, "@b2@@"],
        [{"a": "j", "b": "k"}, "@a@b3@@@a@@"],
        [{"w": "cwnew<Esc>n"}, "5j@w3."],
        [{"a": ""}, "x@ay"],
        [{"a": "3j"}, "2@a4k"],
        [{"x": "@y@@", "y": "p"}, "@x@@"],
        [{}, ""],
    ],
    examples=3,
    wrong_solutions=[
        '''import re

def expandMacro(registers, keys):
    def run(s):
        return re.sub(r"([1-9][0-9]*)?@([a-z])",
                      lambda m: run(registers.get(m.group(2), "")) * int(m.group(1) or 1), s)
    return run(keys)
''',
        MACRO_SOLUTION.replace('if s[j] in "123456789":', 'if s[j].isdigit():'),
        MACRO_SOLUTION.replace('''                for _ in range(count):
                    state["last"] = name
                    run(registers.get(name, ""))''', '''                for _ in range(count):
                    run(registers.get(name, ""))
                state["last"] = name'''),
    ],
    guide=dict(
        prereqs="The *Macros* lesson. Recursion; a simple hand-written scanner.",
        intuition="Executing a macro is the same as typing its contents, so expansion is recursive substitution. The "
                  "one piece of global state is *which register ran last*, because `@@` refers to it, and that can "
                  "change while a macro is in the middle of running.",
        hints=[
            "Write a recursive `run(s)` that appends to a shared output list.",
            "Read digits first; only if the next two characters form `@x` or `@@` is it a count. Otherwise emit the digits literally.",
            "Update the last-run register *before* each recursive call, and resolve `@@` at the moment it is reached.",
        ],
        brute_force="Repeatedly apply a regular-expression substitution replacing `N@x` by N copies of the register "
                    "until nothing changes. This handles nesting, but it cannot resolve `@@` correctly because that "
                    "depends on execution order.",
        approach="A scanner with one-token look-ahead plus recursion.\n\n**Dry run** `@a@@` with `a = 0f,2@bj`, "
                 "`b = x`: `@a` → last = a, run `0f,2@bj`: emit `0`, `f`, `,`; `2@b` → last = b, emit `x` twice; emit "
                 "`j`. Back at the top level, `@@` → last is `b` → emit `x`. Output `0f,xxjx`.",
        complexity="O(size of the output) time and space.",
        pitfalls="- Treating a leading `0` as a count: `0@a` is the motion `0` followed by `@a`.\n- Dropping counts "
                 "that belong to ordinary commands (`3j`).\n- Resolving `@@` to the register named at the top level "
                 "rather than the one that actually ran last.\n- `@@` before any macro has run is a no-op.",
        follow_up="Model macro abort: add a per-key predicate that can fail, and stop the *entire* remaining count "
                  "when it does. That is how `100@a` stops by itself at the end of a file.",
    ),
),
]
