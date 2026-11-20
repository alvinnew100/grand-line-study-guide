PROBLEMS = [
dict(
    id="sec-html-escape",
    title="HTML-Escape Text for an Element Context",
    difficulty="Easy",
    pattern="Output Encoding",
    kind="function",
    entry="escapeHtml",
    description=r"""
Your template engine is about to drop an untrusted string between two tags (`<p>HERE</p>`) or inside a
**quoted** attribute value (`<input value="HERE">`). Before it does, the five characters that HTML treats
as markup must be turned into character references so the browser shows them as text.

Write `escapeHtml(text)` that returns a new string in which:

| character | becomes |
|---|---|
| `&` | `&amp;` |
| `<` | `&lt;` |
| `>` | `&gt;` |
| `"` | `&quot;` |
| `'` | `&#x27;` |

Every other character (including non-ASCII text and whitespace) is copied unchanged. The function must
not "double protect" its own output inside a single call: an input `<` becomes exactly `&lt;`, never
`&amp;lt;`. An input that already contains `&lt;` is *text*, so its ampersand is escaped: `&amp;lt;`.

**Example:** `escapeHtml("<b>Tom & Jerry</b>")` → `"&lt;b&gt;Tom &amp; Jerry&lt;/b&gt;"`

**Example:** `escapeHtml("it's")` → `"it&#x27;s"`
""",
    starter='''def escapeHtml(text: str) -> str:
    pass
''',
    solution=r'''def escapeHtml(text):
    table = {"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#x27;"}
    return "".join(table.get(ch, ch) for ch in text)
''',
    tests=[
        ["<b>Tom & Jerry</b>"],
        ["it's"],
        [""],
        ["plain text 123"],
        ['" onmouseover="x'],
        ["&lt;"],
        ["a < b && c > d"],
        ["<<<>>>"],
        ["café ☃ <i>"],
        ["'single' and \"double\""],
        ["&amp;&amp;"],
        ["line1\nline2\t<br>"],
        ["x" * 2000 + "<"],
    ],
    examples=2,
    wrong_solutions=[
        r'''def escapeHtml(text):
    return (text.replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
            .replace("'", "&#x27;").replace("&", "&amp;"))
''',
        r'''def escapeHtml(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
''',
    ],
    guide=dict(
        prereqs="The cross-site scripting lesson: why data must be encoded for the context it lands in. Python strings and dicts.",
        intuition="The browser's HTML parser switches between *text* and *markup* modes when it meets a handful of "
                  "characters. If every one of those characters in the untrusted string is replaced by its character "
                  "reference, the parser can never leave text mode, so nothing the user typed can become a tag or "
                  "close an attribute.",
        hints=[
            "You only need to treat five characters specially; everything else is copied.",
            "Think about what happens if you replace `<` first and `&` afterwards.",
            "Either map each character through a small dict in a single pass, or do chained `replace` calls with `&` handled **first**.",
        ],
        brute_force="Five chained `str.replace` calls. It works only if the ampersand is replaced first; otherwise the "
                    "ampersands produced by earlier replacements are escaped a second time. Each call scans the whole string, "
                    "so it is O(5n), which is still linear.",
        approach="Build a five-entry lookup table and walk the string once, emitting `table.get(ch, ch)` for every "
                 "character. Because each *input* character is examined exactly once, output is never re-scanned and "
                 "double escaping is impossible.\n\n"
                 "Dry run on `a<'&`: `a` is not in the table → `a`; `<` → `&lt;`; `'` → `&#x27;`; `&` → `&amp;`. "
                 "Joined: `a&lt;&#x27;&amp;`.",
        complexity="Time O(n) for a string of length n; space O(n) for the output (it can be up to six times longer).",
        pitfalls="- Replacing `&` last corrupts earlier replacements (`<` → `&lt;` → `&amp;lt;`).\n"
                 "- Forgetting the quote characters leaves quoted attributes open to break-out.\n"
                 "- This encoding is only right for element content and quoted attributes. It does **not** make a string "
                 "safe inside `<script>`, a URL, CSS, or an unquoted attribute.",
        follow_up="Python ships this as `html.escape(text, quote=True)`. Real template engines (Jinja2, React JSX) apply "
                  "it automatically; the bugs come from the escape hatches (`|safe`, `dangerouslySetInnerHTML`).",
    ),
),
dict(
    id="sec-parameterised-query",
    title="Build a Parameterised Query from a Filter Dict",
    difficulty="Medium",
    pattern="Injection Defence",
    kind="function",
    entry="buildQuery",
    description=r"""
A search endpoint receives a dict of filters from the query string and must turn it into SQL for the
`users` table **without ever placing a value inside the SQL text**. Values travel separately as bound
parameters; column names (which cannot be bound) must come from an allow-list.

Write `buildQuery(filters, allowed)` returning `[sql, params]`, or `None` if the request must be rejected.

Rules:

1. If **any** key of `filters` is not in the list `allowed`, return `None` (compare exactly, case-sensitive).
2. Process the keys in **ascending alphabetical order**. Each key produces one clause:
   - value `None` → `col IS NULL` (no parameter);
   - value is a non-empty list → `col IN (?, ?, ...)` with one `?` per element, elements appended to `params` in order;
   - value is an empty list → the clause `1 = 0` (matches nothing, no parameter);
   - anything else → `col = ?` and the value is appended to `params`.
3. The SQL is `SELECT * FROM users` followed, when there is at least one clause, by ` WHERE ` and the
   clauses joined with ` AND `.

**Example:** `buildQuery({"role": "admin", "city": ["Oslo", "Rome"]}, ["city", "role"])` →
`["SELECT * FROM users WHERE city IN (?, ?) AND role = ?", ["Oslo", "Rome", "admin"]]`

**Example:** `buildQuery({"name": "x' OR '1'='1"}, ["name"])` →
`["SELECT * FROM users WHERE name = ?", ["x' OR '1'='1"]]` — the hostile text is just data.
""",
    starter='''def buildQuery(filters: dict, allowed: list):
    pass
''',
    solution=r'''def buildQuery(filters, allowed):
    clauses, params = [], []
    for col in sorted(filters):
        if col not in allowed:
            return None
        val = filters[col]
        if val is None:
            clauses.append(col + " IS NULL")
        elif isinstance(val, list):
            if not val:
                clauses.append("1 = 0")
            else:
                clauses.append(col + " IN (" + ", ".join("?" for _ in val) + ")")
                params.extend(val)
        else:
            clauses.append(col + " = ?")
            params.append(val)
    sql = "SELECT * FROM users"
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    return [sql, params]
''',
    tests=[
        [{"role": "admin", "city": ["Oslo", "Rome"]}, ["city", "role"]],
        [{"name": "x' OR '1'='1"}, ["name"]],
        [{}, ["name"]],
        [{"age": 30}, ["age", "name"]],
        [{"deleted_at": None, "name": "Ann"}, ["deleted_at", "name"]],
        [{"name = '' OR 1=1 --": "x"}, ["name"]],
        [{"Name": "Ann"}, ["name"]],
        [{"city": []}, ["city"]],
        [{"zip": "0150", "age": 41, "city": ["Oslo"]}, ["age", "city", "zip", "name"]],
        [{"name": "Robert'); DROP TABLE users;--", "age": 9}, ["age", "name"]],
        [{"id": [3, 1, 2], "active": True}, ["id", "active"]],
        [{"name": "Ann", "password": "x"}, ["name"]],
        [{"b": 1, "a": None, "c": [], "d": ["z"]}, ["a", "b", "c", "d"]],
    ],
    examples=2,
    wrong_solutions=[
        r'''def buildQuery(filters, allowed):
    clauses = []
    for col in sorted(filters):
        if col not in allowed:
            return None
        clauses.append("%s = '%s'" % (col, filters[col]))
    sql = "SELECT * FROM users"
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    return [sql, []]
''',
        r'''def buildQuery(filters, allowed):
    clauses, params = [], []
    for col in sorted(filters):
        val = filters[col]
        if val is None:
            clauses.append(col + " IS NULL")
        elif isinstance(val, list):
            if not val:
                clauses.append("1 = 0")
            else:
                clauses.append(col + " IN (" + ", ".join("?" for _ in val) + ")")
                params.extend(val)
        else:
            clauses.append(col + " = ?")
            params.append(val)
    sql = "SELECT * FROM users"
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    return [sql, params]
''',
        r'''def buildQuery(filters, allowed):
    clauses, params = [], []
    for col in filters:
        if col not in allowed:
            return None
        clauses.append(col + " = ?")
        params.append(filters[col])
    sql = "SELECT * FROM users"
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    return [sql, params]
''',
    ],
    guide=dict(
        prereqs="The SQL injection lesson (prepared statements, why identifiers cannot be bound). Dicts, lists, `str.join`.",
        intuition="A SQL statement has a *shape* (keywords, column names, placeholders) and *data*. Injection happens when "
                  "data is allowed to change the shape. So build the shape only from things you control — fixed keywords, "
                  "allow-listed column names and `?` marks — and hand every value to the driver in a separate list.",
        hints=[
            "Produce two things side by side: a list of clause strings and a list of parameters.",
            "Column names can't be `?` placeholders, so the only safe source for them is a fixed allow-list. Reject, don't repair.",
            "Loop over `sorted(filters)`; branch on `None`, list (empty or not) and scalar; join clauses with ` AND ` only if there are any.",
        ],
        brute_force="Format each value straight into the string (`name = '...'`). It 'works' on friendly input and is "
                    "exactly the bug this problem exists to prevent: a quote in the value ends the literal and the rest is "
                    "executed as SQL.",
        approach="1. Start with empty `clauses` and `params`.\n"
                 "2. For each key in sorted order: if it is not allow-listed return `None` immediately.\n"
                 "3. Emit `IS NULL`, `IN (?, ...)`, `1 = 0` or `= ?` depending on the value, extending `params` to match.\n"
                 "4. Join.\n\n"
                 "Dry run `{'role': 'admin', 'city': ['Oslo', 'Rome']}`: sorted keys are `city`, `role`. `city` → clause "
                 "`city IN (?, ?)`, params `['Oslo', 'Rome']`. `role` → `role = ?`, params gains `'admin'`. Result: "
                 "`SELECT * FROM users WHERE city IN (?, ?) AND role = ?`.",
        complexity="Time O(k log k + v) for k filters and v total values (the sort dominates for many keys); space O(k + v).",
        pitfalls="- `col = NULL` is never true in SQL; `None` needs `IS NULL`.\n"
                 "- `IN ()` is a syntax error in most databases, hence the `1 = 0` clause.\n"
                 "- Validating column names with a 'looks like an identifier' regex still lets callers filter on columns "
                 "such as `password_hash`; an explicit allow-list is both safer and simpler.\n"
                 "- The number of `?` marks must equal `len(params)` in the same order.",
        follow_up="Add `ORDER BY` with an allow-listed column and a direction restricted to `ASC`/`DESC`; add `LIMIT ?` "
                  "with an upper bound to prevent expensive unbounded scans.",
    ),
),
dict(
    id="sec-safe-redirect",
    title="Validate a Post-Login Redirect Target",
    difficulty="Medium",
    pattern="Open Redirect Defence",
    kind="function",
    entry="safeRedirect",
    description=r"""
After login your site sends the browser to the address given in a `next` parameter. If that address is
not checked, anyone can craft a link on your trusted domain that bounces visitors to a look-alike site.

Write `safeRedirect(target, allowed_hosts)` that returns `target` **unchanged** when it is safe and the
fallback `"/"` otherwise. `allowed_hosts` is a list of lower-case host names.

A target is safe only if it passes all the general checks and then one of the two shapes:

General checks (fail → `"/"`):

- it is a non-empty string;
- it contains no backslash, no whitespace character of any kind and no control character (code point below 32, or 127).

Shape A — **local path**: it starts with `/` but **not** with `//`.

Shape B — **absolute URL** (parse with `urllib.parse.urlsplit`; a parsing `ValueError` means unsafe):

- scheme is `https` (case-insensitive);
- there is a host name, and its lower-case form is **exactly** one of `allowed_hosts`;
- no user name or password part (`https://user@host/`);
- the port is absent or `443`.

Anything else (relative paths such as `dashboard`, `javascript:` URLs, `http://` URLs, protocol-relative
`//host`) is unsafe.

**Example:** `safeRedirect("/account?tab=2", ["shop.example"])` → `"/account?tab=2"`

**Example:** `safeRedirect("//evil.example/login", ["shop.example"])` → `"/"`
""",
    starter='''from urllib.parse import urlsplit

def safeRedirect(target, allowed_hosts: list) -> str:
    pass
''',
    solution=r'''from urllib.parse import urlsplit

def safeRedirect(target, allowed_hosts):
    if not isinstance(target, str) or not target:
        return "/"
    for ch in target:
        if ch == "\\" or ch.isspace() or ord(ch) < 32 or ord(ch) == 127:
            return "/"
    if target.startswith("/"):
        return "/" if target.startswith("//") else target
    try:
        parts = urlsplit(target)
        host = parts.hostname
        port = parts.port
    except ValueError:
        return "/"
    if parts.scheme.lower() != "https" or not host:
        return "/"
    if parts.username is not None or parts.password is not None:
        return "/"
    if port not in (None, 443):
        return "/"
    return target if host.lower() in allowed_hosts else "/"
''',
    tests=[
        ["/account?tab=2", ["shop.example"]],
        ["//evil.example/login", ["shop.example"]],
        ["https://shop.example/orders/7", ["shop.example"]],
        ["https://evil.example/shop.example", ["shop.example"]],
        ["https://shop.example.evil.example/", ["shop.example"]],
        ["https://shop.example@evil.example/", ["shop.example"]],
        ["http://shop.example/", ["shop.example"]],
        ["javascript:alert(1)", ["shop.example"]],
        ["/\\evil.example", ["shop.example"]],
        ["", ["shop.example"]],
        [None, ["shop.example"]],
        ["dashboard", ["shop.example"]],
        ["HTTPS://SHOP.example/x", ["shop.example"]],
        ["https://shop.example:8443/x", ["shop.example"]],
        ["https://shop.example:443/x", ["shop.example", "pay.shop.example"]],
        ["/ok\nSet-Cookie: x=1", ["shop.example"]],
        ["https://notshop.example/", ["shop.example"]],
        ["/", []],
    ],
    examples=2,
    wrong_solutions=[
        r'''def safeRedirect(target, allowed_hosts):
    if isinstance(target, str) and target.startswith("/"):
        return target
    return "/"
''',
        r'''def safeRedirect(target, allowed_hosts):
    if not isinstance(target, str) or not target:
        return "/"
    if target.startswith("/") and not target.startswith("//") and "\\" not in target and "\n" not in target:
        return target
    for h in allowed_hosts:
        if target.lower().startswith("https://" + h):
            return target
    return "/"
''',
        r'''from urllib.parse import urlsplit

def safeRedirect(target, allowed_hosts):
    if not isinstance(target, str) or not target or "\\" in target or any(c.isspace() for c in target):
        return "/"
    if target.startswith("/"):
        return "/" if target.startswith("//") else target
    parts = urlsplit(target)
    host = (parts.hostname or "").lower()
    if parts.scheme.lower() == "https" and any(host.endswith(h) for h in allowed_hosts):
        return target
    return "/"
''',
    ],
    guide=dict(
        prereqs="The clickjacking and open-redirect lesson; the anatomy of a URL (scheme, userinfo, host, port, path).",
        intuition="Never decide with string tricks what a URL *means* — parse it the way a browser would and compare "
                  "the parsed host for exact equality with a list you wrote yourself. Local paths are the easy, common "
                  "case, but `//host` and `/\\host` look local to a naive check and are treated as another site by browsers.",
        hints=[
            "Handle the junk first: wrong type, empty string, backslashes, whitespace, control characters.",
            "A leading `/` is fine; a leading `//` is a protocol-relative URL pointing at a different host.",
            "For absolute URLs use `urlsplit` and check `.scheme`, `.hostname`, `.username`, `.password`, `.port` — compare the host with `in allowed_hosts`, not with `startswith`/`endswith`.",
        ],
        brute_force="Check `target.startswith('/')` or `allowed_host in target`. Both are bypassed in one line: "
                    "`//evil.example` starts with a slash, and `https://evil.example/?shop.example` contains the allowed name.",
        approach="1. Reject non-strings, empty strings and any string with a backslash, whitespace or control character.\n"
                 "2. If it starts with `/`: unsafe when it starts with `//`, otherwise return it.\n"
                 "3. Otherwise parse. Require scheme `https`, a host, no userinfo, port `None` or `443`.\n"
                 "4. Return the target only if the lower-cased host is an exact member of the allow-list.\n\n"
                 "Dry run `https://shop.example@evil.example/`: no bad characters; not a local path; parsed scheme "
                 "`https`, hostname `evil.example`, username `shop.example` → userinfo present → `/`.",
        complexity="Time O(n + h) for a target of length n and h allowed hosts; space O(n) for the parsed parts.",
        pitfalls="- `startswith('https://shop.example')` also matches `https://shop.example.evil.example`.\n"
                 "- `endswith('shop.example')` also matches `notshop.example`.\n"
                 "- Reading `.port` raises `ValueError` for a non-numeric port, so it belongs inside the `try`.\n"
                 "- Newlines in a redirect target can lead to header injection in older stacks; reject them outright.",
        follow_up="An even stronger design avoids URLs altogether: store the destination server-side and pass only an "
                  "opaque key, or map short names (`next=orders`) to fixed paths.",
    ),
),
dict(
    id="sec-safe-join",
    title="Safe Path Join That Rejects Traversal",
    difficulty="Medium",
    pattern="Path Traversal Defence",
    kind="function",
    entry="safeJoin",
    description=r"""
A download endpoint serves files from one base directory. The file name comes from the request, so it
may contain `..` segments, absolute paths or other tricks intended to escape that directory.

Write `safeJoin(base, user_path)` using POSIX path rules (`/` separators; the `posixpath` module is the
right tool). Return the **normalised** combined path as a string, or `None` when the request must be refused.

Refuse when:

- `user_path` is empty;
- `user_path` contains a NUL character (`"\x00"`) or a backslash;
- `user_path` is absolute (starts with `/`);
- after joining and normalising (`posixpath.normpath(posixpath.join(base, user_path))`), the result is
  neither the normalised base itself nor a path **inside** it. "Inside" means it starts with the base
  followed by a `/` — a sibling such as `/srv/files-private` is *not* inside `/srv/files`.

`base` is an absolute path and may have a trailing slash or redundant segments; normalise it first.

**Example:** `safeJoin("/srv/files", "reports/q1.pdf")` → `"/srv/files/reports/q1.pdf"`

**Example:** `safeJoin("/srv/files", "../../etc/passwd")` → `None`

**Example:** `safeJoin("/srv/files", "a/../b.txt")` → `"/srv/files/b.txt"`
""",
    starter='''import posixpath

def safeJoin(base: str, user_path: str):
    pass
''',
    solution=r'''import posixpath

def safeJoin(base, user_path):
    if not user_path or "\x00" in user_path or "\\" in user_path:
        return None
    if user_path.startswith("/"):
        return None
    root = posixpath.normpath(base)
    full = posixpath.normpath(posixpath.join(root, user_path))
    prefix = root if root.endswith("/") else root + "/"
    if full == root or full.startswith(prefix):
        return full
    return None
''',
    tests=[
        ["/srv/files", "reports/q1.pdf"],
        ["/srv/files", "../../etc/passwd"],
        ["/srv/files", "a/../b.txt"],
        ["/srv/files", "/etc/passwd"],
        ["/srv/files", "../files-private/keys.txt"],
        ["/srv/files/", "notes.txt"],
        ["/srv/files", "a/./b//c.txt"],
        ["/srv/files", "a..b/file..txt"],
        ["/srv/files", ""],
        ["/srv/files", "ok.txt\x00.png"],
        ["/srv/files", "..\\..\\windows\\win.ini"],
        ["/srv/files", "a/../../files/x.txt"],
        ["/srv/files", "."],
        ["/srv/files", "a/b/../../.."],
        ["/srv/./files/../files", "x/y"],
        ["/", "etc/hosts"],
    ],
    examples=3,
    wrong_solutions=[
        r'''def safeJoin(base, user_path):
    if not user_path or ".." in user_path or user_path.startswith("/"):
        return None
    return base.rstrip("/") + "/" + user_path
''',
        r'''import posixpath

def safeJoin(base, user_path):
    if not user_path or "\x00" in user_path or "\\" in user_path or user_path.startswith("/"):
        return None
    root = posixpath.normpath(base)
    full = posixpath.normpath(posixpath.join(root, user_path))
    return full if full.startswith(root) else None
''',
        r'''import posixpath

def safeJoin(base, user_path):
    if not user_path:
        return None
    return posixpath.normpath(posixpath.join(base, user_path))
''',
    ],
    guide=dict(
        prereqs="The path traversal and file upload lesson. `posixpath.join` and `posixpath.normpath`.",
        intuition="Filtering the *input* for bad substrings is a losing game; judge the *result* instead. Resolve the "
                  "path the same way the operating system would, then ask one question: is the final location still "
                  "under my base directory?",
        hints=[
            "Reject the obviously hostile shapes first: empty, NUL byte, backslash, absolute.",
            "`normpath` collapses `.`, `..` and duplicate slashes, giving you the canonical location to judge.",
            "Containment is `full == root or full.startswith(root + '/')` — the trailing slash is what stops `/srv/files-private`.",
        ],
        brute_force="Refuse anything containing `..`. That blocks honest names such as `a..b/file..txt`, does no "
                    "normalising, and in real systems is bypassed by encodings the filter did not anticipate. It also "
                    "never checks where the path actually ends up.",
        approach="1. Refuse empty, NUL-containing, backslash-containing and absolute inputs.\n"
                 "2. `root = normpath(base)`; `full = normpath(join(root, user_path))`.\n"
                 "3. Accept when `full == root` or `full` starts with `root + '/'` (for root `/` the prefix is just `/`).\n\n"
                 "Dry run `('/srv/files', '../files-private/keys.txt')`: join gives `/srv/files/../files-private/keys.txt`; "
                 "normalised `/srv/files-private/keys.txt`. It is not equal to `/srv/files` and does not start with "
                 "`/srv/files/` → `None`. A plain `startswith('/srv/files')` would have accepted it.",
        complexity="Time O(n) in the combined path length; space O(n).",
        pitfalls="- Prefix checks without the separator accept sibling directories.\n"
                 "- `posixpath.join('/srv/files', '/etc/passwd')` silently returns `/etc/passwd`: an absolute second argument discards the base.\n"
                 "- On a real filesystem symbolic links can still point outside; production code resolves with "
                 "`os.path.realpath` (or `Path.resolve`) before the containment check.\n"
                 "- The NUL byte historically truncated names inside C libraries (`report.pdf\\0.png`).",
        follow_up="Best of all, do not accept paths: store files under generated identifiers and look the real "
                  "location up in a database keyed by that identifier.",
    ),
),
dict(
    id="sec-upload-validate",
    title="File Upload Validator",
    difficulty="Medium",
    pattern="File Upload Defence",
    kind="function",
    entry="validateUpload",
    description=r"""
An avatar/document endpoint accepts PNG, JPEG and PDF files. The browser supplies a file name and a
`Content-Type`, both fully controlled by the sender, so the server also inspects the first bytes.

Write `validateUpload(filename, declared_type, head, size, max_size)` where `head` is a list of the
file's first bytes as integers (possibly fewer than you need) and sizes are in bytes. Return `"ok"`, or
the **first** failing reason in this order:

1. `"empty"` — `size <= 0`.
2. `"too-large"` — `size > max_size`.
3. `"bad-name"` — the name is empty, longer than 100 characters, starts with `.`, or contains `/`, a
   backslash or a NUL character.
4. `"bad-extension"` — split the lower-cased name on `.`; there must be at least two parts and the last
   one must be `png`, `jpg`, `jpeg` or `pdf`.
5. `"double-extension"` — any part **between** the first and the last is one of
   `php, exe, js, html, htm, svg, sh, py, jsp, asp, aspx` (e.g. `shell.php.png`).
6. `"type-mismatch"` — `declared_type` is not exactly the type for that extension:
   `png → image/png`, `jpg`/`jpeg → image/jpeg`, `pdf → application/pdf`.
7. `"bad-magic"` — `head` does not begin with the signature for that extension:
   PNG `[137, 80, 78, 71, 13, 10, 26, 10]`, JPEG `[255, 216, 255]`, PDF `[37, 80, 68, 70, 45]` (`%PDF-`).

**Example:** `validateUpload("cat.png", "image/png", [137,80,78,71,13,10,26,10,0], 2048, 1000000)` → `"ok"`

**Example:** `validateUpload("cat.png", "image/png", [60,115,99,114], 2048, 1000000)` → `"bad-magic"`
""",
    starter='''def validateUpload(filename: str, declared_type: str, head: list, size: int, max_size: int) -> str:
    pass
''',
    solution=r'''_TYPES = {
    "png": ("image/png", [137, 80, 78, 71, 13, 10, 26, 10]),
    "jpg": ("image/jpeg", [255, 216, 255]),
    "jpeg": ("image/jpeg", [255, 216, 255]),
    "pdf": ("application/pdf", [37, 80, 68, 70, 45]),
}
_DANGEROUS = {"php", "exe", "js", "html", "htm", "svg", "sh", "py", "jsp", "asp", "aspx"}

def validateUpload(filename, declared_type, head, size, max_size):
    if size <= 0:
        return "empty"
    if size > max_size:
        return "too-large"
    if (not filename or len(filename) > 100 or filename.startswith(".")
            or "/" in filename or "\\" in filename or "\x00" in filename):
        return "bad-name"
    parts = filename.lower().split(".")
    if len(parts) < 2 or parts[-1] not in _TYPES:
        return "bad-extension"
    if any(p in _DANGEROUS for p in parts[1:-1]):
        return "double-extension"
    mime, magic = _TYPES[parts[-1]]
    if declared_type != mime:
        return "type-mismatch"
    if list(head[:len(magic)]) != magic:
        return "bad-magic"
    return "ok"
''',
    tests=[
        ["cat.png", "image/png", [137, 80, 78, 71, 13, 10, 26, 10, 0], 2048, 1000000],
        ["cat.png", "image/png", [60, 115, 99, 114], 2048, 1000000],
        ["photo.JPG", "image/jpeg", [255, 216, 255, 224], 500, 1000],
        ["report.pdf", "application/pdf", [37, 80, 68, 70, 45, 49], 1000, 1000],
        ["report.pdf", "application/pdf", [37, 80, 68, 70, 45, 49], 1001, 1000],
        ["empty.png", "image/png", [], 0, 1000],
        ["shell.php.png", "image/png", [137, 80, 78, 71, 13, 10, 26, 10], 10, 1000],
        ["../../etc/cron.d/x.png", "image/png", [137, 80, 78, 71, 13, 10, 26, 10], 10, 1000],
        [".htaccess", "text/plain", [35], 10, 1000],
        ["page.html", "text/html", [60, 33], 10, 1000],
        ["cat.png", "image/jpeg", [137, 80, 78, 71, 13, 10, 26, 10], 10, 1000],
        ["cat.jpeg", "image/jpeg", [255, 216], 10, 1000],
        ["noextension", "image/png", [137, 80, 78, 71, 13, 10, 26, 10], 10, 1000],
        ["a" * 101 + ".png", "image/png", [137, 80, 78, 71, 13, 10, 26, 10], 10, 1000],
        ["my.holiday.photo.jpg", "image/jpeg", [255, 216, 255], 10, 1000],
        ["trailing.png.", "image/png", [137, 80, 78, 71, 13, 10, 26, 10], 10, 1000],
        ["x.png", "image/png", [137, 80, 78, 71, 13, 10, 26, 10], 5000, 1000],
    ],
    examples=2,
    wrong_solutions=[
        r'''def validateUpload(filename, declared_type, head, size, max_size):
    if size <= 0:
        return "empty"
    if size > max_size:
        return "too-large"
    if declared_type in ("image/png", "image/jpeg", "application/pdf"):
        return "ok"
    return "type-mismatch"
''',
        r'''_TYPES = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "pdf": "application/pdf"}

def validateUpload(filename, declared_type, head, size, max_size):
    if size <= 0:
        return "empty"
    if size > max_size:
        return "too-large"
    if not filename or len(filename) > 100 or filename.startswith(".") or "/" in filename or "\\" in filename or "\x00" in filename:
        return "bad-name"
    ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    if ext not in _TYPES:
        return "bad-extension"
    if declared_type != _TYPES[ext]:
        return "type-mismatch"
    return "ok"
''',
    ],
    guide=dict(
        prereqs="The path traversal and file upload lesson. List slicing; the idea of file signatures (magic bytes).",
        intuition="Three things describe an upload — its name, its declared type and its content — and an attacker "
                  "controls all three independently. Only accept a file when all three tell the same story and that "
                  "story is on a short allow-list. Cheap checks (size, name) go first so hostile input is rejected early.",
        hints=[
            "Follow the numbered order literally; return as soon as one check fails.",
            "Keep one table: extension → (expected MIME type, signature bytes).",
            "Compare `head[:len(signature)]` with the signature; a `head` that is too short simply won't be equal.",
        ],
        brute_force="Trust the `Content-Type` header or the extension alone. Both are text typed by the client, so a "
                    "script named `x.png` or sent as `image/png` sails through.",
        approach="1. Size checks. 2. Name hygiene. 3. Split on dots; last part must be allow-listed. 4. Middle parts "
                 "must not be executable extensions. 5. Declared type must equal the table entry. 6. Signature prefix must match.\n\n"
                 "Dry run `('shell.php.png', 'image/png', PNG bytes, 10, 1000)`: size fine; name fine; parts "
                 "`['shell','php','png']`, last is allowed; middle part `php` is dangerous → `double-extension`.",
        complexity="Time O(n) in the file-name length (signature checks are constant size); space O(n).",
        pitfalls="- Compare extensions case-insensitively (`PHOTO.JPG`).\n"
                 "- A name ending in a dot produces an empty last part; treat it as a bad extension.\n"
                 "- Magic bytes prove very little on their own: a file can start with a valid PNG header and still carry "
                 "other content (polyglots). That is why storage and serving rules matter as much as validation.",
        follow_up="In production also: generate the stored name yourself, keep uploads outside the web root or on a "
                  "separate origin, serve with `Content-Disposition: attachment` and `X-Content-Type-Options: nosniff`, "
                  "re-encode images, and scan for malware.",
    ),
),
dict(
    id="sec-ssrf-guard",
    title="SSRF Guard: Reject Internal Destinations",
    difficulty="Medium",
    pattern="SSRF Defence",
    kind="function",
    entry="isSafeUrl",
    description=r"""
A "fetch preview" feature downloads a URL supplied by the user. Without checks, the server can be asked
to call addresses only *it* can reach: loopback services, the private network, the cloud metadata endpoint.

The caller has already resolved the host name and passes the resulting addresses, so you never do DNS
yourself. Write `isSafeUrl(url, resolved_ips)` returning `True` only when **all** of these hold:

1. `urllib.parse.urlsplit(url)` succeeds (a `ValueError` anywhere means `False`), the scheme is `http`
   or `https`, and there is a host name.
2. The URL has no user name or password part.
3. The port is absent, `80` or `443`.
4. `resolved_ips` is non-empty and **every** entry is a valid IP address literal that is public.

An address is **not public** if it lies in any of these networks:

`0.0.0.0/8`, `10.0.0.0/8`, `100.64.0.0/10`, `127.0.0.0/8`, `169.254.0.0/16`, `172.16.0.0/12`,
`192.168.0.0/16`, `224.0.0.0/4`, `240.0.0.0/4`, `::/128`, `::1/128`, `fc00::/7`, `fe80::/10`, `ff00::/8`.

An IPv4-mapped IPv6 address (`::ffff:a.b.c.d`) is judged by its embedded IPv4 address. A string that
`ipaddress.ip_address` cannot parse makes the whole result `False`.

**Example:** `isSafeUrl("https://img.partner.example/a.png", ["93.184.216.34"])` → `True`

**Example:** `isSafeUrl("http://169.254.169.254/latest/meta-data/", ["169.254.169.254"])` → `False`
""",
    starter='''import ipaddress
from urllib.parse import urlsplit

def isSafeUrl(url: str, resolved_ips: list) -> bool:
    pass
''',
    solution=r'''import ipaddress
from urllib.parse import urlsplit

_BLOCKED = [ipaddress.ip_network(n) for n in (
    "0.0.0.0/8", "10.0.0.0/8", "100.64.0.0/10", "127.0.0.0/8", "169.254.0.0/16", "172.16.0.0/12",
    "192.168.0.0/16", "224.0.0.0/4", "240.0.0.0/4", "::/128", "::1/128", "fc00::/7", "fe80::/10", "ff00::/8")]

def _public(text):
    try:
        ip = ipaddress.ip_address(text)
    except ValueError:
        return False
    if ip.version == 6 and ip.ipv4_mapped is not None:
        ip = ip.ipv4_mapped
    for net in _BLOCKED:
        if net.version == ip.version and ip in net:
            return False
    return True

def isSafeUrl(url, resolved_ips):
    try:
        parts = urlsplit(url)
        host = parts.hostname
        port = parts.port
    except ValueError:
        return False
    if parts.scheme not in ("http", "https") or not host:
        return False
    if parts.username is not None or parts.password is not None:
        return False
    if port not in (None, 80, 443):
        return False
    if not resolved_ips:
        return False
    return all(_public(ip) for ip in resolved_ips)
''',
    tests=[
        ["https://img.partner.example/a.png", ["93.184.216.34"]],
        ["http://169.254.169.254/latest/meta-data/", ["169.254.169.254"]],
        ["http://localhost/admin", ["127.0.0.1"]],
        ["https://intranet.corp.example/", ["10.2.3.4"]],
        ["https://cdn.example/x", ["93.184.216.34", "192.168.1.9"]],
        ["https://cdn.example/x", ["192.168.1.9", "93.184.216.34"]],
        ["file:///etc/passwd", ["93.184.216.34"]],
        ["https://cdn.example:8080/x", ["93.184.216.34"]],
        ["https://user:pw@cdn.example/x", ["93.184.216.34"]],
        ["https://cdn.example/x", []],
        ["https://v6.example/", ["::1"]],
        ["https://v6.example/", ["::ffff:10.0.0.5"]],
        ["https://v6.example/", ["2606:2800:220:1:248:1893:25c8:1946"]],
        ["https://cdn.example/x", ["172.20.10.3"]],
        ["https://cdn.example/x", ["172.32.0.1"]],
        ["https://cdn.example/x", ["2130706433"]],
        ["https://cdn.example:443/x", ["8.8.8.8", "::ffff:8.8.4.4"]],
        ["https://cdn.example/x", ["100.64.1.1"]],
        ["https:///nohost", ["8.8.8.8"]],
        ["https://cdn.example/x", ["fe80::1"]],
    ],
    examples=2,
    wrong_solutions=[
        r'''from urllib.parse import urlsplit

def isSafeUrl(url, resolved_ips):
    parts = urlsplit(url)
    if parts.scheme not in ("http", "https") or not parts.hostname:
        return False
    if parts.username is not None or parts.port not in (None, 80, 443) or not resolved_ips:
        return False
    for ip in resolved_ips:
        if ip.startswith(("10.", "127.", "192.168.", "172.")) or ip == "::1":
            return False
    return True
''',
        r'''import ipaddress
from urllib.parse import urlsplit

def isSafeUrl(url, resolved_ips):
    try:
        parts = urlsplit(url)
        port = parts.port
    except ValueError:
        return False
    if parts.scheme not in ("http", "https") or not parts.hostname:
        return False
    if parts.username is not None or port not in (None, 80, 443) or not resolved_ips:
        return False
    try:
        ip = ipaddress.ip_address(resolved_ips[0])
    except ValueError:
        return False
    return not (ip.is_private or ip.is_loopback or ip.is_link_local)
''',
    ],
    guide=dict(
        prereqs="The SSRF lesson; CIDR notation; Python's `ipaddress` module (`ip_address`, `ip_network`, `in`).",
        intuition="The danger of a server-side fetch is *where the packet goes*, not what the URL text looks like. So "
                  "validate the parsed URL for shape, then judge the actual destination addresses numerically against "
                  "a list of ranges that must never be reachable from this feature. Every address must pass, because the "
                  "HTTP client may pick any of them.",
        hints=[
            "Do the cheap structural checks first: scheme, host, userinfo, port.",
            "Parse each address with `ipaddress.ip_address` and test membership in `ipaddress.ip_network(...)` objects; do not compare strings.",
            "Unwrap `ip.ipv4_mapped` for IPv6 addresses before checking, and use `all(...)` over the list.",
        ],
        brute_force="String prefixes such as `ip.startswith('10.')`. It misses the metadata range `169.254.0.0/16`, "
                    "wrongly blocks public `172.32.x.x`, and is blind to IPv6 and mapped addresses.",
        approach="1. `urlsplit`, reading `.hostname` and `.port` inside a `try`.\n"
                 "2. Scheme allow-list, host present, no credentials, port in `{None, 80, 443}`.\n"
                 "3. Empty address list → `False`.\n"
                 "4. For each address: parse; unwrap mapped IPv4; reject if inside any blocked network.\n\n"
                 "Dry run `('https://v6.example/', ['::ffff:10.0.0.5'])`: structure is fine; the address parses as IPv6 "
                 "with `ipv4_mapped = 10.0.0.5`; that is inside `10.0.0.0/8` → `False`.",
        complexity="Time O(a · b) for a addresses and b blocked networks (b is a constant 14); space O(1) beyond the parsed values.",
        pitfalls="- Checking only the first resolved address.\n"
                 "- Validating the name and then letting the HTTP library resolve it *again* (DNS rebinding): the "
                 "connection must be made to the addresses you validated.\n"
                 "- Following redirects automatically: each hop needs the same check.\n"
                 "- A block-list of ranges is a backstop; when the set of legitimate destinations is known, an allow-list of hosts is stronger.",
        follow_up="Add network-level controls too: run the fetcher in a segment with no route to internal services and "
                  "require the token-based (IMDSv2-style) metadata service on cloud instances.",
    ),
),
dict(
    id="sec-schema-validate",
    title="Allow-List Input Schema Validation",
    difficulty="Medium",
    pattern="Input Validation",
    kind="function",
    entry="validateInput",
    description=r"""
An API handler should accept exactly the fields it knows about, with the types and ranges it expects,
and nothing else. Unknown fields are how "mass assignment" bugs (`"is_admin": true` in a profile update)
get in.

Write `validateInput(data, schema)` returning a **sorted** list of error strings (empty list = valid).

`schema` maps a field name to a rule dict with:

- `"type"`: `"str"`, `"int"` or `"bool"`;
- `"required"`: optional bool, default `False`;
- for strings: optional `"min_len"`, `"max_len"` (inclusive) and `"choices"` (list of allowed values);
- for ints: optional `"min"`, `"max"` (inclusive).

Errors:

- `"unexpected:<field>"` — a key of `data` that is not in `schema`;
- `"missing:<field>"` — a required field absent from `data`;
- `"type:<field>"` — wrong type. A Python `bool` is **not** an acceptable `int`. When the type is wrong,
  report nothing else for that field;
- `"length:<field>"` — string shorter than `min_len` or longer than `max_len`;
- `"choice:<field>"` — string not in `choices`;
- `"range:<field>"` — int below `min` or above `max`.

A string can produce both `length` and `choice` errors.

**Example:** `validateInput({"name": "Ann", "is_admin": True}, {"name": {"type": "str", "required": True}})`
→ `["unexpected:is_admin"]`
""",
    starter='''def validateInput(data: dict, schema: dict) -> list:
    pass
''',
    solution=r'''def validateInput(data, schema):
    errors = []
    for field in data:
        if field not in schema:
            errors.append("unexpected:" + field)
    for field, rule in schema.items():
        if field not in data:
            if rule.get("required", False):
                errors.append("missing:" + field)
            continue
        value = data[field]
        kind = rule["type"]
        if kind == "str":
            ok = isinstance(value, str)
        elif kind == "int":
            ok = isinstance(value, int) and not isinstance(value, bool)
        elif kind == "bool":
            ok = isinstance(value, bool)
        else:
            ok = False
        if not ok:
            errors.append("type:" + field)
            continue
        if kind == "str":
            if "min_len" in rule and len(value) < rule["min_len"]:
                errors.append("length:" + field)
            elif "max_len" in rule and len(value) > rule["max_len"]:
                errors.append("length:" + field)
            if "choices" in rule and value not in rule["choices"]:
                errors.append("choice:" + field)
        elif kind == "int":
            if ("min" in rule and value < rule["min"]) or ("max" in rule and value > rule["max"]):
                errors.append("range:" + field)
    return sorted(errors)
''',
    tests=[
        [{"name": "Ann", "is_admin": True}, {"name": {"type": "str", "required": True}}],
        [{"name": "Ann", "age": 30}, {"name": {"type": "str", "required": True}, "age": {"type": "int", "min": 0, "max": 150}}],
        [{}, {"name": {"type": "str", "required": True}, "bio": {"type": "str"}}],
        [{"age": True}, {"age": {"type": "int"}}],
        [{"age": "30"}, {"age": {"type": "int", "min": 0}}],
        [{"age": -1}, {"age": {"type": "int", "min": 0, "max": 150}}],
        [{"age": 151}, {"age": {"type": "int", "min": 0, "max": 150}}],
        [{"role": "root"}, {"role": {"type": "str", "choices": ["viewer", "editor"]}}],
        [{"role": "superuser-with-a-long-name"}, {"role": {"type": "str", "max_len": 10, "choices": ["viewer", "editor"]}}],
        [{"name": ""}, {"name": {"type": "str", "required": True, "min_len": 1, "max_len": 5}}],
        [{"active": 1}, {"active": {"type": "bool"}}],
        [{"active": False, "name": ["x"]}, {"active": {"type": "bool"}, "name": {"type": "str", "max_len": 3}}],
        [{"z": 1, "a": 2, "name": "Bo"}, {"name": {"type": "str"}, "email": {"type": "str", "required": True}}],
        [{"n": 0}, {"n": {"type": "int", "min": 0, "max": 0}}],
        [{}, {}],
    ],
    examples=1,
    wrong_solutions=[
        r'''def validateInput(data, schema):
    errors = []
    for field, rule in schema.items():
        if field not in data:
            if rule.get("required", False):
                errors.append("missing:" + field)
            continue
        value = data[field]
        kind = rule["type"]
        ok = isinstance(value, {"str": str, "int": int, "bool": bool}[kind]) and not (kind == "int" and isinstance(value, bool))
        if not ok:
            errors.append("type:" + field)
            continue
        if kind == "str":
            if len(value) < rule.get("min_len", 0) or len(value) > rule.get("max_len", 10**9):
                errors.append("length:" + field)
            if "choices" in rule and value not in rule["choices"]:
                errors.append("choice:" + field)
        elif kind == "int":
            if value < rule.get("min", value) or value > rule.get("max", value):
                errors.append("range:" + field)
    return sorted(errors)
''',
        r'''def validateInput(data, schema):
    errors = []
    for field in data:
        if field not in schema:
            errors.append("unexpected:" + field)
    for field, rule in schema.items():
        if field not in data:
            if rule.get("required", False):
                errors.append("missing:" + field)
            continue
        value = data[field]
        kind = rule["type"]
        if not isinstance(value, {"str": str, "int": int, "bool": bool}[kind]):
            errors.append("type:" + field)
            continue
        if kind == "str":
            if len(value) < rule.get("min_len", 0) or len(value) > rule.get("max_len", 10**9):
                errors.append("length:" + field)
            if "choices" in rule and value not in rule["choices"]:
                errors.append("choice:" + field)
        elif kind == "int":
            if value < rule.get("min", value) or value > rule.get("max", value):
                errors.append("range:" + field)
    return sorted(errors)
''',
    ],
    guide=dict(
        prereqs="The secure code review and input validation lesson. `isinstance`, dict iteration.",
        intuition="Validation by allow-list flips the default: instead of hunting for bad input, describe good input "
                  "and refuse everything that does not fit the description — including fields nobody asked for.",
        hints=[
            "Two passes are easiest: one over `data` for unexpected keys, one over `schema` for everything else.",
            "`isinstance(True, int)` is `True` in Python, so the int check needs an explicit bool exclusion.",
            "After a type error, `continue`; the constraint checks would be meaningless (or crash) on the wrong type.",
        ],
        brute_force="Checking each known field by hand inside every handler. It repeats itself, drifts between "
                    "endpoints, and almost always forgets to reject extra keys.",
        approach="1. For each key in `data` not in `schema` add `unexpected:`.\n"
                 "2. For each schema field: absent → `missing:` only if required; present → type check, then constraints.\n"
                 "3. Sort.\n\n"
                 "Dry run `({'role': 'superuser-with-a-long-name'}, {'role': {'type': 'str', 'max_len': 10, 'choices': ['viewer', 'editor']}})`: "
                 "no unexpected keys; type is `str`; length 26 > 10 → `length:role`; not in choices → `choice:role`. "
                 "Sorted: `['choice:role', 'length:role']`.",
        complexity="Time O(d + s + e log e) for d data keys, s schema fields and e errors; space O(e).",
        pitfalls="- Silently dropping unknown fields hides client bugs and, with ORMs that copy dicts onto models, becomes mass assignment.\n"
                 "- Accepting `True` where a number is expected, or `'30'` where an int is expected, lets odd values reach business logic.\n"
                 "- Validation is not output encoding: a perfectly valid name such as `O'Brien <b>` still needs encoding when rendered and binding when queried.",
        follow_up="Libraries such as Pydantic (`model_config = ConfigDict(extra='forbid')`) or JSON Schema "
                  "(`additionalProperties: false`) implement exactly this contract.",
    ),
),
]
