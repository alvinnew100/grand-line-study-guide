"""Linux CLI problems, set 1: permission bits, umask and path normalisation."""

PROBLEMS = [
# ------------------------------------------------------------------ octal -> symbolic
dict(
    id="cli-octal-to-symbolic",
    title="Octal Mode to rwx String",
    difficulty="Easy",
    pattern="Permissions",
    entry="octal_to_symbolic",
    description=r"""
`ls -l` shows permissions as nine characters such as `rwxr-xr-x`, while `chmod` and `stat` often
speak octal (`755`). Write the translator.

Given `mode`, a string of **one to four octal digits**, return the nine-character symbolic string.

* The last three digits are owner, group and other. In each digit, 4 = read, 2 = write, 1 = execute.
* A fourth (leading) digit holds the special bits: 4 = setuid, 2 = setgid, 1 = sticky.
  * setuid replaces the **owner** execute slot with `s` (execute also set) or `S` (execute not set).
  * setgid does the same in the **group** execute slot.
  * sticky replaces the **other** execute slot with `t` or `T`.
* Shorter strings are padded on the left with zeros, so `"5"` means `0005`.

**Example 1:** `mode = "755"` → `"rwxr-xr-x"`

**Example 2:** `mode = "4755"` → `"rwsr-xr-x"`

**Example 3:** `mode = "1777"` → `"rwxrwxrwt"`
""",
    starter='''def octal_to_symbolic(mode: str) -> str:
    pass
''',
    solution='''def octal_to_symbolic(mode):
    n = int(mode, 8)
    chars = []
    for shift in (6, 3, 0):
        bits = (n >> shift) & 7
        chars.append("r" if bits & 4 else "-")
        chars.append("w" if bits & 2 else "-")
        chars.append("x" if bits & 1 else "-")
    special = (n >> 9) & 7
    for bit, pos, letter in ((4, 2, "s"), (2, 5, "s"), (1, 8, "t")):
        if special & bit:
            chars[pos] = letter if chars[pos] == "x" else letter.upper()
    return "".join(chars)
''',
    tests=[
        ["755"], ["4755"], ["1777"], ["644"], ["0600"], ["777"], ["000"], ["2750"],
        ["4644"], ["7777"], ["7000"], ["0"], ["5"], ["640"], ["1770"],
    ],
    examples=3,
    wrong_solutions=[
        '''def octal_to_symbolic(mode):
    n = int(mode, 8)
    out = ""
    for shift in (6, 3, 0):
        b = (n >> shift) & 7
        out += ("r" if b & 4 else "-") + ("w" if b & 2 else "-") + ("x" if b & 1 else "-")
    return out
''',
        '''def octal_to_symbolic(mode):
    mode = mode[-3:]
    table = ["---", "--x", "-w-", "-wx", "r--", "r-x", "rw-", "rwx"]
    return "".join(table[int(d)] for d in mode)
''',
    ],
    guide=dict(
        prereqs="The permissions lesson: the three classes (owner, group, other), the r/w/x bits and the idea that an octal digit is just three bits. Python bit operators `>>` and `&`.",
        intuition="An octal digit is a three-bit number, and each bit answers one yes/no question: read? write? execute? So a mode such as `754` is really twelve switches laid side by side. Converting to text means walking over those switches from left to right and printing a letter when a switch is on and a dash when it is off. The special bits do not get their own columns; they *overlay* the execute column of the class they belong to, which is why you see `s` or `t` where an `x` would be.",
        hints=[
            "Convert the whole string to an integer with `int(mode, 8)` so padding stops being a concern.",
            "Shift right by 6, 3 and 0 and mask with 7 to isolate the owner, group and other triplets.",
            "After building the nine plain characters, inspect bits 11, 10 and 9. For each one that is set, rewrite position 2, 5 or 8: lowercase when an `x` is already there, uppercase when it is a dash.",
        ],
        brute_force="Build a lookup table from each digit `0`–`7` to its three-character string and join three lookups. That is perfectly fine for the low nine bits and is O(1), but it needs a second pass to handle a leading special digit and careful padding when the input is shorter than three digits.",
        approach="""1. `n = int(mode, 8)` — now `"5"`, `"005"` and `"0005"` are all the same number.
2. For each shift in `(6, 3, 0)`, take `(n >> shift) & 7` and emit `r`, `w`, `x` or dashes for bits 4, 2, 1.
3. Take `special = (n >> 9) & 7`.
4. For setuid (4) look at index 2, setgid (2) index 5, sticky (1) index 8. Replace `x` with the lowercase letter, `-` with the uppercase one.

**Dry run, `"2750"`:** `n = 0o2750`. Owner bits `7` → `rwx`; group bits `5` → `r-x`; other `0` → `---`. Plain string: `rwxr-x---`. Special is `2` (setgid): index 5 holds `x`, so it becomes `s`. Result `rwxr-s---`.""",
        complexity="Time O(1) and space O(1): there are always exactly twelve bits to inspect.",
        pitfalls="""* Forgetting the uppercase forms. `4644` is `rwSr--r--` — the capital letter is how `ls` warns you that setuid is on but execute is off, which is almost always a mistake.
* Slicing the last three characters before converting breaks inputs such as `"5"`.
* Mixing up the order of bit values: read is the **high** bit (4), execute is the low one (1).""",
        follow_up="Add the leading file-type character (`-`, `d`, `l`) to produce the full ten-character field, then try the inverse problem.",
    ),
),
# ------------------------------------------------------------------ symbolic -> octal
dict(
    id="cli-symbolic-to-octal",
    title="rwx String to Octal Mode",
    difficulty="Easy",
    pattern="Permissions",
    entry="symbolic_to_octal",
    description=r"""
Go the other way: read the permission field printed by `ls -l` and return the number you would hand
to `chmod`.

`perms` is either nine characters (`rwxr-xr-x`) or ten characters with a leading file-type character
(`drwxr-xr-x`, `-rw-r--r--`, `lrwxrwxrwx`), which you must ignore.

Return a **four-digit** octal string: special bits, owner, group, other.

* In the owner execute slot, `s` means setuid **and** execute, `S` means setuid without execute.
* In the group execute slot, `s`/`S` mean the same for setgid.
* In the other execute slot, `t` means sticky and execute, `T` sticky without execute.

**Example 1:** `"rwxr-xr-x"` → `"0755"`

**Example 2:** `"-rwsr-xr-x"` → `"4755"`

**Example 3:** `"drwxrwxrwt"` → `"1777"`
""",
    starter='''def symbolic_to_octal(perms: str) -> str:
    pass
''',
    solution='''def symbolic_to_octal(perms):
    if len(perms) == 10:
        perms = perms[1:]
    digits = [0, 0, 0]
    special = 0
    special_bit = (4, 2, 1)
    for cls in range(3):
        r, w, x = perms[cls * 3: cls * 3 + 3]
        if r == "r":
            digits[cls] += 4
        if w == "w":
            digits[cls] += 2
        if x in "xst":
            digits[cls] += 1
        if x in "sStT":
            special += special_bit[cls]
    return str(special) + "".join(str(d) for d in digits)
''',
    tests=[
        ["rwxr-xr-x"], ["-rwsr-xr-x"], ["drwxrwxrwt"], ["rw-r--r--"], ["---------"],
        ["rwxrwxrwx"], ["-rwSr--r--"], ["drwxr-s---"], ["rwsrwsrwt"], ["--S--S--T"],
        ["lrwxrwxrwx"], ["-rw-------"], ["drwxrwx--T"], ["r--r--r--"],
    ],
    examples=3,
    wrong_solutions=[
        '''def symbolic_to_octal(perms):
    if len(perms) == 10:
        perms = perms[1:]
    out = "0"
    for c in range(3):
        t = perms[c * 3: c * 3 + 3]
        out += str((4 if t[0] == "r" else 0) + (2 if t[1] == "w" else 0) + (1 if t[2] == "x" else 0))
    return out
''',
        '''def symbolic_to_octal(perms):
    if len(perms) == 10:
        perms = perms[1:]
    digits = [0, 0, 0]
    special = 0
    for cls in range(3):
        r, w, x = perms[cls * 3: cls * 3 + 3]
        digits[cls] = (4 if r == "r" else 0) + (2 if w == "w" else 0) + (1 if x != "-" else 0)
        if x in "sStT":
            special += (4, 2, 1)[cls]
    return str(special) + "".join(map(str, digits))
''',
    ],
    guide=dict(
        prereqs="The permissions lesson and the previous problem. String slicing.",
        intuition="Each group of three characters is one octal digit written out long-hand. Add 4 for a letter in the first slot, 2 for the second and 1 for the third. The only twist is that the third slot is overloaded: it reports the execute bit **and** one special bit at the same time, using letter case to tell you about execute.",
        hints=[
            "Strip the type character first if the string has ten characters.",
            "Process the string in three slices of three. The first two characters of each slice are simple; treat the third separately.",
            "Third slot: lowercase `x`, `s`, `t` all imply execute. Any of `s S t T` implies the special bit for that class (4, 2, 1 for owner, group, other).",
        ],
        brute_force="Enumerate all 4096 modes, convert each to a string with the previous problem's function, and return the one that matches. It works and proves the two functions are inverses, but it is 4096 times more work than reading the string once.",
        approach="""1. Drop the leading type character when `len(perms) == 10`.
2. For class index 0, 1, 2 read the slice `perms[3*i : 3*i+3]` as `r, w, x`.
3. Add 4 if `r == 'r'`, 2 if `w == 'w'`, 1 if `x` is one of `x s t`.
4. If `x` is one of `s S t T`, add the class's special value (4, 2, 1) to the leading digit.
5. Concatenate the four digits.

**Dry run, `"drwxr-s---"`:** strip `d`. Owner `rwx` → 7. Group `r-s` → 4 + 0 + 1 = 5 and special += 2. Other `---` → 0. Answer `"2750"`.""",
        complexity="Time O(1), space O(1): nine characters, always.",
        pitfalls="""* Treating `S` or `T` as execute. Capital means the execute bit is **off**.
* Treating any non-dash in the third slot as execute — the same mistake from the other side.
* Forgetting that symbolic links show `l` and directories `d` in front.""",
        follow_up="Validate the input and raise an error for impossible strings such as `rwtr-xr-x` (a `t` can only appear in the last slot).",
    ),
),
# ------------------------------------------------------------------ chmod expression
dict(
    id="cli-chmod-apply",
    title="Apply a chmod Expression",
    difficulty="Medium",
    pattern="Permissions",
    entry="apply_chmod",
    description=r"""
Implement the symbolic mode language of `chmod`.

`mode` is a three-digit octal string (the current permissions). `expr` is a comma-separated list of
clauses, applied **left to right**. Each clause has the shape `[who][op][perms]`:

* `who` — zero or more of `u` (owner), `g` (group), `o` (other), `a` (all three). An empty `who`
  means `a` (ignore the umask subtlety of the real command).
* `op` — `+` adds the listed bits, `-` removes them, `=` makes the listed bits the **exact** set for
  those classes (anything not listed is cleared).
* `perms` — zero or more of `r`, `w`, `x`. An empty list is legal: `go=` removes everything from
  group and other.

Return the new mode as a three-digit octal string.

**Example 1:** `mode = "644", expr = "u+x"` → `"744"`

**Example 2:** `mode = "777", expr = "go-w"` → `"755"`

**Example 3:** `mode = "600", expr = "u+x,go=r"` → `"744"`
""",
    starter='''def apply_chmod(mode: str, expr: str) -> str:
    pass
''',
    solution='''def apply_chmod(mode, expr):
    n = int(mode, 8)
    shift = {"u": 6, "g": 3, "o": 0}
    value = {"r": 4, "w": 2, "x": 1}
    for clause in expr.split(","):
        i = 0
        while i < len(clause) and clause[i] in "ugoa":
            i += 1
        who, op, perms = clause[:i], clause[i], clause[i + 1:]
        classes = set()
        for c in who or "a":
            classes.update("ugo" if c == "a" else c)
        bits = 0
        for p in perms:
            bits |= value[p]
        for c in classes:
            s = shift[c]
            if op == "+":
                n |= bits << s
            elif op == "-":
                n &= ~(bits << s)
            else:
                n = (n & ~(7 << s)) | (bits << s)
    return format(n & 0o777, "03o")
''',
    tests=[
        ["644", "u+x"], ["777", "go-w"], ["600", "u+x,go=r"], ["000", "a+rwx"], ["755", "a-x"],
        ["640", "+x"], ["777", "go="], ["123", "u=rwx,g=rx,o="], ["644", "ug+w,o-r"],
        ["700", "g+rx,o+rx,u-w"], ["444", "u+w,u-r"], ["666", "=r"], ["751", "a=rwx,o-rwx"],
        ["000", "u+r,u+w,u+x"], ["777", "ugo-rwx"],
    ],
    examples=3,
    wrong_solutions=[
        '''def apply_chmod(mode, expr):
    n = int(mode, 8)
    shift = {"u": 6, "g": 3, "o": 0}
    value = {"r": 4, "w": 2, "x": 1}
    for clause in expr.split(","):
        i = 0
        while i < len(clause) and clause[i] in "ugoa":
            i += 1
        who, op, perms = clause[:i] or "a", clause[i], clause[i + 1:]
        bits = sum(value[p] for p in set(perms))
        for c in ("ugo" if "a" in who else who):
            s = shift[c]
            if op == "-":
                n &= ~(bits << s)
            else:
                n |= bits << s
    return format(n, "03o")
''',
        '''def apply_chmod(mode, expr):
    n = int(mode, 8)
    shift = {"u": 6, "g": 3, "o": 0}
    value = {"r": 4, "w": 2, "x": 1}
    for clause in expr.split(","):
        i = 0
        while i < len(clause) and clause[i] in "ugoa":
            i += 1
        who, op, perms = clause[:i] or "u", clause[i], clause[i + 1:]
        bits = sum(value[p] for p in set(perms))
        for c in ("ugo" if "a" in who else who):
            s = shift[c]
            if op == "+":
                n |= bits << s
            elif op == "-":
                n &= ~(bits << s)
            else:
                n = (n & ~(7 << s)) | (bits << s)
    return format(n, "03o")
''',
    ],
    guide=dict(
        prereqs="The permissions lesson (symbolic notation for `chmod`). Bit operations: OR to set, AND-NOT to clear, shifts to position a triplet.",
        intuition="Octal notation replaces the whole mode; symbolic notation *edits* it. Every clause names some classes and some bits and one of three edits: switch on, switch off, or overwrite. If you keep the mode as a nine-bit integer, those edits are exactly `|=`, `&= ~` and 'clear the triplet then OR'. The parsing is tiny: leading letters from `ugoa`, one operator character, the rest are permission letters.",
        hints=[
            "Split on commas and handle clauses one at a time, carrying the integer mode forward.",
            "Scan the clause while characters are in `ugoa`; the character you stop on is the operator.",
            "Compute a three-bit mask from the permission letters once, then shift it by 6, 3 or 0 for each class named. For `=`, first clear `7 << shift`.",
        ],
        brute_force="Convert the mode to a nine-character list, edit individual characters for every (class, permission) pair and convert back. This is easy to get right and still constant time; it is simply more code and two extra conversions.",
        approach="""1. `n = int(mode, 8)`.
2. For each clause, peel off `who`, `op`, `perms`. Empty `who` becomes all three classes.
3. `bits` = OR of 4/2/1 for the letters in `perms` (possibly 0).
4. For each class with shift `s`: `+` → `n |= bits << s`; `-` → `n &= ~(bits << s)`; `=` → `n = (n & ~(7 << s)) | (bits << s)`.
5. Format with three octal digits.

**Dry run, `"600"` with `"u+x,go=r"`:** start `110 000 000`. Clause `u+x`: bits = 1, shifted by 6 → `111 000 000` (700). Clause `go=r`: bits = 4; group triplet cleared then set to 4; other the same → `111 100 100` = `744`.""",
        complexity="Time O(length of `expr`), space O(1).",
        pitfalls="""* Implementing `=` as `+`. `666` with `=r` must become `444`, not stay `666`.
* An empty permission list with `=` is not an error; it clears the classes.
* Clauses are sequential: `u+w,u-r` on `444` gives `244`, and a later clause may undo an earlier one.
* Formatting without zero padding turns `044` into `44`.""",
        follow_up="Real `chmod` also accepts `X` (execute only if the target is a directory or already executable by someone), the special letters `s` and `t`, and copies such as `g=u`. Add them.",
    ),
),
# ------------------------------------------------------------------ umask
dict(
    id="cli-umask-result",
    title="What Does This umask Produce?",
    difficulty="Easy",
    pattern="Permissions",
    entry="umask_result",
    description=r"""
When a program creates a file it asks for a generous default — `666` for regular files and `777` for
directories — and the kernel then **removes** every bit that is set in the process's umask.

Given `umask` (an octal string of three or four digits; ignore a leading special digit) and `kind`
(`"file"` or `"dir"`), return the resulting permissions as a three-digit octal string.

**Example 1:** `umask = "022", kind = "file"` → `"644"`

**Example 2:** `umask = "022", kind = "dir"` → `"755"`

**Example 3:** `umask = "133", kind = "file"` → `"644"` (not `533` — a mask removes bits, it does not subtract)
""",
    starter='''def umask_result(umask: str, kind: str) -> str:
    pass
''',
    solution='''def umask_result(umask, kind):
    base = 0o666 if kind == "file" else 0o777
    mask = int(umask, 8) & 0o777
    return format(base & ~mask, "03o")
''',
    tests=[
        ["022", "file"], ["022", "dir"], ["133", "file"], ["002", "file"], ["002", "dir"],
        ["077", "file"], ["077", "dir"], ["027", "file"], ["027", "dir"], ["000", "file"],
        ["777", "dir"], ["0022", "dir"], ["111", "file"], ["111", "dir"], ["357", "file"],
    ],
    examples=3,
    wrong_solutions=[
        '''def umask_result(umask, kind):
    base = "666" if kind == "file" else "777"
    u = umask[-3:]
    return "".join(str(int(b) - int(m)) for b, m in zip(base, u))
''',
        '''def umask_result(umask, kind):
    mask = int(umask, 8) & 0o777
    return format(0o777 & ~mask, "03o")
''',
    ],
    guide=dict(
        prereqs="The permissions lesson (default permissions and `umask`). Bitwise AND and NOT.",
        intuition="Think of the umask as a stencil laid over the requested permissions: wherever the stencil has a 1, the bit underneath is scraped away; wherever it has a 0, the request shows through. Scraping away a bit that was never set does nothing — and that is exactly where the popular 'just subtract' shortcut goes wrong.",
        hints=[
            "Pick the base first: `0o666` for files, `0o777` for directories.",
            "The operation is `base AND (NOT mask)`.",
            "Convert with `int(umask, 8)`, mask off anything above the low nine bits, and format the result with `format(x, '03o')`.",
        ],
        brute_force="Go digit by digit and, inside each digit, bit by bit: keep a bit of the base only if the same bit of the mask is 0. Nine tiny decisions; correct, just verbose.",
        approach="""1. `base = 0o666` or `0o777`.
2. `mask = int(umask, 8) & 0o777` (drops a leading special digit such as the first `0` in `0022`).
3. `result = base & ~mask`.
4. Return three octal digits.

**Dry run, umask `133`, file:** base `110 110 110`, mask `001 011 011`. NOT mask = `110 100 100`. AND gives `110 100 100` = `644`. Subtraction would have claimed `533`, which even grants execute to the owner — clearly impossible when the base never had it.""",
        complexity="O(1) time and space.",
        pitfalls="""* Subtracting digits. It only agrees with the real rule when the mask's bits are a subset of the base's bits.
* Using 777 for regular files. Ordinary files never get execute from creation; that is always an explicit `chmod`.
* Python's `~mask` is negative; ANDing with the base brings it back into range, so order of operations matters.""",
        follow_up="Go backwards: given the permissions you *want* new directories to have, compute the umask (`0o777 & ~wanted`).",
    ),
),
# ------------------------------------------------------------------ path normalisation
dict(
    id="cli-normalize-path",
    title="Resolve a Path Like cd Does",
    difficulty="Medium",
    pattern="Paths",
    entry="resolve_path",
    description=r"""
The shell lets you type relative paths, repeated slashes, `.` and `..`. Before anything touches the
disk these are reduced to one clean absolute path. Assume there are **no symbolic links**, so the
reduction is pure string work.

Given the absolute current directory `cwd` and a `path` typed by the user, return the canonical
absolute path:

* If `path` starts with `/` it is absolute and `cwd` is ignored; otherwise it is relative to `cwd`.
* `.` means "this directory" and disappears.
* `..` removes the previous component. At the root, `..` stays at the root.
* Runs of slashes collapse to one; a trailing slash is dropped (except for the root itself).
* An empty `path` means `cwd`.

**Example 1:** `cwd = "/home/mira", path = "notes/../photos"` → `"/home/mira/photos"`

**Example 2:** `cwd = "/var/log", path = "../../etc//ssh/./"` → `"/etc/ssh"`

**Example 3:** `cwd = "/srv", path = "/../.."` → `"/"`
""",
    starter='''def resolve_path(cwd: str, path: str) -> str:
    pass
''',
    solution='''def resolve_path(cwd, path):
    full = path if path.startswith("/") else cwd + "/" + path
    stack = []
    for part in full.split("/"):
        if part == "" or part == ".":
            continue
        if part == "..":
            if stack:
                stack.pop()
        else:
            stack.append(part)
    return "/" + "/".join(stack)
''',
    tests=[
        ["/home/mira", "notes/../photos"], ["/var/log", "../../etc//ssh/./"], ["/srv", "/../.."],
        ["/home/mira", ""], ["/", "."], ["/", "tmp"], ["/a/b/c", "../../../../x"],
        ["/a/b", "./././c"], ["/a/b/", "c/"], ["/x", "/usr//local///bin/"], ["/a/b", ".."],
        ["/a/b", "..."], ["/a/b", ".hidden/../..data"], ["/one/two/three", "../../two/../four/five/.."],
    ],
    examples=3,
    wrong_solutions=[
        '''def resolve_path(cwd, path):
    full = path if path.startswith("/") else cwd + "/" + path
    stack = []
    for part in full.split("/"):
        if part == "" or part == ".":
            continue
        if part == "..":
            stack.pop()
        else:
            stack.append(part)
    return "/" + "/".join(stack)
''',
        '''def resolve_path(cwd, path):
    full = cwd + "/" + path
    stack = []
    for part in full.split("/"):
        if part in ("", "."):
            continue
        if part == "..":
            if stack:
                stack.pop()
        else:
            stack.append(part)
    return "/" + "/".join(stack)
''',
        '''def resolve_path(cwd, path):
    full = path if path.startswith("/") else cwd + "/" + path
    stack = []
    for part in full.split("/"):
        if part == "" or part.startswith("."):
            if part == ".." and stack:
                stack.pop()
            continue
        stack.append(part)
    return "/" + "/".join(stack)
''',
    ],
    guide=dict(
        prereqs="The navigation lesson: absolute versus relative paths, `.` and `..`. A Python list used as a stack.",
        intuition="Walking a path is literally walking: each name takes you one level down, `..` takes you one level back up, and `.` means stand still. A stack models 'where am I': push when you descend, pop when you climb. Whatever is on the stack at the end, joined by slashes, is where you ended up.",
        hints=[
            "Decide first whether to start from `cwd` or from the root, then glue the two strings with a slash — extra slashes are harmless because you will discard empty pieces.",
            "Split on `/`. Empty strings and `.` are skipped.",
            "For `..` pop only if the stack is non-empty; anything else (including odd names like `...` or `.hidden`) is an ordinary component to push.",
        ],
        brute_force="Repeatedly search the string for patterns such as `//`, `/./` and `/name/../` and rewrite them until nothing changes. Each pass is O(n) and you may need O(n) passes, so O(n²), with many edge cases at the ends of the string.",
        approach="""1. `full = path` if absolute, else `cwd + '/' + path`.
2. Iterate over `full.split('/')` with an empty stack.
3. Skip `''` and `.`; pop on `..` when possible; otherwise push.
4. Return `'/' + '/'.join(stack)` — an empty stack naturally yields `/`.

**Dry run, cwd `/var/log`, path `../../etc//ssh/./`:** pieces are `'' var log .. .. etc '' ssh . ''`. Stack: `[var]`, `[var, log]`, pop → `[var]`, pop → `[]`, `[etc]`, skip, `[etc, ssh]`, skip, skip. Result `/etc/ssh`.""",
        complexity="Time O(n) in the length of the combined string, space O(n) for the stack.",
        pitfalls="""* Popping an empty stack: `/..` is `/`, not an exception.
* Treating every dot-name specially. `...` and `.hidden` are normal names.
* Forgetting that an absolute `path` ignores `cwd` entirely.
* Returning an empty string instead of `/` when everything cancels out.""",
        follow_up="With symbolic links the answer depends on the disk: `a/link/..` goes to the parent of the link's *target*. That is the difference between `pwd -L` and `pwd -P`. Extend the function with a dictionary of links.",
    ),
),
]
