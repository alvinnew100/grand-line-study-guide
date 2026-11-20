import hashlib as _hl

PROBLEMS = [
dict(
    id="api-status-class",
    title="Classify an HTTP Status Code",
    difficulty="Easy",
    pattern="HTTP Fundamentals",
    entry="describeStatus",
    description=r"""
Client libraries, load balancers and retry middleware all start by asking the same question about a
response: *what kind of status is this, and is it worth retrying?*

Write `describeStatus(code)` that returns a dict with two keys:

- `"class"` — one of `"informational"` (1xx), `"success"` (2xx), `"redirection"` (3xx),
  `"client_error"` (4xx), `"server_error"` (5xx), or `"invalid"` if `code` is outside `100..599`.
- `"retryable"` — `True` only for the codes a well-behaved client may safely retry after a delay:
  `408` (Request Timeout), `425` (Too Early), `429` (Too Many Requests), `500`, `502`, `503`, `504`.
  Everything else (including invalid codes) is `False`.

**Example:** `describeStatus(404)` → `{"class": "client_error", "retryable": False}`

**Example:** `describeStatus(503)` → `{"class": "server_error", "retryable": True}`

**Example:** `describeStatus(99)` → `{"class": "invalid", "retryable": False}`
""",
    starter='''def describeStatus(code: int) -> dict:
    pass
''',
    solution='''RETRYABLE = {408, 425, 429, 500, 502, 503, 504}
CLASSES = {1: "informational", 2: "success", 3: "redirection", 4: "client_error", 5: "server_error"}

def describeStatus(code):
    if not (100 <= code <= 599):
        return {"class": "invalid", "retryable": False}
    return {"class": CLASSES[code // 100], "retryable": code in RETRYABLE}
''',
    tests=[[200], [404], [503], [99], [100], [301], [429], [501], [599], [600], [0], [408], [422], [204]],
    wrong_solutions=[
        '''def describeStatus(code):
    c = {1: "informational", 2: "success", 3: "redirection", 4: "client_error", 5: "server_error"}.get(code // 100, "invalid")
    return {"class": c, "retryable": code >= 500}
''',
    ],
    guide=dict(
        prereqs="Status code classes (lesson *HTTP: methods, status codes and headers*).",
        intuition="The first digit of a status code *is* its class: integer-divide by 100. Retryability is a "
                  "small, explicit allow-list — never 'all 5xx', because `501 Not Implemented` will never succeed "
                  "no matter how often you retry.",
        hints=["`code // 100` gives the leading digit.",
               "Check the valid range first: `600 // 100 == 6`, and `99 // 100 == 0`.",
               "Keep retryable codes in a set for O(1) membership."],
        brute_force="A long `if/elif` chain over ranges works fine; it is just harder to read.",
        approach="1. If `code` is not in `100..599`, return the invalid dict.\n"
                 "2. Look up `code // 100` in a dict of class names.\n"
                 "3. `retryable = code in RETRYABLE`.",
        complexity="O(1) time and space.",
        pitfalls="- Treating every 5xx as retryable (501, 505 are permanent).\n"
                 "- Forgetting 408/429, which are 4xx but transient.\n"
                 "- Edge values 100, 599, 600, 99.",
        follow_up="Real clients also check the method: only retry non-idempotent methods like POST when the "
                  "request carries an idempotency key.",
    ),
),
dict(
    id="api-etag-check",
    title="ETag and If-None-Match",
    difficulty="Medium",
    pattern="HTTP Caching",
    entry="conditionalGet",
    description=r"""
Implement the server side of an HTTP conditional `GET`.

`conditionalGet(body, if_none_match)` receives the response body you are about to send (a string) and the
value of the request's `If-None-Match` header (a string, or `None` if the header is absent).

1. Compute the strong ETag: the first 16 hex characters of `sha256(body.encode("utf-8"))`, wrapped in
   double quotes, e.g. `"9f86d081884c7d65"` (the quotes are part of the value).
2. Parse `If-None-Match`. It is either `*` or a comma-separated list of entity tags, each possibly
   prefixed with `W/` (a weak tag). Whitespace around items is ignored. For `GET`, comparison is **weak**:
   `W/"abc"` matches `"abc"`.
3. If the header is `*` or any listed tag matches the ETag, return `[304, etag, ""]` (no body).
   Otherwise return `[200, etag, body]`.

**Example:** `conditionalGet("test", None)` → `[200, '"9f86d081884c7d65"', "test"]`

**Example:** `conditionalGet("test", 'W/"9f86d081884c7d65"')` → `[304, '"9f86d081884c7d65"', ""]`
""",
    starter='''import hashlib

def conditionalGet(body: str, if_none_match: str | None) -> list:
    pass
''',
    solution='''import hashlib

def conditionalGet(body, if_none_match):
    etag = '"' + hashlib.sha256(body.encode("utf-8")).hexdigest()[:16] + '"'
    if if_none_match is not None:
        raw = if_none_match.strip()
        if raw == "*":
            return [304, etag, ""]
        for item in raw.split(","):
            tag = item.strip()
            if tag.startswith("W/"):
                tag = tag[2:]
            if tag == etag:
                return [304, etag, ""]
    return [200, etag, body]
''',
    tests=[
        ["test", None],
        ["test", 'W/"9f86d081884c7d65"'],
        ["test", '"9f86d081884c7d65"'],
        ["test", '"nope", "9f86d081884c7d65"'],
        ["test", '"nope"'],
        ["hello", "*"],
        ["", None],
        ["", '"' + _hl.sha256(b"").hexdigest()[:16] + '"'],
        ["héllo wörld", '"' + _hl.sha256("héllo wörld".encode()).hexdigest()[:16] + '"'],
        ["test", '  W/"x" ,   W/"9f86d081884c7d65"  '],
        ["test", "9f86d081884c7d65"],
        ["test", ""],
        ['{"id": 1}', 'W/"' + _hl.sha256(b'{"id": 1}').hexdigest()[:16] + '"'],
    ],
    wrong_solutions=[
        '''import hashlib
def conditionalGet(body, inm):
    etag = '"' + hashlib.sha256(body.encode()).hexdigest()[:16] + '"'
    if inm == etag or inm == "*":
        return [304, etag, ""]
    return [200, etag, body]
''',
        '''import hashlib
def conditionalGet(body, inm):
    etag = '"' + hashlib.sha256(body.encode()).hexdigest()[:16] + '"'
    if inm and etag.strip('"') in inm:
        return [304, etag, ""]
    return [200, etag, body]
''',
    ],
    guide=dict(
        prereqs="Headers and caching (lesson *HTTP: methods, status codes and headers*).",
        intuition="An ETag is a fingerprint of the representation. The client says 'I already have version X'; if "
                  "the fingerprint still matches you save bandwidth by answering `304 Not Modified` with an empty body.",
        hints=["Build the ETag string first, including the surrounding quotes.",
               "Split the header on commas, strip whitespace, drop a leading `W/`.",
               "`*` matches anything; an unquoted value is not a valid tag and must not match."],
        brute_force="Substring search (`etag in header`) looks like it works but gives false positives — for example "
                    "an unquoted value or a longer tag that contains yours.",
        approach="1. `etag = '\"' + sha256(body).hexdigest()[:16] + '\"'`.\n"
                 "2. If header is `None` → 200.\n"
                 "3. If stripped header is `*` → 304.\n"
                 "4. For each comma-separated item: strip, remove `W/`, compare with `etag` exactly.\n"
                 "5. Any match → `[304, etag, \"\"]`, else `[200, etag, body]`.",
        complexity="O(len(body) + len(header)).",
        pitfalls="- Forgetting the quotes are part of the tag.\n- Strong comparison for GET (weak tags must match).\n"
                 "- An empty header string is present but matches nothing.",
        follow_up="`If-Match` (used for optimistic concurrency on PUT/PATCH) uses *strong* comparison and answers "
                  "`412 Precondition Failed` on mismatch.",
    ),
),
dict(
    id="api-route-match",
    title="Match a Route Template",
    difficulty="Medium",
    pattern="Routing",
    entry="matchRoute",
    description=r"""
FastAPI (via Starlette) turns a path template like `/users/{user_id}/posts/{post_id:int}` into a matcher.
Build a small version of it.

`matchRoute(template, path)` returns a dict of extracted parameters if `path` matches, else `None`.

Rules (both strings start with `/`; split them on `/`):

- A **literal** segment must equal the path segment exactly (case-sensitive).
- `{name}` matches any **non-empty** segment and captures it as a string.
- `{name:int}` matches a segment of one or more ASCII digits `0-9` and captures it as an `int`.
- `{name:path}` may only be the **last** template segment; it captures **all remaining** path text
  (slashes included, possibly empty) as a string.
- Without a `:path` parameter, the number of segments must be equal. Trailing slashes are significant:
  `/items/` does not match `/items`.

**Example:** `matchRoute("/users/{uid}/posts/{pid:int}", "/users/ann/posts/42")` → `{"uid": "ann", "pid": 42}`

**Example:** `matchRoute("/files/{fp:path}", "/files/a/b/c.txt")` → `{"fp": "a/b/c.txt"}`

**Example:** `matchRoute("/users/{uid}", "/users/")` → `None`
""",
    starter='''def matchRoute(template: str, path: str) -> dict | None:
    pass
''',
    solution='''def matchRoute(template, path):
    t = template.split("/")
    p = path.split("/")
    out = {}
    for i, seg in enumerate(t):
        if seg.startswith("{") and seg.endswith("}"):
            name, _, conv = seg[1:-1].partition(":")
            if conv == "path":
                if i > len(p):
                    return None
                out[name] = "/".join(p[i:])
                return out
            if i >= len(p):
                return None
            val = p[i]
            if conv == "int":
                if not val or not all("0" <= c <= "9" for c in val):
                    return None
                out[name] = int(val)
            else:
                if val == "":
                    return None
                out[name] = val
        else:
            if i >= len(p) or p[i] != seg:
                return None
    if len(p) != len(t):
        return None
    return out
''',
    tests=[
        ["/users/{uid}/posts/{pid:int}", "/users/ann/posts/42"],
        ["/files/{fp:path}", "/files/a/b/c.txt"],
        ["/users/{uid}", "/users/"],
        ["/users/{uid}", "/users/bob"],
        ["/items/{id:int}", "/items/abc"],
        ["/items/{id:int}", "/items/007"],
        ["/items/{id:int}", "/items/-5"],
        ["/items", "/items/"],
        ["/items", "/items"],
        ["/", "/"],
        ["/files/{fp:path}", "/files/"],
        ["/users/{uid}", "/users/bob/extra"],
        ["/Users/{uid}", "/users/bob"],
        ["/a/{x}/b/{y}", "/a/1/c/2"],
        ["/v1/models/{name}/versions/{ver:int}", "/v1/models/resnet/versions/3"],
        ["/static/{rest:path}", "/static"],
    ],
    wrong_solutions=[
        '''import re
def matchRoute(template, path):
    rx = "^" + re.sub(r"\\{(\\w+)(?::\\w+)?\\}", r"(?P<\\1>[^/]+)", template) + "$"
    m = re.match(rx, path)
    return m.groupdict() if m else None
''',
        '''def matchRoute(template, path):
    t, p = template.strip("/").split("/"), path.strip("/").split("/")
    if len(t) != len(p): return None
    out = {}
    for a, b in zip(t, p):
        if a.startswith("{"):
            n, _, c = a[1:-1].partition(":")
            if c == "int":
                if not b.isdigit(): return None
                out[n] = int(b)
            else: out[n] = b
        elif a != b: return None
    return out
''',
    ],
    guide=dict(
        prereqs="Path parameters (lesson *Your first FastAPI app*).",
        intuition="Routing is just segment-by-segment comparison. Each template segment is either a literal "
                  "(must be equal) or a placeholder (captures, maybe converts). The `path` converter is the only "
                  "one allowed to eat slashes, so it must end the template.",
        hints=["Split both strings on `/` — the leading empty string lines up on both sides.",
               "Parse a placeholder with `seg[1:-1].partition(':')` to get name and converter.",
               "When you see `:path`, join the rest of the path segments with `/` and return immediately.",
               "After the loop, check the segment counts are equal."],
        brute_force="Compile the template to a regular expression (that is what Starlette does). It is a fine "
                    "approach as long as you translate converters and anchors correctly.",
        approach="Walk template segments with index `i`:\n"
                 "- placeholder `path` → capture `'/'.join(p[i:])`, return.\n"
                 "- placeholder `int` → segment must be all digits → `int(seg)`.\n"
                 "- placeholder `str` → segment non-empty.\n"
                 "- literal → equal.\n"
                 "Finally require `len(p) == len(t)`.\n\n"
                 "Dry run `/files/{fp:path}` vs `/files/`: segments `['', 'files', '{fp:path}']` vs "
                 "`['', 'files', '']` → at i=2 capture `''` → `{'fp': ''}`.",
        complexity="O(len(template) + len(path)).",
        pitfalls="- `str.isdigit()` accepts Unicode digits like `'²'`; check `'0' <= c <= '9'`.\n"
                 "- Stripping slashes hides the trailing-slash difference.\n"
                 "- `-5` is not matched by `int` (Starlette's int converter is `[0-9]+`).",
        follow_up="In FastAPI, route *order* matters: `/users/me` must be declared before `/users/{uid}` "
                  "or the placeholder wins.",
    ),
),
dict(
    id="api-query-parse",
    title="Query String Parser with Type Coercion",
    difficulty="Medium",
    pattern="Request Parsing",
    entry="parseQuery",
    description=r"""
When you declare `def list_items(limit: int = 10, tags: list[str] = Query([]))`, FastAPI parses the raw
query string and converts each value to the declared type. Implement the core of that.

`parseQuery(query, schema)`:

- `query` is the raw string after `?` (no leading `?`), e.g. `"limit=5&tags=a&tags=b&q=hello+world"`.
  Pairs are separated by `&`; split each pair on the **first** `=` (a pair without `=` has value `""`);
  skip empty pairs. Decode names and values with `urllib.parse.unquote_plus` (`+` → space, `%XX` decoding).
- `schema` maps a parameter name to a type: `"str"`, `"int"`, `"float"`, `"bool"`, `"list[str]"`, `"list[int]"`.
  Names not in the schema are ignored; parameters absent from the query are omitted from the result.
- Scalars: if the parameter appears more than once, the **last** occurrence wins. Lists collect every
  occurrence in order.
- `int` uses `int(value)`; `float` uses `float(value)`; `bool` accepts (case-insensitive)
  `true/1/yes/on` → `True` and `false/0/no/off` → `False`.
- Any value that fails conversion makes that parameter an error (it is left out of `values`).

Return `{"values": {...}, "errors": sorted list of failing names}`.

**Example:** `parseQuery("limit=5&tags=a&tags=b", {"limit": "int", "tags": "list[str]"})`
→ `{"values": {"limit": 5, "tags": ["a", "b"]}, "errors": []}`
""",
    starter='''from urllib.parse import unquote_plus

def parseQuery(query: str, schema: dict) -> dict:
    pass
''',
    solution='''from urllib.parse import unquote_plus

TRUE = {"true", "1", "yes", "on"}
FALSE = {"false", "0", "no", "off"}

def _conv(kind, v):
    if kind == "str":
        return v
    if kind == "int":
        return int(v)
    if kind == "float":
        return float(v)
    if kind == "bool":
        lv = v.lower()
        if lv in TRUE:
            return True
        if lv in FALSE:
            return False
        raise ValueError(v)
    raise ValueError(kind)

def parseQuery(query, schema):
    raw = {}
    for pair in query.split("&"):
        if not pair:
            continue
        k, _, v = pair.partition("=")
        raw.setdefault(unquote_plus(k), []).append(unquote_plus(v))
    values, errors = {}, []
    for name, kind in schema.items():
        if name not in raw:
            continue
        try:
            if kind.startswith("list["):
                inner = kind[5:-1]
                values[name] = [_conv(inner, v) for v in raw[name]]
            else:
                values[name] = _conv(kind, raw[name][-1])
        except ValueError:
            errors.append(name)
    return {"values": values, "errors": sorted(errors)}
''',
    tests=[
        ["limit=5&tags=a&tags=b", {"limit": "int", "tags": "list[str]"}],
        ["q=hello+world&page=2", {"q": "str", "page": "int"}],
        ["", {"q": "str"}],
        ["limit=abc&offset=3", {"limit": "int", "offset": "int"}],
        ["debug=TRUE&verbose=off&x=maybe", {"debug": "bool", "verbose": "bool", "x": "bool"}],
        ["ids=1&ids=2&ids=x", {"ids": "list[int]"}],
        ["ids=1&ids=2&ids=30", {"ids": "list[int]"}],
        ["limit=1&limit=9", {"limit": "int"}],
        ["name=caf%C3%A9&city=New%20York", {"name": "str", "city": "str"}],
        ["flag&a=1", {"flag": "str", "a": "int"}],
        ["temp=36.6&ratio=1e-3", {"temp": "float", "ratio": "float"}],
        ["eq=a%3Db=c&x=1", {"eq": "str"}],
        ["&&a=1&&", {"a": "int", "b": "int"}],
        ["unknown=1&k=2", {"k": "int"}],
        ["n=+7&m=%2B3", {"n": "int", "m": "int"}],
    ],
    wrong_solutions=[
        '''from urllib.parse import unquote_plus
def parseQuery(query, schema):
    raw = {}
    for pair in query.split("&"):
        if not pair: continue
        k, _, v = pair.partition("=")
        raw.setdefault(unquote_plus(k), []).append(unquote_plus(v))
    values, errors = {}, []
    for n, kind in schema.items():
        if n not in raw: continue
        try:
            if kind.startswith("list["):
                f = int if "int" in kind else str
                values[n] = [f(v) for v in raw[n]]
            elif kind == "bool":
                values[n] = bool(raw[n][0])
            else:
                values[n] = {"int": int, "float": float, "str": str}[kind](raw[n][0])
        except ValueError:
            errors.append(n)
    return {"values": values, "errors": sorted(errors)}
''',
        '''from urllib.parse import unquote_plus
def parseQuery(query, schema):
    raw = {}
    for pair in query.split("&"):
        if not pair: continue
        k, v = (pair.split("=") + [""])[:2]
        raw.setdefault(k, []).append(v)
    values, errors = {}, []
    T = {"true","1","yes","on"}; F = {"false","0","no","off"}
    for n, kind in schema.items():
        if n not in raw: continue
        try:
            def c(kd, v):
                if kd == "bool":
                    if v.lower() in T: return True
                    if v.lower() in F: return False
                    raise ValueError
                return {"int": int, "float": float, "str": str}[kd](v)
            values[n] = [c(kind[5:-1], v) for v in raw[n]] if kind.startswith("list[") else c(kind, raw[n][-1])
        except ValueError:
            errors.append(n)
    return {"values": values, "errors": sorted(errors)}
''',
    ],
    guide=dict(
        prereqs="Query parameters (lesson *Your first FastAPI app*); `urllib.parse`.",
        intuition="Parsing happens in two phases: first build a *multi-dict* (name → list of raw strings), then "
                  "coerce each declared parameter according to its type. Keeping the phases separate makes the "
                  "'last wins' versus 'collect all' rule trivial.",
        hints=["Use `pair.partition('=')` so `a=b=c` gives name `a`, value `b=c`.",
               "Decode *after* splitting — an encoded `%3D` must not split the pair.",
               "Scalars read `raw[name][-1]`; lists convert every element.",
               "Wrap each parameter's conversion in `try/except ValueError`."],
        brute_force="`urllib.parse.parse_qs(query, keep_blank_values=True)` builds the multi-dict for you — "
                    "fine to use once you understand what it does.",
        approach="1. Multi-dict: for every non-empty pair, partition on `=`, `unquote_plus` both halves, append.\n"
                 "2. For each `(name, kind)` in schema with `name` present: convert; on failure record the name.\n"
                 "3. Return values and sorted errors.\n\n"
                 "Dry run `n=+7`: `unquote_plus('+7')` is `' 7'`; `int(' 7')` is `7` because `int` strips whitespace.",
        complexity="O(len(query)).",
        pitfalls="- `bool('false')` is `True` in Python — never use `bool()` on strings.\n"
                 "- Splitting on every `=` instead of the first.\n- Decoding before splitting.",
        follow_up="FastAPI reports conversion problems as a 422 with one entry per failing location, e.g. "
                  "`{\"loc\": [\"query\", \"limit\"], \"type\": \"int_parsing\"}`.",
    ),
),
]
