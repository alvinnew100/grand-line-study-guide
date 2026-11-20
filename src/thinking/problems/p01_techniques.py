PROBLEMS = [
dict(
    id="think-boundary-values",
    title="Boundary Values for an Integer Range",
    difficulty="Easy",
    pattern="Test Design Techniques",
    entry="boundary_values",
    description=r"""
A field accepts every integer from `lo` to `hi` inclusive (`lo <= hi`). Produce the values a tester
should try under **boundary value analysis**.

- When `three_value` is `False` (2-value BVA) return each boundary and its nearest neighbour in the
  *adjacent* partition: `lo - 1, lo, hi, hi + 1`.
- When `three_value` is `True` (3-value BVA) return each boundary together with **both** neighbours:
  `lo - 1, lo, lo + 1, hi - 1, hi, hi + 1`.

Return the values **sorted ascending with duplicates removed** (narrow ranges make neighbours collide).

**Example:** `lo = 1, hi = 100, three_value = False` → `[0, 1, 100, 101]`

**Example:** `lo = 5, hi = 6, three_value = True` → `[4, 5, 6, 7]`

Constraints: `-10^9 <= lo <= hi <= 10^9`.
""",
    starter='''def boundary_values(lo: int, hi: int, three_value: bool) -> List[int]:
    pass
''',
    solution='''def boundary_values(lo, hi, three_value):
    vals = {lo - 1, lo, hi, hi + 1}
    if three_value:
        vals |= {lo + 1, hi - 1}
    return sorted(vals)
''',
    tests=[
        [1, 100, False],
        [5, 6, True],
        [1, 100, True],
        [7, 7, False],
        [7, 7, True],
        [0, 1, False],
        [0, 2, True],
        [-5, 5, True],
        [-10, -1, False],
        [18, 65, True],
        [0, 0, True],
        [-1000000000, 1000000000, True],
    ],
    examples=2,
    wrong_solutions=[
        '''def boundary_values(lo, hi, three_value):
    if three_value:
        return [lo - 1, lo, lo + 1, hi - 1, hi, hi + 1]
    return [lo - 1, lo, hi, hi + 1]
''',
        '''def boundary_values(lo, hi, three_value):
    return sorted({lo - 1, lo, hi, hi + 1})
''',
        '''def boundary_values(lo, hi, three_value):
    vals = {lo, hi}
    if three_value:
        vals |= {lo + 1, hi - 1}
    return sorted(vals)
''',
    ],
    guide=dict(
        prereqs="Lesson *Equivalence partitioning and boundary value analysis*. Python sets and `sorted`.",
        intuition="Off-by-one mistakes live where a comparison flips, so the interesting inputs sit on either "
                  "side of each edge. A valid range has two edges; each edge contributes a fixed handful of neighbours.",
        hints=[
            "Write the six candidate values down by hand for `1..100` first.",
            "What happens to those six values when `lo == hi`? Several of them become the same number.",
            "Put the candidates in a `set`, then return `sorted(the_set)`.",
        ],
        brute_force="Build the list with repeats, then remove duplicates with a nested loop — O(k²) for k ≤ 6 values, "
                    "which works but is more code than a set.",
        approach="1. Start a set with `lo - 1, lo, hi, hi + 1` — the 2-value picks.\n"
                 "2. If `three_value`, add the inside neighbours `lo + 1` and `hi - 1`.\n"
                 "3. Sort and return.\n\n"
                 "**Dry run** `lo=5, hi=6, three_value=True`: set starts `{4,5,6,7}`; adding `lo+1=6` and `hi-1=5` "
                 "changes nothing; result `[4,5,6,7]`.",
        complexity="Time O(1) and space O(1): at most six values regardless of the range width.",
        pitfalls="- Forgetting to de-duplicate when the range is one or two values wide.\n"
                 "- Returning only valid values: the *invalid* neighbours `lo-1` and `hi+1` are the whole point.\n"
                 "- Generating every value in the range — a range can hold two billion integers.",
        follow_up="Extend it to several disjoint valid ranges, or to a float field with a given precision step.",
    ),
),
dict(
    id="think-equivalence-classes",
    title="Partition Inputs into Equivalence Classes",
    difficulty="Easy",
    pattern="Test Design Techniques",
    entry="partition_inputs",
    description=r"""
A numeric input is split into equivalence classes by a sorted list of distinct **cut points**
`cuts = [c0, c1, ..., ck-1]`. They define `k + 1` classes:

- class `0`: values `< c0`
- class `i` (for `1 <= i <= k-1`): values with `c(i-1) <= v < c(i)`
- class `k`: values `>= c(k-1)`

Given `cuts` and a list of observed `values`, return a list of `k + 1` lists where list `i` holds the
values that fall in class `i`, **in their original order** (keep duplicates). If `cuts` is empty there is
a single class containing everything.

**Example:** `cuts = [0, 18, 65], values = [17, 18, -3, 70, 64, 65]` → `[[-3], [17], [18, 64], [70, 65]]`

(An age field: negative is invalid, 0–17 minor, 18–64 adult, 65+ senior.)

Constraints: up to `10^4` cuts and `10^5` values.
""",
    starter='''def partition_inputs(cuts: List[int], values: List[int]) -> List[List[int]]:
    pass
''',
    solution='''def partition_inputs(cuts, values):
    out = [[] for _ in range(len(cuts) + 1)]
    for v in values:
        out[bisect.bisect_right(cuts, v)].append(v)
    return out
''',
    tests=[
        [[0, 18, 65], [17, 18, -3, 70, 64, 65]],
        [[10], [10, 9, 11, 10]],
        [[], [3, 1, 2]],
        [[0, 18, 65], []],
        [[5, 6, 7], [5, 6, 7, 4, 8]],
        [[-10, 0, 10], [-11, -10, -1, 0, 9, 10, 11]],
        [[100], [1, 2, 3]],
        [[100], [100, 200, 300]],
        [[1, 2, 3, 4], [4, 4, 4, 0, 0]],
        [[0], [0]],
        [list(range(0, 10000, 10)), list(range(-5, 10005, 7))],
        [[50, 500, 5000], [5000, 4999, 500, 499, 50, 49]],
    ],
    examples=2,
    wrong_solutions=[
        '''def partition_inputs(cuts, values):
    out = [[] for _ in range(len(cuts) + 1)]
    for v in values:
        out[bisect.bisect_left(cuts, v)].append(v)
    return out
''',
        '''def partition_inputs(cuts, values):
    out = [[] for _ in range(len(cuts) + 1)]
    for v in sorted(values):
        out[bisect.bisect_right(cuts, v)].append(v)
    return out
''',
    ],
    guide=dict(
        prereqs="Lesson *Equivalence partitioning and boundary value analysis*; binary search (`bisect`).",
        intuition="Each cut point is the first value of a new class. The class index of a value is simply "
                  "how many cut points are less than or equal to it.",
        hints=[
            "Create `len(cuts) + 1` empty lists up front so empty classes still appear in the answer.",
            "For one value, count the cuts `c` with `c <= v`. That count is the class index.",
            "`bisect.bisect_right(cuts, v)` returns exactly that count in O(log k).",
        ],
        brute_force="For every value scan the cuts left to right and stop at the first cut greater than the value: "
                    "O(n·k). Fine for small tables, too slow at 10⁵ values × 10⁴ cuts.",
        approach="1. Allocate `k + 1` buckets.\n2. For each value in input order, compute "
                 "`i = bisect_right(cuts, v)` and append to bucket `i`.\n3. Return the buckets.\n\n"
                 "**Dry run** `cuts=[0,18,65]`: `17` → one cut (0) is ≤ 17 → class 1. `18` → two cuts ≤ 18 → class 2. "
                 "`-3` → zero cuts → class 0. `65` → three cuts → class 3.",
        complexity="Time O(n log k), space O(n + k) for the output.",
        pitfalls="- Using `bisect_left`, which puts a value equal to a cut into the class *below* — the classic "
                 "boundary bug this technique is meant to expose.\n- Sorting the values and losing input order.\n"
                 "- Dropping empty classes from the output.",
        follow_up="Return one representative per non-empty class, or report which classes have no test value yet.",
    ),
),
dict(
    id="think-pairwise-uncovered",
    title="Pairwise Coverage Checker",
    difficulty="Medium",
    pattern="Combinatorial Testing",
    entry="uncovered_pairs",
    description=r"""
A system has `len(levels)` parameters; parameter `i` takes values `0 .. levels[i] - 1`.
A **test** is a list with one value per parameter. A suite achieves *pairwise* (all-pairs) coverage
when, for every pair of parameters `i < j` and every combination of a value `a` for `i` and a value
`b` for `j`, some test has `test[i] == a` and `test[j] == b`.

Given `levels` and a `suite`, return the **number of value pairs that no test covers**.
A result of `0` means the suite is pairwise-complete.

**Example:** `levels = [2, 2, 2]`, `suite = [[0,0,0],[0,1,1],[1,0,1],[1,1,0]]` → `0`

**Example:** `levels = [2, 3]`, `suite = [[0,0],[1,1]]` → `4` (six pairs exist, two are covered)

Constraints: up to 8 parameters, each with 1–6 values, up to 500 tests. All tests are well-formed.
""",
    starter='''def uncovered_pairs(levels: List[int], suite: List[List[int]]) -> int:
    pass
''',
    solution='''def uncovered_pairs(levels, suite):
    n = len(levels)
    seen = set()
    for t in suite:
        for i in range(n):
            for j in range(i + 1, n):
                seen.add((i, j, t[i], t[j]))
    total = 0
    for i in range(n):
        for j in range(i + 1, n):
            total += levels[i] * levels[j]
    return total - len(seen)
''',
    tests=[
        [[2, 2, 2], [[0, 0, 0], [0, 1, 1], [1, 0, 1], [1, 1, 0]]],
        [[2, 3], [[0, 0], [1, 1]]],
        [[2, 2, 2], []],
        [[3], [[0], [1]]],
        [[2, 2], [[0, 0], [0, 0], [0, 0]]],
        [[2, 2, 2], [[0, 0, 0], [1, 1, 1]]],
        [[3, 3, 3], [[a, b, (a + b) % 3] for a in range(3) for b in range(3)]],
        [[3, 3, 3], [[a, b, 0] for a in range(3) for b in range(3)]],
        [[1, 1, 1], [[0, 0, 0]]],
        [[2, 3, 4], [[a, b, c] for a in range(2) for b in range(3) for c in range(4)]],
        [[4, 4, 4, 4], [[a, a, a, a] for a in range(4)]],
        [[2, 2, 2, 2, 2, 2], [[0] * 6, [1] * 6, [0, 1, 0, 1, 0, 1]]],
        [[6, 6, 6, 6, 6, 6, 6, 6], [[(i * k) % 6 for k in range(8)] for i in range(300)]],
    ],
    examples=2,
    wrong_solutions=[
        '''def uncovered_pairs(levels, suite):
    n = len(levels)
    total = sum(levels[i] * levels[j] for i in range(n) for j in range(i + 1, n))
    return max(0, total - len(suite) * (n * (n - 1) // 2))
''',
        '''def uncovered_pairs(levels, suite):
    n = len(levels)
    seen = set()
    for t in suite:
        for i in range(n):
            for j in range(i + 1, n):
                seen.add((t[i], t[j]))
    total = sum(levels[i] * levels[j] for i in range(n) for j in range(i + 1, n))
    return total - len(seen)
''',
        '''def uncovered_pairs(levels, suite):
    n = len(levels)
    seen = set()
    for t in suite:
        for i in range(n - 1):
            seen.add((i, i + 1, t[i], t[i + 1]))
    total = sum(levels[i] * levels[j] for i in range(n) for j in range(i + 1, n))
    return total - len(seen)
''',
    ],
    guide=dict(
        prereqs="Lesson *Decision tables, state transitions and pairwise testing*. Sets of tuples.",
        intuition="Every test covers exactly one value pair for each pair of parameter positions. Collect what is "
                  "covered in a set, count what exists, subtract.",
        hints=[
            "How many pairs exist in total? For positions `i < j` it is `levels[i] * levels[j]`.",
            "A covered pair must remember *which parameters* it belongs to, not just the two values.",
            "Store `(i, j, t[i], t[j])` in a set for each test and each `i < j`; answer = total − set size.",
        ],
        brute_force="Enumerate every required pair `(i, j, a, b)` and scan the whole suite looking for a test that "
                    "contains it: O(P · T) where P is the number of pairs — up to ~1000 pairs × 500 tests × per-check cost.",
        approach="1. Walk the suite once; for each test add every `(i, j, t[i], t[j])` with `i < j` to a set.\n"
                 "2. Total pairs = Σ over `i < j` of `levels[i]·levels[j]`.\n3. Return total − len(set).\n\n"
                 "**Dry run** `levels=[2,3]`, suite `[[0,0],[1,1]]`: set = {(0,1,0,0), (0,1,1,1)}; total = 2·3 = 6; "
                 "answer 4.",
        complexity="Time O(T · n²) with T tests and n parameters; space O(min(T·n², total pairs)).",
        pitfalls="- Keying on `(a, b)` only, which merges pairs from different parameter positions.\n"
                 "- Counting duplicates twice (use a set, not a counter).\n"
                 "- Only checking adjacent parameters.",
        follow_up="Return the missing pairs themselves, or generalise to 3-wise coverage.",
    ),
),
dict(
    id="think-pairwise-generate",
    title="Greedy Pairwise Test Generator",
    difficulty="Hard",
    pattern="Combinatorial Testing",
    entry="pairwise_suite",
    description=r"""
Parameter `i` takes values `0 .. levels[i] - 1`. Build a test suite (a list of tests, each a list with
one value per parameter) that covers **every pair of values for every pair of parameters** — see
*Pairwise Coverage Checker* for the definition.

Many suites are valid. Yours is accepted when

1. every test has the right length and only legal values,
2. every value pair is covered, and
3. it has **at most `2 * a * b` tests**, where `a` and `b` are the two largest entries of `levels`
   (the theoretical minimum is at least `a * b`). With a single parameter the limit is `levels[0]`
   tests and each value must appear at least once.

Returning the full Cartesian product is therefore rejected whenever it is larger than the limit.

**Example:** `levels = [2, 2, 2]` → `[[0,0,0],[0,1,1],[1,0,1],[1,1,0]]` is one valid answer (limit 8).

Constraints: 1–6 parameters; the product of all levels is at most 5000.
""",
    starter='''def pairwise_suite(levels: List[int]) -> List[List[int]]:
    pass
''',
    solution='''def pairwise_suite(levels):
    n = len(levels)
    if n == 1:
        return [[v] for v in range(levels[0])]
    uncovered = set()
    for i in range(n):
        for j in range(i + 1, n):
            for a in range(levels[i]):
                for b in range(levels[j]):
                    uncovered.add((i, j, a, b))
    candidates = list(itertools.product(*[range(k) for k in levels]))
    suite = []
    while uncovered:
        best, best_gain = None, -1
        for c in candidates:
            gain = 0
            for i in range(n):
                ci = c[i]
                for j in range(i + 1, n):
                    if (i, j, ci, c[j]) in uncovered:
                        gain += 1
            if gain > best_gain:
                best, best_gain = c, gain
        for i in range(n):
            for j in range(i + 1, n):
                uncovered.discard((i, j, best[i], best[j]))
        suite.append(list(best))
    return suite
''',
    checker='''def check(args, got, expected):
    try:
        levels = args[0]
        n = len(levels)
        if not isinstance(got, list):
            return False
        for t in got:
            if not isinstance(t, list) or len(t) != n:
                return False
            for i, v in enumerate(t):
                if isinstance(v, bool) or not isinstance(v, int) or v < 0 or v >= levels[i]:
                    return False
        if n == 1:
            return len(got) <= levels[0] and {t[0] for t in got} == set(range(levels[0]))
        top = sorted(levels)[-2:]
        if len(got) > 2 * top[0] * top[1]:
            return False
        seen = set()
        for t in got:
            for i in range(n):
                for j in range(i + 1, n):
                    seen.add((i, j, t[i], t[j]))
        total = sum(levels[i] * levels[j] for i in range(n) for j in range(i + 1, n))
        return len(seen) == total
    except Exception:
        return False
''',
    tests=[
        [[2, 2, 2]],
        [[3, 3, 3, 3]],
        [[2, 3]],
        [[4]],
        [[1, 1, 1]],
        [[2, 2, 2, 2, 2, 2]],
        [[3, 2, 4, 2]],
        [[5, 5, 5]],
        [[4, 4, 4, 4, 4]],
        [[6, 2, 2, 2, 2, 2]],
        [[3, 3, 3, 3, 3, 3]],
        [[1, 5, 1, 5]],
    ],
    examples=2,
    wrong_solutions=[
        '''def pairwise_suite(levels):
    return [list(c) for c in itertools.product(*[range(k) for k in levels])]
''',
        '''def pairwise_suite(levels):
    m = max(levels)
    return [[v % k for k in levels] for v in range(m)]
''',
        '''def pairwise_suite(levels):
    n = len(levels)
    out = []
    for i in range(n):
        for j in range(i + 1, n):
            for a in range(levels[i]):
                for b in range(levels[j]):
                    t = [0] * n
                    t[i], t[j] = a, b
                    out.append(t)
    return out or [[v] for v in range(levels[0])]
''',
    ],
    guide=dict(
        prereqs="*Pairwise Coverage Checker* (solve it first), `itertools.product`, greedy algorithms.",
        intuition="One test covers one value pair for each of the n(n−1)/2 parameter pairs at once. So pick tests "
                  "that knock out as many still-uncovered pairs as possible, and repeat until none are left.",
        hints=[
            "Keep a set of uncovered `(i, j, a, b)` tuples; you are done when it is empty.",
            "Because the full product is at most 5000 tests, you can afford to score every candidate each round.",
            "Each round choose the candidate covering the most uncovered pairs, append it, remove its pairs.",
        ],
        brute_force="Return the Cartesian product: always correct on coverage but exponential in the number of "
                    "parameters — 4 parameters of 4 values is 256 tests where roughly 16–20 suffice. It fails the size limit.",
        approach="1. Build the uncovered set.\n2. Enumerate all candidate tests once.\n3. Loop: score each candidate "
                 "by how many of its pairs are still uncovered; take the best; remove its pairs; append.\n\n"
                 "**Dry run** `levels=[2,2,2]` (12 pairs): `[0,0,0]` covers 3 → 9 left. `[0,1,1]` covers 3 new → 6 left. "
                 "`[1,0,1]` covers 3 → 3 left. `[1,1,0]` covers the last 3. Four tests instead of eight.",
        complexity="Each round costs O(P · n²) for P candidates; there are at most (number of pairs) rounds, in "
                   "practice close to a·b. Space O(P + pairs).",
        pitfalls="- A one-parameter system has no pairs at all: handle it separately so every value still appears.\n"
                 "- Building one test per pair with zeros elsewhere is valid coverage but blows the size limit.\n"
                 "- Forgetting that later picks must be scored against the *remaining* pairs, not the original set.",
        follow_up="Add constraints (forbidden combinations), or seed the suite with mandatory tests before the greedy loop.",
    ),
),
dict(
    id="think-risk-priority",
    title="Risk-Based Test Prioritisation",
    difficulty="Easy",
    pattern="Risk-Based Testing",
    entry="prioritise",
    description=r"""
Each test case is `[name, likelihood, impact, minutes]`: how likely the failure it guards against is
(1–5), how bad that failure would be (1–5), and how long the test takes to run.

Return the **names in execution order** using these rules:

1. higher **risk score** `likelihood * impact` first;
2. ties → higher `impact` first (a rare catastrophe outranks a frequent annoyance);
3. still tied → fewer `minutes` first (cheap information sooner);
4. still tied → name in ascending alphabetical order.

**Example:**
`[["refund", 2, 5, 30], ["typo", 5, 2, 5], ["login", 4, 5, 10]]` → `["login", "refund", "typo"]`

`login` scores 20. `refund` and `typo` both score 10, and `refund` has the higher impact.

Constraints: up to `10^4` cases; names are unique.
""",
    starter='''def prioritise(cases: List[list]) -> List[str]:
    pass
''',
    solution='''def prioritise(cases):
    ordered = sorted(cases, key=lambda c: (-(c[1] * c[2]), -c[2], c[3], c[0]))
    return [c[0] for c in ordered]
''',
    tests=[
        [[["refund", 2, 5, 30], ["typo", 5, 2, 5], ["login", 4, 5, 10]]],
        [[["a", 1, 1, 1]]],
        [[]],
        [[["b", 3, 4, 10], ["a", 3, 4, 10]]],
        [[["slow", 3, 4, 60], ["fast", 3, 4, 5]]],
        [[["x", 4, 3, 1], ["y", 3, 4, 100], ["z", 2, 5, 1]]],
        [[["p", 5, 5, 99], ["q", 1, 1, 1], ["r", 5, 1, 1], ["s", 1, 5, 50]]],
        [[["m", 2, 2, 5], ["n", 1, 4, 5], ["o", 4, 1, 5]]],
        [[["t1", 3, 3, 9], ["t2", 3, 3, 9], ["t0", 3, 3, 9], ["t3", 3, 3, 8]]],
        [[["c%03d" % i, (i * 7) % 5 + 1, (i * 3) % 5 + 1, (i * 11) % 13] for i in range(400)]],
        [[["big", 5, 4, 1], ["bigger", 4, 5, 1000]]],
        [[["z", 2, 3, 4], ["y", 3, 2, 4], ["x", 1, 5, 4], ["w", 1, 5, 4]]],
    ],
    examples=1,
    wrong_solutions=[
        '''def prioritise(cases):
    ordered = sorted(cases, key=lambda c: (-(c[1] * c[2]), c[0]))
    return [c[0] for c in ordered]
''',
        '''def prioritise(cases):
    ordered = sorted(cases, key=lambda c: (-(c[1] * c[2]), -c[1], c[3], c[0]))
    return [c[0] for c in ordered]
''',
        '''def prioritise(cases):
    ordered = sorted(cases, key=lambda c: (-(c[1] * c[2]), -c[2], -c[3], c[0]))
    return [c[0] for c in ordered]
''',
    ],
    guide=dict(
        prereqs="Lesson *Exploratory testing, risk and non-functional categories*. Sorting with a tuple key.",
        intuition="Risk is likelihood times impact. Everything after that is a tie-break, and tie-breaks are just "
                  "extra components of the sort key in order of importance.",
        hints=[
            "Python compares tuples left to right, so a tuple key expresses 'first by this, then by that'.",
            "To sort a number descending inside an ascending sort, negate it.",
            "Key: `(-(l*i), -i, minutes, name)`.",
        ],
        brute_force="Repeatedly scan for the best remaining case with a hand-written comparison (selection sort): "
                    "O(n²), 10⁸ comparisons at the upper limit.",
        approach="Build one composite key and call `sorted` once.\n\n**Dry run** on the example: keys are "
                 "refund `(-10, -5, 30, 'refund')`, typo `(-10, -2, 5, 'typo')`, login `(-20, -5, 10, 'login')`. "
                 "Ascending order of keys: login, refund, typo.",
        complexity="Time O(n log n), space O(n).",
        pitfalls="- Breaking ties by likelihood instead of impact.\n- Sorting minutes descending.\n"
                 "- Skipping the name tie-break, which makes the order depend on input order.",
        follow_up="Add a time budget and return only the cases that fit, or weight by cost: risk per minute.",
    ),
),
]
