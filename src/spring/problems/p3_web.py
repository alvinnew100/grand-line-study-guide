_MAP = [
    {"pattern": "/books", "methods": ["GET"], "handler": "listBooks"},
    {"pattern": "/books", "methods": ["POST"], "handler": "createBook"},
    {"pattern": "/books/{id}", "methods": ["GET"], "handler": "getBook"},
    {"pattern": "/books/{id}", "methods": ["PUT", "PATCH"], "handler": "updateBook"},
    {"pattern": "/books/featured", "methods": ["GET"], "handler": "featuredBooks"},
    {"pattern": "/books/{id}/reviews/{reviewId}", "methods": [], "handler": "review"},
    {"pattern": "/books/*/cover", "methods": ["GET"], "handler": "cover"},
    {"pattern": "/files/**", "methods": ["GET"], "handler": "files"},
    {"pattern": "/files/{name}", "methods": ["GET"], "handler": "oneFile"},
    {"pattern": "/", "methods": ["GET"], "handler": "home"},
    {"pattern": "/**", "methods": ["OPTIONS"], "handler": "cors"},
]

_SPEC = [
    {"name": "q", "type": "String", "required": True, "default": None},
    {"name": "page", "type": "int", "required": False, "default": "0"},
    {"name": "size", "type": "int", "required": False, "default": "20"},
    {"name": "inStock", "type": "boolean", "required": False, "default": None},
    {"name": "maxPrice", "type": "double", "required": False, "default": None},
    {"name": "tags", "type": "int[]", "required": False, "default": None},
]

_RULES = {
    "title": [["NotBlank"], ["Size", 2, 60]],
    "isbn": [["NotNull"], ["Pattern", "[0-9]{13}"]],
    "price": [["NotNull"], ["Positive"], ["Max", 500]],
    "pages": [["Min", 1]],
    "contact": [["Email"]],
    "authors": [["NotEmpty"], ["Size", 1, 3]],
}
_BOOK = {"title": "Dune", "isbn": "9780441172719", "price": 12, "pages": 612, "contact": "ed@pub.example", "authors": ["Frank Herbert"]}

_TREE = {
    "Throwable": None, "Exception": "Throwable", "Error": "Throwable", "RuntimeException": "Exception",
    "IOException": "Exception", "IllegalArgumentException": "RuntimeException",
    "NumberFormatException": "IllegalArgumentException", "ShopException": "RuntimeException",
    "BookNotFoundException": "ShopException", "OutOfStockException": "ShopException",
    "PaymentDeclinedException": "ShopException", "CardExpiredException": "PaymentDeclinedException",
    "OutOfMemoryError": "Error",
}
_HANDLERS = [["BookNotFoundException", 404], ["ShopException", 422], ["IllegalArgumentException", 400], ["Exception", 500]]
_ANNOT = {"PaymentDeclinedException": 402, "IOException": 503, "Error": 500, "OutOfStockException": 409}

_PRODUCES = ["application/json", "application/xml", "text/csv"]

