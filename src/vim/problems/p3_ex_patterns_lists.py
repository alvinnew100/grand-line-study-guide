"""Practical Vim problems, part 3: Ex ranges, substitution, :global, pattern translation,
jump/change lists, the buffer list and Visual-block edits."""

SUB_SOLUTION = '''import re

def substitute(lines, start, end, pat, rep, flags):
    rx = re.compile(pat, re.I if "i" in flags else 0)

    def expand(m):
        out = []
        i = 0
        while i < len(rep):
            ch = rep[i]
            if ch == "\\\\" and i + 1 < len(rep):
                nx = rep[i + 1]
                if nx.isdigit():
                    g = int(nx)
                    out.append((m.group(g) or "") if g <= rx.groups else "")
                elif nx == "t":
                    out.append("\\t")
                else:
                    out.append(nx)
                i += 2
            elif ch == "&":
                out.append(m.group(0))
                i += 1
            else:
                out.append(ch)
                i += 1
        return "".join(out)

    out = list(lines)
    subs = changed = 0
    limit = 0 if "g" in flags else 1
    for idx in range(start - 1, end):
        new, k = rx.subn(expand, out[idx], count=limit)
        if k:
            subs += k
            changed += 1
            if "n" not in flags:
                out[idx] = new
    return [out, subs, changed]
'''

GLOBAL_SOLUTION = '''import re

def globalCmd(lines, pat, invert, cmd):
    rx = re.compile(pat)
    hit = [(rx.search(s) is not None) != invert for s in lines]
    marked = [s for s, h in zip(lines, hit) if h]
    rest = [s for s, h in zip(lines, hit) if not h]
    if cmd == "d":
        return rest
    if cmd == "m0":
        return marked[::-1] + rest
    if cmd == "m$":
        return rest + marked
    if cmd == "t0":
        return marked[::-1] + list(lines)
    return list(lines) + marked
'''

RANGE_SOLUTION = '''def parseRange(spec, cur, last, marks):
    def addr(s):
        i = 0
        if s[:1].isdigit():
            while i < len(s) and s[i].isdigit():
                i += 1
            base = int(s[:i])
        elif s[:1] == ".":
            base, i = cur, 1
        elif s[:1] == "$":
            base, i = last, 1
        elif s[:1] == "'":
            name = s[1:2]
            if name not in marks:
                return None
            base, i = marks[name], 2
        else:
            base = cur
        while i < len(s):
            sign = s[i]
            if sign not in "+-":
                return None
            i += 1
            j = i
            while j < len(s) and s[j].isdigit():
                j += 1
            n = int(s[i:j]) if j > i else 1
            base += n if sign == "+" else -n
            i = j
        return base

    if spec == "%":
        a, b = 1, last
    else:
        parts = spec.split(",")
        if len(parts) > 2:
            return [-1, -1]
        a = addr(parts[0])
        b = addr(parts[1]) if len(parts) == 2 else a
    if a is None or b is None:
        return [-1, -1]
    if not (1 <= a <= last and 1 <= b <= last):
        return [-1, -1]
    return [min(a, b), max(a, b)]
'''

VMAGIC_SOLUTION = '''def veryMagicToPython(pat):
    if pat.startswith("\\\\v"):
        pat = pat[2:]
    classes = {"a": "[A-Za-z]", "l": "[a-z]", "u": "[A-Z]", "h": "[A-Za-z_]", "x": "[0-9A-Fa-f]"}
    special = ".^$*+?()[]{}|\\\\"
    out = []
    i = 0
    n = len(pat)
    while i < n:
        ch = pat[i]
        if ch == "\\\\" and i + 1 < n:
            nx = pat[i + 1]
            if nx in classes:
                out.append(classes[nx])
            elif nx.isalnum():
                out.append("\\\\" + nx)
            elif nx in special:
                out.append("\\\\" + nx)
            else:
                out.append(nx)
            i += 2
        elif ch in "<>":
            out.append("\\\\b")
            i += 1
        elif ch == "=":
            out.append("?")
            i += 1
        elif ch == "%" and i + 1 < n and pat[i + 1] == "(":
            out.append("(?:")
            i += 2
        elif ch == "{" and i + 1 < n and pat[i + 1] == "-":
            j = pat.index("}", i)
            body = pat[i + 2:j]
            out.append("{" + body + "}?" if body else "*?")
            i = j + 1
        elif ch == "[":
            j = i + 1
            if j < n and pat[j] == "^":
                j += 1
            if j < n and pat[j] == "]":
                j += 1
            while j < n and pat[j] != "]":
                j += 2 if pat[j] == "\\\\" else 1
            out.append(pat[i:j + 1])
            i = j + 1
        else:
            out.append(ch)
            i += 1
    return "".join(out)
'''

JUMP_SOLUTION = '''def jumpList(ops):
    cur = 1
    lst = []
    idx = 0
    for op in ops:
        if op[0] == "jump":
            lst = [x for x in lst if x != cur]
            lst.append(cur)
            idx = len(lst)
            cur = op[1]
        elif op[0] == "back":
            if idx == len(lst):
                lst = [x for x in lst if x != cur]
                lst.append(cur)
                idx = len(lst) - 1
            if idx > 0:
                idx -= 1
                cur = lst[idx]
        else:
            if idx < len(lst) - 1:
                idx += 1
                cur = lst[idx]
    return [cur, lst]
'''

CHANGE_SOLUTION = '''def changeList(ops):
    cur = 1
    lst = []
    idx = 0
    out = []
    for op in ops:
        kind = op[0]
        if kind == "move":
            cur = op[1]
        elif kind == "edit":
            cur = op[1]
            if not lst or lst[-1] != cur:
                lst.append(cur)
                if len(lst) > 100:
                    lst.pop(0)
            idx = len(lst)
        elif kind == "g;":
            if idx > 0:
                idx -= 1
                cur = lst[idx]
            out.append(cur)
        else:
            if idx < len(lst) - 1:
                idx += 1
                cur = lst[idx]
            out.append(cur)
    return out
'''

BUF_SOLUTION = '''def bufferSim(ops):
    cur = ""
    alt = ""
    lst = []
    for op in ops:
        kind = op[0]
        if kind == "e":
            name = op[1]
            if name == cur:
                continue
            if name not in lst:
                lst.append(name)
            if cur:
                alt = cur
            cur = name
        elif kind in ("bn", "bp"):
            if len(lst) > 1:
                i = lst.index(cur)
                step = 1 if kind == "bn" else -1
                alt = cur
                cur = lst[(i + step) % len(lst)]
        elif kind == "alt":
            if alt:
                cur, alt = alt, cur
        elif kind == "bd":
            if not cur:
                continue
            i = lst.index(cur)
            lst.pop(i)
            if alt:
                cur = alt
            elif lst:
                cur = lst[i] if i < len(lst) else lst[-1]
            else:
                cur = ""
            alt = ""
    return [cur, alt, lst]
'''

