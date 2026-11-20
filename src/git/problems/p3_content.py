"""Git track problems, part 3: diffs, patches, merges and history editing."""

LCS_HELPER = '''
def _table(a, b):
    n, m = len(a), len(b)
    L = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n - 1, -1, -1):
        for j in range(m - 1, -1, -1):
            if a[i] == b[j]:
                L[i][j] = L[i + 1][j + 1] + 1
            else:
                L[i][j] = max(L[i + 1][j], L[i][j + 1])
    return L
'''

CONFIG = ["[server]", "host = localhost", "port = 8080", "", "[cache]", "ttl = 60", "size = 100", "", "[log]", "level = info"]

PROBLEMS = [
dict(
    id="git-lcs-diff",
    title="Line diff with the longest common subsequence",
    difficulty="Medium",
    pattern="Dynamic programming",
    entry="line_diff",
    description=r"""
`git diff` shows how to turn the old version of a file into the new one with the fewest removed and added
lines. The lines that stay are a **longest common subsequence (LCS)** of the two versions.

Write `line_diff(a, b)` where `a` (old) and `b` (new) are lists of strings (lines without newlines).
Return a list of strings, each a line prefixed with two characters:

- `"  "` (two spaces) for a line kept from both versions,
- `"- "` for a line present only in `a`,
- `"+ "` for a line present only in `b`.

Several minimal diffs can exist, so use this exact rule. Let `L[i][j]` be the LCS length of `a[i:]` and
`b[j:]`. Walk with `i = j = 0`:

1. if `a[i] == b[j]`: emit a kept line and advance both;
2. else if `L[i+1][j] >= L[i][j+1]`: emit `- a[i]` and advance `i` (**deletions win ties**);
3. else emit `+ b[j]` and advance `j`.

When one list runs out, emit the remainder of `a` as deletions, then the remainder of `b` as additions.

**Example:** `line_diff(["a", "b", "c"], ["a", "x", "c"])` → `["  a", "- b", "+ x", "  c"]`
""",
    starter='''def line_diff(a, b):
    pass
''',
    solution=LCS_HELPER + '''
def line_diff(a, b):
    L = _table(a, b)
    i = j = 0
    out = []
    while i < len(a) and j < len(b):
        if a[i] == b[j]:
            out.append("  " + a[i])
            i += 1
            j += 1
        elif L[i + 1][j] >= L[i][j + 1]:
            out.append("- " + a[i])
            i += 1
        else:
            out.append("+ " + b[j])
            j += 1
    out.extend("- " + x for x in a[i:])
    out.extend("+ " + x for x in b[j:])
    return out
''',
    tests=[
        [["a", "b", "c"], ["a", "x", "c"]],
        [["a", "b", "c"], ["a", "b", "c"]],
        [[], []],
        [[], ["new", "file"]],
        [["gone", "file"], []],
        [["a", "b"], ["b", "a"]],
        [["a", "b", "c", "d"], ["b", "c", "d", "e"]],
        [["x", "a", "x", "b"], ["a", "x", "b", "x"]],
        [CONFIG, CONFIG[:2] + ["port = 9090"] + CONFIG[3:6] + CONFIG[7:] + ["file = app.log"]],
        [["def f():", "    return 1", "", "def g():", "    return 2"], ["def g():", "    return 2", "", "def f():", "    return 1"]],
        [["same"] * 5, ["same"] * 3],
        [["l%d" % i for i in range(120)], ["l%d" % i for i in range(120) if i % 7] + ["tail"]],
        [["a", "", "b"], ["a", " ", "b"]],
    ],
    examples=2,
    wrong_solutions=[
        '''def line_diff(a, b):
    out = []
    i = j = 0
    while i < len(a) and j < len(b):
        if a[i] == b[j]:
            out.append("  " + a[i]); i += 1; j += 1
        else:
            out.append("- " + a[i]); out.append("+ " + b[j]); i += 1; j += 1
    out.extend("- " + x for x in a[i:])
    out.extend("+ " + x for x in b[j:])
    return out
''',
        LCS_HELPER + '''
def line_diff(a, b):
    L = _table(a, b)
    i = j = 0
    out = []
    while i < len(a) and j < len(b):
        if a[i] == b[j]:
            out.append("  " + a[i]); i += 1; j += 1
        elif L[i + 1][j] > L[i][j + 1]:
            out.append("- " + a[i]); i += 1
        else:
            out.append("+ " + b[j]); j += 1
    out.extend("- " + x for x in a[i:])
    out.extend("+ " + x for x in b[j:])
    return out
''',
    ],
    guide=dict(
        prereqs="The lessons on viewing staged and unstaged changes. Two-dimensional dynamic programming (LCS).",
        intuition="A diff is the complement of what stays the same. If you find the largest set of lines that appear in both files in the same order, everything else in the old file must be deleted and everything else in the new file must be added, and no smaller edit script exists.",
        hints=[
            "Fill a table `L[i][j]` = LCS length of the suffixes `a[i:]` and `b[j:]`, from the bottom-right corner upwards.",
            "Then walk from the top-left. Equal lines are always safe to keep. Otherwise look at the two neighbouring cells to see which move keeps the LCS reachable.",
            "The tie rule matters for the expected output: on equal values delete first. That is what makes a changed line show as `-` then `+`.",
        ],
        brute_force="Walk both files in lock-step and call any mismatch a replace (first wrong solution). One inserted line at the top then makes every following line look changed. Enumerating all common subsequences is exponential.",
        approach="1. Build the suffix LCS table in O(nm).\n2. Walk forward applying the three rules.\n3. Flush the leftovers.\n\n**Dry run** `a = [a, b, c]`, `b = [a, x, c]`: (0,0) equal, keep `a`. (1,1): `b` vs `x` differ; `L[2][1]` = LCS([c],[x,c]) = 1 and `L[1][2]` = LCS([b,c],[c]) = 1, tie, so delete `b`. (2,1): `c` vs `x`; `L[3][1] = 0 < L[2][2] = 1`, so add `x`. (2,2) equal, keep `c`.",
        complexity="Time and space O(n * m) for files of n and m lines. Git's default (Myers) algorithm is O((n + m) * D) for D differences, which is much faster when files are similar.",
        pitfalls="Building the table for prefixes and then walking forward (the directions must agree). Using `>` instead of `>=`, which flips the order of `-`/`+` pairs. Forgetting to flush the tail of both lists.",
        follow_up="Group the output into hunks with three lines of context to get the unified format. Try `git diff --patience` or `--histogram` on moved code to see how different LCS strategies change readability.",
    ),
),
dict(
    id="git-apply-hunk",
    title="Apply a unified-diff hunk",
    difficulty="Medium",
    pattern="Parsing / simulation",
    entry="apply_hunk",
    description=r"""
A patch is a list of **hunks**. Each hunk starts with a header

```
@@ -<old_start>[,<old_count>] +<new_start>[,<new_count>] @@
```

followed by body lines whose first character is a space (context, present in both versions), `-`
(only in the old version) or `+` (only in the new version). A missing count means 1.

Write `apply_hunk(lines, hunk)`: `lines` is the old file as a list of strings; `hunk` is a list of strings,
header first. Return the new file as a list, or `None` if the hunk does not apply.

Rules:

- The **old side** of the hunk is its context and `-` lines in order; the **new side** is its context and `+` lines.
- The hunk is malformed (`None`) if it is empty, the header does not match the shape above, a body line starts
  with any other character (or is empty), or the header counts differ from the actual sizes of the old/new sides.
- The old side must equal `lines[old_start-1 : old_start-1+old_count]` exactly (1-based start, no fuzzy
  matching). Special case: when `old_count` is 0 the hunk only inserts, and the new lines go **after** line
  `old_start` (so `old_start = 0` inserts at the very top). The position must lie inside the file.
- `new_start` is informational; do not validate it.

**Example:**

```
lines = ["red", "green", "blue"]
hunk  = ["@@ -1,3 +1,3 @@", " red", "-green", "+lime", " blue"]
```

→ `["red", "lime", "blue"]`
""",
    starter='''def apply_hunk(lines, hunk):
    pass
''',
    solution='''import re

def apply_hunk(lines, hunk):
    if not hunk:
        return None
    m = re.match(r"@@ -(\\d+)(?:,(\\d+))? \\+(\\d+)(?:,(\\d+))? @@", hunk[0])
    if not m:
        return None
    start = int(m.group(1))
    old_n = int(m.group(2)) if m.group(2) is not None else 1
    new_n = int(m.group(4)) if m.group(4) is not None else 1
    old, new = [], []
    for row in hunk[1:]:
        tag = row[:1]
        if tag == " ":
            old.append(row[1:])
            new.append(row[1:])
        elif tag == "-":
            old.append(row[1:])
        elif tag == "+":
            new.append(row[1:])
        else:
            return None
    if len(old) != old_n or len(new) != new_n:
        return None
    pos = start if old_n == 0 else start - 1
    if pos < 0 or pos + old_n > len(lines):
        return None
    if lines[pos:pos + old_n] != old:
        return None
    return lines[:pos] + new + lines[pos + old_n:]
''',
    tests=[
        [["red", "green", "blue"], ["@@ -1,3 +1,3 @@", " red", "-green", "+lime", " blue"]],
        [["red", "green", "blue"], ["@@ -2 +2 @@", "-green", "+lime"]],
        [["red", "green", "blue"], ["@@ -2,1 +2,0 @@", "-green"]],
        [["red", "green", "blue"], ["@@ -0,0 +1,2 @@", "+top", "+second"]],
        [["red", "green", "blue"], ["@@ -3,0 +4 @@", "+tail"]],
        [["red", "green", "blue"], ["@@ -4,0 +5 @@", "+too far"]],
        [["red", "green", "blue"], ["@@ -1,3 +1,3 @@", " red", "-GREEN", "+lime", " blue"]],
        [["red", "green", "blue"], ["@@ -1,2 +1,3 @@", " red", "-green", "+lime", " blue"]],
        [["red", "green", "blue"], ["@@ -2,3 +2,2 @@", " green", "-blue", "-ghost"]],
        [["red", "green", "blue"], []],
        [["red", "green", "blue"], ["-1,3 +1,3", " red"]],
        [["red", "green", "blue"], ["@@ -1,1 +1,1 @@", "red"]],
        [[], ["@@ -0,0 +1 @@", "+first line"]],
        [CONFIG, ["@@ -2,4 +2,5 @@ [server]", " host = localhost", "-port = 8080", "+port = 9090", "+tls = on", " ", " [cache]"]],
        [["a", "  indented", "b"], ["@@ -1,3 +1,2 @@", " a", "-  indented", " b"]],
        [["x", "x", "x", "x"], ["@@ -3,2 +3,2 @@", " x", "-x", "+y"]],
    ],
    examples=2,
    wrong_solutions=[
        '''import re

def apply_hunk(lines, hunk):
    if not hunk:
        return None
    m = re.match(r"@@ -(\\d+)(?:,(\\d+))? \\+(\\d+)(?:,(\\d+))? @@", hunk[0])
    if not m:
        return None
    pos = int(m.group(1)) - 1
    out = lines[:pos]
    i = pos
    for row in hunk[1:]:
        if row[:1] == " ":
            out.append(row[1:]); i += 1
        elif row[:1] == "-":
            i += 1
        elif row[:1] == "+":
            out.append(row[1:])
        else:
            return None
    return out + lines[i:]
''',
    ],
    guide=dict(
        prereqs="Reading unified diffs (the lesson on recording changes) and the patch-based workflow in the distributed lessons.",
        intuition="A hunk carries both versions of one region of the file interleaved: read the context plus the minus lines and you have the 'before' text; read the context plus the plus lines and you have the 'after' text. Applying it is a guarded find-and-replace: confirm the 'before' text really sits at the stated position, then splice in the 'after' text.",
        hints=[
            "Build two lists from the body, `old` and `new`; context lines go into both.",
            "Slice the file at the stated position and compare it with `old` as whole lists.",
            "A pure insertion has no old lines to anchor it, so the header's start means 'after this line' instead of 'at this line'.",
        ],
        brute_force="Ignore the stated position and search the whole file for the old side. That is how `patch` applies hunks with an offset, but it can hit the wrong copy when a file has repeated blocks, and the task explicitly asks for exact placement.",
        approach="1. Parse the header with a regular expression; default counts to 1.\n2. Split the body into old and new sides, rejecting unknown prefixes.\n3. Check the counts.\n4. Compute the zero-based position (`start - 1`, or `start` for an insertion), bounds-check, compare.\n5. Return `lines[:pos] + new + lines[pos + old_n:]`.\n\n**Dry run** of the example: header gives start 1, counts 3 and 3. Old side `[red, green, blue]`, new side `[red, lime, blue]`. Position 0; the file slice `[0:3]` equals the old side; result is the new side.",
        complexity="Time O(len(lines) + len(hunk)) because of the list splice; space the same.",
        pitfalls="Stripping lines (a context line may consist of spaces, and removed lines may be indented). Treating an empty body line as context. Off-by-one for insert-only hunks. Trusting the header counts without checking them.",
        follow_up="Apply several hunks to one file: process them from the bottom up, or keep a running offset, so earlier splices do not shift later positions. `git apply --check` performs this validation for whole patches, and `git apply -3` falls back to a three-way merge.",
    ),
),
dict(
    id="git-three-way-merge",
    title="Three-way merge of line lists",
    difficulty="Hard",
    pattern="Dynamic programming / merging",
    entry="merge3",
    description=r"""
Merging combines two edited versions of a file using their common ancestor. Implement a line-based
three-way merge: `merge3(base, ours, theirs)` returns `[merged_lines, conflict_count]`.

**Step 1: alignment.** Align `base` with `ours`, and `base` with `theirs`, using the longest common
subsequence found by this deterministic walk (the same rule as the *Line diff* problem): with
`L[i][j]` the LCS length of the suffixes, starting at `i = j = 0`: if the lines are equal, record the pair
`(i, j)` as matched and advance both; else if `L[i+1][j] >= L[i][j+1]` advance `i`; else advance `j`.

**Step 2: anchors.** A base line is an *anchor* if it was matched in **both** alignments. Anchors are
unchanged on both sides and cut the three files into corresponding chunks: the lines before the first
anchor, between consecutive anchors, and after the last anchor (chunks may be empty).

**Step 3: resolve each chunk** with base part `B`, our part `O`, their part `T`:

- `O == T` → output `O` (both sides agree, or neither changed);
- `O == B` → output `T` (only they changed);
- `T == B` → output `O` (only we changed);
- otherwise it is a **conflict**: output `<<<<<<< ours`, the lines of `O`, `=======`, the lines of `T`,
  `>>>>>>> theirs`, and add 1 to the conflict count.

After each chunk output the anchor line itself.

**Example:** `merge3(["a", "b", "c"], ["a", "B", "c"], ["a", "b", "c", "d"])` → `[["a", "B", "c", "d"], 0]`

**Example:** `merge3(["x"], ["ours"], ["theirs"])` →
`[["<<<<<<< ours", "ours", "=======", "theirs", ">>>>>>> theirs"], 1]`
""",
    starter='''def merge3(base, ours, theirs):
    pass
''',
    solution=LCS_HELPER + '''
def _pairs(a, b):
    L = _table(a, b)
    i = j = 0
    out = {}
    while i < len(a) and j < len(b):
        if a[i] == b[j]:
            out[i] = j
            i += 1
            j += 1
        elif L[i + 1][j] >= L[i][j + 1]:
            i += 1
        else:
            j += 1
    return out

def merge3(base, ours, theirs):
    mo = _pairs(base, ours)
    mt = _pairs(base, theirs)
    out = []
    conflicts = 0
    pb = po = pt = 0
    anchors = [i for i in range(len(base)) if i in mo and i in mt]
    anchors.append(None)
    for i in anchors:
        if i is None:
            B, O, T = base[pb:], ours[po:], theirs[pt:]
        else:
            B, O, T = base[pb:i], ours[po:mo[i]], theirs[pt:mt[i]]
        if O == T:
            out.extend(O)
        elif O == B:
            out.extend(T)
        elif T == B:
            out.extend(O)
        else:
            conflicts += 1
            out.append("<<<<<<< ours")
            out.extend(O)
            out.append("=======")
            out.extend(T)
            out.append(">>>>>>> theirs")
        if i is not None:
            out.append(base[i])
            pb, po, pt = i + 1, mo[i] + 1, mt[i] + 1
    return [out, conflicts]
''',
    tests=[
        [["a", "b", "c"], ["a", "B", "c"], ["a", "b", "c", "d"]],
        [["x"], ["ours"], ["theirs"]],
        [["a", "b", "c"], ["a", "b", "c"], ["a", "b", "c"]],
        [[], [], []],
        [[], ["new"], ["new"]],
        [[], ["mine"], []],
        [[], ["mine"], ["yours"]],
        [["a", "b", "c"], ["a", "c"], ["a", "b", "c"]],
        [["a", "b", "c"], ["a", "c"], ["a", "B2", "c"]],
        [["a", "b", "c"], ["a", "X", "c"], ["a", "X", "c"]],
        [["a", "b", "c", "d", "e"], ["a", "b1", "c", "d", "e"], ["a", "b", "c", "d1", "e"]],
        [["a", "b", "c", "d", "e"], ["a", "b1", "c", "d", "e"], ["a", "b2", "c", "d2", "e"]],
        [["a", "b", "c", "d", "e"], ["a", "b1", "c", "d1", "e"], ["a", "b2", "c", "d2", "e"]],
        [CONFIG, CONFIG[:2] + ["port = 9090"] + CONFIG[3:], CONFIG[:6] + ["size = 500"] + CONFIG[7:] + ["file = app.log"]],
        [["h", "body", "f"], ["top", "h", "body", "f"], ["h", "body", "f", "bottom"]],
        [["a", "b"], ["b", "a"], ["a", "b"]],
        [["k", "l", "m"], [], ["k", "l", "m", "n"]],
    ],
    examples=2,
    wrong_solutions=[
        '''def merge3(base, ours, theirs):
    if ours == theirs or theirs == base:
        return [ours, 0]
    if ours == base:
        return [theirs, 0]
    return [["<<<<<<< ours"] + ours + ["======="] + theirs + [">>>>>>> theirs"], 1]
''',
        '''def merge3(base, ours, theirs):
    out, conflicts = [], 0
    n = max(len(base), len(ours), len(theirs))
    g = lambda xs, i: xs[i] if i < len(xs) else None
    for i in range(n):
        b, o, t = g(base, i), g(ours, i), g(theirs, i)
        if o == t or t == b:
            pick = o
        elif o == b:
            pick = t
        else:
            conflicts += 1
            out += ["<<<<<<< ours", o, "=======", t, ">>>>>>> theirs"]
            continue
        if pick is not None:
            out.append(pick)
    return [out, conflicts]
''',
    ],
    guide=dict(
        prereqs="Problem *Line diff with the longest common subsequence*; the lessons on merging and on advanced merging.",
        intuition="The base tells you who changed what. Wherever a region is identical to the base on one side, the other side's version of that region is the intended result. Only where *both* sides differ from the base, and from each other, does a human have to decide. To find the regions, pin down the lines nobody touched (anchors); the gaps between anchors are the chunks to compare.",
        hints=[
            "Reuse the LCS walk, but record matched index pairs instead of printing a diff. Do it for (base, ours) and (base, theirs).",
            "Base lines matched in both alignments are fixed points. Keep three cursors, one per file, and jump them from anchor to anchor.",
            "Each gap gives three slices B, O, T. Four cases in a fixed order resolve it; do not forget the final gap after the last anchor.",
        ],
        brute_force="Treat the whole file as one chunk (first wrong solution): if both sides changed anything anywhere, declare the entire file conflicted. That is how a tool without line alignment would behave and it makes merging unusable. Comparing line i with line i (second wrong solution) falls apart as soon as one side inserts a line.",
        approach="1. `mo`, `mt` = base-index → other-index maps from the two alignments.\n2. `anchors` = sorted base indices present in both, plus a sentinel for the tail.\n3. For each anchor cut `B`, `O`, `T` from the cursors up to the anchor's positions, resolve, emit, emit the anchor, move the cursors past it.\n\n**Dry run** base `[a,b,c]`, ours `[a,B,c]`, theirs `[a,b,c,d]`: `mo = {0:0, 2:2}`, `mt = {0:0, 1:1, 2:2}`; anchors 0 and 2. Before anchor 0 all chunks empty; emit `a`. Before anchor 2: B=[b], O=[B], T=[b]; `T == B`, emit `B`; emit `c`. Tail: B=[], O=[], T=[d]; `O == B`, emit `d`. No conflicts.",
        complexity="Time O(|base| * (|ours| + |theirs|)) for the two LCS tables; space the same.",
        pitfalls="Checking `O == B` before `O == T` is harmless, but forgetting `O == T` reports false conflicts when both sides made the same edit. Losing the tail chunk. Counting conflict *lines* instead of conflict regions.",
        follow_up="Add the base text between `|||||||` and `=======` to get the `diff3`/`zdiff3` conflict style, which makes conflicts far easier to resolve. `git merge-file ours base theirs` runs this algorithm on three plain files.",
    ),
),
dict(
    id="git-cherry-pick-conflicts",
    title="Predict cherry-pick conflicts from touched paths",
    difficulty="Medium",
    pattern="Sets / simulation",
    entry="cherry_pick_conflicts",
    description=r"""
You want to copy some commits from a `source` branch onto a `target` branch with `git cherry-pick`. A
quick (conservative) way to predict trouble is to look only at **which files** each commit touches.

- `source`: the commits on the source branch since it forked from the target, oldest first, each
  `[commit_id, [paths it changes]]`.
- `picked`: the ids you will cherry-pick. They are always applied in **source order**, whatever order this
  list is in.
- `target_paths`: the paths changed on the target branch since the fork point.

Keep a set of **hot paths**, initially `target_paths`. Go through `source` in order:

- a commit that is **not picked** is skipped, and its paths become hot (later source commits were written
  on top of changes the target will not have);
- a commit that **is picked** conflicts on every one of its paths that is currently hot. Picking a commit
  does not change the hot set.

Return a list of `[commit_id, sorted_conflicting_paths]` for the picked commits that have at least one
conflicting path, in source order.

**Example:**

```
source = [["c1", ["api.py"]], ["c2", ["api.py", "docs.md"]], ["c3", ["ui.js"]]]
picked = ["c2", "c3"]
target_paths = ["ui.js"]
```

→ `[["c2", ["api.py"]], ["c3", ["ui.js"]]]` (c2 builds on the skipped c1; c3 collides with the target).
""",
    starter='''def cherry_pick_conflicts(source, picked, target_paths):
    pass
''',
    solution='''def cherry_pick_conflicts(source, picked, target_paths):
    hot = set(target_paths)
    want = set(picked)
    out = []
    for cid, paths in source:
        if cid in want:
            clash = sorted(set(paths) & hot)
            if clash:
                out.append([cid, clash])
        else:
            hot.update(paths)
    return out
''',
    tests=[
        [[["c1", ["api.py"]], ["c2", ["api.py", "docs.md"]], ["c3", ["ui.js"]]], ["c2", "c3"], ["ui.js"]],
        [[["c1", ["api.py"]], ["c2", ["api.py", "docs.md"]], ["c3", ["ui.js"]]], ["c1", "c2", "c3"], []],
        [[["c1", ["api.py"]], ["c2", ["api.py", "docs.md"]], ["c3", ["ui.js"]]], [], ["api.py"]],
        [[], ["c9"], ["a"]],
        [[["c1", ["a", "b"]], ["c2", ["b", "c"]], ["c3", ["c", "a"]]], ["c3", "c1"], []],
        [[["c1", ["a", "b"]], ["c2", ["b", "c"]], ["c3", ["c", "a"]]], ["c3"], []],
        [[["c1", ["a", "b"]], ["c2", ["b", "c"]], ["c3", ["c", "a"]]], ["c2"], ["c", "z"]],
        [[["c1", ["z.txt", "a.txt"]], ["c2", ["a.txt"]]], ["c1", "c2"], ["a.txt", "z.txt"]],
        [[["c1", ["a"]], ["c2", ["a"]], ["c3", ["a"]], ["c4", ["a"]]], ["c1", "c2", "c4"], []],
        [[["c1", ["a"]], ["c2", ["b"]], ["c3", ["a"]]], ["c1", "c3"], []],
        [[["c1", ["a"]], ["c2", ["b"]], ["c3", ["a"]]], ["c1", "c3"], ["b"]],
        [[["s%d" % i, ["f%d" % (i % 10)]] for i in range(200)], ["s%d" % i for i in range(0, 200, 3)], ["f5"]],
    ],
    examples=1,
    wrong_solutions=[
        '''def cherry_pick_conflicts(source, picked, target_paths):
    hot = set(target_paths)
    out = []
    for cid, paths in source:
        if cid in picked:
            clash = sorted(set(paths) & hot)
            if clash:
                out.append([cid, clash])
    return out
''',
        '''def cherry_pick_conflicts(source, picked, target_paths):
    hot = set(target_paths)
    by_id = dict((c, p) for c, p in source)
    out = []
    for cid in picked:
        if cid not in by_id:
            continue
        clash = sorted(set(by_id[cid]) & hot)
        if clash:
            out.append([cid, clash])
    for cid, paths in source:
        if cid not in picked:
            hot.update(paths)
    return out
''',
    ],
    guide=dict(
        prereqs="The cherry-pick material in the distributed-workflow and rescue lessons. Python sets.",
        intuition="A cherry-pick replays one commit's *change* in a new place. The change applies cleanly when the surrounding file content is what the commit expects. Two things can make it differ: the target branch edited the same file, or the commit was written on top of an earlier source commit that you decided not to bring along. Both are tracked by one growing set of 'paths whose content differs from what the source expects'.",
        hints=[
            "Turn `picked` into a set and iterate over `source`, not over `picked`: source order is what matters.",
            "What should happen to the hot set when you pass over a commit you are not picking?",
            "For a picked commit, intersect its paths with the hot set and sort the result; record it only if non-empty.",
        ],
        brute_force="For each picked commit, rescan all earlier source commits to collect skipped paths: O(n^2) set work. Maintaining one running set does it in a single pass.",
        approach="`hot = set(target_paths)`. For each `(id, paths)` in source order: if picked, `clash = sorted(set(paths) & hot)` and record if any; otherwise `hot |= set(paths)`.\n\n**Dry run** of the example: hot = {ui.js}. c1 not picked → hot = {ui.js, api.py}. c2 picked, touches api.py and docs.md → clash [api.py]. c3 picked, touches ui.js → clash [ui.js].",
        complexity="Time O(total number of paths) plus sorting the small clash lists; space O(distinct paths).",
        pitfalls="Iterating in the order of `picked`. Forgetting skipped commits entirely (first wrong solution). Adding skipped paths only after all picks were evaluated (second wrong solution). Returning unsorted path lists.",
        follow_up="Path overlap is a necessary but not sufficient condition: Git merges at the line level, so two edits to different parts of one file usually pick cleanly. `git cherry-pick -n` lets you try without committing, and `git range-diff` compares the picked series with the originals.",
    ),
),
dict(
    id="git-rebase-todo",
    title="Execute an interactive-rebase todo list",
    difficulty="Medium",
    pattern="Simulation",
    entry="apply_todo",
    description=r"""
`git rebase -i` opens a todo list: one line per commit, oldest first, each with an action. You may reorder
lines, delete them and change the actions; Git then replays the list from top to bottom.

`commits` is the original series, oldest first, as `[id, message]` pairs. `todo` is the edited list; each
step is `[action, id]` or, for `reword`, `[action, id, new_message]`. Actions:

- `pick`: keep the commit as it is;
- `reword`: keep the commit but replace its message with `new_message`;
- `squash`: fold the commit into the **previous resulting commit**; the combined message is the previous
  message, a blank line, then this commit's message (`prev + "\n\n" + this`);
- `fixup`: fold into the previous resulting commit and **discard** this commit's message;
- `drop`: remove the commit.

A commit that does not appear in `todo` is dropped as well.

Return the resulting series, oldest first, as a list of `[ids, message]` where `ids` lists the original
commits that went into that result (in the order they were folded). Return `None` if the todo is invalid:
an unknown action, an id not in `commits`, an id used twice, or a `squash`/`fixup` with no previous
resulting commit to fold into.

**Example:**

```
commits = [["a", "add parser"], ["b", "typo"], ["c", "add tests"]]
todo    = [["pick", "a"], ["fixup", "b"], ["reword", "c", "test: cover parser"]]
```

→ `[[["a", "b"], "add parser"], [["c"], "test: cover parser"]]`
""",
    starter='''def apply_todo(commits, todo):
    pass
''',
    solution='''def apply_todo(commits, todo):
    msg = {c[0]: c[1] for c in commits}
    used = set()
    out = []
    for step in todo:
        action, cid = step[0], step[1]
        if cid not in msg or cid in used:
            return None
        used.add(cid)
        if action == "pick":
            out.append([[cid], msg[cid]])
        elif action == "reword":
            out.append([[cid], step[2]])
        elif action in ("squash", "fixup"):
            if not out:
                return None
            out[-1][0].append(cid)
            if action == "squash":
                out[-1][1] += "\\n\\n" + msg[cid]
        elif action != "drop":
            return None
    return out
''',
    tests=[
        [[["a", "add parser"], ["b", "typo"], ["c", "add tests"]], [["pick", "a"], ["fixup", "b"], ["reword", "c", "test: cover parser"]]],
        [[["a", "add parser"], ["b", "typo"], ["c", "add tests"]], [["pick", "a"], ["pick", "b"], ["pick", "c"]]],
        [[["a", "add parser"], ["b", "typo"], ["c", "add tests"]], [["pick", "c"], ["pick", "a"], ["squash", "b"]]],
        [[["a", "add parser"], ["b", "typo"], ["c", "add tests"]], [["pick", "a"], ["squash", "b"], ["squash", "c"]]],
        [[["a", "add parser"], ["b", "typo"], ["c", "add tests"]], [["pick", "a"], ["fixup", "b"], ["squash", "c"]]],
        [[["a", "add parser"], ["b", "typo"], ["c", "add tests"]], [["squash", "a"], ["pick", "b"]]],
        [[["a", "add parser"], ["b", "typo"], ["c", "add tests"]], [["drop", "a"], ["fixup", "b"], ["pick", "c"]]],
        [[["a", "add parser"], ["b", "typo"], ["c", "add tests"]], [["drop", "a"], ["pick", "c"]]],
        [[["a", "add parser"], ["b", "typo"], ["c", "add tests"]], []],
        [[["a", "add parser"], ["b", "typo"], ["c", "add tests"]], [["pick", "a"], ["pick", "a"]]],
        [[["a", "add parser"], ["b", "typo"], ["c", "add tests"]], [["pick", "a"], ["pick", "zz"]]],
        [[["a", "add parser"], ["b", "typo"], ["c", "add tests"]], [["pick", "a"], ["edit!", "b"]]],
        [[["a", "add parser"], ["b", "typo"], ["c", "add tests"]], [["reword", "b", "fix: spelling"], ["fixup", "c"], ["pick", "a"]]],
        [[], []],
        [[["a", "one"], ["b", "two"]], [["pick", "a"], ["drop", "a"]]],
    ],
    examples=1,
    wrong_solutions=[
        '''def apply_todo(commits, todo):
    msg = {c[0]: c[1] for c in commits}
    out = []
    for step in todo:
        action, cid = step[0], step[1]
        if cid not in msg:
            return None
        if action == "pick":
            out.append([[cid], msg[cid]])
        elif action == "reword":
            out.append([[cid], step[2]])
        elif action in ("squash", "fixup"):
            if not out:
                return None
            out[-1][0].append(cid)
            out[-1][1] += "\\n\\n" + msg[cid]
        elif action != "drop":
            return None
    return out
''',
    ],
    guide=dict(
        prereqs="The lesson on rewriting history (interactive rebase).",
        intuition="The todo list is a little program and you are its interpreter. Keep a result list; each instruction either appends a new result commit, modifies the last one, or does nothing. Validation is bookkeeping: known id, not seen before, known action, and something to fold into.",
        hints=[
            "Build a dict from id to message so lookups and the 'unknown id' check are one operation.",
            "`squash` and `fixup` both extend the id list of `out[-1]`; they differ only in what happens to the message.",
            "Track used ids in a set and validate *before* acting, so a bad step anywhere makes the whole result `None`.",
        ],
        brute_force="There is no asymptotically slower sensible algorithm; the pitfalls are all in the rules. A quick hack that treats fixup like squash, or that forgets duplicate detection, passes the happy path only.",
        approach="Loop over steps; validate id; dispatch on the action.\n\n**Dry run** of the example: `pick a` → `[[['a'], 'add parser']]`. `fixup b` → ids become `['a','b']`, message unchanged. `reword c` → append `[['c'], 'test: cover parser']`.",
        complexity="Time O(len(commits) + len(todo)); space the same.",
        pitfalls="Folding into the previous *todo line* rather than the previous *result* (they differ when the previous line was a drop). Mutating a shared list. Letting a later `drop` of an already used id pass.",
        follow_up="Real rebase also offers `edit`, `exec`, `break`, `label`/`reset`/`merge`. `git commit --fixup=<id>` plus `git rebase -i --autosquash` writes the fixup lines for you.",
    ),
),
dict(
    id="git-squash-commits",
    title="Squash a series of commits into one",
    difficulty="Medium",
    pattern="Simulation / dict diff",
    entry="squash",
    description=r"""
A squash merge replaces a series of commits by a single commit with the same overall effect.

- `base` is the snapshot before the series: a dict `{path: content}`.
- `commits` is the series, oldest first, each `[message, changes]`, where `changes` maps a path to its new
  content, or to `None` meaning the commit deletes that path. (Deleting a path that does not exist is a no-op.)

Write `squash(base, commits)` returning `[message, changes]` for the single equivalent commit, or `None` if
`commits` is empty.

- `changes` must be **minimal**: include a path only if its final state differs from `base` (new or changed
  content → that content; present in `base` but gone at the end → `None`). A file that was added and later
  removed, or edited and then restored to its original content, must not appear.
- `message` is the first commit's message; if there are more commits, add a blank line and then one line
  `* <message>` for each of the remaining commits, joined by newlines.

**Example:**

```
base    = {"app.py": "v1"}
commits = [["add cache", {"cache.py": "c1", "app.py": "v2"}],
           ["fix cache", {"cache.py": "c2"}],
           ["revert app tweak", {"app.py": "v1"}]]
```

→ `["add cache\n\n* fix cache\n* revert app tweak", {"cache.py": "c2"}]`
""",
    starter='''def squash(base, commits):
    pass
''',
    solution='''def squash(base, commits):
    if not commits:
        return None
    final = dict(base)
    for _, changes in commits:
        for path, content in changes.items():
            if content is None:
                final.pop(path, None)
            else:
                final[path] = content
    net = {}
    for path in set(base) | set(final):
        if base.get(path) != final.get(path):
            net[path] = final.get(path)
    message = commits[0][0]
    if len(commits) > 1:
        message += "\\n\\n" + "\\n".join("* " + m for m, _ in commits[1:])
    return [message, net]
''',
    tests=[
        [{"app.py": "v1"}, [["add cache", {"cache.py": "c1", "app.py": "v2"}], ["fix cache", {"cache.py": "c2"}], ["revert app tweak", {"app.py": "v1"}]]],
        [{"app.py": "v1"}, [["only", {"app.py": "v2"}]]],
        [{"app.py": "v1"}, []],
        [{}, [["init", {"a": "1"}], ["oops", {"a": None}]]],
        [{"a": "1", "b": "2"}, [["rm a", {"a": None}], ["rm b", {"b": None}]]],
        [{"a": "1"}, [["rm a", {"a": None}], ["re-add a", {"a": "1"}]]],
        [{"a": "1"}, [["rm a", {"a": None}], ["re-add a differently", {"a": "2"}]]],
        [{"a": "1"}, [["rm ghost", {"ghost": None}]]],
        [{"a": "1"}, [["empty commit", {}], ["another", {}]]],
        [{}, [["a", {"x": "1"}], ["b", {"y": "2"}], ["c", {"x": "3", "z": "4"}], ["d", {"y": None}]]],
        [{"keep": "k", "edit": "e0"}, [["e1", {"edit": "e1"}], ["e2", {"edit": "e2"}], ["e3", {"edit": "e3", "new": ""}]]],
        [{"f%d" % i: "0" for i in range(50)}, [["step %d" % s, {"f%d" % i: str((i * s) % 3) for i in range(0, 50, s)}] for s in range(1, 8)]],
    ],
    examples=1,
    wrong_solutions=[
        '''def squash(base, commits):
    if not commits:
        return None
    net = {}
    for _, changes in commits:
        net.update(changes)
    message = commits[0][0]
    if len(commits) > 1:
        message += "\\n\\n" + "\\n".join("* " + m for m, _ in commits[1:])
    return [message, net]
''',
    ],
    guide=dict(
        prereqs="Snapshots versus changes (first module) and the squash-merge discussion in *Team workflows in practice*.",
        intuition="Git stores snapshots, not patches, and a squash is easiest to think about the same way. Do not try to 'add up' the changes. Instead play the series forward from the base to obtain the final snapshot, then compare final with base. Whatever differs is the squashed commit.",
        hints=[
            "Copy `base` and apply each commit's changes in order: assignment for content, removal for `None`.",
            "The net change set is a diff of two dicts. Look at the union of their keys.",
            "`dict.get` returns `None` for a missing key, which conveniently is also the marker for 'deleted'.",
        ],
        brute_force="Merge all change dicts with 'later wins' (the wrong solution). It reports files that ended up identical to the base, and deletions of files that never existed before the series.",
        approach="1. Replay to get `final`.\n2. For each path in `base` or `final`, if the contents differ record `final.get(path)`.\n3. Assemble the message.\n\n**Dry run** of the example: after the three commits `final = {app.py: v1, cache.py: c2}`. Compared with the base, `app.py` is unchanged and `cache.py` is new, so the net change is `{cache.py: c2}`.",
        complexity="Time O(total changes + size of base); space O(size of snapshots).",
        pitfalls="Mutating the caller's `base`. Emitting `None` for a path that was never in `base`. Forgetting that an empty series has no squash.",
        follow_up="This is what `git merge --squash` and `git reset --soft <base> && git commit` produce. The resulting commit has a single parent, so Git no longer knows the feature branch was merged; delete the branch afterwards.",
    ),
),
]