PROBLEMS = [
dict(
    id="spring-request-mapping",
    title="Resolve a request to a handler method",
    difficulty="Hard",
    pattern="Spring MVC",
    entry="resolve",
    description=r"""
`DispatcherServlet` asks its handler mapping which controller method should serve a request. Implement that
decision.

`resolve(mappings, method, path)`:

- `mappings` — list of `{"pattern", "methods", "handler"}`. An empty `methods` list means *any HTTP method*.
- `method` — e.g. `"GET"`. `path` — starts with `/`, no query string.

**Matching.** Split pattern and path on `/` into segments (the root `/` has zero segments). Segment by segment:

- literal text must be equal (case-sensitive),
- `{name}` matches exactly one non-empty segment and captures it (as a string),
- `*` matches exactly one non-empty segment without capturing,
- `**` appears only as the final pattern segment and matches all remaining segments (zero or more).

Apart from `**`, the number of segments must be equal. A trailing slash is significant: `/books/` does not match
`/books` (the Spring Framework 6 default).

**Choosing.**

1. No pattern matches the path → `[404, None, {}]`.
2. Patterns match the path but none of them allows the method → `[405, None, {}]`.
3. Otherwise, among mappings that match path and method, the **most specific** wins: fewest `**`; then fewest
   one-segment wildcards (`{name}` and `*` counted together); then most literal segments. The input never
   contains a tie.

Return `[200, handler, variables]`.

**Example:** `GET /books/featured` matches both `/books/{id}` and `/books/featured`; the literal one wins →
`[200, "featuredBooks", {}]`. `DELETE /books/7` → `[405, None, {}]`.
""",
    starter='''def resolve(mappings: list, method: str, path: str) -> list:
    pass
''',
    solution='''def _segments(text):
    parts = text.split("/")[1:]
    return [] if parts == [""] else parts


def _match(pattern, path_segments):
    wanted = _segments(pattern)
    variables = {}
    for i, seg in enumerate(wanted):
        if seg == "**":
            return variables
        if i >= len(path_segments):
            return None
        actual = path_segments[i]
        if seg == "*" or (seg.startswith("{") and seg.endswith("}")):
            if actual == "":
                return None
            if seg != "*":
                variables[seg[1:-1]] = actual
        elif seg != actual:
            return None
    return variables if len(wanted) == len(path_segments) else None


def _rank(pattern):
    segs = _segments(pattern)
    catch_all = segs.count("**")
    single = sum(1 for s in segs if s == "*" or s.startswith("{"))
    return (catch_all, single, -(len(segs) - catch_all - single))


def resolve(mappings, method, path):
    path_segments = _segments(path)
    path_matched, best = False, None
    for mapping in mappings:
        variables = _match(mapping["pattern"], path_segments)
        if variables is None:
            continue
        path_matched = True
        if mapping["methods"] and method not in mapping["methods"]:
            continue
        rank = _rank(mapping["pattern"])
        if best is None or rank < best[0]:
            best = (rank, mapping["handler"], variables)
    if not path_matched:
        return [404, None, {}]
    if best is None:
        return [405, None, {}]
    return [200, best[1], best[2]]
''',
    tests=[
        [_MAP, "GET", "/books/featured"],
        [_MAP, "DELETE", "/books/7"],
        [_MAP, "GET", "/books"],
        [_MAP, "POST", "/books"],
        [_MAP, "GET", "/books/42"],
        [_MAP, "PATCH", "/books/42"],
        [_MAP, "GET", "/books/"],
        [_MAP, "DELETE", "/books/42/reviews/9"],
        [_MAP, "GET", "/books/42/cover"],
        [_MAP, "GET", "/files/a/b/c.png"],
        [_MAP, "GET", "/files/logo.png"],
        [_MAP, "GET", "/files"],
        [_MAP, "GET", "/"],
        [_MAP, "OPTIONS", "/anything/at/all"],
        [_MAP, "GET", "/authors"],
        [_MAP[:9], "GET", "/authors"],
        [[], "GET", "/"],
        [_MAP[:9], "GET", "/Books"],
    ],
    examples=2,
    wrong_solutions=[
        '''def _segments(t):
    p = t.split("/")[1:]
    return [] if p == [""] else p
def _match(pattern, ps):
    w = _segments(pattern); v = {}
    for i, s in enumerate(w):
        if s == "**": return v
        if i >= len(ps): return None
        if s == "*" or s.startswith("{"):
            if ps[i] == "": return None
            if s != "*": v[s[1:-1]] = ps[i]
        elif s != ps[i]: return None
    return v if len(w) == len(ps) else None
def resolve(mappings, method, path):
    ps = _segments(path)
    for m in mappings:
        v = _match(m["pattern"], ps)
        if v is not None and (not m["methods"] or method in m["methods"]):
            return [200, m["handler"], v]
    return [404, None, {}]
''',
        '''def _segments(t):
    p = t.split("/")[1:]
    return [] if p == [""] else p
def _match(pattern, ps):
    w = _segments(pattern); v = {}
    for i, s in enumerate(w):
        if s == "**": return v
        if i >= len(ps): return None
        if s == "*" or s.startswith("{"):
            if s != "*": v[s[1:-1]] = ps[i]
        elif s != ps[i]: return None
    return v if len(w) == len(ps) else None
def _rank(pattern):
    s = _segments(pattern)
    return (s.count("**"), sum(1 for x in s if x == "*" or x.startswith("{")), -len(s))
def resolve(mappings, method, path):
    ps = _segments(path); seen = False; best = None
    for m in mappings:
        v = _match(m["pattern"], ps)
        if v is None: continue
        seen = True
        if m["methods"] and method not in m["methods"]: continue
        if best is None or _rank(m["pattern"]) < best[0]: best = (_rank(m["pattern"]), m["handler"], v)
    if not seen: return [404, None, {}]
    if best is None: return [405, None, {}]
    return [200, best[1], best[2]]
''',
        '''def _segments(t):
    p = t.split("/")[1:]
    return [] if p == [""] else p
def _match(pattern, ps):
    w = _segments(pattern); v = {}
    for i, s in enumerate(w):
        if s == "**": return v
        if i >= len(ps): return None
        if s == "*" or s.startswith("{"):
            if ps[i] == "": return None
            if s != "*": v[s[1:-1]] = ps[i]
        elif s != ps[i]: return None
    return v if len(w) == len(ps) else None
def _rank(pattern):
    s = _segments(pattern)
    return (s.count("**"), sum(1 for x in s if x == "*" or x.startswith("{")), -len(s))
def resolve(mappings, method, path):
    ps = _segments(path); best = None
    for m in mappings:
        v = _match(m["pattern"], ps)
        if v is None or (m["methods"] and method not in m["methods"]): continue
        if best is None or _rank(m["pattern"]) < best[0]: best = (_rank(m["pattern"]), m["handler"], v)
    if best is None: return [404, None, {}]
    return [200, best[1], best[2]]
''',
    ],
    guide=dict(
        prereqs="Lessons: *Spring MVC: the request flow through DispatcherServlet* and *Request parameters, path variables and the Model*.",
        intuition="Two separate questions: *which patterns fit this path?* and *of those that also accept the "
                  "method, which is the least vague?* Keeping them separate is what lets you tell 404 from 405.",
        hints=[
            "Write `match(pattern, path)` returning a dict of variables or `None`. Compare segment lists, not strings.",
            "Track a flag 'some pattern matched the path' independently of the method check.",
            "Specificity is a tuple you can compare directly: `(count of **, count of single wildcards, -literal count)`.",
        ],
        brute_force="Return the first mapping that matches. It is O(n) too, but registration order then decides "
                    "between `/books/{id}` and `/books/featured`, which Spring never does.",
        approach=r"""
1. Split the path once. For each mapping, match segments left to right, stopping successfully at `**`.
2. Remember that the path matched; skip the mapping if the method is not allowed.
3. Keep the candidate with the smallest rank tuple.

**Dry run** `GET /files/logo.png`: `/files/**` matches (rank `(1,0,-1)`), `/files/{name}` matches with
`name=logo.png` (rank `(0,1,-1)`), `/**` matches the path but only for OPTIONS. Smallest tuple → `oneFile`.

```java
@RestController
@RequestMapping("/books")
class BookController {
    @GetMapping                  List<Book> listBooks()                      { ... }
    @GetMapping("/featured")     List<Book> featuredBooks()                  { ... }
    @GetMapping("/{id}")         Book getBook(@PathVariable long id)         { ... }
    @PutMapping("/{id}")         Book updateBook(@PathVariable long id,
                                                 @RequestBody Book book)    { ... }
}
```

`DELETE /books/7` produces `405 Method Not Allowed` with an `Allow: GET, PUT` header.
""",
        complexity="Time O(M · S) for M mappings and S path segments. Space O(S).",
        pitfalls="Comparing whole strings instead of segments; answering 404 where 405 is correct; letting `{id}` "
                 "match an empty segment so `/books/` hits `getBook`; forgetting that `/files/**` also matches `/files`.",
        follow_up="Spring also narrows by `consumes`, `produces`, `params` and `headers`. Add `produces` using the content-negotiation problem.",
    ),
),
dict(
    id="spring-param-binding",
    title="Bind and convert request parameters",
    difficulty="Medium",
    pattern="Spring MVC",
    entry="bind",
    description=r"""
A controller method declares `@RequestParam` arguments; Spring reads the query string, converts the text to the
declared types and reports a `400 Bad Request` when it cannot.

`bind(spec, query)`:

- `spec` — list of `{"name", "type", "required", "default"}` in parameter order. `type` is one of `"String"`,
  `"int"`, `"boolean"`, `"double"`, `"int[]"`. `default` is a string or `None`.
- `query` — the raw query string without `?`, e.g. `"q=dune&page=2"`. Pairs are separated by `&`; a pair without
  `=` has the empty string as value; `+` means space and `%XX` is percent-decoding (apply to names and values).
  Empty pairs are ignored. Parameters not in the spec are ignored.

For each parameter in order:

1. Take the **first** value given for the name. For `int[]` take *all* values, split each on commas, and drop
   empty pieces.
2. If there is no value — or the value is the empty string and the type is not `String` (for `int[]`: no pieces
   left) — use `default` instead (for `int[]`, split it on commas).
3. Still nothing: when `required`, fail with `"Required request parameter '<name>' is not present"`; otherwise
   the argument is `None` (`[]` for `int[]`).
4. Convert. `int`: optional sign and digits. `double`: optional sign, digits with optional fraction, optional
   exponent (`1e3`, `.5`, `2.` are fine; `abc`, `1,5`, `inf` are not). `boolean`: `true/on/yes/1` → `True`,
   `false/off/no/0` → `False`, ignoring case. On failure:
   `"Failed to convert parameter '<name>' with value '<text>' to <type>"` (for arrays: the offending piece, type `int`).

Return `{"status": 200, "args": {...}}`, or `{"status": 400, "error": message}` for the **first** failing parameter.
""",
    starter='''def bind(spec: list, query: str) -> dict:
    pass
''',
    solution='''import re
from urllib.parse import unquote_plus

_INT = re.compile(r"[+-]?[0-9]+\\Z")
_DOUBLE = re.compile(r"[+-]?([0-9]+\\.?[0-9]*|\\.[0-9]+)([eE][+-]?[0-9]+)?\\Z")
_TRUE, _FALSE = {"true", "on", "yes", "1"}, {"false", "off", "no", "0"}


class _Bad(Exception):
    pass


def _convert(name, kind, text):
    if kind == "String":
        return text
    if kind == "int" and _INT.match(text):
        return int(text)
    if kind == "double" and _DOUBLE.match(text):
        return float(text)
    if kind == "boolean" and text.lower() in _TRUE | _FALSE:
        return text.lower() in _TRUE
    raise _Bad("Failed to convert parameter '%s' with value '%s' to %s" % (name, text, kind))


def bind(spec, query):
    given = {}
    for pair in query.split("&"):
        if pair == "":
            continue
        key, _, value = pair.partition("=")
        given.setdefault(unquote_plus(key), []).append(unquote_plus(value))
    args = {}
    try:
        for p in spec:
            name, kind, values = p["name"], p["type"], given.get(p["name"], [])
            if kind == "int[]":
                pieces = [x for v in values for x in v.split(",") if x != ""]
                if not pieces and p["default"] is not None:
                    pieces = [x for x in p["default"].split(",") if x != ""]
                if not pieces and p["required"]:
                    raise _Bad("Required request parameter '%s' is not present" % name)
                args[name] = [_convert(name, "int", x) for x in pieces]
                continue
            text = values[0] if values else None
            if text is None or (text == "" and kind != "String"):
                text = p["default"]
            if text is None:
                if p["required"]:
                    raise _Bad("Required request parameter '%s' is not present" % name)
                args[name] = None
                continue
            args[name] = _convert(name, kind, text)
    except _Bad as problem:
        return {"status": 400, "error": str(problem)}
    return {"status": 200, "args": args}
''',
    tests=[
        [_SPEC, "q=dune&page=2"],
        [_SPEC, "page=2"],
        [_SPEC, "q=dune&page=two"],
        [_SPEC, "q=war+and+peace&inStock=YES&maxPrice=19.99&tags=1,2&tags=3"],
        [_SPEC, "q=&page=&size=5"],
        [_SPEC, "q=caf%C3%A9&maxPrice=1e2&inStock=0"],
        [_SPEC, "q=x&inStock=maybe&maxPrice=abc"],
        [_SPEC, "q=x&maxPrice=1,5"],
        [_SPEC, "q=x&tags=1,,2,x"],
        [_SPEC, "q=first&q=second&page=-3&&unknown=1"],
        [_SPEC, "q&size=+7&maxPrice=.5"],
        [_SPEC, ""],
        [[{"name": "ids", "type": "int[]", "required": True, "default": None}], "ids="],
        [[{"name": "ids", "type": "int[]", "required": True, "default": "4,5"},
          {"name": "debug", "type": "boolean", "required": True, "default": "off"}], "other=1"],
        [[{"name": "n", "type": "int", "required": True, "default": None}], "n=12abc"],
        [[{"name": "n", "type": "double", "required": False, "default": None}], "n=inf"],
    ],
    examples=3,
    wrong_solutions=[
        '''def bind(spec, query):
    given = dict(pair.split("=") for pair in query.split("&") if "=" in pair)
    args = {}
    for p in spec:
        text = given.get(p["name"], p["default"])
        if text is None:
            if p["required"]:
                return {"status": 400, "error": "Required request parameter '%s' is not present" % p["name"]}
            args[p["name"]] = [] if p["type"] == "int[]" else None
            continue
        try:
            if p["type"] == "int": args[p["name"]] = int(text)
            elif p["type"] == "double": args[p["name"]] = float(text)
            elif p["type"] == "boolean": args[p["name"]] = text == "true"
            elif p["type"] == "int[]": args[p["name"]] = [int(x) for x in text.split(",")]
            else: args[p["name"]] = text
        except ValueError:
            return {"status": 400, "error": "Failed to convert parameter '%s' with value '%s' to %s" % (p["name"], text, p["type"])}
    return {"status": 200, "args": args}
''',
    ],
    guide=dict(
        prereqs="Lesson: *Request parameters, path variables and the Model*. String splitting, `try/except`.",
        intuition="Three stages per parameter: *find* the text, *fall back* to a default or complain, *convert*. "
                  "Errors are data here: the function reports the first one instead of crashing.",
        hints=[
            "Parse the query string once into `name -> list of values`, decoding as you go.",
            "Decide the text to convert before thinking about types; an empty string counts as absent for non-String types.",
            "Raise a private exception from the converter and catch it once, turning it into the 400 result.",
        ],
        brute_force="`dict(pair.split('=') ...)` plus `int(text)` handles the happy path. It loses repeated "
                    "parameters, crashes on pairs without `=`, skips URL decoding and accepts `int(' 7 ')` or `float('inf')`.",
        approach=r"""
**Dry run** for `q=&page=&size=5`: `q` is a String, so the empty text is kept (`""`). `page` is an int with
empty text → default `"0"` → `0`. `size` → `5`. The optional ones become `None`, `tags` becomes `[]`.

```java
@GetMapping("/books/search")
List<Book> search(@RequestParam String q,                                    // required by default
                  @RequestParam(defaultValue = "0") int page,
                  @RequestParam(defaultValue = "20") int size,
                  @RequestParam(required = false) Boolean inStock,
                  @RequestParam(required = false) Double maxPrice,
                  @RequestParam(required = false) List<Integer> tags) { ... }
```

A missing `q` raises `MissingServletRequestParameterException`; `page=two` raises
`MethodArgumentTypeMismatchException`. Both become `400 Bad Request`.
""",
        complexity="Time O(length of the query + number of parameters). Space O(length of the query).",
        pitfalls="Using Python's permissive `int()`/`float()` (they accept spaces, underscores, `inf`, `nan`); "
                 "treating a supplied default as making the parameter optional *and* still reporting it missing; "
                 "decoding `+` after splitting on it; reading the last instead of the first repeated value.",
        follow_up="Bind onto an object instead (`@ModelAttribute`), collecting *all* errors in a `BindingResult`.",
    ),
),
dict(
    id="spring-bean-validation",
    title="Bean Validation: collect field errors",
    difficulty="Medium",
    pattern="REST",
    entry="validate",
    description=r"""
With `@Valid` on a `@RequestBody`, Spring runs Jakarta Bean Validation and answers `400` with the list of
violations. Implement the checker.

`validate(constraints, obj)`:

- `constraints` — dict `field -> list of rules`. A rule is a list whose first item is the constraint name.
- `obj` — dict of the submitted values. A missing field counts as `None`.

| rule | passes when | message |
|---|---|---|
| `["NotNull"]` | value is not `None` | `must not be null` |
| `["NotBlank"]` | a string containing at least one non-whitespace character | `must not be blank` |
| `["NotEmpty"]` | a string or list with length > 0 | `must not be empty` |
| `["Size", min, max]` | `min <= len(value) <= max` (string or list) | `size must be between {min} and {max}` |
| `["Min", n]` | `value >= n` | `must be greater than or equal to {n}` |
| `["Max", n]` | `value <= n` | `must be less than or equal to {n}` |
| `["Positive"]` | `value > 0` | `must be greater than 0` |
| `["Email"]` | empty string, or text of the form `something@something` with no spaces and exactly one `@` | `must be a well-formed email address` |
| `["Pattern", regex]` | the **whole** string matches the regular expression | `must match "{regex}"` |

Important: `None` **passes** every rule except `NotNull`, `NotBlank` and `NotEmpty`. That is how Bean Validation
works: "optional but, if present, valid".

Report every violation. Return `{"status": 200, "errors": []}` when there are none, otherwise
`{"status": 400, "errors": [[field, message], ...]}` ordered by field name (alphabetical) and, within a field, by
the order of its rules.
""",
    starter='''def validate(constraints: dict, obj: dict) -> dict:
    pass
''',
    solution='''import re


def _violation(rule, value):
    kind = rule[0]
    if kind == "NotNull":
        return None if value is not None else "must not be null"
    if kind == "NotBlank":
        return None if isinstance(value, str) and value.strip() else "must not be blank"
    if kind == "NotEmpty":
        return None if value is not None and len(value) > 0 else "must not be empty"
    if value is None:
        return None
    if kind == "Size":
        return None if rule[1] <= len(value) <= rule[2] else "size must be between %d and %d" % (rule[1], rule[2])
    if kind == "Min":
        return None if value >= rule[1] else "must be greater than or equal to %d" % rule[1]
    if kind == "Max":
        return None if value <= rule[1] else "must be less than or equal to %d" % rule[1]
    if kind == "Positive":
        return None if value > 0 else "must be greater than 0"
    if kind == "Email":
        ok = value == "" or re.fullmatch(r"[^@\\s]+@[^@\\s]+", value)
        return None if ok else "must be a well-formed email address"
    if kind == "Pattern":
        return None if re.fullmatch(rule[1], value) else 'must match "%s"' % rule[1]
    raise ValueError(kind)


def validate(constraints, obj):
    errors = []
    for field in sorted(constraints):
        for rule in constraints[field]:
            message = _violation(rule, obj.get(field))
            if message:
                errors.append([field, message])
    return {"status": 400 if errors else 200, "errors": errors}
''',
    tests=[
        [_RULES, _BOOK],
        [_RULES, dict(_BOOK, title="  ", price=0)],
        [_RULES, {}],
        [{}, {"anything": 1}],
        [_RULES, dict(_BOOK, isbn="978044117271", contact="not-an-email")],
        [_RULES, dict(_BOOK, isbn="x9780441172719", pages=0, price=501)],
        [_RULES, dict(_BOOK, pages=None, contact=None)],
        [_RULES, dict(_BOOK, contact="", title="D")],
        [_RULES, dict(_BOOK, authors=[], price=-3)],
        [_RULES, dict(_BOOK, authors=["a", "b", "c", "d"], contact="a@b@c")],
        [_RULES, dict(_BOOK, title="x" * 60, price=500, pages=1, contact="a b@c.d")],
        [{"code": [["Pattern", "[A-Z]{2}-[0-9]+"]], "alias": [["Size", 0, 3], ["NotBlank"]]}, {"code": "AB-12 ", "alias": "    "}],
        [{"zeta": [["NotNull"]], "alpha": [["NotNull"], ["NotBlank"], ["NotEmpty"]]}, {"zeta": None}],
    ],
    examples=2,
    wrong_solutions=[
        '''import re
def _v(rule, value):
    k = rule[0]
    if k == "NotNull": return None if value is not None else "must not be null"
    if k == "NotBlank": return None if isinstance(value, str) and value.strip() else "must not be blank"
    if k == "NotEmpty": return None if value else "must not be empty"
    if value is None: return "must not be null"
    if k == "Size": return None if rule[1] <= len(value) <= rule[2] else "size must be between %d and %d" % (rule[1], rule[2])
    if k == "Min": return None if value >= rule[1] else "must be greater than or equal to %d" % rule[1]
    if k == "Max": return None if value <= rule[1] else "must be less than or equal to %d" % rule[1]
    if k == "Positive": return None if value > 0 else "must be greater than 0"
    if k == "Email": return None if value == "" or re.fullmatch(r"[^@\\s]+@[^@\\s]+", value) else "must be a well-formed email address"
    return None if re.fullmatch(rule[1], value) else 'must match "%s"' % rule[1]
def validate(constraints, obj):
    errors = [[f, m] for f in sorted(constraints) for m in [_v(r, obj.get(f)) for r in constraints[f]] if m]
    return {"status": 400 if errors else 200, "errors": errors}
''',
        '''import re
def _v(rule, value):
    k = rule[0]
    if k == "NotNull": return None if value is not None else "must not be null"
    if k == "NotBlank": return None if value else "must not be blank"
    if k == "NotEmpty": return None if value else "must not be empty"
    if value is None: return None
    if k == "Size": return None if rule[1] <= len(value) <= rule[2] else "size must be between %d and %d" % (rule[1], rule[2])
    if k == "Min": return None if value >= rule[1] else "must be greater than or equal to %d" % rule[1]
    if k == "Max": return None if value <= rule[1] else "must be less than or equal to %d" % rule[1]
    if k == "Positive": return None if value > 0 else "must be greater than 0"
    if k == "Email": return None if "@" in value else "must be a well-formed email address"
    return None if re.match(rule[1], value) else 'must match "%s"' % rule[1]
def validate(constraints, obj):
    errors = []
    for f in sorted(constraints):
        for r in constraints[f]:
            m = _v(r, obj.get(f))
            if m:
                errors.append([f, m]); break
    return {"status": 400 if errors else 200, "errors": errors}
''',
    ],
    guide=dict(
        prereqs="Lesson: *Request bodies, validation and error handling with @RestControllerAdvice*.",
        intuition="Each constraint is a tiny yes/no function of one value. The framework's job is bookkeeping: "
                  "run them all, never stop at the first failure, and report which field each message belongs to.",
        hints=[
            "Write one function that takes a rule and a value and returns a message or `None`.",
            "Handle the three 'presence' rules first, then return 'pass' for `None`, then the rest.",
            "`re.fullmatch` mirrors Java's `String.matches`, which must consume the whole input.",
        ],
        brute_force="A long chain of `if` statements per field works for one class and has to be rewritten for the "
                    "next. The table-driven version is the point of the exercise.",
        approach=r"""
**Dry run** with an empty object and the book rules: `authors` → `NotEmpty` fails, `Size` passes (null);
`contact` passes; `isbn` → `NotNull` fails, `Pattern` passes; `pages` passes; `price` → `NotNull` fails only;
`title` → `NotBlank` fails only. Four errors, alphabetical by field.

```java
public record BookRequest(
        @NotBlank @Size(min = 2, max = 60) String title,
        @NotNull @Pattern(regexp = "[0-9]{13}") String isbn,
        @NotNull @Positive @Max(500) BigDecimal price,
        @Min(1) Integer pages,
        @Email String contact,
        @NotEmpty @Size(min = 1, max = 3) List<String> authors) { }

@PostMapping("/books")
ResponseEntity<Book> create(@Valid @RequestBody BookRequest request) { ... }
// a violation raises MethodArgumentNotValidException -> 400
```
""",
        complexity="Time O(total rules × cost of each check). Space O(number of violations).",
        pitfalls="Failing null values on `@Size`, `@Min`, `@Email` (they are valid; add `@NotNull` if the field is "
                 "mandatory). Using `re.match`, which accepts a prefix. Stopping at the first error per field.",
        follow_up="Add nested validation (`@Valid` on a field containing another object) with paths such as `address.zip`.",
    ),
),
dict(
    id="spring-exception-status",
    title="Map an exception to an HTTP status",
    difficulty="Easy",
    pattern="REST",
    entry="resolve_status",
    description=r"""
When a controller throws, Spring MVC looks for an `@ExceptionHandler` method that fits, and failing that for a
`@ResponseStatus` annotation on the exception class. Reproduce the lookup.

`resolve_status(parents, handlers, annotated, thrown)`:

- `parents` — dict `class -> parent class` (`None` for the root `Throwable`),
- `handlers` — list of `[exception_class, status]` pairs from a `@RestControllerAdvice`,
- `annotated` — dict `exception_class -> status` for classes carrying `@ResponseStatus`,
- `thrown` — the class of the exception that was thrown.

Rules:

1. Walk from `thrown` up through its ancestors. The **first** class that has a handler wins (the closest
   ancestor, with distance 0 for the class itself) → `[status, "handler:<class>"]`.
2. If no handler applies, walk up again and use the first class found in `annotated` →
   `[status, "annotation:<class>"]`.
3. Otherwise → `[500, "default"]`.

**Example:** handlers for `ShopException → 422` and `Exception → 500`; throwing `OutOfStockException` (a subclass
of `ShopException`) → `[422, "handler:ShopException"]`.
""",
    starter='''def resolve_status(parents: dict, handlers: list, annotated: dict, thrown: str) -> list:
    pass
''',
    solution='''def resolve_status(parents, handlers, annotated, thrown):
    lineage, current = [], thrown
    while current is not None:
        lineage.append(current)
        current = parents.get(current)
    handler_status = {cls: status for cls, status in handlers}
    for cls in lineage:
        if cls in handler_status:
            return [handler_status[cls], "handler:" + cls]
    for cls in lineage:
        if cls in annotated:
            return [annotated[cls], "annotation:" + cls]
    return [500, "default"]
''',
    tests=[
        [_TREE, [["ShopException", 422], ["Exception", 500]], {}, "OutOfStockException"],
        [_TREE, _HANDLERS, _ANNOT, "BookNotFoundException"],
        [_TREE, _HANDLERS, _ANNOT, "CardExpiredException"],
        [_TREE, _HANDLERS, _ANNOT, "NumberFormatException"],
        [_TREE, _HANDLERS, _ANNOT, "IOException"],
        [_TREE, _HANDLERS, _ANNOT, "OutOfMemoryError"],
        [_TREE, _HANDLERS[:3], _ANNOT, "IOException"],
        [_TREE, _HANDLERS[:3], _ANNOT, "RuntimeException"],
        [_TREE, [], _ANNOT, "CardExpiredException"],
        [_TREE, [], {}, "Throwable"],
        [_TREE, [["IllegalArgumentException", 400]], _ANNOT, "OutOfStockException"],
        [_TREE, list(reversed(_HANDLERS)), _ANNOT, "CardExpiredException"],
        [_TREE, [["Throwable", 418]], _ANNOT, "OutOfStockException"],
    ],
    examples=2,
    wrong_solutions=[
        '''def resolve_status(parents, handlers, annotated, thrown):
    def is_a(cls, ancestor):
        while cls is not None:
            if cls == ancestor:
                return True
            cls = parents.get(cls)
        return False
    for cls, status in handlers:
        if is_a(thrown, cls):
            return [status, "handler:" + cls]
    for cls, status in annotated.items():
        if is_a(thrown, cls):
            return [status, "annotation:" + cls]
    return [500, "default"]
''',
        '''def resolve_status(parents, handlers, annotated, thrown):
    cls = thrown
    hs = dict((c, s) for c, s in handlers)
    while cls is not None:
        if cls in annotated:
            return [annotated[cls], "annotation:" + cls]
        if cls in hs:
            return [hs[cls], "handler:" + cls]
        cls = parents.get(cls)
    return [500, "default"]
''',
        '''def resolve_status(parents, handlers, annotated, thrown):
    hs = dict((c, s) for c, s in handlers)
    if thrown in hs:
        return [hs[thrown], "handler:" + thrown]
    if thrown in annotated:
        return [annotated[thrown], "annotation:" + thrown]
    return [500, "default"]
''',
    ],
    guide=dict(
        prereqs="Java inheritance (the Java track's exceptions lesson). Lesson: *Request bodies, validation and error handling with @RestControllerAdvice*.",
        intuition="A handler for `ShopException` also covers its subclasses, but a handler written for the exact "
                  "subclass is a better fit. 'Better fit' means fewer steps up the family tree.",
        hints=[
            "First build the list `[thrown, parent, grandparent, ..., Throwable]`.",
            "Turn the handler pairs into a dict so each ancestor check is one lookup.",
            "Do the two passes separately: all handlers are considered before any annotation.",
        ],
        brute_force="For every handler compute the distance from `thrown` by walking up, and keep the minimum: "
                    "O(H · D). Walking the lineage once with a dict is O(H + D).",
        approach=r"""
**Dry run:** `CardExpiredException → PaymentDeclinedException → ShopException → RuntimeException → …`.
Handlers exist for `ShopException` (422) and `Exception` (500). The walk meets `ShopException` first →
`[422, "handler:ShopException"]`. The `@ResponseStatus(402)` on `PaymentDeclinedException` is never consulted
because a handler applied.

```java
@RestControllerAdvice
class ApiErrors {
    @ExceptionHandler(BookNotFoundException.class)
    ResponseEntity<ProblemDetail> notFound(BookNotFoundException e) {
        return ResponseEntity.status(404).body(ProblemDetail.forStatusAndDetail(HttpStatus.NOT_FOUND, e.getMessage()));
    }

    @ExceptionHandler(ShopException.class)
    @ResponseStatus(HttpStatus.UNPROCESSABLE_ENTITY)
    ProblemDetail business(ShopException e) { ... }
}

@ResponseStatus(HttpStatus.PAYMENT_REQUIRED)       // used only when no handler matches
class PaymentDeclinedException extends ShopException { }
```
""",
        complexity="Time O(H + D) for H handlers and inheritance depth D. Space O(H + D).",
        pitfalls="Taking the first handler in declaration order instead of the closest one; mixing the two passes "
                 "so an annotation on a subclass beats a handler on a superclass; forgetting distance 0.",
        follow_up="Real Spring also unwraps `getCause()` when no handler matches the outer exception, and prefers handlers inside the controller over advice classes.",
    ),
),
dict(
    id="spring-content-negotiation",
    title="Content negotiation with the Accept header",
    difficulty="Medium",
    pattern="REST",
    entry="negotiate",
    description=r"""
A client says which response formats it understands with the `Accept` header; the server picks one it can
produce. Implement the choice.

`negotiate(accept, produces)`:

- `accept` — the header value, e.g. `"text/csv;q=0.5, application/*, */*;q=0.1"`, or `None`/empty when absent
  (treat that as `*/*`).
- `produces` — the concrete media types the handler can write, in the server's order of preference.

Steps:

1. Split the header on commas. Each entry is a media range optionally followed by `;`-separated parameters; only
   the `q` parameter matters (a number from 0 to 1, default 1). Ignore surrounding spaces; compare
   case-insensitively (work in lower case). Drop entries with `q = 0`.
2. Sort the entries: higher `q` first; for equal `q`, more specific first (`type/subtype`, then `type/*`, then
   `*/*`); remaining ties keep header order.
3. Go through the sorted entries. For each, scan `produces` in order and return the first type compatible with
   the entry: `*/*` accepts anything, `type/*` accepts the same type, otherwise the types must be equal.
4. Nothing compatible → return `"406 Not Acceptable"`.

Return the chosen media type exactly as written in `produces`.

**Example:** `negotiate("application/xml, application/json;q=0.9", ["application/json", "application/xml"])` →
`"application/xml"`.
""",
    starter='''def negotiate(accept, produces: list) -> str:
    pass
''',
    solution='''def negotiate(accept, produces):
    entries = []
    for index, raw in enumerate((accept or "*/*").split(",")):
        parts = [p.strip().lower() for p in raw.split(";")]
        media = parts[0]
        if not media:
            continue
        q = 1.0
        for param in parts[1:]:
            if param.startswith("q="):
                q = float(param[2:])
        if q <= 0:
            continue
        specificity = 2 if media == "*/*" else 1 if media.endswith("/*") else 0
        entries.append((-q, specificity, index, media))
    if not entries and not (accept or "").strip():
        entries = [(-1.0, 2, 0, "*/*")]
    for _, _, _, media in sorted(entries):
        for candidate in produces:
            low = candidate.lower()
            if media == "*/*" or media == low or (media.endswith("/*") and low.split("/")[0] == media[:-2]):
                return candidate
    return "406 Not Acceptable"
''',
    tests=[
        ["application/xml, application/json;q=0.9", ["application/json", "application/xml"]],
        ["text/html", _PRODUCES],
        [None, _PRODUCES],
        ["", _PRODUCES],
        ["*/*", _PRODUCES],
        ["text/*, application/json;q=0.8", _PRODUCES],
        ["text/csv;q=0.5, application/*, */*;q=0.1", _PRODUCES],
        ["application/json;q=0, */*", ["application/xml"]],
        ["application/json;q=0", _PRODUCES],
        ["*/*;q=0.8, application/xml;q=0.8", _PRODUCES],
        ["Application/XML; charset=utf-8; q=0.7 , TEXT/CSV;q=0.7", _PRODUCES],
        ["image/png, image/*;q=0.9, */*;q=0.1", ["text/csv"]],
        ["application/*;q=0.5, text/csv;q=0.5, application/xml;q=0.4", _PRODUCES],
        ["text/plain, text/html", []],
        ["application/json", ["Application/JSON"]],
    ],
    examples=2,
    wrong_solutions=[
        '''def negotiate(accept, produces):
    wanted = [e.split(";")[0].strip().lower() for e in (accept or "*/*").split(",")]
    for media in wanted:
        for c in produces:
            if media == "*/*" or media == c.lower() or (media.endswith("/*") and c.lower().split("/")[0] == media[:-2]):
                return c
    return "406 Not Acceptable"
''',
        '''def negotiate(accept, produces):
    entries = []
    for i, raw in enumerate((accept or "*/*").split(",")):
        parts = [p.strip().lower() for p in raw.split(";")]
        q = 1.0
        for p in parts[1:]:
            if p.startswith("q="): q = float(p[2:])
        if q > 0 and parts[0]:
            entries.append((-q, i, parts[0]))
    for _, _, media in sorted(entries):
        for c in produces:
            if media == "*/*" or media == c.lower() or (media.endswith("/*") and c.lower().split("/")[0] == media[:-2]):
                return c
    return "406 Not Acceptable"
''',
        '''def negotiate(accept, produces):
    if not produces:
        return "406 Not Acceptable"
    if not accept:
        return produces[0]
    wanted = set(e.split(";")[0].strip().lower() for e in accept.split(","))
    for c in produces:
        if c.lower() in wanted or "*/*" in wanted:
            return c
    return "406 Not Acceptable"
''',
    ],
    guide=dict(
        prereqs="HTTP headers (the networking track or the lesson *REST endpoints with @RestController and ResponseEntity*). Sorting by a tuple.",
        intuition="The client ranks what it wants, the server ranks what it has. Walk the client's ranking from the "
                  "top and stop at the first thing the server can deliver.",
        hints=[
            "Parse each entry into `(q, specificity, position, media range)`.",
            "Sort by `(-q, specificity, position)` so a plain `sorted` gives the right order.",
            "Write the compatibility test for the three shapes `*/*`, `type/*`, `type/subtype` separately.",
        ],
        brute_force="Ignore `q` and take header order. Browsers send `*/*;q=0.8` in the middle of the header, so "
                    "this picks the wrong format regularly.",
        approach=r"""
**Dry run** for `text/csv;q=0.5, application/*, */*;q=0.1` with JSON, XML, CSV on offer. Sorted entries:
`application/*` (q 1), `text/csv` (0.5), `*/*` (0.1). The first entry is compatible with `application/json`,
the server's first preference → JSON.

```java
@GetMapping(value = "/books/{id}",
            produces = {MediaType.APPLICATION_JSON_VALUE, MediaType.APPLICATION_XML_VALUE})
Book getBook(@PathVariable long id) { ... }
```

```bash
curl -H "Accept: application/xml" http://localhost:8080/books/7     # XML if a converter is on the classpath
curl -H "Accept: image/png"       http://localhost:8080/books/7     # 406 Not Acceptable
```
""",
        complexity="Time O(A log A + A · P) for A accept entries and P producible types. Space O(A).",
        pitfalls="Forgetting the default `q=1`; comparing case-sensitively; returning the client's wildcard "
                 "(`application/*`) instead of a concrete type; keeping `q=0` entries.",
        follow_up="Spring can also negotiate with a `?format=xml` parameter. Where would that slot into the algorithm?",
    ),
),
]
