import base64 as _b64
import hashlib as _hashlib
import hmac as _hmac
import json as _json


def _sha(password):
    """htpasswd {SHA} entry for a password."""
    return "{SHA}" + _b64.b64encode(_hashlib.sha1(password.encode()).digest()).decode()


def _basic(user, password):
    """Authorization header value for HTTP basic authentication."""
    return "Basic " + _b64.b64encode(("%s:%s" % (user, password)).encode()).decode()


def _seg(obj):
    raw = obj if isinstance(obj, bytes) else _json.dumps(obj, separators=(",", ":")).encode()
    return _b64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def _jwt(claims, secret, alg="HS256", sign=True):
    """Build a compact JWT; with sign=False the signature part is empty."""
    head = _seg({"alg": alg, "typ": "JWT"}) + "." + _seg(claims)
    sig = _seg(_hmac.new(secret.encode(), head.encode(), _hashlib.sha256).digest()) if sign else ""
    return head + "." + sig


_NOW = 1795000000
_GOOD = {"iss": "https://login.shop.test", "aud": "shop-api", "sub": "rosa", "exp": _NOW + 900}
_TOKEN = _jwt(_GOOD, "s3cret")
_H, _P, _S = _TOKEN.split(".")
_FORGED = _H + "." + _seg(dict(_GOOD, sub="admin")) + "." + _S

_HTPASSWD = ["rosa:" + _sha("tea-time"), "sam:{PLAIN}pa:ss:word", "kim:" + _sha(""), "old:$apr1$abc$unsupportedhashformat"]

_LINT_OK = [
    "worker_processes auto;",
    "events {",
    "    worker_connections 1024;",
    "}",
    "http {",
    "    server {",
    "        listen 80;  # plain HTTP",
    "        return 301 https://$host$request_uri;",
    "    }",
    "}",
]

