import base64 as _b64
import hashlib as _hl
import hmac as _hm
import json as _js


def _b64u(raw):
    return _b64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def _jwt(payload, secret="top-secret", header=None):
    head = header if header is not None else {"alg": "HS256", "typ": "JWT"}
    h = _b64u(_js.dumps(head, separators=(",", ":")).encode())
    p = _b64u(_js.dumps(payload, separators=(",", ":"), sort_keys=True).encode())
    sig = _hm.new(secret.encode(), f"{h}.{p}".encode(), _hl.sha256).digest()
    return f"{h}.{p}.{_b64u(sig)}"


def _stored(password, salt_hex, iterations):
    digest = _hl.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), iterations).hex()
    return f"pbkdf2_sha256${iterations}${salt_hex}${digest}"


_OK = _jwt({"sub": "u1", "exp": 2000, "aud": "shop-api"})
_h, _p, _s = _OK.split(".")
_ADMIN_PAYLOAD = _b64u(_js.dumps({"aud": "shop-api", "exp": 2000, "role": "admin", "sub": "u1"}, separators=(",", ":")).encode())
_TAMPERED = f"{_h}.{_ADMIN_PAYLOAD}.{_s}"
_NONE_HEAD = _b64u(b'{"alg":"none","typ":"JWT"}')
_ALG_NONE = f"{_NONE_HEAD}.{_p}."
_ALG_NONE_SIGNED = _jwt({"sub": "u1", "exp": 2000, "aud": "shop-api"}, header={"alg": "none", "typ": "JWT"})
_HS512 = _jwt({"sub": "u1", "exp": 2000, "aud": "shop-api"}, header={"alg": "HS512", "typ": "JWT"})
_WRONG_KEY = _jwt({"sub": "u1", "exp": 2000, "aud": "shop-api"}, secret="guess")
_NO_EXP = _jwt({"sub": "u1", "aud": "shop-api"})
_STR_EXP = _jwt({"sub": "u1", "exp": "2000", "aud": "shop-api"})
_NBF = _jwt({"sub": "u1", "exp": 2000, "nbf": 1500, "aud": "shop-api"})
_AUD_LIST = _jwt({"sub": "u1", "exp": 2000, "aud": ["billing", "shop-api"]})
_AUD_OTHER = _jwt({"sub": "u1", "exp": 2000, "aud": "billing"})
_NO_AUD = _jwt({"sub": "u1", "exp": 2000})
_EXPIRED_WRONG_AUD = _jwt({"sub": "u1", "exp": 900, "aud": "billing"})
_NOT_JSON = _b64u(b"hello") + "." + _p + "." + _s
_ARRAY_PAYLOAD = _jwt([1, 2, 3])

_S1 = _stored("correct horse", "00112233445566778899aabbccddeeff", 1000)
_S2 = _stored("correct horse", "ffeeddccbbaa99887766554433221100", 1000)
_S_OLD = _stored("legacy-pass", "0a0b0c0d0e0f1011", 300)

_ROLES = {
    "viewer": {"permissions": ["orders:read", "products:read"]},
    "support": {"permissions": ["orders:refund"], "inherits": ["viewer"]},
    "catalog": {"permissions": ["products:*"]},
    "manager": {"permissions": [], "inherits": ["support", "catalog"]},
    "root": {"permissions": ["*"]},
    "loop-a": {"permissions": ["a:read"], "inherits": ["loop-b"]},
    "loop-b": {"permissions": ["b:read"], "inherits": ["loop-a"]},
}

