"""Git track problems, part 2: the commit graph (a DAG given as {commit: [parents]})."""

# A small history used by several tests:
#
#   A - B - C - E - M      (main)
#        \         /
#         D ----- F        (feature, merged at M)        G hangs off E, H off F
G1 = {"A": [], "B": ["A"], "C": ["B"], "D": ["B"], "E": ["C"], "F": ["D"], "M": ["E", "F"], "G": ["E"], "H": ["F"]}
# criss-cross: X merges (P, Q) and Y merges (Q, P)
CRISS = {"R": [], "P": ["R"], "Q": ["R"], "X": ["P", "Q"], "Y": ["Q", "P"], "X2": ["X"], "Y2": ["Y"]}
LINE = {"c0": []}
for _i in range(1, 30):
    LINE["c%d" % _i] = ["c%d" % (_i - 1)]
DEEP = {"n0": []}
for _i in range(1, 5000):
    DEEP["n%d" % _i] = ["n%d" % (_i - 1)]
TWO_ROOTS = {"a1": [], "a2": ["a1"], "b1": [], "b2": ["b1"], "j": ["a2", "b2"]}
OCTO = {"r": [], "x": ["r"], "y": ["r"], "z": ["r"], "o": ["x", "y", "z"], "t": ["o"]}

ANC_HELPER = '''
def _anc(parents, x):
    seen = {x}
    stack = [x]
    while stack:
        c = stack.pop()
        for p in parents.get(c, []):
            if p not in seen:
                seen.add(p)
                stack.append(p)
    return seen
'''

DATED = {
    "A": {"date": 10, "parents": []},
    "B": {"date": 20, "parents": ["A"]},
    "C": {"date": 30, "parents": ["B"]},
    "D": {"date": 25, "parents": ["B"]},
    "E": {"date": 40, "parents": ["C"]},
    "F": {"date": 45, "parents": ["D"]},
    "M": {"date": 50, "parents": ["E", "F"]},
}
SKEW = {
    "A": {"date": 100, "parents": []},
    "B": {"date": 90, "parents": ["A"]},      # clock was wrong: child older than parent
    "C": {"date": 95, "parents": ["B"]},
    "D": {"date": 300, "parents": ["A"]},
    "M": {"date": 200, "parents": ["C", "D"]},
}
TIES = {
    "r": {"date": 1, "parents": []},
    "b": {"date": 5, "parents": ["r"]},
    "a": {"date": 5, "parents": ["r"]},
    "c": {"date": 5, "parents": ["r"]},
    "m": {"date": 9, "parents": ["c", "a", "b"]},
}
DLINE = {"k%03d" % i: {"date": 7, "parents": (["k%03d" % (i + 1)] if i < 199 else [])} for i in range(200)}

