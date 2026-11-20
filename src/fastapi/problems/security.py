import base64 as _b64
import hashlib as _hl
import hmac as _hm
import json as _js


def _b64u(b):
    return _b64.urlsafe_b64encode(b).rstrip(b"=").decode()


def _tok(payload, secret, header=None, sig_secret=None):
    h = header if header is not None else {"alg": "HS256", "typ": "JWT"}
    hs = _b64u(_js.dumps(h, separators=(",", ":")).encode())
    ps = _b64u(_js.dumps(payload, separators=(",", ":"), sort_keys=True).encode())
    sig = _hm.new((sig_secret or secret).encode(), f"{hs}.{ps}".encode(), _hl.sha256).digest()
    return f"{hs}.{ps}.{_b64u(sig)}"


def _pbkdf2(pw, salt, it):
    return _hl.pbkdf2_hmac("sha256", pw.encode(), salt, it).hex()


def _stored(pw, salt_hex, it):
    return f"pbkdf2_sha256${it}${salt_hex}${_pbkdf2(pw, bytes.fromhex(salt_hex), it)}"


_T1 = _tok({"sub": "ann", "exp": 100}, "s3cret")
_h, _p, _s = _T1.split(".")
_TAMPERED = _h + "." + _b64u(_js.dumps({"exp": 100, "role": "admin", "sub": "ann"}, separators=(",", ":")).encode()) + "." + _s
_NONE = _b64u(b'{"alg":"none","typ":"JWT"}') + "." + _p + "."
_HS512 = _tok({"sub": "ann"}, "s3cret", header={"alg": "HS512", "typ": "JWT"})

