"""Linux CLI problems, set 4: head/tail, sed, join, comm and xargs."""

PROBLEMS = [
# ------------------------------------------------------------------ head / tail
dict(
    id="cli-head-tail",
    title="head and tail, Including tail -n +K",
    difficulty="Easy",
    pattern="Text Processing",
    entry="head_tail",
    description=r"""
`head` and `tail` each accept a line count with an optional sign that changes its meaning.

`head_tail(lines, tool, n)` where `tool` is `"head"` or `"tail"` and `n` is the text given to `-n`:

| Call | Meaning |
|---|---|
| `head -n K` | the first K lines |
| `head -n -K` | everything **except the last K** lines |
| `tail -n K` | the last K lines |
| `tail -n +K` | everything **starting at line K** (1-based); `+0` and `+1` both mean the whole input |

K is a non-negative integer. Asking for more lines than exist is not an error.

**Example 1:** `lines = ["a","b","c","d"], tool = "head", n = "2"` → `["a","b"]`

**Example 2:** same lines, `tool = "tail", n = "+2"` → `["b","c","d"]` (skip a one-line header)

**Example 3:** same lines, `tool = "head", n = "-1"` → `["a","b","c"]`
""",
    starter='''def head_tail(lines: List[str], tool: str, n: str) -> List[str]:
    pass
''',
    solution='''def head_tail(lines, tool, n):
    size = len(lines)
    if tool == "head":
        if n.startswith("-"):
            keep = max(0, size - int(n[1:]))
        else:
            keep = int(n)
        return lines[:keep]
    if n.startswith("+"):
        start = max(0, int(n[1:]) - 1)
        return lines[start:]
    k = int(n)
    return lines[max(0, size - k):]
''',
    tests=[
        [["a", "b", "c", "d"], "head", "2"],
        [["a", "b", "c", "d"], "tail", "+2"],
        [["a", "b", "c", "d"], "head", "-1"],
        [["a", "b", "c", "d"], "tail", "2"],
        [["a", "b", "c", "d"], "tail", "0"],
        [["a", "b", "c", "d"], "head", "0"],
        [["a", "b", "c", "d"], "head", "-0"],
        [["a", "b", "c", "d"], "tail", "+0"],
        [["a", "b", "c", "d"], "tail", "+1"],
        [["a", "b", "c", "d"], "tail", "+5"],
        [["a", "b", "c", "d"], "head", "99"],
        [["a", "b", "c", "d"], "tail", "99"],
        [["a", "b", "c", "d"], "head", "-99"],
        [[], "tail", "+3"],
        [["only"], "tail", "1"],
    ],
    examples=3,
    wrong_solutions=[
        '''def head_tail(lines, tool, n):
    if tool == "head":
        return lines[:int(n)]
    if n.startswith("+"):
        return lines[int(n[1:]) - 1:]
    return lines[-int(n):]
''',
        '''def head_tail(lines, tool, n):
    size = len(lines)
    if tool == "head":
        keep = max(0, size - int(n[1:])) if n.startswith("-") else int(n)
        return lines[:keep]
    if n.startswith("+"):
        return lines[int(n[1:]):]
    return lines[max(0, size - int(n)):]
''',
    ],
    guide=dict(
        prereqs="The redirection lesson (`head`, `tail`). Python slicing, including what negative and zero indices do.",
        intuition="All four forms are 'keep one contiguous block'. Either the block is anchored at the top and you need its length, or it is anchored at the bottom and you need where it starts. The signs just let you state that boundary from the other end: `head -n -K` gives the length as 'total minus K', and `tail -n +K` gives the start as an absolute line number.",
        hints=[
            "Translate every case into an explicit, non-negative slice boundary before slicing.",
            "`tail -n +K` starts at index `K - 1`; clamp at 0 so `+0` works.",
            "Never write `lines[-k:]` with a `k` that might be zero — `lines[-0:]` is the whole list.",
        ],
        brute_force="Loop with a counter and append lines one at a time while a condition holds. Fine and still O(n). For `tail -n K` on a true stream (unknown length) the standard trick is a ring buffer of the last K lines, e.g. `collections.deque(maxlen=K)`.",
        approach="""1. `head K` → `lines[:K]`.
2. `head -K` → `lines[:max(0, len - K)]`.
3. `tail +K` → `lines[max(0, K - 1):]`.
4. `tail K` → `lines[max(0, len - K):]`.

**Dry run, `tail -n +2` on `[a, b, c, d]`:** start index `2 - 1 = 1` → `[b, c, d]`. With `+5`, start index 4 → empty list.""",
        complexity="Time O(size of the output), space the same.",
        pitfalls="""* The `-0` traps: `lines[-0:]` and `lines[:-0]` do the opposite of what you want.
* Off-by-one on `+K`: it names the first line to *print*, not the number of lines to skip.
* `head -n -99` on four lines is empty, not an error and not a negative slice surprise.""",
        follow_up="Combine them to print exactly lines 20–30 of a file: `head -n 30 file | tail -n +20`. Then implement `tail -f` conceptually: poll the file size and print what was appended.",
    ),
),
# ------------------------------------------------------------------ sed s///
dict(
    id="cli-sed-substitute",
    title="A Mini sed: s/old/new/ with Addresses",
    difficulty="Medium",
    pattern="Text Processing",
    entry="sed_s",
    description=r"""
Implement the most used `sed` command — substitution — together with line addresses.

`sed_s(lines, script)` applies one script of the form

```
[address]s/old/new/[g]
```

to every line and returns the resulting lines.

* `old` is **literal text** (non-empty); `new` is literal replacement text (may be empty). Neither
  contains `/`.
* Without the trailing `g`, only the **first** occurrence on a line is replaced; with `g`, all
  non-overlapping occurrences are.
* `address` restricts which lines the command touches. Lines are numbered from 1.

| Address | Lines affected |
|---|---|
| *(none)* | every line |
| `N` | line N only |
| `N,M` | lines N through M inclusive (N ≤ M) |
| `N,$` | line N through the last line |
| `$` | the last line only |
| `/text/` | every line that contains `text` |

Lines outside the address are returned unchanged.

**Example 1:** `lines = ["a cat", "cat cat"], script = "s/cat/dog/"` → `["a dog", "dog cat"]`

**Example 2:** same lines, `script = "2s/cat/dog/g"` → `["a cat", "dog dog"]`

**Example 3:** `lines = ["x=1", "# x=1", "x=2"], script = "/#/s/x/y/"` → `["x=1", "# y=1", "x=2"]`
""",
    starter='''def sed_s(lines: List[str], script: str) -> List[str]:
    pass
''',
    solution=r'''import re

def sed_s(lines, script):
    total = len(lines)
    if script.startswith("/"):
        end = script.index("/", 1)
        needle = script[1:end]
        command = script[end + 1:]
        selected = lambda num, line: needle in line
    else:
        m = re.match(r"(\d+|\$)?(?:,(\d+|\$))?", script)
        first, second = m.group(1), m.group(2)
        command = script[m.end():]
        if first is None:
            selected = lambda num, line: True
        else:
            lo = total if first == "$" else int(first)
            if second is None:
                hi = lo
            else:
                hi = total if second == "$" else int(second)
            selected = lambda num, line: lo <= num <= hi
    _, old, new, flag = command.split("/")
    count = -1 if flag == "g" else 1
    out = []
    for num, line in enumerate(lines, 1):
        out.append(line.replace(old, new, count) if selected(num, line) else line)
    return out
''',
    tests=[
        [["a cat", "cat cat"], "s/cat/dog/"],
        [["a cat", "cat cat"], "2s/cat/dog/g"],
        [["x=1", "# x=1", "x=2"], "/#/s/x/y/"],
        [["aaa", "aaa", "aaa"], "s/a/b/g"],
        [["aaa", "aaa", "aaa", "aaa"], "2,3s/a/b/"],
        [["aaa", "aaa", "aaa"], "$s/a/b/g"],
        [["aaa", "aaa", "aaa"], "2,$s/a/b/"],
        [["hello world"], "s/o//g"],
        [["nothing here"], "s/zzz/y/g"],
        [[], "s/a/b/"],
        [["aaa", "aaa"], "9s/a/b/"],
        [["banana"], "s/a/aa/g"],
        [["one", "two"], "1,1s/o/0/g"],
        [["ERROR disk", "info ok", "ERROR net ERROR"], "/ERROR/s/ERROR/E/g"],
        [["path a.b.c"], "s/./-/g"],
        [["11 22", "11 22", "11 22"], "1,2s/1/x/"],
    ],
    examples=3,
    wrong_solutions=[
        r'''import re

def sed_s(lines, script):
    total = len(lines)
    if script.startswith("/"):
        end = script.index("/", 1)
        needle, command = script[1:end], script[end + 1:]
        sel = lambda n, l: needle in l
    else:
        m = re.match(r"(\d+|\$)?(?:,(\d+|\$))?", script)
        a, b = m.group(1), m.group(2)
        command = script[m.end():]
        if a is None:
            sel = lambda n, l: True
        else:
            lo = total if a == "$" else int(a)
            hi = lo if b is None else (total if b == "$" else int(b))
            sel = lambda n, l: lo <= n <= hi
    _, old, new, flag = command.split("/")
    return [l.replace(old, new) if sel(n, l) else l for n, l in enumerate(lines, 1)]
''',
        r'''def sed_s(lines, script):
    command = script[script.index("s/"):]
    _, old, new, flag = command.split("/")
    count = -1 if flag == "g" else 1
    return [l.replace(old, new, count) for l in lines]
''',
        r'''import re

def sed_s(lines, script):
    total = len(lines)
    if script.startswith("/"):
        end = script.index("/", 1)
        needle, command = script[1:end], script[end + 1:]
        sel = lambda n, l: needle in l
    else:
        m = re.match(r"(\d+|\$)?(?:,(\d+|\$))?", script)
        a, b = m.group(1), m.group(2)
        command = script[m.end():]
        if a is None:
            sel = lambda n, l: True
        else:
            lo = total if a == "$" else int(a)
            hi = lo if b is None else (total if b == "$" else int(b))
            sel = lambda n, l: lo <= n <= hi
    _, old, new, flag = command.split("/")
    count = 0 if flag == "g" else 1
    return [re.sub(old, new, l, count=count) if sel(n, l) else l for n, l in enumerate(lines, 1)]
''',
    ],
    guide=dict(
        prereqs="The text-processing lesson covering `sed` (addresses and the `s` command). String `replace` with a count.",
        intuition="`sed` is a loop you do not have to write: *for each line, if the address selects it, run the command; then print the line*. So the script splits naturally into two independent pieces — a predicate on (line number, line text) and an edit. Parse them separately and the main loop is three lines long.",
        hints=[
            "Separate the script into the address part (everything before the `s`) and the command. A script that begins with `/` has a text address.",
            "Turn the address into a function `selected(number, line)`. `$` needs the total number of lines.",
            "`str.replace(old, new, 1)` handles the non-global case; omit the count (or pass -1) for `g`.",
        ],
        brute_force="Special-case each address form inside the loop with string tests on every iteration. It works but re-parses the script n times and tangles selection with editing; building the predicate once is cleaner and faster.",
        approach="""1. If the script starts with `/`, read the text up to the next `/` → predicate `needle in line`.
2. Otherwise match an optional `N` or `$`, optionally followed by `,M` or `,$`. No address → always true. One number → that line. Two → inclusive range, with `$` standing for `len(lines)`.
3. Split the remaining `s/old/new/flag` on `/`.
4. For each numbered line, replace (once or globally) when selected.

**Dry run, `2,$s/a/b/` on three lines of `aaa`:** `lo = 2`, `hi = 3`. Line 1 untouched; lines 2 and 3 get one replacement each → `aaa`, `baa`, `baa`.""",
        complexity="Time O(total characters), space O(output).",
        pitfalls="""* Replacing every occurrence when `g` is absent — the default is first match only.
* Treating `old` as a regular expression in this problem: `s/./-/g` must replace literal dots, not every character.
* `$` is a line address here, not an end-of-line anchor.
* An address past the end of the input simply selects nothing.""",
        follow_up="Real `sed` uses regular expressions for both `old` and `/address/`, supports `&` and `\\1` in the replacement, any delimiter (`s|a|b|`), and commands such as `d` and `p`. Add `d` (delete selected lines).",
    ),
),
# ------------------------------------------------------------------ join
dict(
    id="cli-join-on-key",
    title="join Two Sorted Files on a Key",
    difficulty="Medium",
    pattern="Text Processing",
    entry="join_lines",
    description=r"""
`join` is the command-line cousin of a SQL inner join. Both inputs are text files whose lines consist
of space-separated fields; the **first field is the key**, and both files are already sorted by it.

`join_lines(left, right)` returns one output line for every pair of a left line and a right line
with the same key:

```
key  <remaining fields of the left line>  <remaining fields of the right line>
```

all joined by single spaces. Lines whose key has no partner are dropped. If a key occurs several
times on either side, every combination is produced (left lines in order; for each, the right lines
in order).

**Example 1:**

```
left  = ["1 apple", "2 banana", "4 cherry"]
right = ["1 red", "2 yellow", "3 green"]
→ ["1 apple red", "2 banana yellow"]
```

**Example 2:** `left = ["k a", "k b"], right = ["k x", "k y"]` → `["k a x", "k a y", "k b x", "k b y"]`
""",
    starter='''def join_lines(left: List[str], right: List[str]) -> List[str]:
    pass
''',
    solution='''def join_lines(left, right):
    out = []
    i = j = 0
    while i < len(left) and j < len(right):
        lf, rf = left[i].split(" "), right[j].split(" ")
        if lf[0] < rf[0]:
            i += 1
        elif lf[0] > rf[0]:
            j += 1
        else:
            key = lf[0]
            i_end = i
            while i_end < len(left) and left[i_end].split(" ")[0] == key:
                i_end += 1
            j_end = j
            while j_end < len(right) and right[j_end].split(" ")[0] == key:
                j_end += 1
            for a in range(i, i_end):
                for b in range(j, j_end):
                    fields = [key] + left[a].split(" ")[1:] + right[b].split(" ")[1:]
                    out.append(" ".join(fields))
            i, j = i_end, j_end
    return out
''',
    tests=[
        [["1 apple", "2 banana", "4 cherry"], ["1 red", "2 yellow", "3 green"]],
        [["k a", "k b"], ["k x", "k y"]],
        [[], ["1 x"]],
        [["1 x"], []],
        [["a 1", "b 2"], ["c 3", "d 4"]],
        [["a 1 2 3", "b 4 5 6"], ["a x y", "b z"]],
        [["a", "b", "c"], ["b", "c", "d"]],
        [["a 1", "a 2", "b 3"], ["a x", "b y", "b z"]],
        [["ana 30", "bo 25", "cy 41", "di 19"], ["ana lisbon", "cy oslo", "di lima", "ed rome"]],
        [["u1 login", "u1 logout", "u2 login"], ["u2 admin"]],
        [["%03d v%d" % (i, i) for i in range(0, 300, 2)], ["%03d w%d" % (i, i) for i in range(0, 300, 3)]],
        [["x 1"], ["x 2", "x 3", "x 4"]],
    ],
    examples=2,
    wrong_solutions=[
        '''def join_lines(left, right):
    table = {}
    for line in right:
        f = line.split(" ")
        table[f[0]] = f[1:]
    out = []
    for line in left:
        f = line.split(" ")
        if f[0] in table:
            out.append(" ".join(f + table[f[0]]))
    return out
''',
        '''def join_lines(left, right):
    out = []
    for a, b in zip(left, right):
        fa, fb = a.split(" "), b.split(" ")
        if fa[0] == fb[0]:
            out.append(" ".join(fa + fb[1:]))
    return out
''',
    ],
    guide=dict(
        prereqs="The text-processing lesson (`join`), and why it insists on sorted input. The two-pointer merge from merge sort.",
        intuition="Because both files are sorted by key, you never need to look backwards. Put a finger on the top line of each file. If the keys differ, the smaller one can never find a partner further down the other file, so advance that finger. If they agree, collect the whole run of that key on both sides, emit every pairing, and jump both fingers past the runs. This is the *sort-merge join* that databases use.",
        hints=[
            "Use two indices and compare `left[i]`'s key with `right[j]`'s key.",
            "On equality, find where the run of equal keys ends on each side.",
            "Emit `key + left rest + right rest` for the cross product of the two runs, then set both indices to the run ends.",
        ],
        brute_force="Nested loops: for each left line scan every right line and compare keys — O(L × R). It needs no sorting and gives the right answer, but it is quadratic; a hash map from key to the list of right lines brings it to O(L + R + output) at the cost of holding one whole file in memory.",
        approach="""1. `i = j = 0`.
2. While both are in range: compare keys. Smaller side advances.
3. Equal keys: compute `i_end` and `j_end`, output the cross product, set `i, j = i_end, j_end`.

**Dry run, example 1:** keys `1`=`1` → `1 apple red`. `2`=`2` → `2 banana yellow`. Now `4` vs `3`: right is smaller, advance right → exhausted. Done; `4 cherry` and `3 green` were unpaired.""",
        complexity="Time O(L + R + size of output), space O(1) beyond the output — the reason the real tool can join files far larger than memory.",
        pitfalls="""* Storing one value per key loses duplicates.
* Pairing line i with line i (`zip`) only works when both files have identical key sets.
* Comparing keys numerically when the files were sorted as text (or vice versa); `join` uses the same collation as plain `sort`, so `10` sorts before `9`.""",
        follow_up="Add `-a 1` (also print unpairable left lines — a left outer join) and `-1 N -2 M` to choose the key field on each side.",
    ),
),
# ------------------------------------------------------------------ comm
dict(
    id="cli-comm-columns",
    title="comm: Three-Column Comparison",
    difficulty="Medium",
    pattern="Text Processing",
    entry="comm",
    description=r"""
`comm` compares two **sorted** files line by line and prints three columns: lines only in the first
file, lines only in the second, and lines in both. Columns are made by indentation with tabs.

`comm(a, b)` returns the output lines, in merged sorted order:

* a line found only in `a` → the line as-is;
* a line found only in `b` → one tab (`\t`) followed by the line;
* a line found in both → two tabs followed by the line.

Duplicates are matched one-for-one: if `x` occurs three times in `a` and once in `b`, one `x` is
common and two are unique to `a`.

**Example:**

```
a = ["apple", "cherry", "fig"]
b = ["banana", "cherry", "fig", "grape"]
→ ["apple", "\tbanana", "\t\tcherry", "\t\tfig", "\tgrape"]
```
""",
    starter='''def comm(a: List[str], b: List[str]) -> List[str]:
    pass
''',
    solution='''def comm(a, b):
    out = []
    i = j = 0
    while i < len(a) and j < len(b):
        if a[i] == b[j]:
            out.append("\\t\\t" + a[i])
            i += 1
            j += 1
        elif a[i] < b[j]:
            out.append(a[i])
            i += 1
        else:
            out.append("\\t" + b[j])
            j += 1
    out.extend(a[i:])
    out.extend("\\t" + line for line in b[j:])
    return out
''',
    tests=[
        [["apple", "cherry", "fig"], ["banana", "cherry", "fig", "grape"]],
        [[], []],
        [["a", "b"], []],
        [[], ["a", "b"]],
        [["a", "b", "c"], ["a", "b", "c"]],
        [["a", "c", "e"], ["b", "d", "f"]],
        [["x", "x", "x"], ["x"]],
        [["x"], ["x", "x", "y"]],
        [["a", "a", "b", "b"], ["a", "b", "b", "b"]],
        [["m"], ["a", "z"]],
        [["host%02d" % i for i in range(0, 60, 2)], ["host%02d" % i for i in range(0, 60, 3)]],
        [["alpha", "beta"], ["beta", "gamma"]],
    ],
    examples=1,
    wrong_solutions=[
        '''def comm(a, b):
    sa, sb = set(a), set(b)
    out = []
    for line in sorted(sa | sb):
        if line in sa and line in sb:
            out.append("\\t\\t" + line)
        elif line in sa:
            out.append(line)
        else:
            out.append("\\t" + line)
    return out
''',
        '''def comm(a, b):
    out = []
    i = j = 0
    while i < len(a) and j < len(b):
        if a[i] == b[j]:
            out.append("\\t\\t" + a[i])
            i += 1
            j += 1
        elif a[i] < b[j]:
            out.append(a[i])
            i += 1
        else:
            out.append("\\t" + b[j])
            j += 1
    return out
''',
    ],
    guide=dict(
        prereqs="The text-processing lesson (`comm`, `diff`). The merge step of merge sort.",
        intuition="Two sorted lists can be compared with a single simultaneous pass. Look at the current line of each: if they are equal, it is common; otherwise the smaller one cannot possibly appear later in the other list (everything remaining there is larger), so it is unique to its file. Report it, advance, repeat. When one list runs out, whatever is left in the other is unique.",
        hints=[
            "Two indices, one loop, three cases: equal, `a` smaller, `b` smaller.",
            "Only on equality do both indices advance — that gives the one-for-one treatment of duplicates.",
            "Do not forget the leftovers after the loop ends.",
        ],
        brute_force="For each line of `a` search `b` linearly (and vice versa), marking matches as used so duplicates pair off one-for-one, then sort the combined output. O(n × m) and fiddly; it ignores the gift of sorted input.",
        approach="""1. `i = j = 0`; while both in range, compare `a[i]` and `b[j]`.
2. Equal → `\\t\\t` + line, advance both. `a[i]` smaller → plain line, advance `i`. Otherwise → `\\t` + `b[j]`, advance `j`.
3. Append the rest of `a` plain and the rest of `b` with one tab.

**Dry run, `a = [x, x, x]`, `b = [x]`:** first comparison equal → `\\t\\tx`, both advance; `b` is exhausted; leftovers of `a` → `x`, `x`.""",
        complexity="Time O(n + m), space O(1) beyond the output.",
        pitfalls="""* Using sets destroys duplicate counts.
* Dropping the tail of the longer list.
* Feeding unsorted input: the algorithm silently produces nonsense, which is why GNU `comm` warns about it.""",
        follow_up="Add the suppression flags: `comm -12` prints only the common lines (set intersection), `comm -23` only those unique to the first file (set difference). Note that suppressing a column also removes its tab.",
    ),
),
# ------------------------------------------------------------------ xargs
dict(
    id="cli-xargs-batches",
    title="xargs-Style Batching",
    difficulty="Medium",
    pattern="Pipelines",
    entry="xargs_batches",
    description=r"""
`find . -name '*.tmp' | xargs rm` works even for a million files because `xargs` splits the incoming
items into several command lines, each small enough for the operating system to accept.

`xargs_batches(command, items, max_args, max_chars)` returns the command lines that would be run.

Build lines greedily. A line starts as `command`; items are appended, each preceded by one space,
for as long as **both** limits hold:

* at most `max_args` items per line (like `xargs -n`);
* the finished line is at most `max_chars` characters long (like `xargs -s`).

When the next item does not fit, finish the current line and start a new one. An item that does not
fit even on a fresh line still gets a line of its own. With no items, nothing is run (return `[]`).

**Example 1:** `command = "rm", items = ["a", "b", "c", "d", "e"], max_args = 2, max_chars = 100`
→ `["rm a b", "rm c d", "rm e"]`

**Example 2:** `command = "echo", items = ["aaaa", "bbbb", "cc"], max_args = 10, max_chars = 14`
→ `["echo aaaa bbbb", "echo cc"]`
""",
    starter='''def xargs_batches(command: str, items: List[str], max_args: int, max_chars: int) -> List[str]:
    pass
''',
    solution='''def xargs_batches(command, items, max_args, max_chars):
    out = []
    line, count = command, 0
    for item in items:
        fits = count < max_args and len(line) + 1 + len(item) <= max_chars
        if count > 0 and not fits:
            out.append(line)
            line, count = command, 0
        line += " " + item
        count += 1
    if count:
        out.append(line)
    return out
''',
    tests=[
        ["rm", ["a", "b", "c", "d", "e"], 2, 100],
        ["echo", ["aaaa", "bbbb", "cc"], 10, 14],
        ["rm", [], 5, 100],
        ["rm", ["one"], 5, 100],
        ["gzip -9", ["a.log", "b.log", "c.log"], 1, 100],
        ["echo", ["x"] * 7, 3, 100],
        ["echo", ["abcdefghijklmnop", "q", "r"], 5, 10],
        ["echo", ["a", "abcdefghijklmnop", "b"], 5, 10],
        ["cp -t /backup", ["f1", "f2", "f3", "f4"], 4, 100],
        ["cp -t /backup", ["f1", "f2", "f3", "f4"], 3, 19],
        ["x", ["12345", "12345"], 9, 13],
        ["x", ["12345", "12345"], 9, 12],
        ["wc -l", ["file%d.txt" % i for i in range(25)], 100, 60],
    ],
    examples=2,
    wrong_solutions=[
        '''def xargs_batches(command, items, max_args, max_chars):
    out = []
    for i in range(0, len(items), max_args):
        out.append(command + " " + " ".join(items[i:i + max_args]))
    return out
''',
        '''def xargs_batches(command, items, max_args, max_chars):
    out = []
    line, count = command, 0
    for item in items:
        if count >= max_args or len(line) + 1 + len(item) > max_chars:
            out.append(line)
            line, count = command, 0
        line += " " + item
        count += 1
    out.append(line)
    return out
''',
        '''def xargs_batches(command, items, max_args, max_chars):
    out = []
    line, count = command, 0
    for item in items:
        fits = count < max_args and len(line) + len(item) <= max_chars
        if count > 0 and not fits:
            out.append(line)
            line, count = command, 0
        line += " " + item
        count += 1
    if count:
        out.append(line)
    return out
''',
    ],
    guide=dict(
        prereqs="The searching-for-files lesson (`find … | xargs`). Greedy packing.",
        intuition="Think of loading boxes onto trucks in the order they arrive: keep loading the current truck until the next box would break a limit (too many boxes, or too heavy), then send the truck and start another. `xargs` does exactly this with arguments, where the 'weight' limit is the kernel's maximum command-line size. Greedy is optimal here because order must be preserved and items cannot be split.",
        hints=[
            "Track the current line string and how many items it holds.",
            "Before adding an item, test both limits; the length test must include the separating space.",
            "Only flush a line that already has at least one item — otherwise an oversized item would produce a bare command.",
        ],
        brute_force="Ignore the character limit and chunk by count with `range(0, len(items), max_args)`. That is `xargs -n` alone and is correct only while lines stay short; with long path names the very failure `xargs` exists to prevent ('Argument list too long') comes back.",
        approach="""1. `line = command`, `count = 0`.
2. For each item compute `fits = count < max_args and len(line) + 1 + len(item) <= max_chars`.
3. If the line is non-empty of items and the item does not fit → emit the line and reset.
4. Append the item; increment the count.
5. After the loop emit the last line if it has items.

**Dry run, example 2 (limit 14):** `echo` + ` aaaa` → 9 chars. ` bbbb` → 14, allowed. ` cc` would make 17 → flush `echo aaaa bbbb`, start `echo cc`. End → flush.""",
        complexity="Time O(total length of the items), space O(output).",
        pitfalls="""* Emitting the bare command when there are no items (GNU `xargs` does run it once unless `-r` is given — a real-world gotcha — but here the answer is `[]`).
* Off-by-one in the length check: the limit is inclusive and the space counts.
* Flushing an empty line when an item is longer than the limit.""",
        follow_up="Real file names can contain spaces and newlines; that is why `find -print0 | xargs -0` exists. Add `-I {}` mode, where each item replaces a placeholder and every command line gets exactly one item.",
    ),
),
]
