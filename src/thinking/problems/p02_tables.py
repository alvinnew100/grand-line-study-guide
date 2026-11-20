import itertools as _it

_FORMAT = r"""
**Table format.** A decision table over `n` yes/no conditions is a list of rules. Each rule is
`[pattern, action]` where `pattern` is a string of length `n` made of `"Y"`, `"N"` and `"-"`
(don't-care) and `action` is a string. An **input** is a string of `n` characters, each `"Y"` or `"N"`.
A rule *matches* an input when every pattern character is `"-"` or equals the input character at that
position.
"""

_SHIP = [["YY-", "free"], ["YN-", "standard"], ["N-Y", "express"], ["N-N", "standard"]]
_LOAN = [["Y---", "reject"], ["NYY-", "approve"], ["NYN-", "review"], ["NNYY", "review"], ["NNYN", "reject"]]
_FULL3 = [["".join(p), "a" if p.count("Y") >= 2 else "b"] for p in _it.product("YN", repeat=3)]
_FULL4 = [["".join(p), "odd" if p.count("Y") % 2 else "even"] for p in _it.product("YN", repeat=4)]
_BIG10 = [["".join(p), "x%d" % (p.count("Y") % 3)] for p in _it.product("YN", repeat=10) if p.count("Y") != 5]

PROBLEMS = [
dict(
    id="think-table-first-match",
    title="Evaluate a Decision Table (First Match)",
    difficulty="Easy",
    pattern="Decision Tables",
    entry="evaluate_first",
    description=_FORMAT + r"""
Many rule engines read a table **top to bottom and stop at the first rule that matches**. Implement
that policy: return the action of the first matching rule, or `default` when no rule matches.

**Example:** `rules = [["YY-","free"],["YN-","standard"],["N-Y","express"],["N-N","standard"]]`,
`inp = "NYY"`, `default = "none"` → `"express"`

**Example:** `rules = [["Y-","a"],["-Y","b"]]`, `inp = "YY"` → `"a"` (both match; the first wins)

Constraints: `0 <= len(rules) <= 10^4`, `0 <= n <= 20`.
""",
    starter='''def evaluate_first(rules: List[List[str]], inp: str, default: str) -> str:
    pass
''',
    solution='''def evaluate_first(rules, inp, default):
    for pattern, action in rules:
        if all(p == "-" or p == c for p, c in zip(pattern, inp)):
            return action
    return default
''',
    tests=[
        [_SHIP, "NYY", "none"],
        [[["Y-", "a"], ["-Y", "b"]], "YY", "none"],
        [[["Y-", "a"], ["-Y", "b"]], "NY", "none"],
        [[["Y-", "a"], ["-Y", "b"]], "NN", "none"],
        [[], "YN", "fallback"],
        [[["", "always"]], "", "never"],
        [_LOAN, "YYYY", "?"],
        [_LOAN, "NNYN", "?"],
        [_LOAN, "NNNN", "manual"],
        [[["---", "catch"], ["YYY", "specific"]], "YYY", "d"],
        [[["YYY", "specific"], ["---", "catch"]], "YYY", "d"],
        [[["YYY", "specific"], ["---", "catch"]], "YYN", "d"],
        [_BIG10, "YNYNYNYNYN", "missing"],
        [_BIG10, "YYYYYYYYYY", "missing"],
    ],
    examples=2,
    wrong_solutions=[
        '''def evaluate_first(rules, inp, default):
    for pattern, action in rules:
        if pattern == inp:
            return action
    return default
''',
        '''def evaluate_first(rules, inp, default):
    out = default
    for pattern, action in rules:
        if all(p == "-" or p == c for p, c in zip(pattern, inp)):
            out = action
    return out
''',
        '''def evaluate_first(rules, inp, default):
    for pattern, action in rules:
        if any(p == c for p, c in zip(pattern, inp)):
            return action
    return default
''',
    ],
    guide=dict(
        prereqs="Lesson *Building a decision table from requirements*. `zip`, `all`.",
        intuition="A pattern is a tiny wildcard match. Walk the rules in order and stop at the first one where "
                  "every position is either a wildcard or equal.",
        hints=[
            "Write a helper `matches(pattern, inp)` first and test it alone.",
            "`all(p == '-' or p == c for p, c in zip(pattern, inp))` is that helper.",
            "Return inside the loop on the first match; return `default` after the loop.",
        ],
        brute_force="Expand every rule into all the concrete inputs it covers (2^d for d dashes) and build a "
                    "dictionary, keeping the first writer. Exponential in the number of dashes.",
        approach="Loop over rules; test the match position by position; return on first success.\n\n"
                 "**Dry run** `inp='NYY'` on the shipping table: `YY-` fails at position 0; `YN-` fails at 0; "
                 "`N-Y` → N=N, dash, Y=Y → match → `express`.",
        complexity="Time O(R · n) for R rules, space O(1).",
        pitfalls="- Comparing with `==` and ignoring don't-cares.\n- Returning the *last* match.\n"
                 "- Forgetting the zero-condition table: an empty pattern matches the empty input.",
        follow_up="Pre-compile patterns into (mask, value) integer pairs so each match is two bit operations.",
    ),
),
dict(
    id="think-table-unique-match",
    title="Evaluate a Decision Table (Unique Match)",
    difficulty="Easy",
    pattern="Decision Tables",
    entry="evaluate_unique",
    description=_FORMAT + r"""
A table that is meant to be **order-independent** must give one answer no matter how its rules are
sorted. Evaluate an input under that stricter policy:

- no rule matches → return `"NO_MATCH"`;
- every matching rule has the same action → return that action (redundant rules are tolerated);
- matching rules disagree → return `"CONFLICT"`.

**Example:** `rules = [["Y-","a"],["-Y","b"]]`, `inp = "YY"` → `"CONFLICT"`

**Example:** `rules = [["Y-","a"],["-Y","a"]]`, `inp = "YY"` → `"a"`

Constraints: up to `10^4` rules, `n <= 20`. No action is literally `"NO_MATCH"` or `"CONFLICT"`.
""",
    starter='''def evaluate_unique(rules: List[List[str]], inp: str) -> str:
    pass
''',
    solution='''def evaluate_unique(rules, inp):
    found = set()
    for pattern, action in rules:
        if all(p == "-" or p == c for p, c in zip(pattern, inp)):
            found.add(action)
    if not found:
        return "NO_MATCH"
    if len(found) > 1:
        return "CONFLICT"
    return found.pop()
''',
    tests=[
        [[["Y-", "a"], ["-Y", "b"]], "YY"],
        [[["Y-", "a"], ["-Y", "a"]], "YY"],
        [[["Y-", "a"], ["-Y", "b"]], "NN"],
        [[["Y-", "a"], ["-Y", "b"]], "YN"],
        [[], "Y"],
        [_SHIP, "YYN"],
        [_LOAN, "NNNY"],
        [_LOAN + [["NNY-", "approve"]], "NNYN"],
        [_LOAN + [["NNY-", "review"]], "NNYY"],
        [[["---", "x"], ["YYY", "x"], ["Y--", "x"]], "YYY"],
        [[["---", "x"], ["YYY", "x"], ["Y--", "y"]], "YYY"],
        [[["---", "x"], ["YYY", "x"], ["Y--", "y"]], "NYY"],
        [_BIG10, "YYYYYNNNNN"],
    ],
    examples=2,
    wrong_solutions=[
        '''def evaluate_unique(rules, inp):
    for pattern, action in rules:
        if all(p == "-" or p == c for p, c in zip(pattern, inp)):
            return action
    return "NO_MATCH"
''',
        '''def evaluate_unique(rules, inp):
    hits = [a for p, a in rules if all(x == "-" or x == c for x, c in zip(p, inp))]
    if not hits:
        return "NO_MATCH"
    return hits[0] if len(hits) == 1 else "CONFLICT"
''',
    ],
    guide=dict(
        prereqs="*Evaluate a Decision Table (First Match)*; sets.",
        intuition="Instead of stopping at the first hit, collect the *distinct actions* of all hits. Zero, one or "
                  "several distinct actions map directly onto the three outcomes.",
        hints=[
            "Reuse the match test from the first-match problem.",
            "Two matching rules with the same action are not a conflict — what should you count?",
            "Add each matching action to a set and inspect its size.",
        ],
        brute_force="For each pair of matching rules compare their actions: O(R²) in the worst case.",
        approach="One pass; a set of actions; branch on its size.\n\n**Dry run** rules `Y-→a`, `-Y→b`, input `YY`: "
                 "both match; set = {a, b}; size 2 → `CONFLICT`.",
        complexity="Time O(R · n), space O(distinct actions).",
        pitfalls="- Treating any two matches as a conflict even when they agree.\n"
                 "- Short-circuiting on the first match, which hides the conflict entirely.",
        follow_up="Return the indices of the disagreeing rules so the author can fix the table.",
    ),
),
dict(
    id="think-table-missing",
    title="Find Missing Combinations in a Decision Table",
    difficulty="Medium",
    pattern="Decision Tables",
    entry="missing_inputs",
    description=_FORMAT + r"""
With `n` binary conditions there are `2^n` possible inputs. A table is **complete** when every one of
them is matched by at least one rule. Given `n` and the rules, return every input that **no rule
matches**, sorted in ascending string order (so `"N"` sorts before `"Y"`).

**Example:** `n = 2`, `rules = [["Y-","a"],["NY","b"]]` → `["NN"]`

**Example:** `n = 3`, `rules = [["YY-","x"],["N-N","y"]]` → `["NNY", "NYY", "YNN", "YNY"]`

Constraints: `0 <= n <= 14`, up to 200 rules. For `n = 0` the only input is the empty string.
""",
    starter='''def missing_inputs(n: int, rules: List[List[str]]) -> List[str]:
    pass
''',
    solution='''def missing_inputs(n, rules):
    covered = set()
    for pattern, _ in rules:
        free = [i for i, ch in enumerate(pattern) if ch == "-"]
        base = list(pattern)
        for combo in itertools.product("NY", repeat=len(free)):
            for i, ch in zip(free, combo):
                base[i] = ch
            covered.add("".join(base))
    out = []
    for p in itertools.product("NY", repeat=n):
        s = "".join(p)
        if s not in covered:
            out.append(s)
    return out
''',
    tests=[
        [2, [["Y-", "a"], ["NY", "b"]]],
        [3, [["YY-", "x"], ["N-N", "y"]]],
        [0, []],
        [0, [["", "a"]]],
        [1, []],
        [3, _SHIP],
        [4, _LOAN],
        [3, [["---", "all"]]],
        [3, _FULL3[:-1]],
        [4, [["Y---", "a"], ["-Y--", "a"], ["--Y-", "a"], ["---Y", "a"]]],
        [10, _BIG10],
        [14, [["Y" + "-" * 13, "a"], ["N" + "-" * 12 + "Y", "b"], ["NN" + "-" * 11 + "N", "c"]]],
        [5, [["YNYNY", "only"]]],
    ],
    examples=2,
    wrong_solutions=[
        '''def missing_inputs(n, rules):
    have = {p for p, _ in rules}
    return [s for s in ("".join(p) for p in itertools.product("NY", repeat=n)) if s not in have]
''',
        '''def missing_inputs(n, rules):
    out = []
    for p in itertools.product("YN", repeat=n):
        s = "".join(p)
        if not any(all(a == "-" or a == b for a, b in zip(pat, s)) for pat, _ in rules):
            out.append(s)
    return out
''',
        '''def missing_inputs(n, rules):
    total = 0
    for pat, _ in rules:
        total += 2 ** pat.count("-")
    if total >= 2 ** n:
        return []
    out = []
    for p in itertools.product("NY", repeat=n):
        s = "".join(p)
        if not any(all(a == "-" or a == b for a, b in zip(pat, s)) for pat, _ in rules):
            out.append(s)
    return out
''',
    ],
    guide=dict(
        prereqs="Lesson *Collapsing tables, contradictions and gaps* (the 2^n completeness rule). `itertools.product`.",
        intuition="Completeness is a counting question: 2^n inputs exist; which are untouched? Either test each "
                  "input against the rules or expand each rule into the inputs it covers.",
        hints=[
            "`itertools.product('NY', repeat=n)` yields all inputs already in ascending order.",
            "For one input, `any(matches(rule, input) for rule in rules)` tells you whether it is covered.",
            "Collect the inputs for which that `any` is false.",
        ],
        brute_force="Check every input against every rule: O(2^n · R · n). At n = 14 and 200 rules that is about "
                    "45 million character comparisons — acceptable, and the simplest correct answer.",
        approach="The reference expands each rule into its covered inputs (2^dashes each) into a set, then lists "
                 "the inputs not in the set.\n\n**Dry run** `n=2`, rules `Y-`, `NY`: `Y-` expands to YN, YY; `NY` to "
                 "NY. All inputs in order: NN (missing), NY, YN, YY → `['NN']`.",
        complexity="Time O(2^n · n + Σ 2^dashes), space O(2^n).",
        pitfalls="- Adding up `2^dashes` per rule and comparing with 2^n: overlapping rules double count, so the "
                 "sum can reach 2^n while gaps remain.\n- Iterating `'YN'` instead of `'NY'` and returning the wrong order.\n"
                 "- Treating patterns as literal strings.",
        follow_up="Report the gaps as collapsed patterns with don't-cares rather than as raw inputs.",
    ),
),
dict(
    id="think-table-contradictions",
    title="Find Contradictory Rules",
    difficulty="Medium",
    pattern="Decision Tables",
    entry="contradictions",
    description=_FORMAT + r"""
Two rules **contradict** each other when at least one input matches both of them and their actions
differ. Return every contradictory pair as `[i, j]` with `i < j` (0-based rule indices), sorted
ascending by `i` then `j`.

Two rules that overlap but share an action are merely redundant and must not be reported.

**Example:** `rules = [["Y-","a"],["-Y","b"],["NN","c"]]` → `[[0, 1]]` (input `"YY"` matches rules 0 and 1)

**Example:** `rules = [["Y-","a"],["N-","b"]]` → `[]`

Constraints: up to 400 rules, `n <= 30`.
""",
    starter='''def contradictions(rules: List[List[str]]) -> List[List[int]]:
    pass
''',
    solution='''def contradictions(rules):
    out = []
    for i in range(len(rules)):
        pi, ai = rules[i]
        for j in range(i + 1, len(rules)):
            pj, aj = rules[j]
            if ai == aj:
                continue
            if all(a == "-" or b == "-" or a == b for a, b in zip(pi, pj)):
                out.append([i, j])
    return out
''',
    tests=[
        [[["Y-", "a"], ["-Y", "b"], ["NN", "c"]]],
        [[["Y-", "a"], ["N-", "b"]]],
        [[]],
        [[["--", "a"]]],
        [[["--", "a"], ["--", "b"], ["--", "a"]]],
        [[["Y-", "a"], ["-Y", "a"]]],
        [_SHIP],
        [_LOAN + [["NNY-", "approve"]]],
        [_LOAN + [["----", "reject"]]],
        [[["YNY", "p"], ["YNY", "q"]]],
        [[["Y--", "p"], ["-N-", "q"], ["--Y", "r"], ["NYN", "s"]]],
        [[["".join(p), "a%d" % (i % 3)] for i, p in enumerate(_it.product("YN-", repeat=4))]],
        [[["-" * 30, "x"], ["Y" * 30, "y"], ["N" * 30, "x"], ["Y" * 29 + "N", "z"]]],
    ],
    examples=2,
    wrong_solutions=[
        '''def contradictions(rules):
    out = []
    for i in range(len(rules)):
        for j in range(i + 1, len(rules)):
            if rules[i][0] == rules[j][0] and rules[i][1] != rules[j][1]:
                out.append([i, j])
    return out
''',
        '''def contradictions(rules):
    out = []
    for i in range(len(rules)):
        for j in range(i + 1, len(rules)):
            if all(a == "-" or b == "-" or a == b for a, b in zip(rules[i][0], rules[j][0])):
                out.append([i, j])
    return out
''',
        '''def contradictions(rules):
    out = []
    for i in range(len(rules)):
        for j in range(i + 1, len(rules)):
            if rules[i][1] != rules[j][1] and any(a == "-" or b == "-" or a == b for a, b in zip(rules[i][0], rules[j][0])):
                out.append([i, j])
    return out
''',
    ],
    guide=dict(
        prereqs="Lesson *Collapsing tables, contradictions and gaps*.",
        intuition="You do not need to enumerate inputs. Two patterns share an input exactly when no position "
                  "forces different values: one says Y and the other says N.",
        hints=[
            "When do the patterns `Y-N` and `-YN` overlap? Build an input that satisfies both.",
            "Position by position, the pair is compatible if either side is `-` or both are equal.",
            "Report `[i, j]` when all positions are compatible and the actions differ.",
        ],
        brute_force="Enumerate all 2^n inputs, collect the matching rules of each, and report pairs with different "
                    "actions. Impossible at n = 30 (a billion inputs).",
        approach="Double loop over pairs; skip equal actions; check positional compatibility.\n\n"
                 "**Dry run** rules `Y-→a`, `-Y→b`, `NN→c`. Pair (0,1): pos 0 Y vs `-` ok, pos 1 `-` vs Y ok → overlap, "
                 "actions differ → report. Pair (0,2): Y vs N clash → disjoint. Pair (1,2): pos 1 Y vs N clash → disjoint.",
        complexity="Time O(R² · n), space O(1) besides the output.",
        pitfalls="- Reporting redundant pairs that agree on the action.\n- Requiring identical patterns.\n"
                 "- Using `any` instead of `all` for the compatibility test.",
        follow_up="Return a witness input for each contradiction: take Y/N from whichever side is not a dash.",
    ),
),
dict(
    id="think-table-collapse",
    title="Collapse a Decision Table to Minimum Rules",
    difficulty="Hard",
    pattern="Decision Tables",
    entry="collapse_table",
    description=_FORMAT + r"""
You are given `n` and a **consistent** table (whenever two rules match the same input they have the
same action). It may be incomplete. Produce an **equivalent table with as few rules as possible**:

- for every one of the `2^n` inputs, your table must be consistent and give the same action as the
  original; an input that matched nothing originally must still match nothing;
- your table must have **no more rules than the true minimum** for that behaviour. Rules in your
  answer may overlap as long as they agree.

Any table meeting both conditions is accepted; rule order does not matter.

**Example:** `n = 2`, `rules = [["YY","a"],["YN","a"],["NY","a"],["NN","b"]]` →
`[["Y-","a"],["-Y","a"],["NN","b"]]` (three rules; `a` needs two overlapping rules)

**Example:** `n = 2`, `rules = [["YY","go"],["YN","go"]]` → `[["Y-","go"]]`

Constraints: `0 <= n <= 4`, at most 16 rules, at most 4 distinct actions.
""",
    starter='''def collapse_table(n: int, rules: List[List[str]]) -> List[List[str]]:
    pass
''',
    solution='''def collapse_table(n, rules):
    def matches(pat, s):
        return all(a == "-" or a == b for a, b in zip(pat, s))
    inputs = ["".join(p) for p in itertools.product("NY", repeat=n)]
    act = {}
    for s in inputs:
        for pat, a in rules:
            if matches(pat, s):
                act[s] = a
                break
    cubes = ["".join(p) for p in itertools.product("NY-", repeat=n)]
    out = []
    for a in sorted(set(act.values())):
        target = frozenset(s for s in inputs if act.get(s) == a)
        valid = []
        for c in cubes:
            cov = frozenset(s for s in inputs if matches(c, s))
            if cov <= target:
                valid.append((c, cov))
        primes = [(c, cov) for c, cov in valid if not any(cov < other for _, other in valid)]
        done = False
        for k in range(1, len(primes) + 1):
            for combo in itertools.combinations(primes, k):
                got = frozenset().union(*[cov for _, cov in combo])
                if got == target:
                    out.extend([c, a] for c, _ in combo)
                    done = True
                    break
            if done:
                break
    return out
''',
    checker='''def check(args, got, expected):
    try:
        import itertools
        n, rules = args
        if not isinstance(got, list) or len(got) > len(expected):
            return False
        for r in got:
            if not isinstance(r, list) or len(r) != 2:
                return False
            if not isinstance(r[0], str) or not isinstance(r[1], str):
                return False
            if len(r[0]) != n or any(ch not in "YN-" for ch in r[0]):
                return False
        def acts(table, s):
            return {a for pat, a in table if all(x == "-" or x == y for x, y in zip(pat, s))}
        for p in itertools.product("NY", repeat=n):
            s = "".join(p)
            if acts(rules, s) != acts(got, s):
                return False
        return True
    except Exception:
        return False
''',
    tests=[
        [2, [["YY", "a"], ["YN", "a"], ["NY", "a"], ["NN", "b"]]],
        [2, [["YY", "go"], ["YN", "go"]]],
        [0, []],
        [0, [["", "only"]]],
        [1, [["Y", "a"], ["N", "a"]]],
        [1, [["Y", "a"], ["N", "b"]]],
        [3, _FULL3],
        [4, _FULL4],
        [3, [["NNN", "a"], ["NNY", "a"], ["NYY", "a"], ["YYY", "a"], ["YNN", "b"]]],
        [3, [["NNY", "a"], ["NYY", "a"], ["NNN", "a"], ["YYY", "a"], ["YYN", "a"], ["YNN", "a"]]],
        [4, [["".join(p), "hi" if p[0] == "Y" or (p[1] == "Y" and p[2] == "Y") else "lo"] for p in _it.product("YN", repeat=4)]],
        [3, _SHIP],
        [4, _LOAN],
        [4, [["".join(p), "t"] for p in _it.product("YN", repeat=4) if "".join(p) not in ("NNNN", "YYYY")]],
        [4, [["Y---", "a"], ["YY--", "a"], ["NNNN", "b"], ["NNNY", "b"], ["NNY-", "c"]]],
    ],
    examples=2,
    wrong_solutions=[
        '''def collapse_table(n, rules):
    return rules
''',
        '''def collapse_table(n, rules):
    rules = [list(r) for r in rules]
    changed = True
    while changed:
        changed = False
        for i in range(len(rules)):
            for j in range(i + 1, len(rules)):
                a, b = rules[i], rules[j]
                if a[1] != b[1]:
                    continue
                diff = [k for k in range(n) if a[0][k] != b[0][k]]
                if len(diff) == 1 and "-" not in (a[0][diff[0]], b[0][diff[0]]):
                    k = diff[0]
                    rules[i] = [a[0][:k] + "-" + a[0][k + 1:], a[1]]
                    del rules[j]
                    changed = True
                    break
            if changed:
                break
    return rules
''',
        '''def collapse_table(n, rules):
    acts = sorted({a for _, a in rules})
    return [["-" * n, a] for a in acts[:1]]
''',
    ],
    guide=dict(
        prereqs="Lesson *Collapsing tables, contradictions and gaps*. Helpful: Karnaugh maps / Quine–McCluskey, "
                "`itertools.combinations`.",
        intuition="A rule with dashes is a 'cube' covering 2^dashes inputs. For one action, any cube lying entirely "
                  "inside that action's inputs is legal. The job is to cover each action's inputs with the fewest "
                  "legal cubes — and since n ≤ 4 there are only 3^4 = 81 cubes, exhaustive search is affordable.",
        hints=[
            "First turn the table into a map `input -> action` for all 2^n inputs (unmatched inputs are absent).",
            "For a given action, list every pattern over `Y/N/-` whose covered inputs all have that action. "
            "Drop any pattern whose coverage is strictly inside another's (keep only the maximal ones).",
            "Try subsets of those maximal patterns in increasing size until one covers every input of the action.",
        ],
        brute_force="Repeatedly merge two rules that differ in exactly one position and share an action. It is "
                    "what people do by hand, but it never produces *overlapping* rules and its result depends on merge "
                    "order, so it can stop above the minimum (cyclic layouts get stuck at 3 rules where 2 suffice).",
        approach="1. Expand to the input→action map.\n2. Per action: enumerate the 3^n patterns, keep those fully "
                 "inside the action's input set, discard non-maximal ones (these are the *prime implicants*).\n"
                 "3. Search combinations of primes by increasing size for an exact cover of the action's inputs.\n"
                 "4. Concatenate the per-action answers — actions are independent because rules of different "
                 "actions may never overlap.\n\n**Dry run** example 1: action `a` owns {YY, YN, NY}. Legal patterns: "
                 "YY, YN, NY, `Y-`, `-Y`. Maximal: `Y-`, `-Y`. One prime alone covers only two inputs; the pair covers "
                 "all three → 2 rules. Action `b` owns {NN} → `NN`. Total 3.",
        complexity="At most 81 patterns × 16 inputs to build primes; the cover search is exponential in the number "
                   "of primes but that number is tiny for n ≤ 4. Space O(3^n).",
        pitfalls="- Merging across unmatched inputs: a gap must stay a gap.\n"
                 "- Insisting on disjoint rules; the minimum often needs overlap.\n"
                 "- Minimising actions jointly — they are independent sub-problems.",
        follow_up="For larger n, exact minimisation is NP-hard; production tools use heuristics such as Espresso.",
    ),
),
dict(
    id="think-table-add-condition",
    title="Add a New Condition to a Decision Table",
    difficulty="Medium",
    pattern="Decision Tables",
    entry="add_condition",
    description=_FORMAT + r"""
The business adds one new yes/no condition, appended as the **last** position of every pattern, with
an *override policy*: when the new condition is `Y`, every rule whose action is listed in `affected`
must instead produce `override`. All other behaviour is unchanged.

Rewrite the table, processing rules in their original order:

- a rule whose action is **in** `affected` and differs from `override` becomes two rules, in this
  order: `pattern + "Y"` → `override`, then `pattern + "N"` → original action;
- every other rule becomes one rule `pattern + "-"` with its original action.

**Example:** `rules = [["Y","approve"],["N","reject"]]`, `affected = ["approve"]`, `override = "review"` →
`[["YY","review"],["YN","approve"],["N-","reject"]]`

(New condition: "customer is on the watch list" sends approvals to manual review.)

Constraints: up to `10^4` rules.
""",
    starter='''def add_condition(rules: List[List[str]], affected: List[str], override: str) -> List[List[str]]:
    pass
''',
    solution='''def add_condition(rules, affected, override):
    hit = set(affected)
    out = []
    for pattern, action in rules:
        if action in hit and action != override:
            out.append([pattern + "Y", override])
            out.append([pattern + "N", action])
        else:
            out.append([pattern + "-", action])
    return out
''',
    tests=[
        [[["Y", "approve"], ["N", "reject"]], ["approve"], "review"],
        [_SHIP, ["free"], "standard"],
        [[], ["a"], "b"],
        [_SHIP, [], "blocked"],
        [_SHIP, ["free", "standard", "express"], "blocked"],
        [_LOAN, ["approve", "review"], "review"],
        [[["", "ship"]], ["ship"], "hold"],
        [_LOAN, ["nothing"], "x"],
        [[["Y-", "a"], ["-Y", "a"], ["NN", "b"]], ["a"], "b"],
        [_FULL3, ["a"], "c"],
        [[["--", "same"]], ["same"], "same"],
        [_BIG10[:500], ["x0", "x2"], "x1"],
    ],
    examples=2,
    wrong_solutions=[
        '''def add_condition(rules, affected, override):
    out = []
    for pattern, action in rules:
        if action in affected:
            out.append([pattern + "Y", override])
            out.append([pattern + "N", action])
        else:
            out.append([pattern + "-", action])
    return out
''',
        '''def add_condition(rules, affected, override):
    out = []
    for pattern, action in rules:
        if action in affected and action != override:
            out.append([pattern + "N", action])
            out.append([pattern + "Y", override])
        else:
            out.append([pattern + "-", action])
    return out
''',
        '''def add_condition(rules, affected, override):
    out = []
    for pattern, action in rules:
        out.append([pattern + "Y", override if action in affected else action])
        out.append([pattern + "N", action])
    return out
''',
    ],
    guide=dict(
        prereqs="Lesson *Updating a table when the rules change*.",
        intuition="A new condition doubles the input space. Rules that the new policy does not touch absorb the "
                  "doubling with a don't-care; only the touched rules must actually be split.",
        hints=[
            "For an untouched rule, what single character expresses 'the new condition is irrelevant'?",
            "A touched rule needs one copy for new=Y (overridden) and one for new=N (as before).",
            "If a rule's action already equals `override`, splitting would create two rules with the same action — "
            "keep it as one dashed rule.",
        ],
        brute_force="Expand the old table into all 2^n inputs, double them to 2^(n+1), compute each action and emit "
                    "one fully specified rule per input: correct behaviour but an exponentially larger table.",
        approach="Single pass with a set for `affected`.\n\n**Dry run** rule `Y→approve` with affected={approve}, "
                 "override=review: emit `YY→review`, `YN→approve`. Rule `N→reject`: not affected → `N-→reject`.",
        complexity="Time O(R · n) for string building, output at most 2R rules.",
        pitfalls="- Splitting rules that already produce the override action (needless growth).\n"
                 "- Emitting the N copy before the Y copy (the required order is Y first).\n"
                 "- Splitting every rule mechanically.",
        follow_up="Insert the condition at an arbitrary position, or apply the override only to rules matching a filter pattern.",
    ),
),
dict(
    id="think-table-diff",
    title="Diff Two Decision Tables",
    difficulty="Medium",
    pattern="Decision Tables",
    entry="table_diff",
    description=_FORMAT + r"""
A policy changed and you hold the `old` and `new` tables over the same `n` conditions. Both are
evaluated **first-match**, and an input that matches no rule yields the string `default`.

Return every input whose outcome changed, as `[input, old_action, new_action]`, sorted by input in
ascending string order (`"N"` before `"Y"`). This list is exactly the regression-test set for the
policy change.

**Example:** `n = 2`, `old = [["Y-","free"],["N-","paid"]]`, `new = [["YY","free"],["--","paid"]]`,
`default = "none"` → `[["YN", "free", "paid"]]`

Constraints: `0 <= n <= 12`, up to 100 rules per table.
""",
    starter='''def table_diff(n: int, old: List[List[str]], new: List[List[str]], default: str) -> List[List[str]]:
    pass
''',
    solution='''def table_diff(n, old, new, default):
    def run(table, s):
        for pat, a in table:
            if all(x == "-" or x == y for x, y in zip(pat, s)):
                return a
        return default
    out = []
    for p in itertools.product("NY", repeat=n):
        s = "".join(p)
        a, b = run(old, s), run(new, s)
        if a != b:
            out.append([s, a, b])
    return out
''',
    tests=[
        [2, [["Y-", "free"], ["N-", "paid"]], [["YY", "free"], ["--", "paid"]], "none"],
        [2, [["Y-", "a"]], [["Y-", "a"]], "d"],
        [0, [], [], "d"],
        [0, [["", "a"]], [], "d"],
        [1, [], [["Y", "a"]], "d"],
        [3, _SHIP, _SHIP[::-1], "none"],
        [3, _SHIP, _SHIP[:2], "none"],
        [4, _LOAN, [["Y---", "reject"], ["NY--", "approve"], ["NNYY", "review"]], "reject"],
        [3, _FULL3, [["YY-", "a"], ["Y-Y", "a"], ["-YY", "a"], ["---", "b"]], "zzz"],
        [3, _FULL3, [["Y--", "a"], ["---", "b"]], "zzz"],
        [2, [["--", "x"]], [["--", "y"]], "d"],
        [10, _BIG10, _BIG10[:300] + [["-" * 10, "x1"]], "x1"],
        [12, [["Y" + "-" * 11, "a"]], [["-" * 11 + "Y", "a"]], "b"],
    ],
    examples=1,
    wrong_solutions=[
        '''def table_diff(n, old, new, default):
    def run(table, s):
        for pat, a in table:
            if all(x == "-" or x == y for x, y in zip(pat, s)):
                return a
        return default
    out = []
    for p in itertools.product("YN", repeat=n):
        s = "".join(p)
        a, b = run(old, s), run(new, s)
        if a != b:
            out.append([s, a, b])
    return out
''',
        '''def table_diff(n, old, new, default):
    def run(table, s):
        r = default
        for pat, a in table:
            if all(x == "-" or x == y for x, y in zip(pat, s)):
                r = a
        return r
    out = []
    for p in itertools.product("NY", repeat=n):
        s = "".join(p)
        a, b = run(old, s), run(new, s)
        if a != b:
            out.append([s, a, b])
    return out
''',
        '''def table_diff(n, old, new, default):
    o = {p: a for p, a in old}
    return sorted([p, o.get(p, default), a] for p, a in new if o.get(p, default) != a)
''',
    ],
    guide=dict(
        prereqs="*Evaluate a Decision Table (First Match)*; lesson *Updating a table when the rules change*.",
        intuition="Tables are small finite functions. Two functions over 2^n inputs are compared most reliably by "
                  "evaluating both everywhere — comparing the rule text tells you nothing, because very different "
                  "rule lists can mean the same thing.",
        hints=[
            "Reuse your first-match evaluator as an inner function.",
            "`itertools.product('NY', repeat=n)` enumerates inputs in the required order.",
            "Append `[s, old_result, new_result]` whenever the two results differ.",
        ],
        brute_force="This enumeration *is* the brute force and it is the right tool at n ≤ 12 (4096 inputs).",
        approach="Evaluate both tables on every input and collect differences.\n\n**Dry run** example: NN → paid/paid, "
                 "NY → paid/paid, YN → free vs (YY fails, `--` matches) paid → record, YY → free/free.",
        complexity="Time O(2^n · (R_old + R_new) · n), space O(output).",
        pitfalls="- Diffing rule text instead of behaviour.\n- Forgetting the default on unmatched inputs.\n"
                 "- Last-match evaluation, or iterating `'YN'` and breaking the sort order.",
        follow_up="Summarise the changed inputs as collapsed patterns so a reviewer can read the change as a rule.",
    ),
),
]
