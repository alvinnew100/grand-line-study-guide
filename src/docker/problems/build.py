_REORDER_CHECK = '''
def check(args, got, expected):
    steps, builds = args
    ids = [s[0] for s in steps]
    if not isinstance(got, list) or sorted(got) != sorted(ids):
        return False
    pos = {sid: i for i, sid in enumerate(got)}
    for sid, cost, deps in steps:
        for d in deps:
            if pos[d] > pos[sid]:
                return False
    cost_of = {s[0]: s[1] for s in steps}
    def total(order):
        p = {sid: i for i, sid in enumerate(order)}
        t = 0
        for changed in builds:
            if not changed:
                continue
            first = min(p[c] for c in changed)
            t += sum(cost_of[s] for s in order[first:])
        return t
    return total(got) == total(expected)
'''

PROBLEMS = [
dict(
    id="docker-cmd-entrypoint",
    title="Resolve CMD and ENTRYPOINT",
    difficulty="Medium",
    pattern="Building Images",
    entry="resolveCommand",
    description=r"""
Work out the exact argument list a container starts with. Write
`resolveCommand(entrypoint, cmd, run_args, entrypoint_override)`.

- `entrypoint` and `cmd` are the image's `ENTRYPOINT` and `CMD`. Each is a **list of strings** (exec form),
  a **string** (shell form) or `None` (not set).
- `run_args` is the list of arguments written after the image name in `docker run` (possibly empty).
- `entrypoint_override` is the value of `docker run --entrypoint X` (a single program name), or `None`.

Rules:

1. A shell-form value `s` becomes the list `["/bin/sh", "-c", s]`.
2. **Effective entrypoint.** If `entrypoint_override` is given, the entrypoint is `[entrypoint_override]` and the
   image's `CMD` is discarded (treated as `None`). Otherwise it is the image's entrypoint.
3. **Effective command.** `run_args` if it is non-empty, otherwise the image's `CMD` (after rule 2).
4. If the effective entrypoint came from a **shell-form** `ENTRYPOINT`, the result is that entrypoint alone:
   the command and `run_args` are ignored.
5. Otherwise the result is entrypoint followed by command (a missing part contributes nothing).

Return the final list (possibly `[]`).

**Example 1:** `(["pagecount"], ["serve"], [], None)` → `["pagecount", "serve"]`

**Example 2:** `(["pagecount"], ["serve"], ["migrate", "--dry-run"], None)` → `["pagecount", "migrate", "--dry-run"]`

**Example 3:** `("pagecount serve", ["x"], ["y"], None)` → `["/bin/sh", "-c", "pagecount serve"]`
""",
    starter='''def resolveCommand(entrypoint, cmd, run_args, entrypoint_override):
    pass
''',
    solution='''def resolveCommand(entrypoint, cmd, run_args, entrypoint_override):
    def norm(v):
        if v is None:
            return []
        if isinstance(v, str):
            return ["/bin/sh", "-c", v]
        return list(v)

    shell_entry = False
    if entrypoint_override is not None:
        ep = [entrypoint_override]
        cmd = None
    else:
        ep = norm(entrypoint)
        shell_entry = isinstance(entrypoint, str)
    if shell_entry:
        return ep
    tail = list(run_args) if run_args else norm(cmd)
    return ep + tail
''',
    tests=[
        [["pagecount"], ["serve"], [], None],
        [["pagecount"], ["serve"], ["migrate", "--dry-run"], None],
        ["pagecount serve", ["x"], ["y"], None],
        [None, ["serve"], [], None],
        [None, ["serve"], ["--debug"], None],
        [None, "python app.py --port $PORT", [], None],
        [["tini", "--"], "python app.py", [], None],
        [["tini", "--"], "python app.py", ["sh"], None],
        [None, None, [], None],
        [["backup"], None, [], None],
        [["backup"], ["--full"], [], "sh"],
        [["backup"], ["--full"], ["-c", "ls"], "sh"],
        ["backup --full", ["ignored"], ["-l"], "ls"],
        [None, None, ["echo", "hi"], None],
        ["run-server", None, [], None],
    ],
    examples=3,
    wrong_solutions=[
        '''def resolveCommand(entrypoint, cmd, run_args, entrypoint_override):
    def norm(v):
        if v is None:
            return []
        if isinstance(v, str):
            return ["/bin/sh", "-c", v]
        return list(v)
    ep = [entrypoint_override] if entrypoint_override is not None else norm(entrypoint)
    return ep + norm(cmd) + list(run_args)
''',
        '''def resolveCommand(entrypoint, cmd, run_args, entrypoint_override):
    def norm(v):
        if v is None:
            return []
        if isinstance(v, str):
            return ["/bin/sh", "-c", v]
        return list(v)
    if entrypoint_override is not None:
        ep = [entrypoint_override]
    else:
        ep = norm(entrypoint)
        if isinstance(entrypoint, str):
            return ep
    tail = list(run_args) if run_args else norm(cmd)
    return ep + tail
''',
    ],
    guide=dict(
        prereqs="Lesson *Dockerfile instructions, one by one* (shell form vs exec form, CMD vs ENTRYPOINT).",
        intuition="ENTRYPOINT is the fixed front of the command line; CMD is a default tail that `docker run` arguments **replace**. "
                  "Two special cases bend that: a shell-form ENTRYPOINT swallows everything, and `--entrypoint` wipes the image's CMD.",
        hints=[
            "Write a helper that turns `None`, a string or a list into a list.",
            "Decide the tail first: `run_args` if any, else CMD. Arguments never *append* to CMD.",
            "Remember whether the entrypoint was a string **before** you normalise it; an override is never shell form.",
        ],
        brute_force="Enumerating every combination in an if-ladder (2 override states x 3 entrypoint forms x 3 cmd forms x 2 argument states = 36 branches) works and is unreadable.",
        approach="1. If overridden: `ep = [override]`, forget CMD. Else `ep = norm(entrypoint)` and note shell form.\n"
                 "2. Shell-form entrypoint → return `ep`.\n3. `tail = run_args or norm(cmd)`.\n4. Return `ep + tail`.\n\n"
                 "**Dry run** `(['backup'], ['--full'], ['-c', 'ls'], 'sh')`: override → `ep = ['sh']`, CMD dropped. Not shell form. "
                 "`run_args` non-empty → tail `['-c', 'ls']`. Result `['sh', '-c', 'ls']`.",
        complexity="Time and space O(k) in the total number of arguments.",
        pitfalls="- Appending run arguments after CMD instead of replacing it.\n- Keeping the image CMD when `--entrypoint` is used.\n"
                 "- Wrapping an exec-form list in `/bin/sh -c`.\n- Forgetting that shell-form CMD under an exec-form ENTRYPOINT becomes "
                 "`entrypoint /bin/sh -c ...`, which is rarely what the author wanted.",
        follow_up="Model a child image that sets ENTRYPOINT (which resets an inherited CMD).",
    ),
),
dict(
    id="docker-cache-invalidation",
    title="Which Build Steps Are Rebuilt?",
    difficulty="Easy",
    pattern="Build Cache",
    entry="rebuiltSteps",
    description=r"""
Predict the build cache. Write `rebuiltSteps(steps, changed_files, changed_args)` returning the sorted list of
step indices (0-based) that must be executed again.

`steps` is a single-stage Dockerfile as a list of `[kind, value]`:

| kind | value | invalidated when |
|---|---|---|
| `"FROM"` | image name | never (the base did not change) |
| `"COPY"` | list of sources | at least one path in `changed_files` matches a source |
| `"ARG"` | argument name | the name is in `changed_args` |
| `"RUN"`, `"ENV"`, `"CMD"`, any other kind | text | never by itself |

A changed path matches a COPY source when the source is `"."` (everything), or equals the path exactly, or the
source ends with `/` and the path starts with the source (a directory).

**Rule:** find the first step that is invalidated. That step and **every step after it** are rebuilt. If no step is
invalidated, nothing is rebuilt.

**Example:** steps `[["FROM","python:3.12"], ["COPY",["requirements.txt"]], ["RUN","pip install -r requirements.txt"], ["COPY",["src/"]], ["CMD","python -m app"]]`,
`changed_files = ["src/app.py"]`, `changed_args = []` → `[3, 4]`
""",
    starter='''def rebuiltSteps(steps, changed_files, changed_args):
    pass
''',
    solution='''def rebuiltSteps(steps, changed_files, changed_args):
    def matches(src, path):
        return src == "." or src == path or (src.endswith("/") and path.startswith(src))

    args = set(changed_args)
    for i, (kind, value) in enumerate(steps):
        hit = False
        if kind == "COPY":
            hit = any(matches(s, p) for s in value for p in changed_files)
        elif kind == "ARG":
            hit = value in args
        if hit:
            return list(range(i, len(steps)))
    return []
''',
    tests=[
        [[["FROM", "python:3.12"], ["COPY", ["requirements.txt"]], ["RUN", "pip install -r requirements.txt"], ["COPY", ["src/"]], ["CMD", "python -m app"]], ["src/app.py"], []],
        [[["FROM", "python:3.12"], ["COPY", ["requirements.txt"]], ["RUN", "pip install -r requirements.txt"], ["COPY", ["src/"]], ["CMD", "python -m app"]], ["requirements.txt"], []],
        [[["FROM", "python:3.12"], ["COPY", ["requirements.txt"]], ["RUN", "pip install"], ["COPY", ["src/"]]], ["README.md"], []],
        [[["FROM", "node:22"], ["COPY", ["."]], ["RUN", "npm ci"]], ["README.md"], []],
        [[["FROM", "node:22"], ["COPY", ["."]], ["RUN", "npm ci"]], [], []],
        [[], ["a"], ["B"]],
        [[["FROM", "a"], ["RUN", "x"], ["ARG", "SHA"], ["RUN", "echo $SHA"], ["CMD", "run"]], [], ["SHA"]],
        [[["FROM", "a"], ["ARG", "SHA"], ["COPY", ["src/"]], ["RUN", "build"]], ["src/x"], ["OTHER"]],
        [[["FROM", "a"], ["COPY", ["src/"]], ["RUN", "build"]], ["src2/x", "srcfile"], []],
        [[["FROM", "a"], ["COPY", ["src"]], ["RUN", "build"]], ["src/x"], []],
        [[["FROM", "a"], ["COPY", ["a.txt", "conf/"]], ["RUN", "r"], ["COPY", ["b.txt"]]], ["b.txt", "conf/app.ini"], []],
        [[["FROM", "a"], ["ARG", "V"], ["COPY", ["x"]], ["ARG", "W"], ["RUN", "r"]], ["x"], ["W"]],
        [[["FROM", "a"]] + [["RUN", "step %d" % i] for i in range(50)] + [["COPY", ["late.txt"]], ["RUN", "end"]], ["late.txt"], []],
    ],
    examples=2,
    wrong_solutions=[
        '''def rebuiltSteps(steps, changed_files, changed_args):
    out = []
    for i, (kind, value) in enumerate(steps):
        if kind == "COPY" and any(s == "." or s == p or (s.endswith("/") and p.startswith(s)) for s in value for p in changed_files):
            out.append(i)
        elif kind == "ARG" and value in changed_args:
            out.append(i)
    return out
''',
        '''def rebuiltSteps(steps, changed_files, changed_args):
    for i, (kind, value) in enumerate(steps):
        if kind == "COPY" and any(s == "." or p.startswith(s) for s in value for p in changed_files):
            return list(range(i, len(steps)))
        if kind == "ARG" and value in changed_args:
            return list(range(i, len(steps)))
    return []
''',
    ],
    guide=dict(
        prereqs="Lesson *Layers, the build cache, the context and .dockerignore*.",
        intuition="Each step is built on top of the previous one. Once one step's input changes, its result is new, so every later "
                  "step has a new parent and cannot be reused. You only need to find the **first** miss.",
        hints=[
            "Scan the steps in order and stop at the first invalidated one.",
            "Only `COPY` and `ARG` can start a miss in this model; write the path-matching rule as a small helper.",
            "The answer is always either `[]` or `range(first, len(steps))`.",
        ],
        brute_force="Check every step independently and return those that are directly invalidated. This misses the cascade: an unchanged `RUN` after a changed `COPY` still reruns.",
        approach="Loop with `enumerate`. For `COPY`, test every (source, changed path) pair with the three matching rules. For `ARG`, test set membership. "
                 "On the first hit return the tail range.\n\n**Dry run** (example): step 0 FROM never. Step 1 COPY `requirements.txt` vs `src/app.py` → no. "
                 "Step 2 RUN never. Step 3 COPY `src/`: ends with `/` and `src/app.py` starts with it → hit at 3 → `[3, 4]`.",
        complexity="Time O(S x F x C) worst case (steps x changed files x sources per COPY); space O(S) for the output.",
        pitfalls="- Returning only directly changed steps.\n- Prefix matching without the trailing slash: source `src` must not match `src/x` or `src2/x` under these rules.\n"
                 "- Forgetting `.`.\n- Treating a changed ARG that is declared *before* the first COPY as harmless.",
        follow_up="Extend to multi-stage files where a miss in one stage invalidates `COPY --from` steps in later stages.",
    ),
),
dict(
    id="docker-reorder-instructions",
    title="Reorder Instructions for Cache Hits",
    difficulty="Hard",
    pattern="Build Cache",
    entry="reorderSteps",
    checker=_REORDER_CHECK,
    description=r"""
Given the history of what changed in past builds, order a Dockerfile's instructions so that the least work is redone.

`reorderSteps(steps, builds)`:

- `steps` is a list of `[id, cost, deps]`: a unique string id, the seconds it takes to execute, and the list of ids
  that **must appear before** it (for example the `COPY` a `RUN` needs). There are at most 12 steps and no cycles.
- `builds` is a list of past builds; each is the list of step ids whose input changed in that build (possibly empty).

For a given order, the cost of one build is the total `cost` of the first changed step **and every step after it**
in the order (the cache cascade). A build with no changed step costs 0. The total cost is the sum over all builds.

Return **any** order (a list of all ids) that respects every dependency and has the **minimum possible total cost**.

**Example:** steps `[["src", 1, []], ["deps", 1, []], ["install", 40, ["deps"]]]`,
builds `[["src"], ["src"], ["src"], ["deps"]]` → `["deps", "install", "src"]`
(total 3x1 + 42 = 45; the original order would cost 3x42 + 41 = 167).
""",
    starter='''def reorderSteps(steps, builds):
    pass
''',
    solution='''def reorderSteps(steps, builds):
    n = len(steps)
    if n == 0:
        return []
    idx = {s[0]: i for i, s in enumerate(steps)}
    cost = [s[1] for s in steps]
    need = [0] * n
    for i, s in enumerate(steps):
        for d in s[2]:
            need[i] |= 1 << idx[d]
    bmasks = []
    for b in builds:
        m = 0
        for sid in b:
            m |= 1 << idx[sid]
        if m:
            bmasks.append(m)
    full = (1 << n) - 1
    INF = float("inf")
    dp = [INF] * (full + 1)
    choice = [-1] * (full + 1)
    dp[0] = 0
    for mask in range(1, full + 1):
        hit = sum(1 for m in bmasks if m & mask)
        for i in range(n):
            bit = 1 << i
            if mask & bit:
                prev = mask ^ bit
                if dp[prev] < INF and (need[i] & prev) == need[i]:
                    c = dp[prev] + cost[i] * hit
                    if c < dp[mask]:
                        dp[mask] = c
                        choice[mask] = i
    order, mask = [], full
    while mask:
        i = choice[mask]
        order.append(steps[i][0])
        mask ^= 1 << i
    return order[::-1]
''',
    tests=[
        [[["src", 1, []], ["deps", 1, []], ["install", 40, ["deps"]]], [["src"], ["src"], ["src"], ["deps"]]],
        [[], []],
        [[["a", 5, []]], [["a"], []]],
        [[["a", 5, []], ["b", 7, ["a"]], ["c", 2, ["b"]]], [["c"], ["a"]]],
        [[["x", 10, []], ["y", 10, []]], []],
        [[["x", 10, []], ["y", 1, []]], [["x"], ["y"]]],
        [[["apt", 60, []], ["manifest", 1, []], ["pip", 45, ["manifest"]], ["code", 2, []], ["sha", 1, []]],
         [["code"], ["code", "sha"], ["sha"], ["manifest", "code"], ["code"], ["sha"]]],
        [[["a", 3, []], ["b", 3, []], ["c", 3, []], ["d", 3, []]], [["a"], ["a"], ["b"], ["c"], ["c"], ["c"], ["d"]]],
        [[["base", 30, []], ["cfg", 1, ["base"]], ["build", 50, ["cfg"]], ["assets", 20, []], ["label", 1, []]],
         [["cfg"], ["assets"], ["assets"], ["label"], ["label"], ["label"]]],
        [[["s%d" % i, (i * 7) % 11 + 1, (["s%d" % (i - 3)] if i >= 3 else [])] for i in range(12)],
         [["s%d" % ((j * 5) % 12), "s%d" % ((j * 3 + 1) % 12)] for j in range(15)]],
        [[["a", 1, []], ["b", 100, []]], [["a", "b"]]],
        [[["heavy", 90, []], ["light", 1, ["heavy"]]], [["heavy"]] * 5],
    ],
    examples=1,
    wrong_solutions=[
        '''def reorderSteps(steps, builds):
    return [s[0] for s in steps]
''',
        '''def reorderSteps(steps, builds):
    count = {s[0]: 0 for s in steps}
    for b in builds:
        for sid in b:
            count[sid] += 1
    return [s[0] for s in sorted(steps, key=lambda s: count[s[0]])]
''',
        '''def reorderSteps(steps, builds):
    count = {s[0]: 0 for s in steps}
    for b in builds:
        for sid in b:
            count[sid] += 1
    placed, order, left = set(), [], list(steps)
    while left:
        ready = [s for s in left if all(d in placed for d in s[2])]
        pick = min(ready, key=lambda s: (count[s[0]], -s[1]))
        order.append(pick[0]); placed.add(pick[0]); left.remove(pick)
    return order
''',
    ],
    guide=dict(
        prereqs="Lesson *Layers, the build cache*. Bitmask dynamic programming over subsets; topological constraints.",
        intuition="Rewrite the cost per **step** instead of per build: a step is re-executed in every build that changed something "
                  "placed **at or before** it. So the cost of putting step `s` right after a set `P` of earlier steps depends only on the *set* "
                  "`P ∪ {s}`, not on the order inside `P`. That is exactly the shape subset DP needs.",
        hints=[
            "Stable things first, volatile things last is the right instinct, but a greedy on change frequency ignores costs and dependencies.",
            "Represent a set of already placed steps as a bitmask. `hit(mask)` = number of builds whose changed set intersects `mask`.",
            "`dp[mask] = min over s in mask, deps(s) ⊆ mask - s, of dp[mask - s] + cost[s] * hit(mask)`; remember the choice to rebuild the order.",
        ],
        brute_force="Try all `n!` permutations, discard those that violate a dependency, and evaluate each in O(n x builds). 12! is 479 million: too slow, "
                    "but fine for n up to 8 and a good way to test the DP.",
        approach="1. Index the ids; turn each step's deps and each build into bitmasks.\n2. Fill `dp` for masks 1 to 2^n - 1; the last element of the prefix "
                 "is the step being placed.\n3. Walk `choice` back from the full mask and reverse.\n\n**Dry run** (example): builds masks: src x3, deps x1. "
                 "Placing `deps` first: hit({deps}) = 1 → cost 1. Then `install`: hit({deps, install}) = 1 → +40. Then `src`: hit(all) = 4 → +4. "
                 "Total 45. Starting with `src` gives hit = 3 for the first step and 4 for both others: 3 + 4 + 160 = 167.",
        complexity="Time O(2^n x (n + B)) for n steps and B builds, about 4096 x (12 + B) here. Space O(2^n).",
        pitfalls="- Sorting by change count alone breaks dependencies and ignores cost.\n- Counting a build once per changed step instead of once per build.\n"
                 "- Forgetting empty builds (cost 0).\n- Returning ids in reverse after backtracking.",
        follow_up="When builds are probabilistic instead of a fixed history, the same DP works with expected hit counts.",
    ),
),
dict(
    id="docker-dockerignore",
    title="Match .dockerignore Patterns",
    difficulty="Hard",
    pattern="Build Context",
    entry="isIgnored",
    description=r"""
Decide which files are left out of the build context. Write `isIgnored(patterns, paths)` returning a list of booleans,
one per path (`True` = excluded).

`patterns` are the lines of a `.dockerignore` file; `paths` are relative file paths using `/` (no leading `/`).

**Preparing a line:** strip surrounding spaces. Skip it if it is empty or starts with `#`. If it starts with `!` it
is an *exception*; remove the `!`. Then remove any leading and trailing `/`.

**Matching a pattern against a path:** split both on `/` into segments.

- A pattern segment `**` matches **zero or more** whole path segments.
- Any other pattern segment must match exactly one path segment, where `*` matches any run of characters
  (possibly empty) and `?` matches exactly one character. Neither crosses a `/`.

A pattern *applies* to a path if it matches the whole path **or any ancestor directory of it**
(so `build` applies to `build/out/app.js`).

**Deciding:** go through the lines in order. Each line that applies sets the state: excluded for a normal line,
included for an exception. The **last applying line wins**. A path no line applies to is included.

**Example:** patterns `["*.md", "!README.md", "node_modules", "**/*.log"]`,
paths `["README.md", "CHANGES.md", "docs/guide.md", "node_modules/x/index.js", "a/b/app.log"]`
→ `[False, True, False, True, True]`
""",
    starter='''def isIgnored(patterns, paths):
    pass
''',
    solution='''def isIgnored(patterns, paths):
    def seg_match(pat, text):
        # '*' = any run, '?' = one char; iterative wildcard match
        p = t = 0
        star = -1
        mark = 0
        while t < len(text):
            if p < len(pat) and (pat[p] == "?" or pat[p] == text[t]) and pat[p] != "*":
                p += 1; t += 1
            elif p < len(pat) and pat[p] == "*":
                star = p; mark = t; p += 1
            elif star != -1:
                p = star + 1; mark += 1; t = mark
            else:
                return False
        while p < len(pat) and pat[p] == "*":
            p += 1
        return p == len(pat)

    def match(pat, segs):
        memo = {}
        def go(i, j):
            if (i, j) in memo:
                return memo[(i, j)]
            if i == len(pat):
                r = j == len(segs)
            elif pat[i] == "**":
                r = go(i + 1, j) or (j < len(segs) and go(i, j + 1))
            else:
                r = j < len(segs) and seg_match(pat[i], segs[j]) and go(i + 1, j + 1)
            memo[(i, j)] = r
            return r
        return go(0, 0)

    rules = []
    for line in patterns:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        neg = line.startswith("!")
        if neg:
            line = line[1:]
        line = line.strip("/")
        if line:
            rules.append((neg, line.split("/")))
    out = []
    for path in paths:
        segs = path.split("/")
        ignored = False
        for neg, pat in rules:
            if any(match(pat, segs[:k]) for k in range(1, len(segs) + 1)):
                ignored = not neg
        out.append(ignored)
    return out
''',
    tests=[
        [["*.md", "!README.md", "node_modules", "**/*.log"], ["README.md", "CHANGES.md", "docs/guide.md", "node_modules/x/index.js", "a/b/app.log"]],
        [[], ["a.txt"]],
        [["# comment", "", "   ", "*.pyc"], ["a.pyc", "pkg/a.pyc", "#comment"]],
        [["**/*.pyc"], ["a.pyc", "pkg/a.pyc", "pkg/sub/a.pyc", "a.pyc.bak"]],
        [["!README.md", "*.md"], ["README.md"]],
        [["/build/", "dist"], ["build/out.js", "src/build/out.js", "dist", "distribution/x"]],
        [["**/tmp"], ["tmp", "a/tmp", "a/tmp/b.txt", "a/tmpfile"]],
        [["docs/*.md"], ["docs/a.md", "docs/sub/a.md", "a.md"]],
        [["file?.txt"], ["file1.txt", "file10.txt", "file.txt", "x/file1.txt"]],
        [["*", "!src", "!requirements.txt"], ["src/app.py", "requirements.txt", "README.md", "tests/t.py"]],
        [["secrets", "!secrets/public.pem"], ["secrets/key.pem", "secrets/public.pem"]],
        [["a/**/z"], ["a/z", "a/b/z", "a/b/c/z", "a/b/c/y", "b/a/z"]],
        [["*.env*", "!.env.example"], [".env", ".env.local", ".env.example", "prod.env", "env"]],
        [["**"], ["x", "a/b"]],
        [["a*b*c"], ["abc", "aXbYc", "ac", "abcd", "aabbcc"]],
    ],
    examples=1,
    wrong_solutions=[
        '''import fnmatch

def isIgnored(patterns, paths):
    out = []
    for path in paths:
        ignored = False
        for line in patterns:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            neg = line.startswith("!")
            if neg:
                line = line[1:]
            if fnmatch.fnmatchcase(path, line.strip("/")):
                ignored = not neg
        out.append(ignored)
    return out
''',
        '''def isIgnored(patterns, paths):
    import fnmatch
    out = []
    for path in paths:
        segs = path.split("/")
        ignored = False
        for line in patterns:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            neg = line.startswith("!")
            if neg:
                line = line[1:]
            pat = line.strip("/").split("/")
            for k in range(1, len(segs) + 1):
                if len(pat) == k and all(fnmatch.fnmatchcase(s, p) for s, p in zip(segs[:k], pat)):
                    if not ignored or neg:
                        ignored = not neg
                    break
        out.append(ignored)
    return out
''',
    ],
    guide=dict(
        prereqs="Lesson *Layers, the build cache, the context and .dockerignore*. Recursion with memoisation; wildcard matching.",
        intuition="Solve it at two levels. Inside one path segment you need a classic `*`/`?` wildcard match. Across segments you need a second "
                  "match where `**` can absorb any number of whole segments. Then apply 'last match wins' over the list of rules, testing each rule against "
                  "the path and each of its parent directories.",
        hints=[
            "Pre-process every line into `(is_exception, list_of_segments)` once.",
            "For `**`, recurse two ways: use it for zero segments (`go(i+1, j)`) or let it eat one segment and stay (`go(i, j+1)`).",
            "A rule applies if it matches `segs[:k]` for some `k` from 1 to `len(segs)`; do not stop at the first applying rule, keep overwriting the state.",
        ],
        brute_force="Convert each pattern to one regular expression over the whole path. It works if you translate `*` to `[^/]*`, `?` to `[^/]` and `**/` carefully, "
                    "but `fnmatch` on the full string is wrong because its `*` crosses `/`.",
        approach="1. Parse rules.\n2. `seg_match` for one segment.\n3. `match(pattern_segments, path_segments)` with memoised recursion.\n"
                 "4. For each path, loop over rules in order and every prefix of the path.\n\n**Dry run** `docs/guide.md` with `*.md`: prefixes are `[docs]` and "
                 "`[docs, guide.md]`. Pattern has one segment. `*.md` vs `docs` → no. Against two segments → length mismatch. Not applied, so the file is kept. "
                 "`**/*.log` vs `a/b/app.log`: `**` eats `a`, `b`; `*.log` matches `app.log` → excluded.",
        complexity="Time O(P x R x D x (D x S + W)) in the worst case (paths, rules, depth, segment matching), tiny for real ignore files. Space O(D^2) for the memo.",
        pitfalls="- Letting `*` match across `/`.\n- First match wins instead of last.\n- Forgetting that excluding a directory excludes its contents.\n"
                 "- Treating `**` as needing at least one segment (`**/*.pyc` must match `a.pyc`).\n- Not stripping the leading `/`.",
        follow_up="Real Docker has one more optimisation: it cannot re-include a file whose parent directory is excluded unless patterns say so explicitly. Compare with `.gitignore`, where the rules differ.",
    ),
),
dict(
    id="docker-lint-dockerfile",
    title="Lint a Dockerfile",
    difficulty="Medium",
    pattern="Building Images",
    entry="lintDockerfile",
    description=r"""
Write a tiny linter. `lintDockerfile(lines)` receives the lines of a Dockerfile (each instruction is on one line;
there are no line continuations) and returns a list of `[line_number, rule]` findings, sorted by line number and then
by rule name. Line numbers start at 1.

Ignore blank lines and lines whose first non-space character is `#`. The instruction keyword is the first word and is
case-insensitive; the rest of the line (stripped) is its argument text.

| Rule | Report on the line when |
|---|---|
| `pin-base` | `FROM` whose image (first word after `FROM`) is not `scratch`, is not the name of a stage declared earlier with `AS`, has no `@`, and either has no tag or has the tag `latest`. (A tag is a `:` in the part after the last `/`.) |
| `use-copy` | `ADD` whose first source does not start with `http://` or `https://` and does not end with `.tar`, `.tar.gz` or `.tgz`. |
| `apt-clean` | `RUN` containing `apt-get install` but not containing `rm -rf /var/lib/apt/lists`. |
| `exec-form` | `CMD` or `ENTRYPOINT` whose argument text does not start with `[`. |
| `no-cd` | `RUN` whose argument text starts with `cd `. |
| `run-as-root` | Reported once, on the line of the **last** `FROM`: after that line there is no `USER` instruction, or the last `USER` after it is `root` or `0` (optionally followed by `:group`). Not reported if there is no `FROM` at all. |

**Example:** `["FROM python", "RUN cd /app", "CMD python app.py"]` →
`[[1, "pin-base"], [1, "run-as-root"], [2, "no-cd"], [3, "exec-form"]]`
""",
    starter='''def lintDockerfile(lines):
    pass
''',
    solution='''def lintDockerfile(lines):
    findings = []
    stages = set()
    last_from = None
    last_user = None
    for no, raw in enumerate(lines, start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(None, 1)
        kw = parts[0].upper()
        arg = parts[1].strip() if len(parts) > 1 else ""
        words = arg.split()
        if kw == "FROM":
            image = words[0] if words else ""
            last_from, last_user = no, None
            if image != "scratch" and image not in stages and "@" not in image:
                tail = image.rsplit("/", 1)[-1]
                tag = tail.split(":", 1)[1] if ":" in tail else None
                if tag is None or tag == "latest":
                    findings.append([no, "pin-base"])
            up = [w.upper() for w in words]
            if "AS" in up and up.index("AS") + 1 < len(words):
                stages.add(words[up.index("AS") + 1])
        elif kw == "ADD":
            srcs = [w for w in words if not w.startswith("--")]
            src = srcs[0] if srcs else ""
            if not src.startswith(("http://", "https://")) and not src.endswith((".tar", ".tar.gz", ".tgz")):
                findings.append([no, "use-copy"])
        elif kw == "RUN":
            if "apt-get install" in arg and "rm -rf /var/lib/apt/lists" not in arg:
                findings.append([no, "apt-clean"])
            if arg.startswith("cd "):
                findings.append([no, "no-cd"])
        elif kw in ("CMD", "ENTRYPOINT"):
            if not arg.startswith("["):
                findings.append([no, "exec-form"])
        elif kw == "USER":
            last_user = arg
    if last_from is not None:
        user = (last_user or "").split(":")[0]
        if last_user is None or user in ("root", "0"):
            findings.append([last_from, "run-as-root"])
    findings.sort()
    return findings
''',
    tests=[
        [["FROM python", "RUN cd /app", "CMD python app.py"]],
        [["FROM python:3.12-slim", "WORKDIR /app", "COPY . .", "USER 10001", "CMD [\"python\", \"app.py\"]"]],
        [[]],
        [["# only a comment", "", "   "]],
        [["FROM python:latest", "USER root"]],
        [["FROM golang:1.23 AS build", "RUN go build", "FROM scratch", "COPY --from=build /out /out", "USER 65532:65532", "ENTRYPOINT [\"/out\"]"]],
        [["FROM node:22 AS deps", "FROM deps", "USER node"]],
        [["from localhost:5000/base", "user 0:0"]],
        [["FROM ubuntu:24.04", "RUN apt-get update && apt-get install -y curl", "RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*", "USER app"]],
        [["FROM alpine:3.20", "ADD app.tar.gz /app", "ADD https://example.com/x.bin /x", "ADD config.yml /etc/", "ADD --chown=1:1 src /src", "USER 1"]],
        [["FROM python@sha256:abc", "USER app", "USER root", "ENTRYPOINT python -m app"]],
        [["FROM alpine:3.20 AS a", "USER app", "FROM alpine:3.20", "RUN cd /x && make"]],
        [["RUN cd /tmp", "CMD run"]],
        [["  FROM   registry.example.com:5000/team/app  ", "  USER   app  ", "CMD   [\"run\"]"]],
    ],
    examples=1,
    wrong_solutions=[
        '''def lintDockerfile(lines):
    f = []
    has_user = False
    last_from = None
    for no, raw in enumerate(lines, 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        kw, _, arg = line.partition(" ")
        kw, arg = kw.upper(), arg.strip()
        if kw == "FROM":
            last_from = no
            if ":" not in arg or arg.endswith(":latest"):
                f.append([no, "pin-base"])
        elif kw == "ADD":
            f.append([no, "use-copy"])
        elif kw == "RUN":
            if "apt-get install" in arg and "rm -rf /var/lib/apt/lists" not in arg:
                f.append([no, "apt-clean"])
            if arg.startswith("cd "):
                f.append([no, "no-cd"])
        elif kw in ("CMD", "ENTRYPOINT") and not arg.startswith("["):
            f.append([no, "exec-form"])
        elif kw == "USER":
            has_user = True
    if last_from and not has_user:
        f.append([last_from, "run-as-root"])
    return sorted(f)
''',
    ],
    guide=dict(
        prereqs="Lessons *Dockerfile instructions, one by one* and *Container security*. String splitting; keeping small pieces of state while scanning.",
        intuition="A linter is a loop over lines plus a little memory. Most rules look at one line. Two need memory: `pin-base` must remember stage "
                  "names, and `run-as-root` can only be decided after the whole file is read, because it concerns the final stage.",
        hints=[
            "`line.split(None, 1)` separates the keyword from the rest whatever the spacing.",
            "For `pin-base`, look for the tag colon only after the last `/`, so a registry port such as `localhost:5000/base` is not mistaken for a tag.",
            "Reset `last_user` every time you see `FROM`; after the loop, judge the value left over.",
        ],
        brute_force="Six separate passes over the file, one per rule. Equally correct and O(6n); the single pass is tidier.",
        approach="Keep `stages` (set), `last_from`, `last_user`. Per line: normalise, dispatch on keyword, append findings. After the loop add `run-as-root` if needed, then sort.\n\n"
                 "**Dry run** `['FROM python', 'RUN cd /app', 'CMD python app.py']`: line 1 image `python` has no tag → `pin-base`; `last_from = 1`. "
                 "Line 2 starts with `cd ` → `no-cd`. Line 3 not `[` → `exec-form`. No USER after line 1 → `[1, 'run-as-root']`. Sorted output as in the example.",
        complexity="Time O(total characters), space O(findings + stages).",
        pitfalls="- A registry port read as a tag.\n- Flagging `FROM build` when `build` is an earlier stage, or `FROM scratch`.\n- Counting a `USER` from an earlier stage.\n"
                 "- `USER 0:0` is still root.\n- Skipping flags such as `--chown=` when finding the first `ADD` source.",
        follow_up="Add a rule for `COPY . .` appearing before a dependency install, or support backslash line continuations.",
    ),
),
]
