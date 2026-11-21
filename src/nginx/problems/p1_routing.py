PROBLEMS = [
dict(
    id="nginx-variable-expand",
    title="Expand NGINX Variables in a String",
    difficulty="Easy",
    pattern="Configuration",
    entry="expand_vars",
    description=r"""
Directives such as `return`, `proxy_set_header` and `log_format` accept text with **variables** inside, for example
`https://$host$request_uri`. Write `expand_vars(template, variables)` that returns the text with every variable replaced.

Rules:

- A variable is written `$name` or `${name}`. A name starts with a letter or underscore and continues with letters,
  digits or underscores. `$name` takes the **longest** valid name, so `$hostname` is the variable `hostname`, never
  `host` followed by `name`. Braces mark where the name ends: `${host}name`.
- A variable that is not in `variables` becomes the empty string.
- A `$` that is not followed by a valid name (or by `{name}`) stays in the output unchanged.
- Substitution happens **once**: a `$` inside a substituted value is not expanded again.

**Example:** `"$scheme://$host$request_uri"` with `{"scheme": "https", "host": "shop.test", "request_uri": "/a?b=1"}`
→ `"https://shop.test/a?b=1"`

**Example:** `"${host}name $hostname"` with `{"host": "a", "hostname": "b"}` → `"aname b"`
""",
    starter='''def expand_vars(template, variables):
    # return template with $name and ${name} replaced
    pass
''',
    solution=r'''import re

def expand_vars(template, variables):
    def swap(m):
        name = m.group(1) or m.group(2)
        return str(variables.get(name, ""))
    return re.sub(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}|\$([A-Za-z_][A-Za-z0-9_]*)", swap, template)
''',
    tests=[
        ["$scheme://$host$request_uri", {"scheme": "https", "host": "shop.test", "request_uri": "/a?b=1"}],
        ["${host}name $hostname", {"host": "a", "hostname": "b"}],
        ["user=$remote_user;", {}],
        ["", {"host": "x"}],
        ["no variables here", {"host": "x"}],
        ["$a$b$a", {"a": "1", "b": "2"}],
        ["$a", {"a": "$b", "b": "X"}],
        ["cost: $5 and 100$", {"5": "five"}],
        ["${host", {"host": "x"}],
        ["$$host", {"host": "x"}],
        ["$host_name-$host-name", {"host": "h", "host_name": "hn", "name": "n"}],
        ["X-Forwarded-For: $proxy_add_x_forwarded_for, $remote_addr", {"remote_addr": "203.0.113.9", "proxy_add_x_forwarded_for": "10.0.0.1"}],
    ],
    examples=2,
    wrong_solutions=[
        '''def expand_vars(template, variables):
    for name, value in variables.items():
        template = template.replace("${" + name + "}", str(value)).replace("$" + name, str(value))
    return template
''',
        r'''import re

def expand_vars(template, variables):
    return re.sub(r"\$\{?(\w+)\}?", lambda m: str(variables.get(m.group(1), m.group(0))), template)
''',
    ],
    guide=dict(
        prereqs="Strings and dictionaries. Lesson: *Installing NGINX and reading nginx.conf* (variables).",
        intuition="Scan the text once from left to right. Each time you meet `$`, read the longest name that follows, look it up, and write the value. Never look at the output again.",
        hints=[
            "A regular expression with two alternatives handles both spellings: `\\$\\{name\\}` and `\\$name`.",
            "`re.sub` accepts a function as the replacement; it is called once per match with the match object.",
            "Use `variables.get(name, \"\")` so that unknown variables vanish instead of raising an error.",
        ],
        brute_force="Loop over the dictionary and call `str.replace` for each key. It is short and wrong twice over: `$host` also eats the start of `$hostname`, and a value containing `$x` gets expanded again by a later replacement.",
        approach="1. Write a pattern for a name: `[A-Za-z_][A-Za-z0-9_]*`.\n2. Combine `\\$\\{NAME\\}` and `\\$NAME` with `|`, capturing the name in each.\n3. In the callback take whichever group matched and return `variables.get(name, \"\")`.\n\nDry run on `${host}name $hostname` with host=a, hostname=b: the first match is `${host}` → `a`; `name` is copied; the second match is `$hostname` (the regex is greedy) → `b`. Result `aname b`.",
        complexity="Time O(n) for a template of n characters plus the length of the substituted values; space O(output).",
        pitfalls="Replacing shorter names first; expanding substituted values again; treating `$5` or a lone `$` as a variable; forgetting the braces form.",
        follow_up="NGINX also has positional captures `$1`..`$9` from the last regex match. Extend the function to take a list of captures.",
    ),
),
dict(
    id="nginx-server-block-select",
    title="Choose the Server Block",
    difficulty="Medium",
    pattern="Request Routing",
    entry="select_server",
    description=r"""
Implement both stages NGINX uses to pick a `server` block.

`select_server(servers, local_ip, port, host)` returns the **index** of the chosen server, or `-1` if no server listens
for that connection. Each server is `[listen, names, is_default]`:

- `listen` is `"IP:PORT"` or `"*:PORT"` (every address).
- `names` is the list from `server_name`.
- `is_default` is `True` when the listen line carries `default_server`.

**Stage A (listen socket).** Candidates are the servers whose `listen` equals `local_ip:port` exactly. Only if there are
none, the candidates are the servers listening on `*:port`.

**Stage B (name).** Lower-case `host` and drop a `:port` suffix. If it is non-empty, test the candidates in this order
and stop at the first rule that produces a match:

1. **Exact name.** A name beginning with a dot, `.example.com`, also counts as the exact name `example.com`.
2. **Longest wildcard at the start**: `*.example.com` (or the dot form `.example.com`) matches any host ending in
   `.example.com` with at least one character before it.
3. **Longest wildcard at the end**: `www.example.*` matches any host starting with `www.example.` with at least one
   character after it.
4. **First regular expression** in configuration order. A regex name starts with `~`; test the rest with `re.search`.

Within a rule, ties go to the earlier server. If nothing matched (or `host` is empty or `None`), choose the candidate
with `is_default`, and if none has it, the **first candidate**.

**Example:** servers `[["*:80", ["_"], True], ["*:80", ["shop.test"], False], ["*:80", ["*.shop.test"], False]]`,
connection to `203.0.113.10` port `80`: host `"www.shop.test"` → `2`; host `"other.example"` → `0`.
""",
    starter='''def select_server(servers, local_ip, port, host):
    # return the index of the chosen server block, or -1
    pass
''',
    solution=r'''import re

def select_server(servers, local_ip, port, host):
    cands = [i for i, s in enumerate(servers) if s[0] == "%s:%s" % (local_ip, port)]
    if not cands:
        cands = [i for i, s in enumerate(servers) if s[0] == "*:%s" % port]
    if not cands:
        return -1
    h = (host or "").lower().split(":")[0]
    if h:
        for i in cands:
            for n in servers[i][1]:
                if n == h or (n.startswith(".") and n[1:] == h):
                    return i
        best = None
        for i in cands:
            for n in servers[i][1]:
                suffix = n[1:] if n.startswith("*.") else (n if n.startswith(".") else None)
                if suffix and h.endswith(suffix) and len(h) > len(suffix) and (best is None or len(suffix) > best[0]):
                    best = (len(suffix), i)
        if best:
            return best[1]
        best = None
        for i in cands:
            for n in servers[i][1]:
                if n.endswith(".*"):
                    prefix = n[:-1]
                    if h.startswith(prefix) and len(h) > len(prefix) and (best is None or len(prefix) > best[0]):
                        best = (len(prefix), i)
        if best:
            return best[1]
        for i in cands:
            for n in servers[i][1]:
                if n.startswith("~") and re.search(n[1:], h):
                    return i
    for i in cands:
        if servers[i][2]:
            return i
    return cands[0]
''',
    tests=[
        [[["*:80", ["_"], True], ["*:80", ["shop.test"], False], ["*:80", ["*.shop.test"], False]], "203.0.113.10", 80, "www.shop.test"],
        [[["*:80", ["_"], True], ["*:80", ["shop.test"], False], ["*:80", ["*.shop.test"], False]], "203.0.113.10", 80, "other.example"],
        [[["*:80", ["_"], True], ["*:80", ["shop.test"], False], ["*:80", ["*.shop.test"], False]], "203.0.113.10", 80, "SHOP.TEST:80"],
        [[["*:80", ["a.test"], False], ["*:80", ["b.test"], False]], "10.0.0.1", 80, "zzz.test"],
        [[["*:80", ["a.test"], False], ["*:80", ["b.test"], False]], "10.0.0.1", 80, None],
        [[["*:80", ["a.test"], False], ["*:80", ["b.test"], False]], "10.0.0.1", 443, "a.test"],
        [[["*:80", ["www.shop.test"], False], ["192.0.2.10:80", ["admin.shop.test"], False]], "192.0.2.10", 80, "www.shop.test"],
        [[["*:80", ["www.shop.test"], False], ["192.0.2.10:80", ["admin.shop.test"], False]], "192.0.2.11", 80, "www.shop.test"],
        [[["*:80", ["*.test"], False], ["*:80", ["*.shop.test"], False], ["*:80", ["www.shop.*"], False]], "10.0.0.1", 80, "www.shop.test"],
        [[["*:80", ["www.shop.*"], False], ["*:80", [r"~^www\..*\.org$"], False]], "10.0.0.1", 80, "www.shop.org"],
        [[["*:80", [r"~^(?P<t>[a-z]+)\.shops\.test$"], False], ["*:80", [r"~\.test$"], False], ["*:80", ["x"], True]], "10.0.0.1", 80, "rosa.shops.test"],
        [[["*:80", [r"~^(?P<t>[a-z]+)\.shops\.test$"], False], ["*:80", [r"~\.test$"], False], ["*:80", ["x"], True]], "10.0.0.1", 80, "r2.shops.test"],
        [[["*:80", [".shop.test"], False], ["*:80", ["shop.test"], False], ["*:80", ["x"], True]], "10.0.0.1", 80, "shop.test"],
        [[["*:80", ["x"], True], ["*:80", [".shop.test"], False]], "10.0.0.1", 80, "deep.www.shop.test"],
        [[["*:80", ["x"], True], ["*:80", ["*.shop.test"], False]], "10.0.0.1", 80, "shop.test"],
    ],
    examples=2,
    wrong_solutions=[
        r'''import re

def select_server(servers, local_ip, port, host):
    cands = [i for i, s in enumerate(servers) if s[0].endswith(":%s" % port)]
    if not cands:
        return -1
    h = (host or "").lower().split(":")[0]
    for i in cands:
        for n in servers[i][1]:
            if n == h or (n.startswith(".") and n[1:] == h and h):
                return i
            if n.startswith("*.") and h.endswith(n[1:]) and len(h) > len(n) - 1:
                return i
            if n.startswith(".") and h.endswith(n) and len(h) > len(n):
                return i
            if n.endswith(".*") and h.startswith(n[:-1]) and len(h) > len(n) - 1:
                return i
            if n.startswith("~") and h and re.search(n[1:], h):
                return i
    for i in cands:
        if servers[i][2]:
            return i
    return cands[0]
''',
    ],
    guide=dict(
        prereqs="Lesson: *Serving a first static site and choosing a server block*. String methods `startswith`, `endswith`; `re.search`.",
        intuition="NGINX narrows twice. First by where the connection arrived (address and port), then by the name the client asked for. Names are tried by kind, most specific kind first; file order only breaks ties inside a kind and orders the regexes.",
        hints=[
            "Build the candidate list first. An address-specific `listen` beats `*:port` completely: if any exist, wildcard listeners are not candidates at all.",
            "Do four separate passes over the candidates (exact, leading wildcard, trailing wildcard, regex). Do not try to decide in a single pass.",
            "For the wildcard passes keep the best length seen so far and replace it only when strictly longer, so that earlier servers win ties.",
        ],
        brute_force="One loop over the servers that returns the first name matching in any way. It fails whenever a wildcard server is written before the exact one, which is the classic real-world surprise this algorithm prevents.",
        approach="1. Stage A: candidates with `listen == ip:port`, else those with `*:port`, else `-1`.\n2. Normalise the host: lower-case, cut at `:`.\n3. Pass 1: exact names (and `.x` as `x`).\n4. Pass 2: suffixes from `*.x` and `.x`; keep the longest.\n5. Pass 3: prefixes from `x.*`; keep the longest.\n6. Pass 4: regexes in order.\n7. Fallback: the flagged default, else the first candidate.\n\nDry run: names `*.test` (0), `*.shop.test` (1), `www.shop.*` (2), host `www.shop.test`. No exact match. Leading wildcards: `.test` (5 chars) and `.shop.test` (10 chars) both match; the longer wins → server 1. The trailing wildcard is never consulted.",
        complexity="Time O(total number of names × host length); space O(number of servers) for the candidate list. Real NGINX uses hash tables for the first three passes.",
        pitfalls="Forgetting stage A; treating `_` as a wildcard (it is an ordinary name); letting `*.shop.test` match `shop.test` itself; comparing case-sensitively; keeping the port in the host.",
        follow_up="Add IPv6 listen addresses, and the rule that a request with an invalid Host header is still routed to the default server.",
    ),
),
dict(
    id="nginx-directive-inheritance",
    title="Directive Inheritance Across Levels",
    difficulty="Easy",
    pattern="Configuration",
    entry="effective_config",
    description=r"""
NGINX configuration is nested: `http` contains `server`, which contains `location`. Write
`effective_config(levels, not_inherited)` that returns the directives in force at the **innermost** level.

- `levels` is a list of dictionaries from outermost to innermost. Each maps a directive name to its value: a string for
  ordinary directives, or a **list** of strings for directives that may be repeated (`add_header`, `proxy_set_header`,
  `limit_req` and so on).
- **Ordinary rule:** the innermost level that sets a directive wins.
- **Repeated directives follow the same rule and do not merge:** if an inner level sets `add_header` at all, the lists
  from outer levels are dropped entirely.
- `not_inherited` lists directives that act only at the level where they are written (`return`, `proxy_pass`,
  `try_files`, `rewrite`). They appear in the result only if the innermost level itself sets them.

Return a dictionary. Lists must be new lists with the same items in the same order.

**Example:** `[{"gzip": "on", "add_header": ["X-A 1", "X-B 2"]}, {"root": "/srv"}, {"add_header": ["X-C 3"]}]`,
`[]` → `{"gzip": "on", "root": "/srv", "add_header": ["X-C 3"]}`
""",
    starter='''def effective_config(levels, not_inherited):
    # return the directives in force at the innermost level
    pass
''',
    solution='''def effective_config(levels, not_inherited):
    skip = set(not_inherited)
    out = {}
    last = len(levels) - 1
    for depth, level in enumerate(levels):
        for name, value in level.items():
            if name in skip and depth != last:
                continue
            out[name] = list(value) if isinstance(value, list) else value
    return out
''',
    tests=[
        [[{"gzip": "on", "add_header": ["X-A 1", "X-B 2"]}, {"root": "/srv"}, {"add_header": ["X-C 3"]}], []],
        [[{"gzip": "on"}, {}, {"gzip": "off"}], []],
        [[{"gzip": "on"}, {"gzip": "off"}, {}], []],
        [[], []],
        [[{}], ["return"]],
        [[{"client_max_body_size": "1m"}, {"client_max_body_size": "8m", "proxy_pass": "http://app"}, {"root": "/srv"}], ["proxy_pass", "return"]],
        [[{"client_max_body_size": "1m"}, {"return": "444"}, {"return": "200"}], ["proxy_pass", "return"]],
        [[{"proxy_set_header": ["Host $host", "X-Real-IP $remote_addr"]}, {"proxy_set_header": ["Connection ''"]}, {"proxy_pass": "http://app"}], ["proxy_pass"]],
        [[{"add_header": ["A 1"]}, {"add_header": ["B 2"]}, {"add_header": ["C 3", "D 4"]}], []],
        [[{"add_header": ["A 1"]}, {"add_header": []}, {}], []],
        [[{"limit_req": ["zone=general burst=40"]}, {"limit_req": ["zone=login burst=5"], "try_files": "$uri =404"}], ["try_files"]],
        [[{"a": "1"}, {"b": "2"}, {"c": "3"}, {"a": "4", "d": "5"}], ["b"]],
    ],
    examples=2,
    wrong_solutions=[
        '''def effective_config(levels, not_inherited):
    out = {}
    for level in levels:
        for name, value in level.items():
            if isinstance(value, list):
                out[name] = out.get(name, []) + list(value)
            else:
                out[name] = value
    return {k: v for k, v in out.items() if k not in not_inherited or k in levels[-1]} if levels else {}
''',
        '''def effective_config(levels, not_inherited):
    out = {}
    for level in levels:
        for name, value in level.items():
            out[name] = list(value) if isinstance(value, list) else value
    return out
''',
    ],
    guide=dict(
        prereqs="Dictionaries and lists. Lesson: *Installing NGINX and reading nginx.conf* (contexts and inheritance).",
        intuition="Walk from the outside in and let each level overwrite what it mentions. Two refinements: a list is replaced, never extended, and some directives are actions that never travel inward.",
        hints=[
            "Start with an empty result and process `levels` in order; later assignments overwrite earlier ones.",
            "For a list value, assign a copy of the inner list. Do not concatenate with the outer one.",
            "When a directive is in `not_inherited`, accept it only while processing the last level.",
        ],
        brute_force="For every directive name appearing anywhere, scan the levels from innermost to outermost for the first one that defines it. Same answer, O(names × levels).",
        approach="1. `out = {}`.\n2. For each level with its depth: for each directive, skip it when it is not inherited and this is not the last level; otherwise store it (copying lists).\n3. Return `out`.\n\nDry run on the example: after level 0, `gzip=on`, `add_header=[X-A 1, X-B 2]`. Level 1 adds `root`. Level 2 sets `add_header`, replacing the list with `[X-C 3]`. The two outer headers are gone, which is exactly the trap that removes security headers in real configurations.",
        complexity="Time O(total number of directives across levels); space O(number of distinct directives).",
        pitfalls="Merging lists; mutating the input lists by returning the same object; dropping a not-inherited directive even when the innermost level sets it; crashing on an empty `levels`.",
        follow_up="Recent NGINX versions let some list directives opt in to merging. Add a third argument naming directives whose lists should be concatenated.",
    ),
),
dict(
    id="nginx-location-match",
    title="Pick the Location Block",
    difficulty="Medium",
    pattern="Request Routing",
    entry="match_location",
    description=r"""
Implement NGINX's location selection. `match_location(locations, uri)` returns the **index** of the location that
handles `uri`, or `-1` if none does.

Each location is `[modifier, pattern]` in configuration order. Modifiers:

| Modifier | Meaning |
|---|---|
| `"="` | exact match of the whole URI |
| `""` | prefix match |
| `"^~"` | prefix match that, when it is the longest matching prefix, stops the search |
| `"~"` | case-sensitive regular expression (`re.search`) |
| `"~*"` | case-insensitive regular expression |

Algorithm:

1. If an exact location equals the URI, it wins.
2. Among prefix locations (`""` and `"^~"`), remember the **longest** that the URI starts with.
3. If that longest prefix has `^~`, it wins.
4. Otherwise test the regex locations **in order**; the first that matches wins.
5. If no regex matches, the remembered prefix wins; with no prefix either, return `-1`.

**Example:** `[["", "/images/"], ["~", "\\.(png|jpg)$"]]`, `"/images/logo.png"` → `1`

**Example:** `[["^~", "/images/"], ["~", "\\.(png|jpg)$"]]`, `"/images/logo.png"` → `0`
""",
    starter='''def match_location(locations, uri):
    # return the index of the winning location, or -1
    pass
''',
    solution=r'''import re

def match_location(locations, uri):
    for i, (mod, pat) in enumerate(locations):
        if mod == "=" and uri == pat:
            return i
    best = -1
    for i, (mod, pat) in enumerate(locations):
        if mod in ("", "^~") and uri.startswith(pat):
            if best == -1 or len(pat) > len(locations[best][1]):
                best = i
    if best != -1 and locations[best][0] == "^~":
        return best
    for i, (mod, pat) in enumerate(locations):
        if mod == "~" and re.search(pat, uri):
            return i
        if mod == "~*" and re.search(pat, uri, re.I):
            return i
    return best
''',
    tests=[
        [[["", "/images/"], ["~", r"\.(png|jpg)$"]], "/images/logo.png"],
        [[["^~", "/images/"], ["~", r"\.(png|jpg)$"]], "/images/logo.png"],
        [[["=", "/"], ["", "/"]], "/"],
        [[["=", "/"], ["", "/"]], "/index.html"],
        [[["~", r"^/api/"], ["~", r"\.json$"]], "/api/data.json"],
        [[["~", r"\.json$"], ["~", r"^/api/"]], "/api/data.json"],
        [[["", "/"], ["", "/docs/"], ["", "/docs/private/"]], "/docs/private/a.txt"],
        [[["", "/docs/"], ["~*", r"\.PDF$"]], "/docs/guide.pdf"],
        [[["", "/docs/"], ["~", r"\.PDF$"]], "/docs/guide.pdf"],
        [[["", "/api"]], "/apiary/list"],
        [[["", "/api/"]], "/apiary/list"],
        [[["^~", "/static/"], ["", "/static/img/"], ["~", r"\.png$"]], "/static/img/a.png"],
        [[["", "/a/"], ["^~", "/a/b/"], ["~", r"c$"], ["=", "/a/b/c"]], "/a/b/c"],
        [[["", "/a/"], ["^~", "/a/b/"], ["~", r"c$"], ["=", "/a/b/c"]], "/a/b/cc"],
        [[], "/anything"],
    ],
    examples=2,
    wrong_solutions=[
        r'''import re

def match_location(locations, uri):
    for i, (mod, pat) in enumerate(locations):
        if mod == "=" and uri == pat:
            return i
    best = -1
    for i, (mod, pat) in enumerate(locations):
        if mod in ("", "^~") and uri.startswith(pat):
            if best == -1 or len(pat) > len(locations[best][1]):
                best = i
    if best != -1:
        return best
    for i, (mod, pat) in enumerate(locations):
        if mod in ("~", "~*") and re.search(pat, uri, re.I if mod == "~*" else 0):
            return i
    return -1
''',
        r'''import re

def match_location(locations, uri):
    for i, (mod, pat) in enumerate(locations):
        if mod == "=" and uri == pat:
            return i
    for i, (mod, pat) in enumerate(locations):
        if mod in ("~", "~*") and re.search(pat, uri, re.I if mod == "~*" else 0):
            return i
    best = -1
    for i, (mod, pat) in enumerate(locations):
        if mod in ("", "^~") and uri.startswith(pat):
            if best == -1 or len(pat) > len(locations[best][1]):
                best = i
    return best
''',
    ],
    guide=dict(
        prereqs="Lesson: *How NGINX picks a location block*. `str.startswith`, `re.search` with `re.I`.",
        intuition="Three kinds of location compete in a fixed order of authority: exact, then prefix, then regex, with one twist. A regex normally overrules the best prefix, unless that prefix carries `^~`, which is the author saying \"do not ask the regexes\".",
        hints=[
            "Handle the exact modifier in its own first loop and return immediately.",
            "Find the longest matching prefix before looking at any regex, and keep its index.",
            "Only the *longest* prefix's `^~` matters. A shorter `^~` prefix that also matches has no effect.",
        ],
        brute_force="There is nothing cheaper than three linear passes for a list this small. The mistake to avoid is collapsing them into one pass that returns the first thing that matches.",
        approach="1. Pass 1: exact.\n2. Pass 2: longest prefix among `\"\"` and `\"^~\"`.\n3. If its modifier is `^~`, return it.\n4. Pass 3: regexes in file order, honouring case sensitivity.\n5. Return the remembered prefix (or -1).\n\nDry run: locations `/a/` (0), `^~ /a/b/` (1), `~ c$` (2), `= /a/b/c` (3); URI `/a/b/cc`. No exact match. Prefixes `/a/` and `/a/b/` match; the longest is index 1, which has `^~`, so the answer is 1 and the regex at index 2, which would have matched, is never tried.",
        complexity="Time O(L × |uri|) for L locations; space O(1). NGINX stores prefixes in a tree, so its prefix step is faster.",
        pitfalls="Letting the longest prefix beat a matching regex; honouring `^~` on a prefix that is not the longest; choosing the longest or most specific regex instead of the first; forgetting that `/api` is a prefix of `/apiary`.",
        follow_up="Add named locations (`@name`), which never match a URI, and model the internal redirect done by `index` so that `/` ends up in the location for `/index.html`.",
    ),
),
dict(
    id="nginx-try-files",
    title="Resolve try_files",
    difficulty="Medium",
    pattern="Request Routing",
    entry="try_files",
    description=r"""
`try_files` checks a list of candidates and uses the first that exists; the **last** argument is special. Write
`try_files(files, dirs, args, uri)`.

- `files` lists existing files and `dirs` existing folders, as absolute URL paths under the site root (`"/"` is the
  root folder; other folders have no trailing slash, e.g. `"/docs"`).
- `args` are the directive's arguments, at least one. The text `$uri` inside an argument is replaced by `uri`.

For every argument **except the last**, in order:

- If it ends with `/`, it asks for a **folder**: strip the trailing slashes (an empty result means `"/"`). If that
  folder exists, return `["dir", folder]`.
- Otherwise it asks for a **file**: if it exists, return `["file", path]`.

If none exists, the last argument is a **fallback** that is used without any existence check:

- `=CODE` → `["status", CODE]` with CODE as an integer,
- `@name` → `["named", "@name"]`,
- anything else → `["redirect", path]`, an internal redirect to that URI.

**Example:** files `["/index.html", "/app.js"]`, dirs `["/"]`, args `["$uri", "$uri/", "/index.html"]`:
`"/app.js"` → `["file", "/app.js"]`; `"/tea/oolong"` → `["redirect", "/index.html"]`
""",
    starter='''def try_files(files, dirs, args, uri):
    # return ["file", path], ["dir", path], ["status", code], ["named", name] or ["redirect", uri]
    pass
''',
    solution='''def try_files(files, dirs, args, uri):
    file_set, dir_set = set(files), set(dirs)
    for arg in args[:-1]:
        path = arg.replace("$uri", uri)
        if path.endswith("/"):
            folder = path.rstrip("/") or "/"
            if folder in dir_set:
                return ["dir", folder]
        elif path in file_set:
            return ["file", path]
    last = args[-1].replace("$uri", uri)
    if last.startswith("="):
        return ["status", int(last[1:])]
    if last.startswith("@"):
        return ["named", last]
    return ["redirect", last]
''',
    tests=[
        [["/index.html", "/app.js"], ["/"], ["$uri", "$uri/", "/index.html"], "/app.js"],
        [["/index.html", "/app.js"], ["/"], ["$uri", "$uri/", "/index.html"], "/tea/oolong"],
        [["/index.html", "/app.js"], ["/"], ["$uri", "$uri/", "=404"], "/missing.css"],
        [["/index.html", "/docs/a.html"], ["/", "/docs"], ["$uri", "$uri/", "=404"], "/docs"],
        [["/index.html", "/docs/a.html"], ["/", "/docs"], ["$uri", "$uri/", "=404"], "/docs/"],
        [["/index.html"], ["/"], ["$uri", "$uri/", "=404"], "/"],
        [["/a.html"], ["/"], ["$uri", "$uri.html", "=404"], "/a"],
        [["/a.html"], ["/"], ["$uri", "$uri.html", "@app"], "/b"],
        [["/maintenance.html", "/a.html"], ["/"], ["/maintenance.html", "$uri", "=404"], "/a.html"],
        [[], [], ["/index.html"], "/x"],
        [["/index.html"], ["/"], ["=503"], "/index.html"],
        [["/cache/x"], ["/", "/cache"], ["/cache$uri", "@backend"], "/x"],
        [["/cache/x"], ["/", "/cache"], ["/cache$uri", "@backend"], "/y"],
        [["/fallback"], ["/"], ["$uri", "/fallback"], "/nope"],
        [[], ["/"], ["$uri", "/does-not-exist"], "/nope"],
    ],
    examples=2,
    wrong_solutions=[
        '''def try_files(files, dirs, args, uri):
    file_set, dir_set = set(files), set(dirs)
    for arg in args:
        path = arg.replace("$uri", uri)
        if path.startswith("="):
            return ["status", int(path[1:])]
        if path.startswith("@"):
            return ["named", path]
        if path.endswith("/"):
            folder = path.rstrip("/") or "/"
            if folder in dir_set:
                return ["dir", folder]
        elif path in file_set:
            return ["file", path]
    return ["status", 404]
''',
        '''def try_files(files, dirs, args, uri):
    file_set = set(files) | set(dirs)
    for arg in args[:-1]:
        path = arg.replace("$uri", uri)
        if (path.rstrip("/") or "/") in file_set:
            return ["file", path]
    last = args[-1].replace("$uri", uri)
    if last.startswith("="):
        return ["status", int(last[1:])]
    if last.startswith("@"):
        return ["named", last]
    return ["redirect", last]
''',
    ],
    guide=dict(
        prereqs="Lesson: *try_files, return, rewrite and the proxy_pass slash*. Sets for fast membership tests.",
        intuition="Every argument but the last is a question (\"does this exist?\"). The last is an instruction (\"then do this\"), carried out without asking. A trailing slash turns a question about a file into a question about a folder.",
        hints=[
            "Slice the list: loop over `args[:-1]`, then treat `args[-1]` separately.",
            "A path ending in `/` must be looked up in `dirs`, never in `files`.",
            "The fallback is not checked for existence. `/index.html` as the last argument produces a redirect even if the file is missing.",
        ],
        brute_force="Check each candidate against the lists with `in` on a list: O(n) per check. Converting to sets first makes each check O(1).",
        approach="1. Build sets.\n2. For each non-final argument substitute `$uri`; branch on the trailing slash; return on the first hit.\n3. Classify the final argument by its first character.\n\nDry run: args `$uri $uri/ =404`, URI `/docs`, files `/docs/a.html`, dirs `/`, `/docs`. Candidate 1 `/docs` is not a file. Candidate 2 `/docs/` → folder `/docs` exists → `[\"dir\", \"/docs\"]`. In NGINX the index module then looks for an index file inside it.",
        complexity="Time O(len(args) + len(files) + len(dirs)); space O(len(files) + len(dirs)).",
        pitfalls="Checking the fallback for existence; treating `=404` in the middle of the list as special; accepting a folder for a file candidate; mishandling the root URI `/`, whose folder candidate is `//`.",
        follow_up="Model the loop: when the fallback redirects to a URI that again falls through to the same fallback, NGINX stops after ten rounds with a 500. Detect that.",
    ),
),
dict(
    id="nginx-proxy-pass-uri",
    title="The proxy_pass Trailing Slash",
    difficulty="Easy",
    pattern="Reverse Proxy",
    entry="upstream_uri",
    description=r"""
Given a prefix `location`, the value of `proxy_pass`, and the client's request URI, return the URI that NGINX sends to
the upstream server.

- If `proxy_pass` has **no URI part**, meaning nothing after the host and optional port, the request URI is passed
  unchanged.
- If it **has a URI part**, even a single `/`, the part of the path matched by the location prefix is replaced by that
  URI part.
- The query string (from `?` on) is always kept as it is.

You may assume the request path starts with `location`.

**Example:** `"/app/"`, `"http://backend/"`, `"/app/users?id=7"` → `"/users?id=7"`

**Example:** `"/app/"`, `"http://backend"`, `"/app/users?id=7"` → `"/app/users?id=7"`
""",
    starter='''def upstream_uri(location, proxy_pass, request_uri):
    # return the URI sent to the upstream
    pass
''',
    solution='''def upstream_uri(location, proxy_pass, request_uri):
    path, mark, query = request_uri.partition("?")
    host, slash, uri_part = proxy_pass.split("://", 1)[1].partition("/")
    if slash:
        path = "/" + uri_part + path[len(location):]
    return path + mark + query
''',
    tests=[
        ["/app/", "http://backend/", "/app/users?id=7"],
        ["/app/", "http://backend", "/app/users?id=7"],
        ["/app/", "http://backend/v2/", "/app/users?id=7"],
        ["/app/", "http://backend/v2", "/app/users"],
        ["/app", "http://backend/", "/app/users"],
        ["/", "http://127.0.0.1:8000", "/api/cart"],
        ["/", "http://127.0.0.1:8000/", "/api/cart"],
        ["/api/", "http://10.0.0.5:8080/internal/api/", "/api/"],
        ["/api/", "https://svc.internal/", "/api/a/b/c?x=1&y=/z"],
        ["/v1/users/", "http://users_svc/", "/v1/users/42/orders"],
        ["/a/", "http://b/c", "/a/?q=http://x/y"],
        ["/files/", "http://store:9000/bucket/", "/files/a%20b.txt"],
        ["/a/", "http://b/c/", "/a/x/a/y?next=/a/z"],
    ],
    examples=2,
    wrong_solutions=[
        '''def upstream_uri(location, proxy_pass, request_uri):
    path, mark, query = request_uri.partition("?")
    return "/" + path[len(location):].lstrip("/") + mark + query
''',
        '''def upstream_uri(location, proxy_pass, request_uri):
    rest = proxy_pass.split("://", 1)[1]
    if "/" not in rest:
        return request_uri
    uri_part = rest[rest.index("/"):]
    return request_uri.replace(location, uri_part)
''',
    ],
    guide=dict(
        prereqs="Lesson: *try_files, return, rewrite and the proxy_pass slash*. `str.partition`.",
        intuition="NGINX asks one question: did the author write a path on `proxy_pass`? No path means \"send what you received\". A path means \"swap the matched prefix for my path\", and a lone slash is a path.",
        hints=[
            "Separate the query string first with `partition(\"?\")` and glue it back at the end.",
            "Remove the scheme with `split(\"://\", 1)`, then `partition(\"/\")` tells you whether a URI part exists and what it is.",
            "The replacement is plain string surgery: URI part + the path after the location prefix. Do not add or remove slashes.",
        ],
        brute_force="Not applicable; this is constant-time string handling. The naive mistake is `str.replace(location, ...)`, which also rewrites later occurrences of the prefix inside the path or the query.",
        approach="1. `path, mark, query = request_uri.partition(\"?\")`.\n2. `host, slash, uri_part = after_scheme.partition(\"/\")`.\n3. If `slash` is empty return the original. Otherwise new path = `\"/\" + uri_part + path[len(location):]`.\n\nDry run: location `/app/`, `http://backend/v2`, request `/app/users`. URI part is `v2`; the path after the prefix is `users`; result `/v2users`. That missing slash is a real and common bug, and the function reproduces it faithfully.",
        complexity="Time and space O(length of the URI).",
        pitfalls="Normalising slashes (NGINX does not); losing the query string; treating a port (`:8000`) as a URI part; using `replace`, which may touch the query.",
        follow_up="When `proxy_pass` contains variables, or the location is a regex, NGINX cannot do the replacement and passes the URI as given. Add a flag for that case.",
    ),
),
dict(
    id="nginx-rewrite-eval",
    title="Evaluate rewrite and return Directives",
    difficulty="Medium",
    pattern="Request Routing",
    entry="rewrite_eval",
    description=r"""
Simulate the rewrite module for a list of directives written at one level. `rewrite_eval(directives, uri)` returns
`[status, uri_or_url]`. The URI has no query string in this problem.

Directives are processed in order. Each is one of:

- `["return", code, text]`: stop immediately and return `[code, text]`, with every `$uri` in `text` replaced by the
  **current** URI.
- `["rewrite", regex, replacement, flag]`: if `re.search(regex, uri)` finds nothing, go on to the next directive.
  Otherwise build the new value from `replacement`, replacing `$1`..`$9` with the regex groups (a group that does not
  exist or did not take part becomes the empty string). Then:
  - if the new value starts with `http://` or `https://`: return `[301, value]` when the flag is `"permanent"`,
    otherwise `[302, value]`;
  - flag `"permanent"`: return `[301, value]`; flag `"redirect"`: return `[302, value]`;
  - otherwise the URI becomes the new value. With flag `"last"` or `"break"` processing stops; with the empty flag
    `""` it continues with the next directive.

If processing ends without a redirect or a `return`, the answer is `[200, current_uri]`.

**Example:** `[["rewrite", "^/old/(.*)$", "/new/$1", "last"], ["return", 404, ""]]`, `"/old/page"` → `[200, "/new/page"]`

**Example:** the same directives with `"/other"` → `[404, ""]`
""",
    starter='''def rewrite_eval(directives, uri):
    # return [status, uri_or_url]
    pass
''',
    solution=r'''import re

def rewrite_eval(directives, uri):
    for d in directives:
        if d[0] == "return":
            return [d[1], d[2].replace("$uri", uri)]
        regex, replacement, flag = d[1], d[2], d[3]
        m = re.search(regex, uri)
        if not m:
            continue
        def group(g):
            n = int(g.group(1))
            return (m.group(n) or "") if n <= m.re.groups else ""
        value = re.sub(r"\$([1-9])", group, replacement)
        if value.startswith("http://") or value.startswith("https://"):
            return [301 if flag == "permanent" else 302, value]
        if flag == "permanent":
            return [301, value]
        if flag == "redirect":
            return [302, value]
        uri = value
        if flag in ("last", "break"):
            break
    return [200, uri]
''',
    tests=[
        [[["rewrite", r"^/old/(.*)$", "/new/$1", "last"], ["return", 404, ""]], "/old/page"],
        [[["rewrite", r"^/old/(.*)$", "/new/$1", "last"], ["return", 404, ""]], "/other"],
        [[["rewrite", r"^/a$", "/b", ""], ["rewrite", r"^/b$", "/c", ""], ["rewrite", r"^/c$", "/d", "break"], ["rewrite", r"^/d$", "/e", ""]], "/a"],
        [[["rewrite", r"^/blog/(\d+)/(\w+)$", "/posts?id=$1&slug=$2", "permanent"]], "/blog/42/hello"],
        [[["rewrite", r"^/blog/(\d+)/(\w+)$", "/posts/$2/$1", "redirect"]], "/blog/42/hello"],
        [[["rewrite", r"^/go/(.*)$", "https://example.org/$1", ""]], "/go/docs"],
        [[["rewrite", r"^/go/(.*)$", "https://example.org/$1", "permanent"]], "/go/docs"],
        [[["return", 301, "https://shop.test$uri"]], "/tea"],
        [[["rewrite", r"^/x(/.*)?$", "/y$1", ""], ["return", 302, "https://shop.test$uri"]], "/x/z"],
        [[["rewrite", r"^/x(/.*)?$", "/y$1$2", ""]], "/x"],
        [[], "/keep"],
        [[["rewrite", r"\.php$", "/gone", "last"], ["rewrite", r"^/gone$", "/never", ""]], "/index.php"],
        [[["rewrite", r"(?i)^/Docs/(.*)", "/docs/$1", ""], ["rewrite", r"^/docs/(.*)\.htm$", "/docs/$1.html", "break"]], "/DOCS/a.htm"],
        [[["rewrite", r"^/a", "/a/a", ""], ["rewrite", r"^/a", "/b", ""]], "/a"],
    ],
    examples=2,
    wrong_solutions=[
        r'''import re

def rewrite_eval(directives, uri):
    for d in directives:
        if d[0] == "return":
            return [d[1], d[2].replace("$uri", uri)]
        m = re.search(d[1], uri)
        if not m:
            continue
        value = re.sub(r"\$([1-9])", lambda g: (m.group(int(g.group(1))) or "") if int(g.group(1)) <= m.re.groups else "", d[2])
        if d[3] == "permanent":
            return [301, value]
        if d[3] == "redirect" or value.startswith("http"):
            return [302, value]
        uri = value
    return [200, uri]
''',
        r'''import re

def rewrite_eval(directives, uri):
    original = uri
    for d in directives:
        if d[0] == "return":
            return [d[1], d[2].replace("$uri", original)]
        m = re.search(d[1], original)
        if not m:
            continue
        value = re.sub(r"\$([1-9])", lambda g: (m.group(int(g.group(1))) or "") if int(g.group(1)) <= m.re.groups else "", d[2])
        if value.startswith("http://") or value.startswith("https://"):
            return [301 if d[3] == "permanent" else 302, value]
        if d[3] == "permanent":
            return [301, value]
        if d[3] == "redirect":
            return [302, value]
        uri = value
        if d[3] in ("last", "break"):
            break
    return [200, uri]
''',
    ],
    guide=dict(
        prereqs="Lesson: *try_files, return, rewrite and the proxy_pass slash*. Regular expression groups.",
        intuition="The rewrite module is a tiny program run top to bottom with one register, the current URI. `rewrite` may change the register and may stop the program; `return` always stops it and answers the client.",
        hints=[
            "Keep one variable for the current URI and update it after each successful internal rewrite; later directives must see the new value.",
            "Decide redirects before flags: a replacement beginning with a scheme is a redirect whatever the flag says.",
            "Both `last` and `break` end this list of directives. Only the empty flag lets processing continue.",
        ],
        brute_force="There is no asymptotically different approach; the work is in getting the control flow exactly right. Writing the four outcomes as an explicit if-chain is clearer than trying to be clever.",
        approach="1. Loop over the directives.\n2. `return`: substitute `$uri`, answer.\n3. `rewrite`: search; on a match expand `$1`..`$9`; check for an absolute URL, then `permanent`, then `redirect`; otherwise assign and stop on `last` or `break`.\n4. After the loop answer `[200, uri]`.\n\nDry run: `/a` through `^/a$→/b`, `^/b$→/c`, `^/c$→/d break`, `^/d$→/e`. The URI becomes `/b`, `/c`, `/d`, and `break` stops before the fourth rule: `[200, \"/d\"]`.",
        complexity="Time O(number of directives × cost of each regex search); space O(length of the URI).",
        pitfalls="Matching against the original URI instead of the current one; continuing after `last`; treating only the `redirect` flag as a redirect and missing absolute URLs; crashing on `$2` when the regex has one group.",
        follow_up="In a real server `last` restarts location matching and `break` does not. Combine this function with `match_location` and stop after ten rounds with a 500, as NGINX does.",
    ),
),
]