PROBLEMS = [
dict(
    id="api-jwt-hs256",
    title="JWT (HS256) Encode and Verify",
    difficulty="Hard",
    pattern="Authentication",
    kind="class",
    entry="HS256",
    description=r"""
A JSON Web Token is three base64url segments joined by dots: `header.payload.signature`. With HS256 the
signature is `HMAC-SHA256(secret, "header.payload")`. Implement a minimal, *safe* codec using only
`hmac`, `hashlib`, `base64` and `json`.

`HS256(secret)`:

- `encode(payload)` → token string.
  - header JSON is exactly `{"alg":"HS256","typ":"JWT"}` (compact, that key order);
  - payload JSON is `json.dumps(payload, separators=(",", ":"), sort_keys=True)`;
  - each segment is **base64url without `=` padding**.
- `decode(token, now)` → the payload dict, or one of these error strings:
  - `"malformed"` — not exactly three dot-separated parts, or a header/payload segment that is not valid
    base64url JSON;
  - `"invalid_algorithm"` — header `alg` is not `"HS256"` (this blocks the infamous `alg: none` attack);
  - `"invalid_signature"` — signature mismatch (compare with `hmac.compare_digest`);
  - `"expired"` — payload has `"exp"` and `now >= exp`.
  Check in that order.

**Example:** `encode({"sub": "ann"})` with secret `"k"` gives a token whose middle part decodes to
`{"sub":"ann"}`; `decode(that_token, 0)` → `{"sub": "ann"}`.

> Restoring padding: `seg + "=" * (-len(seg) % 4)` before `base64.urlsafe_b64decode`.
""",
    starter='''import base64, hashlib, hmac, json

class HS256:
    def __init__(self, secret: str):
        pass

    def encode(self, payload: dict) -> str:
        pass

    def decode(self, token: str, now: int):
        pass
''',
    solution='''import base64, hashlib, hmac, json

def _b64u(b):
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()

def _unb64u(s):
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))

class HS256:
    def __init__(self, secret):
        self.key = secret.encode()

    def _sign(self, msg):
        return _b64u(hmac.new(self.key, msg.encode(), hashlib.sha256).digest())

    def encode(self, payload):
        h = _b64u(json.dumps({"alg": "HS256", "typ": "JWT"}, separators=(",", ":")).encode())
        p = _b64u(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode())
        return f"{h}.{p}.{self._sign(h + '.' + p)}"

    def decode(self, token, now):
        parts = token.split(".")
        if len(parts) != 3:
            return "malformed"
        h, p, s = parts
        try:
            header = json.loads(_unb64u(h))
            payload = json.loads(_unb64u(p))
        except Exception:
            return "malformed"
        if not isinstance(header, dict) or not isinstance(payload, dict):
            return "malformed"
        if header.get("alg") != "HS256":
            return "invalid_algorithm"
        if not hmac.compare_digest(self._sign(h + "." + p), s):
            return "invalid_signature"
        if "exp" in payload and now >= payload["exp"]:
            return "expired"
        return payload
''',
    tests=[
        [["HS256", "encode", "decode"], [["k"], [{"sub": "ann"}], [_tok({"sub": "ann"}, "k"), 0]]],
        [["HS256", "decode", "decode", "decode"], [["s3cret"], [_T1, 99], [_T1, 100], [_T1, 5000]]],
        [["HS256", "decode"], [["s3cret"], [_TAMPERED, 0]]],
        [["HS256", "decode"], [["s3cret"], [_NONE, 0]]],
        [["HS256", "decode"], [["s3cret"], [_HS512, 0]]],
        [["HS256", "decode"], [["other"], [_T1, 0]]],
        [["HS256", "decode", "decode", "decode"], [["k"], ["abc", 0], ["a.b", 0], ["a.b.c.d", 0]]],
        [["HS256", "decode"], [["k"], ["!!!.###.sig", 0]]],
        [["HS256", "encode", "encode"], [["key"], [{"b": 2, "a": 1}], [{"role": "admin", "scopes": ["items:read", "items:write"], "exp": 1700000000}]]],
        [["HS256", "decode"], [["key"], [_tok({"b": 2, "a": 1, "nested": {"x": [1, 2]}}, "key"), 0]]],
        [["HS256", "decode"], [["k"], [_tok({"sub": "ann"}, "k")[:-2] + "AA", 0]]],
        [["HS256", "encode"], [["unicodé"], [{"name": "Zoë"}]]],
    ],
    wrong_solutions=[
        '''import base64, hashlib, hmac, json
def _b(b): return base64.urlsafe_b64encode(b).rstrip(b"=").decode()
def _u(s): return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))
class HS256:
    def __init__(self, secret): self.k = secret.encode()
    def _sign(self, m): return _b(hmac.new(self.k, m.encode(), hashlib.sha256).digest())
    def encode(self, payload):
        h = _b(b'{"alg":"HS256","typ":"JWT"}'); p = _b(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode())
        return f"{h}.{p}.{self._sign(h + '.' + p)}"
    def decode(self, token, now):
        parts = token.split(".")
        if len(parts) != 3: return "malformed"
        h, p, s = parts
        try: header = json.loads(_u(h)); payload = json.loads(_u(p))
        except Exception: return "malformed"
        if header.get("alg") == "none": return payload
        if self._sign(h + "." + p) != s: return "invalid_signature"
        if "exp" in payload and now >= payload["exp"]: return "expired"
        return payload
''',
        '''import base64, hashlib, hmac, json
class HS256:
    def __init__(self, secret): self.k = secret.encode()
    def encode(self, payload):
        h = base64.urlsafe_b64encode(b'{"alg":"HS256","typ":"JWT"}').decode()
        p = base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()).decode()
        s = base64.urlsafe_b64encode(hmac.new(self.k, f"{h}.{p}".encode(), hashlib.sha256).digest()).decode()
        return f"{h}.{p}.{s}"
    def decode(self, token, now):
        return "malformed"
''',
    ],
    guide=dict(
        prereqs="JWT structure (lesson *OAuth2 password flow, hashing and JWT*); HMAC.",
        intuition="A JWT is **signed, not encrypted**: anyone can read the payload. The HMAC proves that someone "
                  "holding the secret produced exactly these header and payload bytes. So the verifier must "
                  "(1) pin the algorithm it expects, (2) recompute the HMAC over the *received* segments and compare "
                  "in constant time, and only then (3) trust claims like `exp`.",
        hints=["base64url = `urlsafe_b64encode` then strip `=`; decoding needs the padding restored.",
               "Sign the exact string `header_segment + '.' + payload_segment` — do not re-serialise the JSON.",
               "Wrap both segment decodes in one `try/except` for `malformed`.",
               "Never accept the algorithm the token *claims* unless it is the one you expect."],
        brute_force="Not applicable; the danger is not slowness but insecure shortcuts (trusting `alg`, using `==`).",
        approach="`encode`: serialise header and payload compactly, base64url both, HMAC the joined string, "
                 "base64url the digest. `decode`: split → decode JSON (malformed) → check `alg` → recompute and "
                 "`compare_digest` → check `exp` → return payload.",
        complexity="O(len(token)).",
        pitfalls="- Accepting `alg: none` or any algorithm the attacker picks.\n"
                 "- `==` on signatures leaks timing information; use `hmac.compare_digest`.\n"
                 "- Checking `exp` before verifying the signature (an attacker could set any exp).\n"
                 "- Leaving `=` padding in the output.",
        follow_up="In production use PyJWT: `jwt.decode(token, key, algorithms=['HS256'])` — note the *list* of "
                  "allowed algorithms. Asymmetric RS256/ES256 let many services verify tokens without the signing key.",
    ),
),
dict(
    id="api-password-hash",
    title="Verify a PBKDF2 Password Hash",
    difficulty="Easy",
    pattern="Authentication",
    entry="verifyPassword",
    description=r"""
Never store passwords — store a **slow, salted hash**. A common self-describing format is

```
pbkdf2_sha256$<iterations>$<salt_hex>$<hash_hex>
```

where `hash_hex = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), iterations).hex()`.

Write `verifyPassword(password, stored)` → `True` if the password matches, else `False`. Return `False`
(do not raise) for anything malformed: wrong number of `$` parts, an algorithm other than `pbkdf2_sha256`,
a non-integer or non-positive iteration count, or non-hex salt/hash. Compare digests with
`hmac.compare_digest`.

**Example:** `verifyPassword("hunter2", "pbkdf2_sha256$1000$73616c74$...")` → `True` when the hash matches.

> In the browser, `hashlib.pbkdf2_hmac` needs Pyodide's OpenSSL-backed hashlib; it is loaded automatically
> when your code imports `hashlib`.
""",
    starter='''import hashlib, hmac

def verifyPassword(password: str, stored: str) -> bool:
    pass
''',
    solution='''import hashlib, hmac

def verifyPassword(password, stored):
    parts = stored.split("$")
    if len(parts) != 4 or parts[0] != "pbkdf2_sha256":
        return False
    try:
        iterations = int(parts[1])
        salt = bytes.fromhex(parts[2])
        expected = bytes.fromhex(parts[3])
    except ValueError:
        return False
    if iterations <= 0:
        return False
    got = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, iterations)
    return hmac.compare_digest(got, expected)
''',
    tests=[
        ["hunter2", _stored("hunter2", "73616c74", 1000)],
        ["hunter3", _stored("hunter2", "73616c74", 1000)],
        ["", _stored("", "00ff", 500)],
        ["hunter2", _stored("hunter2", "73616c74", 1000).replace("$1000$", "$1001$")],
        ["hunter2", _stored("hunter2", "73616c74", 1000).replace("pbkdf2_sha256", "pbkdf2_sha1")],
        ["hunter2", "pbkdf2_sha256$1000$73616c74"],
        ["hunter2", "pbkdf2_sha256$abc$73616c74$00"],
        ["hunter2", "pbkdf2_sha256$1000$zz$00"],
        ["hunter2", "pbkdf2_sha256$0$73616c74$00"],
        ["pässwörd", _stored("pässwörd", "a1b2c3d4e5f60718", 2000)],
        ["Hunter2", _stored("hunter2", "73616c74", 1000)],
        ["x", ""],
        ["x", "pbkdf2_sha256$-5$73616c74$00"],
    ],
    wrong_solutions=[
        '''import hashlib
def verifyPassword(password, stored):
    a, it, salt, h = stored.split("$")
    return hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), int(it)).hex() == h
''',
        '''import hashlib, hmac
def verifyPassword(password, stored):
    try:
        a, it, salt, h = stored.split("$")
        return hmac.compare_digest(hashlib.sha256(bytes.fromhex(salt) + password.encode()).hexdigest(), h)
    except ValueError:
        return False
''',
    ],
    guide=dict(
        prereqs="Password hashing (lesson *OAuth2 password flow, hashing and JWT*).",
        intuition="Verification re-runs the same slow function with the stored salt and iteration count, then "
                  "compares. Storing the parameters *in* the hash string lets you raise the iteration count later "
                  "without breaking old hashes.",
        hints=["`stored.split('$')` must give exactly 4 parts.",
               "`int()` and `bytes.fromhex()` raise `ValueError` on bad input — catch it.",
               "Compare raw bytes with `hmac.compare_digest`."],
        brute_force="Comparing hex strings with `==` gives the right answer but leaks timing; a plain `sha256` "
                    "would be *fast* to brute-force, which is exactly what you don't want.",
        approach="Parse, validate, recompute `pbkdf2_hmac`, constant-time compare.",
        complexity="O(iterations) — deliberately slow (production uses hundreds of thousands of iterations, or Argon2).",
        pitfalls="- Raising on malformed input (an attacker-controlled DB row should not crash login).\n"
                 "- Ignoring the algorithm tag.\n- Zero or negative iterations.",
        follow_up="The current FastAPI tutorial uses `pwdlib` with Argon2 (`PasswordHash.recommended()`), a memory-hard "
                  "algorithm that resists GPU cracking better than PBKDF2.",
    ),
),
dict(
    id="api-token-bucket",
    title="Token-Bucket Rate Limiter",
    difficulty="Medium",
    pattern="Rate Limiting",
    kind="class",
    entry="TokenBucket",
    description=r"""
A token bucket allows short bursts while enforcing an average rate. The bucket holds at most `capacity`
tokens and refills continuously at `rate` tokens per second. Each request spends tokens; if there are not
enough, the request is rejected (HTTP 429) and **no tokens are spent**.

`TokenBucket(capacity, rate)` — starts **full** at time `0`.

- `allow(now, cost)` → `True`/`False`. First refill: `tokens = min(capacity, tokens + (now - last) * rate)`,
  set `last = now`. Then if `tokens >= cost`, subtract and return `True`.
- `available(now)` → current tokens after refilling, rounded to 3 decimals.

Timestamps never decrease. Use a small epsilon (`1e-9`) in the comparison to absorb float error.

**Example:** `["TokenBucket","allow","allow","allow","allow"]`, `[[2, 1], [0, 1], [0, 1], [0, 1], [1, 1]]`
→ `[None, True, True, False, True]`
""",
    starter='''class TokenBucket:
    def __init__(self, capacity: float, rate: float):
        pass

    def allow(self, now: float, cost: float) -> bool:
        pass

    def available(self, now: float) -> float:
        pass
''',
    solution='''class TokenBucket:
    def __init__(self, capacity, rate):
        self.capacity, self.rate = capacity, rate
        self.tokens, self.last = float(capacity), 0.0

    def _refill(self, now):
        self.tokens = min(self.capacity, self.tokens + (now - self.last) * self.rate)
        self.last = now

    def allow(self, now, cost):
        self._refill(now)
        if self.tokens + 1e-9 >= cost:
            self.tokens -= cost
            return True
        return False

    def available(self, now):
        self._refill(now)
        return round(self.tokens, 3)
''',
    tests=[
        [["TokenBucket", "allow", "allow", "allow", "allow"], [[2, 1], [0, 1], [0, 1], [0, 1], [1, 1]]],
        [["TokenBucket", "available", "allow", "available"], [[5, 0.5], [0], [0, 5], [3]]],
        [["TokenBucket", "allow", "allow", "available"], [[10, 1], [0, 11], [0, 10], [100]]],
        [["TokenBucket", "allow", "allow", "allow"], [[3, 1], [0, 3], [0.5, 1], [1.0, 1]]],
        [["TokenBucket", "allow", "allow", "allow", "allow"], [[1, 0.1], [0, 1], [5, 1], [9.9, 1], [10, 1]]],
        [["TokenBucket", "allow", "allow", "available"], [[4, 2], [0, 4], [0.5, 2], [0.75]]],
        [["TokenBucket", "allow", "allow", "allow"], [[2, 0], [0, 1], [100, 1], [1000, 1]]],
        [["TokenBucket"] + ["allow"] * 50, [[5, 2]] + [[i * 0.25, 1] for i in range(50)]],
        [["TokenBucket", "allow", "available", "allow"], [[1, 1], [0, 0.3], [0], [0, 0.7]]],
        [["TokenBucket", "allow", "allow", "allow"], [[100, 10], [0, 60], [1, 60], [2, 60]]],
    ],
    wrong_solutions=[
        '''class TokenBucket:
    def __init__(self, capacity, rate):
        self.c, self.r, self.t, self.l = capacity, rate, capacity, 0
    def allow(self, now, cost):
        self.t = self.t + (now - self.l) * self.r; self.l = now
        if self.t >= cost - 1e-9: self.t -= cost; return True
        return False
    def available(self, now):
        self.t = self.t + (now - self.l) * self.r; self.l = now
        return round(self.t, 3)
''',
        '''class TokenBucket:
    def __init__(self, capacity, rate):
        self.c, self.r, self.t, self.l = capacity, rate, capacity, 0
    def allow(self, now, cost):
        self.t = min(self.c, self.t + (now - self.l) * self.r); self.l = now
        self.t -= cost
        if self.t >= -1e-9: return True
        return False
    def available(self, now):
        self.t = min(self.c, self.t + (now - self.l) * self.r); self.l = now
        return round(self.t, 3)
''',
    ],
    guide=dict(
        prereqs="Rate limiting (lesson *Authorization, CORS, rate limiting and common vulnerabilities*).",
        intuition="You don't need a timer to add tokens: compute how many *would* have been added since the last "
                  "call (`elapsed × rate`), cap at capacity, and you're up to date. Lazy refill makes the limiter "
                  "O(1) per request and trivially storable (two numbers per client).",
        hints=["Store `tokens` and `last` only.",
               "Refill before every operation, including `available`.",
               "A rejected request must not change the token count."],
        brute_force="A sliding log of request timestamps per client also works but costs O(requests in window) memory.",
        approach="Dry run `cap=3, rate=1`: t=0 spend 3 → 0 left; t=0.5 refill to 0.5 < 1 → reject; t=1.0 refill to 1.0 "
                 "→ allow.",
        complexity="O(1) time and space per call.",
        pitfalls="- Forgetting the `min(capacity, ...)` cap (idle clients get infinite bursts).\n"
                 "- Spending tokens on a rejected request.\n- Float drift: compare with an epsilon.",
        follow_up="In a multi-worker deployment, the bucket must live in shared storage (e.g. a Redis hash updated "
                  "atomically by a Lua script), otherwise each worker enforces its own limit.",
    ),
),
dict(
    id="api-cors-preflight",
    title="CORS Preflight Decision",
    difficulty="Medium",
    pattern="Security",
    entry="preflight",
    description=r"""
Before a browser sends a "non-simple" cross-origin request (e.g. `PUT` with JSON and an `Authorization`
header) it sends an `OPTIONS` **preflight**. Decide the response, in the spirit of Starlette's `CORSMiddleware`.

`preflight(config, headers)`:

`config` has `allow_origins` (list; `"*"` = any), `allow_methods` (list; `"*"` = any), `allow_headers`
(list; `"*"` = any; compare case-insensitively), `allow_credentials` (bool), `max_age` (int).

`headers` (request headers) contains `Origin`, `Access-Control-Request-Method`, and optionally
`Access-Control-Request-Headers` (comma-separated).

1. Origin allowed if `"*"` in `allow_origins` or exact match. Method allowed if `"*"` in `allow_methods`
   or exact match. Every requested header (stripped, lowercased, empty items ignored) must be allowed: it is
   one of the always-safe `accept`, `accept-language`, `content-language`, `content-type`, or `"*"` is in
   `allow_headers`, or it matches an allowed header case-insensitively.
2. If any check fails → `[400, {}]`.
3. Otherwise `[200, h]` where `h` contains:
   - `"Access-Control-Allow-Origin"`: `"*"` if `"*"` in `allow_origins` **and not** `allow_credentials`;
     otherwise the request's origin echoed back. When echoing, also set `"Vary": "Origin"`.
   - `"Access-Control-Allow-Methods"`: `", ".join(allow_methods)`.
   - `"Access-Control-Allow-Headers"`: the requested headers (lowercased, in request order) joined with
     `", "` — only if at least one was requested.
   - `"Access-Control-Max-Age"`: `str(max_age)`.
   - `"Access-Control-Allow-Credentials": "true"` only if `allow_credentials`.
""",
    starter='''def preflight(config: dict, headers: dict) -> list:
    pass
''',
    solution='''SAFE = {"accept", "accept-language", "content-language", "content-type"}

def preflight(config, headers):
    origin = headers.get("Origin", "")
    method = headers.get("Access-Control-Request-Method", "")
    req = [h.strip().lower() for h in headers.get("Access-Control-Request-Headers", "").split(",") if h.strip()]
    origins, methods = config["allow_origins"], config["allow_methods"]
    allowed_h = {h.lower() for h in config["allow_headers"]}
    any_origin = "*" in origins
    if not (any_origin or origin in origins):
        return [400, {}]
    if not ("*" in methods or method in methods):
        return [400, {}]
    for h in req:
        if not (h in SAFE or "*" in allowed_h or h in allowed_h):
            return [400, {}]
    out = {}
    if any_origin and not config["allow_credentials"]:
        out["Access-Control-Allow-Origin"] = "*"
    else:
        out["Access-Control-Allow-Origin"] = origin
        out["Vary"] = "Origin"
    out["Access-Control-Allow-Methods"] = ", ".join(methods)
    if req:
        out["Access-Control-Allow-Headers"] = ", ".join(req)
    out["Access-Control-Max-Age"] = str(config["max_age"])
    if config["allow_credentials"]:
        out["Access-Control-Allow-Credentials"] = "true"
    return [200, out]
''',
    tests=[
        [{"allow_origins": ["https://app.example.com"], "allow_methods": ["GET", "POST", "PUT"], "allow_headers": ["Authorization"], "allow_credentials": True, "max_age": 600},
         {"Origin": "https://app.example.com", "Access-Control-Request-Method": "PUT", "Access-Control-Request-Headers": "authorization, content-type"}],
        [{"allow_origins": ["https://app.example.com"], "allow_methods": ["GET"], "allow_headers": [], "allow_credentials": False, "max_age": 600},
         {"Origin": "https://evil.example", "Access-Control-Request-Method": "GET"}],
        [{"allow_origins": ["*"], "allow_methods": ["*"], "allow_headers": ["*"], "allow_credentials": False, "max_age": 60},
         {"Origin": "https://x.io", "Access-Control-Request-Method": "DELETE", "Access-Control-Request-Headers": "X-Custom"}],
        [{"allow_origins": ["*"], "allow_methods": ["GET", "POST"], "allow_headers": [], "allow_credentials": True, "max_age": 60},
         {"Origin": "https://x.io", "Access-Control-Request-Method": "POST"}],
        [{"allow_origins": ["*"], "allow_methods": ["GET"], "allow_headers": [], "allow_credentials": False, "max_age": 60},
         {"Origin": "https://x.io", "Access-Control-Request-Method": "PATCH"}],
        [{"allow_origins": ["*"], "allow_methods": ["GET"], "allow_headers": [], "allow_credentials": False, "max_age": 60},
         {"Origin": "https://x.io", "Access-Control-Request-Method": "GET", "Access-Control-Request-Headers": "Content-Type, Accept"}],
        [{"allow_origins": ["*"], "allow_methods": ["GET"], "allow_headers": ["X-Api-Key"], "allow_credentials": False, "max_age": 60},
         {"Origin": "https://x.io", "Access-Control-Request-Method": "GET", "Access-Control-Request-Headers": "x-api-key, x-other"}],
        [{"allow_origins": ["https://a.com", "https://b.com"], "allow_methods": ["GET"], "allow_headers": ["x-api-key"], "allow_credentials": False, "max_age": 0},
         {"Origin": "https://b.com", "Access-Control-Request-Method": "GET", "Access-Control-Request-Headers": " X-API-KEY ,"}],
        [{"allow_origins": ["https://a.com"], "allow_methods": ["GET"], "allow_headers": [], "allow_credentials": False, "max_age": 600},
         {"Origin": "https://a.com.evil.net", "Access-Control-Request-Method": "GET"}],
        [{"allow_origins": ["https://a.com"], "allow_methods": ["GET"], "allow_headers": [], "allow_credentials": False, "max_age": 600},
         {"Origin": "http://a.com", "Access-Control-Request-Method": "GET"}],
        [{"allow_origins": ["https://a.com"], "allow_methods": ["get"], "allow_headers": [], "allow_credentials": False, "max_age": 600},
         {"Origin": "https://a.com", "Access-Control-Request-Method": "GET"}],
    ],
    wrong_solutions=[
        '''def preflight(config, headers):
    o = headers.get("Origin", "")
    if not ("*" in config["allow_origins"] or o in config["allow_origins"]): return [400, {}]
    if not ("*" in config["allow_methods"] or headers.get("Access-Control-Request-Method") in config["allow_methods"]): return [400, {}]
    req = [h.strip().lower() for h in headers.get("Access-Control-Request-Headers", "").split(",") if h.strip()]
    out = {"Access-Control-Allow-Origin": "*" if "*" in config["allow_origins"] else o}
    if out["Access-Control-Allow-Origin"] != "*": out["Vary"] = "Origin"
    out["Access-Control-Allow-Methods"] = ", ".join(config["allow_methods"])
    if req: out["Access-Control-Allow-Headers"] = ", ".join(req)
    out["Access-Control-Max-Age"] = str(config["max_age"])
    if config["allow_credentials"]: out["Access-Control-Allow-Credentials"] = "true"
    return [200, out]
''',
        '''def preflight(config, headers):
    o = headers.get("Origin", "")
    if not ("*" in config["allow_origins"] or any(o.startswith(a) for a in config["allow_origins"])): return [400, {}]
    m = headers.get("Access-Control-Request-Method", "")
    if not ("*" in config["allow_methods"] or m in config["allow_methods"]): return [400, {}]
    req = [h.strip().lower() for h in headers.get("Access-Control-Request-Headers", "").split(",") if h.strip()]
    al = {h.lower() for h in config["allow_headers"]}
    for h in req:
        if not (h in {"accept","accept-language","content-language","content-type"} or "*" in al or h in al): return [400, {}]
    out = {}
    if "*" in config["allow_origins"] and not config["allow_credentials"]: out["Access-Control-Allow-Origin"] = "*"
    else: out["Access-Control-Allow-Origin"] = o; out["Vary"] = "Origin"
    out["Access-Control-Allow-Methods"] = ", ".join(config["allow_methods"])
    if req: out["Access-Control-Allow-Headers"] = ", ".join(req)
    out["Access-Control-Max-Age"] = str(config["max_age"])
    if config["allow_credentials"]: out["Access-Control-Allow-Credentials"] = "true"
    return [200, out]
''',
    ],
    guide=dict(
        prereqs="CORS (lesson *Authorization, CORS, rate limiting and common vulnerabilities*).",
        intuition="CORS is the *server* telling the *browser* which other origins may read its responses. The "
                  "preflight asks 'may origin O send method M with headers H?'. One crucial rule: with credentials "
                  "(cookies), the browser rejects a wildcard `*` origin, so the server must echo the exact origin — "
                  "and add `Vary: Origin` so caches don't serve one origin's answer to another.",
        hints=["Normalise requested headers: split on commas, strip, lowercase, drop empties.",
               "Origins match exactly — scheme, host and port. Never use `startswith`.",
               "Decide `Allow-Origin` from two facts: is `*` configured, and are credentials allowed?"],
        brute_force="Not applicable — this is rule-following, not search.",
        approach="Validate origin, method, then each header; build the header dict in the listed order of rules.",
        complexity="O(number of requested headers).",
        pitfalls="- Prefix matching origins (`https://a.com.evil.net`).\n- Returning `*` together with credentials.\n"
                 "- Case: header names are case-insensitive; methods are case-sensitive.",
        follow_up="CORS protects *users' browsers*, not your API — `curl` ignores it entirely. Authentication and "
                  "authorization still have to happen on every request.",
    ),
),
]