PROBLEMS = [
dict(
    id="nginx-cache-control-ttl",
    title="How Long May NGINX Cache This Response?",
    difficulty="Medium",
    pattern="Caching",
    entry="cache_ttl",
    description=r"""
When a proxied response arrives, NGINX decides whether to store it and for how many seconds. Write
`cache_ttl(status, headers, valid)` returning that number of seconds, where `0` means "do not cache".

- `status` is the upstream's status code.
- `headers` maps **lower-case** response header names to their values.
- `valid` holds the `proxy_cache_valid` settings: keys are status codes as strings (`"200"`) or `"any"`, values are
  seconds.

Apply these rules in order and stop at the first that decides:

1. A `set-cookie` header, or `vary` equal to `*`, means **0**.
2. `x-accel-expires`: its integer value is the answer (0 disables caching). Nothing below is consulted.
3. `cache-control`: split it on commas and ignore case and surrounding spaces.
   - `no-cache`, `no-store` or `private` → **0**;
   - otherwise `s-maxage=N` → `N`; if there is no `s-maxage`, `max-age=N` → `N`.
4. Otherwise use `valid`: the entry for this status, else the entry `"any"`, else **0**.

(The `Expires` header is left out of this problem.)

**Example:** `200`, `{"cache-control": "public, max-age=60"}`, `{"200": 600}` → `60`

**Example:** `200`, `{}`, `{"200": 600}` → `600`
""",
    starter='''def cache_ttl(status, headers, valid):
    # return seconds to cache, 0 for "do not cache"
    pass
''',
    solution='''def cache_ttl(status, headers, valid):
    if "set-cookie" in headers:
        return 0
    if headers.get("vary", "").strip() == "*":
        return 0
    if "x-accel-expires" in headers:
        return max(0, int(headers["x-accel-expires"]))
    parts = [p.strip().lower() for p in headers.get("cache-control", "").split(",") if p.strip()]
    if any(p in ("no-cache", "no-store", "private") for p in parts):
        return 0
    for name in ("s-maxage=", "max-age="):
        for p in parts:
            if p.startswith(name):
                return max(0, int(p[len(name):]))
    if str(status) in valid:
        return valid[str(status)]
    return valid.get("any", 0)
''',
    tests=[
        [200, {"cache-control": "public, max-age=60"}, {"200": 600}],
        [200, {}, {"200": 600}],
        [200, {"cache-control": "max-age=60, s-maxage=300"}, {"200": 600}],
        [200, {"cache-control": "Private, max-age=600"}, {"200": 600}],
        [200, {"cache-control": "no-store"}, {"any": 30}],
        [200, {"cache-control": "max-age=3600", "set-cookie": "sid=abc"}, {"200": 600}],
        [200, {"cache-control": "max-age=3600", "x-accel-expires": "5"}, {"200": 600}],
        [200, {"cache-control": "max-age=3600", "x-accel-expires": "0"}, {"200": 600}],
        [404, {}, {"200": 600, "404": 60}],
        [500, {}, {"200": 600, "404": 60}],
        [301, {}, {"200": 600, "any": 10}],
        [200, {"vary": "*", "cache-control": "max-age=60"}, {"200": 600}],
        [200, {"vary": "Accept-Encoding", "cache-control": "public"}, {"200": 600}],
        [200, {"cache-control": " S-MaxAge=120 ,must-revalidate"}, {}],
        [200, {"cache-control": "max-age=0"}, {"200": 600}],
    ],
    examples=2,
    wrong_solutions=[
        '''def cache_ttl(status, headers, valid):
    if str(status) in valid:
        return valid[str(status)]
    if "any" in valid:
        return valid["any"]
    for p in headers.get("cache-control", "").lower().split(","):
        if p.strip().startswith("max-age="):
            return int(p.strip()[8:])
    return 0
''',
        '''def cache_ttl(status, headers, valid):
    if "set-cookie" in headers or headers.get("vary", "").strip() == "*":
        return 0
    if "x-accel-expires" in headers:
        return max(0, int(headers["x-accel-expires"]))
    parts = [p.strip().lower() for p in headers.get("cache-control", "").split(",") if p.strip()]
    for p in parts:
        if p in ("no-cache", "no-store", "private"):
            return 0
        if p.startswith("max-age="):
            return int(p[8:])
        if p.startswith("s-maxage="):
            return int(p[9:])
    return valid.get(str(status), valid.get("any", 0))
''',
    ],
    guide=dict(
        prereqs="Lesson: *Proxy caching: zones, keys and validity*. Dictionaries and string splitting.",
        intuition="The application knows its data best, so its response headers outrank the proxy's blanket `proxy_cache_valid` rules. Among the headers there is a pecking order too: a private signal for the proxy (`X-Accel-Expires`), then the public `Cache-Control`. Anything that marks the response as personal vetoes caching outright.",
        hints=[
            "Deal with the vetoes first: `Set-Cookie` and `Vary: *`.",
            "Look for `s-maxage` across all parts before looking for `max-age`; their order inside the header must not matter.",
            "`proxy_cache_valid` is the fallback, not the first choice.",
        ],
        brute_force="No cheaper approach exists; the task is a fixed sequence of checks. The usual mistake is collapsing them, for example scanning the `Cache-Control` parts once and returning on the first of `max-age` or `s-maxage` seen.",
        approach="1. Vetoes → 0.\n2. `x-accel-expires` → its value.\n3. Parse `cache-control` into clean lower-case parts; forbidden words → 0; then `s-maxage`, then `max-age`.\n4. `valid[status]`, `valid['any']`, 0.\n\nDry run: status 200, `cache-control: max-age=60, s-maxage=300`, valid `{200: 600}`. No veto, no accel header. Parts: `max-age=60`, `s-maxage=300`. `s-maxage` is searched first → 300. The configured 600 is never used.",
        complexity="Time O(length of the Cache-Control header); space O(number of its parts).",
        pitfalls="Letting `proxy_cache_valid` win; preferring `max-age` because it is written first; case-sensitive matching; treating `max-age=0` as a positive lifetime; caching responses that set cookies.",
        follow_up="Add `proxy_ignore_headers`: a list of header names whose effect is switched off, which is how people cache responses whose applications send unhelpful headers.",
    ),
),
dict(
    id="nginx-cache-decision",
    title="Cache Status: MISS, HIT, EXPIRED, STALE, BYPASS",
    difficulty="Medium",
    pattern="Caching",
    entry="cache_sim",
    description=r"""
Simulate a proxy cache and report the cache status of every request.

`cache_sim(ttl, stale_on_error, requests)`:

- `ttl`: seconds a stored response stays fresh.
- `stale_on_error`: `True` when `proxy_cache_use_stale error timeout ...;` is configured.
- `requests`: a list in time order of `[time, method, scheme, host, uri, upstream_up, bypass]`.

For each request:

1. Only `GET` and `HEAD` are cacheable. Any other method → `"-"` (passed straight through, cache untouched).
2. The cache key is `scheme + host + uri`, with the **host lower-cased** and the URI (including any query string) kept
   exactly as given. `GET` and `HEAD` share entries.
3. If `bypass` is true (the `proxy_cache_bypass` condition holds): the response is fetched from the upstream. If the
   upstream is up, the answer is stored (replacing any entry, stamped with this time) and the status is `"BYPASS"`;
   if it is down → `"ERROR"`.
4. No entry for the key: upstream up → store, `"MISS"`; upstream down → `"ERROR"`.
5. Entry present and `time - stored_time < ttl` → `"HIT"`.
6. Entry present but expired: upstream up → store again, `"EXPIRED"`; upstream down → `"STALE"` if `stale_on_error`
   (the old entry is served and kept), otherwise `"ERROR"`.

Return the list of statuses.

**Example:** `ttl=10`, `stale_on_error=True`, three `GET https shop.test /p` requests at times 0, 5 and 12 with the
upstream up → `["MISS", "HIT", "EXPIRED"]`
""",
    starter='''def cache_sim(ttl, stale_on_error, requests):
    # return the cache status for each request
    pass
''',
    solution='''def cache_sim(ttl, stale_on_error, requests):
    stored = {}
    out = []
    for t, method, scheme, host, uri, upstream_up, bypass in requests:
        if method not in ("GET", "HEAD"):
            out.append("-")
            continue
        key = scheme + host.lower() + uri
        if bypass:
            if upstream_up:
                stored[key] = t
                out.append("BYPASS")
            else:
                out.append("ERROR")
        elif key not in stored:
            if upstream_up:
                stored[key] = t
                out.append("MISS")
            else:
                out.append("ERROR")
        elif t - stored[key] < ttl:
            out.append("HIT")
        elif upstream_up:
            stored[key] = t
            out.append("EXPIRED")
        else:
            out.append("STALE" if stale_on_error else "ERROR")
    return out
''',
    tests=[
        [10, True, [[0, "GET", "https", "shop.test", "/p", True, False], [5, "GET", "https", "shop.test", "/p", True, False], [12, "GET", "https", "shop.test", "/p", True, False]]],
        [10, True, [[0, "GET", "https", "shop.test", "/p", True, False], [20, "GET", "https", "shop.test", "/p", False, False], [25, "GET", "https", "shop.test", "/p", False, False], [30, "GET", "https", "shop.test", "/p", True, False], [31, "GET", "https", "shop.test", "/p", False, False]]],
        [10, False, [[0, "GET", "https", "shop.test", "/p", True, False], [20, "GET", "https", "shop.test", "/p", False, False], [21, "GET", "https", "shop.test", "/q", False, False]]],
        [10, True, [[0, "GET", "https", "shop.test", "/p?page=1", True, False], [1, "GET", "https", "shop.test", "/p?page=2", True, False], [2, "GET", "https", "shop.test", "/p?page=1", True, False], [3, "GET", "https", "shop.test", "/P?page=1", True, False]]],
        [10, True, [[0, "GET", "https", "Shop.Test", "/p", True, False], [1, "GET", "https", "shop.test", "/p", True, False], [2, "GET", "http", "shop.test", "/p", True, False]]],
        [10, True, [[0, "POST", "https", "shop.test", "/p", True, False], [1, "GET", "https", "shop.test", "/p", True, False], [2, "HEAD", "https", "shop.test", "/p", True, False], [3, "DELETE", "https", "shop.test", "/p", True, False], [4, "GET", "https", "shop.test", "/p", True, False]]],
        [10, True, [[0, "GET", "https", "a", "/", True, False], [5, "GET", "https", "a", "/", True, True], [14, "GET", "https", "a", "/", True, False], [16, "GET", "https", "a", "/", True, False]]],
        [10, True, [[0, "GET", "https", "a", "/", False, True], [1, "GET", "https", "a", "/", True, True], [2, "GET", "https", "a", "/", False, False]]],
        [10, True, []],
        [10, True, [[0, "GET", "https", "a", "/", True, False], [10, "GET", "https", "a", "/", True, False], [19, "GET", "https", "a", "/", True, False], [20, "GET", "https", "a", "/", True, False]]],
        [0, True, [[0, "GET", "https", "a", "/", True, False], [0, "GET", "https", "a", "/", True, False], [1, "GET", "https", "a", "/", False, False]]],
        [1, False, [[i, "GET", "https", "a", "/x%d" % (i % 3), i % 5 != 0, i % 7 == 0] for i in range(60)]],
    ],
    examples=1,
    wrong_solutions=[
        '''def cache_sim(ttl, stale_on_error, requests):
    stored = {}
    out = []
    for t, method, scheme, host, uri, upstream_up, bypass in requests:
        if method not in ("GET", "HEAD"):
            out.append("-")
            continue
        key = scheme + host.lower() + uri.split("?")[0]
        if bypass:
            if upstream_up:
                stored[key] = t
            out.append("BYPASS" if upstream_up else "ERROR")
        elif key not in stored:
            if upstream_up:
                stored[key] = t
            out.append("MISS" if upstream_up else "ERROR")
        elif t - stored[key] < ttl:
            out.append("HIT")
        elif upstream_up:
            stored[key] = t
            out.append("EXPIRED")
        else:
            out.append("STALE" if stale_on_error else "ERROR")
    return out
''',
        '''def cache_sim(ttl, stale_on_error, requests):
    stored = {}
    out = []
    for t, method, scheme, host, uri, upstream_up, bypass in requests:
        key = scheme + host.lower() + uri
        if bypass:
            out.append("BYPASS" if upstream_up else "ERROR")
        elif key not in stored:
            if upstream_up:
                stored[key] = t
            out.append("MISS" if upstream_up else "ERROR")
        elif t - stored[key] <= ttl:
            out.append("HIT")
        elif upstream_up:
            stored[key] = t
            out.append("EXPIRED")
        else:
            out.append("STALE" if stale_on_error else "ERROR")
    return out
''',
    ],
    guide=dict(
        prereqs="Lessons: *Proxy caching: zones, keys and validity* and *Bypass, purge, locking, stale content and slicing*.",
        intuition="A cache is a dictionary from key to stored response, plus a clock. Every status name answers two questions: was there an entry, and was it fresh? The extra cases are deliberate skips (BYPASS) and what to do when the upstream cannot refresh an expired entry (STALE or an error).",
        hints=[
            "Build the key exactly as specified: the query string is part of it and the host is case-insensitive.",
            "Store only the time at which the entry was saved; freshness is `time - stored < ttl`.",
            "A STALE answer does not refresh the entry. The next request finds it expired again.",
        ],
        brute_force="Keep a list of all past requests and search backwards for the last time the key was stored: O(n) per request. A dictionary makes it O(1).",
        approach="Write the branches in the order of the statement: method, bypass, no entry, fresh, expired with upstream, expired without.\n\nDry run with `ttl=10`, stale serving on: t=0 → MISS (stored at 0). t=20, upstream down → entry is 20 s old, expired, cannot refresh → STALE. t=25, still down → STALE. t=30, upstream back → EXPIRED, stored at 30. t=31, upstream down again → 1 s old → HIT; the outage is invisible.",
        complexity="Time O(number of requests); space O(number of distinct keys).",
        pitfalls="Dropping the query string from the key, which serves page 1 for page 2; caching POST; refreshing the timestamp on a STALE answer; using `<=` at the freshness boundary; not storing the response fetched during a bypass.",
        follow_up="Add `proxy_cache_min_uses N` (store only after N requests for a key) and `proxy_cache_lock` (concurrent misses for one key produce a single upstream fetch).",
    ),
),
dict(
    id="nginx-config-lint",
    title="A Small Configuration Linter",
    difficulty="Medium",
    pattern="Automation",
    entry="config_lint",
    description=r"""
Pipelines run cheap checks on configuration before it reaches a server. Write `config_lint(lines)` that inspects a
configuration given as a list of text lines and returns a list of findings `[line_number, code]`, with line numbers
starting at 1, sorted by line number and then by code.

The input follows a simplified layout: at most one directive per line; a block opens on a line that ends with `{`; a
block closes on a line that contains only `}`. Everything from a `#` to the end of a line is a comment. Blank lines
and comment-only lines are ignored.

Report:

| Code | When |
|---|---|
| `MISSING_SEMICOLON` | a directive line (not a block opener, not `}`) does not end with `;` |
| `UNEXPECTED_CLOSE` | a `}` appears when no block is open (it is then ignored for the depth count) |
| `UNCLOSED_BLOCK` | at the end, at least one block is still open; report it **once**, with the number of the last line |
| `URI_IN_REDIRECT` | a line whose first word is `return` or `rewrite` uses the variable `$uri` or `$document_uri` |

About the last rule: `$uri` holds the decoded path, so placing it in a redirect lets an attacker inject line breaks
into response headers. `$request_uri` is the safe choice and must not be flagged, nor may longer names that merely
start the same way, such as `$uri_suffix`.

**Example:** `["server {", "    listen 80", "    return 301 https://$host$uri;", "}"]`
→ `[[2, "MISSING_SEMICOLON"], [3, "URI_IN_REDIRECT"]]`
""",
    starter='''def config_lint(lines):
    # return sorted [line_number, code] findings
    pass
''',
    solution=r'''import re

def config_lint(lines):
    findings = []
    depth = 0
    for number, raw in enumerate(lines, 1):
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        if re.match(r"(return|rewrite)\b", line) and re.search(r"\$(uri|document_uri)(?![A-Za-z0-9_])", line):
            findings.append([number, "URI_IN_REDIRECT"])
        if line == "}":
            if depth == 0:
                findings.append([number, "UNEXPECTED_CLOSE"])
            else:
                depth -= 1
        elif line.endswith("{"):
            depth += 1
        elif not line.endswith(";"):
            findings.append([number, "MISSING_SEMICOLON"])
    if depth > 0:
        findings.append([len(lines), "UNCLOSED_BLOCK"])
    return sorted(findings)
''',
    tests=[
        [["server {", "    listen 80", "    return 301 https://$host$uri;", "}"]],
        [_LINT_OK],
        [[]],
        [["# only a comment", "", "   "]],
        [["http {", "    server {", "        listen 80;", "    }"]],
        [["}", "events {", "}", "}"]],
        [["server {", "    listen 80;   # no trailing semicolon here", "    root /srv/www  # missing", "}"]],
        [["location /old {", "    rewrite ^/old/(.*)$ /new/$1 permanent;", "    rewrite ^ https://shop.test$uri permanent", "}"]],
        [["location / {", "    return 302 /go?next=$uri_suffix;", "    return 302 https://a.test$document_uri;", "    return 302 https://a.test$request_uri;", "}"]],
        [["location / {", "    try_files $uri $uri/ /index.html;", "    add_header X-Path $uri;", "}"]],
        [["http {", "server {", "location / {", "return 200 ok;"]],
        [["server {", "    listen 80;", "}", "}", "server {", "    listen 81"]],
        [["worker_processes auto;"] + ["# filler %d" % i for i in range(300)] + ["events {", "worker_connections 1024", "}"]],
    ],
    examples=1,
    wrong_solutions=[
        r'''import re

def config_lint(lines):
    findings = []
    depth = 0
    for number, raw in enumerate(lines, 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if re.match(r"(return|rewrite)\b", line) and re.search(r"\$(uri|document_uri)(?![A-Za-z0-9_])", line):
            findings.append([number, "URI_IN_REDIRECT"])
        if line == "}":
            if depth == 0:
                findings.append([number, "UNEXPECTED_CLOSE"])
            else:
                depth -= 1
        elif line.endswith("{"):
            depth += 1
        elif not line.endswith(";"):
            findings.append([number, "MISSING_SEMICOLON"])
    if depth > 0:
        findings.append([len(lines), "UNCLOSED_BLOCK"])
    return sorted(findings)
''',
        r'''def config_lint(lines):
    findings = []
    depth = 0
    for number, raw in enumerate(lines, 1):
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        if line.split()[0] in ("return", "rewrite") and "$uri" in line:
            findings.append([number, "URI_IN_REDIRECT"])
        if line == "}":
            depth -= 1
        elif line.endswith("{"):
            depth += 1
        elif not line.endswith(";"):
            findings.append([number, "MISSING_SEMICOLON"])
    if depth != 0:
        findings.append([len(lines), "UNCLOSED_BLOCK"])
    return sorted(findings)
''',
    ],
    guide=dict(
        prereqs="Lesson: *Configuration management, templating and the API* (linting in a pipeline). String methods and a little regex.",
        intuition="A linter is a loop with a small amount of memory. Here the memory is one number, the nesting depth. Each line is cleaned of comments and then classified as opener, closer or directive; each class has its own check.",
        hints=[
            "Remove the comment first, then strip whitespace; only then test what the line ends with.",
            "Track depth with a counter: +1 for an opener, -1 for a closer, but never below zero.",
            "For the variable check, make sure the character after `$uri` is not a letter, digit or underscore.",
        ],
        brute_force="A real parser would tokenise the whole file, handling quotes and several directives per line. For the simplified layout that is unnecessary, and line-by-line classification is both shorter and easier to get right.",
        approach="1. For each line with its number: cut at `#`, strip, skip if empty.\n2. If it starts with `return` or `rewrite` and contains the risky variable, record `URI_IN_REDIRECT`.\n3. `}`: depth 0 → `UNEXPECTED_CLOSE`, else depth - 1. Ends with `{`: depth + 1. Otherwise, no `;` at the end → `MISSING_SEMICOLON`.\n4. After the loop, depth > 0 → `UNCLOSED_BLOCK` on the last line.\n5. Sort.\n\nDry run of the example: line 1 opens (depth 1). Line 2 `listen 80` lacks a semicolon. Line 3 is a `return` with `$uri` followed by `;` → flagged. Line 4 closes (depth 0).",
        complexity="Time O(total characters); space O(number of findings).",
        pitfalls="Testing the raw line so that a trailing comment hides a missing semicolon; flagging `$request_uri` or `$uri_suffix`; letting the depth go negative, which then cancels a later unclosed block; reporting `UNCLOSED_BLOCK` once per open block.",
        follow_up="Add a rule for `proxy_pass` with a hostname but no `resolver` in the file, and one for `add_header` inside a location when the enclosing server also has `add_header` lines.",
    ),
),
dict(
    id="nginx-basic-auth",
    title="HTTP Basic Authentication Against an htpasswd File",
    difficulty="Medium",
    pattern="Authentication",
    entry="basic_auth",
    description=r"""
Implement the check behind `auth_basic`. `basic_auth(header, htpasswd)` returns `[status, user]`: `[200, user]` when
the credentials are right, otherwise `[401, ""]`.

- `header` is the value of the `Authorization` request header, or `None`/empty when absent. A valid one looks like
  `Basic dXNlcjpwYXNz`: the word `Basic`, one space, then the **Base64** encoding of `user:password` (UTF-8). The
  password may itself contain colons; the user name ends at the **first** colon.
- `htpasswd` is a list of lines `user:stored`. The **first** line for the user decides. Two storage schemes are
  supported:
  - `{PLAIN}secret`: the password in clear text;
  - `{SHA}xxxx`: Base64 of the SHA-1 digest of the password.
  Any other scheme cannot be verified and means 401.

Return 401 for: a missing header, a scheme other than `Basic`, text that is not valid Base64 or not valid UTF-8, no
colon in the decoded text, an unknown user, or a wrong password. User names and passwords are case-sensitive.

**Example:** header for `rosa` / `tea-time`, file `["rosa:{SHA}...digest of tea-time..."]` → `[200, "rosa"]`
""",
    starter='''import base64, hashlib

def basic_auth(header, htpasswd):
    # return [200, user] or [401, ""]
    pass
''',
    solution='''import base64, hashlib

def basic_auth(header, htpasswd):
    if not header or not header.startswith("Basic "):
        return [401, ""]
    try:
        decoded = base64.b64decode(header[6:], validate=True).decode("utf-8")
    except Exception:
        return [401, ""]
    if ":" not in decoded:
        return [401, ""]
    user, password = decoded.split(":", 1)
    for line in htpasswd:
        name, _, stored = line.partition(":")
        if name != user:
            continue
        if stored.startswith("{PLAIN}"):
            ok = stored[7:] == password
        elif stored.startswith("{SHA}"):
            ok = stored[5:] == base64.b64encode(hashlib.sha1(password.encode("utf-8")).digest()).decode()
        else:
            ok = False
        return [200, user] if ok else [401, ""]
    return [401, ""]
''',
    tests=[
        [_basic("rosa", "tea-time"), _HTPASSWD],
        [_basic("rosa", "wrong"), _HTPASSWD],
        [None, _HTPASSWD],
        [_basic("sam", "pa:ss:word"), _HTPASSWD],
        [_basic("sam", "pa"), _HTPASSWD],
        [_basic("Rosa", "tea-time"), _HTPASSWD],
        [_basic("nobody", "tea-time"), _HTPASSWD],
        ["Bearer " + _basic("rosa", "tea-time")[6:], _HTPASSWD],
        ["Basic !!!not-base64!!!", _HTPASSWD],
        ["Basic " + _b64.b64encode(b"no-colon-here").decode(), _HTPASSWD],
        [_basic("kim", ""), _HTPASSWD],
        [_basic("old", "anything"), _HTPASSWD],
        [_basic("rosa", "second"), ["rosa:" + _sha("first"), "rosa:" + _sha("second")]],
        [_basic("rosa", "tea-time"), []],
        ["Basic " + _b64.b64encode(b"\xff\xfe:x").decode(), _HTPASSWD],
    ],
    examples=2,
    wrong_solutions=[
        '''import base64, hashlib

def basic_auth(header, htpasswd):
    if not header or not header.startswith("Basic "):
        return [401, ""]
    try:
        decoded = base64.b64decode(header[6:], validate=True).decode("utf-8")
    except Exception:
        return [401, ""]
    if ":" not in decoded:
        return [401, ""]
    user, password = decoded.rsplit(":", 1)
    for line in htpasswd:
        name, _, stored = line.partition(":")
        if name != user:
            continue
        if stored.startswith("{PLAIN}"):
            ok = stored[7:] == password
        elif stored.startswith("{SHA}"):
            ok = stored[5:] == base64.b64encode(hashlib.sha1(password.encode("utf-8")).digest()).decode()
        else:
            ok = False
        return [200, user] if ok else [401, ""]
    return [401, ""]
''',
        '''import base64, hashlib

def basic_auth(header, htpasswd):
    if not header or not header.startswith("Basic "):
        return [401, ""]
    try:
        decoded = base64.b64decode(header[6:]).decode("utf-8")
    except Exception:
        return [401, ""]
    if ":" not in decoded:
        return [401, ""]
    user, password = decoded.split(":", 1)
    digest = base64.b64encode(hashlib.sha1(password.encode("utf-8")).digest()).decode()
    for line in htpasswd:
        name, _, stored = line.partition(":")
        if name.lower() == user.lower() and stored in ("{PLAIN}" + password, "{SHA}" + digest):
            return [200, user]
    return [401, ""]
''',
    ],
    guide=dict(
        prereqs="Lesson: *HTTP basic authentication and auth subrequests*. The `base64` and `hashlib` modules.",
        intuition="Basic authentication is two encodings and a comparison. The browser packs `user:password` in Base64, which is a packaging format and not encryption. The server unpacks it, finds the user's line, transforms the offered password the same way the stored one was transformed, and compares.",
        hints=[
            "Reject early: no header, wrong scheme, undecodable text, no colon.",
            "Split on the first colon only: `decoded.split(\":\", 1)`.",
            "For `{SHA}`, hash the offered password with SHA-1, Base64-encode the raw digest, and compare strings.",
        ],
        brute_force="There is no meaningful slower variant; the file is scanned once. What matters is the order of the refusals and never raising an exception on hostile input.",
        approach="1. Validate the header and decode inside `try`.\n2. Split into user and password.\n3. Find the first line whose name equals the user.\n4. Verify according to the scheme prefix; unknown scheme fails.\n\nDry run: header `Basic c2FtOnBhOnNzOndvcmQ=` decodes to `sam:pa:ss:word`. First colon → user `sam`, password `pa:ss:word`. The line `sam:{PLAIN}pa:ss:word` matches → `[200, \"sam\"]`.",
        complexity="Time O(number of htpasswd lines); space O(1).",
        pitfalls="Splitting at the last colon; comparing names without regard to case; accepting when a later duplicate line matches; letting bad Base64 raise an exception; believing Base64 protects the password (it does not; TLS does).",
        follow_up="SHA-1 without a salt is weak. Add the salted `{SSHA}` scheme: Base64 of the SHA-1 of password plus salt, followed by the salt.",
    ),
),
dict(
    id="nginx-jwt-check",
    title="Validate a JSON Web Token (HS256)",
    difficulty="Medium",
    pattern="Authentication",
    entry="jwt_check",
    description=r"""
Write the validation a gateway performs on a JSON Web Token signed with HMAC-SHA256.

`jwt_check(token, secret, now, issuer, audience)` returns `[status, reason]`. A token is three **Base64URL** parts
joined by dots: `header.payload.signature`. Base64URL uses `-` and `_` and omits the `=` padding, so add padding back
before decoding. The header and payload are JSON objects.

Check in this order and stop at the first failure:

1. Not exactly three parts, or a part that cannot be decoded, or header/payload that are not JSON objects
   → `[401, "malformed"]`.
2. Header `alg` is not `"HS256"` → `[401, "algorithm not accepted"]`.
3. The signature is not the HMAC-SHA256 of the text `header.payload` (the two encoded parts with the dot, as received)
   under `secret` → `[401, "bad signature"]`.
4. Claim `exp` is missing or `exp <= now` → `[401, "expired"]`.
5. Claim `nbf` is present and `nbf > now` → `[401, "not yet valid"]`.
6. Claim `iss` differs from `issuer`, or `aud` differs from `audience` → `[401, "wrong issuer or audience"]`.

Otherwise return `[200, "ok"]`. `secret` is a string; use its UTF-8 bytes as the key.
""",
    starter='''import base64, hashlib, hmac, json

def jwt_check(token, secret, now, issuer, audience):
    # return [200, "ok"] or [401, reason]
    pass
''',
    solution='''import base64, hashlib, hmac, json

def jwt_check(token, secret, now, issuer, audience):
    def unb64(part):
        return base64.urlsafe_b64decode(part + "=" * (-len(part) % 4))
    parts = token.split(".")
    if len(parts) != 3:
        return [401, "malformed"]
    try:
        header = json.loads(unb64(parts[0]))
        claims = json.loads(unb64(parts[1]))
        signature = unb64(parts[2])
    except Exception:
        return [401, "malformed"]
    if not isinstance(header, dict) or not isinstance(claims, dict):
        return [401, "malformed"]
    if header.get("alg") != "HS256":
        return [401, "algorithm not accepted"]
    expected = hmac.new(secret.encode("utf-8"), (parts[0] + "." + parts[1]).encode("ascii"), hashlib.sha256).digest()
    if not hmac.compare_digest(expected, signature):
        return [401, "bad signature"]
    if "exp" not in claims or claims["exp"] <= now:
        return [401, "expired"]
    if "nbf" in claims and claims["nbf"] > now:
        return [401, "not yet valid"]
    if claims.get("iss") != issuer or claims.get("aud") != audience:
        return [401, "wrong issuer or audience"]
    return [200, "ok"]
''',
    tests=[
        [_TOKEN, "s3cret", _NOW, "https://login.shop.test", "shop-api"],
        [_TOKEN, "s3cret", _NOW + 900, "https://login.shop.test", "shop-api"],
        [_TOKEN, "s3cret", _NOW + 899, "https://login.shop.test", "shop-api"],
        [_TOKEN, "other-secret", _NOW, "https://login.shop.test", "shop-api"],
        [_FORGED, "s3cret", _NOW, "https://login.shop.test", "shop-api"],
        [_jwt(_GOOD, "s3cret", alg="none", sign=False), "s3cret", _NOW, "https://login.shop.test", "shop-api"],
        [_jwt(_GOOD, "s3cret", alg="HS512"), "s3cret", _NOW, "https://login.shop.test", "shop-api"],
        [_TOKEN, "s3cret", _NOW, "https://login.shop.test", "admin-api"],
        [_jwt(dict(_GOOD, nbf=_NOW + 60), "s3cret"), "s3cret", _NOW, "https://login.shop.test", "shop-api"],
        [_jwt(dict(_GOOD, nbf=_NOW), "s3cret"), "s3cret", _NOW, "https://login.shop.test", "shop-api"],
        [_jwt({"iss": "https://login.shop.test", "aud": "shop-api"}, "s3cret"), "s3cret", _NOW, "https://login.shop.test", "shop-api"],
        ["only.two", "s3cret", _NOW, "https://login.shop.test", "shop-api"],
        ["@@@.###.$$$", "s3cret", _NOW, "https://login.shop.test", "shop-api"],
        [_seg([1, 2]) + "." + _seg(_GOOD) + "." + _S, "s3cret", _NOW, "https://login.shop.test", "shop-api"],
        [_jwt(dict(_GOOD, exp=_NOW - 5, aud="other"), "wrong-key"), "s3cret", _NOW, "https://login.shop.test", "shop-api"],
    ],
    examples=2,
    wrong_solutions=[
        '''import base64, hashlib, hmac, json

def jwt_check(token, secret, now, issuer, audience):
    def unb64(part):
        return base64.urlsafe_b64decode(part + "=" * (-len(part) % 4))
    parts = token.split(".")
    if len(parts) != 3:
        return [401, "malformed"]
    try:
        header = json.loads(unb64(parts[0]))
        claims = json.loads(unb64(parts[1]))
    except Exception:
        return [401, "malformed"]
    if not isinstance(header, dict) or not isinstance(claims, dict):
        return [401, "malformed"]
    if header.get("alg") != "HS256":
        return [401, "algorithm not accepted"]
    if "exp" not in claims or claims["exp"] <= now:
        return [401, "expired"]
    if "nbf" in claims and claims["nbf"] > now:
        return [401, "not yet valid"]
    if claims.get("iss") != issuer or claims.get("aud") != audience:
        return [401, "wrong issuer or audience"]
    return [200, "ok"]
''',
        '''import base64, hashlib, hmac, json

def jwt_check(token, secret, now, issuer, audience):
    def unb64(part):
        return base64.urlsafe_b64decode(part + "=" * (-len(part) % 4))
    parts = token.split(".")
    if len(parts) != 3:
        return [401, "malformed"]
    try:
        header = json.loads(unb64(parts[0]))
        claims = json.loads(unb64(parts[1]))
        signature = unb64(parts[2])
    except Exception:
        return [401, "malformed"]
    if not isinstance(header, dict) or not isinstance(claims, dict):
        return [401, "malformed"]
    if header.get("alg") != "HS256":
        return [401, "algorithm not accepted"]
    expected = hmac.new(secret.encode("utf-8"), (parts[0] + "." + parts[1]).encode("ascii"), hashlib.sha256).digest()
    if not hmac.compare_digest(expected, signature):
        return [401, "bad signature"]
    if claims.get("exp", now + 1) < now:
        return [401, "expired"]
    if claims.get("iss") != issuer or claims.get("aud") != audience:
        return [401, "wrong issuer or audience"]
    return [200, "ok"]
''',
    ],
    guide=dict(
        prereqs="Lesson: *JSON Web Tokens and OpenID Connect*. The `base64`, `hmac`, `hashlib` and `json` modules.",
        intuition="A token is a signed note. Nothing written in it may be believed until the signature has been checked, because anyone can write a note. So the order is fixed: can it be parsed, is the algorithm the one we use, is the signature ours, and only then what do the claims say.",
        hints=[
            "Restore padding with `part + \"=\" * (-len(part) % 4)` before `urlsafe_b64decode`.",
            "Sign exactly the first two parts as they arrived, joined by a dot. Do not re-encode the JSON.",
            "Compare signatures with `hmac.compare_digest`, and treat a missing `exp` as expired.",
        ],
        brute_force="Checking the claims first and the signature last gives the same accept/reject decision for honest tokens but reports the wrong reason for forged ones and, worse, tempts code into trusting unverified claims. Keep the signature check ahead of every claim.",
        approach="1. Split into three; decode each inside `try`.\n2. Require `alg == HS256`. This also defeats the classic `alg: none` attack.\n3. Recompute the HMAC over `parts[0] + \".\" + parts[1]` and compare.\n4. `exp`, then `nbf`, then `iss` and `aud`.\n\nDry run for the forged token: header and payload decode fine and `alg` is HS256. The attacker changed `sub` to `admin`, so the bytes that were signed differ and the recomputed HMAC does not equal the old signature → `bad signature`.",
        complexity="Time O(length of the token); space O(length of the token).",
        pitfalls="Accepting `alg: none`; verifying after reading claims; forgetting Base64URL padding; `exp < now` instead of `<=`; accepting a token with no `exp`; comparing with `==` (timing leak).",
        follow_up="Support RS256: verification with a public key chosen by the header's `kid` from a key set, which is how tokens from an identity provider are checked.",
    ),
),
dict(
    id="nginx-access-control",
    title="allow, deny and satisfy",
    difficulty="Medium",
    pattern="Security",
    entry="access_check",
    description=r"""
Combine NGINX's address rules with authentication. `access_check(rules, client_ip, satisfy, auth_ok)` returns the
status code: `200`, `401` or `403`.

**Address rules.** `rules` is a list of `[action, target]` in order, where `action` is `"allow"` or `"deny"` and
`target` is `"all"`, an IPv4 address (`"203.0.113.5"`) or a network in CIDR form (`"10.0.0.0/8"`). The **first** rule
whose target contains the client address decides. The outcome is one of: *allowed*, *denied*, or *no rule matched*.

**Authentication.** `auth_ok` is `None` when no authentication is configured, otherwise `True` or `False` for whether
the client presented valid credentials.

**Combining them:**

- No authentication configured: denied → `403`, otherwise `200`.
- `satisfy` is `"all"` (the default): denied → `403`; otherwise credentials must be valid: `200` or `401`.
- `satisfy` is `"any"`: allowed by a matching `allow` rule → `200`; otherwise valid credentials → `200`; otherwise
  `401`. ("No rule matched" does not grant access here.)

A network `a.b.c.d/n` contains an address when their first `n` bits are equal. `/0` contains everything.

**Example:** `[["allow", "10.0.0.0/8"], ["deny", "all"]]`, `"10.2.3.4"`, `"all"`, `None` → `200`;
with `"203.0.113.9"` → `403`
""",
    starter='''def access_check(rules, client_ip, satisfy, auth_ok):
    # return 200, 401 or 403
    pass
''',
    solution='''def access_check(rules, client_ip, satisfy, auth_ok):
    def to_int(ip):
        a, b, c, d = (int(x) for x in ip.split("."))
        return (a << 24) | (b << 16) | (c << 8) | d

    ip = to_int(client_ip)
    verdict = None
    for action, target in rules:
        if target == "all":
            hit = True
        else:
            net, _, bits = target.partition("/")
            bits = int(bits) if bits else 32
            mask = ((1 << bits) - 1) << (32 - bits)
            hit = (ip & mask) == (to_int(net) & mask)
        if hit:
            verdict = action
            break
    if auth_ok is None:
        return 403 if verdict == "deny" else 200
    if satisfy == "any":
        return 200 if verdict == "allow" or auth_ok else 401
    if verdict == "deny":
        return 403
    return 200 if auth_ok else 401
''',
    tests=[
        [[["allow", "10.0.0.0/8"], ["deny", "all"]], "10.2.3.4", "all", None],
        [[["allow", "10.0.0.0/8"], ["deny", "all"]], "203.0.113.9", "all", None],
        [[["deny", "10.1.0.0/16"], ["allow", "10.0.0.0/8"], ["deny", "all"]], "10.1.200.3", "all", None],
        [[["deny", "10.1.0.0/16"], ["allow", "10.0.0.0/8"], ["deny", "all"]], "10.2.200.3", "all", None],
        [[], "198.51.100.1", "all", None],
        [[["deny", "198.51.100.1"]], "198.51.100.1", "all", None],
        [[["allow", "192.168.0.0/16"], ["deny", "all"]], "192.168.5.5", "all", False],
        [[["allow", "192.168.0.0/16"], ["deny", "all"]], "8.8.8.8", "all", True],
        [[["allow", "192.168.0.0/16"], ["deny", "all"]], "8.8.8.8", "any", True],
        [[["allow", "192.168.0.0/16"], ["deny", "all"]], "8.8.8.8", "any", False],
        [[["allow", "192.168.0.0/16"], ["deny", "all"]], "192.168.9.9", "any", False],
        [[], "8.8.8.8", "any", False],
        [[["allow", "172.16.0.0/12"], ["deny", "0.0.0.0/0"]], "172.31.255.255", "all", None],
        [[["allow", "172.16.0.0/12"], ["deny", "0.0.0.0/0"]], "172.32.0.0", "all", None],
        [[["allow", "203.0.113.128/25"], ["deny", "all"]], "203.0.113.127", "any", None],
    ],
    examples=2,
    wrong_solutions=[
        '''def access_check(rules, client_ip, satisfy, auth_ok):
    def to_int(ip):
        a, b, c, d = (int(x) for x in ip.split("."))
        return (a << 24) | (b << 16) | (c << 8) | d

    ip = to_int(client_ip)
    verdict = None
    for action, target in rules:
        if target == "all":
            hit = True
        else:
            net, _, bits = target.partition("/")
            bits = int(bits) if bits else 32
            mask = ((1 << bits) - 1) << (32 - bits)
            hit = (ip & mask) == (to_int(net) & mask)
        if hit:
            verdict = action
    if auth_ok is None:
        return 403 if verdict == "deny" else 200
    if satisfy == "any":
        return 200 if verdict == "allow" or auth_ok else 401
    if verdict == "deny":
        return 403
    return 200 if auth_ok else 401
''',
        '''def access_check(rules, client_ip, satisfy, auth_ok):
    verdict = None
    for action, target in rules:
        prefix = target.split("/")[0].rsplit(".0", 1)[0] if "/" in target else target
        if target == "all" or client_ip == target or ("/" in target and client_ip.startswith(prefix)):
            verdict = action
            break
    if auth_ok is None:
        return 403 if verdict == "deny" else 200
    if verdict == "deny":
        return 403
    return 200 if auth_ok else 401
''',
    ],
    guide=dict(
        prereqs="Lesson: *Access rules, satisfy, CORS and secure links*. Bit operations, or the `ipaddress` module.",
        intuition="The address rules work like a list of bouncers in a queue: the first one who recognises you decides, and the rest are never asked. `satisfy` then says whether the address check and the password check are both required (`all`) or whether either is enough (`any`).",
        hints=[
            "Convert an address to one 32-bit integer; then \"same network\" is a comparison after masking.",
            "The mask for `/n` has n one-bits at the top: `((1 << n) - 1) << (32 - n)`.",
            "Keep three outcomes for the address check, not two. Under `satisfy any` only an explicit allow grants access.",
        ],
        brute_force="Compare addresses as strings with `startswith`. It works for `/8`, `/16` and `/24` written on octet boundaries and fails for every other prefix length, such as `/12` or `/25`.",
        approach="1. Parse the client address to an integer.\n2. Walk the rules; on the first hit remember the action and stop.\n3. Branch on `auth_ok is None`, then on `satisfy`.\n\nDry run: rules `allow 192.168.0.0/16; deny all;`, client `8.8.8.8`, `satisfy any`, valid credentials. The first rule does not contain the address; `deny all` does → denied. Under `any`, the address did not grant access, but the credentials do → 200. With `satisfy all` the same request is 403.",
        complexity="Time O(number of rules); space O(1).",
        pitfalls="Letting the last matching rule win; string-prefix matching of networks; returning 403 instead of 401 when credentials would have been enough; treating \"no rule matched\" as an allow under `satisfy any`; a shift by 32 for `/0`.",
        follow_up="Support IPv6 targets and the `geo` block's \"most specific network wins\" rule, which differs from first match.",
    ),
),
dict(
    id="nginx-cors-preflight",
    title="CORS: Preflight and Response Headers",
    difficulty="Medium",
    pattern="Security",
    entry="cors",
    description=r"""
Browsers ask permission before letting a page on one origin call an API on another. Implement the decision a typical
NGINX CORS configuration makes.

`cors(method, origin, acr_method, allowed_origins, allowed_methods)` returns `[status, headers]`:

- `method`: the request method.
- `origin`: the `Origin` request header, or `""` if absent.
- `acr_method`: the `Access-Control-Request-Method` request header, or `""`.
- `allowed_origins`: the exact origins that may call the API.
- `allowed_methods`: the methods to advertise.

`status` is `204` when NGINX answers the request itself and `0` when the request is passed to the application.
`headers` is a dictionary of response headers NGINX adds.

Rules:

1. No `Origin` header → `[0, {}]`. It is not a cross-origin request.
2. A **preflight** is a request with method `OPTIONS` **and** a non-empty `acr_method`. Preflights are answered with
   status `204`; everything else has status `0`.
3. Whenever `Origin` is present, add `"Vary": "Origin"`.
4. If the origin is in `allowed_origins` (exact, case-sensitive comparison), add
   `"Access-Control-Allow-Origin": origin`. For a preflight also add
   `"Access-Control-Allow-Methods"`: the allowed methods joined with `", "`, and `"Access-Control-Max-Age": "86400"`.
5. If the origin is not allowed, add nothing more. The browser will block the call.

**Example:** `"OPTIONS"`, `"https://app.shop.test"`, `"POST"`, `["https://app.shop.test"]`, `["GET", "POST"]` →
`[204, {"Vary": "Origin", "Access-Control-Allow-Origin": "https://app.shop.test", "Access-Control-Allow-Methods": "GET, POST", "Access-Control-Max-Age": "86400"}]`
""",
    starter='''def cors(method, origin, acr_method, allowed_origins, allowed_methods):
    # return [status, headers]
    pass
''',
    solution='''def cors(method, origin, acr_method, allowed_origins, allowed_methods):
    if origin == "":
        return [0, {}]
    preflight = method == "OPTIONS" and acr_method != ""
    headers = {"Vary": "Origin"}
    if origin in allowed_origins:
        headers["Access-Control-Allow-Origin"] = origin
        if preflight:
            headers["Access-Control-Allow-Methods"] = ", ".join(allowed_methods)
            headers["Access-Control-Max-Age"] = "86400"
    return [204 if preflight else 0, headers]
''',
    tests=[
        ["OPTIONS", "https://app.shop.test", "POST", ["https://app.shop.test"], ["GET", "POST"]],
        ["GET", "https://app.shop.test", "", ["https://app.shop.test"], ["GET", "POST"]],
        ["GET", "", "", ["https://app.shop.test"], ["GET", "POST"]],
        ["OPTIONS", "", "", ["https://app.shop.test"], ["GET", "POST"]],
        ["OPTIONS", "https://evil.example", "DELETE", ["https://app.shop.test"], ["GET", "POST"]],
        ["POST", "https://evil.example", "", ["https://app.shop.test"], ["GET", "POST"]],
        ["OPTIONS", "https://app.shop.test", "", ["https://app.shop.test"], ["GET", "POST"]],
        ["GET", "https://APP.shop.test", "", ["https://app.shop.test"], ["GET"]],
        ["GET", "http://app.shop.test", "", ["https://app.shop.test"], ["GET"]],
        ["GET", "https://app.shop.test.evil.example", "", ["https://app.shop.test"], ["GET"]],
        ["OPTIONS", "https://admin.shop.test", "PUT", ["https://app.shop.test", "https://admin.shop.test"], ["GET", "PUT", "DELETE"]],
        ["DELETE", "https://admin.shop.test", "", ["https://app.shop.test", "https://admin.shop.test"], ["GET", "PUT", "DELETE"]],
        ["OPTIONS", "https://app.shop.test", "POST", [], ["GET"]],
    ],
    examples=1,
    wrong_solutions=[
        '''def cors(method, origin, acr_method, allowed_origins, allowed_methods):
    if origin == "":
        return [0, {}]
    preflight = method == "OPTIONS" and acr_method != ""
    headers = {"Vary": "Origin", "Access-Control-Allow-Origin": origin}
    if preflight:
        headers["Access-Control-Allow-Methods"] = ", ".join(allowed_methods)
        headers["Access-Control-Max-Age"] = "86400"
    return [204 if preflight else 0, headers]
''',
        '''def cors(method, origin, acr_method, allowed_origins, allowed_methods):
    if origin == "":
        return [0, {}]
    preflight = method == "OPTIONS"
    headers = {"Vary": "Origin"}
    if any(origin.startswith(o) for o in allowed_origins):
        headers["Access-Control-Allow-Origin"] = origin
        if preflight:
            headers["Access-Control-Allow-Methods"] = ", ".join(allowed_methods)
            headers["Access-Control-Max-Age"] = "86400"
    return [204 if preflight else 0, headers]
''',
    ],
    guide=dict(
        prereqs="Lesson: *Access rules, satisfy, CORS and secure links*. Dictionaries.",
        intuition="CORS is enforced by the browser, not the server. The server's whole job is to state, in response headers, which origins it trusts. A preflight is the browser asking in advance; the reply needs no body, only the permission headers. A server that echoes back any origin has switched the protection off.",
        hints=[
            "Start with the non-CORS case: no `Origin`, no headers, pass through.",
            "Compute `preflight` once and use it for both the status and the extra headers.",
            "Compare the origin with `in allowed_origins`. Prefix or suffix matching lets look-alike domains through.",
        ],
        brute_force="Not applicable; the function is constant time. The naive version returns `Access-Control-Allow-Origin` with whatever origin was sent, which makes every site on the internet an allowed caller.",
        approach="1. Empty origin → `[0, {}]`.\n2. `preflight = method == OPTIONS and acr_method`.\n3. `headers = {Vary: Origin}`.\n4. Allowed → add the origin; if preflight add methods and max age.\n5. Status 204 for preflight, else 0.\n\nDry run: `OPTIONS` from `https://evil.example` asking for `DELETE`. It is a preflight, so status 204. The origin is not allowed, so only `Vary: Origin` is returned and the browser refuses to send the real request.",
        complexity="Time O(number of allowed origins); space O(1).",
        pitfalls="Reflecting any origin; `startswith` matching, fooled by `https://app.shop.test.evil.example`; ignoring scheme or case differences, which make a different origin; treating every `OPTIONS` as a preflight; omitting `Vary: Origin`, which lets a shared cache serve one origin's permission to another.",
        follow_up="Add credentialed requests: `Access-Control-Allow-Credentials: true`, which browsers accept only with an explicit origin, never with `*`, and `Access-Control-Allow-Headers` echoing the requested headers from an allow-list.",
    ),
),
dict(
    id="nginx-https-hsts",
    title="HTTPS Redirects, the Canonical Host and HSTS",
    difficulty="Easy",
    pattern="Security",
    entry="https_redirect",
    description=r"""
A site must be reachable only as `https://CANONICAL`. Decide what NGINX answers.

`https_redirect(scheme, host, uri, forwarded_proto, canonical, hsts_max_age)` returns `[status, location, hsts]`:

- `scheme`: `"http"` or `"https"`, as NGINX itself sees the connection.
- `host`: the `Host` header; it may be in any letter case and may carry a `:port`.
- `uri`: the request URI including any query string.
- `forwarded_proto`: the `X-Forwarded-Proto` header set by a trusted load balancer that terminates TLS, or `""` when
  there is no such balancer. When non-empty it **replaces** `scheme` as the scheme the client used.
- `canonical`: the one allowed host name, lower-case, without a port.
- `hsts_max_age`: seconds for the `Strict-Transport-Security` header; `0` means the header is not used.

Rules:

1. If the client's scheme is not `https`: `[301, "https://" + canonical + uri, ""]`. HSTS is never sent over plain
   HTTP.
2. Otherwise, if the host (lower-cased, port removed) is not the canonical one:
   `[301, "https://" + canonical + uri, hsts]`.
3. Otherwise `[200, "", hsts]`.

`hsts` is `"max-age=N"` when `hsts_max_age > 0`, else `""`.

**Example:** `"http"`, `"www.shop.test"`, `"/tea?x=1"`, `""`, `"shop.test"`, `300`
→ `[301, "https://shop.test/tea?x=1", ""]`
""",
    starter='''def https_redirect(scheme, host, uri, forwarded_proto, canonical, hsts_max_age):
    # return [status, location, hsts]
    pass
''',
    solution='''def https_redirect(scheme, host, uri, forwarded_proto, canonical, hsts_max_age):
    client_scheme = forwarded_proto or scheme
    name = host.lower().split(":")[0]
    hsts = "max-age=%d" % hsts_max_age if hsts_max_age > 0 else ""
    if client_scheme != "https":
        return [301, "https://" + canonical + uri, ""]
    if name != canonical:
        return [301, "https://" + canonical + uri, hsts]
    return [200, "", hsts]
''',
    tests=[
        ["http", "www.shop.test", "/tea?x=1", "", "shop.test", 300],
        ["https", "shop.test", "/", "", "shop.test", 300],
        ["https", "www.shop.test", "/tea", "", "shop.test", 31536000],
        ["http", "shop.test", "/", "", "shop.test", 300],
        ["http", "shop.test", "/cart", "https", "shop.test", 300],
        ["http", "shop.test", "/cart", "http", "shop.test", 300],
        ["https", "shop.test", "/cart", "http", "shop.test", 300],
        ["https", "SHOP.TEST:443", "/a", "", "shop.test", 60],
        ["https", "shop.test", "/a", "", "shop.test", 0],
        ["https", "other.test", "/a?b=c&d=e", "", "shop.test", 0],
        ["http", "WWW.Shop.Test:8080", "/", "https", "shop.test", 86400],
        ["http", "shop.test", "", "", "shop.test", 300],
    ],
    examples=1,
    wrong_solutions=[
        '''def https_redirect(scheme, host, uri, forwarded_proto, canonical, hsts_max_age):
    name = host.lower().split(":")[0]
    hsts = "max-age=%d" % hsts_max_age if hsts_max_age > 0 else ""
    if scheme != "https":
        return [301, "https://" + canonical + uri, ""]
    if name != canonical:
        return [301, "https://" + canonical + uri, hsts]
    return [200, "", hsts]
''',
        '''def https_redirect(scheme, host, uri, forwarded_proto, canonical, hsts_max_age):
    client_scheme = forwarded_proto or scheme
    name = host.lower().split(":")[0]
    hsts = "max-age=%d" % hsts_max_age if hsts_max_age > 0 else ""
    if client_scheme != "https":
        return [301, "https://" + name + uri, hsts]
    if name != canonical:
        return [301, "https://" + canonical + uri, hsts]
    return [200, "", hsts]
''',
    ],
    guide=dict(
        prereqs="Lesson: *TLS, HTTPS redirects, HSTS and upstream encryption*. Basic string handling.",
        intuition="There are four ways to type the address and only one is wanted. Every other form gets a single permanent redirect straight to the wanted one. The only subtlety is knowing which scheme the *client* used when a balancer in front has already removed the encryption.",
        hints=[
            "Work out the client's scheme first: the forwarded header when present, otherwise NGINX's own.",
            "Normalise the host before comparing: lower-case, port removed.",
            "Redirect directly to the canonical HTTPS URL in both cases, so nobody needs two hops.",
        ],
        brute_force="Redirect in two steps, first to HTTPS on the same host and then to the canonical host. It ends in the right place but costs an extra round trip, and needs a certificate for every alias.",
        approach="1. `client_scheme = forwarded_proto or scheme`.\n2. `name = host.lower().split(':')[0]`.\n3. Build the HSTS string.\n4. Not HTTPS → 301 without HSTS. Wrong host → 301 with HSTS. Else 200 with HSTS.\n\nDry run: NGINX sees `http` (the balancer forwards plain HTTP) and `X-Forwarded-Proto: https`, host `shop.test`. The client's scheme is `https` and the host is canonical → `[200, \"\", \"max-age=300\"]`. Had the header been ignored, the answer would be a redirect to the URL the client is already on, repeated for ever.",
        complexity="Time and space O(length of the URL).",
        pitfalls="Ignoring `X-Forwarded-Proto` behind a TLS-terminating balancer, which causes a redirect loop; sending HSTS over HTTP, where browsers ignore it; redirecting to the same host over HTTPS first; dropping the query string; comparing hosts case-sensitively.",
        follow_up="Add `includeSubDomains` and `preload` options to the HSTS value, and refuse `preload` unless `max-age` is at least one year, as the preload list requires.",
    ),
),
]
