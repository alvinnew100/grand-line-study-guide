PROBLEMS = [
dict(
    id="tf-version-constraint",
    title="Match a version against a constraint",
    difficulty="Medium",
    pattern="Versions",
    entry="satisfies",
    description=r"""
`required_version`, `required_providers` and a module's `version` argument all take a **version constraint**
such as `">= 1.5, < 2.0"` or `"~> 6.0"`. Write `satisfies(version, constraint)` that returns `True` when the
version is allowed.

**Versions** are one to three whole numbers joined by dots: `"6"`, `"6.4"`, `"6.4.1"`. Missing parts count as
zero, so `1.2` and `1.2.0` are the same version. Compare versions number by number from the left, as numbers:
`1.10.0` is newer than `1.9.0`.

**Constraints** are one or more terms separated by commas. All terms must hold. A term is an optional
operator, optional spaces, and a version:

| Operator | Meaning |
|---|---|
| `=` or none | exactly this version |
| `!=` | any version except this one |
| `>`, `>=`, `<`, `<=` | ordinary comparisons |
| `~>` | "pessimistic": only the **last number written** may increase |

For `~>`, the term's version is always written with two or three numbers:

- `~> 1.2` allows `>= 1.2.0` and `< 2.0.0`;
- `~> 1.2.3` allows `>= 1.2.3` and `< 1.3.0`.

**Example 1:** `satisfies("6.4.0", "~> 6.0")` → `True`

**Example 2:** `satisfies("1.10.2", ">= 1.5, < 1.10")` → `False`
""",
    starter='''def satisfies(version, constraint):
    pass
''',
    solution='''def satisfies(version, constraint):
    def numbers(text):
        return [int(part) for part in text.strip().split(".")]

    def padded(nums):
        return tuple(nums + [0] * (3 - len(nums)))

    v = padded(numbers(version))
    for term in constraint.split(","):
        term = term.strip()
        operator = "="
        for candidate in ("~>", ">=", "<=", "!=", ">", "<", "="):
            if term.startswith(candidate):
                operator = candidate
                term = term[len(candidate):]
                break
        written = numbers(term)
        c = padded(written)
        if operator == "=":
            ok = v == c
        elif operator == "!=":
            ok = v != c
        elif operator == ">":
            ok = v > c
        elif operator == ">=":
            ok = v >= c
        elif operator == "<":
            ok = v < c
        elif operator == "<=":
            ok = v <= c
        else:
            if len(written) == 2:
                ceiling = (written[0] + 1, 0, 0)
            else:
                ceiling = (written[0], written[1] + 1, 0)
            ok = c <= v < ceiling
        if not ok:
            return False
    return True
''',
    tests=[
        ["6.4.0", "~> 6.0"],
        ["1.10.2", ">= 1.5, < 1.10"],
        ["7.0.0", "~> 6.0"],
        ["6.0.0", "~> 6.0"],
        ["1.2.9", "~> 1.2.3"],
        ["1.3.0", "~> 1.2.3"],
        ["1.10.0", "> 1.9"],
        ["1.2", "1.2.0"],
        ["1.2.1", "1.2"],
        ["2.0.0", ">= 1.0, != 2.0.0, < 3"],
        ["3", ">= 1.0, != 2.0.0, < 3"],
        ["1.5.7", ">=1.5.7,<=1.5.7"],
        ["0.14.0", "~> 0.13.0"],
        ["1.14.3", " >= 1.6 ,  ~> 1.14 "],
        ["4.67.0", "~> 4.9"],
    ],
    examples=2,
    wrong_solutions=[
        '''def satisfies(version, constraint):
    def pad(t):
        p = t.strip().split(".")
        return p + ["0"] * (3 - len(p))
    v = pad(version)
    for term in constraint.split(","):
        term = term.strip(); op = "="
        for cand in ("~>", ">=", "<=", "!=", ">", "<", "="):
            if term.startswith(cand):
                op, term = cand, term[len(cand):]; break
        w = term.strip().split("."); c = pad(term)
        if op == "~>":
            hi = [str(int(w[0]) + 1), "0", "0"] if len(w) == 2 else [w[0], str(int(w[1]) + 1), "0"]
            ok = c <= v < hi
        else:
            ok = {"=": v == c, "!=": v != c, ">": v > c, ">=": v >= c, "<": v < c, "<=": v <= c}[op]
        if not ok:
            return False
    return True
''',
        '''def satisfies(version, constraint):
    def pad(t):
        n = [int(p) for p in t.strip().split(".")]
        return tuple(n + [0] * (3 - len(n)))
    v = pad(version)
    for term in constraint.split(","):
        term = term.strip(); op = "="
        for cand in ("~>", ">=", "<=", "!=", ">", "<", "="):
            if term.startswith(cand):
                op, term = cand, term[len(cand):]; break
        c = pad(term)
        ok = {"=": v == c, "!=": v != c, ">": v > c, ">=": v >= c, "<": v < c, "<=": v <= c, "~>": v >= c}[op]
        if not ok:
            return False
    return True
''',
        '''def satisfies(version, constraint):
    def pad(t):
        n = [int(p) for p in t.strip().split(".")]
        return tuple(n + [0] * (3 - len(n)))
    v = pad(version)
    for term in constraint.split(","):
        term = term.strip(); op = "="
        for cand in ("~>", ">=", "<=", "!=", ">", "<", "="):
            if term.startswith(cand):
                op, term = cand, term[len(cand):]; break
        c = pad(term)
        if op == "~>":
            ok = c <= v < (c[0], c[1] + 1, 0)
        else:
            ok = {"=": v == c, "!=": v != c, ">": v > c, ">=": v >= c, "<": v < c, "<=": v <= c}[op]
        if not ok:
            return False
    return True
''',
    ],
    guide=dict(
        prereqs="Version constraints in *Installing Terraform, signing in safely and creating a first resource* and *Module gotchas and versioning: file paths, inline blocks and releases*. Comparing tuples in Python.",
        intuition="A version is a short list of numbers, and Python compares tuples exactly the way versions should be compared: first numbers first, and only on a tie the next. Once both sides are tuples of three integers, six of the seven operators are one comparison each. The seventh, `~>`, is a range whose lower end is the version written and whose upper end is found by bumping the number *before* the last one written.",
        hints=[
            "Convert each version to a tuple of three integers, padding with zeros. Never compare the strings.",
            "When reading the operator, try the two-character ones before the one-character ones, or `>=` will be read as `>` followed by `=1.5`.",
            "For `~>` you need to know how many numbers were *written*, so look at that before padding.",
        ],
        brute_force="Expand each term into the full list of versions it allows within some limit and test membership. That is unbounded in general. Comparing tuples answers each term in constant time.",
        approach="""1. `v = padded(numbers(version))`.
2. Split the constraint on commas; for each term strip spaces and peel off the operator (default `=`).
3. `written = numbers(term)`, `c = padded(written)`.
4. Ordinary operators: one tuple comparison.
5. `~>`: with two numbers written, `ceiling = (major + 1, 0, 0)`; with three, `ceiling = (major, minor + 1, 0)`. The term holds when `c <= v < ceiling`.
6. Return `False` at the first failing term, `True` if none fails.

**Dry run:** `satisfies("1.14.3", " >= 1.6 ,  ~> 1.14 ")`.

| term | operator | c | test | result |
|---|---|---|---|---|
| `>= 1.6` | >= | (1, 6, 0) | (1, 14, 3) >= (1, 6, 0) | true: 14 > 6 as numbers |
| `~> 1.14` | ~> | (1, 14, 0) | (1, 14, 0) <= v < (2, 0, 0) | true |

Compared as text, `"1.14"` would sort before `"1.6"` and the first term would wrongly fail.""",
        complexity="Time O(t) for t terms, each a constant amount of work. Space O(1).",
        pitfalls="Comparing strings (first wrong solution): `\"10\" < \"9\"` as text. Treating `~>` as a plain `>=` (second wrong solution), which lets a breaking major release through. Always bumping the minor number for `~>` (third wrong solution): `~> 6.0` must allow `6.4.0`, so the number of parts written matters. Matching `>` before `>=`. Treating `1.2` as different from `1.2.0`.",
        follow_up="Real versions may end in a pre-release label such as `-beta1`. Terraform matches those only when the constraint names that exact version. Add that rule.",
    ),
),
dict(
    id="tf-version-select",
    title="Select a provider version like terraform init",
    difficulty="Medium",
    pattern="Versions",
    entry="selectProvider",
    description=r"""
`terraform init` decides which version of each provider to install. It has to respect every constraint in the
configuration and also the **dependency lock file** (`.terraform.lock.hcl`), which records the version chosen
last time so that everyone on the team installs the same one. Write
`selectProvider(available, constraints, locked, upgrade)`.

- `available`: list of published versions, each written with three numbers (`"6.4.0"`), in any order.
- `constraints`: list of constraint strings, one from each module that requires the provider. **All** must
  hold. An empty list allows any version. Constraint syntax is the same as in *Match a version against a
  constraint*: comma-separated terms with `=` (or no operator), `!=`, `>`, `>=`, `<`, `<=`, `~>`; versions
  inside constraints have one to three numbers (two or three after `~>`); missing parts count as zero.
- `locked`: the version in the lock file, or `None` when there is no lock entry.
- `upgrade`: `True` when the command was `terraform init -upgrade`.

**Rules**

1. If there is a locked version and `upgrade` is false:
   - if the locked version meets every constraint, return it, even when newer versions are available;
   - otherwise return `"Error: locked version <locked> does not match constraints"`.
2. Otherwise (no lock entry, or `-upgrade`): return the **newest** available version that meets every
   constraint. If there is none, return `"Error: no available version matches"`.

**Example 1:** `selectProvider(["6.0.0", "6.4.0", "7.1.0"], ["~> 6.0"], None, False)` → `"6.4.0"`

**Example 2:** `selectProvider(["6.0.0", "6.4.0", "7.1.0"], ["~> 6.0"], "6.0.0", False)` → `"6.0.0"`
""",
    starter='''def selectProvider(available, constraints, locked, upgrade):
    pass
''',
    solution='''def selectProvider(available, constraints, locked, upgrade):
    def numbers(text):
        return [int(part) for part in text.strip().split(".")]

    def padded(nums):
        return tuple(nums + [0] * (3 - len(nums)))

    def term_ok(v, term):
        term = term.strip()
        operator = "="
        for candidate in ("~>", ">=", "<=", "!=", ">", "<", "="):
            if term.startswith(candidate):
                operator = candidate
                term = term[len(candidate):]
                break
        written = numbers(term)
        c = padded(written)
        if operator == "=":
            return v == c
        if operator == "!=":
            return v != c
        if operator == ">":
            return v > c
        if operator == ">=":
            return v >= c
        if operator == "<":
            return v < c
        if operator == "<=":
            return v <= c
        if len(written) == 2:
            ceiling = (written[0] + 1, 0, 0)
        else:
            ceiling = (written[0], written[1] + 1, 0)
        return c <= v < ceiling

    def allowed(version):
        v = padded(numbers(version))
        return all(term_ok(v, term) for constraint in constraints for term in constraint.split(","))

    if locked is not None and not upgrade:
        if allowed(locked):
            return locked
        return "Error: locked version " + locked + " does not match constraints"

    candidates = [version for version in available if allowed(version)]
    if not candidates:
        return "Error: no available version matches"
    return max(candidates, key=lambda version: padded(numbers(version)))
''',
    tests=[
        [["6.0.0", "6.4.0", "7.1.0"], ["~> 6.0"], None, False],
        [["6.0.0", "6.4.0", "7.1.0"], ["~> 6.0"], "6.0.0", False],
        [["6.0.0", "6.4.0", "7.1.0"], ["~> 6.0"], "6.0.0", True],
        [["6.0.0", "6.4.0", "7.1.0"], [], None, False],
        [[], ["~> 6.0"], None, False],
        [["6.0.0", "6.4.0", "7.1.0"], ["~> 7.0"], "6.4.0", False],
        [["6.0.0", "6.4.0", "7.1.0"], ["~> 7.0"], "6.4.0", True],
        [["6.9.0", "6.10.0", "6.2.0"], [">= 6.0"], None, False],
        [["6.0.0", "6.4.0", "6.8.0", "7.1.0"], [">= 6.0", "< 6.8", "!= 6.4.0"], None, False],
        [["6.0.0", "6.4.0", "6.8.0", "7.1.0"], [">= 6.2, < 7.0", "~> 6.4"], None, False],
        [["6.0.0", "6.4.0", "6.8.0", "7.1.0"], ["~> 6.0", ">= 7.0"], None, False],
        [["6.4.0"], ["~> 6.0"], "6.2.0", False],
        [["3.0.0", "3.1.4", "3.1.10", "3.2.0"], ["~> 3.1.0"], None, False],
        [["1.0.0", "2.0.0"], ["> 2"], "2.0.0", True],
        [[f"5.{i}.{j}" for i in range(30) for j in range(4)], ["~> 5.9", "< 5.21.2"], None, False],
    ],
    examples=2,
    wrong_solutions=[
        '''def selectProvider(available, constraints, locked, upgrade):
    def pad(t):
        n = [int(p) for p in t.strip().split(".")]
        return tuple(n + [0] * (3 - len(n)))
    def term_ok(v, term):
        term = term.strip(); op = "="
        for cand in ("~>", ">=", "<=", "!=", ">", "<", "="):
            if term.startswith(cand):
                op, term = cand, term[len(cand):]; break
        w = [int(p) for p in term.strip().split(".")]; c = pad(term)
        if op == "~>":
            return c <= v < ((w[0] + 1, 0, 0) if len(w) == 2 else (w[0], w[1] + 1, 0))
        return {"=": v == c, "!=": v != c, ">": v > c, ">=": v >= c, "<": v < c, "<=": v <= c}[op]
    def allowed(ver):
        return all(term_ok(pad(ver), t) for c in constraints for t in c.split(","))
    cands = [a for a in available if allowed(a)]
    if not cands:
        return "Error: no available version matches"
    return max(cands, key=pad)
''',
        '''def selectProvider(available, constraints, locked, upgrade):
    def pad(t):
        n = [int(p) for p in t.strip().split(".")]
        return tuple(n + [0] * (3 - len(n)))
    def term_ok(v, term):
        term = term.strip(); op = "="
        for cand in ("~>", ">=", "<=", "!=", ">", "<", "="):
            if term.startswith(cand):
                op, term = cand, term[len(cand):]; break
        w = [int(p) for p in term.strip().split(".")]; c = pad(term)
        if op == "~>":
            return c <= v < ((w[0] + 1, 0, 0) if len(w) == 2 else (w[0], w[1] + 1, 0))
        return {"=": v == c, "!=": v != c, ">": v > c, ">=": v >= c, "<": v < c, "<=": v <= c}[op]
    def allowed(ver):
        return all(term_ok(pad(ver), t) for c in constraints for t in c.split(","))
    if locked is not None and not upgrade:
        return locked if allowed(locked) else "Error: locked version " + locked + " does not match constraints"
    cands = [a for a in available if allowed(a)]
    if not cands:
        return "Error: no available version matches"
    return max(cands)
''',
        '''def selectProvider(available, constraints, locked, upgrade):
    def pad(t):
        n = [int(p) for p in t.strip().split(".")]
        return tuple(n + [0] * (3 - len(n)))
    def term_ok(v, term):
        term = term.strip(); op = "="
        for cand in ("~>", ">=", "<=", "!=", ">", "<", "="):
            if term.startswith(cand):
                op, term = cand, term[len(cand):]; break
        w = [int(p) for p in term.strip().split(".")]; c = pad(term)
        if op == "~>":
            return c <= v < ((w[0] + 1, 0, 0) if len(w) == 2 else (w[0], w[1] + 1, 0))
        return {"=": v == c, "!=": v != c, ">": v > c, ">=": v >= c, "<": v < c, "<=": v <= c}[op]
    def allowed(ver):
        return all(term_ok(pad(ver), t) for c in constraints for t in c.split(","))
    if locked is not None and allowed(locked):
        return locked
    cands = [a for a in available if allowed(a)]
    if not cands:
        return "Error: no available version matches"
    return max(cands, key=pad)
''',
    ],
    guide=dict(
        prereqs="The dependency lock file in *Installing Terraform, signing in safely and creating a first resource*; provider requirements across modules in *Multiple providers, part 1: aliases, Regions and accounts*. The problem *Match a version against a constraint*.",
        intuition="Two forces pull in different directions. Constraints say what is *permitted*; the lock file says what was *chosen*. Without `-upgrade`, the lock file wins as long as its choice is still permitted, which is why a teammate and the pipeline install identical providers. With `-upgrade`, or with no lock entry, Terraform is free to choose and takes the newest permitted release.",
        hints=[
            "Reuse your constraint matcher. A version is allowed when every term of every constraint string accepts it.",
            "Decide first which of the two rules applies: `locked is not None and not upgrade`.",
            "To find the newest version, compare tuples of integers. `max` accepts a `key` function.",
        ],
        brute_force="Sort all available versions from newest to oldest and test each against every constraint until one passes: O(n log n + n·t). A single `max` over the filtered list is O(n·t) with no sort; both are fine at registry sizes.",
        approach="""1. `allowed(version)`: pad to a tuple; every term in every constraint must accept it.
2. Lock path: `locked` present and no upgrade → return it if allowed, else the lock error.
3. Free path: filter `available` by `allowed`; none → error; else `max` by the padded tuple.

**Dry run:** available `6.0.0, 6.4.0, 6.8.0, 7.1.0`; constraints `">= 6.2, < 7.0"` from the root and `"~> 6.4"` from a child module; no lock.

| version | >= 6.2 | < 7.0 | ~> 6.4 | allowed |
|---|---|---|---|---|
| 6.0.0 | no | | | no |
| 6.4.0 | yes | yes | yes | yes |
| 6.8.0 | yes | yes | yes | yes |
| 7.1.0 | yes | no | | no |

Newest allowed: `6.8.0`. Had the lock file said `6.4.0`, the answer without `-upgrade` would be `6.4.0`.""",
        complexity="Time O(n·t) for n available versions and t constraint terms; space O(n) for the candidate list.",
        pitfalls="Ignoring the lock file (first wrong solution): every run would silently pick up new releases, which is the problem the lock file exists to prevent. Choosing the maximum as text (second wrong solution), so `6.9.0` beats `6.10.0`. Quietly choosing another version when the locked one breaks a constraint (third wrong solution): Terraform stops and asks for `-upgrade`, and that wrong solution also ignores `-upgrade` when the lock still fits. Treating an empty constraint list as 'nothing allowed'.",
        follow_up="The lock file also stores checksums of the provider packages. Extend the model so that a version whose checksum differs from the recorded one is rejected even though the number matches.",
    ),
),
]
