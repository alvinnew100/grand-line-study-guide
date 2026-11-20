_ROUTES = [
    ["", "home"],
    ["stories/", "story-list"],
    ["stories/new/", "story-new"],
    ["stories/<int:pk>/", "story-detail"],
    ["stories/<int:pk>/edit/", "story-edit"],
    ["topics/<slug:slug>/", "topic"],
    ["members/<handle>/", "member"],
    ["files/<path:where>", "file"],
    ["receipts/<uuid:token>/", "receipt"],
    ["archive/<int:year>/<int:month>/", "archive"],
    ["stories/<slug:slug>/", "story-by-slug"],
]

_MW = [
    {"name": "Security"},
    {"name": "Session"},
    {"name": "Csrf"},
    {"name": "Auth"},
]

PROBLEMS = [
dict(
    id="django-url-match",
    title="Resolve a URL with path converters",
    difficulty="Medium",
    pattern="Routing",
    entry="resolve",
    description=r"""
Django's URL resolver walks `urlpatterns` from top to bottom and stops at the **first** route that matches the
whole request path. Build that resolver for `path()`-style routes.

`resolve(patterns, path)`:

- `patterns` is a list of `[route, name]` pairs in priority order. A route is written like the first argument of
  `path()`: literal text plus captures such as `<int:pk>` or `<slug>`.
- `path` is the request path and always starts with `/`. Remove that one leading slash before matching
  (Django does the same), then the **entire** remainder must match the route.

Converters and what they accept:

| converter | accepts | Python value |
|---|---|---|
| `str` (also used when no converter is written, as in `<handle>`) | one or more characters, none of them `/` | `str` |
| `int` | one or more digits `0-9` | `int` |
| `slug` | one or more of ASCII letters, digits, `-`, `_` | `str` |
| `uuid` | lower-case `8-4-4-4-12` hexadecimal groups separated by `-` | `str` (unchanged) |
| `path` | one or more characters, `/` allowed | `str` |

Return `[name, kwargs]` for the first matching route, where `kwargs` maps each captured name to its converted
value, or `None` when nothing matches. There is no automatic slash appending.

**Example:** with routes `[["stories/<int:pk>/", "story-detail"]]`, `resolve(routes, "/stories/42/")` →
`["story-detail", {"pk": 42}]`, while `"/stories/42"` and `"/stories/abc/"` → `None`.
""",
    starter='''def resolve(patterns: list, path: str):
    pass
''',
    solution=r'''import re

_CONV = {
    "str": r"[^/]+",
    "int": r"[0-9]+",
    "slug": r"[-a-zA-Z0-9_]+",
    "uuid": r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
    "path": r".+",
}
_CAPTURE = re.compile(r"<(?:([a-z]+):)?([A-Za-z_][A-Za-z0-9_]*)>")


def _compile(route):
    regex, kinds, pos = "", {}, 0
    for m in _CAPTURE.finditer(route):
        regex += re.escape(route[pos:m.start()])
        kind = m.group(1) or "str"
        kinds[m.group(2)] = kind
        regex += "(?P<%s>%s)" % (m.group(2), _CONV[kind])
        pos = m.end()
    return regex + re.escape(route[pos:]), kinds


def resolve(patterns, path):
    rest = path[1:] if path.startswith("/") else path
    for route, name in patterns:
        regex, kinds = _compile(route)
        m = re.fullmatch(regex, rest)
        if m:
            return [name, {k: int(v) if kinds[k] == "int" else v for k, v in m.groupdict().items()}]
    return None
''',
    tests=[
        [_ROUTES, "/stories/42/"],
        [_ROUTES, "/"],
        [_ROUTES, "/stories/new/"],
        [_ROUTES, "/stories/42"],
        [_ROUTES, "/stories/007/edit/"],
        [_ROUTES, "/topics/tide-tables_2/"],
        [_ROUTES, "/topics/tide tables/"],
        [_ROUTES, "/members/ana.k/"],
        [_ROUTES, "/members/ana/k/"],
        [_ROUTES, "/files/2026/q3/report.pdf"],
        [_ROUTES, "/receipts/0a1b2c3d-0000-4abc-8def-0123456789ab/"],
        [_ROUTES, "/receipts/0A1B2C3D-0000-4ABC-8DEF-0123456789AB/"],
        [_ROUTES, "/archive/2026/11/"],
        [_ROUTES, "/stories/harbour-opens/"],
        [_ROUTES, "/stories/-5/edit/"],
        [[["a.b/", "dot"]], "/axb/"],
        [[], "/anything/"],
    ],
    examples=3,
    wrong_solutions=[
        r'''import re
def resolve(patterns, path):
    rest = path[1:]
    for route, name in patterns:
        regex = re.sub(r"<(?:[a-z]+:)?(\w+)>", r"(?P<\1>[^/]+)", route)
        m = re.fullmatch(regex, rest)
        if m:
            return [name, m.groupdict()]
    return None
''',
        r'''import re
_CONV = {"str": r".+", "int": r"[0-9]+", "slug": r"[-a-zA-Z0-9_]+", "uuid": r"[0-9a-f-]{36}", "path": r".+"}
def resolve(patterns, path):
    rest = path[1:]
    for route, name in patterns:
        kinds = {}
        def sub(m):
            kinds[m.group(2)] = m.group(1) or "str"
            return "(?P<%s>%s)" % (m.group(2), _CONV[m.group(1) or "str"])
        regex = re.sub(r"<(?:([a-z]+):)?(\w+)>", sub, route)
        m = re.match(regex, rest)
        if m:
            return [name, {k: int(v) if kinds[k] == "int" else v for k, v in m.groupdict().items()}]
    return None
''',
    ],
    guide=dict(
        prereqs="The lesson *The request/response cycle, views, URLs and first tests*; Python's `re` module (`fullmatch`, named groups).",
        intuition="Every route is a tiny regular expression in disguise. Translate `<int:pk>` into a named group with the "
                  "converter's regex, escape the literal text around it, and the resolver becomes: try each compiled "
                  "pattern in order with a whole-string match, convert the captured text, stop at the first hit.",
        hints=[
            "Find captures with one regex such as `<(?:([a-z]+):)?(name)>`; the converter group is optional.",
            "Escape the literal pieces with `re.escape` so a dot in a route does not match any character.",
            "Use `re.fullmatch`, not `re.match`, and convert only `int` captures with `int()`.",
        ],
        brute_force="Split route and path on `/` and compare segment by segment. It works for `str`, `int` and `slug`, "
                    "but falls apart for `path`, which swallows several segments, and for routes whose capture is only "
                    "part of a segment. It is still O(total length) per route.",
        approach="""1. Strip the single leading `/` from the request path.
2. For each `[route, name]` in order, compile the route: copy literal text through `re.escape`, and replace each
   capture by `(?P<name>regex-of-converter)`, remembering which converter each name used.
3. `re.fullmatch` the compiled regex against the remaining path.
4. On a match, build kwargs, turning `int` captures into integers, and return immediately.
5. If the loop ends, return `None`.

**Dry run** for `/stories/007/edit/`: `""` fails, `stories/` fails (extra text), `stories/new/` fails,
`stories/(?P<pk>[0-9]+)/` fails because `edit/` is left over, `stories/(?P<pk>[0-9]+)/edit/` matches with
`pk="007"` → `["story-edit", {"pk": 7}]`.""",
        complexity="O(P · L) regex work for P patterns and path length L (Django caches the compiled regexes; you could too). Space O(L).",
        pitfalls="""- Using `re.match` accepts a route that only matches a prefix, so `/stories/42/edit/` would hit the detail route.
- Forgetting `re.escape` makes `a.b/` match `axb/`.
- `int` does not accept a minus sign; `str` must not cross a `/`; `uuid` is lower-case only.
- Order matters: `stories/new/` must be listed before a slug route or it would be captured as a slug.""",
        follow_up="Add `include()` support: a prefix route that delegates the rest of the path to a nested pattern list and merges kwargs.",
    ),
),
dict(
    id="django-url-reverse",
    title="reverse(): build a URL from a name and kwargs",
    difficulty="Medium",
    pattern="Routing",
    entry="reverse",
    description=r"""
Templates and views should never hard-code URLs; they ask for one by **name** (`{% url 'story-detail' pk=7 %}`,
`reverse("story-detail", kwargs={"pk": 7})`). Implement the lookup.

`reverse(patterns, name, kwargs)`:

- `patterns` is a list of `[route, name]` pairs (same route syntax as `path()`); several routes may share a name.
- Consider the routes with the requested `name` **in list order**. A route is a candidate only if the set of its
  capture names equals the set of keys in `kwargs` exactly.
- For each capture, turn the supplied value into text with `str(value)`. The text must fully match the converter's
  pattern, otherwise this route is rejected and the next candidate is tried:
  `str` → one or more non-`/` characters; `int` → digits only; `slug` → letters, digits, `-`, `_`;
  `uuid` → lower-case 8-4-4-4-12 hex; `path` → one or more characters. A capture with no converter is `str`.
- Return `"/"` followed by the route with captures replaced by the text. If no route works return `None`
  (Django would raise `NoReverseMatch`).

**Examples** (routes `[["stories/<int:pk>/", "story"], ["stories/<slug:slug>/", "story"]]`):
`reverse(routes, "story", {"pk": 7})` → `"/stories/7/"`; `reverse(routes, "story", {"slug": "low-tide"})` →
`"/stories/low-tide/"`; `reverse(routes, "story", {"pk": -1})` → `None`.
""",
    starter='''def reverse(patterns: list, name: str, kwargs: dict):
    pass
''',
    solution=r'''import re

_CONV = {
    "str": r"[^/]+",
    "int": r"[0-9]+",
    "slug": r"[-a-zA-Z0-9_]+",
    "uuid": r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
    "path": r".+",
}
_CAPTURE = re.compile(r"<(?:([a-z]+):)?([A-Za-z_][A-Za-z0-9_]*)>")


def reverse(patterns, name, kwargs):
    for route, route_name in patterns:
        if route_name != name:
            continue
        captures = _CAPTURE.findall(route)
        if {n for _, n in captures} != set(kwargs):
            continue
        ok = True
        for kind, n in captures:
            if not re.fullmatch(_CONV[kind or "str"], str(kwargs[n])):
                ok = False
                break
        if ok:
            return "/" + _CAPTURE.sub(lambda m: str(kwargs[m.group(2)]), route)
    return None
''',
    tests=[
        [_ROUTES, "story-detail", {"pk": 7}],
        [_ROUTES, "home", {}],
        [_ROUTES, "story-detail", {"pk": -1}],
        [_ROUTES, "story-detail", {}],
        [_ROUTES, "story-detail", {"pk": 7, "extra": 1}],
        [_ROUTES, "story-detail", {"pk": "12"}],
        [_ROUTES, "story-detail", {"pk": True}],
        [_ROUTES, "archive", {"month": 3, "year": 2026}],
        [_ROUTES, "member", {"handle": "ana/k"}],
        [_ROUTES, "member", {"handle": 99}],
        [_ROUTES, "file", {"where": "2026/q3/report.pdf"}],
        [_ROUTES, "topic", {"slug": "not a slug"}],
        [_ROUTES, "nope", {}],
        [[["s/<int:pk>/", "story"], ["s/<slug:slug>/", "story"]], "story", {"slug": "low-tide"}],
        [[["s/<int:key>/", "story"], ["s/<slug:key>/", "story"]], "story", {"key": "low-tide"}],
        [_ROUTES, "receipt", {"token": "0a1b2c3d-0000-4abc-8def-0123456789ab"}],
        [_ROUTES, "member", {"handle": ""}],
    ],
    examples=3,
    wrong_solutions=[
        r'''import re
def reverse(patterns, name, kwargs):
    for route, route_name in patterns:
        if route_name == name:
            try:
                return "/" + re.sub(r"<(?:[a-z]+:)?(\w+)>", lambda m: str(kwargs[m.group(1)]), route)
            except KeyError:
                return None
    return None
''',
        r'''import re
def reverse(patterns, name, kwargs):
    for route, route_name in patterns:
        if route_name != name:
            continue
        names = re.findall(r"<(?:[a-z]+:)?(\w+)>", route)
        if set(names) != set(kwargs):
            return None
        return "/" + re.sub(r"<(?:[a-z]+:)?(\w+)>", lambda m: str(kwargs[m.group(1)]), route)
    return None
''',
    ],
    guide=dict(
        prereqs="Problem *Resolve a URL with path converters*; named URLs and `{% url %}` from the URLs lesson.",
        intuition="Reversing is resolving run backwards: instead of asking 'does this text fit the pattern?' for a whole "
                  "path, ask it for each supplied value, then pour the values into the holes. Because names are not "
                  "unique, a failed candidate means 'keep looking', not 'give up'.",
        hints=[
            "Extract `(converter, name)` pairs from a route with `re.findall`.",
            "Compare the *set* of capture names with the set of kwargs keys before looking at values.",
            "Validate `str(value)` with `re.fullmatch` against the converter regex; on failure `continue`.",
        ],
        brute_force="Substitute first, then run the forward resolver on the produced URL and check it lands on the same "
                    "name with equal kwargs. Correct but does twice the work and needs care with `int` round-trips such as `\"007\"`.",
        approach="""1. Loop over routes whose name matches.
2. Collect captures. Skip the route unless capture names == kwargs keys.
3. For each capture, `str()` the value and `fullmatch` it against the converter pattern. Any failure → next route.
4. Substitute and prefix `/`.

**Dry run** `reverse(routes, "story", {"key": "low-tide"})` with `s/<int:key>/` then `s/<slug:key>/`:
first route has the right key but `"low-tide"` fails `[0-9]+`, so it is skipped; the second accepts it → `/s/low-tide/`.""",
        complexity="O(P · R) where R is route length; the per-value regex checks are linear in the value length.",
        pitfalls="""- Returning `None` at the first same-named route instead of trying the others.
- Accepting extra kwargs, or missing ones: the key sets must be equal.
- `True` becomes `"True"`, which is not an `int`; `-1` becomes `"-1"`, which is not either.
- An empty string never fits `str` or `path`, both need at least one character.""",
        follow_up="Support namespaces (`gazette:story`) by resolving the namespace to a URL prefix first.",
    ),
),
dict(
    id="django-middleware-chain",
    title="Trace the middleware onion",
    difficulty="Medium",
    pattern="Request lifecycle",
    entry="trace",
    description=r"""
Middleware wraps the view like the layers of an onion: the request travels inwards through `MIDDLEWARE` from top to
bottom, the response travels back out from bottom to top. Produce the exact event trace.

`trace(middlewares, view)`:

- `middlewares` is the settings list, outermost first. Each item is a dict with `name` and two optional keys:
  `short_circuit` (default `False`) and `on_exception` (`"ignore"` by default, or `"pass"` or `"handle"`).
- `view` is a dict with `name` and `raises` (bool).

Rules:

1. **Request phase.** For each middleware in order emit `"<name>:request"`. If it has `short_circuit` true it
   returns a response itself: emit `"<name>:short-circuit"` and stop going inwards. Nothing deeper runs
   (no later middleware, no view), and this middleware does not emit a response event.
2. **View.** If nobody short-circuited, emit `"view:<view name>"`.
3. **Exception phase** (only when the view ran and `raises` is true). Walk the middlewares in **reverse** order.
   `"ignore"` emits nothing. `"pass"` emits `"<name>:exception"` and continues. `"handle"` emits
   `"<name>:exception"` then `"<name>:handled"` and stops the walk. If no middleware handled it, emit `"500"`.
4. **Response phase.** Emit `"<name>:response"` in reverse order for every middleware that completed its request
   phase without short-circuiting.

Return the list of events.

**Example:** middlewares `A`, `B` and a normal view `home` →
`["A:request", "B:request", "view:home", "B:response", "A:response"]`.
""",
    starter='''def trace(middlewares: list, view: dict) -> list:
    pass
''',
    solution='''def trace(middlewares, view):
    events, entered, stopped = [], [], False
    for mw in middlewares:
        events.append(mw["name"] + ":request")
        if mw.get("short_circuit", False):
            events.append(mw["name"] + ":short-circuit")
            stopped = True
            break
        entered.append(mw)
    if not stopped:
        events.append("view:" + view["name"])
        if view.get("raises"):
            handled = False
            for mw in reversed(entered):
                mode = mw.get("on_exception", "ignore")
                if mode == "ignore":
                    continue
                events.append(mw["name"] + ":exception")
                if mode == "handle":
                    events.append(mw["name"] + ":handled")
                    handled = True
                    break
            if not handled:
                events.append("500")
    for mw in reversed(entered):
        events.append(mw["name"] + ":response")
    return events
''',
    tests=[
        [[{"name": "A"}, {"name": "B"}], {"name": "home", "raises": False}],
        [_MW, {"name": "story_list", "raises": False}],
        [[{"name": "A"}, {"name": "Maintenance", "short_circuit": True}, {"name": "C"}], {"name": "home", "raises": False}],
        [[], {"name": "home", "raises": False}],
        [[], {"name": "home", "raises": True}],
        [[{"name": "Gate", "short_circuit": True}], {"name": "home", "raises": True}],
        [[{"name": "A", "on_exception": "handle"}, {"name": "B", "on_exception": "pass"}, {"name": "C"}], {"name": "boom", "raises": True}],
        [[{"name": "A", "on_exception": "pass"}, {"name": "B", "on_exception": "pass"}], {"name": "boom", "raises": True}],
        [[{"name": "A", "on_exception": "handle"}, {"name": "B", "on_exception": "handle"}], {"name": "boom", "raises": True}],
        [[{"name": "A", "on_exception": "handle"}, {"name": "B"}], {"name": "fine", "raises": False}],
        [[{"name": "A"}, {"name": "B"}, {"name": "C", "short_circuit": True}], {"name": "v", "raises": True}],
        [[{"name": "A", "short_circuit": False, "on_exception": "ignore"}, {"name": "B", "on_exception": "handle"}, {"name": "C", "short_circuit": True, "on_exception": "handle"}, {"name": "D"}], {"name": "v", "raises": True}],
        [[{"name": "Only"}], {"name": "v", "raises": True}],
    ],
    examples=3,
    wrong_solutions=[
        '''def trace(middlewares, view):
    events = [m["name"] + ":request" for m in middlewares]
    events.append("view:" + view["name"])
    if view.get("raises"):
        events.append("500")
    events += [m["name"] + ":response" for m in middlewares]
    return events
''',
        '''def trace(middlewares, view):
    events, entered, stopped = [], [], False
    for mw in middlewares:
        events.append(mw["name"] + ":request")
        entered.append(mw)
        if mw.get("short_circuit", False):
            events.append(mw["name"] + ":short-circuit")
            stopped = True
            break
    if not stopped:
        events.append("view:" + view["name"])
        if view.get("raises"):
            handled = False
            for mw in entered:
                mode = mw.get("on_exception", "ignore")
                if mode == "ignore":
                    continue
                events.append(mw["name"] + ":exception")
                if mode == "handle":
                    events.append(mw["name"] + ":handled")
                    handled = True
                    break
            if not handled:
                events.append("500")
    for mw in reversed(entered):
        events.append(mw["name"] + ":response")
    return events
''',
    ],
    guide=dict(
        prereqs="Lessons *The request/response cycle, views, URLs and first tests* and *Architecture questions* (middleware order).",
        intuition="A middleware is a function that calls the next function. Code before the call runs on the way in, code "
                  "after it runs on the way out, so the 'out' order is automatically the reverse of the 'in' order. "
                  "Returning without calling the next layer cuts the onion at that depth.",
        hints=[
            "Keep a list of middlewares that were fully entered; the response phase is that list reversed.",
            "A short-circuiting middleware is not added to the list because it never runs its own after-code.",
            "Exception hooks are visited in reverse as well, and the first handler ends the walk.",
        ],
        brute_force="Build real nested closures (`handler = mw(handler)` in reverse order) and let Python's call stack "
                    "produce the order. It is the most faithful model, but harder to extend with the exception rules.",
        approach="""1. Walk inwards, recording `request` events and the entered list; stop at a short-circuit.
2. If the view is reached, record it; when it raises, walk the entered list backwards applying the
   `ignore`/`pass`/`handle` rule, adding `"500"` when nobody handled the error.
3. Walk the entered list backwards again for `response` events.

**Dry run**: `A(handle)`, `B(pass)`, `C` with a raising view → `A:request, B:request, C:request, view:boom`, then
reverse walk: C ignores, `B:exception`, `A:exception, A:handled`; responses `C, B, A`.""",
        complexity="O(n) time and space for n middlewares.",
        pitfalls="""- Emitting responses top-to-bottom instead of bottom-to-top.
- Letting a short-circuiting middleware (or the ones below it) emit `response`.
- Running exception hooks when the view never ran.
- Forgetting that the response phase still happens after an unhandled exception: Django turns it into a 500 response
  that every outer middleware sees.""",
        follow_up="Model `process_view` hooks, which run top-to-bottom after URL resolution and may also short-circuit.",
    ),
),
dict(
    id="django-template-render",
    title="A miniature template engine",
    difficulty="Hard",
    pattern="Templates",
    entry="render",
    description=r"""
Implement `render(template, context)` for a small, precisely defined subset of the Django template language.

**Variables** `{{ expr }}` where `expr` is a dotted path followed by zero or more filters, e.g.
`{{ story.author.name|default:"staff"|upper }}`. Spaces around the expression are optional.

- *Dotted lookup*: resolve the first name in the context dict, then each further part: if the current value is a
  dict containing that key use it; else if it is a list and the part is all digits and a valid index, use that
  item; otherwise the whole lookup is **missing** and evaluates to the empty string `""`.
- *Filters*, applied left to right (arguments are a double-quoted string or an integer and never contain `|`,
  `:` or `"`):
  `lower`, `upper` (applied to `str(value)`); `default:"x"` (the argument when the value is falsy);
  `length` (`len` of a str, list or dict, otherwise `0`); `truncatechars:N` (with `s = str(value)`: `s` if
  `len(s) <= N`, else the first `N-1` characters followed by the single character `…`).
- The final value is written with `str(value)` (so `None` prints `None`, `True` prints `True`). No HTML escaping.

**Tags**

- `{% for item in path %} ... {% endfor %}`: repeats the body for each element when the path resolves to a list
  (anything else: zero times). Inside the body `item` is bound, and `forloop.counter` (1-based),
  `forloop.first` and `forloop.last` are available. Bindings disappear after the loop.
- `{% if path %} ... {% else %} ... {% endif %}` and `{% if not path %}`: the `else` branch is optional; the test
  is Python truthiness of the dotted lookup (missing is false). Filters are not used in `if`.
- Tags nest arbitrarily. Everything else is literal text and is copied unchanged.

**Example:** `render("{% for t in tags %}{{ forloop.counter }}:{{ t|upper }} {% endfor %}", {"tags": ["a", "b"]})`
→ `"1:A 2:B "`.
""",
    starter='''def render(template: str, context: dict) -> str:
    pass
''',
    solution='''import re

_TOKEN = re.compile(r"({{.*?}}|{%.*?%})")


def _lookup(path, ctx):
    cur = ctx
    for part in path.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        elif isinstance(cur, list) and part.isdigit() and int(part) < len(cur):
            cur = cur[int(part)]
        else:
            return ""
    return cur


def _arg(raw):
    raw = raw.strip()
    return raw[1:-1] if raw.startswith('"') else int(raw)


def _evaluate(expr, ctx):
    parts = [p.strip() for p in expr.split("|")]
    val = _lookup(parts[0], ctx)
    for f in parts[1:]:
        name, _, raw = f.partition(":")
        name = name.strip()
        if name == "lower":
            val = str(val).lower()
        elif name == "upper":
            val = str(val).upper()
        elif name == "default":
            val = val if val else _arg(raw)
        elif name == "length":
            val = len(val) if isinstance(val, (str, list, dict)) else 0
        elif name == "truncatechars":
            n, s = _arg(raw), str(val)
            val = s if len(s) <= n else s[:n - 1] + "…"
    return val


def _parse(tokens, i, stop):
    nodes = []
    while i < len(tokens):
        t = tokens[i]
        if t.startswith("{%"):
            words = t[2:-2].split()
            if words[0] in stop:
                return nodes, i
            if words[0] == "for":
                body, i = _parse(tokens, i + 1, ("endfor",))
                nodes.append(("for", words[1], words[3], body))
            elif words[0] == "if":
                yes, i = _parse(tokens, i + 1, ("else", "endif"))
                no = []
                if tokens[i][2:-2].split()[0] == "else":
                    no, i = _parse(tokens, i + 1, ("endif",))
                nodes.append(("if", words[1] == "not", words[-1], yes, no))
        elif t.startswith("{{"):
            nodes.append(("var", t[2:-2].strip()))
        else:
            nodes.append(("text", t))
        i += 1
    return nodes, i


def _render(nodes, ctx):
    out = []
    for node in nodes:
        kind = node[0]
        if kind == "text":
            out.append(node[1])
        elif kind == "var":
            out.append(str(_evaluate(node[1], ctx)))
        elif kind == "if":
            truth = bool(_lookup(node[2], ctx))
            out.append(_render(node[3] if truth != node[1] else node[4], ctx))
        else:
            seq = _lookup(node[2], ctx)
            if not isinstance(seq, list):
                seq = []
            for k, item in enumerate(seq):
                inner = dict(ctx)
                inner[node[1]] = item
                inner["forloop"] = {"counter": k + 1, "first": k == 0, "last": k == len(seq) - 1}
                out.append(_render(node[3], inner))
    return "".join(out)


def render(template, context):
    tokens = [t for t in _TOKEN.split(template) if t]
    nodes, _ = _parse(tokens, 0, ())
    return _render(nodes, context)
''',
    tests=[
        ["{% for t in tags %}{{ forloop.counter }}:{{ t|upper }} {% endfor %}", {"tags": ["a", "b"]}],
        ["Hello {{ name }}!", {"name": "Imani"}],
        ["{{ story.author.name|default:\"staff\"|upper }}", {"story": {"author": {}}}],
        ["plain text, no tags", {}],
        ["", {"x": 1}],
        ["[{{ missing }}][{{ a.b.c }}][{{ items.5 }}][{{ items.1 }}]", {"a": {"b": 3}, "items": ["x", "y"]}],
        ["{{ title|truncatechars:8 }}|{{ title|truncatechars:40 }}|{{ n|truncatechars:3 }}", {"title": "Harbour reopens", "n": 123456}],
        ["{{ tags|length }} {{ title|length }} {{ nope|length }} {{ n|length }} {{ d|length }}", {"tags": [1, 2, 3], "title": "abcd", "n": 7, "d": {"k": 1}}],
        ["{% if user.is_staff %}edit{% else %}read{% endif %}/{% if not user.is_staff %}no{% endif %}", {"user": {"is_staff": False}}],
        ["{% if user.is_staff %}edit{% else %}read{% endif %}/{% if not user.is_staff %}no{% endif %}", {"user": {"is_staff": True}}],
        ["{% for s in stories %}{% if s.live %}<li>{{ s.title|lower }}{% if not forloop.last %},{% endif %}</li>{% endif %}{% endfor %}",
         {"stories": [{"title": "A", "live": True}, {"title": "B", "live": False}, {"title": "C", "live": True}]}],
        ["{% for row in grid %}{% for c in row %}{{ c }}{% endfor %};{% endfor %}{{ c }}{{ row }}", {"grid": [[1, 2], [3]], "c": "!"}],
        ["{% for x in nothing %}never{% endfor %}{% for x in word %}never{% endfor %}done", {"word": "abc"}],
        ["{{ v }} {{ flag }} {{ zero|default:\"none\" }} {{ zero }} {{ n|default:5 }}", {"v": None, "flag": True, "zero": 0}],
        ["{{name|upper}} {{  name | lower  }}", {"name": "MiXed"}],
        ["{% for p in people %}{% if forloop.first %}first={{ p.name }}{% endif %}{% if forloop.last %} last={{ p.name }}{% endif %}{% endfor %}",
         {"people": [{"name": "Ana"}, {"name": "Bo"}, {"name": "Cy"}]}],
        ["{% for row in grid %}{{ forloop.counter }}{% for c in row %}.{% endfor %}{{ forloop.counter }} {% endfor %}", {"grid": [[1, 2], [3]]}],
    ],
    examples=3,
    wrong_solutions=[
        '''import re
def render(template, context):
    def sub(m):
        cur = context
        for part in m.group(1).strip().split("|")[0].strip().split("."):
            if isinstance(cur, dict) and part in cur:
                cur = cur[part]
            else:
                return ""
        return str(cur)
    return re.sub(r"{{(.*?)}}", sub, template)
''',
        '''import re
_TOKEN = re.compile(r"({{.*?}}|{%.*?%})")
def _lookup(path, ctx):
    cur = ctx
    for part in path.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        elif isinstance(cur, list) and part.isdigit() and int(part) < len(cur):
            cur = cur[int(part)]
        else:
            return ""
    return cur
def _evaluate(expr, ctx):
    parts = [p.strip() for p in expr.split("|")]
    val = _lookup(parts[0], ctx)
    for f in parts[1:]:
        name, _, raw = f.partition(":")
        raw = raw.strip()
        arg = raw[1:-1] if raw.startswith('"') else (int(raw) if raw else None)
        if name == "lower": val = str(val).lower()
        elif name == "upper": val = str(val).upper()
        elif name == "default": val = val if val else arg
        elif name == "length": val = len(val) if isinstance(val, (str, list, dict)) else 0
        elif name == "truncatechars":
            s = str(val); val = s if len(s) <= arg else s[:arg - 1] + "…"
    return val
def _parse(tokens, i, stop):
    nodes = []
    while i < len(tokens):
        t = tokens[i]
        if t.startswith("{%"):
            words = t[2:-2].split()
            if words[0] in stop:
                return nodes, i
            if words[0] == "for":
                body, i = _parse(tokens, i + 1, ("endfor",))
                nodes.append(("for", words[1], words[3], body))
            elif words[0] == "if":
                yes, i = _parse(tokens, i + 1, ("else", "endif"))
                no = []
                if tokens[i][2:-2].split()[0] == "else":
                    no, i = _parse(tokens, i + 1, ("endif",))
                nodes.append(("if", words[1] == "not", words[-1], yes, no))
        elif t.startswith("{{"):
            nodes.append(("var", t[2:-2].strip()))
        else:
            nodes.append(("text", t))
        i += 1
    return nodes, i
def _render(nodes, ctx):
    out = []
    for node in nodes:
        if node[0] == "text": out.append(node[1])
        elif node[0] == "var": out.append(str(_evaluate(node[1], ctx)))
        elif node[0] == "if":
            truth = bool(_lookup(node[2], ctx))
            out.append(_render(node[3] if truth != node[1] else node[4], ctx))
        else:
            seq = _lookup(node[2], ctx)
            if not isinstance(seq, list): seq = []
            for k, item in enumerate(seq):
                ctx[node[1]] = item
                ctx["forloop"] = {"counter": k + 1, "first": k == 0, "last": k == len(seq) - 1}
                out.append(_render(node[3], ctx))
    return "".join(out)
def render(template, context):
    tokens = [t for t in _TOKEN.split(template) if t]
    return _render(_parse(tokens, 0, ())[0], context)
''',
        '''import re
_TOKEN = re.compile(r"({{.*?}}|{%.*?%})")
def _lookup(path, ctx):
    cur = ctx
    for part in path.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return ""
    return cur
def render(template, context):
    out = []
    for t in _TOKEN.split(template):
        if t.startswith("{{"):
            parts = [p.strip() for p in t[2:-2].split("|")]
            val = _lookup(parts[0], context)
            for f in parts[1:]:
                if f == "upper": val = str(val).upper()
                if f == "lower": val = str(val).lower()
                if f == "length": val = len(str(val))
                if f.startswith("default") and val == "": val = f.split(":")[1].strip('"')
                if f.startswith("truncatechars"): val = str(val)[:int(f.split(":")[1])]
            out.append(str(val))
        elif not t.startswith("{%"):
            out.append(t)
    return "".join(out)
''',
    ],
    guide=dict(
        prereqs="Lesson *Templates and the Django template language*; recursion; `re.split` with a capturing group.",
        intuition="A template engine is a three-stage pipeline: **tokenise** the text into literal chunks, `{{ }}` and "
                  "`{% %}` pieces; **parse** the flat token list into a tree, because `for` and `if` own everything up "
                  "to their closing tag; **render** the tree against a context. Django's real engine has exactly these "
                  "stages (Lexer, Parser, NodeList).",
        hints=[
            "`re.split(r\"({{.*?}}|{%.*?%})\", template)` keeps the delimiters, giving you the token stream for free.",
            "Write `parse(tokens, i, stop_words)` that returns `(nodes, index_of_stop_tag)`; call it recursively for block bodies.",
            "Render loops with a *copy* of the context so the loop variable and `forloop` do not leak or clobber outer loops.",
        ],
        brute_force="Repeated regex substitution: replace the innermost `for`/`if` pair, then variables. It handles flat "
                    "templates but breaks on nesting (the regex cannot pair tags) and can re-scan output that happens to "
                    "contain braces. Each pass is O(n), and there may be O(depth) passes.",
        approach="""1. **Tokenise** with the split regex and drop empty strings.
2. **Parse**: literal → `text` node; `{{ }}` → `var` node; `{% for a in b %}` → parse the body until `endfor`;
   `{% if [not] p %}` → parse until `else` or `endif`, and if it stopped at `else` parse again until `endif`.
3. **Evaluate** an expression: split on `|`, look up the dotted path, apply filters in order.
4. **Render** recursively; `for` creates a child context with the item and a `forloop` dict.

**Dry run** on `{% for t in tags %}{{ forloop.counter }}:{{ t|upper }} {% endfor %}` with `tags=["a","b"]`:
tokens = for, var, text `:`, var, text space, endfor. Parse gives one `for` node with four children. Render:
iteration 1 → `1`, `:`, `A`, space; iteration 2 → `2`, `:`, `B`, space. Result `1:A 2:B `.""",
        complexity="O(T) to tokenise and parse a template of length T; rendering is O(output size), since each node is visited once per enclosing loop iteration.",
        pitfalls="""- `default` fires for every falsy value (`0`, `[]`, `None`, missing), not only for missing ones.
- `truncatechars:N` keeps `N-1` characters so that the result, ellipsis included, has length N.
- A string is iterable in Python, but the spec says only lists loop.
- After a nested loop finishes, the outer `forloop` and any shadowed variable must be visible again.
- `length` of an integer is `0`, not the length of its decimal text.""",
        follow_up="Add autoescaping (`<` → `&lt;`) with a `safe` filter, then `{% empty %}` and `elif`.",
    ),
),
dict(
    id="django-template-blocks",
    title="Template inheritance: resolve the blocks",
    difficulty="Medium",
    pattern="Templates",
    entry="render_inheritance",
    description=r"""
`{% extends %}` lets a child template fill named holes in a parent skeleton. Work out the final text.

`render_inheritance(templates, name)`:

- `templates` maps a template name to its source. A child starts (after optional whitespace) with
  `{% extends "parent_name" %}`. Chains may be several levels deep and always end at a template with no `extends`
  (the **root**). Every referenced parent exists.
- A block is written exactly `{% block NAME %}content{% endblock %}`; `NAME` is letters, digits or `_`.
  Blocks are never nested inside one another, and content may span lines.
- The output is the **root** source in which every block is replaced by its resolved content (the block tags
  themselves disappear). The resolved content of a block is the content given by the most-derived template in
  the chain that defines it; if only the root defines it, that is the root's default content.
- Inside a block, the literal text `{{ block.super }}` is replaced by the resolved content of the same block
  one level up the chain (ignoring templates that do not define it). In a template with nothing above it,
  `{{ block.super }}` becomes the empty string.
- Anything a child writes outside blocks is ignored, as are child blocks whose name the root never declares.

**Example:**

```
base:  "<title>{% block title %}Gazette{% endblock %}</title>"
story: '{% extends "base" %}{% block title %}Tides | {{ block.super }}{% endblock %}'
```

`render_inheritance(templates, "story")` → `"<title>Tides | Gazette</title>"`.
""",
    starter='''def render_inheritance(templates: dict, name: str) -> str:
    pass
''',
    solution=r'''import re

_BLOCK = re.compile(r"{% block (\w+) %}(.*?){% endblock %}", re.S)
_EXTENDS = re.compile(r'\s*{% extends "([^"]+)" %}')


def render_inheritance(templates, name):
    chain = []
    while True:
        source = templates[name]
        chain.append(source)
        m = _EXTENDS.match(source)
        if not m:
            break
        name = m.group(1)
    resolved = {}
    for source in reversed(chain):
        for block_name, body in _BLOCK.findall(source):
            resolved[block_name] = body.replace("{{ block.super }}", resolved.get(block_name, ""))
    return _BLOCK.sub(lambda m: resolved[m.group(1)], chain[-1])
''',
    tests=[
        [{"base": "<title>{% block title %}Gazette{% endblock %}</title>",
          "story": '{% extends "base" %}{% block title %}Tides | {{ block.super }}{% endblock %}'}, "story"],
        [{"base": "<title>{% block title %}Gazette{% endblock %}</title>"}, "base"],
        [{"base": "<h1>{% block head %}{% endblock %}</h1><main>{% block body %}empty{% endblock %}</main>",
          "page": '{% extends "base" %}\n{% block body %}Hello{% endblock %}\nstray text'}, "page"],
        [{"base": "A{% block x %}1{% endblock %}B{% block y %}2{% endblock %}C",
          "mid": '{% extends "base" %}{% block x %}m{{ block.super }}{% endblock %}',
          "leaf": '{% extends "mid" %}{% block x %}[{{ block.super }}]{% endblock %}{% block y %}Y{% endblock %}'}, "leaf"],
        [{"base": "A{% block x %}1{% endblock %}B{% block y %}2{% endblock %}C",
          "mid": '{% extends "base" %}{% block x %}m{{ block.super }}{% endblock %}',
          "leaf": '{% extends "mid" %}{% block y %}Y{% endblock %}'}, "leaf"],
        [{"base": "A{% block x %}1{% endblock %}B",
          "mid": '{% extends "base" %}',
          "leaf": '{% extends "mid" %}{% block x %}<{{ block.super }}>{% endblock %}'}, "leaf"],
        [{"base": "{% block x %}{{ block.super }}root{% endblock %}"}, "base"],
        [{"base": "no blocks at all", "child": '{% extends "base" %}{% block ghost %}boo{% endblock %}'}, "child"],
        [{"base": "<ul>\n{% block items %}\n<li>default</li>\n{% endblock %}\n</ul>",
          "list": '  {% extends "base" %}{% block items %}\n<li>one</li>\n<li>two</li>\n{% endblock %}'}, "list"],
        [{"base": "{% block a %}a{% endblock %}{% block b %}b{% endblock %}{% block a2 %}c{% endblock %}",
          "c": '{% extends "base" %}{% block b %}{{ block.super }}{{ block.super }}{% endblock %}{% block a2 %}{% endblock %}'}, "c"],
        [{"r": "{% block t %}0{% endblock %}", "a": '{% extends "r" %}{% block t %}1{{ block.super }}{% endblock %}',
          "b": '{% extends "a" %}{% block t %}2{{ block.super }}{% endblock %}',
          "c": '{% extends "b" %}{% block t %}3{{ block.super }}{% endblock %}'}, "c"],
        [{"r": "{% block t %}0{% endblock %}", "a": '{% extends "r" %}{% block t %}1{{ block.super }}{% endblock %}',
          "b": '{% extends "a" %}{% block t %}2{% endblock %}',
          "c": '{% extends "b" %}{% block t %}3{{ block.super }}{% endblock %}'}, "b"],
    ],
    examples=2,
    wrong_solutions=[
        r'''import re
_BLOCK = re.compile(r"{% block (\w+) %}(.*?){% endblock %}", re.S)
def render_inheritance(templates, name):
    child = templates[name]
    m = re.match(r'\s*{% extends "([^"]+)" %}', child)
    if not m:
        return _BLOCK.sub(lambda b: b.group(2).replace("{{ block.super }}", ""), child)
    parent = templates[m.group(1)]
    over = dict(_BLOCK.findall(child))
    return _BLOCK.sub(lambda b: over.get(b.group(1), b.group(2)).replace("{{ block.super }}", b.group(2)), parent)
''',
        r'''import re
_BLOCK = re.compile(r"{% block (\w+) %}(.*?){% endblock %}", re.S)
_EXTENDS = re.compile(r'\s*{% extends "([^"]+)" %}')
def render_inheritance(templates, name):
    chain = []
    while True:
        source = templates[name]
        chain.append(source)
        m = _EXTENDS.match(source)
        if not m:
            break
        name = m.group(1)
    resolved = {}
    for source in chain:
        for block_name, body in _BLOCK.findall(source):
            resolved.setdefault(block_name, body.replace("{{ block.super }}", ""))
    return _BLOCK.sub(lambda m: resolved[m.group(1)], chain[-1])
''',
    ],
    guide=dict(
        prereqs="Lesson *Class-based views, template inheritance, page tests and a first deployment*; `re.findall`/`re.sub` with `re.S`.",
        intuition="Inheritance in templates works like method overriding in classes. The root declares the 'methods' "
                  "(blocks); each child may override some, and `block.super` is `super().method()`. If you resolve "
                  "blocks from the root downwards, the value already stored for a block is exactly what `block.super` "
                  "means at the next level.",
        hints=[
            "Follow `extends` links to build the chain from the requested template up to the root.",
            "Process the chain root-first, keeping a dict `resolved[name]`; replace `{{ block.super }}` with the current entry before overwriting it.",
            "Finish with one `re.sub` over the root source, replacing each block by its resolved text.",
        ],
        brute_force="Merge two templates at a time, child into parent, re-emitting a new template with block tags, and "
                    "repeat up the chain. It works but re-parses the text once per level: O(depth × size).",
        approach="""1. Build `chain = [leaf, ..., root]` by matching the `extends` tag at the start of each source.
2. Iterate `reversed(chain)` (root first). For each block found: `resolved[name] = body` with `{{ block.super }}`
   replaced by `resolved.get(name, "")`.
3. Substitute every block in the root source with `resolved[name]`.

**Dry run** (root `t=0`, a `1+super`, b `2+super`, c `3+super`): root → `0`; a → `10`; b → `210`; c → `3210`.""",
        complexity="O(total template size): every source is scanned once, plus one substitution pass on the root.",
        pitfalls="""- Handling only one level of `extends`.
- Resolving leaf-first loses `block.super`, because the parent's text is not known yet.
- A middle template that does not mention a block must be skipped transparently.
- Without `re.S` the dot does not cross newlines and multi-line blocks are missed.
- Child blocks unknown to the root must not appear in the output.""",
        follow_up="Allow nested blocks, which requires a real parser like the one in the mini template engine problem.",
    ),
),
]