PROBLEMS = [
dict(
    id="sec-constant-time-compare",
    title="Constant-Time Comparison",
    difficulty="Easy",
    pattern="Cryptographic Hygiene",
    kind="function",
    entry="ctCompare",
    description=r"""
Comparing a secret (an API key, a MAC, a reset token) with `==` stops at the first differing byte. The
time taken therefore reveals how long the matching prefix is, and with enough measurements a secret can
be recovered byte by byte. A *constant-time* comparison examines every byte no matter where the first
difference is.

Write `ctCompare(a, b)` for two strings. Work on their UTF-8 encodings and return `[equal, examined]`:

- If the two byte strings have **different lengths**, return `[False, 0]` (length is not treated as secret).
- Otherwise look at **every** byte pair, even after a mismatch has been found, accumulating the
  difference (for example by OR-ing together the XOR of each pair). Return `[equal, examined]` where
  `examined` is the number of byte pairs inspected — it must always equal the byte length.

Do not use `==` on the whole strings and do not `break`/`return` early inside the loop.

**Example:** `ctCompare("s3cret", "s3cret")` → `[True, 6]`

**Example:** `ctCompare("Xbcdef", "abcdef")` → `[False, 6]` (the first byte differs, yet all six are examined)

**Example:** `ctCompare("abc", "abcd")` → `[False, 0]`
""",
    starter='''def ctCompare(a: str, b: str) -> list:
    pass
''',
    solution=r'''def ctCompare(a, b):
    x = a.encode("utf-8")
    y = b.encode("utf-8")
    if len(x) != len(y):
        return [False, 0]
    diff = 0
    examined = 0
    for p, q in zip(x, y):
        diff |= p ^ q
        examined += 1
    return [diff == 0, examined]
''',
    tests=[
        ["s3cret", "s3cret"],
        ["Xbcdef", "abcdef"],
        ["abc", "abcd"],
        ["", ""],
        ["abcdeX", "abcdef"],
        ["abXdef", "abcdef"],
        ["a", "b"],
        ["é", "e"],
        ["été", "été"],
        ["éa", "èa"],
        ["k" * 500, "k" * 499 + "j"],
        ["k" * 500, "j" + "k" * 499],
        ["token", ""],
    ],
    examples=3,
    wrong_solutions=[
        r'''def ctCompare(a, b):
    x, y = a.encode("utf-8"), b.encode("utf-8")
    if len(x) != len(y):
        return [False, 0]
    examined = 0
    for p, q in zip(x, y):
        examined += 1
        if p != q:
            return [False, examined]
    return [True, examined]
''',
        r'''def ctCompare(a, b):
    if len(a) != len(b):
        return [False, 0]
    diff = 0
    examined = 0
    for p, q in zip(a, b):
        diff |= ord(p) ^ ord(q)
        examined += 1
    return [diff == 0, examined]
''',
    ],
    guide=dict(
        prereqs="The authentication lesson's section on timing side channels. Bitwise XOR and OR.",
        intuition="XOR of two equal bytes is zero. OR-ing all the XOR results together gives zero only if every pair "
                  "matched. Nothing in that loop depends on *where* a mismatch occurs, so the running time carries no "
                  "information about the secret.",
        hints=[
            "Encode both strings first; secrets are compared as bytes.",
            "Different lengths can be answered immediately — that is the one permitted shortcut.",
            "Keep a single integer `diff`; do `diff |= p ^ q` for every pair and test `diff == 0` after the loop.",
        ],
        brute_force="`return a == b` or a loop that returns at the first mismatch. Both are correct as *equality* "
                    "checks and wrong as *secret* checks, because their duration grows with the length of the matching prefix.",
        approach="1. Encode. 2. Length mismatch → `[False, 0]`. 3. Loop over all pairs accumulating `diff` and counting. "
                 "4. Return `[diff == 0, examined]`.\n\n"
                 "Dry run `('Xbcdef', 'abcdef')`: pair 1 gives `0x58 ^ 0x61 = 0x39`, so `diff = 0x39`; pairs 2–6 XOR to 0 "
                 "and leave `diff` unchanged; `examined` reaches 6. Result `[False, 6]`.",
        complexity="Time Θ(n) for n bytes — always the full length, by design; space O(n) for the encoded copies.",
        pitfalls="- Counting characters instead of bytes: `'é'` is one character but two UTF-8 bytes.\n"
                 "- Any early exit reintroduces the leak.\n"
                 "- In real code never hand-roll this: Python's interpreter adds timing noise of its own. Use "
                 "`hmac.compare_digest` (or `secrets.compare_digest`), which is implemented in C for exactly this purpose.",
        follow_up="Where even the length is sensitive, compare fixed-length digests: `compare_digest(sha256(a), sha256(b))`.",
    ),
),
dict(
    id="sec-password-policy",
    title="Password Policy Checker",
    difficulty="Easy",
    pattern="Authentication",
    kind="function",
    entry="checkPassword",
    description=r"""
Modern guidance (NIST SP 800-63B, OWASP) favours **length** and **screening against known-bad
passwords** over forced mixtures of symbols. Implement that style of policy.

Write `checkPassword(password, username, banned)` returning a list of violations in exactly this order
(an empty list means the password is acceptable):

1. `"too-short"` — fewer than 12 characters.
2. `"too-long"` — more than 128 characters (an upper bound keeps hashing cost bounded).
3. `"contains-username"` — `username` has at least 3 characters and appears inside the password,
   ignoring letter case.
4. `"common-password"` — the lower-cased password is in the list `banned` (entries are lower-case).
5. `"low-variety"` — the password uses fewer than 5 distinct characters (e.g. `aaaaaaaaaaaa`).

There are **no** composition rules: `correct horse battery` is fine without digits or symbols, and
spaces and non-ASCII characters are allowed.

**Example:** `checkPassword("Password1234", "ann", ["password1234"])` → `["common-password"]`

**Example:** `checkPassword("ann2024", "Ann", [])` → `["too-short", "contains-username"]`
""",
    starter='''def checkPassword(password: str, username: str, banned: list) -> list:
    pass
''',
    solution=r'''def checkPassword(password, username, banned):
    problems = []
    if len(password) < 12:
        problems.append("too-short")
    if len(password) > 128:
        problems.append("too-long")
    lowered = password.lower()
    if len(username) >= 3 and username.lower() in lowered:
        problems.append("contains-username")
    if lowered in banned:
        problems.append("common-password")
    if len(set(password)) < 5:
        problems.append("low-variety")
    return problems
''',
    tests=[
        ["Password1234", "ann", ["password1234"]],
        ["ann2024", "Ann", []],
        ["correct horse battery", "ann", ["password1234"]],
        ["", "ann", []],
        ["aaaaaaaaaaaa", "bob", []],
        ["x" * 129, "bob", []],
        ["abcdefghijkl" * 10 + "abcdefgh", "bob", []],
        ["MyNameIsROBERTA!!", "roberta", []],
        ["al-is-my-login-ok", "al", []],
        ["abababababab", "zed", ["abababababab"]],
        ["Tr0ub4dor&3xyz", "", []],
        ["пароль длинный", "ivan", []],
        ["qwertyuiopas", "qwe", ["qwertyuiopas"]],
        ["abcd abcd ab", "zed", []],
    ],
    examples=2,
    wrong_solutions=[
        r'''def checkPassword(password, username, banned):
    problems = []
    if len(password) < 12:
        problems.append("too-short")
    if len(password) > 128:
        problems.append("too-long")
    if username in password:
        problems.append("contains-username")
    if password in banned:
        problems.append("common-password")
    if len(set(password)) < 5:
        problems.append("low-variety")
    return problems
''',
        r'''def checkPassword(password, username, banned):
    problems = []
    if len(password) < 12:
        problems.append("too-short")
    if len(password) >= 128:
        problems.append("too-long")
    lowered = password.lower()
    if len(username) >= 3 and username.lower() in lowered:
        problems.append("contains-username")
    if lowered in banned:
        problems.append("common-password")
    if not any(c.isdigit() for c in password):
        problems.append("low-variety")
    return problems
''',
    ],
    guide=dict(
        prereqs="The authentication failures lesson (credential stuffing, why composition rules backfire).",
        intuition="A password is weak when attackers will try it early: because it is short, because it is on a "
                  "breach list, or because it is derived from something public such as the user name. Test for those "
                  "properties directly rather than demanding symbols.",
        hints=[
            "Five independent `if` statements in the stated order — no `elif`.",
            "Lower-case the password once and reuse it for the user-name and ban-list checks.",
            "`len(set(password))` counts distinct characters.",
        ],
        brute_force="A regular expression demanding upper, lower, digit and symbol. It rejects strong passphrases and "
                    "happily accepts `Password1!`, which sits near the top of every cracking dictionary.",
        approach="Evaluate the five predicates in order, appending a code for each that fires.\n\n"
                 "Dry run `('ann2024', 'Ann', [])`: length 7 < 12 → `too-short`; not too long; `ann` (3 chars) is in "
                 "`ann2024` → `contains-username`; not banned; distinct characters `a n 2 0 4` = 5 → fine.",
        complexity="Time O(n + b) for a password of length n and b banned entries (O(n) with a set); space O(n).",
        pitfalls="- An empty or very short user name is a substring of everything; hence the 3-character minimum.\n"
                 "- The upper bound is `> 128`, so exactly 128 characters is allowed.\n"
                 "- Never truncate or strip a password silently, and never limit which characters may be used.\n"
                 "- Policy checks run when a password is *set*; they are not a substitute for slow hashing and rate limiting.",
        follow_up="Real systems screen against large breach corpora using a k-anonymity range query (only the first "
                  "five hex characters of the SHA-1 leave your server), as the Have I Been Pwned API does.",
    ),
),
dict(
    id="sec-password-hash",
    title="Salted PBKDF2 Hash, Verify and Rehash",
    difficulty="Medium",
    pattern="Password Storage",
    kind="class",
    entry="PasswordHasher",
    description=r"""
Store passwords as a salted, deliberately slow hash in a self-describing format, and verify against it.

`PasswordHasher(iterations)` — the work factor used for **new** hashes.

- `hash(password, salt_hex)` → `"pbkdf2_sha256$<iterations>$<salt_hex>$<digest_hex>"` where the digest is
  `hashlib.pbkdf2_hmac("sha256", password_utf8, bytes.fromhex(salt_hex), iterations)` in lower-case hex.
  (The salt is passed in so results are reproducible; production code uses `secrets.token_bytes(16)`.)
- `verify(password, stored)` → `True` if `password` matches. The iteration count and salt are read
  **from the stored string**, not from the hasher. Return `False` (never raise) when `stored` is
  malformed: not exactly four `$`-separated parts, first part not `pbkdf2_sha256`, iterations not a
  positive decimal integer, or salt that is not valid hex. Compare digests with `hmac.compare_digest`.
- `needs_rehash(stored)` → `True` if `stored` is malformed or its iteration count is lower than this
  hasher's `iterations`; otherwise `False`. Applications call this after a successful login to upgrade
  old hashes transparently.

**Example:** `h = PasswordHasher(1000)`; `s = h.hash("correct horse", "00ff")`; `h.verify("correct horse", s)` → `True`;
`h.verify("Correct horse", s)` → `False`; `PasswordHasher(5000).needs_rehash(s)` → `True`.
""",
    starter='''import hashlib
import hmac

class PasswordHasher:
    def __init__(self, iterations: int):
        pass

    def hash(self, password: str, salt_hex: str) -> str:
        pass

    def verify(self, password: str, stored: str) -> bool:
        pass

    def needs_rehash(self, stored: str) -> bool:
        pass
''',
    solution=r'''import hashlib
import hmac

class PasswordHasher:
    def __init__(self, iterations):
        self.iterations = iterations

    @staticmethod
    def _digest(password, salt, iterations):
        return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations).hex()

    @staticmethod
    def _parse(stored):
        if not isinstance(stored, str):
            return None
        parts = stored.split("$")
        if len(parts) != 4 or parts[0] != "pbkdf2_sha256":
            return None
        if not parts[1] or any(c not in "0123456789" for c in parts[1]):
            return None
        iterations = int(parts[1])
        if iterations <= 0:
            return None
        try:
            salt = bytes.fromhex(parts[2])
        except ValueError:
            return None
        return iterations, salt, parts[3]

    def hash(self, password, salt_hex):
        digest = self._digest(password, bytes.fromhex(salt_hex), self.iterations)
        return "pbkdf2_sha256$%d$%s$%s" % (self.iterations, salt_hex, digest)

    def verify(self, password, stored):
        parsed = self._parse(stored)
        if parsed is None:
            return False
        iterations, salt, expected = parsed
        actual = self._digest(password, salt, iterations)
        return hmac.compare_digest(actual.encode(), expected.encode())

    def needs_rehash(self, stored):
        parsed = self._parse(stored)
        return parsed is None or parsed[0] < self.iterations
''',
    tests=[
        [["PasswordHasher", "hash", "verify", "verify"],
         [[1000], ["correct horse", "00112233445566778899aabbccddeeff"], ["correct horse", _S1], ["Correct horse", _S1]]],
        [["PasswordHasher", "hash", "hash"],
         [[1000], ["correct horse", "00112233445566778899aabbccddeeff"], ["correct horse", "ffeeddccbbaa99887766554433221100"]]],
        [["PasswordHasher", "verify", "verify"], [[1000], ["correct horse", _S2], ["correct horse ", _S2]]],
        [["PasswordHasher", "verify", "needs_rehash"], [[2000], ["legacy-pass", _S_OLD], [_S_OLD]]],
        [["PasswordHasher", "needs_rehash", "needs_rehash"], [[1000], [_S1], [_S_OLD]]],
        [["PasswordHasher", "needs_rehash"], [[500], [_S1]]],
        [["PasswordHasher", "verify", "verify", "verify"], [[1000], ["x", ""], ["x", "pbkdf2_sha256$1000$00ff"], ["x", "a$b$c$d$e"]]],
        [["PasswordHasher", "verify", "verify"],
         [[1000], ["correct horse", _S1.replace("pbkdf2_sha256", "md5")], ["correct horse", _S1.replace("$1000$", "$ten$")]]],
        [["PasswordHasher", "verify", "verify"],
         [[1000], ["correct horse", _S1.replace("$1000$", "$0$")], ["correct horse", _S1.replace("0011", "zz11")]]],
        [["PasswordHasher", "needs_rehash", "needs_rehash"], [[1000], ["garbage"], [_S1.replace("$1000$", "$-5$")]]],
        [["PasswordHasher", "hash", "verify"], [[600], ["pässwörd ☃", "abcd"], ["pässwörd ☃", _stored("pässwörd ☃", "abcd", 600)]]],
        [["PasswordHasher", "verify"], [[1000], ["correct horse", _S1[:-2] + "00"]]],
        [["PasswordHasher", "hash", "verify"], [[1], ["", ""], ["", _stored("", "", 1)]]],
    ],
    examples=1,
    wrong_solutions=[
        r'''import hashlib
import hmac

class PasswordHasher:
    def __init__(self, iterations):
        self.iterations = iterations

    def hash(self, password, salt_hex):
        d = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), self.iterations).hex()
        return "pbkdf2_sha256$%d$%s$%s" % (self.iterations, salt_hex, d)

    def verify(self, password, stored):
        parts = stored.split("$")
        if len(parts) != 4:
            return False
        return hmac.compare_digest(self.hash(password, parts[2]), stored)

    def needs_rehash(self, stored):
        parts = stored.split("$")
        return len(parts) != 4 or int(parts[1]) < self.iterations
''',
        r'''import hashlib

class PasswordHasher:
    def __init__(self, iterations):
        self.iterations = iterations

    def hash(self, password, salt_hex):
        d = hashlib.sha256(bytes.fromhex(salt_hex) + password.encode()).hexdigest()
        return "pbkdf2_sha256$%d$%s$%s" % (self.iterations, salt_hex, d)

    def verify(self, password, stored):
        parts = stored.split("$")
        if len(parts) != 4:
            return False
        return self.hash(password, parts[2]).split("$")[3] == parts[3]

    def needs_rehash(self, stored):
        return False
''',
    ],
    guide=dict(
        prereqs="The authentication failures lesson: salts, work factors, why fast hashes are unsuitable. `hashlib.pbkdf2_hmac`.",
        intuition="A stored password record should carry everything needed to check it — algorithm, cost, salt, "
                  "digest — so that the cost can be raised later without breaking old accounts. Verification re-runs "
                  "the derivation with the *record's* parameters and compares the result in constant time.",
        hints=[
            "Write one parser that turns a stored string into `(iterations, salt_bytes, digest_hex)` or `None`; both `verify` and `needs_rehash` use it.",
            "`bytes.fromhex` raises `ValueError` on bad input — catch it.",
            "In `verify`, derive with the iteration count you parsed, not `self.iterations`.",
        ],
        brute_force="Store `sha256(password)` — or worse, the password. Identical passwords then share a hash, "
                    "precomputed tables apply, and commodity GPUs test billions of guesses per second.",
        approach="`hash`: derive with `self.iterations`, format the four fields.\n"
                 "`verify`: parse → derive with parsed parameters → `compare_digest`.\n"
                 "`needs_rehash`: unparseable or weaker than current policy.\n\n"
                 "Dry run: hasher at 2000 iterations verifies a record `pbkdf2_sha256$300$0a0b…$…`. Parsing gives 300 "
                 "iterations; deriving with 300 reproduces the digest → `True`. `needs_rehash` sees 300 < 2000 → `True`, so "
                 "the application re-hashes the password it has just been given and stores the new record.",
        complexity="Time O(iterations × password length) per hash or verify — intentionally expensive; space O(1).",
        pitfalls="- Using the hasher's current iteration count to verify old records locks every existing user out after a cost increase.\n"
                 "- Raising an exception on a corrupt record turns one bad row into a login outage or an error-based oracle.\n"
                 "- `int('-5')` succeeds; reject non-digit strings and non-positive counts explicitly.\n"
                 "- One global salt ('pepper only') does not replace per-user random salts.",
        follow_up="OWASP currently recommends Argon2id first, scrypt second, and PBKDF2-HMAC-SHA256 at 600,000 "
                  "iterations where FIPS compliance is required. The verify-then-rehash pattern is identical for all of them.",
    ),
),
dict(
    id="sec-jwt-validate",
    title="Validate a JWT (HS256 Subset)",
    difficulty="Hard",
    pattern="Token Validation",
    kind="function",
    entry="validateJwt",
    description=r"""
Implement the receiving side of JSON Web Tokens for one fixed algorithm, HS256, with the claim checks an
API needs. Use only `base64`, `hashlib`, `hmac` and `json`.

A token is `header.payload.signature`; each part is base64url **without** `=` padding. The signature is
`HMAC-SHA256(secret_utf8, ascii("header.payload"))` over the first two parts exactly as received.

Write `validateJwt(token, secret, now, audience)` returning the payload dict on success, or the first
applicable error string, checked in this order:

1. `"malformed"` — `token` is not a string with exactly three dot-separated parts; or the header or the
   payload does not base64url-decode to a JSON **object**.
2. `"bad-alg"` — header `alg` is not exactly `"HS256"`. This is decided by **your** code, before any
   signature work: tokens announcing `none`, `HS512`, `RS256`… are refused.
3. `"bad-signature"` — the signature part does not decode, or does not match (use `hmac.compare_digest`).
4. `"expired"` — `exp` is missing, is not a number (`int`/`float`, and not a `bool`), or `now >= exp`.
5. `"not-yet-valid"` — `nbf` is present and is a number and `now < nbf`.
6. `"bad-audience"` — `aud` is missing; or is a string different from `audience`; or is a list that does
   not contain `audience`; or is any other type.

`now` is supplied by the caller (seconds), so the function is deterministic.

**Example:** a token with payload `{"sub":"u1","exp":2000,"aud":"shop-api"}` signed with `"top-secret"`:
`validateJwt(t, "top-secret", 1000, "shop-api")` → the payload; with `now = 2000` → `"expired"`;
with `audience = "billing"` → `"bad-audience"`.
""",
    starter='''import base64
import hashlib
import hmac
import json

def validateJwt(token, secret: str, now, audience: str):
    pass
''',
    solution=r'''import base64
import hashlib
import hmac
import json

def _decode(segment):
    return base64.urlsafe_b64decode(segment + "=" * (-len(segment) % 4))

def _number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)

def validateJwt(token, secret, now, audience):
    if not isinstance(token, str):
        return "malformed"
    parts = token.split(".")
    if len(parts) != 3:
        return "malformed"
    try:
        header = json.loads(_decode(parts[0]))
        payload = json.loads(_decode(parts[1]))
    except Exception:
        return "malformed"
    if not isinstance(header, dict) or not isinstance(payload, dict):
        return "malformed"
    if header.get("alg") != "HS256":
        return "bad-alg"
    signed = (parts[0] + "." + parts[1]).encode("ascii", "replace")
    expected = hmac.new(secret.encode("utf-8"), signed, hashlib.sha256).digest()
    try:
        supplied = _decode(parts[2])
    except Exception:
        return "bad-signature"
    if not hmac.compare_digest(supplied, expected):
        return "bad-signature"
    exp = payload.get("exp")
    if not _number(exp) or now >= exp:
        return "expired"
    nbf = payload.get("nbf")
    if _number(nbf) and now < nbf:
        return "not-yet-valid"
    aud = payload.get("aud")
    if isinstance(aud, str):
        if aud != audience:
            return "bad-audience"
    elif isinstance(aud, list):
        if audience not in aud:
            return "bad-audience"
    else:
        return "bad-audience"
    return payload
''',
    tests=[
        [_OK, "top-secret", 1000, "shop-api"],
        [_OK, "top-secret", 2000, "shop-api"],
        [_OK, "top-secret", 1000, "billing"],
        [_TAMPERED, "top-secret", 1000, "shop-api"],
        [_ALG_NONE, "top-secret", 1000, "shop-api"],
        [_ALG_NONE_SIGNED, "top-secret", 1000, "shop-api"],
        [_HS512, "top-secret", 1000, "shop-api"],
        [_WRONG_KEY, "top-secret", 1000, "shop-api"],
        [_NO_EXP, "top-secret", 1000, "shop-api"],
        [_STR_EXP, "top-secret", 1000, "shop-api"],
        [_NBF, "top-secret", 1499, "shop-api"],
        [_NBF, "top-secret", 1500, "shop-api"],
        [_AUD_LIST, "top-secret", 1999, "shop-api"],
        [_AUD_OTHER, "top-secret", 1000, "shop-api"],
        [_NO_AUD, "top-secret", 1000, "shop-api"],
        [_EXPIRED_WRONG_AUD, "top-secret", 1000, "shop-api"],
        ["not-a-token", "top-secret", 1000, "shop-api"],
        [_OK + ".extra", "top-secret", 1000, "shop-api"],
        [_NOT_JSON, "top-secret", 1000, "shop-api"],
        [_ARRAY_PAYLOAD, "top-secret", 1000, "shop-api"],
        [None, "top-secret", 1000, "shop-api"],
        [_OK[:-3] + "AAA", "top-secret", 1000, "shop-api"],
    ],
    examples=3,
    wrong_solutions=[
        r'''import base64, hashlib, hmac, json

def _decode(segment):
    return base64.urlsafe_b64decode(segment + "=" * (-len(segment) % 4))

def validateJwt(token, secret, now, audience):
    if not isinstance(token, str) or token.count(".") != 2:
        return "malformed"
    h, p, s = token.split(".")
    try:
        header, payload = json.loads(_decode(h)), json.loads(_decode(p))
    except Exception:
        return "malformed"
    if not isinstance(header, dict) or not isinstance(payload, dict):
        return "malformed"
    if header.get("alg") == "none":
        pass
    elif header.get("alg") == "HS256":
        expected = hmac.new(secret.encode(), (h + "." + p).encode(), hashlib.sha256).digest()
        try:
            if not hmac.compare_digest(_decode(s), expected):
                return "bad-signature"
        except Exception:
            return "bad-signature"
    else:
        return "bad-alg"
    exp = payload.get("exp")
    if not isinstance(exp, (int, float)) or now >= exp:
        return "expired"
    aud = payload.get("aud")
    if aud != audience and not (isinstance(aud, list) and audience in aud):
        return "bad-audience"
    return payload
''',
        r'''import base64, json

def validateJwt(token, secret, now, audience):
    if not isinstance(token, str) or token.count(".") != 2:
        return "malformed"
    p = token.split(".")[1]
    try:
        payload = json.loads(base64.urlsafe_b64decode(p + "=" * (-len(p) % 4)))
    except Exception:
        return "malformed"
    if not isinstance(payload, dict):
        return "malformed"
    exp = payload.get("exp")
    if not isinstance(exp, (int, float)) or now >= exp:
        return "expired"
    aud = payload.get("aud")
    if aud != audience and not (isinstance(aud, list) and audience in aud):
        return "bad-audience"
    return payload
''',
        r'''import base64, hashlib, hmac, json

def _decode(segment):
    return base64.urlsafe_b64decode(segment + "=" * (-len(segment) % 4))

def validateJwt(token, secret, now, audience):
    if not isinstance(token, str) or token.count(".") != 2:
        return "malformed"
    h, p, s = token.split(".")
    try:
        header, payload = json.loads(_decode(h)), json.loads(_decode(p))
    except Exception:
        return "malformed"
    if not isinstance(header, dict) or not isinstance(payload, dict):
        return "malformed"
    if header.get("alg") != "HS256":
        return "bad-alg"
    expected = hmac.new(secret.encode(), (h + "." + p).encode(), hashlib.sha256).digest()
    try:
        if not hmac.compare_digest(_decode(s), expected):
            return "bad-signature"
    except Exception:
        return "bad-signature"
    if "exp" in payload and now > payload["exp"]:
        return "expired"
    return payload
''',
    ],
    guide=dict(
        prereqs="The JWT pitfalls lesson; base64url; HMAC. Understand that the payload is readable by anyone and trusted only after the signature check.",
        intuition="Everything inside a token is attacker-supplied text until the signature has been verified with an "
                  "algorithm and key chosen by the **server**. Only then do the claims mean anything — and they still "
                  "have to say 'not expired' and 'meant for this service'.",
        hints=[
            "Write a tiny helper that restores padding: `segment + '=' * (-len(segment) % 4)`.",
            "Pin the algorithm: compare `header['alg']` with the constant `'HS256'`; never look the algorithm up from the header to decide *how* to verify.",
            "Compute the MAC over the received `header.payload` text, not over re-serialised JSON.",
        ],
        brute_force="Decode the middle part and read the claims. That 'validates' any token anyone types, which is "
                    "why libraries separate `decode` from `verify` and why code review should look for the unverified variant.",
        approach="1. Shape: string, three parts.\n2. Decode header and payload to dicts.\n3. `alg == 'HS256'`.\n"
                 "4. Recompute HMAC, constant-time compare with decoded signature.\n5. `exp`, then `nbf`, then `aud`.\n\n"
                 "Dry run on the tampered token (payload swapped for one with `role: admin`, original signature kept): "
                 "shape fine, both parts are JSON objects, `alg` is HS256, but the MAC of the new `header.payload` text "
                 "differs from the supplied signature → `bad-signature`. The `role` claim is never looked at.",
        complexity="Time O(n) in the token length; space O(n).",
        pitfalls="- Honouring `alg: none`, or selecting the verification routine from the header (algorithm confusion).\n"
                 "- Treating a missing `exp` as 'never expires'.\n"
                 "- `now > exp` instead of `now >= exp`: the token is invalid *at* its expiry time.\n"
                 "- Skipping `aud` lets a token issued for one service be replayed against another that shares the key or issuer.\n"
                 "- JSON `true` is an `int` in Python (`isinstance(True, int)`), so exclude bools from numeric claims.",
        follow_up="Production code should use a maintained library with an explicit `algorithms=[...]` allow-list, "
                  "validate `iss`, allow a few seconds of clock skew, and support key rotation through `kid` looked up in a trusted key set.",
    ),
),
dict(
    id="sec-rbac-check",
    title="Role-Based Access Check with Inheritance",
    difficulty="Medium",
    pattern="Access Control",
    kind="function",
    entry="can",
    description=r"""
Implement the decision function of a small role-based access control (RBAC) system. The default answer
is **deny**.

`can(roles, user_roles, permission)` returns a bool.

- `roles` maps a role name to a dict with optional keys `"permissions"` (list of grants) and
  `"inherits"` (list of role names whose grants this role also receives, transitively).
- `user_roles` is the list of roles assigned to the user. Names that are not defined in `roles` are
  ignored (they grant nothing).
- `permission` has the form `"resource:action"`, for example `"orders:refund"`.

A grant matches the requested permission when it is:

- exactly equal to it; or
- `"resource:*"` with the **same resource** (all actions on that resource); or
- `"*"` (everything).

Nothing else matches — in particular `orders:read` does not imply `orders:refund`, and `order:*` does not
cover `orders:read`. Inheritance graphs may contain cycles; your function must terminate.

**Example:** with `roles = {"viewer": {"permissions": ["orders:read"]}, "support": {"permissions": ["orders:refund"], "inherits": ["viewer"]}}`:
`can(roles, ["support"], "orders:read")` → `True`; `can(roles, ["viewer"], "orders:refund")` → `False`.
""",
    starter='''def can(roles: dict, user_roles: list, permission: str) -> bool:
    pass
''',
    solution=r'''def can(roles, user_roles, permission):
    resource = permission.split(":", 1)[0]
    seen = set()
    stack = list(user_roles)
    while stack:
        role = stack.pop()
        if role in seen or role not in roles:
            continue
        seen.add(role)
        definition = roles[role]
        for grant in definition.get("permissions", []):
            if grant == permission or grant == "*" or grant == resource + ":*":
                return True
        stack.extend(definition.get("inherits", []))
    return False
''',
    tests=[
        [_ROLES, ["support"], "orders:read"],
        [_ROLES, ["viewer"], "orders:refund"],
        [_ROLES, ["support"], "orders:refund"],
        [_ROLES, ["catalog"], "products:delete"],
        [_ROLES, ["catalog"], "orders:read"],
        [_ROLES, ["manager"], "products:delete"],
        [_ROLES, ["manager"], "orders:read"],
        [_ROLES, ["manager"], "users:delete"],
        [_ROLES, ["root"], "users:delete"],
        [_ROLES, [], "orders:read"],
        [_ROLES, ["ghost"], "orders:read"],
        [_ROLES, ["loop-a"], "b:read"],
        [_ROLES, ["loop-a"], "c:read"],
        [_ROLES, ["viewer", "catalog"], "products:update"],
        [_ROLES, ["viewer"], "orders:read:all"],
        [{"clerk": {"permissions": ["order:*"]}}, ["clerk"], "orders:read"],
        [{"clerk": {"inherits": ["missing"]}}, ["clerk"], "orders:read"],
    ],
    examples=2,
    wrong_solutions=[
        r'''def can(roles, user_roles, permission):
    for role in user_roles:
        for grant in roles.get(role, {}).get("permissions", []):
            if grant == permission or grant == "*" or grant == permission.split(":")[0] + ":*":
                return True
    return False
''',
        r'''def can(roles, user_roles, permission):
    resource = permission.split(":")[0]
    seen, stack = set(), list(user_roles)
    while stack:
        role = stack.pop()
        if role in seen or role not in roles:
            continue
        seen.add(role)
        for grant in roles[role].get("permissions", []):
            if grant == "*" or grant.split(":")[0] == resource:
                return True
        stack.extend(roles[role].get("inherits", []))
    return False
''',
        r'''def can(roles, user_roles, permission):
    seen, stack = set(), list(user_roles)
    while stack:
        role = stack.pop()
        if role in seen or role not in roles:
            continue
        seen.add(role)
        for grant in roles[role].get("permissions", []):
            if grant == "*" or permission.startswith(grant.rstrip("*")):
                return True
        stack.extend(roles[role].get("inherits", []))
    return False
''',
    ],
    guide=dict(
        prereqs="The broken access control lesson (deny by default, central policy decisions). Graph traversal with a visited set.",
        intuition="Roles form a graph; a user's effective grants are everything reachable from their roles. Walk the "
                  "graph once, and return `True` the moment any reachable grant matches. If the walk finishes without a "
                  "match the answer is `False` — nothing is allowed by accident.",
        hints=[
            "Use a stack (or queue) seeded with the user's roles and a `seen` set to survive cycles.",
            "Extract the resource part once: `permission.split(':', 1)[0]`.",
            "Match with three exact string comparisons; avoid `startswith`.",
        ],
        brute_force="First flatten every role into its full permission set, then check membership. Simple and fine "
                    "for small systems, but it expands roles the user does not even have.",
        approach="Depth-first traversal from the user's roles, skipping unknown or already visited names, testing each "
                 "grant, pushing inherited roles.\n\n"
                 "Dry run `can(roles, ['manager'], 'orders:read')`: pop `manager` (no grants), push `support`, `catalog`. "
                 "Pop `catalog`: `products:*` does not match resource `orders`. Pop `support`: `orders:refund` ≠ `orders:read`; "
                 "push `viewer`. Pop `viewer`: `orders:read` matches → `True`.",
        complexity="Time O(R + G) for R reachable roles and G grants among them; space O(R).",
        pitfalls="- Without the `seen` set, a cycle (`a → b → a`) loops forever.\n"
                 "- Prefix matching makes `order:*` cover `orders:…` and `orders:read` cover `orders:readall`.\n"
                 "- An unknown role must grant nothing rather than raise — otherwise a typo in configuration becomes an outage, or worse, an allow.\n"
                 "- RBAC answers 'may this *kind* of user do this *kind* of thing'; it does not answer 'to **this** record' — that is the object-level check.",
        follow_up="Add explicit deny rules that override allows, or move to attribute-based policies evaluated by a policy engine (OPA, Cedar).",
    ),
),
dict(
    id="sec-object-authz",
    title="Object-Level Authorisation (IDOR Prevention)",
    difficulty="Medium",
    pattern="Access Control",
    kind="function",
    entry="canAccess",
    description=r"""
An endpoint such as `GET /documents/{id}` must check not only that the caller is logged in, but that
the caller may touch **that particular** document. Skipping this check is the classic insecure direct
object reference (IDOR / broken object-level authorisation).

Write `canAccess(user, resource, action)` returning a bool.

- `user`: `{"id": ..., "tenant": ..., "role": "member" | "admin", "active": bool}` (`active` defaults to `True` if absent).
- `resource`: `{"owner_id": ..., "tenant": ..., "visibility": "private" | "tenant"}`.
- `action`: a string.

Evaluate in this order; the first rule that applies decides:

1. `action` is not one of `"read"`, `"update"`, `"delete"` → `False`.
2. The user is not active → `False`.
3. The user's tenant differs from the resource's tenant → `False` — **even for admins**. Tenant isolation is absolute.
4. The user's role is `"admin"` → `True`.
5. The user's id equals the resource's `owner_id` → `True`.
6. `action` is `"read"` and the resource's visibility is `"tenant"` → `True`.
7. Otherwise → `False`.

**Example:** member 7 of tenant `t1` reading a `private` document owned by user 8 of `t1` → `False`.
The same document with visibility `tenant` → `True` for `read`, `False` for `update`.
""",
    starter='''def canAccess(user: dict, resource: dict, action: str) -> bool:
    pass
''',
    solution=r'''def canAccess(user, resource, action):
    if action not in ("read", "update", "delete"):
        return False
    if not user.get("active", True):
        return False
    if user.get("tenant") != resource.get("tenant"):
        return False
    if user.get("role") == "admin":
        return True
    if user.get("id") == resource.get("owner_id"):
        return True
    if action == "read" and resource.get("visibility") == "tenant":
        return True
    return False
''',
    tests=[
        [{"id": 7, "tenant": "t1", "role": "member"}, {"owner_id": 8, "tenant": "t1", "visibility": "private"}, "read"],
        [{"id": 7, "tenant": "t1", "role": "member"}, {"owner_id": 8, "tenant": "t1", "visibility": "tenant"}, "read"],
        [{"id": 7, "tenant": "t1", "role": "member"}, {"owner_id": 8, "tenant": "t1", "visibility": "tenant"}, "update"],
        [{"id": 7, "tenant": "t1", "role": "member"}, {"owner_id": 7, "tenant": "t1", "visibility": "private"}, "delete"],
        [{"id": 1, "tenant": "t1", "role": "admin"}, {"owner_id": 8, "tenant": "t1", "visibility": "private"}, "delete"],
        [{"id": 1, "tenant": "t1", "role": "admin"}, {"owner_id": 8, "tenant": "t2", "visibility": "tenant"}, "read"],
        [{"id": 7, "tenant": "t1", "role": "member"}, {"owner_id": 7, "tenant": "t2", "visibility": "private"}, "read"],
        [{"id": 7, "tenant": "t1", "role": "member", "active": False}, {"owner_id": 7, "tenant": "t1", "visibility": "private"}, "read"],
        [{"id": 1, "tenant": "t1", "role": "admin", "active": False}, {"owner_id": 8, "tenant": "t1", "visibility": "tenant"}, "read"],
        [{"id": 1, "tenant": "t1", "role": "admin"}, {"owner_id": 8, "tenant": "t1", "visibility": "private"}, "export"],
        [{"id": 7, "tenant": "t1", "role": "member"}, {"owner_id": 7, "tenant": "t1", "visibility": "private"}, "READ"],
        [{"id": 7, "tenant": "t1", "role": "member", "active": True}, {"owner_id": 8, "tenant": "t1", "visibility": "tenant"}, "delete"],
        [{"id": "7", "tenant": "t1", "role": "member"}, {"owner_id": 7, "tenant": "t1", "visibility": "private"}, "read"],
        [{"id": 7, "tenant": "t1", "role": "guest"}, {"owner_id": 9, "tenant": "t1", "visibility": "tenant"}, "read"],
    ],
    examples=3,
    wrong_solutions=[
        r'''def canAccess(user, resource, action):
    if action not in ("read", "update", "delete"):
        return False
    if not user.get("active", True):
        return False
    if user.get("role") == "admin":
        return True
    if user.get("tenant") != resource.get("tenant"):
        return False
    if user.get("id") == resource.get("owner_id"):
        return True
    return action == "read" and resource.get("visibility") == "tenant"
''',
        r'''def canAccess(user, resource, action):
    if action not in ("read", "update", "delete"):
        return False
    if user.get("tenant") != resource.get("tenant"):
        return False
    if user.get("role") == "admin" or user.get("id") == resource.get("owner_id"):
        return True
    return resource.get("visibility") == "tenant"
''',
        r'''def canAccess(user, resource, action):
    return user.get("active", True) and action in ("read", "update", "delete")
''',
    ],
    guide=dict(
        prereqs="The broken access control and IDOR lesson. Rule ordering and early returns.",
        intuition="Authorisation is a function of *who*, *what* and *which object*. Identifiers in a URL are merely "
                  "requests; the server loads the object and re-derives the answer from its stored owner and tenant every time.",
        hints=[
            "Translate the seven rules into seven early returns, in order.",
            "Put the tenant comparison **before** the admin shortcut.",
            "Compare ids with `==` exactly as given — the string `'7'` is not the integer `7`.",
        ],
        brute_force="Check only that a user is authenticated (the third wrong solution). Every logged-in user can then "
                    "walk the id space and read everyone's documents.",
        approach="A guard-clause ladder.\n\n"
                 "Dry run: admin of `t1` reads a `tenant`-visible document of `t2`. Action valid; user active; tenants "
                 "differ → `False` at rule 3. The admin rule is never reached.",
        complexity="O(1) time and space.",
        pitfalls="- Letting 'admin' short-circuit before the tenant check turns one customer's administrator into everyone's.\n"
                 "- Forgetting the action dimension makes read-shared documents editable.\n"
                 "- Deactivated accounts with live sessions must still be refused.\n"
                 "- In real code the stronger pattern is to *scope the query* (`WHERE id = ? AND tenant_id = ?`) so that "
                 "a missing check returns 'not found' instead of someone else's data.",
        follow_up="Return 404 rather than 403 for objects the caller may not know exist, and write a test for every "
                  "endpoint that requests another user's object id and expects refusal.",
    ),
),
dict(
    id="sec-login-limiter",
    title="Login Rate Limiter with Lockout",
    difficulty="Medium",
    pattern="Rate Limiting",
    kind="class",
    entry="LoginLimiter",
    description=r"""
Throttle password guessing per account. Timestamps are passed in explicitly (seconds, non-decreasing
across calls), so there is no hidden clock.

`LoginLimiter(max_failures, window, lockout)`

`attempt(username, now, success)` records one login attempt and returns a string:

1. Normalise the user name: strip surrounding whitespace and lower-case it, so `" Ann "` and `"ann"`
   are the same account.
2. If the account is locked — `now < locked_until` — return `"locked"`. The attempt is **not** evaluated
   or counted, even if `success` is `True`.
3. If `success` is `True`: forget all recorded failures for the account and return `"ok"`.
4. Otherwise it is a failure: record `now`; discard recorded failures with timestamp `<= now - window`
   (only failures strictly newer than `now - window` count). If the number of remaining failures is
   `>= max_failures`, set `locked_until = now + lockout` and clear the recorded failures. Return `"fail"`
   in either case (the caller shows the same generic error).

**Example:** `LoginLimiter(3, 60, 300)`: failures at t = 0, 10, 20 → `"fail"`, `"fail"`, `"fail"` (now locked until 320);
a correct password at t = 30 → `"locked"`; at t = 320 → `"ok"`.
""",
    starter='''class LoginLimiter:
    def __init__(self, max_failures: int, window: int, lockout: int):
        pass

    def attempt(self, username: str, now: int, success: bool) -> str:
        pass
''',
    solution=r'''class LoginLimiter:
    def __init__(self, max_failures, window, lockout):
        self.max_failures = max_failures
        self.window = window
        self.lockout = lockout
        self.failures = {}
        self.locked_until = {}

    def attempt(self, username, now, success):
        user = username.strip().lower()
        if now < self.locked_until.get(user, float("-inf")):
            return "locked"
        if success:
            self.failures.pop(user, None)
            return "ok"
        recent = [t for t in self.failures.get(user, []) if t > now - self.window]
        recent.append(now)
        if len(recent) >= self.max_failures:
            self.locked_until[user] = now + self.lockout
            recent = []
        self.failures[user] = recent
        return "fail"
''',
    tests=[
        [["LoginLimiter", "attempt", "attempt", "attempt", "attempt", "attempt"],
         [[3, 60, 300], ["ann", 0, False], ["ann", 10, False], ["ann", 20, False], ["ann", 30, True], ["ann", 320, True]]],
        [["LoginLimiter", "attempt", "attempt", "attempt", "attempt"],
         [[3, 60, 300], ["ann", 0, False], ["ann", 10, False], ["ann", 15, True], ["ann", 20, False]]],
        [["LoginLimiter", "attempt", "attempt", "attempt", "attempt", "attempt"],
         [[3, 60, 300], ["ann", 0, False], ["ann", 10, False], ["ann", 15, True], ["ann", 20, False], ["ann", 25, False]]],
        [["LoginLimiter", "attempt", "attempt", "attempt", "attempt"],
         [[3, 60, 300], ["ann", 0, False], ["ann", 30, False], ["ann", 60, False], ["ann", 61, True]]],
        [["LoginLimiter", "attempt", "attempt", "attempt", "attempt"],
         [[3, 60, 300], ["ann", 0, False], ["ann", 30, False], ["ann", 59, False], ["ann", 61, True]]],
        [["LoginLimiter", "attempt", "attempt", "attempt", "attempt"],
         [[2, 60, 100], ["Ann", 0, False], [" ann ", 1, False], ["ANN", 2, True], ["bob", 2, True]]],
        [["LoginLimiter", "attempt", "attempt", "attempt", "attempt", "attempt"],
         [[2, 60, 100], ["ann", 0, False], ["bob", 1, False], ["ann", 2, False], ["bob", 3, True], ["ann", 3, True]]],
        [["LoginLimiter", "attempt", "attempt", "attempt", "attempt", "attempt", "attempt"],
         [[2, 10, 50], ["ann", 0, False], ["ann", 5, False], ["ann", 54, False], ["ann", 55, False], ["ann", 56, False], ["ann", 60, True]]],
        [["LoginLimiter", "attempt", "attempt"], [[1, 10, 5], ["ann", 0, False], ["ann", 4, True]]],
        [["LoginLimiter", "attempt", "attempt"], [[1, 10, 5], ["ann", 0, False], ["ann", 5, True]]],
        [["LoginLimiter", "attempt", "attempt", "attempt"], [[3, 60, 300], ["ann", 100, True], ["ann", 101, True], ["zed", 101, False]]],
        [["LoginLimiter", "attempt", "attempt", "attempt", "attempt", "attempt", "attempt", "attempt"],
         [[3, 60, 30], ["a", 0, False], ["a", 1, False], ["a", 2, False], ["a", 32, False], ["a", 33, False], ["a", 34, False], ["a", 35, True]]],
    ],
    examples=1,
    wrong_solutions=[
        r'''class LoginLimiter:
    def __init__(self, max_failures, window, lockout):
        self.max_failures, self.window, self.lockout = max_failures, window, lockout
        self.count = {}
        self.locked_until = {}

    def attempt(self, username, now, success):
        user = username.strip().lower()
        if now < self.locked_until.get(user, -1):
            return "locked"
        if success:
            return "ok"
        self.count[user] = self.count.get(user, 0) + 1
        if self.count[user] >= self.max_failures:
            self.locked_until[user] = now + self.lockout
            self.count[user] = 0
        return "fail"
''',
        r'''class LoginLimiter:
    def __init__(self, max_failures, window, lockout):
        self.max_failures, self.window, self.lockout = max_failures, window, lockout
        self.failures = {}
        self.locked_until = {}

    def attempt(self, username, now, success):
        user = username
        if now < self.locked_until.get(user, -1):
            return "locked"
        if success:
            self.failures.pop(user, None)
            return "ok"
        recent = [t for t in self.failures.get(user, []) if t > now - self.window] + [now]
        if len(recent) >= self.max_failures:
            self.locked_until[user] = now + self.lockout
            recent = []
        self.failures[user] = recent
        return "fail"
''',
        r'''class LoginLimiter:
    def __init__(self, max_failures, window, lockout):
        self.max_failures, self.window, self.lockout = max_failures, window, lockout
        self.failures = {}
        self.locked_until = {}

    def attempt(self, username, now, success):
        user = username.strip().lower()
        if success:
            self.failures.pop(user, None)
            self.locked_until.pop(user, None)
            return "ok"
        if now < self.locked_until.get(user, -1):
            return "locked"
        recent = [t for t in self.failures.get(user, []) if t > now - self.window] + [now]
        if len(recent) >= self.max_failures:
            self.locked_until[user] = now + self.lockout
            recent = []
        self.failures[user] = recent
        return "fail"
''',
    ],
    guide=dict(
        prereqs="The denial of service and rate limiting lesson (sliding windows, lockout trade-offs). Dicts of lists.",
        intuition="Online guessing is only feasible if the attacker gets many tries. Remember recent failures per "
                  "account, and once there are too many inside a sliding window, refuse *everything* for a while — "
                  "including the right password, otherwise the lock is merely a delay between guesses.",
        hints=[
            "Keep two dicts keyed by the normalised name: a list of recent failure times and a `locked_until` time.",
            "Check the lock before looking at `success`.",
            "On failure: prune with `t > now - window`, append, then compare the count with `max_failures`.",
        ],
        brute_force="A single counter per account that never expires (first wrong solution). A user who mistypes "
                    "once a week is eventually locked out, and a success never clears the slate.",
        approach="1. Normalise. 2. Locked? → `locked`. 3. Success → clear failures, `ok`. 4. Failure → prune, append, maybe lock, `fail`.\n\n"
                 "Dry run `LoginLimiter(3, 60, 300)`: failure at 0 → `[0]`; at 30 → `[0, 30]`; at 60 → prune `t > 0` "
                 "removes the entry at 0, leaving `[30, 60]` — only two, so no lock. A success at 61 returns `ok`. "
                 "Had the third failure come at 59, `[0, 30, 59]` would trigger the lock until 359.",
        complexity="Each call is O(max_failures) time because the per-account list never grows beyond that; space O(accounts × max_failures).",
        pitfalls="- Evaluating success while locked lets an attacker keep guessing through the lock.\n"
                 "- Not normalising user names gives the attacker a fresh budget for every capitalisation.\n"
                 "- The boundary: a failure exactly `window` seconds old no longer counts; the lock ends exactly at `locked_until`.\n"
                 "- Hard lockouts enable denial of service against known user names. Real systems combine per-account "
                 "throttling with per-IP limits, progressive delays, CAPTCHA and MFA.",
        follow_up="Implement an exponential back-off variant (delay doubles with each failure) and a second limiter keyed by source address to slow password spraying.",
    ),
),
dict(
    id="sec-session-check",
    title="Session Validity: Idle and Absolute Timeouts",
    difficulty="Easy",
    pattern="Session Hardening",
    kind="function",
    entry="checkSession",
    description=r"""
A server-side session record must be re-validated on every request. Write
`checkSession(session, now, idle_timeout, absolute_timeout)` returning one status string.

`session` is `None` (unknown session id) or a dict with integer timestamps `"created"` and `"last_seen"`
and an optional bool `"revoked"`.

Return the first status that applies:

1. `"invalid"` — `session` is `None`; or a timestamp key is missing; or `created > now`; or
   `last_seen > now`; or `last_seen < created` (a record that cannot be genuine).
2. `"revoked"` — `revoked` is true (the user logged out or an administrator ended the session).
3. `"absolute-expired"` — `now - created >= absolute_timeout` (maximum lifetime regardless of activity).
4. `"idle-expired"` — `now - last_seen >= idle_timeout`.
5. `"ok"`.

**Example:** `checkSession({"created": 0, "last_seen": 500}, 1000, 900, 86400)` → `"ok"`

**Example:** `checkSession({"created": 0, "last_seen": 50}, 1000, 900, 86400)` → `"idle-expired"`
""",
    starter='''def checkSession(session, now: int, idle_timeout: int, absolute_timeout: int) -> str:
    pass
''',
    solution=r'''def checkSession(session, now, idle_timeout, absolute_timeout):
    if session is None or "created" not in session or "last_seen" not in session:
        return "invalid"
    created = session["created"]
    last_seen = session["last_seen"]
    if created > now or last_seen > now or last_seen < created:
        return "invalid"
    if session.get("revoked", False):
        return "revoked"
    if now - created >= absolute_timeout:
        return "absolute-expired"
    if now - last_seen >= idle_timeout:
        return "idle-expired"
    return "ok"
''',
    tests=[
        [{"created": 0, "last_seen": 500}, 1000, 900, 86400],
        [{"created": 0, "last_seen": 50}, 1000, 900, 86400],
        [None, 1000, 900, 86400],
        [{"created": 0, "last_seen": 86399, "revoked": True}, 86399, 900, 86400],
        [{"created": 0, "last_seen": 86399}, 86400, 900, 86400],
        [{"created": 0, "last_seen": 86000}, 86399, 900, 86400],
        [{"created": 100, "last_seen": 100}, 1000, 900, 86400],
        [{"created": 100, "last_seen": 101}, 1000, 900, 86400],
        [{"created": 2000, "last_seen": 2000}, 1000, 900, 86400],
        [{"created": 500, "last_seen": 400}, 1000, 900, 86400],
        [{"created": 0}, 1000, 900, 86400],
        [{"created": 0, "last_seen": 10, "revoked": False}, 100000, 900, 86400],
        [{"created": 0, "last_seen": 1001}, 1000, 900, 86400],
        [{"created": 5, "last_seen": 5, "revoked": True}, 1, 900, 86400],
    ],
    examples=2,
    wrong_solutions=[
        r'''def checkSession(session, now, idle_timeout, absolute_timeout):
    if session is None:
        return "invalid"
    if session.get("revoked"):
        return "revoked"
    if now - session["last_seen"] > idle_timeout:
        return "idle-expired"
    return "ok"
''',
        r'''def checkSession(session, now, idle_timeout, absolute_timeout):
    if session is None or "created" not in session or "last_seen" not in session:
        return "invalid"
    if session["created"] > now or session["last_seen"] > now or session["last_seen"] < session["created"]:
        return "invalid"
    if now - session["last_seen"] >= idle_timeout:
        return "idle-expired"
    if now - session["created"] >= absolute_timeout:
        return "absolute-expired"
    if session.get("revoked", False):
        return "revoked"
    return "ok"
''',
    ],
    guide=dict(
        prereqs="The session management lesson (server-side sessions, idle versus absolute expiry, revocation).",
        intuition="A session id is a temporary password. It should die when the user stops using it (idle timeout), "
                  "when it has simply lived too long (absolute timeout), or when someone ends it deliberately (revocation) — "
                  "and a record that does not make sense should be treated as no record at all.",
        hints=[
            "Guard clauses in the listed order.",
            "Both timeouts use `>=`: a session exactly at its limit is expired.",
            "Sanity-check the timestamps before trusting any of them.",
        ],
        brute_force="Only checking that the session id exists in the store. Stolen ids then work for as long as the row survives.",
        approach="Five ordered checks.\n\n"
                 "Dry run `({'created': 0, 'last_seen': 86399}, 86400, 900, 86400)`: record is sane; not revoked; "
                 "`86400 - 0 >= 86400` → `absolute-expired`, even though the user was active one second ago.",
        complexity="O(1) time and space.",
        pitfalls="- Enforcing expiry only through the cookie's `Max-Age` leaves the server accepting old ids forever.\n"
                 "- A sliding idle timeout without an absolute cap lets an attacker keep a stolen session alive indefinitely.\n"
                 "- Report order matters for auditing: a revoked session should say so even if it has also expired.",
        follow_up="On `ok`, update `last_seen`; on login and on privilege change, issue a brand-new session id to prevent fixation.",
    ),
),
]