BLOCK_SOLUTION = '''def blockEdit(lines, top, bottom, col, mode, text):
    out = list(lines)
    for r in range(top, bottom + 1):
        s = out[r]
        if mode == "I":
            if len(s) > col:
                out[r] = s[:col] + text + s[col:]
        elif mode == "A":
            if len(s) <= col:
                s = s + " " * (col + 1 - len(s))
            out[r] = s[:col + 1] + text + s[col + 1:]
        else:
            out[r] = s + text
    return out
'''

PROBLEMS = [
# ------------------------------------------------------------------ vim-ex-range
dict(
    id="vim-ex-range",
    title="Parse an Ex range",
    difficulty="Medium",
    pattern="Vim Ex commands",
    entry="parseRange",
    description=r"""
Most Ex commands accept a range in front: `:3,7d`, `:.,+3>`, `:'<,'>normal .`, `:%s/a/b/`. Resolve a range
specification to a pair of 1-based line numbers.

Arguments: `spec` (the range text, no spaces), `cur` (the cursor's line), `last` (the number of lines in the
buffer, at least 1) and `marks` (a dict from mark name, one character such as `a`, `<` or `>`, to a line number).

Grammar of this subset:

- `spec` is `""`, `"%"`, one *address*, or two addresses separated by a comma.
- An **address** is an optional *base* followed by zero or more *offsets*.
  - Base: a decimal number, `.` (current line), `$` (last line), or `'x` (line of mark `x`).
    A missing base means the current line, so `+2` is `.+2` and the empty string is `.`.
  - Offset: `+N` or `-N`; a bare `+` or `-` means 1. Offsets accumulate: `.+3-1` is `cur + 2`.
- In `a,b` **both** addresses are resolved relative to the cursor (that is what the comma means in Vim; the
  semicolon form is not part of this problem).
- `%` is shorthand for `1,$`.
- One address alone gives a one-line range `[n, n]`; the empty spec gives `[cur, cur]`.

Return `[start, end]`. If the two addresses come out reversed, swap them. Return `[-1, -1]` when the spec uses
an unknown mark, has a malformed address (anything that is not a valid base or offset, or more than one comma),
or when either address falls outside `1..last`.

**Example:** `spec = ".,+3"`, `cur = 5`, `last = 20`, `marks = {}` → `[5, 8]`

**Example:** `spec = "'<,'>"`, `cur = 9`, `last = 20`, `marks = {"<": 4, ">": 9}` → `[4, 9]`

**Example:** `spec = "%"`, `cur = 2`, `last = 12` → `[1, 12]`
""",
    starter='''def parseRange(spec: str, cur: int, last: int, marks: Dict[str, int]) -> List[int]:
    pass
''',
    solution=RANGE_SOLUTION,
    tests=[
        [".,+3", 5, 20, {}],
        ["'<,'>", 9, 20, {"<": 4, ">": 9}],
        ["%", 2, 12, {}],
        ["", 7, 20, {}],
        ["3", 7, 20, {}],
        ["$", 7, 20, {}],
        ["2,$-1", 7, 20, {}],
        [".+3-1", 7, 20, {}],
        ["+,++", 7, 20, {}],
        [",+2", 7, 20, {}],
        ["-2,", 7, 20, {}],
        ["10,4", 7, 20, {}],
        ["'a,'b", 1, 20, {"a": 15, "b": 6}],
        ["'z", 1, 20, {"a": 15}],
        [".,+30", 5, 20, {}],
        ["0,3", 5, 20, {}],
        ["1,2,3", 5, 20, {}],
        ["3x", 5, 20, {}],
        ["$-", 5, 1, {}],
        ["%", 1, 1, {}],
        ["'a+2,$", 3, 30, {"a": 10}],
        ["12-10+5", 3, 30, {}],
    ],
    examples=3,
    wrong_solutions=[
        RANGE_SOLUTION.replace("    return [min(a, b), max(a, b)]", "    return [a, b]"),
        RANGE_SOLUTION.replace('''        a = addr(parts[0])
        b = addr(parts[1]) if len(parts) == 2 else a''', '''        a = addr(parts[0])
        if len(parts) == 2:
            cur = a if a is not None else cur
            b = addr(parts[1])
        else:
            b = a'''),
        RANGE_SOLUTION.replace("            n = int(s[i:j]) if j > i else 1", "            n = int(s[i:j]) if j > i else 0"),
        RANGE_SOLUTION.replace("    if not (1 <= a <= last and 1 <= b <= last):\n        return [-1, -1]\n", ""),
    ],
    guide=dict(
        prereqs="The *Command-line mode* lesson (ranges and addresses). Writing a small recursive-descent style scanner.",
        intuition="A range is at most two addresses, and an address is a starting line plus a running sum of signed "
                  "offsets. Parse the base, then loop over offsets. Everything else is validation.",
        hints=[
            "Handle `%` up front; then `spec.split(',')` gives one or two address strings (the empty string is a valid address).",
            "In the address parser, decide the base from the first character, then consume `+`/`-` followed by optional digits until the string ends.",
            "Return `None` from the address parser for anything unexpected, and turn it into `[-1, -1]` at the top level.",
        ],
        brute_force="A single regular expression such as `^(base)?((?:[+-]\\d*)*)$` per address also works; you still "
                    "need a loop (or `re.findall`) to add up the offsets.",
        approach="`addr(s)` → integer or `None`. Top level: `%`, else split on the comma, resolve, validate bounds, "
                 "order.\n\n**Dry run** `2,$-1` with last = 20: first address has base 2, no offsets → 2. Second: base "
                 "`$` = 20, offset `-1` → 19. Both within 1..20 → `[2, 19]`.",
        complexity="O(len(spec)) time, O(1) space.",
        pitfalls="- Resolving the second address relative to the first: that is `;`, not `,`.\n- A bare `+` means +1, "
                 "not +0.\n- `0` is a number but not a valid line in this model.\n- The empty string on either side of "
                 "the comma is legal and means the current line.\n- Forgetting to swap a backwards range.",
        follow_up="Add pattern addresses (`/re/` and `?re?`), the `;` separator, and `:{range}` with a count such as `:d 3`.",
    ),
),
# ------------------------------------------------------------------ vim-substitute
dict(
    id="vim-substitute",
    title="Apply :s to a range of lines",
    difficulty="Medium",
    pattern="Vim Ex commands",
    entry="substitute",
    description=r"""
Implement the heart of `:[range]s/{pattern}/{replacement}/[flags]`.

Arguments: `lines` (the buffer), `start` and `end` (a valid 1-based inclusive range), `pat`, `rep`, `flags`.

- `pat` uses **Python `re` syntax** so that you can concentrate on substitute semantics rather than on Vim's
  regex dialect. It never matches the empty string.
- Without the `g` flag only the **first** match on each line is replaced. With `g`, every non-overlapping match.
- Flag `i` makes matching case-insensitive.
- Flag `n` only counts: the buffer is returned unchanged, but the counts are reported as if the substitution ran.
- In `rep`:
  - `&` and `\0` stand for the whole match;
  - `\1` … `\9` stand for the corresponding capture group (the empty string if that group did not participate
    or does not exist);
  - `\t` is a tab character;
  - a backslash followed by any other character yields that character literally (so `\&` is an ampersand and
    `\\` is a backslash; `\r` and `\n` do not occur in the tests);
  - everything else is literal.

Return `[new_lines, substitutions, lines_changed]`: the same two numbers Vim reports as "N substitutions on M
lines". Lines outside the range are never touched.

**Example:** `lines = ["a-b-c", "d-e"]`, range `1,2`, `pat = "-"`, `rep = "+"`, `flags = ""` → `[["a+b-c", "d+e"], 2, 2]`

**Example:** same buffer with `flags = "g"` → `[["a+b+c", "d+e"], 3, 2]`

**Example:** `lines = ["Doe, Jane"]`, `pat = r"(\w+), (\w+)"`, `rep = r"\2 \1 <&>"`, `flags = ""` → `[["Jane Doe <Doe, Jane>"], 1, 1]`
""",
    starter='''def substitute(lines: List[str], start: int, end: int, pat: str, rep: str, flags: str) -> list:
    pass
''',
    solution=SUB_SOLUTION,
    tests=[
        [["a-b-c", "d-e"], 1, 2, "-", "+", ""],
        [["a-b-c", "d-e"], 1, 2, "-", "+", "g"],
        [["Doe, Jane"], 1, 1, r"(\w+), (\w+)", r"\2 \1 <&>", ""],
        [["x=1", "x=2", "x=3", "x=4"], 2, 3, "x", "y", "g"],
        [["Error error ERROR"], 1, 1, "error", "warn", "gi"],
        [["Error error ERROR"], 1, 1, "error", "warn", "g"],
        [["aaa", "bbb", "aba"], 1, 3, "a", "X", "gn"],
        [["no match here"], 1, 1, "zzz", "y", "g"],
        [["R&D"], 1, 1, "D", r"\&\\&", ""],
        [["2024-11-20"], 1, 1, r"(\d+)-(\d+)-(\d+)", r"\3/\2/\1", ""],
        [["price: 10", "price: 250"], 1, 2, r"\d+", r"$&.00", "g"],
        [["ab"], 1, 1, r"(a)|(b)", r"[\1\2\9]", "g"],
        [["tab\there"], 1, 1, r"\t", r"\t\t", ""],
        [["a,b,c"], 1, 1, ",", r"\t", "g"],
        [["one", "two", "three"], 3, 3, "e", "E", "g"],
        [[], 1, 0, "a", "b", "g"],
        [["foo.bar", "foo.baz.qux"], 1, 2, r"\.", r"\0\0", "g"],
    ],
    examples=3,
    wrong_solutions=[
        '''import re

def substitute(lines, start, end, pat, rep, flags):
    rx = re.compile(pat, re.I if "i" in flags else 0)
    out = list(lines)
    subs = changed = 0
    for idx in range(start - 1, end):
        new, k = rx.subn(rep, out[idx], count=0 if "g" in flags else 1)
        if k:
            subs += k
            changed += 1
            out[idx] = new
    return [out, subs, changed]
''',
        SUB_SOLUTION.replace('    limit = 0 if "g" in flags else 1', '    limit = 0'),
        SUB_SOLUTION.replace("    for idx in range(start - 1, end):", "    for idx in range(len(out)):"),
        SUB_SOLUTION.replace("            subs += k\n            changed += 1", "            subs += 1\n            changed += 1"),
    ],
    guide=dict(
        prereqs="The *Substitution* lesson. `re.compile`, `Pattern.subn` with a function as the replacement.",
        intuition="Three independent pieces: *which lines* (the range), *which matches on a line* (first or all), and "
                  "*what to write* (the replacement mini-language). Python's own replacement syntax differs from "
                  "Vim's (`&` is not special in Python, `\\g<0>` is), so expand the replacement yourself.",
        hints=[
            "`rx.subn(func, line, count=1)` replaces only the first match and tells you how many replacements were made.",
            "Write `expand(match)` that walks `rep` character by character, handling backslash pairs and `&`.",
            "For the `n` flag do all the counting but skip the assignment back into the list.",
        ],
        brute_force="Find matches manually with `rx.search` in a loop, slicing and rebuilding the line each time. "
                    "Correct but quadratic on long lines, and you must be careful to continue searching after the "
                    "inserted text, not inside it.",
        approach="Compile once, loop over the range, call `subn` with the expansion function, accumulate counts.\n\n"
                 "**Dry run** `Doe, Jane` with `(\\w+), (\\w+)` → `\\2 \\1 <&>`: one match, groups `Doe` and `Jane`. "
                 "Expanding: `\\2` → `Jane`, space, `\\1` → `Doe`, space, `<`, `&` → `Doe, Jane`, `>`.",
        complexity="O(total length of the lines in the range × cost of matching), O(size of the output) space.",
        pitfalls="- Passing `rep` straight to `re.sub`: Python does not understand `&`, and `\\0` means something else.\n"
                 "- Replacing every match when `g` is absent.\n- Counting changed lines instead of substitutions (or "
                 "the reverse).\n- Touching lines outside the range.\n- A group that did not participate is `None` in "
                 "Python; Vim inserts nothing.",
        follow_up="Add `~` (previous replacement string), `\\u`/`\\U…\\E` case modifiers, and the `c` flag driven by a "
                  "list of y/n answers.",
    ),
),
# ------------------------------------------------------------------ vim-global-command
dict(
    id="vim-global-command",
    title="Run :g and :v with d, m and t",
    difficulty="Medium",
    pattern="Vim Ex commands",
    entry="globalCmd",
    description=r"""
`:g/{pattern}/{cmd}` runs an Ex command on every line that matches a pattern; `:v/{pattern}/{cmd}` (also spelled
`:g!`) runs it on every line that does **not** match. It works in two passes:

1. **Mark** every line of the buffer for which the test holds (`re.search(pat, line)` succeeds for `:g`, fails
   for `:v`). `pat` uses Python `re` syntax.
2. **Execute** `cmd` once for each marked line, visiting them in their original top-to-bottom order, with that
   line as the current line. Lines created by the command itself are not marked.

Supported commands:

| `cmd` | Ex meaning | effect per marked line |
|---|---|---|
| `d` | delete | remove the line |
| `m0` | move to before line 1 | the line becomes the first line |
| `m$` | move to after the last line | the line becomes the last line |
| `t0` | copy to before line 1 | a copy becomes the first line |
| `t$` | copy to after the last line | a copy becomes the last line |

Arguments: `lines`, `pat`, `invert` (`False` for `:g`, `True` for `:v`), `cmd`. Return the resulting list of lines.

Think about what the per-line execution order does: `:g/^/m0` moves line 1 to the top, then line 2 above it, then
line 3 above that … and so reverses the buffer.

**Example:** `lines = ["a", "# x", "b", "# y"]`, `pat = "^#"`, `invert = False`, `cmd = "d"` → `["a", "b"]`

**Example:** `lines = ["1", "2", "3"]`, `pat = "^"`, `invert = False`, `cmd = "m0"` → `["3", "2", "1"]`

**Example:** `lines = ["x", "TODO a", "y", "TODO b"]`, `pat = "TODO"`, `invert = False`, `cmd = "t$"` → `["x", "TODO a", "y", "TODO b", "TODO a", "TODO b"]`
""",
    starter='''def globalCmd(lines: List[str], pat: str, invert: bool, cmd: str) -> List[str]:
    pass
''',
    solution=GLOBAL_SOLUTION,
    tests=[
        [["a", "# x", "b", "# y"], "^#", False, "d"],
        [["1", "2", "3"], "^", False, "m0"],
        [["x", "TODO a", "y", "TODO b"], "TODO", False, "t$"],
        [["a", "# x", "b", "# y"], "^#", True, "d"],
        [["x", "TODO a", "y", "TODO b"], "TODO", False, "m$"],
        [["x", "TODO a", "y", "TODO b"], "TODO", False, "m0"],
        [["x", "TODO a", "y", "TODO b"], "TODO", False, "t0"],
        [["x", "TODO a", "y", "TODO b"], "TODO", True, "m$"],
        [[], "a", False, "d"],
        [["only"], "zzz", False, "d"],
        [["only"], "zzz", True, "d"],
        [["", "  ", "text", ""], r"^\s*$", False, "d"],
        [["b", "a", "b", "a"], "a", False, "t$"],
        [["import os", "x = 1", "import re", "y = 2", "import sys"], r"^import", False, "m0"],
        [["k%d" % i for i in range(50)], r"[05]$", True, "d"],
        [["Abc", "abc"], "abc", False, "d"],
    ],
    examples=3,
    wrong_solutions=[
        '''import re

def globalCmd(lines, pat, invert, cmd):
    rx = re.compile(pat)
    hit = [(rx.search(s) is not None) != invert for s in lines]
    marked = [s for s, h in zip(lines, hit) if h]
    rest = [s for s, h in zip(lines, hit) if not h]
    if cmd == "d":
        return rest
    if cmd == "m0":
        return marked + rest
    if cmd == "m$":
        return rest + marked
    if cmd == "t0":
        return marked + list(lines)
    return list(lines) + marked
''',
        GLOBAL_SOLUTION.replace("rx.search(s)", "rx.fullmatch(s)"),
        GLOBAL_SOLUTION.replace("!= invert", "!= False"),
        GLOBAL_SOLUTION.replace("re.compile(pat)", "re.compile(pat, re.I)"),
    ],
    guide=dict(
        prereqs="The *Global command* lesson. `re.search`; list comprehensions.",
        intuition="Because the marking pass is finished before anything runs, you can reason about the final layout "
                  "directly: split the buffer into *marked* and *unmarked* lines. Deleting keeps the unmarked ones; "
                  "moving or copying to the end appends the marked ones in order; moving or copying to the top "
                  "prepends them **reversed**, because each later line lands above the earlier ones.",
        hints=[
            "Compute a boolean per line first; XOR it with `invert`.",
            "Build two lists, `marked` and `rest`, preserving order.",
            "For `m0` and `t0`, reverse `marked` before prepending.",
        ],
        brute_force="Simulate literally: keep a list of (line, mark) pairs and for each originally marked line locate "
                    "it, remove or copy it, and reinsert. O(n²) because each move shifts the list, and matching while "
                    "you mutate (a single pass) is wrong: moved lines get tested again.",
        approach="Mark, partition, assemble.\n\n**Dry run** `[\"1\",\"2\",\"3\"]`, `:g/^/m0`: all three are marked. "
                 "Executing in order: `1` moves to the top (no change), `2` moves above it → `2,1,3`, `3` moves above "
                 "→ `3,2,1`. The formula gives `marked[::-1] + rest` = `[3,2,1] + []`.",
        complexity="O(n × match cost) time, O(n) space.",
        pitfalls="- Testing lines while mutating: `:g` marks first, so copies appended by `t$` are never re-examined.\n"
                 "- Forgetting that `m0`/`t0` reverse the order.\n- Using `fullmatch`: `:g/abc/` matches anywhere in the "
                 "line.\n- Ignoring `invert`.",
        follow_up="Support `:g/pat/normal {keys}` by plugging in the simulator from `vim-normal-sim`, and "
                  "`:g/pat/s/a/b/g` using `vim-substitute`.",
    ),
),
# ------------------------------------------------------------------ vim-very-magic
dict(
    id="vim-very-magic",
    title="Translate a very magic pattern to Python",
    difficulty="Hard",
    pattern="Vim patterns",
    entry="veryMagicToPython",
    description=r"""
With the `\v` switch ("very magic"), Vim patterns read almost like Perl or Python regular expressions: every
ASCII character except letters, digits and underscore is special unless escaped. *Almost*. Translate a
very-magic pattern into an equivalent Python `re` pattern for the following subset.

A leading `\v` in the input, if present, is dropped. Then scan left to right and apply the **first** rule that fits:

| in the Vim pattern | emit | meaning |
|---|---|---|
| `\a` `\l` `\u` `\h` `\x` | `[A-Za-z]` `[a-z]` `[A-Z]` `[A-Za-z_]` `[0-9A-Fa-f]` | Vim-only character classes |
| `\` + any other letter or digit (`\d`, `\w`, `\s`, `\D`, `\t`, `\n`, …) | unchanged | same in both dialects |
| `\` + one of `. ^ $ * + ? ( ) [ ] { } \| \` | unchanged (still escaped) | a literal that Python must also escape |
| `\` + any other character (`\<`, `\>`, `\=`, `\/`, `\%`, …) | just that character | a literal that needs no escape in Python |
| `<` or `>` | `\b` | word boundary |
| `=` | `?` | optional (Vim's alias for `?`) |
| `%(` | `(?:` | non-capturing group |
| `{-}` | `*?` | as few as possible |
| `{-N}`, `{-N,}`, `{-N,M}`, `{-,M}` | `{N}?`, `{N,}?`, `{N,M}?`, `{,M}?` | lazy counted repeat |
| `[` … `]` | copied verbatim | a bracket expression: an optional `^` and then an optional `]` right after the `[` are part of it, a backslash protects the next character, and it ends at the next `]` |
| anything else | unchanged | `( ) \| + ? * . ^ $ {n,m}` and literals mean the same |

Inputs are well formed and never contain unescaped `@`, `~` or `&`.

Write `veryMagicToPython(pat)` returning the Python pattern string.

**Example:** `\v<(get|set)_\a+>` → `\b(get|set)_[A-Za-z]+\b`

**Example:** `\v#\x{6}` → `#[0-9A-Fa-f]{6}`

**Example:** `\vhttps=://%(www\.)=[^/ ]+` → `https?://(?:www\.)?[^/ ]+`
""",
    starter='''def veryMagicToPython(pat: str) -> str:
    pass
''',
    solution=VMAGIC_SOLUTION,
    tests=[
        [r"\v<(get|set)_\a+>"],
        [r"\v#\x{6}"],
        [r"\vhttps=://%(www\.)=[^/ ]+"],
        [r"<the>"],
        [r"\v\<b\>"],
        [r'\v"(.{-})"'],
        [r"\va{-2,3}b{-1,}c{-4}d{-,5}"],
        [r"\v\d+\.\d*"],
        [r"\v[<>=]+ \= \="],
        [r"\v[]<]x[^]>]y"],
        [r"\v[\]<]>"],
        [r"\v\u\l+%(\u\l+)*"],
        [r"\v^\s*(\h\w*)\s*\=\s*(.*)$"],
        [r"\va\/b\\c\%d"],
        [r"\v(\w+)\s+\1"],
        [""],
        [r"\v"],
        [r"\vx{2,4}y{3}"],
    ],
    examples=3,
    wrong_solutions=[
        '''def veryMagicToPython(pat):
    if pat.startswith("\\\\v"):
        pat = pat[2:]
    for a, b in (("\\\\a", "[A-Za-z]"), ("\\\\l", "[a-z]"), ("\\\\u", "[A-Z]"), ("\\\\h", "[A-Za-z_]"),
                 ("\\\\x", "[0-9A-Fa-f]"), ("%(", "(?:"), ("{-}", "*?"), ("<", "\\\\b"), (">", "\\\\b"), ("=", "?")):
        pat = pat.replace(a, b)
    return pat
''',
        VMAGIC_SOLUTION.replace('''        elif ch == "[":
            j = i + 1
            if j < n and pat[j] == "^":
                j += 1
            if j < n and pat[j] == "]":
                j += 1
            while j < n and pat[j] != "]":
                j += 2 if pat[j] == "\\\\" else 1
            out.append(pat[i:j + 1])
            i = j + 1
''', ""),
        VMAGIC_SOLUTION.replace('out.append("{" + body + "}?" if body else "*?")', 'out.append("*?")'),
        VMAGIC_SOLUTION.replace('''            elif nx in special:
                out.append("\\\\" + nx)
            else:
                out.append(nx)''', '''            else:
                out.append("\\\\" + nx)'''),
    ],
    guide=dict(
        prereqs="The *Patterns and search* lesson (magic levels). Comfortable reading Python regular expressions.",
        intuition="Very magic is already 90% Python syntax, so this is a pass-through scanner with a handful of "
                  "rewrites. What makes it a scanner rather than a chain of `str.replace` calls is *context*: a `<` "
                  "inside `[...]` or after a backslash must not become `\\b`.",
        hints=[
            "Process the string with an index, not with global replacements; decide what to do from the current character (and sometimes the next).",
            "Deal with the backslash case first: it consumes two characters and has four sub-cases.",
            "Copy a bracket expression in one go. Find its end carefully: `[]x]` and `[^]x]` contain a literal `]`.",
        ],
        brute_force="A sequence of `replace` calls handles the three examples but fails as soon as a rewritten "
                    "character appears escaped or inside a bracket expression, e.g. `[<>=]` or `\\<`.",
        approach="Loop with `i`; branch on backslash, `<`/`>`, `=`, `%(`, `{-`, `[`, default.\n\n**Dry run** "
                 "`https=://%(www\\.)=[^/ ]+`: `https` copied; `=` → `?`; `://` copied; `%(` → `(?:`; `www` copied; "
                 "`\\.` stays `\\.`; `)` copied; `=` → `?`; `[^/ ]` copied verbatim; `+` copied.",
        complexity="O(n) time and space.",
        pitfalls="- Global replacement of `=` or `<` corrupts bracket expressions and escaped literals.\n- `\\<` in very "
                 "magic is a *literal* less-than sign, the opposite of its meaning in the default magic mode.\n- `{-}` "
                 "is `*?`, but `{-1,}` is `{1,}?` (that is, `+?`).\n- `\\x` is a class in Vim but the start of a hex "
                 "escape in Python.",
        follow_up="Go the other way for *magic* (the default) patterns, where `(`, `|`, `+`, `?`, `{` need a "
                  "backslash to be special, and translate look-arounds (`@=`, `@!`, `@<=`).",
    ),
),
# ------------------------------------------------------------------ vim-jump-list
dict(
    id="vim-jump-list",
    title="Navigate the jump list",
    difficulty="Medium",
    pattern="Vim navigation",
    entry="jumpList",
    description=r"""
Vim records where you were before each *jump* (`G`, `/search`, `%`, a mark…) so that `Ctrl-O` can take you back
and `Ctrl-I` forward again. Model one window whose positions are plain line numbers.

State: the cursor line `cur` (initially `1`), a list `L` (initially empty) and an index `idx` into it.
`idx == len(L)` means "past the newest entry", which is where you are after any ordinary jump.

| op | effect |
|---|---|
| `["jump", n]` | record where you are, then go: remove every entry equal to `cur` from `L`, append `cur`, set `idx = len(L)`, then `cur = n` |
| `["back"]` (`Ctrl-O`) | if `idx == len(L)`, first record the current position so you can return to it: remove entries equal to `cur`, append `cur`, set `idx = len(L) - 1`. Then, if `idx > 0`: `idx -= 1` and `cur = L[idx]`; otherwise nothing more happens |
| `["fwd"]` (`Ctrl-I`) | if `idx < len(L) - 1`: `idx += 1` and `cur = L[idx]`; otherwise nothing happens |

Two consequences worth noticing: the list never holds the same line twice (the older duplicate is dropped), and
a jump made from the middle of the list does **not** discard the newer entries, unlike a browser's history.

Write `jumpList(ops)` returning `[cur, L]`.

**Example:** `[["jump", 40], ["jump", 90], ["back"]]` → `[40, [1, 40, 90]]`

**Example:** `[["jump", 40], ["jump", 90], ["back"], ["back"], ["fwd"]]` → `[40, [1, 40, 90]]`

**Example:** `[["jump", 40], ["jump", 90], ["back"], ["jump", 7]]` → `[7, [1, 90, 40]]`
""",
    starter='''def jumpList(ops: List[list]) -> list:
    pass
''',
    solution=JUMP_SOLUTION,
    tests=[
        [[["jump", 40], ["jump", 90], ["back"]]],
        [[["jump", 40], ["jump", 90], ["back"], ["back"], ["fwd"]]],
        [[["jump", 40], ["jump", 90], ["back"], ["jump", 7]]],
        [[]],
        [[["back"]]],
        [[["fwd"]]],
        [[["jump", 5], ["back"], ["back"], ["back"]]],
        [[["jump", 5], ["back"], ["fwd"], ["fwd"]]],
        [[["jump", 5], ["jump", 1], ["jump", 5], ["jump", 1]]],
        [[["jump", 5], ["back"], ["jump", 5], ["back"]]],
        [[["jump", 10], ["jump", 20], ["jump", 30], ["back"], ["back"], ["back"], ["fwd"], ["jump", 99], ["back"]]],
        [[["jump", 10], ["jump", 20], ["jump", 10], ["back"], ["back"]]],
        [[["jump", 3], ["jump", 3], ["back"]]],
        [[["jump", i] for i in range(2, 30)] + [["back"]] * 10 + [["fwd"]] * 3],
        [[["jump", 8], ["back"], ["fwd"], ["back"], ["fwd"]]],
    ],
    examples=3,
    wrong_solutions=[
        '''def jumpList(ops):
    cur = 1
    lst = []
    idx = 0
    for op in ops:
        if op[0] == "jump":
            lst = lst[:idx]
            lst.append(cur)
            idx = len(lst)
            cur = op[1]
        elif op[0] == "back":
            if idx == len(lst):
                lst.append(cur)
                idx = len(lst) - 1
            if idx > 0:
                idx -= 1
                cur = lst[idx]
        else:
            if idx < len(lst) - 1:
                idx += 1
                cur = lst[idx]
    return [cur, lst]
''',
        JUMP_SOLUTION.replace('''            if idx == len(lst):
                lst = [x for x in lst if x != cur]
                lst.append(cur)
                idx = len(lst) - 1
''', ""),
        JUMP_SOLUTION.replace('''            lst = [x for x in lst if x != cur]
            lst.append(cur)
            idx = len(lst)
            cur = op[1]''', '''            lst.append(cur)
            idx = len(lst)
            cur = op[1]'''),
    ],
    guide=dict(
        prereqs="The *Jumps* lesson. Lists and an index pointer; the browser-history design problem is a useful contrast.",
        intuition="The list stores *departure points*. A jump pushes the place you are leaving. The first `Ctrl-O` "
                  "must also push the place you are leaving, otherwise `Ctrl-I` could never bring you back to it. "
                  "De-duplication keeps the list a set of distinct places ordered by how recently you left them.",
        hints=[
            "Track three variables exactly as the statement names them: `cur`, `L`, `idx`.",
            "Write the de-duplicate-and-append step once; both `jump` and the first `back` use it.",
            "After the special first-`back` step, `idx` points at the entry for the current position, so a single `idx -= 1` moves to the previous place.",
        ],
        brute_force="There is no cheaper trick than simulating; a naive version simply uses list filtering for the "
                    "de-duplication, which is O(len(L)) per jump and entirely adequate (Vim caps the list at 100).",
        approach="Simulate each operation.\n\n**Dry run** of example 3: jump 40 → L = [1], cur 40. jump 90 → "
                 "L = [1, 40], cur 90, idx 2. back → idx equals len, so record 90: L = [1, 40, 90], idx 2 → 1, cur 40. "
                 "jump 7 → remove 40, append 40: L = [1, 90, 40], idx 3, cur 7.",
        complexity="O(len(ops) × len(L)) time, O(len(L)) space.",
        pitfalls="- Truncating the forward entries on a new jump, as a browser would.\n- Forgetting to record the "
                 "current position on the first `back`; then `fwd` cannot return.\n- Keeping duplicates, which makes "
                 "`Ctrl-O` appear to do nothing.\n- `fwd` stops at the last entry, index `len(L) - 1`, not at `len(L)`.",
        follow_up="Positions in real Vim are (file, line, column); extend the model with file names so that `Ctrl-O` "
                  "can cross buffers, and cap the list at 100 entries.",
    ),
),
# ------------------------------------------------------------------ vim-change-list
dict(
    id="vim-change-list",
    title="Walk the change list with g; and g,",
    difficulty="Easy",
    pattern="Vim navigation",
    entry="changeList",
    description=r"""
Separately from the jump list, each buffer remembers **where its text was changed**. `g;` travels back to older
changes and `g,` forward to newer ones. Model it with line numbers only.

State: cursor line `cur` (initially `1`), list `L` of changed lines (initially empty), index `idx` (initially `0`).

| op | effect |
|---|---|
| `["move", n]` | `cur = n`. Nothing is recorded: plain movement is not a change |
| `["edit", n]` | make a change on line `n`: `cur = n`; append `n` to `L` unless the newest entry is already `n` (consecutive changes on one line are merged); keep at most the newest 100 entries; then `idx = len(L)` (past the newest entry) |
| `["g;"]` | if `idx > 0`: `idx -= 1` and `cur = L[idx]`. Otherwise the command fails and the cursor stays |
| `["g,"]` | if `idx < len(L) - 1`: `idx += 1` and `cur = L[idx]`. Otherwise it fails and the cursor stays |

Return a list with the cursor line **after each `g;` or `g,`** (failed ones included), in order.

**Example:** `[["edit", 12], ["edit", 30], ["move", 99], ["g;"], ["g;"], ["g;"], ["g,"]]` → `[30, 12, 12, 30]`

**Example:** `[["edit", 5], ["edit", 5], ["edit", 8], ["g;"], ["g;"]]` → `[8, 5]`
""",
    starter='''def changeList(ops: List[list]) -> List[int]:
    pass
''',
    solution=CHANGE_SOLUTION,
    tests=[
        [[["edit", 12], ["edit", 30], ["move", 99], ["g;"], ["g;"], ["g;"], ["g,"]]],
        [[["edit", 5], ["edit", 5], ["edit", 8], ["g;"], ["g;"]]],
        [[]],
        [[["g;"], ["g,"]]],
        [[["move", 4], ["g;"]]],
        [[["edit", 7], ["g,"], ["g;"], ["g,"]]],
        [[["edit", 1], ["edit", 2], ["edit", 1], ["g;"], ["g;"], ["g;"], ["g;"]]],
        [[["edit", 3], ["edit", 9], ["g;"], ["g;"], ["edit", 20], ["g;"], ["g;"], ["g;"]]],
        [[["edit", 3], ["edit", 9], ["g;"], ["g;"], ["g,"], ["g,"], ["g,"]]],
        [[["edit", i] for i in range(1, 151)] + [["g;"]] * 101],
        [[["edit", 10], ["move", 50], ["edit", 10], ["g;"], ["g;"]]],
        [[["edit", 2], ["edit", 4], ["edit", 6], ["g;"], ["move", 77], ["g;"], ["g,"]]],
        [[["edit", 3], ["edit", 5], ["edit", 5], ["edit", 5], ["g;"], ["g;"], ["g;"]]],
    ],
    examples=2,
    wrong_solutions=[
        CHANGE_SOLUTION.replace("            if not lst or lst[-1] != cur:\n                lst.append(cur)",
                                "            if True:\n                lst.append(cur)"),
        CHANGE_SOLUTION.replace("            idx = len(lst)\n", "            idx = len(lst) - 1\n"),
        CHANGE_SOLUTION.replace("            if idx < len(lst) - 1:", "            if idx < len(lst):"),
        CHANGE_SOLUTION.replace("                if len(lst) > 100:\n                    lst.pop(0)\n", ""),
    ],
    guide=dict(
        prereqs="The *Jumps* lesson (change list section).",
        intuition="It is a history list with a cursor into it, simpler than the jump list: only edits append, "
                  "navigation never modifies the list, and any new edit resets the index to just past the end.",
        hints=[
            "Keep `idx == len(L)` after every edit, so the first `g;` lands on the newest change.",
            "Merging means: compare with `L[-1]` before appending.",
            "Append to the output after *every* `g;`/`g,`, even when the index did not move.",
        ],
        brute_force="Direct simulation is already optimal; the only inefficiency to avoid is `pop(0)` on a huge list, "
                    "which the 100-entry cap makes irrelevant (use `collections.deque(maxlen=100)` if you prefer).",
        approach="One loop, four cases.\n\n**Dry run** of example 1: edits give L = [12, 30], idx 2. `move 99` changes "
                 "only the cursor. `g;` → idx 1, cur 30. `g;` → idx 0, cur 12. `g;` → idx is 0: fails, cur stays 12. "
                 "`g,` → idx 1, cur 30.",
        complexity="O(len(ops)) time, O(min(edits, 100)) space.",
        pitfalls="- Recording plain movement.\n- Starting the index *on* the newest entry: then the first `g;` skips it.\n"
                 "- Letting `g,` step to `len(L)`, which is not an entry.\n- Forgetting the cap: with 150 edits the "
                 "oldest reachable change is line 51.",
        follow_up="Add the `'.` mark (line of the last change) and `gi` (resume inserting where Insert mode was last "
                  "stopped), both of which read from the same bookkeeping.",
    ),
),
# ------------------------------------------------------------------ vim-buffer-list
dict(
    id="vim-buffer-list",
    title="Buffer list and the alternate file",
    difficulty="Medium",
    pattern="Vim files",
    entry="bufferSim",
    description=r"""
Simulate the buffer list of one Vim window. State: the current buffer name `cur` (initially `""`, meaning no
file), the **alternate** buffer `alt` (initially `""`; this is what `#` and `Ctrl-^` refer to) and the ordered
list `L` of listed buffers (initially empty).

| op | Ex command | effect |
|---|---|---|
| `["e", name]` | `:edit name` | if `name == cur`, nothing. Otherwise append `name` to `L` unless already listed; if `cur` is not `""` set `alt = cur`; then `cur = name` |
| `["bn"]` | `:bnext` | if `L` has more than one buffer: `alt = cur`, and `cur` becomes the buffer after it in `L`, wrapping from the last to the first. Otherwise nothing |
| `["bp"]` | `:bprevious` | the same in the other direction, wrapping from the first to the last |
| `["alt"]` | `Ctrl-^` or `:b#` | if `alt` is not `""`, swap `cur` and `alt`. Otherwise nothing |
| `["bd"]` | `:bdelete` | if `cur` is `""`, nothing. Otherwise remove `cur` from `L` (remember its index `i`). The new current buffer is `alt` if `alt` is not `""`; else the buffer now at index `i` of `L`; else, if the deleted buffer was last, the new last buffer; else `""` when `L` is empty. In all cases `alt` becomes `""` |

Write `bufferSim(ops)` returning `[cur, alt, L]`.

**Example:** `[["e","a.py"], ["e","b.py"], ["e","c.py"], ["alt"]]` → `["b.py", "c.py", ["a.py","b.py","c.py"]]`

**Example:** `[["e","a.py"], ["e","b.py"], ["e","c.py"], ["bn"], ["bn"]]` → `["b.py", "a.py", ["a.py","b.py","c.py"]]`

**Example:** `[["e","a.py"], ["e","b.py"], ["bd"], ["bd"]]` → `["", "", []]`
""",
    starter='''def bufferSim(ops: List[List[str]]) -> list:
    pass
''',
    solution=BUF_SOLUTION,
    tests=[
        [[["e", "a.py"], ["e", "b.py"], ["e", "c.py"], ["alt"]]],
        [[["e", "a.py"], ["e", "b.py"], ["e", "c.py"], ["bn"], ["bn"]]],
        [[["e", "a.py"], ["e", "b.py"], ["bd"], ["bd"]]],
        [[]],
        [[["bn"], ["bp"], ["alt"], ["bd"]]],
        [[["e", "a.py"], ["alt"], ["bn"], ["bp"]]],
        [[["e", "a.py"], ["e", "a.py"], ["e", "b.py"], ["e", "a.py"]]],
        [[["e", "a.py"], ["e", "b.py"], ["e", "c.py"], ["bp"], ["bp"], ["bp"]]],
        [[["e", "a.py"], ["e", "b.py"], ["e", "c.py"], ["alt"], ["alt"], ["alt"]]],
        [[["e", "a.py"], ["e", "b.py"], ["e", "c.py"], ["bd"], ["alt"]]],
        [[["e", "a.py"], ["e", "b.py"], ["e", "c.py"], ["bd"], ["bd"]]],
        [[["e", "a.py"], ["e", "b.py"], ["e", "c.py"], ["e", "a.py"], ["bd"], ["bd"]]],
        [[["e", "a.py"], ["e", "b.py"], ["e", "c.py"], ["bd"], ["bd"], ["bn"], ["e", "d.py"], ["alt"]]],
        [[["e", "x"], ["e", "y"], ["e", "z"], ["e", "x"], ["bd"], ["bd"], ["bd"], ["bd"]]],
        [[["e", "m"], ["e", "n"], ["bn"], ["bn"], ["bn"]]],
        [[["e", "a.py"], ["e", "a.py"]]],
        [[["e", "a"], ["e", "b"], ["e", "c"], ["e", "d"], ["e", "b"], ["bd"], ["bd"]]],
        [[["e", "a"], ["e", "b"], ["e", "c"], ["e", "d"], ["e", "c"], ["e", "b"], ["bd"], ["bd"]]],
    ],
    examples=3,
    wrong_solutions=[
        BUF_SOLUTION.replace("            if cur:\n                alt = cur\n            cur = name",
                             "            alt = cur\n            cur = name").replace(
                             "            if name == cur:\n                continue\n", ""),
        BUF_SOLUTION.replace("                alt = cur\n                cur = lst[(i + step) % len(lst)]",
                             "                cur = lst[(i + step) % len(lst)]"),
        BUF_SOLUTION.replace("                cur = lst[i] if i < len(lst) else lst[-1]", "                cur = lst[0]"),
        BUF_SOLUTION.replace("            if alt:\n                cur = alt\n            elif lst:", "            if lst:"),
    ],
    guide=dict(
        prereqs="The *Buffers and the argument list* lesson.",
        intuition="Two names and a list. Every command that switches buffers demotes the old current buffer to "
                  "*alternate*; `Ctrl-^` simply swaps the two names. Deleting is the only fiddly part because a "
                  "replacement has to be chosen.",
        hints=[
            "Treat the empty string as 'no buffer' consistently for both `cur` and `alt`.",
            "`(i + step) % len(L)` gives wrap-around in both directions.",
            "For `bd`, record the index before popping; after popping, that same index is the buffer that used to follow.",
        ],
        brute_force="Simulation is the solution. Using `list.index` makes each step O(len(L)); keeping a position "
                    "dict would make it O(1) but is not worth the bookkeeping at this size.",
        approach="Dispatch on the op.\n\n**Dry run** of example 2: after three edits cur = c.py, alt = b.py. `bn` "
                 "wraps: alt = c.py, cur = a.py. `bn`: alt = a.py, cur = b.py. Result `[b.py, a.py, …]`.",
        complexity="O(len(ops) × len(L)) time, O(len(L)) space.",
        pitfalls="- Setting `alt` when re-editing the current buffer (it must not become its own alternate).\n"
                 "- Forgetting that `:bnext` also updates the alternate.\n- Off-by-one choosing the successor after "
                 "deleting the last entry.\n- `Ctrl-^` with no alternate is an error, not a jump to the first buffer.",
        follow_up="Add `:b N` by buffer number (numbers are never reused), hidden-and-modified buffers that refuse "
                  "`:bdelete` without `!`, and the argument list as a separate, user-curated subset.",
    ),
),
# ------------------------------------------------------------------ vim-visual-block-insert
dict(
    id="vim-visual-block-insert",
    title="Visual-block insert and append",
    difficulty="Medium",
    pattern="Vim visual mode",
    entry="blockEdit",
    description=r"""
In Visual-block mode (`Ctrl-V`) you select a rectangle, and `I` or `A` then types the same text on every row of
it. Reproduce the three common cases on rows `top..bottom` (0-based, inclusive):

| `mode` | keys in Vim | effect on each row of the block |
|---|---|---|
| `"I"` | `Ctrl-V` … `I text Esc` | insert `text` **before** column `col` (the block's left edge). Rows too short to have a character at `col` (`len(row) <= col`) are **left alone** |
| `"A"` | `Ctrl-V` … `A text Esc` | append `text` **after** column `col` (the block's right edge). Rows too short are first **padded with spaces** up to and including column `col` |
| `"$A"` | `Ctrl-V` … `$A text Esc` | the block extends to the end of every row: append `text` at the end of each row, whatever its length (`col` is ignored) |

Rows outside `top..bottom` are untouched. Return the new list of lines.

**Example:** `lines = ["alpha", "beta", "gamma"]`, rows `0..2`, `col = 0`, `mode = "I"`, `text = "- "` → `["- alpha", "- beta", "- gamma"]`

**Example:** `lines = ["x = 1", "yy = 22", "z"]`, rows `0..2`, `mode = "$A"`, `text = ";"` → `["x = 1;", "yy = 22;", "z;"]`

**Example:** `lines = ["abcdef", "ab", "abcd"]`, rows `0..2`, `col = 3`, `mode = "A"`, `text = "|"` → `["abcd|ef", "ab  |", "abcd|"]`
""",
    starter='''def blockEdit(lines: List[str], top: int, bottom: int, col: int, mode: str, text: str) -> List[str]:
    pass
''',
    solution=BLOCK_SOLUTION,
    tests=[
        [["alpha", "beta", "gamma"], 0, 2, 0, "I", "- "],
        [["x = 1", "yy = 22", "z"], 0, 2, 0, "$A", ";"],
        [["abcdef", "ab", "abcd"], 0, 2, 3, "A", "|"],
        [["abcdef", "ab", "abcd"], 0, 2, 3, "I", "|"],
        [["abcdef", "abc", "abcd"], 0, 2, 3, "I", "#"],
        [["one", "two", "three", "four"], 1, 2, 0, "I", "// "],
        [["one", "two", "three", "four"], 1, 2, 0, "$A", ","],
        [["", "", "x"], 0, 2, 0, "I", "> "],
        [["", "", "x"], 0, 2, 0, "A", "!"],
        [["", "", "x"], 0, 2, 0, "$A", "."],
        [["name", "id"], 0, 1, 5, "A", "= None"],
        [["solo"], 0, 0, 3, "A", "?"],
        [["solo"], 0, 0, 3, "I", "?"],
        [["a b c", "d e f"], 0, 1, 2, "I", ""],
        [["r%d" % i for i in range(30)], 5, 24, 1, "A", "_"],
    ],
    examples=3,
    wrong_solutions=[
        BLOCK_SOLUTION.replace("            if len(s) > col:\n                out[r] = s[:col] + text + s[col:]",
                               "            out[r] = s[:col] + text + s[col:]"),
        BLOCK_SOLUTION.replace("            if len(s) <= col:\n                s = s + \" \" * (col + 1 - len(s))\n", ""),
        BLOCK_SOLUTION.replace("out[r] = s[:col + 1] + text + s[col + 1:]", "out[r] = s[:col] + text + s[col:]"),
        BLOCK_SOLUTION.replace("    for r in range(top, bottom + 1):", "    for r in range(len(out)):"),
    ],
    guide=dict(
        prereqs="The *Visual mode* lesson (Visual-block). String slicing.",
        intuition="A block edit is the same single-line edit applied to each row; the three modes differ only in "
                  "**where** on the row the text goes and in **how short rows are treated**: skipped by `I`, padded by "
                  "`A`, irrelevant for `$A`.",
        hints=[
            "Copy the list first so that rows outside the block stay as they are.",
            "`I` inserts at index `col`; `A` inserts at index `col + 1`.",
            "For `A` on a short row, pad to length `col + 1` before slicing.",
        ],
        brute_force="Convert every row to a list of characters and insert character by character. It is equivalent "
                    "and only slower by a constant factor.",
        approach="Loop over the rows in the block and splice.\n\n**Dry run** `[\"abcdef\", \"ab\", \"abcd\"]`, "
                 "col 3, `A`, `|`: row 0 → `abcd` + `|` + `ef`. Row 1 has length 2 ≤ 3: pad to `ab` + two spaces "
                 "(length 4), then append → `ab  |`. Row 2 → `abcd|`.",
        complexity="O(total length of the rows in the block) time and space.",
        pitfalls="- Applying `I` to short rows: Python slicing would silently append the text at their end.\n- Padding "
                 "one space too few or too many for `A`.\n- Confusing `A` (rectangular, pads) with `$A` (ragged right "
                 "edge, never pads).\n- Editing rows outside the block.",
        follow_up="Add `c` (replace the block's columns `col..col2` on each row with the text) and `r{char}` (overwrite "
                  "every character of the block).",
    ),
),
]
