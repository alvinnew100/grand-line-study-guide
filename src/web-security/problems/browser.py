import hashlib as _hl
import hmac as _hm


def _csrf(secret, session_id, ts):
    sig = _hm.new(secret.encode(), f"{session_id}|{ts}".encode(), _hl.sha256).hexdigest()
    return f"{ts}.{sig}"


_GOOD = _csrf("k1", "sess-A", 1000)
_OTHER_SESSION = _csrf("k1", "sess-B", 1000)
_OTHER_SECRET = _csrf("wrong", "sess-A", 1000)
_FUTURE = _csrf("k1", "sess-A", 5000)
_TS_SWAPPED = "1500." + _GOOD.split(".")[1]

PROBLEMS = [
dict(
    id="sec-cookie-audit",
    title="Cookie Attribute Audit",
    difficulty="Easy",
    pattern="Session Hardening",
    kind="function",
    entry="auditCookie",
    description=r"""
A session cookie is only as safe as the attributes it was set with. Write `auditCookie(header)` that
receives the **value** of one `Set-Cookie` header (for example
`sid=abc123; Path=/; HttpOnly; Secure; SameSite=Lax`) and returns a list of findings.

Parsing: split on `;`. The first piece is `name=value`. Every later piece is an attribute, either a bare
flag (`HttpOnly`) or `Key=Value`. Trim surrounding spaces. Attribute **names** and the `SameSite`
**value** are case-insensitive. Ignore empty pieces.

Report, in exactly this order, each finding that applies:

1. `"missing-httponly"` — no `HttpOnly` attribute.
2. `"missing-secure"` — no `Secure` attribute.
3. `"missing-samesite"` — no `SameSite` attribute, or its value is not `Strict`, `Lax` or `None`.
4. `"samesite-none-without-secure"` — `SameSite=None` but no `Secure` (browsers reject such cookies).
5. `"host-prefix-violation"` — the cookie **name** starts with `__Host-` but the cookie lacks `Secure`,
   or has a `Domain` attribute, or its `Path` is not exactly `/`.

Only attributes count: a cookie *value* that happens to contain the word `secure` proves nothing.

**Example:** `auditCookie("sid=abc; Path=/; HttpOnly; Secure; SameSite=Lax")` → `[]`

**Example:** `auditCookie("sid=abc; Path=/")` → `["missing-httponly", "missing-secure", "missing-samesite"]`
""",
    starter='''def auditCookie(header: str) -> list:
    pass
''',
    solution=r'''def auditCookie(header):
    pieces = [p.strip() for p in header.split(";")]
    name = pieces[0].split("=", 1)[0].strip()
    attrs = {}
    for piece in pieces[1:]:
        if not piece:
            continue
        key, _, value = piece.partition("=")
        attrs[key.strip().lower()] = value.strip()
    findings = []
    if "httponly" not in attrs:
        findings.append("missing-httponly")
    secure = "secure" in attrs
    if not secure:
        findings.append("missing-secure")
    same_site = attrs.get("samesite", "").lower()
    if same_site not in ("strict", "lax", "none"):
        findings.append("missing-samesite")
    elif same_site == "none" and not secure:
        findings.append("samesite-none-without-secure")
    if name.startswith("__Host-"):
        if not secure or "domain" in attrs or attrs.get("path") != "/":
            findings.append("host-prefix-violation")
    return findings
''',
    tests=[
        ["sid=abc; Path=/; HttpOnly; Secure; SameSite=Lax"],
        ["sid=abc; Path=/"],
        ["sid=abc; httponly; SECURE; samesite=strict"],
        ["theme=secure-dark; HttpOnly; SameSite=Lax"],
        ["sid=abc; HttpOnly; SameSite=None"],
        ["sid=abc; HttpOnly; Secure; SameSite=None"],
        ["__Host-sid=abc; Path=/; HttpOnly; Secure; SameSite=Strict"],
        ["__Host-sid=abc; Path=/app; HttpOnly; Secure; SameSite=Strict"],
        ["__Host-sid=abc; Path=/; Domain=shop.example; HttpOnly; Secure; SameSite=Strict"],
        ["__Host-sid=abc; HttpOnly; SameSite=Lax"],
        ["sid=abc; HttpOnly; Secure; SameSite=Sometimes"],
        ["sid=a=b=c;HttpOnly;Secure;SameSite=Lax;"],
        ["note=HttpOnly; Max-Age=3600; Secure"],
        ["sid=abc ;  Secure ; HttpOnly ;  SameSite = Lax "],
    ],
    examples=2,
    wrong_solutions=[
        r'''def auditCookie(header):
    findings = []
    if "HttpOnly" not in header:
        findings.append("missing-httponly")
    if "Secure" not in header:
        findings.append("missing-secure")
    if "SameSite" not in header:
        findings.append("missing-samesite")
    return findings
''',
        r'''def auditCookie(header):
    low = header.lower()
    findings = []
    if "httponly" not in low:
        findings.append("missing-httponly")
    if "secure" not in low:
        findings.append("missing-secure")
    if "samesite=strict" not in low and "samesite=lax" not in low and "samesite=none" not in low:
        findings.append("missing-samesite")
    elif "samesite=none" in low and "secure" not in low:
        findings.append("samesite-none-without-secure")
    return findings
''',
    ],
    guide=dict(
        prereqs="The session management lesson (what `HttpOnly`, `Secure`, `SameSite` and the `__Host-` prefix do). `str.split`, `str.partition`.",
        intuition="Treat the header as structured data, not as a blob to search. Once it is parsed into a name plus a "
                  "dict of lower-cased attributes, each finding is a one-line membership test.",
        hints=[
            "Split on `;`, strip each piece, and keep the first piece apart: it is the cookie itself, not an attribute.",
            "`piece.partition('=')` handles both `HttpOnly` (no `=`) and `SameSite=Lax`.",
            "Decide `secure` once and reuse it for findings 2, 4 and 5.",
        ],
        brute_force="Search the raw header for the words `HttpOnly`, `Secure` and `SameSite`. It breaks on different "
                    "capitalisation and is fooled when the cookie value itself contains one of those words.",
        approach="1. Parse into `name` and `attrs` (keys lower-cased).\n"
                 "2. Append findings in the required order.\n"
                 "3. For `__Host-` names require `Secure`, no `Domain`, and `Path=/`.\n\n"
                 "Dry run `theme=secure-dark; HttpOnly; SameSite=Lax`: name `theme`; attrs `{httponly: '', samesite: 'Lax'}`. "
                 "HttpOnly present; `secure` is **not** an attribute → `missing-secure`; SameSite is `lax` → fine. Result "
                 "`['missing-secure']`.",
        complexity="Time O(n) in the header length; space O(n) for the parsed attributes.",
        pitfalls="- Attribute names are case-insensitive; browsers accept `httponly`.\n"
                 "- The value may itself contain `=`; split the first piece only once.\n"
                 "- An unrecognised `SameSite` value is treated by browsers like a missing one (defaulting to `Lax` in most), so report it.\n"
                 "- `__Host-` cookies are refused by the browser unless all three conditions hold — a silent logout bug if you get it wrong.",
        follow_up="Extend the audit with `Max-Age`/`Expires` limits for session cookies and the `__Secure-` prefix rule (requires `Secure`).",
    ),
),
dict(
    id="sec-csp-audit",
    title="Content-Security-Policy Audit",
    difficulty="Medium",
    pattern="Browser Defences",
    kind="function",
    entry="auditCsp",
    description=r"""
A Content Security Policy only helps against script injection when it is strict. Write `auditCsp(header)`
that parses the value of a `Content-Security-Policy` header and returns a **sorted** list of weaknesses.

Parsing: directives are separated by `;`. Within a directive, tokens are separated by whitespace; the
first token is the directive name (case-insensitive), the rest are its sources (compare them lower-cased).
Ignore empty directives. If a directive name appears twice, **only the first occurrence counts** (that is
what browsers do).

Let *effective script sources* be the sources of `script-src` if that directive exists, otherwise those
of `default-src`, otherwise "none defined". Let *effective object sources* be `object-src`, falling back
to `default-src` in the same way.

Findings:

- `"no-script-restriction"` — neither `script-src` nor `default-src` exists.
- `"unsafe-inline-script"` — effective script sources contain `'unsafe-inline'` and contain **no**
  source starting with `'nonce-`, `'sha256-`, `'sha384-` or `'sha512-` (when a nonce or hash is present,
  modern browsers ignore `'unsafe-inline'`).
- `"unsafe-eval"` — effective script sources contain `'unsafe-eval'`.
- `"wildcard-script"` — effective script sources contain `*`, `http:`, `https:` or `data:`.
- `"object-src-not-none"` — effective object sources are undefined or are anything other than exactly `'none'`.
- `"missing-base-uri"` — there is no `base-uri` directive (it does not fall back to `default-src`).
- `"missing-frame-ancestors"` — there is no `frame-ancestors` directive (no fallback either).

**Example:** `auditCsp("default-src 'self'; script-src 'self' 'unsafe-inline'")` →
`["missing-base-uri", "missing-frame-ancestors", "object-src-not-none", "unsafe-inline-script"]`
""",
    starter='''def auditCsp(header: str) -> list:
    pass
''',
    solution=r'''def auditCsp(header):
    directives = {}
    for chunk in header.split(";"):
        tokens = chunk.split()
        if not tokens:
            continue
        name = tokens[0].lower()
        if name not in directives:
            directives[name] = [t.lower() for t in tokens[1:]]
    findings = []
    script = directives.get("script-src", directives.get("default-src"))
    if script is None:
        findings.append("no-script-restriction")
    else:
        strict = any(s.startswith(("'nonce-", "'sha256-", "'sha384-", "'sha512-")) for s in script)
        if "'unsafe-inline'" in script and not strict:
            findings.append("unsafe-inline-script")
        if "'unsafe-eval'" in script:
            findings.append("unsafe-eval")
        if any(s in ("*", "http:", "https:", "data:") for s in script):
            findings.append("wildcard-script")
    obj = directives.get("object-src", directives.get("default-src"))
    if obj != ["'none'"]:
        findings.append("object-src-not-none")
    if "base-uri" not in directives:
        findings.append("missing-base-uri")
    if "frame-ancestors" not in directives:
        findings.append("missing-frame-ancestors")
    return sorted(findings)
''',
    tests=[
        ["default-src 'self'; script-src 'self' 'unsafe-inline'"],
        ["default-src 'none'; script-src 'self'; base-uri 'none'; frame-ancestors 'none'"],
        ["script-src 'nonce-r4nd0m' 'unsafe-inline' 'strict-dynamic'; object-src 'none'; base-uri 'self'; frame-ancestors 'self'"],
        [""],
        ["img-src *"],
        ["default-src *"],
        ["default-src 'self' 'unsafe-eval'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'"],
        ["DEFAULT-SRC 'NONE'; Script-Src 'Self' HTTPS:; BASE-URI 'self'; Frame-Ancestors 'none'"],
        ["script-src 'self'; script-src * 'unsafe-inline'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'"],
        ["default-src 'self';;  ; object-src 'self'; base-uri 'self'"],
        ["script-src 'sha256-abc=' 'unsafe-inline' data:; default-src 'none'; frame-ancestors 'none'"],
        ["default-src 'none'; script-src https://cdn.shop.example; base-uri 'none'; frame-ancestors 'none'"],
        ["object-src 'none'; base-uri 'none'; frame-ancestors 'none'"],
        ["default-src 'none' ; script-src 'self' 'unsafe-inline' 'unsafe-eval' * ; frame-ancestors *"],
    ],
    examples=1,
    wrong_solutions=[
        r'''def auditCsp(header):
    low = header.lower()
    findings = []
    if "script-src" not in low and "default-src" not in low:
        findings.append("no-script-restriction")
    if "'unsafe-inline'" in low:
        findings.append("unsafe-inline-script")
    if "'unsafe-eval'" in low:
        findings.append("unsafe-eval")
    if "*" in low:
        findings.append("wildcard-script")
    if "object-src 'none'" not in low:
        findings.append("object-src-not-none")
    if "base-uri" not in low:
        findings.append("missing-base-uri")
    if "frame-ancestors" not in low:
        findings.append("missing-frame-ancestors")
    return sorted(findings)
''',
        r'''def auditCsp(header):
    directives = {}
    for chunk in header.split(";"):
        tokens = chunk.split()
        if tokens:
            directives[tokens[0].lower()] = [t.lower() for t in tokens[1:]]
    findings = []
    script = directives.get("script-src")
    if script is None:
        findings.append("no-script-restriction")
    else:
        if "'unsafe-inline'" in script:
            findings.append("unsafe-inline-script")
        if "'unsafe-eval'" in script:
            findings.append("unsafe-eval")
        if any(s in ("*", "http:", "https:", "data:") for s in script):
            findings.append("wildcard-script")
    if directives.get("object-src") != ["'none'"]:
        findings.append("object-src-not-none")
    if "base-uri" not in directives:
        findings.append("missing-base-uri")
    if "frame-ancestors" not in directives:
        findings.append("missing-frame-ancestors")
    return sorted(findings)
''',
    ],
    guide=dict(
        prereqs="The security headers and CSP lesson: fetch directives, the `default-src` fallback, nonces and hashes.",
        intuition="A CSP is a small configuration language. Parse it into `directive → sources`, apply the same fallback "
                  "rule the browser applies, and then each weakness is a simple predicate over one list.",
        hints=[
            "`chunk.split()` with no argument both splits on any whitespace and discards empty tokens.",
            "Use `directives.get('script-src', directives.get('default-src'))` to model the fallback; `None` means nothing restricts scripts.",
            "`base-uri` and `frame-ancestors` are not fetch directives: they never inherit from `default-src`.",
        ],
        brute_force="Substring searches over the whole header. They cannot tell `img-src *` (harmless for scripts) from "
                    "`script-src *`, ignore the fallback rule, and mis-handle duplicate directives.",
        approach="1. Build the dict, first occurrence wins.\n"
                 "2. Resolve effective script sources and test the four script predicates.\n"
                 "3. Resolve effective object sources and require exactly `['none']` (with quotes).\n"
                 "4. Check presence of `base-uri` and `frame-ancestors`. Sort.\n\n"
                 "Dry run `default-src 'self'; script-src 'self' 'unsafe-inline'`: script sources `['self', 'unsafe-inline']`, "
                 "no nonce/hash → `unsafe-inline-script`; object sources fall back to `['self']` → `object-src-not-none`; "
                 "no `base-uri`, no `frame-ancestors` → two more findings.",
        complexity="Time O(n) in the header length; space O(n) for the parsed policy.",
        pitfalls="- Keywords are quoted (`'none'`, `'self'`); an unquoted `none` is a host name.\n"
                 "- A later duplicate directive is ignored by browsers — an easy way to believe a policy is stricter than it is.\n"
                 "- `'unsafe-inline'` next to a nonce is a deliberate backwards-compatibility pattern, not a hole.",
        follow_up="Real evaluators (Google's CSP Evaluator) also flag allow-listed hosts that serve JSONP or old "
                  "framework builds, and treat `'strict-dynamic'` as overriding host sources.",
    ),
),
dict(
    id="sec-cors-decision",
    title="CORS Decision for an Origin",
    difficulty="Medium",
    pattern="Browser Defences",
    kind="function",
    entry="corsHeaders",
    description=r"""
Your API must decide which CORS response headers to attach for a request carrying a given `Origin`
header. Write `corsHeaders(origin, policy)` returning a dict of headers (possibly empty).

`policy` has two keys: `"origins"` — a list of exact origins such as `"https://app.shop.example"`, which
may also contain the wildcard `"*"` — and `"allow_credentials"` — a bool.

Rules, in order:

1. If `origin` is `None` (not a cross-origin browser request) or the literal string `"null"`, return `{}`.
   `"null"` is sent by sandboxed frames and local files and must never be trusted, even if listed.
2. If `origin` **exactly equals** an entry of `policy["origins"]` (case-sensitive, no prefix or suffix
   matching), return `{"Access-Control-Allow-Origin": origin, "Vary": "Origin"}`, plus
   `"Access-Control-Allow-Credentials": "true"` when `allow_credentials` is true.
3. Otherwise, if `"*"` is in the list **and** `allow_credentials` is false, return
   `{"Access-Control-Allow-Origin": "*"}`.
4. Otherwise return `{}`. In particular a wildcard policy with credentials never reflects an unknown origin.

**Example:** `corsHeaders("https://app.shop.example", {"origins": ["https://app.shop.example"], "allow_credentials": True})`
→ `{"Access-Control-Allow-Origin": "https://app.shop.example", "Vary": "Origin", "Access-Control-Allow-Credentials": "true"}`

**Example:** `corsHeaders("https://evil.example", {"origins": ["*"], "allow_credentials": True})` → `{}`
""",
    starter='''def corsHeaders(origin, policy: dict) -> dict:
    pass
''',
    solution=r'''def corsHeaders(origin, policy):
    if origin is None or origin == "null":
        return {}
    allowed = policy.get("origins", [])
    credentials = bool(policy.get("allow_credentials", False))
    if origin != "*" and origin in allowed:
        headers = {"Access-Control-Allow-Origin": origin, "Vary": "Origin"}
        if credentials:
            headers["Access-Control-Allow-Credentials"] = "true"
        return headers
    if "*" in allowed and not credentials:
        return {"Access-Control-Allow-Origin": "*"}
    return {}
''',
    tests=[
        ["https://app.shop.example", {"origins": ["https://app.shop.example"], "allow_credentials": True}],
        ["https://evil.example", {"origins": ["*"], "allow_credentials": True}],
        ["https://evil.example", {"origins": ["*"], "allow_credentials": False}],
        [None, {"origins": ["*"], "allow_credentials": False}],
        ["null", {"origins": ["null", "*"], "allow_credentials": False}],
        ["https://app.shop.example.evil.example", {"origins": ["https://app.shop.example"], "allow_credentials": True}],
        ["https://evilapp.shop.example", {"origins": ["https://app.shop.example"], "allow_credentials": False}],
        ["http://app.shop.example", {"origins": ["https://app.shop.example"], "allow_credentials": False}],
        ["https://app.shop.example", {"origins": ["https://admin.shop.example", "https://app.shop.example"], "allow_credentials": False}],
        ["https://app.shop.example", {"origins": ["*", "https://app.shop.example"], "allow_credentials": True}],
        ["https://other.example", {"origins": ["*", "https://app.shop.example"], "allow_credentials": True}],
        ["https://APP.shop.example", {"origins": ["https://app.shop.example"], "allow_credentials": False}],
        ["https://app.shop.example", {"origins": [], "allow_credentials": True}],
        ["https://app.shop.example:8443", {"origins": ["https://app.shop.example"], "allow_credentials": False}],
    ],
    examples=2,
    wrong_solutions=[
        r'''def corsHeaders(origin, policy):
    if origin is None:
        return {}
    headers = {"Access-Control-Allow-Origin": origin, "Vary": "Origin"}
    if policy.get("allow_credentials"):
        headers["Access-Control-Allow-Credentials"] = "true"
    if origin in policy["origins"] or "*" in policy["origins"]:
        return headers
    return {}
''',
        r'''def corsHeaders(origin, policy):
    if origin is None or origin == "null":
        return {}
    creds = policy.get("allow_credentials", False)
    for allowed in policy.get("origins", []):
        if allowed != "*" and origin.startswith(allowed):
            headers = {"Access-Control-Allow-Origin": origin, "Vary": "Origin"}
            if creds:
                headers["Access-Control-Allow-Credentials"] = "true"
            return headers
    if "*" in policy.get("origins", []) and not creds:
        return {"Access-Control-Allow-Origin": "*"}
    return {}
''',
        r'''def corsHeaders(origin, policy):
    if origin is None or origin == "null":
        return {}
    creds = policy.get("allow_credentials", False)
    if origin in policy.get("origins", []):
        headers = {"Access-Control-Allow-Origin": origin}
        if creds:
            headers["Access-Control-Allow-Credentials"] = "true"
        return headers
    if "*" in policy.get("origins", []) and not creds:
        return {"Access-Control-Allow-Origin": "*"}
    return {}
''',
    ],
    guide=dict(
        prereqs="The security headers, CSP and CORS lesson: what an origin is, and that CORS *relaxes* the same-origin policy.",
        intuition="CORS headers are permission slips telling the browser that a foreign page may read this response. "
                  "Hand them out only to origins you named in advance, compare with exact equality, and never combine "
                  "'anyone' with 'and send the user's cookies'.",
        hints=[
            "Deal with the absent origin and `null` first.",
            "Exact membership (`origin in allowed`) is the whole matching rule — resist prefix, suffix or regex matching.",
            "When you echo a specific origin, add `Vary: Origin` so caches do not serve one origin's response to another.",
        ],
        brute_force="Echo back whatever `Origin` arrived whenever the configuration says `*`. With credentials enabled "
                    "that lets every website on the internet read each visitor's private API responses.",
        approach="1. `None` or `null` → `{}`.\n2. Exact match → echo origin, `Vary`, and credentials flag if configured.\n"
                 "3. Wildcard without credentials → `*`.\n4. Else `{}`.\n\n"
                 "Dry run origin `https://other.example`, policy `{origins: ['*', 'https://app.shop.example'], allow_credentials: True}`: "
                 "not `None`/`null`; no exact match; wildcard present but credentials are on → `{}`.",
        complexity="Time O(k) for k configured origins (O(1) with a set); space O(1).",
        pitfalls="- `startswith('https://app.shop.example')` also matches `https://app.shop.example.evil.example`.\n"
                 "- Origins include scheme and port: `http://…` and `…:8443` are different origins.\n"
                 "- Omitting `Vary: Origin` leads to cache poisoning between origins.\n"
                 "- `Access-Control-Allow-Origin: *` together with `Allow-Credentials: true` is rejected by browsers, which tempts "
                 "developers into reflecting the origin instead — the worst option.",
        follow_up="Handle preflight (`OPTIONS`) by also returning `Access-Control-Allow-Methods`, "
                  "`Access-Control-Allow-Headers` from allow-lists and a modest `Access-Control-Max-Age`.",
    ),
),
dict(
    id="sec-csrf-token",
    title="HMAC-Signed CSRF Tokens",
    difficulty="Medium",
    pattern="CSRF Defence",
    kind="class",
    entry="CsrfProtect",
    description=r"""
Implement stateless anti-CSRF tokens: the server can verify a token without storing it, because the
token is a timestamp signed together with the user's session identifier.

`CsrfProtect(secret, max_age)` — `secret` is a string key, `max_age` a number of seconds.

- `issue(session_id, now)` → the string `"<now>.<sig>"` where `now` is an integer timestamp and
  `sig` is the lower-case hex HMAC-SHA256 of the message `"<session_id>|<now>"` under `secret`
  (encode both key and message as UTF-8).
- `verify(session_id, token, now)` → `True` only if **all** hold:
  1. `token` is a string made of exactly two parts separated by one `.`;
  2. the first part consists only of ASCII digits (`0`–`9`), giving timestamp `ts`;
  3. `0 <= now - ts <= max_age` (not from the future, not expired);
  4. the second part equals the expected signature for `(session_id, ts)`, compared with
     `hmac.compare_digest`.

  Otherwise `False`. It must never raise.

**Example:** with `CsrfProtect("k1", 600)`: `t = issue("sess-A", 1000)`; `verify("sess-A", t, 1300)` → `True`;
`verify("sess-B", t, 1300)` → `False` (token bound to another session); `verify("sess-A", t, 1601)` → `False` (expired).
""",
    starter='''import hashlib
import hmac

class CsrfProtect:
    def __init__(self, secret: str, max_age: int):
        pass

    def issue(self, session_id: str, now: int) -> str:
        pass

    def verify(self, session_id: str, token, now: int) -> bool:
        pass
''',
    solution=r'''import hashlib
import hmac

class CsrfProtect:
    def __init__(self, secret, max_age):
        self.key = secret.encode("utf-8")
        self.max_age = max_age

    def _sign(self, session_id, ts):
        msg = (session_id + "|" + str(ts)).encode("utf-8")
        return hmac.new(self.key, msg, hashlib.sha256).hexdigest()

    def issue(self, session_id, now):
        return str(now) + "." + self._sign(session_id, now)

    def verify(self, session_id, token, now):
        if not isinstance(token, str):
            return False
        parts = token.split(".")
        if len(parts) != 2:
            return False
        ts_text, sig = parts
        if not ts_text or any(c not in "0123456789" for c in ts_text):
            return False
        ts = int(ts_text)
        if now - ts < 0 or now - ts > self.max_age:
            return False
        expected = self._sign(session_id, ts)
        return hmac.compare_digest(sig.encode("utf-8"), expected.encode("utf-8"))
''',
    tests=[
        [["CsrfProtect", "issue", "verify", "verify", "verify"],
         [["k1", 600], ["sess-A", 1000], ["sess-A", _GOOD, 1300], ["sess-B", _GOOD, 1300], ["sess-A", _GOOD, 1601]]],
        [["CsrfProtect", "verify", "verify"], [["k1", 600], ["sess-A", _GOOD, 1000], ["sess-A", _GOOD, 1600]]],
        [["CsrfProtect", "verify"], [["k1", 600], ["sess-A", _OTHER_SECRET, 1100]]],
        [["CsrfProtect", "verify"], [["k1", 600], ["sess-A", _OTHER_SESSION, 1100]]],
        [["CsrfProtect", "verify"], [["k1", 600], ["sess-B", _OTHER_SESSION, 1100]]],
        [["CsrfProtect", "verify"], [["k1", 600], ["sess-A", _FUTURE, 1100]]],
        [["CsrfProtect", "verify"], [["k1", 600], ["sess-A", _TS_SWAPPED, 1600]]],
        [["CsrfProtect", "verify", "verify", "verify", "verify"],
         [["k1", 600], ["sess-A", "", 1100], ["sess-A", "abc", 1100], ["sess-A", "1.2.3", 1100], ["sess-A", None, 1100]]],
        [["CsrfProtect", "verify", "verify"], [["k1", 600], ["sess-A", "x." + _GOOD.split(".")[1], 1100], ["sess-A", "1000.", 1100]]],
        [["CsrfProtect", "verify"], [["k1", 600], ["sess-A", _GOOD.upper(), 1100]]],
        [["CsrfProtect", "issue", "issue"], [["another-key", 60], ["u1", 5], ["u2", 5]]],
        [["CsrfProtect", "verify"], [["k1", 0], ["sess-A", _GOOD, 1000]]],
        [["CsrfProtect", "verify"], [["k1", 0], ["sess-A", _GOOD, 1001]]],
    ],
    examples=1,
    wrong_solutions=[
        r'''import hashlib
import hmac

class CsrfProtect:
    def __init__(self, secret, max_age):
        self.key = secret.encode()
        self.max_age = max_age

    def issue(self, session_id, now):
        return str(now) + "." + hmac.new(self.key, (session_id + "|" + str(now)).encode(), hashlib.sha256).hexdigest()

    def verify(self, session_id, token, now):
        if not isinstance(token, str) or token.count(".") != 1:
            return False
        ts, sig = token.split(".")
        if not ts.isdigit():
            return False
        expected = hmac.new(self.key, (session_id + "|" + ts).encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(sig, expected)
''',
        r'''import hashlib
import hmac

class CsrfProtect:
    def __init__(self, secret, max_age):
        self.key = secret.encode()
        self.max_age = max_age

    def issue(self, session_id, now):
        return str(now) + "." + hmac.new(self.key, (session_id + "|" + str(now)).encode(), hashlib.sha256).hexdigest()

    def verify(self, session_id, token, now):
        if not isinstance(token, str) or token.count(".") != 1:
            return False
        ts, sig = token.split(".")
        if not ts.isdigit():
            return False
        if not 0 <= now - int(ts) <= self.max_age:
            return False
        return len(sig) == 64
''',
        r'''import hashlib
import hmac

class CsrfProtect:
    def __init__(self, secret, max_age):
        self.key = secret.encode()
        self.max_age = max_age

    def issue(self, session_id, now):
        return str(now) + "." + hmac.new(self.key, str(now).encode(), hashlib.sha256).hexdigest()

    def verify(self, session_id, token, now):
        if not isinstance(token, str) or token.count(".") != 1:
            return False
        ts, sig = token.split(".")
        if not ts.isdigit() or not 0 <= now - int(ts) <= self.max_age:
            return False
        return hmac.compare_digest(sig, hmac.new(self.key, ts.encode(), hashlib.sha256).hexdigest())
''',
    ],
    guide=dict(
        prereqs="The CSRF lesson (synchroniser tokens and signed double-submit tokens); HMAC from the standard `hmac` module.",
        intuition="A forged cross-site request carries the victim's cookies automatically but cannot contain a value "
                  "the attacker is unable to compute. A MAC over `session id + timestamp` is such a value: only the "
                  "server holds the key, the session binding stops a token minted for one account working on another, "
                  "and the timestamp limits how long a leaked token is useful.",
        hints=[
            "Write one private helper that signs `(session_id, ts)`; both methods call it.",
            "Validate the token's *shape* before touching `int()` so that garbage input cannot raise.",
            "Check the age window before computing the MAC, and compare signatures with `hmac.compare_digest`.",
        ],
        brute_force="Store every issued token in a server-side table and look it up. That is the classic synchroniser "
                    "pattern and is perfectly secure, but costs storage and shared state across servers; signing removes both.",
        approach="`issue`: `sig = HMAC(secret, session_id + '|' + now)`; return `now.sig`.\n\n"
                 "`verify`: type check → split into exactly two parts → digits only → window check → recompute → constant-time compare.\n\n"
                 "Dry run: key `k1`, `max_age` 600, token issued for `sess-A` at 1000. `verify('sess-A', t, 1601)`: shape ok, "
                 "`ts = 1000`, age 601 > 600 → `False` without computing the MAC. `verify('sess-B', t, 1300)`: age ok, expected "
                 "signature is computed over `sess-B|1000`, which differs → `False`.",
        complexity="Time O(n) in the token and session-id length per call; space O(1). No server-side storage.",
        pitfalls="- Signing only the timestamp makes one token valid for every user.\n"
                 "- `str.isdigit()` accepts non-ASCII digits such as `'²'` that `int()` rejects — check against `0-9` explicitly.\n"
                 "- Accepting tokens from the future hides clock problems and extends lifetimes.\n"
                 "- Comparing with `==` leaks timing; hex digests are case-sensitive, so do not normalise case.",
        follow_up="Bind the token to the form action as well, rotate the key with a key-id prefix, and remember that "
                  "any XSS on the origin can read tokens and defeats CSRF protection entirely.",
    ),
),
dict(
    id="sec-samesite-decision",
    title="Will the Browser Send This Cookie? (SameSite)",
    difficulty="Easy",
    pattern="CSRF Defence",
    kind="function",
    entry="cookieIsSent",
    description=r"""
Model the browser's `SameSite` decision so you can reason about which requests carry a session cookie.

Write `cookieIsSent(samesite, secure, same_site, method, top_level)` returning a bool, where:

- `samesite` — the cookie's `SameSite` attribute as a string in any letter case, or `None`/`""` if it
  was not set. Missing or unrecognised values are treated as `Lax` (the modern browser default);
- `secure` — whether the cookie has the `Secure` attribute;
- `same_site` — `True` when the request's initiator and its target belong to the same *site*;
- `method` — HTTP method in any letter case;
- `top_level` — `True` when the request is a top-level navigation (the address bar changes: a link
  click or a form submission), `False` for sub-resource requests such as images, frames and `fetch`.

Assume the request is made over HTTPS. Rules:

- `None`: sent on every request, **but only if** `secure` is true; an insecure `SameSite=None` cookie is
  rejected by browsers and therefore never sent.
- `Strict`: sent only when `same_site` is true.
- `Lax`: sent when `same_site` is true, **or** when the request is a top-level navigation using a safe
  method (`GET`, `HEAD`, `OPTIONS`, `TRACE`).

**Example:** `cookieIsSent("Lax", True, False, "POST", True)` → `False` (a cross-site form post)

**Example:** `cookieIsSent("Lax", True, False, "GET", True)` → `True` (following a link from another site)
""",
    starter='''def cookieIsSent(samesite, secure: bool, same_site: bool, method: str, top_level: bool) -> bool:
    pass
''',
    solution=r'''def cookieIsSent(samesite, secure, same_site, method, top_level):
    mode = (samesite or "").strip().lower()
    if mode not in ("strict", "lax", "none"):
        mode = "lax"
    if mode == "none":
        return bool(secure)
    if same_site:
        return True
    if mode == "strict":
        return False
    return bool(top_level) and method.upper() in ("GET", "HEAD", "OPTIONS", "TRACE")
''',
    tests=[
        ["Lax", True, False, "POST", True],
        ["Lax", True, False, "GET", True],
        ["Strict", True, False, "GET", True],
        ["Strict", True, True, "POST", False],
        ["None", True, False, "POST", False],
        ["None", False, False, "POST", False],
        ["none", False, True, "GET", True],
        [None, True, False, "POST", True],
        [None, False, False, "get", True],
        ["", True, False, "GET", False],
        ["LAX", False, True, "DELETE", False],
        ["bogus", True, False, "POST", False],
        ["bogus", True, False, "HEAD", True],
        ["strict", False, True, "GET", True],
        ["Lax", True, False, "PUT", True],
    ],
    examples=2,
    wrong_solutions=[
        r'''def cookieIsSent(samesite, secure, same_site, method, top_level):
    mode = (samesite or "none").lower()
    if mode == "none":
        return True
    if same_site:
        return True
    if mode == "strict":
        return False
    return top_level and method.upper() == "GET"
''',
        r'''def cookieIsSent(samesite, secure, same_site, method, top_level):
    mode = (samesite or "lax").lower()
    if mode == "none":
        return bool(secure)
    if same_site:
        return True
    if mode == "strict":
        return False
    return method.upper() in ("GET", "HEAD", "OPTIONS", "TRACE")
''',
    ],
    guide=dict(
        prereqs="The CSRF lesson and the cookie attributes section of the session lesson. The difference between *site* and *origin*.",
        intuition="`SameSite` asks one question — did this request start on my own site? — and three modes answer it "
                  "with different strictness. `Lax` makes a single exception so that ordinary links from other sites "
                  "still arrive logged in, while cross-site POSTs, images and scripts arrive anonymous.",
        hints=[
            "Normalise first: lower-case, and map anything unknown to `lax`.",
            "`None` depends only on `secure`; `Strict` depends only on `same_site`.",
            "For `Lax`, the cross-site exception needs **both** a top-level navigation and a safe method.",
        ],
        brute_force="A table of all 3 × 2 × 2 × methods × 2 combinations. It works but hides the three short rules.",
        approach="1. Normalise the mode. 2. `none` → `secure`. 3. Same-site requests → `True`. 4. Cross-site + `strict` → `False`. "
                 "5. Cross-site + `lax` → `top_level and method is safe`.\n\n"
                 "Dry run `('bogus', True, False, 'HEAD', True)`: unknown mode → `lax`; cross-site; top-level and `HEAD` is safe → `True`.",
        complexity="O(1) time and space.",
        pitfalls="- Treating a missing attribute as `None` reflects pre-2020 browsers, not current ones.\n"
                 "- A cross-site `<img>` or `fetch` using GET is **not** top-level, so `Lax` withholds the cookie.\n"
                 "- `Lax` still sends cookies on cross-site top-level GETs, so state-changing GET endpoints remain forgeable.\n"
                 "- *Same site* is broader than *same origin*: `blog.shop.example` and `app.shop.example` are same-site, so a "
                 "compromised sibling subdomain bypasses `SameSite`.",
        follow_up="Chrome applies a short 'Lax + POST' grace period to cookies without an explicit attribute; do not "
                  "rely on defaults — set the attribute explicitly and keep CSRF tokens for sensitive actions.",
    ),
),
dict(
    id="sec-header-audit",
    title="Security Header Audit of a Response",
    difficulty="Easy",
    pattern="Security Misconfiguration",
    kind="function",
    entry="auditHeaders",
    description=r"""
Write `auditHeaders(headers)` that inspects a dict of HTTP **response** headers (name → value) and returns
a **sorted** list of findings. Header names are case-insensitive; trim values before judging them.

| finding | reported when |
|---|---|
| `"hsts"` | `Strict-Transport-Security` is absent, has no `max-age=<digits>`, or the max-age is below `31536000` (one year) |
| `"nosniff"` | `X-Content-Type-Options` is not `nosniff` (case-insensitive) |
| `"csp"` | `Content-Security-Policy` is absent or empty |
| `"framing"` | `X-Frame-Options` is neither `DENY` nor `SAMEORIGIN` (case-insensitive) **and** the CSP does not contain a `frame-ancestors` directive |
| `"referrer"` | `Referrer-Policy` is absent, empty, or `unsafe-url` |
| `"server-version"` | a `Server` header is present and contains at least one digit |
| `"x-powered-by"` | an `X-Powered-By` header is present at all |

**Example:** `auditHeaders({"Server": "nginx/1.25.3", "X-Content-Type-Options": "nosniff"})` →
`["csp", "framing", "hsts", "referrer", "server-version"]`
""",
    starter='''def auditHeaders(headers: dict) -> list:
    pass
''',
    solution=r'''import re

def auditHeaders(headers):
    h = {str(k).lower(): str(v).strip() for k, v in headers.items()}
    findings = []
    match = re.search(r"max-age\s*=\s*(\d+)", h.get("strict-transport-security", "").lower())
    if not match or int(match.group(1)) < 31536000:
        findings.append("hsts")
    if h.get("x-content-type-options", "").lower() != "nosniff":
        findings.append("nosniff")
    csp = h.get("content-security-policy", "")
    if not csp:
        findings.append("csp")
    frame_option = h.get("x-frame-options", "").upper()
    if frame_option not in ("DENY", "SAMEORIGIN") and "frame-ancestors" not in csp.lower():
        findings.append("framing")
    referrer = h.get("referrer-policy", "").lower()
    if not referrer or referrer == "unsafe-url":
        findings.append("referrer")
    if any(c.isdigit() for c in h.get("server", "")):
        findings.append("server-version")
    if "x-powered-by" in h:
        findings.append("x-powered-by")
    return sorted(findings)
''',
    tests=[
        [{"Server": "nginx/1.25.3", "X-Content-Type-Options": "nosniff"}],
        [{}],
        [{"Strict-Transport-Security": "max-age=63072000; includeSubDomains; preload",
          "X-Content-Type-Options": "nosniff",
          "Content-Security-Policy": "default-src 'self'; frame-ancestors 'none'",
          "Referrer-Policy": "strict-origin-when-cross-origin", "Server": "nginx"}],
        [{"strict-transport-security": "max-age=300", "x-content-type-options": "NOSNIFF",
          "content-security-policy": "default-src 'self'", "x-frame-options": "deny", "referrer-policy": "no-referrer"}],
        [{"Strict-Transport-Security": "includeSubDomains", "X-Frame-Options": "ALLOWALL"}],
        [{"X-Powered-By": "Express", "Referrer-Policy": "unsafe-url"}],
        [{"Strict-Transport-Security": "max-age=31536000", "X-Content-Type-Options": " nosniff ",
          "Content-Security-Policy": "default-src 'self'", "X-Frame-Options": "SameOrigin",
          "Referrer-Policy": "same-origin", "Server": "Apache/2.4.58 (Ubuntu)"}],
        [{"Strict-Transport-Security": "max-age=31535999", "Content-Security-Policy": ""}],
        [{"Content-Security-Policy": "FRAME-ANCESTORS 'self'", "X-Content-Type-Options": "sniff"}],
        [{"STRICT-TRANSPORT-SECURITY": "Max-Age = 99999999", "Referrer-Policy": ""}],
        [{"Server": "cloud-frontend", "X-Powered-By": ""}],
        [{"Strict-Transport-Security": "max-age=31536000", "X-Content-Type-Options": "nosniff",
          "Content-Security-Policy": "default-src 'self'", "Referrer-Policy": "origin"}],
    ],
    examples=1,
    wrong_solutions=[
        r'''def auditHeaders(headers):
    findings = []
    if "Strict-Transport-Security" not in headers:
        findings.append("hsts")
    if headers.get("X-Content-Type-Options") != "nosniff":
        findings.append("nosniff")
    if "Content-Security-Policy" not in headers:
        findings.append("csp")
    if "X-Frame-Options" not in headers:
        findings.append("framing")
    if "Referrer-Policy" not in headers:
        findings.append("referrer")
    if any(c.isdigit() for c in headers.get("Server", "")):
        findings.append("server-version")
    if "X-Powered-By" in headers:
        findings.append("x-powered-by")
    return sorted(findings)
''',
        r'''import re

def auditHeaders(headers):
    h = {k.lower(): str(v).strip() for k, v in headers.items()}
    findings = []
    if "strict-transport-security" not in h:
        findings.append("hsts")
    if h.get("x-content-type-options", "").lower() != "nosniff":
        findings.append("nosniff")
    csp = h.get("content-security-policy", "")
    if not csp:
        findings.append("csp")
    if h.get("x-frame-options", "").upper() not in ("DENY", "SAMEORIGIN"):
        findings.append("framing")
    if not h.get("referrer-policy"):
        findings.append("referrer")
    if any(c.isdigit() for c in h.get("server", "")):
        findings.append("server-version")
    if h.get("x-powered-by"):
        findings.append("x-powered-by")
    return sorted(findings)
''',
    ],
    guide=dict(
        prereqs="The security headers lesson (HSTS, nosniff, CSP, framing controls, Referrer-Policy, banner disclosure).",
        intuition="Normalise once — lower-case names, trimmed values — and the audit becomes a checklist of independent "
                  "predicates. Presence is not enough: several headers can be present and still useless.",
        hints=[
            "Build a new dict with lower-cased keys before doing anything else.",
            "For HSTS, extract the number after `max-age=` with a regular expression and compare it numerically.",
            "The framing check passes if **either** mechanism is in place: a good `X-Frame-Options` or a CSP `frame-ancestors`.",
        ],
        brute_force="Test `'Header-Name' in headers` for each header. It misses differently-cased names and accepts "
                    "weak values such as `max-age=300` or `X-Frame-Options: ALLOWALL`.",
        approach="Normalise → seven predicates → sort.\n\n"
                 "Dry run `{'Server': 'nginx/1.25.3', 'X-Content-Type-Options': 'nosniff'}`: no HSTS → `hsts`; nosniff ok; "
                 "no CSP → `csp`; no frame option and no `frame-ancestors` → `framing`; no referrer policy → `referrer`; "
                 "`Server` contains digits → `server-version`; no `X-Powered-By`. Sorted: "
                 "`['csp', 'framing', 'hsts', 'referrer', 'server-version']`.",
        complexity="Time O(total header length); space O(same) for the normalised copy.",
        pitfalls="- HTTP header names are case-insensitive; HTTP/2 delivers them lower-case.\n"
                 "- `X-Powered-By` with an empty value is still a present header.\n"
                 "- `frame-ancestors` supersedes `X-Frame-Options` in modern browsers; either satisfies the check.\n"
                 "- A header audit says nothing about whether the CSP itself is strict — that is a separate audit.",
        follow_up="Add `Permissions-Policy`, `Cross-Origin-Opener-Policy` and `Cross-Origin-Resource-Policy`, and check "
                  "that `Cache-Control: no-store` accompanies responses containing personal data.",
    ),
),
]
