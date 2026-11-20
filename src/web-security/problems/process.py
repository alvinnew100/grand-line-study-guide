_AK = "AKIA" + "IOSFODNN7EXAMPLE"          # the access-key id used throughout vendor documentation
_AK2 = "AKIA" + "ABCDEFGHIJKLMNOP"
_ACME = "acme_" + "0123456789abcdef" * 2     # fictional vendor token format used by this exercise
_PEM = "-----BEGIN " + "RSA PRIVATE KEY-----"
_PEM2 = "-----BEGIN " + "PRIVATE KEY-----"

_ELEMENTS = [
    {"name": "browser", "type": "external"},
    {"name": "api", "type": "process"},
    {"name": "orders-db", "type": "datastore"},
    {"name": "api-to-db", "type": "dataflow"},
]

PROBLEMS = [
dict(
    id="sec-dependency-check",
    title="Dependency Checker Against an Advisory List",
    difficulty="Medium",
    pattern="Supply Chain",
    kind="function",
    entry="vulnerableDeps",
    description=r"""
Software composition analysis tools compare the versions you have installed with published advisories.
Build the core of one.

`vulnerableDeps(installed, advisories)`:

- `installed` maps a package name to a version string such as `"2.31.0"`.
- `advisories` is a list of dicts `{"id": "ADV-1", "package": "requests", "range": ">=2.0.0,<2.31.1"}`.

**Versions** are one to three dot-separated non-negative integers; missing parts are zero, so `"2"` =
`"2.0"` = `"2.0.0"`. Compare them **numerically** part by part (`1.10.0` is newer than `1.9.0`).

A **range** is one or more comparators separated by commas, each an operator `<`, `<=`, `>`, `>=` or `=`
followed by a version; spaces around comparators are allowed. A version is affected when it satisfies
**all** comparators.

**Package names** match case-insensitively, and `_` and `-` are equivalent (`Flask_Login` = `flask-login`).

Return a list of `[package, advisory_id]` pairs for every advisory that affects an installed package,
where `package` is the normalised name (lower-case, `_` replaced by `-`). Sort the list by package name,
then advisory id.

**Example:** `vulnerableDeps({"requests": "2.30.0", "flask": "3.0.0"}, [{"id": "ADV-1", "package": "requests", "range": ">=2.0.0,<2.31.1"}])`
→ `[["requests", "ADV-1"]]`
""",
    starter='''def vulnerableDeps(installed: dict, advisories: list) -> list:
    pass
''',
    solution=r'''def _version(text):
    parts = [int(p) for p in text.strip().split(".")]
    return tuple((parts + [0, 0, 0])[:3])

def _norm(name):
    return name.strip().lower().replace("_", "-")

def _affected(version, spec):
    current = _version(version)
    for comparator in spec.split(","):
        comparator = comparator.strip()
        if comparator.startswith("<="):
            ok = current <= _version(comparator[2:])
        elif comparator.startswith(">="):
            ok = current >= _version(comparator[2:])
        elif comparator.startswith("<"):
            ok = current < _version(comparator[1:])
        elif comparator.startswith(">"):
            ok = current > _version(comparator[1:])
        else:
            ok = current == _version(comparator.lstrip("="))
        if not ok:
            return False
    return True

def vulnerableDeps(installed, advisories):
    have = {_norm(name): version for name, version in installed.items()}
    hits = []
    for advisory in advisories:
        package = _norm(advisory["package"])
        if package in have and _affected(have[package], advisory["range"]):
            hits.append([package, advisory["id"]])
    return sorted(hits)
''',
    tests=[
        [{"requests": "2.30.0", "flask": "3.0.0"}, [{"id": "ADV-1", "package": "requests", "range": ">=2.0.0,<2.31.1"}]],
        [{"requests": "2.31.1"}, [{"id": "ADV-1", "package": "requests", "range": ">=2.0.0,<2.31.1"}]],
        [{"lib": "1.10.0"}, [{"id": "ADV-2", "package": "lib", "range": "<1.9.0"}]],
        [{"lib": "1.9.0"}, [{"id": "ADV-2", "package": "lib", "range": "<1.10.0"}]],
        [{"Flask_Login": "0.6"}, [{"id": "ADV-3", "package": "flask-login", "range": "<=0.6.0"}]],
        [{"lib": "2"}, [{"id": "ADV-4", "package": "LIB", "range": "=2.0.0"}, {"id": "ADV-5", "package": "lib", "range": ">2.0.0"}]],
        [{"a": "1.0.0", "b": "1.0.0"},
         [{"id": "Z-9", "package": "b", "range": "<2"}, {"id": "A-1", "package": "b", "range": "<2"}, {"id": "M-5", "package": "a", "range": ">=1"}]],
        [{}, [{"id": "ADV-1", "package": "requests", "range": "<99"}]],
        [{"requests": "2.30.0"}, []],
        [{"lib": "3.2.1"}, [{"id": "ADV-6", "package": "lib", "range": " >= 3.0 , < 3.2.2 "}]],
        [{"lib": "3.2.2"}, [{"id": "ADV-6", "package": "lib", "range": ">=3.0,<3.2.2"}, {"id": "ADV-7", "package": "lib", "range": ">=3.2.2,<=3.2.2"}]],
        [{"lib": "0.9.9"}, [{"id": "ADV-8", "package": "lib", "range": ">=1.0.0,<2.0.0"}, {"id": "ADV-9", "package": "other", "range": "<5"}]],
        [{"lib": "10.0.0"}, [{"id": "ADV-10", "package": "lib", "range": ">9.9.9"}, {"id": "ADV-11", "package": "lib", "range": "<9.0.0"}]],
        [{"lib": "1.2.3"}, [{"id": "ADV-12", "package": "lib", "range": ">1.2.3"}, {"id": "ADV-13", "package": "lib", "range": ">=1.2.3"}]],
    ],
    examples=1,
    wrong_solutions=[
        r'''def vulnerableDeps(installed, advisories):
    hits = []
    for adv in advisories:
        name = adv["package"].lower().replace("_", "-")
        for pkg, version in installed.items():
            if pkg.lower().replace("_", "-") != name:
                continue
            ok = True
            for comp in adv["range"].split(","):
                comp = comp.strip()
                for op in ("<=", ">=", "<", ">", "="):
                    if comp.startswith(op):
                        target = comp[len(op):].strip()
                        break
                if op == "<=":
                    ok = ok and version <= target
                elif op == ">=":
                    ok = ok and version >= target
                elif op == "<":
                    ok = ok and version < target
                elif op == ">":
                    ok = ok and version > target
                else:
                    ok = ok and version == target
            if ok:
                hits.append([name, adv["id"]])
    return sorted(hits)
''',
        r'''def _version(text):
    parts = [int(p) for p in text.strip().split(".")]
    return tuple((parts + [0, 0, 0])[:3])

def vulnerableDeps(installed, advisories):
    have = {n.lower().replace("_", "-"): v for n, v in installed.items()}
    hits = []
    for adv in advisories:
        name = adv["package"].lower().replace("_", "-")
        if name not in have:
            continue
        current = _version(have[name])
        for comp in adv["range"].split(","):
            comp = comp.strip()
            if comp.startswith("<=") and current <= _version(comp[2:]):
                hits.append([name, adv["id"]]); break
            if comp.startswith(">=") and current >= _version(comp[2:]):
                hits.append([name, adv["id"]]); break
            if comp.startswith("<") and not comp.startswith("<=") and current < _version(comp[1:]):
                hits.append([name, adv["id"]]); break
            if comp.startswith(">") and not comp.startswith(">=") and current > _version(comp[1:]):
                hits.append([name, adv["id"]]); break
            if comp.startswith("=") and current == _version(comp[1:]):
                hits.append([name, adv["id"]]); break
    return sorted(hits)
''',
    ],
    guide=dict(
        prereqs="The dependencies and supply chain lesson (advisories, affected ranges, SCA). Tuple comparison in Python.",
        intuition="Version strings look like text but order like numbers. Convert each one to a tuple of integers and "
                  "Python's tuple comparison does the rest; a range is then just a conjunction of comparisons.",
        hints=[
            "`tuple(int(p) for p in '1.10.0'.split('.'))` gives `(1, 10, 0)`; pad to length three.",
            "Check two-character operators (`<=`, `>=`) before one-character ones.",
            "Normalise both the installed names and the advisory names with the same helper.",
        ],
        brute_force="Compare version strings directly. `'1.10.0' < '1.9.0'` is `True` for strings, so the checker "
                    "reports patched versions as vulnerable and — more dangerously — vulnerable ones as safe.",
        approach="1. Normalise installed names into a dict.\n2. For each advisory: skip if not installed; parse the "
                 "installed version; test every comparator; collect on all-true.\n3. Sort pairs.\n\n"
                 "Dry run: installed `lib 3.2.1`, range `>= 3.0 , < 3.2.2`. `(3,2,1) >= (3,0,0)` ✓, `(3,2,1) < (3,2,2)` ✓ → affected.",
        complexity="Time O(A · c + I + H log H) for A advisories of c comparators, I installed packages, H hits; space O(I + H).",
        pitfalls="- Lexicographic comparison of version text.\n"
                 "- Using *any* comparator instead of *all* — a range is an intersection.\n"
                 "- Package name normalisation: Python's index treats `-`, `_` (and `.`) as equivalent and ignores case.\n"
                 "- Real version schemes have pre-releases, epochs and build metadata; use `packaging.version` or the ecosystem's own library in production.",
        follow_up="Scan the *lock file* (the fully resolved, transitive set), not just direct requirements — most vulnerable packages arrive as dependencies of dependencies.",
    ),
),
dict(
    id="sec-secrets-scan",
    title="Secrets Scanner over Text Lines",
    difficulty="Medium",
    pattern="Secrets Management",
    kind="function",
    entry="scanSecrets",
    description=r"""
Pre-commit hooks and CI jobs scan changes for credentials before they reach the repository. Implement a
small line-based scanner.

`scanSecrets(lines)` receives a list of strings and returns a list of `[line_number, kind]` pairs
(line numbers start at 1), sorted by line number and then by kind. Each kind is reported at most once
per line.

| kind | a line matches when it contains… |
|---|---|
| `"cloud-access-key"` | `AKIA` followed by exactly 16 characters from `A–Z0–9`, not preceded or followed by another `A–Z0–9` character |
| `"vendor-token"` | `acme_` followed by exactly 32 characters from `0–9a–f`, not followed by another `0–9a–f` character |
| `"private-key"` | `-----BEGIN `, optionally one upper-case word and a space (e.g. `RSA `, `EC `), then `PRIVATE KEY-----` |
| `"hardcoded-credential"` | one of the names `password`, `passwd`, `secret`, `api_key`, `apikey`, `token` (any letter case; may be part of a longer name such as `DB_PASSWORD`), optionally a closing quote, optional spaces, `=` or `:`, optional spaces, then a quoted string literal (matching `'…'` or `"…"`) whose content is at least 8 characters and contains no quote characters |

A `hardcoded-credential` match is **ignored** when the literal is a placeholder: its lower-cased content
contains `example`, `changeme`, `placeholder` or `xxxx`, or starts with `${` or `<`.

**Example:** `scanSecrets(['db_password = "hunter2hunter2"', 'password = os.environ["DB_PASSWORD"]'])` →
`[[1, "hardcoded-credential"]]`
""",
    starter='''import re

def scanSecrets(lines: list) -> list:
    pass
''',
    solution=r'''import re

_ACCESS = re.compile(r"(?<![A-Z0-9])AKIA[A-Z0-9]{16}(?![A-Z0-9])")
_VENDOR = re.compile(r"acme_[0-9a-f]{32}(?![0-9a-f])")
_PEM = re.compile(r"-----BEGIN (?:[A-Z]+ )?PRIVATE KEY-----")
_CRED = re.compile(r"(?i)(?:password|passwd|secret|api_key|apikey|token)[\"']?\s*[:=]\s*([\"'])([^\"']{8,})\1")
_PLACEHOLDERS = ("example", "changeme", "placeholder", "xxxx")

def scanSecrets(lines):
    found = []
    for number, line in enumerate(lines, start=1):
        if _ACCESS.search(line):
            found.append([number, "cloud-access-key"])
        if _VENDOR.search(line):
            found.append([number, "vendor-token"])
        if _PEM.search(line):
            found.append([number, "private-key"])
        for match in _CRED.finditer(line):
            value = match.group(2).lower()
            if value.startswith("${") or value.startswith("<"):
                continue
            if any(word in value for word in _PLACEHOLDERS):
                continue
            found.append([number, "hardcoded-credential"])
            break
    return sorted(found)
''',
    tests=[
        [['db_password = "hunter2hunter2"', 'password = os.environ["DB_PASSWORD"]']],
        [["aws_access_key_id = " + _AK, "nothing here", "key=" + _AK2 + "Q"]],
        [[_PEM, "MIIEvQIBADANBg...", "-----END RSA PRIVATE KEY-----", _PEM2, "-----BEGIN PUBLIC KEY-----"]],
        [["token: '" + _ACME + "'"]],
        [["url = https://api.acme.test/?t=" + _ACME, "t=" + _ACME + "ab"]],
        [['API_KEY = "changeme-please"', 'api_key: "<your key here>"', 'secret = "${VAULT_SECRET}"', "SECRET = 'xxxxxxxxxxxx'"]],
        [['password = "short"', 'password = ""', "passwd='exactly8'"]],
        [['config = {"password": "s3cr3t-value-1"}', "password_hint = 'your first pet'"]],
        [[]],
        [["", "   ", "# just a comment about passwords and tokens"]],
        [['x = "' + _AK + '"; SECRET="abcdefgh12345678"; ' + _PEM]],
        [["Token = 'my-example-token'", "Token = 'Zx81-real-looking-value'"]],
        [["apikey=\"0123456789abcdef\"", "apikey=0123456789abcdef", "api-key = 'not-a-listed-name'"]],
        [["password = 'aaaaaaaa' ; password = 'bbbbbbbb'", "akia" + "abcdefghijklmnop".upper().lower()]],
    ],
    examples=1,
    wrong_solutions=[
        r'''def scanSecrets(lines):
    found = []
    for number, line in enumerate(lines, start=1):
        low = line.lower()
        if "akia" in low:
            found.append([number, "cloud-access-key"])
        if "acme_" in low:
            found.append([number, "vendor-token"])
        if "private key" in low:
            found.append([number, "private-key"])
        if "password" in low or "secret" in low or "token" in low or "api_key" in low:
            found.append([number, "hardcoded-credential"])
    return sorted(found)
''',
        r'''import re

_ACCESS = re.compile(r"AKIA[A-Z0-9]{16}")
_VENDOR = re.compile(r"acme_[0-9a-f]{32}")
_PEM = re.compile(r"-----BEGIN (?:[A-Z]+ )?PRIVATE KEY-----")
_CRED = re.compile(r"(?i)(?:password|passwd|secret|api_key|apikey|token)[\"']?\s*[:=]\s*([\"'])([^\"']{8,})\1")

def scanSecrets(lines):
    found = []
    for number, line in enumerate(lines, start=1):
        if _ACCESS.search(line):
            found.append([number, "cloud-access-key"])
        if _VENDOR.search(line):
            found.append([number, "vendor-token"])
        if _PEM.search(line):
            found.append([number, "private-key"])
        if _CRED.search(line):
            found.append([number, "hardcoded-credential"])
    return sorted(found)
''',
    ],
    guide=dict(
        prereqs="The misconfiguration and secrets management lesson. Regular expressions: character classes, counted repetition, look-arounds, back-references.",
        intuition="Many credentials have a recognisable *shape* — a fixed prefix and a fixed-length body — which a "
                  "precise pattern detects with few false alarms. Generic assignments have no fixed shape, so that "
                  "rule looks for a suspicious name next to a literal and then filters obvious placeholders.",
        hints=[
            "Compile one pattern per kind; test each against every line and record the kind once.",
            "Use look-arounds such as `(?![A-Z0-9])` to enforce 'exactly N characters'.",
            "For the credential rule capture the opening quote and reuse it as `\\1` to find the matching closing quote; then inspect the captured content for placeholders.",
        ],
        brute_force="Flag any line containing the word `password` or `token` (first wrong solution). The noise is so "
                    "high that developers switch the scanner off within a week.",
        approach="For each line, run the three shape patterns, then iterate over credential matches until one is not a placeholder.\n\n"
                 "Dry run `API_KEY = \"changeme-please\"`: no access key, no vendor token, no PEM header. The credential "
                 "pattern matches with content `changeme-please`; it contains `changeme` → ignored. No findings for this line.",
        complexity="Time O(total characters) — each pattern is linear on these inputs; space O(findings).",
        pitfalls="- Without boundary look-arounds, a 17-character run after `AKIA` still matches its first 16.\n"
                 "- `password = os.environ[...]` is the *right* way to load a secret and must not be flagged: require a quoted literal.\n"
                 "- A second assignment on the same line may be real even when the first is a placeholder — iterate over all matches.\n"
                 "- Scanners find only what they have patterns for. They complement, never replace, keeping secrets out of code in the first place.",
        follow_up="Real tools (gitleaks, trufflehog, GitHub secret scanning) add entropy checks and verify candidate "
                  "keys against the provider. Remember that a secret which reached git history must be **rotated**, not merely deleted.",
    ),
),
dict(
    id="sec-log-redact",
    title="Redact Sensitive Fields Before Logging",
    difficulty="Medium",
    pattern="Logging & Monitoring",
    kind="function",
    entry="redact",
    description=r"""
Logs are copied to many systems and read by many people, so secrets and personal data must be removed
before an event is written. Write `redact(event, sensitive)` that returns a **new** cleaned structure
and leaves `event` untouched.

`event` is JSON-like: dicts (string keys), lists, strings, numbers, booleans and `None`, nested to any
depth. `sensitive` is a list of key names.

Rules:

1. **Sensitive keys.** For any dict key whose lower-cased form equals a lower-cased entry of
   `sensitive`, replace the value — whatever its type — with the string `"[REDACTED]"`. Do not descend into it.
2. **Card-like numbers.** In every other **string** value (including strings inside lists), replace each
   run of 13 to 19 consecutive digits that is not adjacent to further digits with asterisks followed by
   its last four digits (`4111111111111111` → `************1111`). Shorter and longer digit runs are left alone.
3. **Log injection.** After rule 2, replace each carriage return with the two characters `\r` and each
   line feed with the two characters `\n`, so one event can never forge a second log line.
4. Non-string scalars are copied unchanged; keys themselves are never modified.

**Example:** `redact({"user": "ann", "Password": "hunter2", "note": "card 4111111111111111"}, ["password"])`
→ `{"user": "ann", "Password": "[REDACTED]", "note": "card ************1111"}`
""",
    starter='''import re

def redact(event, sensitive: list):
    pass
''',
    solution=r'''import re

_CARD = re.compile(r"(?<!\d)\d{13,19}(?!\d)")

def _mask(match):
    digits = match.group(0)
    return "*" * (len(digits) - 4) + digits[-4:]

def redact(event, sensitive):
    hidden = {name.lower() for name in sensitive}

    def walk(value):
        if isinstance(value, dict):
            return {key: ("[REDACTED]" if key.lower() in hidden else walk(item)) for key, item in value.items()}
        if isinstance(value, list):
            return [walk(item) for item in value]
        if isinstance(value, str):
            text = _CARD.sub(_mask, value)
            return text.replace("\r", "\\r").replace("\n", "\\n")
        return value

    return walk(event)
''',
    tests=[
        [{"user": "ann", "Password": "hunter2", "note": "card 4111111111111111"}, ["password"]],
        [{"user": {"name": "ann", "token": "abc", "profile": {"SSN": "123-45-6789", "city": "Oslo"}}}, ["token", "ssn"]],
        [{"items": [{"api_key": "k1", "qty": 2}, {"api_key": "k2", "qty": 3}], "ok": True, "n": None}, ["API_KEY"]],
        [{"msg": "login failed\nINFO admin logged in", "ip": "10.0.0.1\r\n"}, []],
        [{"a": "123456789012", "b": "1234567890123", "c": "1234567890123456789", "d": "12345678901234567890"}, []],
        [{"text": "two cards 4111111111111111 and 5500005555555559, phone 004712345678"}, []],
        [{"authorization": {"scheme": "Bearer", "value": "xyz"}, "path": "/login"}, ["Authorization"]],
        [{}, ["password"]],
        ["plain string 4111111111111111\n", ["password"]],
        [[{"password": 12345}, "x", 7, ["4111111111111111"]], ["password"]],
        [{"amount": 4111111111111111, "password_hint": "pet", "pass": "word"}, ["password"]],
        [{"q": "id=4111-1111-1111-1111 ref#9999999999999x"}, []],
        [{"Cookie": "sid=abc", "headers": {"cookie": "sid=def", "Accept": "*/*"}}, ["cookie"]],
    ],
    examples=1,
    wrong_solutions=[
        r'''def redact(event, sensitive):
    out = dict(event)
    for key in out:
        if key in sensitive:
            out[key] = "[REDACTED]"
    return out
''',
        r'''import re

_CARD = re.compile(r"\d{13,19}")

def redact(event, sensitive):
    hidden = set(sensitive)

    def walk(value):
        if isinstance(value, dict):
            return {k: ("[REDACTED]" if k in hidden else walk(v)) for k, v in value.items()}
        if isinstance(value, list):
            return [walk(v) for v in value]
        if isinstance(value, str):
            return _CARD.sub(lambda m: "*" * (len(m.group(0)) - 4) + m.group(0)[-4:], value)
        return value

    return walk(event)
''',
    ],
    guide=dict(
        prereqs="The logging, monitoring and vulnerability management lesson. Recursion over nested JSON-like data; `re.sub` with a function.",
        intuition="Redaction is a tree walk with three kinds of node. Dicts decide by **key** whether to hide a "
                  "subtree; strings are scrubbed by **pattern**; everything else passes through. Building new "
                  "containers as you go guarantees the caller's data is not altered.",
        hints=[
            "Write an inner recursive function with `isinstance` branches for dict, list and str.",
            "Lower-case the sensitive names once into a set.",
            "Use look-arounds `(?<!\\d)` and `(?!\\d)` so that a 20-digit run is not partially masked.",
        ],
        brute_force="Redact only top-level keys with exact-case matching. Secrets nested inside `headers` or "
                    "`user.profile`, or spelled `Password`, flow straight into the log store.",
        approach="1. Build the lower-cased set.\n2. `walk(dict)` → new dict, redacting matching keys, recursing into the others.\n"
                 "3. `walk(list)` → new list.\n4. `walk(str)` → mask card-like runs, then escape CR/LF.\n5. Other values returned as is.\n\n"
                 "Dry run `{'msg': 'login failed\\nINFO admin logged in'}`: key `msg` is not sensitive; the string has no "
                 "long digit runs; the newline becomes the two characters backslash-n, so the forged `INFO` text stays on the same log line.",
        complexity="Time O(total size of the structure); space O(same) for the copy, plus recursion depth equal to nesting depth.",
        pitfalls="- Mutating the input changes what the application later sends to the user or stores.\n"
                 "- Case-sensitive key matching misses `Authorization` versus `authorization`.\n"
                 "- An integer that looks like a card number is not a string and is left alone by rule 2 — a reminder that key-based redaction is the primary control.\n"
                 "- Pattern-based scrubbing is a safety net with false negatives (`4111-1111-1111-1111` slips through); "
                 "the reliable control is never putting such data into log events at all.",
        follow_up="Prefer structured logging with an explicit allow-list of fields per event type; block-lists always trail behind new field names.",
    ),
),
dict(
    id="sec-stride-gaps",
    title="STRIDE Coverage Gaps in a Threat Model",
    difficulty="Medium",
    pattern="Threat Modelling",
    kind="function",
    entry="strideGaps",
    description=r"""
In *STRIDE-per-element* threat modelling, each kind of element in a data-flow diagram is examined for a
specific subset of the six threat categories:

| element type | applicable categories |
|---|---|
| `external` (user, third-party system) | **S**poofing, **R**epudiation |
| `process` (running code) | **S**, **T**ampering, **R**, **I**nformation disclosure, **D**enial of service, **E**levation of privilege |
| `datastore` | **T**, **R**, **I**, **D** |
| `dataflow` | **T**, **I**, **D** |

A team has listed the threats it has considered. Find what it has **not** considered.

`strideGaps(elements, threats)`:

- `elements`: list of `{"name": ..., "type": ...}`. Elements with an unknown type are skipped.
- `threats`: list of `{"element": name, "category": text}` where `category` is the full category name in
  any letter case: `spoofing`, `tampering`, `repudiation`, `information disclosure`, `denial of service`,
  `elevation of privilege`. Threats naming an unknown element, an unknown category, or a category that
  does not apply to that element's type are ignored.

Return a list of `[name, missing]` for every element that has at least one applicable category with no
recorded threat. `missing` is a string of the uncovered category letters in the order `S T R I D E`.
Sort the result by element name.

**Example:** elements `[{"name": "api", "type": "process"}]`, threats
`[{"element": "api", "category": "Spoofing"}, {"element": "api", "category": "tampering"}]` → `[["api", "RIDE"]]`
""",
    starter='''def strideGaps(elements: list, threats: list) -> list:
    pass
''',
    solution=r'''_APPLICABLE = {"external": "SR", "process": "STRIDE", "datastore": "TRID", "dataflow": "TID"}
_LETTER = {
    "spoofing": "S", "tampering": "T", "repudiation": "R",
    "information disclosure": "I", "denial of service": "D", "elevation of privilege": "E",
}

def strideGaps(elements, threats):
    kinds = {e["name"]: e["type"] for e in elements if e.get("type") in _APPLICABLE}
    covered = {name: set() for name in kinds}
    for threat in threats:
        name = threat.get("element")
        letter = _LETTER.get(str(threat.get("category", "")).strip().lower())
        if name in kinds and letter and letter in _APPLICABLE[kinds[name]]:
            covered[name].add(letter)
    gaps = []
    for name in sorted(kinds):
        missing = "".join(c for c in "STRIDE" if c in _APPLICABLE[kinds[name]] and c not in covered[name])
        if missing:
            gaps.append([name, missing])
    return gaps
''',
    tests=[
        [[{"name": "api", "type": "process"}], [{"element": "api", "category": "Spoofing"}, {"element": "api", "category": "tampering"}]],
        [_ELEMENTS, []],
        [_ELEMENTS, [{"element": "browser", "category": "Spoofing"}, {"element": "browser", "category": "Repudiation"}]],
        [_ELEMENTS, [{"element": "browser", "category": "Elevation of privilege"}, {"element": "api-to-db", "category": "Spoofing"}]],
        [[{"name": "db", "type": "datastore"}],
         [{"element": "db", "category": "Tampering"}, {"element": "db", "category": "REPUDIATION"},
          {"element": "db", "category": "Information Disclosure"}, {"element": "db", "category": "denial of service"}]],
        [[{"name": "db", "type": "datastore"}], [{"element": "db", "category": "Info leak"}, {"element": "cache", "category": "Tampering"}]],
        [[], [{"element": "api", "category": "Spoofing"}]],
        [[{"name": "queue", "type": "mystery"}, {"name": "flow", "type": "dataflow"}], [{"element": "flow", "category": " Tampering "}]],
        [[{"name": "zeta", "type": "external"}, {"name": "alpha", "type": "dataflow"}, {"name": "mid", "type": "process"}],
         [{"element": "mid", "category": "Denial of Service"}, {"element": "mid", "category": "Elevation of Privilege"},
          {"element": "mid", "category": "Spoofing"}, {"element": "zeta", "category": "Spoofing"}]],
        [[{"name": "api", "type": "process"}],
         [{"element": "api", "category": c} for c in ("spoofing", "tampering", "repudiation", "information disclosure", "denial of service", "elevation of privilege")]],
        [[{"name": "api", "type": "process"}], [{"element": "api", "category": "spoofing"}] * 5],
        [[{"name": "f", "type": "dataflow"}],
         [{"element": "f", "category": "Information disclosure"}, {"element": "f", "category": "Repudiation"}, {"element": "f", "category": "Denial of service"}]],
    ],
    examples=1,
    wrong_solutions=[
        r'''def strideGaps(elements, threats):
    letters = {"spoofing": "S", "tampering": "T", "repudiation": "R", "information disclosure": "I",
               "denial of service": "D", "elevation of privilege": "E"}
    gaps = []
    for e in sorted(elements, key=lambda x: x["name"]):
        covered = {letters.get(t["category"].strip().lower()) for t in threats if t["element"] == e["name"]}
        missing = "".join(c for c in "STRIDE" if c not in covered)
        if missing:
            gaps.append([e["name"], missing])
    return gaps
''',
        r'''_APPLICABLE = {"external": "SR", "process": "STRIDE", "datastore": "TRID", "dataflow": "TID"}

def strideGaps(elements, threats):
    gaps = []
    for e in elements:
        if e["type"] not in _APPLICABLE:
            continue
        covered = {t["category"][0].upper() for t in threats if t["element"] == e["name"] and t["category"]}
        missing = "".join(c for c in _APPLICABLE[e["type"]] if c not in covered)
        if missing:
            gaps.append([e["name"], missing])
    return gaps
''',
    ],
    guide=dict(
        prereqs="The threat modelling lesson: data-flow diagrams, the six STRIDE categories and the property each one violates.",
        intuition="A threat model is only as good as its coverage. Treat the diagram as a checklist generator: every "
                  "element type implies a fixed set of questions; subtracting the questions already answered leaves the gaps.",
        hints=[
            "Two lookup tables do most of the work: type → applicable letters, and category name → letter.",
            "Build `covered[name]` as a set of letters, adding a letter only if it is applicable to that element's type.",
            "Produce the missing string by filtering the constant `'STRIDE'`, which fixes the order for free.",
        ],
        brute_force="Check all six categories for every element. That floods the model with meaningless items "
                    "('elevation of privilege against a network connection') and is what the per-element table exists to avoid.",
        approach="1. Map valid element names to types.\n2. For each threat, normalise the category, look up its letter, "
                 "and record it when the element exists and the letter applies.\n3. For each element in name order compute the uncovered letters.\n\n"
                 "Dry run: `flow` (dataflow, applicable `TID`) with one threat ` Tampering ` → covered `{T}` → missing `ID`. "
                 "The element `queue` of type `mystery` is skipped entirely.",
        complexity="Time O(E log E + T) for E elements and T threats; space O(E).",
        pitfalls="- Using the first letter of the category text maps 'Info leak' to `I` even though it is not a recognised category.\n"
                 "- The data-store string in the table is `TRID` but output order must follow `STRIDE` (`T R I D` — the same here, but derive it rather than assume).\n"
                 "- Ignoring applicability reports impossible gaps and hides real ones behind noise.",
        follow_up="Extend each threat with a mitigation and a status; a threat with no mitigation is itself a gap. Rank the open ones with the risk-scoring problem.",
    ),
),
dict(
    id="sec-risk-prioritise",
    title="Risk Scoring and Prioritisation",
    difficulty="Easy",
    pattern="Vulnerability Management",
    kind="function",
    entry="prioritise",
    description=r"""
A triage meeting needs findings ordered by risk. Use the classic qualitative model
**risk = likelihood × impact**, each on a 1–5 scale.

`prioritise(findings)` receives a list of dicts `{"id": str, "likelihood": int, "impact": int}` and
returns a list of `[id, score, level]`.

- Skip any finding whose `likelihood` or `impact` is missing, is not an `int` (a `bool` does not count
  as an int), or lies outside `1..5`.
- `score = likelihood * impact`.
- `level`: `"critical"` if score ≥ 15; `"high"` if score ≥ 10; `"medium"` if score ≥ 5; otherwise `"low"`.
- Order by score descending; ties by impact descending (a rare catastrophe outranks a frequent
  annoyance); remaining ties by `id` ascending.

**Example:** `prioritise([{"id": "A", "likelihood": 2, "impact": 5}, {"id": "B", "likelihood": 5, "impact": 2}, {"id": "C", "likelihood": 4, "impact": 4}])`
→ `[["C", 16, "critical"], ["A", 10, "high"], ["B", 10, "high"]]`
""",
    starter='''def prioritise(findings: list) -> list:
    pass
''',
    solution=r'''def _valid(value):
    return isinstance(value, int) and not isinstance(value, bool) and 1 <= value <= 5

def prioritise(findings):
    rows = []
    for finding in findings:
        likelihood = finding.get("likelihood")
        impact = finding.get("impact")
        if not _valid(likelihood) or not _valid(impact):
            continue
        score = likelihood * impact
        if score >= 15:
            level = "critical"
        elif score >= 10:
            level = "high"
        elif score >= 5:
            level = "medium"
        else:
            level = "low"
        rows.append((-score, -impact, finding["id"], score, level))
    rows.sort()
    return [[row[2], row[3], row[4]] for row in rows]
''',
    tests=[
        [[{"id": "A", "likelihood": 2, "impact": 5}, {"id": "B", "likelihood": 5, "impact": 2}, {"id": "C", "likelihood": 4, "impact": 4}]],
        [[]],
        [[{"id": "X", "likelihood": 1, "impact": 1}]],
        [[{"id": "X", "likelihood": 5, "impact": 5}, {"id": "Y", "likelihood": 3, "impact": 5}, {"id": "Z", "likelihood": 5, "impact": 3}]],
        [[{"id": "b", "likelihood": 2, "impact": 2}, {"id": "a", "likelihood": 2, "impact": 2}, {"id": "c", "likelihood": 1, "impact": 4}, {"id": "d", "likelihood": 4, "impact": 1}]],
        [[{"id": "bad1", "likelihood": 0, "impact": 5}, {"id": "bad2", "likelihood": 6, "impact": 1}, {"id": "ok", "likelihood": 1, "impact": 5}]],
        [[{"id": "bad", "likelihood": True, "impact": 5}, {"id": "bad2", "likelihood": 2.0, "impact": 5}, {"id": "bad3", "impact": 5}, {"id": "ok", "likelihood": 3, "impact": 3}]],
        [[{"id": "m1", "likelihood": 1, "impact": 5}, {"id": "m2", "likelihood": 5, "impact": 1}, {"id": "l1", "likelihood": 2, "impact": 2}, {"id": "h1", "likelihood": 2, "impact": 5}, {"id": "h2", "likelihood": 3, "impact": 4}]],
        [[{"id": "p", "likelihood": 3, "impact": 5}, {"id": "q", "likelihood": 5, "impact": 3}, {"id": "r", "likelihood": 7, "impact": 2}]],
        [[{"id": "n%02d" % i, "likelihood": (i % 5) + 1, "impact": (i * 3 % 5) + 1} for i in range(40)]],
        [[{"id": "s", "likelihood": "5", "impact": 5}, {"id": "t", "likelihood": 5, "impact": None}]],
        [[{"id": "e1", "likelihood": 2, "impact": 3}, {"id": "e2", "likelihood": 3, "impact": 2}, {"id": "e3", "likelihood": 1, "impact": 4}]],
    ],
    examples=1,
    wrong_solutions=[
        r'''def prioritise(findings):
    rows = []
    for f in findings:
        score = f["likelihood"] * f["impact"]
        level = "critical" if score >= 15 else "high" if score >= 10 else "medium" if score >= 5 else "low"
        rows.append([f["id"], score, level])
    rows.sort(key=lambda r: -r[1])
    return rows
''',
        r'''def prioritise(findings):
    rows = []
    for f in findings:
        l, i = f.get("likelihood"), f.get("impact")
        if not (isinstance(l, int) and isinstance(i, int)) or isinstance(l, bool) or isinstance(i, bool):
            continue
        if not (1 <= l <= 5 and 1 <= i <= 5):
            continue
        score = l + i
        level = "critical" if score >= 15 else "high" if score >= 10 else "medium" if score >= 5 else "low"
        rows.append([f["id"], score, level])
    rows.sort(key=lambda r: (-r[1], r[0]))
    return rows
''',
        r'''def prioritise(findings):
    rows = []
    for f in findings:
        l, i = f.get("likelihood"), f.get("impact")
        if not (isinstance(l, int) and isinstance(i, int)) or isinstance(l, bool) or isinstance(i, bool):
            continue
        if not (1 <= l <= 5 and 1 <= i <= 5):
            continue
        score = l * i
        level = "critical" if score > 15 else "high" if score > 10 else "medium" if score > 5 else "low"
        rows.append((-score, f["id"], score, level))
    rows.sort()
    return [[r[1], r[2], r[3]] for r in rows]
''',
    ],
    guide=dict(
        prereqs="The threat modelling lesson (risk rating) and the vulnerability management lesson (triage). Sorting with composite keys.",
        intuition="Risk has two independent ingredients: how likely something is to happen and how bad it would be. "
                  "Multiplying them gives a single number to sort by; the tie-break by impact encodes the judgement "
                  "that severe outcomes deserve attention first.",
        hints=[
            "Filter invalid rows before computing anything.",
            "Map the score to a level with a descending chain of `>=` comparisons.",
            "Sort by the tuple `(-score, -impact, id)`.",
        ],
        brute_force="Sort by score alone with a stable sort and hope the input order is helpful. Ties then come out "
                    "in arbitrary order and two analysts get two different priority lists from the same data.",
        approach="1. Validate. 2. Score and level. 3. Sort with the three-part key. 4. Project to `[id, score, level]`.\n\n"
                 "Dry run of the example: A = 2×5 = 10 (high), B = 5×2 = 10 (high), C = 4×4 = 16 (critical). C first. A and B tie "
                 "on score; A has impact 5, B has impact 2 → A before B.",
        complexity="Time O(n log n) for the sort; space O(n).",
        pitfalls="- `True` passes `isinstance(x, int)`; exclude bools.\n"
                 "- Thresholds are inclusive (`>= 15` is critical, so 3 × 5 qualifies).\n"
                 "- Adding instead of multiplying compresses the scale and reorders findings.\n"
                 "- Ordinal 1–5 scores are a communication tool, not a measurement: 4 × 4 is not literally 'more risk' than 3 × 5 in any physical sense.",
        follow_up="Compare with CVSS, which scores a vulnerability's intrinsic severity; organisations combine it with "
                  "exploit likelihood (EPSS, known-exploited lists) and asset criticality to decide what to patch first.",
    ),
),
]
