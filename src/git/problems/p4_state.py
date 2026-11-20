"""Git track problems, part 4: HEAD, index, working tree and the stash."""

SNAPS = {
    "c1": {"app.py": "v1"},
    "c2": {"app.py": "v2", "util.py": "u1"},
    "c3": {"app.py": "v3", "util.py": "u1", "docs.md": "d1"},
}

PROBLEMS = [
dict(
    id="git-reset-modes",
    title="Simulate git reset --soft / --mixed / --hard",
    difficulty="Medium",
    pattern="State simulation",
    entry="reset",
    description=r"""
Git keeps three "trees": the commit **HEAD** points at, the **index** (staging area) and the **working
tree**. `git reset <mode> <target>` rewinds them in stages.

Arguments of `reset(commits, head, index, worktree, mode, target)`:

- `commits`: dict `{commit_id: snapshot}` where a snapshot is `{path: content}`;
- `head`: the current commit id; `index`, `worktree`: dicts `{path: content}`;
- `mode`: `"soft"`, `"mixed"` or `"hard"`; `target`: the commit id to reset to.

Return `[new_head, new_index, new_worktree]` (do not mutate the inputs), or `None` if `target` is not in
`commits` or the mode is unknown.

- **soft**: only HEAD moves to `target`.
- **mixed**: HEAD moves and the index becomes a copy of the target snapshot. The working tree is untouched.
- **hard**: HEAD moves, the index becomes the target snapshot, and the working tree becomes the target
  snapshot **plus the untracked files**, which Git leaves alone. A working-tree path is *untracked* when it
  is neither in the **old index** nor in the **target snapshot**.

**Example:** HEAD at `c2` = `{"app.py": "v2"}`, index and working tree both `{"app.py": "v2-edited"}`,
`commits["c1"] = {"app.py": "v1"}`:

- soft to `c1` → `["c1", {"app.py": "v2-edited"}, {"app.py": "v2-edited"}]`
- hard to `c1` → `["c1", {"app.py": "v1"}, {"app.py": "v1"}]`
""",
    starter='''def reset(commits, head, index, worktree, mode, target):
    pass
''',
    solution='''def reset(commits, head, index, worktree, mode, target):
    if target not in commits or mode not in ("soft", "mixed", "hard"):
        return None
    snap = commits[target]
    if mode == "soft":
        return [target, dict(index), dict(worktree)]
    if mode == "mixed":
        return [target, dict(snap), dict(worktree)]
    new_wt = dict(snap)
    for path, content in worktree.items():
        if path not in index and path not in snap:
            new_wt[path] = content
    return [target, dict(snap), new_wt]
''',
    tests=[
        [{"c1": {"app.py": "v1"}, "c2": {"app.py": "v2"}}, "c2", {"app.py": "v2-edited"}, {"app.py": "v2-edited"}, "soft", "c1"],
        [{"c1": {"app.py": "v1"}, "c2": {"app.py": "v2"}}, "c2", {"app.py": "v2-edited"}, {"app.py": "v2-edited"}, "hard", "c1"],
        [{"c1": {"app.py": "v1"}, "c2": {"app.py": "v2"}}, "c2", {"app.py": "v2-edited"}, {"app.py": "v2-edited"}, "mixed", "c1"],
        [SNAPS, "c3", dict(SNAPS["c3"]), dict(SNAPS["c3"]), "soft", "c1"],
        [SNAPS, "c3", dict(SNAPS["c3"]), dict(SNAPS["c3"]), "mixed", "c1"],
        [SNAPS, "c3", dict(SNAPS["c3"]), dict(SNAPS["c3"]), "hard", "c1"],
        [SNAPS, "c3", dict(SNAPS["c3"]), dict(SNAPS["c3"], **{"notes.txt": "scratch"}), "hard", "c2"],
        [SNAPS, "c3", dict(SNAPS["c3"], **{"new.py": "staged"}), dict(SNAPS["c3"], **{"new.py": "staged", "notes.txt": "scratch"}), "hard", "c3"],
        [SNAPS, "c1", dict(SNAPS["c1"]), {"app.py": "v1", "docs.md": "my local draft"}, "hard", "c3"],
        [SNAPS, "c2", {"app.py": "v2"}, {"app.py": "v2", "util.py": "u1"}, "hard", "c1"],
        [SNAPS, "c2", dict(SNAPS["c2"]), {}, "mixed", "c2"],
        [SNAPS, "c2", dict(SNAPS["c2"]), {}, "hard", "c2"],
        [SNAPS, "c2", dict(SNAPS["c2"]), dict(SNAPS["c2"]), "hard", "c9"],
        [SNAPS, "c2", dict(SNAPS["c2"]), dict(SNAPS["c2"]), "keep", "c1"],
    ],
    examples=2,
    wrong_solutions=[
        '''def reset(commits, head, index, worktree, mode, target):
    if target not in commits or mode not in ("soft", "mixed", "hard"):
        return None
    snap = commits[target]
    if mode == "soft":
        return [target, dict(index), dict(worktree)]
    if mode == "mixed":
        return [target, dict(snap), dict(worktree)]
    return [target, dict(snap), dict(snap)]
''',
        '''def reset(commits, head, index, worktree, mode, target):
    if target not in commits or mode not in ("soft", "mixed", "hard"):
        return None
    snap = commits[target]
    if mode == "soft":
        return [target, dict(index), dict(worktree)]
    if mode == "mixed":
        return [target, dict(snap), dict(worktree)]
    new_wt = dict(worktree)
    new_wt.update(snap)
    return [target, dict(snap), new_wt]
''',
    ],
    guide=dict(
        prereqs="The lesson *Reset demystified*.",
        intuition="Reset is three steps performed in a fixed order, and the mode says after which step to stop. Step 1 moves the branch HEAD points at. Step 2 copies that commit into the index. Step 3 copies the index into the working tree. Soft stops after 1, mixed after 2, hard does all three. The only subtlety is what 'copy into the working tree' means for files Git is not tracking.",
        hints=[
            "Write the soft case first, then extend: each stronger mode does everything the weaker one does plus one more overwrite.",
            "For hard, start from a copy of the target snapshot and then decide which working-tree files survive.",
            "A file survives a hard reset only if Git has no opinion about it: it was not staged or tracked before, and the target does not contain it.",
        ],
        brute_force="Not applicable in a complexity sense. The naive hard reset (first wrong solution) wipes the working tree to exactly the snapshot, deleting untracked notes; the opposite mistake (second wrong solution) keeps tracked files that the target commit does not have.",
        approach="Validate. `soft` → copies of the old index and tree. `mixed` → target snapshot as the index. `hard` → target snapshot as both, then add every working-tree path that is in neither the old index nor the target.\n\n**Dry run**: HEAD c3, clean, plus an untracked `notes.txt`; `hard` to c2. The snapshot of c2 is `{app.py: v2, util.py: u1}`. `docs.md` is in the old index, so it is tracked and disappears. `notes.txt` is in neither, so it stays.",
        complexity="Time and space O(size of the snapshots).",
        pitfalls="Returning the same dict objects that were passed in. Deciding 'untracked' with the *new* index instead of the old one. Forgetting that an untracked file with the same path as a file in the target is overwritten.",
        follow_up="`git reset --keep` and `--merge` are safer variants that refuse to clobber local edits. `git restore` and `git switch` took over the file-level and branch-level jobs of `checkout`/`reset` in Git 2.23.",
    ),
),
dict(
    id="git-status-categories",
    title="Compute git status from three snapshots",
    difficulty="Easy",
    pattern="Dict comparison",
    entry="status",
    description=r"""
`git status` is two diffs and a set difference. Given three dicts `{path: content}`:

- `head`: the snapshot of the last commit,
- `index`: the staging area,
- `worktree`: the files on disk,

write `status(head, index, worktree)` returning a dict with three sorted lists:

- `"staged"` (*Changes to be committed*, index compared with head):
  `"new file: P"` if P is in the index but not in head; `"modified: P"` if in both with different content;
  `"deleted: P"` if in head but not in the index.
- `"unstaged"` (*Changes not staged for commit*, working tree compared with the index, for paths in the index):
  `"modified: P"` if the content differs; `"deleted: P"` if P is missing from the working tree.
- `"untracked"`: the paths (just the path, no label) present in the working tree but not in the index.

Sort each list by **path**.

**Example:**

```
head     = {"a.txt": "1", "b.txt": "1"}
index    = {"a.txt": "2", "b.txt": "1", "c.txt": "new"}
worktree = {"a.txt": "3", "c.txt": "new", "tmp.log": "x"}
```

→ `{"staged": ["modified: a.txt", "new file: c.txt"], "unstaged": ["modified: a.txt", "deleted: b.txt"], "untracked": ["tmp.log"]}`
""",
    starter='''def status(head, index, worktree):
    pass
''',
    solution='''def status(head, index, worktree):
    staged, unstaged, untracked = [], [], []
    for p in sorted(set(head) | set(index)):
        if p not in head:
            staged.append("new file: " + p)
        elif p not in index:
            staged.append("deleted: " + p)
        elif head[p] != index[p]:
            staged.append("modified: " + p)
    for p in sorted(index):
        if p not in worktree:
            unstaged.append("deleted: " + p)
        elif worktree[p] != index[p]:
            unstaged.append("modified: " + p)
    for p in sorted(worktree):
        if p not in index:
            untracked.append(p)
    return {"staged": staged, "unstaged": unstaged, "untracked": untracked}
''',
    tests=[
        [{"a.txt": "1", "b.txt": "1"}, {"a.txt": "2", "b.txt": "1", "c.txt": "new"}, {"a.txt": "3", "c.txt": "new", "tmp.log": "x"}],
        [{"a.txt": "1"}, {"a.txt": "1"}, {"a.txt": "1"}],
        [{}, {}, {}],
        [{}, {}, {"README.md": "hi", "main.py": ""}],
        [{}, {"README.md": "hi"}, {"README.md": "hi"}],
        [{"old.txt": "x"}, {}, {}],
        [{"old.txt": "x"}, {}, {"old.txt": "x"}],
        [{"a": "1"}, {"a": "2"}, {"a": "1"}],
        [{"a": "1"}, {"a": "1"}, {}],
        [{"z": "1", "m": "1", "a": "1"}, {"z": "2", "m": "2", "a": "2"}, {"z": "3", "m": "3", "a": "3", "b": "", "y": ""}],
        [{"zeta": "1"}, {"alpha": "1"}, {"alpha": "1"}],
        [{"src/a.py": "1", "src/b.py": "1"}, {"src/a.py": "1", "src/c.py": "1"}, {"src/a.py": "x", "src/c.py": "1", "src/b.py": "1"}],
    ],
    examples=1,
    wrong_solutions=[
        '''def status(head, index, worktree):
    staged, unstaged, untracked = [], [], []
    for p in sorted(set(head) | set(index)):
        if p not in head:
            staged.append("new file: " + p)
        elif p not in index:
            staged.append("deleted: " + p)
        elif head[p] != index[p]:
            staged.append("modified: " + p)
    for p in sorted(worktree):
        if p not in head:
            untracked.append(p)
        elif worktree[p] != head[p]:
            unstaged.append("modified: " + p)
    for p in sorted(head):
        if p not in worktree:
            unstaged.append("deleted: " + p)
    return {"staged": staged, "unstaged": sorted(unstaged), "untracked": untracked}
''',
        '''def status(head, index, worktree):
    staged = sorted(("new file: " if p not in head else "deleted: " if p not in index else "modified: ") + p
                    for p in set(head) | set(index) if head.get(p) != index.get(p))
    unstaged = sorted(("deleted: " if p not in worktree else "modified: ") + p
                      for p in index if worktree.get(p) != index[p])
    untracked = sorted(p for p in worktree if p not in index)
    return {"staged": staged, "unstaged": unstaged, "untracked": untracked}
''',
    ],
    guide=dict(
        prereqs="The lesson on recording changes: the three areas and the file life cycle.",
        intuition="Status never compares the working tree with the last commit directly. It makes two adjacent comparisons: commit versus index tells you what the next commit would contain, index versus working tree tells you what you have not staged yet. A file can therefore appear in both lists at once, when you stage an edit and then edit again.",
        hints=[
            "Handle the three lists independently; each is a small loop.",
            "For the staged list iterate over the union of keys of `head` and `index`.",
            "Sort by path, not by the finished label string: `deleted: z` would sort before `modified: a`.",
        ],
        brute_force="Comparing the working tree against HEAD (first wrong solution) merges the two stages into one and cannot express 'staged and then modified again'. It also calls a staged new file untracked.",
        approach="Three passes over sorted keys, exactly as the rules read.\n\n**Dry run** of the example. Staged: `a.txt` differs (1 → 2) so modified; `b.txt` equal; `c.txt` only in index so new file. Unstaged: `a.txt` 2 vs 3 modified; `b.txt` missing on disk so deleted; `c.txt` equal. Untracked: `tmp.log`.",
        complexity="Time O(n log n) for sorting n paths; space O(n).",
        pitfalls="Sorting the label strings (second wrong solution). Calling a path untracked because it is not in HEAD. Listing a file as unstaged-deleted when it is not in the index at all.",
        follow_up="`git status --short` prints the same information as two status letters per file; the next problem builds that format while simulating `add` and `commit`.",
    ),
),
dict(
    id="git-staging-sim",
    title="Simulate add, unstage and commit; print short status",
    difficulty="Medium",
    pattern="State simulation",
    entry="simulate",
    description=r"""
Simulate a repository that starts empty (no commits, empty index, empty working tree) and process a list
of operations:

- `["write", path, content]`: create or overwrite a file in the working tree.
- `["remove", path]`: delete the file from the working tree (no-op if absent).
- `["add", path]`: stage the working-tree state of `path`: copy its content into the index, or, if the file
  is absent from the working tree, remove the path from the index. If `path` is `"."`, do this for every
  path that is in the working tree or in the index.
- `["unstage", path]`: restore the index entry from HEAD (like `git restore --staged`): set it to HEAD's
  content, or remove it from the index if HEAD does not have the path.
- `["commit"]`: if the index differs from HEAD's snapshot, HEAD's snapshot becomes a copy of the index and
  the commit counter goes up by one; otherwise nothing happens.

Return `[commit_count, lines]` where `lines` is the final `git status --short` style report. For each path
in sorted order:

- compute `X` (index vs HEAD): `A` in the index but not HEAD, `M` in both with different content, `D` in HEAD
  but not the index, otherwise a space;
- compute `Y` (working tree vs index, only for paths in the index): `M` different content, `D` missing from
  the working tree, otherwise a space;
- if `X` or `Y` is not a space, output `X + Y + " " + path`;
- then, if the path is in the working tree but not in the index, also output `"?? " + path`.

**Example:** `[["write", "a.txt", "1"], ["add", "a.txt"], ["write", "a.txt", "2"], ["write", "b.txt", "x"]]`
→ `[0, ["AM a.txt", "?? b.txt"]]`
""",
    starter='''def simulate(ops):
    pass
''',
    solution='''def simulate(ops):
    head, index, wt = {}, {}, {}
    count = 0

    def stage(p):
        if p in wt:
            index[p] = wt[p]
        else:
            index.pop(p, None)

    for op in ops:
        kind = op[0]
        if kind == "write":
            wt[op[1]] = op[2]
        elif kind == "remove":
            wt.pop(op[1], None)
        elif kind == "add":
            if op[1] == ".":
                for p in set(wt) | set(index):
                    stage(p)
            else:
                stage(op[1])
        elif kind == "unstage":
            if op[1] in head:
                index[op[1]] = head[op[1]]
            else:
                index.pop(op[1], None)
        elif kind == "commit":
            if index != head:
                head = dict(index)
                count += 1
    lines = []
    for p in sorted(set(head) | set(index) | set(wt)):
        x = y = " "
        if p in index and p not in head:
            x = "A"
        elif p in head and p not in index:
            x = "D"
        elif p in head and head[p] != index[p]:
            x = "M"
        if p in index:
            if p not in wt:
                y = "D"
            elif wt[p] != index[p]:
                y = "M"
        if x != " " or y != " ":
            lines.append(x + y + " " + p)
        if p in wt and p not in index:
            lines.append("?? " + p)
    return [count, lines]
''',
    tests=[
        [[["write", "a.txt", "1"], ["add", "a.txt"], ["write", "a.txt", "2"], ["write", "b.txt", "x"]]],
        [[]],
        [[["commit"]]],
        [[["write", "a.txt", "1"], ["add", "a.txt"], ["commit"]]],
        [[["write", "a.txt", "1"], ["add", "a.txt"], ["commit"], ["commit"], ["write", "a.txt", "2"], ["commit"]]],
        [[["write", "a.txt", "1"], ["add", "."], ["commit"], ["write", "a.txt", "2"], ["add", "a.txt"], ["write", "a.txt", "1"]]],
        [[["write", "a.txt", "1"], ["add", "."], ["commit"], ["remove", "a.txt"]]],
        [[["write", "a.txt", "1"], ["add", "."], ["commit"], ["remove", "a.txt"], ["add", "a.txt"]]],
        [[["write", "a.txt", "1"], ["add", "."], ["commit"], ["remove", "a.txt"], ["add", "a.txt"], ["write", "a.txt", "again"]]],
        [[["write", "a.txt", "1"], ["add", "."], ["commit"], ["remove", "a.txt"], ["add", "."], ["commit"]]],
        [[["write", "a.txt", "1"], ["add", "a.txt"], ["unstage", "a.txt"]]],
        [[["write", "a.txt", "1"], ["add", "."], ["commit"], ["write", "a.txt", "2"], ["add", "."], ["unstage", "a.txt"]]],
        [[["write", "z", "1"], ["write", "m", "1"], ["write", "a", "1"], ["add", "."], ["commit"], ["write", "z", "2"], ["write", "m", "2"], ["add", "m"], ["remove", "a"], ["write", "new", ""], ["add", "ghost"]]],
        [[["write", "a", "1"], ["add", "a"], ["write", "a", "2"], ["commit"], ["add", "a"], ["commit"], ["write", "b", "b"], ["add", "."], ["remove", "b"], ["commit"]]],
        [[["write", "a", "1"], ["add", "."], ["commit"], ["write", "a", "2"], ["add", "."], ["write", "a", "1"], ["add", "."], ["commit"]]],
    ],
    examples=1,
    wrong_solutions=[
        '''def simulate(ops):
    head, wt, staged = {}, {}, set()
    count = 0
    for op in ops:
        kind = op[0]
        if kind == "write":
            wt[op[1]] = op[2]
        elif kind == "remove":
            wt.pop(op[1], None)
        elif kind == "add":
            staged |= (set(wt) | set(head)) if op[1] == "." else {op[1]}
        elif kind == "unstage":
            staged.discard(op[1])
        elif kind == "commit":
            changed = False
            for p in staged:
                if wt.get(p) != head.get(p):
                    changed = True
                    if p in wt:
                        head[p] = wt[p]
                    else:
                        head.pop(p, None)
            staged = set()
            count += changed
    lines = []
    for p in sorted(set(head) | set(wt)):
        if p not in head:
            lines.append(("A  " if p in staged else "?? ") + p)
        elif p not in wt:
            lines.append(("D  " if p in staged else " D ") + p)
        elif wt[p] != head[p]:
            lines.append(("M  " if p in staged else " M ") + p)
    return [count, lines]
''',
    ],
    guide=dict(
        prereqs="Problem *Compute git status from three snapshots* and the lesson on recording changes.",
        intuition="The index is a real snapshot with its own copy of each staged file, not a list of 'files marked for commit'. `add` copies working tree → index, `commit` copies index → HEAD, `unstage` copies HEAD → index. Model the three dicts honestly and every odd-looking status (`AM`, `MM`, `D` plus `??`) falls out by itself.",
        hints=[
            "Keep three dicts. Each operation is one or two dict assignments or deletions.",
            "`add` of a file that no longer exists on disk stages its *deletion*.",
            "`commit` compares whole dicts: `index != head`. Remember to copy the index, not alias it.",
        ],
        brute_force="Tracking only a set of 'staged file names' (the wrong solution). It commits whatever is on disk at commit time rather than what was staged, so `add`, edit, `commit` records the wrong content and the `AM`/`MM` states cannot be represented.",
        approach="Process operations into the three dicts, then derive the report path by path.\n\n**Dry run** of the example: write a.txt=1; add → index {a:1}; write a.txt=2; write b.txt. HEAD is empty. For `a.txt`: in index, not in HEAD → X = `A`; working tree 2 vs index 1 → Y = `M`; line `AM a.txt`. For `b.txt`: not in index or HEAD, no XY line; in working tree and not index → `?? b.txt`.",
        complexity="Time O(ops + paths log paths), with `add .` costing O(paths); space O(paths).",
        pitfalls="Aliasing `head = index` so later staging silently changes history. Iterating over a dict while mutating it in `add .`. Forgetting that an edit reverted before commit makes `index == head`, so the commit is a no-op.",
        follow_up="Real short status has more codes (`R` renamed, `C` copied, `U` unmerged, `!!` ignored). `git status --porcelain=v2` is the stable, script-friendly format.",
    ),
),
dict(
    id="git-stash-stack",
    title="Simulate the stash stack",
    difficulty="Medium",
    pattern="Stack simulation",
    entry="stash_sim",
    description=r"""
`git stash` shelves your uncommitted changes on a stack so you can switch tasks with a clean tree.

Model the uncommitted changes as a dict `dirty` `{path: content}` (empty means a clean working tree) and
the stash as a list where index 0 is the **newest** entry. Each entry has a message and a saved dict.
Process `ops` in order:

- `["edit", path, content]`: `dirty[path] = content`.
- `["push", message]`: if `dirty` is empty, record the error `"nothing to stash"`; otherwise put
  `(message, dirty)` at position 0 and make `dirty` empty.
- `["apply", n]`: if there is no entry `n`, record `"no such stash"`. If any path saved in entry `n` is
  also in `dirty`, record `"conflict"` and change nothing. Otherwise merge the saved paths into `dirty`
  (the entry stays on the stack).
- `["pop", n]`: like `apply`, and if it succeeds the entry is also removed.
- `["drop", n]`: remove entry `n`, or record `"no such stash"`.

`n` is a non-negative integer; positions shift down when an entry above is removed.

Return `[dirty, listing, errors]` where `listing` is the final stack as strings `"stash@{i}: <message>"`
(newest first) and `errors` is the list of recorded error strings in order.

**Example:** `[["edit", "a", "1"], ["push", "wip a"], ["edit", "b", "2"], ["push", "wip b"], ["pop", 1]]`
→ `[{"a": "1"}, ["stash@{0}: wip b"], []]`
""",
    starter='''def stash_sim(ops):
    pass
''',
    solution='''def stash_sim(ops):
    dirty = {}
    stack = []
    errors = []
    for op in ops:
        kind = op[0]
        if kind == "edit":
            dirty[op[1]] = op[2]
        elif kind == "push":
            if not dirty:
                errors.append("nothing to stash")
            else:
                stack.insert(0, (op[1], dirty))
                dirty = {}
        elif kind in ("apply", "pop"):
            n = op[1]
            if n >= len(stack):
                errors.append("no such stash")
                continue
            saved = stack[n][1]
            if any(p in dirty for p in saved):
                errors.append("conflict")
                continue
            dirty.update(saved)
            if kind == "pop":
                del stack[n]
        elif kind == "drop":
            if op[1] >= len(stack):
                errors.append("no such stash")
            else:
                del stack[op[1]]
    listing = ["stash@{%d}: %s" % (i, m) for i, (m, _) in enumerate(stack)]
    return [dirty, listing, errors]
''',
    tests=[
        [[["edit", "a", "1"], ["push", "wip a"], ["edit", "b", "2"], ["push", "wip b"], ["pop", 1]]],
        [[]],
        [[["push", "empty"]]],
        [[["pop", 0]]],
        [[["edit", "a", "1"], ["push", "one"], ["pop", 0]]],
        [[["edit", "a", "1"], ["push", "one"], ["apply", 0], ["apply", 0]]],
        [[["edit", "a", "1"], ["push", "one"], ["edit", "a", "2"], ["pop", 0]]],
        [[["edit", "a", "1"], ["push", "one"], ["edit", "b", "2"], ["pop", 0], ["push", "both"], ["drop", 0], ["drop", 0]]],
        [[["edit", "a", "1"], ["push", "s1"], ["edit", "b", "1"], ["push", "s2"], ["edit", "c", "1"], ["push", "s3"], ["drop", 1], ["apply", 1], ["apply", 2]]],
        [[["edit", "a", "1"], ["push", "s1"], ["edit", "a", "2"], ["push", "s2"], ["pop", 0], ["pop", 0]]],
        [[["edit", "a", "1"], ["edit", "b", "1"], ["push", "two files"], ["edit", "c", "1"], ["apply", 0], ["edit", "a", "changed"], ["push", "again"], ["pop", 1], ["pop", 0], ["pop", 0]]],
        [[["edit", "x", "1"], ["push", "p1"], ["edit", "x", "2"], ["push", "p2"], ["edit", "x", "3"], ["push", "p3"], ["pop", 2], ["push", "p4"], ["drop", 5]]],
    ],
    examples=1,
    wrong_solutions=[
        '''def stash_sim(ops):
    dirty = {}
    stack = []
    errors = []
    for op in ops:
        kind = op[0]
        if kind == "edit":
            dirty[op[1]] = op[2]
        elif kind == "push":
            if not dirty:
                errors.append("nothing to stash")
            else:
                stack.append((op[1], dirty))
                dirty = {}
        elif kind in ("apply", "pop"):
            n = op[1]
            if n >= len(stack):
                errors.append("no such stash")
                continue
            saved = stack[n][1]
            if any(p in dirty for p in saved):
                errors.append("conflict")
                continue
            dirty.update(saved)
            if kind == "pop":
                del stack[n]
        elif kind == "drop":
            if op[1] >= len(stack):
                errors.append("no such stash")
            else:
                del stack[op[1]]
    listing = ["stash@{%d}: %s" % (i, m) for i, (m, _) in enumerate(stack)]
    return [dirty, listing, errors]
''',
        '''def stash_sim(ops):
    dirty = {}
    stack = []
    errors = []
    for op in ops:
        kind = op[0]
        if kind == "edit":
            dirty[op[1]] = op[2]
        elif kind == "push":
            if not dirty:
                errors.append("nothing to stash")
            else:
                stack.insert(0, (op[1], dirty))
                dirty = {}
        elif kind in ("apply", "pop"):
            n = op[1]
            if n >= len(stack):
                errors.append("no such stash")
                continue
            dirty.update(stack[n][1])
            del stack[n]
        elif kind == "drop":
            if op[1] >= len(stack):
                errors.append("no such stash")
            else:
                del stack[op[1]]
    listing = ["stash@{%d}: %s" % (i, m) for i, (m, _) in enumerate(stack)]
    return [dirty, listing, errors]
''',
    ],
    guide=dict(
        prereqs="The lesson on stashing and cleaning. Lists used as stacks.",
        intuition="The stash is a stack whose top is numbered 0, so pushing renumbers everything below. Applying is a merge of saved changes into the current ones, and Git refuses when the same file is involved on both sides. Pop is 'apply, and only if that worked, drop', which is why a conflicting pop leaves the entry in place.",
        hints=[
            "Insert new entries at the front of a list so that list index equals stash number.",
            "Check for a missing entry first, then for overlap, and only then change any state.",
            "After `push`, create a *new* empty dict for `dirty`; do not `clear()` the one you just saved.",
        ],
        brute_force="Appending to the end of the list and treating index n as position n (first wrong solution) reverses the numbering. Skipping the overlap check (second wrong solution) silently overwrites local edits, which Git never does.",
        approach="A loop with one branch per operation, mutating `dirty`, `stack` and `errors`.\n\n**Dry run** of the example: edit a; push → stack [wip a], clean. edit b; push → stack [wip b, wip a], clean. `pop 1` → entry 1 is `wip a` saving {a: 1}; no overlap with the empty dirty set; dirty = {a: 1}; entry removed; stack [wip b].",
        complexity="Time O(total paths handled) with O(k) list shifts for a stack of k entries; space proportional to the saved changes.",
        pitfalls="Clearing the saved dict by aliasing. Dropping the entry even when the apply failed. Reporting `conflict` before `no such stash`.",
        follow_up="Real stashes are commits: `git stash show -p stash@{0}`, `git stash branch <name>` to turn one into a branch, `git stash -u` to include untracked files, and `--index` to restore what was staged.",
    ),
),
]
