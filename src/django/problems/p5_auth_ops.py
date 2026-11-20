_GROUPS = {
    "editors": ["stories.change_story", "stories.delete_story"],
    "members": ["stories.add_story", "stories.change_own_story", "stories.view_story"],
    "moderators": ["stories.delete_reply"],
}
_ANA = {"id": 1, "is_active": True, "is_superuser": False, "perms": [], "groups": ["members"]}
_BO = {"id": 2, "is_active": True, "is_superuser": False, "perms": ["stories.delete_own_story"], "groups": ["editors", "ghosts"]}
_ROOT = {"id": 3, "is_active": True, "is_superuser": True, "perms": [], "groups": []}
_GONE = {"id": 4, "is_active": False, "is_superuser": True, "perms": ["stories.view_story"], "groups": ["editors"]}
_STORY1 = {"owner_id": 1}

_SCHEMA = {
    "DEBUG": {"type": "bool"},
    "SECRET_KEY": {"type": "str", "required": True},
    "ALLOWED_HOSTS": {"type": "list"},
    "DB_PORT": {"type": "int"},
    "EMAIL_HOST": {"type": "str"},
}
_ENVFILE = [
    "# local development",
    "",
    "DEBUG=true",
    "export SECRET_KEY='dev-only-key'",
    'ALLOWED_HOSTS = "localhost, 127.0.0.1,,"',
    "DB_PORT=5432   # default postgres",
    "NOT_IN_SCHEMA=1",
    "this line has no equals sign",
]

