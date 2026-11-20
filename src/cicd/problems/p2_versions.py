PROBLEMS = [
dict(
    id="cicd-version-constraint",
    title="Does the Version Satisfy the Constraint?",
    difficulty="Medium",
    pattern="Parsing / Strings",
    entry="satisfies",
    description=r"""
Package managers accept a *range* of versions for each dependency. Decide whether a concrete version lies in a range.

A **version** is `MAJOR.MINOR.PATCH`, three non-negative integers such as `1.4.2`.

A **constraint** is one or more clauses separated by commas; the version must satisfy **all** of them. Spaces
around clauses may be ignored. Each clause is an operator followed by a version that may leave out trailing parts
(`1.2` means `1.2.0`, `1` means `1.0.0`):

| clause | meaning |
|---|---|
| `>=V`, `>V`, `<=V`, `<V`, `==V` | ordinary comparison with `V` |
| `^V` (caret) | at least `V`, and below the next version that changes the left-most **non-zero** part of `V`: `^1.2.3` → `<2.0.0`; `^0.3.1` → `<0.4.0`; `^0.0.5` → `<0.0.6`; `^0` or `^0.0` or `^0.0.0` → `<0.0.1` |
| `~V` (tilde) | at least `V`; if only the major part was written, below the next major (`~1` → `<2.0.0`); otherwise below the next minor (`~1.4` and `~1.4.2` → `<1.5.0`) |

Versions compare number by number, so `1.10.0` is newer than `1.9.0`.

**Example 1:** `version = "1.4.2"`, `constraint = "^1.2"` → `True`

**Example 2:** `version = "1.4.2"`, `constraint = ">=1,<1.4"` → `False`
""",
    starter='''def satisfies(version: str, constraint: str) -> bool:
    pass
''',
    solution='''def satisfies(version, constraint):
    def parse(text):
        parts = [int(x) for x in text.split(".")]
        return tuple(parts + [0] * (3 - len(parts))), len(parts)

    v, _ = parse(version)
    for clause in constraint.split(","):
        clause = clause.strip()
        for op in (">=", "<=", "==", ">", "<", "^", "~"):
            if clause.startswith(op):
                break
        base, written = parse(clause[len(op):].strip())
        if op == ">=":
            ok = v >= base
        elif op == "<=":
            ok = v <= base
        elif op == "==":
            ok = v == base
        elif op == ">":
            ok = v > base
        elif op == "<":
            ok = v < base
        elif op == "^":
            if base[0] > 0:
                upper = (base[0] + 1, 0, 0)
            elif base[1] > 0:
                upper = (0, base[1] + 1, 0)
            else:
                upper = (0, 0, base[2] + 1)
            ok = base <= v < upper
        else:
            upper = (base[0] + 1, 0, 0) if written == 1 else (base[0], base[1] + 1, 0)
            ok = base <= v < upper
        if not ok:
            return False
    return True
''',
    tests=[
        ["1.4.2", "^1.2"],
        ["1.4.2", ">=1,<1.4"],
        ["1.4.2", "~1.4"],
        ["1.5.0", "~1.4"],
        ["1.4.2", ">=1,<2"],
        ["2.0.0", "^1.2"],
        ["1.10.0", ">1.9.0"],
        ["0.3.9", "^0.3.1"],
        ["0.4.0", "^0.3.1"],
        ["0.0.5", "^0.0.5"],
        ["0.0.6", "^0.0.5"],
        ["1.9.9", "~1"],
        ["2.0.0", "~1"],
        ["1.4.2", "==1.4.2"],
        ["1.4.2", " >= 1.4.2 , <= 1.4.2 "],
        ["1.1.9", "^1.2"],
        ["0.0.0", "^0"],
        ["10.2.3", ">=9.9.9,<10.10"],
    ],
    examples=2,
    wrong_solutions=[
        '''def satisfies(version, constraint):
    def pad(t):
        return t + ".0" * (2 - t.count("."))
    v = pad(version)
    for clause in constraint.split(","):
        clause = clause.strip()
        for op in (">=", "<=", "==", ">", "<", "^", "~"):
            if clause.startswith(op):
                break
        b = pad(clause[len(op):].strip())
        if op in ("^", "~"):
            ok = v >= b and v.split(".")[0] == b.split(".")[0]
        else:
            ok = eval(repr(v) + op + repr(b))
        if not ok:
            return False
    return True
''',
        '''def satisfies(version, constraint):
    def parse(t):
        p = [int(x) for x in t.split(".")]
        return tuple(p + [0] * (3 - len(p)))
    v = parse(version)
    for clause in constraint.split(","):
        clause = clause.strip()
        for op in (">=", "<=", "==", ">", "<", "^", "~"):
            if clause.startswith(op):
                break
        b = parse(clause[len(op):].strip())
        if op == "^":
            ok = b <= v < (b[0] + 1, 0, 0)
        elif op == "~":
            ok = b <= v < (b[0], b[1] + 1, 0)
        else:
            ok = {">=": v >= b, "<=": v <= b, "==": v == b, ">": v > b, "<": v < b}[op]
        if not ok:
            return False
    return True
''',
    ],
    guide=dict(
        prereqs="Splitting strings, converting text to integers, and comparing tuples (Python compares tuples element by element). "
                "See the lesson *Version control everything and pin your dependencies*.",
        intuition="Turn every version into a tuple of three integers. Then each clause is a lower bound, an upper bound, or both, and tuple "
                  "comparison does the rest. Caret and tilde are shorthand for a pair of bounds.",
        hints=[
            "Parse `'1.4'` into `(1, 4, 0)` and also remember how many parts were written; tilde needs that.",
            "Check two-character operators (`>=`, `<=`, `==`) before one-character ones (`>`, `<`).",
            "For caret, find the left-most non-zero part of the base, add one to it, and zero everything to its right; that is the exclusive upper bound.",
        ],
        brute_force="Enumerate every version below some limit that the constraint accepts and test membership. It works for tiny numbers and is "
                    "pointless otherwise; direct comparison is both easier and exact.",
        approach="For each clause (split on commas, stripped):\n\n"
                 "1. Identify the operator and parse the rest into `base` plus `written` (how many parts appeared).\n"
                 "2. Comparison operators: compare tuples directly.\n"
                 "3. Caret: `upper` = (major+1,0,0) if major > 0; else (0,minor+1,0) if minor > 0; else (0,0,patch+1). Require `base <= v < upper`.\n"
                 "4. Tilde: `upper` = (major+1,0,0) if only the major was written, else (major,minor+1,0). Require `base <= v < upper`.\n"
                 "5. Return False at the first failing clause, True if all pass.\n\n"
                 "**Dry run**: version 0.4.0, constraint `^0.3.1`. base = (0,3,1); major is 0 and minor is 3, so upper = (0,4,0). "
                 "(0,3,1) <= (0,4,0) holds but (0,4,0) < (0,4,0) does not, so the answer is False.",
        complexity="Time O(C) for C clauses, each handled in constant time. Space O(1).",
        pitfalls="- Comparing version *strings* puts `1.10.0` before `1.9.0`.\n"
                 "- Caret below 1.0 is stricter: `^0.3.1` stops before `0.4.0`.\n"
                 "- `~1` and `~1.0` differ: the first allows all of 1.x, the second only 1.0.x.\n"
                 "- Upper bounds from caret and tilde are exclusive.",
        follow_up="Add pre-release versions such as `2.0.0-rc.1`, which sort before `2.0.0`. Or return the newest version from a list that satisfies the constraint.",
    ),
),
dict(
    id="cicd-config-layering",
    title="Merge Configuration Layers",
    difficulty="Easy",
    pattern="Recursion / Dictionaries",
    entry="merge_config",
    description=r"""
Applications are configured by stacking **layers**: defaults first, then environment-specific overrides, then
anything supplied at start-up. Later layers win.

Given `layers`, a list of dictionaries ordered from lowest to highest priority, return the merged configuration
using these rules for each key of a later layer:

- If the value is `None`, the key is **removed** from the result (a way to unset a default).
- If the value is a dictionary and the current value for that key is also a dictionary, merge them
  **recursively** with the same rules.
- Otherwise the later value **replaces** the earlier one. Lists are replaced as a whole, never joined.

The input must not be modified. An empty list of layers gives `{}`.

**Example 1:** `[{"db": {"host": "localhost", "pool": 10}, "debug": True}, {"db": {"pool": 50}}]`
→ `{"db": {"host": "localhost", "pool": 50}, "debug": True}`

**Example 2:** `[{"origins": ["a", "b"], "debug": True}, {"origins": ["c"], "debug": None}]` → `{"origins": ["c"]}`
""",
    starter='''def merge_config(layers: List[dict]) -> dict:
    pass
''',
    solution='''import copy

def merge_config(layers):
    def merge(base, override):
        for key, value in override.items():
            if value is None:
                base.pop(key, None)
            elif isinstance(value, dict) and isinstance(base.get(key), dict):
                merge(base[key], value)
            elif isinstance(value, dict):
                base[key] = {}
                merge(base[key], value)
            else:
                base[key] = copy.deepcopy(value)
        return base
    result = {}
    for layer in layers:
        merge(result, layer)
    return result
''',
    tests=[
        [[{"db": {"host": "localhost", "pool": 10}, "debug": True}, {"db": {"pool": 50}}]],
        [[{"origins": ["a", "b"], "debug": True}, {"origins": ["c"], "debug": None}]],
        [[]],
        [[{}]],
        [[{"a": 1}]],
        [[{"a": 1}, {"a": 2}, {"a": 3}]],
        [[{"a": {"b": {"c": 1, "d": 2}}}, {"a": {"b": {"c": 9}}}, {"a": {"b": {"e": 5}}}]],
        [[{"a": {"b": 1}}, {"a": 5}]],
        [[{"a": 5}, {"a": {"b": 1}}]],
        [[{"a": {"b": 1, "c": 2}}, {"a": {"b": None}}]],
        [[{"a": 1}, {"missing": None}]],
        [[{"a": {"x": 1}}, {"a": {"x": None, "y": {"z": None, "w": 1}}}]],
        [[{"a": [1, 2]}, {"a": []}]],
        [[{"a": 0, "b": False, "c": ""}, {"d": 1}]],
        [[{f"k{i}": {"v": i, "keep": True}} for i in range(200)] + [{f"k{i}": {"v": -i}} for i in range(0, 200, 2)]],
    ],
    examples=2,
    wrong_solutions=[
        '''def merge_config(layers):
    result = {}
    for layer in layers:
        result.update(layer)
    return {k: v for k, v in result.items() if v is not None}
''',
        '''def merge_config(layers):
    def merge(base, override):
        for k, v in override.items():
            if isinstance(v, dict) and isinstance(base.get(k), dict):
                merge(base[k], v)
            elif isinstance(v, list) and isinstance(base.get(k), list):
                base[k] = base[k] + v
            else:
                base[k] = v
        return base
    result = {}
    for layer in layers:
        merge(result, layer)
    return result
''',
    ],
    guide=dict(
        prereqs="Dictionaries, `isinstance`, and a function that calls itself (recursion). See the lesson *Environments, configuration and secrets*.",
        intuition="Merging two layers is the same job at every depth: walk the keys of the override; where both sides hold a dictionary, do the "
                  "same job one level down; otherwise the override wins. `None` is a special message meaning 'delete this'.",
        hints=[
            "Write `merge(base, override)` for two dictionaries first, then apply it across the list from left to right.",
            "Check for `None` before anything else, and use `pop(key, None)` so that a missing key is not an error.",
            "When the override holds a dictionary but the base does not, start from an empty dictionary and merge into it, so nested `None` values are still dropped.",
        ],
        brute_force="Flatten every layer into dotted paths (`db.pool`), apply them in order into one flat dictionary, then rebuild the nesting. "
                    "It works, but handling replacement of a whole subtree and deletions is fiddlier than the recursive version.",
        approach="1. Start with `result = {}`.\n"
                 "2. For each layer, for each `(key, value)`:\n"
                 "   - `None` -> remove the key from the result;\n"
                 "   - dictionary and the result already has a dictionary there -> recurse;\n"
                 "   - dictionary otherwise -> put `{}` there and recurse into it;\n"
                 "   - anything else -> store a copy of the value.\n\n"
                 "**Dry run** on Example 1: after layer 1 the result equals layer 1. Layer 2 has `db` -> dictionary on both sides, so recurse: "
                 "`pool` is replaced by 50 and `host` is untouched. `debug` is not mentioned, so it stays.",
        complexity="Time O(N), where N is the total number of keys in all layers. Space O(N) for the result; recursion depth equals the nesting depth.",
        pitfalls="- `dict.update` replaces a whole nested dictionary, losing sibling keys such as `host`.\n"
                 "- Lists are replaced, not concatenated.\n"
                 "- Use `is None`, not a truthiness test: `0`, `False` and `''` are real values.\n"
                 "- Storing the input's own nested objects in the result means later merges would modify the input; copy them.",
        follow_up="Report, for each final value, which layer it came from. That is what configuration debugging tools show.",
    ),
),
dict(
    id="cicd-semver-bump",
    title="Next Version from Commit Messages",
    difficulty="Medium",
    pattern="Parsing / Strings",
    entry="next_version",
    description=r"""
With the *Conventional Commits* format, the next version number can be computed from the commit messages since
the last release.

The first line of a message (the header) has the form `type(scope)!: description`, where `(scope)` and `!` are
optional, `type` is lowercase letters, and there is exactly one space after the colon followed by at least one
character. A header that does not match this form contributes nothing.

Each commit asks for a bump:

- **major** if the header has `!` before the colon, or if any later line of the message starts with
  `BREAKING CHANGE:` or `BREAKING-CHANGE:`;
- otherwise **minor** if the type is `feat`;
- otherwise **patch** if the type is `fix` or `perf`;
- otherwise nothing.

The release applies the **largest** bump requested by any commit, once:

- major: `MAJOR+1.0.0`
- minor: `MAJOR.MINOR+1.0`
- patch: `MAJOR.MINOR.PATCH+1`
- nothing: the version is unchanged.

**Example 1:** `current = "1.4.2"`, `commits = ["fix: handle empty basket", "feat(cart): support gift cards"]` → `"1.5.0"`

**Example 2:** `current = "1.4.2"`, `commits = ["docs: fix typo", "chore(deps): bump httpx"]` → `"1.4.2"`
""",
    starter='''def next_version(current: str, commits: List[str]) -> str:
    pass
''',
    solution='''import re

_HEADER = re.compile(r"^([a-z]+)(\\([^)]*\\))?(!)?: .+")

def next_version(current, commits):
    level = 0
    for message in commits:
        lines = message.split("\\n")
        m = _HEADER.match(lines[0])
        if not m:
            continue
        if m.group(3) or any(l.startswith(("BREAKING CHANGE:", "BREAKING-CHANGE:")) for l in lines[1:]):
            bump = 3
        elif m.group(1) == "feat":
            bump = 2
        elif m.group(1) in ("fix", "perf"):
            bump = 1
        else:
            bump = 0
        level = max(level, bump)
    major, minor, patch = (int(x) for x in current.split("."))
    if level == 3:
        return f"{major + 1}.0.0"
    if level == 2:
        return f"{major}.{minor + 1}.0"
    if level == 1:
        return f"{major}.{minor}.{patch + 1}"
    return current
''',
    tests=[
        ["1.4.2", ["fix: handle empty basket", "feat(cart): support gift cards"]],
        ["1.4.2", ["docs: fix typo", "chore(deps): bump httpx"]],
        ["1.4.2", []],
        ["1.4.2", ["fix(cart): correct VAT rounding"]],
        ["1.4.2", ["feat(api)!: remove v1 endpoints", "fix: typo"]],
        ["1.4.2", ["refactor: tidy\n\nBREAKING CHANGE: Money now requires a currency"]],
        ["1.4.2", ["fix: a", "fix: b", "fix: c"]],
        ["1.4.2", ["feat: a", "feat: b"]],
        ["0.9.9", ["perf: faster lookup"]],
        ["2.0.0", ["chore!: drop Python 3.9"]],
        ["1.4.2", ["Fix: capitalised type", "feat:missing space", "random text", "feat : space before colon"]],
        ["1.4.2", ["fix: mention of BREAKING CHANGE: in the header only"]],
        ["1.4.2", ["feat: x\n\nsome body\nBREAKING-CHANGE: y"]],
        ["3.7.11", ["fix: x\n\nnote: BREAKING CHANGE: not at line start"]],
        ["10.20.30", ["docs: a"] * 500 + ["feat(ui): b"]],
    ],
    examples=2,
    wrong_solutions=[
        '''import re

def next_version(current, commits):
    major, minor, patch = (int(x) for x in current.split("."))
    for message in commits:
        m = re.match(r"^([a-z]+)(\\([^)]*\\))?(!)?: .+", message.split("\\n")[0])
        if not m:
            continue
        if m.group(3) or "BREAKING CHANGE:" in message:
            major, minor, patch = major + 1, 0, 0
        elif m.group(1) == "feat":
            minor, patch = minor + 1, 0
        elif m.group(1) in ("fix", "perf"):
            patch += 1
    return f"{major}.{minor}.{patch}"
''',
        '''import re

def next_version(current, commits):
    level = 0
    for message in commits:
        m = re.match(r"^([a-z]+)(\\([^)]*\\))?(!)?: .+", message.split("\\n")[0])
        if not m:
            continue
        level = max(level, 3 if m.group(3) else 2 if m.group(1) == "feat" else 1 if m.group(1) in ("fix", "perf") else 0)
    major, minor, patch = (int(x) for x in current.split("."))
    return [current, f"{major}.{minor}.{patch + 1}", f"{major}.{minor + 1}.0", f"{major + 1}.0.0"][level]
''',
    ],
    guide=dict(
        prereqs="String splitting, a little pattern matching (a regular expression, or careful manual parsing), and `max`. "
                "See the lesson *Monorepo vs polyrepo and artifact versioning*.",
        intuition="Each commit votes for a bump size. The release takes the single largest vote, not the sum of the votes: ten fixes still make "
                  "one patch release.",
        hints=[
            "Give the bumps numbers: 0 nothing, 1 patch, 2 minor, 3 major. Then the answer is the maximum over the commits.",
            "Only the first line is the header. Breaking-change footers are found on the *later* lines, at the start of a line.",
            "Apply the bump once at the end, remembering to reset the lower parts to zero.",
        ],
        brute_force="There is no asymptotically worse sensible approach; the task is a single pass. The risk is in the parsing details, not the speed.",
        approach="1. For each message split into lines. Match the first line against `type(scope)!: description`.\n"
                 "2. If it does not match, skip the commit.\n"
                 "3. Major if `!` is present or a later line starts with a breaking-change footer; else minor for `feat`; else patch for `fix`/`perf`.\n"
                 "4. Keep the maximum level, then build the new version string.\n\n"
                 "**Dry run** on Example 1: `fix:` -> 1, `feat(cart):` -> 2. Maximum 2 (minor). 1.4.2 -> 1.5.0.",
        complexity="Time O(total length of the messages). Space O(1) beyond the input.",
        pitfalls="- Applying every commit's bump in turn turns three fixes into three patch bumps.\n"
                 "- Forgetting the footer rule misses breaking changes that have no `!`.\n"
                 "- The footer must start a line after the header; the words appearing inside the header do not count.\n"
                 "- A minor bump resets patch to 0, and a major bump resets both minor and patch.\n"
                 "- `feat:x` (no space) and `Fix: x` (capital) are not valid headers.",
        follow_up="Many tools treat breaking changes differently before 1.0.0, bumping the minor part instead of the major. How would you add that rule?",
    ),
),
dict(
    id="cicd-flag-rollout",
    title="Feature Flag Percentage Rollout",
    difficulty="Easy",
    pattern="Hashing",
    entry="enabled_users",
    description=r"""
A feature flag is being rolled out to a percentage of users. Each user must get a **stable** answer: the same
user sees the same result on every request, and raising the percentage only ever adds users.

Define a user's **bucket** for a flag exactly like this:

1. Build the text `flag + ":" + user_id`.
2. Compute its SHA-256 hash (text encoded as UTF-8) as lowercase hexadecimal.
3. Take the first 8 hexadecimal characters, read them as a base-16 integer, and take the remainder modulo `10000`.

The bucket is therefore a number from `0` to `9999`. The flag is **on** for a user when
`bucket < percent * 100`, where `percent` is an integer from `0` to `100`.

Return the users for whom the flag is on, in the same order as the input list.

**Example 1:** `flag = "new-checkout"`, `users = ["ana", "ben", "cy"]`, `percent = 100` → `["ana", "ben", "cy"]`

**Example 2:** `flag = "new-checkout"`, `users = ["ana", "ben", "cy"]`, `percent = 0` → `[]`

Use `hashlib.sha256` from the standard library.
""",
    starter='''import hashlib

def enabled_users(flag: str, users: List[str], percent: int) -> List[str]:
    pass
''',
    solution='''import hashlib

def enabled_users(flag, users, percent):
    def bucket(user):
        digest = hashlib.sha256((flag + ":" + user).encode("utf-8")).hexdigest()
        return int(digest[:8], 16) % 10000
    return [u for u in users if bucket(u) < percent * 100]
''',
    tests=[
        ["new-checkout", ["ana", "ben", "cy"], 100],
        ["new-checkout", ["ana", "ben", "cy"], 0],
        ["new-checkout", [], 50],
        ["new-checkout", [f"user-{i}" for i in range(60)], 50],
        ["new-checkout", [f"user-{i}" for i in range(60)], 10],
        ["dark-mode", [f"user-{i}" for i in range(60)], 10],
        ["new-checkout", [f"user-{i}" for i in range(200)], 1],
        ["new-checkout", [f"user-{i}" for i in range(200)], 99],
        ["f", ["a", "a", "b", "a"], 60],
        ["", ["", "x"], 50],
        ["café", ["zürich", "tokyo", "lima"], 40],
        ["new-checkout", [f"u{i}" for i in range(5000)], 25],
    ],
    examples=2,
    wrong_solutions=[
        '''import hashlib

def enabled_users(flag, users, percent):
    def bucket(user):
        return int(hashlib.sha256(user.encode("utf-8")).hexdigest()[:8], 16) % 10000
    return [u for u in users if bucket(u) < percent * 100]
''',
        '''import hashlib

def enabled_users(flag, users, percent):
    def bucket(user):
        return int(hashlib.sha256((flag + ":" + user).encode("utf-8")).hexdigest()[:8], 16) % 100
    return [u for u in users if bucket(u) < percent]
''',
    ],
    guide=dict(
        prereqs="Calling `hashlib.sha256(...).hexdigest()`, slicing a string, `int(text, 16)` and the modulo operator `%`. "
                "See the lesson *Feature toggles and branch by abstraction*.",
        intuition="A hash turns a user's identity into a number that looks random but never changes. Dividing the range of that number into "
                  "10,000 buckets and switching on the lowest buckets gives a steady, evenly spread sample. A higher percentage switches on more "
                  "buckets, so earlier users stay in.",
        hints=[
            "Follow the three steps literally; the order of flag, colon and user matters.",
            "`int('1f', 16)` is 31: the second argument says the text is base 16.",
            "Compare the bucket with `percent * 100`, using strictly less than, so that 0% enables nobody and 100% enables everybody.",
        ],
        brute_force="There is nothing slower that is still correct; each user needs one hash. A tempting alternative, choosing a random number per "
                    "request, is wrong because the same user would flip between on and off.",
        approach="1. Write `bucket(user)`: hash `flag + ':' + user`, take 8 hex characters, convert, modulo 10000.\n"
                 "2. Keep the users whose bucket is below `percent * 100`, preserving order.\n\n"
                 "**Dry run** with percent = 100: the limit is 10000 and every bucket is at most 9999, so everyone is kept. "
                 "With percent = 0 the limit is 0 and no bucket is below it, so nobody is kept.",
        complexity="Time O(n) hashes for n users. Space O(n) for the output.",
        pitfalls="- Python's built-in `hash()` gives different results for text on each run of the program, so it cannot be used.\n"
                 "- Leaving the flag name out of the hashed text selects the same users for every flag.\n"
                 "- Using only 100 buckets changes who is selected and loses precision.\n"
                 "- `<=` would enable bucket 0 at 0%.\n"
                 "- Duplicated users in the input appear in the output as often as they occur.",
        follow_up="Add targeting rules that are checked before the percentage: an allow-list of user ids that always get the flag, and a deny-list that never do.",
    ),
),
dict(
    id="cicd-freeze-window",
    title="Deployment Freeze Check",
    difficulty="Easy",
    pattern="Intervals / Dates",
    entry="can_deploy",
    description=r"""
Before deploying, a pipeline checks its **freeze policy**.

- `when` is the proposed deployment time as text in the form `YYYY-MM-DDTHH:MM` (all times are in UTC).
- `windows` is a list of freeze windows `[start, end, allow_emergency]`. A window covers every time `t` with
  `start <= t < end` (the end is **not** included). `allow_emergency` is a boolean.
- `blocked_weekdays` is a list of weekday numbers on which routine deployments are not allowed
  (`0` = Monday … `6` = Sunday).
- `emergency` says whether this deployment is an emergency fix.

Decide whether the deployment may go ahead:

- A **routine** deployment (`emergency` is false) is allowed only if `when` is in no freeze window **and** its
  weekday is not blocked.
- An **emergency** deployment ignores blocked weekdays. It is allowed unless `when` is inside a freeze window
  whose `allow_emergency` is false.

**Example 1:** `when = "2026-11-27T10:00"`, `windows = [["2026-11-25T00:00", "2026-12-02T00:00", True]]`,
`blocked_weekdays = [5, 6]`, `emergency = False` → `False`

**Example 2:** the same, but `emergency = True` → `True`

`datetime.datetime.strptime(text, "%Y-%m-%dT%H:%M").weekday()` gives the weekday number.
""",
    starter='''import datetime

def can_deploy(when: str, windows: List[list], blocked_weekdays: List[int], emergency: bool) -> bool:
    pass
''',
    solution='''import datetime

def can_deploy(when, windows, blocked_weekdays, emergency):
    inside = [w for w in windows if w[0] <= when < w[1]]
    if emergency:
        return all(w[2] for w in inside)
    if inside:
        return False
    weekday = datetime.datetime.strptime(when, "%Y-%m-%dT%H:%M").weekday()
    return weekday not in blocked_weekdays
''',
    tests=[
        ["2026-11-27T10:00", [["2026-11-25T00:00", "2026-12-02T00:00", True]], [5, 6], False],
        ["2026-11-27T10:00", [["2026-11-25T00:00", "2026-12-02T00:00", True]], [5, 6], True],
        ["2026-11-24T23:59", [["2026-11-25T00:00", "2026-12-02T00:00", True]], [5, 6], False],
        ["2026-11-25T00:00", [["2026-11-25T00:00", "2026-12-02T00:00", True]], [], False],
        ["2026-12-02T00:00", [["2026-11-25T00:00", "2026-12-02T00:00", True]], [], False],
        ["2026-12-01T23:59", [["2026-11-25T00:00", "2026-12-02T00:00", True]], [], False],
        ["2026-06-06T12:00", [], [5, 6], False],
        ["2026-06-06T12:00", [], [5, 6], True],
        ["2026-06-08T12:00", [], [5, 6], False],
        ["2026-12-31T12:00", [["2026-12-24T00:00", "2027-01-02T00:00", False]], [], True],
        ["2026-12-31T12:00", [["2026-12-24T00:00", "2027-01-02T00:00", False]], [], False],
        ["2026-12-31T12:00", [["2026-12-01T00:00", "2027-01-15T00:00", True], ["2026-12-24T00:00", "2027-01-02T00:00", False]], [], True],
        ["2026-12-10T12:00", [["2026-12-01T00:00", "2027-01-15T00:00", True], ["2026-12-24T00:00", "2027-01-02T00:00", False]], [], True],
        ["2026-03-04T09:30", [["2026-03-04T09:30", "2026-03-04T09:30", False]], [], False],
        ["2026-06-03T12:00", [], [0, 1, 2, 3, 4, 5, 6], False],
    ],
    examples=2,
    wrong_solutions=[
        '''import datetime

def can_deploy(when, windows, blocked_weekdays, emergency):
    if emergency:
        return True
    if any(w[0] <= when <= w[1] for w in windows):
        return False
    return datetime.datetime.strptime(when, "%Y-%m-%dT%H:%M").weekday() not in blocked_weekdays
''',
        '''import datetime

def can_deploy(when, windows, blocked_weekdays, emergency):
    inside = [w for w in windows if w[0] <= when < w[1]]
    if emergency:
        return all(w[2] for w in inside)
    return not inside
''',
    ],
    guide=dict(
        prereqs="Comparing strings, lists and booleans, and reading a date with `datetime`. See the lesson *Maturity, risk and compliance*.",
        intuition="Timestamps written as year-month-day-hour-minute with fixed widths sort the same way as the times they stand for, so they can be "
                  "compared as plain text. The rest is a small decision table: routine deployments are stopped by any window or blocked day; "
                  "emergencies are stopped only by a window that forbids them.",
        hints=[
            "First collect the windows that contain `when`, using `start <= when < end`.",
            "Handle the emergency case next: it passes only if every containing window allows emergencies.",
            "For a routine deployment, any containing window blocks it; otherwise check the weekday.",
        ],
        brute_force="Convert everything to minutes since some fixed date and compare numbers. It gives the same answer with more work; the text "
                    "comparison is already correct for this fixed format.",
        approach="1. `inside` = windows with `start <= when < end`.\n"
                 "2. If `emergency`: return whether all windows in `inside` have `allow_emergency` true (true when `inside` is empty).\n"
                 "3. Otherwise: if `inside` is not empty, return False.\n"
                 "4. Otherwise return whether the weekday of `when` is absent from `blocked_weekdays`.\n\n"
                 "**Dry run** on Example 1: 27 November lies between the 25th and 2 December, so `inside` has one window. "
                 "The deployment is routine, so the answer is False. In Example 2 the window allows emergencies, so the answer is True.",
        complexity="Time O(W) for W windows. Space O(W) in the worst case for the list of containing windows.",
        pitfalls="- The end of a window is excluded: a deployment exactly at `end` is allowed.\n"
                 "- An emergency does not override every freeze; a window can forbid emergencies too.\n"
                 "- With overlapping windows, one that forbids emergencies is enough to block.\n"
                 "- A window whose start equals its end contains no time at all.\n"
                 "- Weekday 0 is Monday in Python's `weekday()`.",
        follow_up="Return the earliest time at or after `when` at which a routine deployment would be allowed.",
    ),
),
dict(
    id="cicd-required-checks",
    title="Pull Request Merge Gate",
    difficulty="Medium",
    pattern="Simulation / Dictionaries",
    entry="merge_blockers",
    description=r"""
A hosting platform decides whether a pull request may be merged. Return the list of reasons that block the
merge; an empty list means it may be merged.

`pr` is a dictionary with:

- `"author"`: the author's name;
- `"approvals"`: a list of names of people who approved (names may repeat);
- `"checks"`: a list of `[name, state]` pairs in the order the results were reported. A check may be reported
  several times (for example after a re-run); only its **latest** state counts. States are `"success"`,
  `"failure"`, `"pending"` and `"skipped"`;
- `"base"`: the commit of the main branch that the pull request was last updated from;
- `"unresolved"`: the number of unresolved review conversations.

`rules` is a dictionary with:

- `"min_approvals"`: how many **distinct** approvers other than the author are required;
- `"required_checks"`: names of the checks that must pass. A check passes if its latest state is `"success"`
  or `"skipped"`. A required check that was never reported does not pass;
- `"require_up_to_date"`: if true, `pr["base"]` must equal `rules["main_head"]`;
- `"main_head"`: the current tip of the main branch.

Blocking reasons, as strings:

- `"approvals"` — not enough valid approvals;
- `"check:<name>"` — one per required check that does not pass;
- `"outdated"` — the branch must be up to date and is not;
- `"conversations"` — there is at least one unresolved conversation.

Return the reasons sorted alphabetically.

**Example 1:** author `"ana"`, approvals `["ben"]`, checks `[["lint","success"],["unit","success"]]`, base `"c1"`,
unresolved `0`; rules: 1 approval, required `["lint","unit"]`, up to date required, main head `"c1"` → `[]`

**Example 2:** the same pull request but approvals `["ana"]` and checks `[["lint","success"]]` → `["approvals", "check:unit"]`
""",
    starter='''def merge_blockers(pr: dict, rules: dict) -> List[str]:
    pass
''',
    solution='''def merge_blockers(pr, rules):
    reasons = []
    approvers = {a for a in pr["approvals"] if a != pr["author"]}
    if len(approvers) < rules["min_approvals"]:
        reasons.append("approvals")
    latest = {}
    for name, state in pr["checks"]:
        latest[name] = state
    for name in set(rules["required_checks"]):
        if latest.get(name) not in ("success", "skipped"):
            reasons.append("check:" + name)
    if rules["require_up_to_date"] and pr["base"] != rules["main_head"]:
        reasons.append("outdated")
    if pr["unresolved"] > 0:
        reasons.append("conversations")
    return sorted(reasons)
''',
    tests=[
        [{"author": "ana", "approvals": ["ben"], "checks": [["lint", "success"], ["unit", "success"]], "base": "c1", "unresolved": 0},
         {"min_approvals": 1, "required_checks": ["lint", "unit"], "require_up_to_date": True, "main_head": "c1"}],
        [{"author": "ana", "approvals": ["ana"], "checks": [["lint", "success"]], "base": "c1", "unresolved": 0},
         {"min_approvals": 1, "required_checks": ["lint", "unit"], "require_up_to_date": True, "main_head": "c1"}],
        [{"author": "ana", "approvals": ["ben", "ben", "ana"], "checks": [], "base": "c1", "unresolved": 0},
         {"min_approvals": 2, "required_checks": [], "require_up_to_date": False, "main_head": "c9"}],
        [{"author": "ana", "approvals": ["ben", "cy"], "checks": [], "base": "c1", "unresolved": 0},
         {"min_approvals": 2, "required_checks": [], "require_up_to_date": False, "main_head": "c9"}],
        [{"author": "ana", "approvals": [], "checks": [], "base": "c1", "unresolved": 0},
         {"min_approvals": 0, "required_checks": [], "require_up_to_date": False, "main_head": "c1"}],
        [{"author": "ana", "approvals": ["ben"], "checks": [["unit", "failure"], ["unit", "success"]], "base": "c1", "unresolved": 0},
         {"min_approvals": 1, "required_checks": ["unit"], "require_up_to_date": True, "main_head": "c1"}],
        [{"author": "ana", "approvals": ["ben"], "checks": [["unit", "success"], ["unit", "failure"]], "base": "c1", "unresolved": 0},
         {"min_approvals": 1, "required_checks": ["unit"], "require_up_to_date": True, "main_head": "c1"}],
        [{"author": "ana", "approvals": ["ben"], "checks": [["unit", "pending"], ["docs", "failure"], ["e2e", "skipped"]], "base": "c1", "unresolved": 0},
         {"min_approvals": 1, "required_checks": ["unit", "e2e"], "require_up_to_date": True, "main_head": "c1"}],
        [{"author": "ana", "approvals": ["ben"], "checks": [["unit", "success"]], "base": "c1", "unresolved": 3},
         {"min_approvals": 1, "required_checks": ["unit"], "require_up_to_date": True, "main_head": "c2"}],
        [{"author": "ana", "approvals": ["ben"], "checks": [["unit", "success"]], "base": "c1", "unresolved": 0},
         {"min_approvals": 1, "required_checks": ["unit"], "require_up_to_date": False, "main_head": "c2"}],
        [{"author": "ana", "approvals": [], "checks": [["b", "failure"], ["a", "failure"]], "base": "x", "unresolved": 1},
         {"min_approvals": 1, "required_checks": ["b", "a", "zz"], "require_up_to_date": True, "main_head": "y"}],
        [{"author": "ana", "approvals": ["ben"], "checks": [["unit", "success"]], "base": "c1", "unresolved": 0},
         {"min_approvals": 1, "required_checks": ["unit", "unit"], "require_up_to_date": True, "main_head": "c1"}],
        [{"author": "ana", "approvals": ["ben"], "checks": [[f"c{i}", "success" if i % 7 else "failure"] for i in range(300)], "base": "c1", "unresolved": 0},
         {"min_approvals": 1, "required_checks": [f"c{i}" for i in range(0, 300, 5)], "require_up_to_date": True, "main_head": "c1"}],
    ],
    examples=2,
    wrong_solutions=[
        '''def merge_blockers(pr, rules):
    reasons = []
    if len(set(pr["approvals"])) < rules["min_approvals"]:
        reasons.append("approvals")
    latest = dict(pr["checks"])
    for name in set(rules["required_checks"]):
        if latest.get(name) not in ("success", "skipped"):
            reasons.append("check:" + name)
    if rules["require_up_to_date"] and pr["base"] != rules["main_head"]:
        reasons.append("outdated")
    if pr["unresolved"] > 0:
        reasons.append("conversations")
    return sorted(reasons)
''',
        '''def merge_blockers(pr, rules):
    reasons = []
    if len({a for a in pr["approvals"] if a != pr["author"]}) < rules["min_approvals"]:
        reasons.append("approvals")
    for name, state in pr["checks"]:
        if name in rules["required_checks"] and state == "failure" and "check:" + name not in reasons:
            reasons.append("check:" + name)
    if rules["require_up_to_date"] and pr["base"] != rules["main_head"]:
        reasons.append("outdated")
    if pr["unresolved"] > 0:
        reasons.append("conversations")
    return sorted(reasons)
''',
    ],
    guide=dict(
        prereqs="Dictionaries, sets and sorting. See the lesson *Guardrails: branch protection, required checks and merge queues*.",
        intuition="The gate is four independent questions. Each either adds a reason or does not. The care is in the details: who counts as an "
                  "approver, which result of a re-run check counts, and what a missing check means.",
        hints=[
            "Turn the approvals into a set and remove the author before counting.",
            "Walk the check results in order, storing each in a dictionary; later results overwrite earlier ones, leaving the latest.",
            "Loop over the *required* checks, not the reported ones. `latest.get(name)` returns `None` for a check that never reported, and `None` does not pass.",
        ],
        brute_force="For each required check, scan the whole list of results from the end to find its latest state: O(R * C) for R required checks "
                    "and C results. Building the dictionary once makes it O(R + C).",
        approach="1. `approvers` = distinct approvers except the author; add `approvals` if there are too few.\n"
                 "2. Build `latest[name] = state` by iterating over the results in order.\n"
                 "3. For each distinct required check, add `check:<name>` unless its latest state is `success` or `skipped`.\n"
                 "4. Add `outdated` if the rule is on and the base differs from the main head.\n"
                 "5. Add `conversations` if `unresolved > 0`. Sort and return.\n\n"
                 "**Dry run** on Example 2: the only approval is the author's own, so `approvals`. `latest` = {lint: success}; `unit` is missing, "
                 "so `check:unit`. Base equals main head; no conversations. Result: [approvals, check:unit].",
        complexity="Time O(A + C + R log R) for A approvals, C check results and R reasons. Space O(A + C).",
        pitfalls="- The author's own approval never counts, and the same reviewer approving twice counts once.\n"
                 "- A missing or pending required check blocks, exactly as a failure does.\n"
                 "- After a re-run, only the latest state matters: failure then success passes, success then failure does not.\n"
                 "- Checks that are not required never block, even when they fail.\n"
                 "- A required check listed twice must produce one reason, not two.",
        follow_up="Add code owners: given the changed paths and a list of (path prefix, owners) rules where the last match wins, require an approval "
                  "from an owner of every changed path.",
    ),
),
]
