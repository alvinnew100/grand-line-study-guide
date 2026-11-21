PROBLEMS = [
dict(
    id="fastapi-content-negotiation",
    title="Pick a Response Type from the Accept Header",
    difficulty="Medium",
    pattern="HTTP Fundamentals",
    entry="negotiate",
    description=r"""
A client says which response formats it can handle in the `Accept` request header, for example
`text/html, application/json;q=0.9, */*;q=0.1`. The server compares that list with the formats it can
produce and picks the best one. If nothing acceptable is left, the answer is `406 Not Acceptable`.
This is called **content negotiation**. Implement the choice.

`negotiate(accept, available)`:

- `available` is the list of media types the server can produce, **in the server's order of
  preference**. Return the chosen string exactly as it appears in `available`, or `None` (meaning 406).
- `accept` is the header value. An empty or blank header means "anything" (treat it as `*/*`).
- Split the header on commas into **media ranges**. Each range is `type/subtype` followed by
  optional `;name=value` parameters. Ignore empty pieces and pieces without a `/`.
- The parameter `q` (case-insensitive name) is the quality, a number between 0 and 1; it defaults to
  `1`. If `q` is present but is not a valid number, ignore that whole range. Other parameters are
  ignored.
- Matching is case-insensitive. A range matches a media type when it is exactly equal (specificity 2),
  when it is `type/*` with the same type (specificity 1), or when it is `*/*` (specificity 0). Any
  other wildcard form, such as `*/json`, matches nothing.
- The quality of an available type is the `q` of the **most specific** range that matches it (if
  several ranges tie on specificity, take the highest `q` among them). A type matched by no range has
  quality 0.
- Choose the available type with the highest quality, provided it is greater than 0. Ties go to the
  type that comes first in `available`.

**Example:** `negotiate("text/html,application/xml;q=0.9,*/*;q=0.8", ["application/json", "text/html"])`
→ `"text/html"` (quality 1 versus 0.8)

**Example:** `negotiate("*/*;q=1, application/json;q=0.2", ["application/json", "text/csv"])` →
`"text/csv"`: the specific range gives JSON only 0.2, while CSV gets 1 from `*/*`.
""",
    starter='''def negotiate(accept: str, available: list[str]) -> str | None:
    pass
''',
    solution='''def negotiate(accept, available):
    if accept is None or not accept.strip():
        accept = "*/*"
    ranges = []                                    # (type, subtype, q)
    for piece in accept.split(","):
        parts = [p.strip() for p in piece.split(";")]
        media = parts[0].lower()
        if "/" not in media:
            continue
        typ, sub = media.split("/", 1)
        q, ok = 1.0, True
        for param in parts[1:]:
            name, _, value = param.partition("=")
            if name.strip().lower() == "q":
                try:
                    q = float(value)
                except ValueError:
                    ok = False
        if ok:
            ranges.append((typ, sub, q))

    def quality(media_type):
        t, _, s = media_type.lower().partition("/")
        best_spec, best_q = -1, 0.0
        for typ, sub, q in ranges:
            if typ == t and sub == s:
                spec = 2
            elif typ == t and sub == "*":
                spec = 1
            elif typ == "*" and sub == "*":
                spec = 0
            else:
                continue
            if spec > best_spec or (spec == best_spec and q > best_q):
                best_spec, best_q = spec, q
        return best_q

    best, best_q = None, 0.0
    for media_type in available:
        q = quality(media_type)
        if q > best_q:
            best, best_q = media_type, q
    return best
''',
    tests=[
        ["text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8", ["application/json", "text/html"]],
        ["*/*;q=1, application/json;q=0.2", ["application/json", "text/csv"]],
        ["application/json", ["application/json", "text/html"]],
        ["", ["application/json", "text/csv"]],
        ["text/csv", ["application/json"]],
        ["application/json;q=0.5, text/csv;q=0.9", ["application/json", "text/csv"]],
        ["text/*;q=0.3, text/csv;q=0, */*;q=0.1", ["text/csv", "text/plain", "application/json"]],
        ["*/*;q=0", ["application/json"]],
        ["APPLICATION/JSON", ["application/json"]],
        ["text/html;level=1;q=0.7, application/json;q=0.7", ["application/json", "text/html"]],
        ["image/*", ["image/png", "image/webp"]],
        ["application/json;q=abc, text/csv;q=0.2", ["application/json", "text/csv"]],
        ["text/csv, */*;q=0.5", ["Application/JSON", "text/csv"]],
        [" , ;q=1, text/csv", ["text/csv"]],
        ["*/json", ["application/json"]],
        ["application/json;Q=0.4, application/json;q=0.6", ["application/json"]],
    ],
    examples=2,
    wrong_solutions=[
        '''def negotiate(accept, available):
    if not accept.strip():
        return available[0] if available else None
    for t in available:
        if t.lower() in accept.lower():
            return t
    return None
''',
        '''def negotiate(accept, available):
    if not accept.strip():
        accept = "*/*"
    ranges = []
    for piece in accept.split(","):
        parts = [p.strip() for p in piece.split(";")]
        if "/" not in parts[0]:
            continue
        typ, sub = parts[0].lower().split("/", 1)
        q = 1.0
        for p in parts[1:]:
            n, _, v = p.partition("=")
            if n.strip().lower() == "q":
                try:
                    q = float(v)
                except ValueError:
                    q = 0.0
        ranges.append((typ, sub, q))
    best, bq = None, 0.0
    for m in available:
        t, _, s = m.lower().partition("/")
        q = max([rq for rt, rs, rq in ranges if (rt, rs) in ((t, s), (t, "*"), ("*", "*"))] or [0.0])
        if q > bq:
            best, bq = m, q
    return best
''',
    ],
    guide=dict(
        prereqs="Request headers and status codes (lesson *HTTP: methods, status codes and headers*); "
                "`str.split`, `str.partition`, `float()`.",
        intuition="Two separate questions are hiding here. First, *how much does the client like each "
                  "format?*: for one media type, find the matching ranges and let the most specific one "
                  "decide, because `application/json;q=0.2` is a more precise statement than `*/*`. "
                  "Second, *which format do we send?*: the highest quality wins and the server's own "
                  "order breaks ties.",
        hints=["Parse the header once into a list of `(type, subtype, q)` triples.",
               "Write a helper `quality(media_type)` that returns the q of the most specific matching range, or 0.",
               "Use a strict `>` when scanning `available`, so earlier types win ties.",
               "`q=0` is an explicit 'never send me this', not a missing value."],
        brute_force="Checking whether each available type appears as a substring of the header ignores "
                    "wildcards and q-values entirely, and treats `text/csv;q=0` as a yes.",
        approach="1. Parse: split on `,`, then on `;`; keep ranges with a `/`; read `q`, dropping ranges "
                 "with an invalid `q`.\n2. For each available type compute its quality: specificity 2 for "
                 "an exact match, 1 for `type/*`, 0 for `*/*`; keep the best specificity, then the best q.\n"
                 "3. Scan `available` in order, keeping the first type with the strictly highest quality > 0.\n\n"
                 "Dry run `text/*;q=0.3, text/csv;q=0, */*;q=0.1` with `[text/csv, text/plain, application/json]`: "
                 "csv is matched exactly with q 0 → 0; plain is matched by `text/*` → 0.3; json only by "
                 "`*/*` → 0.1. Answer `text/plain`.",
        complexity="O(R · A) for R ranges and A available types; both are tiny in practice.",
        pitfalls="- Taking the maximum q of *all* matching ranges: `text/csv;q=0` must beat `text/*;q=0.3`.\n"
                 "- Forgetting that an empty header means `*/*`.\n- Case-sensitive comparison.\n"
                 "- Returning the lower-cased type instead of the server's original string.",
        follow_up="FastAPI does not negotiate automatically: an endpoint returns one `response_class`. To "
                  "serve JSON or CSV from one route, read `request.headers.get('accept')`, call a function "
                  "like this, and raise `HTTPException(406)` when it returns `None`.",
    ),
),
dict(
    id="fastapi-crud-store",
    title="In-Memory CRUD Store with Correct Status Codes",
    difficulty="Medium",
    pattern="API Design",
    kind="class",
    entry="ItemStore",
    description=r"""
Most APIs start as **CRUD**: create, read, update and delete records. Getting the *status codes*
right is half the job. Implement an in-memory store whose methods return `[status, body]` exactly as
the corresponding endpoints would.

An item is `{"id": int, "name": str, "price": number}`. A **valid payload** for create and update is a
dict with exactly the keys `name` and `price`, where `name` is a string of 1 to 50 characters and
`price` is an int or float (not a boolean) that is `>= 0`.

`ItemStore()` methods:

- `create(item)` (`POST /items`): invalid payload → `[422, None]`; a name already used by another item,
  compared case-insensitively → `[409, None]`; otherwise store it with the next id (1, 2, 3, ...; ids
  are never reused, and failed creates do not use one up) → `[201, item]`.
- `get(item_id)` (`GET /items/{id}`): `[200, item]` or `[404, None]`.
- `update(item_id, item)` (`PUT`, full replacement): invalid payload → `[422, None]` **even if the id
  does not exist** (FastAPI validates the body before your code runs); unknown id → `[404, None]`;
  name used by a *different* item → `[409, None]`; otherwise replace → `[200, item]`.
- `patch(item_id, changes)` (`PATCH`, partial): `changes` may contain only `name` and/or `price`, each
  valid if present (an empty dict is fine); anything else → `[422, None]`; then unknown id → `[404,
  None]`; name used by a different item → `[409, None]`; otherwise apply → `[200, item]`.
- `delete(item_id)`: `[204, None]` or `[404, None]`.
- `list_items()`: `[200, [all items in increasing id order]]`.

**Example:** `["ItemStore","create","create","get","get"]`,
`[[],[{"name":"Pen","price":1.5}],[{"name":"Cup","price":4}],[1],[3]]` →
`[None,[201,{"id":1,"name":"Pen","price":1.5}],[201,{"id":2,"name":"Cup","price":4}],[200,{"id":1,"name":"Pen","price":1.5}],[404,None]]`
""",
    starter='''class ItemStore:
    def __init__(self):
        pass

    def create(self, item: dict) -> list:
        pass

    def get(self, item_id: int) -> list:
        pass

    def update(self, item_id: int, item: dict) -> list:
        pass

    def patch(self, item_id: int, changes: dict) -> list:
        pass

    def delete(self, item_id: int) -> list:
        pass

    def list_items(self) -> list:
        pass
''',
    solution='''class ItemStore:
    def __init__(self):
        self.items = {}
        self.next_id = 1

    @staticmethod
    def _name_ok(v):
        return isinstance(v, str) and 1 <= len(v) <= 50

    @staticmethod
    def _price_ok(v):
        return isinstance(v, (int, float)) and not isinstance(v, bool) and v >= 0

    def _full_ok(self, item):
        return (isinstance(item, dict) and set(item) == {"name", "price"}
                and self._name_ok(item["name"]) and self._price_ok(item["price"]))

    def _taken(self, name, except_id=None):
        low = name.lower()
        return any(i != except_id and it["name"].lower() == low for i, it in self.items.items())

    def create(self, item):
        if not self._full_ok(item):
            return [422, None]
        if self._taken(item["name"]):
            return [409, None]
        new = {"id": self.next_id, "name": item["name"], "price": item["price"]}
        self.items[self.next_id] = new
        self.next_id += 1
        return [201, dict(new)]

    def get(self, item_id):
        it = self.items.get(item_id)
        return [200, dict(it)] if it else [404, None]

    def update(self, item_id, item):
        if not self._full_ok(item):
            return [422, None]
        if item_id not in self.items:
            return [404, None]
        if self._taken(item["name"], item_id):
            return [409, None]
        new = {"id": item_id, "name": item["name"], "price": item["price"]}
        self.items[item_id] = new
        return [200, dict(new)]

    def patch(self, item_id, changes):
        if not isinstance(changes, dict) or not set(changes) <= {"name", "price"}:
            return [422, None]
        if "name" in changes and not self._name_ok(changes["name"]):
            return [422, None]
        if "price" in changes and not self._price_ok(changes["price"]):
            return [422, None]
        if item_id not in self.items:
            return [404, None]
        if "name" in changes and self._taken(changes["name"], item_id):
            return [409, None]
        self.items[item_id].update(changes)
        return [200, dict(self.items[item_id])]

    def delete(self, item_id):
        if item_id not in self.items:
            return [404, None]
        del self.items[item_id]
        return [204, None]

    def list_items(self):
        return [200, [dict(self.items[k]) for k in sorted(self.items)]]
''',
    tests=[
        [["ItemStore", "create", "create", "get", "get"],
         [[], [{"name": "Pen", "price": 1.5}], [{"name": "Cup", "price": 4}], [1], [3]]],
        [["ItemStore", "create", "create", "create", "list_items"],
         [[], [{"name": "Pen", "price": 1}], [{"name": "pen", "price": 2}], [{"name": "PEN ", "price": 3}], []]],
        [["ItemStore", "create", "create", "create", "create", "create", "create", "create", "create"],
         [[], [{"name": "A"}], [{"name": "A", "price": 1, "colour": "red"}], [{"name": "A", "price": -0.01}],
          [{"name": "A", "price": True}], [{"name": "", "price": 1}], [{"name": "x" * 51, "price": 1}],
          [{"name": 123, "price": 1}], [{"name": "A", "price": 0}]]],
        [["ItemStore", "create", "create", "delete", "delete", "create", "list_items"],
         [[], [{"name": "A", "price": 1}], [{"name": "B", "price": 2}], [1], [1], [{"name": "C", "price": 3}], []]],
        [["ItemStore", "create", "update", "update", "update", "update", "get"],
         [[], [{"name": "A", "price": 1}], [1, {"name": "A2", "price": 3}], [9, {"name": "Z", "price": 1}],
          [9, {"name": "x"}], [1, {"name": "A3", "price": -2}], [1]]],
        [["ItemStore", "create", "create", "update", "update", "update"],
         [[], [{"name": "A", "price": 1}], [{"name": "B", "price": 2}], [2, {"name": "a", "price": 1}],
          [2, {"name": "B", "price": 9}], [1, {"name": "A", "price": 0}]]],
        [["ItemStore", "create", "patch", "patch", "patch", "patch", "patch", "patch", "get"],
         [[], [{"name": "A", "price": 1}], [1, {"price": 2.5}], [1, {}], [1, {"colour": "red"}],
          [2, {"price": 1}], [2, {"price": -1}], [1, {"name": ""}], [1]]],
        [["ItemStore", "create", "create", "patch", "patch", "get"],
         [[], [{"name": "A", "price": 1}], [{"name": "B", "price": 2}], [2, {"name": "A"}], [2, {"name": "b"}], [2]]],
        [["ItemStore", "list_items", "get", "delete", "patch", "update"],
         [[], [], [0], [0], [0, {}], [0, {"name": "Q", "price": 1}]]],
        [["ItemStore", "create", "patch", "update", "get"],
         [[], [{"name": "Lamp", "price": 20}], [1, {"name": "Desk lamp"}], [1, {"name": "Lamp", "price": 25}], [1]]],
        [["ItemStore", "create", "delete", "create", "get", "get"],
         [[], [{"name": "Solo", "price": 3}], [1], [{"name": "solo", "price": 4}], [1], [2]]],
        [["ItemStore"] + ["create"] * 60 + ["delete"] * 30 + ["list_items"],
         [[]] + [[{"name": f"item{i}", "price": i}] for i in range(60)] + [[2 * k] for k in range(1, 31)] + [[]]],
    ],
    examples=1,
    wrong_solutions=[
        '''class ItemStore:
    def __init__(self):
        self.items, self.next_id = {}, 1
    def _ok(self, it):
        return (isinstance(it, dict) and set(it) == {"name", "price"} and isinstance(it["name"], str)
                and 1 <= len(it["name"]) <= 50 and isinstance(it["price"], (int, float))
                and not isinstance(it["price"], bool) and it["price"] >= 0)
    def _taken(self, n, ex=None):
        return any(i != ex and v["name"].lower() == n.lower() for i, v in self.items.items())
    def create(self, it):
        if not self._ok(it): return [422, None]
        if self._taken(it["name"]): return [409, None]
        new = {"id": self.next_id, **it}; self.items[self.next_id] = new; self.next_id += 1
        return [201, dict(new)]
    def get(self, i):
        return [200, dict(self.items[i])] if i in self.items else [404, None]
    def update(self, i, it):
        if i not in self.items: return [404, None]
        if not self._ok(it): return [422, None]
        if self._taken(it["name"], i): return [409, None]
        self.items[i] = {"id": i, **it}; return [200, dict(self.items[i])]
    def patch(self, i, ch):
        if i not in self.items: return [404, None]
        if not set(ch) <= {"name", "price"}: return [422, None]
        merged = {k: v for k, v in self.items[i].items() if k != "id"}; merged.update(ch)
        if not self._ok(merged): return [422, None]
        if self._taken(merged["name"], i): return [409, None]
        self.items[i].update(ch); return [200, dict(self.items[i])]
    def delete(self, i):
        if i not in self.items: return [404, None]
        del self.items[i]; return [204, None]
    def list_items(self):
        return [200, [dict(self.items[k]) for k in sorted(self.items)]]
''',
        '''class ItemStore:
    def __init__(self):
        self.items, self.next_id = {}, 1
    def _ok(self, it):
        return (isinstance(it, dict) and set(it) == {"name", "price"} and isinstance(it["name"], str)
                and 1 <= len(it["name"]) <= 50 and isinstance(it["price"], (int, float)) and it["price"] >= 0)
    def _taken(self, n, ex=None):
        return any(i != ex and v["name"] == n for i, v in self.items.items())
    def create(self, it):
        if not self._ok(it): return [422, None]
        if self._taken(it["name"]): return [409, None]
        new = {"id": self.next_id, **it}; self.items[self.next_id] = new; self.next_id += 1
        return [201, dict(new)]
    def get(self, i):
        return [200, dict(self.items[i])] if i in self.items else [404, None]
    def update(self, i, it):
        if not self._ok(it): return [422, None]
        if i not in self.items: return [404, None]
        if self._taken(it["name"], i): return [409, None]
        self.items[i] = {"id": i, **it}; return [200, dict(self.items[i])]
    def patch(self, i, ch):
        if not set(ch) <= {"name", "price"}: return [422, None]
        if i not in self.items: return [404, None]
        merged = {k: v for k, v in self.items[i].items() if k != "id"}; merged.update(ch)
        if not self._ok(merged): return [422, None]
        if self._taken(merged["name"], i): return [409, None]
        self.items[i].update(ch); return [200, dict(self.items[i])]
    def delete(self, i):
        if i not in self.items: return [404, None]
        del self.items[i]; return [204, None]
    def list_items(self):
        return [200, [dict(self.items[k]) for k in sorted(self.items)]]
''',
    ],
    guide=dict(
        prereqs="Status codes 201/204/404/409/422 (lessons *HTTP: methods, status codes and headers* and "
                "*Request bodies, responses and status codes*); PUT versus PATCH (lesson *REST design and JSON*).",
        intuition="Each method is a short list of checks in a fixed order, and the order *is* the "
                  "specification. FastAPI validates the request body before your endpoint runs, so a bad "
                  "body yields 422 even for an id that does not exist; only then does your code look the "
                  "id up (404); only then can it detect a clash with another record (409).",
        hints=["Write the validation helpers first: `_name_ok`, `_price_ok`, and `_full_ok` for a whole payload.",
               "`isinstance(True, int)` is `True` in Python, so reject booleans explicitly.",
               "A name clash ignores the item being updated: renaming item 2 from `B` to `b` is allowed.",
               "Keep a `next_id` counter that only grows; do not use `len(items) + 1`."],
        brute_force="Not applicable: the work is in the order of the checks, not in the data structure.",
        approach="Store items in a dict keyed by id. `create`: validate → clash → assign id → 201. `update`: "
                 "validate → exists → clash (excluding itself) → replace → 200. `patch`: validate only the "
                 "keys present (and reject unknown keys) → exists → clash → merge → 200. `delete`: exists → "
                 "remove → 204.\n\nDry run of test 5: create A (id 1); update 1 to A2 → 200; update 9 with a "
                 "valid body → 404; update 9 with `{name: 'x'}` → 422 (validation first); update 1 with a "
                 "negative price → 422; get 1 → A2.",
        complexity="O(1) for get/delete, O(n) for the name-clash scan (a second dict keyed by lower-cased "
                   "name would make it O(1)); `list_items` is O(n log n).",
        pitfalls="- Checking 404 before 422.\n- Case-sensitive uniqueness.\n- Accepting `true` as a price.\n"
                 "- Reusing ids after a delete (clients may have cached the old id).\n"
                 "- Treating PATCH like PUT and requiring every field.",
        follow_up="In a real service the uniqueness check belongs in the database as a unique index on "
                  "`lower(name)`: two concurrent requests can both pass an in-memory check. Catch the "
                  "integrity error in the data layer and turn it into a `Duplicate` domain exception (409).",
    ),
),
dict(
    id="fastapi-settings-from-env",
    title="Load Typed Settings from Environment Variables",
    difficulty="Medium",
    pattern="Configuration",
    entry="loadSettings",
    description=r"""
`pydantic-settings` reads configuration from environment variables, converts the text to the right
types and refuses to start when something is missing or malformed. Implement a small version.

`loadSettings(schema, env, prefix)`:

- `schema` maps a field name to a spec. `[type]` means **required**; `[type, default]` means optional
  with that default (the default may be `None`). `type` is one of `"str"`, `"int"`, `"float"`,
  `"bool"`, `"list"`.
- `env` maps environment variable names to string values. The variable for field `f` is
  `prefix + f`, looked up **case-insensitively** (`APP_PORT`, `app_port` and `App_Port` are the same).
  Variables that match no field are ignored. No two variables in a test differ only by case.
- Conversion of a found value:
  - `str`: the value unchanged (spaces kept).
  - `int` / `float`: Python's `int()` / `float()` of the value with surrounding spaces removed;
    failure → invalid. (Tests use only ordinary decimal numbers.)
  - `bool`: after stripping and lower-casing, `1 true yes on` → `True`, `0 false no off` → `False`,
    anything else → invalid.
  - `list`: split on commas, strip each piece, drop empty pieces (so `""` gives `[]`).
- A field with no variable takes its default **as given, without conversion** (pydantic does not
  validate defaults unless asked to). A required field with no variable is `"missing"`.
- If any field is missing or invalid, return `{"errors": [[field, "missing" or "invalid"], ...]}` in
  schema order. Otherwise return `{"settings": {field: value, ...}}` in schema order.

**Example:** `schema = {"debug": ["bool", False], "port": ["int", 8000], "db_url": ["str"]}`,
`env = {"APP_DB_URL": "sqlite://", "APP_PORT": "9000"}`, `prefix = "APP_"` →
`{"settings": {"debug": False, "port": 9000, "db_url": "sqlite://"}}`
""",
    starter='''def loadSettings(schema: dict, env: dict, prefix: str) -> dict:
    pass
''',
    solution='''TRUE = {"1", "true", "yes", "on"}
FALSE = {"0", "false", "no", "off"}

def _convert(typ, raw):
    s = raw.strip()
    if typ == "str":
        return raw
    if typ == "int":
        return int(s)
    if typ == "float":
        return float(s)
    if typ == "bool":
        if s.lower() in TRUE:
            return True
        if s.lower() in FALSE:
            return False
        raise ValueError(raw)
    if typ == "list":
        return [p.strip() for p in raw.split(",") if p.strip()]
    raise ValueError(typ)

def loadSettings(schema, env, prefix):
    lookup = {k.lower(): v for k, v in env.items()}
    settings, errors = {}, []
    for field, spec in schema.items():
        key = (prefix + field).lower()
        if key not in lookup:
            if len(spec) == 1:
                errors.append([field, "missing"])
            else:
                settings[field] = spec[1]
            continue
        try:
            settings[field] = _convert(spec[0], lookup[key])
        except ValueError:
            errors.append([field, "invalid"])
    return {"errors": errors} if errors else {"settings": settings}
''',
    tests=[
        [{"debug": ["bool", False], "port": ["int", 8000], "db_url": ["str"]}, {"APP_DB_URL": "sqlite://", "APP_PORT": "9000"}, "APP_"],
        [{"debug": ["bool", False], "port": ["int", 8000], "db_url": ["str"]}, {}, "APP_"],
        [{"port": ["int", 1], "debug": ["bool", False], "key": ["str"]}, {"APP_PORT": "80.5", "APP_DEBUG": "maybe"}, "APP_"],
        [{"debug": ["bool", False], "port": ["int", 1]}, {"app_debug": "TRUE", "App_Port": " 42 "}, "APP_"],
        [{"a": ["bool"], "b": ["bool"], "c": ["bool"], "d": ["bool"]}, {"X_A": "yes", "X_B": "Off", "X_C": "1", "X_D": " 0 "}, "X_"],
        [{"hosts": ["list"], "empty": ["list", ["default"]]}, {"S_HOSTS": "a.com, b.com,,c.com ", "S_EMPTY": ""}, "S_"],
        [{"ratio": ["float"], "neg": ["float", 0.0]}, {"M_RATIO": "0.25", "M_NEG": "-1e3"}, "M_"],
        [{"debug": ["bool", False]}, {"DEBUG": "on"}, ""],
        [{"port": ["int", "8000"], "workers": ["int", 2]}, {}, "APP_"],
        [{"sentry_dsn": ["str", None], "name": ["str", "svc"]}, {"APP_NAME": "api"}, "APP_"],
        [{"motto": ["str"]}, {"X_MOTTO": "  hi there "}, "X_"],
        [{"port": ["int", 1]}, {"PORT": "1", "APP_PORT": "2", "OTHER_PORT": "3"}, "APP_"],
        [{"port": ["int"], "ratio": ["float"], "tags": ["list"]}, {"P_PORT": "", "P_RATIO": "abc"}, "P_"],
        [{f"f{i}": ["int", i] for i in range(40)}, {f"APP_F{i}": str(i * 10) for i in range(0, 40, 3)}, "APP_"],
    ],
    examples=2,
    wrong_solutions=[
        '''def loadSettings(schema, env, prefix):
    settings, errors = {}, []
    for field, spec in schema.items():
        key = prefix + field.upper()
        if key not in env:
            if len(spec) == 1: errors.append([field, "missing"])
            else: settings[field] = spec[1]
            continue
        raw, typ = env[key], spec[0]
        try:
            if typ == "int": v = int(raw.strip())
            elif typ == "float": v = float(raw.strip())
            elif typ == "bool":
                s = raw.strip().lower()
                if s in ("1", "true", "yes", "on"): v = True
                elif s in ("0", "false", "no", "off"): v = False
                else: raise ValueError
            elif typ == "list": v = [p.strip() for p in raw.split(",") if p.strip()]
            else: v = raw
            settings[field] = v
        except ValueError:
            errors.append([field, "invalid"])
    return {"errors": errors} if errors else {"settings": settings}
''',
        '''def loadSettings(schema, env, prefix):
    lk = {k.lower(): v for k, v in env.items()}
    settings, errors = {}, []
    for field, spec in schema.items():
        key = (prefix + field).lower()
        if key not in lk:
            if len(spec) == 1: errors.append([field, "missing"])
            else: settings[field] = spec[1]
            continue
        raw, typ = lk[key], spec[0]
        try:
            if typ == "int": v = int(raw.strip())
            elif typ == "float": v = float(raw.strip())
            elif typ == "bool": v = raw.strip().lower() == "true"
            elif typ == "list": v = [p.strip() for p in raw.split(",") if p.strip()]
            else: v = raw
            settings[field] = v
        except ValueError:
            errors.append([field, "invalid"])
    return {"errors": errors} if errors else {"settings": settings}
''',
        '''def loadSettings(schema, env, prefix):
    lk = {k.lower(): v for k, v in env.items()}
    conv = {"int": int, "float": float, "str": str}
    settings, errors = {}, []
    for field, spec in schema.items():
        key = (prefix + field).lower()
        typ = spec[0]
        if key not in lk:
            if len(spec) == 1: errors.append([field, "missing"]); continue
            raw = spec[1]
            if raw is None or typ not in conv: settings[field] = raw; continue
            settings[field] = conv[typ](raw); continue
        raw = lk[key]
        try:
            if typ == "bool":
                s = raw.strip().lower()
                if s in ("1", "true", "yes", "on"): v = True
                elif s in ("0", "false", "no", "off"): v = False
                else: raise ValueError
            elif typ == "list": v = [p.strip() for p in raw.split(",") if p.strip()]
            elif typ == "str": v = raw
            else: v = conv[typ](raw.strip())
            settings[field] = v
        except ValueError:
            errors.append([field, "invalid"])
    return {"errors": errors} if errors else {"settings": settings}
''',
    ],
    guide=dict(
        prereqs="Settings and the twelve-factor principle (lesson *Settings and configuration management*); "
                "dict comprehensions; `try`/`except ValueError`.",
        intuition="Environment variables are always text, and configuration bugs should stop the app at "
                  "startup, not surface at 3 a.m. So: find each field's variable (ignoring case), convert "
                  "it strictly, and collect *every* problem before giving up, so the operator can fix them "
                  "all in one go.",
        hints=["Build a lower-cased copy of `env` once, then look up `(prefix + field).lower()`.",
               "Put each type's conversion in one helper that raises `ValueError` on bad input.",
               "A bool needs an explicit 'false' list: anything not in either list is invalid, not False.",
               "Defaults are used exactly as given: `\"8000\"` stays a string."],
        brute_force="Already linear; the challenge is the conversion rules and error collection.",
        approach="1. Lower-case the environment keys.\n2. For each field in schema order: if the variable is "
                 "missing, record `missing` for required fields or use the default; otherwise convert it and "
                 "record `invalid` on `ValueError`.\n3. Return errors if any, else the settings.\n\nDry run of "
                 "test 3: `port` is `\"80.5\"` → `int()` fails → invalid; `debug` is `\"maybe\"` → invalid; "
                 "`key` is absent and required → missing.",
        complexity="O(F + E) for F fields and E variables.",
        pitfalls="- Case-sensitive lookup.\n- `bool(\"false\")` is `True` in Python: never use `bool()` on text.\n"
                 "- Stopping at the first error instead of reporting them all.\n- Stripping `str` values.\n"
                 "- Converting defaults.",
        follow_up="pydantic-settings adds sources with a precedence order (init arguments, environment, "
                  "`.env` file, secrets directory, defaults), nested models via a delimiter such as "
                  "`APP_DB__HOST`, JSON parsing for complex types, and `SecretStr` to keep values out of logs.",
    ),
),
dict(
    id="fastapi-yield-teardown",
    title="Set-Up and Tear-Down Order of Yield Dependencies",
    difficulty="Easy",
    pattern="Dependency Injection",
    entry="runRequest",
    description=r"""
A dependency with `yield` has two halves: code before `yield` runs before the endpoint (set-up) and
code after it runs afterwards (tear-down). Simulate one request.

`runRequest(deps, endpoint_status)`:

- `deps` is the list of dependencies **in the order FastAPI resolved them**, each `[name, fail]`.
  `fail = 0` means its set-up succeeds; any other number means its set-up raises
  `HTTPException(fail)`.
- A name that appears again later in the list is the **same cached dependency**: skip it (no second
  set-up, no second tear-down; its `fail` value is ignored).
- Go through the list, logging `"setup:<name>"` for each set-up. If a set-up fails, stop: no further
  set-ups and **no endpoint**. The failed dependency never reached its `yield`, so it gets no
  tear-down.
- If every set-up succeeded, log `"endpoint"`. `endpoint_status = 0` means it returns normally;
  any other number means it raises `HTTPException(endpoint_status)`.
- Then tear down every dependency that completed set-up, in **reverse** order, logging
  `"teardown:<name>:ok"`, or `"teardown:<name>:error"` if an exception is propagating (code after
  `yield` sees it).
- The response status is the status of the exception raised, or `200` if none was.

Return `[status, log]`.

**Example:** `runRequest([["db", 0], ["user", 401], ["page", 0]], 0)` →
`[401, ["setup:db", "setup:user", "teardown:db:error"]]`
""",
    starter='''def runRequest(deps: list, endpoint_status: int) -> list:
    pass
''',
    solution='''def runRequest(deps, endpoint_status):
    log, completed, seen = [], [], set()
    error = 0
    for name, fail in deps:
        if name in seen:
            continue
        seen.add(name)
        log.append("setup:" + name)
        if fail:
            error = fail
            break
        completed.append(name)
    if not error:
        log.append("endpoint")
        error = endpoint_status
    outcome = "error" if error else "ok"
    for name in reversed(completed):
        log.append(f"teardown:{name}:{outcome}")
    return [error or 200, log]
''',
    tests=[
        [[["db", 0], ["user", 401], ["page", 0]], 0],
        [[["settings", 0], ["db", 0], ["user", 0]], 0],
        [[["db", 0]], 404],
        [[], 0],
        [[], 500],
        [[["db", 503], ["user", 0]], 0],
        [[["db", 0], ["user", 0], ["db", 0]], 0],
        [[["db", 0], ["db", 500]], 0],
        [[["a", 0], ["b", 403], ["b", 0], ["c", 0]], 0],
        [[["a", 0], ["b", 401]], 500],
        [[["settings", 0], ["session", 0], ["token", 0], ["user", 0], ["session", 0], ["settings", 0]], 422],
        [[[f"dep{i}", 0] for i in range(30)], 0],
        [[[f"dep{i}", 0] for i in range(15)] + [["dep3", 0], ["boom", 418]] + [[f"late{i}", 0] for i in range(5)], 0],
    ],
    examples=2,
    wrong_solutions=[
        '''def runRequest(deps, endpoint_status):
    log, done, seen, err = [], [], set(), 0
    for name, fail in deps:
        if name in seen: continue
        seen.add(name); log.append("setup:" + name)
        if fail: err = fail; break
        done.append(name)
    if not err:
        log.append("endpoint"); err = endpoint_status
    for name in done:
        log.append(f"teardown:{name}:{'error' if err else 'ok'}")
    return [err or 200, log]
''',
        '''def runRequest(deps, endpoint_status):
    log, done, err = [], [], 0
    for name, fail in deps:
        log.append("setup:" + name)
        if fail: err = fail; break
        done.append(name)
    if not err:
        log.append("endpoint"); err = endpoint_status
    for name in reversed(done):
        log.append(f"teardown:{name}:{'error' if err else 'ok'}")
    return [err or 200, log]
''',
        '''def runRequest(deps, endpoint_status):
    log, done, seen, err = [], [], set(), 0
    for name, fail in deps:
        if name in seen: continue
        seen.add(name); log.append("setup:" + name); done.append(name)
        if fail: err = fail; break
    if not err:
        log.append("endpoint"); err = endpoint_status
    for name in reversed(done):
        log.append(f"teardown:{name}:{'error' if err else 'ok'}")
    return [err or 200, log]
''',
    ],
    guide=dict(
        prereqs="Dependencies with `yield` and the per-request cache (lessons *Depends, Annotated and "
                "sub-dependencies* and *Yield dependencies, scopes and test overrides*).",
        intuition="Yield dependencies behave like nested `with` blocks: the first opened is the last "
                  "closed, the way you take off a coat after the jumper you put on over it. A block that "
                  "failed while opening was never entered, so there is nothing to close. And an exception "
                  "travels outward through every block that *is* open, which is why each tear-down can see it.",
        hints=["Keep a list of dependencies whose set-up completed; tear down `reversed(...)` of it.",
               "Use a `seen` set to skip cached repeats.",
               "Decide 'ok' or 'error' once, after the endpoint step, and use it for every tear-down."],
        brute_force="Already linear; the challenge is the order and the skip rules.",
        approach="Loop over `deps`, skipping names already seen. Log the set-up; on failure record the "
                 "status and stop; otherwise remember the name. If nothing failed, log the endpoint and "
                 "take its status. Tear down the remembered names in reverse.\n\nDry run of the example: "
                 "`db` sets up; `user` fails with 401 → stop. Only `db` completed → `teardown:db:error`. "
                 "Result `[401, [...]]`.",
        complexity="O(n) time and space.",
        pitfalls="- Tearing down in set-up order.\n- Tearing down the dependency that failed during set-up.\n"
                 "- Running the endpoint after a failed set-up.\n- Setting up a cached dependency twice.",
        follow_up="FastAPI drives this with an `AsyncExitStack`: each yield dependency is entered as a "
                  "context manager and the stack unwinds in reverse. Because exceptions are thrown into the "
                  "generator at the `yield`, wrap it in `try/except/finally` to roll back a transaction on "
                  "error and always close the session; re-raise what you catch.",
    ),
),
dict(
    id="fastapi-router-include",
    title="Flatten Nested Routers and Find Shadowed Routes",
    difficulty="Medium",
    pattern="Routing",
    entry="flattenRoutes",
    description=r"""
Bigger FastAPI apps split routes across `APIRouter`s that are included into each other, each adding a
path prefix, tags and dependencies. The app ends up with one flat, ordered list of routes, and the
first route that matches a request wins. Compute that list.

`flattenRoutes(router)`: a router is a dict with optional keys `prefix` (string, default `""`),
`tags` (list), `dependencies` (list), `routes` (list of `[method, path, name]`) and `include` (list of
child routers). Missing keys mean empty.

- **Order:** a router's own routes come first, in order, then each included router's routes,
  recursively (depth-first, in `include` order).
- **Path:** the concatenation of every prefix from the root down, then the route's path. If the result
  is the empty string, use `"/"`.
- **Tags:** the root's tags, then each deeper router's, with duplicates removed (first occurrence
  kept).
- **Dependencies:** the root's first, then each deeper router's; duplicates kept.
- **Reachable:** a route is unreachable when an earlier route with the **same method** matches every
  path it matches. Split both paths on `"/"`; the earlier one covers the later one if they have the
  same number of segments and, position by position, the earlier segment is a parameter (it starts
  with `{` and ends with `}`), or both segments are the same literal text. A literal never covers a
  parameter. Parameters never contain `:` converters.

Return a list of `[method, path, name, tags, dependencies, reachable]`.

**Example:** a root with route `["GET", "/health", "health"]` that includes
`{"prefix": "/users", "tags": ["users"], "dependencies": ["auth"], "routes": [["GET", "/{user_id}", "get_user"], ["GET", "/me", "me"]]}`
→ `[["GET","/health","health",[],[],True], ["GET","/users/{user_id}","get_user",["users"],["auth"],True], ["GET","/users/me","me",["users"],["auth"],False]]`
""",
    starter='''def flattenRoutes(router: dict) -> list:
    pass
''',
    solution='''def _is_param(seg):
    return seg.startswith("{") and seg.endswith("}")

def _covers(earlier, later):
    a, b = earlier.split("/"), later.split("/")
    if len(a) != len(b):
        return False
    for x, y in zip(a, b):
        if _is_param(x):
            continue
        if _is_param(y) or x != y:
            return False
    return True

def flattenRoutes(router):
    flat = []

    def walk(r, prefix, tags, deps):
        prefix = prefix + r.get("prefix", "")
        tags = list(tags)
        for t in r.get("tags", []):
            if t not in tags:
                tags.append(t)
        deps = deps + list(r.get("dependencies", []))
        for method, path, name in r.get("routes", []):
            flat.append([method, (prefix + path) or "/", name, list(tags), list(deps)])
        for child in r.get("include", []):
            walk(child, prefix, tags, deps)

    walk(router, "", [], [])
    out = []
    for i, (method, path, name, tags, deps) in enumerate(flat):
        reachable = not any(flat[j][0] == method and _covers(flat[j][1], path) for j in range(i))
        out.append([method, path, name, tags, deps, reachable])
    return out
''',
    tests=[
        [{"routes": [["GET", "/health", "health"]],
          "include": [{"prefix": "/users", "tags": ["users"], "dependencies": ["auth"],
                       "routes": [["GET", "/{user_id}", "get_user"], ["GET", "/me", "me"], ["POST", "", "create_user"]]}]}],
        [{"prefix": "/api", "dependencies": ["log"],
          "include": [{"prefix": "/v1", "tags": ["v1"],
                       "include": [{"prefix": "/items", "tags": ["items", "v1"], "dependencies": ["db"],
                                    "routes": [["GET", "/{id}", "read_item"], ["DELETE", "/{id}", "delete_item"]]}]}]}],
        [{}],
        [{"routes": [["GET", "", "root"], ["GET", "/", "root2"]]}],
        [{"prefix": "/items", "routes": [["GET", "/{id}", "read"], ["PUT", "/{id}", "replace"], ["DELETE", "/{id}", "remove"]]}],
        [{"prefix": "/users", "routes": [["GET", "/me", "me"], ["GET", "/{id}", "by_id"]]}],
        [{"routes": [["GET", "/files/{name}", "one"], ["GET", "/files/a/b", "nested"]]}],
        [{"routes": [["GET", "/a/{x}/{y}", "xy"], ["GET", "/a/{p}/b", "pb"], ["GET", "/a/{x}/c", "xc"], ["POST", "/a/{p}/b", "post_pb"]]}],
        [{"routes": [["GET", "/a/{x}/c", "xc"], ["GET", "/a/{p}/{q}", "pq"]]}],
        [{"routes": [["GET", "/items", "no_slash"], ["GET", "/items/", "slash"]]}],
        [{"include": [{"prefix": "/late", "routes": [["GET", "/x", "child"]]}], "routes": [["GET", "/late/{anything}", "root_route"]]}],
        [{"tags": ["app"], "include": [{"prefix": "/v1", "tags": ["app", "billing"], "routes": [["GET", "/invoices", "list_v1"]]},
                                        {"prefix": "/v2", "tags": ["billing"], "routes": [["GET", "/invoices", "list_v2"]]}]}],
        [{"prefix": "", "tags": ["t0"], "dependencies": ["d0"],
          "include": [{"prefix": f"/l{i}", "tags": [f"t{i}"], "dependencies": [f"d{i}"],
                       "routes": [["GET", "/{id}", f"get{i}"], ["GET", "/list", f"list{i}"]]} for i in range(1, 15)]}],
    ],
    examples=1,
    wrong_solutions=[
        '''def flattenRoutes(router):
    flat = []
    def walk(r, prefix, tags, deps):
        prefix += r.get("prefix", "")
        tags = list(tags) + [t for t in r.get("tags", []) if t not in tags]
        deps = deps + list(r.get("dependencies", []))
        for m, p, n in r.get("routes", []):
            flat.append([m, (prefix + p) or "/", n, list(tags), list(deps)])
        for c in r.get("include", []):
            walk(c, prefix, tags, deps)
    walk(router, "", [], [])
    out = []
    for i, (m, p, n, t, d) in enumerate(flat):
        out.append([m, p, n, t, d, not any(flat[j][0] == m and flat[j][1] == p for j in range(i))])
    return out
''',
        '''def flattenRoutes(router):
    flat = []
    def walk(r, prefix, tags, deps):
        prefix += r.get("prefix", "")
        tags = list(tags) + [t for t in r.get("tags", []) if t not in tags]
        deps = deps + list(r.get("dependencies", []))
        for c in r.get("include", []):
            walk(c, prefix, tags, deps)
        for m, p, n in r.get("routes", []):
            flat.append([m, (prefix + p) or "/", n, list(tags), list(deps)])
    walk(router, "", [], [])
    def cov(a, b):
        a, b = a.split("/"), b.split("/")
        return len(a) == len(b) and all(x.startswith("{") or (x == y and not y.startswith("{")) for x, y in zip(a, b))
    return [[m, p, n, t, d, not any(flat[j][0] == m and cov(flat[j][1], p) for j in range(i))]
            for i, (m, p, n, t, d) in enumerate(flat)]
''',
        '''def flattenRoutes(router):
    flat = []
    def walk(r, prefix, tags, deps):
        prefix += r.get("prefix", "")
        tags = list(tags) + list(r.get("tags", []))
        deps = deps + list(r.get("dependencies", []))
        for m, p, n in r.get("routes", []):
            flat.append([m, (prefix + p) or "/", n, list(tags), list(deps)])
        for c in r.get("include", []):
            walk(c, prefix, tags, deps)
    walk(router, "", [], [])
    def cov(a, b):
        a, b = a.split("/"), b.split("/")
        return len(a) == len(b) and all(x.startswith("{") or (x == y and not y.startswith("{")) for x, y in zip(a, b))
    return [[m, p, n, t, d, not any(flat[j][0] == m and cov(flat[j][1], p) for j in range(i))]
            for i, (m, p, n, t, d) in enumerate(flat)]
''',
    ],
    guide=dict(
        prereqs="`APIRouter`, `include_router`, prefixes and router-level dependencies (lesson *APIRouter and "
                "bigger applications*); recursion over nested dicts.",
        intuition="Including a router copies its routes into the parent, with the parent's prefix, tags "
                  "and dependencies wrapped around them. After that, routing is a first-match scan down one "
                  "list, so a broad template such as `/users/{user_id}` registered before `/users/me` "
                  "silently swallows it: `me` becomes the value of `user_id`.",
        hints=["Recurse with the accumulated prefix, tags and dependencies as arguments.",
               "Emit a router's own routes before recursing into its children.",
               "For reachability compare each route with every earlier route of the same method.",
               "Segment-by-segment: a parameter covers anything; a literal covers only the same literal."],
        brute_force="Comparing full path strings for equality finds exact duplicates but misses the classic "
                    "bug, a parameter route shadowing a literal one.",
        approach="1. Depth-first walk building `[method, path, name, tags, deps]`.\n2. For route i, mark it "
                 "unreachable if any j < i has the same method and `covers(path_j, path_i)`.\n\nDry run of "
                 "the example: `/health` first. Then the users router: `/users/{user_id}` is reachable; "
                 "`/users/me` has the same segment count, `{user_id}` covers `me`, so it is unreachable; "
                 "`POST /users` is a different method and path, reachable.",
        complexity="O(n² · s) for n routes of s segments, fine for the few hundred routes of a real app.",
        pitfalls="- Recursing into children before emitting the router's own routes.\n- Letting a literal "
                 "cover a parameter (`/a/{x}/c` does not shadow `/a/{p}/{q}`).\n- Comparing across methods.\n"
                 "- Forgetting that the empty path becomes `/`.\n- Not deduplicating tags.",
        follow_up="Fix shadowing by declaring literal routes before parameter routes, or by typing the "
                  "parameter (`user_id: int` makes `me` fail validation, though FastAPI then answers 422 "
                  "rather than trying the next route). `app.routes` shows the real flattened list.",
    ),
),
dict(
    id="fastapi-token-claims",
    title="Validate Access-Token Claims with an Injected Clock",
    difficulty="Medium",
    pattern="Authentication",
    entry="checkToken",
    description=r"""
After a JWT's signature has been verified, its **claims** (the fields inside it) still have to be
checked: is it expired, is it meant for this API, does it carry the right permissions? Passing the
current time in as an argument (an *injected clock*) makes the check testable. Implement it.

`checkToken(claims, now, audience, leeway, required_scopes)` returns `[status, reason_or_subject]`.
Apply these checks **in this order** and return at the first failure:

1. `sub` missing, not a string, or empty → `[401, "missing sub"]`.
2. `exp` missing → `[401, "missing exp"]`.
3. `now >= exp + leeway` → `[401, "expired"]`.
4. `nbf` ("not before") present and `now + leeway < nbf` → `[401, "not yet valid"]`.
5. `iat` ("issued at") present and `iat > now + leeway` → `[401, "issued in the future"]`.
6. Audience: the token's `aud` may be a string, a list of strings, or absent. If `audience` is a
   non-empty string, it must equal `aud` or be in the list, else `[401, "wrong audience"]`. If
   `audience` is empty (`""`), a token that *does* carry a non-empty `aud` is also rejected with
   `[401, "wrong audience"]` (PyJWT behaves this way: a token aimed at some audience should not be
   accepted by a service that expects none).
7. `scope` is a space-separated string (absent means no scopes). Every scope in `required_scopes`
   must be present as a whole word, else `[403, "insufficient scope"]`.

Otherwise return `[200, sub]`. Times are integers (seconds); `leeway >= 0`.

**Example:** `checkToken({"sub": "ann", "exp": 1100, "aud": "api", "scope": "items:read items:write"}, 1000, "api", 0, ["items:read"])` → `[200, "ann"]`
""",
    starter='''def checkToken(claims: dict, now: int, audience: str, leeway: int, required_scopes: list) -> list:
    pass
''',
    solution='''def checkToken(claims, now, audience, leeway, required_scopes):
    sub = claims.get("sub")
    if not isinstance(sub, str) or not sub:
        return [401, "missing sub"]
    exp = claims.get("exp")
    if exp is None:
        return [401, "missing exp"]
    if now >= exp + leeway:
        return [401, "expired"]
    nbf = claims.get("nbf")
    if nbf is not None and now + leeway < nbf:
        return [401, "not yet valid"]
    iat = claims.get("iat")
    if iat is not None and iat > now + leeway:
        return [401, "issued in the future"]
    aud = claims.get("aud")
    if isinstance(aud, str):
        auds = [aud] if aud else []
    else:
        auds = list(aud or [])
    if audience:
        if audience not in auds:
            return [401, "wrong audience"]
    elif auds:
        return [401, "wrong audience"]
    granted = set(claims.get("scope", "").split())
    if not set(required_scopes) <= granted:
        return [403, "insufficient scope"]
    return [200, sub]
''',
    tests=[
        [{"sub": "ann", "exp": 1100, "aud": "api", "scope": "items:read items:write"}, 1000, "api", 0, ["items:read"]],
        [{"sub": "ann", "exp": 1000}, 1000, "", 0, []],
        [{"sub": "ann", "exp": 995}, 1000, "", 10, []],
        [{"sub": "ann", "exp": 990}, 1000, "", 10, []],
        [{"sub": "ann"}, 1000, "", 0, []],
        [{"exp": 2000}, 1000, "", 0, []],
        [{"sub": "", "exp": 2000}, 1000, "", 0, []],
        [{"sub": "ann", "exp": 2000, "nbf": 1050}, 1000, "", 0, []],
        [{"sub": "ann", "exp": 2000, "nbf": 1005}, 1000, "", 10, []],
        [{"sub": "ann", "exp": 2000, "iat": 1200}, 1000, "", 30, []],
        [{"sub": "ann", "exp": 2000, "aud": ["web", "api"]}, 1000, "api", 0, []],
        [{"sub": "ann", "exp": 2000, "aud": "web"}, 1000, "api", 0, []],
        [{"sub": "ann", "exp": 2000}, 1000, "api", 0, []],
        [{"sub": "ann", "exp": 2000, "aud": "api"}, 1000, "", 0, []],
        [{"sub": "ann", "exp": 2000, "scope": "items:read"}, 1000, "", 0, ["items:read", "admin"]],
        [{"sub": "ann", "exp": 2000}, 1000, "", 0, []],
        [{"sub": "ann", "exp": 900, "aud": "web"}, 1000, "api", 0, []],
        [{"sub": "ann", "exp": 2000, "scope": "items:readonly"}, 1000, "", 0, ["items:read"]],
    ],
    examples=2,
    wrong_solutions=[
        '''def checkToken(claims, now, audience, leeway, required_scopes):
    sub = claims.get("sub")
    if not isinstance(sub, str) or not sub: return [401, "missing sub"]
    if "exp" not in claims: return [401, "missing exp"]
    if now > claims["exp"]: return [401, "expired"]
    if "nbf" in claims and now + leeway < claims["nbf"]: return [401, "not yet valid"]
    if "iat" in claims and claims["iat"] > now + leeway: return [401, "issued in the future"]
    aud = claims.get("aud")
    auds = [aud] if isinstance(aud, str) and aud else list(aud or []) if not isinstance(aud, str) else []
    if audience and audience not in auds: return [401, "wrong audience"]
    if not audience and auds: return [401, "wrong audience"]
    if not set(required_scopes) <= set(claims.get("scope", "").split()): return [403, "insufficient scope"]
    return [200, sub]
''',
        '''def checkToken(claims, now, audience, leeway, required_scopes):
    sub = claims.get("sub")
    if not isinstance(sub, str) or not sub: return [401, "missing sub"]
    if "exp" not in claims: return [401, "missing exp"]
    if now >= claims["exp"] + leeway: return [401, "expired"]
    if "nbf" in claims and now + leeway < claims["nbf"]: return [401, "not yet valid"]
    if "iat" in claims and claims["iat"] > now + leeway: return [401, "issued in the future"]
    aud = claims.get("aud")
    auds = [aud] if isinstance(aud, str) and aud else list(aud or []) if not isinstance(aud, str) else []
    if audience and audience not in auds: return [401, "wrong audience"]
    if not audience and auds: return [401, "wrong audience"]
    if any(s not in claims.get("scope", "") for s in required_scopes): return [403, "insufficient scope"]
    return [200, sub]
''',
        '''def checkToken(claims, now, audience, leeway, required_scopes):
    sub = claims.get("sub")
    if not isinstance(sub, str) or not sub: return [401, "missing sub"]
    if "exp" not in claims: return [401, "missing exp"]
    if now >= claims["exp"] + leeway: return [401, "expired"]
    if "nbf" in claims and now + leeway < claims["nbf"]: return [401, "not yet valid"]
    if "iat" in claims and claims["iat"] > now + leeway: return [401, "issued in the future"]
    aud = claims.get("aud")
    auds = [aud] if isinstance(aud, str) else list(aud or [])
    if audience and audience not in auds: return [401, "wrong audience"]
    if not set(required_scopes) <= set(claims.get("scope", "").split()): return [403, "insufficient scope"]
    return [200, sub]
''',
    ],
    guide=dict(
        prereqs="JWT structure and the `exp`/`sub` claims (lesson *OAuth2 password flow, hashing and JWT*); "
                "OAuth2 scopes and 401 versus 403 (lesson *Authorization, CORS, rate limiting and common vulnerabilities*).",
        intuition="A valid signature only proves the token was issued by you; it says nothing about whether "
                  "it is still valid *now*, meant for *this* service, or allows *this* action. Each claim is "
                  "one small comparison. Taking `now` as a parameter instead of calling `time.time()` means "
                  "every boundary (exactly at expiry, exactly at the leeway) can be tested deterministically.",
        hints=["Leeway forgives clock drift between servers: it extends `exp` and pulls `nbf`/`iat` earlier.",
               "Expired means `now >= exp + leeway`: a token is valid strictly *before* its expiry time.",
               "Normalise `aud` into a list first, treating `\"\"` and a missing claim as no audience.",
               "Split `scope` on whitespace and compare sets; never use substring tests."],
        brute_force="Not applicable; the work is getting each boundary and the check order right.",
        approach="Check `sub`, then `exp`, `nbf`, `iat`, audience and scopes, returning at the first "
                 "failure. Authentication problems (who are you, is the token valid) are 401; a valid token "
                 "lacking permission is 403.\n\nDry run of test 4: exp 990, now 1000, leeway 10 → 1000 >= "
                 "1000 → expired. Test 3: exp 995 → 1000 >= 1005 is false → passes → `[200, 'ann']`.",
        complexity="O(s) for s scopes.",
        pitfalls="- `>` instead of `>=` at the expiry boundary.\n- Forgetting the leeway, or applying it in "
                 "the wrong direction.\n- `'items:read' in 'items:readonly'` is true: compare whole words.\n"
                 "- Answering 401 for missing scopes (the user *is* authenticated; 403 is correct).",
        follow_up="PyJWT performs steps 3 to 6 inside `jwt.decode(token, key, algorithms=['HS256'], "
                  "audience='api', leeway=10)`, raising `ExpiredSignatureError`, `ImmatureSignatureError` "
                  "or `InvalidAudienceError`; FastAPI's `SecurityScopes` supplies `required_scopes` per route.",
    ),
),
]