PROBLEMS = [
dict(
    id="django-permission-check",
    title="has_perm with groups and object ownership",
    difficulty="Medium",
    pattern="Auth",
    entry="can",
    description=r"""
Authorisation answers "may this user do this?". Django's answer combines the user's own permissions, the
permissions of their groups, and two flags; many projects add an ownership rule on top. Implement all of it.

`can(user, perm, obj, groups)`:

- `user`: dict with `id`, `is_active`, `is_superuser`, `perms` (list of permission strings) and `groups`
  (list of group names).
- `perm`: a string `"<app>.<action>_<model>"`, e.g. `"stories.change_story"` (the action never contains `_`).
- `obj`: `None`, or a dict with `owner_id`.
- `groups`: dict mapping group name to its list of permissions. Group names the dict does not know are ignored.

Decision, in this order:

1. An inactive user can do nothing → `False` (even a superuser).
2. An active superuser can do everything → `True`.
3. The user's **effective permissions** are their own `perms` plus those of all their groups. If `perm` is among
   them → `True`.
4. Ownership: if `obj` is given, `obj["owner_id"] == user["id"]`, and the effective permissions contain the
   "own" variant `"<app>.<action>_own_<model>"` → `True`.
5. Otherwise `False`.

**Example:** a member whose group grants `stories.change_own_story` may change a story they own
(`obj={"owner_id": their id}`), but not someone else's, and not "stories in general" (`obj=None`).
""",
    starter='''def can(user: dict, perm: str, obj, groups: dict) -> bool:
    pass
''',
    solution='''def can(user, perm, obj, groups):
    if not user["is_active"]:
        return False
    if user["is_superuser"]:
        return True
    effective = set(user["perms"])
    for name in user["groups"]:
        effective.update(groups.get(name, []))
    if perm in effective:
        return True
    if obj is not None and obj.get("owner_id") == user["id"]:
        app, codename = perm.split(".", 1)
        action, model = codename.split("_", 1)
        return "%s.%s_own_%s" % (app, action, model) in effective
    return False
''',
    tests=[
        [_ANA, "stories.change_story", _STORY1, _GROUPS],
        [_ANA, "stories.change_story", {"owner_id": 2}, _GROUPS],
        [_ANA, "stories.change_story", None, _GROUPS],
        [_ANA, "stories.add_story", None, _GROUPS],
        [_ANA, "stories.delete_story", _STORY1, _GROUPS],
        [_BO, "stories.change_story", _STORY1, _GROUPS],
        [_BO, "stories.delete_story", None, _GROUPS],
        [_BO, "stories.add_story", None, _GROUPS],
        [_BO, "stories.delete_reply", {"owner_id": 2}, _GROUPS],
        [_ROOT, "anything.at_all", None, _GROUPS],
        [_GONE, "stories.view_story", None, _GROUPS],
        [_GONE, "stories.change_story", {"owner_id": 4}, _GROUPS],
        [{"id": 9, "is_active": True, "is_superuser": False, "perms": ["stories.delete_own_story"], "groups": []}, "stories.delete_story", {"owner_id": 9}, {}],
        [{"id": 9, "is_active": True, "is_superuser": False, "perms": ["stories.delete_own_story"], "groups": []}, "stories.delete_own_story", None, {}],
        [{"id": 9, "is_active": True, "is_superuser": False, "perms": ["wiki.change_own_page_draft"], "groups": []}, "wiki.change_page_draft", {"owner_id": 9}, {}],
        [{"id": 0, "is_active": True, "is_superuser": False, "perms": [], "groups": ["members"]}, "stories.change_story", {"owner_id": 0}, _GROUPS],
    ],
    examples=3,
    wrong_solutions=[
        '''def can(user, perm, obj, groups):
    if user["is_superuser"]:
        return True
    eff = set(user["perms"])
    for g in user["groups"]:
        eff.update(groups[g] if g in groups else [])
    return perm in eff
''',
        '''def can(user, perm, obj, groups):
    if not user["is_active"]:
        return False
    if user["is_superuser"]:
        return True
    eff = set(user["perms"])
    for g in user["groups"]:
        eff.update(groups.get(g, []))
    if perm in eff:
        return True
    return obj is not None and obj.get("owner_id") == user["id"]
''',
    ],
    guide=dict(
        prereqs="Lesson *Permissions, authorisation and mixins*; sets.",
        intuition="Permission checks are a short ladder of rules, most decisive first. Inactive beats everything, superuser "
                  "beats the tables, then the union of user and group permissions, then the narrower 'only your own' "
                  "grant. Django's `ModelBackend` implements the first three rungs; object-level rules are your job.",
        hints=[
            "Check `is_active` before `is_superuser`.",
            "Union the user's permissions with each known group's permissions into one set.",
            "Build the 'own' codename by splitting the codename at the **first** underscore.",
        ],
        brute_force="Query the permission tables on every check. Django instead computes the effective set once per request and caches it on the user object (`_perm_cache`).",
        approach="""1. Inactive → `False`. 2. Superuser → `True`. 3. Effective set = own ∪ groups; direct hit → `True`.
4. If the object belongs to the user, test the `_own_` variant. 5. `False`.

**Dry run** Ana (group `members`) changing her own story: not superuser; effective set lacks `stories.change_story`;
the story's owner is Ana and `stories.change_own_story` is present → `True`.""",
        complexity="O(P) to build the effective set of size P, then O(1) lookups.",
        pitfalls="""- A deactivated superuser must be refused.
- Ownership alone is not a permission; the `_own_` grant must exist.
- `user["id"] == 0` is a valid id; do not use truthiness tests.
- Model names may contain underscores (`page_draft`); split the codename only once.""",
        follow_up="Turn this into a custom authentication backend with `has_perm(user_obj, perm, obj=None)` and register it in `AUTHENTICATION_BACKENDS`.",
    ),
),
dict(
    id="django-login-redirect",
    title="Login redirects without open-redirect holes",
    difficulty="Medium",
    pattern="Auth",
    entry="login_redirects",
    description=r"""
When an anonymous visitor opens a protected page, Django sends them to the login page and remembers where they
wanted to go in a `next` query parameter. After a successful login it redirects to `next`, but only if that
value is **safe**: an attacker must not be able to craft a login link that bounces the victim to another site.

`login_redirects(path, next_param, host, login_url, default)` returns a two-element list:

**1. The redirect to the login page** for the protected `path` (a path that may include a query string):
`login_url + "?next=" + quoted`, where `quoted` percent-encodes `path` with `urllib.parse.quote(path, safe="/")`
(so `/` stays, while `?`, `=`, `&` and spaces are encoded).

**2. Where to go after login**, given the `next_param` that actually arrived (possibly attacker-controlled,
possibly `None`). First, if it is `None` use `default`. Otherwise strip surrounding whitespace; the stripped
value is returned if it is safe, else `default`. A value is **unsafe** when any of these holds:

- it is empty;
- it contains a backslash, or any character with code below 32;
- it starts with `///`;
- parsing it with `urllib.parse.urlsplit` gives a scheme other than `""`, `"http"` or `"https"`;
- it has a network location (netloc) that differs from `host` (compare case-insensitively);
- it has a scheme but an empty netloc (e.g. `https:evil.example`, `javascript:alert(1)`);
- it has neither scheme nor netloc and does not start with `/`.

**Example:** `login_redirects("/stories/new/?draft=1", "//evil.example/x", "gazette.example", "/accounts/login/", "/")`
→ `["/accounts/login/?next=/stories/new/%3Fdraft%3D1", "/"]`.
""",
    starter='''def login_redirects(path: str, next_param, host: str, login_url: str, default: str) -> list:
    pass
''',
    solution='''from urllib.parse import quote, urlsplit


def _safe(url, host):
    if not url or "\\\\" in url or any(ord(c) < 32 for c in url) or url.startswith("///"):
        return False
    try:
        parts = urlsplit(url)
    except ValueError:
        return False
    if parts.scheme not in ("", "http", "https"):
        return False
    if parts.netloc:
        return parts.netloc.lower() == host.lower()
    if parts.scheme:
        return False
    return url.startswith("/")


def login_redirects(path, next_param, host, login_url, default):
    to_login = login_url + "?next=" + quote(path, safe="/")
    target = default
    if next_param is not None:
        candidate = next_param.strip()
        if _safe(candidate, host):
            target = candidate
    return [to_login, target]
''',
    tests=[
        ["/stories/new/?draft=1", "//evil.example/x", "gazette.example", "/accounts/login/", "/"],
        ["/stories/new/", "/stories/new/", "gazette.example", "/accounts/login/", "/"],
        ["/", None, "gazette.example", "/accounts/login/", "/home/"],
        ["/search/?q=low tide&page=2", "/search/?q=low%20tide&page=2", "gazette.example", "/login/", "/"],
        ["/a/", "https://evil.example/a/", "gazette.example", "/login/", "/"],
        ["/a/", "https://gazette.example/a/", "gazette.example", "/login/", "/"],
        ["/a/", "HTTP://GAZETTE.EXAMPLE/a/", "gazette.example", "/login/", "/"],
        ["/a/", "javascript:alert(1)", "gazette.example", "/login/", "/"],
        ["/a/", "/\\\\evil.example", "gazette.example", "/login/", "/"],
        ["/a/", "///evil.example", "gazette.example", "/login/", "/"],
        ["/a/", "", "gazette.example", "/login/", "/dash/"],
        ["/a/", "   /stories/7/  ", "gazette.example", "/login/", "/"],
        ["/a/", "stories/7/", "gazette.example", "/login/", "/"],
        ["/a/", "https:evil.example", "gazette.example", "/login/", "/"],
        ["/a/", "/stories/\\n/7/", "gazette.example", "/login/", "/"],
        ["/a/", "ftp://gazette.example/file", "gazette.example", "/login/", "/"],
        ["/caf\\u00e9/menu/", "//gazette.example/ok", "gazette.example", "/login/", "/"],
        ["/a/", "https://gazette.example.evil.io/", "gazette.example", "/login/", "/"],
    ],
    examples=2,
    wrong_solutions=[
        '''def login_redirects(path, next_param, host, login_url, default):
    return [login_url + "?next=" + path, next_param or default]
''',
        '''from urllib.parse import quote
def login_redirects(path, next_param, host, login_url, default):
    to_login = login_url + "?next=" + quote(path, safe="/")
    if next_param is None:
        return [to_login, default]
    n = next_param.strip()
    ok = n.startswith("/") or host in n
    return [to_login, n if ok else default]
''',
    ],
    guide=dict(
        prereqs="Lesson *Login, logout and sign-up views*; `urllib.parse.quote` and `urlsplit`.",
        intuition="Two halves. Building the link is an encoding problem: the original path must survive as a *value* inside "
                  "another URL, so its `?` and `&` have to be escaped. Following the link is a trust problem: `next` "
                  "arrives from the browser, so treat it as hostile and accept only same-site destinations.",
        hints=[
            "`quote(path, safe=\"/\")` is the whole first half.",
            "`//evil.example` has no scheme but **does** have a netloc: it is a scheme-relative URL to another host.",
            "Reject backslashes and control characters before parsing; browsers normalise them in surprising ways.",
        ],
        brute_force="A check such as 'starts with `/`' or 'contains my hostname'. Both are classic vulnerabilities: `//evil.example` starts with a slash, and `https://gazette.example.evil.io` contains the hostname.",
        approach="""1. `to_login = login_url + "?next=" + quote(path, safe="/")`.
2. `None` → default. Strip. Run the unsafe checklist in order; safe → the stripped value, else default.

**Dry run** `next="//evil.example/x"`: not empty, no backslash, does not start with `///`; `urlsplit` gives scheme
`""`, netloc `evil.example` ≠ host → unsafe → default `/`.""",
        complexity="O(n) in the length of the URL.",
        pitfalls="""- Not encoding the query string of the original path: `?next=/a/?b=1&c=2` would lose `c`.
- Substring host checks.
- Forgetting scheme-relative (`//host`) and backslash (`/\\host`) forms.
- In real code never write this yourself: call `django.utils.http.url_has_allowed_host_and_scheme(url, allowed_hosts, require_https)`.""",
        follow_up="Add a `require_https` flag that refuses `http://` targets when the current request is secure, as Django's helper does.",
    ),
),
dict(
    id="django-session-expiry",
    title="Session expiry with explicit timestamps",
    difficulty="Medium",
    pattern="Auth",
    entry="session_log",
    description=r"""
A session is the server-side record that keeps a user logged in between requests. Whether it is still alive
depends on three settings. Replay a timeline of events and say what each one observes.

`session_log(events, cookie_age, save_every_request, expire_at_browser_close)`:

- `events`: list of `[t, action]` with non-decreasing integer timestamps `t` (seconds).
- `cookie_age`: `SESSION_COOKIE_AGE` in seconds. `save_every_request` and `expire_at_browser_close` are booleans.

State: at most one session, with an `expiry` timestamp. Initially there is none. For each event produce one
result string:

| action | behaviour | result |
|---|---|---|
| `login` | discard any existing session; create one with `expiry = t + cookie_age` | `"ok"` |
| `view`, `modify` | no session → `"anonymous"`. Session with `t >= expiry` → delete it, result `"expired"`. Otherwise `"ok"`, and if the action is `modify` **or** `save_every_request` is true, slide the window: `expiry = t + cookie_age` | see left |
| `logout` | delete the session if there is one | `"logged_out"` |
| `close_browser` | if `expire_at_browser_close` is true, delete the session (the cookie was a browser-session cookie) | `"closed"` |

A plain `view` does **not** extend the session unless `save_every_request` is on: Django only saves (and so
re-dates) a session that was modified. After a session expired, later requests are `"anonymous"`.

Return the list of results.

**Example:** `session_log([[0, "login"], [50, "view"], [100, "view"]], 100, False, False)` →
`["ok", "ok", "expired"]`.
""",
    starter='''def session_log(events: list, cookie_age: int, save_every_request: bool, expire_at_browser_close: bool) -> list:
    pass
''',
    solution='''def session_log(events, cookie_age, save_every_request, expire_at_browser_close):
    expiry = None
    out = []
    for t, action in events:
        if action == "login":
            expiry = t + cookie_age
            out.append("ok")
        elif action in ("view", "modify"):
            if expiry is None:
                out.append("anonymous")
            elif t >= expiry:
                expiry = None
                out.append("expired")
            else:
                if action == "modify" or save_every_request:
                    expiry = t + cookie_age
                out.append("ok")
        elif action == "logout":
            expiry = None
            out.append("logged_out")
        else:
            if expire_at_browser_close:
                expiry = None
            out.append("closed")
    return out
''',
    tests=[
        [[[0, "login"], [50, "view"], [100, "view"]], 100, False, False],
        [[[0, "login"], [50, "view"], [100, "view"]], 100, True, False],
        [[[0, "view"], [1, "modify"]], 100, False, False],
        [[], 100, False, False],
        [[[0, "login"], [99, "modify"], [198, "view"], [199, "view"], [200, "view"]], 100, False, False],
        [[[0, "login"], [99, "view"], [198, "view"]], 100, True, False],
        [[[0, "login"], [10, "close_browser"], [20, "view"]], 100, False, True],
        [[[0, "login"], [10, "close_browser"], [20, "view"]], 100, False, False],
        [[[0, "login"], [10, "logout"], [11, "view"], [12, "logout"], [13, "login"], [14, "view"]], 100, False, False],
        [[[0, "login"], [150, "view"], [151, "view"], [152, "login"], [153, "modify"]], 100, False, False],
        [[[0, "login"], [90, "login"], [150, "view"], [190, "view"]], 100, False, False],
        [[[5, "login"], [5, "view"], [5, "modify"]], 0, False, False],
        [[[0, "close_browser"], [1, "login"], [2, "close_browser"], [3, "modify"], [4, "login"], [1000, "view"]], 1209600, True, True],
        [[[0, "login"]] + [[i * 60, "view"] for i in range(1, 40)], 1800, False, False],
        [[[0, "login"]] + [[i * 60, "view"] for i in range(1, 40)], 1800, True, False],
    ],
    examples=2,
    wrong_solutions=[
        '''def session_log(events, cookie_age, save_every_request, expire_at_browser_close):
    expiry, out = None, []
    for t, action in events:
        if action == "login":
            expiry = t + cookie_age; out.append("ok")
        elif action in ("view", "modify"):
            if expiry is None: out.append("anonymous")
            elif t > expiry:
                expiry = None; out.append("expired")
            else:
                expiry = t + cookie_age; out.append("ok")
        elif action == "logout":
            expiry = None; out.append("logged_out")
        else:
            if expire_at_browser_close: expiry = None
            out.append("closed")
    return out
''',
        '''def session_log(events, cookie_age, save_every_request, expire_at_browser_close):
    expiry, out = None, []
    for t, action in events:
        if action == "login":
            expiry = t + cookie_age; out.append("ok")
        elif action in ("view", "modify"):
            if expiry is None: out.append("anonymous")
            elif t >= expiry: out.append("expired")
            else:
                if action == "modify" or save_every_request: expiry = t + cookie_age
                out.append("ok")
        elif action == "logout":
            expiry = None; out.append("logged_out")
        else:
            expiry = None; out.append("closed")
    return out
''',
    ],
    guide=dict(
        prereqs="Lesson *The auth app: users, passwords and sessions*.",
        intuition="A session is a record with a best-before date. Reading it does not change the date; *saving* it does. "
                  "So an idle-timeout ('log me out after 30 minutes of inactivity') needs `SESSION_SAVE_EVERY_REQUEST`, "
                  "while the default behaves like an absolute lifetime measured from the last modification.",
        hints=[
            "One variable is enough: `expiry`, or `None` for 'no session'.",
            "Expired means `t >= expiry`; at that moment forget the session so later requests are anonymous.",
            "Only slide the expiry on `modify`, or on any successful request when `save_every_request` is true.",
        ],
        brute_force="Store every event and recompute the expiry from the whole history for each request: O(n²). The state machine with one variable is O(n).",
        approach="""1. Keep `expiry`. 2. Apply the table row for each event. 3. Collect results.

**Dry run** age 100, no sliding: login at 0 → expiry 100; modify at 99 → ok, expiry 199; view at 198 → ok
(unchanged); view at 199 → `199 >= 199` → expired; view at 200 → anonymous.""",
        complexity="O(n) time, O(1) state.",
        pitfalls="""- Extending the session on every read when `save_every_request` is false.
- Using `>` at the boundary.
- Reporting `expired` forever instead of once.
- Deleting the session on `close_browser` when the setting is off.""",
        follow_up="Real expired rows stay in the `django_session` table until `python manage.py clearsessions` runs; add a counter of rows that would be purged.",
    ),
),
dict(
    id="django-signal-dispatch",
    title="Signal dispatch order",
    difficulty="Medium",
    pattern="Signals",
    entry="run_signals",
    description=r"""
A Django **signal** lets one piece of code announce "this happened" and any number of **receivers** react,
without the sender knowing who they are. Simulate one signal object.

`run_signals(ops)` processes a list of operations and returns one result per `send`/`send_robust`:

- `["connect", receiver, sender, uid]`: register a receiver (a name). `sender` is a model name, or `None` to
  listen to every sender. `uid` is the `dispatch_uid` or `None`. The registration key is
  `(uid, sender)` when `uid` is given and `(receiver, sender)` otherwise. **If the key is already registered
  the call does nothing** (this is how `dispatch_uid` prevents double registration).
- `["disconnect", receiver, sender, uid]`: remove the registration with the same key, if present.
- `["send", sender]`: call, **in order of connection**, every receiver registered with that sender or with
  `None`. A receiver whose name starts with `bad` raises an exception. With `send`, the exception propagates:
  the result is the names called so far followed by `"!" + name`, and the remaining receivers are **not** called.
- `["send_robust", sender]`: the same, but exceptions are caught: record `"!" + name` and continue with the rest.

Receivers that succeed are recorded by name. Return the list of result lists.

**Example:** connect `log` (any sender), `bad_mailer` (sender `Story`), `index` (sender `Story`), then
`["send", "Story"]` → `["log", "!bad_mailer"]`; `["send_robust", "Story"]` → `["log", "!bad_mailer", "index"]`;
`["send", "Reply"]` → `["log"]`.
""",
    starter='''def run_signals(ops: list) -> list:
    pass
''',
    solution='''def run_signals(ops):
    registry = []  # list of (key, receiver, sender) in connection order
    results = []
    for op in ops:
        kind = op[0]
        if kind in ("connect", "disconnect"):
            _, receiver, sender, uid = op
            key = (uid if uid is not None else receiver, sender)
            exists = any(k == key for k, _, _ in registry)
            if kind == "connect" and not exists:
                registry.append((key, receiver, sender))
            elif kind == "disconnect":
                registry = [entry for entry in registry if entry[0] != key]
        else:
            sender = op[1]
            called = []
            for _, receiver, wanted in registry:
                if wanted is not None and wanted != sender:
                    continue
                if receiver.startswith("bad"):
                    called.append("!" + receiver)
                    if kind == "send":
                        break
                else:
                    called.append(receiver)
            results.append(called)
    return results
''',
    tests=[
        [[["connect", "log", None, None], ["connect", "bad_mailer", "Story", None], ["connect", "index", "Story", None],
          ["send", "Story"], ["send_robust", "Story"], ["send", "Reply"]]],
        [[["send", "Story"]]],
        [[]],
        [[["connect", "a", "Story", None], ["connect", "a", "Story", None], ["send", "Story"]]],
        [[["connect", "a", "Story", None], ["connect", "a", "Reply", None], ["connect", "a", None, None], ["send", "Story"], ["send", "Reply"], ["send", "Tag"]]],
        [[["connect", "a", "Story", "uid-1"], ["connect", "b", "Story", "uid-1"], ["send", "Story"]]],
        [[["connect", "a", "Story", "uid-1"], ["connect", "a", "Story", None], ["send", "Story"]]],
        [[["connect", "z", None, None], ["connect", "y", None, None], ["connect", "x", None, None], ["send", "S"], ["disconnect", "y", None, None], ["send", "S"]]],
        [[["connect", "a", "Story", "u"], ["disconnect", "a", "Story", None], ["send", "Story"], ["disconnect", "zzz", "Story", "u"], ["send", "Story"]]],
        [[["connect", "bad1", None, None], ["connect", "ok", None, None], ["connect", "bad2", None, None], ["send", "S"], ["send_robust", "S"]]],
        [[["connect", "a", None, None], ["disconnect", "a", None, None], ["connect", "b", None, None], ["connect", "a", None, None], ["send_robust", "S"]]],
        [[["disconnect", "ghost", None, None], ["connect", "a", "Story", None], ["disconnect", "a", "Reply", None], ["send", "Story"]]],
        [[["connect", "first", "Story", None], ["connect", "second", None, None], ["connect", "third", "Story", None], ["send", "Story"], ["send", None]]],
    ],
    examples=1,
    wrong_solutions=[
        '''def run_signals(ops):
    registry, results = [], []
    for op in ops:
        if op[0] == "connect":
            registry.append((op[1], op[2]))
        elif op[0] == "disconnect":
            registry = [r for r in registry if r != (op[1], op[2])]
        else:
            results.append([("!" + r if r.startswith("bad") else r) for r, s in registry if s is None or s == op[1]])
    return results
''',
        '''def run_signals(ops):
    registry, results = {}, []
    for op in ops:
        kind = op[0]
        if kind in ("connect", "disconnect"):
            _, receiver, sender, uid = op
            key = (uid if uid is not None else receiver, sender)
            if kind == "connect":
                registry[key] = (receiver, sender)
            else:
                registry.pop(key, None)
        else:
            called = []
            for receiver, wanted in sorted(registry.values(), key=lambda e: e[0]):
                if wanted is not None and wanted != op[1]:
                    continue
                if receiver.startswith("bad"):
                    called.append("!" + receiver)
                    if kind == "send":
                        break
                else:
                    called.append(receiver)
            results.append(called)
    return results
''',
    ],
    guide=dict(
        prereqs="Lesson *Architecture questions* (signals).",
        intuition="A signal is a list of callbacks with a filter. Connecting appends to the list unless the same key is "
                  "already there; sending walks the list in order and calls the entries whose sender filter matches. "
                  "`send` and `send_robust` differ only in what happens when a callback blows up.",
        hints=[
            "Use a list (not a set) for the registry so connection order is preserved.",
            "The key is `(uid or receiver, sender)`; a duplicate `connect` is silently ignored and keeps the original receiver.",
            "`break` on the first failure for `send`; keep going for `send_robust`.",
        ],
        brute_force="No cheaper trick exists; the naive version forgets de-duplication, so a module imported twice runs its receiver twice. That is the real-world bug `dispatch_uid` exists to prevent.",
        approach="""1. `connect`: compute the key, append if absent. `disconnect`: drop the entry with that key.
2. `send*`: iterate in order, filter by sender, record names, handle `bad*` per mode.

**Dry run** registry `log(None)`, `bad_mailer(Story)`, `index(Story)`; `send Story` → `log`, then `!bad_mailer`
and stop; `send_robust Story` → `log`, `!bad_mailer`, `index`.""",
        complexity="O(R) per operation for R registered receivers.",
        pitfalls="""- Registering the same receiver twice.
- With a `dispatch_uid`, a second `connect` under the same uid does **not** replace the first receiver.
- A receiver connected with `sender=None` hears everything, including senders nobody registered for.
- Signals run synchronously inside the sender's call (and transaction); one failing receiver under `send` hides the others.""",
        follow_up="Django 5.0 added `asend()`/`asend_robust()`, which run async receivers concurrently. Think about what 'order' means there.",
    ),
),
dict(
    id="django-cache-key",
    title="View-cache keys and invalidation",
    difficulty="Medium",
    pattern="Performance",
    entry="cache_sim",
    description=r"""
A per-view cache stores whole responses under a key derived from the request. Two requests share a cached page
exactly when their keys are equal, so the key must contain everything that changes the response and nothing
that does not. Simulate such a cache.

`cache_sim(ops, prefix, vary_on)`:

The cache starts empty with **version 1**. The key of a request is

`"{prefix}:{version}:{METHOD}:{path}?{query}:{vary}"`

- `query`: the request's query parameters (a dict) rendered as `k=v` pairs joined by `&`, **sorted by key**
  (empty string when there are none);
- `vary`: for each header name in `vary_on` (in that order) the request's value for it, or `""` when absent,
  joined by `,`.

Operations (return one result string per operation):

- `["request", method, path, query, headers]`:
  - methods other than `GET` and `HEAD` are never cached → `"BYPASS"`;
  - if the key is stored → `"HIT " + key`; otherwise store it → `"MISS " + key`.
- `["delete_path", path]`: remove every stored key **of the current version** whose path equals `path`
  (any method, query or vary values) → `"deleted=" + count`.
- `["bump"]`: increase the version by 1. Old entries stay in storage but can no longer be reached →
  `"version=" + new version`.

**Example:** `prefix="gz"`, `vary_on=["cookie"]`: `GET /stories/ {"page": "2"}` with no headers →
`"MISS gz:1:GET:/stories/?page=2:"`; the same request again → `"HIT gz:1:GET:/stories/?page=2:"`.
""",
    starter='''def cache_sim(ops: list, prefix: str, vary_on: list) -> list:
    pass
''',
    solution='''def cache_sim(ops, prefix, vary_on):
    version = 1
    store = {}  # key -> (version, path)
    out = []
    for op in ops:
        if op[0] == "request":
            _, method, path, query, headers = op
            if method not in ("GET", "HEAD"):
                out.append("BYPASS")
                continue
            qs = "&".join("%s=%s" % (k, query[k]) for k in sorted(query))
            vary = ",".join(headers.get(h, "") for h in vary_on)
            key = "%s:%d:%s:%s?%s:%s" % (prefix, version, method, path, qs, vary)
            if key in store:
                out.append("HIT " + key)
            else:
                store[key] = (version, path)
                out.append("MISS " + key)
        elif op[0] == "delete_path":
            doomed = [k for k, (v, p) in store.items() if v == version and p == op[1]]
            for k in doomed:
                del store[k]
            out.append("deleted=%d" % len(doomed))
        else:
            version += 1
            out.append("version=%d" % version)
    return out
''',
    tests=[
        [[["request", "GET", "/stories/", {"page": "2"}, {}], ["request", "GET", "/stories/", {"page": "2"}, {}]], "gz", ["cookie"]],
        [[["request", "GET", "/", {}, {}], ["request", "POST", "/", {}, {}], ["request", "GET", "/", {}, {}]], "gz", []],
        [[], "gz", []],
        [[["request", "GET", "/s/", {"b": "2", "a": "1"}, {}], ["request", "GET", "/s/", {"a": "1", "b": "2"}, {}], ["request", "GET", "/s/", {"a": "1"}, {}]], "p", []],
        [[["request", "GET", "/me/", {}, {"cookie": "sid=1"}], ["request", "GET", "/me/", {}, {"cookie": "sid=2"}], ["request", "GET", "/me/", {}, {"cookie": "sid=1"}], ["request", "GET", "/me/", {}, {}]], "p", ["cookie"]],
        [[["request", "GET", "/me/", {}, {"cookie": "sid=1"}], ["request", "GET", "/me/", {}, {"cookie": "sid=2"}]], "p", []],
        [[["request", "GET", "/a/", {}, {}], ["request", "HEAD", "/a/", {}, {}], ["request", "HEAD", "/a/", {}, {}], ["request", "DELETE", "/a/", {}, {}]], "p", []],
        [[["request", "GET", "/a/", {}, {}], ["bump"], ["request", "GET", "/a/", {}, {}], ["request", "GET", "/a/", {}, {}]], "p", []],
        [[["request", "GET", "/a/", {}, {}], ["request", "GET", "/a/", {"x": "1"}, {}], ["request", "HEAD", "/a/", {}, {}], ["request", "GET", "/b/", {}, {}],
          ["delete_path", "/a/"], ["request", "GET", "/a/", {}, {}], ["request", "GET", "/b/", {}, {}], ["delete_path", "/zzz/"]], "p", []],
        [[["request", "GET", "/a/", {}, {}], ["bump"], ["delete_path", "/a/"], ["request", "GET", "/a/", {}, {}], ["delete_path", "/a/"], ["delete_path", "/a/"]], "p", []],
        [[["request", "GET", "/a/", {}, {"accept-language": "fr", "cookie": "c"}], ["request", "GET", "/a/", {}, {"accept-language": "en", "cookie": "c"}],
          ["request", "GET", "/a/", {}, {"cookie": "c", "accept-language": "fr"}]], "site", ["accept-language", "cookie"]],
        [[["bump"], ["bump"], ["request", "GET", "/a/", {"q": ""}, {}]], "", ["x"]],
        [[["request", "GET", "/a", {}, {}], ["request", "GET", "/a/", {}, {}], ["delete_path", "/a"], ["request", "GET", "/a/", {}, {}]], "p", []],
    ],
    examples=2,
    wrong_solutions=[
        '''def cache_sim(ops, prefix, vary_on):
    store, out, version = set(), [], 1
    for op in ops:
        if op[0] == "request":
            key = "%s:%d:%s:%s" % (prefix, version, op[1], op[2])
            if key in store: out.append("HIT " + key)
            else:
                store.add(key); out.append("MISS " + key)
        elif op[0] == "delete_path":
            n = len([k for k in store if k.endswith(op[1])])
            store = {k for k in store if not k.endswith(op[1])}
            out.append("deleted=%d" % n)
        else:
            version += 1; out.append("version=%d" % version)
    return out
''',
        '''def cache_sim(ops, prefix, vary_on):
    version, store, out = 1, {}, []
    for op in ops:
        if op[0] == "request":
            _, method, path, query, headers = op
            if method == "POST":
                out.append("BYPASS"); continue
            qs = "&".join("%s=%s" % (k, v) for k, v in query.items())
            vary = ",".join(headers.get(h, "") for h in vary_on)
            key = "%s:%d:%s:%s?%s:%s" % (prefix, version, method, path, qs, vary)
            if key in store: out.append("HIT " + key)
            else:
                store[key] = path; out.append("MISS " + key)
        elif op[0] == "delete_path":
            doomed = [k for k, p in store.items() if p == op[1]]
            for k in doomed: del store[k]
            out.append("deleted=%d" % len(doomed))
        else:
            version += 1; out.append("version=%d" % version)
    return out
''',
    ],
    guide=dict(
        prereqs="Lesson *Caching, the debug toolbar and the security middleware*; string formatting; dictionaries.",
        intuition="Caching has two hard parts: naming and forgetting. The key names a response by everything it depends "
                  "on (method, path, query, selected headers). Forgetting comes in two flavours: delete specific keys, "
                  "or bump a version number so that every old key becomes unreachable at once without touching storage.",
        hints=[
            "Sort the query items so parameter order does not create duplicate entries.",
            "Store, next to each key, the version and path it was created for; `delete_path` needs both.",
            "`bump` only increments a counter. Nothing is deleted.",
        ],
        brute_force="Clear the whole cache whenever anything changes. Correct and simple, but every user then pays for a cold cache; targeted deletion and versioning limit the blast radius.",
        approach="""1. For a request: bypass unsafe methods; build `qs` and `vary`; format the key; hit or store.
2. `delete_path`: collect keys whose stored version equals the current one and whose path matches; delete; report the count.
3. `bump`: `version += 1`.

**Dry run** GET `/a/` → MISS (v1). `bump` → version 2. `delete_path /a/` → the stored key belongs to version 1 →
`deleted=0`. GET `/a/` → new key with `:2:` → MISS.""",
        complexity="O(q log q) per request for q query parameters; `delete_path` scans the store, O(S). Real caches cannot scan, which is why key design and versioning matter.",
        pitfalls="""- Leaving the query string or the `Vary` headers out of the key serves one user's page to another.
- Caching `POST` responses.
- Matching paths by suffix (`/a` vs `/a/`).
- Counting unreachable old-version entries in `delete_path`.
- Real Django keys hash the full URL as received, so `?a=1&b=2` and `?b=2&a=1` are separate entries there.""",
        follow_up="Add a TTL per entry with explicit timestamps, then implement `cache.get_or_set` on top of it.",
    ),
),
dict(
    id="django-settings-env",
    title="Settings precedence from environment variables",
    difficulty="Medium",
    pattern="Deployment",
    entry="load_settings",
    description=r"""
Twelve-factor apps read configuration from the environment. A typical `settings.py` merges three sources:
real environment variables (highest priority), a `.env` file, and defaults in code. Environment values are
always strings, so they must be **cast**.

`load_settings(schema, defaults, env_lines, environ)`:

- `schema`: dict (ordered) `NAME -> {"type": "str" | "int" | "bool" | "list", "required": bool (default False)}`.
- `defaults`: dict of ready-made Python values (used as they are, never cast).
- `env_lines`: the lines of a `.env` file. Parse each line as follows: strip whitespace; skip it if empty or
  starting with `#`; remove a leading `export ` if present; skip it if it has no `=`; split at the **first**
  `=` into key and value and strip both. If the value starts and ends with the same quote character (`'` or
  `"`, and is at least 2 characters long) remove that pair of quotes; otherwise cut the value at the first
  occurrence of ` #` (space, hash: an inline comment) and strip it again. Later lines override earlier ones.
- `environ`: dict of real environment variables (strings).

For each `NAME` in schema order: take the raw string from `environ` if present, else from the `.env` data,
and cast it; if neither has it, use `defaults[NAME]` if present; if nothing provides it, record the error
`"NAME: missing"` when the setting is required and otherwise leave it out.

Casting: `str` → unchanged. `int` → optional `-` and digits, else error. `bool` → case-insensitively
`1/true/yes/on` → `True`, `0/false/no/off` and the empty string → `False`, anything else is an error.
`list` → split on commas, strip each item, drop empty items. A failed cast records `"NAME: invalid <type>"`
and the setting is left out (no fallback to the default).

Names not in the schema are ignored. Return `[settings, errors]` with errors in schema order.

**Example:** schema `{"DEBUG": {"type": "bool"}}`, defaults `{"DEBUG": False}`, `.env` line `DEBUG=true`,
environ `{"DEBUG": "0"}` → `[{"DEBUG": False}, []]` (the real environment wins).
""",
    starter='''def load_settings(schema: dict, defaults: dict, env_lines: list, environ: dict) -> list:
    pass
''',
    solution=r'''import re

_TRUE = {"1", "true", "yes", "on"}
_FALSE = {"0", "false", "no", "off", ""}


def _parse_env(lines):
    data = {}
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export "):]
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key, value = key.strip(), value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
            value = value[1:-1]
        else:
            cut = value.find(" #")
            if cut != -1:
                value = value[:cut].strip()
        data[key] = value
    return data


def _cast(raw, kind):
    if kind == "str":
        return True, raw
    if kind == "int":
        if re.fullmatch(r"-?[0-9]+", raw):
            return True, int(raw)
        return False, None
    if kind == "bool":
        low = raw.lower()
        if low in _TRUE:
            return True, True
        if low in _FALSE:
            return True, False
        return False, None
    return True, [item.strip() for item in raw.split(",") if item.strip()]


def load_settings(schema, defaults, env_lines, environ):
    file_values = _parse_env(env_lines)
    settings, errors = {}, []
    for name, rule in schema.items():
        if name in environ:
            raw = environ[name]
        elif name in file_values:
            raw = file_values[name]
        else:
            if name in defaults:
                settings[name] = defaults[name]
            elif rule.get("required", False):
                errors.append(name + ": missing")
            continue
        ok, value = _cast(raw, rule["type"])
        if ok:
            settings[name] = value
        else:
            errors.append("%s: invalid %s" % (name, rule["type"]))
    return [settings, errors]
''',
    tests=[
        [{"DEBUG": {"type": "bool"}}, {"DEBUG": False}, ["DEBUG=true"], {"DEBUG": "0"}],
        [_SCHEMA, {"DEBUG": False, "ALLOWED_HOSTS": [], "DB_PORT": 5432}, _ENVFILE, {}],
        [_SCHEMA, {"DEBUG": False, "ALLOWED_HOSTS": [], "DB_PORT": 5432}, [], {}],
        [_SCHEMA, {}, _ENVFILE, {"DEBUG": "Off", "SECRET_KEY": "prod # not a comment", "ALLOWED_HOSTS": "gazette.example", "DB_PORT": "6543", "EMAIL_HOST": ""}],
        [_SCHEMA, {"DB_PORT": 5432}, ["SECRET_KEY=x"], {"DEBUG": "maybe", "DB_PORT": "54a32"}],
        [_SCHEMA, {"SECRET_KEY": "fallback"}, ["SECRET_KEY=first", "SECRET_KEY=second=with=equals"], {}],
        [{}, {"A": 1}, ["A=2"], {"A": "3"}],
        [{"A": {"type": "int", "required": True}, "B": {"type": "int", "required": True}}, {"B": 7}, ["  # c", "A = -12  "], {}],
        [{"L": {"type": "list"}}, {}, ["L= a , b,,c ,"], {}],
        [{"L": {"type": "list"}, "E": {"type": "bool"}}, {}, ["L=", "E="], {}],
        [{"Q": {"type": "str"}, "R": {"type": "str"}, "S": {"type": "str"}}, {}, ["Q=\"double 'inner' # kept\"", "R='single", "S=plain value # trailing comment"], {}],
        [{"X": {"type": "bool"}, "Y": {"type": "bool"}, "Z": {"type": "bool"}}, {}, ["X=YES", "Y=On", "Z=1"], {"Z": "FALSE"}],
        [{"N": {"type": "int"}}, {"N": 1}, ["N=oops"], {}],
        [{"N": {"type": "int"}, "M": {"type": "int"}}, {}, ["export N=5", "exportM=6", "M=+7"], {}],
        [{"K": {"type": "str", "required": True}}, {}, ["#K=commented"], {"OTHER": "1"}],
    ],
    examples=2,
    wrong_solutions=[
        '''def load_settings(schema, defaults, env_lines, environ):
    settings = dict(defaults)
    for line in env_lines:
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            settings[k.strip()] = v.strip()
    settings.update(environ)
    return [{k: v for k, v in settings.items() if k in schema}, []]
''',
        r'''import re
def load_settings(schema, defaults, env_lines, environ):
    data = {}
    for line in env_lines:
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):
            line = line[7:]
        k, v = line.split("=", 1)
        data[k.strip()] = v.strip().strip("'\"").split(" #")[0].strip()
    settings, errors = {}, []
    for name, rule in schema.items():
        raw = data.get(name, environ.get(name))
        if raw is None:
            if name in defaults: settings[name] = defaults[name]
            elif rule.get("required"): errors.append(name + ": missing")
            continue
        t = rule["type"]
        if t == "str": settings[name] = raw
        elif t == "int":
            if re.fullmatch(r"-?[0-9]+", raw): settings[name] = int(raw)
            else: errors.append(name + ": invalid int")
        elif t == "bool":
            if raw.lower() in ("1", "true", "yes", "on"): settings[name] = True
            elif raw.lower() in ("0", "false", "no", "off", ""): settings[name] = False
            else: errors.append(name + ": invalid bool")
        else:
            settings[name] = [i.strip() for i in raw.split(",") if i.strip()]
    return [settings, errors]
''',
    ],
    guide=dict(
        prereqs="Lesson *Production settings and the security checklist*; string parsing.",
        intuition="Configuration is layered like transparent sheets: defaults at the bottom, the `.env` file over them, the "
                  "real environment on top. For each name you look down through the stack and take the first value you "
                  "see. Since the top two layers hold only text, the schema says how to turn text into a Python value, "
                  "and a value that cannot be converted is an error, never a silent fallback.",
        hints=[
            "Parse the `.env` lines into a dict first; keep that separate from the precedence logic.",
            "`bool(\"False\")` is `True` in Python. Compare lower-cased text against explicit sets.",
            "Check `name in environ` rather than truthiness: an empty string in the environment is a real value.",
        ],
        brute_force="`os.environ.get(\"DEBUG\", False)` sprinkled through the settings file. It 'works' until someone sets `DEBUG=False` and the non-empty string turns debug mode **on** in production.",
        approach="""1. Parse the file (skip comments, `export`, split on the first `=`, unquote or cut inline comments).
2. For each schema entry choose the source: environ, file, default, or missing.
3. Cast strings from the first two sources; collect errors.

**Dry run** `DB_PORT=5432   # default postgres`: value is not quoted → cut at ` #` → `5432` → `int` 5432.
`ALLOWED_HOSTS = "localhost, 127.0.0.1,,"`: quoted → unquote → list `["localhost", "127.0.0.1"]`.""",
        complexity="O(total size of the inputs).",
        pitfalls="""- Wrong precedence (file over environment) makes it impossible to override settings on the server.
- Treating `"0"` or `"false"` as true.
- Splitting on every `=` breaks secrets that contain one.
- A `#` inside quotes is data, not a comment.
- Falling back to a default after a failed cast hides a typo in production configuration.""",
        follow_up="Libraries such as `django-environ` and `python-decouple` implement exactly this. Add URL parsing for `DATABASE_URL=postgres://user:pass@host:5432/name`.",
    ),
),
]
