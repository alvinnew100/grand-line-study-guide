PROBLEMS = [
dict(
    id="cicd-git-bisect",
    title="Simulate git bisect",
    difficulty="Easy",
    pattern="Binary Search",
    entry="bisect_commits",
    description=r"""
A bug appeared somewhere in a range of commits. `bad[i]` tells whether commit `i` has the bug. Once the bug is
introduced, every later commit has it too, so the list is some `False` values followed by some `True` values.
It is guaranteed that the first commit is good (`bad[0]` is `False`), the last is bad (`bad[-1]` is `True`), and
the list has at least 2 commits.

Find the **first bad commit** the way `git bisect` does, testing as few commits as possible:

1. Keep two markers: `good = 0` (known good) and `broken = len(bad) - 1` (known bad). These two are already
   known and do **not** count as tests.
2. While `broken - good > 1`: test the commit `mid = (good + broken) // 2`. If it is bad, set `broken = mid`;
   otherwise set `good = mid`.
3. When the markers are adjacent, `broken` is the first bad commit.

Return `[first_bad_index, tested]`, where `tested` is the list of commit indices you tested, in order.

**Example 1:** `bad = [False, False, False, False, True, True, True, True]` → `[4, [3, 5, 4]]`

**Example 2:** `bad = [False, True]` → `[1, []]` (nothing needs testing)
""",
    starter='''def bisect_commits(bad: List[bool]) -> list:
    pass
''',
    solution='''def bisect_commits(bad):
    good, broken = 0, len(bad) - 1
    tested = []
    while broken - good > 1:
        mid = (good + broken) // 2
        tested.append(mid)
        if bad[mid]:
            broken = mid
        else:
            good = mid
    return [broken, tested]
''',
    tests=[
        [[False, False, False, False, True, True, True, True]],
        [[False, True]],
        [[False, True, True]],
        [[False, False, True]],
        [[False] + [True] * 15],
        [[False] * 15 + [True]],
        [[False] * 5 + [True] * 4],
        [[False] * 26 + [True] * 14],
        [[False] * 617 + [True] * 383],
        [[False] * 3 + [True] * 4997],
        [[False] * 4999 + [True]],
        [[False] * 2500 + [True] * 2500],
    ],
    examples=2,
    wrong_solutions=[
        '''def bisect_commits(bad):
    tested = []
    for i in range(1, len(bad) - 1):
        tested.append(i)
        if bad[i]:
            return [i, tested]
    return [len(bad) - 1, tested]
''',
        '''def bisect_commits(bad):
    lo, hi = 0, len(bad) - 1
    tested = []
    while lo < hi:
        mid = (lo + hi) // 2
        tested.append(mid)
        if bad[mid]:
            hi = mid
        else:
            lo = mid + 1
    return [lo, tested]
''',
    ],
    guide=dict(
        prereqs="Lists, a `while` loop and integer division `//`. See the lesson *Recovery: revert first, bisect, quarantine and learn*.",
        intuition="Because the commits are 'good, good, ..., bad, bad', testing the middle commit tells you which half holds the boundary, and "
                  "the other half can be thrown away. Halving a range repeatedly reaches a single position in about log2(n) steps.",
        hints=[
            "Keep one promise true at all times: the commit at `good` is good and the commit at `broken` is bad.",
            "Each test moves exactly one of the two markers to the middle.",
            "Stop when the markers are next to each other; the answer is the bad marker.",
        ],
        brute_force="Test the commits one after another from the start until the first bad one: up to n - 2 tests. If each test is a ten-minute "
                    "test run and there are a thousand commits, that is days instead of a couple of hours.",
        approach="1. `good, broken = 0, len(bad) - 1`.\n"
                 "2. While `broken - good > 1`: `mid = (good + broken) // 2`; record it; move `broken` to `mid` if it is bad, otherwise move `good`.\n"
                 "3. Return `[broken, tested]`.\n\n"
                 "**Dry run** on Example 1 (8 commits, first bad is 4): good 0, broken 7 -> mid 3, good -> good = 3. mid 5, bad -> broken = 5. "
                 "mid 4, bad -> broken = 4. Markers 3 and 4 are adjacent: answer 4, tested [3, 5, 4].",
        complexity="Time O(log n) tests. Space O(log n) for the list of tested commits.",
        pitfalls="- The two end commits are already known; testing them wastes tests.\n"
                 "- A different loop shape (`lo < hi` with `lo = mid + 1`) finds the same commit but tests a different sequence, and can test the end commit.\n"
                 "- Scanning linearly is correct and far too slow.\n"
                 "- With two commits there is nothing to test.",
        follow_up="Some commits cannot be tested (they do not build). `git bisect skip` handles that. How would you choose the next commit to test, and what "
                  "can you report if the boundary lies inside a run of skipped commits?",
    ),
),
dict(
    id="cicd-revert-selection",
    title="Choose Commits to Revert",
    difficulty="Medium",
    pattern="Matrix / Scan",
    entry="commits_to_revert",
    description=r"""
The main branch is red. You have the test results after each recent commit and must decide which commits to
revert.

`results` is a table. Row `i` holds the results after commit `i`; column `j` is test `j`; `True` means the test
passed. Row `0` is the last known-good state. Every row has the same number of columns.

For each test that **fails in the last row**, the commit to blame is the one where that test **most recently**
went from passing to failing: the largest `i >= 1` with `results[i-1][j]` true and `results[i][j]` false.
(A test that broke earlier and was fixed again is not that earlier commit's fault any more.)

If a test fails in the last row but was never seen passing (it already failed in row `0`), no commit in this
range can be blamed for it; ignore it.

Return the sorted list of distinct commit indices to revert. Return `[]` if nothing in the last row fails.

**Example 1:**
```
results = [[True,  True,  True ],     row 0: all green
           [True,  False, True ],     commit 1 breaks test 1
           [True,  False, True ],
           [False, False, True ]]     commit 3 breaks test 0
```
→ `[1, 3]`

**Example 2:** `[[True, True], [False, True], [True, True]]` → `[]` (broken by commit 1, fixed by commit 2)
""",
    starter='''def commits_to_revert(results: List[List[bool]]) -> List[int]:
    pass
''',
    solution='''def commits_to_revert(results):
    if not results:
        return []
    last = len(results) - 1
    culprits = set()
    for j in range(len(results[0])):
        if results[last][j]:
            continue
        i = last
        while i >= 1 and not results[i - 1][j]:
            i -= 1
        if i >= 1:
            culprits.add(i)
    return sorted(culprits)
''',
    tests=[
        [[[True, True, True], [True, False, True], [True, False, True], [False, False, True]]],
        [[[True, True], [False, True], [True, True]]],
        [[]],
        [[[True, True, True]]],
        [[[False, True]]],
        [[[True], [False]]],
        [[[True, True], [False, False]]],
        [[[True], [False], [True], [False], [False]]],
        [[[False, True], [False, True], [False, False]]],
        [[[False], [True], [False]]],
        [[[True, True, True, True], [True, True, True, True], [False, True, False, True], [False, False, False, True], [True, False, False, True]]],
        [[[True] * 6, [False] * 6]],
        [[[True] * 50] + [[(c + r) % 7 != 0 for c in range(50)] for r in range(1, 120)]],
        [[[True] * 200] + [[c >= r for c in range(200)] for r in range(1, 201)]],
    ],
    examples=2,
    wrong_solutions=[
        '''def commits_to_revert(results):
    if not results:
        return []
    culprits = set()
    for j in range(len(results[0])):
        if results[-1][j]:
            continue
        for i in range(1, len(results)):
            if results[i - 1][j] and not results[i][j]:
                culprits.add(i)
                break
    return sorted(culprits)
''',
        '''def commits_to_revert(results):
    return sorted({i for i in range(1, len(results))
                   for j in range(len(results[0]))
                   if results[i - 1][j] and not results[i][j]})
''',
    ],
    guide=dict(
        prereqs="Lists of lists (a table), nested loops and sets. See the lesson *Recovery: revert first, bisect, quarantine and learn*.",
        intuition="Look at one test at a time, reading its column from the bottom upwards. If it is failing now, walk up while it keeps failing. "
                  "The row where the failing run begins is the commit that broke it. Earlier breakages that were later fixed are above that run "
                  "and are never reached.",
        hints=[
            "Only columns whose last entry is `False` matter.",
            "Walk upwards from the last row while the row above is also failing.",
            "If you reach row 0 and it is failing too, there is no commit to blame for that test.",
        ],
        brute_force="For every failing test, list every pass-to-fail transition in its column and take the last. That is the same amount of work in "
                    "the worst case, but it reads the whole column even when the answer is near the bottom.",
        approach="1. Empty table -> `[]`. Let `last` be the index of the final row.\n"
                 "2. For each column `j` with `results[last][j]` false: set `i = last`; while `i >= 1` and `results[i-1][j]` is false, decrease `i`.\n"
                 "3. If `i >= 1`, commit `i` broke the test: add it to a set.\n"
                 "4. Return the set sorted.\n\n"
                 "**Dry run** on Example 1: test 0 fails at row 3 and passed at row 2 -> commit 3. Test 1 fails at rows 3, 2 and 1 and passed at "
                 "row 0 -> commit 1. Test 2 passes. Answer [1, 3].",
        complexity="Time O(rows * columns) in the worst case. Space O(columns) for the set of culprits.",
        pitfalls="- Taking the *first* transition blames a commit whose damage was already repaired.\n"
                 "- Collecting every transition reverts commits for tests that are passing now.\n"
                 "- A test that was already failing in row 0 has no culprit in this range.\n"
                 "- Several tests broken by the same commit must give that commit once.\n"
                 "- An empty table, or a table with one row, has nothing to revert.",
        follow_up="Reverting a commit can conflict with later commits that touched the same files. Given the files each commit changed, return the "
                  "extra commits that would have to be reverted as well.",
    ),
),
dict(
    id="cicd-merge-queue",
    title="Merge Queue with Batching",
    difficulty="Medium",
    pattern="Simulation / Divide and Conquer",
    entry="merge_queue",
    description=r"""
A merge queue tests several queued changes together in a **batch**, to save CI runs. If a batch fails, it
searches for the failing change by splitting the batch.

- `queue` is the list of change names in queue order (all distinct).
- `bad` lists the changes that make the build fail. A group of changes passes CI only if it contains **no** bad change.
- `batch_size` is the maximum number of changes per batch (at least 1).

Process the queue like this:

1. Take the next `batch_size` changes from the front of the queue (fewer if fewer remain) and **process** that group.
2. To **process a group**: run CI on it (this counts as one CI run).
   - If it passes, all its changes are merged, in order.
   - If it fails and contains exactly one change, that change is **ejected**.
   - If it fails and contains more than one change, split it into a first half of `len(group) // 2` changes and
     a second half with the rest. Process the first half completely, then the second half.
3. Repeat until the queue is empty.

Return `[merged, ejected, ci_runs]`: the merged changes in the order they were merged, the ejected changes in
the order they were ejected, and the total number of CI runs.

**Example 1:** `queue = ["a","b","c","d"]`, `bad = ["c"]`, `batch_size = 4` → `[["a","b","d"], ["c"], 5]`
(runs: abcd fails; ab passes; cd fails; c fails and is ejected; d passes)

**Example 2:** `queue = ["a","b","c"]`, `bad = []`, `batch_size = 2` → `[["a","b","c"], [], 2]`
""",
    starter='''def merge_queue(queue: List[str], bad: List[str], batch_size: int) -> list:
    pass
''',
    solution='''def merge_queue(queue, bad, batch_size):
    bad_set = set(bad)
    merged, ejected = [], []
    runs = 0
    for start in range(0, len(queue), batch_size):
        stack = [queue[start:start + batch_size]]
        while stack:
            group = stack.pop()
            runs += 1
            if not any(c in bad_set for c in group):
                merged.extend(group)
            elif len(group) == 1:
                ejected.append(group[0])
            else:
                half = len(group) // 2
                stack.append(group[half:])
                stack.append(group[:half])
    return [merged, ejected, runs]
''',
    tests=[
        [["a", "b", "c", "d"], ["c"], 4],
        [["a", "b", "c"], [], 2],
        [[], [], 3],
        [["a"], [], 5],
        [["a"], ["a"], 5],
        [["a", "b", "c", "d"], ["c"], 1],
        [["a", "b", "c", "d", "e"], ["a", "e"], 5],
        [["a", "b", "c", "d", "e"], ["a", "b", "c", "d", "e"], 5],
        [["a", "b", "c", "d", "e", "f", "g"], ["d"], 3],
        [["a", "b", "c"], ["zzz"], 3],
        [["a", "b", "c", "d", "e", "f", "g", "h"], ["h"], 8],
        [["a", "b", "c", "d", "e", "f", "g", "h"], ["a"], 8],
        [[f"pr{i}" for i in range(1, 13)], ["pr7"], 12],
        [[f"pr{i}" for i in range(500)], [f"pr{i}" for i in range(0, 500, 37)], 16],
    ],
    examples=2,
    wrong_solutions=[
        '''def merge_queue(queue, bad, batch_size):
    bad_set = set(bad)
    merged, ejected, runs = [], [], 0
    for start in range(0, len(queue), batch_size):
        group = queue[start:start + batch_size]
        runs += 1
        if any(c in bad_set for c in group):
            ejected.extend(group)
        else:
            merged.extend(group)
    return [merged, ejected, runs]
''',
        '''def merge_queue(queue, bad, batch_size):
    bad_set = set(bad)
    merged = [c for c in queue if c not in bad_set]
    ejected = [c for c in queue if c in bad_set]
    return [merged, ejected, len(queue)]
''',
    ],
    guide=dict(
        prereqs="Lists, slicing, sets, and either recursion or a stack. See the lesson *Guardrails: branch protection, required checks and merge queues*.",
        intuition="One CI run on a batch answers the question 'is every change in here fine?'. If yes, the whole batch lands for the price of one "
                  "run. If no, halve the batch and ask again. Good changes are confirmed in bulk; only the neighbourhood of a bad change needs extra runs.",
        hints=[
            "Write a function that processes one group: count a run, then merge, eject or split.",
            "When splitting, the first half must be processed completely before the second half, to keep the merge order.",
            "With an explicit stack, push the second half first and the first half second, so that the first half is popped first.",
        ],
        brute_force="Test every change separately: exactly one CI run per change. It gives the same merged and ejected lists with more runs whenever "
                    "failures are rare, which is the normal situation.",
        approach="For each batch (slices of `batch_size`), keep a stack of groups starting with the batch:\n\n"
                 "1. Pop a group and add 1 to the run count.\n"
                 "2. No bad change in it -> extend `merged`.\n"
                 "3. Otherwise, if it has one change -> append it to `ejected`.\n"
                 "4. Otherwise split at `len // 2`; push the second half, then the first half.\n\n"
                 "**Dry run** on Example 1: [a,b,c,d] fails (1 run) -> [a,b] passes (2), merged a, b -> [c,d] fails (3) -> [c] fails (4), ejected -> "
                 "[d] passes (5), merged d. Result [[a,b,d],[c],5].",
        complexity="With one bad change in a batch of size k, about 2 * log2(k) + 1 runs. In general O(b * log k) extra runs for b bad changes, and "
                   "never more than about 2k - 1 runs per batch. Space O(k).",
        pitfalls="- Ejecting the whole failing batch punishes innocent changes.\n"
                 "- Processing the second half before the first changes the merge order.\n"
                 "- The run on the full batch counts, even when it fails.\n"
                 "- A name in `bad` that is not in the queue has no effect.\n"
                 "- When nearly every change is bad, batching costs more runs than testing one at a time.",
        follow_up="In a real queue, a change may be fine alone and fail only in combination with an earlier one. Model `conflicts` as pairs of "
                  "changes that cannot both be merged, and eject the later one of each pair.",
    ),
),
dict(
    id="cicd-flaky-tests",
    title="Detect Flaky Tests from Run History",
    difficulty="Medium",
    pattern="Hash Map / Grouping",
    entry="classify_tests",
    description=r"""
A test is **flaky** if it can both pass and fail on the same code. Classify tests from the history of CI runs.

`runs` is a list of `[commit, test, passed]` records in the order they happened. The same test may run several
times on the same commit (because of re-runs). Commits appear in chronological order: once a new commit shows up
in the list, records for older commits may still appear later (late re-runs), but the *first appearance* of each
commit defines the commit order.

Classify each test that appears:

- `"flaky"` — on at least one commit, the test has both a passing and a failing record;
- otherwise `"broken"` — on the **most recent commit on which this test ran** (by commit order), every record of
  it is a failure;
- otherwise `"healthy"`.

Return a list of `[test, status]` pairs sorted by test name.

**Example 1:**
`[["c1","login",True],["c1","refund",True],["c2","login",True],["c2","refund",False],["c2","refund",True],["c3","login",False],["c3","login",False]]`
→ `[["login","broken"],["refund","flaky"]]`

**Example 2:** `[["c1","search",False],["c2","search",True]]` → `[["search","healthy"]]`
(it failed on an older commit, consistently, and passes on the newest: a bug that was fixed)
""",
    starter='''def classify_tests(runs: List[list]) -> List[List[str]]:
    pass
''',
    solution='''def classify_tests(runs):
    commit_order = {}
    outcomes = {}
    for commit, test, passed in runs:
        if commit not in commit_order:
            commit_order[commit] = len(commit_order)
        outcomes.setdefault(test, {}).setdefault(commit, set()).add(bool(passed))
    result = []
    for test in sorted(outcomes):
        by_commit = outcomes[test]
        if any(len(seen) == 2 for seen in by_commit.values()):
            status = "flaky"
        else:
            latest = max(by_commit, key=lambda c: commit_order[c])
            status = "broken" if by_commit[latest] == {False} else "healthy"
        result.append([test, status])
    return result
''',
    tests=[
        [[["c1", "login", True], ["c1", "refund", True], ["c2", "login", True], ["c2", "refund", False],
          ["c2", "refund", True], ["c3", "login", False], ["c3", "login", False]]],
        [[["c1", "search", False], ["c2", "search", True]]],
        [[]],
        [[["c1", "t", True]]],
        [[["c1", "t", False]]],
        [[["c1", "t", False], ["c1", "t", False], ["c1", "t", False]]],
        [[["c1", "t", True], ["c1", "t", False]]],
        [[["c1", "t", True], ["c2", "t", False], ["c1", "t", True]]],
        [[["c1", "t", True], ["c2", "t", False], ["c1", "t", False]]],
        [[["c1", "a", True], ["c2", "b", False], ["c3", "a", True]]],
        [[["c1", "a", False], ["c1", "a", True], ["c2", "a", True], ["c3", "a", True]]],
        [[["c1", "z", True], ["c1", "y", False], ["c2", "x", True], ["c2", "y", True], ["c3", "z", False]]],
        [[[f"c{c}", f"t{t:03d}", not (t % 5 == 0 and c >= 30) and not (t % 11 == 0 and (c * 7 + r) % 4 == 0)]
          for c in range(40) for t in range(60) for r in range(2)]],
    ],
    examples=2,
    wrong_solutions=[
        '''def classify_tests(runs):
    seen = {}
    for commit, test, passed in runs:
        seen.setdefault(test, set()).add(bool(passed))
    out = []
    for test in sorted(seen):
        s = seen[test]
        out.append([test, "flaky" if len(s) == 2 else "broken" if s == {False} else "healthy"])
    return out
''',
        '''def classify_tests(runs):
    outcomes, last = {}, {}
    for commit, test, passed in runs:
        outcomes.setdefault(test, {}).setdefault(commit, set()).add(bool(passed))
        last[test] = commit
    out = []
    for test in sorted(outcomes):
        by = outcomes[test]
        if any(len(s) == 2 for s in by.values()):
            out.append([test, "flaky"])
        else:
            out.append([test, "broken" if by[last[test]] == {False} else "healthy"])
    return out
''',
    ],
    guide=dict(
        prereqs="Dictionaries, sets and grouping records by a key. See the lessons *Test data, asynchrony and flaky tests* and "
                "*Recovery: revert first, bisect, quarantine and learn*.",
        intuition="Group the records by test and then by commit. For one test on one commit, the code is fixed, so the set of outcomes should "
                  "have one member. Two members mean the test disagreed with itself: flaky. If it never disagreed with itself, its newest commit "
                  "tells you whether it is broken now.",
        hints=[
            "Build `outcomes[test][commit]` as a set of booleans.",
            "Remember the order in which commits first appear; you need it to find a test's most recent commit.",
            "Decide 'flaky' first. Only if no commit has mixed outcomes do you look at the latest commit for that test.",
        ],
        brute_force="For every test and every commit, scan the entire list of runs to collect the outcomes: O(tests * commits * runs). "
                    "One pass that fills nested dictionaries does the same in O(runs).",
        approach="1. One pass over `runs`: record each commit's first-appearance position, and add each outcome to `outcomes[test][commit]`.\n"
                 "2. For each test in sorted order: if any commit's set has both values -> `flaky`.\n"
                 "3. Otherwise find the test's commit with the largest position; `broken` if its set is `{False}`, else `healthy`.\n\n"
                 "**Dry run** on Example 1: refund on c2 has {False, True} -> flaky. login: c1 {True}, c2 {True}, c3 {False}; no mixed commit; "
                 "latest is c3 with only failures -> broken.",
        complexity="Time O(n + t log t) for n records and t tests. Space O(n).",
        pitfalls="- Passing on one commit and failing on another is not flakiness; the code changed in between.\n"
                 "- 'Most recent commit' means commit order, not the position of the test's last record: a late re-run of an old commit must not "
                 "count as the newest.\n"
                 "- A test that failed in the past and passes on its newest commit is healthy.\n"
                 "- A test may not have run on the newest commit overall; use the newest commit on which *it* ran.",
        follow_up="Compute a flake rate per test (failures divided by runs, on commits where it also passed) and return the tests above a threshold, worst first.",
    ),
),
]