PROBLEMS = [
dict(
    id="git-is-ancestor",
    title="Can this branch fast-forward?",
    difficulty="Easy",
    pattern="Graph traversal",
    entry="can_fast_forward",
    description=r"""
A history is given as a dict `parents` mapping every commit id to the list of its parent ids (empty
list for a root commit). A branch pointing at `current` can be **fast-forwarded** to `target` exactly
when `current` is an ancestor of `target`: you can reach `current` from `target` by following parent
links zero or more times. (Zero links means a commit counts as its own ancestor.)

Write `can_fast_forward(parents, current, target)` returning `True` or `False`.

Histories may be thousands of commits deep, so a recursive walk will overflow the stack.

**Example:** with `A <- B <- C` (`{"A": [], "B": ["A"], "C": ["B"]}`), `can_fast_forward(p, "A", "C")` → `True`
and `can_fast_forward(p, "C", "A")` → `False`.
""",
    starter='''def can_fast_forward(parents, current, target):
    pass
''',
    solution='''def can_fast_forward(parents, current, target):
    seen = {target}
    stack = [target]
    while stack:
        c = stack.pop()
        if c == current:
            return True
        for p in parents.get(c, []):
            if p not in seen:
                seen.add(p)
                stack.append(p)
    return False
''',
    tests=[
        [{"A": [], "B": ["A"], "C": ["B"]}, "A", "C"],
        [{"A": [], "B": ["A"], "C": ["B"]}, "C", "A"],
        [G1, "D", "M"],
        [G1, "M", "M"],
        [G1, "C", "F"],
        [G1, "G", "M"],
        [G1, "B", "H"],
        [G1, "E", "H"],
        [TWO_ROOTS, "b1", "j"],
        [TWO_ROOTS, "a1", "b2"],
        [DEEP, "n0", "n4999"],
        [DEEP, "n4999", "n0"],
        [CRISS, "P", "Y2"],
        [OCTO, "z", "t"],
    ],
    examples=2,
    wrong_solutions=[
        '''def can_fast_forward(parents, current, target):
    c = target
    while True:
        if c == current:
            return True
        if not parents.get(c):
            return False
        c = parents[c][0]
''',
        '''def can_fast_forward(parents, current, target):
    def walk(c):
        if c == current:
            return True
        return any(walk(p) for p in parents.get(c, []))
    try:
        return walk(target)
    except RecursionError:
        return False
''',
    ],
    guide=dict(
        prereqs="The branching lessons (fast-forward merges). Depth-first or breadth-first search with a visited set.",
        intuition="Commits only know their parents, so the natural direction to walk is backwards in time. Start at the newer commit (`target`) and explore everything reachable; if you bump into `current`, then `target` already contains all of `current`'s history and the branch label can simply slide forward.",
        hints=[
            "Which commit should the search start from? Parent links point from new to old.",
            "A merge commit has several parents. Following only the first one misses whole side branches.",
            "Use an explicit stack and a `seen` set; without the set, histories with many merges are revisited exponentially often.",
        ],
        brute_force="Recursive DFS without a visited set: correct on tiny inputs, but it re-explores shared history once per path (exponential with repeated merges) and dies with `RecursionError` on a long chain.",
        approach="Iterative DFS from `target`. Pop a commit; if it equals `current` return `True`; otherwise push its unseen parents. If the stack empties, return `False`.\n\n**Dry run** on the sample graph asking `D -> M`: stack `[M]`; pop M, push E and F; pop F, push D; pop D, equals current, return `True`. Asking `C -> F`: from F we see D, B, A and never C, so `False`: `main` at C and `feature` at F have diverged.",
        complexity="Time O(V + E) in the part of the graph reachable from `target`; space O(V) for the visited set.",
        pitfalls="Searching from `current` (you cannot walk towards children). Following only first parents. Forgetting the reflexive case `current == target`.",
        follow_up="`git merge-base --is-ancestor A B` answers exactly this with its exit status. Git speeds it up using commit dates/generation numbers to stop early.",
    ),
),
dict(
    id="git-merge-base",
    title="Find the merge base",
    difficulty="Medium",
    pattern="Graph traversal",
    entry="merge_base",
    description=r"""
The **merge base** of two commits is their best common ancestor: the point where the two lines of
history last agreed. A three-way merge compares both tips against it.

`parents` maps every commit id to its list of parent ids. A commit counts as its own ancestor.
A *common ancestor* of `a` and `b` is a commit that is an ancestor of both. A common ancestor is **best**
if it is not a (proper) ancestor of any other common ancestor.

Write `merge_base(parents, a, b)` returning the **sorted list** of all best common ancestors. Usually it
has one element; with unrelated histories it is empty; after a criss-cross merge it can have several.

**Example:** `main` is `A <- B <- C`, and `feature` forked at B: `A <- B <- D`.
`merge_base(p, "C", "D")` → `["B"]`

**Example:** `merge_base(p, "B", "D")` → `["B"]` (B is an ancestor of D, so the base is B itself)
""",
    starter='''def merge_base(parents, a, b):
    pass
''',
    solution=ANC_HELPER + '''
def merge_base(parents, a, b):
    common = _anc(parents, a) & _anc(parents, b)
    dominated = set()
    for c in common:
        dominated.update(parents.get(c, []))
    return sorted(common - dominated)
''',
    tests=[
        [{"A": [], "B": ["A"], "C": ["B"], "D": ["B"]}, "C", "D"],
        [{"A": [], "B": ["A"], "C": ["B"], "D": ["B"]}, "B", "D"],
        [G1, "E", "F"],
        [G1, "G", "H"],
        [G1, "M", "H"],
        [G1, "M", "G"],
        [G1, "A", "A"],
        [TWO_ROOTS, "a2", "b2"],
        [TWO_ROOTS, "j", "b2"],
        [CRISS, "X", "Y"],
        [CRISS, "X2", "Y2"],
        [CRISS, "X2", "Q"],
        [OCTO, "t", "y"],
        [DEEP, "n4999", "n1234"],
        [dict(LINE, s=["c10"], s2=["s"], t=["c20", "s"]), "s2", "t"],
    ],
    examples=2,
    wrong_solutions=[
        ANC_HELPER + '''
def merge_base(parents, a, b):
    return sorted(_anc(parents, a) & _anc(parents, b))
''',
        '''def merge_base(parents, a, b):
    seen = set()
    c = a
    while True:
        seen.add(c)
        if not parents.get(c):
            break
        c = parents[c][0]
    c = b
    while True:
        if c in seen:
            return [c]
        if not parents.get(c):
            return []
        c = parents[c][0]
''',
    ],
    guide=dict(
        prereqs="Problem *Can this branch fast-forward?* and the lesson on basic merging. Set operations.",
        intuition="Collect everything reachable from `a`, everything reachable from `b`, and intersect: those are the common ancestors. Most of them are uninteresting old history. The best ones are the 'newest layer' of that intersection, the common ancestors that no other common ancestor sits on top of.",
        hints=[
            "Reuse the reachability walk from the previous problem, but collect the whole visited set instead of stopping early.",
            "The set of common ancestors is closed: every parent of a common ancestor is itself a common ancestor.",
            "Because of that closure, a common ancestor is dominated exactly when it is the *parent* of some other common ancestor. Subtract all such parents.",
        ],
        brute_force="For every pair of common ancestors (x, y) run a reachability test to see whether x is an ancestor of y, and drop x if so. That is O(k^2) walks for k common ancestors, far too slow on a long shared history.",
        approach="1. `A = ancestors(a)`, `B = ancestors(b)`, `common = A & B`.\n2. `dominated = union of parents[c] for c in common`.\n3. Return `sorted(common - dominated)`.\n\n**Dry run** on the sample graph for `E` and `F`: ancestors(E) = {E, C, B, A}; ancestors(F) = {F, D, B, A}; common = {B, A}. Parents of B are {A}; parents of A are {}. dominated = {A}. Answer `['B']`. For the criss-cross graph and tips X, Y: common = {P, Q, R}, dominated = {R}, answer `['P', 'Q']`, which is why Git's default merge strategy first merges P and Q into a virtual base.",
        complexity="Time O(V + E) for the two walks and one pass over the common set; space O(V).",
        pitfalls="Returning all common ancestors. Walking only first parents (misses bases reached through a merge). Returning the *oldest* common ancestor (the root) instead of the newest.",
        follow_up="`git merge-base A B` prints one best base, `--all` prints every one. For more than two commits `git merge-base --octopus` intersects them all.",
    ),
),
dict(
    id="git-rev-range",
    title="Commits in the range A..B",
    difficulty="Easy",
    pattern="Graph traversal",
    entry="rev_range",
    description=r"""
The double-dot range `A..B` selects every commit that is **reachable from B but not reachable from A**
(a commit is reachable from itself). It answers "what does B have that A does not?", for example
`origin/main..HEAD` lists what you are about to push.

`parents` maps each commit id to its list of parent ids. Write `rev_range(parents, a, b)` returning the
selected commit ids as a **sorted list**.

**Example:** `main` is `A <- B <- C` and `topic` forked from B with commits `D <- E`.
`rev_range(p, "C", "E")` → `["D", "E"]` and `rev_range(p, "E", "C")` → `["C"]`.
""",
    starter='''def rev_range(parents, a, b):
    pass
''',
    solution=ANC_HELPER + '''
def rev_range(parents, a, b):
    return sorted(_anc(parents, b) - _anc(parents, a))
''',
    tests=[
        [{"A": [], "B": ["A"], "C": ["B"], "D": ["B"], "E": ["D"]}, "C", "E"],
        [{"A": [], "B": ["A"], "C": ["B"], "D": ["B"], "E": ["D"]}, "E", "C"],
        [G1, "E", "M"],
        [G1, "M", "E"],
        [G1, "G", "H"],
        [G1, "A", "M"],
        [G1, "M", "M"],
        [TWO_ROOTS, "a2", "b2"],
        [TWO_ROOTS, "a2", "j"],
        [CRISS, "X", "Y2"],
        [OCTO, "x", "t"],
        [DEEP, "n4990", "n4999"],
        [LINE, "c29", "c3"],
    ],
    examples=2,
    wrong_solutions=[
        ANC_HELPER + '''
def rev_range(parents, a, b):
    return sorted(_anc(parents, a) - _anc(parents, b))
''',
        '''def rev_range(parents, a, b):
    out = []
    c = b
    while c != a:
        out.append(c)
        if not parents.get(c):
            break
        c = parents[c][0]
    return sorted(out)
''',
    ],
    guide=dict(
        prereqs="Reachability on the commit graph (previous problems) and the lesson on revision selection.",
        intuition="Think of each commit as standing for the *set* of commits in its history. `A..B` is then nothing more than set subtraction: history of B minus history of A.",
        hints=[
            "Write a function that returns the set of all commits reachable from one commit.",
            "Call it twice. Which set do you subtract from which?",
            "The range is not symmetric and not 'the commits between A and B on a line': with a merge inside, it includes both sides of the merge.",
        ],
        brute_force="Walk from B and, for each commit met, run a fresh ancestor test against A. That costs a full traversal per commit, O(V * (V + E)).",
        approach="`sorted(ancestors(b) - ancestors(a))`.\n\n**Dry run** on the sample graph for `E..M`: ancestors(M) = {M, E, F, C, D, B, A}; ancestors(E) = {E, C, B, A}; difference = {M, F, D}: the merge commit plus the two feature commits it brought in.",
        complexity="Time O(V + E); space O(V).",
        pitfalls="Subtracting in the wrong direction. Walking a single parent chain from B until A is found: A might not be on that chain at all, and merges add commits off the chain.",
        follow_up="`A...B` (three dots) is the symmetric difference: commits reachable from exactly one side. `^A B` is another spelling of `A..B`, and you can exclude several tips at once.",
    ),
),
dict(
    id="git-log-order",
    title="git log order: topological with newest-first ties",
    difficulty="Medium",
    pattern="Topological sort + heap",
    entry="log_order",
    description=r"""
`git log --date-order` lists commits so that **no parent is shown before any of its children**, and
among the commits that are currently allowed to be shown it prefers the **newest** one.

`commits` maps each id to `{"date": int, "parents": [ids]}`. Starting from `start`, consider only commits
reachable from it. Produce the order by repeating:

- A commit is *ready* when every reachable commit that lists it as a parent has already been output
  (`start` is ready at the beginning).
- Output the ready commit with the **largest date**; break ties by the **smallest id** (string order).

Return the list of ids. Dates are not trustworthy: a child may carry an older date than its parent
(a wrong clock), and the parent must still come after the child.

**Example:** `A(10) <- B(20) <- C(30)`, `log_order(c, "C")` → `["C", "B", "A"]`
""",
    starter='''def log_order(commits, start):
    pass
''',
    solution='''import heapq

def log_order(commits, start):
    seen = {start}
    stack = [start]
    while stack:
        c = stack.pop()
        for p in commits[c]["parents"]:
            if p not in seen:
                seen.add(p)
                stack.append(p)
    pending = {c: 0 for c in seen}
    for c in seen:
        for p in commits[c]["parents"]:
            pending[p] += 1
    heap = [(-commits[start]["date"], start)]
    out = []
    while heap:
        _, c = heapq.heappop(heap)
        out.append(c)
        for p in commits[c]["parents"]:
            pending[p] -= 1
            if pending[p] == 0:
                heapq.heappush(heap, (-commits[p]["date"], p))
    return out
''',
    tests=[
        [{"A": {"date": 10, "parents": []}, "B": {"date": 20, "parents": ["A"]}, "C": {"date": 30, "parents": ["B"]}}, "C"],
        [DATED, "M"],
        [DATED, "F"],
        [DATED, "A"],
        [SKEW, "M"],
        [SKEW, "C"],
        [TIES, "m"],
        [DLINE, "k000"],
        [{"r": {"date": 5, "parents": []}, "x": {"date": 5, "parents": ["r"]}, "y": {"date": 5, "parents": ["r"]}, "z": {"date": 5, "parents": ["y", "x"]}}, "z"],
        [{"r1": {"date": 1, "parents": []}, "r2": {"date": 2, "parents": []}, "j": {"date": 3, "parents": ["r1", "r2"]}}, "j"],
        [{"a": {"date": 1, "parents": []}, "b": {"date": 2, "parents": ["a"]}, "c": {"date": 3, "parents": ["a"]}, "d": {"date": 4, "parents": ["b", "c"]}, "e": {"date": 0, "parents": ["d"]}, "f": {"date": 9, "parents": ["a"]}, "g": {"date": 8, "parents": ["e", "f"]}}, "g"],
    ],
    examples=2,
    wrong_solutions=[
        '''def log_order(commits, start):
    seen = {start}
    stack = [start]
    while stack:
        c = stack.pop()
        for p in commits[c]["parents"]:
            if p not in seen:
                seen.add(p)
                stack.append(p)
    return sorted(seen, key=lambda c: (-commits[c]["date"], c))
''',
        '''import heapq

def log_order(commits, start):
    heap = [(-commits[start]["date"], start)]
    seen = {start}
    out = []
    while heap:
        _, c = heapq.heappop(heap)
        out.append(c)
        for p in commits[c]["parents"]:
            if p not in seen:
                seen.add(p)
                heapq.heappush(heap, (-commits[p]["date"], p))
    return out
''',
    ],
    guide=dict(
        prereqs="The history-viewing lesson. Kahn's algorithm for topological sorting and Python's `heapq`.",
        intuition="This is Kahn's topological sort run 'backwards' (children before parents), with the usual queue swapped for a priority queue so that, whenever several commits are allowed next, the newest wins. The topological constraint guarantees sane output even when timestamps lie.",
        hints=[
            "First find the set of commits reachable from `start`; children outside that set must not count.",
            "For every reachable commit count how many reachable children it has. A commit becomes ready when that counter hits zero.",
            "Keep ready commits in a heap keyed by `(-date, id)` so the pop order is newest first, then smallest id.",
        ],
        brute_force="Repeatedly scan all remaining commits to find the ready ones and pick the best: O(V^2) or worse. Simply sorting by date is not a solution at all, because it breaks the parent-after-child rule under clock skew.",
        approach="1. DFS from `start` to get the reachable set.\n2. `pending[p]` = number of reachable children of p.\n3. Push `start`. Pop the best ready commit, append it, decrement `pending` for each parent, push parents that reach zero.\n\n**Dry run** on the skewed history (A100, B90 child of A, C95 child of B, D300 child of A, M200 merging C and D), start M: output M; C and D become ready; D(300) is newer so D; A still waits for B. Then C, then B, then A. Result `M D C B A`. Plain date sorting would have printed D first and A before C.",
        complexity="Time O((V + E) log V) because each commit enters the heap once; space O(V).",
        pitfalls="Counting children that are not reachable from `start`. Pushing a parent as soon as it is first seen rather than when its last child is output (the second wrong solution; that is how plain `git log` without ordering flags behaves, and it can show a parent before a child). Using a min-heap on date without negating.",
        follow_up="`--topo-order` additionally avoids interleaving two lines of development; `--author-date-order` uses the author timestamp. `--graph` implies topological ordering.",
    ),
),
dict(
    id="git-resolve-revision",
    title="Resolve revision expressions like HEAD~2^2",
    difficulty="Medium",
    pattern="Parsing + graph walking",
    entry="resolve",
    description=r"""
Git lets you name commits relative to others. Implement the two most common suffixes.

- `parents` maps every commit id to its **ordered** list of parent ids (first parent first).
- `refs` maps names such as `"HEAD"`, `"main"`, `"v1.0"` to commit ids.
- `expr` is a base name followed by zero or more suffixes:
  - `~n` : follow the **first parent** `n` times. `~` alone means `~1`; `~0` is the commit itself.
  - `^n` : take the **n-th parent** (1-based) of the current commit. `^` alone means `^1`; `^0` is the commit itself.

The base name is looked up in `refs` first; if it is not a ref it must be a commit id present in `parents`.
Suffixes apply left to right. Return the resulting commit id, or `None` if the base name is unknown, the
expression is malformed, or a requested parent does not exist.

**Example:** in the history below, with `refs = {"HEAD": "M"}` and `M`'s parents `["E", "F"]`:
`resolve(p, refs, "HEAD^2")` → `"F"`, `resolve(p, refs, "HEAD~2")` → `"C"`, `resolve(p, refs, "HEAD^2~1")` → `"D"`.

```
A - B - C - E - M
     \         /
      D ----- F
```
""",
    starter='''def resolve(parents, refs, expr):
    pass
''',
    solution='''import re

def resolve(parents, refs, expr):
    m = re.fullmatch(r"([^~^]+)((?:[~^][0-9]*)*)", expr)
    if not m:
        return None
    cur = refs.get(m.group(1), m.group(1))
    if cur not in parents:
        return None
    for op, num in re.findall(r"([~^])([0-9]*)", m.group(2)):
        n = int(num) if num else 1
        if op == "~":
            for _ in range(n):
                if not parents[cur]:
                    return None
                cur = parents[cur][0]
        elif n > 0:
            if n > len(parents[cur]):
                return None
            cur = parents[cur][n - 1]
    return cur
''',
    tests=[
        [G1, {"HEAD": "M"}, "HEAD^2"],
        [G1, {"HEAD": "M"}, "HEAD~2"],
        [G1, {"HEAD": "M"}, "HEAD^2~1"],
        [G1, {"HEAD": "M", "main": "M"}, "main"],
        [G1, {"HEAD": "M"}, "HEAD^^^"],
        [G1, {"HEAD": "M"}, "HEAD~4"],
        [G1, {"HEAD": "M"}, "HEAD~5"],
        [G1, {"HEAD": "M"}, "HEAD^3"],
        [G1, {"HEAD": "M"}, "HEAD^0"],
        [G1, {"HEAD": "M"}, "HEAD~0^2^0~2"],
        [G1, {"HEAD": "M"}, "G~1^"],
        [G1, {"HEAD": "M"}, "nope~1"],
        [G1, {"HEAD": "M"}, "HEAD~x"],
        [G1, {"HEAD": "M"}, "~1"],
        [OCTO, {"tip": "t"}, "tip~1^3"],
        [OCTO, {"tip": "t"}, "tip^^2~"],
        [G1, {"A": "M"}, "A^2"],
        [LINE, {"HEAD": "c29"}, "HEAD~10~10^^"],
    ],
    examples=3,
    wrong_solutions=[
        '''import re

def resolve(parents, refs, expr):
    m = re.fullmatch(r"([^~^]+)((?:[~^][0-9]*)*)", expr)
    if not m:
        return None
    cur = refs.get(m.group(1), m.group(1))
    if cur not in parents:
        return None
    for op, num in re.findall(r"([~^])([0-9]*)", m.group(2)):
        n = int(num) if num else 1
        for _ in range(n):
            if not parents[cur]:
                return None
            cur = parents[cur][0]
    return cur
''',
    ],
    guide=dict(
        prereqs="The lesson on revision selection (ancestry references).",
        intuition="Both suffixes are tiny instructions for a cursor sitting on a commit. `~n` means 'step to the first parent, n times' (go back n generations along the main line). `^n` means 'step once, to parent number n' (choose which side of a merge). Parse the string into a list of such instructions and execute them in order.",
        hints=[
            "Split the expression into a base name and a suffix string; a regular expression such as `[~^]\\d*` then tokenises the suffixes.",
            "`~3` is three steps; `^3` is one step to the third parent. They only coincide for n = 1.",
            "Check for a missing parent at every single step and return `None` immediately.",
        ],
        brute_force="Character-by-character scanning with manual index bookkeeping works but is error-prone around multi-digit numbers and the implicit 1. There is no asymptotically worse algorithm; the risk is only in parsing.",
        approach="1. Full-match `name (suffix)*`; resolve the name through `refs` then as a raw id.\n2. For each `(op, number)`: default number 1. For `~` step to `parents[cur][0]` that many times. For `^` with n > 0 move to `parents[cur][n-1]`.\n\n**Dry run** `HEAD^2~1` with HEAD = M (parents E, F): `^2` moves to F; `~1` moves to F's first parent D. Result `D`. `HEAD^^^` is E, C, B.",
        complexity="Time O(length of expression + total steps); space O(1) beyond the tokens.",
        pitfalls="Treating `^2` as 'two generations back' (that is `~2` or `^^`). Forgetting `^0`/`~0`. Looking up raw ids before refs. Accepting junk like `HEAD~x`.",
        follow_up="Real Git has more: `@{u}` for the upstream, `@{2}` reflog entries, `^{tree}`, `:/text` message search. On Windows `cmd`, `^` must be doubled or quoted.",
    ),
),
dict(
    id="git-bisect-next",
    title="Choose the next commit for git bisect",
    difficulty="Hard",
    pattern="Graph traversal / binary search",
    entry="bisect_next",
    description=r"""
`git bisect` hunts for the first bad commit. You tell it one **bad** commit and some **good** commits; it
repeatedly picks a commit to test that cuts the remaining suspects roughly in half.

`parents` maps commit ids to parent lists. Define the **suspects** as the commits that are ancestors of
`bad` (including `bad`) but are **not** ancestors of any commit in `good` (a good commit and all its
ancestors are cleared).

For a suspect `c`, let `x(c)` be the number of suspects that are ancestors of `c` (including `c`), and
`n` the total number of suspects. Testing `c` leaves `x(c)` suspects if it is bad and `n - x(c)` if it is good,
so its usefulness is `min(x(c), n - x(c))`.

Write `bisect_next(parents, good, bad)`:

- if there are no suspects, return `None` (contradictory input: `bad` is an ancestor of a good commit);
- if there is exactly one suspect, return it (it is the first bad commit);
- otherwise return the suspect with the **largest usefulness**, breaking ties by the smallest id.

**Example:** a line `c0 <- c1 <- ... <- c8`, `good = ["c0"]`, `bad = "c8"`: suspects are c1..c8 (n = 8) and
`x(c4) = 4`, so the answer is `"c4"`.
""",
    starter='''def bisect_next(parents, good, bad):
    pass
''',
    solution=ANC_HELPER + '''
def bisect_next(parents, good, bad):
    cleared = set()
    for g in good:
        cleared |= _anc(parents, g)
    suspects = _anc(parents, bad) - cleared
    n = len(suspects)
    if n == 0:
        return None
    best = None
    for c in sorted(suspects):
        x = len(_anc(parents, c) & suspects)
        score = min(x, n - x)
        if best is None or score > best[0]:
            best = (score, c)
    return best[1]
''',
    tests=[
        [{"c%d" % i: (["c%d" % (i - 1)] if i else []) for i in range(9)}, ["c0"], "c8"],
        [{"c%d" % i: (["c%d" % (i - 1)] if i else []) for i in range(9)}, ["c4"], "c8"],
        [{"c%d" % i: (["c%d" % (i - 1)] if i else []) for i in range(9)}, ["c6"], "c7"],
        [{"c%d" % i: (["c%d" % (i - 1)] if i else []) for i in range(9)}, ["c8"], "c3"],
        [{"c%d" % i: (["c%d" % (i - 1)] if i else []) for i in range(9)}, [], "c5"],
        [G1, ["B"], "M"],
        [G1, ["E"], "M"],
        [G1, ["E", "D"], "M"],
        [G1, ["A"], "H"],
        [G1, ["M"], "M"],
        [CRISS, ["R"], "Y2"],
        [OCTO, ["r"], "t"],
        [TWO_ROOTS, ["a1"], "j"],
        [{"k%03d" % i: (["k%03d" % (i - 1)] if i else []) for i in range(400)}, ["k010"], "k390"],
        [{"k%03d" % i: (["k%03d" % (i - 1)] if i else []) for i in range(400)}, ["k010", "k200"], "k333"],
    ],
    examples=2,
    wrong_solutions=[
        ANC_HELPER + '''
def bisect_next(parents, good, bad):
    cleared = set()
    for g in good:
        cleared |= _anc(parents, g)
    suspects = sorted(_anc(parents, bad) - cleared)
    if not suspects:
        return None
    return suspects[len(suspects) // 2]
''',
        ANC_HELPER + '''
def bisect_next(parents, good, bad):
    suspects = _anc(parents, bad) - set(good)
    n = len(suspects)
    if n == 0:
        return None
    best = None
    for c in sorted(suspects):
        x = len(_anc(parents, c) & suspects)
        score = min(x, n - x)
        if best is None or score > best[0]:
            best = (score, c)
    return best[1]
''',
    ],
    guide=dict(
        prereqs="The lesson on debugging with bisect and blame. Ancestor sets from the earlier graph problems; binary search.",
        intuition="On a straight line, bisect is plain binary search: test the middle. Real history is a graph, so 'the middle' needs a definition. The right question for a candidate is: if I test this commit, how many suspects survive in the worse of the two outcomes? A bad verdict keeps the candidate's own suspect ancestors; a good verdict clears them and keeps the rest. Pick the commit that balances the two.",
        hints=[
            "Compute the suspect set with set arithmetic: ancestors of bad minus the union of ancestors of each good commit.",
            "For each suspect, count how many suspects lie in its ancestry (itself included).",
            "Score each suspect by `min(x, n - x)` and take the maximum; iterate in sorted order so ties resolve to the smallest id.",
        ],
        brute_force="The approach described is already the straightforward O(n) walks for n suspects, O(n * (V + E)) in total. Picking the middle of a sorted id list (first wrong solution) is not an algorithm for this problem at all: ids say nothing about position in history.",
        approach="1. `cleared` = union of ancestor sets of good commits.\n2. `suspects = ancestors(bad) - cleared`.\n3. For each suspect in sorted order compute `x` and the score; keep the best.\n\n**Dry run** on the sample graph with good = [B], bad = M: suspects = {C, D, E, F, M}, n = 5. x(C) = 1, x(D) = 1, x(E) = 2 (C, E), x(F) = 2 (D, F), x(M) = 5. Scores: 1, 1, 2, 2, 0. Best score 2, smallest id `E`. If E turns out good, the suspects shrink to {D, F, M}.",
        complexity="Time O(n * (V + E)) with n suspects; space O(V). Git computes all the counts in one pass with bitmaps for small sets and falls back to approximations on huge ranges.",
        pitfalls="Clearing only the good commits themselves rather than their whole ancestry (second wrong solution). Returning `bad` when other suspects remain (its score is always 0). Assuming history is linear.",
        follow_up="Each step halves the suspects, so about log2(n) tests are needed. `git bisect run <cmd>` automates the loop using the command's exit status (125 means 'skip').",
    ),
),
dict(
    id="git-push-check",
    title="Detect a non-fast-forward push",
    difficulty="Easy",
    pattern="Graph traversal",
    entry="push_check",
    description=r"""
When you push a branch, the server compares its current tip of that branch with the commit you are
sending. It accepts the update only if nothing would be lost.

`parents` is **your local** commit graph (id → parent ids). `remote_tip` is the commit the server's
branch points at now, or `None` if the branch does not exist there yet. `local_tip` is what you push.
`force` says whether you passed `--force`.

Return one of these strings from `push_check(parents, remote_tip, local_tip, force)`:

- `"new-branch"` : `remote_tip` is `None`;
- `"up-to-date"` : both tips are the same commit;
- `"fast-forward"` : `remote_tip` is an ancestor of `local_tip`;
- `"forced"` : otherwise, when `force` is true (the remote commits not in your history are discarded);
- `"rejected"` : otherwise.

Check in that order. Note that `remote_tip` may be a commit you have never fetched, in which case it does
not appear in `parents` at all and cannot be an ancestor of anything you have.

**Example:** local history `A <- B <- C`; `push_check(p, "B", "C", False)` → `"fast-forward"`.

**Example:** a teammate pushed `X` on top of B first: `push_check(p, "X", "C", False)` → `"rejected"`.
""",
    starter='''def push_check(parents, remote_tip, local_tip, force):
    pass
''',
    solution='''def push_check(parents, remote_tip, local_tip, force):
    if remote_tip is None:
        return "new-branch"
    if remote_tip == local_tip:
        return "up-to-date"
    seen = {local_tip}
    stack = [local_tip]
    while stack:
        c = stack.pop()
        if c == remote_tip:
            return "fast-forward"
        for p in parents.get(c, []):
            if p not in seen:
                seen.add(p)
                stack.append(p)
    return "forced" if force else "rejected"
''',
    tests=[
        [{"A": [], "B": ["A"], "C": ["B"]}, "B", "C", False],
        [{"A": [], "B": ["A"], "C": ["B"]}, "X", "C", False],
        [{"A": [], "B": ["A"], "C": ["B"]}, "X", "C", True],
        [{"A": [], "B": ["A"], "C": ["B"]}, None, "C", False],
        [{"A": [], "B": ["A"], "C": ["B"]}, None, "C", True],
        [{"A": [], "B": ["A"], "C": ["B"]}, "C", "C", True],
        [{"A": [], "B": ["A"], "C": ["B"]}, "C", "B", False],
        [{"A": [], "B": ["A"], "C": ["B"]}, "C", "B", True],
        [G1, "F", "M", False],
        [G1, "G", "M", False],
        [G1, "E", "H", True],
        [G1, "B", "H", True],
        [DEEP, "n5", "n4999", False],
        [CRISS, "Q", "X2", False],
    ],
    examples=2,
    wrong_solutions=[
        '''def push_check(parents, remote_tip, local_tip, force):
    if remote_tip is None:
        return "new-branch"
    if remote_tip == local_tip:
        return "up-to-date"
    if force:
        return "forced"
    c = local_tip
    while parents.get(c):
        c = parents[c][0]
        if c == remote_tip:
            return "fast-forward"
    return "rejected"
''',
    ],
    guide=dict(
        prereqs="Problem *Can this branch fast-forward?* and the lesson on working with remotes.",
        intuition="A push is a request to move a label on the server from one commit to another. Moving it forward along history loses nothing, so it is allowed. Moving it anywhere else would orphan the commits the label used to reach, so the server says no unless you insist. 'Forward along history' is exactly the ancestor test.",
        hints=[
            "Handle the two trivial cases (no remote branch, same commit) before any graph work.",
            "Walk backwards from `local_tip` through all parents looking for `remote_tip`.",
            "`force` matters only after the ancestor test has failed; a forced push that happens to be a fast-forward is still reported as a fast-forward.",
        ],
        brute_force="Compute the complete ancestor set of `local_tip` and test membership. Same complexity class, slightly more memory than stopping at the first hit.",
        approach="Check `None`, check equality, then DFS from `local_tip`. Found → `fast-forward`. Not found → `forced` or `rejected` by the flag.\n\n**Dry run**: local `A <- B <- C`, server at `X` (a teammate's commit you have not fetched). Walk from C: C, B, A, never X. Without force the push is rejected, the famous `! [rejected] main -> main (fetch first)`; the cure is to fetch and integrate X, then push again.",
        complexity="Time O(V + E) in your local graph; space O(V).",
        pitfalls="Returning `forced` whenever the flag is set, even for clean fast-forwards. Following only first parents (the server tip may be reachable through a merge's second parent). Pushing an *older* commit over a newer one is also a non-fast-forward.",
        follow_up="`--force-with-lease` adds one more condition: the server tip must still equal your remote-tracking ref, so you cannot wipe out work you have never seen.",
    ),
),
dict(
    id="git-reflog-recover",
    title="Recover a deleted branch from the reflog",
    difficulty="Medium",
    pattern="Log replay",
    entry="recover_branch",
    description=r"""
You ran `git branch -D payments` and want the branch back. The branch's own log is gone, but the
**HEAD reflog** still records every position HEAD has had.

`entries` is the HEAD reflog **oldest first**; each entry is `[sha, message]` where `sha` is the commit HEAD
pointed at *after* the action. `start_branch` is the branch that was checked out before the first entry.

Replay the log, tracking which branch is checked out:

- A message of the form `checkout: moving from <X> to <Y>` switches the current branch to `<Y>` (take
  everything after the last `" to "`). The entry's `sha` is the tip of `<Y>` at that moment.
- Every other message (`commit: ...`, `commit (amend): ...`, `reset: moving to ...`, `merge ...`,
  `cherry-pick: ...`, ...) happens **on the current branch** and moves that branch to `sha`.

Write `recover_branch(entries, start_branch, branch)` returning the last commit that `branch` was known
to point at, or `None` if HEAD was never on that branch.

**Example:**

```
[["a1", "commit: add cart"],
 ["b7", "checkout: moving from main to payments"],
 ["c3", "commit: add stripe client"],
 ["d9", "commit: handle refunds"],
 ["a1", "checkout: moving from payments to main"]]
```

with `start_branch = "main"`: `recover_branch(e, "main", "payments")` → `"d9"`, so `git branch payments d9` restores it.
""",
    starter='''def recover_branch(entries, start_branch, branch):
    pass
''',
    solution='''def recover_branch(entries, start_branch, branch):
    current = start_branch
    last = None
    prefix = "checkout: moving from "
    for sha, msg in entries:
        if msg.startswith(prefix):
            current = msg.rsplit(" to ", 1)[1]
        if current == branch:
            last = sha
    return last
''',
    tests=[
        [[["a1", "commit: add cart"], ["b7", "checkout: moving from main to payments"], ["c3", "commit: add stripe client"], ["d9", "commit: handle refunds"], ["a1", "checkout: moving from payments to main"]], "main", "payments"],
        [[["a1", "commit: add cart"], ["b7", "checkout: moving from main to payments"], ["c3", "commit: add stripe client"], ["d9", "commit: handle refunds"], ["a1", "checkout: moving from payments to main"]], "main", "main"],
        [[["a1", "commit: add cart"], ["b7", "checkout: moving from main to payments"]], "main", "search"],
        [[], "main", "main"],
        [[["a1", "commit: one"], ["a2", "commit: two"]], "dev", "dev"],
        [[["a1", "commit: one"], ["a2", "commit: two"]], "dev", "main"],
        [[["b1", "checkout: moving from main to fix"], ["b2", "commit: wip"], ["b3", "commit (amend): wip done"], ["b1", "reset: moving to HEAD~1"], ["m5", "checkout: moving from fix to main"], ["m6", "commit: unrelated"]], "main", "fix"],
        [[["b1", "checkout: moving from main to fix"], ["m5", "checkout: moving from fix to main"], ["b1", "checkout: moving from main to fix"], ["b9", "commit: later work"], ["m5", "checkout: moving from fix to main"]], "main", "fix"],
        [[["d0", "checkout: moving from main to 4f2a9c1"], ["d1", "commit: detached experiment"], ["m1", "checkout: moving from 4f2a9c1 to main"]], "main", "4f2a9c1"],
        [[["d0", "checkout: moving from main to 4f2a9c1"], ["d1", "commit: detached experiment"], ["m1", "checkout: moving from 4f2a9c1 to main"]], "main", "main"],
        [[["t1", "checkout: moving from main to docs"], ["t2", "commit: explain moving from v1 to v2"], ["t3", "commit: more"]], "main", "docs"],
        [[["x1", "commit: checkout: moving from main to trap"], ["x2", "commit: next"]], "main", "trap"],
        [[["f1", "checkout: moving from main to feature/login"], ["f2", "merge main: Merge made by the 'ort' strategy."], ["f3", "cherry-pick: fix typo"], ["m2", "checkout: moving from feature/login to main"], ["m3", "merge feature/login: Fast-forward"]], "main", "feature/login"],
    ],
    examples=1,
    wrong_solutions=[
        '''def recover_branch(entries, start_branch, branch):
    last = None
    for sha, msg in entries:
        if msg.endswith(" to " + branch):
            last = sha
    return last
''',
        '''def recover_branch(entries, start_branch, branch):
    current = start_branch
    last = None
    for sha, msg in entries:
        if current == branch:
            last = sha
        if "moving from " in msg:
            current = msg.rsplit(" to ", 1)[1]
    return last
''',
    ],
    guide=dict(
        prereqs="The lesson on maintenance and data recovery (reflog). Simple state machines.",
        intuition="The reflog is a diary of HEAD. If you replay it while remembering which branch HEAD was attached to at each moment, every entry tells you where that branch pointed just then. The last such entry for the deleted branch is its final tip.",
        hints=[
            "Keep one variable, the current branch, and update it only on checkout entries.",
            "Decide the order carefully: on a checkout entry the sha already belongs to the branch you moved *to*.",
            "A commit message can contain misleading text such as `moving from a to b`; only a message that *starts* with `checkout: moving from ` is a switch.",
        ],
        brute_force="Search the log for the last checkout *to* the branch and return that sha. This misses every commit made after switching to it, so it usually returns a stale tip.",
        approach="Loop over entries oldest to newest. If the message starts with the checkout prefix, set `current` to the text after the last ` to `. Then, if `current == branch`, remember `sha`.\n\n**Dry run** on the example for `payments`: entry 1 on main; entry 2 switches to payments, last = b7; entry 3 commit, last = c3; entry 4 commit, last = d9; entry 5 switches to main. Answer d9.",
        complexity="Time O(n) over the entries, space O(1).",
        pitfalls="Updating `last` before processing the switch (off by one entry in both directions). Parsing with `in` instead of `startswith`. Splitting on the first ` to ` rather than the last when branch names or messages contain the word.",
        follow_up="In real life: `git reflog` to find the sha, then `git branch payments <sha>`. If the commits never touched HEAD on this machine, `git fsck --lost-found` lists dangling commits. Unreachable commits survive about 30 days by default before garbage collection may remove them.",
    ),
),
]
